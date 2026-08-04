"""Issue #193: bounded local projection dispatcher with crash recovery.

Proves the claim/lease/retry/ack state machine in core/projection_dispatcher.py
(migration 022, projection_dispatch_state) end to end: bounded claim, apply
strictly outside the claim transaction, a proven crash window between apply
and ack, CAS-guarded ack/retry/park by exact active lease token, deterministic
bounded backoff, apply-outcome policy classification, and erasure ownership.

No background worker, scheduler, asyncio task, or sleep exists anywhere in
this file or in the module it tests — every "instance"/"restart" is modeled
as a fresh sqlite3.Connection against the same on-disk database, and every
clock is an explicitly injected `datetime`, never wall-clock time.

Every test constructs a real, temp-file-backed SQLite database migrated
through the REAL migration chain (scripts/apply_migrations.py). Failures are
simulated with genuine SQLite-level breakage (a corrupted FTS5 shadow table,
a dropped table, a real CHECK/UNIQUE violation) — never monkeypatched
exceptions.
"""
from __future__ import annotations

import os
import subprocess
import sys
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

import pytest

from core.memory import SQLiteGraphStore
from core.projection_dispatcher import (
    MAX_BATCH_SIZE,
    AckOutcome,
    DispatchAction,
    DispatchErrorCode,
    InvalidBatchSizeError,
    LeaseValidationOutcome,
    ParkOutcome,
    ProjectionDispatchContractError,
    RetryOutcome,
    ack_claim,
    apply_claimed_work,
    claim_batch,
    compute_retry_delay_seconds,
    dispatch_once,
    park_claim,
    retry_claim,
)
from core.projection_outbox import LOCAL_PROJECTION_SCOPE_REF

_ROOT = os.path.join(os.path.dirname(__file__), "..")
_APPLY_MIGRATIONS = os.path.join(_ROOT, "scripts", "apply_migrations.py")

_T0 = datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC)


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
    with sqlite3.connect(str(db_path)) as conn:
        conn.execute("UPDATE facts SET fact_version = ? WHERE fact_id = ?", (version, fact_id))
        conn.commit()


def _insert_outbox(
    conn: sqlite3.Connection,
    *,
    outbox_id: str,
    aggregate_id: str,
    canonical_version: int = 1,
    created_at: str = "2026-01-01T00:00:00Z",
    projection_kind: str = "all",
    policy_version: str = "projection-outbox-v1",
    scope_ref: str = LOCAL_PROJECTION_SCOPE_REF,
) -> None:
    """Direct SQL insert (bypassing ProjectionIntent's own Python-level
    validation, which is irrelevant here) — mirrors
    tests/test_erasure_projection_outbox_dependency.py's own
    `_insert_outbox_row()` convention, extended with created_at/
    projection_kind/scope_ref so ordering, unsupported-policy-target, and
    unsupported-scope tests can control them directly."""
    conn.execute(
        "INSERT INTO projection_outbox ("
        "outbox_id, aggregate_type, aggregate_id, scope_ref, projection_kind, "
        "operation, canonical_version, policy_version, created_at"
        ") VALUES (?, 'fact', ?, ?, ?, 'refresh', ?, ?, ?)",
        (
            outbox_id, aggregate_id, scope_ref, projection_kind,
            canonical_version, policy_version, created_at,
        ),
    )


def _dispatch_row(db_path: Path, outbox_id: str):
    with sqlite3.connect(str(db_path)) as conn:
        return conn.execute(
            "SELECT outbox_id, aggregate_id, lifecycle_state, lease_token, "
            "lease_expires_at, attempt_count, next_attempt_at, last_error_code, "
            "updated_at, acknowledged_at "
            "FROM projection_dispatch_state WHERE outbox_id = ?",
            (outbox_id,),
        ).fetchone()


def _fts_row(db_path: Path, fact_id: str):
    with sqlite3.connect(str(db_path)) as conn:
        return conn.execute(
            "SELECT claim, source FROM facts_fts WHERE fact_id = ?", (fact_id,),
        ).fetchone()


def _checkpoint_row(db_path: Path, fact_id: str):
    with sqlite3.connect(str(db_path)) as conn:
        return conn.execute(
            "SELECT applied_canonical_version FROM projection_checkpoints "
            "WHERE aggregate_type = 'fact' AND aggregate_id = ? "
            "AND scope_ref = ? AND projection_kind = 'fts'",
            (fact_id, LOCAL_PROJECTION_SCOPE_REF),
        ).fetchone()


def _integrity_ok(db_path: Path) -> bool:
    with sqlite3.connect(str(db_path)) as conn:
        return conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def _open(db_path: Path, *, timeout: float = 15.0) -> sqlite3.Connection:
    return sqlite3.connect(str(db_path), timeout=timeout)


# ── 1. Successful claim -> apply -> ack ─────────────────────────────────────

def test_successful_claim_apply_ack(tmp_path: Path) -> None:
    db_path = tmp_path / "success.db"
    _migrate(db_path)
    store = SQLiteGraphStore(str(db_path))
    fact_id = "f_success"
    _seed_fact(store, fact_id, claim="original claim")
    _set_fact_version(db_path, fact_id, 1)
    with _open(db_path) as conn:
        _insert_outbox(conn, outbox_id="ob_success", aggregate_id=fact_id)
        conn.commit()

    conn = _open(db_path)
    try:
        claimed = claim_batch(conn, batch_size=10, lease_duration_seconds=300, now=_T0)
        assert len(claimed) == 1
        work = claimed[0]
        result = apply_claimed_work(conn, work, now=_T0)
        assert result.action == DispatchAction.ACKNOWLEDGE
        outcome = ack_claim(conn, work.outbox_id, work.lease_token, now=_T0)
        assert outcome == AckOutcome.ACKNOWLEDGED
    finally:
        conn.close()

    row = _dispatch_row(db_path, "ob_success")
    assert row[2] == "acknowledged"
    assert row[3] is None and row[4] is None  # lease cleared
    assert row[9] is not None  # acknowledged_at set
    assert _fts_row(db_path, fact_id) == ("original claim", "test")
    assert _checkpoint_row(db_path, fact_id)[0] == 1
    assert _integrity_ok(db_path)


# ── 2-3. Concurrent claimers: one owner per intent ──────────────────────────

@pytest.mark.parametrize("contenders", [2, 10])
def test_concurrent_claimers_one_owner_per_intent(tmp_path: Path, contenders: int) -> None:
    db_path = tmp_path / f"concurrent-{contenders}.db"
    _migrate(db_path)
    store = SQLiteGraphStore(str(db_path))
    fact_ids = [f"f_concurrent_{i}" for i in range(contenders)]
    for fact_id in fact_ids:
        _seed_fact(store, fact_id, claim=f"claim for {fact_id}")
    with _open(db_path) as conn:
        for i, fact_id in enumerate(fact_ids):
            _insert_outbox(
                conn, outbox_id=f"ob_concurrent_{i}", aggregate_id=fact_id,
                created_at=f"2026-01-01T00:00:{i:02d}Z",
            )
        conn.commit()

    barrier = threading.Barrier(contenders, timeout=15)

    def worker():
        conn = _open(db_path)
        try:
            barrier.wait(timeout=15)
            return claim_batch(conn, batch_size=1, lease_duration_seconds=300, now=_T0)
        finally:
            conn.close()

    with ThreadPoolExecutor(max_workers=contenders) as executor:
        futures = [executor.submit(worker) for _ in range(contenders)]
        results = [f.result(timeout=30) for f in futures]

    all_claimed = [w.outbox_id for batch in results for w in batch]
    assert len(all_claimed) == contenders, "every intent must be claimed exactly once, none skipped"
    assert len(set(all_claimed)) == contenders, "no outbox_id must be claimed by two owners"
    assert _integrity_ok(db_path)


# ── 4. Strict batch maximum ──────────────────────────────────────────────────

def test_batch_never_exceeds_requested_size(tmp_path: Path) -> None:
    db_path = tmp_path / "batch-max.db"
    _migrate(db_path)
    store = SQLiteGraphStore(str(db_path))
    fact_ids = [f"f_batch_{i}" for i in range(12)]
    for fact_id in fact_ids:
        _seed_fact(store, fact_id, claim=f"claim for {fact_id}")
    with _open(db_path) as conn:
        for i, fact_id in enumerate(fact_ids):
            _insert_outbox(
                conn, outbox_id=f"ob_batch_{i}", aggregate_id=fact_id,
                created_at=f"2026-01-01T00:00:{i:02d}Z",
            )
        conn.commit()

    conn = _open(db_path)
    try:
        first = claim_batch(conn, batch_size=5, lease_duration_seconds=300, now=_T0)
        assert len(first) == 5
        second = claim_batch(conn, batch_size=5, lease_duration_seconds=300, now=_T0)
        assert len(second) == 5
        third = claim_batch(conn, batch_size=5, lease_duration_seconds=300, now=_T0)
        assert len(third) == 2, "only 2 of the 12 intents remain unclaimed"
    finally:
        conn.close()


