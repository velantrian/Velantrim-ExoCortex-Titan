"""Adversarial tests for the pure Continuity admission evaluator."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from hashlib import sha256

import pytest

from core.continuity.admission_evaluator import (
    ContinuityAdmissionEvaluatorDefinition,
    ContinuityAdmissionReason,
    ContinuityAdmissionRegistry,
    ContinuityAdmissionRuleDefinition,
    ContinuityCurrentDecisionEvidence,
    ContinuityCurrentDecisionStatus,
    evaluate_continuity_admission,
)
from core.continuity.contracts import SubjectKind, SubjectRef
from core.continuity.observations import ContinuitySignalType
from core.continuity.source_admission import (
    ContinuityAuthorizationContext,
    ContinuityPrincipalContext,
    ContinuitySourceAdmissionError,
    ContinuitySourceBindingReceipt,
)
from core.continuity.source_admission_payloads import (
    ContinuityObservationDraft,
    ContinuitySourceEnvelope,
)

_NOW = datetime(2026, 8, 7, 18, 0, tzinfo=UTC)
_SUBJECT = SubjectRef(subject_id="subject:alice", kind=SubjectKind.PERSON)


def _principal(*, suffix: str = "a") -> ContinuityPrincipalContext:
    return ContinuityPrincipalContext.create(
        principal_ref=f"principal:{suffix}",
        principal_kind="human",
        authentication_method="oidc",
        authentication_strength="mfa",
        authenticated_at=_NOW - timedelta(minutes=20),
        issuer_ref="issuer:test",
        authentication_receipt_ref=f"authentication:{suffix}",
    )


def _authorization(
    *,
    principal: ContinuityPrincipalContext | None = None,
    tenant_ref: str = "tenant:one",
    purpose_code: str = "continuity_analysis",
    data_handling_mode: str = "local_only",
    retention_class: str = "ephemeral",
) -> ContinuityAuthorizationContext:
    principal_value = principal or _principal()
    return ContinuityAuthorizationContext.create(
        tenant_ref=tenant_ref,
        subject_refs=(_SUBJECT,),
        principal_context=principal_value,
        purpose_code=purpose_code,
        lawful_basis_or_consent_ref="consent:active",
        authorization_receipt_ref="authorization:active",
        policy_snapshot_id="policy:current",
        retention_class=retention_class,
        erasure_domain_refs=("erasure:alice",),
        valid_from=_NOW - timedelta(hours=1),
        valid_until=_NOW + timedelta(hours=1),
        data_handling_mode=data_handling_mode,
    )


def _binding() -> ContinuitySourceBindingReceipt:
    return ContinuitySourceBindingReceipt.create(
        source_type="state_reconciliation_result",
        source_result_id="state-result:a",
        source_digest=sha256(b"state-result:a").hexdigest(),
        source_owner="continuity.state_reconciler",
        tenant_ref="tenant:one",
        subject_refs=(_SUBJECT,),
        source_component_version="1",
        source_policy_version="1",
        source_as_of=_NOW - timedelta(minutes=5),
        evidence_refs=("event:a",),
        issued_at=_NOW - timedelta(minutes=4),
    )


def _envelope(
    *,
    authorization: ContinuityAuthorizationContext | None = None,
    binding: ContinuitySourceBindingReceipt | None = None,
    adapter_id: str = "continuity.state_reconciliation_to_drafts",
) -> ContinuitySourceEnvelope:
    return ContinuitySourceEnvelope.create(
        binding_receipt=binding or _binding(),
        authorization_context=authorization or _authorization(),
        source_schema_version="continuity.state_projection.v1",
        producer_adapter_id=adapter_id,
        producer_adapter_version="1",
        created_at=_NOW - timedelta(minutes=3),
    )


def _draft(
    *,
    envelope: ContinuitySourceEnvelope | None = None,
    signal_type: ContinuitySignalType = ContinuitySignalType.CONTEXT_DEGRADED,
    value: object = True,
    confidence: float = 1.0,
    derivation_rule_id: str = "state.context_degraded.v1",
    tag: str = "a",
    created_at: datetime | None = None,
) -> ContinuityObservationDraft:
    envelope_value = envelope or _envelope()
    return ContinuityObservationDraft.create(
        source_envelope=envelope_value,
        signal_type=signal_type,
        value=value,
        proposed_confidence=confidence,
        evidence_refs=envelope_value.evidence_refs,
        reason_codes=(f"reason:{tag}",),
        derivation_rule_id=derivation_rule_id,
        created_at=created_at or (_NOW - timedelta(minutes=2)),
        scope=f"scope:{tag}",
    )


def _rule(**overrides: object) -> ContinuityAdmissionRuleDefinition:
    values: dict[str, object] = {
        "rule_id": "continuity.admission.default",
        "rule_version": "1",
        "allowed_source_types": (
            "state_reconciliation_result",
            "goal_projection_result",
            "open_loop_projection_result",
        ),
        "allowed_adapter_ids": (
            "continuity.state_reconciliation_to_drafts",
            "continuity.goal_projection_to_drafts",
            "continuity.open_loop_projection_to_drafts",
        ),
        "allowed_derivation_rule_ids": (
            "state.context_degraded.v1",
            "state.active_contradiction.v1",
            "state.context_freshness.v1",
            "goal.active_evidence_coverage.v1",
            "open_loop.active_evidence_coverage.v1",
        ),
        "allowed_signal_types": (
            ContinuitySignalType.CONTEXT_DEGRADED,
            ContinuitySignalType.ACTIVE_CONTRADICTION,
            ContinuitySignalType.CONTEXT_FRESHNESS,
            ContinuitySignalType.EVIDENCE_COVERAGE_ITEM,
        ),
        "minimum_confidence": 0.8,
        "maximum_draft_age_seconds": 600,
        "required_purpose_code": "continuity_analysis",
        "required_data_handling_mode": "local_only",
        "allowed_retention_classes": ("ephemeral",),
    }
    values.update(overrides)
    return ContinuityAdmissionRuleDefinition.create(**values)  # type: ignore[arg-type]


def _registry(
    *,
    rule: ContinuityAdmissionRuleDefinition | None = None,
    evaluator_id: str = "continuity.admission_evaluator",
    evaluator_version: str = "1",
) -> ContinuityAdmissionRegistry:
    rule_value = rule or _rule()
    evaluator = ContinuityAdmissionEvaluatorDefinition.create(
        evaluator_id=evaluator_id,
        evaluator_version=evaluator_version,
        allowed_rules=(rule_value,),
    )
    return ContinuityAdmissionRegistry.create(
        evaluator_definitions=(evaluator,),
        rule_definitions=(rule_value,),
    )


def _current(
    *,
    principal: ContinuityPrincipalContext | None = None,
    authorization: ContinuityAuthorizationContext | None = None,
    authorization_status: ContinuityCurrentDecisionStatus = (
        ContinuityCurrentDecisionStatus.ACTIVE
    ),
    lawful_basis_status: ContinuityCurrentDecisionStatus = (
        ContinuityCurrentDecisionStatus.ACTIVE
    ),
    restriction_status: ContinuityCurrentDecisionStatus = (
        ContinuityCurrentDecisionStatus.CLEAR
    ),
    erasure_status: ContinuityCurrentDecisionStatus = (
        ContinuityCurrentDecisionStatus.CLEAR
    ),
    observed_at: datetime | None = None,
    valid_until: datetime | None = None,
) -> ContinuityCurrentDecisionEvidence:
    principal_value = principal or _principal()
    authorization_value = authorization or _authorization(principal=principal_value)
    return ContinuityCurrentDecisionEvidence.create(
        principal_context=principal_value,
        authorization_context=authorization_value,
        authorization_status=authorization_status,
        lawful_basis_status=lawful_basis_status,
        restriction_status=restriction_status,
        erasure_status=erasure_status,
        observed_at=observed_at or (_NOW - timedelta(minutes=1)),
        valid_until=valid_until or (_NOW + timedelta(minutes=10)),
        evidence_refs=(
            "current:principal",
            "current:authorization",
            "current:consent",
            "current:restriction",
            "current:erasure",
            "current:policy",
        ),
    )


def _evaluate(
    *,
    registry: ContinuityAdmissionRegistry | None = None,
    authorization: ContinuityAuthorizationContext | None = None,
    binding: ContinuitySourceBindingReceipt | None = None,
    envelope: ContinuitySourceEnvelope | None = None,
    drafts: tuple[ContinuityObservationDraft, ...] | None = None,
    current: ContinuityCurrentDecisionEvidence | None = None,
    evaluator_id: str = "continuity.admission_evaluator",
    evaluator_version: str = "1",
    rule_id: str = "continuity.admission.default",
    rule_version: str = "1",
    evaluated_at: datetime = _NOW,
):
    authorization_value = authorization or _authorization()
    binding_value = binding or _binding()
    envelope_value = envelope or _envelope(
        authorization=authorization_value,
        binding=binding_value,
    )
    draft_values = drafts or (_draft(envelope=envelope_value),)
    current_value = current or _current(authorization=authorization_value)
    return evaluate_continuity_admission(
        registry=registry or _registry(),
        evaluator_id=evaluator_id,
        evaluator_version=evaluator_version,
        rule_id=rule_id,
        rule_version=rule_version,
        source_envelope=envelope_value,
        binding_receipt=binding_value,
        authorization_context=authorization_value,
        drafts=draft_values,
        current_decision_evidence=current_value,
        evaluated_at=evaluated_at,
    )


def test_evaluator_is_deterministic_and_admits_allowlisted_draft() -> None:
    first = _evaluate()
    second = _evaluate()

    assert first == second
    assert len(first.admitted_draft_ids) == 1
    assert first.rejected_drafts == ()
    assert first.receipt.admission_evaluator_id == first.evaluator_definition_id
    assert first.receipt.admission_rule_id == first.rule_definition_id
    assert first.no_runtime_authority is True


def test_draft_order_does_not_change_receipt_identity() -> None:
    authorization = _authorization()
    binding = _binding()
    envelope = _envelope(authorization=authorization, binding=binding)
    first = _draft(envelope=envelope, tag="first")
    second = _draft(
        envelope=envelope,
        signal_type=ContinuitySignalType.CONTEXT_FRESHNESS,
        value="fresh",
        derivation_rule_id="state.context_freshness.v1",
        tag="second",
    )
    current = _current(authorization=authorization)

    left = _evaluate(
        authorization=authorization,
        binding=binding,
        envelope=envelope,
        drafts=(first, second),
        current=current,
    )
    right = _evaluate(
        authorization=authorization,
        binding=binding,
        envelope=envelope,
        drafts=(second, first),
        current=current,
    )

    assert left.receipt.receipt_id == right.receipt.receipt_id
    assert left.admitted_draft_ids == right.admitted_draft_ids


def test_low_confidence_and_stale_drafts_are_rejected_with_stable_reasons() -> None:
    authorization = _authorization()
    binding = _binding()
    envelope = _envelope(authorization=authorization, binding=binding)
    low = _draft(envelope=envelope, confidence=0.2, tag="low")
    stale = _draft(
        envelope=envelope,
        created_at=_NOW - timedelta(minutes=20),
        tag="stale",
    )

    result = _evaluate(
        authorization=authorization,
        binding=binding,
        envelope=envelope,
        drafts=(low, stale),
        current=_current(authorization=authorization),
    )

    reasons = {value.draft_id: value.reason_code for value in result.rejected_drafts}
    assert reasons[low.draft_id] == ContinuityAdmissionReason.CONFIDENCE_BELOW_MINIMUM
    assert reasons[stale.draft_id] == ContinuityAdmissionReason.DRAFT_STALE
    assert result.admitted_draft_ids == ()


@pytest.mark.parametrize(
    ("field", "status", "reason"),
    [
        (
            "authorization_status",
            ContinuityCurrentDecisionStatus.WITHDRAWN,
            ContinuityAdmissionReason.CURRENT_AUTHORIZATION_NOT_ACTIVE,
        ),
        (
            "lawful_basis_status",
            ContinuityCurrentDecisionStatus.INACTIVE,
            ContinuityAdmissionReason.CURRENT_LAWFUL_BASIS_NOT_ACTIVE,
        ),
        (
            "restriction_status",
            ContinuityCurrentDecisionStatus.BLOCKED,
            ContinuityAdmissionReason.CURRENT_RESTRICTION_NOT_CLEAR,
        ),
        (
            "erasure_status",
            ContinuityCurrentDecisionStatus.BLOCKED,
            ContinuityAdmissionReason.CURRENT_ERASURE_NOT_CLEAR,
        ),
    ],
)
def test_current_status_blocks_every_draft(
    field: str,
    status: ContinuityCurrentDecisionStatus,
    reason: ContinuityAdmissionReason,
) -> None:
    authorization = _authorization()
    current = _current(authorization=authorization, **{field: status})
    result = _evaluate(authorization=authorization, current=current)

    assert result.admitted_draft_ids == ()
    assert {value.reason_code for value in result.rejected_drafts} == {reason.value}


def test_mismatched_or_expired_current_evidence_rejects_fail_closed() -> None:
    authorization = _authorization()
    other_principal = _principal(suffix="other")
    other_authorization = _authorization(
        principal=other_principal,
        tenant_ref="tenant:other",
    )
    mismatch = _current(
        principal=other_principal,
        authorization=other_authorization,
    )
    mismatched = _evaluate(authorization=authorization, current=mismatch)
    assert mismatched.rejected_drafts[0].reason_code == (
        ContinuityAdmissionReason.CURRENT_EVIDENCE_MISMATCH.value
    )

    stale = _current(
        authorization=authorization,
        observed_at=_NOW - timedelta(hours=1),
        valid_until=_NOW - timedelta(minutes=1),
    )
    expired = _evaluate(authorization=authorization, current=stale)
    assert expired.rejected_drafts[0].reason_code == (
        ContinuityAdmissionReason.CURRENT_EVIDENCE_STALE.value
    )


def test_unknown_or_nonallowlisted_evaluator_and_rule_fail_closed() -> None:
    with pytest.raises(ContinuitySourceAdmissionError, match="not allowlisted"):
        _evaluate(evaluator_id="unknown")
    with pytest.raises(ContinuitySourceAdmissionError, match="not allowlisted"):
        _evaluate(rule_id="unknown")


def test_rule_rejects_unapproved_adapter_derivation_and_signal() -> None:
    authorization = _authorization()
    binding = _binding()
    envelope = _envelope(
        authorization=authorization,
        binding=binding,
        adapter_id="continuity.unapproved_adapter",
    )
    draft = _draft(
        envelope=envelope,
        derivation_rule_id="unapproved.derivation",
        signal_type=ContinuitySignalType.REQUIRES_CURRENT_STATE,
    )
    result = _evaluate(
        authorization=authorization,
        binding=binding,
        envelope=envelope,
        drafts=(draft,),
        current=_current(authorization=authorization),
    )
    assert result.rejected_drafts[0].reason_code == (
        ContinuityAdmissionReason.ADAPTER_NOT_ALLOWED.value
    )


def test_registry_rejects_rule_not_allowlisted_for_evaluator() -> None:
    first = _rule(rule_id="first")
    second = _rule(rule_id="second")
    evaluator = ContinuityAdmissionEvaluatorDefinition.create(
        evaluator_id="continuity.admission_evaluator",
        evaluator_version="1",
        allowed_rules=(first,),
    )
    registry = ContinuityAdmissionRegistry.create(
        evaluator_definitions=(evaluator,),
        rule_definitions=(first, second),
    )
    with pytest.raises(ContinuitySourceAdmissionError, match="selected evaluator"):
        _evaluate(registry=registry, rule_id="second")


def test_definitions_and_current_evidence_are_frozen_and_tamper_evident() -> None:
    rule = _rule()
    registry = _registry(rule=rule)
    current = _current()

    with pytest.raises(FrozenInstanceError):
        rule.rule_id = "changed"  # type: ignore[misc]
    with pytest.raises(ContinuitySourceAdmissionError, match="canonical"):
        replace(rule, rule_definition_id="0" * 64)
    with pytest.raises(ContinuitySourceAdmissionError, match="canonical"):
        replace(registry, registry_id="0" * 64)
    with pytest.raises(ContinuitySourceAdmissionError, match="canonical"):
        replace(current, current_decision_evidence_id="0" * 64)


def test_missing_or_malformed_inputs_fail_without_receipt() -> None:
    with pytest.raises(ContinuitySourceAdmissionError, match="current_decision_evidence"):
        _evaluate(current="missing")  # type: ignore[arg-type]
    with pytest.raises(ContinuitySourceAdmissionError, match="duplicate"):
        authorization = _authorization()
        binding = _binding()
        envelope = _envelope(authorization=authorization, binding=binding)
        draft = _draft(envelope=envelope)
        _evaluate(
            authorization=authorization,
            binding=binding,
            envelope=envelope,
            drafts=(draft, draft),
            current=_current(authorization=authorization),
        )
