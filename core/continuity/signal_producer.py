"""Deterministic, policy-driven trusted producer for continuity compute signals.

Warning/safety booleans use trusted-OR semantics: one applicable trusted true
observation is enough to preserve ``context_degraded``, ``important_claim``,
or ``requires_current_state``. ``minimum_confirmations`` is intentionally
reserved for the positive capability claim ``continuity_available=True``;
distinct producers are counted and a positive/negative conflict resolves
fail-conservative to ``False``.
"""
from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from hashlib import sha256
import json
import math

from core.compute_controller import (
    ComputeSensitivity,
    ContextFreshness,
    ContinuityComputeSignals,
)

from .observations import (
    OBSERVATION_SCHEMA_VERSION,
    ContinuitySignalObservation,
    ContinuitySignalType,
)

SIGNAL_PRODUCER_VERSION = "continuity.signal_producer.v1"
SIGNAL_PRODUCER_POLICY_VERSION = "continuity.signal_producer.policy.v1"
SIGNAL_PRODUCER_RESULT_SCHEMA_VERSION = "continuity.signal_producer.result.v1"

_SCOPE_REQUIRED_TYPES = frozenset(
    {
        ContinuitySignalType.EVIDENCE_COVERAGE_ITEM,
        ContinuitySignalType.ACTIVE_CONTRADICTION,
    }
)
_FRESHNESS_PRIORITY = {"critical_stale": 4, "stale": 3, "unknown": 2, "fresh": 1}
_SENSITIVITY_PRIORITY = {"critical": 4, "high": 3, "medium": 2, "low": 1}
_REJECTION_MESSAGES = {
    "UNKNOWN_SCHEMA_VERSION": "observation schema_version is not supported by this producer",
    "UNTRUSTED_PRODUCER": "producer is not in policy.trusted_producers",
    "UNSUPPORTED_SOURCE_TYPE": "source_type is not in policy.allowed_source_types",
    "CONFIDENCE_BELOW_THRESHOLD": "confidence is below policy.minimum_confidence",
    "MISSING_EVIDENCE_REFS": "policy.require_evidence_refs is set but evidence_refs is empty",
    "MISSING_REQUIRED_SCOPE": "this signal_type requires a non-empty scope",
}


class ContinuitySignalProducerError(ValueError):
    """Raised when a policy or producer call is malformed."""


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContinuitySignalProducerError(f"{name} must be a non-empty string")
    return value.strip()


def _bool(value: object, name: str) -> bool:
    if not isinstance(value, bool):
        raise ContinuitySignalProducerError(f"{name} must be a bool")
    return value


