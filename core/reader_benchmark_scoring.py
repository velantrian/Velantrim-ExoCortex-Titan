"""Deterministic Reader Core prediction scoring for PR-RDR-12.

This module normalizes source-linked Reader artifacts and compares them with a
fully adjudicated human label set. Matching is exact and one-to-one. There is no
semantic similarity, embedding, LLM judge, majority vote, or live runtime
wiring.

The output is a PR-RDR-10 ``ReaderBenchmarkObservation``. It remains evaluation
evidence only and grants no Canon, memory, query, policy, graph, tool,
TruthGate, Write Gate, promotion, or live-integration authority.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Hashable
from dataclasses import dataclass
from typing import Iterable, Protocol, TypeAlias, TypeVar

from core.critical_exceptions import (
    CriticalExceptionCandidate,
    ExceptionValidationStatus,
)
from core.global_synthesis import GlobalDocumentSynthesis
from core.knowledge_capsule import ClaimModality, SourceSpan
from core.reader_benchmark_runner import ReaderBenchmarkObservation
from core.reader_core_contracts import RelationKind, stable_reader_core_id
from core.reader_corpus_adjudication import (
    HumanClaimLabel,
    HumanExceptionLabel,
    HumanLabelSet,
    HumanQualifierLabel,
    HumanRelationLabel,
    LabelSetRole,
    QualifierKind,
)
from core.section_card import SectionCard
from core.section_relations import (
    CrossSectionRelationCandidate,
    CrossSectionRelationSet,
    RelationValidationState,
)

READER_SCORING_SCHEMA_VERSION = "reader-core.deterministic-scoring.v1"


class ReaderScoringError(ValueError):
    """Raised when prediction or scoring invariants are invalid."""


class _PredictionWithId(Protocol):
    @property
    def prediction_id(self) -> str: ...


PredictionT = TypeVar("PredictionT", bound=_PredictionWithId)
MatchT = TypeVar("MatchT", bound=Hashable)
SpanKey: TypeAlias = tuple[str, str | None, int, int, str]
ClaimKey: TypeAlias = tuple[
    str,
    tuple[SpanKey, ...],
    tuple[str, ...],
    tuple[str, ...],
]
ExceptionKey: TypeAlias = tuple[str, SpanKey, SpanKey, tuple[str, ...]]
RelationKey: TypeAlias = tuple[str, str, str, tuple[SpanKey, ...]]
QualifierKey: TypeAlias = tuple[str, str, SpanKey]


@dataclass(frozen=True, slots=True)
class ReaderClaimPrediction:
    prediction_id: str
    source_claim_id: str
    document_id: str
    source_revision: str
    modality: ClaimModality
    source_spans: tuple[SourceSpan, ...]
    qualifier_codes: tuple[str, ...] = ()
    applicability_codes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _validate_identity_fields(
            self.prediction_id,
            self.source_claim_id,
            self.document_id,
            self.source_revision,
        )
        if not isinstance(self.modality, ClaimModality):
            raise ReaderScoringError("modality must be a ClaimModality")
        spans = _canonical_spans(
            self.source_spans,
            document_id=self.document_id,
            source_revision=self.source_revision,
            field_name="claim source span",
        )
        qualifiers = _unique_sorted_text(self.qualifier_codes, "qualifier_code")
        applicability = _unique_sorted_text(
            self.applicability_codes,
            "applicability_code",
        )
        object.__setattr__(self, "source_spans", spans)
        object.__setattr__(self, "qualifier_codes", qualifiers)
        object.__setattr__(self, "applicability_codes", applicability)
        _verify_content_id(
            actual=self.prediction_id,
            namespace="reader-scoring-claim-prediction",
            payload=self.identity_payload(include_id=False),
            field_name="prediction_id",
        )

    @classmethod
    def create(
        cls,
        *,
        source_claim_id: str,
        document_id: str,
        source_revision: str,
        modality: ClaimModality,
        source_spans: Iterable[SourceSpan],
        qualifier_codes: Iterable[str] = (),
        applicability_codes: Iterable[str] = (),
    ) -> ReaderClaimPrediction:
        spans = _sorted_spans(source_spans)
        qualifiers = tuple(sorted(qualifier_codes))
        applicability = tuple(sorted(applicability_codes))
        payload: dict[str, object] = {
            "source_claim_id": source_claim_id,
            "document_id": document_id,
            "source_revision": source_revision,
            "modality": modality.value,
            "source_spans": [span.identity_payload() for span in spans],
            "qualifier_codes": list(qualifiers),
            "applicability_codes": list(applicability),
        }
        return cls(
            prediction_id=stable_reader_core_id(
                "reader-scoring-claim-prediction",
                payload,
            ),
            source_claim_id=source_claim_id,
            document_id=document_id,
            source_revision=source_revision,
            modality=modality,
            source_spans=spans,
            qualifier_codes=qualifiers,
            applicability_codes=applicability,
        )

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "source_claim_id": self.source_claim_id,
            "document_id": self.document_id,
            "source_revision": self.source_revision,
            "modality": self.modality.value,
            "source_spans": [span.identity_payload() for span in self.source_spans],
            "qualifier_codes": list(self.qualifier_codes),
            "applicability_codes": list(self.applicability_codes),
        }
        if include_id:
            payload["prediction_id"] = self.prediction_id
        return payload

    @property
    def matching_key(self) -> ClaimKey:
        return (
            self.modality.value,
            tuple(_span_key(span) for span in self.source_spans),
            self.qualifier_codes,
            self.applicability_codes,
        )


@dataclass(frozen=True, slots=True)
class ReaderExceptionPrediction:
    prediction_id: str
    source_candidate_id: str
    document_id: str
    source_revision: str
    category: str
    trigger_span: SourceSpan
    statement_span: SourceSpan
    target_source_claim_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _validate_identity_fields(
            self.prediction_id,
            self.source_candidate_id,
            self.document_id,
            self.source_revision,
            self.category,
        )
        _validate_span(
            self.trigger_span,
            document_id=self.document_id,
            source_revision=self.source_revision,
            field_name="trigger_span",
        )
        _validate_span(
            self.statement_span,
            document_id=self.document_id,
            source_revision=self.source_revision,
            field_name="statement_span",
        )
        if (
            self.trigger_span.start_offset < self.statement_span.start_offset
            or self.trigger_span.end_offset > self.statement_span.end_offset
        ):
            raise ReaderScoringError(
                "trigger_span must be contained in statement_span"
            )
        targets = _unique_sorted_text(
            self.target_source_claim_ids,
            "target_source_claim_id",
        )
        object.__setattr__(self, "target_source_claim_ids", targets)
        _verify_content_id(
            actual=self.prediction_id,
            namespace="reader-scoring-exception-prediction",
            payload=self.identity_payload(include_id=False),
            field_name="prediction_id",
        )

    @classmethod
    def from_candidate(
        cls,
        candidate: CriticalExceptionCandidate,
    ) -> ReaderExceptionPrediction:
        if not isinstance(candidate, CriticalExceptionCandidate):
            raise ReaderScoringError(
                "candidate must be a CriticalExceptionCandidate"
            )
        if candidate.validation_status is ExceptionValidationStatus.REJECTED:
            raise ReaderScoringError(
                "rejected exception candidates are not predictions"
            )
        return cls.create(
            source_candidate_id=candidate.candidate_id,
            document_id=candidate.document_id,
            source_revision=candidate.source_revision,
            category=candidate.category.value,
            trigger_span=candidate.trigger_span,
            statement_span=candidate.statement_span,
            target_source_claim_ids=candidate.target_claim_refs,
        )

    @classmethod
    def create(
        cls,
        *,
        source_candidate_id: str,
        document_id: str,
        source_revision: str,
        category: str,
        trigger_span: SourceSpan,
        statement_span: SourceSpan,
        target_source_claim_ids: Iterable[str],
    ) -> ReaderExceptionPrediction:
        targets = tuple(sorted(target_source_claim_ids))
        payload: dict[str, object] = {
            "source_candidate_id": source_candidate_id,
            "document_id": document_id,
            "source_revision": source_revision,
            "category": category,
            "trigger_span": trigger_span.identity_payload(),
            "statement_span": statement_span.identity_payload(),
            "target_source_claim_ids": list(targets),
        }
        return cls(
            prediction_id=stable_reader_core_id(
                "reader-scoring-exception-prediction",
                payload,
            ),
            source_candidate_id=source_candidate_id,
            document_id=document_id,
            source_revision=source_revision,
            category=category,
            trigger_span=trigger_span,
            statement_span=statement_span,
            target_source_claim_ids=targets,
        )

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "source_candidate_id": self.source_candidate_id,
            "document_id": self.document_id,
            "source_revision": self.source_revision,
            "category": self.category,
            "trigger_span": self.trigger_span.identity_payload(),
            "statement_span": self.statement_span.identity_payload(),
            "target_source_claim_ids": list(self.target_source_claim_ids),
        }
        if include_id:
            payload["prediction_id"] = self.prediction_id
        return payload


@dataclass(frozen=True, slots=True)
class ReaderRelationPrediction:
    prediction_id: str
    source_relation_id: str
    document_id: str
    source_revision: str
    kind: RelationKind
    source_claim_id: str
    target_claim_id: str
    evidence_spans: tuple[SourceSpan, ...]

    def __post_init__(self) -> None:
        _validate_identity_fields(
            self.prediction_id,
            self.source_relation_id,
            self.document_id,
            self.source_revision,
            self.source_claim_id,
            self.target_claim_id,
        )
        if not isinstance(self.kind, RelationKind):
            raise ReaderScoringError("kind must be a RelationKind")
        if self.source_claim_id == self.target_claim_id:
            raise ReaderScoringError("relation self-loops are forbidden")
        spans = _canonical_spans(
            self.evidence_spans,
            document_id=self.document_id,
            source_revision=self.source_revision,
            field_name="relation evidence span",
        )
        object.__setattr__(self, "evidence_spans", spans)
        _verify_content_id(
            actual=self.prediction_id,
            namespace="reader-scoring-relation-prediction",
            payload=self.identity_payload(include_id=False),
            field_name="prediction_id",
        )

    @classmethod
    def from_candidate(
        cls,
        candidate: CrossSectionRelationCandidate,
    ) -> ReaderRelationPrediction:
        if not isinstance(candidate, CrossSectionRelationCandidate):
            raise ReaderScoringError(
                "candidate must be a CrossSectionRelationCandidate"
            )
        if candidate.validation_state is RelationValidationState.REJECTED:
            raise ReaderScoringError(
                "rejected relation candidates are not predictions"
            )
        return cls.create(
            source_relation_id=candidate.relation_id,
            document_id=candidate.source.document_id,
            source_revision=candidate.source.source_revision,
            kind=candidate.kind,
            source_claim_id=candidate.source.claim_id,
            target_claim_id=candidate.target.claim_id,
            evidence_spans=candidate.evidence_spans,
        )

    @classmethod
    def create(
        cls,
        *,
        source_relation_id: str,
        document_id: str,
        source_revision: str,
        kind: RelationKind,
        source_claim_id: str,
        target_claim_id: str,
        evidence_spans: Iterable[SourceSpan],
    ) -> ReaderRelationPrediction:
        spans = _sorted_spans(evidence_spans)
        payload: dict[str, object] = {
            "source_relation_id": source_relation_id,
            "document_id": document_id,
            "source_revision": source_revision,
            "kind": kind.value,
            "source_claim_id": source_claim_id,
            "target_claim_id": target_claim_id,
            "evidence_spans": [span.identity_payload() for span in spans],
        }
        return cls(
            prediction_id=stable_reader_core_id(
                "reader-scoring-relation-prediction",
                payload,
            ),
            source_relation_id=source_relation_id,
            document_id=document_id,
            source_revision=source_revision,
            kind=kind,
            source_claim_id=source_claim_id,
            target_claim_id=target_claim_id,
            evidence_spans=spans,
        )

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "source_relation_id": self.source_relation_id,
            "document_id": self.document_id,
            "source_revision": self.source_revision,
            "kind": self.kind.value,
            "source_claim_id": self.source_claim_id,
            "target_claim_id": self.target_claim_id,
            "evidence_spans": [span.identity_payload() for span in self.evidence_spans],
        }
        if include_id:
            payload["prediction_id"] = self.prediction_id
        return payload


@dataclass(frozen=True, slots=True)
class ReaderQualifierPrediction:
    prediction_id: str
    document_id: str
    source_revision: str
    kind: QualifierKind
    target_claim_id: str
    source_span: SourceSpan

    def __post_init__(self) -> None:
        _validate_identity_fields(
            self.prediction_id,
            self.document_id,
            self.source_revision,
            self.target_claim_id,
        )
        if not isinstance(self.kind, QualifierKind):
            raise ReaderScoringError("kind must be a QualifierKind")
        _validate_span(
            self.source_span,
            document_id=self.document_id,
            source_revision=self.source_revision,
            field_name="qualifier source span",
        )
        _verify_content_id(
            actual=self.prediction_id,
            namespace="reader-scoring-qualifier-prediction",
            payload=self.identity_payload(include_id=False),
            field_name="prediction_id",
        )

    @classmethod
    def create(
        cls,
        *,
        document_id: str,
        source_revision: str,
        kind: QualifierKind,
        target_claim_id: str,
        source_span: SourceSpan,
    ) -> ReaderQualifierPrediction:
        payload: dict[str, object] = {
            "document_id": document_id,
            "source_revision": source_revision,
            "kind": kind.value,
            "target_claim_id": target_claim_id,
            "source_span": source_span.identity_payload(),
        }
        return cls(
            prediction_id=stable_reader_core_id(
                "reader-scoring-qualifier-prediction",
                payload,
            ),
            document_id=document_id,
            source_revision=source_revision,
            kind=kind,
            target_claim_id=target_claim_id,
            source_span=source_span,
        )

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "document_id": self.document_id,
            "source_revision": self.source_revision,
            "kind": self.kind.value,
            "target_claim_id": self.target_claim_id,
            "source_span": self.source_span.identity_payload(),
        }
        if include_id:
            payload["prediction_id"] = self.prediction_id
        return payload


@dataclass(frozen=True, slots=True)
class ReaderSynthesisPrediction:
    synthesis_claim_id: str
    supporting_source_claim_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_text(self.synthesis_claim_id, "synthesis_claim_id")
        supports = _unique_sorted_text(
            self.supporting_source_claim_ids,
            "supporting_source_claim_id",
        )
        if not supports:
            raise ReaderScoringError(
                "synthesis predictions require supporting source claims"
            )
        object.__setattr__(self, "supporting_source_claim_ids", supports)


@dataclass(frozen=True, slots=True)
class ReaderDocumentPrediction:
    document_descriptor_id: str
    document_id: str
    source_revision: str
    claims: tuple[ReaderClaimPrediction, ...]
    exceptions: tuple[ReaderExceptionPrediction, ...] = ()
    relations: tuple[ReaderRelationPrediction, ...] = ()
    qualifiers: tuple[ReaderQualifierPrediction, ...] = ()
    synthesis_claims: tuple[ReaderSynthesisPrediction, ...] = ()
    artifact_ids: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    schema_version: str = READER_SCORING_SCHEMA_VERSION
    prediction_id: str = ""

    def __post_init__(self) -> None:
        _validate_identity_fields(
            self.document_descriptor_id,
            self.document_id,
            self.source_revision,
        )
        if self.schema_version != READER_SCORING_SCHEMA_VERSION:
            raise ReaderScoringError("unsupported deterministic scoring schema")
        claims = _canonical_predictions(
            self.claims,
            ReaderClaimPrediction,
            "claims",
        )
        if not claims:
            raise ReaderScoringError(
                "document predictions require at least one claim"
            )
        exceptions = _canonical_predictions(
            self.exceptions,
            ReaderExceptionPrediction,
            "exceptions",
        )
        relations = _canonical_predictions(
            self.relations,
            ReaderRelationPrediction,
            "relations",
        )
        qualifiers = _canonical_predictions(
            self.qualifiers,
            ReaderQualifierPrediction,
            "qualifiers",
        )
        synthesis = tuple(self.synthesis_claims)
        if any(not isinstance(item, ReaderSynthesisPrediction) for item in synthesis):
            raise ReaderScoringError(
                "synthesis_claims contain invalid values"
            )
        ordered_synthesis = tuple(
            sorted(synthesis, key=lambda item: item.synthesis_claim_id)
        )
        if synthesis != ordered_synthesis:
            raise ReaderScoringError(
                "synthesis_claims must use canonical ordering"
            )
        if len({item.synthesis_claim_id for item in synthesis}) != len(synthesis):
            raise ReaderScoringError("synthesis claim IDs must be unique")
        artifacts = _unique_sorted_text(self.artifact_ids, "artifact_id")
        warnings = _unique_sorted_text(self.warnings, "warning")
        all_predictions: tuple[
            ReaderClaimPrediction
            | ReaderExceptionPrediction
            | ReaderRelationPrediction
            | ReaderQualifierPrediction,
            ...,
        ] = (*claims, *exceptions, *relations, *qualifiers)
        for prediction in all_predictions:
            if (
                prediction.document_id != self.document_id
                or prediction.source_revision != self.source_revision
            ):
                raise ReaderScoringError(
                    "every prediction must match document identity"
                )
        claim_ids = {claim.source_claim_id for claim in claims}
        if len(claim_ids) != len(claims):
            raise ReaderScoringError("source claim IDs must be unique")
        for exception_prediction in exceptions:
            if not set(exception_prediction.target_source_claim_ids).issubset(
                claim_ids
            ):
                raise ReaderScoringError(
                    "exception targets must reference predicted claims"
                )
        for relation_prediction in relations:
            if (
                relation_prediction.source_claim_id not in claim_ids
                or relation_prediction.target_claim_id not in claim_ids
            ):
                raise ReaderScoringError(
                    "relation endpoints must reference predicted claims"
                )
        for qualifier_prediction in qualifiers:
            if qualifier_prediction.target_claim_id not in claim_ids:
                raise ReaderScoringError(
                    "qualifier targets must reference predicted claims"
                )
        for synthesis_prediction in synthesis:
            if not set(
                synthesis_prediction.supporting_source_claim_ids
            ).issubset(claim_ids):
                raise ReaderScoringError(
                    "synthesis support must reference predicted claims"
                )
        object.__setattr__(self, "claims", claims)
        object.__setattr__(self, "exceptions", exceptions)
        object.__setattr__(self, "relations", relations)
        object.__setattr__(self, "qualifiers", qualifiers)
        object.__setattr__(self, "synthesis_claims", synthesis)
        object.__setattr__(self, "artifact_ids", artifacts)
        object.__setattr__(self, "warnings", warnings)
        expected = stable_reader_core_id(
            "reader-document-scoring-prediction",
            self.identity_payload(include_id=False),
        )
        if self.prediction_id:
            if self.prediction_id != expected:
                raise ReaderScoringError(
                    "prediction_id does not match document prediction content"
                )
        else:
            object.__setattr__(self, "prediction_id", expected)

    @classmethod
    def from_artifacts(
        cls,
        *,
        document_descriptor_id: str,
        cards: Iterable[SectionCard],
        exception_candidates: Iterable[CriticalExceptionCandidate] = (),
        relation_set: CrossSectionRelationSet | None = None,
        qualifiers: Iterable[ReaderQualifierPrediction] = (),
        synthesis: GlobalDocumentSynthesis | None = None,
        warnings: Iterable[str] = (),
    ) -> ReaderDocumentPrediction:
        cards_tuple = tuple(cards)
        if not cards_tuple or any(
            not isinstance(card, SectionCard) for card in cards_tuple
        ):
            raise ReaderScoringError(
                "cards require at least one SectionCard"
            )
        ordered_cards = tuple(sorted(cards_tuple, key=lambda card: card.card_id))
        identity = (
            ordered_cards[0].document_id,
            ordered_cards[0].source_revision,
            ordered_cards[0].structure_map_id,
            ordered_cards[0].plan_id,
        )
        for card in ordered_cards[1:]:
            if (
                card.document_id,
                card.source_revision,
                card.structure_map_id,
                card.plan_id,
            ) != identity:
                raise ReaderScoringError(
                    "all cards must share document, revision, structure map, and plan"
                )
        document_id, source_revision, structure_map_id, plan_id = identity
        claims_by_id: dict[str, ReaderClaimPrediction] = {}
        for card in ordered_cards:
            for card_claim in card.claims:
                claim = card_claim.claim
                normalized = ReaderClaimPrediction.create(
                    source_claim_id=claim.claim_id,
                    document_id=document_id,
                    source_revision=source_revision,
                    modality=claim.modality,
                    source_spans=claim.source_spans,
                    qualifier_codes=claim.qualifiers,
                    applicability_codes=claim.applicability_conditions,
                )
                previous = claims_by_id.get(claim.claim_id)
                if previous is not None and previous != normalized:
                    raise ReaderScoringError(
                        "duplicate source claim ID has inconsistent content"
                    )
                claims_by_id[claim.claim_id] = normalized

        exception_predictions: list[ReaderExceptionPrediction] = []
        for exception_candidate in exception_candidates:
            if (
                exception_candidate.validation_status
                is ExceptionValidationStatus.REJECTED
            ):
                continue
            if (
                exception_candidate.document_id != document_id
                or exception_candidate.source_revision != source_revision
            ):
                raise ReaderScoringError(
                    "exception candidates must match document identity"
                )
            exception_predictions.append(
                ReaderExceptionPrediction.from_candidate(exception_candidate)
            )

        relation_predictions: list[ReaderRelationPrediction] = []
        artifact_ids = [card.card_id for card in ordered_cards]
        if relation_set is not None:
            if not isinstance(relation_set, CrossSectionRelationSet):
                raise ReaderScoringError(
                    "relation_set must be a CrossSectionRelationSet"
                )
            if (
                relation_set.document_id != document_id
                or relation_set.source_revision != source_revision
                or relation_set.structure_map_id != structure_map_id
                or relation_set.plan_id != plan_id
            ):
                raise ReaderScoringError(
                    "relation_set must match card identity"
                )
            for relation_candidate in relation_set.candidates:
                if (
                    relation_candidate.validation_state
                    is RelationValidationState.REJECTED
                ):
                    continue
                relation_predictions.append(
                    ReaderRelationPrediction.from_candidate(relation_candidate)
                )
            artifact_ids.append(relation_set.relation_set_id)

        synthesis_predictions: tuple[ReaderSynthesisPrediction, ...] = ()
        if synthesis is not None:
            if not isinstance(synthesis, GlobalDocumentSynthesis):
                raise ReaderScoringError(
                    "synthesis must be a GlobalDocumentSynthesis"
                )
            if (
                synthesis.document_id != document_id
                or synthesis.source_revision != source_revision
                or synthesis.structure_map_id != structure_map_id
                or synthesis.plan_id != plan_id
            ):
                raise ReaderScoringError(
                    "synthesis must match card identity"
                )
            synthesis_predictions = tuple(
                sorted(
                    (
                        ReaderSynthesisPrediction(
                            synthesis_claim_id=synthesis_claim.synthesis_claim_id,
                            supporting_source_claim_ids=(
                                synthesis_claim.supporting_claim_ids
                            ),
                        )
                        for synthesis_claim in synthesis.claims
                    ),
                    key=lambda synthesis_prediction: (
                        synthesis_prediction.synthesis_claim_id
                    ),
                )
            )
            artifact_ids.append(synthesis.synthesis_id)
        artifact_ids.extend(
            exception_prediction.source_candidate_id
            for exception_prediction in exception_predictions
        )
        qualifier_predictions = tuple(qualifiers)
        return cls(
            document_descriptor_id=document_descriptor_id,
            document_id=document_id,
            source_revision=source_revision,
            claims=tuple(
                sorted(
                    claims_by_id.values(),
                    key=lambda claim_prediction: claim_prediction.prediction_id,
                )
            ),
            exceptions=tuple(
                sorted(
                    exception_predictions,
                    key=lambda exception_prediction: (
                        exception_prediction.prediction_id
                    ),
                )
            ),
            relations=tuple(
                sorted(
                    relation_predictions,
                    key=lambda relation_prediction: (
                        relation_prediction.prediction_id
                    ),
                )
            ),
            qualifiers=tuple(
                sorted(
                    qualifier_predictions,
                    key=lambda qualifier_prediction: (
                        qualifier_prediction.prediction_id
                    ),
                )
            ),
            synthesis_claims=synthesis_predictions,
            artifact_ids=tuple(sorted(set(artifact_ids))),
            warnings=tuple(sorted(warnings)),
        )

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema_version": self.schema_version,
            "document_descriptor_id": self.document_descriptor_id,
            "document_id": self.document_id,
            "source_revision": self.source_revision,
            "claim_prediction_ids": [item.prediction_id for item in self.claims],
            "exception_prediction_ids": [
                item.prediction_id for item in self.exceptions
            ],
            "relation_prediction_ids": [
                item.prediction_id for item in self.relations
            ],
            "qualifier_prediction_ids": [
                item.prediction_id for item in self.qualifiers
            ],
            "synthesis_claims": [
                {
                    "synthesis_claim_id": item.synthesis_claim_id,
                    "supporting_source_claim_ids": list(
                        item.supporting_source_claim_ids
                    ),
                }
                for item in self.synthesis_claims
            ],
            "artifact_ids": list(self.artifact_ids),
            "warnings": list(self.warnings),
        }
        if include_id:
            payload["prediction_id"] = self.prediction_id
        return payload

    @property
    def replay_artifact_ids(self) -> tuple[str, ...]:
        return (self.prediction_id, *self.artifact_ids)


@dataclass(frozen=True, slots=True)
class ReaderExecutionMeasurement:
    section_latencies_ms: tuple[int, ...]
    session_wall_time_ms: int
    model_tokens: int
    projection_bytes: int
    rebuild_time_ms: int
    query_path_latency_delta_ms: int
    resume_reused_units: int
    resume_eligible_units: int
    truth_gate_bypass_count: int = 0
    query_path_write_count: int = 0
    direct_canon_write_count: int = 0
    untrusted_instruction_execution_count: int = 0
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        latencies = tuple(self.section_latencies_ms)
        for value in latencies:
            _nonnegative_int(value, "section_latency_ms")
        for name in (
            "session_wall_time_ms",
            "model_tokens",
            "projection_bytes",
            "rebuild_time_ms",
            "resume_reused_units",
            "resume_eligible_units",
            "truth_gate_bypass_count",
            "query_path_write_count",
            "direct_canon_write_count",
            "untrusted_instruction_execution_count",
        ):
            _nonnegative_int(getattr(self, name), name)
        if (
            isinstance(self.query_path_latency_delta_ms, bool)
            or not isinstance(self.query_path_latency_delta_ms, int)
        ):
            raise ReaderScoringError(
                "query_path_latency_delta_ms must be an integer"
            )
        warnings = _unique_sorted_text(self.warnings, "warning")
        object.__setattr__(self, "section_latencies_ms", latencies)
        object.__setattr__(self, "warnings", warnings)


class DeterministicReaderGoldScorer:
    """Score one prediction and one replay against one adjudicated gold set."""

    policy_version = "exact-source-linked-v1"

    def score(
        self,
        *,
        gold: HumanLabelSet,
        first: ReaderDocumentPrediction,
        replay: ReaderDocumentPrediction,
        measurement: ReaderExecutionMeasurement,
    ) -> ReaderBenchmarkObservation:
        if not isinstance(gold, HumanLabelSet):
            raise ReaderScoringError("gold must be a HumanLabelSet")
        if gold.role is not LabelSetRole.ADJUDICATED:
            raise ReaderScoringError(
                "gold label set must have adjudicated role"
            )
        if not isinstance(first, ReaderDocumentPrediction):
            raise ReaderScoringError(
                "first must be a ReaderDocumentPrediction"
            )
        if not isinstance(replay, ReaderDocumentPrediction):
            raise ReaderScoringError(
                "replay must be a ReaderDocumentPrediction"
            )
        if not isinstance(measurement, ReaderExecutionMeasurement):
            raise ReaderScoringError(
                "measurement must be a ReaderExecutionMeasurement"
            )
        self._validate_identity(gold, first)
        self._validate_identity(gold, replay)

        claim_mapping = _match_claims(first.claims, gold.claims)
        predicted_spans = tuple(
            span for claim in first.claims for span in claim.source_spans
        )
        gold_spans = tuple(
            span for claim in gold.claims for span in claim.source_spans
        )
        correct_source_span_count = _multiset_match_count(
            tuple(_span_key(span) for span in predicted_spans),
            tuple(_span_key(span) for span in gold_spans),
        )

        predicted_exception_keys_list: list[ExceptionKey] = []
        for exception_prediction in first.exceptions:
            exception_key = _predicted_exception_key(
                exception_prediction,
                claim_mapping,
            )
            if exception_key is not None:
                predicted_exception_keys_list.append(exception_key)
        predicted_exception_keys = tuple(predicted_exception_keys_list)
        matched_exception_count = _multiset_match_count(
            predicted_exception_keys,
            tuple(_gold_exception_key(label) for label in gold.exceptions),
        )

        predicted_relation_keys_list: list[RelationKey] = []
        for relation_prediction in first.relations:
            relation_key = _predicted_relation_key(
                relation_prediction,
                claim_mapping,
            )
            if relation_key is not None:
                predicted_relation_keys_list.append(relation_key)
        predicted_relation_keys = tuple(predicted_relation_keys_list)
        matched_relation_keys = _matched_items(
            predicted_relation_keys,
            tuple(_gold_relation_key(label) for label in gold.relations),
        )
        matched_relation_count = len(matched_relation_keys)
        matched_contradiction_count = sum(
            relation_key[0] == RelationKind.CONTRADICTS.value
            for relation_key in matched_relation_keys
        )

        predicted_qualifier_keys_list: list[QualifierKey] = []
        for qualifier_prediction in first.qualifiers:
            qualifier_key = _predicted_qualifier_key(
                qualifier_prediction,
                claim_mapping,
            )
            if qualifier_key is not None:
                predicted_qualifier_keys_list.append(qualifier_key)
        predicted_qualifier_keys = tuple(predicted_qualifier_keys_list)
        connected_qualifier_count = _multiset_match_count(
            predicted_qualifier_keys,
            tuple(_gold_qualifier_key(label) for label in gold.qualifiers),
        )

        synthesis_support_ids = {
            claim_id
            for synthesis_prediction in first.synthesis_claims
            for claim_id in synthesis_prediction.supporting_source_claim_ids
        }
        orphan_source_claim_count = sum(
            claim_prediction.source_claim_id not in synthesis_support_ids
            for claim_prediction in first.claims
        )
        unsupported_synthesis_claim_count = sum(
            not any(
                claim_id in claim_mapping
                for claim_id in synthesis_prediction.supporting_source_claim_ids
            )
            for synthesis_prediction in first.synthesis_claims
        )
        warnings = tuple(
            sorted(
                {
                    *first.warnings,
                    *replay.warnings,
                    *measurement.warnings,
                    f"scoring_policy:{self.policy_version}",
                }
            )
        )
        return ReaderBenchmarkObservation(
            case_id=gold.document_id,
            predicted_claim_count=len(first.claims),
            matched_claim_count=len(claim_mapping),
            predicted_source_span_count=len(predicted_spans),
            correct_source_span_count=correct_source_span_count,
            predicted_exception_count=len(first.exceptions),
            matched_exception_count=matched_exception_count,
            predicted_relation_count=len(first.relations),
            matched_relation_count=matched_relation_count,
            false_relation_count=len(first.relations) - matched_relation_count,
            matched_contradiction_count=matched_contradiction_count,
            connected_qualifier_count=connected_qualifier_count,
            source_claim_count=len(first.claims),
            orphan_source_claim_count=orphan_source_claim_count,
            synthesis_claim_count=len(first.synthesis_claims),
            unsupported_synthesis_claim_count=(
                unsupported_synthesis_claim_count
            ),
            first_artifact_ids=first.replay_artifact_ids,
            second_artifact_ids=replay.replay_artifact_ids,
            section_latencies_ms=measurement.section_latencies_ms,
            session_wall_time_ms=measurement.session_wall_time_ms,
            model_tokens=measurement.model_tokens,
            projection_bytes=measurement.projection_bytes,
            rebuild_time_ms=measurement.rebuild_time_ms,
            query_path_latency_delta_ms=(
                measurement.query_path_latency_delta_ms
            ),
            resume_reused_units=measurement.resume_reused_units,
            resume_eligible_units=measurement.resume_eligible_units,
            truth_gate_bypass_count=measurement.truth_gate_bypass_count,
            query_path_write_count=measurement.query_path_write_count,
            direct_canon_write_count=measurement.direct_canon_write_count,
            untrusted_instruction_execution_count=(
                measurement.untrusted_instruction_execution_count
            ),
            warnings=warnings,
        )

    @staticmethod
    def _validate_identity(
        gold: HumanLabelSet,
        prediction: ReaderDocumentPrediction,
    ) -> None:
        if prediction.document_descriptor_id != gold.document_descriptor_id:
            raise ReaderScoringError(
                "prediction descriptor must match gold label set"
            )
        if prediction.document_id != gold.document_id:
            raise ReaderScoringError(
                "prediction document_id must match gold label set"
            )
        if prediction.source_revision != gold.source_revision:
            raise ReaderScoringError(
                "prediction source_revision must match gold label set"
            )


def _match_claims(
    predictions: tuple[ReaderClaimPrediction, ...],
    gold_labels: tuple[HumanClaimLabel, ...],
) -> dict[str, str]:
    predicted_by_key: dict[ClaimKey, list[ReaderClaimPrediction]] = defaultdict(list)
    gold_by_key: dict[ClaimKey, list[HumanClaimLabel]] = defaultdict(list)
    for claim_prediction in predictions:
        predicted_by_key[claim_prediction.matching_key].append(claim_prediction)
    for gold_claim in gold_labels:
        gold_by_key[_gold_claim_key(gold_claim)].append(gold_claim)
    mapping: dict[str, str] = {}
    common_keys = sorted(set(predicted_by_key) & set(gold_by_key), key=repr)
    for claim_key in common_keys:
        predicted_items = sorted(
            predicted_by_key[claim_key],
            key=lambda claim_prediction: claim_prediction.source_claim_id,
        )
        gold_items = sorted(
            gold_by_key[claim_key],
            key=lambda gold_claim: gold_claim.label_id,
        )
        for claim_prediction, gold_claim in zip(
            predicted_items,
            gold_items,
            strict=False,
        ):
            mapping[claim_prediction.source_claim_id] = gold_claim.label_id
    return mapping


def _gold_claim_key(label: HumanClaimLabel) -> ClaimKey:
    return (
        label.modality.value,
        tuple(_span_key(span) for span in label.source_spans),
        label.qualifier_codes,
        label.applicability_codes,
    )


def _predicted_exception_key(
    prediction: ReaderExceptionPrediction,
    claim_mapping: dict[str, str],
) -> ExceptionKey | None:
    mapped_targets: list[str] = []
    for claim_id in prediction.target_source_claim_ids:
        target = claim_mapping.get(claim_id)
        if target is None:
            return None
        mapped_targets.append(target)
    return (
        prediction.category,
        _span_key(prediction.trigger_span),
        _span_key(prediction.statement_span),
        tuple(sorted(mapped_targets)),
    )


def _gold_exception_key(label: HumanExceptionLabel) -> ExceptionKey:
    return (
        label.category.value,
        _span_key(label.trigger_span),
        _span_key(label.statement_span),
        label.target_claim_label_ids,
    )


def _predicted_relation_key(
    prediction: ReaderRelationPrediction,
    claim_mapping: dict[str, str],
) -> RelationKey | None:
    source = claim_mapping.get(prediction.source_claim_id)
    target = claim_mapping.get(prediction.target_claim_id)
    if source is None or target is None:
        return None
    return (
        prediction.kind.value,
        source,
        target,
        tuple(_span_key(span) for span in prediction.evidence_spans),
    )


def _gold_relation_key(label: HumanRelationLabel) -> RelationKey:
    return (
        label.relation_kind.value,
        label.source_claim_label_id,
        label.target_claim_label_id,
        tuple(_span_key(span) for span in label.evidence_spans),
    )


def _predicted_qualifier_key(
    prediction: ReaderQualifierPrediction,
    claim_mapping: dict[str, str],
) -> QualifierKey | None:
    target = claim_mapping.get(prediction.target_claim_id)
    if target is None:
        return None
    return (
        prediction.kind.value,
        target,
        _span_key(prediction.source_span),
    )


def _gold_qualifier_key(label: HumanQualifierLabel) -> QualifierKey:
    return (
        label.qualifier_kind.value,
        label.target_claim_label_id,
        _span_key(label.source_span),
    )


def _multiset_match_count(
    predictions: tuple[MatchT, ...],
    gold: tuple[MatchT, ...],
) -> int:
    return len(_matched_items(predictions, gold))


def _matched_items(
    predictions: tuple[MatchT, ...],
    gold: tuple[MatchT, ...],
) -> tuple[MatchT, ...]:
    remaining: dict[MatchT, int] = defaultdict(int)
    for gold_item in gold:
        remaining[gold_item] += 1
    matched: list[MatchT] = []
    for predicted_item in predictions:
        if remaining[predicted_item] > 0:
            remaining[predicted_item] -= 1
            matched.append(predicted_item)
    return tuple(matched)


def _span_key(span: SourceSpan) -> SpanKey:
    return (
        span.document_id,
        span.source_revision,
        span.start_offset,
        span.end_offset,
        span.content_hash,
    )


def _validate_span(
    span: SourceSpan,
    *,
    document_id: str,
    source_revision: str,
    field_name: str,
) -> None:
    if not isinstance(span, SourceSpan):
        raise ReaderScoringError(f"{field_name} must be a SourceSpan")
    if span.document_id != document_id:
        raise ReaderScoringError(f"{field_name} document_id mismatch")
    if span.source_revision != source_revision:
        raise ReaderScoringError(f"{field_name} source_revision mismatch")


def _sorted_spans(values: Iterable[SourceSpan]) -> tuple[SourceSpan, ...]:
    return tuple(
        sorted(
            values,
            key=lambda span: (
                span.start_offset,
                span.end_offset,
                span.content_hash,
                span.span_id,
            ),
        )
    )


def _canonical_spans(
    values: Iterable[SourceSpan],
    *,
    document_id: str,
    source_revision: str,
    field_name: str,
) -> tuple[SourceSpan, ...]:
    spans = tuple(values)
    if not spans:
        raise ReaderScoringError(f"{field_name} values must not be empty")
    for span in spans:
        _validate_span(
            span,
            document_id=document_id,
            source_revision=source_revision,
            field_name=field_name,
        )
    if len({_span_key(span) for span in spans}) != len(spans):
        raise ReaderScoringError(f"{field_name} values must be unique")
    if spans != _sorted_spans(spans):
        raise ReaderScoringError(f"{field_name} values must be canonical")
    return spans


def _canonical_predictions(
    values: Iterable[PredictionT],
    expected_type: type[PredictionT],
    field_name: str,
) -> tuple[PredictionT, ...]:
    predictions = tuple(values)
    if any(not isinstance(item, expected_type) for item in predictions):
        raise ReaderScoringError(
            f"{field_name} contain invalid prediction types"
        )
    ordered = tuple(sorted(predictions, key=lambda item: item.prediction_id))
    if predictions != ordered:
        raise ReaderScoringError(f"{field_name} must use canonical ordering")
    if len({item.prediction_id for item in predictions}) != len(predictions):
        raise ReaderScoringError(f"{field_name} prediction IDs must be unique")
    return predictions


def _verify_content_id(
    *,
    actual: str,
    namespace: str,
    payload: dict[str, object],
    field_name: str,
) -> None:
    expected = stable_reader_core_id(namespace, payload)
    if actual != expected:
        raise ReaderScoringError(
            f"{field_name} does not match prediction content"
        )


def _validate_identity_fields(*values: str) -> None:
    for value in values:
        _require_text(value, "identity field")


def _require_text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReaderScoringError(f"{field_name} must be a non-empty string")
    return value


def _unique_sorted_text(
    values: Iterable[str],
    field_name: str,
) -> tuple[str, ...]:
    result = tuple(values)
    for value in result:
        _require_text(value, field_name)
    if len(set(result)) != len(result):
        raise ReaderScoringError(f"{field_name} values must be unique")
    ordered = tuple(sorted(result))
    if result != ordered:
        raise ReaderScoringError(f"{field_name} values must be sorted")
    return result


def _nonnegative_int(value: int, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ReaderScoringError(f"{field_name} must be an integer >= 0")
    return value


__all__ = [
    "READER_SCORING_SCHEMA_VERSION",
    "DeterministicReaderGoldScorer",
    "ReaderClaimPrediction",
    "ReaderDocumentPrediction",
    "ReaderExceptionPrediction",
    "ReaderExecutionMeasurement",
    "ReaderQualifierPrediction",
    "ReaderRelationPrediction",
    "ReaderScoringError",
    "ReaderSynthesisPrediction",
]
