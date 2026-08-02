"""End-to-end replay and zero-tolerance hard-gate tests."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime

import pytest

from core.compute_controller import (
    ContextFreshness,
    ContinuityComputeSignals,
    decide_compute_path,
)
from core.context_pack import ContextPackBudget, ContextPackBuilder
from core.continuity.context_pack import ContinuityContextAssembler
from core.continuity.contracts import (
    ActorKind,
    ActorRef,
    AssertionRecord,
    OriginType,
    SubjectKind,
    SubjectRef,
)
from core.continuity.conversation_bridge import ConversationEpisode
from core.continuity.evaluation import (
    HardGate,
    ReplayEvaluationError,
    ReplayEvaluationReport,
    ShadowRunSnapshot,
    ShadowSafetyObservation,
)
from core.continuity.goal_open_loop import (
    GoalAttestation,
    GoalBasis,
    GoalProjector,
    GoalRecordSnapshot,
    OpenLoopKind,
    OpenLoopProjector,
    OpenLoopSignal,
)
from core.continuity.projection_working_memory_adapter import (
    ProjectionGatePolicy,
    ProjectionWorkingMemoryAdapter,
)
from core.continuity.state_reconciler import StateReconciler
from core.continuity.thread_weaver import ThreadWeaver
from core.continuity.working_memory_adapter import (
    ContinuityItemGatePolicy,
    ContinuityWorkingMemoryAdapter,
)
from core.conversation_consolidation import ConversationNotebook
from core.goal_stack import Goal
from core.knowledge_capsule import (
    CapsuleClaim,
    ClaimModality,
    KnowledgeCapsule,
    SourceSpan,
)
from core.working_memory_gate import (
    WorkingMemoryBudget,
    WorkingMemoryCandidate,
    WorkingMemoryGate,
)

NOW = datetime(2026, 8, 2, 12, 0, tzinfo=UTC)
USER = ActorRef("actor:user", ActorKind.HUMAN)
PROJECT = SubjectRef("project:titan", SubjectKind.PROJECT)


def _episode(
    chat_id: str,
    *,
    goal: str,
    related: list[str] | None = None,
    created_at: str,
) -> ConversationEpisode:
    return ConversationEpisode.from_notebook(
        ConversationNotebook(
            chat_id=chat_id,
            main_topic="Titan continuity",
            user_goal=goal,
            key_insights=["Preserve provenance"],
            conclusion="Keep the milestone deterministic",
            related_chats=related or [],
            facts_count=2,
            messages_count=5,
            produced_gist=True,
            created_at=created_at,
            finalized_at=created_at,
        )
    )


def _build_snapshot(
    *,
    query: str = "Explain the current Titan priority",
    observation: ShadowSafetyObservation | None = None,
) -> ShadowRunSnapshot:
    older = _episode(
        "chat:older",
        goal="Finish the MVP first",
        created_at="2026-08-01T10:00:00+00:00",
    )
    current = _episode(
        "chat:current",
        goal="Add another architecture layer",
        related=["chat:older"],
        created_at="2026-08-02T10:00:00+00:00",
    )
    episodes = [older, current]
    weave = ThreadWeaver().weave(episodes)
    continuity_result = ContinuityContextAssembler().assemble(
        request_ref="request:milestone-demo",
        current_episode=current,
        episodes=episodes,
        weave_result=weave,
    )
    continuity_policies = [
        ContinuityItemGatePolicy(
            item_id=item.item_id,
            attention_score=0.8,
            recall_allowed=True,
            eligible=True,
            restricted=False,
            erased=False,
            protected=False,
            conflict=False,
        )
        for item in continuity_result.pack.items
    ]
    continuity_batch = ContinuityWorkingMemoryAdapter().adapt(
        continuity_result.pack,
        episodes,
        continuity_policies,
    )

    assertion = AssertionRecord.create(
        subject_ref=PROJECT,
        predicate="priority",
        value="finish-mvp",
        origin_type=OriginType.USER_STATED,
        source_refs=("conversation:priority",),
        asserted_by=USER,
        valid_from=datetime(2026, 8, 1, 9, 0, tzinfo=UTC),
        recorded_at=datetime(2026, 8, 1, 9, 0, tzinfo=UTC),
    )
    state_result = StateReconciler().reconcile(
        [assertion], [], as_of=NOW
    )

    goal_snapshot = GoalRecordSnapshot.from_goal(
        Goal(
            goal_id="goal:mvp",
            user_id="user:ruslan",
            title="Finish the MVP",
            description="Complete the milestone before adding layers",
            status="active",
            priority=10,
            keywords=["mvp", "titan"],
            created_at="2026-08-01T09:00:00+00:00",
            updated_at="2026-08-02T10:00:00+00:00",
        )
    )
    goal_attestation = GoalAttestation.create(
        goal_ref=goal_snapshot.goal_ref,
        basis=GoalBasis.ACCEPTED_DECISION,
        source_refs=("conversation:goal-decision",),
        confirmed_at=datetime(2026, 8, 2, 10, 0, tzinfo=UTC),
    )
    goal_result = GoalProjector().project(
        [goal_snapshot], [goal_attestation]
    )

    loop_signal = OpenLoopSignal.create(
        loop_key="loop:new-layer",
        kind=OpenLoopKind.DEFERRED_DECISION,
        summary="Decide whether to add another architecture layer",
        source_refs=("conversation:open-loop",),
        opened_at=datetime(2026, 8, 1, 10, 0, tzinfo=UTC),
        related_goal_ref=goal_snapshot.goal_ref,
    )
    open_loop_result = OpenLoopProjector().project(
        [loop_signal], [], as_of=NOW
    )

    state_projection = state_result.projections[0]
    goal_projection = goal_result.projections[0]
    loop_projection = open_loop_result.projections[0]
    projection_policies = [
        ProjectionGatePolicy(
            projection_id=projection_id,
            attention_score=0.9,
            recall_allowed=True,
            eligible=True,
            restricted=False,
            erased=False,
            protected=False,
            conflict=False,
        )
        for projection_id in (
            state_projection.projection_id,
            goal_projection.projection_id,
            loop_projection.projection_id,
        )
    ]
    projection_batch = ProjectionWorkingMemoryAdapter().adapt(
        state_projections=[state_projection],
        assertions=[assertion],
        goal_projections=[goal_projection],
        open_loop_projections=[loop_projection],
        policies=projection_policies,
    )

    candidates = (
        *continuity_batch.candidates,
        *projection_batch.candidates,
    )
    capsules = (
        *continuity_batch.capsules,
        *projection_batch.capsules,
    )
    plan = WorkingMemoryGate().plan(
        candidates,
        budget=WorkingMemoryBudget(max_items=20, max_chars=20_000),
    )
    context_pack = ContextPackBuilder().build(
        plan,
        capsules,
        budget=ContextPackBudget(max_tokens=100_000),
    )
    decision = decide_compute_path(
        query,
        candidate_count=len(candidates),
        continuity=ContinuityComputeSignals(
            context_freshness=ContextFreshness.FRESH,
            evidence_coverage=1.0,
            active_contradictions=0,
            continuity_available=True,
            important_claim=True,
            requires_current_state=True,
        ),
    )
    return ShadowRunSnapshot.create(
        scenario_id="milestone-1-continuity-demo",
        continuity_pack=continuity_result.pack,
        continuity_receipt=continuity_result.receipt,
        state_result=state_result,
        goal_result=goal_result,
        open_loop_result=open_loop_result,
        working_memory_plan=plan,
        context_pack=context_pack,
        compute_decision=decision,
        observation=observation,
    )


def _hypothesis_as_fact_snapshot() -> ShadowRunSnapshot:
    span = SourceSpan.from_text(
        document_id="document:hypothesis",
        raw_text="The user wants another layer",
        start_offset=0,
        end_offset=len("The user wants another layer"),
        source_revision="revision:1",
    )
    claim = CapsuleClaim.create(
        text="The user wants another layer",
        modality=ClaimModality.HYPOTHESIS,
        source_spans=(span,),
        extraction_confidence=1.0,
        truth_confidence=0.9,
    )
    capsule = KnowledgeCapsule.create(
        source_document_id="document:hypothesis",
        essence=claim.text,
        claims=(claim,),
        reader_id="test-reader",
        reader_version="test-reader.v1",
        coverage_score=1.0,
        compression_ratio=1.0,
        created_at=NOW,
    )
    candidate = WorkingMemoryCandidate(
        capsule=capsule,
        attention_score=1.0,
        recall_allowed=True,
        eligible=True,
        restricted=False,
        erased=False,
        protected=False,
        conflict=False,
    )
    plan = WorkingMemoryGate().plan(
        [candidate],
        budget=WorkingMemoryBudget(max_items=2, max_chars=2_000),
    )
    context_pack = ContextPackBuilder().build(
        plan,
        [capsule],
        budget=ContextPackBudget(max_tokens=10_000),
    )
    return ShadowRunSnapshot.create(
        scenario_id="hypothesis-as-fact",
        working_memory_plan=plan,
        context_pack=context_pack,
        compute_decision=decide_compute_path("Evaluate the hypothesis"),
    )


def test_real_pipeline_replays_to_identical_snapshot_and_passes() -> None:
    baseline = _build_snapshot()
    replay = _build_snapshot()

    report = ReplayEvaluationReport.compare(baseline, replay)

    assert baseline.snapshot_id == replay.snapshot_id
    assert baseline.canonical_bytes() == replay.canonical_bytes()
    assert baseline.hard_gates.passed is True
    assert report.replay_equal is True
    assert report.passed is True
    assert report.failed_gates == ()


def test_changed_compute_decision_is_detected_as_replay_divergence() -> None:
    baseline = _build_snapshot()
    replay = _build_snapshot(query="Verify this medical claim")

    report = ReplayEvaluationReport.compare(baseline, replay)

    assert report.replay_equal is False
    assert report.passed is False
    assert report.hard_gates.replay_divergence == 1
    assert report.failed_gates == (HardGate.REPLAY_DIVERGENCE,)


def test_hypothesis_with_truth_confidence_fails_inference_gate() -> None:
    snapshot = _hypothesis_as_fact_snapshot()
    report = ReplayEvaluationReport.compare(snapshot, snapshot)

    assert snapshot.hard_gates.inference_as_fact == 1
    assert report.passed is False
    assert HardGate.INFERENCE_AS_FACT in report.failed_gates


def test_explicit_observer_violations_fail_zero_tolerance_gates() -> None:
    snapshot = _build_snapshot(
        observation=ShadowSafetyObservation(
            privacy_leakage=1,
            missing_provenance=2,
            budget_overflow=1,
            query_time_canon_write=1,
            silent_overwrite=1,
        )
    )

    report = ReplayEvaluationReport.compare(snapshot, snapshot)

    assert report.passed is False
    assert set(report.failed_gates) == {
        HardGate.PRIVACY_LEAKAGE,
        HardGate.MISSING_PROVENANCE,
        HardGate.BUDGET_OVERFLOW,
        HardGate.QUERY_TIME_CANON_WRITE,
        HardGate.SILENT_OVERWRITE,
    }


def test_report_identity_is_deterministic() -> None:
    baseline = _build_snapshot()
    replay = _build_snapshot()

    first = ReplayEvaluationReport.compare(baseline, replay)
    second = ReplayEvaluationReport.compare(baseline, replay)

    assert first == second
    assert first.report_id == second.report_id
    assert first.to_dict() == second.to_dict()


def test_different_scenarios_cannot_be_compared() -> None:
    baseline = _build_snapshot()
    replay = _hypothesis_as_fact_snapshot()

    with pytest.raises(ReplayEvaluationError, match="same scenario_id"):
        ReplayEvaluationReport.compare(baseline, replay)


def test_invalid_observation_counts_fail_closed() -> None:
    with pytest.raises(ReplayEvaluationError, match="privacy_leakage"):
        ShadowSafetyObservation(privacy_leakage=True)  # type: ignore[arg-type]
    with pytest.raises(ReplayEvaluationError, match="silent_overwrite"):
        ShadowSafetyObservation(silent_overwrite=-1)


def test_snapshot_and_report_are_immutable_and_have_no_runtime_authority() -> None:
    snapshot = _build_snapshot()
    report = ReplayEvaluationReport.compare(snapshot, snapshot)

    with pytest.raises(FrozenInstanceError):
        snapshot.scenario_id = "mutated"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.passed = False  # type: ignore[misc]

    for value in (snapshot, report):
        for forbidden in (
            "answer",
            "canon_write",
            "action_decision",
            "advice",
            "persist",
        ):
            assert not hasattr(value, forbidden)
