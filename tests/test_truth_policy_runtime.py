"""Tests for the fail-closed TruthPolicy hot-path adapter."""

from __future__ import annotations

from core.truth_policy import TruthVerdict
from core.truth_policy_runtime import (
    TruthPolicyRuntimeResult,
    evaluate_truth_policy_runtime,
)


def test_disabled_policy_is_not_evaluated_and_does_not_block() -> None:
    called = False

    def decider(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("disabled policy must not be called")

    result = evaluate_truth_policy_runtime(
        "query",
        [],
        mode="BALANCED",
        enabled=False,
        decider=decider,
    )

    assert called is False
    assert result.enabled is False
    assert result.evaluated is False
    assert result.blocks_llm is False
    assert result.truth_block is None
    assert result.reason_code == "truth_policy_disabled"


def test_allow_verdict_preserves_block_and_allows_llm() -> None:
    verdict = TruthVerdict(
        decision="allow",
        truth_status="supported",
        reason="admissible_evidence",
        admissible_count=2,
        evidence_ids=["e1"],
        trace_note="measured",
    )

    result = evaluate_truth_policy_runtime(
        "query",
        [{"fact_id": "f1"}],
        mode="BALANCED",
        enabled=True,
        decider=lambda *args, **kwargs: verdict,
    )

    assert result.enabled is True
    assert result.evaluated is True
    assert result.blocks_llm is False
    assert result.reason_code == "truth_policy_allow"
    assert result.truth_block == verdict.to_dict()


def test_gap_notice_preserves_honest_non_citation_grade_state() -> None:
    verdict = TruthVerdict(
        decision="gap_notice",
        truth_status="supported_without_structural_evidence",
        reason="no_structured_evidence",
        admissible_count=1,
    )

    result = evaluate_truth_policy_runtime(
        "query",
        [],
        mode="CAUTIOUS",
        enabled=True,
        decider=lambda *args, **kwargs: verdict,
    )

    assert result.evaluated is True
    assert result.blocks_llm is False
    assert result.reason_code == "truth_policy_gap_notice"
    assert result.truth_block["decision"] == "gap_notice"


def test_reject_verdict_blocks_llm() -> None:
    verdict = TruthVerdict(
        decision="reject",
        truth_status="unsupported",
        reason="no_admissible_facts",
    )

    result = evaluate_truth_policy_runtime(
        "query",
        [],
        mode="BALANCED",
        enabled=True,
        decider=lambda *args, **kwargs: verdict,
    )

    assert result.evaluated is True
    assert result.blocks_llm is True
    assert result.reason_code == "truth_policy_reject"
    assert result.truth_block["decision"] == "reject"


def test_enabled_policy_exception_fails_closed_without_payload_leak() -> None:
    def failing_decider(*args, **kwargs):
        raise RuntimeError("/private/db.sqlite SELECT secret_payload")

    result = evaluate_truth_policy_runtime(
        "sensitive user query",
        [{"claim": "private claim", "fact_id": "secret-fact"}],
        mode="BALANCED",
        enabled=True,
        decider=failing_decider,
    )

    assert result.enabled is True
    assert result.evaluated is False
    assert result.blocks_llm is True
    assert result.reason_code == "truth_policy_unavailable"
    assert result.truth_block == {
        "decision": "reject",
        "truth_status": "policy_unavailable",
        "reason": "truth_policy_unavailable",
        "admissible_count": 0,
        "evidence_ids": [],
        "trace_note": "",
    }
    serialized = str(result.truth_block)
    assert "private" not in serialized
    assert "secret" not in serialized
    assert "SELECT" not in serialized


def test_wrong_verdict_type_fails_closed() -> None:
    result = evaluate_truth_policy_runtime(
        "query",
        [],
        mode="BALANCED",
        enabled=True,
        decider=lambda *args, **kwargs: {"decision": "allow"},
    )

    assert result.evaluated is False
    assert result.blocks_llm is True
    assert result.reason_code == "truth_policy_unavailable"


def test_unknown_decision_fails_closed() -> None:
    result = evaluate_truth_policy_runtime(
        "query",
        [],
        mode="BALANCED",
        enabled=True,
        decider=lambda *args, **kwargs: TruthVerdict(decision="maybe"),
    )

    assert result.evaluated is False
    assert result.blocks_llm is True
    assert result.truth_block["decision"] == "reject"


def test_result_contract_rejects_disabled_blocking_claim() -> None:
    try:
        TruthPolicyRuntimeResult(
            enabled=False,
            evaluated=False,
            blocks_llm=True,
            truth_block=None,
            reason_code="invalid_disabled_state",
        )
    except ValueError as exc:
        assert "disabled" in str(exc)
    else:
        raise AssertionError("invalid disabled result must be rejected")
