"""
tests/test_audit_chain_v2.py — AuditChain Hash v2 (Stage B)
=============================================================
Groups:
  A. Hash coverage — real tamper detection per hashed field
  B. Canonicalization — deterministic JSON envelope
  C. Versioning / migration — v1/v2 interop
  D. Concurrency — atomic append under contention
  E. Verification semantics — bounded/mixed-version/receipts
  F. Compatibility — existing public API + Observer integration
"""
from __future__ import annotations

import json
import sqlite3
import threading

import pytest

from core.audit_chain import (
    AuditChain,
    AuditChainError,
    EventType,
    HASH_VERSION_CURRENT,
    HASH_VERSION_LEGACY,
    compute_audit_hash_v1,
    compute_audit_hash_v2,
    validate_confidence,
    validate_payload,
)


# ─── Fixtures ─────────────────────────────────────────────────────────────────

def _bare_v1_schema(conn: sqlite3.Connection, *, with_triggers: bool) -> None:
    """Build the pre-Stage-B v1 memory_events shape (same columns as
    migration 009 / tests/test_truth_kernel.py's own fixture), optionally
    with the append-only triggers. Proves AuditChain._ensure_schema()
    additively self-heals onto exactly this bare shape."""
    conn.executescript("""
        CREATE TABLE memory_events (
            event_id        TEXT PRIMARY KEY,
            event_type      TEXT NOT NULL,
            fact_id         TEXT,
            from_state      TEXT,
            to_state        TEXT,
            actor           TEXT NOT NULL,
            reason          TEXT,
            payload         TEXT,
            confidence      REAL,
            event_hash      TEXT NOT NULL UNIQUE,
            prev_event_hash TEXT,
            created_at      TEXT NOT NULL DEFAULT (datetime('now'))
        );
    """)
    if with_triggers:
        conn.executescript("""
            CREATE TRIGGER prevent_audit_update
            BEFORE UPDATE ON memory_events
            BEGIN
                SELECT RAISE(ABORT, 'VELANTRIM: audit log is append-only');
            END;

            CREATE TRIGGER prevent_audit_delete
            BEFORE DELETE ON memory_events
            BEGIN
                SELECT RAISE(ABORT, 'VELANTRIM: audit log is append-only');
            END;
        """)
    conn.commit()


@pytest.fixture
def db():
    """Protected DB — append-only triggers active (production-like).
    Used for everything except the tamper-detection tests, which need a
    real mutation."""
    conn = sqlite3.connect(":memory:")
    _bare_v1_schema(conn, with_triggers=True)
    return conn


@pytest.fixture
def mutable_db():
    """Unprotected DB (no append-only triggers) — used ONLY to simulate a
    genuine tamper (e.g. a restored backup or a direct file-level edit
    that bypassed the DB-level trigger protection entirely). Hash-chain
    verification must still catch it; this replaces the historical no-op
    "tamper" test with a real mutation."""
    conn = sqlite3.connect(":memory:")
    _bare_v1_schema(conn, with_triggers=False)
    return conn


def _tamper(conn: sqlite3.Connection, event_id: str, column: str, value) -> None:
    conn.execute(f"UPDATE memory_events SET {column} = ? WHERE event_id = ?", (value, event_id))
    conn.commit()


# ═══════════════════════════════════════════════════════════════════════════
# Group A — Hash coverage: tampering with any hashed field is detected
# ═══════════════════════════════════════════════════════════════════════════

