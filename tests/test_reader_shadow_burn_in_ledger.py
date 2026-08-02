from __future__ import annotations

from dataclasses import replace

import pytest

from core.reader_shadow_burn_in import (
    ReaderShadowBurnInPlan,
    ReaderShadowBurnInPlanSignature,
    ReaderShadowBurnInPlanSigner,
    ReaderShadowBurnInSource,
    ReaderShadowBurnInStatusReceipt,
    ShadowBurnInStatus,
)
from core.reader_shadow_burn_in_ledger import (
    ReaderShadowBurnInLedger,
    ReaderShadowBurnInLedgerBuilder,
    ReaderShadowBurnInLedgerError,
    ReaderShadowWorkReceipt,
    ReaderShadowWorkSigner,
    ShadowBurnInLedgerStatus,
    ShadowWorkResult,
)

SECRET = b"0123456789abcdef0123456789abcdef"
WRONG_SECRET = b"abcdef0123456789abcdef0123456789"


def _plan(
    *,
    work_item_ids: tuple[str, ...] = ("work-a", "work-b"),
    max_attempts: int = 2,
    per_item_timeout_ms: int = 10_000,
    max_wall_ms: int = 60_000,
    max_tokens: int = 1_000,
    max_bytes: int = 10_000,
    max_failures: int = 3,
) -> tuple[ReaderShadowBurnInPlan, ReaderShadowBurnInPlanSignature]:
    source = ReaderShadowBurnInSource(
        campaign_name="reader-shadow-ledger-fixture",
        environment_id="shadow-env-fixed-001",
        harness_digest="shadow-harness-fixed-001",
        planned_start_utc="2026-08-02T10:00:00Z",
        planned_end_utc="2026-08-02T12:00:00Z",
        work_item_ids=work_item_ids,
        max_attempts_per_work_item=max_attempts,
        per_work_item_timeout_ms=per_item_timeout_ms,
        max_total_wall_time_ms=max_wall_ms,
        max_total_model_tokens=max_tokens,
        max_total_artifact_bytes=max_bytes,
        max_consecutive_failures=max_failures,
        condition_codes=(
            "kill_switch_required",
            "no_production_traffic",
        ),
    )
    plan = ReaderShadowBurnInPlan(
        source=source,
        decision_id="decision-fixed-001",
        decision_signature_id="decision-signature-fixed-001",
        decision_status_id="decision-status-fixed-001",
        evidence_id="evidence-fixed-001",
        benchmark_verification_id="benchmark-verification-fixed-001",
        retention_manifest_id="retention-manifest-fixed-001",
        retention_verification_id="retention-verification-fixed-001",
    )
    signature = ReaderShadowBurnInPlanSigner.sign(
        plan,
        key_id="shadow-plan-key-v1",
        secret=SECRET,
    )
    return plan, signature


def _status(
    plan: ReaderShadowBurnInPlan,
    signature: ReaderShadowBurnInPlanSignature,
    as_of_utc: str,
    *,
    status: ShadowBurnInStatus = ShadowBurnInStatus.READY,
) -> ReaderShadowBurnInStatusReceipt:
    return ReaderShadowBurnInStatusReceipt(
        plan_id=plan.plan_id,
        plan_signature_id=signature.signature_id,
        control_receipt_id=f"control-receipt-{as_of_utc}",
        control_signature_id=f"control-signature-{as_of_utc}",
        decision_status_id=f"decision-status-{as_of_utc}",
        as_of_utc=as_of_utc,
        status=status,
        shadow_evaluation_authorized=status is ShadowBurnInStatus.READY,
    )


