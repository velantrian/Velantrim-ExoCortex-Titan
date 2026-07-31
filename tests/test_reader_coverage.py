from dataclasses import replace
from hashlib import sha256
import re

import pytest

from core.critical_exceptions import DeterministicCriticalExceptionScanner
from core.document_structure import (
    DeterministicDocumentStructureParser,
    DocumentStructureFormat,
)
from core.hierarchical_section_planner import (
    HierarchicalSectionPlan,
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
from core.reader_core_contracts import (
    ContentKind,
    CoverageAxis,
    DocumentSection,
    DocumentStructureMap,
    READER_CORE_SCHEMA_VERSION,
)
from core.reader_coverage import CoverageMapBuilder, CoverageMapError
from core.section_card import SectionCard, SectionCardBuilder, SpanCoordinateSpace
from core.semantic_reader import (
    RawSource,
    ReaderResult,
    ReaderWarning,
)


def _text_pipeline() -> tuple[RawSource, DocumentStructureMap, HierarchicalSectionPlan]:
    text = (
        "Alpha rule applies to ordinary data. However, secrets are excluded.\n\n"
        "Beta rule applies only if an operator approves the request."
    )
    source = RawSource(
        document_id="coverage-doc",
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
            max_unit_chars=72,
            min_unit_chars=20,
            boundary_search_chars=50,
        ),
    )
    assert len(plan.units) == 2
    return source, structure, plan


def _card_for_unit(
    source: RawSource,
    plan: HierarchicalSectionPlan,
    unit: ReadingUnit,
    *,
    partial: bool = False,
) -> SectionCard:
    unit_text = source.text[unit.start_offset : unit.end_offset]
    match = re.search(r"[A-Za-z]+", unit_text)
    assert match is not None
    claim_text = match.group(0)
    span = SourceSpan.from_text(
        document_id=unit.document_id,
        raw_text=unit_text,
        start_offset=match.start(),
        end_offset=match.end(),
        source_revision=unit.source_revision,
    )
    claim = CapsuleClaim.create(
        text=claim_text,
        modality=ClaimModality.OBSERVATION,
        source_spans=(span,),
        extraction_confidence=1.0,
    )
    capsule = KnowledgeCapsule.create(
        source_document_id=unit.document_id,
        essence=f"Local note for {claim_text}.",
        claims=(claim,),
        reader_id="coverage-reader",
        reader_version="1",
        coverage_score=0.25,
    )
    result = ReaderResult.success(capsule)
    if partial:
        result = ReaderResult.partial(
            capsule,
            warnings=(
                ReaderWarning(
                    code="reader_partial_fixture",
                    safe_message="Fixture marks this result partial.",
                ),
            ),
        )
    return SectionCardBuilder().build(
        source,
        unit,
        result,
        plan_id=plan.plan_id,
        coordinate_space=SpanCoordinateSpace.UNIT_LOCAL,
    )


def test_coverage_axes_are_independent_and_have_explicit_denominators() -> None:
    source, structure, plan = _text_pipeline()
    first_card = _card_for_unit(source, plan, plan.units[0])
    first_scan = DeterministicCriticalExceptionScanner().scan(source, first_card)

    coverage = CoverageMapBuilder().build(
        source,
        structure,
        plan,
        cards=(first_card,),
        exception_scans=(first_scan,),
    )

    structural = coverage.axis(CoverageAxis.STRUCTURAL)
    claim = coverage.axis(CoverageAxis.CLAIM)
    exception = coverage.axis(CoverageAxis.EXCEPTION)
    relation = coverage.axis(CoverageAxis.RELATION)
    table_figure = coverage.axis(CoverageAxis.TABLE_FIGURE)
    validation = coverage.axis(CoverageAxis.VALIDATION)

    assert structural.ratio == 0.5
    assert structural.unresolved_ids == (plan.units[1].unit_id,)
    assert exception.ratio == 0.5
    assert exception.unresolved_ids == (plan.units[1].unit_id,)
    assert claim.denominator_count == sum(
        1 for character in source.text if not character.isspace()
    )
    assert claim.processed_count > 0
    assert claim.ratio is not None and 0.0 < claim.ratio < 1.0
    assert relation.denominator_count is None
    assert relation.ratio is None
    assert table_figure.denominator_count == 0
    assert table_figure.ratio is None
    assert validation.processed_count == validation.denominator_count == 1
    assert validation.ratio == 1.0
    assert not hasattr(coverage, "global_score")
    assert "relation_axis_unavailable_until_rdr_06" in coverage.warnings

    unresolved = {
        (region.axis, region.unit_id, region.reason_code)
        for region in coverage.unresolved_regions
    }
    assert (
        CoverageAxis.STRUCTURAL,
        plan.units[1].unit_id,
        "missing_section_card",
    ) in unresolved
    assert (
        CoverageAxis.CLAIM,
        plan.units[1].unit_id,
        "unread_unit_has_no_claim_provenance",
    ) in unresolved
    assert (
        CoverageAxis.EXCEPTION,
        plan.units[1].unit_id,
        "exception_scan_missing",
    ) in unresolved


