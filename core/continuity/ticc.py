"""Typed Interaction Continuity Capture (TICC) shadow-only source adapter.

TICC preserves source-bound distinctions before semantic compression. It is an
explicit, in-memory/shadow adapter only: no persistence, Canon, TruthGate,
belief/identity, reply, tool/action, network, or runtime authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from hashlib import sha256
import json
import re
from typing import Iterable
import unicodedata

from .contracts import (
    ActorKind,
    ActorRef,
    AssertionRecord,
    InteractionEvent,
    InteractionEventType,
    JsonScalar,
    OriginType,
    SensitivityCategory,
    SensitivityLevel,
    SubjectRef,
    Visibility,
)

TICC_SCHEMA_VERSION = "continuity.ticc.v0_1.shadow"
TICC_ADAPTER_ID = "continuity.ticc.capture"
TICC_ADAPTER_VERSION = "0.1"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class TICCError(ValueError):
    """Raised when a TICC source/candidate invariant is violated."""


class TICCMode(str, Enum):
    SHADOW = "shadow"


class TICCDisposition(str, Enum):
    CAPTURED = "captured"
    CAPTURED_WITH_DECLARED_LOSS = "captured_with_declared_loss"
    DEFERRED = "deferred"
    REJECTED = "rejected"
    DISABLED = "disabled"


class TICCSemanticModality(str, Enum):
    ASSERTION = "assertion"
    DIRECTIVE = "directive"
    PROPOSAL = "proposal"
    RECOMMENDATION = "recommendation"
    DECISION = "decision"
    CORRECTION = "correction"
    RETRACTION = "retraction"
    EXAMPLE = "example"
    HYPOTHESIS = "hypothesis"
    PREDICTION = "prediction"
    SIMULATION = "simulation"
    PSEUDOCODE = "pseudocode"
    QUESTION = "question"
    UNRESOLVED = "unresolved"


class TICCReasonCode(str, Enum):
    SHADOW_FEATURE_DISABLED = "shadow_feature_disabled"
    SOURCE_DIGEST_MISMATCH = "source_digest_mismatch"
    SOURCE_SPAN_INVALID = "source_span_invalid"
    QUALIFIER_NOT_SOURCE_BOUND = "qualifier_not_source_bound"
    ACTOR_ORIGIN_MISMATCH = "actor_origin_mismatch"
    ASSERTION_SPEC_INCOMPLETE = "assertion_spec_incomplete"
    ASSERTION_NOT_PERMITTED_FOR_MODALITY = "assertion_not_permitted_for_modality"
    RELATION_NOT_IMPLEMENTED = "relation_not_implemented"
    CAPTURE_LOSS_DECLARED = "capture_loss_declared"
    NO_RUNTIME_AUTHORITY = "no_runtime_authority"


_ASSERTION_MODALITIES = {
    TICCSemanticModality.ASSERTION,
    TICCSemanticModality.DIRECTIVE,
    TICCSemanticModality.DECISION,
}
_RELATION_REQUIRED_MODALITIES = {
    TICCSemanticModality.CORRECTION,
    TICCSemanticModality.RETRACTION,
}


@dataclass(frozen=True, slots=True)
class TICCConfig:
    mode: TICCMode = TICCMode.SHADOW
    enabled: bool = False
    scenario_id: str = "ticc-v0_1-shadow"

    def __post_init__(self) -> None:
        if self.mode is not TICCMode.SHADOW:
            raise TICCError("only shadow mode is supported")
        if not isinstance(self.enabled, bool):
            raise TICCError("enabled must be a bool")
        if not isinstance(self.scenario_id, str) or not self.scenario_id.strip():
            raise TICCError("scenario_id must be non-empty")


@dataclass(frozen=True, slots=True)
class ConversationSourceTurn:
    turn_ref: str
    session_ref: str
    sequence: int
    event_type: InteractionEventType
    actor_ref: ActorRef
    subject_refs: tuple[SubjectRef, ...]
    raw_text: str
    occurred_at: datetime
    recorded_at: datetime
    visibility: Visibility = Visibility.PRIVATE
    sensitivity_category: SensitivityCategory = SensitivityCategory.NORMAL
    sensitivity_level: SensitivityLevel = SensitivityLevel.NORMAL
    raw_text_sha256: str = ""

    def __post_init__(self) -> None:
        _nonempty(self.turn_ref, "turn_ref")
        _nonempty(self.session_ref, "session_ref")
        if isinstance(self.sequence, bool) or not isinstance(self.sequence, int) or self.sequence <= 0:
            raise TICCError("sequence must be a positive integer")
        if not isinstance(self.event_type, InteractionEventType):
            raise TICCError("event_type must be InteractionEventType")
        if not isinstance(self.actor_ref, ActorRef):
            raise TICCError("actor_ref must be ActorRef")
        if any(not isinstance(value, SubjectRef) for value in self.subject_refs):
            raise TICCError("subject_refs must contain SubjectRef values")
        normalized = _normalize_text(self.raw_text, "raw_text")
        object.__setattr__(self, "raw_text", normalized)
        if not _aware(self.occurred_at) or not _aware(self.recorded_at):
            raise TICCError("timestamps must be timezone-aware")
        if self.recorded_at.astimezone(UTC) < self.occurred_at.astimezone(UTC):
            raise TICCError("recorded_at cannot precede occurred_at")
        if not isinstance(self.visibility, Visibility):
            raise TICCError("visibility must be Visibility")
        if not isinstance(self.sensitivity_category, SensitivityCategory):
            raise TICCError("sensitivity_category must be SensitivityCategory")
        if not isinstance(self.sensitivity_level, SensitivityLevel):
            raise TICCError("sensitivity_level must be SensitivityLevel")
        if not isinstance(self.raw_text_sha256, str) or _SHA256_RE.fullmatch(self.raw_text_sha256) is None:
            raise TICCError("raw_text_sha256 must be lowercase SHA-256")
        expected = sha256(normalized.encode("utf-8")).hexdigest()
        if self.raw_text_sha256 != expected:
            raise TICCError(TICCReasonCode.SOURCE_DIGEST_MISMATCH.value)


@dataclass(frozen=True, slots=True)
class TICCSourceSpan:
    source_turn_ref: str
    start_offset: int
    end_offset: int
    slice_sha256: str

    def __post_init__(self) -> None:
        _nonempty(self.source_turn_ref, "source_turn_ref")
        if isinstance(self.start_offset, bool) or not isinstance(self.start_offset, int):
            raise TICCError("start_offset must be an integer")
        if isinstance(self.end_offset, bool) or not isinstance(self.end_offset, int):
            raise TICCError("end_offset must be an integer")
        if self.start_offset < 0 or self.end_offset <= self.start_offset:
            raise TICCError(TICCReasonCode.SOURCE_SPAN_INVALID.value)
        if not isinstance(self.slice_sha256, str) or _SHA256_RE.fullmatch(self.slice_sha256) is None:
            raise TICCError("slice_sha256 must be lowercase SHA-256")


@dataclass(frozen=True, slots=True)
class TICCAssertionSpec:
    subject_ref: SubjectRef
    predicate: str
    value: JsonScalar
    origin_type: OriginType
    valid_from: datetime
    valid_to: datetime | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.subject_ref, SubjectRef):
            raise TICCError("subject_ref must be SubjectRef")
        _nonempty(self.predicate, "predicate")
        if not isinstance(self.origin_type, OriginType):
            raise TICCError("origin_type must be OriginType")
        if not _aware(self.valid_from):
            raise TICCError("valid_from must be timezone-aware")
        if self.valid_to is not None:
            if not _aware(self.valid_to):
                raise TICCError("valid_to must be timezone-aware")
            if self.valid_to.astimezone(UTC) < self.valid_from.astimezone(UTC):
                raise TICCError("valid_to cannot precede valid_from")


@dataclass(frozen=True, slots=True)
class TICCSemanticAnnotation:
    modality: TICCSemanticModality
    source_span: TICCSourceSpan
    origin_type: OriginType | None = None
    assertion_spec: TICCAssertionSpec | None = None
    qualifier_text: str | None = None
    uncertainty_codes: tuple[str, ...] = ()
    declared_loss_codes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.modality, TICCSemanticModality):
            raise TICCError("modality must be TICCSemanticModality")
        if not isinstance(self.source_span, TICCSourceSpan):
            raise TICCError("source_span must be TICCSourceSpan")
        if self.origin_type is not None and not isinstance(self.origin_type, OriginType):
            raise TICCError("origin_type must be OriginType or None")
        if self.qualifier_text is not None:
            object.__setattr__(self, "qualifier_text", _normalize_text(self.qualifier_text, "qualifier_text"))
        object.__setattr__(self, "uncertainty_codes", _codes(self.uncertainty_codes))
        object.__setattr__(self, "declared_loss_codes", _codes(self.declared_loss_codes))


@dataclass(frozen=True, slots=True)
class TICCCaptureCandidate:
    candidate_id: str
    schema_version: str
    source_turn_ref: str
    source_ref: str
    interaction_event_ref: str
    semantic_modality: TICCSemanticModality
    actor_ref: ActorRef
    origin_type: OriginType | None
    assertion_ref: str | None
    qualifier_text: str | None
    disposition: TICCDisposition
    uncertainty_codes: tuple[str, ...]
    declared_loss_codes: tuple[str, ...]
    reason_codes: tuple[TICCReasonCode, ...]
    payload_hash: str


@dataclass(frozen=True, slots=True)
class TICCCaptureReceipt:
    receipt_id: str
    schema_version: str
    adapter_id: str
    adapter_version: str
    mode: TICCMode
    source_turn_ref: str
    source_turn_digest: str
    interaction_event_ref: str | None
    candidate_refs: tuple[str, ...]
    assertion_refs: tuple[str, ...]
    reason_codes: tuple[TICCReasonCode, ...]
    shadow_only: bool
    no_runtime_authority: bool
    payload_hash: str


@dataclass(frozen=True, slots=True)
class TICCCaptureResult:
    interaction_event: InteractionEvent | None
    candidates: tuple[TICCCaptureCandidate, ...]
    assertions: tuple[AssertionRecord, ...]
    receipt: TICCCaptureReceipt


def capture_turn(
    *,
    turn: ConversationSourceTurn,
    annotation: TICCSemanticAnnotation,
    config: TICCConfig,
    created_at: datetime,
) -> TICCCaptureResult:
    """Capture one explicitly annotated turn into non-authoritative shadow artifacts."""
    if not isinstance(config, TICCConfig):
        raise TICCError("config must be TICCConfig")
    if not _aware(created_at):
        raise TICCError("created_at must be timezone-aware")
    if not config.enabled:
        return _disabled_result(turn, created_at)

    source_ref, source_text = _validate_and_encode_span(turn, annotation.source_span)
    _validate_actor_origin(turn, annotation)
    _validate_qualifier(source_text, annotation.qualifier_text)

    event = InteractionEvent.create(
        event_type=turn.event_type,
        actor_ref=turn.actor_ref,
        subject_refs=turn.subject_refs,
        session_ref=turn.session_ref,
        content_ref=source_ref,
        occurred_at=turn.occurred_at,
        recorded_at=turn.recorded_at,
        visibility=turn.visibility,
        sensitivity_category=turn.sensitivity_category,
        sensitivity_level=turn.sensitivity_level,
    )

    reason_codes: list[TICCReasonCode] = [TICCReasonCode.NO_RUNTIME_AUTHORITY]
    disposition = TICCDisposition.CAPTURED
    assertion: AssertionRecord | None = None

    if annotation.declared_loss_codes:
        reason_codes.append(TICCReasonCode.CAPTURE_LOSS_DECLARED)
        disposition = TICCDisposition.CAPTURED_WITH_DECLARED_LOSS

    if annotation.modality in _RELATION_REQUIRED_MODALITIES:
        # v0.1 intentionally has no relation target contract. A correction or
        # retraction without its exact target must never become a standalone
        # assertion that downstream reconciliation could mistake for ordinary state.
        reason_codes.append(TICCReasonCode.RELATION_NOT_IMPLEMENTED)
        disposition = TICCDisposition.DEFERRED
    elif annotation.assertion_spec is not None:
        if annotation.modality not in _ASSERTION_MODALITIES:
            raise TICCError(TICCReasonCode.ASSERTION_NOT_PERMITTED_FOR_MODALITY.value)
        if annotation.origin_type is None:
            raise TICCError(TICCReasonCode.ASSERTION_SPEC_INCOMPLETE.value)
        if annotation.assertion_spec.origin_type is not annotation.origin_type:
            raise TICCError(TICCReasonCode.ACTOR_ORIGIN_MISMATCH.value)
        assertion = AssertionRecord.create(
            subject_ref=annotation.assertion_spec.subject_ref,
            predicate=annotation.assertion_spec.predicate,
            value=annotation.assertion_spec.value,
            origin_type=annotation.assertion_spec.origin_type,
            source_refs=(source_ref,),
            asserted_by=turn.actor_ref,
            valid_from=annotation.assertion_spec.valid_from,
            valid_to=annotation.assertion_spec.valid_to,
            recorded_at=turn.recorded_at,
            visibility=turn.visibility,
            sensitivity_category=turn.sensitivity_category,
            sensitivity_level=turn.sensitivity_level,
        )

    candidate_payload = {
        "schema_version": TICC_SCHEMA_VERSION,
        "source_turn_ref": turn.turn_ref,
        "source_ref": source_ref,
        "interaction_event_ref": event.event_id,
        "semantic_modality": annotation.modality.value,
        "actor": turn.actor_ref.identity_payload(),
        "origin_type": annotation.origin_type.value if annotation.origin_type else None,
        "assertion_ref": assertion.assertion_id if assertion else None,
        "qualifier_text": annotation.qualifier_text,
        "disposition": disposition.value,
        "uncertainty_codes": annotation.uncertainty_codes,
        "declared_loss_codes": annotation.declared_loss_codes,
        "reason_codes": tuple(code.value for code in reason_codes),
    }
    candidate_hash = _digest(candidate_payload)
    candidate = TICCCaptureCandidate(
        candidate_id=candidate_hash,
        schema_version=TICC_SCHEMA_VERSION,
        source_turn_ref=turn.turn_ref,
        source_ref=source_ref,
        interaction_event_ref=event.event_id,
        semantic_modality=annotation.modality,
        actor_ref=turn.actor_ref,
        origin_type=annotation.origin_type,
        assertion_ref=assertion.assertion_id if assertion else None,
        qualifier_text=annotation.qualifier_text,
        disposition=disposition,
        uncertainty_codes=annotation.uncertainty_codes,
        declared_loss_codes=annotation.declared_loss_codes,
        reason_codes=tuple(reason_codes),
        payload_hash=candidate_hash,
    )

    assertions = (assertion,) if assertion is not None else ()
    receipt = _receipt(
        turn=turn,
        created_at=created_at,
        interaction_event_ref=event.event_id,
        candidate_refs=(candidate.candidate_id,),
        assertion_refs=tuple(item.assertion_id for item in assertions),
        reason_codes=tuple(reason_codes),
    )
    return TICCCaptureResult(event, (candidate,), assertions, receipt)


def _disabled_result(turn: ConversationSourceTurn, created_at: datetime) -> TICCCaptureResult:
    reasons = (TICCReasonCode.SHADOW_FEATURE_DISABLED, TICCReasonCode.NO_RUNTIME_AUTHORITY)
    return TICCCaptureResult(
        None,
        (),
        (),
        _receipt(
            turn=turn,
            created_at=created_at,
            interaction_event_ref=None,
            candidate_refs=(),
            assertion_refs=(),
            reason_codes=reasons,
        ),
    )


def _receipt(
    *,
    turn: ConversationSourceTurn,
    created_at: datetime,
    interaction_event_ref: str | None,
    candidate_refs: tuple[str, ...],
    assertion_refs: tuple[str, ...],
    reason_codes: tuple[TICCReasonCode, ...],
) -> TICCCaptureReceipt:
    payload = {
        "schema_version": TICC_SCHEMA_VERSION,
        "adapter_id": TICC_ADAPTER_ID,
        "adapter_version": TICC_ADAPTER_VERSION,
        "mode": TICCMode.SHADOW.value,
        "source_turn_ref": turn.turn_ref,
        "source_turn_digest": turn.raw_text_sha256,
        "interaction_event_ref": interaction_event_ref,
        "candidate_refs": candidate_refs,
        "assertion_refs": assertion_refs,
        "reason_codes": tuple(code.value for code in reason_codes),
        "created_at": created_at.astimezone(UTC).isoformat(timespec="microseconds"),
        "shadow_only": True,
        "no_runtime_authority": True,
    }
    digest = _digest(payload)
    return TICCCaptureReceipt(
        digest,
        TICC_SCHEMA_VERSION,
        TICC_ADAPTER_ID,
        TICC_ADAPTER_VERSION,
        TICCMode.SHADOW,
        turn.turn_ref,
        turn.raw_text_sha256,
        interaction_event_ref,
        candidate_refs,
        assertion_refs,
        reason_codes,
        True,
        True,
        digest,
    )


def _validate_and_encode_span(turn: ConversationSourceTurn, span: TICCSourceSpan) -> tuple[str, str]:
    if span.source_turn_ref != turn.turn_ref or span.end_offset > len(turn.raw_text):
        raise TICCError(TICCReasonCode.SOURCE_SPAN_INVALID.value)
    text = turn.raw_text[span.start_offset:span.end_offset]
    expected = sha256(text.encode("utf-8")).hexdigest()
    if expected != span.slice_sha256:
        raise TICCError(TICCReasonCode.SOURCE_SPAN_INVALID.value)
    ref = (
        f"conversation_turn:v0_1:{turn.session_ref}:{turn.sequence}:{turn.turn_ref}:"
        f"{turn.raw_text_sha256}#char={span.start_offset}:{span.end_offset};sha256={span.slice_sha256}"
    )
    return ref, text


def _validate_qualifier(source_text: str, qualifier_text: str | None) -> None:
    if qualifier_text is not None and qualifier_text not in source_text:
        raise TICCError(TICCReasonCode.QUALIFIER_NOT_SOURCE_BOUND.value)


def _validate_actor_origin(turn: ConversationSourceTurn, annotation: TICCSemanticAnnotation) -> None:
    origin = annotation.origin_type
    if origin is None:
        return
    if origin is OriginType.USER_STATED and turn.actor_ref.kind not in {ActorKind.HUMAN, ActorKind.OPERATOR}:
        raise TICCError(TICCReasonCode.ACTOR_ORIGIN_MISMATCH.value)
    if origin is OriginType.MODEL_INFERRED and turn.actor_ref.kind not in {ActorKind.TITAN_COMPONENT, ActorKind.EXTERNAL_AGENT}:
        raise TICCError(TICCReasonCode.ACTOR_ORIGIN_MISMATCH.value)
    if origin in {OriginType.SYSTEM_OBSERVED, OriginType.SYSTEM_MEASURED} and turn.actor_ref.kind not in {ActorKind.SYSTEM, ActorKind.SERVICE, ActorKind.TOOL}:
        raise TICCError(TICCReasonCode.ACTOR_ORIGIN_MISMATCH.value)


def _nonempty(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TICCError(f"{field_name} must be non-empty")
    return value


def _normalize_text(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise TICCError(f"{field_name} must be a string")
    normalized = unicodedata.normalize("NFC", value)
    if not normalized.strip():
        raise TICCError(f"{field_name} must be non-empty")
    return normalized


def _aware(value: object) -> bool:
    return isinstance(value, datetime) and value.tzinfo is not None and value.utcoffset() is not None


def _codes(values: Iterable[str]) -> tuple[str, ...]:
    result = tuple(sorted(_normalize_text(value, "code") for value in values))
    if len(result) != len(set(result)):
        raise TICCError("codes cannot contain duplicates")
    return result


def _digest(payload: object) -> str:
    return sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()


__all__ = [
    "ConversationSourceTurn",
    "TICCAssertionSpec",
    "TICCCaptureCandidate",
    "TICCCaptureReceipt",
    "TICCCaptureResult",
    "TICCConfig",
    "TICCDisposition",
    "TICCError",
    "TICCMode",
    "TICCReasonCode",
    "TICCSemanticAnnotation",
    "TICCSemanticModality",
    "TICCSourceSpan",
    "capture_turn",
]