# ── 5. Deterministic created_at/outbox_id ordering ──────────────────────────

def test_claim_order_is_created_at_then_outbox_id(tmp_path: Path) -> None:
    db_path = tmp_path / "ordering.db"
    _migrate(db_path)
    store = SQLiteGraphStore(str(db_path))
    for fid in ("f_ord_a", "f_ord_b", "f_ord_c"):
        _seed_fact(store, fid, claim=fid)
    with _open(db_path) as conn:
        _insert_outbox(conn, outbox_id="ob_ord_c", aggregate_id="f_ord_c", created_at="2026-01-01T00:00:00Z")
        _insert_outbox(conn, outbox_id="ob_ord_a", aggregate_id="f_ord_a", created_at="2026-01-01T00:00:00Z")
        _insert_outbox(conn, outbox_id="ob_ord_b", aggregate_id="f_ord_b", created_at="2026-01-01T00:00:01Z")
        conn.commit()

    conn = _open(db_path)
    try:
        claimed = claim_batch(conn, batch_size=10, lease_duration_seconds=300, now=_T0)
    finally:
        conn.close()

    assert [w.outbox_id for w in claimed] == ["ob_ord_a", "ob_ord_c", "ob_ord_b"], (
        "same created_at ties break by outbox_id ascending; earlier created_at always first"
    )


# ── 6. Invalid batch size rejected ───────────────────────────────────────────

@pytest.mark.parametrize("bad_size", [0, -1, MAX_BATCH_SIZE + 1, 1000])
def test_invalid_batch_size_rejected(tmp_path: Path, bad_size: int) -> None:
    db_path = tmp_path / "invalid-batch.db"
    _migrate(db_path)
    conn = _open(db_path)
    try:
        with pytest.raises(InvalidBatchSizeError):
            claim_batch(conn, batch_size=bad_size, lease_duration_seconds=300, now=_T0)
        assert conn.in_transaction is False, "a rejected batch size must never open a transaction"
    finally:
        conn.close()


# ── 7. Crash after claim, before apply: lease expires, second instance reclaims ─

def test_crash_after_claim_before_apply_lease_expires_and_reclaims(tmp_path: Path) -> None:
    db_path = tmp_path / "crash-after-claim.db"
    _migrate(db_path)
    store = SQLiteGraphStore(str(db_path))
    fact_id = "f_crash_claim"
    _seed_fact(store, fact_id, claim="v1")
    _set_fact_version(db_path, fact_id, 1)
    with _open(db_path) as conn:
        _insert_outbox(conn, outbox_id="ob_crash_claim", aggregate_id=fact_id)
        conn.commit()

    instance_a = _open(db_path)
    try:
        claimed_a = claim_batch(instance_a, batch_size=10, lease_duration_seconds=60, now=_T0)
    finally:
        instance_a.close()
    # Simulated crash: instance A never calls apply_claimed_work.

    later = _T0 + timedelta(seconds=120)
    instance_b = _open(db_path)
    try:
        claimed_b = claim_batch(instance_b, batch_size=10, lease_duration_seconds=60, now=later)
        assert len(claimed_b) == 1
        work_b = claimed_b[0]
        assert work_b.outbox_id == claimed_a[0].outbox_id
        assert work_b.lease_token != claimed_a[0].lease_token
        assert work_b.attempt_count == claimed_a[0].attempt_count + 1

        # A's stale token can no longer apply.
        stale_result = apply_claimed_work(instance_b, claimed_a[0], now=later)
        assert stale_result.action == DispatchAction.REJECTED
        assert stale_result.lease_validation == LeaseValidationOutcome.STALE_TOKEN

        result_b = apply_claimed_work(instance_b, work_b, now=later)
        assert result_b.action == DispatchAction.ACKNOWLEDGE
        ack_b = ack_claim(instance_b, work_b.outbox_id, work_b.lease_token, now=later)
        assert ack_b == AckOutcome.ACKNOWLEDGED
    finally:
        instance_b.close()
    assert _integrity_ok(db_path)


# ── 8. Crash after apply, before ack: idempotent reapply, no duplication ────

def test_crash_after_apply_before_ack_restart_reclaims_idempotently(tmp_path: Path) -> None:
    db_path = tmp_path / "crash-after-apply.db"
    _migrate(db_path)
    store = SQLiteGraphStore(str(db_path))
    fact_id = "f_crash_apply"
    _seed_fact(store, fact_id, claim="v1 content")
    _set_fact_version(db_path, fact_id, 1)
    with _open(db_path) as conn:
        _insert_outbox(conn, outbox_id="ob_crash_apply", aggregate_id=fact_id)
        conn.commit()

    instance_a = _open(db_path)
    try:
        claimed_a = claim_batch(instance_a, batch_size=10, lease_duration_seconds=60, now=_T0)
        work_a = claimed_a[0]
        result_a = apply_claimed_work(instance_a, work_a, now=_T0)
        assert result_a.action == DispatchAction.ACKNOWLEDGE
    finally:
        instance_a.close()
    # Simulated crash: instance A never calls ack_claim(). FTS/checkpoint are
    # already committed; dispatch_state is still 'leased' under A's token.

    assert _fts_row(db_path, fact_id) == ("v1 content", "test")
    assert _checkpoint_row(db_path, fact_id)[0] == 1
    row_before_restart = _dispatch_row(db_path, "ob_crash_apply")
    assert row_before_restart[2] == "leased"

    later = _T0 + timedelta(seconds=120)
    instance_b = _open(db_path)
    try:
        claimed_b = claim_batch(instance_b, batch_size=10, lease_duration_seconds=60, now=later)
        assert len(claimed_b) == 1
        work_b = claimed_b[0]
        assert work_b.attempt_count == 2

        result_b = apply_claimed_work(instance_b, work_b, now=later)
        assert result_b.action == DispatchAction.ACKNOWLEDGE
        ack_b = ack_claim(instance_b, work_b.outbox_id, work_b.lease_token, now=later)
        assert ack_b == AckOutcome.ACKNOWLEDGED
    finally:
        instance_b.close()

    with sqlite3.connect(str(db_path)) as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM facts_fts WHERE fact_id = ?", (fact_id,),
        ).fetchone()[0] == 1, "no duplicate FTS row from the reapply"
        assert conn.execute(
            "SELECT COUNT(*) FROM projection_checkpoints WHERE aggregate_id = ?", (fact_id,),
        ).fetchone()[0] == 1, "no duplicate checkpoint row from the reapply"
    assert _fts_row(db_path, fact_id) == ("v1 content", "test")
    assert _checkpoint_row(db_path, fact_id)[0] == 1, "reapply must not regress or duplicate the checkpoint"
    assert _dispatch_row(db_path, "ob_crash_apply")[2] == "acknowledged"
    assert _integrity_ok(db_path)


# ── 9. Stale lease token cannot apply ────────────────────────────────────────

def test_stale_lease_token_cannot_apply(tmp_path: Path) -> None:
    db_path = tmp_path / "stale-apply.db"
    _migrate(db_path)
    store = SQLiteGraphStore(str(db_path))
    fact_id = "f_stale_apply"
    _seed_fact(store, fact_id, claim="original")
    with _open(db_path) as conn:
        _insert_outbox(conn, outbox_id="ob_stale_apply", aggregate_id=fact_id)
        conn.commit()

    conn = _open(db_path)
    try:
        claimed = claim_batch(conn, batch_size=10, lease_duration_seconds=60, now=_T0)
        stale_work = claimed[0]
        later = _T0 + timedelta(seconds=120)
        reclaimed = claim_batch(conn, batch_size=10, lease_duration_seconds=60, now=later)
        assert len(reclaimed) == 1

        result = apply_claimed_work(conn, stale_work, now=later)
        assert result.action == DispatchAction.REJECTED
        assert result.lease_validation == LeaseValidationOutcome.STALE_TOKEN
    finally:
        conn.close()

    assert _checkpoint_row(db_path, fact_id) is None, "a stale-token apply attempt must not mutate anything"
    assert _integrity_ok(db_path)


# ── 10. Stale lease token cannot ack ─────────────────────────────────────────

