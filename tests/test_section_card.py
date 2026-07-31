from dataclasses import FrozenInstanceError

import pytest

from core.document_structure import (
    DeterministicDocumentStructureParser,
    DocumentStructureFormat,
)
from core.hierarchical_section_planner import (
    HierarchicalSectionPlanner,
    ReadingUnit,
    SectionPlanningBudget,
)
from core.knowledge_capsule import (
    CapsuleClaim,
    ClaimModality,
    KnowledgeCapsule,
    SourceSpan,
)
from core.section_card import (
    InterpretationKind,
    SectionCardBuilder,
    SectionCardError,
    SectionCardInterpretation,
    SpanCoordinateSpace,
)
from core.semantic_reader import (
    RawSource,
    ReaderResult,
    ReaderStatus,
    ReaderWarning,
)


def _source_and_unit() -> tuple[RawSource, ReadingUnit, str]:
    text = (
        "Alpha claim appears here. More alpha context.\n\n"
        "Beta claim appears later. Final context."
    )
    source = RawSource(
        document_id="doc-1",
        text=text,
        source_revision="revision-1",
    )
    structure = DeterministicDocumentStructureParser().parse(
        source,
        document_format=DocumentStructureFormat.PLAIN_TEXT,
    )
    plan = HierarchicalSectionPlanner().plan(
        source,
        structure,
        budget=SectionPlanningBudget(
            max_unit_chars=48,
            min_unit_chars=15,
            boundary_search_chars=30,
        ),
    )
    return source, plan.units[0], plan.plan_id


def _capsule(
    *,
    source: RawSource,
    unit: ReadingUnit,
    coordinate_space: SpanCoordinateSpace,
    reader_id: str = "reader-a",
    reader_version: str = "1",
    coverage_score: float = 0.5,
) -> KnowledgeCapsule:
    unit_text = source.text[unit.start_offset : unit.end_offset]
    quote = "Alpha claim"
    if coordinate_space is SpanCoordinateSpace.UNIT_LOCAL:
        start = unit_text.index(quote)
        span = SourceSpan.from_text(
            document_id=unit.document_id,
            raw_text=unit_text,
            start_offset=start,
            end_offset=start + len(quote),
            source_revision=unit.source_revision,
        )
    else:
        start = source.text.index(quote)
        span = SourceSpan.from_text(
            document_id=unit.document_id,
            raw_text=source.text,
            start_offset=start,
            end_offset=start + len(quote),
            source_revision=unit.source_revision,
        )
    claim = CapsuleClaim.create(
        text=quote,
        modality=ClaimModality.OBSERVATION,
        source_spans=(span,),
        extraction_confidence=1.0,
    )
    return KnowledgeCapsule.create(
        source_document_id=unit.document_id,
        essence="Alpha claim is present.",
        claims=(claim,),
        reader_id=reader_id,
        reader_version=reader_version,
        entities=("Alpha",),
        omitted_questions=("What follows?",),
        coverage_score=coverage_score,
        compression_ratio=0.25,
    )


def test_unit_local_claim_spans_are_rebased_to_absolute_offsets() -> None:
    source, unit, plan_id = _source_and_unit()
    capsule = _capsule(
        source=source,
        unit=unit,
        coordinate_space=SpanCoordinateSpace.UNIT_LOCAL,
    )

    card = SectionCardBuilder().build(
        source,
        unit,
        ReaderResult.success(capsule),
        plan_id=plan_id,
        coordinate_space=SpanCoordinateSpace.UNIT_LOCAL,
    )

    claim = card.claims[0]
    absolute_span = claim.claim.source_spans[0]
    assert claim.origin_claim_id == capsule.claims[0].claim_id
    assert claim.source_capsule_id == capsule.capsule_id
    assert absolute_span.start_offset == source.text.index("Alpha claim")
    assert absolute_span.end_offset == absolute_span.start_offset + len("Alpha claim")
    assert absolute_span.verify(source.text)
    assert card.unit_source_span == unit.source_span
    assert card.build_receipt.referenced_source_chars == len("Alpha claim")
    assert card.build_receipt.reader_reported_coverage_score == 0.5


def test_absolute_claim_spans_are_preserved_and_verified() -> None:
    source, unit, plan_id = _source_and_unit()
    capsule = _capsule(
        source=source,
        unit=unit,
        coordinate_space=SpanCoordinateSpace.DOCUMENT_ABSOLUTE,
    )

    card = SectionCardBuilder().build(
        source,
        unit,
        ReaderResult.success(capsule),
        plan_id=plan_id,
        coordinate_space=SpanCoordinateSpace.DOCUMENT_ABSOLUTE,
    )

    original = capsule.claims[0].source_spans[0]
    resolved = card.claims[0].claim.source_spans[0]
    assert (resolved.start_offset, resolved.end_offset) == (
        original.start_offset,
        original.end_offset,
    )
    assert resolved.verify(source.text)


def test_partial_reader_warnings_are_preserved_as_codes() -> None:
    source, unit, plan_id = _source_and_unit()
    capsule = _capsule(
        source=source,
        unit=unit,
        coordinate_space=SpanCoordinateSpace.UNIT_LOCAL,
    )
    result = ReaderResult.partial(
        capsule,
        warnings=(
            ReaderWarning(
                code="reader_truncated",
                safe_message="Reader stopped at its configured claim limit.",
            ),
        ),
    )

    card = SectionCardBuilder().build(
        source,
        unit,
        result,
        plan_id=plan_id,
        coordinate_space=SpanCoordinateSpace.UNIT_LOCAL,
    )

    assert card.build_receipt.reader_status is ReaderStatus.PARTIAL
    assert card.build_receipt.reader_warning_codes == ("reader_truncated",)
    assert "reader_truncated" in card.warnings