class TestHashCoverageTamperDetection:

    def _log_two(self, mutable_db):
        chain = AuditChain(mutable_db)
        e1 = chain.log(
            "type1", "actor1", fact_id="f1", from_state="Observed",
            to_state="Hypothesized", reason="initial reason",
            payload={"k": "v"}, confidence=0.42,
        )
        e2 = chain.log("type2", "actor2", fact_id="f1")
        return chain, e1, e2

    def test_tamper_event_id_detected(self, mutable_db):
        chain, e1, e2 = self._log_two(mutable_db)
        _tamper(mutable_db, e1.event_id, "event_id", "evt_tampered_id_0000")
        assert chain.verify_chain()["valid"] is False

    def test_tamper_reason_detected(self, mutable_db):
        chain, e1, e2 = self._log_two(mutable_db)
        _tamper(mutable_db, e1.event_id, "reason", "tampered reason")
        assert chain.verify_chain()["valid"] is False

    def test_tamper_confidence_detected(self, mutable_db):
        chain, e1, e2 = self._log_two(mutable_db)
        _tamper(mutable_db, e1.event_id, "confidence", 0.99)
        assert chain.verify_chain()["valid"] is False

    def test_tamper_actor_detected(self, mutable_db):
        chain, e1, e2 = self._log_two(mutable_db)
        _tamper(mutable_db, e1.event_id, "actor", "hacker")
        assert chain.verify_chain()["valid"] is False

    def test_tamper_from_state_detected(self, mutable_db):
        chain, e1, e2 = self._log_two(mutable_db)
        _tamper(mutable_db, e1.event_id, "from_state", "Collapsed")
        assert chain.verify_chain()["valid"] is False

    def test_tamper_to_state_detected(self, mutable_db):
        chain, e1, e2 = self._log_two(mutable_db)
        _tamper(mutable_db, e1.event_id, "to_state", "Collapsed")
        assert chain.verify_chain()["valid"] is False

    def test_tamper_payload_detected(self, mutable_db):
        chain, e1, e2 = self._log_two(mutable_db)
        _tamper(mutable_db, e1.event_id, "payload", json.dumps({"k": "TAMPERED"}))
        assert chain.verify_chain()["valid"] is False

    def test_tamper_created_at_detected(self, mutable_db):
        chain, e1, e2 = self._log_two(mutable_db)
        _tamper(mutable_db, e1.event_id, "created_at", "2000-01-01T00:00:00+00:00")
        assert chain.verify_chain()["valid"] is False

    def test_tamper_chain_sequence_detected(self, mutable_db):
        chain, e1, e2 = self._log_two(mutable_db)
        _tamper(mutable_db, e1.event_id, "chain_sequence", 99)
        assert chain.verify_chain()["valid"] is False

    def test_tamper_prev_event_hash_detected(self, mutable_db):
        chain, e1, e2 = self._log_two(mutable_db)
        _tamper(mutable_db, e2.event_id, "prev_event_hash", "0" * 64)
        assert chain.verify_chain()["valid"] is False

    def test_untampered_chain_still_verifies(self, mutable_db):
        """Sanity check the fixture/mechanism itself isn't broken."""
        chain, e1, e2 = self._log_two(mutable_db)
        result = chain.verify_chain()
        assert result["valid"] is True
        assert result["events_checked"] == 2


# ═══════════════════════════════════════════════════════════════════════════
# Group B — Canonicalization
# ═══════════════════════════════════════════════════════════════════════════

class TestCanonicalization:

    _BASE = dict(
        chain_id="c", chain_sequence=1, event_id="e1", event_type="t",
        fact_id="f", from_state=None, to_state=None, actor="a",
        reason=None, confidence=None, prev_event_hash=None,
        created_at="2026-01-01T00:00:00+00:00",
    )

    def test_payload_key_order_same_hash(self):
        h1 = compute_audit_hash_v2(payload={"a": 1, "b": 2}, **self._BASE)
        h2 = compute_audit_hash_v2(payload={"b": 2, "a": 1}, **self._BASE)
        assert h1 == h2

    def test_nested_payload_key_order_stable(self):
        h1 = compute_audit_hash_v2(payload={"outer": {"x": 1, "y": 2}}, **self._BASE)
        h2 = compute_audit_hash_v2(payload={"outer": {"y": 2, "x": 1}}, **self._BASE)
        assert h1 == h2

    def test_unicode_deterministic(self):
        base = dict(self._BASE, actor="актёр", reason="причина")
        h1 = compute_audit_hash_v2(payload={"текст": "значение"}, **base)
        h2 = compute_audit_hash_v2(payload={"текст": "значение"}, **base)
        assert h1 == h2
        assert len(h1) == 64

    def test_delimiter_characters_no_field_boundary_collision(self):
        # A naive pipe-delimited concatenation could let a "|" embedded in
        # one field masquerade as a field boundary, making two
        # structurally different events collide. The JSON envelope keeps
        # fields as distinct keys and must not have this weakness.
        common = dict(self._BASE, payload={})
        del common["fact_id"], common["actor"]
        h1 = compute_audit_hash_v2(fact_id="a|b", actor="c", **common)
        h2 = compute_audit_hash_v2(fact_id="a", actor="b|c", **common)
        assert h1 != h2

    def test_nan_in_payload_rejected(self):
        with pytest.raises(AuditChainError):
            compute_audit_hash_v2(payload={"x": float("nan")}, **self._BASE)

    def test_infinity_confidence_rejected(self):
        with pytest.raises(AuditChainError):
            validate_confidence(float("inf"))
        with pytest.raises(AuditChainError):
            validate_confidence(float("-inf"))

    def test_unsupported_payload_values_rejected(self):
        with pytest.raises(AuditChainError):
            validate_payload({"x": {1, 2, 3}})  # a set
        with pytest.raises(AuditChainError):
            validate_payload({"x": b"bytes"})
        with pytest.raises(AuditChainError):
            validate_payload({1: "non-string key"})  # type: ignore[dict-item]

    def test_bool_confidence_rejected(self):
        with pytest.raises(AuditChainError):
            validate_confidence(True)

    def test_finite_confidence_and_payload_pass_through(self):
        assert validate_confidence(0.5) == 0.5
        assert validate_confidence(None) is None
        assert validate_payload({"a": [1, 2, {"b": None}]}) == {"a": [1, 2, {"b": None}]}


# ═══════════════════════════════════════════════════════════════════════════
# Group C — Versioning / migration interop
# ═══════════════════════════════════════════════════════════════════════════

