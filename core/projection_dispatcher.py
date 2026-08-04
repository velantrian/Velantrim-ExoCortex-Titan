"""Bounded local projection dispatcher with crash recovery (issue #193).

This module is the FIRST reader of `projection_outbox` rows and the first
writer of `projection_dispatch_state` (migration 022). It deliberately owns
no background worker, scheduler, asyncio task, infinite loop, sleep, retry
timer, or network call — `dispatch_once()` is a bounded, single-pass
primitive a caller (today: tests; later, in a separately reviewed change:
server startup wiring) invokes explicitly.

Three units of work, each opening and closing its OWN short SQLite
transaction on a caller-owned connection (never the caller's already-open
transaction — unlike `append_projection_intent_in_transaction()` and
`apply_fts_projection()`, which require one):

  1. ``claim_batch()`` — one bounded, ordered claim of eligible intents.
     Never applies a projection inside its own transaction.
  2. ``apply_claimed_work()`` — validates the lease is still the caller's,
     then applies exactly one projection in a SEPARATE transaction from the
     claim above. Commits FTS/checkpoint mutation, but does NOT touch
     `projection_dispatch_state` — that gap is the crash window between
     "apply committed" and "acknowledged", proven by this file's own
     crash-recovery tests.
  3. ``ack_claim()`` / ``retry_claim()`` / ``park_claim()`` — each a single
     CAS `UPDATE ... WHERE lifecycle_state='leased' AND lease_token=?`,
     rejecting (not silently succeeding) a stale or expired holder.

`dispatch_once()` composes these three steps for one bounded batch and
returns a structured summary. It does not retry within itself, does not
sleep, and does not loop.

At-least-once, not exactly-once: a crash between step 2's commit and step
3's ack leaves the projection already correctly applied but the intent
still `leased` until its lease expires, at which point a later claim will
re-apply it — safe only because `apply_fts_projection()`'s current-Canon,
version-monotonic contract makes every reapply idempotent.
"""

from __future__ import annotations

import secrets
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Final

from core.projection_apply import (
    CanonVersionBehindIntentError,
    ProjectionApplyContractError,
    ProjectionApplyOutcome,
    UnsupportedPolicyTargetError,
    apply_fts_projection,
    resolve_projection_targets,
)
from core.projection_outbox import LOCAL_PROJECTION_SCOPE_REF, ProjectionKind, ProjectionOperation

#: Hard ceiling on how many intents one claim_batch() call may lease at
#: once — a bounded dispatcher never claims an unbounded queue.
MAX_BATCH_SIZE: Final = 100

#: Deterministic bounded exponential backoff (no jitter in v1 — see
#: ADR-2026-08-04-bounded-local-projection-dispatcher.md for why jitter is
#: deferred rather than added speculatively).
BASE_RETRY_SECONDS: Final = 1.0
MAX_RETRY_SECONDS: Final = 300.0
MAX_RETRY_EXPONENT: Final = 9


class ProjectionDispatchContractError(RuntimeError):
    """Raised when a caller violates this module's transaction-ownership
    contract — passing a connection that already has an active transaction
    to a primitive that must own its own short transaction (the inverse of
    core.projection_outbox/core.projection_apply's `conn.in_transaction`
    requirement, since those participate in a CALLER's transaction while
    every primitive here is itself the unit of work)."""


class InvalidBatchSizeError(ValueError):
    """Raised by claim_batch() for batch_size < 1 or > MAX_BATCH_SIZE."""


class DispatchLifecycleState(StrEnum):
    """Closed `projection_dispatch_state.lifecycle_state` values. Absence
    of a row means pending/unclaimed — not a fourth state."""

    LEASED = "leased"
    RETRY = "retry"
    ACKNOWLEDGED = "acknowledged"
    PARKED = "parked"


