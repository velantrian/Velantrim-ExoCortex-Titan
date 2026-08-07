"""Regression proof for the OpenLoop result-level ``as_of`` boundary."""

from datetime import UTC, datetime

from core.continuity.goal_open_loop import (
    OpenLoopKind,
    OpenLoopProjector,
    OpenLoopSignal,
    _digest,
)
from core.continuity.open_loop_source_adapter import _projection_payload


def test_as_of_is_bound_by_result_not_projection_identity() -> None:
    signal = OpenLoopSignal.create(
        user_id="user:alice",
        loop_key="loop:result-as-of-boundary",
        kind=OpenLoopKind.DEFERRED_DECISION,
        summary="Keep as_of at the result boundary",
        source_refs=("conversation:result-as-of-boundary",),
        opened_at=datetime(2026, 8, 7, 9, 0, tzinfo=UTC),
    )
    result = OpenLoopProjector().project(
        (signal,),
        (),
        as_of=datetime(2026, 8, 7, 12, 0, tzinfo=UTC),
    )
    projection = result.projections[0]
    payload = _projection_payload(projection)

    assert "as_of" not in payload
    assert _digest(payload) == projection.projection_id
    assert result.as_of == datetime(2026, 8, 7, 12, 0, tzinfo=UTC)