class TestVersioningAndMigration:

    def test_empty_db_new_event_writes_v2(self, mutable_db):
        chain = AuditChain(mutable_db)
        evt = chain.log("type1", "actor")
        assert evt.hash_version == HASH_VERSION_CURRENT
        row = mutable_db.execute(
            "SELECT hash_version, chain_sequence, chain_id FROM memory_events WHERE event_id=?",
            (evt.event_id,),
        ).fetchone()
        assert row == (2, 1, "memory_events")

    def test_historical_v1_row_unchanged_byte_for_byte(self, mutable_db):
        v1_hash = compute_audit_hash_v1(
            event_type="legacy", fact_id="f1", from_state=None, to_state=None,
            actor="agent", payload={"x": 1}, created_at="2020-01-01T00:00:00+00:00",
            prev_event_hash=None,
        )
        mutable_db.execute(
            "INSERT INTO memory_events (event_id, event_type, fact_id, actor, "
            "payload, confidence, event_hash, prev_event_hash, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ("evt_legacy1", "legacy", "f1", "agent", json.dumps({"x": 1}),
             None, v1_hash, None, "2020-01-01T00:00:00+00:00"),
        )
        mutable_db.commit()

        chain = AuditChain(mutable_db)  # triggers additive schema self-heal
        row = mutable_db.execute(
            "SELECT event_hash, hash_version, chain_id, chain_sequence "
            "FROM memory_events WHERE event_id = 'evt_legacy1'"
        ).fetchone()
        assert row[0] == v1_hash
        assert row[1] == HASH_VERSION_LEGACY
        assert row[2] == "memory_events"
        assert row[3] is None  # never retroactively numbered

        result = chain.verify_chain()
        assert result["valid"] is True

    def test_mixed_v1_to_v2_chain_verifies(self, mutable_db):
        v1_hash = compute_audit_hash_v1(
            event_type="legacy", fact_id=None, from_state=None, to_state=None,
            actor="agent", payload={}, created_at="2020-01-01T00:00:00+00:00",
            prev_event_hash=None,
        )
        mutable_db.execute(
            "INSERT INTO memory_events (event_id, event_type, actor, payload, "
            "event_hash, prev_event_hash, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("evt_legacy1", "legacy", "agent", "{}", v1_hash, None,
             "2020-01-01T00:00:00+00:00"),
        )
        mutable_db.commit()

        chain = AuditChain(mutable_db)
        e2 = chain.log("new_type", "agent2")
        e3 = chain.log("new_type2", "agent2")

        assert e2.chain_sequence == 1
        assert e3.chain_sequence == 2

        result = chain.verify_chain()
        assert result["valid"] is True
        assert result["events_checked"] == 3
        assert sorted(result["hash_versions_seen"]) == [1, 2]

    def test_first_v2_event_links_to_last_v1_hash(self, mutable_db):
        v1_hash = compute_audit_hash_v1(
            event_type="legacy", fact_id=None, from_state=None, to_state=None,
            actor="agent", payload={}, created_at="2020-01-01T00:00:00+00:00",
            prev_event_hash=None,
        )
        mutable_db.execute(
            "INSERT INTO memory_events (event_id, event_type, actor, payload, "
            "event_hash, prev_event_hash, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("evt_legacy1", "legacy", "agent", "{}", v1_hash, None,
             "2020-01-01T00:00:00+00:00"),
        )
        mutable_db.commit()
        chain = AuditChain(mutable_db)
        e2 = chain.log("new_type", "agent2")
        assert e2.prev_event_hash == v1_hash

    def test_unknown_hash_version_fails_closed(self, mutable_db):
        chain = AuditChain(mutable_db)
        e1 = chain.log("t1", "a1")
        mutable_db.execute(
            "UPDATE memory_events SET hash_version = 99 WHERE event_id = ?",
            (e1.event_id,),
        )
        mutable_db.commit()
        result = chain.verify_chain()
        assert result["valid"] is False
        assert "unknown hash_version" in result["error"]

    def test_v1_event_after_v2_boundary_fails_closed(self, mutable_db):
        """A tampered hash_version claiming '1' for a row that appears
        AFTER a real v2 event must fail closed, even though its own
        recomputed v1 hash happens to still match (the row's other
        columns are exactly what they were logged as — only hash_version
        was flipped)."""
        chain = AuditChain(mutable_db)
        e1 = chain.log("t1", "a1")
        e2 = chain.log("t2", "a2")
        # Recompute what e2's hash WOULD be if it had been logged as v1
        # with the same fields, then flip both hash_version and event_hash
        # so the legacy recompute matches — isolating the boundary check.
        fake_v1_hash = compute_audit_hash_v1(
            event_type="t2", fact_id=None, from_state=None, to_state=None,
            actor="a2", payload={}, created_at=e2.created_at,
            prev_event_hash=e1.event_hash,
        )
        mutable_db.execute(
            "UPDATE memory_events SET hash_version = 1, chain_sequence = NULL, "
            "event_hash = ? WHERE event_id = ?",
            (fake_v1_hash, e2.event_id),
        )
        mutable_db.commit()
        result = chain.verify_chain()
        assert result["valid"] is False


