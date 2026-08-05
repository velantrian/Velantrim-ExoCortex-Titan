from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta

import pytest

from core.continuity import (
    ActorKind,
    ActorRef,
    AssertionRecord,
    AssertionRelation,
    AssertionRelationType,
    ContinuityContractError,
    InteractionEvent,
    InteractionEventType,
    OriginType,
    SubjectKind,
    SubjectRef,
)

NOW = datetime(2026, 8, 2, 6, 30, tzinfo=UTC)


def actor() -> ActorRef:
    return ActorRef("user:ruslan", ActorKind.HUMAN)


def project() -> SubjectRef:
    return SubjectRef("project:titan", SubjectKind.PROJECT)


def test_interaction_event_identity_is_deterministic_and_subject_order_independent():
    system = SubjectRef("system:titan", SubjectKind.SOFTWARE_SYSTEM)
    first = InteractionEvent.create(
        event_type=InteractionEventType.MESSAGE,
        actor_ref=actor(),
        subject_refs=(system, project()),
        session_ref="session:1",
        content_ref="message:1",
        occurred_at=NOW,
        recorded_at=NOW,
    )
    second = InteractionEvent.create(
        event_type=InteractionEventType.MESSAGE,
        actor_ref=actor(),
        subject_refs=(project(), system),
        session_ref="session:1",
        content_ref="message:1",
        occurred_at=NOW,
        recorded_at=NOW,
    )
    assert first.event_id == second.event_id
    assert first.payload_hash == second.payload_hash
    assert first.canonical_bytes() == second.canonical_bytes()


def test_assertion_identity_is_deterministic_and_source_order_independent():
    first = AssertionRecord.create(
        subject_ref=project(),
        predicate="priority",
        value="mvp_first",
        origin_type=OriginType.USER_STATED,
        source_refs=("event:b", "event:a"),
        asserted_by=actor(),
        valid_from=NOW,
        recorded_at=NOW,
    )
    second = AssertionRecord.create(
        subject_ref=project(),
        predicate="priority",
        value="mvp_first",
        origin_type=OriginType.USER_STATED,
        source_refs=("event:a", "event:b"),
        asserted_by=actor(),
        valid_from=NOW,
        recorded_at=NOW,
    )
    assert first.assertion_id == second.assertion_id
    assert first.canonical_bytes() == second.canonical_bytes()


def test_changed_semantic_field_changes_assertion_hash():
    base = dict(
        subject_ref=project(),
        predicate="priority",
        origin_type=OriginType.USER_STATED,
        source_refs=("event:a",),
        asserted_by=actor(),
        valid_from=NOW,
        recorded_at=NOW,
    )
    first = AssertionRecord.create(value="mvp_first", **base)
    second = AssertionRecord.create(value="new_layer_first", **base)
    assert first.assertion_id != second.assertion_id


def test_contracts_are_immutable():
    reference = actor()
    with pytest.raises(FrozenInstanceError):
        reference.actor_id = "changed"  # type: ignore[misc]


def test_naive_datetime_is_rejected():
    naive = datetime(2026, 8, 2, 6, 30)
    with pytest.raises(ContinuityContractError, match="timezone-aware"):
        InteractionEvent.create(
            event_type=InteractionEventType.MESSAGE,
            actor_ref=actor(),
            subject_refs=(project(),),
            session_ref="session:1",
            content_ref="message:1",
            occurred_at=naive,
            recorded_at=NOW,
        )


def test_recorded_at_before_occurred_at_is_rejected():
    with pytest.raises(ContinuityContractError, match="cannot precede"):
        InteractionEvent.create(
            event_type=InteractionEventType.MESSAGE,
            actor_ref=actor(),
            subject_refs=(project(),),
            session_ref="session:1",
            content_ref="message:1",
            occurred_at=NOW,
            recorded_at=NOW - timedelta(seconds=1),
        )


def test_duplicate_provenance_refs_are_rejected():
    with pytest.raises(ContinuityContractError, match="duplicates"):
        AssertionRecord.create(
            subject_ref=project(),
            predicate="priority",
            value="mvp_first",
            origin_type=OriginType.USER_STATED,
            source_refs=("event:a", "event:a"),
            asserted_by=actor(),
            valid_from=NOW,
            recorded_at=NOW,
        )


def test_empty_provenance_is_rejected():
    with pytest.raises(ContinuityContractError, match="cannot be empty"):
        AssertionRecord.create(
            subject_ref=project(),
            predicate="priority",
            value="mvp_first",
            origin_type=OriginType.USER_STATED,
            source_refs=(),
            asserted_by=actor(),
            valid_from=NOW,
            recorded_at=NOW,
        )


def test_mutable_or_nested_assertion_value_is_rejected():
    with pytest.raises(ContinuityContractError, match="JSON scalar"):
        AssertionRecord.create(
            subject_ref=project(),
            predicate="settings",
            value={"mode": "deep"},  # type: ignore[arg-type]
            origin_type=OriginType.USER_STATED,
            source_refs=("event:a",),
            asserted_by=actor(),
            valid_from=NOW,
            recorded_at=NOW,
        )


def test_non_finite_float_is_rejected():
    with pytest.raises(ContinuityContractError, match="finite"):
        AssertionRecord.create(
            subject_ref=project(),
            predicate="score",
            value=float("nan"),
            origin_type=OriginType.SYSTEM_MEASURED,
            source_refs=("event:a",),
            asserted_by=ActorRef("component:metrics", ActorKind.TITAN_COMPONENT),
            valid_from=NOW,
            recorded_at=NOW,
        )


def test_valid_to_before_valid_from_is_rejected():
    with pytest.raises(ContinuityContractError, match="valid_to"):
        AssertionRecord.create(
            subject_ref=project(),
            predicate="priority",
            value="mvp_first",
            origin_type=OriginType.USER_STATED,
            source_refs=("event:a",),
            asserted_by=actor(),
            valid_from=NOW,
            valid_to=NOW - timedelta(days=1),
            recorded_at=NOW,
        )


def test_relation_requires_distinct_assertions_and_evidence():
    with pytest.raises(ContinuityContractError, match="distinct"):
        AssertionRelation.create(
            relation_type=AssertionRelationType.CONTRADICTS,
            source_assertion_ref="assertion:a",
            target_assertion_ref="assertion:a",
            evidence_refs=("event:a",),
            actor_ref=actor(),
            created_at=NOW,
        )


def test_relation_identity_is_evidence_order_independent():
    first = AssertionRelation.create(
        relation_type=AssertionRelationType.SUPERSEDES,
        source_assertion_ref="assertion:new",
        target_assertion_ref="assertion:old",
        evidence_refs=("event:b", "event:a"),
        actor_ref=actor(),
        created_at=NOW,
    )
    second = AssertionRelation.create(
        relation_type=AssertionRelationType.SUPERSEDES,
        source_assertion_ref="assertion:new",
        target_assertion_ref="assertion:old",
        evidence_refs=("event:a", "event:b"),
        actor_ref=actor(),
        created_at=NOW,
    )
    assert first.relation_id == second.relation_id
    assert first.canonical_bytes() == second.canonical_bytes()


def test_assertion_record_has_no_mutable_lifecycle_status():
    record = AssertionRecord.create(
        subject_ref=project(),
        predicate="priority",
        value="mvp_first",
        origin_type=OriginType.USER_STATED,
        source_refs=("event:a",),
        asserted_by=actor(),
        valid_from=NOW,
        recorded_at=NOW,
    )
    assert not hasattr(record, "status")
    assert not hasattr(record, "supersedes_id")
    assert not hasattr(record, "contradicted_by")
