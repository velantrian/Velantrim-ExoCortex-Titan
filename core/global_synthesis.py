"""Source-linked global synthesis candidates for Reader Core PR-RDR-08.

The builder validates explicit structured proposals against completed reading
artifacts. It generates no prose, calls no model, and grants no Canon, memory,
policy, graph, tool, TruthGate, or Write Gate authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from core.critical_exceptions import CriticalExceptionCandidate
from core.knowledge_capsule import SourceSpan
from core.reader_core_contracts import SessionState, stable_reader_core_id
from core.reader_coverage import CoverageMap
from core.reading_session import (
    ReadingSession,
    SessionArtifactKind,
)
from core.section_card import SectionCard, SectionCardClaim
from core.section_relations import (
    CrossSectionRelationCandidate,
    CrossSectionRelationSet,
)

GLOBAL_SYNTHESIS_SCHEMA_VERSION = "reader-core.global-synthesis.v1"


class GlobalSynthesisError(ValueError):
    """Raised when synthesis inputs or provenance invariants are invalid."""


class SynthesisClaimKind(str, Enum):
    CENTRAL_THEME = "central_theme"
    AUTHOR_POSITION = "author_position"
    NARRATIVE_ARC = "narrative_arc"
    CONCEPT = "concept"
    DEFINITION = "definition"
    ARGUMENT_STEP = "argument_step"
    EPISODE = "episode"
    EXAMPLE = "example"
    QUOTATION = "quotation"
    LIMITATION = "limitation"
    CONTRADICTION = "contradiction"
    CONCLUSION = "conclusion"


class SynthesisValidationState(str, Enum):
    UNVALIDATED = "unvalidated"
    SUPPORTED = "supported"
    REJECTED = "rejected"
    AMBIGUOUS = "ambiguous"


@dataclass(frozen=True, slots=True)
class SynthesisClaimProposal:
    """Caller-supplied proposal; the builder only validates and materializes it."""

    proposal_key: str
    kind: SynthesisClaimKind
    text: str
    supporting_claim_ids: tuple[str, ...]
    opposing_claim_ids: tuple[str, ...] = ()
    exception_candidate_ids: tuple[str, ...] = ()
    relation_ids: tuple[str, ...] = ()
    qualifiers: tuple[str, ...] = ()
    inference_reason: str = "cross_section_synthesis"

    def __post_init__(self) -> None:
        _require_text(self.proposal_key, "proposal_key")
        if not isinstance(self.kind, SynthesisClaimKind):
            raise GlobalSynthesisError("kind must be a SynthesisClaimKind")
        _require_text(self.text, "text")
        supporting = _unique_sorted_text(
            self.supporting_claim_ids,
            "supporting_claim_id",
        )
        if not supporting:
            raise GlobalSynthesisError(
                "a synthesis claim requires at least one supporting claim"
            )
        opposing = _unique_sorted_text(
            self.opposing_claim_ids,
            "opposing_claim_id",
        )
        if set(supporting) & set(opposing):
            raise GlobalSynthesisError(
                "supporting and opposing claim IDs must be disjoint"
            )
        exceptions = _unique_sorted_text(
            self.exception_candidate_ids,
            "exception_candidate_id",
        )
        relations = _unique_sorted_text(self.relation_ids, "relation_id")
        qualifiers = _unique_text_tuple(self.qualifiers, "qualifier")
        _require_text(self.inference_reason, "inference_reason")
        object.__setattr__(self, "supporting_claim_ids", supporting)
        object.__setattr__(self, "opposing_claim_ids", opposing)
        object.__setattr__(self, "exception_candidate_ids", exceptions)
        object.__setattr__(self, "relation_ids", relations)
        object.__setattr__(self, "qualifiers", qualifiers)


@dataclass(frozen=True, slots=True)
class AlternativeInterpretationProposal:
    proposal_key: str
    text: str
    supporting_synthesis_keys: tuple[str, ...]
    source_claim_ids: tuple[str, ...]
    contrast_reason: str

    def __post_init__(self) -> None:
        _require_text(self.proposal_key, "proposal_key")
        _require_text(self.text, "text")
        synthesis_keys = _unique_sorted_text(
            self.supporting_synthesis_keys,
            "supporting_synthesis_key",
        )
        source_claims = _unique_sorted_text(
            self.source_claim_ids,
            "source_claim_id",
        )
        if not synthesis_keys or not source_claims:
            raise GlobalSynthesisError(
                "alternative interpretations require synthesis and source support"
            )
        _require_text(self.contrast_reason, "contrast_reason")
        object.__setattr__(self, "supporting_synthesis_keys", synthesis_keys)
        object.__setattr__(self, "source_claim_ids", source_claims)


@dataclass(frozen=True, slots=True)
class UnresolvedQuestionProposal:
    proposal_key: str
    question: str
    reason_code: str
    related_synthesis_keys: tuple[str, ...] = ()
    related_source_claim_ids: tuple[str, ...] = ()
    related_exception_candidate_ids: tuple[str, ...] = ()
    related_relation_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_text(self.proposal_key, "proposal_key")
        _require_text(self.question, "question")
        _require_text(self.reason_code, "reason_code")
        synthesis_keys = _unique_sorted_text(
            self.related_synthesis_keys,
            "related_synthesis_key",
        )
        source_claims = _unique_sorted_text(
            self.related_source_claim_ids,
            "related_source_claim_id",
        )
        exceptions = _unique_sorted_text(
            self.related_exception_candidate_ids,
            "related_exception_candidate_id",
        )
        relations = _unique_sorted_text(
            self.related_relation_ids,
            "related_relation_id",
        )
        if not (synthesis_keys or source_claims or exceptions or relations):
            raise GlobalSynthesisError(
                "an unresolved question requires at least one source-linked reference"
            )
        object.__setattr__(self, "related_synthesis_keys", synthesis_keys)
        object.__setattr__(self, "related_source_claim_ids", source_claims)
        object.__setattr__(
            self,
            "related_exception_candidate_ids",
            exceptions,
        )
        object.__setattr__(self, "related_relation_ids", relations)


@dataclass(frozen=True, slots=True)
class SynthesisClaim:
    proposal_key: str
    kind: SynthesisClaimKind
    text: str
    supporting_claim_ids: tuple[str, ...]
    opposing_claim_ids: tuple[str, ...]
    exception_candidate_ids: tuple[str, ...]
    relation_ids: tuple[str, ...]
    source_card_ids: tuple[str, ...]
    source_section_ids: tuple[str, ...]
    source_spans: tuple[SourceSpan, ...]
    qualifiers: tuple[str, ...]
    inference_reason: str
    validation_state: SynthesisValidationState = (
        SynthesisValidationState.UNVALIDATED
    )
    synthesis_claim_id: str = ""

    def __post_init__(self) -> None:
        _require_text(self.proposal_key, "proposal_key")
        if not isinstance(self.kind, SynthesisClaimKind):
            raise GlobalSynthesisError("kind must be a SynthesisClaimKind")
        _require_text(self.text, "text")
        supporting = _unique_sorted_text(
            self.supporting_claim_ids,
            "supporting_claim_id",
        )
        if not supporting:
            raise GlobalSynthesisError(
                "a synthesis claim requires at least one supporting claim"
            )
        opposing = _unique_sorted_text(
            self.opposing_claim_ids,
            "opposing_claim_id",
        )
        exceptions = _unique_sorted_text(
            self.exception_candidate_ids,
            "exception_candidate_id",
        )
        relations = _unique_sorted_text(self.relation_ids, "relation_id")
        cards = _unique_sorted_text(self.source_card_ids, "source_card_id")
        sections = _unique_sorted_text(
            self.source_section_ids,
            "source_section_id",
        )
        spans = _canonical_spans(self.source_spans)
        if not cards or not sections or not spans:
            raise GlobalSynthesisError(
                "synthesis claims require cards, sections, and exact source spans"
            )
        qualifiers = _unique_text_tuple(self.qualifiers, "qualifier")
        _require_text(self.inference_reason, "inference_reason")
        if not isinstance(self.validation_state, SynthesisValidationState):
            raise GlobalSynthesisError(
                "validation_state must be a SynthesisValidationState"
            )
        object.__setattr__(self, "supporting_claim_ids", supporting)
        object.__setattr__(self, "opposing_claim_ids", opposing)
        object.__setattr__(self, "exception_candidate_ids", exceptions)
        object.__setattr__(self, "relation_ids", relations)
        object.__setattr__(self, "source_card_ids", cards)
        object.__setattr__(self, "source_section_ids", sections)
        object.__setattr__(self, "source_spans", spans)
        object.__setattr__(self, "qualifiers", qualifiers)
        expected = stable_reader_core_id(
            "global-synthesis-claim",
            self.identity_payload(include_id=False),
        )
        if self.synthesis_claim_id:
            if self.synthesis_claim_id != expected:
                raise GlobalSynthesisError(
                    "synthesis_claim_id does not match claim content"
                )
        else:
            object.__setattr__(self, "synthesis_claim_id", expected)

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "proposal_key": self.proposal_key,
            "kind": self.kind.value,
            "text": self.text,
            "supporting_claim_ids": list(self.supporting_claim_ids),
            "opposing_claim_ids": list(self.opposing_claim_ids),
            "exception_candidate_ids": list(self.exception_candidate_ids),
            "relation_ids": list(self.relation_ids),
            "source_card_ids": list(self.source_card_ids),
            "source_section_ids": list(self.source_section_ids),
            "source_spans": [span.identity_payload() for span in self.source_spans],
            "qualifiers": list(self.qualifiers),
            "inference_reason": self.inference_reason,
            "validation_state": self.validation_state.value,
        }
        if include_id:
            payload["synthesis_claim_id"] = self.synthesis_claim_id
        return payload


@dataclass(frozen=True, slots=True)
class AlternativeInterpretation:
    proposal_key: str
    text: str
    supporting_synthesis_claim_ids: tuple[str, ...]
    source_claim_ids: tuple[str, ...]
    source_spans: tuple[SourceSpan, ...]
    contrast_reason: str
    validation_state: SynthesisValidationState = (
        SynthesisValidationState.UNVALIDATED
    )
    interpretation_id: str = ""

    def __post_init__(self) -> None:
        _require_text(self.proposal_key, "proposal_key")
        _require_text(self.text, "text")
        synthesis_ids = _unique_sorted_text(
            self.supporting_synthesis_claim_ids,
            "supporting_synthesis_claim_id",
        )
        source_ids = _unique_sorted_text(self.source_claim_ids, "source_claim_id")
        spans = _canonical_spans(self.source_spans)
        if not synthesis_ids or not source_ids or not spans:
            raise GlobalSynthesisError(
                "alternative interpretations require synthesis and source support"
            )
        _require_text(self.contrast_reason, "contrast_reason")
        if not isinstance(self.validation_state, SynthesisValidationState):
            raise GlobalSynthesisError(
                "validation_state must be a SynthesisValidationState"
            )
        object.__setattr__(self, "supporting_synthesis_claim_ids", synthesis_ids)
        object.__setattr__(self, "source_claim_ids", source_ids)
        object.__setattr__(self, "source_spans", spans)
        expected = stable_reader_core_id(
            "global-synthesis-alternative",
            self.identity_payload(include_id=False),
        )
        if self.interpretation_id:
            if self.interpretation_id != expected:
                raise GlobalSynthesisError(
                    "interpretation_id does not match interpretation content"
                )
        else:
            object.__setattr__(self, "interpretation_id", expected)

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "proposal_key": self.proposal_key,
            "text": self.text,
            "supporting_synthesis_claim_ids": list(
                self.supporting_synthesis_claim_ids
            ),
            "source_claim_ids": list(self.source_claim_ids),
            "source_spans": [span.identity_payload() for span in self.source_spans],
            "contrast_reason": self.contrast_reason,
            "validation_state": self.validation_state.value,
        }
        if include_id:
            payload["interpretation_id"] = self.interpretation_id
        return payload


@dataclass(frozen=True, slots=True)
class UnresolvedSynthesisQuestion:
    proposal_key: str
    question: str
    reason_code: str
    related_synthesis_claim_ids: tuple[str, ...]
    related_source_claim_ids: tuple[str, ...]
    related_exception_candidate_ids: tuple[str, ...]
    related_relation_ids: tuple[str, ...]
    source_spans: tuple[SourceSpan, ...]
    question_id: str = ""

    def __post_init__(self) -> None:
        _require_text(self.proposal_key, "proposal_key")
        _require_text(self.question, "question")
        _require_text(self.reason_code, "reason_code")
        synthesis_ids = _unique_sorted_text(
            self.related_synthesis_claim_ids,
            "related_synthesis_claim_id",
        )
        source_ids = _unique_sorted_text(
            self.related_source_claim_ids,
            "related_source_claim_id",
        )
        exceptions = _unique_sorted_text(
            self.related_exception_candidate_ids,
            "related_exception_candidate_id",
        )
        relations = _unique_sorted_text(
            self.related_relation_ids,
            "related_relation_id",
        )
        spans = _canonical_spans(self.source_spans)
        if not spans:
            raise GlobalSynthesisError(
                "unresolved questions require exact source-linked support"
            )
        object.__setattr__(self, "related_synthesis_claim_ids", synthesis_ids)
        object.__setattr__(self, "related_source_claim_ids", source_ids)
        object.__setattr__(
            self,
            "related_exception_candidate_ids",
            exceptions,
        )
        object.__setattr__(self, "related_relation_ids", relations)
        object.__setattr__(self, "source_spans", spans)
        expected = stable_reader_core_id(
            "global-synthesis-question",
            self.identity_payload(include_id=False),
        )
        if self.question_id:
            if self.question_id != expected:
                raise GlobalSynthesisError(
                    "question_id does not match question content"
                )
        else:
            object.__setattr__(self, "question_id", expected)

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "proposal_key": self.proposal_key,
            "question": self.question,
            "reason_code": self.reason_code,
            "related_synthesis_claim_ids": list(
                self.related_synthesis_claim_ids
            ),
            "related_source_claim_ids": list(self.related_source_claim_ids),
            "related_exception_candidate_ids": list(
                self.related_exception_candidate_ids
            ),
            "related_relation_ids": list(self.related_relation_ids),
            "source_spans": [span.identity_payload() for span in self.source_spans],
        }
        if include_id:
            payload["question_id"] = self.question_id
        return payload


@dataclass(frozen=True, slots=True)
class GlobalDocumentSynthesis:
    builder_version: str
    document_id: str
    source_revision: str
    structure_map_id: str
    plan_id: str
    session_id: str
    session_snapshot_id: str
    coverage_map_id: str
    relation_set_id: str
    card_ids: tuple[str, ...]
    exception_candidate_ids: tuple[str, ...]
    central_theme_claim_id: str
    claims: tuple[SynthesisClaim, ...]
    alternative_interpretations: tuple[AlternativeInterpretation, ...]
    unresolved_questions: tuple[UnresolvedSynthesisQuestion, ...]
    unsupported_source_claim_ids: tuple[str, ...]
    warnings: tuple[str, ...] = ()
    schema_version: str = GLOBAL_SYNTHESIS_SCHEMA_VERSION
    synthesis_id: str = ""

    def __post_init__(self) -> None:
        for name in (
            "builder_version",
            "document_id",
            "source_revision",
            "structure_map_id",
            "plan_id",
            "session_id",
            "session_snapshot_id",
            "coverage_map_id",
            "relation_set_id",
            "central_theme_claim_id",
        ):
            _require_text(getattr(self, name), name)
        if self.schema_version != GLOBAL_SYNTHESIS_SCHEMA_VERSION:
            raise GlobalSynthesisError(
                "unsupported GlobalDocumentSynthesis schema_version"
            )
        cards = _unique_sorted_text(self.card_ids, "card_id")
        exceptions = _unique_sorted_text(
            self.exception_candidate_ids,
            "exception_candidate_id",
        )
        claims = tuple(self.claims)
        alternatives = tuple(self.alternative_interpretations)
        questions = tuple(self.unresolved_questions)
        if not claims or any(not isinstance(item, SynthesisClaim) for item in claims):
            raise GlobalSynthesisError(
                "claims require at least one SynthesisClaim"
            )
        if any(not isinstance(item, AlternativeInterpretation) for item in alternatives):
            raise GlobalSynthesisError(
                "alternative_interpretations contain invalid values"
            )
        if any(not isinstance(item, UnresolvedSynthesisQuestion) for item in questions):
            raise GlobalSynthesisError(
                "unresolved_questions contain invalid values"
            )
        if tuple(item.proposal_key for item in claims) != tuple(
            sorted(item.proposal_key for item in claims)
        ):
            raise GlobalSynthesisError("claims must use canonical proposal-key order")
        if tuple(item.proposal_key for item in alternatives) != tuple(
            sorted(item.proposal_key for item in alternatives)
        ):
            raise GlobalSynthesisError(
                "alternative interpretations must use canonical proposal-key order"
            )
        if tuple(item.proposal_key for item in questions) != tuple(
            sorted(item.proposal_key for item in questions)
        ):
            raise GlobalSynthesisError(
                "unresolved questions must use canonical proposal-key order"
            )
        claim_ids = {item.synthesis_claim_id for item in claims}
        if len(claim_ids) != len(claims):
            raise GlobalSynthesisError("synthesis claim IDs must be unique")
        if self.central_theme_claim_id not in claim_ids:
            raise GlobalSynthesisError(
                "central_theme_claim_id must reference a synthesis claim"
            )
        central = next(
            item
            for item in claims
            if item.synthesis_claim_id == self.central_theme_claim_id
        )
        if central.kind is not SynthesisClaimKind.CENTRAL_THEME:
            raise GlobalSynthesisError(
                "central_theme_claim_id must reference CENTRAL_THEME"
            )
        unsupported = _unique_sorted_text(
            self.unsupported_source_claim_ids,
            "unsupported_source_claim_id",
        )
        warnings = _unique_text_tuple(self.warnings, "warning")
        object.__setattr__(self, "card_ids", cards)
        object.__setattr__(self, "exception_candidate_ids", exceptions)
        object.__setattr__(self, "claims", claims)
        object.__setattr__(self, "alternative_interpretations", alternatives)
        object.__setattr__(self, "unresolved_questions", questions)
        object.__setattr__(self, "unsupported_source_claim_ids", unsupported)
        object.__setattr__(self, "warnings", warnings)
        expected = stable_reader_core_id(
            "global-document-synthesis",
            self.identity_payload(include_id=False),
        )
        if self.synthesis_id:
            if self.synthesis_id != expected:
                raise GlobalSynthesisError(
                    "synthesis_id does not match synthesis content"
                )
        else:
            object.__setattr__(self, "synthesis_id", expected)

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema_version": self.schema_version,
            "builder_version": self.builder_version,
            "document_id": self.document_id,
            "source_revision": self.source_revision,
            "structure_map_id": self.structure_map_id,
            "plan_id": self.plan_id,
            "session_id": self.session_id,
            "session_snapshot_id": self.session_snapshot_id,
            "coverage_map_id": self.coverage_map_id,
            "relation_set_id": self.relation_set_id,
            "card_ids": list(self.card_ids),
            "exception_candidate_ids": list(self.exception_candidate_ids),
            "central_theme_claim_id": self.central_theme_claim_id,
            "claims": [item.identity_payload() for item in self.claims],
            "alternative_interpretations": [
                item.identity_payload() for item in self.alternative_interpretations
            ],
            "unresolved_questions": [
                item.identity_payload() for item in self.unresolved_questions
            ],
            "unsupported_source_claim_ids": list(
                self.unsupported_source_claim_ids
            ),
            "warnings": list(self.warnings),
        }
        if include_id:
            payload["synthesis_id"] = self.synthesis_id
        return payload


class GlobalDocumentSynthesisBuilder:
    """Validate explicit synthesis proposals against completed source artifacts."""

    builder_version = "1.0.0"

    def build(
        self,
        session: ReadingSession,
        coverage_map: CoverageMap,
        relation_set: CrossSectionRelationSet,
        *,
        cards: Iterable[SectionCard],
        exception_candidates: Iterable[CriticalExceptionCandidate],
        claim_proposals: Iterable[SynthesisClaimProposal],
        central_theme_proposal_key: str,
        alternative_proposals: Iterable[AlternativeInterpretationProposal] = (),
        unresolved_question_proposals: Iterable[UnresolvedQuestionProposal] = (),
    ) -> GlobalDocumentSynthesis:
        self._validate_session_artifacts(session, coverage_map, relation_set)
        card_tuple = tuple(cards)
        exception_tuple = tuple(exception_candidates)
        card_by_id, source_claims, claim_cards = self._validate_cards(
            session,
            coverage_map,
            relation_set,
            card_tuple,
        )
        exception_by_id = self._validate_exceptions(
            coverage_map,
            exception_tuple,
            source_claims,
        )
        relation_by_id = {
            candidate.relation_id: candidate
            for candidate in relation_set.candidates
        }
        proposals = tuple(claim_proposals)
        if not proposals:
            raise GlobalSynthesisError("claim_proposals must not be empty")
        if len({item.proposal_key for item in proposals}) != len(proposals):
            raise GlobalSynthesisError("claim proposal keys must be unique")
        ordered_proposals = tuple(sorted(proposals, key=lambda item: item.proposal_key))
        claims = tuple(
            self._build_claim(
                proposal,
                source_claims=source_claims,
                claim_cards=claim_cards,
                exceptions=exception_by_id,
                relations=relation_by_id,
            )
            for proposal in ordered_proposals
        )
        claims_by_key = {item.proposal_key: item for item in claims}
        _require_text(central_theme_proposal_key, "central_theme_proposal_key")
        central = claims_by_key.get(central_theme_proposal_key)
        if central is None:
            raise GlobalSynthesisError(
                "central theme proposal key must reference a synthesis claim"
            )
        if central.kind is not SynthesisClaimKind.CENTRAL_THEME:
            raise GlobalSynthesisError(
                "central theme proposal must use CENTRAL_THEME kind"
            )

        alternatives = tuple(
            self._build_alternative(
                proposal,
                claims_by_key=claims_by_key,
                source_claims=source_claims,
            )
            for proposal in sorted(
                tuple(alternative_proposals),
                key=lambda item: item.proposal_key,
            )
        )
        if len({item.proposal_key for item in alternatives}) != len(alternatives):
            raise GlobalSynthesisError(
                "alternative interpretation proposal keys must be unique"
            )
        questions = tuple(
            self._build_question(
                proposal,
                claims_by_key=claims_by_key,
                source_claims=source_claims,
                exceptions=exception_by_id,
                relations=relation_by_id,
            )
            for proposal in sorted(
                tuple(unresolved_question_proposals),
                key=lambda item: item.proposal_key,
            )
        )
        if len({item.proposal_key for item in questions}) != len(questions):
            raise GlobalSynthesisError(
                "unresolved question proposal keys must be unique"
            )

        represented_source_claims: set[str] = set()
        for claim in claims:
            represented_source_claims.update(claim.supporting_claim_ids)
            represented_source_claims.update(claim.opposing_claim_ids)
        for alternative in alternatives:
            represented_source_claims.update(alternative.source_claim_ids)
        for question in questions:
            represented_source_claims.update(question.related_source_claim_ids)
        unsupported = tuple(sorted(set(source_claims) - represented_source_claims))
        warnings: list[str] = []
        if unsupported:
            warnings.append("source_claims_not_represented_in_synthesis")
        if coverage_map.unresolved_regions:
            warnings.append("coverage_contains_unresolved_regions")
        if coverage_map.unsupported_assets:
            warnings.append("coverage_contains_unsupported_assets")
        if alternatives:
            warnings.append("alternative_interpretations_present")
        if questions:
            warnings.append("unresolved_synthesis_questions_present")
        return GlobalDocumentSynthesis(
            builder_version=self.builder_version,
            document_id=session.document_id,
            source_revision=session.source_revision,
            structure_map_id=session.structure_map_id,
            plan_id=session.plan_id,
            session_id=session.session_id,
            session_snapshot_id=session.snapshot_id,
            coverage_map_id=coverage_map.coverage_map_id,
            relation_set_id=relation_set.relation_set_id,
            card_ids=tuple(sorted(card_by_id)),
            exception_candidate_ids=tuple(sorted(exception_by_id)),
            central_theme_claim_id=central.synthesis_claim_id,
            claims=claims,
            alternative_interpretations=alternatives,
            unresolved_questions=questions,
            unsupported_source_claim_ids=unsupported,
            warnings=tuple(warnings),
        )

    @staticmethod
    def _validate_session_artifacts(
        session: ReadingSession,
        coverage_map: CoverageMap,
        relation_set: CrossSectionRelationSet,
    ) -> None:
        if not isinstance(session, ReadingSession):
            raise GlobalSynthesisError("session must be a ReadingSession")
        if session.state is not SessionState.COMPLETED:
            raise GlobalSynthesisError(
                "global synthesis requires a COMPLETED ReadingSession"
            )
        if any(
            item.kind is SessionArtifactKind.REUSED_CARD
            for item in session.unit_artifacts
        ):
            raise GlobalSynthesisError(
                "reused cards require provenance rebasing before synthesis"
            )
        if not isinstance(coverage_map, CoverageMap):
            raise GlobalSynthesisError("coverage_map must be a CoverageMap")
        if not isinstance(relation_set, CrossSectionRelationSet):
            raise GlobalSynthesisError(
                "relation_set must be a CrossSectionRelationSet"
            )
        identity = (
            session.document_id,
            session.source_revision,
            session.structure_map_id,
            session.plan_id,
        )
        if identity != (
            coverage_map.document_id,
            coverage_map.source_revision,
            coverage_map.structure_map_id,
            coverage_map.plan_id,
        ):
            raise GlobalSynthesisError("CoverageMap identity must match session")
        if identity != (
            relation_set.document_id,
            relation_set.source_revision,
            relation_set.structure_map_id,
            relation_set.plan_id,
        ):
            raise GlobalSynthesisError("relation set identity must match session")
        if session.coverage_map_id != coverage_map.coverage_map_id:
            raise GlobalSynthesisError("session CoverageMap reference mismatch")
        if session.relation_set_id != relation_set.relation_set_id:
            raise GlobalSynthesisError("session relation-set reference mismatch")

    @staticmethod
    def _validate_cards(
        session: ReadingSession,
        coverage_map: CoverageMap,
        relation_set: CrossSectionRelationSet,
        cards: tuple[SectionCard, ...],
    ) -> tuple[
        dict[str, SectionCard],
        dict[str, SectionCardClaim],
        dict[str, SectionCard],
    ]:
        if not cards or any(not isinstance(card, SectionCard) for card in cards):
            raise GlobalSynthesisError("cards require SectionCard values")
        card_by_id = {card.card_id: card for card in cards}
        if len(card_by_id) != len(cards):
            raise GlobalSynthesisError("card IDs must be unique")
        expected_artifacts = tuple(item.artifact_id for item in session.unit_artifacts)
        if set(card_by_id) != set(expected_artifacts):
            raise GlobalSynthesisError(
                "cards must exactly match completed session artifacts"
            )
        if set(card_by_id) != set(coverage_map.card_ids):
            raise GlobalSynthesisError("cards must exactly match CoverageMap card IDs")
        source_claims: dict[str, SectionCardClaim] = {}
        claim_cards: dict[str, SectionCard] = {}
        for card in cards:
            if (
                card.document_id != session.document_id
                or card.source_revision != session.source_revision
                or card.structure_map_id != session.structure_map_id
                or card.plan_id != session.plan_id
            ):
                raise GlobalSynthesisError("card identity must match session")
            for card_claim in card.claims:
                claim_id = card_claim.claim.claim_id
                if claim_id in source_claims:
                    raise GlobalSynthesisError("source claim IDs must be unique")
                source_claims[claim_id] = card_claim
                claim_cards[claim_id] = card
        if set(source_claims) != set(relation_set.known_claim_ids):
            raise GlobalSynthesisError(
                "relation-set known claims must exactly match card claims"
            )
        return card_by_id, source_claims, claim_cards

    @staticmethod
    def _validate_exceptions(
        coverage_map: CoverageMap,
        candidates: tuple[CriticalExceptionCandidate, ...],
        source_claims: dict[str, SectionCardClaim],
    ) -> dict[str, CriticalExceptionCandidate]:
        if any(not isinstance(item, CriticalExceptionCandidate) for item in candidates):
            raise GlobalSynthesisError(
                "exception_candidates require CriticalExceptionCandidate values"
            )
        by_id = {item.candidate_id: item for item in candidates}
        if len(by_id) != len(candidates):
            raise GlobalSynthesisError("exception candidate IDs must be unique")
        if set(by_id) != set(coverage_map.exception_candidate_ids):
            raise GlobalSynthesisError(
                "exception candidates must exactly match CoverageMap IDs"
            )
        for candidate in candidates:
            if any(ref not in source_claims for ref in candidate.target_claim_refs):
                raise GlobalSynthesisError(
                    "exception target claim must exist in SectionCards"
                )
        return by_id

    @staticmethod
    def _build_claim(
        proposal: SynthesisClaimProposal,
        *,
        source_claims: dict[str, SectionCardClaim],
        claim_cards: dict[str, SectionCard],
        exceptions: dict[str, CriticalExceptionCandidate],
        relations: dict[str, CrossSectionRelationCandidate],
    ) -> SynthesisClaim:
        if not isinstance(proposal, SynthesisClaimProposal):
            raise GlobalSynthesisError(
                "claim_proposals require SynthesisClaimProposal values"
            )
        referenced_claim_ids = set(proposal.supporting_claim_ids) | set(
            proposal.opposing_claim_ids
        )
        if any(claim_id not in source_claims for claim_id in referenced_claim_ids):
            raise GlobalSynthesisError(
                "synthesis proposal references an unknown source claim"
            )
        for candidate_id in proposal.exception_candidate_ids:
            candidate = exceptions.get(candidate_id)
            if candidate is None:
                raise GlobalSynthesisError(
                    "synthesis proposal references an unknown exception"
                )
            if not candidate.target_claim_refs:
                raise GlobalSynthesisError(
                    "unresolved-target exceptions belong in unresolved questions"
                )
            if not set(candidate.target_claim_refs) & referenced_claim_ids:
                raise GlobalSynthesisError(
                    "exception must qualify a referenced source claim"
                )
        for relation_id in proposal.relation_ids:
            relation = relations.get(relation_id)
            if relation is None:
                raise GlobalSynthesisError(
                    "synthesis proposal references an unknown relation"
                )
            endpoints = {relation.source.claim_id, relation.target.claim_id}
            if not endpoints <= referenced_claim_ids:
                raise GlobalSynthesisError(
                    "referenced relation endpoints must appear in the proposal"
                )
        spans: list[SourceSpan] = []
        cards: set[str] = set()
        sections: set[str] = set()
        for claim_id in sorted(referenced_claim_ids):
            card_claim = source_claims[claim_id]
            card = claim_cards[claim_id]
            spans.extend(card_claim.claim.source_spans)
            cards.add(card.card_id)
            sections.add(card.section_id)
        for candidate_id in proposal.exception_candidate_ids:
            spans.append(exceptions[candidate_id].statement_span)
        return SynthesisClaim(
            proposal_key=proposal.proposal_key,
            kind=proposal.kind,
            text=proposal.text,
            supporting_claim_ids=proposal.supporting_claim_ids,
            opposing_claim_ids=proposal.opposing_claim_ids,
            exception_candidate_ids=proposal.exception_candidate_ids,
            relation_ids=proposal.relation_ids,
            source_card_ids=tuple(sorted(cards)),
            source_section_ids=tuple(sorted(sections)),
            source_spans=tuple(spans),
            qualifiers=proposal.qualifiers,
            inference_reason=proposal.inference_reason,
        )

    @staticmethod
    def _build_alternative(
        proposal: AlternativeInterpretationProposal,
        *,
        claims_by_key: dict[str, SynthesisClaim],
        source_claims: dict[str, SectionCardClaim],
    ) -> AlternativeInterpretation:
        if not isinstance(proposal, AlternativeInterpretationProposal):
            raise GlobalSynthesisError(
                "alternative proposals require AlternativeInterpretationProposal values"
            )
        try:
            synthesis_ids = tuple(
                sorted(
                    claims_by_key[key].synthesis_claim_id
                    for key in proposal.supporting_synthesis_keys
                )
            )
        except KeyError as exc:
            raise GlobalSynthesisError(
                "alternative references an unknown synthesis proposal key"
            ) from exc
        if any(claim_id not in source_claims for claim_id in proposal.source_claim_ids):
            raise GlobalSynthesisError(
                "alternative references an unknown source claim"
            )
        spans = tuple(
            span
            for claim_id in proposal.source_claim_ids
            for span in source_claims[claim_id].claim.source_spans
        )
        return AlternativeInterpretation(
            proposal_key=proposal.proposal_key,
            text=proposal.text,
            supporting_synthesis_claim_ids=synthesis_ids,
            source_claim_ids=proposal.source_claim_ids,
            source_spans=spans,
            contrast_reason=proposal.contrast_reason,
        )

    @staticmethod
    def _build_question(
        proposal: UnresolvedQuestionProposal,
        *,
        claims_by_key: dict[str, SynthesisClaim],
        source_claims: dict[str, SectionCardClaim],
        exceptions: dict[str, CriticalExceptionCandidate],
        relations: dict[str, CrossSectionRelationCandidate],
    ) -> UnresolvedSynthesisQuestion:
        if not isinstance(proposal, UnresolvedQuestionProposal):
            raise GlobalSynthesisError(
                "question proposals require UnresolvedQuestionProposal values"
            )
        try:
            synthesis_ids = tuple(
                sorted(
                    claims_by_key[key].synthesis_claim_id
                    for key in proposal.related_synthesis_keys
                )
            )
        except KeyError as exc:
            raise GlobalSynthesisError(
                "question references an unknown synthesis proposal key"
            ) from exc
        if any(
            claim_id not in source_claims
            for claim_id in proposal.related_source_claim_ids
        ):
            raise GlobalSynthesisError("question references an unknown source claim")
        if any(
            candidate_id not in exceptions
            for candidate_id in proposal.related_exception_candidate_ids
        ):
            raise GlobalSynthesisError("question references an unknown exception")
        if any(
            relation_id not in relations
            for relation_id in proposal.related_relation_ids
        ):
            raise GlobalSynthesisError("question references an unknown relation")
        spans: list[SourceSpan] = []
        for claim_id in proposal.related_source_claim_ids:
            spans.extend(source_claims[claim_id].claim.source_spans)
        for candidate_id in proposal.related_exception_candidate_ids:
            spans.append(exceptions[candidate_id].statement_span)
        for relation_id in proposal.related_relation_ids:
            relation = relations[relation_id]
            spans.extend(relation.evidence_spans)
        for key in proposal.related_synthesis_keys:
            spans.extend(claims_by_key[key].source_spans)
        return UnresolvedSynthesisQuestion(
            proposal_key=proposal.proposal_key,
            question=proposal.question,
            reason_code=proposal.reason_code,
            related_synthesis_claim_ids=synthesis_ids,
            related_source_claim_ids=proposal.related_source_claim_ids,
            related_exception_candidate_ids=(
                proposal.related_exception_candidate_ids
            ),
            related_relation_ids=proposal.related_relation_ids,
            source_spans=tuple(spans),
        )


def _canonical_spans(values: Iterable[SourceSpan]) -> tuple[SourceSpan, ...]:
    spans = tuple(values)
    if any(not isinstance(span, SourceSpan) for span in spans):
        raise GlobalSynthesisError("source spans require SourceSpan values")
    by_key: dict[tuple[str, str, int, int, str], SourceSpan] = {}
    for span in spans:
        key = (
            span.document_id,
            span.source_revision or "",
            span.start_offset,
            span.end_offset,
            span.content_hash,
        )
        by_key[key] = span
    return tuple(by_key[key] for key in sorted(by_key))


def _require_text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise GlobalSynthesisError(f"{field_name} must be a non-empty string")
    return value


def _unique_text_tuple(
    values: Iterable[str],
    field_name: str,
) -> tuple[str, ...]:
    result = tuple(values)
    for value in result:
        _require_text(value, field_name)
    if len(set(result)) != len(result):
        raise GlobalSynthesisError(f"{field_name} values must be unique")
    return result


def _unique_sorted_text(
    values: Iterable[str],
    field_name: str,
) -> tuple[str, ...]:
    result = _unique_text_tuple(values, field_name)
    ordered = tuple(sorted(result))
    if result != ordered:
        raise GlobalSynthesisError(f"{field_name} values must be sorted")
    return result


__all__ = [
    "GLOBAL_SYNTHESIS_SCHEMA_VERSION",
    "AlternativeInterpretation",
    "AlternativeInterpretationProposal",
    "GlobalDocumentSynthesis",
    "GlobalDocumentSynthesisBuilder",
    "GlobalSynthesisError",
    "SynthesisClaim",
    "SynthesisClaimKind",
    "SynthesisClaimProposal",
    "SynthesisValidationState",
    "UnresolvedQuestionProposal",
    "UnresolvedSynthesisQuestion",
]
