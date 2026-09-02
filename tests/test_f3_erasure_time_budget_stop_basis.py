from __future__ import annotations

from core.erasure_startup_recovery import (
    RecoveryDomain,
    RecoveryDomainReceipt,
    StartupRecoveryBudget,
    StartupRecoveryReceipt,
)
from core.runtime_evidence import ObservationState


def _domain(domain: RecoveryDomain, *, remaining_backlog: int) -> RecoveryDomainReceipt:
    return RecoveryDomainReceipt(
        domain=domain,
        selected=0,
        attempted=0,
        completed=0,
        partial=0,
        failed=0,
        skipped=0,
        remaining_backlog=remaining_backlog,
    )


def _receipt(*, stopped_by_time_budget: bool) -> StartupRecoveryReceipt:
    return StartupRecoveryReceipt(
        run_id=(
            "f3-time-budget-stop"
            if stopped_by_time_budget
            else "f3-work-remaining-stop"
        ),
        started_at_utc="2026-09-02T12:00:00+00:00",
        completed_at_utc="2026-09-02T12:00:01+00:00",
        budget=StartupRecoveryBudget(
            max_single_jobs=1,
            max_batches=1,
            time_budget_ms=1_000,
        ),
        single_fact=_domain(RecoveryDomain.SINGLE_FACT, remaining_backlog=3),
        batch=_domain(RecoveryDomain.BATCH, remaining_backlog=0),
        stopped_by_time_budget=stopped_by_time_budget,
    )


def test_f3_same_unresolved_observation_preserves_time_budget_basis() -> None:
    """Same unresolved outward state retains time-budget vs ordinary-work basis."""
    time_budget_stop = _receipt(stopped_by_time_budget=True)
    work_remaining_stop = _receipt(stopped_by_time_budget=False)

    for receipt in (time_budget_stop, work_remaining_stop):
        assert receipt.unresolved_count == 3
        assert receipt.observation.state is ObservationState.OBSERVED_NONZERO
        assert receipt.observation.observed_value == 3

    assert time_budget_stop.observation.reason_code == "time_budget_exhausted"
    assert work_remaining_stop.observation.reason_code == "recovery_work_remaining"
    assert (
        time_budget_stop.observation.reason_code
        != work_remaining_stop.observation.reason_code
    )

    # This probe observes a typed time-budget basis only. It does not claim that
    # draft freshness, task insufficiency, or irreducible uncertainty are the same
    # stop class, and it introduces no retry/scheduler semantics.
