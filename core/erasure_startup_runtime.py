"""Process-local state and health projection for startup erasure recovery.

The actual bounded recovery pass lives in :mod:`core.erasure_startup_runner`.
This module validates hard startup budgets, records exactly one content-free
receipt for the current process, and exposes a fail-closed readiness projection.
It does not register FastAPI routes, lifecycle hooks, schedulers, or workers.
"""

from __future__ import annotations

import os
import threading
from collections.abc import Callable, Mapping
from typing import Any, TypeAlias

from core.erasure_startup_recovery import (
    StartupRecoveryBudget,
    StartupRecoveryFailureReceipt,
    StartupRecoveryReceipt,
)
from core.erasure_startup_runner import run_startup_recovery
from core.runtime_evidence import ObservationState

ERASURE_STARTUP_HEALTH_SCHEMA_VERSION = "titan.erasure-startup-health.v1"

_ENV_MAX_SINGLE = "VELANTRIM_ERASURE_STARTUP_MAX_SINGLE_JOBS"
_ENV_MAX_BATCHES = "VELANTRIM_ERASURE_STARTUP_MAX_BATCHES"
_ENV_TIME_BUDGET_MS = "VELANTRIM_ERASURE_STARTUP_TIME_BUDGET_MS"

_MAX_SINGLE_HARD_CAP = 1_000
_MAX_BATCH_HARD_CAP = 100
_MAX_TIME_BUDGET_MS_HARD_CAP = 60_000

RecoveryReceipt: TypeAlias = StartupRecoveryReceipt | StartupRecoveryFailureReceipt
RecoveryExecutor: TypeAlias = Callable[[StartupRecoveryBudget], RecoveryReceipt]

_state_lock = threading.RLock()
_latest_receipt: RecoveryReceipt | None = None


def _parse_bounded_int(
    environ: Mapping[str, str],
    key: str,
    *,
    default: int,
    minimum: int,
    maximum: int,
) -> int:
    raw = str(environ.get(key, str(default))).strip()
    if not raw:
        raise ValueError(f"{key} must be an integer in [{minimum}, {maximum}]")
    try:
        value = int(raw, 10)
    except ValueError as exc:
        raise ValueError(
            f"{key} must be an integer in [{minimum}, {maximum}]"
        ) from exc
    if value < minimum or value > maximum:
        raise ValueError(f"{key} must be in [{minimum}, {maximum}]")
    return value


def load_startup_recovery_budget(
    environ: Mapping[str, str] | None = None,
) -> StartupRecoveryBudget:
    """Load a bounded budget from environment without silent fallback.

    Invalid explicit values raise before recovery starts. This prevents a typo
    from disabling a domain or expanding startup work beyond reviewed caps.
    """

    source = os.environ if environ is None else environ
    max_single_jobs = _parse_bounded_int(
        source,
        _ENV_MAX_SINGLE,
        default=25,
        minimum=0,
        maximum=_MAX_SINGLE_HARD_CAP,
    )
    max_batches = _parse_bounded_int(
        source,
        _ENV_MAX_BATCHES,
        default=5,
        minimum=0,
        maximum=_MAX_BATCH_HARD_CAP,
    )
    time_budget_ms = _parse_bounded_int(
        source,
        _ENV_TIME_BUDGET_MS,
        default=5_000,
        minimum=1,
        maximum=_MAX_TIME_BUDGET_MS_HARD_CAP,
    )
    return StartupRecoveryBudget(
        max_single_jobs=max_single_jobs,
        max_batches=max_batches,
        time_budget_ms=time_budget_ms,
    )


def record_startup_recovery_receipt(receipt: RecoveryReceipt) -> RecoveryReceipt:
    if not isinstance(receipt, (StartupRecoveryReceipt, StartupRecoveryFailureReceipt)):
        raise TypeError("receipt must be a startup recovery receipt")
    global _latest_receipt
    with _state_lock:
        _latest_receipt = receipt
    return receipt


def execute_and_record_startup_recovery(
    budget: StartupRecoveryBudget | None = None,
    *,
    executor: RecoveryExecutor = run_startup_recovery,
) -> RecoveryReceipt:
    active_budget = budget or load_startup_recovery_budget()
    receipt = executor(active_budget)
    return record_startup_recovery_receipt(receipt)


def get_startup_recovery_receipt() -> RecoveryReceipt | None:
    with _state_lock:
        return _latest_receipt


def get_startup_recovery_health() -> dict[str, Any]:
    """Return a content-free readiness projection for the current process."""

    receipt = get_startup_recovery_receipt()
    if receipt is None:
        return {
            "schema_version": ERASURE_STARTUP_HEALTH_SCHEMA_VERSION,
            "status": "not_observed",
            "ready": False,
            "http_status": 503,
            "observation_state": ObservationState.NOT_OBSERVED.value,
            "reason_code": "startup_recovery_not_run",
            "receipt": None,
        }

    if isinstance(receipt, StartupRecoveryFailureReceipt):
        return {
            "schema_version": ERASURE_STARTUP_HEALTH_SCHEMA_VERSION,
            "status": "observer_failed",
            "ready": False,
            "http_status": 503,
            "observation_state": receipt.observation.state.value,
            "reason_code": receipt.error_code,
            "receipt": receipt.to_dict(),
        }

    state = receipt.observation.state
    if state is ObservationState.OBSERVED_ZERO:
        status = "clean"
        ready = True
        http_status = 200
    elif state is ObservationState.OBSERVED_NONZERO:
        status = "degraded"
        ready = False
        http_status = 503
    else:
        status = "observer_failed"
        ready = False
        http_status = 503

    return {
        "schema_version": ERASURE_STARTUP_HEALTH_SCHEMA_VERSION,
        "status": status,
        "ready": ready,
        "http_status": http_status,
        "observation_state": state.value,
        "reason_code": receipt.observation.reason_code,
        "receipt": receipt.to_dict(),
    }


def startup_recovery_http_status() -> int:
    return int(get_startup_recovery_health()["http_status"])


def _reset_startup_recovery_state_for_tests() -> None:
    global _latest_receipt
    with _state_lock:
        _latest_receipt = None


__all__ = [
    "ERASURE_STARTUP_HEALTH_SCHEMA_VERSION",
    "execute_and_record_startup_recovery",
    "get_startup_recovery_health",
    "get_startup_recovery_receipt",
    "load_startup_recovery_budget",
    "record_startup_recovery_receipt",
    "startup_recovery_http_status",
]
