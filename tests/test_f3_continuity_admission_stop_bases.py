from __future__ import annotations

from datetime import UTC, datetime, timedelta
from hashlib import sha256

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
    ContinuitySourceBindingReceipt,
)
from core.continuity.source_admission_payloads import (
    ContinuityObservationDraft,
    ContinuitySourceEnvelope,
)

_NOW = datetime(2026, 8, 7, 18, 0, tzinfo=UTC)
_SUBJECT = SubjectRef(subject_id="subject:f3", kind=SubjectKind.PERSON)


def _scenario():
    principal = ContinuityPrincipalContext.create(
        principal_ref="principal:f3",
        principal_kind="human",
        authentication_method="oidc",
        authentication_strength="mfa",
        authenticated_at=_NOW - timedelta(minutes=20),
        issuer_ref="issuer:test",
        authentication_receipt_ref="authentication:f3",
    )
    authorization = ContinuityAuthorizationContext.create(
        tenant_ref="tenant:f3",
        subject_refs=(_SUBJECT,),
        principal_context=principal,
        purpose_code="continuity_analysis",
        lawful_basis_or_consent_ref="consent:active",
        authorization_receipt_ref="authorization:active",
        policy_snapshot_id="policy:current",
        retention_class="ephemeral",
        erasure_domain_refs=("erasure:f3",),
        valid_from=_NOW - timedelta(hours=1),
        valid_until=_NOW + timedelta(hours=1),
        data_handling_mode="local_only",
    )
    binding = ContinuitySourceBindingReceipt.create(
        source_type="state_reconciliation_result",
        source_result_id="state-result:f3",
        source_digest=sha256(b"state-result:f3").hexdigest(),
        source_owner="continuity.state_reconciler",
        tenant_ref="tenant:f3",
        subject_refs=(_SUBJECT,),
        source_component_version="1",
        source_policy_version="1",
        source_as_of=_NOW - timedelta(minutes=5),
        evidence_refs=("event:f3",),
        issued_at=_NOW - timedelta(minutes=4),
    )
    envelope = ContinuitySourceEnvelope.create(
        binding_receipt=binding,
        authorization_context=authorization,
        source_schema_version="continuity.state_projection.v1",
        producer_adapter_id="continuity.state_reconciliation_to_drafts",
        producer_adapter_version="1",
        created_at=_NOW - timedelta(minutes=3),
    )
    return principal, authorization, binding, envelope


def _rule(*, maximum_draft_age_seconds: int = 600):
    return ContinuityAdmissionRuleDefinition.create(
        rule_id="continuity.admission.f3",
        rule_version="1",
        allowed_source_types=("state_reconciliation_result",),
        allowed_adapter_ids=("continuity.state_reconciliation_to_drafts",),
        allowed_derivation_rule_ids=("state.context_degraded.v1",),
        allowed_signal_types=(ContinuitySignalType.CONTEXT_DEGRADED,),
        minimum_confidence=0.8,
        maximum_draft_age_seconds=maximum_draft_age_seconds,
        required_purpose_code="continuity_analysis",
        required_data_handling_mode="local_only",
        allowed_retention_classes=("ephemeral",),
    )


def _registry(rule):
    evaluator = ContinuityAdmissionEvaluatorDefinition.create(
        evaluator_id="continuity.admission_evaluator.f3",
        evaluator_version="1",
        allowed_rules=(rule,),
    )
    return ContinuityAdmissionRegistry.create(
        evaluator_definitions=(evaluator,),
        rule_definitions=(rule,),
    )


def _current(principal, authorization, *, authorization_status=ContinuityCurrentDecisionStatus.ACTIVE):
    return ContinuityCurrentDecisionEvidence.create(
        principal_context=principal,
        authorization_context=authorization,
        authorization_status=authorization_status,
        lawful_basis_status=ContinuityCurrentDecisionStatus.ACTIVE,
        restriction_status=ContinuityCurrentDecisionStatus.CLEAR,
        erasure_status=ContinuityCurrentDecisionStatus.CLEAR,
        observed_at=_NOW - timedelta(minutes=1),
        valid_until=_NOW + timedelta(minutes=10),
        evidence_refs=(
            "current:principal",
            "current:authorization",
            "current:consent",
            "current:restriction",
            "current:erasure",
            "current:policy",
        ),
    )


