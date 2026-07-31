from dataclasses import replace
import re

import pytest

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
from core.reader_core_contracts import SessionState
from core.reading_session import (
    ReadingSessionBudget,
    ReadingSessionBudgetExceeded,
    ReadingSessionError,
    ReadingSessionManager,
    ReadingSessionUsage,
    SessionArtifactKind,
    SessionEventKind,
)
from core.section_card import SectionCard, SectionCardBuilder, SpanCoordinateSpace
from core.semantic_reader import RawSource, ReaderResult


def _plan_for_text(
    text: str,
    *,
    document_id: str = "session-doc",
    revision: str = "revision-1",
) -> tuple[RawSource, HierarchicalSectionPlan]:
    source = RawSource(
        document_id=document_id,
        text=text,
        source_revision=revision,
    )
    structure = DeterministicDocumentStructureParser().parse(
        source,
        document_format=DocumentStructureFormat.PLAIN_TEXT,
    )
    plan = HierarchicalSectionPlanner().plan(
        source,
        structure,
        budget=SectionPlanningBudget(
            max_unit_chars=80,
            min_unit_chars=20,
            boundary_search_chars=60,
        ),
    )
    return source, plan


def _two_unit_pipeline() -> tuple[RawSource, HierarchicalSectionPlan]:
    text = (
        "Alpha rule covers ordinary records and creates a local receipt.\n\n"
        "Beta rule covers archived records and creates another receipt."
    )
    source, plan = _plan_for_text(text)
    assert len(plan.units) == 2
    return source, plan


def _card_for_unit(
    source: RawSource,
    plan: HierarchicalSectionPlan,
    unit: ReadingUnit,
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
        reader_id="session-fixture-reader",
        reader_version="1",
        coverage_score=0.5,
    )
    return SectionCardBuilder().build(
        source,
        unit,
        ReaderResult.success(capsule),
        plan_id=plan.plan_id,
        coordinate_space=SpanCoordinateSpace.UNIT_LOCAL,
    )


def _created_session(
    plan: HierarchicalSectionPlan,
    *,
    budget: ReadingSessionBudget | None = None,
):
    return ReadingSessionManager().create(
        plan,
        session_key="stable-session-key",
        resource_budget=budget,
        policy_snapshot_id="policy-snapshot-1",
        policy_version="policy-v1",
        capability_lease_ref="capability-lease-ref",
    )


def test_create_is_idempotent_and_partitions_all_units_as_pending() -> None:
    _, plan = _two_unit_pipeline()
    first = _created_session(plan)
    second = _created_session(plan)

    assert first.session_id == second.session_id
    assert first.snapshot_id == second.snapshot_id
    assert first.state is SessionState.CREATED
    assert first.pending_unit_ids == tuple(unit.unit_id for unit in plan.units)
    assert first.completed_unit_ids == ()
    assert first.unit_artifacts == ()
    assert first.receipts[0].event_kind is SessionEventKind.CREATED
    assert first.resource_usage.receipts_emitted == 1


def test_pause_checkpoint_restore_resume_and_complete_flow() -> None:
    source, plan = _two_unit_pipeline()
    manager = ReadingSessionManager()
    session = _created_session(plan)
    session = manager.claim(
        session,
        runner_id="runner-a",
        expires_at_ms=100,
        now_ms=0,
    )
    first_lease = session.active_lease
    assert first_lease is not None
    session = manager.start(session, first_lease, now_ms=1)
    session = manager.pause(
        session,
        first_lease,
        reason_code="operator_pause",
        now_ms=2,
    )
    assert session.state is SessionState.PAUSED
    assert session.active_lease is None

    checkpoint = manager.checkpoint(session)
    restored = checkpoint.restore()
    assert restored == session
    assert restored.snapshot_id == session.snapshot_id

    session = manager.claim(
        restored,
        runner_id="runner-b",
        expires_at_ms=200,
        now_ms=3,
    )
    second_lease = session.active_lease
    assert second_lease is not None
    assert second_lease.generation == 2
    session = manager.start(session, second_lease, now_ms=4)
    assert session.receipts[-1].event_kind is SessionEventKind.RESUMED

    cards = tuple(_card_for_unit(source, plan, unit) for unit in plan.units)
    session = manager.record_cards(
        session,
        second_lease,
        cards,
        usage_delta=ReadingSessionUsage(
            processed_units=2,
            source_chars=sum(unit.char_count for unit in plan.units),
            wall_time_ms=25,
        ),
        now_ms=5,
    )
    assert session.pending_unit_ids == ()
    assert session.completed_unit_ids == tuple(unit.unit_id for unit in plan.units)
    assert all(
        artifact.kind is SessionArtifactKind.CURRENT_CARD
        for artifact in session.unit_artifacts
    )

    session = manager.attach_artifacts(
        session,
        second_lease,
        coverage_map_id="coverage-map-1",
        relation_set_id="relation-set-1",
        unresolved_question_refs=("question-1",),
        now_ms=6,
    )
    session = manager.complete(session, second_lease, now_ms=7)
    assert session.state is SessionState.COMPLETED
    assert session.active_lease is None
    assert session.coverage_map_id == "coverage-map-1"
    assert session.resource_usage.processed_units == 2
    assert session.resource_usage.receipts_emitted == len(session.receipts)