def _receipt(
    plan: ReaderShadowBurnInPlan,
    signature: ReaderShadowBurnInPlanSignature,
    status: ReaderShadowBurnInStatusReceipt,
    *,
    work_item_id: str,
    attempt: int,
    completed_at_utc: str,
    result: ShadowWorkResult = ShadowWorkResult.SUCCEEDED,
    model_tokens: int = 10,
    artifact_bytes: int = 100,
    error_code: str | None = None,
) -> ReaderShadowWorkReceipt:
    return ReaderShadowWorkReceipt(
        plan_id=plan.plan_id,
        plan_signature_id=signature.signature_id,
        status_id=status.status_id,
        environment_id=plan.source.environment_id,
        harness_digest=plan.source.harness_digest,
        work_item_id=work_item_id,
        attempt=attempt,
        started_at_utc=status.as_of_utc,
        completed_at_utc=completed_at_utc,
        result=result,
        wall_time_ms=1_000,
        model_tokens=model_tokens,
        artifact_bytes=artifact_bytes,
        artifact_ids=(f"artifact-{work_item_id}-{attempt}",),
        error_code=(
            error_code
            if result is ShadowWorkResult.FAILED
            else None
        ),
    )


def _append(
    *,
    plan: ReaderShadowBurnInPlan,
    plan_signature: ReaderShadowBurnInPlanSignature,
    status: ReaderShadowBurnInStatusReceipt,
    ledger: ReaderShadowBurnInLedger,
    receipt: ReaderShadowWorkReceipt,
    secret: bytes = SECRET,
) -> ReaderShadowBurnInLedger:
    receipt_signature = ReaderShadowWorkSigner.sign(
        receipt,
        key_id="shadow-work-key-v1",
        secret=SECRET,
    )
    return ReaderShadowBurnInLedgerBuilder.append(
        plan=plan,
        plan_signature=plan_signature,
        status=status,
        ledger=ledger,
        receipt=receipt,
        receipt_signature=receipt_signature,
        secret=secret,
    )


def test_empty_ledger_requires_signed_ready_campaign() -> None:
    plan, plan_signature = _plan()
    ready = _status(plan, plan_signature, "2026-08-02T10:01:00Z")

    ledger = ReaderShadowBurnInLedgerBuilder.empty(
        plan=plan,
        plan_signature=plan_signature,
        status=ready,
        secret=SECRET,
    )

    assert ledger.status is ShadowBurnInLedgerStatus.READY
    assert ledger.pending_work_item_ids == ("work-a", "work-b")
    assert ledger.receipts == ()

    with pytest.raises(
        ReaderShadowBurnInLedgerError,
        match="plan signature verification failed",
    ):
        ReaderShadowBurnInLedgerBuilder.empty(
            plan=plan,
            plan_signature=plan_signature,
            status=ready,
            secret=WRONG_SECRET,
        )


def test_non_ready_status_cannot_admit_shadow_work() -> None:
    plan, plan_signature = _plan()
    paused = _status(
        plan,
        plan_signature,
        "2026-08-02T10:01:00Z",
        status=ShadowBurnInStatus.PAUSED,
    )

    with pytest.raises(ReaderShadowBurnInLedgerError, match="exact READY"):
        ReaderShadowBurnInLedgerBuilder.empty(
            plan=plan,
            plan_signature=plan_signature,
            status=paused,
            secret=SECRET,
        )


def test_two_signed_successes_complete_campaign() -> None:
    plan, plan_signature = _plan()
    first_status = _status(plan, plan_signature, "2026-08-02T10:01:00Z")
    ledger = ReaderShadowBurnInLedgerBuilder.empty(
        plan=plan,
        plan_signature=plan_signature,
        status=first_status,
        secret=SECRET,
    )
    first = _receipt(
        plan,
        plan_signature,
        first_status,
        work_item_id="work-a",
        attempt=1,
        completed_at_utc="2026-08-02T10:01:01Z",
    )
    ledger = _append(
        plan=plan,
        plan_signature=plan_signature,
        status=first_status,
        ledger=ledger,
        receipt=first,
    )
    second_status = _status(plan, plan_signature, "2026-08-02T10:02:00Z")
    second = _receipt(
        plan,
        plan_signature,
        second_status,
        work_item_id="work-b",
        attempt=1,
        completed_at_utc="2026-08-02T10:02:01Z",
    )
    ledger = _append(
        plan=plan,
        plan_signature=plan_signature,
        status=second_status,
        ledger=ledger,
        receipt=second,
    )

    assert ledger.status is ShadowBurnInLedgerStatus.COMPLETE_SUCCESS
    assert ledger.is_terminal is True
    assert ledger.successful_work_item_ids == ("work-a", "work-b")
    assert ledger.pending_work_item_ids == ()
    assert ledger.total_model_tokens == 20
    assert ledger.total_artifact_bytes == 200
    assert ledger.total_wall_time_ms == 2_000

    with pytest.raises(ReaderShadowBurnInLedgerError, match="terminal"):
        _append(
            plan=plan,
            plan_signature=plan_signature,
            status=second_status,
            ledger=ledger,
            receipt=second,
        )


