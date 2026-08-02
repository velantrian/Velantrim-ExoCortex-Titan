"""Bounded startup adapter over the durable batch-erasure coordinator.

The adapter bounds candidate selection and the shared monotonic execution
window. It does not duplicate batch claims, lease heartbeats, fencing tokens,
item ownership, per-fact erasure, finalization, or compliance logic; all of
those remain owned by ``BatchErasureCoordinator``.
"""

from __future__ import annotations

import time
from typing import Callable

import core.erasure_batch_coordinator as batch_module
from core.erasure_batch_coordinator import (
    COMPLETE,
    COMPLETE_WITH_RESIDUAL,
    CRITICAL_COMPLIANCE_VIOLATION,
    FAILED,
    PARTIAL,
    PENDING,
    RUNNING,
    SUBJECT_CONFLICT,
    BatchErasureCoordinator,
    get_batch_coordinator,
)
from core.erasure_bounded_recovery import _clock_now, _validate_finite_number
from core.erasure_startup_recovery import RecoveryDomain, RecoveryDomainReceipt


_BATCH_PARTIAL_OUTCOMES = {PARTIAL, COMPLETE_WITH_RESIDUAL}


def _validate_max_batches(max_batches: int) -> int:
    if (
        isinstance(max_batches, bool)
        or not isinstance(max_batches, int)
        or max_batches < 0
    ):
        raise ValueError("max_batches must be a non-negative integer")
    return max_batches


def _select_batch_candidates_bounded(
    coordinator: BatchErasureCoordinator,
    max_batches: int,
) -> list[tuple[str, bool]]:
    """Select a bounded, deterministic, category-aware candidate window.

    Stale-terminal candidates receive the first slot because a successful
    reconciliation permanently moves them out of that bounded category. If
    ordinary work also exists, it receives the next slot. Remaining capacity
    alternates between the two ordered streams. Duplicate IDs are removed.

    With a one-item budget, no stateless selector can prove starvation freedom
    for both non-empty categories. The default startup budget is larger; a
    durable cross-run fairness cursor, if later required by evidence, belongs
    in a separate reviewed contract rather than being implied here.
    """

    if max_batches == 0:
        return []

    now = batch_module._now()
    terminal = batch_module._TERMINAL_BATCH_STATUSES
    retryable_items = batch_module._ITEM_RETRYABLE_STATUSES
    stale_limit = min(max_batches, batch_module._RECOVERY_SWEEP_LIMIT)

    with coordinator._jobs_db() as conn:
        ordinary_rows = conn.execute(
            "SELECT batch_id FROM erasure_batches WHERE "
            "status IN (?, ?, ?) OR "
            "(status = ? AND lease_expires_at IS NOT NULL "
            "AND lease_expires_at < ?) "
            "ORDER BY created_at, batch_id LIMIT ?",
            (PENDING, PARTIAL, FAILED, RUNNING, now, max_batches),
        ).fetchall()
        stale_rows = conn.execute(
            "SELECT batch_id FROM erasure_batches AS b WHERE "
            "status IN (?, ?, ?) AND EXISTS ("
            "  SELECT 1 FROM erasure_batch_items AS i "
            "  WHERE i.batch_id = b.batch_id AND i.status IN (?, ?, ?)"
            ") ORDER BY created_at, batch_id LIMIT ?",
            (*terminal, *retryable_items, stale_limit),
        ).fetchall()

    streams = (
        [(str(row["batch_id"]), True) for row in stale_rows],
        [(str(row["batch_id"]), False) for row in ordinary_rows],
    )
    offsets = [0, 0]
    selected: list[tuple[str, bool]] = []
    seen: set[str] = set()

    while len(selected) < max_batches:
        progressed = False
        for index, stream in enumerate(streams):
            while offsets[index] < len(stream):
                candidate = stream[offsets[index]]
                offsets[index] += 1
                if candidate[0] in seen:
                    continue
                seen.add(candidate[0])
                selected.append(candidate)
                progressed = True
                break
            if len(selected) >= max_batches:
                break
        if not progressed:
            break
    return selected