def _score(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ContinuitySignalProducerError(f"{name} must be a finite number in [0, 1]")
    result = float(value)
    if not math.isfinite(result) or not 0.0 <= result <= 1.0:
        raise ContinuitySignalProducerError(f"{name} must be a finite number in [0, 1]")
    return result


def _non_empty_frozenset(values: object, name: str) -> frozenset[str]:
    """Normalize a public ``Iterable[str]`` contract without accepting text.

    ``str`` and ``bytes`` are iterable but represent one malformed collection,
    not a collection of identifiers. Iterators/generators are consumed once.
    """

    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise ContinuitySignalProducerError(f"{name} must be an iterable of strings")
    try:
        items = frozenset(_text(value, name) for value in values)
    except TypeError as exc:
        raise ContinuitySignalProducerError(
            f"{name} must be an iterable of strings"
        ) from exc
    if not items:
        raise ContinuitySignalProducerError(f"{name} cannot be empty")
    return items


def _positive_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ContinuitySignalProducerError(f"{name} must be a positive int")
    return value


def _non_negative_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ContinuitySignalProducerError(f"{name} must be a non-negative int")
    return value


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


@dataclass(frozen=True, slots=True)
class ContinuitySignalPolicy:
    """Immutable, content-addressed policy for one producer run."""

    policy_id: str
    policy_version: str
    trusted_producers: frozenset[str]
    allowed_source_types: frozenset[str]
    minimum_confidence: float
    require_evidence_refs: bool
    minimum_confirmations: int
    max_contradiction_count: int

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "policy_version", _text(self.policy_version, "policy_version")
        )
        object.__setattr__(
            self,
            "trusted_producers",
            _non_empty_frozenset(self.trusted_producers, "trusted_producers"),
        )
        object.__setattr__(
            self,
            "allowed_source_types",
            _non_empty_frozenset(self.allowed_source_types, "allowed_source_types"),
        )
        object.__setattr__(
            self,
            "minimum_confidence",
            _score(self.minimum_confidence, "minimum_confidence"),
        )
        object.__setattr__(
            self,
            "require_evidence_refs",
            _bool(self.require_evidence_refs, "require_evidence_refs"),
        )
        object.__setattr__(
            self,
            "minimum_confirmations",
            _positive_int(self.minimum_confirmations, "minimum_confirmations"),
        )
        object.__setattr__(
            self,
            "max_contradiction_count",
            _non_negative_int(
                self.max_contradiction_count, "max_contradiction_count"
            ),
        )
        expected = _digest(
            self._identity_payload_from(
                policy_version=self.policy_version,
                trusted_producers=self.trusted_producers,
                allowed_source_types=self.allowed_source_types,
                minimum_confidence=self.minimum_confidence,
                require_evidence_refs=self.require_evidence_refs,
                minimum_confirmations=self.minimum_confirmations,
                max_contradiction_count=self.max_contradiction_count,
            )
        )
        if self.policy_id != expected:
            raise ContinuitySignalProducerError(
                "policy_id must match canonical policy content"
            )

    @classmethod
    def create(
        cls,
        *,
        trusted_producers: Iterable[str],
        allowed_source_types: Iterable[str],
        minimum_confidence: float,
        require_evidence_refs: bool,
        minimum_confirmations: int,
        max_contradiction_count: int,
        policy_version: str = SIGNAL_PRODUCER_POLICY_VERSION,
    ) -> ContinuitySignalPolicy:
        version = _text(policy_version, "policy_version")
        producers = _non_empty_frozenset(trusted_producers, "trusted_producers")
        sources = _non_empty_frozenset(allowed_source_types, "allowed_source_types")
        min_confidence = _score(minimum_confidence, "minimum_confidence")
        require_refs = _bool(require_evidence_refs, "require_evidence_refs")
        min_confirmations = _positive_int(
            minimum_confirmations, "minimum_confirmations"
        )
        max_contradictions = _non_negative_int(
            max_contradiction_count, "max_contradiction_count"
        )
        payload = cls._identity_payload_from(
            policy_version=version,
            trusted_producers=producers,
            allowed_source_types=sources,
            minimum_confidence=min_confidence,
            require_evidence_refs=require_refs,
            minimum_confirmations=min_confirmations,
            max_contradiction_count=max_contradictions,
        )
        return cls(
            policy_id=_digest(payload),
            policy_version=version,
            trusted_producers=producers,
            allowed_source_types=sources,
            minimum_confidence=min_confidence,
            require_evidence_refs=require_refs,
            minimum_confirmations=min_confirmations,
            max_contradiction_count=max_contradictions,
        )

    @staticmethod
    def _identity_payload_from(
        *,
        policy_version: str,
        trusted_producers: frozenset[str],
        allowed_source_types: frozenset[str],
        minimum_confidence: float,
        require_evidence_refs: bool,
        minimum_confirmations: int,
        max_contradiction_count: int,
    ) -> dict[str, object]:
        return {
            "policy_version": policy_version,
            "trusted_producers": sorted(trusted_producers),
            "allowed_source_types": sorted(allowed_source_types),
            "minimum_confidence": minimum_confidence,
            "require_evidence_refs": require_evidence_refs,
            "minimum_confirmations": minimum_confirmations,
            "max_contradiction_count": max_contradiction_count,
        }

    def to_dict(self) -> dict[str, object]:
        return {
            "policy_id": self.policy_id,
            **self._identity_payload_from(
                policy_version=self.policy_version,
                trusted_producers=self.trusted_producers,
                allowed_source_types=self.allowed_source_types,
                minimum_confidence=self.minimum_confidence,
                require_evidence_refs=self.require_evidence_refs,
                minimum_confirmations=self.minimum_confirmations,
                max_contradiction_count=self.max_contradiction_count,
            ),
        }


