"""Focused regression checks for Goal projection subject binding v2."""

from datetime import UTC, datetime

from core.continuity.goal_open_loop import (
    GOAL_PROJECTION_SCHEMA_VERSION,
    GoalAttestation,
    GoalBasis,
    GoalProjector,
    GoalRecordSnapshot,
)
from core.goal_stack import Goal


def test_goal_projection_v2_identity_includes_explicit_subject() -> None:
    goal = Goal(
        goal_id="goal:subject-binding",
        user_id="user:subject-a",
        title="Bind the goal subject",
        description="Keep source ownership explicit",
        status="active",
        priority=5,
        keywords=["continuity"],
        created_at="2026-08-06T10:00:00+00:00",
        updated_at="2026-08-06T11:00:00+00:00",
    )
    snapshot = GoalRecordSnapshot.from_goal(goal)
    attestation = GoalAttestation.create(
        user_id=snapshot.user_id,
        goal_ref=snapshot.goal_ref,
        basis=GoalBasis.EXPLICIT_INTENT,
        source_refs=("evidence:subject-binding",),
        confirmed_at=datetime(2026, 8, 6, 11, 0, tzinfo=UTC),
    )

    result = GoalProjector().project((snapshot,), (attestation,))

    assert GOAL_PROJECTION_SCHEMA_VERSION == "continuity.goal_projection.v2"
    assert result.subject_ids == (snapshot.user_id,)
    assert result.projections[0].user_id == snapshot.user_id
    assert result.decisions[0].user_id == snapshot.user_id