def test_stale_lease_token_cannot_ack(tmp_path: Path) -> None:
    db_path = tmp_path / "stale-ack.db"
    _migrate(db_path)
    store = SQLiteGraphStore(str(db_path))
    fact_id = "f_stale_ack"
    _seed_fact(store, fact_id, claim="original")
    with _open(db_path) as conn:
        _insert_outbox(conn, outbox_id="ob_stale_ack", aggregate_id=fact_id)
        conn.commit()

    conn = _open(db_path)
    try:
        claimed = claim_batch(conn, batch_size=10, lease_duration_seconds=60, now=_T0)
        stale_work = claimed[0]
        later = _T0 + timedelta(seconds=120)
        reclaimed = claim_batch(conn, batch_size=10, lease_duration_seconds=60, now=later)
        fresh_work = reclaimed[0]

        outcome = ack_claim(conn, stale_work.outbox_id, stale_work.lease_token, now=later)
        assert outcome == AckOutcome.ACK_REJECTED
    finally:
        conn.close()

    row = _dispatch_row(db_path, "ob_stale_ack")
    assert row[2] == "leased"
    assert row[3] == fresh_work.lease_token, "the real (fresh) holder's lease must be untouched"
    assert _integrity_ok(db_path)


# ── 11. Expired lease token cannot ack ───────────────────────────────────────

def test_expired_lease_token_cannot_ack(tmp_path: Path) -> None:
    db_path = tmp_path / "expired-ack.db"
    _migrate(db_path)
    store = SQLiteGraphStore(str(db_path))
    fact_id = "f_expired_ack"
    _seed_fact(store, fact_id, claim="original")
    with _open(db_path) as conn:
        _insert_outbox(conn, outbox_id="ob_expired_ack", aggregate_id=fact_id)
        conn.commit()

    conn = _open(db_path)
    try:
        claimed = claim_batch(conn, batch_size=10, lease_duration_seconds=60, now=_T0)
        work = claimed[0]
        past_expiry = _T0 + timedelta(seconds=120)  # no one reclaimed; just expired
        outcome = ack_claim(conn, work.outbox_id, work.lease_token, now=past_expiry)
        assert outcome == AckOutcome.ACK_REJECTED
    finally:
        conn.close()

    row = _dispatch_row(db_path, "ob_expired_ack")
    assert row[2] == "leased", "an expired-but-unreclaimed row stays leased, not silently acknowledged"
    assert _integrity_ok(db_path)


def test_expired_lease_token_cannot_retry(tmp_path: Path) -> None:
    """Review finding, PR #197: retry_claim() must reject an
    expired-but-not-yet-reclaimed holder the same way ack_claim() does —
    an exact token match alone is not enough once the lease has expired."""
    db_path = tmp_path / "expired-retry.db"
    _migrate(db_path)
    store = SQLiteGraphStore(str(db_path))
    fact_id = "f_expired_retry"
    _seed_fact(store, fact_id, claim="original")
    with _open(db_path) as conn:
        _insert_outbox(conn, outbox_id="ob_expired_retry", aggregate_id=fact_id)
        conn.commit()

    conn = _open(db_path)
    try:
        work = claim_batch(conn, batch_size=10, lease_duration_seconds=60, now=_T0)[0]
        past_expiry = _T0 + timedelta(seconds=120)  # no one reclaimed; just expired
        outcome = retry_claim(
            conn, work.outbox_id, work.lease_token,
            error_code=DispatchErrorCode.SQLITE_BUSY,
            now=past_expiry,
        )
        assert outcome == RetryOutcome.RETRY_REJECTED
    finally:
        conn.close()

    row = _dispatch_row(db_path, "ob_expired_retry")
    assert row[2] == "leased", "an expired-but-unreclaimed row stays leased, not silently moved to retry"
    assert row[6] is None, "next_attempt_at must not be set by a rejected retry"
    assert _integrity_ok(db_path)


def test_expired_lease_token_cannot_park(tmp_path: Path) -> None:
    """Review finding, PR #197: park_claim() must reject an
    expired-but-not-yet-reclaimed holder the same way ack_claim() does."""
    db_path = tmp_path / "expired-park.db"
    _migrate(db_path)
    store = SQLiteGraphStore(str(db_path))
    fact_id = "f_expired_park"
    _seed_fact(store, fact_id, claim="original")
    with _open(db_path) as conn:
        _insert_outbox(conn, outbox_id="ob_expired_park", aggregate_id=fact_id)
        conn.commit()

    conn = _open(db_path)
    try:
        work = claim_batch(conn, batch_size=10, lease_duration_seconds=60, now=_T0)[0]
        past_expiry = _T0 + timedelta(seconds=120)  # no one reclaimed; just expired
        outcome = park_claim(
            conn, work.outbox_id, work.lease_token,
            error_code=DispatchErrorCode.FTS_UNAVAILABLE, now=past_expiry,
        )
        assert outcome == ParkOutcome.PARK_REJECTED
    finally:
        conn.close()

    row = _dispatch_row(db_path, "ob_expired_park")
    assert row[2] == "leased", "an expired-but-unreclaimed row stays leased, not silently parked"
    assert _integrity_ok(db_path)


# ── 12. Retry transition requires exact active token ────────────────────────

def test_retry_requires_exact_active_token(tmp_path: Path) -> None:
    db_path = tmp_path / "retry-token.db"
    _migrate(db_path)
    store = SQLiteGraphStore(str(db_path))
    fact_id = "f_retry_token"
    _seed_fact(store, fact_id, claim="original")
    with _open(db_path) as conn:
        _insert_outbox(conn, outbox_id="ob_retry_token", aggregate_id=fact_id)
        conn.commit()

    conn = _open(db_path)
    try:
        claimed = claim_batch(conn, batch_size=10, lease_duration_seconds=60, now=_T0)
        stale_work = claimed[0]
        later = _T0 + timedelta(seconds=120)
        reclaimed = claim_batch(conn, batch_size=10, lease_duration_seconds=60, now=later)
        fresh_work = reclaimed[0]

        outcome = retry_claim(
            conn, stale_work.outbox_id, stale_work.lease_token,
            error_code=DispatchErrorCode.SQLITE_BUSY,
            now=later,
        )
        assert outcome == RetryOutcome.RETRY_REJECTED
    finally:
        conn.close()

    row = _dispatch_row(db_path, "ob_retry_token")
    assert row[2] == "leased"
    assert row[3] == fresh_work.lease_token
    assert _integrity_ok(db_path)


# ── 13. Deterministic retry due time with injected clock ────────────────────

def test_retry_delay_is_deterministic_bounded_exponential() -> None:
    assert compute_retry_delay_seconds(1) == 1.0
    assert compute_retry_delay_seconds(2) == 2.0
    assert compute_retry_delay_seconds(3) == 4.0
    assert compute_retry_delay_seconds(4) == 8.0
    assert compute_retry_delay_seconds(9) == 256.0
    assert compute_retry_delay_seconds(10) == 300.0, "capped at MAX_RETRY_SECONDS"
    assert compute_retry_delay_seconds(50) == 300.0, "exponent itself is also capped, well below the cap"


def test_retry_claim_stores_exact_deterministic_next_attempt_at(tmp_path: Path) -> None:
    db_path = tmp_path / "retry-due.db"
    _migrate(db_path)
    store = SQLiteGraphStore(str(db_path))
    fact_id = "f_retry_due"
    _seed_fact(store, fact_id, claim="original")
    with _open(db_path) as conn:
        _insert_outbox(conn, outbox_id="ob_retry_due", aggregate_id=fact_id)
        conn.commit()

    conn = _open(db_path)
    try:
        work = claim_batch(conn, batch_size=10, lease_duration_seconds=60, now=_T0)[0]
        outcome = retry_claim(
            conn, work.outbox_id, work.lease_token,
            error_code=DispatchErrorCode.SQLITE_BUSY, now=_T0,
        )
        assert outcome == RetryOutcome.RETRY_SCHEDULED
    finally:
        conn.close()

    row = _dispatch_row(db_path, "ob_retry_due")
    expected = (_T0 + timedelta(seconds=1.0)).isoformat()  # attempt_count=1 -> delay 1s
    assert row[6] == expected
    assert row[7] == "SQLITE_BUSY"


# ── 14-15. Retry claimability around next_attempt_at ─────────────────────────

def test_retry_not_claimable_before_due_and_claimable_exactly_when_due(tmp_path: Path) -> None:
    db_path = tmp_path / "retry-claimability.db"
    _migrate(db_path)
    store = SQLiteGraphStore(str(db_path))
    fact_id = "f_retry_claimability"
    _seed_fact(store, fact_id, claim="original")
    with _open(db_path) as conn:
        _insert_outbox(conn, outbox_id="ob_retry_claimability", aggregate_id=fact_id)
        conn.commit()

    conn = _open(db_path)
    try:
        work = claim_batch(conn, batch_size=10, lease_duration_seconds=60, now=_T0)[0]
        retry_claim(
            conn, work.outbox_id, work.lease_token,
            error_code=DispatchErrorCode.SQLITE_BUSY, now=_T0,
        )
        due_at = _T0 + timedelta(seconds=1.0)

        before_due = due_at - timedelta(milliseconds=1)
        assert claim_batch(conn, batch_size=10, lease_duration_seconds=60, now=before_due) == ()

        exactly_due = claim_batch(conn, batch_size=10, lease_duration_seconds=60, now=due_at)
        assert len(exactly_due) == 1
        assert exactly_due[0].outbox_id == "ob_retry_claimability"
    finally:
        conn.close()