@dataclass(frozen=True, slots=True)
class ContinuitySignalProvenance:
    signal_type: ContinuitySignalType
    observation_ids: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    producers: tuple[str, ...]
    confidence: float
    rule: str
    value: object

    def __post_init__(self) -> None:
        if not isinstance(self.signal_type, ContinuitySignalType):
            raise ContinuitySignalProducerError(
                "signal_type must be a ContinuitySignalType"
            )
        object.__setattr__(
            self, "observation_ids", tuple(sorted(set(self.observation_ids)))
        )
        object.__setattr__(
            self, "evidence_refs", tuple(sorted(set(self.evidence_refs)))
        )
        object.__setattr__(self, "producers", tuple(sorted(set(self.producers))))
        object.__setattr__(self, "confidence", _score(self.confidence, "confidence"))
        object.__setattr__(self, "rule", _text(self.rule, "rule"))

    def to_dict(self) -> dict[str, object]:
        return {
            "signal_type": self.signal_type.value,
            "observation_ids": list(self.observation_ids),
            "evidence_refs": list(self.evidence_refs),
            "producers": list(self.producers),
            "confidence": self.confidence,
            "rule": self.rule,
            "value": self.value,
        }


@dataclass(frozen=True, slots=True)
class RejectedObservation:
    observation_id: str
    reason_code: str
    message: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "observation_id", _text(self.observation_id, "observation_id"))
        object.__setattr__(self, "reason_code", _text(self.reason_code, "reason_code"))
        object.__setattr__(self, "message", _text(self.message, "message"))

    def to_dict(self) -> dict[str, object]:
        return {
            "observation_id": self.observation_id,
            "reason_code": self.reason_code,
            "message": self.message,
        }


@dataclass(frozen=True, slots=True)
class ContinuitySignalProductionResult:
    result_hash: str
    schema_version: str
    producer_version: str
    policy_id: str
    signals: ContinuityComputeSignals
    provenance: tuple[ContinuitySignalProvenance, ...]
    rejected_observations: tuple[RejectedObservation, ...]
    reason_codes: tuple[str, ...]
    observation_ids: tuple[str, ...]
    ignored_or_rejected_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.signals, ContinuityComputeSignals):
            raise ContinuitySignalProducerError(
                "signals must be a ContinuityComputeSignals"
            )
        if any(not isinstance(item, ContinuitySignalProvenance) for item in self.provenance):
            raise ContinuitySignalProducerError(
                "provenance must contain only ContinuitySignalProvenance"
            )
        if any(not isinstance(item, RejectedObservation) for item in self.rejected_observations):
            raise ContinuitySignalProducerError(
                "rejected_observations must contain only RejectedObservation"
            )
        object.__setattr__(self, "reason_codes", tuple(sorted(set(self.reason_codes))))
        object.__setattr__(self, "observation_ids", tuple(sorted(set(self.observation_ids))))
        object.__setattr__(
            self,
            "ignored_or_rejected_ids",
            tuple(sorted(set(self.ignored_or_rejected_ids))),
        )
        if self.result_hash != _digest(self._identity_payload()):
            raise ContinuitySignalProducerError(
                "result_hash must match canonical production content"
            )

    def _identity_payload(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "producer_version": self.producer_version,
            "policy_id": self.policy_id,
            "signals": _signals_dict(self.signals),
            "provenance": [item.to_dict() for item in self.provenance],
            "rejected_observations": [
                item.to_dict() for item in self.rejected_observations
            ],
            "reason_codes": list(self.reason_codes),
            "observation_ids": list(self.observation_ids),
            "ignored_or_rejected_ids": list(self.ignored_or_rejected_ids),
        }

    def to_dict(self) -> dict[str, object]:
        return {"result_hash": self.result_hash, **self._identity_payload()}