def test_complete_cards_and_scans_produce_complete_process_axes() -> None:
    source, structure, plan = _text_pipeline()
    cards = tuple(_card_for_unit(source, plan, unit) for unit in plan.units)
    scans = tuple(
        DeterministicCriticalExceptionScanner().scan(source, card)
        for card in cards
    )

    coverage = CoverageMapBuilder().build(
        source,
        structure,
        plan,
        cards=cards,
        exception_scans=scans,
    )

    assert coverage.axis(CoverageAxis.STRUCTURAL).ratio == 1.0
    assert coverage.axis(CoverageAxis.EXCEPTION).ratio == 1.0
    assert coverage.axis(CoverageAxis.VALIDATION).ratio == 1.0
    assert coverage.axis(CoverageAxis.RELATION).ratio is None


def test_coverage_identity_is_deterministic_for_equivalent_input_order() -> None:
    source, structure, plan = _text_pipeline()
    cards = tuple(_card_for_unit(source, plan, unit) for unit in plan.units)
    scans = tuple(
        DeterministicCriticalExceptionScanner().scan(source, card)
        for card in cards
    )
    builder = CoverageMapBuilder()

    first = builder.build(
        source,
        structure,
        plan,
        cards=cards,
        exception_scans=scans,
    )
    second = builder.build(
        source,
        structure,
        plan,
        cards=tuple(reversed(cards)),
        exception_scans=tuple(reversed(scans)),
    )

    assert first.coverage_map_id == second.coverage_map_id
    assert first == second


def test_partial_card_creates_validation_unresolved_region() -> None:
    source, structure, plan = _text_pipeline()
    card = _card_for_unit(source, plan, plan.units[0], partial=True)
    scan = DeterministicCriticalExceptionScanner().scan(source, card)

    coverage = CoverageMapBuilder().build(
        source,
        structure,
        plan,
        cards=(card,),
        exception_scans=(scan,),
    )

    assert "partial_reader_results_present" in coverage.warnings
    assert any(
        region.axis is CoverageAxis.VALIDATION
        and region.unit_id == card.unit_id
        and region.reason_code == "partial_reader_result"
        for region in coverage.unresolved_regions
    )


def test_atomic_oversize_asset_is_reported_without_being_split() -> None:
    text = "T" * 80
    source = RawSource(
        document_id="asset-doc",
        text=text,
        source_revision="revision-1",
    )
    section = DocumentSection.create(
        document_id=source.document_id,
        source_revision=source.source_revision,
        order_index=0,
        heading="Table 1",
        level=1,
        start_offset=0,
        end_offset=len(text),
        content_kind=ContentKind.TABLE,
    )
    structure = DocumentStructureMap(
        map_id="asset-map",
        schema_version=READER_CORE_SCHEMA_VERSION,
        document_id=source.document_id,
        source_revision=source.source_revision,
        parser_id="fixture",
        parser_version="1",
        content_hash=sha256(text.encode("utf-8")).hexdigest(),
        sections=(section,),
    )
    plan = HierarchicalSectionPlanner().plan(
        source,
        structure,
        budget=SectionPlanningBudget(
            max_unit_chars=20,
            min_unit_chars=10,
            boundary_search_chars=10,
        ),
    )

    coverage = CoverageMapBuilder().build(source, structure, plan)

    table_axis = coverage.axis(CoverageAxis.TABLE_FIGURE)
    assert table_axis.processed_count == 0
    assert table_axis.denominator_count == 1
    assert table_axis.ratio == 0.0
    assert len(coverage.unsupported_assets) == 1
    asset = coverage.unsupported_assets[0]
    assert asset.unit_id == plan.units[0].unit_id
    assert asset.content_kind is ContentKind.TABLE
    assert asset.reason_code == "atomic_section_exceeds_budget"
    assert asset.source_span.verify(source.text)
    assert "unsupported_atomic_assets_present" in coverage.warnings


def test_exception_scan_without_matching_card_is_rejected() -> None:
    source, structure, plan = _text_pipeline()
    card = _card_for_unit(source, plan, plan.units[0])
    scan = DeterministicCriticalExceptionScanner().scan(source, card)

    with pytest.raises(CoverageMapError, match="requires a known SectionCard"):
        CoverageMapBuilder().build(
            source,
            structure,
            plan,
            exception_scans=(scan,),
        )


def test_coverage_content_cannot_change_under_a_stale_id() -> None:
    source, structure, plan = _text_pipeline()
    coverage = CoverageMapBuilder().build(source, structure, plan)

    with pytest.raises(CoverageMapError, match="coverage_map_id"):
        replace(
            coverage,
            warnings=(*coverage.warnings, "forged_warning"),
        )