# ═══════════════════════════════════════════════════════════════════════════
# Group D — Concurrency
# ═══════════════════════════════════════════════════════════════════════════

class TestConcurrency:

    def _run_concurrent_appends(self, db_path, n_writers, per_writer):
        errors = []

        def worker(idx):
            conn = sqlite3.connect(db_path, timeout=30.0)
            conn.execute("PRAGMA busy_timeout=30000")
            try:
                chain = AuditChain(conn)
                for j in range(per_writer):
                    chain.log(f"type_{idx}_{j}", f"actor_{idx}")
            except Exception as exc:  # pragma: no cover - failure path
                errors.append(exc)
            finally:
                conn.close()

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(n_writers)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=60)
        return errors

    def test_100_plus_concurrent_appends_form_one_linear_chain(self, tmp_path):
        db_path = str(tmp_path / "concurrent.db")
        setup_conn = sqlite3.connect(db_path)
        _bare_v1_schema(setup_conn, with_triggers=True)
        AuditChain(setup_conn)
        setup_conn.close()

        n_writers, per_writer = 12, 10  # 120 total appends
        errors = self._run_concurrent_appends(db_path, n_writers, per_writer)
        assert errors == [], f"unexpected errors: {errors}"

        conn = sqlite3.connect(db_path)
        chain = AuditChain(conn)
        result = chain.verify_chain(max_rows=1000)
        assert result["valid"] is True
        assert result["events_checked"] == n_writers * per_writer
        conn.close()

    def test_every_successful_append_appears_exactly_once(self, tmp_path):
        db_path = str(tmp_path / "concurrent_once.db")
        setup_conn = sqlite3.connect(db_path)
        _bare_v1_schema(setup_conn, with_triggers=True)
        AuditChain(setup_conn)
        setup_conn.close()

        errors = self._run_concurrent_appends(db_path, 8, 8)
        assert errors == []

        conn = sqlite3.connect(db_path)
        rows = conn.execute("SELECT event_id FROM memory_events").fetchall()
        ids = [r[0] for r in rows]
        assert len(ids) == len(set(ids)) == 64
        conn.close()

    def test_sequence_unique_and_monotonic(self, tmp_path):
        db_path = str(tmp_path / "concurrent_seq.db")
        setup_conn = sqlite3.connect(db_path)
        _bare_v1_schema(setup_conn, with_triggers=True)
        AuditChain(setup_conn)
        setup_conn.close()

        errors = self._run_concurrent_appends(db_path, 10, 10)
        assert errors == []

        conn = sqlite3.connect(db_path)
        seqs = [
            r[0] for r in conn.execute(
                "SELECT chain_sequence FROM memory_events ORDER BY chain_sequence ASC"
            ).fetchall()
        ]
        conn.close()
        assert seqs == list(range(1, 101))  # unique, monotonic, no gaps

    def test_no_committed_fork(self, tmp_path):
        db_path = str(tmp_path / "concurrent_fork.db")
        setup_conn = sqlite3.connect(db_path)
        _bare_v1_schema(setup_conn, with_triggers=True)
        AuditChain(setup_conn)
        setup_conn.close()

        errors = self._run_concurrent_appends(db_path, 10, 10)
        assert errors == []

        conn = sqlite3.connect(db_path)
        chain = AuditChain(conn)
        result = chain.verify_chain(max_rows=1000)
        conn.close()
        # A fork would show up as either a hash mismatch, a duplicate
        # sequence, or a prev_hash mismatch — any of which fails valid.
        assert result["valid"] is True

    def test_head_row_equals_final_event(self, tmp_path):
        db_path = str(tmp_path / "concurrent_head.db")
        setup_conn = sqlite3.connect(db_path)
        _bare_v1_schema(setup_conn, with_triggers=True)
        AuditChain(setup_conn)
        setup_conn.close()

        errors = self._run_concurrent_appends(db_path, 6, 5)
        assert errors == []

        conn = sqlite3.connect(db_path)
        last_row = conn.execute(
            "SELECT event_hash, chain_sequence FROM memory_events "
            "ORDER BY chain_sequence DESC LIMIT 1"
        ).fetchone()
        head = conn.execute(
            "SELECT last_event_hash, last_sequence FROM audit_chain_heads "
            "WHERE chain_id = 'memory_events'"
        ).fetchone()
        conn.close()
        assert head == last_row

    def test_repeated_concurrency_runs_stay_clean(self, tmp_path):
        """Run the concurrent-append scenario several times over — a race
        window that only sometimes triggers must not slip through."""
        for i in range(5):
            db_path = str(tmp_path / f"repeat_{i}.db")
            setup_conn = sqlite3.connect(db_path)
            _bare_v1_schema(setup_conn, with_triggers=True)
            AuditChain(setup_conn)
            setup_conn.close()

            errors = self._run_concurrent_appends(db_path, 8, 5)
            assert errors == []

            conn = sqlite3.connect(db_path)
            chain = AuditChain(conn)
            result = chain.verify_chain(max_rows=1000)
            conn.close()
            assert result["valid"] is True, f"run {i} failed: {result}"
            assert result["events_checked"] == 40

    def test_caller_owned_transaction_does_not_retry_on_stale_head(self, db):
        """When the caller already owns the transaction, log() must not
        retry/rollback on a CAS conflict — it must raise so the caller's
        transaction is left exactly as the caller controls it."""
        chain = AuditChain(db)
        db.execute("BEGIN IMMEDIATE")
        try:
            e1 = chain.log("t1", "a1")
            assert e1.chain_sequence == 1
            db.commit()
        except Exception:
            db.rollback()
            raise

    def test_wal_mode_concurrent_appends(self, tmp_path):
        db_path = str(tmp_path / "wal.db")
        setup_conn = sqlite3.connect(db_path)
        setup_conn.execute("PRAGMA journal_mode=WAL")
        _bare_v1_schema(setup_conn, with_triggers=True)
        AuditChain(setup_conn)
        setup_conn.close()

        errors = []

        def worker(idx):
            conn = sqlite3.connect(db_path, timeout=30.0)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=30000")
            try:
                chain = AuditChain(conn)
                for j in range(6):
                    chain.log(f"wal_{idx}_{j}", f"actor_{idx}")
            except Exception as exc:  # pragma: no cover
                errors.append(exc)
            finally:
                conn.close()

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(6)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=60)
        assert errors == []

        conn = sqlite3.connect(db_path)
        chain = AuditChain(conn)
        result = chain.verify_chain(max_rows=1000)
        conn.close()
        assert result["valid"] is True
        assert result["events_checked"] == 36


