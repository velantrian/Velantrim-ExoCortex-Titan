"""Immutable, deterministic contracts for Titan continuity foundations.

These contracts describe neutral interactions, assertions, and relations. They
carry no Canon, TruthGate, advisory, action, or compute authority.
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


def _require_text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContinuityContractError(f"{field_name} must be a non-empty string")
    return value


def _normalize_text(value: str) -> str:
    if not isinstance(value, str):
        raise ContinuityContractError("canonical text values must be strings")
    return unicodedata.normalize("NFC", value)


def _require_aware_datetime(value: datetime, field_name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ContinuityContractError(f"{field_name} must be timezone-aware")
    return value


def _canonical_datetime(value: datetime) -> str:
    aware = _require_aware_datetime(value, "datetime")
    return aware.astimezone(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _canonical_json(payload: object) -> str:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _stable_digest(payload: object) -> str:
    return sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _validate_hash(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
        raise ContinuityContractError(f"{field_name} must be a lowercase SHA-256 hex digest")
    return value


def _canonical_refs(values: Iterable[str], field_name: str, *, required: bool) -> tuple[str, ...]:
    result = tuple(values)
    for value in result:
        _require_text(value, field_name)
    if required and not result:
        raise ContinuityContractError(f"{field_name} cannot be empty")
    if len(set(result)) != len(result):
        raise ContinuityContractError(f"{field_name} cannot contain duplicates")
    return tuple(sorted(result))


def _canonical_subjects(values: Iterable[SubjectRef]) -> tuple[SubjectRef, ...]:
    result = tuple(values)
    if any(not isinstance(value, SubjectRef) for value in result):
        raise ContinuityContractError("subject_refs must contain SubjectRef values")
    keys = [(value.subject_id, value.kind.value) for value in result]
    if len(set(keys)) != len(keys):
        raise ContinuityContractError("subject_refs cannot contain duplicates")
    return tuple(sorted(result, key=lambda value: (value.subject_id, value.kind.value)))


def _validate_scalar(value: JsonScalar) -> JsonScalar:
    if isinstance(value, float) and not math.isfinite(value):
        raise ContinuityContractError("assertion value float must be finite")
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise ContinuityContractError("assertion value must be a JSON scalar")


@dataclass(frozen=True, slots=True)
class ActorRef:
    actor_id: str
    kind: ActorKind

    def __post_init__(self) -> None:
        _require_text(self.actor_id, "actor_id")
        if not isinstance(self.kind, ActorKind):
            raise ContinuityContractError("kind must be an ActorKind")

    def identity_payload(self) -> dict[str, str]:
        return {"actor_id": _normalize_text(self.actor_id), "kind": self.kind.value}


@dataclass(frozen=True, slots=True)
class SubjectRef:
    subject_id: str
    kind: SubjectKind

    def __post_init__(self) -> None:
        _require_text(self.subject_id, "subject_id")
        if not isinstance(self.kind, SubjectKind):
            raise ContinuityContractError("kind must be a SubjectKind")

    def identity_payload(self) -> dict[str, str]:
        return {"subject_id": _normalize_text(self.subject_id), "kind": self.kind.value}


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
        _require_text(self.event_id, "event_id")
        _require_text(self.schema_version, "schema_version")
        if not isinstance(self.event_type, InteractionEventType):
            raise ContinuityContractError("event_type must be an InteractionEventType")
        if not isinstance(self.actor_ref, ActorRef):
            raise ContinuityContractError("actor_ref must be an ActorRef")
        object.__setattr__(self, "subject_refs", _canonical_subjects(self.subject_refs))
        _require_text(self.session_ref, "session_ref")
        _require_text(self.content_ref, "content_ref")
        _require_aware_datetime(self.occurred_at, "occurred_at")
        _require_aware_datetime(self.recorded_at, "recorded_at")
        if self.recorded_at.astimezone(UTC) < self.occurred_at.astimezone(UTC):
            raise ContinuityContractError("recorded_at cannot precede occurred_at")
        if not isinstance(self.visibility, Visibility):
            raise ContinuityContractError("visibility must be a Visibility")
        if not isinstance(self.sensitivity_category, SensitivityCategory):
            raise ContinuityContractError("sensitivity_category must be a SensitivityCategory")
        if not isinstance(self.sensitivity_level, SensitivityLevel):
            raise ContinuityContractError("sensitivity_level must be a SensitivityLevel")
        _validate_hash(self.payload_hash, "payload_hash")
        expected = _stable_digest(self.identity_payload())
        if self.event_id != expected or self.payload_hash != expected:
            raise ContinuityContractError("event_id and payload_hash must match event content")

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
        canonical_subjects = _canonical_subjects(subject_refs)
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
        digest = _stable_digest(payload)
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
        return {
            "schema_version": _normalize_text(schema_version),
            "event_type": event_type.value,
            "actor_ref": actor_ref.identity_payload(),
            "subject_refs": [value.identity_payload() for value in subject_refs],
            "session_ref": _normalize_text(session_ref),
            "content_ref": _normalize_text(content_ref),
            "occurred_at": _canonical_datetime(occurred_at),
            "recorded_at": _canonical_datetime(recorded_at),
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
        _require_text(self.assertion_id, "assertion_id")
        _require_text(self.schema_version, "schema_version")
        if not isinstance(self.subject_ref, SubjectRef):
            raise ContinuityContractError("subject_ref must be a SubjectRef")
        _require_text(self.predicate, "predicate")
        object.__setattr__(self, "value", _validate_scalar(self.value))
        if not isinstance(self.origin_type, OriginType):
            raise ContinuityContractError("origin_type must be an OriginType")
        object.__setattr__(
            self, "source_refs", _canonical_refs(self.source_refs, "source_refs", required=True)
        )
        if not isinstance(self.asserted_by, ActorRef):
            raise ContinuityContractError("asserted_by must be an ActorRef")
        _require_aware_datetime(self.valid_from, "valid_from")
        if self.valid_to is not None:
            _require_aware_datetime(self.valid_to, "valid_to")
            if self.valid_to.astimezone(UTC) < self.valid_from.astimezone(UTC):
                raise ContinuityContractError("valid_to cannot precede valid_from")
        _require_aware_datetime(self.recorded_at, "recorded_at")
        if not isinstance(self.visibility, Visibility):
            raise ContinuityContractError("visibility must be a Visibility")
        if not isinstance(self.sensitivity_category, SensitivityCategory):
            raise ContinuityContractError("sensitivity_category must be a SensitivityCategory")
        if not isinstance(self.sensitivity_level, SensitivityLevel):
            raise ContinuityContractError("sensitivity_level must be a SensitivityLevel")
        _validate_hash(self.payload_hash, "payload_hash")
        expected = _stable_digest(self.identity_payload())
        if self.assertion_id != expected or self.payload_hash != expected:
            raise ContinuityContractError(
                "assertion_id and payload_hash must match assertion content"
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
        canonical_refs = _canonical_refs(source_refs, "source_refs", required=True)
        scalar = _validate_scalar(value)
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
        digest = _stable_digest(payload)
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
        return {
            "schema_version": _normalize_text(schema_version),
            "subject_ref": subject_ref.identity_payload(),
            "predicate": _normalize_text(predicate),
            "value": _normalize_text(value) if isinstance(value, str) else value,
            "origin_type": origin_type.value,
            "source_refs": [_normalize_text(value) for value in source_refs],
            "asserted_by": asserted_by.identity_payload(),
            "valid_from": _canonical_datetime(valid_from),
            "valid_to": _canonical_datetime(valid_to) if valid_to is not None else None,
            "recorded_at": _canonical_datetime(recorded_at),
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
        _require_text(self.relation_id, "relation_id")
        _require_text(self.schema_version, "schema_version")
        if not isinstance(self.relation_type, AssertionRelationType):
            raise ContinuityContractError(
                "relation_type must be an AssertionRelationType"
            )
        _require_text(self.source_assertion_ref, "source_assertion_ref")
        _require_text(self.target_assertion_ref, "target_assertion_ref")
        if self.source_assertion_ref == self.target_assertion_ref:
            raise ContinuityContractError("assertion relation endpoints must be distinct")
        object.__setattr__(
            self,
            "evidence_refs",
            _canonical_refs(self.evidence_refs, "evidence_refs", required=True),
        )
        if not isinstance(self.actor_ref, ActorRef):
            raise ContinuityContractError("actor_ref must be an ActorRef")
        _require_aware_datetime(self.created_at, "created_at")
        _validate_hash(self.payload_hash, "payload_hash")
        expected = _stable_digest(self.identity_payload())
        if self.relation_id != expected or self.payload_hash != expected:
            raise ContinuityContractError(
                "relation_id and payload_hash must match relation content"
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
        canonical_refs = _canonical_refs(evidence_refs, "evidence_refs", required=True)
        payload = cls._identity_payload(
            schema_version=schema_version,
            relation_type=relation_type,
            source_assertion_ref=source_assertion_ref,
            target_assertion_ref=target_assertion_ref,
            evidence_refs=canonical_refs,
            actor_ref=actor_ref,
            created_at=created_at,
        )
        digest = _stable_digest(payload)
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
        return {
            "schema_version": _normalize_text(schema_version),
            "relation_type": relation_type.value,
            "source_assertion_ref": _normalize_text(source_assertion_ref),
            "target_assertion_ref": _normalize_text(target_assertion_ref),
            "evidence_refs": [_normalize_text(value) for value in evidence_refs],
            "actor_ref": actor_ref.identity_payload(),
            "created_at": _canonical_datetime(created_at),
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
