"""Tests for deterministic current-state reconciliation."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime

import pytest

from core.continuity.contracts import (
    ActorKind,
    ActorRef,
    AssertionRecord,
    AssertionRelation,
    AssertionRelationType,
    OriginType,
    SubjectKind,
    SubjectRef,
)
from core.continuity.state_reconciler import (
    ProjectionStatus,
    StateReason,
    StateReconciler,
    StateReconciliationError,
)

AS_OF = datetime(2026, 8, 2, 12, 0, tzinfo=UTC)
USER = ActorRef("actor:user", ActorKind.HUMAN)
OTHER_USER = ActorRef("actor:other-user", ActorKind.HUMAN)
MODEL = ActorRef("actor:model", ActorKind.TITAN_COMPONENT)
OPERATOR = ActorRef("actor:operator", ActorKind.OPERATOR)
PROJECT = SubjectRef("project:titan", SubjectKind.PROJECT)
OTHER_PROJECT = SubjectRef("project:other", SubjectKind.PROJECT)


def _assertion(
    value: str,
    *,
    origin: OriginType = OriginType.USER_STATED,
    actor: ActorRef = USER,
    subject: SubjectRef = PROJECT,
    predicate: str = "priority",
    valid_from: datetime = datetime(2026, 8, 1, 9, 0, tzinfo=UTC),
    valid_to: datetime | None = None,
    recorded_at: datetime | None = None,
    source_suffix: str = "default",
) -> AssertionRecord:
    return AssertionRecord.create(
        subject_ref=subject,
        predicate=predicate,
        value=value,
        origin_type=origin,
        source_refs=(f"source:{source_suffix}",),
        asserted_by=actor,
        valid_from=valid_from,
        valid_to=valid_to,
        recorded_at=recorded_at or valid_from,
    )


def _relation(
    relation_type: AssertionRelationType,
    source: AssertionRecord,
    target: AssertionRecord,
    *,
    created_at: datetime = AS_OF,
) -> AssertionRelation:
    return AssertionRelation.create(
        relation_type=relation_type,
        source_assertion_ref=source.assertion_id,
        target_assertion_ref=target.assertion_id,
        evidence_refs=(f"evidence:{relation_type.value}",),
        actor_ref=OPERATOR,
        created_at=created_at,
    )


def _projection(assertions, relations=()):
    result = StateReconciler().reconcile(
        assertions,
        relations,
        as_of=AS_OF,
    )
    assert len(result.projections) == 1
    return result.projections[0]


def test_explicit_correction_selects_source_and_supersedes_target() -> None:
    old = _assertion("finish-mvp", source_suffix="old")
    corrected = _assertion(
        "pause-mvp",
        actor=OTHER_USER,
        valid_from=datetime(2026, 8, 2, 8, 0, tzinfo=UTC),
        source_suffix="corrected",
    )
    relation = _relation(AssertionRelationType.CORRECTS, corrected, old)

    projection = _projection([old, corrected], [relation])

    assert projection.status is ProjectionStatus.CURRENT
    assert projection.selected_assertion_ref == corrected.assertion_id
    assert projection.superseded_assertion_refs == (old.assertion_id,)
    assert StateReason.EXPLICIT_CORRECTION in projection.reason_codes


def test_newer_user_statement_supersedes_older_same_actor() -> None:
    old = _assertion("finish-mvp", source_suffix="old")
    newer = _assertion(
        "add-layer",
        valid_from=datetime(2026, 8, 2, 8, 0, tzinfo=UTC),
        source_suffix="newer",
    )

    projection = _projection([old, newer])

    assert projection.status is ProjectionStatus.CURRENT
    assert projection.selected_assertion_ref == newer.assertion_id
    assert projection.superseded_assertion_refs == (old.assertion_id,)
    assert StateReason.NEWER_USER_STATEMENT in projection.reason_codes


def test_model_inference_cannot_replace_user_statement() -> None:
    user = _assertion("finish-mvp", source_suffix="user")
    inference = _assertion(
        "add-layer",
        origin=OriginType.MODEL_INFERRED,
        actor=MODEL,
        valid_from=datetime(2026, 8, 2, 10, 0, tzinfo=UTC),
        source_suffix="inference",
    )

    projection = _projection([inference, user])

    assert projection.status is ProjectionStatus.CONTESTED
    assert projection.selected_assertion_ref == user.assertion_id
    assert projection.contradiction_assertion_refs == (
        inference.assertion_id,
    )
    assert (
        StateReason.USER_STATEMENT_PREFERRED_OVER_INFERENCE
        in projection.reason_codes
    )


def test_inferred_lifecycle_relation_cannot_displace_user_assertion() -> None:
    user = _assertion("finish-mvp", source_suffix="user")
    inference = _assertion(
        "add-layer",
        origin=OriginType.MODEL_INFERRED,
        actor=MODEL,
        source_suffix="inference",
    )
    relation = _relation(
        AssertionRelationType.SUPERSEDES,
        inference,
        user,
    )

    with pytest.raises(
        StateReconciliationError,
        match="MODEL_INFERRED cannot displace",
    ):
        StateReconciler().reconcile(
            [user, inference],
            [relation],
            as_of=AS_OF,
        )


def test_conflicting_user_statements_from_different_actors_remain_contested() -> None:
    first = _assertion("finish-mvp", source_suffix="first")
    second = _assertion(
        "add-layer",
        actor=OTHER_USER,
        source_suffix="second",
    )

    projection = _projection([first, second])

    assert projection.status is ProjectionStatus.CONTESTED
    assert projection.selected_assertion_ref is None
    assert set(projection.contradiction_assertion_refs) == {
        first.assertion_id,
        second.assertion_id,
    }
    assert projection.review_required is True


def test_same_value_assertions_are_corroborating_not_conflicting() -> None:
    first = _assertion("finish-mvp", source_suffix="first")
    second = _assertion(
        "finish-mvp",
        origin=OriginType.DOCUMENT_STATED,
        actor=OPERATOR,
        valid_from=datetime(2026, 8, 2, 8, 0, tzinfo=UTC),
        source_suffix="second",
    )

    projection = _projection([first, second])

    assert projection.status is ProjectionStatus.CURRENT
    assert projection.selected_assertion_ref == second.assertion_id
    assert projection.supporting_assertion_refs == (first.assertion_id,)
    assert StateReason.SAME_VALUE_CORROBORATION in projection.reason_codes


def test_explicit_contradiction_keeps_same_value_projection_contested() -> None:
    first = _assertion("finish-mvp", source_suffix="first")
    second = _assertion(
        "finish-mvp",
        actor=OTHER_USER,
        valid_from=datetime(2026, 8, 2, 8, 0, tzinfo=UTC),
        source_suffix="second",
    )
    relation = _relation(AssertionRelationType.CONTRADICTS, first, second)

    projection = _projection([first, second], [relation])

    assert projection.status is ProjectionStatus.CONTESTED
    assert projection.selected_assertion_ref == second.assertion_id
    assert projection.contradiction_assertion_refs == (first.assertion_id,)
    assert StateReason.EXPLICIT_CONTRADICTION in projection.reason_codes


def test_only_expired_assertions_produce_expired_projection() -> None:
    expired = _assertion(
        "finish-mvp",
        valid_to=datetime(2026, 8, 2, 8, 0, tzinfo=UTC),
        source_suffix="expired",
    )

    projection = _projection([expired])

    assert projection.status is ProjectionStatus.EXPIRED
    assert projection.selected_assertion_ref is None
    assert projection.expired_assertion_refs == (expired.assertion_id,)


def test_only_future_assertions_produce_unresolved_projection() -> None:
    future = _assertion(
        "add-layer",
        valid_from=datetime(2026, 8, 3, 8, 0, tzinfo=UTC),
        source_suffix="future",
    )

    projection = _projection([future])

    assert projection.status is ProjectionStatus.UNRESOLVED
    assert projection.selected_assertion_ref is None
    assert projection.future_assertion_refs == (future.assertion_id,)


def test_expired_to_future_gap_is_stale_and_requires_review() -> None:
    expired = _assertion(
        "finish-mvp",
        valid_to=datetime(2026, 8, 2, 8, 0, tzinfo=UTC),
        source_suffix="expired",
    )
    future = _assertion(
        "add-layer",
        actor=OTHER_USER,
        valid_from=datetime(2026, 8, 3, 8, 0, tzinfo=UTC),
        source_suffix="future",
    )

    projection = _projection([future, expired])

    assert projection.status is ProjectionStatus.STALE
    assert projection.review_required is True


def test_circular_retractions_fail_closed_as_superseded_projection() -> None:
    first = _assertion("finish-mvp", source_suffix="first")
    second = _assertion(
        "add-layer",
        actor=OTHER_USER,
        source_suffix="second",
    )
    relations = [
        _relation(AssertionRelationType.RETRACTS, first, second),
        _relation(AssertionRelationType.RETRACTS, second, first),
    ]

    projection = _projection([first, second], relations)

    assert projection.status is ProjectionStatus.SUPERSEDED
    assert projection.selected_assertion_ref is None
    assert set(projection.retracted_assertion_refs) == {
        first.assertion_id,
        second.assertion_id,
    }


def test_missing_relation_endpoint_fails_closed() -> None:
    assertion = _assertion("finish-mvp", source_suffix="assertion")
    relation = AssertionRelation.create(
        relation_type=AssertionRelationType.SUPPORTS,
        source_assertion_ref=assertion.assertion_id,
        target_assertion_ref="missing:assertion",
        evidence_refs=("evidence:missing",),
        actor_ref=OPERATOR,
        created_at=AS_OF,
    )

    with pytest.raises(StateReconciliationError, match="endpoint missing"):
        StateReconciler().reconcile(
            [assertion],
            [relation],
            as_of=AS_OF,
        )


def test_lifecycle_relation_cannot_cross_state_keys() -> None:
    source = _assertion("finish-mvp", source_suffix="source")
    target = _assertion(
        "finish-other",
        subject=OTHER_PROJECT,
        source_suffix="target",
    )
    relation = _relation(
        AssertionRelationType.SUPERSEDES,
        source,
        target,
    )

    with pytest.raises(StateReconciliationError, match="one state key"):
        StateReconciler().reconcile(
            [source, target],
            [relation],
            as_of=AS_OF,
        )


def test_input_order_does_not_change_result_or_projection_identity() -> None:
    first = _assertion("finish-mvp", source_suffix="first")
    second = _assertion(
        "finish-mvp",
        origin=OriginType.DOCUMENT_STATED,
        actor=OPERATOR,
        source_suffix="second",
    )
    relation = _relation(AssertionRelationType.SUPPORTS, second, first)

    forward = StateReconciler().reconcile(
        [first, second],
        [relation],
        as_of=AS_OF,
    )
    reverse = StateReconciler().reconcile(
        [second, first],
        [relation],
        as_of=AS_OF,
    )

    assert forward.result_id == reverse.result_id
    assert forward.canonical_bytes() == reverse.canonical_bytes()
    assert (
        forward.projections[0].projection_id
        == reverse.projections[0].projection_id
    )


def test_projection_is_immutable_and_has_no_epistemic_or_action_authority() -> None:
    assertion = _assertion("finish-mvp", source_suffix="assertion")
    projection = _projection([assertion])

    with pytest.raises(FrozenInstanceError):
        projection.status = ProjectionStatus.CONTESTED  # type: ignore[misc]

    for forbidden in (
        "epistemic_state",
        "truth_status",
        "canon_write",
        "advice",
        "action_decision",
        "processing_mode",
    ):
        assert not hasattr(projection, forbidden)
