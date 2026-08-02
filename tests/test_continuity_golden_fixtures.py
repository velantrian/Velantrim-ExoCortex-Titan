"""Golden-vector conformance tests for continuity contract v1."""

from __future__ import annotations

from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path

from core.continuity import (
    CONTINUITY_SCHEMA_VERSION,
    ActorKind,
    ActorRef,
    AssertionRecord,
    AssertionRelation,
    AssertionRelationType,
    InteractionEvent,
    InteractionEventType,
    OriginType,
    SensitivityCategory,
    SensitivityLevel,
    SubjectKind,
    SubjectRef,
    Visibility,
)

_FIXTURE_PATH = Path(__file__).parent / "fixtures" / "continuity_contracts_v1.json"


def _load_vectors() -> dict[str, dict[str, object]]:
    payload = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))
    assert payload["schema_version"] == CONTINUITY_SCHEMA_VERSION
    return payload["vectors"]


def _datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _actor(payload: dict[str, str]) -> ActorRef:
    return ActorRef(actor_id=payload["actor_id"], kind=ActorKind(payload["kind"]))


def _subject(payload: dict[str, str]) -> SubjectRef:
    return SubjectRef(subject_id=payload["subject_id"], kind=SubjectKind(payload["kind"]))


def _build_assertion(vector: dict[str, object]) -> AssertionRecord:
    payload = vector["input"]
    assert isinstance(payload, dict)
    valid_from = _datetime(payload["valid_from"])
    recorded_at = _datetime(payload["recorded_at"])
    assert valid_from is not None and recorded_at is not None
    return AssertionRecord.create(
        subject_ref=_subject(payload["subject_ref"]),
        predicate=payload["predicate"],
        value=payload["value"],
        origin_type=OriginType(payload["origin_type"]),
        source_refs=payload["source_refs"],
        asserted_by=_actor(payload["asserted_by"]),
        valid_from=valid_from,
        valid_to=_datetime(payload["valid_to"]),
        recorded_at=recorded_at,
        visibility=Visibility(payload["visibility"]),
        sensitivity_category=SensitivityCategory(payload["sensitivity_category"]),
        sensitivity_level=SensitivityLevel(payload["sensitivity_level"]),
    )


def test_fixture_canonical_json_matches_expected_sha256() -> None:
    for vector in _load_vectors().values():
        canonical_json = vector["canonical_json"]
        expected_hash = vector["sha256"]
        assert isinstance(canonical_json, str)
        assert isinstance(expected_hash, str)
        assert sha256(canonical_json.encode("utf-8")).hexdigest() == expected_hash


def test_interaction_event_matches_golden_vector() -> None:
    vector = _load_vectors()["interaction_event"]
    payload = vector["input"]
    assert isinstance(payload, dict)
    occurred_at = _datetime(payload["occurred_at"])
    recorded_at = _datetime(payload["recorded_at"])
    assert occurred_at is not None and recorded_at is not None

    event = InteractionEvent.create(
        event_type=InteractionEventType(payload["event_type"]),
        actor_ref=_actor(payload["actor_ref"]),
        subject_refs=tuple(_subject(item) for item in payload["subject_refs"]),
        session_ref=payload["session_ref"],
        content_ref=payload["content_ref"],
        occurred_at=occurred_at,
        recorded_at=recorded_at,
        visibility=Visibility(payload["visibility"]),
        sensitivity_category=SensitivityCategory(payload["sensitivity_category"]),
        sensitivity_level=SensitivityLevel(payload["sensitivity_level"]),
    )

    assert event.canonical_bytes().decode("utf-8") == vector["canonical_json"]
    assert event.event_id == vector["sha256"]
    assert event.payload_hash == vector["sha256"]
    assert tuple(subject.subject_id for subject in event.subject_refs) == (
        "project:titan",
        "system:titan",
    )


def test_assertions_match_golden_vectors() -> None:
    vectors = _load_vectors()
    for name in ("assertion_primary", "assertion_secondary"):
        assertion = _build_assertion(vectors[name])
        assert assertion.canonical_bytes().decode("utf-8") == vectors[name]["canonical_json"]
        assert assertion.assertion_id == vectors[name]["sha256"]
        assert assertion.payload_hash == vectors[name]["sha256"]


def test_assertion_relation_matches_golden_vector() -> None:
    vector = _load_vectors()["assertion_relation"]
    payload = vector["input"]
    assert isinstance(payload, dict)
    created_at = _datetime(payload["created_at"])
    assert created_at is not None

    relation = AssertionRelation.create(
        relation_type=AssertionRelationType(payload["relation_type"]),
        source_assertion_ref=payload["source_assertion_ref"],
        target_assertion_ref=payload["target_assertion_ref"],
        evidence_refs=payload["evidence_refs"],
        actor_ref=_actor(payload["actor_ref"]),
        created_at=created_at,
    )

    assert relation.canonical_bytes().decode("utf-8") == vector["canonical_json"]
    assert relation.relation_id == vector["sha256"]
    assert relation.payload_hash == vector["sha256"]
    assert relation.evidence_refs == tuple(sorted(payload["evidence_refs"]))
