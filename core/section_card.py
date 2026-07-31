"""Source-linked SectionCard contracts and builder for Reader Core PR-RDR-03.

A SectionCard is a derived, rebuildable reading note. It preserves accepted
``KnowledgeCapsule`` claims, rebases unit-local source spans into absolute
document coordinates, and keeps inferred interpretations explicitly separate.
It grants no Canon, memory, policy, tool, TruthGate, or Write Gate authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import math
from typing import Iterable

from core.hierarchical_section_planner import ReadingUnit
from core.knowledge_capsule import CapsuleClaim, KnowledgeCapsule, SourceSpan
from core.reader_core_contracts import stable_reader_core_id
from core.semantic_reader import RawSource, ReaderResult, ReaderStatus

SECTION_CARD_SCHEMA_VERSION = "reader-core.section-card.v1"


class SectionCardError(ValueError):
    """Raised when a SectionCard invariant or build boundary is violated."""


class SpanCoordinateSpace(str, Enum):
    """Coordinate system used by source spans in an input KnowledgeCapsule."""

    UNIT_LOCAL = "unit_local"
    DOCUMENT_ABSOLUTE = "document_absolute"


class InterpretationKind(str, Enum):
    """Explicit category for a derived interpretation, never an extracted claim."""

    DEFINITION = "definition"
    ARGUMENT = "argument"
    EXAMPLE = "example"
    CONDITION = "condition"
    UNCERTAINTY = "uncertainty"
    IMPORTANT_QUOTE = "important_quote"
    OTHER = "other"


@dataclass(frozen=True, slots=True)
class SectionCardClaim:
    """One accepted capsule claim with absolute document provenance."""

    origin_claim_id: str
    source_capsule_id: str
    claim: CapsuleClaim

    def __post_init__(self) -> None:
        _require_text(self.origin_claim_id, "origin_claim_id")
        _require_text(self.source_capsule_id, "source_capsule_id")
        if not isinstance(self.claim, CapsuleClaim):
            raise SectionCardError("claim must be a CapsuleClaim")


@dataclass(frozen=True, slots=True)
class SectionCardInterpretation:
    """An explicitly inferred note supported by source spans.

    Interpretations are never placed in ``claims`` and always require a reason.
    This prevents an inference from silently becoming an extracted source claim.
    """

    interpretation_id: str
    kind: InterpretationKind
    text: str
    supporting_spans: tuple[SourceSpan, ...]
    inference_reason: str

    def __post_init__(self) -> None:
        _require_text(self.interpretation_id, "interpretation_id")
        if not isinstance(self.kind, InterpretationKind):
            raise SectionCardError("kind must be an InterpretationKind")
        _require_text(self.text, "text")
        _require_text(self.inference_reason, "inference_reason")
        spans = tuple(self.supporting_spans)
        if not spans or any(not isinstance(span, SourceSpan) for span in spans):
            raise SectionCardError(
                "interpretations require at least one supporting SourceSpan"
            )
        object.__setattr__(self, "supporting_spans", spans)
        expected_id = _interpretation_identity(
            kind=self.kind,
            text=self.text,
            supporting_spans=spans,
            inference_reason=self.inference_reason,
        )
        if self.interpretation_id != expected_id:
            raise SectionCardError(
                "interpretation_id does not match interpretation content"
            )

    @classmethod
    def create(
        cls,
        *,
        kind: InterpretationKind,
        text: str,
        supporting_spans: Iterable[SourceSpan],
        inference_reason: str,
    ) -> SectionCardInterpretation:
        spans = tuple(supporting_spans)
        return cls(
            interpretation_id=_interpretation_identity(
                kind=kind,
                text=text,
                supporting_spans=spans,
                inference_reason=inference_reason,
            ),
            kind=kind,
            text=text,
            supporting_spans=spans,
            inference_reason=inference_reason,
        )


@dataclass(frozen=True, slots=True)
class SectionCardBuildReceipt:
    """Observable build counts; not truth confidence and not CoverageMap."""

    receipt_id: str
    unit_id: str
    original_capsule_id: str
    reader_status: ReaderStatus
    coordinate_space: SpanCoordinateSpace
    absolute_claim_ids: tuple[str, ...]
    claim_count: int
    source_span_count: int
    referenced_source_chars: int
    unit_char_count: int
    omitted_question_count: int
    reader_reported_coverage_score: float
    reader_warning_codes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_text(self.receipt_id, "receipt_id")
        _require_text(self.unit_id, "unit_id")
        _require_text(self.original_capsule_id, "original_capsule_id")
        if self.reader_status not in {ReaderStatus.SUCCESS, ReaderStatus.PARTIAL}:
            raise SectionCardError(
                "reader_status must be SUCCESS or PARTIAL for a card receipt"
            )
        if not isinstance(self.coordinate_space, SpanCoordinateSpace):
            raise SectionCardError(
                "coordinate_space must be a SpanCoordinateSpace"
            )
        claim_ids = _text_tuple(self.absolute_claim_ids, "absolute_claim_id")
        if not claim_ids or len(set(claim_ids)) != len(claim_ids):
            raise SectionCardError(
                "absolute_claim_ids must be non-empty and unique"
            )
        object.__setattr__(self, "absolute_claim_ids", claim_ids)
        for name in (
            "claim_count",
            "source_span_count",
            "referenced_source_chars",
            "unit_char_count",
            "omitted_question_count",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise SectionCardError(f"{name} must be an integer >= 0")
        if self.claim_count != len(claim_ids):
            raise SectionCardError(
                "claim_count must equal the number of absolute_claim_ids"
            )
        if self.source_span_count <= 0:
            raise SectionCardError("source_span_count must be positive")
        if self.unit_char_count <= 0:
            raise SectionCardError("unit_char_count must be positive")
        if self.referenced_source_chars > self.unit_char_count:
            raise SectionCardError(
                "referenced_source_chars cannot exceed unit_char_count"
            )
        score = _probability(
            self.reader_reported_coverage_score,
            "reader_reported_coverage_score",
        )
        object.__setattr__(self, "reader_reported_coverage_score", score)
        warning_codes = _text_tuple(
            self.reader_warning_codes,
            "reader_warning_code",
        )
        object.__setattr__(self, "reader_warning_codes", warning_codes)
        expected_id = _receipt_identity(
            unit_id=self.unit_id,
            original_capsule_id=self.original_capsule_id,
            reader_status=self.reader_status,
            coordinate_space=self.coordinate_space,
            absolute_claim_ids=claim_ids,
            source_span_count=self.source_span_count,
            referenced_source_chars=self.referenced_source_chars,
            unit_char_count=self.unit_char_count,
            omitted_question_count=self.omitted_question_count,
            reader_reported_coverage_score=score,
            reader_warning_codes=warning_codes,
        )
        if self.receipt_id != expected_id:
            raise SectionCardError("receipt_id does not match receipt content")


@dataclass(frozen=True, slots=True)
class SectionCard:
    """One immutable source-linked reading note for one ReadingUnit."""

    card_id: str
    schema_version: str
    builder_version: str
    document_id: str
    source_revision: str
    structure_map_id: str
    plan_id: str
    section_id: str
    unit_id: str
    unit_source_span: SourceSpan
    local_essence: str
    claims: tuple[SectionCardClaim, ...]
    interpretations: tuple[SectionCardInterpretation, ...]
    entities: tuple[str, ...]
    omitted_questions: tuple[str, ...]
    reader_id: str
    reader_version: str
    prompt_version: str | None
    build_receipt: SectionCardBuildReceipt
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in (
            "card_id",
            "schema_version",
            "builder_version",
            "document_id",
            "source_revision",
            "structure_map_id",
            "plan_id",
            "section_id",
            "unit_id",
            "local_essence",
            "reader_id",
            "reader_version",
        ):
            _require_text(getattr(self, name), name)
        if self.schema_version != SECTION_CARD_SCHEMA_VERSION:
            raise SectionCardError("unsupported SectionCard schema_version")
        if self.prompt_version is not None:
            _require_text(self.prompt_version, "prompt_version")
        if not isinstance(self.unit_source_span, SourceSpan):
            raise SectionCardError("unit_source_span must be a SourceSpan")
        self._validate_span(self.unit_source_span, "unit_source_span")
        if self.unit_source_span.span_id != self.unit_id:
            raise SectionCardError("unit_source_span span_id must equal unit_id")

        claims = tuple(self.claims)
        if not claims or any(not isinstance(item, SectionCardClaim) for item in claims):
            raise SectionCardError(
                "claims must contain at least one SectionCardClaim"
            )
        for card_claim in claims:
            for span in card_claim.claim.source_spans:
                self._validate_span(span, "claim source span")
                self._require_inside_unit(span)
        object.__setattr__(self, "claims", claims)

        interpretations = tuple(self.interpretations)
        if any(
            not isinstance(item, SectionCardInterpretation)
            for item in interpretations
        ):
            raise SectionCardError(
                "interpretations must contain SectionCardInterpretation values"
            )
        for interpretation in interpretations:
            for span in interpretation.supporting_spans:
                self._validate_span(span, "interpretation supporting span")
                self._require_inside_unit(span)
        object.__setattr__(self, "interpretations", interpretations)
        entities = _text_tuple(self.entities, "entity")
        omitted_questions = _text_tuple(
            self.omitted_questions,
            "omitted_question",
        )
        object.__setattr__(self, "entities", entities)
        object.__setattr__(self, "omitted_questions", omitted_questions)
        if not isinstance(self.build_receipt, SectionCardBuildReceipt):
            raise SectionCardError(
                "build_receipt must be a SectionCardBuildReceipt"
            )
        self._validate_receipt(claims, omitted_questions)
        warnings = _text_tuple(self.warnings, "warning")
        if not set(self.build_receipt.reader_warning_codes).issubset(warnings):
            raise SectionCardError(
                "card warnings must include every Reader warning code"
            )
        object.__setattr__(self, "warnings", warnings)

        expected_id = _card_identity(
            schema_version=self.schema_version,
            builder_version=self.builder_version,
            document_id=self.document_id,
            source_revision=self.source_revision,
            structure_map_id=self.structure_map_id,
            plan_id=self.plan_id,
            section_id=self.section_id,
            unit_id=self.unit_id,
            unit_source_span=self.unit_source_span,
            local_essence=self.local_essence,
            claims=claims,
            interpretations=interpretations,
            entities=entities,
            omitted_questions=omitted_questions,
        )
        if self.card_id != expected_id:
            raise SectionCardError("card_id does not match card content")

    def _validate_span(self, span: SourceSpan, field_name: str) -> None:
        if span.document_id != self.document_id:
            raise SectionCardError(f"{field_name} document_id must match card")
        if span.source_revision != self.source_revision:
            raise SectionCardError(f"{field_name} source_revision must match card")

    def _require_inside_unit(self, span: SourceSpan) -> None:
        if (
            span.start_offset < self.unit_source_span.start_offset
            or span.end_offset > self.unit_source_span.end_offset
        ):
            raise SectionCardError(
                "all card provenance spans must be contained in the unit span"
            )

    def _validate_receipt(
        self,
        claims: tuple[SectionCardClaim, ...],
        omitted_questions: tuple[str, ...],
    ) -> None:
        receipt = self.build_receipt
        if receipt.unit_id != self.unit_id:
            raise SectionCardError("build receipt unit_id must match card")
        capsule_ids = {card_claim.source_capsule_id for card_claim in claims}
        if capsule_ids != {receipt.original_capsule_id}:
            raise SectionCardError(
                "all card claims must reference the receipt capsule"
            )
        claim_ids = tuple(card_claim.claim.claim_id for card_claim in claims)
        if receipt.absolute_claim_ids != claim_ids:
            raise SectionCardError(
                "receipt absolute_claim_ids must match card claims"
            )
        claim_spans = tuple(
            span
            for card_claim in claims
            for span in card_claim.claim.source_spans
        )
        if receipt.source_span_count != len(claim_spans):
            raise SectionCardError(
                "receipt source_span_count must match card claims"
            )
        if receipt.referenced_source_chars != _union_char_count(claim_spans):
            raise SectionCardError(
                "receipt referenced_source_chars must match card claims"
            )
        unit_char_count = (
            self.unit_source_span.end_offset - self.unit_source_span.start_offset
        )
        if receipt.unit_char_count != unit_char_count:
            raise SectionCardError(
                "receipt unit_char_count must match unit_source_span"
            )
        if receipt.omitted_question_count != len(omitted_questions):
            raise SectionCardError(
                "receipt omitted_question_count must match card"
            )


class SectionCardBuilder:
    """Build cards from accepted Reader results without widening authority."""

    builder_version = "1.1.0"

    def build(
        self,
        source: RawSource,
        unit: ReadingUnit,
        reader_result: ReaderResult,
        *,
        plan_id: str,
        coordinate_space: SpanCoordinateSpace,
        interpretations: Iterable[SectionCardInterpretation] = (),
    ) -> SectionCard:
        """Validate, rebase, and freeze one accepted Reader result as a card."""

        _require_text(plan_id, "plan_id")
        if not isinstance(coordinate_space, SpanCoordinateSpace):
            raise SectionCardError(
                "coordinate_space must be a SpanCoordinateSpace"
            )
        self._validate_source_and_unit(source, unit)
        capsule = self._accepted_capsule(reader_result)
        if capsule.source_document_id != unit.document_id:
            raise SectionCardError(
                "capsule source_document_id must match reading unit"
            )

        card_claims = tuple(
            SectionCardClaim(
                origin_claim_id=claim.claim_id,
                source_capsule_id=capsule.capsule_id,
                claim=self._absolute_claim(
                    source,
                    unit,
                    claim,
                    coordinate_space=coordinate_space,
                ),
            )
            for claim in capsule.claims
        )
        resolved_interpretations = tuple(interpretations)
        self._validate_interpretations(
            source,
            unit,
            resolved_interpretations,
        )
        warning_codes = tuple(warning.code for warning in reader_result.warnings)
        all_claim_spans = tuple(
            span
            for card_claim in card_claims
            for span in card_claim.claim.source_spans
        )
        absolute_claim_ids = tuple(
            card_claim.claim.claim_id for card_claim in card_claims
        )
        referenced_chars = _union_char_count(all_claim_spans)
        receipt_id = _receipt_identity(
            unit_id=unit.unit_id,
            original_capsule_id=capsule.capsule_id,
            reader_status=reader_result.status,
            coordinate_space=coordinate_space,
            absolute_claim_ids=absolute_claim_ids,
            source_span_count=len(all_claim_spans),
            referenced_source_chars=referenced_chars,
            unit_char_count=unit.char_count,
            omitted_question_count=len(capsule.omitted_questions),
            reader_reported_coverage_score=capsule.coverage_score,
            reader_warning_codes=warning_codes,
        )
        receipt = SectionCardBuildReceipt(
            receipt_id=receipt_id,
            unit_id=unit.unit_id,
            original_capsule_id=capsule.capsule_id,
            reader_status=reader_result.status,
            coordinate_space=coordinate_space,
            absolute_claim_ids=absolute_claim_ids,
            claim_count=len(card_claims),
            source_span_count=len(all_claim_spans),
            referenced_source_chars=referenced_chars,
            unit_char_count=unit.char_count,
            omitted_question_count=len(capsule.omitted_questions),
            reader_reported_coverage_score=capsule.coverage_score,
            reader_warning_codes=warning_codes,
        )
        card_id = _card_identity(
            schema_version=SECTION_CARD_SCHEMA_VERSION,
            builder_version=self.builder_version,
            document_id=unit.document_id,
            source_revision=unit.source_revision,
            structure_map_id=unit.structure_map_id,
            plan_id=plan_id,
            section_id=unit.section_id,
            unit_id=unit.unit_id,
            unit_source_span=unit.source_span,
            local_essence=capsule.essence,
            claims=card_claims,
            interpretations=resolved_interpretations,
            entities=capsule.entities,
            omitted_questions=capsule.omitted_questions,
        )
        warnings = tuple(dict.fromkeys((*warning_codes, *unit.warnings)))
        return SectionCard(
            card_id=card_id,
            schema_version=SECTION_CARD_SCHEMA_VERSION,
            builder_version=self.builder_version,
            document_id=unit.document_id,
            source_revision=unit.source_revision,
            structure_map_id=unit.structure_map_id,
            plan_id=plan_id,
            section_id=unit.section_id,
            unit_id=unit.unit_id,
            unit_source_span=unit.source_span,
            local_essence=capsule.essence,
            claims=card_claims,
            interpretations=resolved_interpretations,
            entities=capsule.entities,
            omitted_questions=capsule.omitted_questions,
            reader_id=capsule.reader_id,
            reader_version=capsule.reader_version,
            prompt_version=capsule.prompt_version,
            build_receipt=receipt,
            warnings=warnings,
        )

    @staticmethod
    def _accepted_capsule(reader_result: ReaderResult) -> KnowledgeCapsule:
        if not isinstance(reader_result, ReaderResult):
            raise SectionCardError("reader_result must be a ReaderResult")
        if reader_result.status not in {ReaderStatus.SUCCESS, ReaderStatus.PARTIAL}:
            raise SectionCardError(
                "SectionCard requires a SUCCESS or PARTIAL ReaderResult"
            )
        if reader_result.capsule is None:
            raise SectionCardError("accepted ReaderResult must contain a capsule")
        return reader_result.capsule

    @staticmethod
    def _validate_source_and_unit(source: RawSource, unit: ReadingUnit) -> None:
        if not isinstance(source, RawSource):
            raise SectionCardError("source must be a RawSource")
        if not isinstance(unit, ReadingUnit):
            raise SectionCardError("unit must be a ReadingUnit")
        if source.document_id != unit.document_id:
            raise SectionCardError("source document_id must match unit")
        if _source_revision(source) != unit.source_revision:
            raise SectionCardError("source revision must match unit")
        if not unit.source_span.verify(source.text):
            raise SectionCardError("unit source span must verify against source")

    def _absolute_claim(
        self,
        source: RawSource,
        unit: ReadingUnit,
        claim: CapsuleClaim,
        *,
        coordinate_space: SpanCoordinateSpace,
    ) -> CapsuleClaim:
        absolute_spans = tuple(
            self._absolute_span(
                source,
                unit,
                span,
                coordinate_space=coordinate_space,
            )
            for span in claim.source_spans
        )
        return CapsuleClaim.create(
            text=claim.text,
            modality=claim.modality,
            source_spans=absolute_spans,
            extraction_confidence=claim.extraction_confidence,
            truth_confidence=claim.truth_confidence,
            qualifiers=claim.qualifiers,
            uncertainties=claim.uncertainties,
            applicability_conditions=claim.applicability_conditions,
            temporal_scope=claim.temporal_scope,
        )

    @staticmethod
    def _absolute_span(
        source: RawSource,
        unit: ReadingUnit,
        span: SourceSpan,
        *,
        coordinate_space: SpanCoordinateSpace,
    ) -> SourceSpan:
        if span.document_id != unit.document_id:
            raise SectionCardError("claim span document_id must match unit")
        if span.source_revision not in {None, unit.source_revision}:
            raise SectionCardError("claim span source_revision must match unit")

        if coordinate_space is SpanCoordinateSpace.UNIT_LOCAL:
            if span.start_offset < 0 or span.end_offset > unit.char_count:
                raise SectionCardError(
                    "unit-local claim span must fit inside the reading unit"
                )
            unit_text = source.text[unit.start_offset : unit.end_offset]
            if not span.verify(unit_text):
                raise SectionCardError(
                    "unit-local claim span hash must verify against unit text"
                )
            absolute_start = unit.start_offset + span.start_offset
            absolute_end = unit.start_offset + span.end_offset
        else:
            absolute_start = span.start_offset
            absolute_end = span.end_offset
            if (
                absolute_start < unit.start_offset
                or absolute_end > unit.end_offset
            ):
                raise SectionCardError(
                    "absolute claim span must fit inside the reading unit"
                )
            if not span.verify(source.text):
                raise SectionCardError(
                    "absolute claim span hash must verify against source"
                )

        return SourceSpan.from_text(
            document_id=unit.document_id,
            raw_text=source.text,
            start_offset=absolute_start,
            end_offset=absolute_end,
            source_revision=unit.source_revision,
        )

    @staticmethod
    def _validate_interpretations(
        source: RawSource,
        unit: ReadingUnit,
        interpretations: tuple[SectionCardInterpretation, ...],
    ) -> None:
        for interpretation in interpretations:
            if not isinstance(interpretation, SectionCardInterpretation):
                raise SectionCardError(
                    "interpretations must contain SectionCardInterpretation values"
                )
            for span in interpretation.supporting_spans:
                if span.document_id != unit.document_id:
                    raise SectionCardError(
                        "interpretation span document_id must match unit"
                    )
                if span.source_revision != unit.source_revision:
                    raise SectionCardError(
                        "interpretation span source_revision must match unit"
                    )
                if (
                    span.start_offset < unit.start_offset
                    or span.end_offset > unit.end_offset
                ):
                    raise SectionCardError(
                        "interpretation spans must fit inside the reading unit"
                    )
                if not span.verify(source.text):
                    raise SectionCardError(
                        "interpretation span hash must verify against source"
                    )


def _interpretation_identity(
    *,
    kind: InterpretationKind,
    text: str,
    supporting_spans: tuple[SourceSpan, ...],
    inference_reason: str,
) -> str:
    return stable_reader_core_id(
        "section-card-interpretation",
        {
            "kind": kind.value if isinstance(kind, InterpretationKind) else kind,
            "text": text,
            "supporting_spans": [
                span.identity_payload() for span in supporting_spans
            ],
            "inference_reason": inference_reason,
        },
    )


def _receipt_identity(
    *,
    unit_id: str,
    original_capsule_id: str,
    reader_status: ReaderStatus,
    coordinate_space: SpanCoordinateSpace,
    absolute_claim_ids: tuple[str, ...],
    source_span_count: int,
    referenced_source_chars: int,
    unit_char_count: int,
    omitted_question_count: int,
    reader_reported_coverage_score: float,
    reader_warning_codes: tuple[str, ...],
) -> str:
    return stable_reader_core_id(
        "section-card-build-receipt",
        {
            "unit_id": unit_id,
            "original_capsule_id": original_capsule_id,
            "reader_status": reader_status.value,
            "coordinate_space": coordinate_space.value,
            "absolute_claim_ids": list(absolute_claim_ids),
            "source_span_count": source_span_count,
            "referenced_source_chars": referenced_source_chars,
            "unit_char_count": unit_char_count,
            "omitted_question_count": omitted_question_count,
            "reader_reported_coverage_score": reader_reported_coverage_score,
            "reader_warning_codes": list(reader_warning_codes),
        },
    )


def _card_identity(
    *,
    schema_version: str,
    builder_version: str,
    document_id: str,
    source_revision: str,
    structure_map_id: str,
    plan_id: str,
    section_id: str,
    unit_id: str,
    unit_source_span: SourceSpan,
    local_essence: str,
    claims: tuple[SectionCardClaim, ...],
    interpretations: tuple[SectionCardInterpretation, ...],
    entities: tuple[str, ...],
    omitted_questions: tuple[str, ...],
) -> str:
    return stable_reader_core_id(
        "section-card",
        {
            "schema_version": schema_version,
            "builder_version": builder_version,
            "document_id": document_id,
            "source_revision": source_revision,
            "structure_map_id": structure_map_id,
            "plan_id": plan_id,
            "section_id": section_id,
            "unit_id": unit_id,
            "unit_source_span": unit_source_span.identity_payload(),
            "local_essence": local_essence,
            "claim_payloads": [
                card_claim.claim.identity_payload() for card_claim in claims
            ],
            "interpretation_ids": [
                interpretation.interpretation_id
                for interpretation in interpretations
            ],
            "entities": sorted(entities),
            "omitted_questions": sorted(omitted_questions),
        },
    )


def _source_revision(source: RawSource) -> str:
    if source.source_revision is not None:
        return source.source_revision
    content_hash = sha256(source.text.encode("utf-8")).hexdigest()
    return f"sha256:{content_hash}"


def _union_char_count(spans: Iterable[SourceSpan]) -> int:
    intervals = sorted((span.start_offset, span.end_offset) for span in spans)
    if not intervals:
        return 0
    total = 0
    current_start, current_end = intervals[0]
    for start, end in intervals[1:]:
        if start <= current_end:
            current_end = max(current_end, end)
            continue
        total += current_end - current_start
        current_start, current_end = start, end
    return total + current_end - current_start


def _probability(value: float, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SectionCardError(f"{field_name} must be a number in [0, 1]")
    result = float(value)
    if not math.isfinite(result) or not 0.0 <= result <= 1.0:
        raise SectionCardError(f"{field_name} must be finite and in [0, 1]")
    return result


def _require_text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SectionCardError(f"{field_name} must be a non-empty string")
    return value


def _text_tuple(values: Iterable[str], field_name: str) -> tuple[str, ...]:
    result = tuple(values)
    for value in result:
        _require_text(value, field_name)
    return result


__all__ = [
    "InterpretationKind",
    "SECTION_CARD_SCHEMA_VERSION",
    "SectionCard",
    "SectionCardBuildReceipt",
    "SectionCardBuilder",
    "SectionCardClaim",
    "SectionCardError",
    "SectionCardInterpretation",
    "SpanCoordinateSpace",
]