def _signals_dict(signals: ContinuityComputeSignals) -> dict[str, object]:
    return {
        "context_degraded": signals.context_degraded,
        "context_freshness": signals.context_freshness.value,
        "evidence_coverage": signals.evidence_coverage,
        "active_contradictions": signals.active_contradictions,
        "sensitivity": signals.sensitivity.value,
        "continuity_available": signals.continuity_available,
        "important_claim": signals.important_claim,
        "requires_current_state": signals.requires_current_state,
    }


def _ordered_unique(
    observations: Sequence[ContinuitySignalObservation],
) -> tuple[ContinuitySignalObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Sequence):
        raise ContinuitySignalProducerError(
            "observations must be a sequence of ContinuitySignalObservation"
        )
    seen: dict[str, ContinuitySignalObservation] = {}
    for observation in observations:
        if not isinstance(observation, ContinuitySignalObservation):
            raise ContinuitySignalProducerError(
                "observations must contain only ContinuitySignalObservation values"
            )
        previous = seen.get(observation.observation_id)
        if previous is not None and previous != observation:
            raise ContinuitySignalProducerError(
                f"conflicting observation content for id {observation.observation_id}"
            )
        seen[observation.observation_id] = observation
    return tuple(seen[key] for key in sorted(seen))


def _trust_reason(
    observation: ContinuitySignalObservation, policy: ContinuitySignalPolicy
) -> str | None:
    if observation.schema_version != OBSERVATION_SCHEMA_VERSION:
        return "UNKNOWN_SCHEMA_VERSION"
    if observation.producer not in policy.trusted_producers:
        return "UNTRUSTED_PRODUCER"
    if observation.source_type not in policy.allowed_source_types:
        return "UNSUPPORTED_SOURCE_TYPE"
    if observation.confidence < policy.minimum_confidence:
        return "CONFIDENCE_BELOW_THRESHOLD"
    if policy.require_evidence_refs and not observation.evidence_refs:
        return "MISSING_EVIDENCE_REFS"
    if observation.signal_type in _SCOPE_REQUIRED_TYPES and not observation.scope:
        return "MISSING_REQUIRED_SCOPE"
    return None


def _group_by_type(
    trusted: tuple[ContinuitySignalObservation, ...],
) -> dict[ContinuitySignalType, tuple[ContinuitySignalObservation, ...]]:
    groups: dict[ContinuitySignalType, list[ContinuitySignalObservation]] = defaultdict(list)
    for observation in trusted:
        groups[observation.signal_type].append(observation)
    return {key: tuple(value) for key, value in groups.items()}


def _refs_union(observations: Iterable[ContinuitySignalObservation]) -> tuple[str, ...]:
    return tuple(sorted({ref for observation in observations for ref in observation.evidence_refs}))


def _producers(observations: Iterable[ContinuitySignalObservation]) -> tuple[str, ...]:
    return tuple(sorted({observation.producer for observation in observations}))


def _min_confidence(observations: tuple[ContinuitySignalObservation, ...]) -> float:
    return min((observation.confidence for observation in observations), default=0.0)


def _string_value(value: object) -> str:
    if not isinstance(value, str):
        raise ContinuitySignalProducerError(
            "expected a string-shaped observation value"
        )
    return value


def _required_scope(value: str | None) -> str:
    if value is None:
        raise ContinuitySignalProducerError(
            "scope is required for this signal_type and must not be None here"
        )
    return value


