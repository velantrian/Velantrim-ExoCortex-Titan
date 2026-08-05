"""Compatibility and safety tests for Continuity R4 compute assessment."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
import inspect

import pytest

from core.compute_controller import (
    CONTINUITY_COMPUTE_POLICY_VERSION,
    ComputeDecision,
    ComputePath,
    ComputeSensitivity,
    ContextFreshness,
    ContinuityComputeAssessment,
    ContinuityComputeSignals,
    assess_compute_with_continuity,
    decide_compute_path,
)
from core.goal_frame import GoalFrame, GoalIntent, RiskLevel
from core.rapid_orientation import _cost_for_path


def _goal(
    *,
    intent: GoalIntent = GoalIntent.UNKNOWN,
    risk: RiskLevel = RiskLevel.LOW,
    style: str = "balanced",
) -> GoalFrame:
    return GoalFrame(
        query="q",
        intent=intent,
        risk_level=risk,
        output_style=style,
        reasons=["seed"],
    )


def test_legacy_function_signature_is_unchanged() -> None:
    signature = inspect.signature(decide_compute_path)

    assert tuple(signature.parameters) == (
        "query",
        "goal",
        "candidate_count",
        "uncertainty",
    )
    assert signature.parameters["query"].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
    for name in ("goal", "candidate_count", "uncertainty"):
        assert signature.parameters[name].kind is inspect.Parameter.KEYWORD_ONLY
    assert "continuity" not in signature.parameters
    assert "signals" not in signature.parameters


def test_legacy_compute_path_set_is_unchanged() -> None:
    assert {path.value for path in ComputePath} == {
        "fast_path",
        "normal_path",
        "deep_path",
        "verify_path",
        "creative_path",
    }


def test_legacy_direct_constructor_and_mutable_reasons_remain_compatible() -> None:
    decision = ComputeDecision(
        ComputePath.NORMAL_PATH,
        10,
        True,
        False,
        True,
        3,
        ["legacy"],
    )

    decision.reasons.append("still-supported")

    assert decision.reasons == ["legacy", "still-supported"]
    assert decision.to_dict() == {
        "path": "normal_path",
        "retrieval_k": 10,
        "require_truth_gate": True,
        "require_reflection": False,
        "require_noetic_pass": True,
        "max_reasoning_steps": 3,
        "reasons": ["legacy", "still-supported"],
    }


@pytest.mark.parametrize(
    ("goal", "candidate_count", "uncertainty", "expected"),
    [
        (
            _goal(risk=RiskLevel.HIGH),
            0,
            0.0,
            (
                ComputePath.VERIFY_PATH,
                16,
                True,
                True,
                True,
                6,
                ["seed", "verification or high-risk query"],
            ),
        ),
        (
            _goal(intent=GoalIntent.CREATE),
            0,
            0.0,
            (
                ComputePath.CREATIVE_PATH,
                10,
                True,
                False,
                True,
                4,
                ["seed", "creative generation requested"],
            ),
        ),
        (
            _goal(style="deep"),
            0,
            0.0,
            (
                ComputePath.DEEP_PATH,
                14,
                True,
                True,
                True,
                5,
                ["seed", "deep analysis or elevated uncertainty"],
            ),
        ),
        (
            _goal(style="short"),
            4,
            0.2,
            (
                ComputePath.FAST_PATH,
                6,
                True,
                False,
                False,
                2,
                ["seed", "short low-risk query"],
            ),
        ),
        (
            _goal(),
            8,
            0.2,
            (
                ComputePath.NORMAL_PATH,
                10,
                True,
                False,
                True,
                3,
                ["seed", "default balanced route"],
            ),
        ),
    ],
)
def test_legacy_decision_matrix_is_unchanged(
    goal: GoalFrame,
    candidate_count: int,
    uncertainty: float,
    expected: tuple[ComputePath, int, bool, bool, bool, int, list[str]],
) -> None:
    decision = decide_compute_path(
        "q",
        goal=goal,
        candidate_count=candidate_count,
        uncertainty=uncertainty,
    )

    assert (
        decision.path,
        decision.retrieval_k,
        decision.require_truth_gate,
        decision.require_reflection,
        decision.require_noetic_pass,
        decision.max_reasoning_steps,
        decision.reasons,
    ) == expected


def test_neutral_signals_leave_legacy_decision_identical() -> None:
    assessment = assess_compute_with_continuity(
        "q",
        goal=_goal(style="short"),
        candidate_count=2,
        uncertainty=0.1,
        signals=ContinuityComputeSignals(
            context_freshness=ContextFreshness.FRESH,
            continuity_available=True,
        ),
    )

    assert assessment.decision == assessment.base_decision
    assert assessment.changed_legacy_decision is False
    assert assessment.context_rebuild_required is False
    assert assessment.reason_codes == ()


def test_important_active_contradiction_raises_to_verify() -> None:
    assessment = assess_compute_with_continuity(
        "q",
        goal=_goal(style="short"),
        signals=ContinuityComputeSignals(
            context_freshness=ContextFreshness.FRESH,
            continuity_available=True,
            evidence_coverage=0.9,
            active_contradictions=2,
            important_claim=True,
        ),
    )

    assert assessment.base_decision.path is ComputePath.FAST_PATH
    assert assessment.decision.path is ComputePath.VERIFY_PATH
    assert assessment.changed_legacy_decision is True
    assert "important_claim_requires_conflict_verification" in assessment.reason_codes
    assert "continuity:important_claim_requires_conflict_verification" in (
        assessment.decision.reasons
    )


def test_unimportant_contradiction_is_visible_but_does_not_override() -> None:
    assessment = assess_compute_with_continuity(
        "q",
        goal=_goal(style="short"),
        signals=ContinuityComputeSignals(
            context_freshness=ContextFreshness.FRESH,
            continuity_available=True,
            active_contradictions=1,
            important_claim=False,
        ),
    )

    assert assessment.decision == assessment.base_decision
    assert assessment.reason_codes == ("active_contradictions",)


def test_missing_required_continuity_requests_rebuild_and_verify() -> None:
    assessment = assess_compute_with_continuity(
        "q",
        goal=_goal(style="short"),
        signals=ContinuityComputeSignals(
            continuity_available=False,
            requires_current_state=True,
        ),
    )

    assert assessment.context_rebuild_required is True
    assert assessment.decision.path is ComputePath.VERIFY_PATH
    assert "required_state_unavailable" in assessment.reason_codes
    assert "context_rebuild_required" in assessment.reason_codes


def test_stale_required_state_requests_rebuild_and_verify() -> None:
    assessment = assess_compute_with_continuity(
        "q",
        goal=_goal(),
        signals=ContinuityComputeSignals(
            continuity_available=True,
            context_freshness=ContextFreshness.CRITICAL_STALE,
            requires_current_state=True,
        ),
    )

    assert assessment.context_rebuild_required is True
    assert assessment.decision.path is ComputePath.VERIFY_PATH
    assert "critical_state_staleness" in assessment.reason_codes


def test_sensitive_low_evidence_raises_to_verify() -> None:
    assessment = assess_compute_with_continuity(
        "q",
        goal=_goal(style="short"),
        signals=ContinuityComputeSignals(
            continuity_available=True,
            context_freshness=ContextFreshness.FRESH,
            sensitivity=ComputeSensitivity.HIGH,
            evidence_coverage=0.2,
            important_claim=True,
        ),
    )

    assert assessment.decision.path is ComputePath.VERIFY_PATH
    assert "sensitive_claim_requires_verification" in assessment.reason_codes


def test_critical_near_zero_evidence_verifies_without_new_compute_path() -> None:
    assessment = assess_compute_with_continuity(
        "q",
        goal=_goal(style="short"),
        signals=ContinuityComputeSignals(
            continuity_available=False,
            sensitivity=ComputeSensitivity.CRITICAL,
            evidence_coverage=0.1,
            important_claim=True,
        ),
    )

    assert assessment.decision.path is ComputePath.VERIFY_PATH
    assert "critical_sensitivity_insufficient_evidence" in assessment.reason_codes
    assert "defer_path" not in {path.value for path in ComputePath}


def test_degraded_context_caps_only_deep_legacy_route() -> None:
    assessment = assess_compute_with_continuity(
        "q",
        goal=_goal(style="deep"),
        signals=ContinuityComputeSignals(
            context_degraded=True,
            continuity_available=True,
            context_freshness=ContextFreshness.FRESH,
        ),
    )

    assert assessment.base_decision.path is ComputePath.DEEP_PATH
    assert assessment.decision.path is ComputePath.NORMAL_PATH
    assert assessment.decision.retrieval_k == 8
    assert assessment.decision.max_reasoning_steps == 3
    assert assessment.decision.require_reflection is False
    assert "degraded_context_depth_cap" in assessment.reason_codes


def test_degraded_context_never_downgrades_verify() -> None:
    assessment = assess_compute_with_continuity(
        "q",
        goal=_goal(risk=RiskLevel.HIGH),
        signals=ContinuityComputeSignals(
            context_degraded=True,
            continuity_available=True,
        ),
    )

    assert assessment.base_decision.path is ComputePath.VERIFY_PATH
    assert assessment.decision.path is ComputePath.VERIFY_PATH
    assert assessment.changed_legacy_decision is False
    assert assessment.reason_codes == ("context_degraded",)


def test_signal_validation_fails_closed() -> None:
    with pytest.raises(ValueError, match="evidence_coverage"):
        ContinuityComputeSignals(evidence_coverage=float("nan"))
    with pytest.raises(ValueError, match="active_contradictions"):
        ContinuityComputeSignals(active_contradictions=True)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="context_degraded"):
        ContinuityComputeSignals(context_degraded=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="context_freshness"):
        ContinuityComputeSignals(context_freshness="fresh")  # type: ignore[arg-type]


def test_assessment_requires_typed_signals() -> None:
    with pytest.raises(ValueError, match="signals"):
        assess_compute_with_continuity(
            "q",
            signals={"continuity_available": True},  # type: ignore[arg-type]
        )


def test_assessment_is_deterministic_and_immutable() -> None:
    signals = ContinuityComputeSignals(
        context_degraded=True,
        context_freshness=ContextFreshness.STALE,
        continuity_available=True,
        evidence_coverage=0.7,
        requires_current_state=True,
    )

    first = assess_compute_with_continuity("q", goal=_goal(), signals=signals)
    second = assess_compute_with_continuity("q", goal=_goal(), signals=signals)

    assert first == second
    assert first.to_dict() == second.to_dict()
    assert first.policy_version == CONTINUITY_COMPUTE_POLICY_VERSION
    assert first.shadow_only is True
    with pytest.raises(FrozenInstanceError):
        first.context_rebuild_required = False  # type: ignore[misc]


def test_shadow_only_cannot_be_disabled() -> None:
    base = decide_compute_path("q", goal=_goal())
    with pytest.raises(ValueError, match="shadow-only"):
        ContinuityComputeAssessment(
            base_decision=base,
            decision=base,
            context_rebuild_required=False,
            reason_codes=(),
            shadow_only=False,
        )


def test_rapid_orientation_mapping_remains_exhaustive() -> None:
    assert {_cost_for_path(path) for path in ComputePath} == {1, 2, 3, 4}


def test_assessment_payload_has_no_execution_authority() -> None:
    payload = assess_compute_with_continuity(
        "q",
        goal=_goal(),
        signals=ContinuityComputeSignals(),
    ).to_dict()

    forbidden = {
        "answer",
        "advice",
        "action",
        "tool",
        "canon_write",
        "truth_status",
        "persist",
        "execute",
    }
    assert forbidden.isdisjoint(payload)