class DispatchErrorCode(StrEnum):
    """Closed allowlist for `projection_dispatch_state.last_error_code`.
    Never a raw exception message or stack trace — see migrations/
    022_projection_dispatch_state.sql's CHECK constraint, which enforces
    this same closed set at the schema level."""

    FTS_UNAVAILABLE = "FTS_UNAVAILABLE"
    UNSUPPORTED_POLICY_TARGET = "UNSUPPORTED_POLICY_TARGET"
    UNSUPPORTED_SCOPE = "UNSUPPORTED_SCOPE"
    CANON_VERSION_BEHIND_INTENT = "CANON_VERSION_BEHIND_INTENT"
    INTERNAL_CONTRACT = "INTERNAL_CONTRACT"
    SQLITE_BUSY = "SQLITE_BUSY"
    SQLITE_PERMANENT = "SQLITE_PERMANENT"


class DispatchAction(StrEnum):
    """What apply_claimed_work() decided should happen next. REJECTED means
    lease validation itself failed — no projection mutation was attempted,
    and the caller must not ack/retry/park on this holder's behalf."""

    ACKNOWLEDGE = "acknowledge"
    RETRY = "retry"
    PARK = "park"
    REJECTED = "rejected"


class LeaseValidationOutcome(StrEnum):
    """Closed reason set for why apply_claimed_work() did or did not
    proceed to apply a projection."""

    VALID = "valid"
    NOT_LEASED = "not_leased"
    STALE_TOKEN = "stale_token"
    EXPIRED = "expired"
    INTENT_MISSING = "intent_missing"
    AGGREGATE_MISMATCH = "aggregate_mismatch"


class AckOutcome(StrEnum):
    ACKNOWLEDGED = "acknowledged"
    ACK_REJECTED = "ack_rejected"


class RetryOutcome(StrEnum):
    RETRY_SCHEDULED = "retry_scheduled"
    RETRY_REJECTED = "retry_rejected"


class ParkOutcome(StrEnum):
    PARKED = "parked"
    PARK_REJECTED = "park_rejected"


@dataclass(frozen=True, slots=True)
class ClaimedWork:
    """Immutable snapshot of one claimed intent plus this claimer's own
    lease. `aggregate_id` here is read back from `projection_outbox`
    itself (via claim_batch()'s INSERT ... SELECT), never trusted from
    caller input."""

    outbox_id: str
    aggregate_id: str
    scope_ref: str
    projection_kind: ProjectionKind
    operation: ProjectionOperation
    canonical_version: int
    policy_version: str
    lease_token: str
    lease_expires_at: str
    attempt_count: int


@dataclass(frozen=True, slots=True)
class ApplyAttemptResult:
    """Structured outcome of one apply_claimed_work() call. Never carries
    a raw exception message — `error_code` is always a closed
    DispatchErrorCode or None."""

    outbox_id: str
    action: DispatchAction
    error_code: DispatchErrorCode | None
    lease_validation: LeaseValidationOutcome


@dataclass(frozen=True, slots=True)
class DispatchOnceSummary:
    """Structured result of one dispatch_once() call."""

    claimed: int
    acknowledged: int
    retried: int
    parked: int
    rejected: int
    outbox_ids: tuple[str, ...]


def _require_no_active_transaction(conn: sqlite3.Connection) -> None:
    if conn.in_transaction:
        raise ProjectionDispatchContractError(
            "this primitive must own its own short transaction — conn "
            "must not already have an active transaction"
        )


def _normalize_now(now: datetime) -> str:
    """Fail closed on a naive datetime (review finding, PR #197) — a naive
    value could silently be interpreted against the wrong timezone. Every
    comparison in this module is a plain ISO-8601 STRING comparison
    (`lease_expires_at <= now_iso`), which is only correct if every
    timestamp is normalized to one canonical timezone first — two
    datetimes representing the SAME instant under different UTC offsets
    must produce the SAME string, not two lexicographically different
    ones."""
    if now.tzinfo is None or now.utcoffset() is None:
        raise ProjectionDispatchContractError(
            "now must be a timezone-aware datetime — a naive value could "
            "silently be compared against the wrong timezone"
        )
    return now.astimezone(UTC).isoformat()