def _aggregate_boolean_or(
    group: tuple[ContinuitySignalObservation, ...],
    signal_type: ContinuitySignalType,
) -> tuple[bool, ContinuitySignalProvenance]:
    true_observations = tuple(
        observation for observation in group if observation.value is True
    )
    value = bool(true_observations)
    provenance = ContinuitySignalProvenance(
        signal_type=signal_type,
        observation_ids=tuple(
            observation.observation_id for observation in true_observations
        ),
        evidence_refs=_refs_union(true_observations),
        producers=_producers(true_observations),
        confidence=_min_confidence(true_observations),
        rule=(
            "trusted_true_observation_or"
            if true_observations
            else "no_trusted_true_observations"
        ),
        value=value,
    )
    return value, provenance


def _aggregate_continuity_available(
    group: tuple[ContinuitySignalObservation, ...],
    policy: ContinuitySignalPolicy,
) -> tuple[bool, ContinuitySignalProvenance, bool]:
    true_observations = tuple(
        observation for observation in group if observation.value is True
    )
    false_observations = tuple(
        observation for observation in group if observation.value is False
    )
    producers = _producers(true_observations)
    conflict = bool(true_observations) and bool(false_observations)

    if conflict:
        value = False
        rule = "conflicting_positive_and_negative_observations_fail_conservative"
        contributing = true_observations + false_observations
    elif len(producers) >= policy.minimum_confirmations:
        value = True
        rule = (
            f"{len(producers)}_distinct_producers_of_"
            f"{policy.minimum_confirmations}_required"
        )
        contributing = true_observations
    else:
        value = False
        rule = (
            "no_trusted_true_observations"
            if not true_observations
            else "insufficient_confirmations"
        )
        contributing = true_observations

    provenance = ContinuitySignalProvenance(
        signal_type=ContinuitySignalType.CONTINUITY_AVAILABLE,
        observation_ids=tuple(
            observation.observation_id for observation in contributing
        ),
        evidence_refs=_refs_union(contributing),
        producers=_producers(contributing),
        confidence=_min_confidence(contributing),
        rule=rule,
        value=value,
    )
    return value, provenance, conflict


def _aggregate_priority_categorical(
    group: tuple[ContinuitySignalObservation, ...],
    priority_table: dict[str, int],
    default_value: str,
    signal_type: ContinuitySignalType,
) -> tuple[str, ContinuitySignalProvenance]:
    if not group:
        return default_value, ContinuitySignalProvenance(
            signal_type=signal_type,
            observation_ids=(),
            evidence_refs=(),
            producers=(),
            confidence=0.0,
            rule="no_trusted_observations_default_applied",
            value=default_value,
        )
    top_priority = max(
        priority_table[_string_value(observation.value)] for observation in group
    )
    contributing = tuple(
        observation
        for observation in group
        if priority_table[_string_value(observation.value)] == top_priority
    )
    value = _string_value(contributing[0].value)
    return value, ContinuitySignalProvenance(
        signal_type=signal_type,
        observation_ids=tuple(
            observation.observation_id for observation in contributing
        ),
        evidence_refs=_refs_union(contributing),
        producers=_producers(contributing),
        confidence=_min_confidence(contributing),
        rule=f"most_severe_among_{len(group)}_trusted_observations",
        value=value,
    )


def _aggregate_contradictions(
    group: tuple[ContinuitySignalObservation, ...],
    policy: ContinuitySignalPolicy,
) -> tuple[int, ContinuitySignalProvenance, bool]:
    if not group:
        return 0, ContinuitySignalProvenance(
            signal_type=ContinuitySignalType.ACTIVE_CONTRADICTION,
            observation_ids=(),
            evidence_refs=(),
            producers=(),
            confidence=0.0,
            rule="no_trusted_observations",
            value=0,
        ), False
    by_scope: dict[str, ContinuitySignalObservation] = {}
    for observation in sorted(group, key=lambda item: item.observation_id):
        by_scope.setdefault(_required_scope(observation.scope), observation)
    unique = tuple(by_scope[key] for key in sorted(by_scope))
    raw_count = len(unique)
    capped = raw_count > policy.max_contradiction_count
    count = min(raw_count, policy.max_contradiction_count)
    rule = f"unique_scopes_deduped_from_{len(group)}_observations"
    if capped:
        rule += "_capped_by_policy"
    return count, ContinuitySignalProvenance(
        signal_type=ContinuitySignalType.ACTIVE_CONTRADICTION,
        observation_ids=tuple(observation.observation_id for observation in unique),
        evidence_refs=_refs_union(unique),
        producers=_producers(unique),
        confidence=_min_confidence(unique),
        rule=rule,
        value=count,
    ), capped