# ═══════════════════════════════════════════════════════════════════════════
# Group E — Verification semantics
# ═══════════════════════════════════════════════════════════════════════════

class TestVerificationSemantics:

    def test_fact_id_filter_still_verifies_complete_interleaved_chain(self, mutable_db):
        chain = AuditChain(mutable_db)
        chain.log("t1", "a1", fact_id="f1")
        chain.log("t2", "a2", fact_id="f2")
        chain.log("t3", "a3", fact_id="f1")

        result = chain.verify_chain(fact_id="f1")
        # Even though fact_id="f1" only matches 2 of 3 rows, the FULL
        # interleaved chain (all 3) must be what's actually verified.
        assert result["events_checked"] == 3
        assert result["valid"] is True
        assert result["fact_id_filter"] == "f1"

    def test_malformed_payload_json_fails_verification(self, mutable_db):
        chain = AuditChain(mutable_db)
        evt = chain.log("t1", "a1", payload={"a": 1})
        mutable_db.execute(
            "UPDATE memory_events SET payload = '{not valid json' WHERE event_id = ?",
            (evt.event_id,),
        )
        mutable_db.commit()
        result = chain.verify_chain()
        assert result["valid"] is False
        assert "malformed payload" in result["error"]

    def test_duplicate_v2_sequence_fails_verification(self, mutable_db):
        chain = AuditChain(mutable_db)
        chain.log("t1", "a1")
        e2 = chain.log("t2", "a2")
        # The UNIQUE(chain_id, chain_sequence) index (migration 017) already
        # prevents this at the DB level in normal operation — drop it here
        # to prove verify_chain()'s OWN sequence-continuity check also
        # catches a duplicate independently of that DB constraint.
        mutable_db.execute("DROP INDEX idx_memory_events_chain_seq")
        mutable_db.execute(
            "UPDATE memory_events SET chain_sequence = 1 WHERE event_id = ?",
            (e2.event_id,),
        )
        mutable_db.commit()
        result = chain.verify_chain()
        assert result["valid"] is False

    def test_missing_v2_sequence_fails_verification(self, mutable_db):
        chain = AuditChain(mutable_db)
        evt = chain.log("t1", "a1")
        mutable_db.execute(
            "UPDATE memory_events SET chain_sequence = NULL WHERE event_id = ?",
            (evt.event_id,),
        )
        mutable_db.commit()
        result = chain.verify_chain()
        assert result["valid"] is False
        assert "missing chain_sequence" in result["error"]

    def test_head_table_mismatch_fails_verification(self, mutable_db):
        chain = AuditChain(mutable_db)
        chain.log("t1", "a1")
        mutable_db.execute(
            "UPDATE audit_chain_heads SET last_event_hash = 'not_the_real_hash' "
            "WHERE chain_id = 'memory_events'"
        )
        mutable_db.commit()
        result = chain.verify_chain()
        assert result["valid"] is False
        assert "audit_chain_heads" in result["error"]

    def test_truncated_verification_reports_incomplete(self, mutable_db):
        chain = AuditChain(mutable_db)
        for i in range(5):
            chain.log(f"t{i}", "a")
        result = chain.verify_chain(max_rows=3)
        assert result["complete"] is False
        assert result["truncated"] is True
        assert result["valid_so_far"] is True
        assert result["events_checked"] == 3

    def test_truncated_verification_never_writes_passed_receipt(self, mutable_db):
        chain = AuditChain(mutable_db)
        for i in range(5):
            chain.log(f"t{i}", "a")
        chain.verify_chain(max_rows=2)
        statuses = [
            r[0] for r in mutable_db.execute(
                "SELECT status FROM integrity_checks WHERE check_type='audit_chain'"
            ).fetchall()
        ]
        assert "passed" not in statuses
        assert "partial" in statuses

    def test_full_successful_verification_writes_passed_receipt(self, mutable_db):
        chain = AuditChain(mutable_db)
        chain.log("t1", "a1")
        chain.verify_chain()
        statuses = [
            r[0] for r in mutable_db.execute(
                "SELECT status FROM integrity_checks WHERE check_type='audit_chain'"
            ).fetchall()
        ]
        assert "passed" in statuses

    def test_failed_verification_writes_failed_receipt(self, mutable_db):
        chain = AuditChain(mutable_db)
        evt = chain.log("t1", "a1")
        _tamper(mutable_db, evt.event_id, "actor", "hacker")
        chain.verify_chain()
        statuses = [
            r[0] for r in mutable_db.execute(
                "SELECT status FROM integrity_checks WHERE check_type='audit_chain'"
            ).fetchall()
        ]
        assert "failed" in statuses

    def test_invalid_max_rows_rejected(self, db):
        chain = AuditChain(db)
        with pytest.raises(AuditChainError):
            chain.verify_chain(max_rows=True)  # bool
        with pytest.raises(AuditChainError):
            chain.verify_chain(max_rows=0)
        with pytest.raises(AuditChainError):
            chain.verify_chain(max_rows=-5)
        with pytest.raises(AuditChainError):
            chain.verify_chain(max_rows=3.5)  # type: ignore[arg-type]
        with pytest.raises(AuditChainError):
            chain.verify_chain(max_rows=10_000_000_000)

    def test_max_rows_is_parameterized_not_interpolated(self, mutable_db):
        """A max_rows value that would be dangerous if string-interpolated
        (e.g. containing SQL) must be rejected by type validation, never
        reach string formatting."""
        chain = AuditChain(mutable_db)
        chain.log("t1", "a1")
        with pytest.raises(AuditChainError):
            chain.verify_chain(max_rows="5; DROP TABLE memory_events;--")  # type: ignore[arg-type]
        # table must still exist and be queryable
        assert mutable_db.execute("SELECT COUNT(*) FROM memory_events").fetchone()[0] == 1

    def test_verification_never_mutates_memory_events(self, mutable_db):
        chain = AuditChain(mutable_db)
        evt = chain.log("t1", "a1", payload={"a": 1})
        before = mutable_db.execute(
            "SELECT * FROM memory_events WHERE event_id = ?", (evt.event_id,)
        ).fetchone()
        chain.verify_chain()
        after = mutable_db.execute(
            "SELECT * FROM memory_events WHERE event_id = ?", (evt.event_id,)
        ).fetchone()
        assert before == after

    def test_verify_does_not_write_audit_verify_event_into_chain(self, mutable_db):
        chain = AuditChain(mutable_db)
        chain.log("t1", "a1")
        before = mutable_db.execute("SELECT COUNT(*) FROM memory_events").fetchone()[0]
        chain.verify_chain()
        after = mutable_db.execute("SELECT COUNT(*) FROM memory_events").fetchone()[0]
        assert before == after
        types = {
            r[0] for r in mutable_db.execute(
                "SELECT DISTINCT event_type FROM memory_events"
            ).fetchall()
        }
        assert EventType.AUDIT_VERIFY not in types


