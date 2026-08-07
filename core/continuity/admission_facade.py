"""Internal admission-aware facade for Continuity source evidence.

This module pins one content-addressed evaluator registry and one typed current-decision
resolver identity before invoking the pure admission evaluator. It is an internal,
explicitly invoked boundary. It does not call the signal producer, build a live runtime
path, persist artifacts, read process-global configuration, answer, remind, notify,
execute tools/actions, route compute, or mutate Canon/ESM/TruthGate/GoalStack.

The facade verifies represented evidence and resolver identity. Deployment/operator
selection of the facade policy remains an external trust decision; this module does not
select or activate itself.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, runtime_checkable

from .admission_evaluator import (
    ContinuityAdmissionEvaluationResult,
    ContinuityAdmissionRegistry,
    ContinuityCurrentDecisionEvidence,
    evaluate_continuity_admission,
)
from .contracts import SubjectRef
from .source_admission import (
    ContinuityAuthorizationContext,
    ContinuityPrincipalContext,
    ContinuitySourceAdmissionError,
    ContinuitySourceBindingReceipt,
    _aware,
    _canonical_datetime,
    _digest,
    _hash,
    _items,
    _text,
    _verify_id,
)
from .source_admission_payloads import (
    ContinuityObservationDraft,
    ContinuitySourceEnvelope,
)

ADMISSION_FACADE_SCHEMA_VERSION = "continuity.admission_facade.v1"
_POLICY_AUTHORITY = "admission_facade_policy_only"
_RESULT_AUTHORITY = "admission_facade_evidence_only"


def _subject_keys(subjects: tuple[SubjectRef, ...]) -> tuple[tuple[str, str], ...]:
    return tuple((value.subject_id, value.kind.value) for value in subjects)


@runtime_checkable
class ContinuityCurrentDecisionResolver(Protocol):
    """Typed resolver boundary; implementations remain owned outside Continuity."""

    @property
    def resolver_id(self) -> str: ...

    @property
    def resolver_version(self) -> str: ...

    def resolve_current_decision(
        self,
        *,
        principal_context: ContinuityPrincipalContext,
        authorization_context: ContinuityAuthorizationContext,
        source_envelope: ContinuitySourceEnvelope,
        binding_receipt: ContinuitySourceBindingReceipt,
        evaluated_at: datetime,
    ) -> ContinuityCurrentDecisionEvidence: ...


@dataclass(frozen=True, slots=True)
class ContinuityAdmissionFacadePolicy:
    """Pinned evidence configuration for one internal facade invocation family."""

    facade_policy_id: str
    schema_version: str
    expected_registry_id: str
    evaluator_id: str
    evaluator_version: str
    rule_id: str
    rule_version: str
    resolver_id: str
    resolver_version: str
    authority: str = _POLICY_AUTHORITY
    no_runtime_authority: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "schema_version",
            _text(self.schema_version, "schema_version"),
        )
        object.__setattr__(
            self,
            "expected_registry_id",
            _hash(self.expected_registry_id, "expected_registry_id"),
        )
        for field_name in (
            "evaluator_id",
            "evaluator_version",
            "rule_id",
            "rule_version",
            "resolver_id",
            "resolver_version",
        ):
            object.__setattr__(
                self,
                field_name,
                _text(getattr(self, field_name), field_name),
            )
        object.__setattr__(self, "authority", _text(self.authority, "authority"))
        if self.authority != _POLICY_AUTHORITY:
            raise ContinuitySourceAdmissionError(
                f"authority must be {_POLICY_AUTHORITY!r}"
            )
        if self.no_runtime_authority is not True:
            raise ContinuitySourceAdmissionError(
                "no_runtime_authority must remain True"
            )
        _verify_id(
            self.facade_policy_id,
            _digest(self.identity_payload()),
            "facade_policy_id",
        )

    @classmethod
    def create(
        cls,
        *,
        expected_registry: ContinuityAdmissionRegistry,
        evaluator_id: str,
        evaluator_version: str,
        rule_id: str,
        rule_version: str,
        resolver_id: str,
        resolver_version: str,
        schema_version: str = ADMISSION_FACADE_SCHEMA_VERSION,
    ) -> ContinuityAdmissionFacadePolicy:
        if not isinstance(expected_registry, ContinuityAdmissionRegistry):
            raise ContinuitySourceAdmissionError(
                "expected_registry must be a ContinuityAdmissionRegistry"
            )
        version = _text(schema_version, "schema_version")
        evaluator_name = _text(evaluator_id, "evaluator_id")
        evaluator_revision = _text(evaluator_version, "evaluator_version")
        rule_name = _text(rule_id, "rule_id")
        rule_revision = _text(rule_version, "rule_version")
        resolver_name = _text(resolver_id, "resolver_id")
        resolver_revision = _text(resolver_version, "resolver_version")
        expected_registry.resolve(
            evaluator_id=evaluator_name,
            evaluator_version=evaluator_revision,
            rule_id=rule_name,
            rule_version=rule_revision,
        )
        payload: dict[str, object] = {
            "schema_version": version,
            "expected_registry_id": expected_registry.registry_id,
            "evaluator_id": evaluator_name,
            "evaluator_version": evaluator_revision,
            "rule_id": rule_name,
            "rule_version": rule_revision,
            "resolver_id": resolver_name,
            "resolver_version": resolver_revision,
            "authority": _POLICY_AUTHORITY,
            "no_runtime_authority": True,
        }
        return cls(
            facade_policy_id=_digest(payload),
            schema_version=version,
            expected_registry_id=expected_registry.registry_id,
            evaluator_id=evaluator_name,
            evaluator_version=evaluator_revision,
            rule_id=rule_name,
            rule_version=rule_revision,
            resolver_id=resolver_name,
            resolver_version=resolver_revision,
            authority=_POLICY_AUTHORITY,
            no_runtime_authority=True,
        )

    def identity_payload(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "expected_registry_id": self.expected_registry_id,
            "evaluator_id": self.evaluator_id,
            "evaluator_version": self.evaluator_version,
            "rule_id": self.rule_id,
            "rule_version": self.rule_version,
            "resolver_id": self.resolver_id,
            "resolver_version": self.resolver_version,
            "authority": self.authority,
            "no_runtime_authority": self.no_runtime_authority,
        }

    def to_dict(self) -> dict[str, object]:
        return {"facade_policy_id": self.facade_policy_id, **self.identity_payload()}


@dataclass(frozen=True, slots=True)
class ContinuityAdmissionFacadeResult:
    """Content-addressed evidence that the facade resolved and evaluated one set."""

    facade_result_id: str
    schema_version: str
    facade_policy_id: str
    registry_id: str
    resolver_id: str
    resolver_version: str
    current_decision_evidence_id: str
    evaluation: ContinuityAdmissionEvaluationResult
    evaluated_at: datetime
    authority: str = _RESULT_AUTHORITY
    no_runtime_authority: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "schema_version",
            _text(self.schema_version, "schema_version"),
        )
        for field_name in (
            "facade_policy_id",
            "registry_id",
            "current_decision_evidence_id",
        ):
            object.__setattr__(
                self,
                field_name,
                _hash(getattr(self, field_name), field_name),
            )
        object.__setattr__(
            self,
            "resolver_id",
            _text(self.resolver_id, "resolver_id"),
        )
        object.__setattr__(
            self,
            "resolver_version",
            _text(self.resolver_version, "resolver_version"),
        )
        if not isinstance(self.evaluation, ContinuityAdmissionEvaluationResult):
            raise ContinuitySourceAdmissionError(
                "evaluation must be a ContinuityAdmissionEvaluationResult"
            )
        if self.evaluation.registry_id != self.registry_id:
            raise ContinuitySourceAdmissionError(
                "evaluation registry must match facade registry"
            )
        if (
            self.evaluation.current_decision_evidence_id
            != self.current_decision_evidence_id
        ):
            raise ContinuitySourceAdmissionError(
                "evaluation current evidence must match facade evidence"
            )
        object.__setattr__(
            self,
            "evaluated_at",
            _aware(self.evaluated_at, "evaluated_at"),
        )
        object.__setattr__(self, "authority", _text(self.authority, "authority"))
        if self.authority != _RESULT_AUTHORITY:
            raise ContinuitySourceAdmissionError(
                f"authority must be {_RESULT_AUTHORITY!r}"
            )
        if self.no_runtime_authority is not True:
            raise ContinuitySourceAdmissionError(
                "no_runtime_authority must remain True"
            )
        _verify_id(
            self.facade_result_id,
            _digest(self.identity_payload()),
            "facade_result_id",
        )

    @classmethod
    def create(
        cls,
        *,
        policy: ContinuityAdmissionFacadePolicy,
        registry: ContinuityAdmissionRegistry,
        resolver_id: str,
        resolver_version: str,
        current_decision_evidence: ContinuityCurrentDecisionEvidence,
        evaluation: ContinuityAdmissionEvaluationResult,
        evaluated_at: datetime,
        schema_version: str = ADMISSION_FACADE_SCHEMA_VERSION,
    ) -> ContinuityAdmissionFacadeResult:
        if not isinstance(policy, ContinuityAdmissionFacadePolicy):
            raise ContinuitySourceAdmissionError(
                "policy must be a ContinuityAdmissionFacadePolicy"
            )
        if not isinstance(registry, ContinuityAdmissionRegistry):
            raise ContinuitySourceAdmissionError(
                "registry must be a ContinuityAdmissionRegistry"
            )
        if not isinstance(
            current_decision_evidence,
            ContinuityCurrentDecisionEvidence,
        ):
            raise ContinuitySourceAdmissionError(
                "current_decision_evidence must be ContinuityCurrentDecisionEvidence"
            )
        if not isinstance(evaluation, ContinuityAdmissionEvaluationResult):
            raise ContinuitySourceAdmissionError(
                "evaluation must be a ContinuityAdmissionEvaluationResult"
            )
        version = _text(schema_version, "schema_version")
        resolver_name = _text(resolver_id, "resolver_id")
        resolver_revision = _text(resolver_version, "resolver_version")
        evaluated = _aware(evaluated_at, "evaluated_at")
        payload: dict[str, object] = {
            "schema_version": version,
            "facade_policy_id": policy.facade_policy_id,
            "registry_id": registry.registry_id,
            "resolver_id": resolver_name,
            "resolver_version": resolver_revision,
            "current_decision_evidence_id": (
                current_decision_evidence.current_decision_evidence_id
            ),
            "evaluation_receipt_id": evaluation.receipt.receipt_id,
            "evaluated_at": _canonical_datetime(evaluated),
            "authority": _RESULT_AUTHORITY,
            "no_runtime_authority": True,
        }
        return cls(
            facade_result_id=_digest(payload),
            schema_version=version,
            facade_policy_id=policy.facade_policy_id,
            registry_id=registry.registry_id,
            resolver_id=resolver_name,
            resolver_version=resolver_revision,
            current_decision_evidence_id=(
                current_decision_evidence.current_decision_evidence_id
            ),
            evaluation=evaluation,
            evaluated_at=evaluated,
            authority=_RESULT_AUTHORITY,
            no_runtime_authority=True,
        )

    def identity_payload(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "facade_policy_id": self.facade_policy_id,
            "registry_id": self.registry_id,
            "resolver_id": self.resolver_id,
            "resolver_version": self.resolver_version,
            "current_decision_evidence_id": self.current_decision_evidence_id,
            "evaluation_receipt_id": self.evaluation.receipt.receipt_id,
            "evaluated_at": _canonical_datetime(self.evaluated_at),
            "authority": self.authority,
            "no_runtime_authority": self.no_runtime_authority,
        }

    def to_dict(self) -> dict[str, object]:
        return {"facade_result_id": self.facade_result_id, **self.identity_payload()}


def _validate_cross_contract_identity(
    *,
    principal_context: ContinuityPrincipalContext,
    authorization_context: ContinuityAuthorizationContext,
    source_envelope: ContinuitySourceEnvelope,
    binding_receipt: ContinuitySourceBindingReceipt,
) -> None:
    if (
        authorization_context.principal_context_id
        != principal_context.principal_context_id
    ):
        raise ContinuitySourceAdmissionError(
            "authorization context must reference the supplied principal context"
        )
    if source_envelope.source_binding_receipt_id != binding_receipt.binding_receipt_id:
        raise ContinuitySourceAdmissionError(
            "source envelope must reference the supplied binding receipt"
        )
    if (
        source_envelope.authorization_context_id
        != authorization_context.authorization_context_id
    ):
        raise ContinuitySourceAdmissionError(
            "source envelope must reference the supplied authorization context"
        )
    if not (
        source_envelope.tenant_ref
        == binding_receipt.tenant_ref
        == authorization_context.tenant_ref
    ):
        raise ContinuitySourceAdmissionError(
            "principal source and authorization tenant scope must match"
        )
    envelope_subjects = _subject_keys(source_envelope.subject_refs)
    binding_subjects = _subject_keys(binding_receipt.subject_refs)
    authorization_subjects = set(_subject_keys(authorization_context.subject_refs))
    if envelope_subjects != binding_subjects:
        raise ContinuitySourceAdmissionError(
            "source envelope and binding receipt subjects must match exactly"
        )
    if not set(binding_subjects).issubset(authorization_subjects):
        raise ContinuitySourceAdmissionError(
            "source subjects must remain within authorization scope"
        )


def evaluate_continuity_admission_facade(
    *,
    policy: ContinuityAdmissionFacadePolicy,
    registry: ContinuityAdmissionRegistry,
    resolver: ContinuityCurrentDecisionResolver,
    principal_context: ContinuityPrincipalContext,
    authorization_context: ContinuityAuthorizationContext,
    source_envelope: ContinuitySourceEnvelope,
    binding_receipt: ContinuitySourceBindingReceipt,
    drafts: Iterable[ContinuityObservationDraft],
    evaluated_at: datetime,
) -> ContinuityAdmissionFacadeResult:
    """Resolve current evidence and invoke the pure evaluator fail-closed."""

    if not isinstance(policy, ContinuityAdmissionFacadePolicy):
        raise ContinuitySourceAdmissionError(
            "policy must be a ContinuityAdmissionFacadePolicy"
        )
    if not isinstance(registry, ContinuityAdmissionRegistry):
        raise ContinuitySourceAdmissionError(
            "registry must be a ContinuityAdmissionRegistry"
        )
    if not isinstance(resolver, ContinuityCurrentDecisionResolver):
        raise ContinuitySourceAdmissionError(
            "resolver must implement ContinuityCurrentDecisionResolver"
        )
    if not isinstance(principal_context, ContinuityPrincipalContext):
        raise ContinuitySourceAdmissionError(
            "principal_context must be a ContinuityPrincipalContext"
        )
    if not isinstance(authorization_context, ContinuityAuthorizationContext):
        raise ContinuitySourceAdmissionError(
            "authorization_context must be a ContinuityAuthorizationContext"
        )
    if not isinstance(source_envelope, ContinuitySourceEnvelope):
        raise ContinuitySourceAdmissionError(
            "source_envelope must be a ContinuitySourceEnvelope"
        )
    if not isinstance(binding_receipt, ContinuitySourceBindingReceipt):
        raise ContinuitySourceAdmissionError(
            "binding_receipt must be a ContinuitySourceBindingReceipt"
        )
    if registry.registry_id != policy.expected_registry_id:
        raise ContinuitySourceAdmissionError(
            "registry does not match the pinned facade policy"
        )
    resolver_id = _text(resolver.resolver_id, "resolver.resolver_id")
    resolver_version = _text(
        resolver.resolver_version,
        "resolver.resolver_version",
    )
    if (
        resolver_id != policy.resolver_id
        or resolver_version != policy.resolver_version
    ):
        raise ContinuitySourceAdmissionError(
            "resolver identity does not match the pinned facade policy"
        )
    registry.resolve(
        evaluator_id=policy.evaluator_id,
        evaluator_version=policy.evaluator_version,
        rule_id=policy.rule_id,
        rule_version=policy.rule_version,
    )
    _validate_cross_contract_identity(
        principal_context=principal_context,
        authorization_context=authorization_context,
        source_envelope=source_envelope,
        binding_receipt=binding_receipt,
    )
    evaluated = _aware(evaluated_at, "evaluated_at")
    draft_items = _items(drafts, "drafts")
    if not draft_items or any(
        not isinstance(value, ContinuityObservationDraft) for value in draft_items
    ):
        raise ContinuitySourceAdmissionError(
            "drafts must contain ContinuityObservationDraft values"
        )
    normalized_drafts = tuple(
        value
        for value in draft_items
        if isinstance(value, ContinuityObservationDraft)
    )
    try:
        current_evidence = resolver.resolve_current_decision(
            principal_context=principal_context,
            authorization_context=authorization_context,
            source_envelope=source_envelope,
            binding_receipt=binding_receipt,
            evaluated_at=evaluated,
        )
    except Exception as exc:
        raise ContinuitySourceAdmissionError(
            "current decision resolver failed closed"
        ) from exc
    if not isinstance(current_evidence, ContinuityCurrentDecisionEvidence):
        raise ContinuitySourceAdmissionError(
            "resolver must return ContinuityCurrentDecisionEvidence"
        )
    if (
        current_evidence.principal_context_id
        != principal_context.principal_context_id
        or current_evidence.authorization_context_id
        != authorization_context.authorization_context_id
        or current_evidence.tenant_ref != authorization_context.tenant_ref
        or _subject_keys(current_evidence.subject_refs)
        != _subject_keys(authorization_context.subject_refs)
    ):
        raise ContinuitySourceAdmissionError(
            "resolver evidence must cover the exact principal authorization and subject set"
        )
    evaluation = evaluate_continuity_admission(
        registry=registry,
        evaluator_id=policy.evaluator_id,
        evaluator_version=policy.evaluator_version,
        rule_id=policy.rule_id,
        rule_version=policy.rule_version,
        source_envelope=source_envelope,
        binding_receipt=binding_receipt,
        authorization_context=authorization_context,
        drafts=normalized_drafts,
        current_decision_evidence=current_evidence,
        evaluated_at=evaluated,
    )
    return ContinuityAdmissionFacadeResult.create(
        policy=policy,
        registry=registry,
        resolver_id=resolver_id,
        resolver_version=resolver_version,
        current_decision_evidence=current_evidence,
        evaluation=evaluation,
        evaluated_at=evaluated,
    )
