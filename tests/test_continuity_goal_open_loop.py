"""Tests for evidence-qualified goals and typed open-loop projections."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime

import pytest

from core.continuity.goal_open_loop import (
    GoalAttestation,
    GoalBasis,
    GoalDecisionDisposition,
    GoalDecisionReason,
    GoalOpenLoopError,
    GoalProjector,
    GoalRecordSnapshot,
    GoalStackSnapshotBridge,
    GoalStatus,
    OpenLoopKind,
    OpenLoopProjector,
    OpenLoopReason,
    OpenLoopResolution,
    OpenLoopSignal,
    OpenLoopStatus,
)
from core.goal_stack import Goal, GoalStack

NOW = datetime(2026, 8, 2, 12, 0, tzinfo=UTC)


def _goal(
    goal_id: str = "goal:mvp",
    *,
    status: str = "active",
    priority: int = 10,
    title: str = "Finish the MVP",
) -> Goal:
    return Goal(
        goal_id=goal_id,
        user_id="user:ruslan",
        title=title,
        description="Complete the current milestone before adding layers",
        status=status,
        priority=priority,
        keywords=["mvp", "titan"],
        created_at="2026-08-01T09:00:00+00:00",
        updated_at="2026-08-02T10:00:00+00:00",
    )


def _attestation(
    goal_ref: str = "goal:mvp", *, user_id: str = "user:ruslan"
) -> GoalAttestation:
    return GoalAttestation.create(
        user_id=user_id,
        goal_ref=goal_ref,
        basis=GoalBasis.ACCEPTED_DECISION,
        source_refs=("conversation:decision-001",),
        confirmed_at=datetime(2026, 8, 2, 10, 0, tzinfo=UTC),
    )


def _signal(
    loop_key: str = "loop:architecture-layer",
    *,
    kind: OpenLoopKind = OpenLoopKind.DEFERRED_DECISION,
    opened_at: datetime = datetime(2026, 8, 1, 10, 0, tzinfo=UTC),
    due_at: datetime | None = None,
) -> OpenLoopSignal:
    return OpenLoopSignal.create(
        loop_key=loop_key,
        kind=kind,
        summary="Decide whether to add another architecture layer",
        source_refs=("conversation:decision-001",),
        opened_at=opened_at,
        due_at=due_at,
        related_goal_ref="goal:mvp",
    )


class _Reader:
    def __init__(self, goals: list[Goal]) -> None:
        self.goals = goals
        self.calls: list[tuple[str, str | None, int]] = []

    def list_goals(
        self,
        user_id: str = "default",
        *,
        status: str | None = "active",
        limit: int = 50,
    ) -> list[Goal]:
        self.calls.append((user_id, status, limit))
        return list(self.goals)


def test_goal_snapshot_bridge_reads_all_statuses_and_detaches_mutability() -> None:
    source = _goal()
    reader = _Reader([source])

    snapshot = GoalStackSnapshotBridge(reader).snapshots("user:ruslan")[0]
    source.keywords.append("mutated")
    source.title = "Mutated"

    assert reader.calls == [("user:ruslan", None, 200)]
    assert snapshot.title == "Finish the MVP"
    assert snapshot.keywords == ("mvp", "titan")
    assert snapshot.status is GoalStatus.ACTIVE
    assert snapshot.source_ref == "goal_stack:goal:mvp"


def test_real_goal_stack_bridge_is_read_only(tmp_path) -> None:
    stack = GoalStack(str(tmp_path / "goals.db"))
    created = stack.create(
        user_id="user:ruslan",
        title="Finish the MVP",
        description="Do not add a new layer yet",
        priority=10,
        keywords=["mvp", "titan"],
        goal_id="goal:mvp",
    )
    before = stack.get(created.goal_id)

    snapshots = GoalStackSnapshotBridge(stack).snapshots("user:ruslan")
    after = stack.get(created.goal_id)

    assert len(snapshots) == 1
    assert before == after
    assert snapshots[0].goal_ref == created.goal_id


def test_unattested_legacy_goal_is_excluded_from_projection() -> None:
    snapshot = GoalRecordSnapshot.from_goal(_goal())

    result = GoalProjector().project([snapshot], [])

    assert result.projections == ()
    assert result.decisions[0].disposition is GoalDecisionDisposition.EXCLUDED
    assert result.decisions[0].reason_codes == (
        GoalDecisionReason.MISSING_ATTESTATION,
    )


def test_attested_goal_becomes_source_linked_projection() -> None:
    snapshot = GoalRecordSnapshot.from_goal(_goal())
    attestation = _attestation()

    result = GoalProjector().project([snapshot], [attestation])
    projection = result.projections[0]

    assert projection.goal_ref == snapshot.goal_ref
    assert projection.basis is GoalBasis.ACCEPTED_DECISION
    assert projection.status is GoalStatus.ACTIVE
    assert projection.source_refs == (
        "conversation:decision-001",
        "goal_stack:goal:mvp",
    )
    assert result.decisions[0].disposition is GoalDecisionDisposition.INCLUDED
    assert projection.user_id == snapshot.user_id
    assert result.decisions[0].user_id == snapshot.user_id
    assert result.subject_ids == (snapshot.user_id,)


def test_goal_subject_binding_is_content_addressed_and_multi_subject_explicit() -> None:
    first = GoalRecordSnapshot.from_goal(_goal())
    other_goal = _goal("goal:other", title="Other subject goal")
    other_goal.user_id = "user:other"
    second = GoalRecordSnapshot.from_goal(other_goal)
    result = GoalProjector().project(
        [first, second],
        [
            _attestation(first.goal_ref, user_id=first.user_id),
            _attestation(second.goal_ref, user_id=second.user_id),
        ],
    )
    assert result.subject_ids == ("user:other", "user:ruslan")
    assert {value.user_id for value in result.projections} == set(result.subject_ids)
    assert {value.user_id for value in result.decisions} == set(result.subject_ids)


def test_goal_attestation_cannot_cross_subject_boundary() -> None:
    snapshot = GoalRecordSnapshot.from_goal(_goal())
    wrong_subject = _attestation(snapshot.goal_ref, user_id="user:other")
    with pytest.raises(GoalOpenLoopError, match="user_id does not match"):
        GoalProjector().project([snapshot], [wrong_subject])


def test_goal_projection_is_order_independent() -> None:
    first = GoalRecordSnapshot.from_goal(_goal())
    second = GoalRecordSnapshot.from_goal(
        _goal("goal:docs", priority=5, title="Document the architecture")
    )
    attestations = [_attestation(first.goal_ref), _attestation(second.goal_ref)]

    forward = GoalProjector().project([first, second], attestations)
    reverse = GoalProjector().project(
        [second, first], list(reversed(attestations))
    )

    assert forward.result_id == reverse.result_id
    assert tuple(value.projection_id for value in forward.projections) == tuple(
        value.projection_id for value in reverse.projections
    )


def test_unknown_or_multiple_goal_attestations_fail_closed() -> None:
    snapshot = GoalRecordSnapshot.from_goal(_goal())
    unknown = _attestation("goal:unknown")

    with pytest.raises(GoalOpenLoopError, match="unknown goal"):
        GoalProjector().project([snapshot], [unknown])

    second = GoalAttestation.create(
        user_id=snapshot.user_id,
        goal_ref=snapshot.goal_ref,
        basis=GoalBasis.EXPLICIT_INTENT,
        source_refs=("conversation:intent-002",),
        confirmed_at=NOW,
    )
    with pytest.raises(GoalOpenLoopError, match="multiple attestations"):
        GoalProjector().project([snapshot], [_attestation(), second])


def test_typed_open_loop_is_open_and_requires_review() -> None:
    signal = _signal()

    projection = OpenLoopProjector().project(
        [signal], [], as_of=NOW
    ).projections[0]

    assert projection.status is OpenLoopStatus.OPEN
    assert projection.review_required is True
    assert OpenLoopReason.TYPED_SOURCE_SIGNAL in projection.reason_codes
    assert OpenLoopReason.OPENED_AS_OF_REQUEST in projection.reason_codes


def test_deadline_and_resolution_change_projection_without_mutating_signal() -> None:
    signal = _signal(
        due_at=datetime(2026, 8, 2, 9, 0, tzinfo=UTC)
    )
    overdue = OpenLoopProjector().project(
        [signal], [], as_of=NOW
    ).projections[0]
    resolution = OpenLoopResolution.create(
        loop_key=signal.loop_key,
        source_refs=("conversation:resolution-001",),
        resolved_at=datetime(2026, 8, 2, 11, 0, tzinfo=UTC),
    )
    resolved = OpenLoopProjector().project(
        [signal], [resolution], as_of=NOW
    ).projections[0]

    assert overdue.status is OpenLoopStatus.OVERDUE
    assert OpenLoopReason.DEADLINE_PASSED in overdue.reason_codes
    assert resolved.status is OpenLoopStatus.RESOLVED
    assert resolved.review_required is False
    assert resolved.resolution_ids == (resolution.resolution_id,)
    assert signal.due_at == datetime(2026, 8, 2, 9, 0, tzinfo=UTC)


def test_future_signal_is_not_yet_open() -> None:
    signal = _signal(
        opened_at=datetime(2026, 8, 3, 10, 0, tzinfo=UTC)
    )

    projection = OpenLoopProjector().project(
        [signal], [], as_of=NOW
    ).projections[0]

    assert projection.status is OpenLoopStatus.NOT_YET_OPEN
    assert projection.review_required is False
    assert OpenLoopReason.FUTURE_OPEN_TIME in projection.reason_codes


def test_unknown_early_or_conflicting_open_loop_inputs_fail_closed() -> None:
    signal = _signal()
    unknown_resolution = OpenLoopResolution.create(
        loop_key="loop:unknown",
        source_refs=("conversation:unknown-resolution",),
        resolved_at=NOW,
    )
    with pytest.raises(GoalOpenLoopError, match="unknown loop"):
        OpenLoopProjector().project(
            [signal], [unknown_resolution], as_of=NOW
        )

    early = OpenLoopResolution.create(
        loop_key=signal.loop_key,
        source_refs=("conversation:early-resolution",),
        resolved_at=datetime(2026, 7, 31, 10, 0, tzinfo=UTC),
    )
    with pytest.raises(GoalOpenLoopError, match="precedes open time"):
        OpenLoopProjector().project([signal], [early], as_of=NOW)

    conflicting = OpenLoopSignal.create(
        loop_key=signal.loop_key,
        kind=OpenLoopKind.BLOCKER,
        summary="A different meaning for the same loop key",
        source_refs=("conversation:other",),
        opened_at=signal.opened_at,
    )
    with pytest.raises(GoalOpenLoopError, match="conflicting signals"):
        OpenLoopProjector().project(
            [signal, conflicting], [], as_of=NOW
        )


def test_open_loop_projection_is_replay_stable_and_order_independent() -> None:
    first = _signal("loop:first")
    second = _signal(
        "loop:second", kind=OpenLoopKind.UNANSWERED_QUESTION
    )

    forward = OpenLoopProjector().project(
        [first, second], [], as_of=NOW
    )
    reverse = OpenLoopProjector().project(
        [second, first], [], as_of=NOW
    )

    assert forward.result_id == reverse.result_id
    assert tuple(value.projection_id for value in forward.projections) == tuple(
        value.projection_id for value in reverse.projections
    )


def test_goal_and_open_loop_objects_are_immutable_and_have_no_action_authority() -> None:
    goal = GoalProjector().project(
        [GoalRecordSnapshot.from_goal(_goal())], [_attestation()]
    ).projections[0]
    loop = OpenLoopProjector().project(
        [_signal()], [], as_of=NOW
    ).projections[0]

    with pytest.raises(FrozenInstanceError):
        goal.title = "Mutated"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        loop.status = OpenLoopStatus.RESOLVED  # type: ignore[misc]

    for value in (goal, loop):
        for forbidden in (
            "truth_status",
            "canon_write",
            "advice",
            "action_decision",
            "processing_mode",
        ):
            assert not hasattr(value, forbidden)
