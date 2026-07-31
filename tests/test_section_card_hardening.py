from dataclasses import replace

import pytest

from core.document_structure import (
    DeterministicDocumentStructureParser,
    DocumentStructureFormat,
)
from core.hierarchical_section_planner import HierarchicalSectionPlanner
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
from core.semantic_reader import RawSource, ReaderResult


def _plan_without_explicit_revision() -> tuple[RawSource, object, str]:
    source = RawSource(
        document_id="derived-revision-doc",
        text="Alpha claim appears in this source.",
    )
    structure = DeterministicDocumentStructureParser().parse(
        source,
        document_format=DocumentStructureFormat.PLAIN_TEXT,
    )
    plan = HierarchicalSectionPlanner().plan(source, structure)
    return source, plan.units[0], plan.plan_id


def _capsule(
    source: RawSource,
    unit: object,
    *,
    coordinate_space: SpanCoordinateSpace,
) -> KnowledgeCapsule:
    start = source.text.index("Alpha claim")
    end = start + len("Alpha claim")
    if coordinate_space is SpanCoordinateSpace.UNIT_LOCAL:
        unit_text = source.text[unit.start_offset : unit.end_offset]
        local_start = unit_text.index("Alpha claim")
        span = SourceSpan.from_text(
            document_id=unit.document_id,
            raw_text=unit_text,
            start_offset=local_start,
            end_offset=local_start + len("Alpha claim"),
            source_revision=unit.source_revision,
        )
    else:
        span = SourceSpan.from_text(
            document_id=unit.document_id,
            raw_text=source.text,
            start_offset=start,
            end_offset=end,
            source_revision=unit.source_revision,
        )
    claim = CapsuleClaim.create(
        text="Alpha claim",
        modality=ClaimModality.OBSERVATION,
        source_spans=(span,),
        extraction_confidence=1.0,
    )
    return KnowledgeCapsule.create(
        source_document_id=unit.document_id,
        essence="Alpha claim is present.",
        claims=(claim,),
        reader_id="reader",
        reader_version="1",
        coverage_score=0.5,
    )


def test_builder_accepts_source_with_derived_revision() -> None:
    source, unit, plan_id = _plan_without_explicit_revision()
    capsule = _capsule(
        source,
        unit,
        coordinate_space=SpanCoordinateSpace.UNIT_LOCAL,
    )

    card = SectionCardBuilder().build(
        source,
        unit,
        ReaderResult.success(capsule),
        plan_id=plan_id,
        coordinate_space=SpanCoordinateSpace.UNIT_LOCAL,
    )

    assert card.source_revision.startswith("sha256:")
    assert card.source_revision == unit.source_revision


def test_card_identity_is_independent_of_input_coordinate_space() -> None:
    source, unit, plan_id = _plan_without_explicit_revision()
    local_capsule = _capsule(
        source,
        unit,
        coordinate_space=SpanCoordinateSpace.UNIT_LOCAL,
    )
    absolute_capsule = _capsule(
        source,
        unit,
        coordinate_space=SpanCoordinateSpace.DOCUMENT_ABSOLUTE,
    )
    builder = SectionCardBuilder()

    local_card = builder.build(
        source,
        unit,
        ReaderResult.success(local_capsule),
        plan_id=plan_id,
        coordinate_space=SpanCoordinateSpace.UNIT_LOCAL,
    )
    absolute_card = builder.build(
        source,
        unit,
        ReaderResult.success(absolute_capsule),
        plan_id=plan_id,
        coordinate_space=SpanCoordinateSpace.DOCUMENT_ABSOLUTE,
    )

    assert local_card.claims[0].claim == absolute_card.claims[0].claim
    assert local_card.card_id == absolute_card.card_id
    assert local_card.build_receipt.receipt_id != absolute_card.build_receipt.receipt_id


def test_forged_interpretation_identity_is_rejected() -> None:
    source, unit, _ = _plan_without_explicit_revision()
    span = SourceSpan.from_text(
        document_id=unit.document_id,
        raw_text=source.text,
        start_offset=0,
        end_offset=len("Alpha claim"),
        source_revision=unit.source_revision,
    )

    with pytest.raises(SectionCardError, match="interpretation_id"):
        SectionCardInterpretation(
            interpretation_id="forged",
            kind=InterpretationKind.ARGUMENT,
            text="An inferred argument.",
            supporting_spans=(span,),
            inference_reason="Test inference.",
        )


def test_forged_card_and_receipt_content_are_rejected() -> None:
    source, unit, plan_id = _plan_without_explicit_revision()
    capsule = _capsule(
        source,
        unit,
        coordinate_space=SpanCoordinateSpace.UNIT_LOCAL,
    )
    card = SectionCardBuilder().build(
        source,
        unit,
        ReaderResult.success(capsule),
        plan_id=plan_id,
        coordinate_space=SpanCoordinateSpace.UNIT_LOCAL,
    )

    with pytest.raises(SectionCardError, match="receipt_id"):
        replace(
            card.build_receipt,
            referenced_source_chars=card.build_receipt.referenced_source_chars - 1,
        )

    with pytest.raises(SectionCardError, match="card_id"):
        replace(card, local_essence="Changed without changing identity.")
