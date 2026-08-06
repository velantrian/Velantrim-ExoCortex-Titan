"""Typed, provenance-carrying input observations for the trusted signal producer.

An observation is one immutable, content-addressed claim about a single
dimension of :class:`core.compute_controller.ContinuityComputeSignals`,
contributed by a named producer with an explicit evidence trail. This module
only validates the *shape* of one observation in isolation: that its value
matches what its declared ``signal_type`` expects, that its confidence is a
well-formed score, and that its identifiers are non-empty and deterministic.

It intentionally does **not** decide whether an observation is *trusted* —
whether its producer is on an allowlist, whether its confidence clears a
policy threshold, or whether its ``scope`` satisfies a signal-type-specific
requirement. Those are business-policy decisions that depend on a
caller-supplied :class:`~core.continuity.signal_producer.ContinuitySignalPolicy`,
not a structural property of the observation itself, so they are made once,
in one place, by ``signal_producer.py``. Baking a fixed confidence threshold
into this module would couple one observation to one policy and make it
impossible to re-evaluate the same raw observation under a different policy.

This module carries no Canon, TruthGate, compute-routing, advisory, response,
persistence, or action authority. Constructing an observation has no runtime
effect.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from hashlib import sha256
import json
import math
from typing import Iterable

OBSERVATION_SCHEMA_VERSION = "continuity.signal_producer.observation.v1"


class ContinuitySignalObservationError(ValueError):
    """Raised when one observation's own shape is invalid."""


class ContinuitySignalType(str, Enum):
    """One dimension of ``ContinuityComputeSignals`` an observation reports on.

    Names match the real fields of ``core.compute_controller.
    ContinuityComputeSignals`` exactly; ``EVIDENCE_COVERAGE_ITEM`` and
    ``ACTIVE_CONTRADICTION`` are singular per-item/per-contradiction claims
    that the producer aggregates into the plural ``evidence_coverage`` and
    ``active_contradictions`` output fields.
    """

    CONTEXT_DEGRADED = "context_degraded"
    CONTEXT_FRESHNESS = "context_freshness"
    EVIDENCE_COVERAGE_ITEM = "evidence_coverage_item"
    ACTIVE_CONTRADICTION = "active_contradiction"
    SENSITIVITY = "sensitivity"
    CONTINUITY_AVAILABLE = "continuity_available"
    IMPORTANT_CLAIM = "important_claim"
    REQUIRES_CURRENT_STATE = "requires_current_state"


_BOOLEAN_SIGNAL_TYPES = frozenset(
    {
        ContinuitySignalType.CONTEXT_DEGRADED,
        ContinuitySignalType.EVIDENCE_COVERAGE_ITEM,
        ContinuitySignalType.CONTINUITY_AVAILABLE,
        ContinuitySignalType.IMPORTANT_CLAIM,
        ContinuitySignalType.REQUIRES_CURRENT_STATE,
    }
)
# Real ContextFreshness/ComputeSensitivity string values (core/compute_controller.py).
# Duplicated here deliberately, as a frozen literal set: this module must not
# import core.compute_controller so that a change to those enums cannot
# silently change what an already-recorded observation means.
_CONTEXT_FRESHNESS_VALUES = frozenset({"unknown", "fresh", "stale", "critical_stale"})
_COMPUTE_SENSITIVITY_VALUES = frozenset({"low", "medium", "high", "critical"})


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContinuitySignalObservationError(f"{name} must be a non-empty string")
    return value.strip()


def _optional_text(value: object, name: str) -> str | None:
    if value is None:
        return None
    return _text(value, name)


def _bool(value: object, name: str) -> bool:
    if not isinstance(value, bool):
        raise ContinuitySignalObservationError(f"{name} must be a bool")
    return value


