"""
tests/test_fact_version_consistency.py — PR-C1b (Issue #37) regression tests
==============================================================================

Issue #37: existing-fact UPDATEs that change claim/confidence/epistemic_state
through store_fact()/store_fact_result()/store_facts_batch()/core.forgetting's
PII redaction never bumped `facts.fact_version` — so migration 009's
`bump_fact_version` trigger aborted them on any DB that actually has that
migration applied. Separately, the VersionStore pre-image snapshot for these
writes was taken *before* the write's outcome was known, so a rejected write
still left a "superseded" `fact_versions` row with no successor for a fact
that never actually changed (a phantom audit entry).

Fix (this PR): _store_fact_outcome()'s upsert (and its drift-sync, folded
into the same statement) and store_facts_batch()'s upsert now bump
`fact_version` via the existing `_fact_version_bump_sql()` helper exactly
when claim/confidence/epistemic_state genuinely change — not on metadata-only
updates, which the trigger's WHEN clause never touches anyway. The
VersionStore snapshot is now taken only after the write actually commits
(mirroring _promote_to_validated_cas()/supersede_fact_cas(), which already
did this — see tests/test_truthgate_api_transition.py's "Follow-up fix #2,
item 4" for the identical precedent this PR follows for _store_fact_outcome()).
core.forgetting's PII redaction gets the same bump via a small shared helper
(core.memory.facts_table_has_fact_version()) rather than a duplicated PRAGMA
check.

NOTE ON FIXTURES: a plain SQLiteGraphStore(tmp_path / "x.db") only runs the
runtime bootstrap DDL (core/memory.py's CREATE TABLE IF NOT EXISTS facts) —
that DDL does NOT include fact_version or any of migration 009's triggers.
Every test here uses `migrated_store`, which explicitly runs
scripts/apply_migrations.py against the temp DB first (same subprocess
pattern as tests/test_migrations.py) so the real bump_fact_version /
prevent_*_mutation triggers are genuinely present; without this, these tests
would pass trivially regardless of whether the fix is in place.

DELIBERATELY NOT TESTED HERE (see Issue #37 / final PR-C1b report for why):
  - VersionStore.get_fact_as_of() across MULTIPLE historical versions of the
    same fact_id. A separate, pre-existing VersionStore defect (recorded_at
    is derived from the fact's bi-temporal t_ingestion_start, which is
    frozen at creation and never advances — so every snapshot for a given
    fact_id shares the same recorded_at) makes multi-version time-travel
    queries resolve to the wrong version. This is unrelated to
    bump_fact_version/snapshot-ordering and out of this PR's mandated scope
    (no VersionStore redesign) — flagged as a deferred finding.
  - ImmutableCore/Collapsed mutation-guard triggers as a failure-injection
    mechanism for the snapshot-ordering tests below. update_state() has its
    own, separate, unrelated ordering bug when transitioning INTO
    'Collapsed' (a same-transaction metadata-sync UPDATE runs after
    epistemic_state is already 'Collapsed', tripping
    prevent_collapsed_mutation on itself) — discovered while probing this
    area, also out of scope. The tests below inject a deterministic,
    understood failure instead (disabling the bump helper), isolating the
    ordering fix under test from either of those unrelated defects.
"""
from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
import time
from datetime import UTC, datetime

import pytest

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "scripts")
APPLY_MIGRATIONS = os.path.join(SCRIPTS_DIR, "apply_migrations.py")


def _run_apply(db_path: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, APPLY_MIGRATIONS, "--db", db_path, "--no-backup"],
        capture_output=True, text=True,
    )


@pytest.fixture
def migrated_store(tmp_path, monkeypatch):
    """Like test_write_result.py's `isolated_store`, but with migrations
    008-017 actually applied — real fact_version column + bump_fact_version
    and the other truth-kernel triggers genuinely present."""
    from core import memory

    db_path = str(tmp_path / "fv.db")
    memory.SQLiteGraphStore(db_path).get_fact("__bootstrap__")
    result = _run_apply(db_path)
    assert result.returncode == 0, (
        f"apply_migrations failed:\nstdout={result.stdout}\nstderr={result.stderr}"
    )

    fresh = memory.make_store(db_path)
    monkeypatch.setattr(memory, "_GLOBAL_STORE", fresh)
    monkeypatch.setattr(memory, "_L0", fresh._l0)
    monkeypatch.setattr(memory, "_DDL_INITIALIZED", fresh._ddl_initialized_paths)
    monkeypatch.setattr(memory, "SQLITE_PATH", db_path)
    yield fresh
    fresh.close()


