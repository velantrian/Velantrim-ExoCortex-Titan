"""Strict, rebuildable cross-section relation candidates for PR-RDR-06.

Relations are derived proposals over existing SectionCard claims. They are not
facts, graph authority, Canon entries, memory writes, or execution commands.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from core.knowledge_capsule import SourceSpan
from core.reader_core_contracts import RelationKind, stable_reader_core_id
from core.section_card import SectionCard, SectionCardClaim

SECTION_RELATION_SCHEMA_VERSION = "reader-core.section-relations.v1"


class SectionRelationError(ValueError):
    """Raised when a relation candidate or relation set violates invariants."""


class RelationValidationState(str, Enum):
    UNVALIDATED = "unvalidated"
    SUPPORTED = "supported"
    REJECTED = "rejected"
    AMBIGUOUS = "ambiguous"


@dataclass(frozen=True, slots=True)
class ClaimEndpoint:
    """One exact claim endpoint inside one SectionCard."""

    document_id: str
    source_revision: str
    structure_map_id: str
    plan_id: str
    card_id: str
    section_id: str
    unit_id: str
    claim_id: str
    source_spans: tuple[SourceSpan, ...]

    def __post_init__(self) -> None:
        for name in (
            "document_id",
            "source_revision",
            "structure_map_id",
            "plan_id",
            "card_id",
            "section_id",
            "unit_id",
            "claim_id",
        ):
            _require_text(getattr(self, name), name)
        spans = tuple(self.source_spans)
        if not spans or any(not isinstance(span, SourceSpan) for span in spans):
            raise SectionRelationError("source_spans require SourceSpan values")
        for span in spans:
            if span.document_id != self.document_id:
                raise SectionRelationError("endpoint span document_id mismatch")
            if span.source_revision != self.source_revision:
                raise SectionRelationError("endpoint span source_revision mismatch")
        object.__setattr__(self, "source_spans", spans)

    @classmethod
    def from_card_claim(
        cls,
        card: SectionCard,
        card_claim: SectionCardClaim,
    ) -> ClaimEndpoint:
        if card_claim not in card.claims:
            raise SectionRelationError("card_claim must belong to card")
        return cls(
            document_id=card.document_id,
            source_revision=card.source_revision,
            structure_map_id=card.structure_map_id,
            plan_id=card.plan_id,
            card_id=card.card_id,
            section_id=card.section_id,
            unit_id=card.unit_id,
            claim_id=card_claim.claim.claim_id,
            source_spans=card_claim.claim.source_spans,
        )

    def identity_payload(self) -> dict[str, object]:
        return {
            "document_id": self.document_id,
            "source_revision": self.source_revision,
            "structure_map_id": self.structure_map_id,
            "plan_id": self.plan_id,
            "card_id": self.card_id,
            "section_id": self.section_id,
            "unit_id": self.unit_id,
            "claim_id": self.claim_id,
            "source_spans": [span.identity_payload() for span in self.source_spans],
        }


@dataclass(frozen=True, slots=True)
class CrossSectionRelationCandidate:
    """One directed, source-linked, non-authoritative relation proposal."""

    relation_id: str
    schema_version: str
    detector_id: str
    detector_version: str
    kind: RelationKind
    source: ClaimEndpoint
    target: ClaimEndpoint
    reason_code: str
    evidence_spans: tuple[SourceSpan, ...]
    validation_state: RelationValidationState = RelationValidationState.UNVALIDATED

    def __post_init__(self) -> None:
        for name in (
            "relation_id",
            "schema_version",
            "detector_id",
            "detector_version",
            "reason_code",
        ):
            _require_text(getattr(self, name), name)
        if self.schema_version != SECTION_RELATION_SCHEMA_VERSION:
            raise SectionRelationError("unsupported relation schema_version")
        if not isinstance(self.kind, RelationKind):
            raise SectionRelationError("kind must be a RelationKind")
        if not isinstance(self.source, ClaimEndpoint):
            raise SectionRelationError("source must be a ClaimEndpoint")
        if not isinstance(self.target, ClaimEndpoint):
            raise SectionRelationError("target must be a ClaimEndpoint")
        _validate_endpoint_pair(self.source, self.target)
        if self.source.claim_id == self.target.claim_id:
            raise SectionRelationError("relation self-loops are forbidden")
        spans = tuple(self.evidence_spans)
        if not spans or any(not isinstance(span, SourceSpan) for span in spans):
            raise SectionRelationError("evidence_spans require SourceSpan values")
        for span in spans:
            if span.document_id != self.source.document_id:
                raise SectionRelationError("evidence span document_id mismatch")
            if span.source_revision != self.source.source_revision:
                raise SectionRelationError("evidence span source_revision mismatch")
        object.__setattr__(self, "evidence_spans", spans)
        if not isinstance(self.validation_state, RelationValidationState):
            raise SectionRelationError(
                "validation_state must be a RelationValidationState"
            )
        expected_id = _relation_identity(
            detector_id=self.detector_id,
            detector_version=self.detector_version,
            kind=self.kind,
            source=self.source,
            target=self.target,
            reason_code=self.reason_code,
            evidence_spans=spans,
        )
        if self.relation_id != expected_id:
            raise SectionRelationError(
                "relation_id does not match relation content"
            )

    @classmethod
    def create(
        cls,
        *,
        detector_id: str,
        detector_version: str,
        kind: RelationKind,
        source: ClaimEndpoint,
        target: ClaimEndpoint,
        reason_code: str,
        evidence_spans: Iterable[SourceSpan],
    ) -> CrossSectionRelationCandidate:
        spans = tuple(evidence_spans)
        return cls(
            relation_id=_relation_identity(
                detector_id=detector_id,
                detector_version=detector_version,
                kind=kind,
                source=source,
                target=target,
                reason_code=reason_code,
                evidence_spans=spans,
            ),
            schema_version=SECTION_RELATION_SCHEMA_VERSION,
            detector_id=detector_id,
            detector_version=detector_version,
            kind=kind,
            source=source,
            target=target,
            reason_code=reason_code,
            evidence_spans=spans,
        )

    @property
    def canonical_key(self) -> tuple[str, str, str]:
        return (self.kind.value, self.source.claim_id, self.target.claim_id)


@dataclass(frozen=True, slots=True)
class CrossSectionRelationSet:
    """Canonical rebuildable relation projection for one exact reading plan."""

    relation_set_id: str
    schema_version: str
    document_id: str
    source_revision: str
    structure_map_id: str
    plan_id: str
    known_claim_ids: tuple[str, ...]
    evaluated_pair_keys: tuple[str, ...]
    candidates: tuple[CrossSectionRelationCandidate, ...]

    def __post_init__(self) -> None:
        for name in (
            "relation_set_id",
            "schema_version",
            "document_id",
            "source_revision",
            "structure_map_id",
            "plan_id",
        ):
            _require_text(getattr(self, name), name)
        if self.schema_version != SECTION_RELATION_SCHEMA_VERSION:
            raise SectionRelationError("unsupported relation-set schema_version")
        claims = _unique_sorted_text(self.known_claim_ids, "known_claim_id")
        pair_keys = _unique_sorted_text(
            self.evaluated_pair_keys,
            "evaluated_pair_key",
        )
        candidates = tuple(self.candidates)
        if any(
            not isinstance(candidate, CrossSectionRelationCandidate)
            for candidate in candidates
        ):
            raise SectionRelationError(
                "candidates require CrossSectionRelationCandidate values"
            )
        ordered = tuple(sorted(candidates, key=lambda item: item.canonical_key))
        if candidates != ordered:
            raise SectionRelationError("candidates must use canonical ordering")
        if len({candidate.relation_id for candidate in candidates}) != len(candidates):
            raise SectionRelationError("relation IDs must be unique")
        if len({candidate.canonical_key for candidate in candidates}) != len(candidates):
            raise SectionRelationError("duplicate directed relations are forbidden")
        for candidate in candidates:
            if (
                candidate.source.document_id != self.document_id
                or candidate.target.document_id != self.document_id
                or candidate.source.source_revision != self.source_revision
                or candidate.target.source_revision != self.source_revision
                or candidate.source.structure_map_id != self.structure_map_id
                or candidate.target.structure_map_id != self.structure_map_id
                or candidate.source.plan_id != self.plan_id
                or candidate.target.plan_id != self.plan_id
            ):
                raise SectionRelationError(
                    "every candidate must match relation-set identity"
                )
            if candidate.source.claim_id not in claims:
                raise SectionRelationError("source claim is not in known_claim_ids")
            if candidate.target.claim_id not in claims:
                raise SectionRelationError("target claim is not in known_claim_ids")
        object.__setattr__(self, "known_claim_ids", claims)
        object.__setattr__(self, "evaluated_pair_keys", pair_keys)
        object.__setattr__(self, "candidates", candidates)
        expected_id = stable_reader_core_id(
            "cross-section-relation-set",
            {
                "schema_version": self.schema_version,
                "document_id": self.document_id,
                "source_revision": self.source_revision,
                "structure_map_id": self.structure_map_id,
                "plan_id": self.plan_id,
                "known_claim_ids": list(claims),
                "evaluated_pair_keys": list(pair_keys),
                "relation_ids": [candidate.relation_id for candidate in candidates],
            },
        )
        if self.relation_set_id != expected_id:
            raise SectionRelationError(
                "relation_set_id does not match relation-set content"
            )

    @property
    def relation_denominator(self) -> int:
        return len(self.evaluated_pair_keys)


def relation_pair_key(source_claim_id: str, target_claim_id: str) -> str:
    _require_text(source_claim_id, "source_claim_id")
    _require_text(target_claim_id, "target_claim_id")
    if source_claim_id == target_claim_id:
        raise SectionRelationError("relation pair self-loops are forbidden")
    return f"{source_claim_id}->{target_claim_id}"


def _validate_endpoint_pair(source: ClaimEndpoint, target: ClaimEndpoint) -> None:
    if (
        source.document_id != target.document_id
        or source.source_revision != target.source_revision
        or source.structure_map_id != target.structure_map_id
        or source.plan_id != target.plan_id
    ):
        raise SectionRelationError(
            "relation endpoints must share document, revision, structure map, and plan"
        )


def _relation_identity(
    *,
    detector_id: str,
    detector_version: str,
    kind: RelationKind,
    source: ClaimEndpoint,
    target: ClaimEndpoint,
    reason_code: str,
    evidence_spans: tuple[SourceSpan, ...],
) -> str:
    return stable_reader_core_id(
        "cross-section-relation-candidate",
        {
            "schema_version": SECTION_RELATION_SCHEMA_VERSION,
            "detector_id": detector_id,
            "detector_version": detector_version,
            "kind": kind.value,
            "source": source.identity_payload(),
            "target": target.identity_payload(),
            "reason_code": reason_code,
            "evidence_spans": [span.identity_payload() for span in evidence_spans],
        },
    )


def _require_text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SectionRelationError(f"{field_name} must be a non-empty string")
    return value


def _unique_sorted_text(
    values: Iterable[str],
    field_name: str,
) -> tuple[str, ...]:
    result = tuple(values)
    for value in result:
        _require_text(value, field_name)
    if len(set(result)) != len(result):
        raise SectionRelationError(f"{field_name} values must be unique")
    ordered = tuple(sorted(result))
    if result != ordered:
        raise SectionRelationError(f"{field_name} values must be sorted")
    return result


__all__ = [
    "ClaimEndpoint",
    "CrossSectionRelationCandidate",
    "CrossSectionRelationSet",
    "RelationValidationState",
    "SECTION_RELATION_SCHEMA_VERSION",
    "SectionRelationError",
    "relation_pair_key",
]
