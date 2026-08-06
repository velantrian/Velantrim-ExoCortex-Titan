"""Immutable admission-decision and authorized-batch evidence contracts.

This module records caller-supplied admission outcomes and deterministically
materializes admitted drafts as existing v1 observations inside a bounded
batch. It does not evaluate authentication, consent, restriction, erasure,
policy, or source freshness; it does not persist, route, answer, notify,
execute, call the signal producer, or create runtime authority.

A future admission gate must resolve and re-check every referenced object and
current authorization/restriction/erasure state before using a batch.
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from .contracts import SubjectRef
from .observations import ContinuitySignalObservation
from .source_admission import (
    ContinuityAuthorizationContext,
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
from .source_admission_payloads import (
    ContinuityObservationDraft,
    ContinuitySourceEnvelope,
)

SOURCE_ADMISSION_DECISION_SCHEMA_VERSION = "continuity.source_admission.decisions.v1"
_REJECTION_AUTHORITY = "draft_rejection_evidence_only"
_RECEIPT_AUTHORITY = "observation_admission_evidence_only"
_LINK_AUTHORITY = "draft_observation_trace_only"


class ContinuityAdmissionDisposition(str, Enum):
    """Structural outcome of a complete draft partition."""

    ADMITTED = "admitted"
    PARTIAL = "partial"
    REJECTED = "rejected"


def _typed_tuple(values: object, name: str, expected: type[object]) -> tuple[object, ...]:
    items = _items(values, name)
    if any(not isinstance(value, expected) for value in items):
        raise ContinuitySourceAdmissionError(
            f"{name} must contain {expected.__name__} values"
        )
    return items


def _unique_by_id(values: tuple[object, ...], name: str, field_name: str) -> None:
    identifiers = tuple(getattr(value, field_name) for value in values)
    if len(identifiers) != len(set(identifiers)):
        raise ContinuitySourceAdmissionError(f"{name} cannot contain duplicate IDs")


def _subject_keys(subjects: tuple[SubjectRef, ...]) -> frozenset[tuple[str, str]]:
    return frozenset((subject.subject_id, subject.kind.value) for subject in subjects)


@dataclass(frozen=True, slots=True)
class ContinuityDraftRejection:
    """Reason-coded rejection evidence for one observation draft."""

    rejection_id: str
    schema_version: str
    draft_id: str
    reason_code: str
    evidence_refs: tuple[str, ...]
    authority: str = _REJECTION_AUTHORITY

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "schema_version", _text(self.schema_version, "schema_version")
        )
        object.__setattr__(self, "draft_id", _hash(self.draft_id, "draft_id"))
        object.__setattr__(
            self, "reason_code", _text(self.reason_code, "reason_code")
        )
        object.__setattr__(
            self,
            "evidence_refs",
            _refs(self.evidence_refs, "evidence_refs", required=True),
        )
        object.__setattr__(self, "authority", _text(self.authority, "authority"))
        if self.authority != _REJECTION_AUTHORITY:
            raise ContinuitySourceAdmissionError(
                f"authority must be {_REJECTION_AUTHORITY!r}"
            )
        _verify_id(
            self.rejection_id,
            _digest(self.identity_payload()),
            "rejection_id",
        )

    @classmethod
    def create(
        cls,
        *,
        draft: ContinuityObservationDraft,
        reason_code: str,
        evidence_refs: Iterable[str],
        schema_version: str = SOURCE_ADMISSION_DECISION_SCHEMA_VERSION,
    ) -> ContinuityDraftRejection:
        if not isinstance(draft, ContinuityObservationDraft):
            raise ContinuitySourceAdmissionError(
                "draft must be a ContinuityObservationDraft"
            )
        version = _text(schema_version, "schema_version")
        reason = _text(reason_code, "reason_code")
        evidence = _refs(evidence_refs, "evidence_refs", required=True)
        payload: dict[str, object] = {
            "schema_version": version,
            "draft_id": draft.draft_id,
            "reason_code": reason,
            "evidence_refs": list(evidence),
            "authority": _REJECTION_AUTHORITY,
        }
        return cls(
            rejection_id=_digest(payload),
            schema_version=version,
            draft_id=draft.draft_id,
            reason_code=reason,
            evidence_refs=evidence,
            authority=_REJECTION_AUTHORITY,
        )

    def identity_payload(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "draft_id": self.draft_id,
            "reason_code": self.reason_code,
            "evidence_refs": list(self.evidence_refs),
            "authority": self.authority,
        }

    def to_dict(self) -> dict[str, object]:
        return {"rejection_id": self.rejection_id, **self.identity_payload()}


@dataclass(frozen=True, slots=True)
class ContinuityObservationAdmissionReceipt:
    """Immutable evidence that completely partitions one envelope's drafts."""

    receipt_id: str
    schema_version: str
    source_envelope_id: str
    source_binding_receipt_id: str
    authorization_context_id: str
    policy_snapshot_id: str
    adapter_id: str
    adapter_version: str
    draft_ids: tuple[str, ...]
    admitted_draft_ids: tuple[str, ...]
    rejected_drafts: tuple[ContinuityDraftRejection, ...]
    disposition: ContinuityAdmissionDisposition
    evaluated_at: datetime
    authority: str = _RECEIPT_AUTHORITY

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "schema_version", _text(self.schema_version, "schema_version")
        )
        for field_name in (
            "source_envelope_id",
            "source_binding_receipt_id",
            "authorization_context_id",
        ):
            object.__setattr__(
                self,
                field_name,
                _hash(getattr(self, field_name), field_name),
            )
        object.__setattr__(
            self,
            "policy_snapshot_id",
            _text(self.policy_snapshot_id, "policy_snapshot_id"),
        )
        object.__setattr__(self, "adapter_id", _text(self.adapter_id, "adapter_id"))
        object.__setattr__(
            self, "adapter_version", _text(self.adapter_version, "adapter_version")
        )
        object.__setattr__(
            self, "draft_ids", _refs(self.draft_ids, "draft_ids", required=True)
        )
        object.__setattr__(
            self,
            "admitted_draft_ids",
            _refs(self.admitted_draft_ids, "admitted_draft_ids"),
        )
        rejection_items = _typed_tuple(
            self.rejected_drafts,
            "rejected_drafts",
            ContinuityDraftRejection,
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
        _unique_by_id(rejections, "rejected_drafts", "draft_id")
        object.__setattr__(self, "rejected_drafts", rejections)
        if not isinstance(self.disposition, ContinuityAdmissionDisposition):
            raise ContinuitySourceAdmissionError(
                "disposition must be a ContinuityAdmissionDisposition"
            )
        object.__setattr__(
            self, "evaluated_at", _aware(self.evaluated_at, "evaluated_at")
        )
        object.__setattr__(self, "authority", _text(self.authority, "authority"))
        if self.authority != _RECEIPT_AUTHORITY:
            raise ContinuitySourceAdmissionError(
                f"authority must be {_RECEIPT_AUTHORITY!r}"
            )
        admitted = set(self.admitted_draft_ids)
        rejected = {value.draft_id for value in self.rejected_drafts}
        drafts = set(self.draft_ids)
        if admitted & rejected:
            raise ContinuitySourceAdmissionError(
                "admitted and rejected draft IDs must be disjoint"
            )
        if admitted | rejected != drafts:
            raise ContinuitySourceAdmissionError(
                "admitted and rejected draft IDs must completely partition draft_ids"
            )
        expected_disposition = self._derive_disposition(
            admitted_count=len(admitted),
            rejected_count=len(rejected),
        )
        if self.disposition is not expected_disposition:
            raise ContinuitySourceAdmissionError(
                "disposition must match the admitted/rejected partition"
            )
        _verify_id(
            self.receipt_id,
            _digest(self.identity_payload()),
            "receipt_id",
        )

    @staticmethod
    def _derive_disposition(
        *, admitted_count: int, rejected_count: int
    ) -> ContinuityAdmissionDisposition:
        if admitted_count and rejected_count:
            return ContinuityAdmissionDisposition.PARTIAL
        if admitted_count:
            return ContinuityAdmissionDisposition.ADMITTED
        return ContinuityAdmissionDisposition.REJECTED

    @classmethod
    def create(
        cls,
        *,
        source_envelope: ContinuitySourceEnvelope,
        binding_receipt: ContinuitySourceBindingReceipt,
        authorization_context: ContinuityAuthorizationContext,
        drafts: Iterable[ContinuityObservationDraft],
        admitted_drafts: Iterable[ContinuityObservationDraft],
        rejected_drafts: Iterable[ContinuityDraftRejection],
        evaluated_at: datetime,
        schema_version: str = SOURCE_ADMISSION_DECISION_SCHEMA_VERSION,
    ) -> ContinuityObservationAdmissionReceipt:
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
        if source_envelope.source_binding_receipt_id != binding_receipt.binding_receipt_id:
            raise ContinuitySourceAdmissionError(
                "source envelope must reference the supplied binding receipt"
            )
        if source_envelope.authorization_context_id != authorization_context.authorization_context_id:
            raise ContinuitySourceAdmissionError(
                "source envelope must reference the supplied authorization context"
            )
        if not (
            source_envelope.tenant_ref
            == binding_receipt.tenant_ref
            == authorization_context.tenant_ref
        ):
            raise ContinuitySourceAdmissionError(
                "envelope, binding and authorization tenants must match"
            )
        if source_envelope.subject_refs != binding_receipt.subject_refs:
            raise ContinuitySourceAdmissionError(
                "envelope subjects must exactly match binding subjects"
            )
        if not _subject_keys(source_envelope.subject_refs).issubset(
            _subject_keys(authorization_context.subject_refs)
        ):
            raise ContinuitySourceAdmissionError(
                "source subjects must be a subset of authorized subjects"
            )
        if (
            source_envelope.source_type != binding_receipt.source_type
            or source_envelope.source_result_id != binding_receipt.source_result_id
            or source_envelope.source_digest != binding_receipt.source_digest
            or source_envelope.source_policy_version
            != binding_receipt.source_policy_version
            or source_envelope.evidence_refs != binding_receipt.evidence_refs
        ):
            raise ContinuitySourceAdmissionError(
                "source envelope content must match the binding receipt"
            )
        draft_items = _typed_tuple(drafts, "drafts", ContinuityObservationDraft)
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
        if not normalized_drafts:
            raise ContinuitySourceAdmissionError("drafts cannot be empty")
        _unique_by_id(normalized_drafts, "drafts", "draft_id")
        if any(
            value.source_envelope_id != source_envelope.envelope_id
            for value in normalized_drafts
        ):
            raise ContinuitySourceAdmissionError(
                "all drafts must reference the supplied source envelope"
            )
        admitted_items = _typed_tuple(
            admitted_drafts,
            "admitted_drafts",
            ContinuityObservationDraft,
        )
        normalized_admitted = tuple(
            sorted(
                (
                    value
                    for value in admitted_items
                    if isinstance(value, ContinuityObservationDraft)
                ),
                key=lambda value: value.draft_id,
            )
        )
        _unique_by_id(normalized_admitted, "admitted_drafts", "draft_id")
        all_ids = {value.draft_id for value in normalized_drafts}
        admitted_ids = {value.draft_id for value in normalized_admitted}
        if not admitted_ids.issubset(all_ids):
            raise ContinuitySourceAdmissionError(
                "admitted_drafts must be a subset of drafts"
            )
        rejection_items = _typed_tuple(
            rejected_drafts,
            "rejected_drafts",
            ContinuityDraftRejection,
        )
        normalized_rejections = tuple(
            sorted(
                (
                    value
                    for value in rejection_items
                    if isinstance(value, ContinuityDraftRejection)
                ),
                key=lambda value: value.draft_id,
            )
        )
        _unique_by_id(normalized_rejections, "rejected_drafts", "draft_id")
        rejected_ids = {value.draft_id for value in normalized_rejections}
        if not rejected_ids.issubset(all_ids):
            raise ContinuitySourceAdmissionError(
                "rejected draft IDs must be a subset of drafts"
            )
        if admitted_ids & rejected_ids:
            raise ContinuitySourceAdmissionError(
                "admitted and rejected draft IDs must be disjoint"
            )
        if admitted_ids | rejected_ids != all_ids:
            raise ContinuitySourceAdmissionError(
                "admitted and rejected drafts must completely partition drafts"
            )
        evaluated = _aware(evaluated_at, "evaluated_at")
        if evaluated < source_envelope.created_at or any(
            evaluated < value.created_at for value in normalized_drafts
        ):
            raise ContinuitySourceAdmissionError(
                "evaluated_at cannot be earlier than envelope or draft creation"
            )
        if not (
            authorization_context.valid_from
            <= evaluated
            < authorization_context.valid_until
        ):
            raise ContinuitySourceAdmissionError(
                "evaluated_at must fall within the authorization validity interval"
            )
        disposition = cls._derive_disposition(
            admitted_count=len(admitted_ids),
            rejected_count=len(rejected_ids),
        )
        version = _text(schema_version, "schema_version")
        payload: dict[str, object] = {
            "schema_version": version,
            "source_envelope_id": source_envelope.envelope_id,
            "source_binding_receipt_id": binding_receipt.binding_receipt_id,
            "authorization_context_id": authorization_context.authorization_context_id,
            "policy_snapshot_id": authorization_context.policy_snapshot_id,
            "adapter_id": source_envelope.producer_adapter_id,
            "adapter_version": source_envelope.producer_adapter_version,
            "draft_ids": sorted(all_ids),
            "admitted_draft_ids": sorted(admitted_ids),
            "rejected_drafts": [
                value.to_dict() for value in normalized_rejections
            ],
            "disposition": disposition.value,
            "evaluated_at": _canonical_datetime(evaluated),
            "authority": _RECEIPT_AUTHORITY,
        }
        return cls(
            receipt_id=_digest(payload),
            schema_version=version,
            source_envelope_id=source_envelope.envelope_id,
            source_binding_receipt_id=binding_receipt.binding_receipt_id,
            authorization_context_id=authorization_context.authorization_context_id,
            policy_snapshot_id=authorization_context.policy_snapshot_id,
            adapter_id=source_envelope.producer_adapter_id,
            adapter_version=source_envelope.producer_adapter_version,
            draft_ids=tuple(sorted(all_ids)),
            admitted_draft_ids=tuple(sorted(admitted_ids)),
            rejected_drafts=normalized_rejections,
            disposition=disposition,
            evaluated_at=evaluated,
            authority=_RECEIPT_AUTHORITY,
        )

    def identity_payload(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "source_envelope_id": self.source_envelope_id,
            "source_binding_receipt_id": self.source_binding_receipt_id,
            "authorization_context_id": self.authorization_context_id,
            "policy_snapshot_id": self.policy_snapshot_id,
            "adapter_id": self.adapter_id,
            "adapter_version": self.adapter_version,
            "draft_ids": list(self.draft_ids),
            "admitted_draft_ids": list(self.admitted_draft_ids),
            "rejected_drafts": [value.to_dict() for value in self.rejected_drafts],
            "disposition": self.disposition.value,
            "evaluated_at": _canonical_datetime(self.evaluated_at),
            "authority": self.authority,
        }

    def to_dict(self) -> dict[str, object]:
        return {"receipt_id": self.receipt_id, **self.identity_payload()}


@dataclass(frozen=True, slots=True)
class ContinuityDraftObservationLink:
    """Immutable trace from one admitted draft to one v1 observation."""

    link_id: str
    schema_version: str
    draft_id: str
    observation_id: str
    source_envelope_id: str
    authority: str = _LINK_AUTHORITY

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "schema_version", _text(self.schema_version, "schema_version")
        )
        for field_name in ("draft_id", "observation_id", "source_envelope_id"):
            object.__setattr__(
                self,
                field_name,
                _hash(getattr(self, field_name), field_name),
            )
        object.__setattr__(self, "authority", _text(self.authority, "authority"))
        if self.authority != _LINK_AUTHORITY:
            raise ContinuitySourceAdmissionError(
                f"authority must be {_LINK_AUTHORITY!r}"
            )
        _verify_id(self.link_id, _digest(self.identity_payload()), "link_id")

    @classmethod
    def create(
        cls,
        *,
        draft: ContinuityObservationDraft,
        observation: ContinuitySignalObservation,
        schema_version: str = SOURCE_ADMISSION_DECISION_SCHEMA_VERSION,
    ) -> ContinuityDraftObservationLink:
        if not isinstance(draft, ContinuityObservationDraft):
            raise ContinuitySourceAdmissionError(
                "draft must be a ContinuityObservationDraft"
            )
        if not isinstance(observation, ContinuitySignalObservation):
            raise ContinuitySourceAdmissionError(
                "observation must be a ContinuitySignalObservation"
            )
        version = _text(schema_version, "schema_version")
        payload: dict[str, object] = {
            "schema_version": version,
            "draft_id": draft.draft_id,
            "observation_id": observation.observation_id,
            "source_envelope_id": draft.source_envelope_id,
            "authority": _LINK_AUTHORITY,
        }
        return cls(
            link_id=_digest(payload),
            schema_version=version,
            draft_id=draft.draft_id,
            observation_id=observation.observation_id,
            source_envelope_id=draft.source_envelope_id,
            authority=_LINK_AUTHORITY,
        )

    def identity_payload(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "draft_id": self.draft_id,
            "observation_id": self.observation_id,
            "source_envelope_id": self.source_envelope_id,
            "authority": self.authority,
        }

    def to_dict(self) -> dict[str, object]:
        return {"link_id": self.link_id, **self.identity_payload()}


