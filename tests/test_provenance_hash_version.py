"""
Regression tests for the M4 hash_version fix (Claude audit 2026-07-28).

ProvenanceChain._compute_hash's formula was changed in-place (FIX #6/#7) to
fold actor/reason into the hash, with no schema versioning — unlike
audit_chain.py's hash_version v1/v2 dual-dispatch for the exact same kind of
change. Any row hashed under the pre-#6/#7 formula (no actor/reason) would
fail verify() with a false hash_mismatch: HASH_VERSION_LEGACY (1) restores
that original formula for exactly such rows, HASH_VERSION_CURRENT (2) is
what append() now writes, and verify() dispatches per stored hash_version.
"""
from __future__ import annotations

import sqlite3
import tempfile
import os

import pytest

from core.provenance_chain import (
    GENESIS,
    HASH_VERSION_CURRENT,
    HASH_VERSION_LEGACY,
    ProvenanceChain,
)


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "pc.db")


class TestNewRowsAreTaggedCurrentAndVerify:
    def test_appended_rows_are_hash_version_current(self, db_path):
        chain = ProvenanceChain(db_path)
        chain.append("f1", event_type="fact_created", actor="user")
        events = chain.get_chain("f1")
        assert events[0]["hash_version"] == HASH_VERSION_CURRENT

    def test_verify_still_detects_actor_tampering_on_current_rows(self, db_path):
        """Sibling assertion to test_I_PC2 (test_invariants.py): the
        actor/reason coverage FIX #6/#7 added must still work after this fix."""
        chain = ProvenanceChain(db_path)
        chain.append("f2", event_type="fact_created", actor="user")

        # The append-only triggers (this session's own Low fix) correctly
        # block this UPDATE now — drop them first to simulate a genuine
        # tamper that bypassed the DB-level guard entirely (e.g. a restored
        # backup or direct file-level edit), same convention as
        # test_audit_chain_v2.py's `mutable_db` fixture.
        with sqlite3.connect(db_path) as conn:
            conn.execute("DROP TRIGGER IF EXISTS prevent_provenance_update")
            conn.execute(
                "UPDATE provenance_chains SET actor = 'attacker' "
                "WHERE fact_id = 'f2' AND seq = 0"
            )
            conn.commit()

        ok, msg = chain.verify("f2")
        assert not ok
        assert "hash_mismatch" in msg


class TestLegacyRowsVerifyWithoutFalseMismatch:
    def _insert_legacy_row(self, db_path, fact_id, *, actor="user", reason=None,
                            event_type="fact_created", from_state=None, to_state=None):
        """Insert a row exactly as append() would have, before FIX #6/#7 —
        hashed with the pre-actor/reason formula and tagged HASH_VERSION_LEGACY."""
        import hashlib
        import json
        from datetime import datetime, timezone

        created_at = datetime.now(timezone.utc).isoformat()
        payload_str = json.dumps({}, sort_keys=True, ensure_ascii=False)
        data = "|".join([
            GENESIS, event_type, fact_id,
            from_state or "", to_state or "", payload_str, created_at,
        ])
        event_hash = hashlib.sha256(data.encode("utf-8")).hexdigest()

        with sqlite3.connect(db_path) as conn:
            conn.execute(
                """INSERT INTO provenance_chains
                   (fact_id, seq, event_type, actor, from_state, to_state,
                    reason, payload_json, event_hash, prev_hash, created_at,
                    hash_version)
                   VALUES (?, 0, ?, ?, ?, ?, ?, '{}', ?, ?, ?, ?)""",
                (
                    fact_id, event_type, actor, from_state, to_state,
                    reason, event_hash, GENESIS, created_at, HASH_VERSION_LEGACY,
                ),
            )
            conn.commit()

    def test_legacy_row_verifies_true_not_false_mismatch(self, db_path):
        chain = ProvenanceChain(db_path)  # runs schema self-heal first
        self._insert_legacy_row(db_path, "legacy-1")

        ok, msg = chain.verify("legacy-1")
        assert ok, f"a genuine pre-fix row must verify clean, got: {msg}"

    def test_legacy_row_followed_by_new_append_still_verifies(self, db_path):
        """The realistic case: a fact with history predating the fix, then
        a fresh event appended after upgrade — the chain must validate
        end-to-end across the version boundary."""
        chain = ProvenanceChain(db_path)
        self._insert_legacy_row(db_path, "legacy-2")

        # append()'s seq/prev_hash logic reads the real last row, so the
        # new event correctly chains onto the legacy row's actual hash.
        ok2, _ = chain.append("legacy-2", event_type="fact_updated", actor="system")
        assert ok2

        ok, msg = chain.verify("legacy-2")
        assert ok, f"chain spanning legacy + current rows must verify clean, got: {msg}"

        events = chain.get_chain("legacy-2")
        assert events[0]["hash_version"] == HASH_VERSION_LEGACY
        assert events[1]["hash_version"] == HASH_VERSION_CURRENT

    def test_tampering_a_legacy_row_is_still_detected(self, db_path):
        chain = ProvenanceChain(db_path)
        self._insert_legacy_row(db_path, "legacy-3", from_state="Observed", to_state="Hypothesized")

        # See test_verify_still_detects_actor_tampering_on_current_rows above
        # for why the trigger is dropped first.
        with sqlite3.connect(db_path) as conn:
            conn.execute("DROP TRIGGER IF EXISTS prevent_provenance_update")
            conn.execute(
                "UPDATE provenance_chains SET to_state = 'Validated' "
                "WHERE fact_id = 'legacy-3' AND seq = 0"
            )
            conn.commit()

        ok, msg = chain.verify("legacy-3")
        assert not ok
        assert "hash_mismatch" in msg