#: Primary SQLite result codes treated as transient/worth retrying — see
#: _classify_sqlite_failure(). Extended codes (e.g. SQLITE_BUSY_TIMEOUT)
#: reduce to their primary code via `& 0xFF` before this check.
_TRANSIENT_SQLITE_PRIMARY_CODES: Final = frozenset({sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED})


def _classify_sqlite_failure(exc: sqlite3.Error) -> DispatchErrorCode:
    """Classify a real SQLite failure by its primary result code (review
    finding, PR #197) — never by exception class alone (sqlite3.IntegrityError
    and a corrupted-database sqlite3.DatabaseError are NOT
    sqlite3.OperationalError, but were previously funneled into the same
    "transient, retry" bucket) and never by message string-matching
    (locale/wording-fragile). Only SQLITE_BUSY/SQLITE_LOCKED (in any
    extended-code form) are transient and worth retrying — no
    maximum-attempts cap exists in this module, so anything else
    (constraint violations, corruption, missing schema objects, or any
    other DatabaseError) must PARK rather than retry forever."""
    code = getattr(exc, "sqlite_errorcode", None)
    if code is not None and (code & 0xFF) in _TRANSIENT_SQLITE_PRIMARY_CODES:
        return DispatchErrorCode.SQLITE_BUSY
    return DispatchErrorCode.SQLITE_PERMANENT


def compute_retry_delay_seconds(attempt_count: int) -> float:
    """Deterministic bounded exponential backoff, no jitter, no sleep —
    the caller (test or future dispatcher loop) decides what to do with
    the delay. See ADR for why v1 has no maximum-attempts cap: exhaustion
    would need to become PARKED, never silently dropped or delivered, and
    no separate reason to cap has been reviewed yet."""
    if not isinstance(attempt_count, int) or isinstance(attempt_count, bool) or attempt_count < 1:
        raise ValueError("attempt_count must be a positive int")
    return min(
        BASE_RETRY_SECONDS * (2 ** min(attempt_count - 1, MAX_RETRY_EXPONENT)),
        MAX_RETRY_SECONDS,
    )