def test_interpretation_is_explicit_and_source_supported() -> None:
    source, unit, plan_id = _source_and_unit()
    capsule = _capsule(
        source=source,
        unit=unit,
        coordinate_space=SpanCoordinateSpace.UNIT_LOCAL,
    )
    support = SourceSpan.from_text(
        document_id=unit.document_id,
        raw_text=source.text,
        start_offset=unit.start_offset,
        end_offset=unit.start_offset + len("Alpha claim"),
        source_revision=unit.source_revision,
    )
    interpretation = SectionCardInterpretation.create(
        kind=InterpretationKind.ARGUMENT,
        text="The section opens with an example claim.",
        supporting_spans=(support,),
        inference_reason="Derived from the section order; not quoted as a claim.",
    )

    card = SectionCardBuilder().build(
        source,
        unit,
        ReaderResult.success(capsule),
        plan_id=plan_id,
        coordinate_space=SpanCoordinateSpace.UNIT_LOCAL,
        interpretations=(interpretation,),
    )

    assert card.interpretations == (interpretation,)
    assert all(
        item.interpretation_id != card.claims[0].claim.claim_id
        for item in card.interpretations
    )


def test_out_of_unit_absolute_span_is_rejected() -> None:
    source, unit, plan_id = _source_and_unit()
    quote = "Beta claim"
    start = source.text.index(quote)
    outside_span = SourceSpan.from_text(
        document_id=unit.document_id,
        raw_text=source.text,
        start_offset=start,
        end_offset=start + len(quote),
        source_revision=unit.source_revision,
    )
    claim = CapsuleClaim.create(
        text=quote,
        modality=ClaimModality.OBSERVATION,
        source_spans=(outside_span,),
        extraction_confidence=1.0,
    )
    capsule = KnowledgeCapsule.create(
        source_document_id=unit.document_id,
        essence="Beta claim.",
        claims=(claim,),
        reader_id="reader",
        reader_version="1",
    )

    with pytest.raises(SectionCardError, match="fit inside"):
        SectionCardBuilder().build(
            source,
            unit,
            ReaderResult.success(capsule),
            plan_id=plan_id,
            coordinate_space=SpanCoordinateSpace.DOCUMENT_ABSOLUTE,
        )


def test_invalid_unit_local_span_hash_is_rejected() -> None:
    source, unit, plan_id = _source_and_unit()
    wrong_text = "Wrong claim"
    span = SourceSpan.from_text(
        document_id=unit.document_id,
        raw_text=wrong_text,
        start_offset=0,
        end_offset=len(wrong_text),
        source_revision=unit.source_revision,
    )
    claim = CapsuleClaim.create(
        text=wrong_text,
        modality=ClaimModality.OBSERVATION,
        source_spans=(span,),
        extraction_confidence=1.0,
    )
    capsule = KnowledgeCapsule.create(
        source_document_id=unit.document_id,
        essence="Wrong claim.",
        claims=(claim,),
        reader_id="reader",
        reader_version="1",
    )

    with pytest.raises(SectionCardError, match="hash"):
        SectionCardBuilder().build(
            source,
            unit,
            ReaderResult.success(capsule),
            plan_id=plan_id,
            coordinate_space=SpanCoordinateSpace.UNIT_LOCAL,
        )


def test_failed_reader_result_cannot_become_a_card() -> None:
    source, unit, plan_id = _source_and_unit()
    result = ReaderResult.failed(
        ReaderStatus.INVALID_OUTPUT,
        code="invalid",
        safe_message="Invalid reader output.",
    )

    with pytest.raises(SectionCardError, match="SUCCESS or PARTIAL"):
        SectionCardBuilder().build(
            source,
            unit,
            result,
            plan_id=plan_id,
            coordinate_space=SpanCoordinateSpace.UNIT_LOCAL,
        )


def test_card_identity_excludes_replaceable_reader_metadata() -> None:
    source, unit, plan_id = _source_and_unit()
    first_capsule = _capsule(
        source=source,
        unit=unit,
        coordinate_space=SpanCoordinateSpace.UNIT_LOCAL,
        reader_id="reader-a",
        reader_version="1",
    )
    second_capsule = _capsule(
        source=source,
        unit=unit,
        coordinate_space=SpanCoordinateSpace.UNIT_LOCAL,
        reader_id="reader-b",
        reader_version="99",
    )
    builder = SectionCardBuilder()

    first = builder.build(
        source,
        unit,
        ReaderResult.success(first_capsule),
        plan_id=plan_id,
        coordinate_space=SpanCoordinateSpace.UNIT_LOCAL,
    )
    second = builder.build(
        source,
        unit,
        ReaderResult.success(second_capsule),
        plan_id=plan_id,
        coordinate_space=SpanCoordinateSpace.UNIT_LOCAL,
    )

    assert first_capsule.capsule_id == second_capsule.capsule_id
    assert first.card_id == second.card_id
    assert first.reader_id != second.reader_id


def test_card_is_immutable_and_exposes_no_authority_fields() -> None:
    source, unit, plan_id = _source_and_unit()
    capsule = _capsule(
        source=source,
        unit=unit,
        coordinate_space=SpanCoordinateSpace.UNIT_LOCAL,
    )
    card = SectionCardBuilder().build(
        source,
        unit,
        ReaderResult.success(capsule),
        plan_id=plan_id,
        coordinate_space=SpanCoordinateSpace.UNIT_LOCAL,
    )

    with pytest.raises(FrozenInstanceError):
        card.local_essence = "changed"  # type: ignore[misc]

    forbidden = {
        "canon_write",
        "memory_write",
        "truth_gate_bypass",
        "tool_authority",
        "policy_authority",
    }
    assert forbidden.isdisjoint(card.__dataclass_fields__)
