"""Pre-resolution hardening tests for the Continuity admission facade."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from hashlib import sha256

import pytest

from core.continuity.admission_evaluator import (
    ContinuityAdmissionEvaluatorDefinition,
    ContinuityAdmissionRegistry,
    ContinuityAdmissionRuleDefinition,
    ContinuityCurrentDecisionEvidence,
    ContinuityCurrentDecisionStatus,
)
from core.continuity.admission_facade import (
    ContinuityAdmissionFacadePolicy,
    evaluate_continuity_admission_facade,
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

_NOW = datetime(2026, 8, 7, 22, 0, tzinfo=UTC)
_SUBJECT = SubjectRef(subject_id="subject:alice", kind=SubjectKind.PERSON)


def _principal() -> ContinuityPrincipalContext:
    return ContinuityPrincipalContext.create(
        principal_ref="principal:alice",
        principal_kind="human",
        authentication_method="oidc",
        authentication_strength="mfa",
        authenticated_at=_NOW - timedelta(minutes=20),
        issuer_ref="issuer:test",
        authentication_receipt_ref="authentication:alice",
    )


def _authorization(
    principal: ContinuityPrincipalContext,
) -> ContinuityAuthorizationContext:
    return ContinuityAuthorizationContext.create(
        tenant_ref="tenant:one",
        subject_refs=(_SUBJECT,),
        principal_context=principal,
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


def _binding(*, suffix: str) -> ContinuitySourceBindingReceipt:
    return ContinuitySourceBindingReceipt.create(
        source_type="state_reconciliation_result",
        source_result_id=f"state-result:{suffix}",
        source_digest=sha256(f"state-result:{suffix}".encode()).hexdigest(),
        source_owner="continuity.state_reconciler",
        tenant_ref="tenant:one",
        subject_refs=(_SUBJECT,),
        source_component_version="1",
        source_policy_version="1",
        source_as_of=_NOW - timedelta(minutes=5),
        evidence_refs=(f"event:{suffix}",),
        issued_at=_NOW - timedelta(minutes=4),
    )


def _envelope(
    *,
    authorization: ContinuityAuthorizationContext,
    binding: ContinuitySourceBindingReceipt,
) -> ContinuitySourceEnvelope:
    return ContinuitySourceEnvelope.create(
        binding_receipt=binding,
        authorization_context=authorization,
        source_schema_version="continuity.state_projection.v1",
        producer_adapter_id="continuity.state_reconciliation_to_drafts",
        producer_adapter_version="1",
        created_at=_NOW - timedelta(minutes=3),
    )


def _draft(
    *,
    envelope: ContinuitySourceEnvelope,
    tag: str,
) -> ContinuityObservationDraft:
    return ContinuityObservationDraft.create(
        source_envelope=envelope,
        signal_type=ContinuitySignalType.CONTEXT_DEGRADED,
        value=True,
        proposed_confidence=1.0,
        evidence_refs=envelope.evidence_refs,
        reason_codes=(f"reason:{tag}",),
        derivation_rule_id="state.context_degraded.v1",
        created_at=_NOW - timedelta(minutes=2),
        scope=f"scope:{tag}",
    )


def _registry() -> ContinuityAdmissionRegistry:
    rule = ContinuityAdmissionRuleDefinition.create(
        rule_id="continuity.admission.default",
        rule_version="1",
        allowed_source_types=("state_reconciliation_result",),
        allowed_adapter_ids=("continuity.state_reconciliation_to_drafts",),
        allowed_derivation_rule_ids=("state.context_degraded.v1",),
        allowed_signal_types=(ContinuitySignalType.CONTEXT_DEGRADED,),
        minimum_confidence=0.8,
        maximum_draft_age_seconds=600,
        required_purpose_code="continuity_analysis",
        required_data_handling_mode="local_only",
        allowed_retention_classes=("ephemeral",),
    )
    evaluator = ContinuityAdmissionEvaluatorDefinition.create(
        evaluator_id="continuity.admission_evaluator",
        evaluator_version="1",
        allowed_rules=(rule,),
    )
    return ContinuityAdmissionRegistry.create(
        evaluator_definitions=(evaluator,),
        rule_definitions=(rule,),
    )


def _current(
    *,
    principal: ContinuityPrincipalContext,
    authorization: ContinuityAuthorizationContext,
) -> ContinuityCurrentDecisionEvidence:
    return ContinuityCurrentDecisionEvidence.create(
        principal_context=principal,
        authorization_context=authorization,
        authorization_status=ContinuityCurrentDecisionStatus.ACTIVE,
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


def _policy(registry: ContinuityAdmissionRegistry) -> ContinuityAdmissionFacadePolicy:
    return ContinuityAdmissionFacadePolicy.create(
        expected_registry=registry,
        evaluator_id="continuity.admission_evaluator",
        evaluator_version="1",
        rule_id="continuity.admission.default",
        rule_version="1",
        resolver_id="continuity.current_decision_resolver",
        resolver_version="1",
    )


@dataclass(slots=True)
class _CountingResolver:
    evidence: ContinuityCurrentDecisionEvidence
    resolver_id: str = "continuity.current_decision_resolver"
    resolver_version: str = "1"
    calls: int = 0

    def resolve_current_decision(
        self,
        *,
        principal_context: ContinuityPrincipalContext,
        authorization_context: ContinuityAuthorizationContext,
        source_envelope: ContinuitySourceEnvelope,
        binding_receipt: ContinuitySourceBindingReceipt,
        evaluated_at: datetime,
    ) -> ContinuityCurrentDecisionEvidence:
        del (
            principal_context,
            authorization_context,
            source_envelope,
            binding_receipt,
            evaluated_at,
        )
        self.calls += 1
        return self.evidence


class _ExplodingIdentityResolver:
    @property
    def resolver_id(self) -> str:
        raise RuntimeError("identity unavailable")

    @property
    def resolver_version(self) -> str:
        return "1"

    def resolve_current_decision(
        self,
        *,
        principal_context: ContinuityPrincipalContext,
        authorization_context: ContinuityAuthorizationContext,
        source_envelope: ContinuitySourceEnvelope,
        binding_receipt: ContinuitySourceBindingReceipt,
        evaluated_at: datetime,
    ) -> ContinuityCurrentDecisionEvidence:
        raise AssertionError("resolver method must not be called")


def _scenario() -> tuple[
    ContinuityPrincipalContext,
    ContinuityAuthorizationContext,
    ContinuitySourceBindingReceipt,
    ContinuitySourceEnvelope,
    ContinuityObservationDraft,
    ContinuityAdmissionRegistry,
]:
    principal = _principal()
    authorization = _authorization(principal)
    binding = _binding(suffix="primary")
    envelope = _envelope(authorization=authorization, binding=binding)
    draft = _draft(envelope=envelope, tag="primary")
    return principal, authorization, binding, envelope, draft, _registry()


def test_duplicate_drafts_fail_before_current_resolver_call() -> None:
    principal, authorization, binding, envelope, draft, registry = _scenario()
    resolver = _CountingResolver(
        _current(principal=principal, authorization=authorization)
    )

    with pytest.raises(ContinuitySourceAdmissionError, match="duplicate IDs"):
        evaluate_continuity_admission_facade(
            policy=_policy(registry),
            registry=registry,
            resolver=resolver,
            principal_context=principal,
            authorization_context=authorization,
            source_envelope=envelope,
            binding_receipt=binding,
            drafts=(draft, draft),
            evaluated_at=_NOW,
        )

    assert resolver.calls == 0


def test_cross_envelope_draft_fails_before_current_resolver_call() -> None:
    principal, authorization, binding, envelope, _, registry = _scenario()
    other_binding = _binding(suffix="other")
    other_envelope = _envelope(
        authorization=authorization,
        binding=other_binding,
    )
    other_draft = _draft(envelope=other_envelope, tag="other")
    resolver = _CountingResolver(
        _current(principal=principal, authorization=authorization)
    )

    with pytest.raises(ContinuitySourceAdmissionError, match="supplied source envelope"):
        evaluate_continuity_admission_facade(
            policy=_policy(registry),
            registry=registry,
            resolver=resolver,
            principal_context=principal,
            authorization_context=authorization,
            source_envelope=envelope,
            binding_receipt=binding,
            drafts=(other_draft,),
            evaluated_at=_NOW,
        )

    assert resolver.calls == 0


def test_resolver_identity_property_failure_is_controlled() -> None:
    principal, authorization, binding, envelope, draft, registry = _scenario()

    with pytest.raises(
        ContinuitySourceAdmissionError,
        match="resolver identity failed closed",
    ):
        evaluate_continuity_admission_facade(
            policy=_policy(registry),
            registry=registry,
            resolver=_ExplodingIdentityResolver(),
            principal_context=principal,
            authorization_context=authorization,
            source_envelope=envelope,
            binding_receipt=binding,
            drafts=(draft,),
            evaluated_at=_NOW,
        )
