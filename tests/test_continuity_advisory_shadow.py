"""Tests for deterministic continuity Advisory Shadow v2."""

from __future__ import annotations

from datetime import UTC, datetime
from dataclasses import FrozenInstanceError

import pytest

from core.continuity.advisory_shadow import (
    ADVISORY_POLICY_VERSION,
    AdviceCandidate,
    AdvisoryAction,
    AdvisoryAudience,
    AdvisoryReason,
    AdvisoryRisk,
    AdvisorySensitivity,
    AdvisoryShadowError,
    AdvisoryShadowGate,
    AdvisoryShadowRequest,
    AdvisorySignal,
    AdvisorySignalKind,
)
from core.continuity.contracts import SubjectKind, SubjectRef
from core.continuity.evaluation import (
    EVALUATION_POLICY_VERSION,
    EVALUATION_SCHEMA_VERSION,
    HardGateCounters,
    ReplayEvaluationReport,
)
from core.continuity.goal_open_loop import (
    GOAL_OPEN_LOOP_POLICY_VERSION,
    GOAL_PROJECTION_SCHEMA_VERSION,
    OPEN_LOOP_SCHEMA_VERSION,
    GoalBasis,
    GoalProjection,
    GoalStatus,
    OpenLoopKind,
    OpenLoopProjection,
    OpenLoopReason,
    OpenLoopStatus,
)
from core.continuity.state_reconciler import (
    STATE_PROJECTION_SCHEMA_VERSION,
    STATE_RECONCILIATION_POLICY_VERSION,
    CurrentStateProjection,
    ProjectionStatus,
    StateReason,
)

NOW = datetime(2026, 8, 5, 12, 0, tzinfo=UTC)


def _report(*, passed: bool = True) -> ReplayEvaluationReport:
    counters = HardGateCounters(
        replay_divergence=0 if passed else 1,
    )
    return ReplayEvaluationReport(
        report_id="report-pass" if passed else "report-fail",
        schema_version=EVALUATION_SCHEMA_VERSION,
        policy_version=EVALUATION_POLICY_VERSION,
        scenario_id="scenario-1",
        baseline_snapshot_id="baseline",
        replay_snapshot_id="replay",
        replay_equal=passed,
        hard_gates=counters,
        passed=passed,
    )


def _request(
    *,
    audience: AdvisoryAudience = AdvisoryAudience.PRIVATE,
    allow_reminders: bool = True,
    allow_confirmation_questions: bool = True,
) -> AdvisoryShadowRequest:
    return AdvisoryShadowRequest(
        request_ref="request-1",
        audience=audience,
        sensitivity=AdvisorySensitivity.MEDIUM,
        allow_reminders=allow_reminders,
        allow_confirmation_questions=allow_confirmation_questions,
    )


def _state(
    *,
    projection_id: str = "state-1",
    contested: bool = True,
) -> CurrentStateProjection:
    return CurrentStateProjection(
        projection_id=projection_id,
        schema_version=STATE_PROJECTION_SCHEMA_VERSION,
        policy_version=STATE_RECONCILIATION_POLICY_VERSION,
        subject_ref=SubjectRef("project-titan", SubjectKind.PROJECT),
        predicate="priority",
        as_of=NOW,
        status=(ProjectionStatus.CONTESTED if contested else ProjectionStatus.CURRENT),
        selected_assertion_ref="assertion-a",
        candidate_assertion_refs=("assertion-a", "assertion-b"),
        supporting_assertion_refs=("assertion-a",),
        contradiction_assertion_refs=("assertion-b",) if contested else (),
        superseded_assertion_refs=(),
        retracted_assertion_refs=(),
        expired_assertion_refs=(),
        future_assertion_refs=(),
        reason_codes=(StateReason.ACTIVE_VALUE_CONFLICT,) if contested else (),
        review_required=contested,
    )


def _goal(
    *,
    projection_id: str = "goal-projection-1",
    status: GoalStatus = GoalStatus.ACTIVE,
) -> GoalProjection:
    return GoalProjection(
        projection_id=projection_id,
        schema_version=GOAL_PROJECTION_SCHEMA_VERSION,
        policy_version=GOAL_OPEN_LOOP_POLICY_VERSION,
        user_id="user:advisory-fixture",
        goal_ref="goal-1",
        source_snapshot_id="snapshot-1",
        attestation_id="attestation-1",
        basis=GoalBasis.EXPLICIT_INTENT,
        status=status,
        title="Завершить аудит Titan",
        description="Проверить recovery-слои",
        priority=8,
        keywords=("audit", "titan"),
        source_refs=("message-1",),
        updated_at=NOW,
    )