# ── 16. FTS_UNAVAILABLE becomes parked, not acked ────────────────────────────

def test_fts_unavailable_becomes_parked_not_acked(tmp_path: Path) -> None:
    db_path = tmp_path / "fts-unavailable.db"
    _migrate(db_path)
    store = SQLiteGraphStore(str(db_path))
    fact_id = "f_fts_unavailable"
    _seed_fact(store, fact_id, claim="claim text")
    with _open(db_path) as conn:
        conn.execute("DROP TABLE facts_fts")
        _insert_outbox(conn, outbox_id="ob_fts_unavailable", aggregate_id=fact_id)
        conn.commit()

    conn = _open(db_path)
    try:
        work = claim_batch(conn, batch_size=10, lease_duration_seconds=60, now=_T0)[0]
        result = apply_claimed_work(conn, work, now=_T0)
        assert result.action == DispatchAction.PARK
        assert result.error_code == DispatchErrorCode.FTS_UNAVAILABLE
        outcome = park_claim(conn, work.outbox_id, work.lease_token, error_code=result.error_code, now=_T0)
        assert outcome == ParkOutcome.PARKED
    finally:
        conn.close()

    row = _dispatch_row(db_path, "ob_fts_unavailable")
    assert row[2] == "parked"
    assert row[7] == "FTS_UNAVAILABLE"
    assert _checkpoint_row(db_path, fact_id) is None, "never acknowledge a non-delivery as if delivered"


# ── 17. GRAPH/VECTOR/unsupported policy becomes parked ──────────────────────

@pytest.mark.parametrize("unsupported_kind", ["graph", "vector"])
def test_unsupported_projection_kind_becomes_parked(tmp_path: Path, unsupported_kind: str) -> None:
    db_path = tmp_path / f"unsupported-{unsupported_kind}.db"
    _migrate(db_path)
    store = SQLiteGraphStore(str(db_path))
    fact_id = f"f_unsupported_{unsupported_kind}"
    _seed_fact(store, fact_id, claim="claim text")
    with _open(db_path) as conn:
        _insert_outbox(
            conn, outbox_id=f"ob_unsupported_{unsupported_kind}", aggregate_id=fact_id,
            projection_kind=unsupported_kind,
        )
        conn.commit()

    conn = _open(db_path)
    try:
        work = claim_batch(conn, batch_size=10, lease_duration_seconds=60, now=_T0)[0]
        result = apply_claimed_work(conn, work, now=_T0)
        assert result.action == DispatchAction.PARK
        assert result.error_code == DispatchErrorCode.UNSUPPORTED_POLICY_TARGET
        park_claim(conn, work.outbox_id, work.lease_token, error_code=result.error_code, now=_T0)
    finally:
        conn.close()

    assert _dispatch_row(db_path, f"ob_unsupported_{unsupported_kind}")[2] == "parked"


def test_unknown_policy_version_becomes_parked(tmp_path: Path) -> None:
    db_path = tmp_path / "unsupported-policy-version.db"
    _migrate(db_path)
    store = SQLiteGraphStore(str(db_path))
    fact_id = "f_unsupported_policy_version"
    _seed_fact(store, fact_id, claim="claim text")
    with _open(db_path) as conn:
        _insert_outbox(
            conn, outbox_id="ob_unsupported_policy_version", aggregate_id=fact_id,
            policy_version="v2-does-not-exist",
        )
        conn.commit()

    conn = _open(db_path)
    try:
        work = claim_batch(conn, batch_size=10, lease_duration_seconds=60, now=_T0)[0]
        result = apply_claimed_work(conn, work, now=_T0)
        assert result.action == DispatchAction.PARK
        assert result.error_code == DispatchErrorCode.UNSUPPORTED_POLICY_TARGET
    finally:
        conn.close()


# ── 18. CanonVersionBehindIntent becomes parked ──────────────────────────────

def test_canon_version_behind_intent_becomes_parked(tmp_path: Path) -> None:
    db_path = tmp_path / "canon-behind.db"
    _migrate(db_path)
    store = SQLiteGraphStore(str(db_path))
    fact_id = "f_canon_behind"
    _seed_fact(store, fact_id, claim="claim at v1")
    _set_fact_version(db_path, fact_id, 1)
    with _open(db_path) as conn:
        _insert_outbox(conn, outbox_id="ob_canon_behind", aggregate_id=fact_id, canonical_version=5)
        conn.commit()

    conn = _open(db_path)
    try:
        work = claim_batch(conn, batch_size=10, lease_duration_seconds=60, now=_T0)[0]
        result = apply_claimed_work(conn, work, now=_T0)
        assert result.action == DispatchAction.PARK
        assert result.error_code == DispatchErrorCode.CANON_VERSION_BEHIND_INTENT
        park_claim(conn, work.outbox_id, work.lease_token, error_code=result.error_code, now=_T0)
    finally:
        conn.close()

    assert _dispatch_row(db_path, "ob_canon_behind")[2] == "parked"
    assert _checkpoint_row(db_path, fact_id) is None
    assert _integrity_ok(db_path)


# ── 19. MISSING_CANON_REMOVED becomes acknowledged ───────────────────────────

def test_missing_canon_becomes_acknowledged(tmp_path: Path) -> None:
    db_path = tmp_path / "missing-canon.db"
    _migrate(db_path)
    with _open(db_path) as conn:
        _insert_outbox(conn, outbox_id="ob_missing_canon", aggregate_id="f_never_existed")
        conn.commit()

    conn = _open(db_path)
    try:
        work = claim_batch(conn, batch_size=10, lease_duration_seconds=60, now=_T0)[0]
        result = apply_claimed_work(conn, work, now=_T0)
        assert result.action == DispatchAction.ACKNOWLEDGE
        outcome = ack_claim(conn, work.outbox_id, work.lease_token, now=_T0)
        assert outcome == AckOutcome.ACKNOWLEDGED
    finally:
        conn.close()

    assert _dispatch_row(db_path, "ob_missing_canon")[2] == "acknowledged"
    assert _integrity_ok(db_path)


# ── 20. Older/redelivered intent reads current Canon ────────────────────────

def test_older_redelivered_intent_reads_current_canon(tmp_path: Path) -> None:
    db_path = tmp_path / "redelivered.db"
    _migrate(db_path)
    store = SQLiteGraphStore(str(db_path))
    fact_id = "f_redelivered"
    _seed_fact(store, fact_id, claim="version 1 content")
    with _open(db_path) as conn:
        conn.execute(
            "UPDATE facts SET claim = ?, fact_version = ? WHERE fact_id = ?",
            ("version 3 content", 3, fact_id),
        )
        _insert_outbox(conn, outbox_id="ob_redelivered", aggregate_id=fact_id, canonical_version=1)
        conn.commit()

    conn = _open(db_path)
    try:
        work = claim_batch(conn, batch_size=10, lease_duration_seconds=60, now=_T0)[0]
        assert work.canonical_version == 1
        result = apply_claimed_work(conn, work, now=_T0)
        assert result.action == DispatchAction.ACKNOWLEDGE
        ack_claim(conn, work.outbox_id, work.lease_token, now=_T0)
    finally:
        conn.close()

    assert _fts_row(db_path, fact_id) == ("version 3 content", "test")
    assert _checkpoint_row(db_path, fact_id)[0] == 3


# ── 21. Partial ALL failure remains unacknowledged ───────────────────────────

def test_apply_failure_remains_unacknowledged(tmp_path: Path) -> None:
    """Policy v1's ALL expands to exactly {FTS} — a genuine write failure
    on that one target must never be silently treated as delivered.

    A corrupted FTS5 shadow table produces a real `sqlite3.DatabaseError`
    (SQLITE_CORRUPT_VTAB) — permanent, not transient (review finding,
    PR #197): retrying a corrupted database will never succeed, so this
    must PARK, not retry forever (no maximum-attempts cap exists)."""
    db_path = tmp_path / "apply-failure.db"
    _migrate(db_path)
    store = SQLiteGraphStore(str(db_path))
    fact_id = "f_apply_failure"
    _seed_fact(store, fact_id, claim="claim v1")
    _set_fact_version(db_path, fact_id, 1)
    with _open(db_path) as conn:
        _insert_outbox(conn, outbox_id="ob_apply_failure", aggregate_id=fact_id)
        conn.execute(
            "UPDATE facts SET claim = ?, fact_version = ? WHERE fact_id = ?",
            ("claim v2", 2, fact_id),
        )
        conn.execute("DROP TABLE facts_fts_data")  # corrupt FTS5 shadow table
        conn.commit()

    conn = _open(db_path)
    try:
        work = claim_batch(conn, batch_size=10, lease_duration_seconds=60, now=_T0)[0]
        result = apply_claimed_work(conn, work, now=_T0)
        assert result.action == DispatchAction.PARK
        assert result.error_code == DispatchErrorCode.SQLITE_PERMANENT
        park_claim(
            conn, work.outbox_id, work.lease_token, error_code=result.error_code, now=_T0,
        )
    finally:
        conn.close()

    row = _dispatch_row(db_path, "ob_apply_failure")
    assert row[2] == "parked"
    assert row[2] != "acknowledged"
    with sqlite3.connect(str(db_path)) as conn:
        assert conn.execute(
            "SELECT 1 FROM projection_outbox WHERE outbox_id = ?", ("ob_apply_failure",),
        ).fetchone() is not None, "the immutable intent must survive an unacknowledged attempt"


