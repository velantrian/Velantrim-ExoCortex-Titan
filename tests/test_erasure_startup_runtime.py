"""Tests for startup recovery budget parsing and health projection."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

import core.erasure_startup_runtime as runtime
from core.erasure_startup_recovery import (
    ErasureStartupRecoveryError,
    RecoveryDomain,
    RecoveryDomainReceipt,
    StartupRecoveryBudget,
    StartupRecoveryFailureReceipt,
    StartupRecoveryReceipt,
)
from core.runtime_evidence import ObservationState


@pytest.fixture(autouse=True)
def reset_runtime_state():
    runtime._reset_startup_recovery_state_for_tests()
    yield
    runtime._reset_startup_recovery_state_for_tests()


def _domain(
    domain: RecoveryDomain,
    *,
    partial: int = 0,
    failed: int = 0,
    backlog: int = 0,
    error_codes: tuple[str, ...] = (),
) -> RecoveryDomainReceipt:
    attempted = partial + failed
    return RecoveryDomainReceipt(
        domain=domain,
        selected=attempted,
        attempted=attempted,
        completed=0,
        partial=partial,
        failed=failed,
        skipped=0,
        remaining_backlog=backlog,
        error_codes=error_codes,
    )


def _measured_receipt(*, backlog: int = 0) -> StartupRecoveryReceipt:
    now = datetime(2026, 8, 2, 12, 0, tzinfo=timezone.utc).isoformat()
    return StartupRecoveryReceipt(
        run_id="esr_runtime_test",
        started_at_utc=now,
        completed_at_utc=now,
        budget=StartupRecoveryBudget(
            max_single_jobs=25,
            max_batches=5,
            time_budget_ms=5_000,
        ),
        single_fact=_domain(RecoveryDomain.SINGLE_FACT, backlog=backlog),
        batch=_domain(RecoveryDomain.BATCH),
        stopped_by_time_budget=backlog > 0,
    )


def _failure_receipt() -> StartupRecoveryFailureReceipt:
    now = datetime(2026, 8, 2, 12, 0, tzinfo=timezone.utc).isoformat()
    return StartupRecoveryFailureReceipt(
        run_id="esr_runtime_failure",
        started_at_utc=now,
        failed_at_utc=now,
        budget=StartupRecoveryBudget(
            max_single_jobs=25,
            max_batches=5,
            time_budget_ms=5_000,
        ),
        error_code="single_fact_database_failed",
    )


def test_default_budget_is_bounded() -> None:
    budget = runtime.load_startup_recovery_budget({})
    assert budget.max_single_jobs == 25
    assert budget.max_batches == 5
    assert budget.time_budget_ms == 5_000


def test_explicit_budget_values_are_loaded() -> None:
    budget = runtime.load_startup_recovery_budget(
        {
            "VELANTRIM_ERASURE_STARTUP_MAX_SINGLE_JOBS": "12",
            "VELANTRIM_ERASURE_STARTUP_MAX_BATCHES": "3",
            "VELANTRIM_ERASURE_STARTUP_TIME_BUDGET_MS": "2500",
        }
    )
    assert budget == StartupRecoveryBudget(
        max_single_jobs=12,
        max_batches=3,
        time_budget_ms=2_500,
    )


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("VELANTRIM_ERASURE_STARTUP_MAX_SINGLE_JOBS", "not-an-int"),
        ("VELANTRIM_ERASURE_STARTUP_MAX_SINGLE_JOBS", "1001"),
        ("VELANTRIM_ERASURE_STARTUP_MAX_BATCHES", "101"),
        ("VELANTRIM_ERASURE_STARTUP_TIME_BUDGET_MS", "0"),
        ("VELANTRIM_ERASURE_STARTUP_TIME_BUDGET_MS", "60001"),
    ],
)
def test_invalid_explicit_budget_does_not_silently_fallback(key: str, value: str) -> None:
    with pytest.raises(ValueError, match=key):
        runtime.load_startup_recovery_budget({key: value})


def test_both_domains_cannot_be_disabled() -> None:
    with pytest.raises(ErasureStartupRecoveryError, match="at least one recovery domain"):
        runtime.load_startup_recovery_budget(
            {
                "VELANTRIM_ERASURE_STARTUP_MAX_SINGLE_JOBS": "0",
                "VELANTRIM_ERASURE_STARTUP_MAX_BATCHES": "0",
            }
        )


def test_health_is_not_observed_before_startup_run() -> None:
    health = runtime.get_startup_recovery_health()
    assert health["status"] == "not_observed"
    assert health["ready"] is False
    assert health["http_status"] == 503
    assert health["observation_state"] == ObservationState.NOT_OBSERVED.value
    assert health["receipt"] is None


def test_clean_receipt_is_ready() -> None:
    runtime.record_startup_recovery_receipt(_measured_receipt())
    health = runtime.get_startup_recovery_health()
    assert health["status"] == "clean"
    assert health["ready"] is True
    assert health["http_status"] == 200
    assert health["observation_state"] == ObservationState.OBSERVED_ZERO.value
    assert health["receipt"]["persisted"] is False


def test_unresolved_backlog_is_degraded_and_not_ready() -> None:
    runtime.record_startup_recovery_receipt(_measured_receipt(backlog=4))
    health = runtime.get_startup_recovery_health()
    assert health["status"] == "degraded"
    assert health["ready"] is False
    assert health["http_status"] == 503
    assert health["receipt"]["unresolved_count"] == 4
    assert health["reason_code"] == "time_budget_exhausted"


def test_failure_receipt_is_observer_failed_and_content_free() -> None:
    runtime.record_startup_recovery_receipt(_failure_receipt())
    health = runtime.get_startup_recovery_health()
    assert health["status"] == "observer_failed"
    assert health["ready"] is False
    assert health["http_status"] == 503
    assert health["reason_code"] == "single_fact_database_failed"
    serialized = str(health)
    assert "/private/" not in serialized
    assert "SELECT " not in serialized


def test_execute_records_exact_executor_result() -> None:
    expected = _measured_receipt()
    seen: list[StartupRecoveryBudget] = []

    def executor(budget: StartupRecoveryBudget):
        seen.append(budget)
        return expected

    budget = StartupRecoveryBudget(
        max_single_jobs=2,
        max_batches=1,
        time_budget_ms=250,
    )
    result = runtime.execute_and_record_startup_recovery(
        budget,
        executor=executor,
    )

    assert result is expected
    assert runtime.get_startup_recovery_receipt() is expected
    assert seen == [budget]


def test_record_rejects_untyped_payload() -> None:
    with pytest.raises(TypeError, match="startup recovery receipt"):
        runtime.record_startup_recovery_receipt({})  # type: ignore[arg-type]


def test_http_status_helper_tracks_latest_state() -> None:
    assert runtime.startup_recovery_http_status() == 503
    runtime.record_startup_recovery_receipt(_measured_receipt())
    assert runtime.startup_recovery_http_status() == 200
