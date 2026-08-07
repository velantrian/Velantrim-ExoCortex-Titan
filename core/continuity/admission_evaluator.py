"""Pure deterministic admission evaluation for Continuity observation Drafts.

The evaluator in this module consumes only immutable caller-supplied evidence. It does
not read the clock, environment, network, database, process-global state or runtime
configuration. It does not invoke the signal producer, persist artifacts, route a
request, answer, remind, deliver, execute a tool/action, mutate Canon/ESM/TruthGate, or
grant runtime authority.

Evaluator and rule names are not trusted by themselves. Evaluation requires immutable,
content-addressed definitions resolved through an explicit allowlisted registry.
Current authorization, lawful-basis, restriction and erasure state is represented by a
separate content-addressed evidence object; this module does not invent or fetch it.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import math

from .contracts import SubjectRef
from .observations import ContinuitySignalType
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
    _refs,
    _subject_payload,
    _subjects,
    _text,
    _verify_id,
)
from .source_admission_decisions import (
    ContinuityDraftRejection,
    ContinuityObservationAdmissionReceipt,
)
from .source_admission_payloads import (
    ContinuityObservationDraft,
    ContinuitySourceEnvelope,
)

ADMISSION_EVALUATOR_SCHEMA_VERSION = "continuity.admission_evaluator.v1"
_RULE_AUTHORITY = "admission_rule_definition_only"
_EVALUATOR_AUTHORITY = "admission_evaluator_definition_only"
_REGISTRY_AUTHORITY = "admission_allowlist_registry_only"
_CURRENT_EVIDENCE_AUTHORITY = "current_decision_evidence_only"
_RESULT_AUTHORITY = "admission_evaluation_evidence_only"


class ContinuityCurrentDecisionStatus(str, Enum):
    """Explicit current-state disposition supplied by an external resolver."""

    ACTIVE = "active"
    CLEAR = "clear"
    BLOCKED = "blocked"
    INACTIVE = "inactive"
    WITHDRAWN = "withdrawn"
    UNKNOWN = "unknown"


class ContinuityAdmissionReason(str, Enum):
    """Stable fail-closed reason codes emitted by the pure evaluator."""

    CURRENT_EVIDENCE_MISMATCH = "current_evidence_mismatch"
    CURRENT_EVIDENCE_STALE = "current_evidence_stale"
    CURRENT_AUTHORIZATION_NOT_ACTIVE = "current_authorization_not_active"
    CURRENT_LAWFUL_BASIS_NOT_ACTIVE = "current_lawful_basis_not_active"
    CURRENT_RESTRICTION_NOT_CLEAR = "current_restriction_not_clear"
    CURRENT_ERASURE_NOT_CLEAR = "current_erasure_not_clear"
    SOURCE_TYPE_NOT_ALLOWED = "source_type_not_allowed"
    ADAPTER_NOT_ALLOWED = "adapter_not_allowed"
    PURPOSE_NOT_ALLOWED = "purpose_not_allowed"
    DATA_HANDLING_MODE_NOT_ALLOWED = "data_handling_mode_not_allowed"
    RETENTION_CLASS_NOT_ALLOWED = "retention_class_not_allowed"
    DERIVATION_RULE_NOT_ALLOWED = "derivation_rule_not_allowed"
    SIGNAL_TYPE_NOT_ALLOWED = "signal_type_not_allowed"
    CONFIDENCE_BELOW_MINIMUM = "confidence_below_minimum"
    DRAFT_STALE = "draft_stale"


def _text_tuple(values: object, name: str, *, required: bool = True) -> tuple[str, ...]:
    return _refs(values, name, required=required)


def _signal_types(values: object) -> tuple[ContinuitySignalType, ...]:
    items = _items(values, "allowed_signal_types")
    if not items:
        raise ContinuitySourceAdmissionError("allowed_signal_types cannot be empty")
    if any(not isinstance(value, ContinuitySignalType) for value in items):
        raise ContinuitySourceAdmissionError(
            "allowed_signal_types must contain ContinuitySignalType values"
        )
    normalized = tuple(
        sorted(
            (value for value in items if isinstance(value, ContinuitySignalType)),
            key=lambda value: value.value,
        )
    )
    if len(normalized) != len(set(normalized)):
        raise ContinuitySourceAdmissionError(
            "allowed_signal_types cannot contain duplicates"
        )
    return normalized


def _confidence(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ContinuitySourceAdmissionError(
            "minimum_confidence must be a finite number in [0.0, 1.0]"
        )
    result = float(value)
    if not math.isfinite(result) or not 0.0 <= result <= 1.0:
        raise ContinuitySourceAdmissionError(
            "minimum_confidence must be a finite number in [0.0, 1.0]"
        )
    return result


def _positive_seconds(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ContinuitySourceAdmissionError(f"{name} must be a positive integer")
    return value


def _subject_keys(subjects: tuple[SubjectRef, ...]) -> tuple[tuple[str, str], ...]:
    return tuple((value.subject_id, value.kind.value) for value in subjects)


def _evidence_refs(*groups: Iterable[str]) -> tuple[str, ...]:
    values: set[str] = set()
    for group in groups:
        values.update(group)
    return tuple(sorted(values))


@dataclass(frozen=True, slots=True)
class ContinuityAdmissionRuleDefinition:
    """One immutable allowlist rule used by the deterministic evaluator."""

    rule_definition_id: str
    schema_version: str
    rule_id: str
    rule_version: str
    allowed_source_types: tuple[str, ...]
    allowed_adapter_ids: tuple[str, ...]
    allowed_derivation_rule_ids: tuple[str, ...]
    allowed_signal_types: tuple[ContinuitySignalType, ...]
    minimum_confidence: float
    maximum_draft_age_seconds: int
    required_purpose_code: str
    required_data_handling_mode: str
    allowed_retention_classes: tuple[str, ...]
    authority: str = _RULE_AUTHORITY

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "schema_version", _text(self.schema_version, "schema_version")
        )
        object.__setattr__(self, "rule_id", _text(self.rule_id, "rule_id"))
        object.__setattr__(
            self, "rule_version", _text(self.rule_version, "rule_version")
        )
        object.__setattr__(
            self,
            "allowed_source_types",
            _text_tuple(self.allowed_source_types, "allowed_source_types"),
        )
        object.__setattr__(
            self,
            "allowed_adapter_ids",
            _text_tuple(self.allowed_adapter_ids, "allowed_adapter_ids"),
        )
        object.__setattr__(
            self,
            "allowed_derivation_rule_ids",
            _text_tuple(
                self.allowed_derivation_rule_ids,
                "allowed_derivation_rule_ids",
            ),
        )
        object.__setattr__(
            self,
            "allowed_signal_types",
            _signal_types(self.allowed_signal_types),
        )
        object.__setattr__(
            self, "minimum_confidence", _confidence(self.minimum_confidence)
        )
        object.__setattr__(
            self,
            "maximum_draft_age_seconds",
            _positive_seconds(
                self.maximum_draft_age_seconds,
                "maximum_draft_age_seconds",
            ),
        )
        object.__setattr__(
            self,
            "required_purpose_code",
            _text(self.required_purpose_code, "required_purpose_code"),
        )
        object.__setattr__(
            self,
            "required_data_handling_mode",
            _text(
                self.required_data_handling_mode,
                "required_data_handling_mode",
            ),
        )
        object.__setattr__(
            self,
            "allowed_retention_classes",
            _text_tuple(
                self.allowed_retention_classes,
                "allowed_retention_classes",
            ),
        )
        object.__setattr__(self, "authority", _text(self.authority, "authority"))
        if self.authority != _RULE_AUTHORITY:
            raise ContinuitySourceAdmissionError(
                f"authority must be {_RULE_AUTHORITY!r}"
            )
        _verify_id(
            self.rule_definition_id,
            _digest(self.identity_payload()),
            "rule_definition_id",
        )

    @classmethod
    def create(
        cls,
        *,
        rule_id: str,
        rule_version: str,
        allowed_source_types: Iterable[str],
        allowed_adapter_ids: Iterable[str],
        allowed_derivation_rule_ids: Iterable[str],
        allowed_signal_types: Iterable[ContinuitySignalType],
        minimum_confidence: float,
        maximum_draft_age_seconds: int,
        required_purpose_code: str,
        required_data_handling_mode: str,
        allowed_retention_classes: Iterable[str],
        schema_version: str = ADMISSION_EVALUATOR_SCHEMA_VERSION,
    ) -> ContinuityAdmissionRuleDefinition:
        version = _text(schema_version, "schema_version")
        identifier = _text(rule_id, "rule_id")
        rule_revision = _text(rule_version, "rule_version")
        source_types = _text_tuple(allowed_source_types, "allowed_source_types")
        adapters = _text_tuple(allowed_adapter_ids, "allowed_adapter_ids")
        derivation_rules = _text_tuple(
            allowed_derivation_rule_ids,
            "allowed_derivation_rule_ids",
        )
        signal_types = _signal_types(allowed_signal_types)
        confidence = _confidence(minimum_confidence)
        maximum_age = _positive_seconds(
            maximum_draft_age_seconds,
            "maximum_draft_age_seconds",
        )
        purpose = _text(required_purpose_code, "required_purpose_code")
        handling = _text(
            required_data_handling_mode,
            "required_data_handling_mode",
        )
        retention = _text_tuple(
            allowed_retention_classes,
            "allowed_retention_classes",
        )
        payload: dict[str, object] = {
            "schema_version": version,
            "rule_id": identifier,
            "rule_version": rule_revision,
            "allowed_source_types": list(source_types),
            "allowed_adapter_ids": list(adapters),
            "allowed_derivation_rule_ids": list(derivation_rules),
            "allowed_signal_types": [value.value for value in signal_types],
            "minimum_confidence": confidence,
            "maximum_draft_age_seconds": maximum_age,
            "required_purpose_code": purpose,
            "required_data_handling_mode": handling,
            "allowed_retention_classes": list(retention),
            "authority": _RULE_AUTHORITY,
        }
        return cls(
            rule_definition_id=_digest(payload),
            schema_version=version,
            rule_id=identifier,
            rule_version=rule_revision,
            allowed_source_types=source_types,
            allowed_adapter_ids=adapters,
            allowed_derivation_rule_ids=derivation_rules,
            allowed_signal_types=signal_types,
            minimum_confidence=confidence,
            maximum_draft_age_seconds=maximum_age,
            required_purpose_code=purpose,
            required_data_handling_mode=handling,
            allowed_retention_classes=retention,
            authority=_RULE_AUTHORITY,
        )

    def identity_payload(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "rule_id": self.rule_id,
            "rule_version": self.rule_version,
            "allowed_source_types": list(self.allowed_source_types),
            "allowed_adapter_ids": list(self.allowed_adapter_ids),
            "allowed_derivation_rule_ids": list(
                self.allowed_derivation_rule_ids
            ),
            "allowed_signal_types": [
                value.value for value in self.allowed_signal_types
            ],
            "minimum_confidence": self.minimum_confidence,
            "maximum_draft_age_seconds": self.maximum_draft_age_seconds,
            "required_purpose_code": self.required_purpose_code,
            "required_data_handling_mode": self.required_data_handling_mode,
            "allowed_retention_classes": list(self.allowed_retention_classes),
            "authority": self.authority,
        }

    def to_dict(self) -> dict[str, object]:
        return {"rule_definition_id": self.rule_definition_id, **self.identity_payload()}


@dataclass(frozen=True, slots=True)
class ContinuityAdmissionEvaluatorDefinition:
    """Immutable evaluator identity and its allowlisted rule definitions."""

    evaluator_definition_id: str
    schema_version: str
    evaluator_id: str
    evaluator_version: str
    allowed_rule_definition_ids: tuple[str, ...]
    authority: str = _EVALUATOR_AUTHORITY

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "schema_version", _text(self.schema_version, "schema_version")
        )
        object.__setattr__(
            self, "evaluator_id", _text(self.evaluator_id, "evaluator_id")
        )
        object.__setattr__(
            self,
            "evaluator_version",
            _text(self.evaluator_version, "evaluator_version"),
        )
        rule_ids = tuple(
            sorted(
                _hash(value, "allowed_rule_definition_ids")
                for value in _items(
                    self.allowed_rule_definition_ids,
                    "allowed_rule_definition_ids",
                )
            )
        )
        if not rule_ids:
            raise ContinuitySourceAdmissionError(
                "allowed_rule_definition_ids cannot be empty"
            )
        if len(rule_ids) != len(set(rule_ids)):
            raise ContinuitySourceAdmissionError(
                "allowed_rule_definition_ids cannot contain duplicates"
            )
        object.__setattr__(self, "allowed_rule_definition_ids", rule_ids)
        object.__setattr__(self, "authority", _text(self.authority, "authority"))
        if self.authority != _EVALUATOR_AUTHORITY:
            raise ContinuitySourceAdmissionError(
                f"authority must be {_EVALUATOR_AUTHORITY!r}"
            )
        _verify_id(
            self.evaluator_definition_id,
            _digest(self.identity_payload()),
            "evaluator_definition_id",
        )

    @classmethod
    def create(
        cls,
        *,
        evaluator_id: str,
        evaluator_version: str,
        allowed_rules: Iterable[ContinuityAdmissionRuleDefinition],
        schema_version: str = ADMISSION_EVALUATOR_SCHEMA_VERSION,
    ) -> ContinuityAdmissionEvaluatorDefinition:
        items = _items(allowed_rules, "allowed_rules")
        if not items or any(
            not isinstance(value, ContinuityAdmissionRuleDefinition) for value in items
        ):
            raise ContinuitySourceAdmissionError(
                "allowed_rules must contain ContinuityAdmissionRuleDefinition values"
            )
        rule_ids = tuple(
            sorted(
                value.rule_definition_id
                for value in items
                if isinstance(value, ContinuityAdmissionRuleDefinition)
            )
        )
        if len(rule_ids) != len(set(rule_ids)):
            raise ContinuitySourceAdmissionError(
                "allowed_rules cannot contain duplicate definitions"
            )
        version = _text(schema_version, "schema_version")
        identifier = _text(evaluator_id, "evaluator_id")
        evaluator_revision = _text(evaluator_version, "evaluator_version")
        payload: dict[str, object] = {
            "schema_version": version,
            "evaluator_id": identifier,
            "evaluator_version": evaluator_revision,
            "allowed_rule_definition_ids": list(rule_ids),
            "authority": _EVALUATOR_AUTHORITY,
        }
        return cls(
            evaluator_definition_id=_digest(payload),
            schema_version=version,
            evaluator_id=identifier,
            evaluator_version=evaluator_revision,
            allowed_rule_definition_ids=rule_ids,
            authority=_EVALUATOR_AUTHORITY,
        )

    def identity_payload(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "evaluator_id": self.evaluator_id,
            "evaluator_version": self.evaluator_version,
            "allowed_rule_definition_ids": list(self.allowed_rule_definition_ids),
            "authority": self.authority,
        }

    def to_dict(self) -> dict[str, object]:
        return {
            "evaluator_definition_id": self.evaluator_definition_id,
            **self.identity_payload(),
        }


@dataclass(frozen=True, slots=True)
class ContinuityAdmissionRegistry:
    """Explicit immutable allowlist of evaluator and rule definitions."""

    registry_id: str
    schema_version: str
    evaluator_definitions: tuple[ContinuityAdmissionEvaluatorDefinition, ...]
    rule_definitions: tuple[ContinuityAdmissionRuleDefinition, ...]
    authority: str = _REGISTRY_AUTHORITY

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "schema_version", _text(self.schema_version, "schema_version")
        )
        evaluators = self._normalize_evaluators(self.evaluator_definitions)
        rules = self._normalize_rules(self.rule_definitions)
        rule_ids = {value.rule_definition_id for value in rules}
        if any(
            not set(value.allowed_rule_definition_ids).issubset(rule_ids)
            for value in evaluators
        ):
            raise ContinuitySourceAdmissionError(
                "every evaluator rule reference must resolve inside the registry"
            )
        object.__setattr__(self, "evaluator_definitions", evaluators)
        object.__setattr__(self, "rule_definitions", rules)
        object.__setattr__(self, "authority", _text(self.authority, "authority"))
        if self.authority != _REGISTRY_AUTHORITY:
            raise ContinuitySourceAdmissionError(
                f"authority must be {_REGISTRY_AUTHORITY!r}"
            )
        _verify_id(self.registry_id, _digest(self.identity_payload()), "registry_id")

    @staticmethod
    def _normalize_evaluators(
        values: object,
    ) -> tuple[ContinuityAdmissionEvaluatorDefinition, ...]:
        items = _items(values, "evaluator_definitions")
        if not items or any(
            not isinstance(value, ContinuityAdmissionEvaluatorDefinition)
            for value in items
        ):
            raise ContinuitySourceAdmissionError(
                "evaluator_definitions must contain evaluator definitions"
            )
        normalized = tuple(
            sorted(
                (
                    value
                    for value in items
                    if isinstance(value, ContinuityAdmissionEvaluatorDefinition)
                ),
                key=lambda value: (value.evaluator_id, value.evaluator_version),
            )
        )
        keys = tuple(
            (value.evaluator_id, value.evaluator_version) for value in normalized
        )
        if len(keys) != len(set(keys)):
            raise ContinuitySourceAdmissionError(
                "evaluator_definitions cannot duplicate evaluator ID/version"
            )
        return normalized

    @staticmethod
    def _normalize_rules(
        values: object,
    ) -> tuple[ContinuityAdmissionRuleDefinition, ...]:
        items = _items(values, "rule_definitions")
        if not items or any(
            not isinstance(value, ContinuityAdmissionRuleDefinition) for value in items
        ):
            raise ContinuitySourceAdmissionError(
                "rule_definitions must contain rule definitions"
            )
        normalized = tuple(
            sorted(
                (
                    value
                    for value in items
                    if isinstance(value, ContinuityAdmissionRuleDefinition)
                ),
                key=lambda value: (value.rule_id, value.rule_version),
            )
        )
        keys = tuple((value.rule_id, value.rule_version) for value in normalized)
        if len(keys) != len(set(keys)):
            raise ContinuitySourceAdmissionError(
                "rule_definitions cannot duplicate rule ID/version"
            )
        return normalized

    @classmethod
    def create(
        cls,
        *,
        evaluator_definitions: Iterable[ContinuityAdmissionEvaluatorDefinition],
        rule_definitions: Iterable[ContinuityAdmissionRuleDefinition],
        schema_version: str = ADMISSION_EVALUATOR_SCHEMA_VERSION,
    ) -> ContinuityAdmissionRegistry:
        version = _text(schema_version, "schema_version")
        evaluators = cls._normalize_evaluators(evaluator_definitions)
        rules = cls._normalize_rules(rule_definitions)
        rule_ids = {value.rule_definition_id for value in rules}
        if any(
            not set(value.allowed_rule_definition_ids).issubset(rule_ids)
            for value in evaluators
        ):
            raise ContinuitySourceAdmissionError(
                "every evaluator rule reference must resolve inside the registry"
            )
        payload: dict[str, object] = {
            "schema_version": version,
            "evaluator_definitions": [value.to_dict() for value in evaluators],
            "rule_definitions": [value.to_dict() for value in rules],
            "authority": _REGISTRY_AUTHORITY,
        }
        return cls(
            registry_id=_digest(payload),
            schema_version=version,
            evaluator_definitions=evaluators,
            rule_definitions=rules,
            authority=_REGISTRY_AUTHORITY,
        )

    def resolve(
        self,
        *,
        evaluator_id: str,
        evaluator_version: str,
        rule_id: str,
        rule_version: str,
    ) -> tuple[
        ContinuityAdmissionEvaluatorDefinition,
        ContinuityAdmissionRuleDefinition,
    ]:
        evaluator_key = (
            _text(evaluator_id, "evaluator_id"),
            _text(evaluator_version, "evaluator_version"),
        )
        rule_key = (_text(rule_id, "rule_id"), _text(rule_version, "rule_version"))
        evaluator = next(
            (
                value
                for value in self.evaluator_definitions
                if (value.evaluator_id, value.evaluator_version) == evaluator_key
            ),
            None,
        )
        if evaluator is None:
            raise ContinuitySourceAdmissionError(
                "evaluator ID/version is not allowlisted"
            )
        rule = next(
            (
                value
                for value in self.rule_definitions
                if (value.rule_id, value.rule_version) == rule_key
            ),
            None,
        )
        if rule is None:
            raise ContinuitySourceAdmissionError("rule ID/version is not allowlisted")
        if rule.rule_definition_id not in evaluator.allowed_rule_definition_ids:
            raise ContinuitySourceAdmissionError(
                "rule is not allowlisted for the selected evaluator"
            )
        return evaluator, rule

    def identity_payload(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "evaluator_definitions": [
                value.to_dict() for value in self.evaluator_definitions
            ],
            "rule_definitions": [value.to_dict() for value in self.rule_definitions],
            "authority": self.authority,
        }

    def to_dict(self) -> dict[str, object]:
        return {"registry_id": self.registry_id, **self.identity_payload()}


@dataclass(frozen=True, slots=True)
class ContinuityCurrentDecisionEvidence:
    """Resolved current-state evidence supplied to the pure evaluator."""

    current_decision_evidence_id: str
    schema_version: str
    principal_context_id: str
    authorization_context_id: str
    tenant_ref: str
    subject_refs: tuple[SubjectRef, ...]
    purpose_code: str
    policy_snapshot_id: str
    lawful_basis_or_consent_ref: str
    authorization_receipt_ref: str
    erasure_domain_refs: tuple[str, ...]
    authorization_status: ContinuityCurrentDecisionStatus
    lawful_basis_status: ContinuityCurrentDecisionStatus
    restriction_status: ContinuityCurrentDecisionStatus
    erasure_status: ContinuityCurrentDecisionStatus
    observed_at: datetime
    valid_until: datetime
    evidence_refs: tuple[str, ...]
    authority: str = _CURRENT_EVIDENCE_AUTHORITY

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "schema_version", _text(self.schema_version, "schema_version")
        )
        for field_name in ("principal_context_id", "authorization_context_id"):
            object.__setattr__(
                self,
                field_name,
                _hash(getattr(self, field_name), field_name),
            )
        object.__setattr__(self, "tenant_ref", _text(self.tenant_ref, "tenant_ref"))
        object.__setattr__(self, "subject_refs", _subjects(self.subject_refs))
        for field_name in (
            "purpose_code",
            "policy_snapshot_id",
            "lawful_basis_or_consent_ref",
            "authorization_receipt_ref",
        ):
            object.__setattr__(
                self,
                field_name,
                _text(getattr(self, field_name), field_name),
            )
        object.__setattr__(
            self,
            "erasure_domain_refs",
            _text_tuple(self.erasure_domain_refs, "erasure_domain_refs"),
        )
        for field_name in (
            "authorization_status",
            "lawful_basis_status",
            "restriction_status",
            "erasure_status",
        ):
            if not isinstance(
                getattr(self, field_name), ContinuityCurrentDecisionStatus
            ):
                raise ContinuitySourceAdmissionError(
                    f"{field_name} must be a ContinuityCurrentDecisionStatus"
                )
        object.__setattr__(self, "observed_at", _aware(self.observed_at, "observed_at"))
        object.__setattr__(
            self, "valid_until", _aware(self.valid_until, "valid_until")
        )
        if self.valid_until <= self.observed_at:
            raise ContinuitySourceAdmissionError(
                "valid_until must be later than observed_at"
            )
        object.__setattr__(
            self,
            "evidence_refs",
            _text_tuple(self.evidence_refs, "evidence_refs"),
        )
        object.__setattr__(self, "authority", _text(self.authority, "authority"))
        if self.authority != _CURRENT_EVIDENCE_AUTHORITY:
            raise ContinuitySourceAdmissionError(
                f"authority must be {_CURRENT_EVIDENCE_AUTHORITY!r}"
            )
        _verify_id(
            self.current_decision_evidence_id,
            _digest(self.identity_payload()),
            "current_decision_evidence_id",
        )

    @classmethod
    def create(
        cls,
        *,
        principal_context: ContinuityPrincipalContext,
        authorization_context: ContinuityAuthorizationContext,
        authorization_status: ContinuityCurrentDecisionStatus,
        lawful_basis_status: ContinuityCurrentDecisionStatus,
        restriction_status: ContinuityCurrentDecisionStatus,
        erasure_status: ContinuityCurrentDecisionStatus,
        observed_at: datetime,
        valid_until: datetime,
        evidence_refs: Iterable[str],
        schema_version: str = ADMISSION_EVALUATOR_SCHEMA_VERSION,
    ) -> ContinuityCurrentDecisionEvidence:
        if not isinstance(principal_context, ContinuityPrincipalContext):
            raise ContinuitySourceAdmissionError(
                "principal_context must be a ContinuityPrincipalContext"
            )
        if not isinstance(authorization_context, ContinuityAuthorizationContext):
            raise ContinuitySourceAdmissionError(
                "authorization_context must be a ContinuityAuthorizationContext"
            )
        if (
            authorization_context.principal_context_id
            != principal_context.principal_context_id
        ):
            raise ContinuitySourceAdmissionError(
                "authorization context must reference the supplied principal context"
            )
        for field_name, value in (
            ("authorization_status", authorization_status),
            ("lawful_basis_status", lawful_basis_status),
            ("restriction_status", restriction_status),
            ("erasure_status", erasure_status),
        ):
            if not isinstance(value, ContinuityCurrentDecisionStatus):
                raise ContinuitySourceAdmissionError(
                    f"{field_name} must be a ContinuityCurrentDecisionStatus"
                )
        version = _text(schema_version, "schema_version")
        observed = _aware(observed_at, "observed_at")
        expires = _aware(valid_until, "valid_until")
        if expires <= observed:
            raise ContinuitySourceAdmissionError(
                "valid_until must be later than observed_at"
            )
        refs = _text_tuple(evidence_refs, "evidence_refs")
        payload: dict[str, object] = {
            "schema_version": version,
            "principal_context_id": principal_context.principal_context_id,
            "authorization_context_id": authorization_context.authorization_context_id,
            "tenant_ref": authorization_context.tenant_ref,
            "subject_refs": _subject_payload(authorization_context.subject_refs),
            "purpose_code": authorization_context.purpose_code,
            "policy_snapshot_id": authorization_context.policy_snapshot_id,
            "lawful_basis_or_consent_ref": (
                authorization_context.lawful_basis_or_consent_ref
            ),
            "authorization_receipt_ref": (
                authorization_context.authorization_receipt_ref
            ),
            "erasure_domain_refs": list(authorization_context.erasure_domain_refs),
            "authorization_status": authorization_status.value,
            "lawful_basis_status": lawful_basis_status.value,
            "restriction_status": restriction_status.value,
            "erasure_status": erasure_status.value,
            "observed_at": _canonical_datetime(observed),
            "valid_until": _canonical_datetime(expires),
            "evidence_refs": list(refs),
            "authority": _CURRENT_EVIDENCE_AUTHORITY,
        }
        return cls(
            current_decision_evidence_id=_digest(payload),
            schema_version=version,
            principal_context_id=principal_context.principal_context_id,
            authorization_context_id=authorization_context.authorization_context_id,
            tenant_ref=authorization_context.tenant_ref,
            subject_refs=authorization_context.subject_refs,
            purpose_code=authorization_context.purpose_code,
            policy_snapshot_id=authorization_context.policy_snapshot_id,
            lawful_basis_or_consent_ref=(
                authorization_context.lawful_basis_or_consent_ref
            ),
            authorization_receipt_ref=(
                authorization_context.authorization_receipt_ref
            ),
            erasure_domain_refs=authorization_context.erasure_domain_refs,
            authorization_status=authorization_status,
            lawful_basis_status=lawful_basis_status,
            restriction_status=restriction_status,
            erasure_status=erasure_status,
            observed_at=observed,
            valid_until=expires,
            evidence_refs=refs,
            authority=_CURRENT_EVIDENCE_AUTHORITY,
        )

    def identity_payload(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "principal_context_id": self.principal_context_id,
            "authorization_context_id": self.authorization_context_id,
            "tenant_ref": self.tenant_ref,
            "subject_refs": _subject_payload(self.subject_refs),
            "purpose_code": self.purpose_code,
            "policy_snapshot_id": self.policy_snapshot_id,
            "lawful_basis_or_consent_ref": self.lawful_basis_or_consent_ref,
            "authorization_receipt_ref": self.authorization_receipt_ref,
            "erasure_domain_refs": list(self.erasure_domain_refs),
            "authorization_status": self.authorization_status.value,
            "lawful_basis_status": self.lawful_basis_status.value,
            "restriction_status": self.restriction_status.value,
            "erasure_status": self.erasure_status.value,
            "observed_at": _canonical_datetime(self.observed_at),
            "valid_until": _canonical_datetime(self.valid_until),
            "evidence_refs": list(self.evidence_refs),
            "authority": self.authority,
        }

    def to_dict(self) -> dict[str, object]:
        return {
            "current_decision_evidence_id": self.current_decision_evidence_id,
            **self.identity_payload(),
        }


@dataclass(frozen=True, slots=True)
class ContinuityAdmissionEvaluationResult:
    """Evidence-only output of one deterministic evaluator invocation."""

    evaluator_definition_id: str
    rule_definition_id: str
    registry_id: str
    current_decision_evidence_id: str
    receipt: ContinuityObservationAdmissionReceipt
    admitted_draft_ids: tuple[str, ...]
    rejected_drafts: tuple[ContinuityDraftRejection, ...]
    authority: str = _RESULT_AUTHORITY
    no_runtime_authority: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "evaluator_definition_id",
            "rule_definition_id",
            "registry_id",
            "current_decision_evidence_id",
        ):
            object.__setattr__(
                self,
                field_name,
                _hash(getattr(self, field_name), field_name),
            )
        if not isinstance(self.receipt, ContinuityObservationAdmissionReceipt):
            raise ContinuitySourceAdmissionError(
                "receipt must be a ContinuityObservationAdmissionReceipt"
            )
        admitted = tuple(
            sorted(
                _hash(value, "admitted_draft_ids")
                for value in _items(self.admitted_draft_ids, "admitted_draft_ids")
            )
        )
        if len(admitted) != len(set(admitted)):
            raise ContinuitySourceAdmissionError(
                "admitted_draft_ids cannot contain duplicates"
            )
        object.__setattr__(self, "admitted_draft_ids", admitted)
        rejection_items = _items(self.rejected_drafts, "rejected_drafts")
        if any(not isinstance(value, ContinuityDraftRejection) for value in rejection_items):
            raise ContinuitySourceAdmissionError(
                "rejected_drafts must contain ContinuityDraftRejection values"
            )
        rejections = tuple(
            sorted(
                (
                    value
                    for value in rejection_items
                    if isinstance(value, ContinuityDraftRejection)
                ),
                key=lambda value: value.draft_id,
            )
        )
        object.__setattr__(self, "rejected_drafts", rejections)
        if self.receipt.admission_evaluator_id != self.evaluator_definition_id:
            raise ContinuitySourceAdmissionError(
                "receipt must reference the selected evaluator definition"
            )
        if self.receipt.admission_rule_id != self.rule_definition_id:
            raise ContinuitySourceAdmissionError(
                "receipt must reference the selected rule definition"
            )
        if self.receipt.admitted_draft_ids != self.admitted_draft_ids:
            raise ContinuitySourceAdmissionError(
                "result admitted_draft_ids must match the receipt"
            )
        if self.receipt.rejected_drafts != self.rejected_drafts:
            raise ContinuitySourceAdmissionError(
                "result rejected_drafts must match the receipt"
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


def _current_evidence_mismatch(
    *,
    evidence: ContinuityCurrentDecisionEvidence,
    authorization: ContinuityAuthorizationContext,
) -> bool:
    return any(
        (
            evidence.principal_context_id != authorization.principal_context_id,
            evidence.authorization_context_id != authorization.authorization_context_id,
            evidence.tenant_ref != authorization.tenant_ref,
            _subject_keys(evidence.subject_refs)
            != _subject_keys(authorization.subject_refs),
            evidence.purpose_code != authorization.purpose_code,
            evidence.policy_snapshot_id != authorization.policy_snapshot_id,
            evidence.lawful_basis_or_consent_ref
            != authorization.lawful_basis_or_consent_ref,
            evidence.authorization_receipt_ref
            != authorization.authorization_receipt_ref,
            evidence.erasure_domain_refs != authorization.erasure_domain_refs,
        )
    )


def _global_reason(
    *,
    evidence: ContinuityCurrentDecisionEvidence,
    authorization: ContinuityAuthorizationContext,
    evaluated_at: datetime,
) -> ContinuityAdmissionReason | None:
    if _current_evidence_mismatch(evidence=evidence, authorization=authorization):
        return ContinuityAdmissionReason.CURRENT_EVIDENCE_MISMATCH
    if not evidence.observed_at <= evaluated_at < evidence.valid_until:
        return ContinuityAdmissionReason.CURRENT_EVIDENCE_STALE
    if not authorization.valid_from <= evaluated_at < authorization.valid_until:
        return ContinuityAdmissionReason.CURRENT_AUTHORIZATION_NOT_ACTIVE
    if evidence.authorization_status is not ContinuityCurrentDecisionStatus.ACTIVE:
        return ContinuityAdmissionReason.CURRENT_AUTHORIZATION_NOT_ACTIVE
    if evidence.lawful_basis_status is not ContinuityCurrentDecisionStatus.ACTIVE:
        return ContinuityAdmissionReason.CURRENT_LAWFUL_BASIS_NOT_ACTIVE
    if evidence.restriction_status is not ContinuityCurrentDecisionStatus.CLEAR:
        return ContinuityAdmissionReason.CURRENT_RESTRICTION_NOT_CLEAR
    if evidence.erasure_status is not ContinuityCurrentDecisionStatus.CLEAR:
        return ContinuityAdmissionReason.CURRENT_ERASURE_NOT_CLEAR
    return None


def _draft_reason(
    *,
    draft: ContinuityObservationDraft,
    envelope: ContinuitySourceEnvelope,
    authorization: ContinuityAuthorizationContext,
    rule: ContinuityAdmissionRuleDefinition,
    evaluated_at: datetime,
) -> ContinuityAdmissionReason | None:
    if envelope.source_type not in rule.allowed_source_types:
        return ContinuityAdmissionReason.SOURCE_TYPE_NOT_ALLOWED
    if envelope.producer_adapter_id not in rule.allowed_adapter_ids:
        return ContinuityAdmissionReason.ADAPTER_NOT_ALLOWED
    if authorization.purpose_code != rule.required_purpose_code:
        return ContinuityAdmissionReason.PURPOSE_NOT_ALLOWED
    if authorization.data_handling_mode != rule.required_data_handling_mode:
        return ContinuityAdmissionReason.DATA_HANDLING_MODE_NOT_ALLOWED
    if authorization.retention_class not in rule.allowed_retention_classes:
        return ContinuityAdmissionReason.RETENTION_CLASS_NOT_ALLOWED
    if draft.derivation_rule_id not in rule.allowed_derivation_rule_ids:
        return ContinuityAdmissionReason.DERIVATION_RULE_NOT_ALLOWED
    if draft.signal_type not in rule.allowed_signal_types:
        return ContinuityAdmissionReason.SIGNAL_TYPE_NOT_ALLOWED
    if draft.proposed_confidence < rule.minimum_confidence:
        return ContinuityAdmissionReason.CONFIDENCE_BELOW_MINIMUM
    age_seconds = (evaluated_at - draft.created_at).total_seconds()
    if age_seconds < 0 or age_seconds > rule.maximum_draft_age_seconds:
        return ContinuityAdmissionReason.DRAFT_STALE
    return None


def evaluate_continuity_admission(
    *,
    registry: ContinuityAdmissionRegistry,
    evaluator_id: str,
    evaluator_version: str,
    rule_id: str,
    rule_version: str,
    source_envelope: ContinuitySourceEnvelope,
    binding_receipt: ContinuitySourceBindingReceipt,
    authorization_context: ContinuityAuthorizationContext,
    drafts: Iterable[ContinuityObservationDraft],
    current_decision_evidence: ContinuityCurrentDecisionEvidence,
    evaluated_at: datetime,
) -> ContinuityAdmissionEvaluationResult:
    """Return a complete deterministic Draft partition and immutable receipt."""

    if not isinstance(registry, ContinuityAdmissionRegistry):
        raise ContinuitySourceAdmissionError(
            "registry must be a ContinuityAdmissionRegistry"
        )
    if not isinstance(source_envelope, ContinuitySourceEnvelope):
        raise ContinuitySourceAdmissionError(
            "source_envelope must be a ContinuitySourceEnvelope"
        )
    if not isinstance(binding_receipt, ContinuitySourceBindingReceipt):
        raise ContinuitySourceAdmissionError(
            "binding_receipt must be a ContinuitySourceBindingReceipt"
        )
    if not isinstance(authorization_context, ContinuityAuthorizationContext):
        raise ContinuitySourceAdmissionError(
            "authorization_context must be a ContinuityAuthorizationContext"
        )
    if not isinstance(current_decision_evidence, ContinuityCurrentDecisionEvidence):
        raise ContinuitySourceAdmissionError(
            "current_decision_evidence must be ContinuityCurrentDecisionEvidence"
        )
    evaluator, rule = registry.resolve(
        evaluator_id=evaluator_id,
        evaluator_version=evaluator_version,
        rule_id=rule_id,
        rule_version=rule_version,
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
        sorted(
            (
                value
                for value in draft_items
                if isinstance(value, ContinuityObservationDraft)
            ),
            key=lambda value: value.draft_id,
        )
    )
    if len(normalized_drafts) != len({value.draft_id for value in normalized_drafts}):
        raise ContinuitySourceAdmissionError("drafts cannot contain duplicate IDs")
    if any(
        value.source_envelope_id != source_envelope.envelope_id
        for value in normalized_drafts
    ):
        raise ContinuitySourceAdmissionError(
            "all drafts must reference the supplied source envelope"
        )

    global_reason = _global_reason(
        evidence=current_decision_evidence,
        authorization=authorization_context,
        evaluated_at=evaluated,
    )
    admitted: list[ContinuityObservationDraft] = []
    rejected: list[ContinuityDraftRejection] = []
    rejection_evidence = _evidence_refs(
        current_decision_evidence.evidence_refs,
        (
            f"registry:{registry.registry_id}",
            f"evaluator_definition:{evaluator.evaluator_definition_id}",
            f"rule_definition:{rule.rule_definition_id}",
            f"current_decision_evidence:{current_decision_evidence.current_decision_evidence_id}",
        ),
    )
    for draft in normalized_drafts:
        reason = global_reason or _draft_reason(
            draft=draft,
            envelope=source_envelope,
            authorization=authorization_context,
            rule=rule,
            evaluated_at=evaluated,
        )
        if reason is None:
            admitted.append(draft)
            continue
        rejected.append(
            ContinuityDraftRejection.create(
                draft=draft,
                reason_code=reason.value,
                evidence_refs=rejection_evidence,
            )
        )

    evaluation_evidence = _evidence_refs(
        rejection_evidence,
        source_envelope.evidence_refs,
    )
    receipt = ContinuityObservationAdmissionReceipt.create(
        source_envelope=source_envelope,
        binding_receipt=binding_receipt,
        authorization_context=authorization_context,
        drafts=normalized_drafts,
        admitted_drafts=tuple(admitted),
        rejected_drafts=tuple(rejected),
        admission_evaluator_id=evaluator.evaluator_definition_id,
        admission_evaluator_version=evaluator.evaluator_version,
        admission_rule_id=rule.rule_definition_id,
        evaluation_evidence_refs=evaluation_evidence,
        evaluated_at=evaluated,
    )
    return ContinuityAdmissionEvaluationResult(
        evaluator_definition_id=evaluator.evaluator_definition_id,
        rule_definition_id=rule.rule_definition_id,
        registry_id=registry.registry_id,
        current_decision_evidence_id=(
            current_decision_evidence.current_decision_evidence_id
        ),
        receipt=receipt,
        admitted_draft_ids=receipt.admitted_draft_ids,
        rejected_drafts=receipt.rejected_drafts,
        authority=_RESULT_AUTHORITY,
        no_runtime_authority=True,
    )