def claim_batch(
    conn: sqlite3.Connection,
    *,
    batch_size: int,
    lease_duration_seconds: float,
    now: datetime,
) -> tuple[ClaimedWork, ...]:
    """Claim up to `batch_size` eligible `projection_outbox` intents in one
    short, exclusive transaction: intents with no dispatch-state row,
    `retry` rows whose `next_attempt_at <= now`, and `leased` rows whose
    `lease_expires_at <= now` (an expired holder). Never selects
    `acknowledged` or `parked` rows. Ordered strictly by
    `(projection_outbox.created_at, projection_outbox.outbox_id)`.

    Opens and commits its own `BEGIN IMMEDIATE` transaction — `conn` must
    NOT already be in one. Never applies a projection here."""
    _require_no_active_transaction(conn)
    if (
        not isinstance(batch_size, int)
        or isinstance(batch_size, bool)
        or batch_size < 1
        or batch_size > MAX_BATCH_SIZE
    ):
        raise InvalidBatchSizeError(
            f"batch_size must be an int in [1, {MAX_BATCH_SIZE}], got {batch_size!r}"
        )
    if not isinstance(lease_duration_seconds, (int, float)) or isinstance(
        lease_duration_seconds, bool
    ) or lease_duration_seconds <= 0:
        raise ValueError("lease_duration_seconds must be > 0")

    now_iso = _normalize_now(now)
    lease_expires_iso = _normalize_now(now + timedelta(seconds=lease_duration_seconds))

    conn.execute("BEGIN IMMEDIATE")
    try:
        candidates = conn.execute(
            "SELECT po.outbox_id, po.aggregate_id, po.scope_ref, po.projection_kind, "
            "po.operation, po.canonical_version, po.policy_version, "
            "COALESCE(pds.attempt_count, 0) "
            "FROM projection_outbox po "
            "LEFT JOIN projection_dispatch_state pds ON pds.outbox_id = po.outbox_id "
            "WHERE pds.outbox_id IS NULL "
            "   OR (pds.lifecycle_state = 'retry' AND pds.next_attempt_at <= ?) "
            "   OR (pds.lifecycle_state = 'leased' AND pds.lease_expires_at <= ?) "
            "ORDER BY po.created_at, po.outbox_id "
            "LIMIT ?",
            (now_iso, now_iso, batch_size),
        ).fetchall()

        claimed: list[ClaimedWork] = []
        for row in candidates:
            (
                outbox_id, aggregate_id, scope_ref, projection_kind,
                operation, canonical_version, policy_version, prior_attempt_count,
            ) = row
            lease_token = secrets.token_hex(16)
            next_attempt_count = prior_attempt_count + 1
            cur = conn.execute(
                "INSERT INTO projection_dispatch_state "
                "(outbox_id, aggregate_id, lifecycle_state, lease_token, "
                " lease_expires_at, attempt_count, next_attempt_at, "
                " last_error_code, updated_at, acknowledged_at) "
                "SELECT outbox_id, aggregate_id, 'leased', ?, ?, ?, NULL, NULL, ?, NULL "
                "FROM projection_outbox WHERE outbox_id = ? "
                "ON CONFLICT(outbox_id) DO UPDATE SET "
                "  lifecycle_state = 'leased', "
                "  lease_token = excluded.lease_token, "
                "  lease_expires_at = excluded.lease_expires_at, "
                "  attempt_count = excluded.attempt_count, "
                "  next_attempt_at = NULL, "
                "  last_error_code = NULL, "
                "  updated_at = excluded.updated_at, "
                "  acknowledged_at = NULL "
                "WHERE (projection_dispatch_state.lifecycle_state = 'retry' "
                "       AND projection_dispatch_state.next_attempt_at <= ?) "
                "   OR (projection_dispatch_state.lifecycle_state = 'leased' "
                "       AND projection_dispatch_state.lease_expires_at <= ?)",
                (
                    lease_token, lease_expires_iso, next_attempt_count, now_iso,
                    outbox_id, now_iso, now_iso,
                ),
            )
            if cur.rowcount != 1:
                # Defense in depth only: BEGIN IMMEDIATE already fully
                # serializes writers, so this should be unreachable — but
                # this module never trusts lock timing alone (see the rest
                # of this codebase's CAS conventions), so a claim that did
                # not actually take is simply not returned as claimed.
                continue
            claimed.append(
                ClaimedWork(
                    outbox_id=outbox_id,
                    aggregate_id=aggregate_id,
                    scope_ref=scope_ref,
                    projection_kind=ProjectionKind(projection_kind),
                    operation=ProjectionOperation(operation),
                    canonical_version=canonical_version,
                    policy_version=policy_version,
                    lease_token=lease_token,
                    lease_expires_at=lease_expires_iso,
                    attempt_count=next_attempt_count,
                )
            )
    except Exception:
        conn.rollback()
        raise
    conn.commit()
    return tuple(claimed)