def _confidence(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ContinuitySignalObservationError(
            "confidence must be a finite number in [0.0, 1.0]"
        )
    result = float(value)
    if not math.isfinite(result) or not 0.0 <= result <= 1.0:
        raise ContinuitySignalObservationError(
            "confidence must be a finite number in [0.0, 1.0]"
        )
    return result


def _aware(value: object, name: str) -> datetime:
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise ContinuitySignalObservationError(f"{name} must be timezone-aware")
    return value


def _canonical_datetime(value: datetime) -> str:
    return value.astimezone(UTC).isoformat(timespec="microseconds").replace(
        "+00:00", "Z"
    )


def _refs(values: Iterable[str], name: str) -> tuple[str, ...]:
    items = tuple(_text(value, name) for value in values)
    if len(items) != len(set(items)):
        raise ContinuitySignalObservationError(f"{name} cannot contain duplicates")
    return tuple(sorted(items))


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


def _validate_value_shape(signal_type: ContinuitySignalType, value: object) -> object:
    """Reject a value whose shape does not match its declared signal_type.

    This is structural only: it does not know about trust, thresholds, or
    per-type ``scope`` requirements — see the module docstring.
    """

    if signal_type in _BOOLEAN_SIGNAL_TYPES:
        return _bool(value, "value")
    if signal_type is ContinuitySignalType.ACTIVE_CONTRADICTION:
        if value is not True:
            raise ContinuitySignalObservationError(
                "active_contradiction observations must assert value=True"
            )
        return True
    if signal_type is ContinuitySignalType.CONTEXT_FRESHNESS:
        if not isinstance(value, str) or value not in _CONTEXT_FRESHNESS_VALUES:
            raise ContinuitySignalObservationError(
                f"value for context_freshness must be one of {sorted(_CONTEXT_FRESHNESS_VALUES)}"
            )
        return value
    if signal_type is ContinuitySignalType.SENSITIVITY:
        if not isinstance(value, str) or value not in _COMPUTE_SENSITIVITY_VALUES:
            raise ContinuitySignalObservationError(
                f"value for sensitivity must be one of {sorted(_COMPUTE_SENSITIVITY_VALUES)}"
            )
        return value
    raise ContinuitySignalObservationError(  # pragma: no cover - exhaustive guard
        f"unhandled signal_type: {signal_type}"
    )


@dataclass(frozen=True, slots=True)
class ContinuitySignalObservation:
    """One immutable, content-addressed claim about one signal dimension."""

    observation_id: str
    schema_version: str
    signal_type: ContinuitySignalType
    value: object
    confidence: float
    producer: str
    source_type: str
    source_id: str
    observed_at: datetime
    evidence_refs: tuple[str, ...]
    reason_codes: tuple[str, ...]
    scope: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "schema_version", _text(self.schema_version, "schema_version")
        )
        if not isinstance(self.signal_type, ContinuitySignalType):
            raise ContinuitySignalObservationError(
                "signal_type must be a ContinuitySignalType"
            )
        object.__setattr__(
            self, "value", _validate_value_shape(self.signal_type, self.value)
        )
        object.__setattr__(self, "confidence", _confidence(self.confidence))
        object.__setattr__(self, "producer", _text(self.producer, "producer"))
        object.__setattr__(
            self, "source_type", _text(self.source_type, "source_type")
        )
        object.__setattr__(self, "source_id", _text(self.source_id, "source_id"))
        _aware(self.observed_at, "observed_at")
        object.__setattr__(
            self, "evidence_refs", _refs(self.evidence_refs, "evidence_refs")
        )
        object.__setattr__(
            self, "reason_codes", _refs(self.reason_codes, "reason_codes")
        )
        object.__setattr__(
            self, "scope", _optional_text(self.scope, "scope")
        )
        _digest_input = self._identity_payload(
            schema_version=self.schema_version,
            signal_type=self.signal_type,
            value=self.value,
            confidence=self.confidence,
            producer=self.producer,
            source_type=self.source_type,
            source_id=self.source_id,
            observed_at=self.observed_at,
            evidence_refs=self.evidence_refs,
            reason_codes=self.reason_codes,
            scope=self.scope,
        )
        expected = _digest(_digest_input)
        if self.observation_id != expected:
            raise ContinuitySignalObservationError(
                "observation_id must match canonical observation content"
            )

    @classmethod
    def create(
        cls,
        *,
        signal_type: ContinuitySignalType,
        value: object,
        confidence: float,
        producer: str,
        source_type: str,
        source_id: str,
        observed_at: datetime,
        evidence_refs: Iterable[str] = (),
        reason_codes: Iterable[str] = (),
        scope: str | None = None,
        schema_version: str = OBSERVATION_SCHEMA_VERSION,
    ) -> ContinuitySignalObservation:
        """Build one observation, computing its deterministic content ID.

        No clock, network, environment, or global mutable state is read here:
        ``observed_at`` is caller-supplied and is the only timestamp involved.
        """

        if not isinstance(signal_type, ContinuitySignalType):
            raise ContinuitySignalObservationError(
                "signal_type must be a ContinuitySignalType"
            )
        shaped_value = _validate_value_shape(signal_type, value)
        conf = _confidence(confidence)
        producer_text = _text(producer, "producer")
        source_type_text = _text(source_type, "source_type")
        source_id_text = _text(source_id, "source_id")
        _aware(observed_at, "observed_at")
        refs = _refs(evidence_refs, "evidence_refs")
        reasons = _refs(reason_codes, "reason_codes")
        scope_text = _optional_text(scope, "scope")
        version = _text(schema_version, "schema_version")

        payload = cls._identity_payload(
            schema_version=version,
            signal_type=signal_type,
            value=shaped_value,
            confidence=conf,
            producer=producer_text,
            source_type=source_type_text,
            source_id=source_id_text,
            observed_at=observed_at,
            evidence_refs=refs,
            reason_codes=reasons,
            scope=scope_text,
        )
        return cls(
            observation_id=_digest(payload),
            schema_version=version,
            signal_type=signal_type,
            value=shaped_value,
            confidence=conf,
            producer=producer_text,
            source_type=source_type_text,
            source_id=source_id_text,
            observed_at=observed_at,
            evidence_refs=refs,
            reason_codes=reasons,
            scope=scope_text,
        )

    @staticmethod
    def _identity_payload(
        *,
        schema_version: str,
        signal_type: ContinuitySignalType,
        value: object,
        confidence: float,
        producer: str,
        source_type: str,
        source_id: str,
        observed_at: datetime,
        evidence_refs: tuple[str, ...],
        reason_codes: tuple[str, ...],
        scope: str | None,
    ) -> dict[str, object]:
        return {
            "schema_version": schema_version,
            "signal_type": signal_type.value,
            "value": value,
            "confidence": confidence,
            "producer": producer,
            "source_type": source_type,
            "source_id": source_id,
            "observed_at": _canonical_datetime(_aware(observed_at, "observed_at")),
            "evidence_refs": list(evidence_refs),
            "reason_codes": list(reason_codes),
            "scope": scope,
        }

    def identity_payload(self) -> dict[str, object]:
        return self._identity_payload(
            schema_version=self.schema_version,
            signal_type=self.signal_type,
            value=self.value,
            confidence=self.confidence,
            producer=self.producer,
            source_type=self.source_type,
            source_id=self.source_id,
            observed_at=self.observed_at,
            evidence_refs=self.evidence_refs,
            reason_codes=self.reason_codes,
            scope=self.scope,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "observation_id": self.observation_id,
            **self.identity_payload(),
        }


__all__ = [
    "OBSERVATION_SCHEMA_VERSION",
    "ContinuitySignalObservation",
    "ContinuitySignalObservationError",
    "ContinuitySignalType",
]