def _draft(envelope, *, confidence=1.0, created_at=None, tag="f3"):
    return ContinuityObservationDraft.create(
        source_envelope=envelope,
        signal_type=ContinuitySignalType.CONTEXT_DEGRADED,
        value=True,
        proposed_confidence=confidence,
        evidence_refs=envelope.evidence_refs,
        reason_codes=(f"reason:{tag}",),
        derivation_rule_id="state.context_degraded.v1",
        created_at=created_at or (_NOW - timedelta(minutes=2)),
        scope=f"scope:{tag}",
    )


def _evaluate(*, rule, authorization, binding, envelope, draft, current):
    return evaluate_continuity_admission(
        registry=_registry(rule),
        evaluator_id="continuity.admission_evaluator.f3",
        evaluator_version="1",
        rule_id="continuity.admission.f3",
        rule_version="1",
        source_envelope=envelope,
        binding_receipt=binding,
        authorization_context=authorization,
        drafts=(draft,),
        current_decision_evidence=current,
        evaluated_at=_NOW,
    )


def test_f3_same_rejection_preserves_authority_quality_and_freshness_bases() -> None:
    """Same no-admission outcome keeps three materially different existing bases."""
    principal, authorization, binding, envelope = _scenario()

    authority_rule = _rule()
    authority_draft = _draft(envelope, tag="authority")
    authority_stop = _evaluate(
        rule=authority_rule,
        authorization=authorization,
        binding=binding,
        envelope=envelope,
        draft=authority_draft,
        current=_current(
            principal,
            authorization,
            authorization_status=ContinuityCurrentDecisionStatus.WITHDRAWN,
        ),
    )

    quality_rule = _rule()
    quality_draft = _draft(envelope, confidence=0.2, tag="quality")
    quality_stop = _evaluate(
        rule=quality_rule,
        authorization=authorization,
        binding=binding,
        envelope=envelope,
        draft=quality_draft,
        current=_current(principal, authorization),
    )

    freshness_rule = _rule(maximum_draft_age_seconds=30)
    freshness_draft = _draft(
        envelope,
        created_at=_NOW - timedelta(minutes=2),
        tag="freshness",
    )
    freshness_stop = _evaluate(
        rule=freshness_rule,
        authorization=authorization,
        binding=binding,
        envelope=envelope,
        draft=freshness_draft,
        current=_current(principal, authorization),
    )

    stopped = (authority_stop, quality_stop, freshness_stop)
    assert all(result.admitted_draft_ids == () for result in stopped)
    assert all(len(result.rejected_drafts) == 1 for result in stopped)
    assert all(result.no_runtime_authority is True for result in stopped)
    assert tuple(result.rejected_drafts[0].reason_code for result in stopped) == (
        ContinuityAdmissionReason.CURRENT_AUTHORIZATION_NOT_ACTIVE.value,
        ContinuityAdmissionReason.CONFIDENCE_BELOW_MINIMUM.value,
        ContinuityAdmissionReason.DRAFT_STALE.value,
    )

    # Release each rejection by changing only the condition named by its existing
    # reason. This is not a retry scheduler or an automatic authority escalation.
    authority_released = _evaluate(
        rule=authority_rule,
        authorization=authorization,
        binding=binding,
        envelope=envelope,
        draft=authority_draft,
        current=_current(principal, authorization),
    )
    quality_released = _evaluate(
        rule=quality_rule,
        authorization=authorization,
        binding=binding,
        envelope=envelope,
        draft=_draft(envelope, confidence=1.0, tag="quality-released"),
        current=_current(principal, authorization),
    )
    freshness_released = _evaluate(
        rule=freshness_rule,
        authorization=authorization,
        binding=binding,
        envelope=envelope,
        draft=_draft(envelope, created_at=_NOW - timedelta(seconds=10), tag="freshness-released"),
        current=_current(principal, authorization),
    )

    for result in (authority_released, quality_released, freshness_released):
        assert len(result.admitted_draft_ids) == 1
        assert result.rejected_drafts == ()
        assert result.no_runtime_authority is True