def test_expired_owner_is_fenced_after_a_new_claim_generation() -> None:
    _, plan = _two_unit_pipeline()
    manager = ReadingSessionManager()
    session = _created_session(plan)
    session = manager.claim(
        session,
        runner_id="runner-a",
        expires_at_ms=10,
        now_ms=0,
    )
    stale_lease = session.active_lease
    assert stale_lease is not None

    session = manager.claim(
        session,
        runner_id="runner-b",
        expires_at_ms=30,
        now_ms=11,
    )
    live_lease = session.active_lease
    assert live_lease is not None
    assert live_lease.generation == stale_lease.generation + 1

    with pytest.raises(ReadingSessionError, match="does not own"):
        manager.start(session, stale_lease, now_ms=12)

    started = manager.start(session, live_lease, now_ms=12)
    assert started.state is SessionState.READING


def test_resource_budget_exhaustion_is_fail_closed() -> None:
    source, plan = _two_unit_pipeline()
    manager = ReadingSessionManager()
    session = _created_session(
        plan,
        budget=ReadingSessionBudget(
            max_processed_units=1,
            max_source_chars=10_000,
            max_model_tokens=100,
            max_wall_time_ms=1_000,
            max_receipts=100,
        ),
    )
    session = manager.claim(
        session,
        runner_id="runner",
        expires_at_ms=100,
        now_ms=0,
    )
    lease = session.active_lease
    assert lease is not None
    session = manager.start(session, lease, now_ms=1)
    cards = tuple(_card_for_unit(source, plan, unit) for unit in plan.units)
    before = session

    with pytest.raises(ReadingSessionBudgetExceeded, match="processed units"):
        manager.record_cards(
            session,
            lease,
            cards,
            usage_delta=ReadingSessionUsage(
                processed_units=2,
                source_chars=sum(unit.char_count for unit in plan.units),
            ),
            now_ms=2,
        )

    assert session == before
    assert session.completed_unit_ids == ()


def test_completion_requires_no_pending_units_and_a_coverage_map() -> None:
    _, plan = _two_unit_pipeline()
    manager = ReadingSessionManager()
    session = _created_session(plan)
    session = manager.claim(
        session,
        runner_id="runner",
        expires_at_ms=100,
        now_ms=0,
    )
    lease = session.active_lease
    assert lease is not None
    session = manager.start(session, lease, now_ms=1)

    with pytest.raises(ReadingSessionError, match="pending units"):
        manager.complete(session, lease, now_ms=2)


def test_snapshot_and_receipt_ids_are_self_verifying() -> None:
    _, plan = _two_unit_pipeline()
    session = _created_session(plan)

    with pytest.raises(ReadingSessionError, match="snapshot_id"):
        replace(session, snapshot_id="forged")

    with pytest.raises(ReadingSessionError, match="receipt_id"):
        replace(session.receipts[0], reason_code="forged")