def _loop(
    *,
    projection_id: str = "loop-projection-1",
    kind: OpenLoopKind = OpenLoopKind.UNANSWERED_QUESTION,
    status: OpenLoopStatus = OpenLoopStatus.OPEN,
) -> OpenLoopProjection:
    reasons = [OpenLoopReason.TYPED_SOURCE_SIGNAL]
    if status in {OpenLoopStatus.OPEN, OpenLoopStatus.OVERDUE}:
        reasons.append(OpenLoopReason.OPENED_AS_OF_REQUEST)
    if status is OpenLoopStatus.OVERDUE:
        reasons.append(OpenLoopReason.DEADLINE_PASSED)
    return OpenLoopProjection(
        projection_id=projection_id,
        schema_version=OPEN_LOOP_SCHEMA_VERSION,
        policy_version=GOAL_OPEN_LOOP_POLICY_VERSION,
        loop_key="loop-1",
        signal_id="loop-signal-1",
        kind=kind,
        summary="Проверить post-merge evidence",
        status=status,
        source_refs=("message-2",),
        resolution_ids=(),
        opened_at=NOW,
        due_at=NOW if status is OpenLoopStatus.OVERDUE else None,
        related_goal_ref="goal-1",
        reason_codes=tuple(reasons),
        review_required=False,
    )


def test_failed_hard_gates_defer_without_text() -> None:
    goal = _goal()
    signal = AdvisorySignal.create(
        kind=AdvisorySignalKind.GOAL_RELEVANT,
        projection_id=goal.projection_id,
    )

    result = AdvisoryShadowGate().evaluate(
        request=_request(),
        hard_gate_report=_report(passed=False),
        signals=(signal,),
        goal_projections=(goal,),
    )

    assert result.candidate.action is AdvisoryAction.DEFER
    assert result.candidate.proposed_text is None
    assert AdvisoryReason.HARD_GATES_FAILED in result.candidate.reason_codes
    assert result.receipt.hard_gates_passed is False
    assert result.receipt.excluded_signal_ids == (signal.signal_id,)


def test_non_private_audience_silences_personal_continuity() -> None:
    goal = _goal()
    signal = AdvisorySignal.create(
        kind=AdvisorySignalKind.GOAL_RELEVANT,
        projection_id=goal.projection_id,
    )

    result = AdvisoryShadowGate().evaluate(
        request=_request(audience=AdvisoryAudience.SHARED),
        hard_gate_report=_report(),
        signals=(signal,),
        goal_projections=(goal,),
    )

    assert result.candidate.action is AdvisoryAction.SILENCE
    assert AdvisoryReason.NON_PRIVATE_AUDIENCE in result.candidate.reason_codes
    assert result.candidate.proposed_text is None


def test_contested_priority_requires_explicit_confirmation() -> None:
    state = _state()
    signal = AdvisorySignal.create(
        kind=AdvisorySignalKind.PRIORITY_MAY_HAVE_CHANGED,
        projection_id=state.projection_id,
    )

    result = AdvisoryShadowGate().evaluate(
        request=_request(),
        hard_gate_report=_report(),
        signals=(signal,),
        state_projections=(state,),
    )

    assert result.candidate.action is AdvisoryAction.ASK_CONFIRMATION
    assert "приоритет" in (result.candidate.proposed_text or "")
    assert state.projection_id in result.candidate.basis_refs
    assert AdvisoryReason.CONTESTED_STATE in result.candidate.reason_codes
    assert result.receipt.evaluated_signal_ids == (signal.signal_id,)


def test_confirmation_permission_is_enforced() -> None:
    state = _state()
    signal = AdvisorySignal.create(
        kind=AdvisorySignalKind.PRIORITY_MAY_HAVE_CHANGED,
        projection_id=state.projection_id,
    )

    result = AdvisoryShadowGate().evaluate(
        request=_request(allow_confirmation_questions=False),
        hard_gate_report=_report(),
        signals=(signal,),
        state_projections=(state,),
    )

    assert result.candidate.action is AdvisoryAction.SILENCE
    assert AdvisoryReason.CONFIRMATION_NOT_ALLOWED in result.candidate.reason_codes


