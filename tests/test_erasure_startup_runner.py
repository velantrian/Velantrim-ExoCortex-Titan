"""Contract tests for the aggregate bounded erasure startup runner."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone

import pytest

from core.erasure_startup_recovery import (
    RecoveryDomain,
    RecoveryDomainReceipt,
    StartupRecoveryBudget,
    StartupRecoveryFailureReceipt,
    StartupRecoveryReceipt,
)
from core.erasure_startup_runner import run_startup_recovery
from core.runtime_evidence import ObservationState


def _receipt(
    domain: RecoveryDomain,
    *,
    selected: int = 0,
    attempted: int = 0,
    completed: int = 0,
    partial: int = 0,
    failed: int = 0,
    skipped: int = 0,
    backlog: int = 0,
    error_codes: tuple[str, ...] = (),
) -> RecoveryDomainReceipt:
    return RecoveryDomainReceipt(
        domain=domain,
        selected=selected,
        attempted=attempted,
        completed=completed,
        partial=partial,
        failed=failed,
        skipped=skipped,
        remaining_backlog=backlog,
        error_codes=error_codes,
    )


def test_clean_run_uses_one_shared_deadline_and_observes_zero() -> None:
    budget = StartupRecoveryBudget(
        max_single_jobs=2,
        max_batches=1,
        time_budget_ms=5_000,
    )
    started = datetime(2026, 8, 2, 12, 0, tzinfo=timezone.utc)
    wall_times = iter((started, started + timedelta(milliseconds=20)))
    deadlines: list[float] = []

    def single_runner(**kwargs):
        deadlines.append(kwargs["deadline_monotonic"])
        assert kwargs["max_jobs"] == 2
        return _receipt(
            RecoveryDomain.SINGLE_FACT,
            selected=1,
            attempted=1,
            completed=1,
        ), False

    def batch_runner(**kwargs):
        deadlines.append(kwargs["deadline_monotonic"])
        assert kwargs["max_batches"] == 1
        return _receipt(
            RecoveryDomain.BATCH,
            selected=1,
            attempted=1,
            completed=1,
        ), False

    result = run_startup_recovery(
        budget,
        monotonic=lambda: 10.0,
        now_utc=lambda: next(wall_times),
        run_id_factory=lambda: "esr_test_clean",
        single_runner=single_runner,
        batch_runner=batch_runner,
    )

    assert isinstance(result, StartupRecoveryReceipt)
    assert deadlines == [15.0, 15.0]
    assert result.unresolved_count == 0
    assert result.observation.state is ObservationState.OBSERVED_ZERO
    assert result.persisted is False
    assert result.storage_ref is None


def test_time_budget_stop_and_backlog_observe_nonzero() -> None:
    budget = StartupRecoveryBudget(max_single_jobs=1, max_batches=1, time_budget_ms=10)
    now = datetime(2026, 8, 2, 12, 0, tzinfo=timezone.utc)

    def single_runner(**kwargs):
        return _receipt(
            RecoveryDomain.SINGLE_FACT,
            selected=1,
            attempted=0,
            backlog=3,
        ), True

    def batch_runner(**kwargs):
        return _receipt(RecoveryDomain.BATCH), False

    result = run_startup_recovery(
        budget,
        monotonic=lambda: 1.0,
        now_utc=lambda: now,
        run_id_factory=lambda: "esr_test_timeout",
        single_runner=single_runner,
        batch_runner=batch_runner,
    )

    assert isinstance(result, StartupRecoveryReceipt)
    assert result.stopped_by_time_budget is True
    assert result.unresolved_count == 3
    assert result.observation.state is ObservationState.OBSERVED_NONZERO
    assert result.observation.reason_code == "time_budget_exhausted"


def test_zero_budget_domain_is_not_called() -> None:
    budget = StartupRecoveryBudget(max_single_jobs=0, max_batches=1, time_budget_ms=100)
    now = datetime(2026, 8, 2, 12, 0, tzinfo=timezone.utc)

    def forbidden_single(**kwargs):
        raise AssertionError("single runner must not be called")

    result = run_startup_recovery(
        budget,
        monotonic=lambda: 1.0,
        now_utc=lambda: now,
        run_id_factory=lambda: "esr_zero_single",
        single_runner=forbidden_single,
        batch_runner=lambda **kwargs: (_receipt(RecoveryDomain.BATCH), False),
    )

    assert isinstance(result, StartupRecoveryReceipt)
    assert result.single_fact.selected == 0
    assert result.single_fact.attempted == 0


def test_single_database_failure_returns_observer_failed_without_payload_leak() -> None:
    budget = StartupRecoveryBudget(max_single_jobs=1, max_batches=1, time_budget_ms=100)
    now = datetime(2026, 8, 2, 12, 0, tzinfo=timezone.utc)

    def failing_single(**kwargs):
        raise sqlite3.DatabaseError("/private/path.db: secret SQL payload")

    result = run_startup_recovery(
        budget,
        monotonic=lambda: 1.0,
        now_utc=lambda: now,
        run_id_factory=lambda: "esr_single_db_failure",
        single_runner=failing_single,
        batch_runner=lambda **kwargs: pytest.fail("batch must not run"),
    )

    assert isinstance(result, StartupRecoveryFailureReceipt)
    assert result.error_code == "single_fact_database_failed"
    assert result.observation.state is ObservationState.OBSERVER_FAILED
    serialized = str(result.to_dict())
    assert "private" not in serialized
    assert "secret" not in serialized
    assert "SQL" not in serialized


def test_batch_contract_failure_after_single_measurement_fails_whole_aggregate() -> None:
    budget = StartupRecoveryBudget(max_single_jobs=1, max_batches=1, time_budget_ms=100)
    now = datetime(2026, 8, 2, 12, 0, tzinfo=timezone.utc)

    def failing_batch(**kwargs):
        raise ValueError("unknown batch outcome")

    result = run_startup_recovery(
        budget,
        monotonic=lambda: 1.0,
        now_utc=lambda: now,
        run_id_factory=lambda: "esr_batch_contract_failure",
        single_runner=lambda **kwargs: (
            _receipt(
                RecoveryDomain.SINGLE_FACT,
                selected=1,
                attempted=1,
                completed=1,
            ),
            False,
        ),
        batch_runner=failing_batch,
    )

    assert isinstance(result, StartupRecoveryFailureReceipt)
    assert result.error_code == "batch_contract_failed"
    assert result.observation.state is ObservationState.OBSERVER_FAILED


def test_wrong_domain_receipt_is_rejected_by_aggregate_contract() -> None:
    budget = StartupRecoveryBudget(max_single_jobs=1, max_batches=1, time_budget_ms=100)
    now = datetime(2026, 8, 2, 12, 0, tzinfo=timezone.utc)

    result = run_startup_recovery(
        budget,
        monotonic=lambda: 1.0,
        now_utc=lambda: now,
        run_id_factory=lambda: "esr_wrong_domain",
        single_runner=lambda **kwargs: (_receipt(RecoveryDomain.BATCH), False),
        batch_runner=lambda **kwargs: (_receipt(RecoveryDomain.BATCH), False),
    )

    assert isinstance(result, StartupRecoveryFailureReceipt)
    assert result.error_code == "aggregate_contract_failed"


def test_nonfinite_monotonic_clock_returns_typed_failure() -> None:
    budget = StartupRecoveryBudget(max_single_jobs=1, max_batches=1, time_budget_ms=100)
    now = datetime(2026, 8, 2, 12, 0, tzinfo=timezone.utc)

    result = run_startup_recovery(
        budget,
        monotonic=lambda: float("nan"),
        now_utc=lambda: now,
        run_id_factory=lambda: "esr_bad_monotonic",
    )

    assert isinstance(result, StartupRecoveryFailureReceipt)
    assert result.error_code == "startup_clock_contract_failed"


def test_wall_clock_failure_returns_typed_failure_receipt() -> None:
    budget = StartupRecoveryBudget(max_single_jobs=1, max_batches=0, time_budget_ms=100)

    def broken_wall_clock() -> datetime:
        raise RuntimeError("clock unavailable")

    result = run_startup_recovery(
        budget,
        now_utc=broken_wall_clock,
        run_id_factory=lambda: "esr_bad_wall_clock",
    )

    assert isinstance(result, StartupRecoveryFailureReceipt)
    assert result.error_code == "startup_wall_clock_failed"
    assert result.observation.state is ObservationState.OBSERVER_FAILED


def test_run_id_failure_returns_typed_failure_receipt() -> None:
    budget = StartupRecoveryBudget(max_single_jobs=1, max_batches=0, time_budget_ms=100)
    now = datetime(2026, 8, 2, 12, 0, tzinfo=timezone.utc)

    def broken_run_id() -> str:
        raise RuntimeError("identity unavailable")

    result = run_startup_recovery(
        budget,
        now_utc=lambda: now,
        run_id_factory=broken_run_id,
    )

    assert isinstance(result, StartupRecoveryFailureReceipt)
    assert result.error_code == "startup_identity_failed"
    assert result.run_id.startswith("esr_identity_failure_")


def test_completion_wall_clock_failure_is_not_reported_as_measured_success() -> None:
    budget = StartupRecoveryBudget(max_single_jobs=1, max_batches=0, time_budget_ms=100)
    started = datetime(2026, 8, 2, 12, 0, tzinfo=timezone.utc)
    calls = 0

    def wall_clock() -> datetime:
        nonlocal calls
        calls += 1
        if calls == 1:
            return started
        raise RuntimeError("completion clock unavailable")

    result = run_startup_recovery(
        budget,
        monotonic=lambda: 1.0,
        now_utc=wall_clock,
        run_id_factory=lambda: "esr_completion_clock",
        single_runner=lambda **kwargs: (_receipt(RecoveryDomain.SINGLE_FACT), False),
    )

    assert isinstance(result, StartupRecoveryFailureReceipt)
    assert result.error_code == "completion_clock_contract_failed"


def test_invalid_budget_type_is_programmer_error() -> None:
    with pytest.raises(TypeError, match="StartupRecoveryBudget"):
        run_startup_recovery(object())  # type: ignore[arg-type]
