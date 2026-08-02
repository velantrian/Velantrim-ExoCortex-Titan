"""Tests for deterministic low-risk Advisory Shadow decisions."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime

import pytest

from core.compute_controller import decide_compute_path
from core.context_pack import ContextPackBudget, ContextPackBuilder
from core.continuity.advisory_shadow import (
    AdviceCandidate,
    AdvisoryAction,
    AdvisoryAudience,
    AdvisoryReason,
    AdvisoryShadowError,
    AdvisoryShadowGate,
    AdvisoryShadowRequest,
    AdvisorySignal,
    AdvisorySignalKind,
)
from core.continuity.contracts import (
    ActorKind,
    ActorRef,
    AssertionRecord,
    OriginType,
    SubjectKind,
    SubjectRef,
)
from core.continuity.evaluation import (
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
    OpenLoopResolution,
    OpenLoopSignal,
)
from core.continuity.state_reconciler import (
    CurrentStateProjection,
    ProjectionStatus,
    StateReason,
    StateReconciler,
)
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


def _report(*, failed: bool = False) -> ReplayEvaluationReport:
    text = "Safe shadow evidence"
    span = SourceSpan.from_text(
        document_id="document:advisory-test",
        raw_text=text,
        start_offset=0,
        end_offset=len(text),
        source_revision="revision:1",
    )
    claim = CapsuleClaim.create(
        text=text,
        modality=ClaimModality.INTERPRETATION,
        source_spans=(span,),
        extraction_confidence=1.0,
        truth_confidence=None,
    )
    capsule = KnowledgeCapsule.create(
        source_document_id="document:advisory-test",
        essence=text,
        claims=(claim,),
        reader_id="advisory-test-reader",
        reader_version="advisory-test-reader.v1",
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
    snapshot = ShadowRunSnapshot.create(
        scenario_id="advisory-shadow-test",
        working_memory_plan=plan,
        context_pack=context_pack,
        compute_decision=decide_compute_path("Evaluate advisory shadow"),
        observation=(
            ShadowSafetyObservation(privacy_leakage=1)
            if failed
            else ShadowSafetyObservation()
        ),
    )
    return ReplayEvaluationReport.compare(snapshot, snapshot)


def _request(
    *,
    audience: AdvisoryAudience = AdvisoryAudience.PRIVATE,
    allow_reminders: bool = True,
    allow_confirmation_questions: bool = True,
) -> AdvisoryShadowRequest:
    return AdvisoryShadowRequest(
        request_ref="request:advisory-shadow",
        audience=audience,
        allow_reminders=allow_reminders,
        allow_confirmation_questions=allow_confirmation_questions,
    )


def _state_projection(*, contested: bool = False) -> CurrentStateProjection:
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
    if not contested:
        return StateReconciler().reconcile(
            [assertion], [], as_of=NOW
        ).projections[0]
    return CurrentStateProjection.create(
        subject_ref=PROJECT,
        predicate="priority",
        as_of=NOW,
        status=ProjectionStatus.CONTESTED,
        selected_assertion_ref=assertion.assertion_id,
        candidate_assertion_refs=(assertion.assertion_id,),
        contradiction_assertion_refs=("assertion:other-priority",),
        reason_codes=(StateReason.ACTIVE_VALUE_CONFLICT,),
        review_required=True,
    )


def _goal_projection(*, status: str = "active"):
    snapshot = GoalRecordSnapshot.from_goal(
        Goal(
            goal_id=f"goal:{status}",
            user_id="user:ruslan",
            title="Finish the MVP",
            description="Complete the current milestone first",
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
    return GoalProjector().project(
        [snapshot], [attestation]
    ).projections[0]


def _loop_projection(
    *,
    kind: OpenLoopKind = OpenLoopKind.DEFERRED_DECISION,
    overdue: bool = False,
    resolved: bool = False,
):
    signal = OpenLoopSignal.create(
        loop_key=f"loop:{kind.value}",
        kind=kind,
        summary="Decide whether to add another architecture layer",
        source_refs=("conversation:open-loop",),
        opened_at=datetime(2026, 8, 1, 10, 0, tzinfo=UTC),
        due_at=(
            datetime(2026, 8, 2, 9, 0, tzinfo=UTC)
            if overdue
            else None
        ),
        related_goal_ref="goal:active",
    )
    resolutions = ()
    if resolved:
        resolutions = (
            OpenLoopResolution.create(
                loop_key=signal.loop_key,
                source_refs=("conversation:loop-resolution",),
                resolved_at=datetime(2026, 8, 2, 11, 0, tzinfo=UTC),
            ),
        )
    return OpenLoopProjector().project(
        [signal], resolutions, as_of=NOW
    ).projections[0]


def test_failed_hard_gates_always_defer_without_text() -> None:
    goal = _goal_projection()
    signal = AdvisorySignal.create(
        kind=AdvisorySignalKind.GOAL_RELEVANT,
        projection_id=goal.projection_id,
    )

    result = AdvisoryShadowGate().evaluate(
        request=_request(),
        hard_gate_report=_report(failed=True),
        signals=[signal],
        goal_projections=[goal],
    )

    assert result.candidate.action is AdvisoryAction.DEFER
    assert result.candidate.proposed_text is None
    assert AdvisoryReason.HARD_GATES_FAILED in result.candidate.reason_codes
    assert result.receipt.excluded_signal_ids == (signal.signal_id,)


def test_shared_or_unknown_audience_always_silences_personal_continuity() -> None:
    goal = _goal_projection()
    signal = AdvisorySignal.create(
        kind=AdvisorySignalKind.GOAL_RELEVANT,
        projection_id=goal.projection_id,
    )

    for audience in (AdvisoryAudience.SHARED, AdvisoryAudience.UNKNOWN):
        result = AdvisoryShadowGate().evaluate(
            request=_request(audience=audience),
            hard_gate_report=_report(),
            signals=[signal],
            goal_projections=[goal],
        )
        assert result.candidate.action is AdvisoryAction.SILENCE
        assert result.candidate.proposed_text is None
        assert (
            AdvisoryReason.NON_PRIVATE_AUDIENCE
            in result.candidate.reason_codes
        )


def test_priority_change_signal_asks_confirmation_and_preserves_basis() -> None:
    state = _state_projection(contested=True)
    signal = AdvisorySignal.create(
        kind=AdvisorySignalKind.PRIORITY_MAY_HAVE_CHANGED,
        projection_id=state.projection_id,
    )

    result = AdvisoryShadowGate().evaluate(
        request=_request(),
        hard_gate_report=_report(),
        signals=[signal],
        state_projections=[state],
    )

    assert result.candidate.action is AdvisoryAction.ASK_CONFIRMATION
    assert "изменился ли приоритет" in result.candidate.proposed_text
    assert result.candidate.basis_refs
    assert AdvisoryReason.CONTESTED_STATE in result.candidate.reason_codes
    assert result.candidate.shadow_only is True


def test_active_goal_reminds_or_asks_when_reminders_disabled() -> None:
    goal = _goal_projection()
    signal = AdvisorySignal.create(
        kind=AdvisorySignalKind.GOAL_RELEVANT,
        projection_id=goal.projection_id,
    )

    reminder = AdvisoryShadowGate().evaluate(
        request=_request(),
        hard_gate_report=_report(),
        signals=[signal],
        goal_projections=[goal],
    )
    confirmation = AdvisoryShadowGate().evaluate(
        request=_request(allow_reminders=False),
        hard_gate_report=_report(),
        signals=[signal],
        goal_projections=[goal],
    )

    assert reminder.candidate.action is AdvisoryAction.REMIND
    assert "Finish the MVP" in reminder.candidate.proposed_text
    assert confirmation.candidate.action is AdvisoryAction.ASK_CONFIRMATION
    assert "всё ещё актуальна" in confirmation.candidate.proposed_text


def test_open_loop_asks_confirmation_and_overdue_loop_reminds() -> None:
    open_loop = _loop_projection()
    overdue = _loop_projection(overdue=True)
    open_signal = AdvisorySignal.create(
        kind=AdvisorySignalKind.OPEN_LOOP_RELEVANT,
        projection_id=open_loop.projection_id,
    )
    overdue_signal = AdvisorySignal.create(
        kind=AdvisorySignalKind.OPEN_LOOP_RELEVANT,
        projection_id=overdue.projection_id,
    )

    open_result = AdvisoryShadowGate().evaluate(
        request=_request(),
        hard_gate_report=_report(),
        signals=[open_signal],
        open_loop_projections=[open_loop],
    )
    overdue_result = AdvisoryShadowGate().evaluate(
        request=_request(),
        hard_gate_report=_report(),
        signals=[overdue_signal],
        open_loop_projections=[overdue],
    )

    assert open_result.candidate.action is AdvisoryAction.ASK_CONFIRMATION
    assert overdue_result.candidate.action is AdvisoryAction.REMIND
    assert AdvisoryReason.OPEN_LOOP_OVERDUE in overdue_result.candidate.reason_codes


def test_blocker_signal_requires_typed_blocker_projection() -> None:
    deferred = _loop_projection()
    blocker = _loop_projection(kind=OpenLoopKind.BLOCKER)
    wrong_signal = AdvisorySignal.create(
        kind=AdvisorySignalKind.BLOCKER_RELEVANT,
        projection_id=deferred.projection_id,
    )
    blocker_signal = AdvisorySignal.create(
        kind=AdvisorySignalKind.BLOCKER_RELEVANT,
        projection_id=blocker.projection_id,
    )

    wrong = AdvisoryShadowGate().evaluate(
        request=_request(),
        hard_gate_report=_report(),
        signals=[wrong_signal],
        open_loop_projections=[deferred],
    )
    valid = AdvisoryShadowGate().evaluate(
        request=_request(),
        hard_gate_report=_report(),
        signals=[blocker_signal],
        open_loop_projections=[blocker],
    )

    assert wrong.candidate.action is AdvisoryAction.SILENCE
    assert valid.candidate.action is AdvisoryAction.ASK_CONFIRMATION
    assert AdvisoryReason.BLOCKER_RELEVANT in valid.candidate.reason_codes


def test_inactive_goal_and_resolved_loop_are_not_actionable() -> None:
    goal = _goal_projection(status="done")
    loop = _loop_projection(resolved=True)
    signals = [
        AdvisorySignal.create(
            kind=AdvisorySignalKind.GOAL_RELEVANT,
            projection_id=goal.projection_id,
        ),
        AdvisorySignal.create(
            kind=AdvisorySignalKind.OPEN_LOOP_RELEVANT,
            projection_id=loop.projection_id,
        ),
    ]

    result = AdvisoryShadowGate().evaluate(
        request=_request(),
        hard_gate_report=_report(),
        signals=signals,
        goal_projections=[goal],
        open_loop_projections=[loop],
    )

    assert result.candidate.action is AdvisoryAction.SILENCE
    assert set(result.receipt.excluded_signal_ids) == {
        value.signal_id for value in signals
    }


def test_no_permissions_or_no_signal_produces_silence() -> None:
    goal = _goal_projection()
    signal = AdvisorySignal.create(
        kind=AdvisorySignalKind.GOAL_RELEVANT,
        projection_id=goal.projection_id,
    )

    denied = AdvisoryShadowGate().evaluate(
        request=_request(
            allow_reminders=False,
            allow_confirmation_questions=False,
        ),
        hard_gate_report=_report(),
        signals=[signal],
        goal_projections=[goal],
    )
    empty = AdvisoryShadowGate().evaluate(
        request=_request(),
        hard_gate_report=_report(),
    )

    assert denied.candidate.action is AdvisoryAction.SILENCE
    assert empty.candidate.action is AdvisoryAction.SILENCE
    assert AdvisoryReason.NO_RELEVANT_SIGNAL in empty.candidate.reason_codes


def test_signal_priority_is_deterministic_and_input_order_independent() -> None:
    state = _state_projection(contested=True)
    goal = _goal_projection()
    loop = _loop_projection()
    signals = [
        AdvisorySignal.create(
            kind=AdvisorySignalKind.GOAL_RELEVANT,
            projection_id=goal.projection_id,
        ),
        AdvisorySignal.create(
            kind=AdvisorySignalKind.OPEN_LOOP_RELEVANT,
            projection_id=loop.projection_id,
        ),
        AdvisorySignal.create(
            kind=AdvisorySignalKind.PRIORITY_MAY_HAVE_CHANGED,
            projection_id=state.projection_id,
        ),
    ]
    gate = AdvisoryShadowGate()

    forward = gate.evaluate(
        request=_request(),
        hard_gate_report=_report(),
        signals=signals,
        state_projections=[state],
        goal_projections=[goal],
        open_loop_projections=[loop],
    )
    reverse = gate.evaluate(
        request=_request(),
        hard_gate_report=_report(),
        signals=reversed(signals),
        state_projections=[state],
        goal_projections=[goal],
        open_loop_projections=[loop],
    )

    assert forward == reverse
    assert forward.candidate.action is AdvisoryAction.ASK_CONFIRMATION
    assert forward.candidate.source_signal_id == signals[2].signal_id


def test_unknown_signal_target_fails_closed() -> None:
    signal = AdvisorySignal.create(
        kind=AdvisorySignalKind.GOAL_RELEVANT,
        projection_id="projection:missing",
    )

    with pytest.raises(AdvisoryShadowError, match="unknown goal projection"):
        AdvisoryShadowGate().evaluate(
            request=_request(),
            hard_gate_report=_report(),
            signals=[signal],
        )


def test_contract_cannot_be_switched_out_of_shadow_mode() -> None:
    with pytest.raises(AdvisoryShadowError, match="cannot be activated"):
        AdvisoryShadowRequest(
            request_ref="request:active-advice",
            audience=AdvisoryAudience.PRIVATE,
            shadow_only=False,
        )


def test_v1_never_emits_suggest_warn_or_answer_only() -> None:
    goal = _goal_projection()
    loop = _loop_projection()
    signals = [
        AdvisorySignal.create(
            kind=AdvisorySignalKind.GOAL_RELEVANT,
            projection_id=goal.projection_id,
        ),
        AdvisorySignal.create(
            kind=AdvisorySignalKind.OPEN_LOOP_RELEVANT,
            projection_id=loop.projection_id,
        ),
    ]

    result = AdvisoryShadowGate().evaluate(
        request=_request(),
        hard_gate_report=_report(),
        signals=signals,
        goal_projections=[goal],
        open_loop_projections=[loop],
    )

    assert result.candidate.action in {
        AdvisoryAction.REMIND,
        AdvisoryAction.ASK_CONFIRMATION,
    }
    assert result.candidate.action not in {
        AdvisoryAction.SUGGEST,
        AdvisoryAction.WARN,
        AdvisoryAction.ANSWER_ONLY,
    }


def test_result_is_immutable_and_has_no_runtime_authority() -> None:
    goal = _goal_projection()
    signal = AdvisorySignal.create(
        kind=AdvisorySignalKind.GOAL_RELEVANT,
        projection_id=goal.projection_id,
    )
    result = AdvisoryShadowGate().evaluate(
        request=_request(),
        hard_gate_report=_report(),
        signals=[signal],
        goal_projections=[goal],
    )

    with pytest.raises(FrozenInstanceError):
        result.candidate.action = AdvisoryAction.SILENCE  # type: ignore[misc]

    assert isinstance(result.candidate, AdviceCandidate)
    for forbidden in (
        "send",
        "answer",
        "persist",
        "canon_write",
        "action_decision",
        "execute",
    ):
        assert not hasattr(result, forbidden)