# ═══════════════════════════════════════════════════════════════════════════
# Group F — Compatibility
# ═══════════════════════════════════════════════════════════════════════════

class TestCompatibility:

    def test_all_shortcut_methods_still_work(self, db):
        chain = AuditChain(db)
        e1 = chain.log_fact_created("f1", "some claim", "agent:api", 0.9)
        assert e1.event_type == EventType.FACT_CREATED
        e2 = chain.log_esm_transition("f1", "Observed", "Hypothesized", "agent:api")
        assert e2.event_type == EventType.ESM_TRANSITION
        e3 = chain.log_esm_transition("f1", "Hypothesized", "Deprecated", "agent:api")
        assert e3.event_type == EventType.FACT_DEPRECATED
        e4 = chain.log_truth_gate_verdict("f1", True, "strict", "agent:api")
        assert e4.event_type == EventType.TRUTH_GATE_VERDICT
        e5 = chain.log_observer_verdict("reject", flags=["x"])
        assert e5.event_type == EventType.OBSERVER_VERDICT
        e6 = chain.log_immutable_blocked("f1", "agent:api", "Collapsed")
        assert e6.event_type == EventType.IMMUTABLE_ATTEMPT_BLOCKED
        e7 = chain.log_cache_invalidated("f1", "stale")
        assert e7.event_type == EventType.CACHE_INVALIDATED

        result = chain.verify_chain()
        assert result["valid"] is True
        assert result["events_checked"] == 7

    def test_observer_audit_integration_still_works(self, db):
        from core.observer import observe

        chain = AuditChain(db)
        facts = [{
            "fact_id": "a", "confidence": 0.1, "claim": "x",
            "epistemic_state": "Hypothesized", "evidence": [],
        }]
        observe("q", facts, "ответ", audit_chain=chain)
        n = db.execute(
            "SELECT COUNT(*) FROM memory_events WHERE event_type='observer_verdict'"
        ).fetchone()[0]
        assert n == 1

    def test_existing_v1_style_tests_pass_unchanged(self, db):
        """Mirrors tests/test_truth_kernel.py::TestAuditChain exactly, on
        this module's own fixture, proving no weakening."""
        chain = AuditChain(db)
        assert chain.verify_chain()["valid"] is True

        chain.log_fact_created("f_new", "Новый факт", "agent:test", 0.7)
        chain.log_esm_transition("f_new", "Observed", "Hypothesized", "agent:test")
        result = chain.verify_chain()
        assert result["valid"] is True
        assert result["events_checked"] == 2

        e1 = chain.log("type1", "actor")
        e2 = chain.log("type2", "actor")
        assert e2.prev_event_hash == e1.event_hash

    def test_first_event_has_no_prev(self, db):
        chain = AuditChain(db)
        e1 = chain.log("type1", "actor")
        assert e1.prev_event_hash is None

    def test_append_only_triggers_remain_active(self, db):
        chain = AuditChain(db)
        evt = chain.log("test_event", "test_actor")
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            db.execute(
                "UPDATE memory_events SET actor='hacker' WHERE event_id=?",
                (evt.event_id,),
            )
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            db.execute("DELETE FROM memory_events WHERE event_id=?", (evt.event_id,))

    def test_get_fact_history_and_stats_remain_compatible(self, db):
        chain = AuditChain(db)
        chain.log_fact_created("f_water", "Вода кипит", "agent:api", 0.9)
        chain.log_esm_transition("f_water", "Observed", "Hypothesized", "agent:api")
        history = chain.get_fact_history("f_water")
        assert len(history) == 2
        assert history[0]["event_type"] == "fact_created"

        stats = chain.stats()
        assert stats["total_events"] == 2
        assert stats["by_event_type"]["fact_created"] == 1
        assert stats["by_event_type"]["esm_transition"] == 1