def test_active_attested_goal_can_produce_shadow_reminder() -> None:
    goal = _goal()
    signal = AdvisorySignal.create(
        kind=AdvisorySignalKind.GOAL_RELEVANT,
        projection_id=goal.projection_id,
    )

    result = AdvisoryShadowGate().evaluate(
        request=_request(),
        hard_gate_report=_report(),
        signals=(signal,),
        goal_projections=(goal,),
    )

    assert result.candidate.action is AdvisoryAction.REMIND
    assert goal.title in (result.candidate.proposed_text or "")
    assert result.candidate.risk is AdvisoryRisk.LOW
    assert goal.projection_id in result.candidate.basis_refs


def test_inactive_goal_is_not_actionable() -> None:
    goal = _goal(status=GoalStatus.COMPLETED)
    signal = AdvisorySignal.create(
        kind=AdvisorySignalKind.GOAL_RELEVANT,
        projection_id=goal.projection_id,
    )

    result = AdvisoryShadowGate().evaluate(
        request=_request(),
        hard_gate_report=_report(),
        signals=(signal,),
        goal_projections=(goal,),
    )

    assert result.candidate.action is AdvisoryAction.SILENCE
    assert AdvisoryReason.NO_RELEVANT_SIGNAL in result.candidate.reason_codes


def test_overdue_blocker_has_priority_and_medium_risk() -> None:
    blocker = _loop(
        kind=OpenLoopKind.BLOCKER,
        status=OpenLoopStatus.OVERDUE,
    )
    goal = _goal()
    blocker_signal = AdvisorySignal.create(
        kind=AdvisorySignalKind.BLOCKER_RELEVANT,
        projection_id=blocker.projection_id,
    )
    goal_signal = AdvisorySignal.create(
        kind=AdvisorySignalKind.GOAL_RELEVANT,
        projection_id=goal.projection_id,
    )

    result = AdvisoryShadowGate().evaluate(
        request=_request(),
        hard_gate_report=_report(),
        signals=(goal_signal, blocker_signal),
        goal_projections=(goal,),
        open_loop_projections=(blocker,),
    )

    assert result.candidate.source_signal_id == blocker_signal.signal_id
    assert result.candidate.action is AdvisoryAction.REMIND
    assert result.candidate.risk is AdvisoryRisk.MEDIUM
    assert AdvisoryReason.BLOCKER_RELEVANT in result.candidate.reason_codes
    assert AdvisoryReason.OPEN_LOOP_OVERDUE in result.candidate.reason_codes
    assert goal_signal.signal_id in result.receipt.excluded_signal_ids


def test_blocker_signal_cannot_relabel_non_blocker_loop() -> None:
    loop = _loop(kind=OpenLoopKind.UNANSWERED_QUESTION)
    signal = AdvisorySignal.create(
        kind=AdvisorySignalKind.BLOCKER_RELEVANT,
        projection_id=loop.projection_id,
    )

    result = AdvisoryShadowGate().evaluate(
        request=_request(),
        hard_gate_report=_report(),
        signals=(signal,),
        open_loop_projections=(loop,),
    )

    assert result.candidate.action is AdvisoryAction.SILENCE
    assert AdvisoryReason.NO_RELEVANT_SIGNAL in result.candidate.reason_codes


def test_reminder_permission_is_enforced() -> None:
    goal = _goal()
    signal = AdvisorySignal.create(
        kind=AdvisorySignalKind.GOAL_RELEVANT,
        projection_id=goal.projection_id,
    )

    result = AdvisoryShadowGate().evaluate(
        request=_request(allow_reminders=False),
        hard_gate_report=_report(),
        signals=(signal,),
        goal_projections=(goal,),
    )

    assert result.candidate.action is AdvisoryAction.SILENCE
    assert AdvisoryReason.REMINDER_NOT_ALLOWED in result.candidate.reason_codes


def test_priority_signal_outranks_goal_signal() -> None:
    state = _state()
    goal = _goal()
    state_signal = AdvisorySignal.create(
        kind=AdvisorySignalKind.PRIORITY_MAY_HAVE_CHANGED,
        projection_id=state.projection_id,
    )
    goal_signal = AdvisorySignal.create(
        kind=AdvisorySignalKind.GOAL_RELEVANT,
        projection_id=goal.projection_id,
    )

    result = AdvisoryShadowGate().evaluate(
        request=_request(),
        hard_gate_report=_report(),
        signals=(goal_signal, state_signal),
        state_projections=(state,),
        goal_projections=(goal,),
    )

    assert result.candidate.source_signal_id == state_signal.signal_id
    assert result.candidate.action is AdvisoryAction.ASK_CONFIRMATION