def _raw_row(store, fact_id: str):
    with store._db() as conn:
        return conn.execute(
            "SELECT claim, confidence, epistemic_state, metadata, fact_version "
            "FROM facts WHERE fact_id = ?",
            (fact_id,),
        ).fetchone()


def _version_count(store, fact_id: str) -> int:
    with store._db() as conn:
        return conn.execute(
            "SELECT COUNT(*) FROM fact_versions WHERE fact_id = ?", (fact_id,)
        ).fetchone()[0]


class _FlakyUpdateConn:
    """Transparent sqlite3.Connection proxy that raises on any `UPDATE
    facts SET ...` statement and forwards everything else untouched.
    sqlite3.Connection is an immutable C type — its methods can't be
    monkeypatched directly — so this wraps what sqlite3.connect() returns
    instead, used to test that core.forgetting's redact_pii_* always closes
    (and never leaks the WAL lock on) its connection, even when the UPDATE
    itself fails."""

    def __init__(self, real_conn):
        object.__setattr__(self, "_real", real_conn)

    def execute(self, sql, *args, **kwargs):
        if isinstance(sql, str) and sql.strip().upper().startswith("UPDATE FACTS SET"):
            raise sqlite3.OperationalError("injected failure for leak test")
        return self._real.execute(sql, *args, **kwargs)

    def __getattr__(self, name):
        return getattr(self._real, name)

    def __setattr__(self, name, value):
        setattr(self._real, name, value)


def _patch_flaky_update(monkeypatch):
    """Make every subsequent sqlite3.connect() in this test return a
    _FlakyUpdateConn wrapping a real connection."""
    real_connect = sqlite3.connect

    def _flaky_connect(*args, **kwargs):
        return _FlakyUpdateConn(real_connect(*args, **kwargs))

    monkeypatch.setattr(sqlite3, "connect", _flaky_connect)


# ─── Scenarios 1-4: single-fact content updates via store_fact_result() ──────

