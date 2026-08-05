"""R1 regression tests discovered during current-main continuity recovery."""

from __future__ import annotations

from datetime import UTC, datetime
import json

from core.continuity import (
    ActorKind,
    ActorRef,
    AssertionRecord,
    OriginType,
    SensitivityCategory,
    SensitivityLevel,
    SubjectKind,
    SubjectRef,
    Visibility,
)

NOW = datetime(2026, 8, 5, 14, 0, tzinfo=UTC)


def _assertion(value: str) -> AssertionRecord:
    return AssertionRecord.create(
        subject_ref=SubjectRef("person:001", SubjectKind.PERSON),
        predicate="preferred_name",
        value=value,
        origin_type=OriginType.USER_STATED,
        source_refs=("event:001",),
        asserted_by=ActorRef("user:001", ActorKind.HUMAN),
        valid_from=NOW,
        recorded_at=NOW,
        visibility=Visibility.PRIVATE,
        sensitivity_category=SensitivityCategory.PERSONAL,
        sensitivity_level=SensitivityLevel.NORMAL,
    )


def test_string_assertion_values_are_nfc_canonicalized() -> None:
    composed = _assertion("Café")
    decomposed = _assertion("Cafe\u0301")

    assert composed == decomposed
    assert composed.value == "Café"
    assert composed.assertion_id == decomposed.assertion_id
    assert composed.canonical_bytes() == decomposed.canonical_bytes()


def test_origin_does_not_become_truth_or_projection_status() -> None:
    record = AssertionRecord.create(
        subject_ref=SubjectRef("project:titan", SubjectKind.PROJECT),
        predicate="candidate_priority",
        value="finish_mvp_first",
        origin_type=OriginType.MODEL_INFERRED,
        source_refs=("event:inference",),
        asserted_by=ActorRef("component:model", ActorKind.TITAN_COMPONENT),
        valid_from=NOW,
        recorded_at=NOW,
    )

    serialized = json.dumps(record.identity_payload(), sort_keys=True)
    assert record.origin_type is OriginType.MODEL_INFERRED
    assert "truth" not in serialized.lower()
    assert "projection_status" not in serialized
    assert not hasattr(record, "admit")
    assert not hasattr(record, "write")
    assert not hasattr(record, "execute")