class TestSchemaSelfHealOnPreExistingTable:
    def test_table_created_before_hash_version_existed_gets_column_added(self, db_path):
        """A DB whose provenance_chains table predates this fix (no
        hash_version column at all) must self-heal on construction, not
        crash on the very first get_chain()/append() call."""
        pre_fix_ddl = """
        CREATE TABLE provenance_chains (
            fact_id     TEXT NOT NULL,
            seq         INTEGER NOT NULL DEFAULT 0,
            event_type  TEXT NOT NULL,
            actor       TEXT NOT NULL DEFAULT 'system',
            from_state  TEXT DEFAULT NULL,
            to_state    TEXT DEFAULT NULL,
            reason      TEXT DEFAULT NULL,
            payload_json TEXT DEFAULT '{}',
            event_hash  TEXT NOT NULL DEFAULT '',
            prev_hash   TEXT DEFAULT NULL,
            created_at  TEXT NOT NULL,
            PRIMARY KEY (fact_id, seq)
        );
        """
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        with sqlite3.connect(db_path) as conn:
            conn.executescript(pre_fix_ddl)
            conn.commit()

        chain = ProvenanceChain(db_path)  # must not raise
        ok, h = chain.append("post-heal", event_type="fact_created", actor="user")
        assert ok

        with sqlite3.connect(db_path) as conn:
            cols = {row[1] for row in conn.execute("PRAGMA table_info(provenance_chains)").fetchall()}
        assert "hash_version" in cols

        ok, msg = chain.verify("post-heal")
        assert ok, msg


class TestNextSeqLogsInsteadOfSilentlySwallowing:
    def test_next_seq_failure_is_logged_not_silent(self, db_path, monkeypatch, caplog):
        """Low finding (Claude audit 2026-07-28): _next_seq()'s except
        branch returned 0 — the SAME value as the legitimate "no prior
        events" sentinel — with no log at all, so a genuine query failure
        was indistinguishable from an empty chain. Must still return 0
        (unchanged fallback), but now visibly."""
        import logging

        chain = ProvenanceChain(db_path)

        real_connect = sqlite3.connect

        def boom_connect(*a, **k):
            raise sqlite3.OperationalError("simulated failure")

        monkeypatch.setattr(sqlite3, "connect", boom_connect)
        with caplog.at_level(logging.WARNING, logger="velantrim.provenance_chain"):
            seq = chain._next_seq("some-fact")
        monkeypatch.setattr(sqlite3, "connect", real_connect)

        assert seq == 0
        assert any("_next_seq failed" in r.message for r in caplog.records)


class TestAppendOnlyDBTriggers:
    """Low finding (Claude audit 2026-07-28): provenance_chains had no
    DB-level append-only enforcement at all, unlike memory_events/
    audit_chain's prevent_audit_update/prevent_audit_delete."""

    def test_update_is_rejected_at_the_db_level(self, db_path):
        chain = ProvenanceChain(db_path)
        chain.append("t1", event_type="fact_created", actor="user")

        with sqlite3.connect(db_path) as conn:
            with pytest.raises(sqlite3.IntegrityError, match="append-only"):
                conn.execute(
                    "UPDATE provenance_chains SET actor = 'x' WHERE fact_id = 't1'"
                )

    def test_delete_is_rejected_at_the_db_level(self, db_path):
        chain = ProvenanceChain(db_path)
        chain.append("t2", event_type="fact_created", actor="user")

        with sqlite3.connect(db_path) as conn:
            with pytest.raises(sqlite3.IntegrityError, match="append-only"):
                conn.execute("DELETE FROM provenance_chains WHERE fact_id = 't2'")
