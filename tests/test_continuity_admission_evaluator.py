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
) -> ContinuityAuthorizationContext:
    principal_value = principal or _principal()
    return ContinuityAuthorizationContext.create(
        tenant_ref=tenant_ref,
        subject_refs=(_SUBJECT,),
        principal_context=principal_value,
        purpose_code="continuity_analysis",
        lawful_basis_or_consent_ref="consent:active",
        authorization_receipt_ref="authorization:active",
        policy_snapshot_id="policy:current",
        retention_class="ephemeral",
        erasure_domain_refs=("erasure:alice",),
        valid_from=_NOW - timedelta(hours=1),
        valid_until=_NOW + timedelta(hours=1),
        data_handling_mode="local_only",
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
    authorization: ContinuityAuthorizationContext,
    binding: ContinuitySourceBindingReceipt,
    adapter_id: str = "continuity.state_reconciliation_to_drafts",
) -> ContinuitySourceEnvelope:
    return ContinuitySourceEnvelope.create(
        binding_receipt=binding,
        authorization_context=authorization,
        source_schema_version="continuity.state_projection.v1",
        producer_adapter_id=adapter_id,
        producer_adapter_version="1",
        created_at=_NOW - timedelta(minutes=3),
    )


def _draft(
    *,
    envelope: ContinuitySourceEnvelope,
    signal_type: ContinuitySignalType = ContinuitySignalType.CONTEXT_DEGRADED,
    value: object = True,
    confidence: float = 1.0,
    derivation_rule_id: str = "state.context_degraded.v1",
    tag: str = "a",
    created_at: datetime | None = None,
) -> ContinuityObservationDraft:
    return ContinuityObservationDraft.create(
        source_envelope=envelope,
        signal_type=signal_type,
        value=value,
        proposed_confidence=confidence,
        evidence_refs=envelope.evidence_refs,
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
) -> ContinuityAdmissionRegistry:
    rule_value = rule or _rule()
    evaluator = ContinuityAdmissionEvaluatorDefinition.create(
        evaluator_id="continuity.admission_evaluator",
        evaluator_version="1",
        allowed_rules=(rule_value,),
    )
    return ContinuityAdmissionRegistry.create(
        evaluator_definitions=(evaluator,),
        rule_definitions=(rule_value,),
    )


