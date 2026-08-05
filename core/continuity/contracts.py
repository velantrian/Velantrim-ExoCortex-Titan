"""Immutable, deterministic contracts for Titan continuity foundations.

These contracts describe neutral interaction evidence, typed assertions, and explicit
relations between assertions. They carry no Canon, TruthGate, compute-routing,
advisory, response, persistence, or action authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from hashlib import sha256
import json
import math
import re
from typing import Iterable, TypeAlias
import unicodedata

CONTINUITY_SCHEMA_VERSION = "continuity.contracts.v1"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

JsonScalar: TypeAlias = str | int | float | bool | None


class ContinuityContractError(ValueError):
    """Raised when a continuity contract invariant is violated."""


class ActorKind(str, Enum):
    HUMAN = "human"
    TITAN_COMPONENT = "titan_component"
    EXTERNAL_AGENT = "external_agent"
    TOOL = "tool"
    SERVICE = "service"
    OPERATOR = "operator"
    SYSTEM = "system"


class SubjectKind(str, Enum):
    PERSON = "person"
    GROUP = "group"
    ORGANIZATION = "organization"
    PROJECT = "project"
    SOFTWARE_SYSTEM = "software_system"
    AGENT = "agent"
    ENVIRONMENT = "environment"


class InteractionEventType(str, Enum):
    MESSAGE = "message"
    TOOL_RESULT = "tool_result"
    DECISION = "decision"
    ACTION = "action"
    OBSERVATION = "observation"
    DOCUMENT_ADDED = "document_added"
    STATE_CORRECTION = "state_correction"
    ERASURE_REQUESTED = "erasure_requested"


class OriginType(str, Enum):
    USER_STATED = "user_stated"
    DOCUMENT_STATED = "document_stated"
    SYSTEM_OBSERVED = "system_observed"
    SYSTEM_MEASURED = "system_measured"
    MODEL_INFERRED = "model_inferred"
    EXTERNAL_STATED = "external_stated"


class AssertionRelationType(str, Enum):
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    SUPERSEDES = "supersedes"
    CORRECTS = "corrects"
    RETRACTS = "retracts"
    DUPLICATES = "duplicates"
    REFINES = "refines"


class Visibility(str, Enum):
    PRIVATE = "private"
    SUBJECT_ONLY = "subject_only"
    SHARED_WITH_GROUP = "shared_with_group"
    ORGANIZATION = "organization"
    PUBLIC = "public"


class SensitivityCategory(str, Enum):
    NORMAL = "normal"
    PERSONAL = "personal"
    PII = "pii"
    HEALTH_RELATED = "health_related"
    FINANCIAL = "financial"
    POLITICAL = "political"
    PSYCHOLOGICAL = "psychological"


class SensitivityLevel(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


def _text(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise ContinuityContractError(f"{field_name} must be a string")
    normalized = unicodedata.normalize("NFC", value)
    if not normalized.strip():
        raise ContinuityContractError(f"{field_name} must be non-empty")
    return normalized


def _aware(value: object, field_name: str) -> datetime:
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise ContinuityContractError(f"{field_name} must be timezone-aware")
    return value


def _canonical_datetime(value: datetime) -> str:
    return (
        _aware(value, "datetime")
        .astimezone(UTC)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def _canonical_json(payload: object) -> str:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _digest(payload: object) -> str:
    return sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _hash(value: object, field_name: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise ContinuityContractError(
            f"{field_name} must be a lowercase SHA-256 hex digest"
        )
    return value


def _refs(
    values: Iterable[str],
    field_name: str,
    *,
    required: bool,
) -> tuple[str, ...]:
    refs = tuple(_text(value, field_name) for value in values)
    if required and not refs:
        raise ContinuityContractError(f"{field_name} cannot be empty")
    if len(refs) != len(set(refs)):
        raise ContinuityContractError(f"{field_name} cannot contain duplicates")
    return tuple(sorted(refs))


def _scalar(value: object) -> JsonScalar:
    if value is None:
        return None
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ContinuityContractError("assertion value float must be finite")
        return value
    raise ContinuityContractError("assertion value must be a JSON scalar")


@dataclass(frozen=True, slots=True)
class ActorRef:
    actor_id: str
    kind: ActorKind

    def __post_init__(self) -> None:
        object.__setattr__(self, "actor_id", _text(self.actor_id, "actor_id"))
        if not isinstance(self.kind, ActorKind):
            raise ContinuityContractError("kind must be an ActorKind")

    def identity_payload(self) -> dict[str, str]:
        return {"actor_id": self.actor_id, "kind": self.kind.value}


@dataclass(frozen=True, slots=True)
class SubjectRef:
    subject_id: str
    kind: SubjectKind

    def __post_init__(self) -> None:
        object.__setattr__(self, "subject_id", _text(self.subject_id, "subject_id"))
        if not isinstance(self.kind, SubjectKind):
            raise ContinuityContractError("kind must be a SubjectKind")

    def identity_payload(self) -> dict[str, str]:
        return {"subject_id": self.subject_id, "kind": self.kind.value}


def _subjects(values: Iterable[SubjectRef]) -> tuple[SubjectRef, ...]:
    subjects = tuple(values)
    if any(not isinstance(value, SubjectRef) for value in subjects):
        raise ContinuityContractError(
            "subject_refs must contain SubjectRef values"
        )
    keys = tuple((value.subject_id, value.kind.value) for value in subjects)
    if len(keys) != len(set(keys)):
        raise ContinuityContractError("subject_refs cannot contain duplicates")
    return tuple(
        sorted(subjects, key=lambda value: (value.subject_id, value.kind.value))
    )


@dataclass(frozen=True, slots=True)
class InteractionEvent:
    event_id: str
    schema_version: str
    event_type: InteractionEventType
    actor_ref: ActorRef
    subject_refs: tuple[SubjectRef, ...]
    session_ref: str
    content_ref: str
    occurred_at: datetime
    recorded_at: datetime
    visibility: Visibility
    sensitivity_category: SensitivityCategory
    sensitivity_level: SensitivityLevel
    payload_hash: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "schema_version",
            _text(self.schema_version, "schema_version"),
        )
        if not isinstance(self.event_type, InteractionEventType):
            raise ContinuityContractError(
                "event_type must be an InteractionEventType"
            )
        if not isinstance(self.actor_ref, ActorRef):
            raise ContinuityContractError("actor_ref must be an ActorRef")
        object.__setattr__(self, "subject_refs", _subjects(self.subject_refs))
        object.__setattr__(
            self,
            "session_ref",
            _text(self.session_ref, "session_ref"),
        )
        object.__setattr__(
            self,
            "content_ref",
            _text(self.content_ref, "content_ref"),
        )
        _aware(self.occurred_at, "occurred_at")
        _aware(self.recorded_at, "recorded_at")
        if self.recorded_at.astimezone(UTC) < self.occurred_at.astimezone(UTC):
            raise ContinuityContractError(
                "recorded_at cannot precede occurred_at"
            )
        if not isinstance(self.visibility, Visibility):
            raise ContinuityContractError("visibility must be a Visibility")
        if not isinstance(self.sensitivity_category, SensitivityCategory):
            raise ContinuityContractError(
                "sensitivity_category must be a SensitivityCategory"
            )
        if not isinstance(self.sensitivity_level, SensitivityLevel):
            raise ContinuityContractError(
                "sensitivity_level must be a SensitivityLevel"
            )
        _hash(self.event_id, "event_id")
        _hash(self.payload_hash, "payload_hash")
        expected = _digest(self.identity_payload())
        if self.event_id != expected or self.payload_hash != expected:
            raise ContinuityContractError(
                "event_id and payload_hash must match canonical event content"
            )

    @classmethod
    def create(
        cls,
        *,
        event_type: InteractionEventType,
        actor_ref: ActorRef,
        subject_refs: Iterable[SubjectRef],
        session_ref: str,
        content_ref: str,
        occurred_at: datetime,
        recorded_at: datetime,
        visibility: Visibility = Visibility.PRIVATE,
        sensitivity_category: SensitivityCategory = SensitivityCategory.NORMAL,
        sensitivity_level: SensitivityLevel = SensitivityLevel.NORMAL,
        schema_version: str = CONTINUITY_SCHEMA_VERSION,
    ) -> InteractionEvent:
        canonical_subjects = _subjects(subject_refs)
        payload = cls._identity_payload(
            schema_version=schema_version,
            event_type=event_type,
            actor_ref=actor_ref,
            subject_refs=canonical_subjects,
            session_ref=session_ref,
            content_ref=content_ref,
            occurred_at=occurred_at,
            recorded_at=recorded_at,
            visibility=visibility,
            sensitivity_category=sensitivity_category,
            sensitivity_level=sensitivity_level,
        )
        digest = _digest(payload)
        return cls(
            event_id=digest,
            schema_version=schema_version,
            event_type=event_type,
            actor_ref=actor_ref,
            subject_refs=canonical_subjects,
            session_ref=session_ref,
            content_ref=content_ref,
            occurred_at=occurred_at,
            recorded_at=recorded_at,
            visibility=visibility,
            sensitivity_category=sensitivity_category,
            sensitivity_level=sensitivity_level,
            payload_hash=digest,
        )

    @staticmethod
    def _identity_payload(
        *,
        schema_version: str,
        event_type: InteractionEventType,
        actor_ref: ActorRef,
        subject_refs: tuple[SubjectRef, ...],
        session_ref: str,
        content_ref: str,
        occurred_at: datetime,
        recorded_at: datetime,
        visibility: Visibility,
        sensitivity_category: SensitivityCategory,
        sensitivity_level: SensitivityLevel,
    ) -> dict[str, object]:
        if not isinstance(event_type, InteractionEventType):
            raise ContinuityContractError(
                "event_type must be an InteractionEventType"
            )
        if not isinstance(actor_ref, ActorRef):
            raise ContinuityContractError("actor_ref must be an ActorRef")
        if not isinstance(visibility, Visibility):
            raise ContinuityContractError("visibility must be a Visibility")
        if not isinstance(sensitivity_category, SensitivityCategory):
            raise ContinuityContractError(
                "sensitivity_category must be a SensitivityCategory"
            )
        if not isinstance(sensitivity_level, SensitivityLevel):
            raise ContinuityContractError(
                "sensitivity_level must be a SensitivityLevel"
            )
        occurred = _aware(occurred_at, "occurred_at")
        recorded = _aware(recorded_at, "recorded_at")
        if recorded.astimezone(UTC) < occurred.astimezone(UTC):
            raise ContinuityContractError(
                "recorded_at cannot precede occurred_at"
            )
        return {
            "schema_version": _text(schema_version, "schema_version"),
            "event_type": event_type.value,
            "actor_ref": actor_ref.identity_payload(),
            "subject_refs": [value.identity_payload() for value in subject_refs],
            "session_ref": _text(session_ref, "session_ref"),
            "content_ref": _text(content_ref, "content_ref"),
            "occurred_at": _canonical_datetime(occurred),
            "recorded_at": _canonical_datetime(recorded),
            "visibility": visibility.value,
            "sensitivity_category": sensitivity_category.value,
            "sensitivity_level": sensitivity_level.value,
        }

    def identity_payload(self) -> dict[str, object]:
        return self._identity_payload(
            schema_version=self.schema_version,
            event_type=self.event_type,
            actor_ref=self.actor_ref,
            subject_refs=self.subject_refs,
            session_ref=self.session_ref,
            content_ref=self.content_ref,
            occurred_at=self.occurred_at,
            recorded_at=self.recorded_at,
            visibility=self.visibility,
            sensitivity_category=self.sensitivity_category,
            sensitivity_level=self.sensitivity_level,
        )

    def canonical_bytes(self) -> bytes:
        return _canonical_json(self.identity_payload()).encode("utf-8")


@dataclass(frozen=True, slots=True)
class AssertionRecord:
    assertion_id: str
    schema_version: str
    subject_ref: SubjectRef
    predicate: str
    value: JsonScalar
    origin_type: OriginType
    source_refs: tuple[str, ...]
    asserted_by: ActorRef
    valid_from: datetime
    valid_to: datetime | None
    recorded_at: datetime
    visibility: Visibility
    sensitivity_category: SensitivityCategory
    sensitivity_level: SensitivityLevel
    payload_hash: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "schema_version",
            _text(self.schema_version, "schema_version"),
        )
        if not isinstance(self.subject_ref, SubjectRef):
            raise ContinuityContractError("subject_ref must be a SubjectRef")
        object.__setattr__(self, "predicate", _text(self.predicate, "predicate"))
        object.__setattr__(self, "value", _scalar(self.value))
        if not isinstance(self.origin_type, OriginType):
            raise ContinuityContractError("origin_type must be an OriginType")
        object.__setattr__(
            self,
            "source_refs",
            _refs(self.source_refs, "source_refs", required=True),
        )
        if not isinstance(self.asserted_by, ActorRef):
            raise ContinuityContractError("asserted_by must be an ActorRef")
        _aware(self.valid_from, "valid_from")
        if self.valid_to is not None:
            _aware(self.valid_to, "valid_to")
            if self.valid_to.astimezone(UTC) < self.valid_from.astimezone(UTC):
                raise ContinuityContractError(
                    "valid_to cannot precede valid_from"
                )
        _aware(self.recorded_at, "recorded_at")
        if not isinstance(self.visibility, Visibility):
            raise ContinuityContractError("visibility must be a Visibility")
        if not isinstance(self.sensitivity_category, SensitivityCategory):
            raise ContinuityContractError(
                "sensitivity_category must be a SensitivityCategory"
            )
        if not isinstance(self.sensitivity_level, SensitivityLevel):
            raise ContinuityContractError(
                "sensitivity_level must be a SensitivityLevel"
            )
        _hash(self.assertion_id, "assertion_id")
        _hash(self.payload_hash, "payload_hash")
        expected = _digest(self.identity_payload())
        if self.assertion_id != expected or self.payload_hash != expected:
            raise ContinuityContractError(
                "assertion_id and payload_hash must match canonical assertion content"
            )

    @classmethod
    def create(
        cls,
        *,
        subject_ref: SubjectRef,
        predicate: str,
        value: JsonScalar,
        origin_type: OriginType,
        source_refs: Iterable[str],
        asserted_by: ActorRef,
        valid_from: datetime,
        recorded_at: datetime,
        valid_to: datetime | None = None,
        visibility: Visibility = Visibility.PRIVATE,
        sensitivity_category: SensitivityCategory = SensitivityCategory.NORMAL,
        sensitivity_level: SensitivityLevel = SensitivityLevel.NORMAL,
        schema_version: str = CONTINUITY_SCHEMA_VERSION,
    ) -> AssertionRecord:
        canonical_refs = _refs(source_refs, "source_refs", required=True)
        scalar = _scalar(value)
        payload = cls._identity_payload(
            schema_version=schema_version,
            subject_ref=subject_ref,
            predicate=predicate,
            value=scalar,
            origin_type=origin_type,
            source_refs=canonical_refs,
            asserted_by=asserted_by,
            valid_from=valid_from,
            valid_to=valid_to,
            recorded_at=recorded_at,
            visibility=visibility,
            sensitivity_category=sensitivity_category,
            sensitivity_level=sensitivity_level,
        )
        digest = _digest(payload)
        return cls(
            assertion_id=digest,
            schema_version=schema_version,
            subject_ref=subject_ref,
            predicate=predicate,
            value=scalar,
            origin_type=origin_type,
            source_refs=canonical_refs,
            asserted_by=asserted_by,
            valid_from=valid_from,
            valid_to=valid_to,
            recorded_at=recorded_at,
            visibility=visibility,
            sensitivity_category=sensitivity_category,
            sensitivity_level=sensitivity_level,
            payload_hash=digest,
        )

    @staticmethod
    def _identity_payload(
        *,
        schema_version: str,
        subject_ref: SubjectRef,
        predicate: str,
        value: JsonScalar,
        origin_type: OriginType,
        source_refs: tuple[str, ...],
        asserted_by: ActorRef,
        valid_from: datetime,
        valid_to: datetime | None,
        recorded_at: datetime,
        visibility: Visibility,
        sensitivity_category: SensitivityCategory,
        sensitivity_level: SensitivityLevel,
    ) -> dict[str, object]:
        if not isinstance(subject_ref, SubjectRef):
            raise ContinuityContractError("subject_ref must be a SubjectRef")
        if not isinstance(origin_type, OriginType):
            raise ContinuityContractError("origin_type must be an OriginType")
        if not isinstance(asserted_by, ActorRef):
            raise ContinuityContractError("asserted_by must be an ActorRef")
        if not isinstance(visibility, Visibility):
            raise ContinuityContractError("visibility must be a Visibility")
        if not isinstance(sensitivity_category, SensitivityCategory):
            raise ContinuityContractError(
                "sensitivity_category must be a SensitivityCategory"
            )
        if not isinstance(sensitivity_level, SensitivityLevel):
            raise ContinuityContractError(
                "sensitivity_level must be a SensitivityLevel"
            )
        start = _aware(valid_from, "valid_from")
        end = _aware(valid_to, "valid_to") if valid_to is not None else None
        if end is not None and end.astimezone(UTC) < start.astimezone(UTC):
            raise ContinuityContractError("valid_to cannot precede valid_from")
        return {
            "schema_version": _text(schema_version, "schema_version"),
            "subject_ref": subject_ref.identity_payload(),
            "predicate": _text(predicate, "predicate"),
            "value": _scalar(value),
            "origin_type": origin_type.value,
            "source_refs": list(source_refs),
            "asserted_by": asserted_by.identity_payload(),
            "valid_from": _canonical_datetime(start),
            "valid_to": _canonical_datetime(end) if end is not None else None,
            "recorded_at": _canonical_datetime(
                _aware(recorded_at, "recorded_at")
            ),
            "visibility": visibility.value,
            "sensitivity_category": sensitivity_category.value,
            "sensitivity_level": sensitivity_level.value,
        }

    def identity_payload(self) -> dict[str, object]:
        return self._identity_payload(
            schema_version=self.schema_version,
            subject_ref=self.subject_ref,
            predicate=self.predicate,
            value=self.value,
            origin_type=self.origin_type,
            source_refs=self.source_refs,
            asserted_by=self.asserted_by,
            valid_from=self.valid_from,
            valid_to=self.valid_to,
            recorded_at=self.recorded_at,
            visibility=self.visibility,
            sensitivity_category=self.sensitivity_category,
            sensitivity_level=self.sensitivity_level,
        )

    def canonical_bytes(self) -> bytes:
        return _canonical_json(self.identity_payload()).encode("utf-8")


@dataclass(frozen=True, slots=True)
class AssertionRelation:
    relation_id: str
    schema_version: str
    relation_type: AssertionRelationType
    source_assertion_ref: str
    target_assertion_ref: str
    evidence_refs: tuple[str, ...]
    actor_ref: ActorRef
    created_at: datetime
    payload_hash: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "schema_version",
            _text(self.schema_version, "schema_version"),
        )
        if not isinstance(self.relation_type, AssertionRelationType):
            raise ContinuityContractError(
                "relation_type must be an AssertionRelationType"
            )
        object.__setattr__(
            self,
            "source_assertion_ref",
            _text(self.source_assertion_ref, "source_assertion_ref"),
        )
        object.__setattr__(
            self,
            "target_assertion_ref",
            _text(self.target_assertion_ref, "target_assertion_ref"),
        )
        if self.source_assertion_ref == self.target_assertion_ref:
            raise ContinuityContractError(
                "assertion relation requires distinct assertions"
            )
        object.__setattr__(
            self,
            "evidence_refs",
            _refs(self.evidence_refs, "evidence_refs", required=True),
        )
        if not isinstance(self.actor_ref, ActorRef):
            raise ContinuityContractError("actor_ref must be an ActorRef")
        _aware(self.created_at, "created_at")
        _hash(self.relation_id, "relation_id")
        _hash(self.payload_hash, "payload_hash")
        expected = _digest(self.identity_payload())
        if self.relation_id != expected or self.payload_hash != expected:
            raise ContinuityContractError(
                "relation_id and payload_hash must match canonical relation content"
            )

    @classmethod
    def create(
        cls,
        *,
        relation_type: AssertionRelationType,
        source_assertion_ref: str,
        target_assertion_ref: str,
        evidence_refs: Iterable[str],
        actor_ref: ActorRef,
        created_at: datetime,
        schema_version: str = CONTINUITY_SCHEMA_VERSION,
    ) -> AssertionRelation:
        canonical_refs = _refs(evidence_refs, "evidence_refs", required=True)
        payload = cls._identity_payload(
            schema_version=schema_version,
            relation_type=relation_type,
            source_assertion_ref=source_assertion_ref,
            target_assertion_ref=target_assertion_ref,
            evidence_refs=canonical_refs,
            actor_ref=actor_ref,
            created_at=created_at,
        )
        digest = _digest(payload)
        return cls(
            relation_id=digest,
            schema_version=schema_version,
            relation_type=relation_type,
            source_assertion_ref=source_assertion_ref,
            target_assertion_ref=target_assertion_ref,
            evidence_refs=canonical_refs,
            actor_ref=actor_ref,
            created_at=created_at,
            payload_hash=digest,
        )

    @staticmethod
    def _identity_payload(
        *,
        schema_version: str,
        relation_type: AssertionRelationType,
        source_assertion_ref: str,
        target_assertion_ref: str,
        evidence_refs: tuple[str, ...],
        actor_ref: ActorRef,
        created_at: datetime,
    ) -> dict[str, object]:
        if not isinstance(relation_type, AssertionRelationType):
            raise ContinuityContractError(
                "relation_type must be an AssertionRelationType"
            )
        source = _text(source_assertion_ref, "source_assertion_ref")
        target = _text(target_assertion_ref, "target_assertion_ref")
        if source == target:
            raise ContinuityContractError(
                "assertion relation requires distinct assertions"
            )
        if not isinstance(actor_ref, ActorRef):
            raise ContinuityContractError("actor_ref must be an ActorRef")
        return {
            "schema_version": _text(schema_version, "schema_version"),
            "relation_type": relation_type.value,
            "source_assertion_ref": source,
            "target_assertion_ref": target,
            "evidence_refs": list(evidence_refs),
            "actor_ref": actor_ref.identity_payload(),
            "created_at": _canonical_datetime(
                _aware(created_at, "created_at")
            ),
        }

    def identity_payload(self) -> dict[str, object]:
        return self._identity_payload(
            schema_version=self.schema_version,
            relation_type=self.relation_type,
            source_assertion_ref=self.source_assertion_ref,
            target_assertion_ref=self.target_assertion_ref,
            evidence_refs=self.evidence_refs,
            actor_ref=self.actor_ref,
            created_at=self.created_at,
        )

    def canonical_bytes(self) -> bytes:
        return _canonical_json(self.identity_payload()).encode("utf-8")


__all__ = [
    "CONTINUITY_SCHEMA_VERSION",
    "ActorKind",
    "ActorRef",
    "AssertionRecord",
    "AssertionRelation",
    "AssertionRelationType",
    "ContinuityContractError",
    "InteractionEvent",
    "InteractionEventType",
    "JsonScalar",
    "OriginType",
    "SensitivityCategory",
    "SensitivityLevel",
    "SubjectKind",
    "SubjectRef",
    "Visibility",
]
