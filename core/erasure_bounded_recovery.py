"""Bounded adapters over Titan's existing durable erasure coordinators.

This module adds no scheduler, worker, deletion policy, or new erasure state. It
reuses the existing single-fact coordinator's tombstone reconciliation and CAS
claim paths while bounding the initial candidate prefix and shared monotonic
execution window. Batch recovery and FastAPI lifespan wiring are separate
increments.
"""

from __future__ import annotations

import math
import time
from typing import Callable

from core.erasure_coordinator import (
    COMPLETE,
    FAILED,
    PARTIAL,
    RESIDUAL_IMMUTABLE_DATA,
    ErasureCoordinator,
    _RESUMABLE_STATUSES,
    get_coordinator,
)
from core.erasure_startup_recovery import RecoveryDomain, RecoveryDomainReceipt


_SINGLE_PARTIAL_OUTCOMES = {PARTIAL, RESIDUAL_IMMUTABLE_DATA}


def _validate_max_jobs(max_jobs: int) -> int:
    if isinstance(max_jobs, bool) or not isinstance(max_jobs, int) or max_jobs < 0:
        raise ValueError("max_jobs must be a non-negative integer")
    return max_jobs


def _validate_finite_number(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite number")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{name} must be a finite number")
    return number


def _clock_now(monotonic: Callable[[], float]) -> float:
    return _validate_finite_number(monotonic(), "monotonic clock result")


def _select_resumable_job_ids(
    coordinator: ErasureCoordinator,
    max_jobs: int,
) -> list[str]:
    with coordinator._jobs_db() as conn:
        placeholders = ", ".join("?" for _ in _RESUMABLE_STATUSES)
        rows = conn.execute(
            f"SELECT job_id FROM erasure_jobs "  # noqa: S608
            f"WHERE status IN ({placeholders}) "
            "ORDER BY created_at, job_id LIMIT ?",
            (*_RESUMABLE_STATUSES, max_jobs),
        ).fetchall()
    return [str(row["job_id"]) for row in rows]


def _remaining_resumable_count(
    coordinator: ErasureCoordinator,
    accounted_ids: list[str],
) -> int:
    with coordinator._jobs_db() as conn:
        status_placeholders = ", ".join("?" for _ in _RESUMABLE_STATUSES)
        if accounted_ids:
            id_placeholders = ", ".join("?" for _ in accounted_ids)
            row = conn.execute(
                f"SELECT COUNT(*) AS count FROM erasure_jobs "  # noqa: S608
                f"WHERE status IN ({status_placeholders}) "
                f"AND job_id NOT IN ({id_placeholders})",
                (*_RESUMABLE_STATUSES, *accounted_ids),
            ).fetchone()
        else:
            row = conn.execute(
                f"SELECT COUNT(*) AS count FROM erasure_jobs "  # noqa: S608
                f"WHERE status IN ({status_placeholders})",
                _RESUMABLE_STATUSES,
            ).fetchone()
    return int(row["count"] if row is not None else 0)


def resume_single_fact_jobs_bounded(
    *,
    max_jobs: int,
    deadline_monotonic: float,
    monotonic: Callable[[], float] = time.monotonic,
    coordinator: ErasureCoordinator | None = None,
) -> tuple[RecoveryDomainReceipt, bool]:
    """Recover a deterministic bounded prefix of resumable single-fact jobs.

    Unexpected database, schema, clock, or outcome-contract failures propagate.
    The later aggregate startup runner is responsible for converting those
    failures into ``StartupRecoveryFailureReceipt`` rather than manufacturing
    measured counters.
    """

    limit = _validate_max_jobs(max_jobs)
    deadline = _validate_finite_number(deadline_monotonic, "deadline_monotonic")
    active = coordinator or get_coordinator()
    selected_ids = _select_resumable_job_ids(active, limit)

    attempted = 0
    completed = 0
    partial = 0
    failed = 0
    skipped = 0
    accounted_ids: list[str] = []
    stopped_by_time_budget = False

    for job_id in selected_ids:
        if _clock_now(monotonic) >= deadline:
            stopped_by_time_budget = True
            break

        attempted += 1
        reconciled = active._reconcile_completed_job_from_tombstone(job_id)
        result = (
            reconciled
            if reconciled is not None
            else active._run_job(job_id, wait_if_running=False)
        )
        if result is None:
            skipped += 1
            continue

        outcome = str(result.get("outcome") or "")
        if outcome == COMPLETE:
            completed += 1
        elif outcome == FAILED:
            failed += 1
        elif outcome in _SINGLE_PARTIAL_OUTCOMES:
            partial += 1
        else:
            raise ValueError(f"unsupported single-fact recovery outcome: {outcome!r}")
        accounted_ids.append(job_id)

    durable_backlog = _remaining_resumable_count(active, accounted_ids)
    selected_but_unattempted = len(selected_ids) - attempted
    remaining_backlog = max(durable_backlog, selected_but_unattempted)
    error_codes = ("single_fact_recovery_failed",) if failed > 0 else ()

    receipt = RecoveryDomainReceipt(
        domain=RecoveryDomain.SINGLE_FACT,
        selected=len(selected_ids),
        attempted=attempted,
        completed=completed,
        partial=partial,
        failed=failed,
        skipped=skipped,
        remaining_backlog=remaining_backlog,
        error_codes=error_codes,
    )
    return receipt, stopped_by_time_budget


__all__ = ["resume_single_fact_jobs_bounded"]