def apply_claimed_work(
    conn: sqlite3.Connection, claimed: ClaimedWork, *, now: datetime,
) -> ApplyAttemptResult:
    """Validate this caller's lease is still the exact active holder, then
    apply exactly one FTS projection, in ONE short transaction SEPARATE
    from claim_batch()'s. Never acknowledges, retries, or parks — that is
    the caller's job in a SEPARATE transaction, which is precisely the
    proven crash window between "applied" and "acknowledged"."""
    _require_no_active_transaction(conn)
    now_iso = _normalize_now(now)

    try:
        conn.execute("BEGIN IMMEDIATE")
    except sqlite3.OperationalError as exc:
        code = _classify_sqlite_failure(exc)
        action = DispatchAction.RETRY if code == DispatchErrorCode.SQLITE_BUSY else DispatchAction.PARK
        return ApplyAttemptResult(claimed.outbox_id, action, code, LeaseValidationOutcome.VALID)

    def _reject(outcome: LeaseValidationOutcome) -> ApplyAttemptResult:
        conn.rollback()
        return ApplyAttemptResult(claimed.outbox_id, DispatchAction.REJECTED, None, outcome)

    def _park(error_code: DispatchErrorCode) -> ApplyAttemptResult:
        conn.rollback()
        return ApplyAttemptResult(claimed.outbox_id, DispatchAction.PARK, error_code, LeaseValidationOutcome.VALID)

    def _retry(error_code: DispatchErrorCode) -> ApplyAttemptResult:
        conn.rollback()
        return ApplyAttemptResult(claimed.outbox_id, DispatchAction.RETRY, error_code, LeaseValidationOutcome.VALID)

    try:
        state_row = conn.execute(
            "SELECT lifecycle_state, lease_token, lease_expires_at, aggregate_id "
            "FROM projection_dispatch_state WHERE outbox_id = ?",
            (claimed.outbox_id,),
        ).fetchone()
        if state_row is None:
            return _reject(LeaseValidationOutcome.NOT_LEASED)
        lifecycle_state, lease_token, lease_expires_at, state_aggregate_id = state_row
        if lifecycle_state != DispatchLifecycleState.LEASED.value:
            return _reject(LeaseValidationOutcome.NOT_LEASED)
        if lease_token != claimed.lease_token:
            return _reject(LeaseValidationOutcome.STALE_TOKEN)
        if lease_expires_at is None or lease_expires_at <= now_iso:
            return _reject(LeaseValidationOutcome.EXPIRED)

        intent_row = conn.execute(
            "SELECT aggregate_id, scope_ref FROM projection_outbox WHERE outbox_id = ?",
            (claimed.outbox_id,),
        ).fetchone()
        if intent_row is None:
            return _reject(LeaseValidationOutcome.INTENT_MISSING)
        intent_aggregate_id, intent_scope_ref = intent_row
        if intent_aggregate_id != state_aggregate_id:
            return _reject(LeaseValidationOutcome.AGGREGATE_MISMATCH)
        # Re-read scope_ref fresh (review finding, PR #197): migration 020
        # has no SQL-level CHECK narrowing scope_ref (unlike
        # aggregate_type/projection_kind/operation, which do), so this is
        # the one intent field that a raw/malformed row could carry
        # outside policy v1's single supported value. Fails closed rather
        # than silently applying under the wrong routing scope.
        if intent_scope_ref != LOCAL_PROJECTION_SCOPE_REF:
            return _park(DispatchErrorCode.UNSUPPORTED_SCOPE)

        try:
            # Policy v1 ALL resolves to exactly {FTS} — see
            # core.projection_apply. No other target exists to iterate.
            resolve_projection_targets(claimed.policy_version, claimed.projection_kind)
        except UnsupportedPolicyTargetError:
            return _park(DispatchErrorCode.UNSUPPORTED_POLICY_TARGET)

        try:
            apply_result = apply_fts_projection(
                conn,
                fact_id=intent_aggregate_id,
                intent_canonical_version=claimed.canonical_version,
            )
        except CanonVersionBehindIntentError:
            return _park(DispatchErrorCode.CANON_VERSION_BEHIND_INTENT)
        except ProjectionApplyContractError:
            return _park(DispatchErrorCode.INTERNAL_CONTRACT)
        except sqlite3.Error as exc:
            code = _classify_sqlite_failure(exc)
            return _retry(code) if code == DispatchErrorCode.SQLITE_BUSY else _park(code)
    except Exception:
        conn.rollback()
        raise

    conn.commit()

    if apply_result.outcome in (
        ProjectionApplyOutcome.APPLIED, ProjectionApplyOutcome.MISSING_CANON_REMOVED,
    ):
        return ApplyAttemptResult(
            claimed.outbox_id, DispatchAction.ACKNOWLEDGE, None, LeaseValidationOutcome.VALID,
        )
    # ProjectionApplyOutcome.FTS_UNAVAILABLE
    return ApplyAttemptResult(
        claimed.outbox_id, DispatchAction.PARK, DispatchErrorCode.FTS_UNAVAILABLE,
        LeaseValidationOutcome.VALID,
    )


