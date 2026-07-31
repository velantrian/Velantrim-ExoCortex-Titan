from hashlib import sha256

import pytest

from core.document_structure import (
    DeterministicDocumentStructureParser,
    DocumentStructureFormat,
)
from core.hierarchical_section_planner import (
    HierarchicalSectionPlanner,
    SectionPlanningBudget,
    SectionPlanningError,
    UnitBoundaryKind,
)
from core.reader_core_contracts import (
    ContentKind,
    DocumentSection,
    DocumentStructureMap,
    READER_CORE_SCHEMA_VERSION,
)
from core.semantic_reader import RawSource


def _plain_structure(source: RawSource) -> DocumentStructureMap:
    return DeterministicDocumentStructureParser().parse(
        source,
        document_format=DocumentStructureFormat.PLAIN_TEXT,
    )


def _markdown_structure(source: RawSource) -> DocumentStructureMap:
    return DeterministicDocumentStructureParser().parse(
        source,
        document_format=DocumentStructureFormat.MARKDOWN,
    )


def test_planner_partitions_source_without_overlap_and_prefers_paragraphs() -> None:
    text = (
        "Alpha sentence one. Alpha sentence two.\n\n"
        "Beta sentence one. Beta sentence two.\n\n"
        "Gamma sentence one. Gamma sentence two."
    )
    source = RawSource(document_id="doc", text=text, source_revision="rev")
    plan = HierarchicalSectionPlanner().plan(
        source,
        _plain_structure(source),
        budget=SectionPlanningBudget(
            max_unit_chars=55,
            min_unit_chars=15,
            boundary_search_chars=40,
        ),
    )

    assert plan.units[0].boundary_kind is UnitBoundaryKind.PARAGRAPH
    assert text[plan.units[0].start_offset : plan.units[0].end_offset].endswith(
        "\n\n"
    )
    assert plan.units[0].start_offset == 0
    assert plan.units[-1].end_offset == len(text)
    for previous, current in zip(plan.units, plan.units[1:]):
        assert previous.end_offset == current.start_offset
    assert all(unit.char_count <= plan.budget.max_unit_chars for unit in plan.units)
    assert all(unit.source_span.verify(text) for unit in plan.units)


def test_unbroken_text_emits_forced_continuation_receipts() -> None:
    text = "x" * 65
    source = RawSource(document_id="doc", text=text, source_revision="rev")
    plan = HierarchicalSectionPlanner().plan(
        source,
        _plain_structure(source),
        budget=SectionPlanningBudget(
            max_unit_chars=20,
            min_unit_chars=10,
            boundary_search_chars=10,
        ),
    )

    assert [unit.char_count for unit in plan.units] == [20, 20, 20, 5]
    assert [unit.boundary_kind for unit in plan.units] == [
        UnitBoundaryKind.HARD_LIMIT,
        UnitBoundaryKind.HARD_LIMIT,
        UnitBoundaryKind.HARD_LIMIT,
        UnitBoundaryKind.SECTION_END,
    ]
    assert len(plan.continuation_receipts) == 3
    assert all(receipt.forced_split for receipt in plan.continuation_receipts)
    assert "forced_hard_limit_split" in plan.warnings
    for index, receipt in enumerate(plan.continuation_receipts):
        assert receipt.from_unit_id == plan.units[index].unit_id
        assert receipt.to_unit_id == plan.units[index + 1].unit_id
        assert receipt.split_offset == plan.units[index].end_offset


def test_planner_preserves_section_hierarchy_and_continuation_links() -> None:
    text = (
        "# Root\n"
        "Root body sentence one. Root body sentence two. Root body sentence three.\n\n"
        "## Child\n"
        "Child body sentence one. Child body sentence two. Child body sentence three."
    )
    source = RawSource(document_id="markdown", text=text, source_revision="rev")
    structure = _markdown_structure(source)
    plan = HierarchicalSectionPlanner().plan(
        source,
        structure,
        budget=SectionPlanningBudget(
            max_unit_chars=45,
            min_unit_chars=15,
            boundary_search_chars=30,
        ),
    )

    child_section = structure.sections[1]
    child_units = [unit for unit in plan.units if unit.section_id == child_section.section_id]
    assert child_units
    assert all(
        unit.parent_section_id == child_section.parent_section_id
        for unit in child_units
    )
    if len(child_units) > 1:
        assert child_units[0].continuation_to_unit_id == child_units[1].unit_id
        assert child_units[1].continuation_from_unit_id == child_units[0].unit_id


def test_atomic_oversize_section_is_preserved_and_reported() -> None:
    text = "T" * 80
    source = RawSource(document_id="table-doc", text=text, source_revision="rev")
    section = DocumentSection.create(
        document_id="table-doc",
        source_revision="rev",
        order_index=0,
        heading="Table 1",
        level=1,
        start_offset=0,
        end_offset=len(text),
        content_kind=ContentKind.TABLE,
    )
    structure = DocumentStructureMap(
        map_id="table-map",
        schema_version=READER_CORE_SCHEMA_VERSION,
        document_id="table-doc",
        source_revision="rev",
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

    assert len(plan.units) == 1
    assert plan.units[0].char_count == len(text)
    assert plan.units[0].boundary_kind is UnitBoundaryKind.ATOMIC_OVERSIZE
    assert plan.units[0].warnings == ("atomic_section_exceeds_budget",)
    assert plan.continuation_receipts == ()
    assert "atomic_section_exceeds_budget" in plan.warnings


def test_plan_identity_is_deterministic() -> None:
    text = "Sentence one. Sentence two. Sentence three. Sentence four."
    source = RawSource(document_id="doc", text=text, source_revision="rev")
    structure = _plain_structure(source)
    planner = HierarchicalSectionPlanner()
    budget = SectionPlanningBudget(
        max_unit_chars=25,
        min_unit_chars=10,
        boundary_search_chars=15,
    )

    first = planner.plan(source, structure, budget=budget)
    second = planner.plan(source, structure, budget=budget)

    assert first.plan_id == second.plan_id
    assert [unit.unit_id for unit in first.units] == [
        unit.unit_id for unit in second.units
    ]
    assert [receipt.receipt_id for receipt in first.continuation_receipts] == [
        receipt.receipt_id for receipt in second.continuation_receipts
    ]


def test_source_and_structure_hash_mismatch_is_rejected() -> None:
    original = RawSource(document_id="doc", text="Original text", source_revision="rev")
    structure = _plain_structure(original)
    changed = RawSource(document_id="doc", text="Changed text", source_revision="rev")

    with pytest.raises(SectionPlanningError, match="content hash"):
        HierarchicalSectionPlanner().plan(changed, structure)


def test_invalid_budget_is_rejected() -> None:
    with pytest.raises(SectionPlanningError, match="cannot exceed"):
        SectionPlanningBudget(
            max_unit_chars=10,
            min_unit_chars=11,
        )