class TestExistingFactContentUpdates:
    def test_claim_update_succeeds_and_bumps_fact_version_by_one(self, migrated_store):
        store = migrated_store
        store.store_fact_result(
            {"fact_id": "f1", "claim": "original", "source": "s", "confidence": 0.5}
        )
        v0 = _raw_row(store, "f1")[4]
        assert v0 == 1

        result = store.store_fact_result(
            {"fact_id": "f1", "claim": "changed", "source": "s", "confidence": 0.5}
        )
        assert result.status.name == "UPDATED"

        row = _raw_row(store, "f1")
        assert row[0] == "changed"
        assert row[4] == v0 + 1, f"fact_version should bump by exactly 1, got {v0} -> {row[4]}"

    def test_confidence_update_succeeds_and_bumps_fact_version_by_one(self, migrated_store):
        store = migrated_store
        store.store_fact_result(
            {"fact_id": "f2", "claim": "c", "source": "s", "confidence": 0.5}
        )
        result = store.store_fact_result(
            {"fact_id": "f2", "claim": "c", "source": "s", "confidence": 0.9}
        )
        assert result.status.name == "UPDATED"

        row = _raw_row(store, "f2")
        assert row[1] == 0.9
        assert row[4] == 2

    def test_metadata_only_update_succeeds_without_bumping_fact_version(self, migrated_store):
        """Metadata-only changes never touch claim/confidence/epistemic_state
        — bump_fact_version's WHEN clause never fires for them, so the fix
        must not force an unneeded bump either."""
        store = migrated_store
        store.store_fact_result({
            "fact_id": "f3", "claim": "c", "source": "s", "confidence": 0.5,
            "metadata": {"tag": "v1"},
        })
        result = store.store_fact_result({
            "fact_id": "f3", "claim": "c", "source": "s", "confidence": 0.5,
            "metadata": {"tag": "v2"},
        })
        assert result.status.name == "UPDATED"

        row = _raw_row(store, "f3")
        assert json.loads(row[3])["tag"] == "v2", (
            "PR-C1b review fix: parse and compare the decoded value instead "
            "of a raw-JSON-text substring check, which is brittle to "
            "serialization spacing/key order"
        )
        assert row[4] == 1, "metadata-only update must not bump fact_version"

    def test_noop_existing_fact_performs_no_write_and_no_bump(self, migrated_store):
        store = migrated_store
        store.store_fact_result(
            {"fact_id": "f4", "claim": "c", "source": "s", "confidence": 0.5}
        )
        result = store.store_fact_result(
            {"fact_id": "f4", "claim": "c", "source": "s", "confidence": 0.5}
        )
        assert result.status.name == "NOOP_EXISTING"
        assert result.durable_write is False

        row = _raw_row(store, "f4")
        assert row[4] == 1
        assert _version_count(store, "f4") == 0, (
            "a true no-op must not create a VersionStore snapshot either "
            "— nothing changed, there is nothing to supersede"
        )

    def test_subepsilon_confidence_change_with_metadata_change_still_bumps(self, migrated_store):
        """PR-C1b review fix: the bump decision must compare confidence
        EXACTLY, matching the trigger's `OLD.confidence != NEW.confidence`
        (migration 009) exactly — not with an epsilon.

        NOTE: through the normal write path, confidence is always rounded
        to 4 decimals by _validate_confidence() before this comparison ever
        runs, so two *distinct* confidences reaching it always differ by at
        least 1e-4 — far above the old 1e-9 epsilon, which is why that
        epsilon never actually misfired for a value store_fact_result()
        itself produced. The reachable case is a pre-existing row with
        higher-precision confidence than the app ever writes today (legacy
        data, a direct import, a future caller bypassing rounding) —
        simulated here via a raw SQL seed — compared against a freshly
        rounded new value that lands suspiciously close to it."""
        store = migrated_store
        store.store_fact_result({
            "fact_id": "eps1", "claim": "c", "source": "s", "confidence": 0.5,
            "metadata": {"tag": "v1"},
        })
        legacy_confidence = 0.5 + 1.23e-10
        with store._db() as conn:
            conn.execute(
                "UPDATE facts SET confidence = ?, fact_version = fact_version + 1 "
                "WHERE fact_id = ?",
                (legacy_confidence, "eps1"),
            )
        store._l0_del("eps1")  # the raw seed above bypassed the L1->L0 publish

        new_confidence = 0.5
        assert new_confidence != legacy_confidence, "sanity: genuinely distinct floats"
        assert abs(new_confidence - legacy_confidence) < 1e-9, "sanity: delta must be sub-epsilon"

        result = store.store_fact_result({
            "fact_id": "eps1", "claim": "c", "source": "s", "confidence": new_confidence,
            "metadata": {"tag": "v2"},
        })
        assert result.status.name == "UPDATED"

        row = _raw_row(store, "eps1")
        assert row[1] == new_confidence
        assert row[4] == 3, (
            f"a genuine (if tiny) confidence change must bump fact_version "
            f"by exactly 1 over the seeded state (1 create + 1 seed bump + "
            f"1 real update), got {row[4]}"
        )


# ─── Scenario 5: drift protection (TASK-02) ───────────────────────────────────

class TestDriftProtectionUpdate:
    def test_drift_protection_transitions_to_contradicted_with_single_bump(self, migrated_store):
        """A claim change on a Validated/Supported fact triggers TASK-02
        drift protection (auto-transition to Contradicted). This changes
        BOTH claim and epistemic_state in one logical write — before this
        fix these were two separate UPDATE statements (main upsert +
        drift-sync), each independently subject to bump_fact_version's WHEN
        clause: bumping both would double-count, bumping neither would
        crash. Must land as exactly +1."""
        store = migrated_store
        store.store_fact_result(
            {"fact_id": "f5", "claim": "original", "source": "s", "confidence": 0.9}
        )
        store.transition_esm("f5", "Hypothesized", by="test")
        store.transition_esm("f5", "Supported", by="test")
        v0 = _raw_row(store, "f5")[4]

        result = store.store_fact_result({
            "fact_id": "f5", "claim": "a completely different claim",
            "source": "s", "confidence": 0.9,
        })
        assert result.status.name == "UPDATED"

        row = _raw_row(store, "f5")
        assert row[0] == "a completely different claim"
        assert row[2] == "Contradicted"
        assert row[4] == v0 + 1, (
            f"drift-protection update must bump fact_version by exactly 1 "
            f"(not 0, not 2), got {v0} -> {row[4]}"
        )


# ─── Scenarios 6, 7, 12: VersionStore snapshot consistency ───────────────────

