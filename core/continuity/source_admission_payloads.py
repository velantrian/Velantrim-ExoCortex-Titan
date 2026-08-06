"""Neutral source-envelope and observation-draft contracts.

These contracts extend the accepted Continuity source-admission architecture
without creating an admission decision, trusted batch, adapter, persistence,
runtime composition, compute-route, response, reminder, tool, action, Canon,
or TruthGate authority.

Cross-contract ownership checks are performed by ``create`` methods using the
supplied immutable evidence objects. Direct construction still verifies shape
and content identity, but referenced receipts must be resolved and revalidated
by a future admission gate before any live use.
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
import math

from .contracts import SubjectRef
from .observations import ContinuitySignalType
from .source_admission import (
    ContinuityAuthorizationContext,
    ContinuitySourceAdmissionError,
    ContinuitySourceBindingReceipt,
    _aware,
    _canonical_datetime,
    _digest,
    _hash,
    _optional_text,
    _refs,
    _subject_payload,
    _subjects,
    _text,
    _verify_id,
)

SOURCE_ADMISSION_PAYLOAD_SCHEMA_VERSION = "continuity.source_admission.payloads.v1"
_SOURCE_ENVELOPE_AUTHORITY = "analysis_proposal_only"
_OBSERVATION_DRAFT_AUTHORITY = "observation_proposal_only"

_BOOLEAN_SIGNAL_TYPES = frozenset(
    {
        ContinuitySignalType.CONTEXT_DEGRADED,
        ContinuitySignalType.EVIDENCE_COVERAGE_ITEM,
        ContinuitySignalType.CONTINUITY_AVAILABLE,
        ContinuitySignalType.IMPORTANT_CLAIM,
        ContinuitySignalType.REQUIRES_CURRENT_STATE,
    }
)
_CONTEXT_FRESHNESS_VALUES = frozenset(
    {"unknown", "fresh", "stale", "critical_stale"}
)
_COMPUTE_SENSITIVITY_VALUES = frozenset(
    {"low", "medium", "high", "critical"}
)


def _subject_keys(subjects: tuple[SubjectRef, ...]) -> frozenset[tuple[str, str]]:
    return frozenset((subject.subject_id, subject.kind.value) for subject in subjects)


def _confidence(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ContinuitySourceAdmissionError(
            "proposed_confidence must be a finite number in [0.0, 1.0]"
        )
    result = float(value)
    if not math.isfinite(result) or not 0.0 <= result <= 1.0:
        raise ContinuitySourceAdmissionError(
            "proposed_confidence must be a finite number in [0.0, 1.0]"
        )
    return result


def _signal_value(signal_type: ContinuitySignalType, value: object) -> object:
    if signal_type in _BOOLEAN_SIGNAL_TYPES:
        if not isinstance(value, bool):
            raise ContinuitySourceAdmissionError(
                f"value for {signal_type.value} must be a bool"
            )
        return value
    if signal_type is ContinuitySignalType.ACTIVE_CONTRADICTION:
        if value is not True:
            raise ContinuitySourceAdmissionError(
                "active_contradiction drafts must assert value=True"
            )
        return True
    if signal_type is ContinuitySignalType.CONTEXT_FRESHNESS:
        if not isinstance(value, str) or value not in _CONTEXT_FRESHNESS_VALUES:
            raise ContinuitySourceAdmissionError(
                "value for context_freshness must be one of "
                f"{sorted(_CONTEXT_FRESHNESS_VALUES)}"
            )
        return value
    if signal_type is ContinuitySignalType.SENSITIVITY:
        if not isinstance(value, str) or value not in _COMPUTE_SENSITIVITY_VALUES:
            raise ContinuitySourceAdmissionError(
                "value for sensitivity must be one of "
                f"{sorted(_COMPUTE_SENSITIVITY_VALUES)}"
            )
        return value
    raise ContinuitySourceAdmissionError(  # pragma: no cover - exhaustive guard
        f"unhandled signal_type: {signal_type}"
    )


@dataclass(frozen=True, slots=True)
class ContinuitySourceEnvelope:
    """Immutable proposal envelope around one subject-bound source result."""

    envelope_id: str
    schema_version: str
    source_type: str
    source_schema_version: str
    source_result_id: str
    source_digest: str
    source_as_of: datetime
    source_policy_version: str
    source_binding_receipt_id: str
    producer_adapter_id: str
    producer_adapter_version: str
    authorization_context_id: str
    tenant_ref: str
    subject_refs: tuple[SubjectRef, ...]
    evidence_refs: tuple[str, ...]
    created_at: datetime
    authority: str = _SOURCE_ENVELOPE_AUTHORITY

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "schema_version", _text(self.schema_version, "schema_version")
        )
        for field_name in (
            "source_type",
            "source_schema_version",
            "source_result_id",
            "source_policy_version",
            "producer_adapter_id",
            "producer_adapter_version",
            "tenant_ref",
        ):
            object.__setattr__(
                self,
                field_name,
                _text(getattr(self, field_name), field_name),
            )
        object.__setattr__(
            self, "source_digest", _hash(self.source_digest, "source_digest")
        )
        object.__setattr__(
            self, "source_as_of", _aware(self.source_as_of, "source_as_of")
        )
        object.__setattr__(
            self,
            "source_binding_receipt_id",
            _hash(self.source_binding_receipt_id, "source_binding_receipt_id"),
        )
        object.__setattr__(
            self,
            "authorization_context_id",
            _hash(self.authorization_context_id, "authorization_context_id"),
        )
        object.__setattr__(self, "subject_refs", _subjects(self.subject_refs))
        object.__setattr__(
            self,
            "evidence_refs",
            _refs(self.evidence_refs, "evidence_refs", required=True),
        )
        object.__setattr__(self, "created_at", _aware(self.created_at, "created_at"))
        if self.created_at < self.source_as_of:
            raise ContinuitySourceAdmissionError(
                "created_at cannot be earlier than source_as_of"
            )
        object.__setattr__(self, "authority", _text(self.authority, "authority"))
        if self.authority != _SOURCE_ENVELOPE_AUTHORITY:
            raise ContinuitySourceAdmissionError(
                f"authority must be {_SOURCE_ENVELOPE_AUTHORITY!r}"
            )
        _verify_id(
            self.envelope_id,
            _digest(self.identity_payload()),
            "envelope_id",
        )

    @classmethod
    def create(
        cls,
        *,
        binding_receipt: ContinuitySourceBindingReceipt,
        authorization_context: ContinuityAuthorizationContext,
        source_schema_version: str,
        producer_adapter_id: str,
        producer_adapter_version: str,
        created_at: datetime,
        schema_version: str = SOURCE_ADMISSION_PAYLOAD_SCHEMA_VERSION,
    ) -> ContinuitySourceEnvelope:
        if not isinstance(binding_receipt, ContinuitySourceBindingReceipt):
            raise ContinuitySourceAdmissionError(
                "binding_receipt must be a ContinuitySourceBindingReceipt"
            )
        if not isinstance(authorization_context, ContinuityAuthorizationContext):
            raise ContinuitySourceAdmissionError(
                "authorization_context must be a ContinuityAuthorizationContext"
            )
        if binding_receipt.tenant_ref != authorization_context.tenant_ref:
            raise ContinuitySourceAdmissionError(
                "source binding tenant must match authorization tenant"
            )
        source_subjects = _subject_keys(binding_receipt.subject_refs)
        authorized_subjects = _subject_keys(authorization_context.subject_refs)
        if not source_subjects.issubset(authorized_subjects):
            raise ContinuitySourceAdmissionError(
                "source subjects must be a subset of authorized subjects"
            )
        created = _aware(created_at, "created_at")
        if created < binding_receipt.source_as_of:
            raise ContinuitySourceAdmissionError(
                "created_at cannot be earlier than source_as_of"
            )
        if created < binding_receipt.issued_at:
            raise ContinuitySourceAdmissionError(
                "created_at cannot be earlier than binding receipt issued_at"
            )
        if not authorization_context.valid_from <= created < authorization_context.valid_until:
            raise ContinuitySourceAdmissionError(
                "created_at must fall within the authorization validity interval"
            )
        version = _text(schema_version, "schema_version")
        source_schema = _text(source_schema_version, "source_schema_version")
        adapter_id = _text(producer_adapter_id, "producer_adapter_id")
        adapter_version = _text(
            producer_adapter_version,
            "producer_adapter_version",
        )
        payload: dict[str, object] = {
            "schema_version": version,
            "source_type": binding_receipt.source_type,
            "source_schema_version": source_schema,
            "source_result_id": binding_receipt.source_result_id,
            "source_digest": binding_receipt.source_digest,
            "source_as_of": _canonical_datetime(binding_receipt.source_as_of),
            "source_policy_version": binding_receipt.source_policy_version,
            "source_binding_receipt_id": binding_receipt.binding_receipt_id,
            "producer_adapter_id": adapter_id,
            "producer_adapter_version": adapter_version,
            "authorization_context_id": authorization_context.authorization_context_id,
            "tenant_ref": binding_receipt.tenant_ref,
            "subject_refs": _subject_payload(binding_receipt.subject_refs),
            "evidence_refs": list(binding_receipt.evidence_refs),
            "created_at": _canonical_datetime(created),
            "authority": _SOURCE_ENVELOPE_AUTHORITY,
        }
        return cls(
            envelope_id=_digest(payload),
            schema_version=version,
            source_type=binding_receipt.source_type,
            source_schema_version=source_schema,
            source_result_id=binding_receipt.source_result_id,
            source_digest=binding_receipt.source_digest,
            source_as_of=binding_receipt.source_as_of,
            source_policy_version=binding_receipt.source_policy_version,
            source_binding_receipt_id=binding_receipt.binding_receipt_id,
            producer_adapter_id=adapter_id,
            producer_adapter_version=adapter_version,
            authorization_context_id=authorization_context.authorization_context_id,
            tenant_ref=binding_receipt.tenant_ref,
            subject_refs=binding_receipt.subject_refs,
            evidence_refs=binding_receipt.evidence_refs,
            created_at=created,
            authority=_SOURCE_ENVELOPE_AUTHORITY,
        )

    def identity_payload(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "source_type": self.source_type,
            "source_schema_version": self.source_schema_version,
            "source_result_id": self.source_result_id,
            "source_digest": self.source_digest,
            "source_as_of": _canonical_datetime(self.source_as_of),
            "source_policy_version": self.source_policy_version,
            "source_binding_receipt_id": self.source_binding_receipt_id,
            "producer_adapter_id": self.producer_adapter_id,
            "producer_adapter_version": self.producer_adapter_version,
            "authorization_context_id": self.authorization_context_id,
            "tenant_ref": self.tenant_ref,
            "subject_refs": _subject_payload(self.subject_refs),
            "evidence_refs": list(self.evidence_refs),
            "created_at": _canonical_datetime(self.created_at),
            "authority": self.authority,
        }

    def to_dict(self) -> dict[str, object]:
        return {"envelope_id": self.envelope_id, **self.identity_payload()}


@dataclass(frozen=True, slots=True)
class ContinuityObservationDraft:
    """One deterministic signal proposal derived from a source envelope."""

    draft_id: str
    schema_version: str
    signal_type: ContinuitySignalType
    value: object
    proposed_confidence: float
    source_envelope_id: str
    evidence_refs: tuple[str, ...]
    reason_codes: tuple[str, ...]
    derivation_rule_id: str
    created_at: datetime
    scope: str | None = None
    authority: str = _OBSERVATION_DRAFT_AUTHORITY

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "schema_version", _text(self.schema_version, "schema_version")
        )
        if not isinstance(self.signal_type, ContinuitySignalType):
            raise ContinuitySourceAdmissionError(
                "signal_type must be a ContinuitySignalType"
            )
        object.__setattr__(
            self,
            "value",
            _signal_value(self.signal_type, self.value),
        )
        object.__setattr__(
            self,
            "proposed_confidence",
            _confidence(self.proposed_confidence),
        )
        object.__setattr__(
            self,
            "source_envelope_id",
            _hash(self.source_envelope_id, "source_envelope_id"),
        )
        object.__setattr__(
            self,
            "evidence_refs",
            _refs(self.evidence_refs, "evidence_refs", required=True),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _refs(self.reason_codes, "reason_codes", required=True),
        )
        object.__setattr__(
            self,
            "derivation_rule_id",
            _text(self.derivation_rule_id, "derivation_rule_id"),
        )
        object.__setattr__(self, "created_at", _aware(self.created_at, "created_at"))
        object.__setattr__(self, "scope", _optional_text(self.scope, "scope"))
        object.__setattr__(self, "authority", _text(self.authority, "authority"))
        if self.authority != _OBSERVATION_DRAFT_AUTHORITY:
            raise ContinuitySourceAdmissionError(
                f"authority must be {_OBSERVATION_DRAFT_AUTHORITY!r}"
            )
        _verify_id(
            self.draft_id,
            _digest(self.identity_payload()),
            "draft_id",
        )

    @classmethod
    def create(
        cls,
        *,
        source_envelope: ContinuitySourceEnvelope,
        signal_type: ContinuitySignalType,
        value: object,
        proposed_confidence: float,
        evidence_refs: Iterable[str],
        reason_codes: Iterable[str],
        derivation_rule_id: str,
        created_at: datetime,
        scope: str | None = None,
        schema_version: str = SOURCE_ADMISSION_PAYLOAD_SCHEMA_VERSION,
    ) -> ContinuityObservationDraft:
        if not isinstance(source_envelope, ContinuitySourceEnvelope):
            raise ContinuitySourceAdmissionError(
                "source_envelope must be a ContinuitySourceEnvelope"
            )
        if not isinstance(signal_type, ContinuitySignalType):
            raise ContinuitySourceAdmissionError(
                "signal_type must be a ContinuitySignalType"
            )
        shaped_value = _signal_value(signal_type, value)
        confidence = _confidence(proposed_confidence)
        refs = _refs(evidence_refs, "evidence_refs", required=True)
        if not set(refs).issubset(set(source_envelope.evidence_refs)):
            raise ContinuitySourceAdmissionError(
                "draft evidence_refs must be a subset of source envelope evidence_refs"
            )
        reasons = _refs(reason_codes, "reason_codes", required=True)
        rule_id = _text(derivation_rule_id, "derivation_rule_id")
        created = _aware(created_at, "created_at")
        if created < source_envelope.created_at:
            raise ContinuitySourceAdmissionError(
                "created_at cannot be earlier than source envelope created_at"
            )
        scope_text = _optional_text(scope, "scope")
        version = _text(schema_version, "schema_version")
        payload: dict[str, object] = {
            "schema_version": version,
            "signal_type": signal_type.value,
            "value": shaped_value,
            "proposed_confidence": confidence,
            "source_envelope_id": source_envelope.envelope_id,
            "evidence_refs": list(refs),
            "reason_codes": list(reasons),
            "derivation_rule_id": rule_id,
            "created_at": _canonical_datetime(created),
            "scope": scope_text,
            "authority": _OBSERVATION_DRAFT_AUTHORITY,
        }
        return cls(
            draft_id=_digest(payload),
            schema_version=version,
            signal_type=signal_type,
            value=shaped_value,
            proposed_confidence=confidence,
            source_envelope_id=source_envelope.envelope_id,
            evidence_refs=refs,
            reason_codes=reasons,
            derivation_rule_id=rule_id,
            created_at=created,
            scope=scope_text,
            authority=_OBSERVATION_DRAFT_AUTHORITY,
        )

    def identity_payload(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "signal_type": self.signal_type.value,
            "value": self.value,
            "proposed_confidence": self.proposed_confidence,
            "source_envelope_id": self.source_envelope_id,
            "evidence_refs": list(self.evidence_refs),
            "reason_codes": list(self.reason_codes),
            "derivation_rule_id": self.derivation_rule_id,
            "created_at": _canonical_datetime(self.created_at),
            "scope": self.scope,
            "authority": self.authority,
        }

    def to_dict(self) -> dict[str, object]:
        return {"draft_id": self.draft_id, **self.identity_payload()}
