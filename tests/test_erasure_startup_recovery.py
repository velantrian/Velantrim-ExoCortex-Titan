from __future__ import annotations

import pytest

from core.erasure_startup_recovery import (
    ErasureStartupRecoveryError,
    RecoveryDomain,
    RecoveryDomainReceipt,
    StartupRecoveryBudget,
    StartupRecoveryReceipt,
)
from core.runtime_evidence import ObservationState


def _domain(
    domain: RecoveryDomain,
    *,
    selected: int = 0,
    attempted: int = 0,
    completed: int = 0,
    partial: int = 0,
    failed: int = 0,
    skipped: int = 0,
    remaining_backlog: int = 0,
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
        remaining_backlog=remaining_backlog,
        error_codes=error_codes,
    )


def _clean_receipt(**overrides: object) -> StartupRecoveryReceipt:
    values: dict[str, object] = {
        "run_id": "recovery-run-1",
        "started_at_utc": "2026-08-02T12:00:00Z",
        "completed_at_utc": "2026-08-02T12:00:00.250000Z",
        "budget": StartupRecoveryBudget(
            max_single_jobs=2,
            max_batches=1,
            time_budget_ms=1_000,
        ),
        "single_fact": _domain(
            RecoveryDomain.SINGLE_FACT,
            selected=1,
            attempted=1,
            completed=1,
        ),
        "batch": _domain(RecoveryDomain.BATCH),
    }
    values.update(overrides)
    return StartupRecoveryReceipt(**values)  # type: ignore[arg-type]


def test_budget_requires_a_positive_domain_and_time_limit() -> None:
    with pytest.raises(ErasureStartupRecoveryError, match="at least one"):
        StartupRecoveryBudget(max_single_jobs=0, max_batches=0, time_budget_ms=1)
    with pytest.raises(ErasureStartupRecoveryError, match="greater than zero"):
        StartupRecoveryBudget(max_single_jobs=1, max_batches=0, time_budget_ms=0)
    with pytest.raises(ErasureStartupRecoveryError, match="non-negative integer"):
        StartupRecoveryBudget(max_single_jobs=True, max_batches=0, time_budget_ms=1)


def test_domain_receipt_requires_exact_attempt_accounting() -> None:
    with pytest.raises(ErasureStartupRecoveryError, match="must equal attempted"):
        _domain(
            RecoveryDomain.SINGLE_FACT,
            selected=2,
            attempted=2,
            completed=1,
        )


def test_unattempted_selected_work_must_remain_in_backlog() -> None:
    with pytest.raises(ErasureStartupRecoveryError, match="unattempted"):
        _domain(
            RecoveryDomain.SINGLE_FACT,
            selected=2,
            attempted=1,
            completed=1,
            remaining_backlog=0,
        )


def test_failed_outcome_requires_canonical_error_codes() -> None:
    with pytest.raises(ErasureStartupRecoveryError, match="require at least one"):
        _domain(
            RecoveryDomain.SINGLE_FACT,
            selected=1,
            attempted=1,
            failed=1,
        )

    receipt = _domain(
        RecoveryDomain.SINGLE_FACT,
        selected=1,
        attempted=1,
        failed=1,
        remaining_backlog=1,
        error_codes=("backend_timeout", "backend_timeout", "claim_failed"),
    )
    assert receipt.error_codes == ("backend_timeout", "claim_failed")


def test_clean_receipt_derives_observed_zero() -> None:
    receipt = _clean_receipt()

    assert receipt.duration_ms == 250
    assert receipt.unresolved_count == 0
    assert receipt.observation.state is ObservationState.OBSERVED_ZERO
    assert receipt.observation.observed_value == 0
    assert receipt.observation.hard_gate_satisfied is True
    assert receipt.to_dict()["persisted"] is False


def test_remaining_work_derives_observed_nonzero() -> None:
    receipt = _clean_receipt(
        single_fact=_domain(
            RecoveryDomain.SINGLE_FACT,
            selected=1,
            attempted=1,
            partial=1,
            remaining_backlog=2,
        )
    )

    assert receipt.unresolved_count == 3
    assert receipt.observation.state is ObservationState.OBSERVED_NONZERO
    assert receipt.observation.observed_value == 3
    assert receipt.observation.reason_code == "recovery_work_remaining"
    assert receipt.observation.hard_gate_satisfied is False


def test_unattempted_work_requires_time_budget_stop() -> None:
    single = _domain(
        RecoveryDomain.SINGLE_FACT,
        selected=2,
        attempted=1,
        completed=1,
        remaining_backlog=1,
    )
    with pytest.raises(ErasureStartupRecoveryError, match="time_budget"):
        _clean_receipt(single_fact=single)

    receipt = _clean_receipt(
        single_fact=single,
        stopped_by_time_budget=True,
    )
    assert receipt.observation.state is ObservationState.OBSERVED_NONZERO
    assert receipt.observation.reason_code == "time_budget_exhausted"


def test_selected_counts_cannot_exceed_declared_budget() -> None:
    with pytest.raises(ErasureStartupRecoveryError, match="max_single_jobs"):
        _clean_receipt(
            single_fact=_domain(
                RecoveryDomain.SINGLE_FACT,
                selected=3,
                attempted=3,
                completed=3,
            )
        )


def test_persistence_claim_requires_storage_reference() -> None:
    with pytest.raises(ErasureStartupRecoveryError, match="requires storage_ref"):
        _clean_receipt(persisted=True)
    with pytest.raises(ErasureStartupRecoveryError, match="cannot claim storage_ref"):
        _clean_receipt(storage_ref="ledger:receipt-1")

    receipt = _clean_receipt(
        persisted=True,
        storage_ref="ledger:receipt-1",
    )
    assert receipt.persisted is True
    assert receipt.storage_ref == "ledger:receipt-1"


def test_receipt_requires_ordered_utc_timestamps() -> None:
    with pytest.raises(ErasureStartupRecoveryError, match="must be UTC"):
        _clean_receipt(started_at_utc="2026-08-02T13:00:00+01:00")
    with pytest.raises(ErasureStartupRecoveryError, match="cannot be before"):
        _clean_receipt(
            started_at_utc="2026-08-02T12:00:01Z",
            completed_at_utc="2026-08-02T12:00:00Z",
        )