class TestVersionStoreSnapshotConsistency:
    """A failed canonical update must not leave a dangling VersionStore
    snapshot, and a successful one must leave exactly the expected one —
    Issue #37 p.1 (phantom "superseded" snapshot with no successor,
    breaking VersionStore.get_fact_as_of())."""

    def test_failed_update_creates_no_fact_versions_row(self, migrated_store, monkeypatch):
        """Deterministic failure injection: force _fact_version_bump_sql()
        to no-op (reproducing the pre-fix condition), isolating the
        ordering fix under test from any other trigger's own behavior."""
        store = migrated_store
        store.store_fact_result(
            {"fact_id": "f6", "claim": "original", "source": "s", "confidence": 0.5}
        )

        monkeypatch.setattr(store, "_fact_version_bump_sql", lambda conn: "")

        result = store.store_fact_result({
            "fact_id": "f6", "claim": "should not persist",
            "source": "s", "confidence": 0.5,
        })
        assert result.status.name == "FAILED_STORAGE"

        assert _version_count(store, "f6") == 0, (
            "a failed canonical update must not create a fact_versions snapshot"
        )
        assert store.get_fact("f6")["claim"] == "original"

    def test_successful_update_creates_exactly_one_fact_versions_row(self, migrated_store):
        store = migrated_store
        store.store_fact_result(
            {"fact_id": "f7", "claim": "original", "source": "s", "confidence": 0.5}
        )
        assert _version_count(store, "f7") == 0

        result = store.store_fact_result(
            {"fact_id": "f7", "claim": "updated", "source": "s", "confidence": 0.5}
        )
        assert result.status.name == "UPDATED"

        from core.version_store import VersionStore

        history = VersionStore(store.db_path).get_fact_history("f7")
        assert len(history) == 1, f"expected exactly one historical snapshot, got {len(history)}"
        assert history[0].claim == "original", "snapshot must capture the PRE-image, not the new claim"
        assert history[0].superseded_at is not None

    def test_get_fact_as_of_unaffected_by_a_failed_update(self, migrated_store, monkeypatch):
        """Issue #37 p.1's core claim: a failed update must not make
        time-travel queries diverge from a fact that never actually
        changed, nor corrupt the history a LATER successful update adds."""
        from core.version_store import VersionStore

        store = migrated_store
        store.store_fact_result(
            {"fact_id": "f8", "claim": "original", "source": "s", "confidence": 0.5}
        )
        t_before = datetime.now(UTC).isoformat()
        time.sleep(0.01)

        monkeypatch.setattr(store, "_fact_version_bump_sql", lambda conn: "")
        store.store_fact_result({
            "fact_id": "f8", "claim": "should not persist",
            "source": "s", "confidence": 0.5,
        })
        monkeypatch.undo()

        vs = VersionStore(store.db_path)
        assert vs.count_versions("f8") == 0
        assert vs.get_fact_as_of("f8", t_before) is None, (
            "no snapshot exists yet (nothing has ever been superseded) — "
            "this is the correct, unaffected answer, not a regression: the "
            "failed attempt did not add a bogus entry."
        )

        time.sleep(0.01)
        result = store.store_fact_result({
            "fact_id": "f8", "claim": "updated for real",
            "source": "s", "confidence": 0.5,
        })
        assert result.status.name == "UPDATED"

        assert vs.count_versions("f8") == 1, (
            "the failed attempt must not have left a row for the later "
            "successful update to pile on top of"
        )
        as_of = vs.get_fact_as_of("f8", t_before)
        assert as_of is not None
        assert as_of.claim == "original", (
            "get_fact_as_of() for a time before the (only) successful "
            "update must resolve to the pre-update claim, unaffected by "
            "the earlier failed attempt"
        )


# ─── Scenario 8: store_facts_batch() ──────────────────────────────────────────

