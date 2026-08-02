"""Tests for continuity signals in the existing ComputeController."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from core.compute_controller import (
    COMPUTE_POLICY_VERSION,
    ComputePath,
    ComputeSensitivity,
    ContextFreshness,
    ContinuityComputeSignals,
    decide_compute_path,
)


def test_legacy_calls_keep_existing_high_risk_route() -> None:
    decision = decide_compute_path("verify medical claim")

    assert decision.path is ComputePath.VERIFY_PATH
    assert decision.retrieval_k == 16
    assert decision.require_truth_gate is True
    assert decision.require_reflection is True
    assert decision.context_rebuild_required is False
    assert decision.defer_reason is None


def test_important_active_contradiction_forces_verify() -> None:
    signals = ContinuityComputeSignals(
        context_freshness=ContextFreshness.FRESH,
        evidence_coverage=0.9,
        active_contradictions=2,
        sensitivity=ComputeSensitivity.MEDIUM,
        continuity_available=True,
        important_claim=True,
    )

    decision = decide_compute_path("give a short answer", continuity=signals)

    assert decision.path is ComputePath.VERIFY_PATH
    assert decision.max_reasoning_steps == 6
    assert decision.context_rebuild_required is False
    assert "continuity:important_claim_requires_conflict_verification" in decision.reasons


def test_unimportant_contradiction_does_not_override_base_route() -> None:
    signals = ContinuityComputeSignals(
        context_freshness=ContextFreshness.FRESH,
        evidence_coverage=0.9,
        active_contradictions=1,
        continuity_available=True,
        important_claim=False,
    )

    decision = decide_compute_path("answer briefly", continuity=signals)

    assert decision.path in {ComputePath.FAST_PATH, ComputePath.NORMAL_PATH}
    assert "continuity:active_contradictions" in decision.reasons


def test_critical_stale_required_state_requests_rebuild_and_verify() -> None:
    signals = ContinuityComputeSignals(
        context_freshness=ContextFreshness.CRITICAL_STALE,
        evidence_coverage=0.8,
        continuity_available=True,
        requires_current_state=True,
    )

    decision = decide_compute_path("what is the current project priority?", continuity=signals)

    assert decision.path is ComputePath.VERIFY_PATH
    assert decision.context_rebuild_required is True
    assert "continuity:context_rebuild_required" in decision.reasons


def test_missing_required_continuity_requests_rebuild() -> None:
    signals = ContinuityComputeSignals(
        context_freshness=ContextFreshness.UNKNOWN,
        evidence_coverage=0.8,
        continuity_available=False,
        requires_current_state=True,
    )

    decision = decide_compute_path("continue from the last decision", continuity=signals)

    assert decision.path is ComputePath.VERIFY_PATH
    assert decision.context_rebuild_required is True
    assert "continuity:required_state_unavailable" in decision.reasons


def test_critical_sensitivity_and_near_zero_evidence_defers() -> None:
    signals = ContinuityComputeSignals(
        context_freshness=ContextFreshness.UNKNOWN,
        evidence_coverage=0.1,
        sensitivity=ComputeSensitivity.CRITICAL,
        continuity_available=False,
        important_claim=True,
    )

    decision = decide_compute_path("state the conclusion", continuity=signals)

    assert decision.path is ComputePath.DEFER_PATH
    assert decision.retrieval_k == 0
    assert decision.max_reasoning_steps == 0
    assert decision.defer_reason == "critical_sensitivity_insufficient_evidence"
    assert decision.require_truth_gate is True


def test_high_sensitivity_low_evidence_verifies_without_defer() -> None:
    signals = ContinuityComputeSignals(
        context_freshness=ContextFreshness.FRESH,
        evidence_coverage=0.2,
        sensitivity=ComputeSensitivity.HIGH,
        continuity_available=True,
        important_claim=True,
    )

    decision = decide_compute_path("assess this important claim", continuity=signals)

    assert decision.path is ComputePath.VERIFY_PATH
    assert decision.defer_reason is None
    assert "continuity:sensitive_claim_requires_verification" in decision.reasons


def test_degraded_context_caps_deep_route_without_silent_drop() -> None:
    signals = ContinuityComputeSignals(
        context_degraded=True,
        context_freshness=ContextFreshness.FRESH,
        evidence_coverage=0.8,
        continuity_available=True,
    )

    decision = decide_compute_path(
        "analyze this architecture deeply",
        uncertainty=0.7,
        continuity=signals,
    )

    assert decision.path is ComputePath.NORMAL_PATH
    assert decision.retrieval_k == 8
    assert decision.max_reasoning_steps == 3
    assert decision.require_reflection is False
    assert "continuity:degraded_context_depth_cap" in decision.reasons


def test_degraded_context_does_not_downgrade_verify() -> None:
    signals = ContinuityComputeSignals(
        context_degraded=True,
        context_freshness=ContextFreshness.FRESH,
        evidence_coverage=0.9,
        active_contradictions=1,
        continuity_available=True,
        important_claim=True,
    )

    decision = decide_compute_path("check the claim", continuity=signals)

    assert decision.path is ComputePath.VERIFY_PATH
    assert decision.retrieval_k == 16
    assert decision.max_reasoning_steps == 6


def test_signal_validation_rejects_ambiguous_values() -> None:
    with pytest.raises(ValueError, match="evidence_coverage"):
        ContinuityComputeSignals(evidence_coverage=float("nan"))
    with pytest.raises(ValueError, match="active_contradictions"):
        ContinuityComputeSignals(active_contradictions=True)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="context_degraded"):
        ContinuityComputeSignals(context_degraded=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="uncertainty"):
        decide_compute_path("query", uncertainty=1.1)
    with pytest.raises(ValueError, match="candidate_count"):
        decide_compute_path("query", candidate_count=-1)


def test_decision_is_immutable_and_serializes_new_fields() -> None:
    decision = decide_compute_path(
        "continue the current task",
        continuity=ContinuityComputeSignals(
            context_freshness=ContextFreshness.STALE,
            continuity_available=True,
            requires_current_state=True,
        ),
    )

    with pytest.raises(FrozenInstanceError):
        decision.path = ComputePath.FAST_PATH  # type: ignore[misc]

    payload = decision.to_dict()
    assert payload["policy_version"] == COMPUTE_POLICY_VERSION
    assert payload["context_rebuild_required"] is True
    assert isinstance(payload["reasons"], list)


def test_same_inputs_produce_same_decision() -> None:
    signals = ContinuityComputeSignals(
        context_degraded=False,
        context_freshness=ContextFreshness.FRESH,
        evidence_coverage=0.75,
        active_contradictions=0,
        sensitivity=ComputeSensitivity.MEDIUM,
        continuity_available=True,
        important_claim=False,
        requires_current_state=False,
    )

    first = decide_compute_path(
        "explain the architecture",
        candidate_count=7,
        uncertainty=0.4,
        continuity=signals,
    )
    second = decide_compute_path(
        "explain the architecture",
        candidate_count=7,
        uncertainty=0.4,
        continuity=signals,
    )

    assert first == second
    assert first.to_dict() == second.to_dict()