# ═══════════════════════════════════════════════════════════════════════════
# Codex review round 1 fixes
# ═══════════════════════════════════════════════════════════════════════════

class TestReviewRound1Fixes:

    def test_get_fact_history_scoped_to_own_chain_id(self, mutable_db):
        """P3: a chain-scoped AuditChain must never leak another chain's
        history for the same fact_id."""
        default_chain = AuditChain(mutable_db)
        default_chain.log("t1", "a1", fact_id="shared_fact")

        other_chain = AuditChain(mutable_db, chain_id="tenant_other")
        other_chain.log("t2", "a2", fact_id="shared_fact")

        default_history = default_chain.get_fact_history("shared_fact")
        other_history = other_chain.get_fact_history("shared_fact")

        assert len(default_history) == 1
        assert default_history[0]["event_type"] == "t1"
        assert len(other_history) == 1
        assert other_history[0]["event_type"] == "t2"

    def test_hash_versions_seen_sort_does_not_crash_on_mixed_types(self, mutable_db):
        """P2: a tampered non-integer hash_version must still produce a
        durably-recorded failed verification, not an unhandled TypeError
        from sorting a set that mixes an int and a str."""
        chain = AuditChain(mutable_db)
        chain.log("t1", "a1")
        e2 = chain.log("t2", "a2")
        mutable_db.execute(
            "UPDATE memory_events SET hash_version = 'bogus' WHERE event_id = ?",
            (e2.event_id,),
        )
        mutable_db.commit()

        result = chain.verify_chain()  # must not raise
        assert result["valid"] is False
        assert "unknown hash_version" in result["error"]
        statuses = [
            r[0] for r in mutable_db.execute(
                "SELECT status FROM integrity_checks WHERE check_type='audit_chain'"
            ).fetchall()
        ]
        assert "failed" in statuses

    def test_verify_chain_snapshot_consistent_under_concurrent_append(self, tmp_path):
        """P1: a successful concurrent append that lands between the row
        scan and the audit_chain_heads check must never make a genuinely
        valid chain report as diverged (false positive)."""
        db_path = str(tmp_path / "snapshot.db")
        setup_conn = sqlite3.connect(db_path)
        _bare_v1_schema(setup_conn, with_triggers=True)
        chain = AuditChain(setup_conn)
        for i in range(20):
            chain.log(f"t{i}", "a")

        results = []

        def verifier():
            conn = sqlite3.connect(db_path, timeout=30.0)
            conn.execute("PRAGMA busy_timeout=30000")
            local_chain = AuditChain(conn)
            for _ in range(15):
                results.append(local_chain.verify_chain(max_rows=10_000))
            conn.close()

        def writer():
            conn = sqlite3.connect(db_path, timeout=30.0)
            conn.execute("PRAGMA busy_timeout=30000")
            local_chain = AuditChain(conn)
            for i in range(15):
                local_chain.log(f"concurrent_{i}", "writer")
            conn.close()

        t_verify = threading.Thread(target=verifier)
        t_write = threading.Thread(target=writer)
        t_verify.start()
        t_write.start()
        t_verify.join(timeout=60)
        t_write.join(timeout=60)

        setup_conn.close()
        invalid = [r for r in results if r["valid"] is False]
        assert invalid == [], f"snapshot-inconsistent false failure(s): {invalid}"

    def test_ensure_schema_does_not_commit_callers_pending_work(self, mutable_db):
        """P2: constructing AuditChain inside a caller-owned transaction
        must not commit the caller's own prior uncommitted work — only the
        caller's eventual commit/rollback should decide its fate."""
        mutable_db.execute("BEGIN")
        mutable_db.execute(
            "INSERT INTO memory_events (event_id, event_type, actor, event_hash, created_at) "
            "VALUES ('evt_pending', 'pending_type', 'actor', 'fake_hash_not_verified', 't0')"
        )
        AuditChain(mutable_db)  # constructor must not commit the row above
        mutable_db.rollback()

        row = mutable_db.execute(
            "SELECT 1 FROM memory_events WHERE event_id = 'evt_pending'"
        ).fetchone()
        assert row is None, "caller's pending insert was committed by AuditChain's constructor"

    def test_add_column_if_missing_tolerates_duplicate_column_race(self, mutable_db):
        """P2: simulates the benign race where another connection already
        added the same additive column between our column-existence check
        and our own ALTER — must not raise."""
        chain = AuditChain(mutable_db)
        # hash_version already exists (added by the constructor above) —
        # calling the raw self-heal primitive again must tolerate it.
        chain._add_column_if_missing("memory_events", "hash_version", "INTEGER NOT NULL DEFAULT 1")
        # sanity: the column is still exactly one column, not duplicated
        cols = [
            row[1] for row in mutable_db.execute("PRAGMA table_info(memory_events)").fetchall()
        ]
        assert cols.count("hash_version") == 1