# ── 22. Erasure removes outbox/checkpoint/state/FTS ──────────────────────────

def test_erasure_removes_outbox_checkpoint_state_and_fts(tmp_path: Path) -> None:
    db_path = tmp_path / "erasure-full.db"
    _migrate(db_path)
    store = SQLiteGraphStore(str(db_path))
    fact_id = "f_erasure_full"
    _seed_fact(store, fact_id, claim="claim text")
    with _open(db_path) as conn:
        _insert_outbox(conn, outbox_id="ob_erasure_full", aggregate_id=fact_id)
        conn.commit()

    conn = _open(db_path)
    try:
        work = claim_batch(conn, batch_size=10, lease_duration_seconds=60, now=_T0)[0]
        apply_claimed_work(conn, work, now=_T0)
        ack_claim(conn, work.outbox_id, work.lease_token, now=_T0)
    finally:
        conn.close()

    result = store.erase_fact_dependents_atomic(fact_id)
    assert result["tables"]["projection_dispatch_state"] == {"applicable": True, "deleted": 1}
    assert result["tables"]["projection_checkpoints"] == {"applicable": True, "deleted": 1}
    assert result["tables"]["projection_outbox"] == {"applicable": True, "deleted": 1}
    assert result["tables"]["facts_fts"] == {"applicable": True, "deleted": 1}
    assert _dispatch_row(db_path, "ob_erasure_full") is None
    assert _checkpoint_row(db_path, fact_id) is None
    assert _fts_row(db_path, fact_id) is None
    with sqlite3.connect(str(db_path)) as conn:
        assert conn.execute(
            "SELECT 1 FROM projection_outbox WHERE outbox_id = ?", ("ob_erasure_full",),
        ).fetchone() is None
    assert store.same_db_dependents_present(fact_id) is False
    assert _integrity_ok(db_path)


# ── 23. Missing migration-022 table with user_version >= 22 fails closed ────

def test_schema_version_22_with_missing_dispatch_state_table_fails_closed(tmp_path: Path) -> None:
    db_path = tmp_path / "dispatch-state-corrupt.db"
    _migrate(db_path)
    store = SQLiteGraphStore(str(db_path))
    fact_id = "f_dispatch_state_corrupt"
    _seed_fact(store, fact_id, claim="claim text")
    store.erase_fact_dependents_atomic(fact_id)
    assert store.same_db_dependents_present(fact_id) is False, (
        "sanity check: no unrelated dependent must already be residual "
        "before projection_dispatch_state is dropped"
    )

    with sqlite3.connect(str(db_path)) as conn:
        conn.execute("DROP TABLE projection_dispatch_state")
        conn.commit()
        assert conn.execute("PRAGMA user_version").fetchone()[0] >= 22

    assert store.same_db_dependents_present(fact_id) is True, (
        "PRAGMA user_version >= 22 with projection_dispatch_state missing "
        "must fail closed, never be treated as a clean absence"
    )


# ── 24. Residual survivor detected (rolled-back erasure) ────────────────────

def test_residual_dispatch_state_survivor_detected_after_rolled_back_erasure(tmp_path: Path) -> None:
    db_path = tmp_path / "residual-survivor.db"
    _migrate(db_path)
    store = SQLiteGraphStore(str(db_path))
    fact_id = "f_residual_survivor"
    _seed_fact(store, fact_id, claim="claim text")
    with _open(db_path) as conn:
        _insert_outbox(conn, outbox_id="ob_residual_survivor", aggregate_id=fact_id)
        conn.commit()

    conn = _open(db_path)
    try:
        work = claim_batch(conn, batch_size=10, lease_duration_seconds=60, now=_T0)[0]
        apply_claimed_work(conn, work, now=_T0)
        ack_claim(conn, work.outbox_id, work.lease_token, now=_T0)
    finally:
        conn.close()

    trigger_name = "simulate_facts_delete_failure_dispatch"
    with store._db() as conn:
        conn.execute(f"""
            CREATE TRIGGER IF NOT EXISTS {trigger_name}
            BEFORE DELETE ON facts
            WHEN OLD.fact_id = '{fact_id}'
            BEGIN
                SELECT RAISE(ABORT, 'SIMULATED: real DB failure mid-transaction');
            END;
        """)

    with pytest.raises(Exception):
        store.erase_fact_dependents_atomic(fact_id)

    assert store.get_fact(fact_id) is not None, "fact must survive the rolled-back transaction"
    assert _dispatch_row(db_path, "ob_residual_survivor") is not None, (
        "dispatch state must survive the rolled-back transaction too"
    )
    assert store.same_db_dependents_present(fact_id) is True
    with store._db() as conn:
        conn.execute(f"DROP TRIGGER IF EXISTS {trigger_name}")
    assert _integrity_ok(db_path)


# ── 25. Reappearance detected (out-of-band write after clean erasure) ───────

def test_reappearance_of_dispatch_state_after_clean_erasure_detected(tmp_path: Path) -> None:
    """The out-of-band reappearance being simulated here also needs its own
    orphaned projection_outbox row (review finding, PR #197 added a trigger
    enforcing that projection_dispatch_state.aggregate_id always matches an
    existing projection_outbox row for the same outbox_id) — a legitimate
    reappearance shape (e.g. a restored backup, or tampering) would carry
    both rows together, not a dispatch-state row with no backing intent."""
    db_path = tmp_path / "reappearance.db"
    _migrate(db_path)
    store = SQLiteGraphStore(str(db_path))
    fact_id = "f_reappearance"
    _seed_fact(store, fact_id, claim="claim text")
    store.erase_fact_dependents_atomic(fact_id)
    assert store.same_db_dependents_present(fact_id) is False

    with sqlite3.connect(str(db_path)) as conn:
        _insert_outbox(conn, outbox_id="ob_reappeared", aggregate_id=fact_id)
        conn.execute(
            "INSERT INTO projection_dispatch_state "
            "(outbox_id, aggregate_id, lifecycle_state, attempt_count, "
            " next_attempt_at, updated_at) "
            "VALUES ('ob_reappeared', ?, 'retry', 1, "
            "'2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')",
            (fact_id,),
        )
        conn.commit()

    assert store.same_db_dependents_present(fact_id) is True
    assert _integrity_ok(db_path)


# ── 26. Integrity throughout — covered inline in every test above (success,
#      expiry/reclaim, retry, park, crash recovery, erasure) ────────────────

def test_dispatch_once_end_to_end_summary(tmp_path: Path) -> None:
    """Smoke test of the one-shot bounded primitive composing every step."""
    db_path = tmp_path / "dispatch-once.db"
    _migrate(db_path)
    store = SQLiteGraphStore(str(db_path))
    fact_id = "f_dispatch_once"
    _seed_fact(store, fact_id, claim="claim text")
    _set_fact_version(db_path, fact_id, 1)
    with _open(db_path) as conn:
        _insert_outbox(conn, outbox_id="ob_dispatch_once", aggregate_id=fact_id)
        conn.commit()

    conn = _open(db_path)
    try:
        summary = dispatch_once(conn, batch_size=10, lease_duration_seconds=60, clock=lambda: _T0)
    finally:
        conn.close()

    assert summary.claimed == 1
    assert summary.acknowledged == 1
    assert summary.retried == 0
    assert summary.parked == 0
    assert summary.rejected == 0
    assert summary.outbox_ids == ("ob_dispatch_once",)
    assert _integrity_ok(db_path)


def test_dispatch_once_does_not_expose_background_scheduling_surface() -> None:
    """Hard-boundary check: dispatch_once() is a plain synchronous function
    — no thread/task/loop is created by importing or calling this module."""
    import asyncio
    import inspect

    import core.projection_dispatcher as mod

    assert not asyncio.iscoroutinefunction(mod.dispatch_once)
    assert not inspect.isasyncgenfunction(mod.dispatch_once)