class TestBatchUpdateVersioning:
    def test_batch_update_bumps_only_changed_records_and_stays_atomic(self, migrated_store):
        store = migrated_store
        for fid in ("a", "b", "c"):
            store.store_fact_result(
                {"fact_id": fid, "claim": f"original {fid}", "source": "s", "confidence": 0.5}
            )

        stats = store.store_facts_batch([
            {"fact_id": "a", "claim": "original a", "source": "s", "confidence": 0.5},  # unchanged
            {"fact_id": "b", "claim": "CHANGED b", "source": "s", "confidence": 0.5},   # changed
            {"fact_id": "c", "claim": "original c", "source": "s", "confidence": 0.5},  # unchanged
        ])
        assert stats["errors"] == 0
        assert stats["updated"] == 3

        assert _raw_row(store, "a")[:1] + (_raw_row(store, "a")[4],) == ("original a", 1)
        assert _raw_row(store, "b")[:1] + (_raw_row(store, "b")[4],) == ("CHANGED b", 2)
        assert _raw_row(store, "c")[:1] + (_raw_row(store, "c")[4],) == ("original c", 1)

    def test_batch_subepsilon_confidence_change_bumps_and_does_not_rollback(self, migrated_store):
        """Same review fix as the single-fact path (see
        TestExistingFactContentUpdates.test_subepsilon_confidence_change_with_metadata_change_still_bumps)
        and same reachability caveat: through the normal write path,
        confidence is always rounded to 4 decimals before this comparison
        runs, so the reachable case is a pre-existing row with
        higher-precision confidence than the app writes today — simulated
        here via a raw SQL seed, same as the single-fact test."""
        store = migrated_store
        store.store_fact_result(
            {"fact_id": "beps1", "claim": "original", "source": "s", "confidence": 0.5}
        )
        legacy_confidence = 0.5 + 1.23e-10
        with store._db() as conn:
            conn.execute(
                "UPDATE facts SET confidence = ?, fact_version = fact_version + 1 "
                "WHERE fact_id = ?",
                (legacy_confidence, "beps1"),
            )
        store._l0_del("beps1")

        new_confidence = 0.5
        assert new_confidence != legacy_confidence
        assert abs(new_confidence - legacy_confidence) < 1e-9

        stats = store.store_facts_batch([
            {"fact_id": "beps1", "claim": "original", "source": "s", "confidence": new_confidence},
        ])
        assert stats["errors"] == 0
        assert stats["updated"] == 1

        row = _raw_row(store, "beps1")
        assert row[1] == new_confidence
        assert row[4] == 3, (
            f"a genuine (if tiny) confidence change must bump fact_version "
            f"by exactly 1 over the seeded state, got {row[4]}"
        )

    def test_batch_one_conflicting_record_still_rolls_back_whole_transaction(
        self, migrated_store, monkeypatch,
    ):
        """store_facts_batch() must keep its existing all-or-nothing
        transaction semantics — a real conflict (forced here by disabling
        the bump) must roll back the ENTIRE batch, not just skip the
        offending record."""
        store = migrated_store
        for fid in ("x", "y"):
            store.store_fact_result(
                {"fact_id": fid, "claim": f"original {fid}", "source": "s", "confidence": 0.5}
            )

        monkeypatch.setattr(store, "_fact_version_bump_sql", lambda conn: "")

        # PR-C1b review fix: assert the precise exception type. The failure
        # injection specifically targets bump_fact_version's trigger abort
        # (sqlite3.IntegrityError) — a bare Exception would also pass for
        # an unrelated bug elsewhere in the batch path.
        with pytest.raises(sqlite3.IntegrityError):
            store.store_facts_batch([
                {"fact_id": "x", "claim": "CHANGED x", "source": "s", "confidence": 0.5},
                {"fact_id": "y", "claim": "CHANGED y", "source": "s", "confidence": 0.5},
            ])

        assert store.get_fact("x")["claim"] == "original x"
        assert store.get_fact("y")["claim"] == "original y"


# ─── Scenario 9: CognitiveFactStore.save_many() ───────────────────────────────

class TestCognitiveStoreSaveManyBatchUpdate:
    def test_save_many_batch_update_bumps_fact_version(self, migrated_store):
        store = migrated_store
        store.store_fact_result(
            {"fact_id": "cog1", "claim": "original", "source": "s", "confidence": 0.5}
        )

        from core.cognitive_fact import CognitiveFact
        from core.cognitive_store import CognitiveFactStore

        cf = CognitiveFact(
            id="cog1", canonical_text="changed via cognitive store",
            source="s", epistemic_state="Observed", confidence=0.5,
        )
        stats = CognitiveFactStore().save_many([cf])
        assert stats["updated"] == 1
        assert stats["errors"] == 0

        row = _raw_row(store, "cog1")
        assert row[0] == "changed via cognitive store"
        assert row[4] == 2


# ─── Scenarios 10, 11: core.forgetting PII redaction ──────────────────────────

