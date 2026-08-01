from dataclasses import replace

import pytest

from core.reader_benchmark_batch import (
    BatchCaseStatus,
    ReaderBenchmarkBatchError,
    ReaderBenchmarkBatchPlanner,
    ReaderBenchmarkCaseReceipt,
)


def _plan(*, max_attempts: int = 2):
    return ReaderBenchmarkBatchPlanner.create_plan(
        corpus_id="corpus-1",
        environment_id="environment-1",
        threshold_policy_id="thresholds-1",
        case_ids=("case-b", "case-a"),
        max_attempts_per_case=max_attempts,
    )


def _receipt(
    plan_id: str,
    case_id: str,
    status: BatchCaseStatus,
    attempt: int,
    *,
    observation_id: str | None = None,
    error_code: str | None = None,
) -> ReaderBenchmarkCaseReceipt:
    return ReaderBenchmarkCaseReceipt(
        plan_id=plan_id,
        case_id=case_id,
        status=status,
        attempt=attempt,
        observation_id=observation_id,
        error_code=error_code,
        artifact_ids=(f"artifact-{case_id}-{attempt}",),
    )


def test_plan_is_canonical_and_self_verifying() -> None:
    first = _plan()
    second = ReaderBenchmarkBatchPlanner.create_plan(
        corpus_id="corpus-1",
        environment_id="environment-1",
        threshold_policy_id="thresholds-1",
        case_ids=("case-a", "case-b"),
        max_attempts_per_case=2,
    )
    assert first == second
    assert first.case_ids == ("case-a", "case-b")
    with pytest.raises(ReaderBenchmarkBatchError, match="plan_id"):
        replace(first, corpus_id="forged")


def test_failed_case_can_resume_with_contiguous_attempt() -> None:
    plan = _plan()
    checkpoint = ReaderBenchmarkBatchPlanner.empty_checkpoint(plan)
    failed = _receipt(
        plan.plan_id,
        "case-a",
        BatchCaseStatus.FAILED,
        1,
        error_code="timeout",
    )
    checkpoint = ReaderBenchmarkBatchPlanner.append_receipt(checkpoint, failed)
    assert checkpoint.pending_case_ids == ("case-a", "case-b")

    succeeded = _receipt(
        plan.plan_id,
        "case-a",
        BatchCaseStatus.SUCCEEDED,
        2,
        observation_id="observation-a",
    )
    checkpoint = ReaderBenchmarkBatchPlanner.append_receipt(
        checkpoint,
        succeeded,
    )
    assert checkpoint.pending_case_ids == ("case-b",)


def test_batch_completes_and_exposes_only_successful_observations() -> None:
    plan = _plan(max_attempts=1)
    checkpoint = ReaderBenchmarkBatchPlanner.empty_checkpoint(plan)
    with pytest.raises(ReaderBenchmarkBatchError, match="complete"):
        _ = checkpoint.successful_observation_ids

    checkpoint = ReaderBenchmarkBatchPlanner.append_receipt(
        checkpoint,
        _receipt(
            plan.plan_id,
            "case-a",
            BatchCaseStatus.SUCCEEDED,
            1,
            observation_id="observation-a",
        ),
    )
    checkpoint = ReaderBenchmarkBatchPlanner.append_receipt(
        checkpoint,
        _receipt(
            plan.plan_id,
            "case-b",
            BatchCaseStatus.SKIPPED,
            1,
            error_code="missing-gold-labels",
        ),
    )
    assert checkpoint.is_complete is True
    assert checkpoint.pending_case_ids == ()
    assert checkpoint.successful_observation_ids == ("observation-a",)
    with pytest.raises(ReaderBenchmarkBatchError, match="completed"):
        ReaderBenchmarkBatchPlanner.append_receipt(
            checkpoint,
            _receipt(
                plan.plan_id,
                "case-b",
                BatchCaseStatus.SUCCEEDED,
                1,
                observation_id="late",
            ),
        )


def test_foreign_unknown_and_duplicate_receipts_fail_closed() -> None:
    plan = _plan()
    checkpoint = ReaderBenchmarkBatchPlanner.empty_checkpoint(plan)
    with pytest.raises(ReaderBenchmarkBatchError, match="different batch"):
        ReaderBenchmarkBatchPlanner.append_receipt(
            checkpoint,
            _receipt(
                "foreign-plan",
                "case-a",
                BatchCaseStatus.SUCCEEDED,
                1,
                observation_id="observation-a",
            ),
        )
    with pytest.raises(ReaderBenchmarkBatchError, match="not present"):
        ReaderBenchmarkBatchPlanner.append_receipt(
            checkpoint,
            _receipt(
                plan.plan_id,
                "unknown-case",
                BatchCaseStatus.SUCCEEDED,
                1,
                observation_id="observation-x",
            ),
        )

    first = _receipt(
        plan.plan_id,
        "case-a",
        BatchCaseStatus.FAILED,
        1,
        error_code="timeout",
    )
    checkpoint = ReaderBenchmarkBatchPlanner.append_receipt(checkpoint, first)
    with pytest.raises(ReaderBenchmarkBatchError, match="duplicate"):
        ReaderBenchmarkBatchPlanner.append_receipt(checkpoint, first)


def test_attempt_limits_and_nonterminal_result_fields_are_rejected() -> None:
    plan = _plan(max_attempts=1)
    checkpoint = ReaderBenchmarkBatchPlanner.empty_checkpoint(plan)
    with pytest.raises(ReaderBenchmarkBatchError, match="result fields"):
        ReaderBenchmarkCaseReceipt(
            plan_id=plan.plan_id,
            case_id="case-a",
            status=BatchCaseStatus.RUNNING,
            attempt=1,
            error_code="not-allowed",
        )
    with pytest.raises(ReaderBenchmarkBatchError, match="exceeds"):
        ReaderBenchmarkBatchPlanner.append_receipt(
            checkpoint,
            _receipt(
                plan.plan_id,
                "case-a",
                BatchCaseStatus.FAILED,
                2,
                error_code="timeout",
            ),
        )


def test_new_attempt_requires_terminal_previous_attempt() -> None:
    plan = _plan()
    checkpoint = ReaderBenchmarkBatchPlanner.empty_checkpoint(plan)
    checkpoint = ReaderBenchmarkBatchPlanner.append_receipt(
        checkpoint,
        _receipt(plan.plan_id, "case-a", BatchCaseStatus.RUNNING, 1),
    )
    with pytest.raises(ReaderBenchmarkBatchError, match="terminal"):
        ReaderBenchmarkBatchPlanner.append_receipt(
            checkpoint,
            _receipt(
                plan.plan_id,
                "case-a",
                BatchCaseStatus.SUCCEEDED,
                2,
                observation_id="observation-a",
            ),
        )