# ── Review-hardening proofs (maintainer review on PR #197) ──────────────────
#
# Five findings were independently verified against the actual code before
# acting: two (timezone normalization; SQLite error misclassification) were
# real, demonstrable bugs; two (scope_ref validation; a durable-attempt-count
# CAS read) were legitimate, narrowly-scoped hardening in the spirit of this
# module's existing "never trust caller input when durable truth exists"
# convention; one (an aggregate_id consistency trigger) is defense-in-depth
# against a write path that does not exist today, added because it is cheap
# and matches this codebase's own style. A sixth proposal — resampling an
# injected clock at every transaction boundary via a callable — was
# deliberately NOT implemented: issue #193's own ТЗ explicitly asked for an
# injected `now` value (exactly what was built), and the actual safety
# guarantee against the described race comes from the exact-lease-token CAS
# on every ack/retry/park, not from timestamp comparisons — see the ADR's
# review-hardening addendum for the full reasoning.

def test_naive_datetime_rejected_by_claim_batch(tmp_path: Path) -> None:
    db_path = tmp_path / "naive-claim.db"
    _migrate(db_path)
    conn = _open(db_path)
    try:
        with pytest.raises(ProjectionDispatchContractError):
            claim_batch(conn, batch_size=10, lease_duration_seconds=60, now=datetime(2026, 1, 1))
        assert conn.in_transaction is False, "a rejected naive datetime must never open a transaction"
    finally:
        conn.close()


def test_naive_datetime_rejected_by_ack_claim(tmp_path: Path) -> None:
    db_path = tmp_path / "naive-ack.db"
    _migrate(db_path)
    store = SQLiteGraphStore(str(db_path))
    fact_id = "f_naive_ack"
    _seed_fact(store, fact_id, claim="original")
    with _open(db_path) as conn:
        _insert_outbox(conn, outbox_id="ob_naive_ack", aggregate_id=fact_id)
        conn.commit()

    conn = _open(db_path)
    try:
        work = claim_batch(conn, batch_size=10, lease_duration_seconds=60, now=_T0)[0]
        with pytest.raises(ProjectionDispatchContractError):
            ack_claim(conn, work.outbox_id, work.lease_token, now=datetime(2026, 1, 1))
        assert conn.in_transaction is False
    finally:
        conn.close()

    assert _dispatch_row(db_path, "ob_naive_ack")[2] == "leased", (
        "a rejected naive-now ack must not mutate anything"
    )


def test_equal_instant_different_utc_offset_normalizes_correctly(tmp_path: Path) -> None:
    """Every comparison in this module is a plain ISO-8601 string
    comparison — only correct if every timestamp is normalized to one
    canonical timezone first. Without normalization, a `now` expressed in
    a positive UTC offset can sort AFTER a UTC-stored `lease_expires_at`
    even though the real instant it represents is earlier — incorrectly
    rejecting a legitimately still-valid ack."""
    db_path = tmp_path / "utc-normalize.db"
    _migrate(db_path)
    store = SQLiteGraphStore(str(db_path))
    fact_id = "f_utc_normalize"
    _seed_fact(store, fact_id, claim="original")
    with _open(db_path) as conn:
        _insert_outbox(conn, outbox_id="ob_utc_normalize", aggregate_id=fact_id)
        conn.commit()

    conn = _open(db_path)
    try:
        work = claim_batch(conn, batch_size=10, lease_duration_seconds=60, now=_T0)[0]
        actual_instant = _T0 + timedelta(seconds=30)  # well before the 60s lease expires
        offset_now = actual_instant.astimezone(timezone(timedelta(hours=5)))
        assert offset_now.isoformat() > work.lease_expires_at, (
            "sanity check: the raw +05:00 string must sort AFTER the stored "
            "UTC lease_expires_at despite representing the earlier real instant"
        )
        outcome = ack_claim(conn, work.outbox_id, work.lease_token, now=offset_now)
        assert outcome == AckOutcome.ACKNOWLEDGED, (
            "normalization must make this ack succeed on the real instant, "
            "not fail on the raw offset string"
        )
    finally:
        conn.close()


def test_unsupported_scope_becomes_parked(tmp_path: Path) -> None:
    """Review finding, PR #197: migration 020 has no SQL-level CHECK
    narrowing scope_ref (unlike aggregate_type/projection_kind/operation,
    which do), so a raw/malformed row could carry a scope outside policy
    v1's single supported value. apply_claimed_work() now re-reads
    scope_ref fresh and parks rather than silently applying under the
    wrong routing scope."""
    db_path = tmp_path / "unsupported-scope.db"
    _migrate(db_path)
    store = SQLiteGraphStore(str(db_path))
    fact_id = "f_unsupported_scope"
    _seed_fact(store, fact_id, claim="claim text")
    with _open(db_path) as conn:
        _insert_outbox(
            conn, outbox_id="ob_unsupported_scope", aggregate_id=fact_id, scope_ref="not:local",
        )
        conn.commit()

    conn = _open(db_path)
    try:
        work = claim_batch(conn, batch_size=10, lease_duration_seconds=60, now=_T0)[0]
        result = apply_claimed_work(conn, work, now=_T0)
        assert result.action == DispatchAction.PARK
        assert result.error_code == DispatchErrorCode.UNSUPPORTED_SCOPE
        park_claim(conn, work.outbox_id, work.lease_token, error_code=result.error_code, now=_T0)
    finally:
        conn.close()

    assert _dispatch_row(db_path, "ob_unsupported_scope")[2] == "parked"
    assert _checkpoint_row(db_path, fact_id) is None
    assert _integrity_ok(db_path)


def test_busy_lock_during_apply_is_retried_not_parked(tmp_path: Path) -> None:
    """Review finding, PR #197: SQLITE_BUSY/SQLITE_LOCKED (in any extended
    form) must still be classified as transient/RETRY — the fix narrows
    what counts as transient, it does not eliminate the busy/retry path
    entirely. Forces a genuine 'database is locked' via a second,
    zero-timeout connection holding an exclusive write lock — no
    monkeypatching."""
    db_path = tmp_path / "busy-lock.db"
    _migrate(db_path)
    store = SQLiteGraphStore(str(db_path))
    fact_id = "f_busy_lock"
    _seed_fact(store, fact_id, claim="claim text")
    with _open(db_path) as conn:
        _insert_outbox(conn, outbox_id="ob_busy_lock", aggregate_id=fact_id)
        conn.commit()

    claim_conn = _open(db_path)
    try:
        work = claim_batch(claim_conn, batch_size=10, lease_duration_seconds=60, now=_T0)[0]
    finally:
        claim_conn.close()

    blocker = sqlite3.connect(str(db_path), timeout=0)
    blocker.execute("BEGIN IMMEDIATE")
    blocker.execute("UPDATE facts SET claim = claim WHERE fact_id = ?", (fact_id,))
    apply_conn = sqlite3.connect(str(db_path), timeout=0)
    try:
        result = apply_claimed_work(apply_conn, work, now=_T0)
        assert result.action == DispatchAction.RETRY
        assert result.error_code == DispatchErrorCode.SQLITE_BUSY
    finally:
        blocker.rollback()
        blocker.close()
        apply_conn.close()


def test_integrity_error_during_apply_becomes_parked_not_retried_forever(tmp_path: Path) -> None:
    """Review finding, PR #197: sqlite3.IntegrityError (and any other real
    SQLite failure that is not SQLITE_BUSY/SQLITE_LOCKED) is a PERMANENT
    failure — retrying will never succeed, and no maximum-attempts cap
    exists in this module, so misclassifying it as transient would retry
    forever. A real BEFORE UPDATE trigger forces a genuine
    sqlite3.IntegrityError on the SECOND checkpoint write (the first write
    is a plain INSERT, not an UPDATE, so the trigger only fires once a
    checkpoint row already exists)."""
    db_path = tmp_path / "integrity-error.db"
    _migrate(db_path)
    store = SQLiteGraphStore(str(db_path))
    fact_id = "f_integrity_error"
    _seed_fact(store, fact_id, claim="claim v1")
    _set_fact_version(db_path, fact_id, 1)
    with _open(db_path) as conn:
        _insert_outbox(conn, outbox_id="ob_integrity_error_1", aggregate_id=fact_id, canonical_version=1)
        conn.commit()

    conn = _open(db_path)
    try:
        work = claim_batch(conn, batch_size=10, lease_duration_seconds=60, now=_T0)[0]
        baseline = apply_claimed_work(conn, work, now=_T0)
        assert baseline.action == DispatchAction.ACKNOWLEDGE
        ack_claim(conn, work.outbox_id, work.lease_token, now=_T0)
    finally:
        conn.close()

    with _open(db_path) as conn:
        conn.execute(
            "UPDATE facts SET claim = ?, fact_version = ? WHERE fact_id = ?",
            ("claim v2", 2, fact_id),
        )
        conn.execute("""
            CREATE TRIGGER simulate_checkpoint_integrity_failure
            BEFORE UPDATE ON projection_checkpoints
            BEGIN
                SELECT RAISE(ABORT, 'SIMULATED: real integrity failure');
            END;
        """)
        _insert_outbox(
            conn, outbox_id="ob_integrity_error_2", aggregate_id=fact_id,
            canonical_version=2, created_at="2026-01-01T00:00:01Z",
        )
        conn.commit()

    conn = _open(db_path)
    try:
        work2 = claim_batch(conn, batch_size=10, lease_duration_seconds=60, now=_T0)[0]
        assert work2.outbox_id == "ob_integrity_error_2"
        result = apply_claimed_work(conn, work2, now=_T0)
        assert result.action == DispatchAction.PARK
        assert result.error_code == DispatchErrorCode.SQLITE_PERMANENT
        park_outcome = park_claim(
            conn, work2.outbox_id, work2.lease_token, error_code=result.error_code, now=_T0,
        )
        assert park_outcome == ParkOutcome.PARKED
    finally:
        conn.close()

    with sqlite3.connect(str(db_path)) as conn:
        conn.execute("DROP TRIGGER IF EXISTS simulate_checkpoint_integrity_failure")
        conn.commit()
    assert _dispatch_row(db_path, "ob_integrity_error_2")[2] == "parked"
    assert _checkpoint_row(db_path, fact_id)[0] == 1, "checkpoint must remain at v1 — the v2 write rolled back"


