"""Aggregate one bounded GDPR erasure recovery pass at application startup.

This module is synchronous by design. FastAPI lifespan wiring is a separate
increment and must invoke :func:`run_startup_recovery` through one awaited
``asyncio.to_thread`` call after migrations. No scheduler, recurring worker,
Canon write, or user-visible action is registered here.
"""

from __future__ import annotations

import logging
import sqlite3
import time
import uuid
from datetime import datetime, timezone
from typing import Callable

from core.erasure_batch_coordinator import BatchErasureCoordinator
from core.erasure_bounded_batch_recovery import resume_batch_jobs_bounded
from core.erasure_bounded_recovery import (
    _clock_now,
    resume_single_fact_jobs_bounded,
)
from core.erasure_coordinator import ErasureCoordinator
from core.erasure_startup_recovery import (
    ErasureStartupRecoveryError,
    RecoveryDomain,
    RecoveryDomainReceipt,
    StartupRecoveryBudget,
    StartupRecoveryFailureReceipt,
    StartupRecoveryReceipt,
)

logger = logging.getLogger("velantrim.erasure_startup")

RecoveryRunner = Callable[..., tuple[RecoveryDomainReceipt, bool]]
WallClock = Callable[[], datetime]
RunIdFactory = Callable[[], str]


def _default_run_id() -> str:
    return f"esr_{uuid.uuid4().hex[:20]}"


def _utc_iso(value: datetime) -> str:
    if not isinstance(value, datetime):
        raise ValueError("wall clock must return datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("wall clock must return timezone-aware datetime")
    return value.astimezone(timezone.utc).isoformat()


def _safe_wall_time(now_utc: WallClock) -> tuple[str, str | None]:
    """Return a UTC timestamp and an optional typed failure code.

    A broken injected wall clock must not prevent creation of a truthful
    failure receipt. The fallback uses the process wall clock only for receipt
    timing; it never changes recovery outcomes or hides the failure code.
    """

    try:
        return _utc_iso(now_utc()), None
    except Exception:  # noqa: BLE001 - converted to a typed, content-free code
        logger.exception("startup erasure recovery wall clock failed")
        return datetime.now(timezone.utc).isoformat(), "startup_wall_clock_failed"


def _empty_domain_receipt(domain: RecoveryDomain) -> RecoveryDomainReceipt:
    return RecoveryDomainReceipt(
        domain=domain,
        selected=0,
        attempted=0,
        completed=0,
        partial=0,
        failed=0,
        skipped=0,
        remaining_backlog=0,
    )


def _failure_code(phase: str, exc: Exception) -> str:
    if isinstance(exc, sqlite3.DatabaseError):
        return f"{phase}_database_failed"
    if isinstance(exc, (ErasureStartupRecoveryError, ValueError, TypeError)):
        return f"{phase}_contract_failed"
    return f"{phase}_observer_failed"


def run_startup_recovery(
    budget: StartupRecoveryBudget,
    *,
    monotonic: Callable[[], float] = time.monotonic,
    now_utc: WallClock = lambda: datetime.now(timezone.utc),
    run_id_factory: RunIdFactory = _default_run_id,
    single_coordinator: ErasureCoordinator | None = None,
    batch_coordinator: BatchErasureCoordinator | None = None,
    single_runner: RecoveryRunner = resume_single_fact_jobs_bounded,
    batch_runner: RecoveryRunner = resume_batch_jobs_bounded,
) -> StartupRecoveryReceipt | StartupRecoveryFailureReceipt:
    """Run one count- and time-bounded recovery sweep.

    Both domains receive one absolute monotonic deadline. Single-fact recovery
    runs first; batch recovery still performs its bounded candidate observation
    when the execution deadline is already exhausted, so selected-but-unattempted
    batch work remains visible instead of disappearing from the receipt.

    Any schema/database/clock/contract failure returns
    :class:`StartupRecoveryFailureReceipt`. Exception messages, paths, SQL and
    payload fragments are logged only to protected server logs and are never
    copied into the receipt.
    """

    if not isinstance(budget, StartupRecoveryBudget):
        raise TypeError("budget must be StartupRecoveryBudget")

    run_id = str(run_id_factory()).strip()
    started_at, wall_clock_error = _safe_wall_time(now_utc)
    if wall_clock_error is not None:
        return StartupRecoveryFailureReceipt(
            run_id=run_id or "esr_wall_clock_failure",
            started_at_utc=started_at,
            failed_at_utc=started_at,
            budget=budget,
            error_code=wall_clock_error,
        )

    phase = "startup_clock"
    try:
        started_monotonic = _clock_now(monotonic)
        deadline = started_monotonic + (budget.time_budget_ms / 1_000.0)

        phase = "single_fact"
        if budget.max_single_jobs > 0:
            single_receipt, single_stopped = single_runner(
                max_jobs=budget.max_single_jobs,
                deadline_monotonic=deadline,
                monotonic=monotonic,
                coordinator=single_coordinator,
            )
        else:
            single_receipt = _empty_domain_receipt(RecoveryDomain.SINGLE_FACT)
            single_stopped = False

        phase = "batch"
        if budget.max_batches > 0:
            batch_receipt, batch_stopped = batch_runner(
                max_batches=budget.max_batches,
                deadline_monotonic=deadline,
                monotonic=monotonic,
                coordinator=batch_coordinator,
            )
        else:
            batch_receipt = _empty_domain_receipt(RecoveryDomain.BATCH)
            batch_stopped = False

        phase = "aggregate"
        completed_at, completion_clock_error = _safe_wall_time(now_utc)
        if completion_clock_error is not None:
            raise ValueError(completion_clock_error)

        return StartupRecoveryReceipt(
            run_id=run_id,
            started_at_utc=started_at,
            completed_at_utc=completed_at,
            budget=budget,
            single_fact=single_receipt,
            batch=batch_receipt,
            stopped_by_time_budget=single_stopped or batch_stopped,
            persisted=False,
            storage_ref=None,
        )
    except Exception as exc:  # noqa: BLE001 - converted to typed failure evidence
        logger.exception("startup erasure recovery failed during phase=%s", phase)
        failed_at, _ = _safe_wall_time(now_utc)
        return StartupRecoveryFailureReceipt(
            run_id=run_id or "esr_startup_failure",
            started_at_utc=started_at,
            failed_at_utc=failed_at,
            budget=budget,
            error_code=_failure_code(phase, exc),
            persisted=False,
            storage_ref=None,
        )


__all__ = ["run_startup_recovery"]
