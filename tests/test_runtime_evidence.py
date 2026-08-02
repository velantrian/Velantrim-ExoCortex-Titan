from __future__ import annotations

import pytest

from core.runtime_evidence import (
    ActivationStage,
    FeatureActivationReceipt,
    ObservationResult,
    ObservationState,
    RuntimeEvidenceError,
    evaluate_hard_gates,
)


def test_not_observed_never_passes_a_hard_gate() -> None:
    observation = ObservationResult(
        feature_name="response_audit",
        metric_name="audit_events",
        state=ObservationState.NOT_OBSERVED,
        reason_code="event_bus_unavailable",
    )

    passed, failures = evaluate_hard_gates([observation])

    assert passed is False
    assert failures == ("response_audit:audit_events:not_observed",)


def test_observed_zero_passes_and_canonicalizes_sources() -> None:
    observation = ObservationResult(
        feature_name="continuity_shadow",
        metric_name="canon_writes",
        state=ObservationState.OBSERVED_ZERO,
        observed_value=0,
        source_refs=("receipt-b", "receipt-a", "receipt-a"),
    )

    passed, failures = evaluate_hard_gates([observation])

    assert passed is True
    assert failures == ()
    assert observation.source_refs == ("receipt-a", "receipt-b")


def test_effective_receipt_requires_observed_runtime() -> None:
    observation = ObservationResult(
        feature_name="continuity_shadow",
        metric_name="shadow_runs",
        state=ObservationState.NOT_OBSERVED,
        reason_code="observer_not_started",
    )

    with pytest.raises(RuntimeEvidenceError, match="observed runtime result"):
        FeatureActivationReceipt(
            feature_name="continuity_shadow",
            requested=True,
            configured=True,
            dependencies_ready=True,
            registered=True,
            started=True,
            observation=observation,
            effective=True,
        )


def test_observed_runtime_requires_started_stage() -> None:
    observation = ObservationResult(
        feature_name="response_audit",
        metric_name="audit_events",
        state=ObservationState.OBSERVED_ZERO,
        observed_value=0,
    )

    with pytest.raises(RuntimeEvidenceError, match="requires the feature to have started"):
        FeatureActivationReceipt(
            feature_name="response_audit",
            requested=True,
            configured=True,
            dependencies_ready=True,
            registered=True,
            started=False,
            observation=observation,
            effective=False,
            failure_reason="handler_not_started",
        )


def test_requested_but_ineffective_receipt_requires_reason() -> None:
    observation = ObservationResult(
        feature_name="response_audit",
        metric_name="audit_events",
        state=ObservationState.OBSERVER_FAILED,
        reason_code="handler_registration_failed",
    )

    with pytest.raises(RuntimeEvidenceError, match="requires failure_reason"):
        FeatureActivationReceipt(
            feature_name="response_audit",
            requested=True,
            configured=True,
            dependencies_ready=False,
            registered=False,
            started=False,
            observation=observation,
            effective=False,
        )


def test_highest_stage_reports_last_proven_stage() -> None:
    observation = ObservationResult(
        feature_name="response_audit",
        metric_name="audit_events",
        state=ObservationState.NOT_OBSERVED,
        reason_code="event_bus_unavailable",
    )
    receipt = FeatureActivationReceipt(
        feature_name="response_audit",
        requested=True,
        configured=True,
        dependencies_ready=False,
        registered=False,
        started=False,
        observation=observation,
        effective=False,
        failure_reason="event_bus_unavailable",
    )

    assert receipt.highest_stage is ActivationStage.CONFIGURED


def test_activation_stages_cannot_skip_failed_stage() -> None:
    observation = ObservationResult(
        feature_name="response_audit",
        metric_name="audit_events",
        state=ObservationState.NOT_OBSERVED,
        reason_code="invalid_stage_order",
    )

    with pytest.raises(RuntimeEvidenceError, match="cannot skip"):
        FeatureActivationReceipt(
            feature_name="response_audit",
            requested=True,
            configured=False,
            dependencies_ready=True,
            registered=False,
            started=False,
            observation=observation,
            effective=False,
            failure_reason="invalid_stage_order",
        )
