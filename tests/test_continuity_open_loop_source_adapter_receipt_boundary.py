"""Regression proof for OpenLoop source-binding receipt chronology."""

from datetime import UTC, datetime

from core.continuity.contracts import SubjectKind, SubjectRef
from core.continuity.goal_open_loop import (
    OpenLoopKind,
    OpenLoopProjector,
    OpenLoopSignal,
)
from core.continuity.open_loop_source_adapter import (
    OPEN_LOOP_SOURCE_COMPONENT_VERSION,
    OPEN_LOOP_SOURCE_OWNER,
    OPEN_LOOP_SOURCE_TYPE,
)
from core.continuity.source_admission import ContinuitySourceBindingReceipt


def test_open_loop_binding_can_be_issued_at_source_as_of() -> None:
    as_of = datetime(2026, 8, 7, 12, 0, tzinfo=UTC)
    signal = OpenLoopSignal.create(
        user_id="user:alice",
        loop_key="loop:receipt-time-boundary",
        kind=OpenLoopKind.DEFERRED_DECISION,
        summary="Issue source binding at the represented result time",
        source_refs=("conversation:receipt-time-boundary",),
        opened_at=datetime(2026, 8, 7, 9, 0, tzinfo=UTC),
    )
    result = OpenLoopProjector().project((signal,), (), as_of=as_of)
    projection = result.projections[0]
    evidence_refs = tuple(
        sorted(
            {
                result.result_id,
                projection.projection_id,
                projection.signal_id,
                *projection.source_refs,
            }
        )
    )

    receipt = ContinuitySourceBindingReceipt.create(
        source_type=OPEN_LOOP_SOURCE_TYPE,
        source_result_id=result.result_id,
        source_digest=result.result_id,
        source_owner=OPEN_LOOP_SOURCE_OWNER,
        tenant_ref="tenant:one",
        subject_refs=(
            SubjectRef(subject_id="user:alice", kind=SubjectKind.PERSON),
        ),
        source_component_version=OPEN_LOOP_SOURCE_COMPONENT_VERSION,
        source_policy_version=result.policy_version,
        source_as_of=result.as_of,
        evidence_refs=evidence_refs,
        issued_at=result.as_of,
    )

    assert receipt.source_as_of == as_of
    assert receipt.issued_at == as_of
