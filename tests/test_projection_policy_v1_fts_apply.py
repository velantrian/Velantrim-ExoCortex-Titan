"""Issue #194: projection policy v1 and version-monotonic FTS apply contract.

Resolves two of issue #193's Phase 0 blockers before any dispatcher lease/
retry/ack state machine exists:

  1. `ProjectionKind.ALL` had no executable interpretation anywhere.
  2. No projection target stored a version to compare against, so nothing
     prevented an older/redelivered intent from regressing a newer
     projection.

This file proves ONLY the policy-v1 resolver and the strict, version-
monotonic FTS apply primitive (`core.projection_apply`). No dispatcher
claim/lease/retry/ack exists yet — `apply_fts_projection()` is a plain,
caller-transaction-owned function; every test manages its own connection
and transaction boundary explicitly.

Every test constructs a real, temp-file-backed SQLite database migrated
through the REAL migration chain (scripts/apply_migrations.py) — no
fakes/stubs/mocks for SQLite itself. Failures are simulated with genuine
SQLite-level breakage (a real trigger for the checkpoint table; a
corrupted FTS5 shadow table for the FTS side, since SQLite does not allow
triggers on virtual tables at all), never monkeypatched exceptions.
"""
from __future__ import annotations

import os
import subprocess
import sys
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from core.memory import SQLiteGraphStore
from core.projection_apply import (
    CanonVersionBehindIntentError,
    ProjectionApplyOutcome,
    UnsupportedPolicyTargetError,
    apply_fts_projection,
    resolve_projection_targets,
)
from core.projection_outbox import LOCAL_PROJECTION_SCOPE_REF, ProjectionKind

_ROOT = os.path.join(os.path.dirname(__file__), "..")
_APPLY_MIGRATIONS = os.path.join(_ROOT, "scripts", "apply_migrations.py")


def _migrate(db_path: Path) -> None:
    subprocess.run(
        [sys.executable, _APPLY_MIGRATIONS, "--db", str(db_path), "--no-backup"],
        check=True, capture_output=True,
    )


def _seed_fact(store: SQLiteGraphStore, fact_id: str, *, claim: str, source: str = "test") -> None:
    assert store.store_fact(
        {"fact_id": fact_id, "claim": claim, "source": source, "confidence": 0.9}
    ) is True


def _set_fact_version(db_path: Path, fact_id: str, version: int) -> None:
    """Direct fixture manipulation: the code under test only ever READS
    facts.fact_version — how a real deployment reached a given version is
    irrelevant to what apply_fts_projection() does with it, so tests pin
    exact version numbers directly rather than replaying long promotion
    chains."""
    with sqlite3.connect(str(db_path)) as conn:
        conn.execute("UPDATE facts SET fact_version = ? WHERE fact_id = ?", (version, fact_id))
        conn.commit()


def _checkpoint_row(db_path: Path, fact_id: str):
    with sqlite3.connect(str(db_path)) as conn:
        return conn.execute(
            "SELECT applied_canonical_version, updated_at FROM projection_checkpoints "
            "WHERE aggregate_type = 'fact' AND aggregate_id = ? "
            "AND scope_ref = ? AND projection_kind = 'fts'",
            (fact_id, LOCAL_PROJECTION_SCOPE_REF),
        ).fetchone()


def _fts_row(db_path: Path, fact_id: str):
    with sqlite3.connect(str(db_path)) as conn:
        return conn.execute(
            "SELECT claim, source FROM facts_fts WHERE fact_id = ?", (fact_id,),
        ).fetchone()


def _integrity_ok(db_path: Path) -> bool:
    with sqlite3.connect(str(db_path)) as conn:
        return conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def _apply(db_path: Path, fact_id: str, intent_canonical_version: int):
    """Open a fresh connection, run one caller-owned transaction around
    apply_fts_projection(), commit, close. apply_fts_projection() itself
    never commits/rolls back — this mirrors how a future caller (or this
    file's own rollback tests) is expected to manage the boundary."""
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute("BEGIN IMMEDIATE")
        result = apply_fts_projection(
            conn, fact_id=fact_id, intent_canonical_version=intent_canonical_version,
        )
        conn.commit()
        return result
    finally:
        conn.close()