class TestForgettingRedactPiiVersionSafe:
    def test_redact_pii_fact_bumps_fact_version_and_actually_redacts(self, migrated_store):
        store = migrated_store
        store.store_fact_result({
            "fact_id": "pii1", "claim": "contact me at alice@example.com",
            "source": "s", "confidence": 0.5,
        })

        from core.forgetting import ForgettingEngine

        engine = ForgettingEngine(db_path=store.db_path)
        verdict = engine.redact_pii_fact("pii1")

        assert verdict.allowed is True
        assert verdict.reason == "redacted"
        assert verdict.redacted_count == 1

        row = _raw_row(store, "pii1")
        assert row[0] == "contact me at [EMAIL]", (
            f"redaction must actually persist, not silently no-op: {row[0]!r}"
        )
        assert row[4] == 2, "claim change through redaction must bump fact_version by exactly 1"

    def test_redact_pii_batch_bumps_fact_version_for_every_redacted_row(self, migrated_store):
        store = migrated_store
        store.store_fact_result({
            "fact_id": "pii2", "claim": "email bob@example.com",
            "source": "s", "confidence": 0.5,
        })
        store.store_fact_result({
            "fact_id": "pii3", "claim": "no pii in this claim at all",
            "source": "s", "confidence": 0.5,
        })

        from core.forgetting import ForgettingEngine

        engine = ForgettingEngine(db_path=store.db_path)
        verdict = engine.redact_pii_batch(limit=100)

        assert verdict.allowed is True
        assert verdict.redacted_count == 1, "only pii2 actually contains PII"

        row2 = _raw_row(store, "pii2")
        assert row2[0] == "email [EMAIL]"
        assert row2[4] == 2

        row3 = _raw_row(store, "pii3")
        assert row3[0] == "no pii in this claim at all"
        assert row3[4] == 1, "a claim with no PII must not be touched or bumped"


# ─── PR-C1b review fix: redact_pii_* must never leak its connection ──────────

class TestForgettingConnectionNotLeakedOnFailure:
    """redact_pii_fact()/redact_pii_batch() must close their SQLite
    connection (releasing its WAL lock) even when the UPDATE itself fails —
    the pre-fix code only closed on the success path, so any exception
    between connect() and that single conn.close() call leaked the
    connection (and its lock) indefinitely. External contract (a
    ForgetVerdict, never a raise) must stay unchanged."""

    def test_redact_pii_fact_closes_connection_on_update_failure(self, migrated_store, monkeypatch):
        store = migrated_store
        store.store_fact_result({
            "fact_id": "leak1", "claim": "email leak1@example.com",
            "source": "s", "confidence": 0.5,
        })

        _patch_flaky_update(monkeypatch)

        from core.forgetting import ForgettingEngine

        engine = ForgettingEngine(db_path=store.db_path)
        verdict = engine.redact_pii_fact("leak1")

        assert verdict.allowed is False, (
            "contract unchanged: a storage failure surfaces as an "
            "unallowed verdict, not a raise"
        )
        assert "store_error" in verdict.reason

        monkeypatch.undo()

        # A brand-new connection must be able to write immediately — if the
        # failed attempt's connection had leaked, this would raise
        # "database is locked" against the still-open WAL lock.
        probe = sqlite3.connect(store.db_path, timeout=2.0)
        try:
            probe.execute(
                "UPDATE facts SET updated_at = ? WHERE fact_id = ?",
                (datetime.now(UTC).isoformat(), "leak1"),
            )
            probe.commit()
        finally:
            probe.close()

        assert store.get_fact("leak1")["claim"] == "email leak1@example.com", (
            "the failed redaction must not have partially applied"
        )

    def test_redact_pii_batch_closes_connection_on_update_failure(self, migrated_store, monkeypatch):
        store = migrated_store
        store.store_fact_result({
            "fact_id": "leak2", "claim": "email leak2@example.com",
            "source": "s", "confidence": 0.5,
        })

        _patch_flaky_update(monkeypatch)

        from core.forgetting import ForgettingEngine

        engine = ForgettingEngine(db_path=store.db_path)
        verdict = engine.redact_pii_batch(limit=100)

        assert verdict.allowed is False
        assert "store_error" in verdict.reason

        monkeypatch.undo()

        probe = sqlite3.connect(store.db_path, timeout=2.0)
        try:
            probe.execute(
                "UPDATE facts SET updated_at = ? WHERE fact_id = ?",
                (datetime.now(UTC).isoformat(), "leak2"),
            )
            probe.commit()
        finally:
            probe.close()

        assert store.get_fact("leak2")["claim"] == "email leak2@example.com"