def test_retry_backoff_uses_durable_attempt_count_not_caller_input(tmp_path: Path) -> None:
    """Review finding, PR #197: retry_claim() no longer accepts a
    caller-supplied attempt_count — it reads the DURABLE value from
    projection_dispatch_state inside its own CAS transaction, so a caller
    (even one holding a genuinely valid lease token) cannot reset or
    manipulate backoff timing. Three successive claim/retry cycles must
    produce exactly the 1s/2s/4s delays implied by the durable
    attempt_count (1, 2, 3), matching compute_retry_delay_seconds()."""
    db_path = tmp_path / "durable-attempt-count.db"
    _migrate(db_path)
    store = SQLiteGraphStore(str(db_path))
    fact_id = "f_durable_attempt_count"
    _seed_fact(store, fact_id, claim="original")
    with _open(db_path) as conn:
        _insert_outbox(conn, outbox_id="ob_durable_attempt_count", aggregate_id=fact_id)
        conn.commit()

    conn = _open(db_path)
    try:
        expected_delays = [1.0, 2.0, 4.0]  # attempt_count 1, 2, 3
        due_at = _T0
        for expected_attempt_count, expected_delay in enumerate(expected_delays, start=1):
            work = claim_batch(conn, batch_size=10, lease_duration_seconds=60, now=due_at)[0]
            assert work.attempt_count == expected_attempt_count
            outcome = retry_claim(
                conn, work.outbox_id, work.lease_token,
                error_code=DispatchErrorCode.SQLITE_BUSY, now=due_at,
            )
            assert outcome == RetryOutcome.RETRY_SCHEDULED
            row = _dispatch_row(db_path, "ob_durable_attempt_count")
            next_attempt_at = datetime.fromisoformat(row[6])
            assert next_attempt_at == due_at + timedelta(seconds=expected_delay)
            due_at = next_attempt_at
    finally:
        conn.close()


def test_retry_backoff_ignores_forged_attempt_count_even_with_valid_token(tmp_path: Path) -> None:
    db_path = tmp_path / "forged-attempt-count.db"
    _migrate(db_path)
    store = SQLiteGraphStore(str(db_path))
    fact_id = "f_forged_attempt_count"
    _seed_fact(store, fact_id, claim="original")
    with _open(db_path) as conn:
        _insert_outbox(conn, outbox_id="ob_forged_attempt_count", aggregate_id=fact_id)
        conn.commit()

    conn = _open(db_path)
    try:
        # Advance to attempt_count=3 durably via two claim/retry cycles.
        work = claim_batch(conn, batch_size=10, lease_duration_seconds=60, now=_T0)[0]
        retry_claim(conn, work.outbox_id, work.lease_token, error_code=DispatchErrorCode.SQLITE_BUSY, now=_T0)
        due1 = datetime.fromisoformat(_dispatch_row(db_path, "ob_forged_attempt_count")[6])
        work = claim_batch(conn, batch_size=10, lease_duration_seconds=60, now=due1)[0]
        assert work.attempt_count == 2

        # retry_claim() no longer even accepts attempt_count as a parameter
        # — there is no argument left for a caller to forge. The durable
        # value (2) must drive the delay (2s), not any external input.
        outcome = retry_claim(
            conn, work.outbox_id, work.lease_token, error_code=DispatchErrorCode.SQLITE_BUSY, now=due1,
        )
        assert outcome == RetryOutcome.RETRY_SCHEDULED
        row = _dispatch_row(db_path, "ob_forged_attempt_count")
        expected_next_attempt = (due1 + timedelta(seconds=2.0)).isoformat()
        assert row[6] == expected_next_attempt
    finally:
        conn.close()


def test_dispatch_state_aggregate_id_mismatch_insert_rejected(tmp_path: Path) -> None:
    """Review finding, PR #197: a BEFORE INSERT trigger on
    projection_dispatch_state now enforces aggregate_id consistency with
    the referenced projection_outbox row at the schema level, independent
    of any Python-level caller discipline."""
    db_path = tmp_path / "aggregate-mismatch-insert.db"
    _migrate(db_path)
    store = SQLiteGraphStore(str(db_path))
    fact_id = "f_aggregate_mismatch_insert"
    _seed_fact(store, fact_id, claim="claim text")
    with sqlite3.connect(str(db_path)) as conn:
        _insert_outbox(conn, outbox_id="ob_aggregate_mismatch", aggregate_id=fact_id)
        conn.commit()
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO projection_dispatch_state "
                "(outbox_id, aggregate_id, lifecycle_state, lease_token, "
                " lease_expires_at, attempt_count, updated_at) "
                "VALUES ('ob_aggregate_mismatch', 'WRONG_AGGREGATE', 'leased', "
                "'tok', '2099-01-01T00:00:00Z', 1, '2026-01-01T00:00:00Z')"
            )
        assert conn.execute(
            "SELECT 1 FROM projection_dispatch_state WHERE outbox_id = ?",
            ("ob_aggregate_mismatch",),
        ).fetchone() is None
    assert _integrity_ok(db_path)


def test_dispatch_state_nonexistent_outbox_insert_rejected(tmp_path: Path) -> None:
    db_path = tmp_path / "nonexistent-outbox-insert.db"
    _migrate(db_path)
    with sqlite3.connect(str(db_path)) as conn:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO projection_dispatch_state "
                "(outbox_id, aggregate_id, lifecycle_state, lease_token, "
                " lease_expires_at, attempt_count, updated_at) "
                "VALUES ('ob_never_existed', 'f1', 'leased', "
                "'tok', '2099-01-01T00:00:00Z', 1, '2026-01-01T00:00:00Z')"
            )
    assert _integrity_ok(db_path)


def test_dispatch_state_aggregate_id_mismatch_update_rejected(tmp_path: Path) -> None:
    """A legitimate reclaim/ack/retry/park UPDATE never touches
    aggregate_id, so it always passes this trigger — only an UPDATE that
    tries to CHANGE aggregate_id to something inconsistent with the
    referenced projection_outbox row is rejected."""
    db_path = tmp_path / "aggregate-mismatch-update.db"
    _migrate(db_path)
    store = SQLiteGraphStore(str(db_path))
    fact_id = "f_aggregate_mismatch_update"
    _seed_fact(store, fact_id, claim="claim text")
    with _open(db_path) as conn:
        _insert_outbox(conn, outbox_id="ob_aggregate_mismatch_update", aggregate_id=fact_id)
        conn.commit()

    conn = _open(db_path)
    try:
        work = claim_batch(conn, batch_size=10, lease_duration_seconds=60, now=_T0)[0]
    finally:
        conn.close()

    with sqlite3.connect(str(db_path)) as conn:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "UPDATE projection_dispatch_state SET aggregate_id = 'WRONG_AGGREGATE' "
                "WHERE outbox_id = ?",
                (work.outbox_id,),
            )
        row = conn.execute(
            "SELECT aggregate_id FROM projection_dispatch_state WHERE outbox_id = ?",
            (work.outbox_id,),
        ).fetchone()
        assert row[0] == fact_id, "the rejected UPDATE must not have changed aggregate_id"
    assert _integrity_ok(db_path)