# ── 1-3. Policy v1 resolver ─────────────────────────────────────────────────

def test_policy_v1_all_expands_exactly_to_fts() -> None:
    assert resolve_projection_targets("v1", ProjectionKind.ALL) == (ProjectionKind.FTS,)


def test_policy_v1_fts_expands_to_fts() -> None:
    assert resolve_projection_targets("v1", ProjectionKind.FTS) == (ProjectionKind.FTS,)


def test_policy_v1_expansion_independent_of_environment_flags(monkeypatch) -> None:
    """No dynamic environment/config-derived expansion is allowed in v1 —
    the target set must be deterministic from policy_version alone."""
    for flag in (
        "VELANTRIM_ENABLE_GRAPH_PROJECTION", "VELANTRIM_ENABLE_VECTOR_PROJECTION",
        "STORAGE_BACKEND", "ENABLE_ETIR", "ENABLE_IMMUTABLE_CORE",
    ):
        monkeypatch.setenv(flag, "true")
    assert resolve_projection_targets("v1", ProjectionKind.ALL) == (ProjectionKind.FTS,)
    for flag in (
        "VELANTRIM_ENABLE_GRAPH_PROJECTION", "VELANTRIM_ENABLE_VECTOR_PROJECTION",
    ):
        monkeypatch.setenv(flag, "false")
    assert resolve_projection_targets("v1", ProjectionKind.ALL) == (ProjectionKind.FTS,)


@pytest.mark.parametrize("unsupported_kind", [ProjectionKind.GRAPH, ProjectionKind.VECTOR])
def test_policy_v1_graph_and_vector_are_unsupported_never_silent(
    unsupported_kind: ProjectionKind,
) -> None:
    with pytest.raises(UnsupportedPolicyTargetError):
        resolve_projection_targets("v1", unsupported_kind)


def test_unknown_policy_version_is_unsupported() -> None:
    with pytest.raises(UnsupportedPolicyTargetError):
        resolve_projection_targets("v2-does-not-exist", ProjectionKind.ALL)


# ── 4-5. First refresh + idempotent repeat ──────────────────────────────────

def test_first_refresh_writes_current_canon_content_and_checkpoint(tmp_path: Path) -> None:
    db_path = tmp_path / "first-refresh.db"
    _migrate(db_path)
    store = SQLiteGraphStore(str(db_path))
    fact_id = "f_first_refresh"
    _seed_fact(store, fact_id, claim="original claim text")
    _set_fact_version(db_path, fact_id, 1)

    result = _apply(db_path, fact_id, intent_canonical_version=1)

    assert result.outcome == ProjectionApplyOutcome.APPLIED
    assert result.applied_canonical_version == 1
    assert _fts_row(db_path, fact_id) == ("original claim text", "test")
    assert _checkpoint_row(db_path, fact_id)[0] == 1
    assert _integrity_ok(db_path)


def test_exact_repeat_is_idempotent(tmp_path: Path) -> None:
    db_path = tmp_path / "idempotent-repeat.db"
    _migrate(db_path)
    store = SQLiteGraphStore(str(db_path))
    fact_id = "f_idempotent"
    _seed_fact(store, fact_id, claim="stable claim")
    _set_fact_version(db_path, fact_id, 1)

    first = _apply(db_path, fact_id, intent_canonical_version=1)
    second = _apply(db_path, fact_id, intent_canonical_version=1)

    assert first.outcome == second.outcome == ProjectionApplyOutcome.APPLIED
    assert first.applied_canonical_version == second.applied_canonical_version == 1
    with sqlite3.connect(str(db_path)) as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM facts_fts WHERE fact_id = ?", (fact_id,),
        ).fetchone()[0] == 1
        assert conn.execute(
            "SELECT COUNT(*) FROM projection_checkpoints WHERE aggregate_id = ?", (fact_id,),
        ).fetchone()[0] == 1
    assert _integrity_ok(db_path)


# ── 6-7. Current-Canon rule + monotonic checkpoint ──────────────────────────