def _observation_from_draft(
    draft: ContinuityObservationDraft,
    envelope: ContinuitySourceEnvelope,
) -> ContinuitySignalObservation:
    if draft.source_envelope_id != envelope.envelope_id:
        raise ContinuitySourceAdmissionError(
            "draft must reference the supplied source envelope"
        )
    return ContinuitySignalObservation.create(
        signal_type=draft.signal_type,
        value=draft.value,
        confidence=draft.proposed_confidence,
        producer=envelope.producer_adapter_id,
        source_type=envelope.source_type,
        source_id=envelope.source_result_id,
        observed_at=envelope.source_as_of,
        evidence_refs=draft.evidence_refs,
        reason_codes=draft.reason_codes,
        scope=draft.scope,
    )


@dataclass(frozen=True, slots=True)
class AuthorizedContinuityObservationBatch:
    """Bounded batch of admitted v1 observations with no runtime authority."""

    batch_id: str
    schema_version: str
    authorization_context_id: str
    admission_receipt_ids: tuple[str, ...]
    source_binding_receipt_ids: tuple[str, ...]
    tenant_ref: str
    subject_refs: tuple[SubjectRef, ...]
    observations: tuple[ContinuitySignalObservation, ...]
    draft_observation_links: tuple[ContinuityDraftObservationLink, ...]
    source_envelope_ids: tuple[str, ...]
    policy_snapshot_id: str
    created_at: datetime
    valid_until: datetime
    no_runtime_authority: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "schema_version", _text(self.schema_version, "schema_version")
        )
        object.__setattr__(
            self,
            "authorization_context_id",
            _hash(self.authorization_context_id, "authorization_context_id"),
        )
        object.__setattr__(
            self,
            "admission_receipt_ids",
            _refs(
                self.admission_receipt_ids,
                "admission_receipt_ids",
                required=True,
            ),
        )
        object.__setattr__(
            self,
            "source_binding_receipt_ids",
            _refs(
                self.source_binding_receipt_ids,
                "source_binding_receipt_ids",
                required=True,
            ),
        )
        object.__setattr__(
            self, "tenant_ref", _text(self.tenant_ref, "tenant_ref")
        )
        object.__setattr__(self, "subject_refs", _subjects(self.subject_refs))
        observation_items = _typed_tuple(
            self.observations,
            "observations",
            ContinuitySignalObservation,
        )
        observations = tuple(
            sorted(
                (
                    value
                    for value in observation_items
                    if isinstance(value, ContinuitySignalObservation)
                ),
                key=lambda value: value.observation_id,
            )
        )
        if not observations:
            raise ContinuitySourceAdmissionError("observations cannot be empty")
        _unique_by_id(observations, "observations", "observation_id")
        object.__setattr__(self, "observations", observations)
        link_items = _typed_tuple(
            self.draft_observation_links,
            "draft_observation_links",
            ContinuityDraftObservationLink,
        )
        links = tuple(
            sorted(
                (
                    value
                    for value in link_items
                    if isinstance(value, ContinuityDraftObservationLink)
                ),
                key=lambda value: value.draft_id,
            )
        )
        if not links:
            raise ContinuitySourceAdmissionError(
                "draft_observation_links cannot be empty"
            )
        _unique_by_id(links, "draft_observation_links", "draft_id")
        _unique_by_id(links, "draft_observation_links", "observation_id")
        if {value.observation_id for value in links} != {
            value.observation_id for value in observations
        }:
            raise ContinuitySourceAdmissionError(
                "draft_observation_links must map exactly to observations"
            )
        object.__setattr__(self, "draft_observation_links", links)
        object.__setattr__(
            self,
            "source_envelope_ids",
            _refs(self.source_envelope_ids, "source_envelope_ids", required=True),
        )
        if not {value.source_envelope_id for value in links}.issubset(
            set(self.source_envelope_ids)
        ):
            raise ContinuitySourceAdmissionError(
                "all trace links must reference source_envelope_ids"
            )
        object.__setattr__(
            self,
            "policy_snapshot_id",
            _text(self.policy_snapshot_id, "policy_snapshot_id"),
        )
        object.__setattr__(self, "created_at", _aware(self.created_at, "created_at"))
        object.__setattr__(
            self, "valid_until", _aware(self.valid_until, "valid_until")
        )
        if self.valid_until <= self.created_at:
            raise ContinuitySourceAdmissionError(
                "valid_until must be later than created_at"
            )
        if self.no_runtime_authority is not True:
            raise ContinuitySourceAdmissionError(
                "no_runtime_authority must remain True"
            )
        _verify_id(self.batch_id, _digest(self.identity_payload()), "batch_id")

    @classmethod
    def create(
        cls,
        *,
        authorization_context: ContinuityAuthorizationContext,
        receipts: Iterable[ContinuityObservationAdmissionReceipt],
        envelopes: Iterable[ContinuitySourceEnvelope],
        binding_receipts: Iterable[ContinuitySourceBindingReceipt],
        admitted_drafts: Iterable[ContinuityObservationDraft],
        created_at: datetime,
        valid_until: datetime,
        schema_version: str = SOURCE_ADMISSION_DECISION_SCHEMA_VERSION,
    ) -> AuthorizedContinuityObservationBatch:
        if not isinstance(authorization_context, ContinuityAuthorizationContext):
            raise ContinuitySourceAdmissionError(
                "authorization_context must be a ContinuityAuthorizationContext"
            )
        receipt_items = _typed_tuple(
            receipts,
            "receipts",
            ContinuityObservationAdmissionReceipt,
        )
        normalized_receipts = tuple(
            sorted(
                (
                    value
                    for value in receipt_items
                    if isinstance(value, ContinuityObservationAdmissionReceipt)
                ),
                key=lambda value: value.receipt_id,
            )
        )
        if not normalized_receipts:
            raise ContinuitySourceAdmissionError("receipts cannot be empty")
        _unique_by_id(normalized_receipts, "receipts", "receipt_id")
        _unique_by_id(normalized_receipts, "receipts", "source_envelope_id")
        envelope_items = _typed_tuple(
            envelopes,
            "envelopes",
            ContinuitySourceEnvelope,
        )
        normalized_envelopes = tuple(
            sorted(
                (
                    value
                    for value in envelope_items
                    if isinstance(value, ContinuitySourceEnvelope)
                ),
                key=lambda value: value.envelope_id,
            )
        )
        if not normalized_envelopes:
            raise ContinuitySourceAdmissionError("envelopes cannot be empty")
        _unique_by_id(normalized_envelopes, "envelopes", "envelope_id")
        binding_items = _typed_tuple(
            binding_receipts,
            "binding_receipts",
            ContinuitySourceBindingReceipt,
        )
        normalized_bindings = tuple(
            sorted(
                (
                    value
                    for value in binding_items
                    if isinstance(value, ContinuitySourceBindingReceipt)
                ),
                key=lambda value: value.binding_receipt_id,
            )
        )
        if not normalized_bindings:
            raise ContinuitySourceAdmissionError(
                "binding_receipts cannot be empty"
            )
        _unique_by_id(normalized_bindings, "binding_receipts", "binding_receipt_id")
        envelope_map = {value.envelope_id: value for value in normalized_envelopes}
        binding_map = {
            value.binding_receipt_id: value for value in normalized_bindings
        }
        receipt_envelope_ids = {
            value.source_envelope_id for value in normalized_receipts
        }
        receipt_binding_ids = {
            value.source_binding_receipt_id for value in normalized_receipts
        }
        if set(envelope_map) != receipt_envelope_ids:
            raise ContinuitySourceAdmissionError(
                "envelopes must exactly match receipt source envelopes"
            )
        if set(binding_map) != receipt_binding_ids:
            raise ContinuitySourceAdmissionError(
                "binding_receipts must exactly match receipt binding receipts"
            )
        if any(
            value.authorization_context_id
            != authorization_context.authorization_context_id
            or value.policy_snapshot_id != authorization_context.policy_snapshot_id
            for value in normalized_receipts
        ):
            raise ContinuitySourceAdmissionError(
                "all receipts must match the authorization context and policy snapshot"
            )
        for receipt in normalized_receipts:
            envelope = envelope_map[receipt.source_envelope_id]
            binding = binding_map[receipt.source_binding_receipt_id]
            if envelope.source_binding_receipt_id != binding.binding_receipt_id:
                raise ContinuitySourceAdmissionError(
                    "receipt envelope must reference its binding receipt"
                )
            if envelope.authorization_context_id != authorization_context.authorization_context_id:
                raise ContinuitySourceAdmissionError(
                    "all envelopes must match the authorization context"
                )
            if not (
                envelope.tenant_ref
                == binding.tenant_ref
                == authorization_context.tenant_ref
            ):
                raise ContinuitySourceAdmissionError(
                    "all batch tenants must match"
                )
            if envelope.subject_refs != binding.subject_refs:
                raise ContinuitySourceAdmissionError(
                    "envelope subjects must match binding subjects"
                )
            if receipt.adapter_id != envelope.producer_adapter_id or (
                receipt.adapter_version != envelope.producer_adapter_version
            ):
                raise ContinuitySourceAdmissionError(
                    "receipt adapter identity must match its envelope"
                )
        draft_items = _typed_tuple(
            admitted_drafts,
            "admitted_drafts",
            ContinuityObservationDraft,
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
        if not normalized_drafts:
            raise ContinuitySourceAdmissionError("admitted_drafts cannot be empty")
        _unique_by_id(normalized_drafts, "admitted_drafts", "draft_id")
        required_admitted_ids = {
            draft_id
            for receipt in normalized_receipts
            for draft_id in receipt.admitted_draft_ids
        }
        supplied_draft_ids = {value.draft_id for value in normalized_drafts}
        if supplied_draft_ids != required_admitted_ids:
            raise ContinuitySourceAdmissionError(
                "admitted_drafts must exactly match receipt admitted_draft_ids"
            )
        receipt_by_envelope = {
            value.source_envelope_id: value for value in normalized_receipts
        }
        if any(
            value.source_envelope_id not in receipt_by_envelope
            for value in normalized_drafts
        ):
            raise ContinuitySourceAdmissionError(
                "every admitted draft must reference a receipt envelope"
            )
        observations: list[ContinuitySignalObservation] = []
        links: list[ContinuityDraftObservationLink] = []
        for draft in normalized_drafts:
            envelope = envelope_map[draft.source_envelope_id]
            observation = _observation_from_draft(draft, envelope)
            observations.append(observation)
            links.append(
                ContinuityDraftObservationLink.create(
                    draft=draft,
                    observation=observation,
                    schema_version=schema_version,
                )
            )
        if len({value.observation_id for value in observations}) != len(observations):
            raise ContinuitySourceAdmissionError(
                "multiple admitted drafts cannot collapse to one v1 observation"
            )
        subjects_by_key: dict[tuple[str, str], SubjectRef] = {}
        for envelope in normalized_envelopes:
            for subject in envelope.subject_refs:
                subjects_by_key[(subject.subject_id, subject.kind.value)] = subject
        batch_subjects = tuple(
            sorted(
                subjects_by_key.values(),
                key=lambda value: (value.subject_id, value.kind.value),
            )
        )
        if not _subject_keys(batch_subjects).issubset(
            _subject_keys(authorization_context.subject_refs)
        ):
            raise ContinuitySourceAdmissionError(
                "batch subjects must be a subset of authorized subjects"
            )
        created = _aware(created_at, "created_at")
        if any(created < value.evaluated_at for value in normalized_receipts):
            raise ContinuitySourceAdmissionError(
                "created_at cannot be earlier than receipt evaluation"
            )
        expires = _aware(valid_until, "valid_until")
        if expires <= created:
            raise ContinuitySourceAdmissionError(
                "valid_until must be later than created_at"
            )
        if not (
            authorization_context.valid_from
            <= created
            < expires
            <= authorization_context.valid_until
        ):
            raise ContinuitySourceAdmissionError(
                "batch validity must remain within authorization validity"
            )
        version = _text(schema_version, "schema_version")
        normalized_observations = tuple(
            sorted(observations, key=lambda value: value.observation_id)
        )
        normalized_links = tuple(sorted(links, key=lambda value: value.draft_id))
        payload: dict[str, object] = {
            "schema_version": version,
            "authorization_context_id": authorization_context.authorization_context_id,
            "admission_receipt_ids": [
                value.receipt_id for value in normalized_receipts
            ],
            "source_binding_receipt_ids": [
                value.binding_receipt_id for value in normalized_bindings
            ],
            "tenant_ref": authorization_context.tenant_ref,
            "subject_refs": _subject_payload(batch_subjects),
            "observations": [value.to_dict() for value in normalized_observations],
            "draft_observation_links": [
                value.to_dict() for value in normalized_links
            ],
            "source_envelope_ids": [
                value.envelope_id for value in normalized_envelopes
            ],
            "policy_snapshot_id": authorization_context.policy_snapshot_id,
            "created_at": _canonical_datetime(created),
            "valid_until": _canonical_datetime(expires),
            "no_runtime_authority": True,
        }
        return cls(
            batch_id=_digest(payload),
            schema_version=version,
            authorization_context_id=authorization_context.authorization_context_id,
            admission_receipt_ids=tuple(
                value.receipt_id for value in normalized_receipts
            ),
            source_binding_receipt_ids=tuple(
                value.binding_receipt_id for value in normalized_bindings
            ),
            tenant_ref=authorization_context.tenant_ref,
            subject_refs=batch_subjects,
            observations=normalized_observations,
            draft_observation_links=normalized_links,
            source_envelope_ids=tuple(
                value.envelope_id for value in normalized_envelopes
            ),
            policy_snapshot_id=authorization_context.policy_snapshot_id,
            created_at=created,
            valid_until=expires,
            no_runtime_authority=True,
        )

    def identity_payload(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "authorization_context_id": self.authorization_context_id,
            "admission_receipt_ids": list(self.admission_receipt_ids),
            "source_binding_receipt_ids": list(
                self.source_binding_receipt_ids
            ),
            "tenant_ref": self.tenant_ref,
            "subject_refs": _subject_payload(self.subject_refs),
            "observations": [value.to_dict() for value in self.observations],
            "draft_observation_links": [
                value.to_dict() for value in self.draft_observation_links
            ],
            "source_envelope_ids": list(self.source_envelope_ids),
            "policy_snapshot_id": self.policy_snapshot_id,
            "created_at": _canonical_datetime(self.created_at),
            "valid_until": _canonical_datetime(self.valid_until),
            "no_runtime_authority": self.no_runtime_authority,
        }

    def to_dict(self) -> dict[str, object]:
        return {"batch_id": self.batch_id, **self.identity_payload()}