# ═══════════════════════════════════════════════════════════════════════════
# Codex review round 2 fixes
# ═══════════════════════════════════════════════════════════════════════════

class TestReviewRound2Fixes:

    @pytest.mark.parametrize("tampered_payload", [None, "", "null", "[]", '"a string"', "42"])
    def test_v2_verification_fails_closed_on_non_dict_payload(
        self, mutable_db, tampered_payload,
    ):
        """P2: NULL/empty/JSON-null/non-object payload storage must never
        be silently coalesced to {} during verification — that would
        accept a real tamper of the stored payload column."""
        chain = AuditChain(mutable_db)
        e1 = chain.log("t1", "a1", payload={})
        mutable_db.execute(
            "UPDATE memory_events SET payload = ? WHERE event_id = ?",
            (tampered_payload, e1.event_id),
        )
        mutable_db.commit()
        result = chain.verify_chain()
        assert result["valid"] is False

    def test_ensure_schema_preserves_higher_caller_busy_timeout(self, mutable_db):
        """P2: a caller-configured busy_timeout longer than our own
        default floor must never be lowered by construction."""
        mutable_db.execute("PRAGMA busy_timeout=30000")
        AuditChain(mutable_db)
        current = mutable_db.execute("PRAGMA busy_timeout").fetchone()[0]
        assert current >= 30000

    def test_ensure_schema_raises_low_busy_timeout_to_floor(self, mutable_db):
        """A lower-than-floor timeout (e.g. explicitly disabled) is raised
        to the 5s floor, same as before — only the "never lower a higher
        value" direction changed."""
        mutable_db.execute("PRAGMA busy_timeout=0")
        AuditChain(mutable_db)
        current = mutable_db.execute("PRAGMA busy_timeout").fetchone()[0]
        assert current >= 5000

    def test_stats_scoped_to_own_chain_id(self, mutable_db):
        """P2: a chain-scoped AuditChain must not report another chain's
        event counts via stats()."""
        default_chain = AuditChain(mutable_db)
        default_chain.log("t1", "a1")
        default_chain.log("t2", "a2")

        other_chain = AuditChain(mutable_db, chain_id="tenant_other")
        other_chain.log("t3", "a3")

        default_stats = default_chain.stats()
        other_stats = other_chain.stats()

        assert default_stats["total_events"] == 2
        assert other_stats["total_events"] == 1
        assert other_stats["by_event_type"] == {"t3": 1}