def ack_claim(
    conn: sqlite3.Connection, outbox_id: str, lease_token: str, *, now: datetime,
) -> AckOutcome:
    """Single CAS acknowledgement: only the exact active, non-expired
    lease holder may ack. A stale or expired token is a structured
    ACK_REJECTED, never treated as success. Never deletes the immutable
    `projection_outbox` intent."""
    _require_no_active_transaction(conn)
    now_iso = _normalize_now(now)
    conn.execute("BEGIN IMMEDIATE")
    try:
        cur = conn.execute(
            "UPDATE projection_dispatch_state "
            "SET lifecycle_state='acknowledged', lease_token=NULL, "
            "    lease_expires_at=NULL, last_error_code=NULL, "
            "    acknowledged_at=?, updated_at=? "
            "WHERE outbox_id=? AND lifecycle_state='leased' "
            "  AND lease_token=? AND lease_expires_at > ?",
            (now_iso, now_iso, outbox_id, lease_token, now_iso),
        )
    except Exception:
        conn.rollback()
        raise
    conn.commit()
    return AckOutcome.ACKNOWLEDGED if cur.rowcount == 1 else AckOutcome.ACK_REJECTED


def retry_claim(
    conn: sqlite3.Connection,
    outbox_id: str,
    lease_token: str,
    *,
    error_code: DispatchErrorCode,
    now: datetime,
) -> RetryOutcome:
    """Single CAS retry transition, by exact ACTIVE (non-expired) lease
    token — the same `lease_expires_at > now` guard as ack_claim(), so an
    expired-but-not-yet-reclaimed holder cannot schedule a retry either.

    The backoff delay is computed from the DURABLE `attempt_count` already
    stored for this row, read inside this same transaction (review
    finding, PR #197) — never from a caller-supplied parameter, so a
    caller cannot reset or manipulate backoff timing even while holding a
    valid lease token. Never sleeps, never uses wall-clock time directly."""
    _require_no_active_transaction(conn)
    now_iso = _normalize_now(now)
    conn.execute("BEGIN IMMEDIATE")
    try:
        row = conn.execute(
            "SELECT attempt_count FROM projection_dispatch_state "
            "WHERE outbox_id=? AND lifecycle_state='leased' AND lease_token=? "
            "  AND lease_expires_at > ?",
            (outbox_id, lease_token, now_iso),
        ).fetchone()
        if row is None:
            conn.rollback()
            return RetryOutcome.RETRY_REJECTED
        delay = compute_retry_delay_seconds(row[0])
        next_attempt_at = _normalize_now(now + timedelta(seconds=delay))
        cur = conn.execute(
            "UPDATE projection_dispatch_state "
            "SET lifecycle_state='retry', lease_token=NULL, lease_expires_at=NULL, "
            "    next_attempt_at=?, last_error_code=?, updated_at=? "
            "WHERE outbox_id=? AND lifecycle_state='leased' AND lease_token=? "
            "  AND lease_expires_at > ?",
            (next_attempt_at, error_code.value, now_iso, outbox_id, lease_token, now_iso),
        )
    except Exception:
        conn.rollback()
        raise
    conn.commit()
    return RetryOutcome.RETRY_SCHEDULED if cur.rowcount == 1 else RetryOutcome.RETRY_REJECTED