def _aggregate_evidence_coverage(
    group: tuple[ContinuitySignalObservation, ...],
    *,
    globally_empty: bool,
) -> tuple[float, ContinuitySignalProvenance]:
    if globally_empty:
        return 1.0, ContinuitySignalProvenance(
            signal_type=ContinuitySignalType.EVIDENCE_COVERAGE_ITEM,
            observation_ids=(),
            evidence_refs=(),
            producers=(),
            confidence=0.0,
            rule="no_observations_at_all_matches_shadow_off_default",
            value=1.0,
        )
    if not group:
        return 0.0, ContinuitySignalProvenance(
            signal_type=ContinuitySignalType.EVIDENCE_COVERAGE_ITEM,
            observation_ids=(),
            evidence_refs=(),
            producers=(),
            confidence=0.0,
            rule="no_trusted_evidence_observations_fail_closed",
            value=0.0,
        )
    by_scope: dict[str, tuple[ContinuitySignalObservation, ...]] = defaultdict(tuple)
    for observation in sorted(group, key=lambda item: item.observation_id):
        scope = _required_scope(observation.scope)
        by_scope[scope] = by_scope[scope] + (observation,)
    considered: list[ContinuitySignalObservation] = []
    covered = 0
    for scope in sorted(by_scope):
        items = by_scope[scope]
        considered.extend(items)
        values = {item.value for item in items}
        if True in values and False not in values:
            covered += 1
    total = len(by_scope)
    value = round(covered / total, 6)
    return value, ContinuitySignalProvenance(
        signal_type=ContinuitySignalType.EVIDENCE_COVERAGE_ITEM,
        observation_ids=tuple(
            observation.observation_id for observation in considered
        ),
        evidence_refs=_refs_union(considered),
        producers=_producers(considered),
        confidence=_min_confidence(tuple(considered)),
        rule=f"{covered}_of_{total}_unique_scopes_covered",
        value=value,
    )


