"""Tests for state/goal/open-loop projection admission to Synaptic memory."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime

import pytest

from core.context_pack import ContextPackBudget, ContextPackBuilder
from core.continuity.contracts import (
    ActorKind,
    ActorRef,
    AssertionRecord,
    OriginType,
    SubjectKind,
    SubjectRef,
)
from core.continuity.goal_open_loop import (
    GoalAttestation,
    GoalBasis,
    GoalProjector,
    GoalRecordSnapshot,
    OpenLoopKind,
    OpenLoopProjector,
    OpenLoopResolution,
    OpenLoopSignal,
)
from core.continuity.projection_working_memory_adapter import (
    ProjectionGatePolicy,
    ProjectionKind,
    ProjectionOmissionReason,
    ProjectionWorkingMemoryAdapter,
    ProjectionWorkingMemoryAdapterError,
)
from core.continuity.state_reconciler import (
    CurrentStateProjection,
    ProjectionStatus,
    StateReason,
    StateReconciler,
)
from core.goal_stack import Goal
from core.knowledge_capsule import ClaimModality
from core.working_memory_gate import (
    GateDisposition,
    WorkingMemoryBudget,
    WorkingMemoryGate,
)

NOW = datetime(2026, 8, 2, 12, 0, tzinfo=UTC)
USER = ActorRef("actor:user", ActorKind.HUMAN)
MODEL = ActorRef("actor:model", ActorKind.TITAN_COMPONENT)
PROJECT = SubjectRef("project:titan", SubjectKind.PROJECT)


def _assertion(
    value: str,
    *,
    origin: OriginType = OriginType.USER_STATED,
    actor: ActorRef = USER,
    source: str = "conversation:state",
) -> AssertionRecord:
    return AssertionRecord.create(
        subject_ref=PROJECT,
        predicate="priority",
        value=value,
        origin_type=origin,
        source_refs=(source,),
        asserted_by=actor,
        valid_from=datetime(2026, 8, 1, 9, 0, tzinfo=UTC),
        recorded_at=datetime(2026, 8, 1, 9, 0, tzinfo=UTC),
    )


def _goal_projection(status: str = "active"):
    snapshot = GoalRecordSnapshot.from_goal(
        Goal(
            goal_id=f"goal:{status}",
            user_id="user:ruslan",
            title="Finish the MVP",
            description="Complete the milestone before adding layers",
            status=status,
            priority=10,
            keywords=["mvp", "titan"],
            created_at="2026-08-01T09:00:00+00:00",
            updated_at="2026-08-02T10:00:00+00:00",
        )
    )
    attestation = GoalAttestation.create(
        goal_ref=snapshot.goal_ref,
        basis=GoalBasis.ACCEPTED_DECISION,
        source_refs=("conversation:goal-decision",),
        confirmed_at=datetime(2026, 8, 2, 10, 0, tzinfo=UTC),
    )
    return GoalProjector().project([snapshot], [attestation]).projections[0]


def _open_loop_projection(*, resolved: bool = False):
    signal = OpenLoopSignal.create(
        loop_key="loop:new-layer",
        kind=OpenLoopKind.DEFERRED_DECISION,
        summary="Decide whether to add another architecture layer",
        source_refs=("conversation:loop-open",),
        opened_at=datetime(2026, 8, 1, 10, 0, tzinfo=UTC),
        related_goal_ref="goal:active",
    )
    resolutions = ()
    if resolved:
        resolutions = (
            OpenLoopResolution.create(
                loop_key=signal.loop_key,
                source_refs=("conversation:loop-resolved",),
                resolved_at=datetime(2026, 8, 2, 11, 0, tzinfo=UTC),
            ),
        )
    return OpenLoopProjector().project(
        [signal], resolutions, as_of=NOW
    ).projections[0]


def _policy(projection_id: str, *, conflict: bool = False):
    return ProjectionGatePolicy(
        projection_id=projection_id,
        attention_score=0.9,
        recall_allowed=True,
        eligible=True,
        restricted=False,
        erased=False,
        protected=False,
        conflict=conflict,
    )


def test_current_state_adapts_without_truth_upgrade() -> None:
    assertion = _assertion("finish-mvp")
    projection = StateReconciler().reconcile(
        [assertion], [], as_of=NOW
    ).projections[0]

    batch = ProjectionWorkingMemoryAdapter().adapt(
        state_projections=[projection],
        assertions=[assertion],
        policies=[_policy(projection.projection_id)],
    )

    assert len(batch.candidates) == 1
    claim = batch.candidates[0].capsule.claims[0]
    assert claim.text == 'priority: "finish-mvp"'
    assert claim.modality is ClaimModality.USER_REPORT
    assert claim.truth_confidence is None
    assert "projection_not_canon" in claim.uncertainties
    assert batch.bindings[0].source_refs == ("conversation:state",)


def test_model_inferred_state_remains_hypothesis() -> None:
    assertion = _assertion(
        "add-layer",
        origin=OriginType.MODEL_INFERRED,
        actor=MODEL,
        source="model:inference",
    )
    projection = StateReconciler().reconcile(
        [assertion], [], as_of=NOW
    ).projections[0]

    batch = ProjectionWorkingMemoryAdapter().adapt(
        state_projections=[projection],
        assertions=[assertion],
        policies=[_policy(projection.projection_id)],
    )

    assert batch.candidates[0].capsule.claims[0].modality is ClaimModality.HYPOTHESIS
    assert batch.candidates[0].capsule.claims[0].truth_confidence is None


def test_contested_state_with_selected_assertion_is_quarantined_by_gate() -> None:
    assertion = _assertion("finish-mvp")
    projection = CurrentStateProjection.create(
        subject_ref=PROJECT,
        predicate="priority",
        as_of=NOW,
        status=ProjectionStatus.CONTESTED,
        selected_assertion_ref=assertion.assertion_id,
        candidate_assertion_refs=(assertion.assertion_id,),
        contradiction_assertion_refs=("assertion:conflict",),
        reason_codes=(StateReason.ACTIVE_VALUE_CONFLICT,),
        review_required=True,
    )
    batch = ProjectionWorkingMemoryAdapter().adapt(
        state_projections=[projection],
        assertions=[assertion],
        policies=[_policy(projection.projection_id)],
    )
    plan = WorkingMemoryGate().plan(
        batch.candidates,
        budget=WorkingMemoryBudget(max_items=8, max_chars=4_000),
    )

    assert plan.decisions[0].disposition is GateDisposition.QUARANTINE


def test_state_without_selection_is_omitted_before_gate() -> None:
    projection = CurrentStateProjection.create(
        subject_ref=PROJECT,
        predicate="priority",
        as_of=NOW,
        status=ProjectionStatus.CONTESTED,
        selected_assertion_ref=None,
        candidate_assertion_refs=("assertion:a", "assertion:b"),
        contradiction_assertion_refs=("assertion:a", "assertion:b"),
        reason_codes=(StateReason.ACTIVE_VALUE_CONFLICT,),
        review_required=True,
    )

    batch = ProjectionWorkingMemoryAdapter().adapt(
        state_projections=[projection]
    )

    assert batch.candidates == ()
    assert batch.omissions[0].reason is (
        ProjectionOmissionReason.STATE_HAS_NO_SELECTED_ASSERTION
    )


def test_active_goal_and_open_loop_use_existing_gate_and_context_pack() -> None:
    goal = _goal_projection()
    loop = _open_loop_projection()
    policies = [_policy(goal.projection_id), _policy(loop.projection_id)]

    batch = ProjectionWorkingMemoryAdapter().adapt(
        goal_projections=[goal],
        open_loop_projections=[loop],
        policies=reversed(policies),
    )
    plan = WorkingMemoryGate().plan(
        batch.candidates,
        budget=WorkingMemoryBudget(max_items=8, max_chars=8_000),
    )
    pack = ContextPackBuilder().build(
        plan,
        batch.capsules,
        budget=ContextPackBudget(max_tokens=100_000),
    )

    assert {binding.projection_kind for binding in batch.bindings} == {
        ProjectionKind.GOAL,
        ProjectionKind.OPEN_LOOP,
    }
    assert len(plan.active) == 2
    assert len(pack.claims) == 2
    assert all(value.truth_confidence is None for value in pack.claims)
    assert {value.modality for value in pack.claims} == {
        ClaimModality.GOAL,
        ClaimModality.INTERPRETATION,
    }


def test_completed_goal_and_resolved_loop_are_omitted_without_policies() -> None:
    goal = _goal_projection("done")
    loop = _open_loop_projection(resolved=True)

    batch = ProjectionWorkingMemoryAdapter().adapt(
        goal_projections=[goal], open_loop_projections=[loop]
    )

    assert batch.candidates == ()
    assert {value.reason for value in batch.omissions} == {
        ProjectionOmissionReason.GOAL_NOT_ACTIVE,
        ProjectionOmissionReason.OPEN_LOOP_NOT_ACTIVE,
    }


def test_exact_policy_coverage_is_required() -> None:
    goal = _goal_projection()

    with pytest.raises(
        ProjectionWorkingMemoryAdapterError,
        match="policy/projection mismatch",
    ):
        ProjectionWorkingMemoryAdapter().adapt(goal_projections=[goal])

    with pytest.raises(
        ProjectionWorkingMemoryAdapterError,
        match="policy/projection mismatch",
    ):
        ProjectionWorkingMemoryAdapter().adapt(
            goal_projections=[goal],
            policies=[
                _policy(goal.projection_id),
                _policy("projection:unexpected"),
            ],
        )


def test_missing_or_mismatched_selected_assertion_fails_closed() -> None:
    assertion = _assertion("finish-mvp")
    projection = StateReconciler().reconcile(
        [assertion], [], as_of=NOW
    ).projections[0]

    with pytest.raises(
        ProjectionWorkingMemoryAdapterError,
        match="selected state assertion is missing",
    ):
        ProjectionWorkingMemoryAdapter().adapt(
            state_projections=[projection],
            policies=[_policy(projection.projection_id)],
        )

    mismatched = AssertionRecord.create(
        subject_ref=SubjectRef("project:other", SubjectKind.PROJECT),
        predicate="priority",
        value="finish-mvp",
        origin_type=OriginType.USER_STATED,
        source_refs=("conversation:other",),
        asserted_by=USER,
        valid_from=datetime(2026, 8, 1, 9, 0, tzinfo=UTC),
        recorded_at=datetime(2026, 8, 1, 9, 0, tzinfo=UTC),
    )
    forged = CurrentStateProjection.create(
        subject_ref=PROJECT,
        predicate="priority",
        as_of=NOW,
        status=ProjectionStatus.CURRENT,
        selected_assertion_ref=mismatched.assertion_id,
        candidate_assertion_refs=(mismatched.assertion_id,),
        reason_codes=(StateReason.ACTIVE_ASSERTION,),
    )
    with pytest.raises(
        ProjectionWorkingMemoryAdapterError,
        match="does not match state projection",
    ):
        ProjectionWorkingMemoryAdapter().adapt(
            state_projections=[forged],
            assertions=[mismatched],
            policies=[_policy(forged.projection_id)],
        )


def test_input_order_is_replay_stable() -> None:
    goal = _goal_projection()
    loop = _open_loop_projection()
    adapter = ProjectionWorkingMemoryAdapter()
    policies = [_policy(goal.projection_id), _policy(loop.projection_id)]

    forward = adapter.adapt(
        goal_projections=[goal],
        open_loop_projections=[loop],
        policies=policies,
    )
    reverse = adapter.adapt(
        goal_projections=reversed([goal]),
        open_loop_projections=reversed([loop]),
        policies=reversed(policies),
    )

    assert forward.bindings == reverse.bindings
    assert forward.capsules == reverse.capsules


def test_batch_is_immutable_and_has_no_execution_authority() -> None:
    goal = _goal_projection()
    batch = ProjectionWorkingMemoryAdapter().adapt(
        goal_projections=[goal],
        policies=[_policy(goal.projection_id)],
    )

    with pytest.raises(FrozenInstanceError):
        batch.candidates = ()  # type: ignore[misc]

    for forbidden in (
        "plan",
        "answer",
        "canon_write",
        "action_decision",
        "processing_mode",
    ):
        assert not hasattr(batch, forbidden)