def _remaining_batch_backlog(
    coordinator: BatchErasureCoordinator,
    accounted_ids: list[str],
) -> int:
    terminal = batch_module._TERMINAL_BATCH_STATUSES
    retryable_items = batch_module._ITEM_RETRYABLE_STATUSES
    now = batch_module._now()
    excluded_sql = ""
    excluded_params: tuple[str, ...] = ()
    if accounted_ids:
        placeholders = ", ".join("?" for _ in accounted_ids)
        excluded_sql = f" AND b.batch_id NOT IN ({placeholders})"
        excluded_params = tuple(accounted_ids)

    with coordinator._jobs_db() as conn:
        row = conn.execute(
            "SELECT COUNT(DISTINCT b.batch_id) AS count "
            "FROM erasure_batches AS b WHERE ("
            "  b.status IN (?, ?, ?) OR "
            "  (b.status = ? AND b.lease_expires_at IS NOT NULL "
            "   AND b.lease_expires_at < ?) OR "
            "  (b.status IN (?, ?, ?) AND EXISTS ("
            "    SELECT 1 FROM erasure_batch_items AS i "
            "    WHERE i.batch_id = b.batch_id AND i.status IN (?, ?, ?)"
            "  ))"
            f"){excluded_sql}",  # noqa: S608
            (
                PENDING,
                PARTIAL,
                FAILED,
                RUNNING,
                now,
                *terminal,
                *retryable_items,
                *excluded_params,
            ),
        ).fetchone()
    return int(row["count"] if row is not None else 0)


def resume_batch_jobs_bounded(
    *,
    max_batches: int,
    deadline_monotonic: float,
    monotonic: Callable[[], float] = time.monotonic,
    coordinator: BatchErasureCoordinator | None = None,
) -> tuple[RecoveryDomainReceipt, bool]:
    """Recover a bounded category-aware window of durable batch jobs."""

    limit = _validate_max_batches(max_batches)
    deadline = _validate_finite_number(deadline_monotonic, "deadline_monotonic")
    active = coordinator or get_batch_coordinator()
    candidates = _select_batch_candidates_bounded(active, limit)

    attempted = 0
    completed = 0
    partial = 0
    failed = 0
    skipped = 0
    accounted_ids: list[str] = []
    error_codes: set[str] = set()
    stopped_by_time_budget = False

    for batch_id, needs_reconcile in candidates:
        if _clock_now(monotonic) >= deadline:
            stopped_by_time_budget = True
            break

        attempted += 1
        if needs_reconcile:
            active._report(
                active._load_batch(batch_id),
                active._load_items(batch_id),
            )
        result = active._run_batch(batch_id, wait_if_running=False)
        if result is None:
            skipped += 1
            continue

        outcome = str(result.get("outcome") or "")
        critical = bool(result.get("critical_compliance_violation")) or (
            result.get("compliance_status") == CRITICAL_COMPLIANCE_VIOLATION
        )
        if critical:
            failed += 1
            error_codes.add("batch_compliance_violation")
        elif outcome == COMPLETE and result.get("success") is True:
            completed += 1
        elif outcome == COMPLETE:
            failed += 1
            error_codes.add("batch_terminal_incomplete")
        elif outcome in _BATCH_PARTIAL_OUTCOMES:
            partial += 1
        elif outcome == FAILED:
            failed += 1
            error_codes.add("batch_recovery_failed")
        elif outcome == SUBJECT_CONFLICT:
            failed += 1
            error_codes.add("batch_subject_conflict")
        else:
            raise ValueError(f"unsupported batch recovery outcome: {outcome!r}")
        accounted_ids.append(batch_id)

    durable_backlog = _remaining_batch_backlog(active, accounted_ids)
    selected_but_unattempted = len(candidates) - attempted
    remaining_backlog = max(durable_backlog, selected_but_unattempted)
    receipt = RecoveryDomainReceipt(
        domain=RecoveryDomain.BATCH,
        selected=len(candidates),
        attempted=attempted,
        completed=completed,
        partial=partial,
        failed=failed,
        skipped=skipped,
        remaining_backlog=remaining_backlog,
        error_codes=tuple(sorted(error_codes)),
    )
    return receipt, stopped_by_time_budget


__all__ = ["resume_batch_jobs_bounded"]