def test_stale_intent_with_newer_current_canon_projects_current_canon(
    tmp_path: Path,
) -> None:
    """An old/redelivered intent (canonical_version=1) arriving after Canon
    has already advanced to version 3 must refresh to CURRENT Canon content
    and version — never replay the stale content the intent was created
    against."""
    db_path = tmp_path / "stale-intent-newer-canon.db"
    _migrate(db_path)
    store = SQLiteGraphStore(str(db_path))
    fact_id = "f_stale_intent"
    _seed_fact(store, fact_id, claim="version 1 content")
    _set_fact_version(db_path, fact_id, 1)
    first = _apply(db_path, fact_id, intent_canonical_version=1)
    assert first.applied_canonical_version == 1
    assert _fts_row(db_path, fact_id) == ("version 1 content", "test")

    with sqlite3.connect(str(db_path)) as conn:
        conn.execute(
            "UPDATE facts SET claim = ?, fact_version = ? WHERE fact_id = ?",
            ("version 3 content", 3, fact_id),
        )
        conn.commit()

    stale_replay = _apply(db_path, fact_id, intent_canonical_version=1)

    assert stale_replay.outcome == ProjectionApplyOutcome.APPLIED
    assert stale_replay.applied_canonical_version == 3
    assert _fts_row(db_path, fact_id) == ("version 3 content", "test")
    assert _checkpoint_row(db_path, fact_id)[0] == 3


def test_checkpoint_never_decreases_under_out_of_order_apply(tmp_path: Path) -> None:
    db_path = tmp_path / "monotonic-checkpoint.db"
    _migrate(db_path)
    store = SQLiteGraphStore(str(db_path))
    fact_id = "f_monotonic"
    _seed_fact(store, fact_id, claim="claim at v7")
    _set_fact_version(db_path, fact_id, 7)
    advanced = _apply(db_path, fact_id, intent_canonical_version=7)
    assert advanced.applied_canonical_version == 7
    checkpoint_before = _checkpoint_row(db_path, fact_id)

    stale = _apply(db_path, fact_id, intent_canonical_version=5)

    assert stale.outcome == ProjectionApplyOutcome.APPLIED
    assert stale.applied_canonical_version == 7, (
        "current Canon is still 7 — a stale intent must never pull the "
        "checkpoint or FTS content backward"
    )
    assert _checkpoint_row(db_path, fact_id)[0] == 7
    assert _checkpoint_row(db_path, fact_id)[1] == checkpoint_before[1], (
        "a blocked (no-op) monotonic upsert must not even touch updated_at"
    )
    assert _fts_row(db_path, fact_id) == ("claim at v7", "test")


# ── 8. Fail closed on behind-Canon intent ───────────────────────────────────

def test_canon_version_behind_intent_fails_closed(tmp_path: Path) -> None:
    db_path = tmp_path / "behind-intent.db"
    _migrate(db_path)
    store = SQLiteGraphStore(str(db_path))
    fact_id = "f_behind"
    _seed_fact(store, fact_id, claim="claim at v3")
    _set_fact_version(db_path, fact_id, 3)
    # store_fact()'s own pre-existing best-effort FTS sync (unrelated to
    # this module) already wrote a facts_fts row during seeding — capture
    # it so the assertion below proves it is UNCHANGED, not absent.
    fts_row_before = _fts_row(db_path, fact_id)
    assert fts_row_before is not None

    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute("BEGIN IMMEDIATE")
        with pytest.raises(CanonVersionBehindIntentError):
            apply_fts_projection(conn, fact_id=fact_id, intent_canonical_version=5)
        conn.rollback()
    finally:
        conn.close()

    assert _fts_row(db_path, fact_id) == fts_row_before, (
        "a fail-closed apply must not touch the pre-existing FTS row at all"
    )
    assert _checkpoint_row(db_path, fact_id) is None
    assert _integrity_ok(db_path)


# ── 9. Missing/erased Canon ──────────────────────────────────────────────────