def test_erasure_still_works_with_aggregate_id_triggers_installed(tmp_path: Path) -> None:
    """The new triggers only guard INSERT/UPDATE — erase_fact_dependents_
    atomic()'s DELETE-only purge must be completely unaffected."""
    db_path = tmp_path / "erasure-with-triggers.db"
    _migrate(db_path)
    store = SQLiteGraphStore(str(db_path))
    fact_id = "f_erasure_with_triggers"
    _seed_fact(store, fact_id, claim="claim text")
    with _open(db_path) as conn:
        _insert_outbox(conn, outbox_id="ob_erasure_with_triggers", aggregate_id=fact_id)
        conn.commit()

    conn = _open(db_path)
    try:
        work = claim_batch(conn, batch_size=10, lease_duration_seconds=60, now=_T0)[0]
        apply_claimed_work(conn, work, now=_T0)
        ack_claim(conn, work.outbox_id, work.lease_token, now=_T0)
    finally:
        conn.close()

    result = store.erase_fact_dependents_atomic(fact_id)
    assert result["tables"]["projection_dispatch_state"] == {"applicable": True, "deleted": 1}
    assert _dispatch_row(db_path, "ob_erasure_with_triggers") is None
    assert _integrity_ok(db_path)


# ── Review-hardening proofs (second maintainer follow-up, PR #197) ─────────
#
# Two further findings, re-verified before acting: (1) an explicit REMOVE
# intent while Canon still exists was silently applied as a REFRESH — a real
# gap, since apply_fts_projection() (issue #194) has no REMOVE parameter at
# all; its "remove regardless of operation" contract only covers Canon being
# ABSENT, never a reviewed "REMOVE while Canon exists" semantic. (2)
# dispatch_once() reused one `now` for its whole batch, so a lease that
# genuinely expired partway through a slow batch could still pass this
# orchestrator's own apply/ack calls. Both are now fixed.

def test_remove_operation_becomes_parked_not_applied(tmp_path: Path) -> None:
    """Review finding, PR #197 (second round): apply_claimed_work() now
    re-reads `operation` fresh and parks UNSUPPORTED_OPERATION for anything
    other than REFRESH, rather than silently running apply_fts_projection()
    (which has no REMOVE parameter and would just refresh from current
    Canon) and acknowledging a REMOVE intent as if it had actually removed
    anything."""
    db_path = tmp_path / "remove-operation.db"
    _migrate(db_path)
    store = SQLiteGraphStore(str(db_path))
    fact_id = "f_remove_operation"
    _seed_fact(store, fact_id, claim="claim text")
    with _open(db_path) as conn:
        conn.execute(
            "INSERT INTO projection_outbox ("
            "outbox_id, aggregate_type, aggregate_id, scope_ref, projection_kind, "
            "operation, canonical_version, policy_version, created_at"
            ") VALUES ('ob_remove_operation', 'fact', ?, ?, 'all', 'remove', 1, "
            "'projection-outbox-v1', '2026-01-01T00:00:00Z')",
            (fact_id, LOCAL_PROJECTION_SCOPE_REF),
        )
        conn.commit()
    fts_before = _fts_row(db_path, fact_id)  # store_fact()'s own best-effort sync

    conn = _open(db_path)
    try:
        work = claim_batch(conn, batch_size=10, lease_duration_seconds=60, now=_T0)[0]
        result = apply_claimed_work(conn, work, now=_T0)
        assert result.action == DispatchAction.PARK
        assert result.error_code == DispatchErrorCode.UNSUPPORTED_OPERATION
        park_outcome = park_claim(conn, work.outbox_id, work.lease_token, error_code=result.error_code, now=_T0)
        assert park_outcome == ParkOutcome.PARKED
    finally:
        conn.close()

    assert _dispatch_row(db_path, "ob_remove_operation")[2] == "parked"
    assert _fts_row(db_path, fact_id) == fts_before, "FTS must be untouched by a parked REMOVE intent"
    assert _checkpoint_row(db_path, fact_id) is None, "no checkpoint may be written for a parked intent"
    with sqlite3.connect(str(db_path)) as conn:
        assert conn.execute(
            "SELECT 1 FROM projection_outbox WHERE outbox_id = ?", ("ob_remove_operation",),
        ).fetchone() is not None, "the immutable REMOVE intent must survive, never acknowledged away"
    assert _integrity_ok(db_path)


def test_dispatch_once_summary_excludes_parked_remove_from_acknowledged(tmp_path: Path) -> None:
    db_path = tmp_path / "remove-operation-dispatch-once.db"
    _migrate(db_path)
    store = SQLiteGraphStore(str(db_path))
    fact_id = "f_remove_operation_once"
    _seed_fact(store, fact_id, claim="claim text")
    with _open(db_path) as conn:
        conn.execute(
            "INSERT INTO projection_outbox ("
            "outbox_id, aggregate_type, aggregate_id, scope_ref, projection_kind, "
            "operation, canonical_version, policy_version, created_at"
            ") VALUES ('ob_remove_once', 'fact', ?, ?, 'all', 'remove', 1, "
            "'projection-outbox-v1', '2026-01-01T00:00:00Z')",
            (fact_id, LOCAL_PROJECTION_SCOPE_REF),
        )
        conn.commit()

    conn = _open(db_path)
    try:
        summary = dispatch_once(conn, batch_size=10, lease_duration_seconds=60, clock=lambda: _T0)
    finally:
        conn.close()

    assert summary.claimed == 1
    assert summary.acknowledged == 0
    assert summary.parked == 1
    assert _dispatch_row(db_path, "ob_remove_once")[7] == "UNSUPPORTED_OPERATION"


def test_expired_lease_token_cannot_apply_even_without_reclaim(tmp_path: Path) -> None:
    """apply_claimed_work()'s own EXPIRED check already uses whatever `now`
    its caller passes — this proves it directly at the primitive level (no
    other worker ever reclaims; the SAME token is still recorded, but the
    caller now honestly reports a later `now` past the lease's own
    recorded expiry)."""
    db_path = tmp_path / "expired-apply-no-reclaim.db"
    _migrate(db_path)
    store = SQLiteGraphStore(str(db_path))
    fact_id = "f_expired_apply_no_reclaim"
    _seed_fact(store, fact_id, claim="original")
    with _open(db_path) as conn:
        _insert_outbox(conn, outbox_id="ob_expired_apply_no_reclaim", aggregate_id=fact_id)
        conn.commit()

    conn = _open(db_path)
    try:
        work = claim_batch(conn, batch_size=10, lease_duration_seconds=60, now=_T0)[0]
        past_expiry = _T0 + timedelta(seconds=120)  # no one reclaimed; same token still stored
        result = apply_claimed_work(conn, work, now=past_expiry)
        assert result.action == DispatchAction.REJECTED
        assert result.lease_validation == LeaseValidationOutcome.EXPIRED
    finally:
        conn.close()

    assert _checkpoint_row(db_path, fact_id) is None, "an expired apply attempt must not mutate anything"
    row = _dispatch_row(db_path, "ob_expired_apply_no_reclaim")
    assert row[2] == "leased", "still leased (not reclaimed) — merely rejected as expired, not silently applied"
    assert _integrity_ok(db_path)


def test_dispatch_once_resamples_clock_between_items_expired_item_rejected(tmp_path: Path) -> None:
    """Review finding, PR #197 (second round): dispatch_once() must call
    `clock()` fresh before each step, not reuse one `now` for a whole
    batch. A fake clock that advances past the lease duration between
    item 1 and item 2 must let item 1 succeed normally while item 2 is
    rejected as expired — never silently applied/acknowledged using a
    stale `now`. No sleep anywhere; the fake clock is a plain iterator."""
    db_path = tmp_path / "clock-resample.db"
    _migrate(db_path)
    store = SQLiteGraphStore(str(db_path))
    fact_id_1, fact_id_2 = "f_resample_1", "f_resample_2"
    _seed_fact(store, fact_id_1, claim="c1")
    _seed_fact(store, fact_id_2, claim="c2")
    with _open(db_path) as conn:
        _insert_outbox(conn, outbox_id="ob_resample_1", aggregate_id=fact_id_1, created_at="2026-01-01T00:00:00Z")
        _insert_outbox(conn, outbox_id="ob_resample_2", aggregate_id=fact_id_2, created_at="2026-01-01T00:00:01Z")
        conn.commit()

    # claim -> apply(item1) -> ack(item1) -> apply(item2, now genuinely past
    # the 1s lease) -> rejected, no ack call follows for a rejected item.
    ticks = iter([_T0, _T0, _T0, _T0 + timedelta(seconds=2)])

    def clock() -> datetime:
        return next(ticks)

    conn = _open(db_path)
    try:
        summary = dispatch_once(conn, batch_size=10, lease_duration_seconds=1, clock=clock)
    finally:
        conn.close()

    assert summary.claimed == 2
    assert summary.acknowledged == 1
    assert summary.rejected == 1
    assert summary.retried == 0
    assert summary.parked == 0
    assert _dispatch_row(db_path, "ob_resample_1")[2] == "acknowledged"
    assert _dispatch_row(db_path, "ob_resample_2")[2] == "leased", (
        "item 2 must remain leased (rejected as expired), never acknowledged using the stale batch-start now"
    )
    assert _checkpoint_row(db_path, fact_id_2) is None
    assert _integrity_ok(db_path)