def test_failed_work_item_can_retry_with_next_ready_status() -> None:
    plan, plan_signature = _plan(work_item_ids=("work-a",))
    first_status = _status(plan, plan_signature, "2026-08-02T10:01:00Z")
    ledger = ReaderShadowBurnInLedgerBuilder.empty(
        plan=plan,
        plan_signature=plan_signature,
        status=first_status,
        secret=SECRET,
    )
    failed = _receipt(
        plan,
        plan_signature,
        first_status,
        work_item_id="work-a",
        attempt=1,
        completed_at_utc="2026-08-02T10:01:01Z",
        result=ShadowWorkResult.FAILED,
        error_code="transient-local-failure",
    )
    ledger = _append(
        plan=plan,
        plan_signature=plan_signature,
        status=first_status,
        ledger=ledger,
        receipt=failed,
    )
    assert ledger.status is ShadowBurnInLedgerStatus.IN_PROGRESS
    assert ledger.consecutive_failure_count == 1

    retry_status = _status(plan, plan_signature, "2026-08-02T10:02:00Z")
    retry = _receipt(
        plan,
        plan_signature,
        retry_status,
        work_item_id="work-a",
        attempt=2,
        completed_at_utc="2026-08-02T10:02:01Z",
    )
    ledger = _append(
        plan=plan,
        plan_signature=plan_signature,
        status=retry_status,
        ledger=ledger,
        receipt=retry,
    )

    assert ledger.status is ShadowBurnInLedgerStatus.COMPLETE_SUCCESS
    assert ledger.consecutive_failure_count == 0


def test_attempts_must_be_contiguous_and_within_plan() -> None:
    plan, plan_signature = _plan(work_item_ids=("work-a",))
    ready = _status(plan, plan_signature, "2026-08-02T10:01:00Z")
    ledger = ReaderShadowBurnInLedgerBuilder.empty(
        plan=plan,
        plan_signature=plan_signature,
        status=ready,
        secret=SECRET,
    )
    receipt = _receipt(
        plan,
        plan_signature,
        ready,
        work_item_id="work-a",
        attempt=2,
        completed_at_utc="2026-08-02T10:01:01Z",
    )

    with pytest.raises(ReaderShadowBurnInLedgerError, match="contiguous"):
        _append(
            plan=plan,
            plan_signature=plan_signature,
            status=ready,
            ledger=ledger,
            receipt=receipt,
        )


def test_budget_exhaustion_is_retained_and_terminal() -> None:
    plan, plan_signature = _plan(max_tokens=10)
    ready = _status(plan, plan_signature, "2026-08-02T10:01:00Z")
    ledger = ReaderShadowBurnInLedgerBuilder.empty(
        plan=plan,
        plan_signature=plan_signature,
        status=ready,
        secret=SECRET,
    )
    receipt = _receipt(
        plan,
        plan_signature,
        ready,
        work_item_id="work-a",
        attempt=1,
        completed_at_utc="2026-08-02T10:01:01Z",
        model_tokens=10,
    )
    ledger = _append(
        plan=plan,
        plan_signature=plan_signature,
        status=ready,
        ledger=ledger,
        receipt=receipt,
    )

    assert ledger.status is ShadowBurnInLedgerStatus.BUDGET_EXHAUSTED
    assert ledger.exhaustion_codes == ("total_model_tokens_exhausted",)
    assert ledger.is_terminal is True