def park_claim(
    conn: sqlite3.Connection,
    outbox_id: str,
    lease_token: str,
    *,
    error_code: DispatchErrorCode,
    now: datetime,
) -> ParkOutcome:
    """Single CAS terminal park transition, by exact ACTIVE (non-expired)
    lease token — the same `lease_expires_at > now` guard as ack_claim()
    and retry_claim(). A parked row is never automatically retried — it
    matches none of claim_batch()'s eligibility conditions — and is never
    silently dropped or treated as delivered."""
    _require_no_active_transaction(conn)
    now_iso = _normalize_now(now)
    conn.execute("BEGIN IMMEDIATE")
    try:
        cur = conn.execute(
            "UPDATE projection_dispatch_state "
            "SET lifecycle_state='parked', lease_token=NULL, lease_expires_at=NULL, "
            "    next_attempt_at=NULL, last_error_code=?, updated_at=? "
            "WHERE outbox_id=? AND lifecycle_state='leased' AND lease_token=? "
            "  AND lease_expires_at > ?",
            (error_code.value, now_iso, outbox_id, lease_token, now_iso),
        )
    except Exception:
        conn.rollback()
        raise
    conn.commit()
    return ParkOutcome.PARKED if cur.rowcount == 1 else ParkOutcome.PARK_REJECTED


def dispatch_once(
    conn: sqlite3.Connection,
    *,
    batch_size: int,
    lease_duration_seconds: float,
    now: datetime,
) -> DispatchOnceSummary:
    """Bounded, single-pass dispatch: claim one batch, apply each claim
    separately, ack/retry/park each by structured policy, return a
    structured summary. Does NOT loop, sleep, retry within itself,
    register with any scheduler, spawn a task, or make a network call —
    the caller decides if/when to call this again."""
    claimed = claim_batch(
        conn, batch_size=batch_size, lease_duration_seconds=lease_duration_seconds, now=now,
    )
    acknowledged = retried = parked = rejected = 0
    outbox_ids: list[str] = []

    for work in claimed:
        outbox_ids.append(work.outbox_id)
        result = apply_claimed_work(conn, work, now=now)

        if result.action == DispatchAction.ACKNOWLEDGE:
            ack_outcome = ack_claim(conn, work.outbox_id, work.lease_token, now=now)
            if ack_outcome == AckOutcome.ACKNOWLEDGED:
                acknowledged += 1
            else:
                rejected += 1
        elif result.action == DispatchAction.RETRY:
            assert result.error_code is not None
            retry_outcome = retry_claim(
                conn, work.outbox_id, work.lease_token,
                error_code=result.error_code, now=now,
            )
            if retry_outcome == RetryOutcome.RETRY_SCHEDULED:
                retried += 1
            else:
                rejected += 1
        elif result.action == DispatchAction.PARK:
            assert result.error_code is not None
            park_outcome = park_claim(
                conn, work.outbox_id, work.lease_token, error_code=result.error_code, now=now,
            )
            if park_outcome == ParkOutcome.PARKED:
                parked += 1
            else:
                rejected += 1
        else:
            rejected += 1

    return DispatchOnceSummary(
        claimed=len(claimed),
        acknowledged=acknowledged,
        retried=retried,
        parked=parked,
        rejected=rejected,
        outbox_ids=tuple(outbox_ids),
    )


__all__ = [
    "MAX_BATCH_SIZE",
    "AckOutcome",
    "ApplyAttemptResult",
    "ClaimedWork",
    "DispatchAction",
    "DispatchErrorCode",
    "DispatchLifecycleState",
    "DispatchOnceSummary",
    "InvalidBatchSizeError",
    "LeaseValidationOutcome",
    "ParkOutcome",
    "ProjectionDispatchContractError",
    "RetryOutcome",
    "ack_claim",
    "apply_claimed_work",
    "claim_batch",
    "compute_retry_delay_seconds",
    "dispatch_once",
    "park_claim",
    "retry_claim",
]
