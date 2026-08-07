"""Adversarial tests for the internal Continuity admission-aware facade."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime, timedelta
from hashlib import sha256

import pytest

import core.continuity as continuity_package
from core.continuity.admission_evaluator import (
    ContinuityAdmissionEvaluatorDefinition,
    ContinuityAdmissionRegistry,
    ContinuityAdmissionRuleDefinition,
    ContinuityCurrentDecisionEvidence,
    ContinuityCurrentDecisionStatus,
)
from core.continuity.admission_facade import (
    ContinuityAdmissionFacadePolicy,
    ContinuityCurrentDecisionResolver,
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

_NOW = datetime(2026, 8, 7, 21, 0, tzinfo=UTC)
_SUBJECT = SubjectRef(subject_id="subject:alice", kind=SubjectKind.PERSON)
_OTHER_SUBJECT = SubjectRef(subject_id="subject:bob", kind=SubjectKind.PERSON)


def _principal(*, suffix: str = "alice") -> ContinuityPrincipalContext:
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
    principal: ContinuityPrincipalContext,
    subjects: tuple[SubjectRef, ...] = (_SUBJECT,),
    tenant_ref: str = "tenant:one",
) -> ContinuityAuthorizationContext:
    return ContinuityAuthorizationContext.create(
        tenant_ref=tenant_ref,
        subject_refs=subjects,
        principal_context=principal,
        purpose_code="continuity_analysis",
        lawful_basis_or_consent_ref="consent:active",
        authorization_receipt_ref="authorization:active",
        policy_snapshot_id="policy:current",
        retention_class="ephemeral",
        erasure_domain_refs=tuple(
            f"erasure:{value.subject_id}" for value in subjects
        ),
        valid_from=_NOW - timedelta(hours=1),
        valid_until=_NOW + timedelta(hours=1),
        data_handling_mode="local_only",
    )


def _binding(
    *,
    subjects: tuple[SubjectRef, ...] = (_SUBJECT,),
    suffix: str = "a",
) -> ContinuitySourceBindingReceipt:
    return ContinuitySourceBindingReceipt.create(
        source_type="state_reconciliation_result",
        source_result_id=f"state-result:{suffix}",
        source_digest=sha256(f"state-result:{suffix}".encode()).hexdigest(),
        source_owner="continuity.state_reconciler",
        tenant_ref="tenant:one",
        subject_refs=subjects,
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
    tag: str = "a",
    confidence: float = 1.0,
) -> ContinuityObservationDraft:
    return ContinuityObservationDraft.create(
        source_envelope=envelope,
        signal_type=ContinuitySignalType.CONTEXT_DEGRADED,
        value=True,
        proposed_confidence=confidence,
        evidence_refs=envelope.evidence_refs,
        reason_codes=(f"reason:{tag}",),
        derivation_rule_id="state.context_degraded.v1",
        created_at=_NOW - timedelta(minutes=2),
        scope=f"scope:{tag}",
    )


def _rule(*, suffix: str = "default") -> ContinuityAdmissionRuleDefinition:
    return ContinuityAdmissionRuleDefinition.create(
        rule_id=f"continuity.admission.{suffix}",
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


def _registry(*, suffix: str = "default") -> ContinuityAdmissionRegistry:
    rule = _rule(suffix=suffix)
    evaluator = ContinuityAdmissionEvaluatorDefinition.create(
        evaluator_id="continuity.admission_evaluator",
        evaluator_version="1",
        allowed_rules=(rule,),
    )
    return ContinuityAdmissionRegistry.create(
        evaluator_definitions=(evaluator,),
        rule_definitions=(rule,),
    )


def _current_evidence(
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
) -> ContinuityCurrentDecisionEvidence:
    return ContinuityCurrentDecisionEvidence.create(
        principal_context=principal,
        authorization_context=authorization,
        authorization_status=authorization_status,
        lawful_basis_status=lawful_basis_status,
        restriction_status=restriction_status,
        erasure_status=erasure_status,
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


@dataclass(slots=True)
class _StaticResolver:
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


@dataclass(slots=True)
class _FailingResolver:
    resolver_id: str = "continuity.current_decision_resolver"
    resolver_version: str = "1"

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
        raise RuntimeError("resolver unavailable")


def _scenario(
    *,
    subjects: tuple[SubjectRef, ...] = (_SUBJECT,),
) -> tuple[
    ContinuityPrincipalContext,
    ContinuityAuthorizationContext,
    ContinuitySourceBindingReceipt,
    ContinuitySourceEnvelope,
    ContinuityObservationDraft,
    ContinuityAdmissionRegistry,
]:
    principal = _principal()
    authorization = _authorization(principal=principal, subjects=subjects)
    binding = _binding(subjects=subjects)
    envelope = _envelope(authorization=authorization, binding=binding)
    draft = _draft(envelope=envelope)
    return principal, authorization, binding, envelope, draft, _registry()


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


def test_facade_is_deterministic_and_pins_registry_and_resolver() -> None:
    principal, authorization, binding, envelope, draft, registry = _scenario()
    evidence = _current_evidence(
        principal=principal,
        authorization=authorization,
    )
    resolver = _StaticResolver(evidence)
    policy = _policy(registry)

    first = evaluate_continuity_admission_facade(
        policy=policy,
        registry=registry,
        resolver=resolver,
        principal_context=principal,
        authorization_context=authorization,
        source_envelope=envelope,
        binding_receipt=binding,
        drafts=(draft,),
        evaluated_at=_NOW,
    )
    second = evaluate_continuity_admission_facade(
        policy=policy,
        registry=registry,
        resolver=resolver,
        principal_context=principal,
        authorization_context=authorization,
        source_envelope=envelope,
        binding_receipt=binding,
        drafts=(draft,),
        evaluated_at=_NOW,
    )

    assert first == second
    assert first.facade_result_id == second.facade_result_id
    assert first.evaluation.admitted_draft_ids == (draft.draft_id,)
    assert first.evaluation.rejected_drafts == ()
    assert first.no_runtime_authority is True
    assert resolver.calls == 2


def test_policy_rejects_substituted_registry_before_resolver_call() -> None:
    principal, authorization, binding, envelope, draft, registry = _scenario()
    resolver = _StaticResolver(
        _current_evidence(principal=principal, authorization=authorization)
    )

    with pytest.raises(ContinuitySourceAdmissionError, match="pinned facade policy"):
        evaluate_continuity_admission_facade(
            policy=_policy(registry),
            registry=_registry(suffix="other"),
            resolver=resolver,
            principal_context=principal,
            authorization_context=authorization,
            source_envelope=envelope,
            binding_receipt=binding,
            drafts=(draft,),
            evaluated_at=_NOW,
        )

    assert resolver.calls == 0


def test_policy_rejects_resolver_identity_mismatch() -> None:
    principal, authorization, binding, envelope, draft, registry = _scenario()
    resolver = _StaticResolver(
        _current_evidence(principal=principal, authorization=authorization),
        resolver_version="2",
    )

    with pytest.raises(ContinuitySourceAdmissionError, match="resolver identity"):
        evaluate_continuity_admission_facade(
            policy=_policy(registry),
            registry=registry,
            resolver=resolver,
            principal_context=principal,
            authorization_context=authorization,
            source_envelope=envelope,
            binding_receipt=binding,
            drafts=(draft,),
            evaluated_at=_NOW,
        )

    assert resolver.calls == 0


def test_resolver_failure_is_controlled_and_fail_closed() -> None:
    principal, authorization, binding, envelope, draft, registry = _scenario()

    with pytest.raises(ContinuitySourceAdmissionError, match="failed closed"):
        evaluate_continuity_admission_facade(
            policy=_policy(registry),
            registry=registry,
            resolver=_FailingResolver(),
            principal_context=principal,
            authorization_context=authorization,
            source_envelope=envelope,
            binding_receipt=binding,
            drafts=(draft,),
            evaluated_at=_NOW,
        )


def test_resolver_must_cover_exact_authorization_subject_set() -> None:
    principal, authorization, binding, envelope, draft, registry = _scenario(
        subjects=(_SUBJECT, _OTHER_SUBJECT)
    )
    partial_authorization = _authorization(
        principal=principal,
        subjects=(_SUBJECT,),
    )
    resolver = _StaticResolver(
        _current_evidence(
            principal=principal,
            authorization=partial_authorization,
        )
    )

    with pytest.raises(ContinuitySourceAdmissionError, match="exact principal"):
        evaluate_continuity_admission_facade(
            policy=_policy(registry),
            registry=registry,
            resolver=resolver,
            principal_context=principal,
            authorization_context=authorization,
            source_envelope=envelope,
            binding_receipt=binding,
            drafts=(draft,),
            evaluated_at=_NOW,
        )


def test_current_blocking_state_produces_rejection_evidence_not_authority() -> None:
    principal, authorization, binding, envelope, draft, registry = _scenario()
    resolver = _StaticResolver(
        _current_evidence(
            principal=principal,
            authorization=authorization,
            erasure_status=ContinuityCurrentDecisionStatus.BLOCKED,
        )
    )

    result = evaluate_continuity_admission_facade(
        policy=_policy(registry),
        registry=registry,
        resolver=resolver,
        principal_context=principal,
        authorization_context=authorization,
        source_envelope=envelope,
        binding_receipt=binding,
        drafts=(draft,),
        evaluated_at=_NOW,
    )

    assert result.evaluation.admitted_draft_ids == ()
    assert result.evaluation.rejected_drafts[0].reason_code == (
        "current_erasure_not_clear"
    )
    assert result.no_runtime_authority is True


def test_cross_contract_binding_substitution_fails_before_resolution() -> None:
    principal, authorization, binding, envelope, draft, registry = _scenario()
    resolver = _StaticResolver(
        _current_evidence(principal=principal, authorization=authorization)
    )

    with pytest.raises(ContinuitySourceAdmissionError, match="binding receipt"):
        evaluate_continuity_admission_facade(
            policy=_policy(registry),
            registry=registry,
            resolver=resolver,
            principal_context=principal,
            authorization_context=authorization,
            source_envelope=envelope,
            binding_receipt=_binding(suffix="other"),
            drafts=(draft,),
            evaluated_at=_NOW,
        )

    assert resolver.calls == 0


def test_policy_and_result_are_frozen_and_tamper_evident() -> None:
    principal, authorization, binding, envelope, draft, registry = _scenario()
    policy = _policy(registry)
    result = evaluate_continuity_admission_facade(
        policy=policy,
        registry=registry,
        resolver=_StaticResolver(
            _current_evidence(principal=principal, authorization=authorization)
        ),
        principal_context=principal,
        authorization_context=authorization,
        source_envelope=envelope,
        binding_receipt=binding,
        drafts=(draft,),
        evaluated_at=_NOW,
    )

    with pytest.raises(FrozenInstanceError):
        policy.rule_id = "changed"  # type: ignore[misc]
    with pytest.raises(ContinuitySourceAdmissionError, match="canonical"):
        replace(policy, facade_policy_id="0" * 64)
    with pytest.raises(ContinuitySourceAdmissionError, match="canonical"):
        replace(result, facade_result_id="0" * 64)


def test_facade_remains_internal_and_unexported() -> None:
    assert isinstance(_FailingResolver(), ContinuityCurrentDecisionResolver)
    assert not hasattr(
        continuity_package,
        "evaluate_continuity_admission_facade",
    )
    assert not hasattr(continuity_package, "ContinuityAdmissionFacadePolicy")