def test_non_actionable_higher_priority_does_not_break_lower_candidate() -> None:
    current_state = _state(contested=False)
    goal = _goal()
    state_signal = AdvisorySignal.create(
        kind=AdvisorySignalKind.PRIORITY_MAY_HAVE_CHANGED,
        projection_id=current_state.projection_id,
    )
    goal_signal = AdvisorySignal.create(
        kind=AdvisorySignalKind.GOAL_RELEVANT,
        projection_id=goal.projection_id,
    )

    result = AdvisoryShadowGate().evaluate(
        request=_request(),
        hard_gate_report=_report(),
        signals=(state_signal, goal_signal),
        state_projections=(current_state,),
        goal_projections=(goal,),
    )

    assert result.candidate.source_signal_id == goal_signal.signal_id
    assert result.candidate.action is AdvisoryAction.REMIND
    assert result.receipt.excluded_signal_ids == (state_signal.signal_id,)


def test_input_order_does_not_change_result() -> None:
    goal = _goal()
    loop = _loop()
    signals = (
        AdvisorySignal.create(
            kind=AdvisorySignalKind.GOAL_RELEVANT,
            projection_id=goal.projection_id,
        ),
        AdvisorySignal.create(
            kind=AdvisorySignalKind.OPEN_LOOP_RELEVANT,
            projection_id=loop.projection_id,
        ),
    )

    first = AdvisoryShadowGate().evaluate(
        request=_request(),
        hard_gate_report=_report(),
        signals=signals,
        goal_projections=(goal,),
        open_loop_projections=(loop,),
    )
    second = AdvisoryShadowGate().evaluate(
        request=_request(),
        hard_gate_report=_report(),
        signals=tuple(reversed(signals)),
        goal_projections=(goal,),
        open_loop_projections=(loop,),
    )

    assert first == second
    assert first.to_dict() == second.to_dict()


def test_unknown_projection_is_silenced_not_inferred() -> None:
    signal = AdvisorySignal.create(
        kind=AdvisorySignalKind.GOAL_RELEVANT,
        projection_id="missing-projection",
    )

    result = AdvisoryShadowGate().evaluate(
        request=_request(),
        hard_gate_report=_report(),
        signals=(signal,),
    )

    assert result.candidate.action is AdvisoryAction.SILENCE
    assert result.candidate.proposed_text is None


def test_request_cannot_activate_shadow_contract() -> None:
    with pytest.raises(AdvisoryShadowError, match="cannot be activated"):
        AdvisoryShadowRequest(
            request_ref="request-1",
            audience=AdvisoryAudience.PRIVATE,
            shadow_only=False,
        )


def test_candidate_validation_requires_shadow_reason_and_basis() -> None:
    with pytest.raises(AdvisoryShadowError, match="SHADOW_ONLY"):
        AdviceCandidate.create(
            request_ref="request-1",
            action=AdvisoryAction.SILENCE,
            proposed_text=None,
            basis_refs=(),
            reason_codes=(AdvisoryReason.NO_RELEVANT_SIGNAL,),
            source_signal_id=None,
            sensitivity=AdvisorySensitivity.LOW,
            risk=AdvisoryRisk.LOW,
        )
    with pytest.raises(AdvisoryShadowError, match="basis_refs"):
        AdviceCandidate.create(
            request_ref="request-1",
            action=AdvisoryAction.REMIND,
            proposed_text="Reminder",
            basis_refs=(),
            reason_codes=(AdvisoryReason.SHADOW_ONLY,),
            source_signal_id="signal-1",
            sensitivity=AdvisorySensitivity.LOW,
            risk=AdvisoryRisk.LOW,
        )


def test_result_is_immutable_and_has_no_execution_authority() -> None:
    goal = _goal()
    signal = AdvisorySignal.create(
        kind=AdvisorySignalKind.GOAL_RELEVANT,
        projection_id=goal.projection_id,
    )
    result = AdvisoryShadowGate().evaluate(
        request=_request(),
        hard_gate_report=_report(),
        signals=(signal,),
        goal_projections=(goal,),
    )

    assert result.candidate.policy_version == ADVISORY_POLICY_VERSION
    assert result.candidate.shadow_only is True
    assert result.receipt.shadow_only is True
    with pytest.raises(FrozenInstanceError):
        result.candidate.action = AdvisoryAction.SILENCE  # type: ignore[misc]

    payload = result.to_dict()
    forbidden = {
        "canon_write",
        "truth_status",
        "persist",
        "execute",
        "tool_call",
        "send",
        "answer_authority",
        "action_authority",
    }
    assert forbidden.isdisjoint(payload)