def test_revision_reuse_keeps_only_unique_exact_text_units() -> None:
    old_text = (
        "Alpha section remains exactly stable across the new revision.\n\n"
        "Beta section changes materially in the replacement revision."
    )
    new_text = (
        "Alpha section remains exactly stable across the new revision.\n\n"
        "Gamma section now contains different replacement material."
    )
    old_source, old_plan = _plan_for_text(old_text, revision="revision-1")
    new_source, new_plan = _plan_for_text(new_text, revision="revision-2")
    assert len(old_plan.units) == len(new_plan.units) == 2

    manager = ReadingSessionManager()
    session = _created_session(old_plan)
    session = manager.claim(
        session,
        runner_id="runner-a",
        expires_at_ms=100,
        now_ms=0,
    )
    lease = session.active_lease
    assert lease is not None
    session = manager.start(session, lease, now_ms=1)
    cards = tuple(_card_for_unit(old_source, old_plan, unit) for unit in old_plan.units)
    session = manager.record_cards(
        session,
        lease,
        cards,
        usage_delta=ReadingSessionUsage(
            processed_units=2,
            source_chars=len(old_text),
        ),
        now_ms=2,
    )
    session = manager.mark_stale(
        session,
        lease,
        reason_code="source_revision_changed",
        now_ms=3,
    )

    reuse = manager.plan_revision_reuse(
        session,
        old_source,
        old_plan,
        new_source,
        new_plan,
    )
    assert len(reuse.pairs) == 1
    assert reuse.pairs[0].old_unit_id == old_plan.units[0].unit_id
    assert reuse.pairs[0].new_unit_id == new_plan.units[0].unit_id
    assert reuse.invalidated_old_unit_ids == (old_plan.units[1].unit_id,)
    assert reuse.pending_new_unit_ids == (new_plan.units[1].unit_id,)

    session = manager.claim(
        session,
        runner_id="runner-b",
        expires_at_ms=200,
        now_ms=4,
    )
    rebase_lease = session.active_lease
    assert rebase_lease is not None
    rebased = manager.rebase_revision(
        session,
        rebase_lease,
        new_plan,
        reuse,
        policy_snapshot_id="policy-snapshot-2",
        policy_version="policy-v2",
        now_ms=5,
    )
    assert rebased.state is SessionState.CREATED
    assert rebased.revision_generation == 1
    assert rebased.source_revision == "revision-2"
    assert rebased.completed_unit_ids == (new_plan.units[0].unit_id,)
    assert rebased.pending_unit_ids == (new_plan.units[1].unit_id,)
    assert rebased.unit_artifacts[0].kind is SessionArtifactKind.REUSED_CARD
    assert rebased.coverage_map_id is None
    assert rebased.relation_set_id is None


def test_ambiguous_identical_units_are_not_reused() -> None:
    paragraph = "Repeated section text is deliberately identical and long enough."
    old_text = f"{paragraph}\n\n{paragraph}"
    new_text = f"{paragraph}\n\n{paragraph}"
    old_source, old_plan = _plan_for_text(old_text, revision="revision-1")
    new_source, new_plan = _plan_for_text(new_text, revision="revision-2")
    assert len(old_plan.units) == len(new_plan.units) == 2

    manager = ReadingSessionManager()
    session = _created_session(old_plan)
    session = manager.claim(
        session,
        runner_id="runner",
        expires_at_ms=100,
        now_ms=0,
    )
    lease = session.active_lease
    assert lease is not None
    session = manager.start(session, lease, now_ms=1)
    cards = tuple(_card_for_unit(old_source, old_plan, unit) for unit in old_plan.units)
    session = manager.record_cards(
        session,
        lease,
        cards,
        usage_delta=ReadingSessionUsage(
            processed_units=2,
            source_chars=len(old_text),
        ),
        now_ms=2,
    )

    reuse = manager.plan_revision_reuse(
        session,
        old_source,
        old_plan,
        new_source,
        new_plan,
    )
    assert reuse.pairs == ()
    assert reuse.invalidated_old_unit_ids == tuple(
        unit.unit_id for unit in old_plan.units
    )
    assert reuse.pending_new_unit_ids == tuple(unit.unit_id for unit in new_plan.units)
    assert "ambiguous_identical_unit_text_not_reused" in reuse.warnings