def produce_continuity_compute_signals(
    observations: Sequence[ContinuitySignalObservation],
    *,
    policy: ContinuitySignalPolicy,
) -> ContinuitySignalProductionResult:
    if not isinstance(policy, ContinuitySignalPolicy):
        raise ContinuitySignalProducerError("policy must be a ContinuitySignalPolicy")
    ordered = _ordered_unique(observations)
    globally_empty = not ordered
    trusted: list[ContinuitySignalObservation] = []
    rejected: list[RejectedObservation] = []
    for observation in ordered:
        reason = _trust_reason(observation, policy)
        if reason is None:
            trusted.append(observation)
        else:
            rejected.append(
                RejectedObservation(
                    observation.observation_id,
                    reason,
                    _REJECTION_MESSAGES[reason],
                )
            )
    by_type = _group_by_type(tuple(trusted))
    reason_codes: set[str] = set()
    provenance: list[ContinuitySignalProvenance] = []

    context_degraded, item = _aggregate_boolean_or(
        by_type.get(ContinuitySignalType.CONTEXT_DEGRADED, ()),
        ContinuitySignalType.CONTEXT_DEGRADED,
    )
    provenance.append(item)
    important_claim, item = _aggregate_boolean_or(
        by_type.get(ContinuitySignalType.IMPORTANT_CLAIM, ()),
        ContinuitySignalType.IMPORTANT_CLAIM,
    )
    provenance.append(item)
    requires_current_state, item = _aggregate_boolean_or(
        by_type.get(ContinuitySignalType.REQUIRES_CURRENT_STATE, ()),
        ContinuitySignalType.REQUIRES_CURRENT_STATE,
    )
    provenance.append(item)
    continuity_available, item, conflict = _aggregate_continuity_available(
        by_type.get(ContinuitySignalType.CONTINUITY_AVAILABLE, ()), policy
    )
    provenance.append(item)
    if conflict:
        reason_codes.add("continuity_available_conflict")

    freshness_value, item = _aggregate_priority_categorical(
        by_type.get(ContinuitySignalType.CONTEXT_FRESHNESS, ()),
        _FRESHNESS_PRIORITY,
        ContextFreshness.UNKNOWN.value,
        ContinuitySignalType.CONTEXT_FRESHNESS,
    )
    provenance.append(item)
    sensitivity_value, item = _aggregate_priority_categorical(
        by_type.get(ContinuitySignalType.SENSITIVITY, ()),
        _SENSITIVITY_PRIORITY,
        ComputeSensitivity.LOW.value,
        ContinuitySignalType.SENSITIVITY,
    )
    provenance.append(item)
    active_contradictions, item, capped = _aggregate_contradictions(
        by_type.get(ContinuitySignalType.ACTIVE_CONTRADICTION, ()), policy
    )
    provenance.append(item)
    if capped:
        reason_codes.add("contradiction_count_capped")
    evidence_coverage, item = _aggregate_evidence_coverage(
        by_type.get(ContinuitySignalType.EVIDENCE_COVERAGE_ITEM, ()),
        globally_empty=globally_empty,
    )
    provenance.append(item)

    if rejected:
        reason_codes.add("observations_rejected")
    if globally_empty:
        reason_codes.add("no_observations_provided")

    signals = ContinuityComputeSignals(
        context_degraded=context_degraded,
        context_freshness=ContextFreshness(freshness_value),
        evidence_coverage=evidence_coverage,
        active_contradictions=active_contradictions,
        sensitivity=ComputeSensitivity(sensitivity_value),
        continuity_available=continuity_available,
        important_claim=important_claim,
        requires_current_state=requires_current_state,
    )
    observation_ids = tuple(observation.observation_id for observation in trusted)
    ignored_ids = tuple(item.observation_id for item in rejected)
    reason_codes_tuple = tuple(sorted(reason_codes))
    provenance_tuple = tuple(provenance)
    identity_payload = {
        "schema_version": SIGNAL_PRODUCER_RESULT_SCHEMA_VERSION,
        "producer_version": SIGNAL_PRODUCER_VERSION,
        "policy_id": policy.policy_id,
        "signals": _signals_dict(signals),
        "provenance": [item.to_dict() for item in provenance_tuple],
        "rejected_observations": [item.to_dict() for item in rejected],
        "reason_codes": sorted(reason_codes_tuple),
        "observation_ids": sorted(observation_ids),
        "ignored_or_rejected_ids": sorted(ignored_ids),
    }
    return ContinuitySignalProductionResult(
        result_hash=_digest(identity_payload),
        schema_version=SIGNAL_PRODUCER_RESULT_SCHEMA_VERSION,
        producer_version=SIGNAL_PRODUCER_VERSION,
        policy_id=policy.policy_id,
        signals=signals,
        provenance=provenance_tuple,
        rejected_observations=tuple(rejected),
        reason_codes=reason_codes_tuple,
        observation_ids=observation_ids,
        ignored_or_rejected_ids=ignored_ids,
    )


__all__ = [
    "SIGNAL_PRODUCER_POLICY_VERSION",
    "SIGNAL_PRODUCER_RESULT_SCHEMA_VERSION",
    "SIGNAL_PRODUCER_VERSION",
    "ContinuitySignalPolicy",
    "ContinuitySignalProducerError",
    "ContinuitySignalProductionResult",
    "ContinuitySignalProvenance",
    "RejectedObservation",
    "produce_continuity_compute_signals",
]
