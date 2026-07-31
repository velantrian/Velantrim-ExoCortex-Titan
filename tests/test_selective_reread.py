from dataclasses import replace
from hashlib import sha256
import re

import pytest

from core.critical_exceptions import (
    CriticalExceptionCandidate,
    DeterministicCriticalExceptionScanner,
)
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
    DocumentSection,
    DocumentStructureMap,
    READER_CORE_SCHEMA_VERSION,
)
from core.reader_coverage import CoverageMap, CoverageMapBuilder
from core.section_card import SectionCard, SectionCardBuilder, SpanCoordinateSpace
from core.selective_reread import (
    ReReadAction,
    ReReadDeferralReason,
    ReReadPriority,
    ReReadTrigger,
    SelectiveReReadBudget,
    SelectiveReReadError,
    SelectiveReReadPlanner,
)
from core.semantic_reader import (
    RawSource,
    ReaderMode,
    ReaderResult,
    ReaderWarning,
)


def _two_unit_pipeline() -> tuple[
    RawSource,
    DocumentStructureMap,
    HierarchicalSectionPlan,
]:
    text = (
        "Alpha rule covers ordinary data and records a local receipt.\n\n"
        "Beta rule covers archived data and records a second local receipt."
    )
    source = RawSource(
        document_id="reread-doc",
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
            max_unit_chars=70,
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
    claim_text: str | None = None,
    partial: bool = False,
) -> SectionCard:
    unit_text = source.text[unit.start_offset : unit.end_offset]
    if claim_text is None:
        match = re.search(r"[A-Za-z]+", unit_text)
        assert match is not None
        claim_text = match.group(0)
        local_start = match.start()
    else:
        local_start = unit_text.index(claim_text)
    span = SourceSpan.from_text(
        document_id=unit.document_id,
        raw_text=unit_text,
        start_offset=local_start,
        end_offset=local_start + len(claim_text),
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
        reader_id="reread-fixture-reader",
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


def _coverage(
    source: RawSource,
    structure: DocumentStructureMap,
    plan: HierarchicalSectionPlan,
    cards: tuple[SectionCard, ...],
) -> tuple[CoverageMap, tuple[CriticalExceptionCandidate, ...]]:
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
    candidates = tuple(
        candidate for scan in scans for candidate in scan.candidates
    )
    return coverage, candidates


def test_missing_unit_reasons_are_deduplicated_into_one_targeted_task() -> None:
    source, structure, plan = _two_unit_pipeline()
    first_card = _card_for_unit(source, plan, plan.units[0])
    coverage, candidates = _coverage(
        source,
        structure,
        plan,
        (first_card,),
    )

    reread = SelectiveReReadPlanner().plan(
        source,
        plan,
        coverage,
        exception_candidates=candidates,
    )

    assert len(reread.tasks) == 1
    assert reread.deferred_items == ()
    task = reread.tasks[0]
    assert task.unit_id == plan.units[1].unit_id
    assert task.priority is ReReadPriority.HIGH
    assert task.actions == (
        ReReadAction.READ_UNIT,
        ReReadAction.RESCAN_EXCEPTIONS,
    )
    assert task.trigger_codes == (
        ReReadTrigger.MISSING_SECTION_CARD,
        ReReadTrigger.CLAIM_PROVENANCE_MISSING,
        ReReadTrigger.EXCEPTION_SCAN_MISSING,
    )
    assert task.reader_mode is ReaderMode.STANDARD
    assert len(task.evidence_refs) == 3
    assert task.source_span == plan.units[1].source_span
    assert task.queue_index == 0
    assert reread.triggered_unit_ids == (plan.units[1].unit_id,)
    assert reread.total_queued_chars == plan.units[1].char_count


def test_partial_reader_result_requests_deep_reread_only_for_that_unit() -> None:
    source, structure, plan = _two_unit_pipeline()
    first_card = _card_for_unit(
        source,
        plan,
        plan.units[0],
        partial=True,
    )
    second_card = _card_for_unit(source, plan, plan.units[1])
    coverage, candidates = _coverage(
        source,
        structure,
        plan,
        (first_card, second_card),
    )

    reread = SelectiveReReadPlanner().plan(
        source,
        plan,
        coverage,
        exception_candidates=candidates,
    )

    assert len(reread.tasks) == 1
    task = reread.tasks[0]
    assert task.unit_id == first_card.unit_id
    assert task.actions == (ReReadAction.DEEPEN_UNIT,)
    assert task.trigger_codes == (ReReadTrigger.PARTIAL_READER_RESULT,)
    assert task.reader_mode is ReaderMode.DEEP
    assert task.priority is ReReadPriority.HIGH


def test_unresolved_exception_target_has_critical_priority() -> None:
    text = "Unless approved, operation stops. A later claim appears here."
    source = RawSource(
        document_id="exception-reread-doc",
        text=text,
        source_revision="revision-1",
    )
    structure = DeterministicDocumentStructureParser().parse(
        source,
        document_format=DocumentStructureFormat.PLAIN_TEXT,
    )
    plan = HierarchicalSectionPlanner().plan(source, structure)
    card = _card_for_unit(
        source,
        plan,
        plan.units[0],
        claim_text="A later claim",
    )
    coverage, candidates = _coverage(source, structure, plan, (card,))
    assert len(candidates) == 1
    assert candidates[0].target_claim_refs == ()

    reread = SelectiveReReadPlanner().plan(
        source,
        plan,
        coverage,
        exception_candidates=candidates,
    )

    assert len(reread.tasks) == 1
    task = reread.tasks[0]
    assert task.priority is ReReadPriority.CRITICAL
    assert task.actions == (ReReadAction.RESOLVE_EXCEPTION_TARGET,)
    assert task.trigger_codes == (
        ReReadTrigger.UNRESOLVED_EXCEPTION_TARGET,
    )
    assert task.evidence_refs == (candidates[0].candidate_id,)
    assert task.reader_mode is None


def test_atomic_oversize_work_is_explicitly_deferred_by_task_char_limit() -> None:
    text = "T" * 80
    source = RawSource(
        document_id="atomic-reread-doc",
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
        map_id="atomic-structure-map",
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

    reread = SelectiveReReadPlanner().plan(
        source,
        plan,
        coverage,
        budget=SelectiveReReadBudget(
            max_tasks=4,
            max_total_chars=100,
            max_task_chars=20,
            max_tasks_per_section=4,
        ),
    )

    assert reread.tasks == ()
    assert len(reread.deferred_items) == 1
    item = reread.deferred_items[0]
    assert item.priority is ReReadPriority.CRITICAL
    assert item.deferral_reason is ReReadDeferralReason.TASK_CHAR_LIMIT
    assert item.actions == (
        ReReadAction.READ_UNIT,
        ReReadAction.RESCAN_EXCEPTIONS,
        ReReadAction.INSPECT_ATOMIC_ASSET,
    )
    assert ReReadTrigger.ATOMIC_ASSET_EXCEEDS_BUDGET in item.trigger_codes
    assert item.reader_mode is ReaderMode.STANDARD
    assert reread.triggered_unit_ids == (plan.units[0].unit_id,)
    assert "reread_work_deferred_by_budget" in reread.warnings


def test_section_budget_defers_extra_units_without_losing_triggers() -> None:
    text = (
        "Alpha paragraph has enough text for one bounded reading unit.\n\n"
        "Beta paragraph has enough text for another bounded reading unit.\n\n"
        "Gamma paragraph has enough text for a final bounded reading unit."
    )
    source = RawSource(
        document_id="section-budget-doc",
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
            max_unit_chars=70,
            min_unit_chars=20,
            boundary_search_chars=50,
        ),
    )
    assert len(plan.units) == 3
    coverage = CoverageMapBuilder().build(source, structure, plan)

    reread = SelectiveReReadPlanner().plan(
        source,
        plan,
        coverage,
        budget=SelectiveReReadBudget(
            max_tasks=10,
            max_total_chars=1_000,
            max_task_chars=100,
            max_tasks_per_section=1,
        ),
    )

    assert len(reread.tasks) == 1
    assert len(reread.deferred_items) == 2
    assert all(
        item.deferral_reason is ReReadDeferralReason.SECTION_TASK_LIMIT
        for item in reread.deferred_items
    )
    represented = {
        task.unit_id for task in reread.tasks
    } | {item.unit_id for item in reread.deferred_items}
    assert represented == set(reread.triggered_unit_ids) == {
        unit.unit_id for unit in plan.units
    }


def test_complete_processing_does_not_create_a_full_document_reread() -> None:
    source, structure, plan = _two_unit_pipeline()
    cards = tuple(_card_for_unit(source, plan, unit) for unit in plan.units)
    coverage, candidates = _coverage(source, structure, plan, cards)

    reread = SelectiveReReadPlanner().plan(
        source,
        plan,
        coverage,
        exception_candidates=candidates,
    )

    assert reread.tasks == ()
    assert reread.deferred_items == ()
    assert reread.triggered_unit_ids == ()
    assert reread.total_queued_chars == 0
    assert reread.warnings == ("no_reread_triggers",)


def test_candidate_set_must_exactly_match_coverage_map() -> None:
    text = "Unless approved, operation stops. A later claim appears here."
    source = RawSource(
        document_id="candidate-set-doc",
        text=text,
        source_revision="revision-1",
    )
    structure = DeterministicDocumentStructureParser().parse(
        source,
        document_format=DocumentStructureFormat.PLAIN_TEXT,
    )
    plan = HierarchicalSectionPlanner().plan(source, structure)
    card = _card_for_unit(
        source,
        plan,
        plan.units[0],
        claim_text="A later claim",
    )
    coverage, candidates = _coverage(source, structure, plan, (card,))
    assert candidates

    with pytest.raises(SelectiveReReadError, match="exactly match"):
        SelectiveReReadPlanner().plan(source, plan, coverage)


def test_stale_source_revision_is_rejected() -> None:
    source, structure, plan = _two_unit_pipeline()
    coverage = CoverageMapBuilder().build(source, structure, plan)
    stale = RawSource(
        document_id=source.document_id,
        text=source.text,
        source_revision="revision-2",
    )

    with pytest.raises(SelectiveReReadError, match="revision"):
        SelectiveReReadPlanner().plan(stale, plan, coverage)


def test_task_and_plan_content_cannot_change_under_stale_ids() -> None:
    source, structure, plan = _two_unit_pipeline()
    coverage = CoverageMapBuilder().build(source, structure, plan)
    reread = SelectiveReReadPlanner().plan(source, plan, coverage)
    task = reread.tasks[0]

    with pytest.raises(SelectiveReReadError, match="task_id"):
        replace(task, priority=ReReadPriority.CRITICAL)

    with pytest.raises(SelectiveReReadError, match="reread_plan_id"):
        replace(
            reread,
            warnings=(*reread.warnings, "forged_warning"),
        )