def test_failure_streak_stops_further_admission() -> None:
    plan, plan_signature = _plan(
        work_item_ids=("work-a",),
        max_attempts=3,
        max_failures=2,
    )
    first_status = _status(plan, plan_signature, "2026-08-02T10:01:00Z")
    ledger = ReaderShadowBurnInLedgerBuilder.empty(
        plan=plan,
        plan_signature=plan_signature,
        status=first_status,
        secret=SECRET,
    )
    first = _receipt(
        plan,
        plan_signature,
        first_status,
        work_item_id="work-a",
        attempt=1,
        completed_at_utc="2026-08-02T10:01:01Z",
        result=ShadowWorkResult.FAILED,
        error_code="failure-one",
    )
    ledger = _append(
        plan=plan,
        plan_signature=plan_signature,
        status=first_status,
        ledger=ledger,
        receipt=first,
    )
    second_status = _status(plan, plan_signature, "2026-08-02T10:02:00Z")
    second = _receipt(
        plan,
        plan_signature,
        second_status,
        work_item_id="work-a",
        attempt=2,
        completed_at_utc="2026-08-02T10:02:01Z",
        result=ShadowWorkResult.FAILED,
        error_code="failure-two",
    )
    ledger = _append(
        plan=plan,
        plan_signature=plan_signature,
        status=second_status,
        ledger=ledger,
        receipt=second,
    )

    assert ledger.status is ShadowBurnInLedgerStatus.FAILURE_LIMIT_REACHED
    assert ledger.consecutive_failure_count == 2
    assert ledger.is_terminal is True


def test_receipt_requires_exact_status_time_and_valid_signature() -> None:
    plan, plan_signature = _plan(work_item_ids=("work-a",))
    ready = _status(plan, plan_signature, "2026-08-02T10:01:00Z")
    ledger = ReaderShadowBurnInLedgerBuilder.empty(
        plan=plan,
        plan_signature=plan_signature,
        status=ready,
        secret=SECRET,
    )
    receipt = _receipt(
        plan,
        plan_signature,
        ready,
        work_item_id="work-a",
        attempt=1,
        completed_at_utc="2026-08-02T10:01:01Z",
    )
    signature = ReaderShadowWorkSigner.sign(
        receipt,
        key_id="shadow-work-key-v1",
        secret=SECRET,
    )

    with pytest.raises(ReaderShadowBurnInLedgerError, match="verification failed"):
        ReaderShadowBurnInLedgerBuilder.append(
            plan=plan,
            plan_signature=plan_signature,
            status=ready,
            ledger=ledger,
            receipt=receipt,
            receipt_signature=signature,
            secret=WRONG_SECRET,
        )

    stale_status = _status(plan, plan_signature, "2026-08-02T10:00:59Z")
    with pytest.raises(ReaderShadowBurnInLedgerError, match="exact READY"):
        ReaderShadowBurnInLedgerBuilder.append(
            plan=plan,
            plan_signature=plan_signature,
            status=stale_status,
            ledger=ledger,
            receipt=receipt,
            receipt_signature=signature,
            secret=SECRET,
        )


def test_shadow_receipts_reject_forbidden_side_effects() -> None:
    plan, plan_signature = _plan(work_item_ids=("work-a",))
    ready = _status(plan, plan_signature, "2026-08-02T10:01:00Z")
    receipt = _receipt(
        plan,
        plan_signature,
        ready,
        work_item_id="work-a",
        attempt=1,
        completed_at_utc="2026-08-02T10:01:01Z",
    )

    with pytest.raises(ReaderShadowBurnInLedgerError, match="canon_writes"):
        replace(receipt, canon_writes=1, receipt_id="")
    with pytest.raises(
        ReaderShadowBurnInLedgerError,
        match="production_traffic_observed",
    ):
        replace(receipt, production_traffic_observed=True, receipt_id="")


def test_ledger_identity_is_self_verifying() -> None:
    plan, plan_signature = _plan()
    ready = _status(plan, plan_signature, "2026-08-02T10:01:00Z")
    ledger = ReaderShadowBurnInLedgerBuilder.empty(
        plan=plan,
        plan_signature=plan_signature,
        status=ready,
        secret=SECRET,
    )

    with pytest.raises(ReaderShadowBurnInLedgerError, match="ledger_id"):
        replace(ledger, ledger_id="forged-ledger")