def _current(
    *,
    principal: ContinuityPrincipalContext,
    authorization: ContinuityAuthorizationContext,
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
    return ContinuityCurrentDecisionEvidence.create(
        principal_context=principal,
        authorization_context=authorization,
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


def _scenario(
    *,
    adapter_id: str = "continuity.state_reconciliation_to_drafts",
) -> tuple[
    ContinuityPrincipalContext,
    ContinuityAuthorizationContext,
    ContinuitySourceBindingReceipt,
    ContinuitySourceEnvelope,
]:
    principal = _principal()
    authorization = _authorization(principal=principal)
    binding = _binding()
    envelope = _envelope(
        authorization=authorization,
        binding=binding,
        adapter_id=adapter_id,
    )
    return principal, authorization, binding, envelope


def _evaluate(
    *,
    registry: ContinuityAdmissionRegistry | None = None,
    authorization: ContinuityAuthorizationContext,
    binding: ContinuitySourceBindingReceipt,
    envelope: ContinuitySourceEnvelope,
    drafts: tuple[ContinuityObservationDraft, ...],
    current: ContinuityCurrentDecisionEvidence,
    evaluator_id: str = "continuity.admission_evaluator",
    rule_id: str = "continuity.admission.default",
):
    return evaluate_continuity_admission(
        registry=registry or _registry(),
        evaluator_id=evaluator_id,
        evaluator_version="1",
        rule_id=rule_id,
        rule_version="1",
        source_envelope=envelope,
        binding_receipt=binding,
        authorization_context=authorization,
        drafts=drafts,
        current_decision_evidence=current,
        evaluated_at=_NOW,
    )


def test_allowlisted_admission_is_deterministic_and_order_independent() -> None:
    principal, authorization, binding, envelope = _scenario()
    first = _draft(envelope=envelope, tag="first")
    second = _draft(
        envelope=envelope,
        signal_type=ContinuitySignalType.CONTEXT_FRESHNESS,
        value="fresh",
        derivation_rule_id="state.context_freshness.v1",
        tag="second",
    )
    current = _current(principal=principal, authorization=authorization)

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

    assert left == right
    assert left.receipt.receipt_id == right.receipt.receipt_id
    assert left.admitted_draft_ids == tuple(
        sorted((first.draft_id, second.draft_id))
    )
    assert left.rejected_drafts == ()
    assert left.no_runtime_authority is True


def test_low_confidence_and_stale_drafts_have_stable_reasons() -> None:
    principal, authorization, binding, envelope = _scenario()
    low = _draft(envelope=envelope, confidence=0.2, tag="low")
    stale = _draft(
        envelope=envelope,
        created_at=_NOW - timedelta(minutes=2),
        tag="stale",
    )
    registry = _registry(rule=_rule(maximum_draft_age_seconds=30))

    result = _evaluate(
        registry=registry,
        authorization=authorization,
        binding=binding,
        envelope=envelope,
        drafts=(low, stale),
        current=_current(principal=principal, authorization=authorization),
    )

    reasons = {value.draft_id: value.reason_code for value in result.rejected_drafts}
    assert reasons[low.draft_id] == (
        ContinuityAdmissionReason.CONFIDENCE_BELOW_MINIMUM.value
    )
    assert reasons[stale.draft_id] == ContinuityAdmissionReason.DRAFT_STALE.value
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
def test_current_decision_state_rejects_every_draft(
    field: str,
    status: ContinuityCurrentDecisionStatus,
    reason: ContinuityAdmissionReason,
) -> None:
    principal, authorization, binding, envelope = _scenario()
    draft = _draft(envelope=envelope)
    current = _current(
        principal=principal,
        authorization=authorization,
        **{field: status},
    )

    result = _evaluate(
        authorization=authorization,
        binding=binding,
        envelope=envelope,
        drafts=(draft,),
        current=current,
    )

    assert result.admitted_draft_ids == ()
    assert result.rejected_drafts[0].reason_code == reason.value


def test_mismatched_and_expired_current_evidence_reject_fail_closed() -> None:
    _, authorization, binding, envelope = _scenario()
    draft = _draft(envelope=envelope)
    other_principal = _principal(suffix="other")
    other_authorization = _authorization(
        principal=other_principal,
        tenant_ref="tenant:other",
    )
    mismatch = _current(
        principal=other_principal,
        authorization=other_authorization,
    )
    mismatched = _evaluate(
        authorization=authorization,
        binding=binding,
        envelope=envelope,
        drafts=(draft,),
        current=mismatch,
    )
    assert mismatched.rejected_drafts[0].reason_code == (
        ContinuityAdmissionReason.CURRENT_EVIDENCE_MISMATCH.value
    )

    principal = _principal()
    authorization = _authorization(principal=principal)
    envelope = _envelope(authorization=authorization, binding=binding)
    draft = _draft(envelope=envelope)
    expired = _current(
        principal=principal,
        authorization=authorization,
        observed_at=_NOW - timedelta(hours=1),
        valid_until=_NOW - timedelta(minutes=1),
    )
    stale_result = _evaluate(
        authorization=authorization,
        binding=binding,
        envelope=envelope,
        drafts=(draft,),
        current=expired,
    )
    assert stale_result.rejected_drafts[0].reason_code == (
        ContinuityAdmissionReason.CURRENT_EVIDENCE_STALE.value
    )


def test_unknown_evaluator_rule_and_evaluator_specific_rule_fail_closed() -> None:
    principal, authorization, binding, envelope = _scenario()
    draft = _draft(envelope=envelope)
    current = _current(principal=principal, authorization=authorization)

    with pytest.raises(ContinuitySourceAdmissionError, match="not allowlisted"):
        _evaluate(
            authorization=authorization,
            binding=binding,
            envelope=envelope,
            drafts=(draft,),
            current=current,
            evaluator_id="unknown",
        )
    with pytest.raises(ContinuitySourceAdmissionError, match="not allowlisted"):
        _evaluate(
            authorization=authorization,
            binding=binding,
            envelope=envelope,
            drafts=(draft,),
            current=current,
            rule_id="unknown",
        )

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
        _evaluate(
            registry=registry,
            authorization=authorization,
            binding=binding,
            envelope=envelope,
            drafts=(draft,),
            current=current,
            rule_id="second",
        )


def test_unapproved_adapter_is_rejected_before_weaker_rule_failures() -> None:
    principal, authorization, binding, envelope = _scenario(
        adapter_id="continuity.unapproved_adapter"
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
        current=_current(principal=principal, authorization=authorization),
    )
    assert result.rejected_drafts[0].reason_code == (
        ContinuityAdmissionReason.ADAPTER_NOT_ALLOWED.value
    )


def test_definitions_registry_and_current_evidence_are_tamper_evident() -> None:
    principal, authorization, _, _ = _scenario()
    rule = _rule()
    registry = _registry(rule=rule)
    current = _current(principal=principal, authorization=authorization)

    with pytest.raises(FrozenInstanceError):
        rule.rule_id = "changed"  # type: ignore[misc]
    with pytest.raises(ContinuitySourceAdmissionError, match="canonical"):
        replace(rule, rule_definition_id="0" * 64)
    with pytest.raises(ContinuitySourceAdmissionError, match="canonical"):
        replace(registry, registry_id="0" * 64)
    with pytest.raises(ContinuitySourceAdmissionError, match="canonical"):
        replace(current, current_decision_evidence_id="0" * 64)


def test_duplicate_or_malformed_inputs_fail_without_receipt() -> None:
    principal, authorization, binding, envelope = _scenario()
    draft = _draft(envelope=envelope)
    current = _current(principal=principal, authorization=authorization)

    with pytest.raises(ContinuitySourceAdmissionError, match="duplicate"):
        _evaluate(
            authorization=authorization,
            binding=binding,
            envelope=envelope,
            drafts=(draft, draft),
            current=current,
        )
    with pytest.raises(ContinuitySourceAdmissionError, match="current_decision_evidence"):
        evaluate_continuity_admission(
            registry=_registry(),
            evaluator_id="continuity.admission_evaluator",
            evaluator_version="1",
            rule_id="continuity.admission.default",
            rule_version="1",
            source_envelope=envelope,
            binding_receipt=binding,
            authorization_context=authorization,
            drafts=(draft,),
            current_decision_evidence="missing",  # type: ignore[arg-type]
            evaluated_at=_NOW,
        )