def test_missing_canon_removes_fts_and_checkpoint_never_resurrects(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "missing-canon.db"
    _migrate(db_path)
    store = SQLiteGraphStore(str(db_path))
    fact_id = "f_missing_canon"
    _seed_fact(store, fact_id, claim="will be erased")
    _set_fact_version(db_path, fact_id, 1)
    applied = _apply(db_path, fact_id, intent_canonical_version=1)
    assert applied.outcome == ProjectionApplyOutcome.APPLIED
    assert _fts_row(db_path, fact_id) is not None
    assert _checkpoint_row(db_path, fact_id) is not None

    store.erase_fact_dependents_atomic(fact_id)
    assert store.get_fact(fact_id) is None

    result = _apply(db_path, fact_id, intent_canonical_version=1)

    assert result.outcome == ProjectionApplyOutcome.MISSING_CANON_REMOVED
    assert result.applied_canonical_version is None
    assert _fts_row(db_path, fact_id) is None
    assert _checkpoint_row(db_path, fact_id) is None
    assert _integrity_ok(db_path)


# ── 10. FTS unavailable ──────────────────────────────────────────────────────

def test_missing_facts_fts_table_yields_structured_non_delivery(tmp_path: Path) -> None:
    db_path = tmp_path / "fts-unavailable.db"
    _migrate(db_path)
    store = SQLiteGraphStore(str(db_path))
    fact_id = "f_fts_unavailable"
    _seed_fact(store, fact_id, claim="claim text")
    _set_fact_version(db_path, fact_id, 1)
    with sqlite3.connect(str(db_path)) as conn:
        conn.execute("DROP TABLE facts_fts")
        conn.commit()

    result = _apply(db_path, fact_id, intent_canonical_version=1)

    assert result.outcome == ProjectionApplyOutcome.FTS_UNAVAILABLE
    assert result.applied_canonical_version is None
    assert _checkpoint_row(db_path, fact_id) is None, (
        "FTS_UNAVAILABLE must never write a checkpoint claiming delivery"
    )
    assert _integrity_ok(db_path)


# ── 11. Rollback both directions ────────────────────────────────────────────

def test_fts_write_failure_rolls_back_checkpoint(tmp_path: Path) -> None:
    """SQLite does not allow triggers on virtual (FTS5) tables at all — a
    genuine FTS write failure is instead forced by corrupting one of
    facts_fts's own shadow tables, a real DB-level breakage, not a mock."""
    db_path = tmp_path / "fts-failure-rollback.db"
    _migrate(db_path)
    store = SQLiteGraphStore(str(db_path))
    fact_id = "f_fts_failure"
    _seed_fact(store, fact_id, claim="claim at v1")
    _set_fact_version(db_path, fact_id, 1)
    baseline = _apply(db_path, fact_id, intent_canonical_version=1)
    assert baseline.applied_canonical_version == 1
    checkpoint_before = _checkpoint_row(db_path, fact_id)

    with sqlite3.connect(str(db_path)) as conn:
        conn.execute("UPDATE facts SET claim = ?, fact_version = ? WHERE fact_id = ?",
                     ("claim at v2", 2, fact_id))
        conn.execute("DROP TABLE facts_fts_data")
        conn.commit()

    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute("BEGIN IMMEDIATE")
        with pytest.raises(sqlite3.DatabaseError):
            apply_fts_projection(conn, fact_id=fact_id, intent_canonical_version=1)
        conn.rollback()
    finally:
        conn.close()

    assert _checkpoint_row(db_path, fact_id) == checkpoint_before, (
        "checkpoint must roll back to v1 together with the failed FTS write "
        "for v2 — never left claiming v2 was applied"
    )


def test_checkpoint_write_failure_rolls_back_the_whole_attempt(tmp_path: Path) -> None:
    db_path = tmp_path / "checkpoint-failure-rollback.db"
    _migrate(db_path)
    store = SQLiteGraphStore(str(db_path))
    fact_id = "f_checkpoint_failure"
    _seed_fact(store, fact_id, claim="claim at v1")
    _set_fact_version(db_path, fact_id, 1)
    baseline = _apply(db_path, fact_id, intent_canonical_version=1)
    assert baseline.applied_canonical_version == 1

    with sqlite3.connect(str(db_path)) as conn:
        conn.execute("UPDATE facts SET claim = ?, fact_version = ? WHERE fact_id = ?",
                     ("claim at v2", 2, fact_id))
        conn.execute("""
            CREATE TRIGGER simulate_checkpoint_write_failure
            BEFORE UPDATE ON projection_checkpoints
            BEGIN
                SELECT RAISE(ABORT, 'SIMULATED: real DB failure mid-transaction');
            END;
        """)
        conn.commit()

    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute("BEGIN IMMEDIATE")
        with pytest.raises(sqlite3.IntegrityError):
            apply_fts_projection(conn, fact_id=fact_id, intent_canonical_version=1)
        conn.rollback()
    finally:
        conn.close()

    assert _checkpoint_row(db_path, fact_id)[0] == 1, "checkpoint must stay at v1"
    assert _fts_row(db_path, fact_id) == ("claim at v1", "test"), (
        "FTS must not have been advanced to v2's content when the "
        "checkpoint write for v2 failed first"
    )
    with sqlite3.connect(str(db_path)) as conn:
        conn.execute("DROP TRIGGER simulate_checkpoint_write_failure")
        conn.commit()
    assert _integrity_ok(db_path)


# ── 12. Concurrency ──────────────────────────────────────────────────────────

@pytest.mark.parametrize("contenders", [2, 10])
def test_concurrent_applies_preserve_one_monotonic_final_state(
    tmp_path: Path, contenders: int,
) -> None:
    db_path = tmp_path / f"concurrent-{contenders}.db"
    _migrate(db_path)
    store = SQLiteGraphStore(str(db_path))
    fact_id = "f_concurrent"
    _seed_fact(store, fact_id, claim="final canon content")
    _set_fact_version(db_path, fact_id, contenders)

    barrier = threading.Barrier(contenders, timeout=15)

    def worker(intent_version: int):
        conn = sqlite3.connect(str(db_path), timeout=15)
        try:
            barrier.wait(timeout=15)
            conn.execute("BEGIN IMMEDIATE")
            result = apply_fts_projection(
                conn, fact_id=fact_id, intent_canonical_version=intent_version,
            )
            conn.commit()
            return result
        finally:
            conn.close()

    with ThreadPoolExecutor(max_workers=contenders) as executor:
        futures = [
            executor.submit(worker, (i % contenders) + 1) for i in range(contenders)
        ]
        results = [f.result(timeout=30) for f in futures]

    assert all(r.outcome == ProjectionApplyOutcome.APPLIED for r in results)
    assert all(r.applied_canonical_version == contenders for r in results), (
        "every contender must observe the final monotonic checkpoint value, "
        "never an intermediate/lower one"
    )
    assert _checkpoint_row(db_path, fact_id)[0] == contenders
    assert _fts_row(db_path, fact_id) == ("final canon content", "test")
    assert _integrity_ok(db_path)


# ── 13. Erasure ──────────────────────────────────────────────────────────────

def test_erasure_removes_checkpoint_and_detects_reappearance(tmp_path: Path) -> None:
    db_path = tmp_path / "erasure-checkpoint.db"
    _migrate(db_path)
    store = SQLiteGraphStore(str(db_path))
    fact_id = "f_erasure_checkpoint"
    _seed_fact(store, fact_id, claim="claim text")
    _set_fact_version(db_path, fact_id, 1)
    applied = _apply(db_path, fact_id, intent_canonical_version=1)
    assert applied.outcome == ProjectionApplyOutcome.APPLIED

    result = store.erase_fact_dependents_atomic(fact_id)

    assert result["tables"]["projection_checkpoints"] == {"applicable": True, "deleted": 1}
    assert _checkpoint_row(db_path, fact_id) is None
    assert store.same_db_dependents_present(fact_id) is False

    # Reappearance: a checkpoint row surviving/reappearing for an
    # already-erased fact must be detected as residual.
    with sqlite3.connect(str(db_path)) as conn:
        conn.execute(
            "INSERT INTO projection_checkpoints "
            "(aggregate_type, aggregate_id, scope_ref, projection_kind, "
            "applied_canonical_version, updated_at) "
            "VALUES ('fact', ?, ?, 'fts', 1, '2026-08-04T00:00:00Z')",
            (fact_id, LOCAL_PROJECTION_SCOPE_REF),
        )
        conn.commit()

    assert store.same_db_dependents_present(fact_id) is True
    assert _integrity_ok(db_path)


# ── 14. Integrity throughout — covered inline in every test above ──────────
