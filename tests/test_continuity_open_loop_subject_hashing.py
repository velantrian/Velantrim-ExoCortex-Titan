"""Regression proofs for OpenLoop subject identity in content-addressed IDs."""

from datetime import UTC, datetime

from core.continuity.goal_open_loop import (
    OpenLoopKind,
    OpenLoopProjector,
    OpenLoopResolution,
    OpenLoopSignal,
)

OPENED_AT = datetime(2026, 8, 1, 10, 0, tzinfo=UTC)
RESOLVED_AT = datetime(2026, 8, 2, 11, 0, tzinfo=UTC)
AS_OF = datetime(2026, 8, 2, 12, 0, tzinfo=UTC)


def _signal(user_id: str) -> OpenLoopSignal:
    return OpenLoopSignal.create(
        user_id=user_id,
        loop_key="loop:subject-hash-regression",
        kind=OpenLoopKind.DEFERRED_DECISION,
        summary="Decide whether to activate the next continuity slice",
        source_refs=("conversation:subject-hash-regression",),
        opened_at=OPENED_AT,
        related_goal_ref="goal:continuity",
    )


def _resolution(user_id: str) -> OpenLoopResolution:
    return OpenLoopResolution.create(
        user_id=user_id,
        loop_key="loop:subject-hash-regression",
        source_refs=("conversation:subject-hash-resolution",),
        resolved_at=RESOLVED_AT,
    )


def test_user_id_changes_every_open_loop_content_addressed_identity() -> None:
    first_signal = _signal("user:first")
    second_signal = _signal("user:second")
    first_resolution = _resolution("user:first")
    second_resolution = _resolution("user:second")

    first_result = OpenLoopProjector().project(
        [first_signal], [first_resolution], as_of=AS_OF
    )
    second_result = OpenLoopProjector().project(
        [second_signal], [second_resolution], as_of=AS_OF
    )

    assert first_signal.signal_id != second_signal.signal_id
    assert first_resolution.resolution_id != second_resolution.resolution_id
    assert first_result.projections[0].projection_id != second_result.projections[0].projection_id
    assert first_result.result_id != second_result.result_id
    assert first_result.subject_ids == ("user:first",)
    assert second_result.subject_ids == ("user:second",)
