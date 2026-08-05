"""Deterministic, policy-driven trusted producer for ContinuityComputeSignals.

::

    typed observations (observations.py)
          |
          v
    trust + shape filtering, under one explicit policy
          |
          v
    deterministic, permutation-invariant aggregation
          |
          v
    ContinuityComputeSignals (unchanged core.compute_controller contract)
          |
          v
    ContinuitySignalProductionResult (signals + full provenance + rejections)

This module never imports network, clock, environment, or global mutable
state. It never mutates its inputs. It never constructs, imports, or wires
itself into ``core.continuity.shadow_runner``, ``StateReconciliationResult``,
``GoalProjectionResult``, ``OpenLoopProjectionResult``, or any other live
runtime state — a caller may pass its ``ContinuitySignalProductionResult
.signals`` into an existing shadow-runner input as a pure composition step,
but that wiring is deliberately left to the caller. This module carries no
Canon, TruthGate, compute-routing, advisory, response, persistence, or
action authority; it does not change ``ComputePath``, ``ComputeDecision``,
``decide_compute_path()``, ``ContinuityComputeSignals``, or
``assess_compute_with_continuity()``.

Isolation decision (see the accompanying ADR): this producer deliberately
does not import or bridge to ``core.evidence``, ``core.confidence``,
``core.contradiction_registry``, or ``core.provenance_chain``. Unifying
Titan's evidence/confidence/provenance primitives is a separate, larger
architectural decision that this PR does not make; duplicating a small,
local, fully-owned notion of confidence/evidence here is a scope choice, not
an accident, and is not declared permanent architecture.

Two aggregation decisions are underspecified by nature and are resolved here
explicitly rather than left implicit:

* ``evidence_coverage`` has two distinct empty cases. If the producer
  receives *zero observations at all*, every field falls back to the
  existing ``ContinuityComputeSignals()`` dataclass default — for
  ``evidence_coverage`` that default is ``1.0``, matching the pre-existing
  "no signal computed" / off-state semantics used throughout R4/R5A/R5B. If
  the producer receives *some* observations but *none* of type
  ``EVIDENCE_COVERAGE_ITEM`` survive trust filtering, that is a materially
  different situation — there is something to say about this stream, and
  evidence just isn't part of it — so this producer reports ``0.0``
  (fail-closed), not ``1.0``. A naive ``covered / total if total else 1.0``
  would silently collapse both cases into the permissive answer; this
  producer treats that collapse as the exact failure mode it must avoid.
* ``minimum_confirmations`` (policy) counts **distinct trusted producer
  identities**, not raw observation count, for every boolean signal that
  requires confirmation. One producer submitting many duplicate or
  fabricated observations can never single-handedly cross a
  ``minimum_confirmations`` threshold greater than 1.
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
    """Raised when a policy or the producer call itself is malformed."""


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
    if not isinstance(values, (frozenset, set)):
        raise ContinuitySignalProducerError(f"{name} must be a frozenset of strings")
    items = frozenset(_text(value, name) for value in values)
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
    """Immutable, content-addressed policy for one producer run.

    There is no field, default, or code path here that can disable
    shadow-only behavior or grant this producer runtime authority: the
    producer only ever returns a ``ContinuityComputeSignals`` value for the
    caller to pass into the existing, unchanged ``assess_compute_with_
    continuity()``.
    """

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
    """Explains exactly one output dimension of one production run."""

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
        object.__setattr__(
            self, "confidence", _score(self.confidence, "confidence")
        )
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
    """One input observation that did not survive trust or shape filtering."""

    observation_id: str
    reason_code: str
    message: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "observation_id", _text(self.observation_id, "observation_id")
        )
        object.__setattr__(
            self, "reason_code", _text(self.reason_code, "reason_code")
        )
        object.__setattr__(self, "message", _text(self.message, "message"))

    def to_dict(self) -> dict[str, object]:
        return {
            "observation_id": self.observation_id,
            "reason_code": self.reason_code,
            "message": self.message,
        }


@dataclass(frozen=True, slots=True)
class ContinuitySignalProductionResult:
    """The full, reproducible output of one ``produce_continuity_compute_signals`` call."""

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
        if any(
            not isinstance(item, ContinuitySignalProvenance)
            for item in self.provenance
        ):
            raise ContinuitySignalProducerError(
                "provenance must contain only ContinuitySignalProvenance"
            )
        if any(
            not isinstance(item, RejectedObservation)
            for item in self.rejected_observations
        ):
            raise ContinuitySignalProducerError(
                "rejected_observations must contain only RejectedObservation"
            )
        object.__setattr__(
            self, "reason_codes", tuple(sorted(set(self.reason_codes)))
        )
        object.__setattr__(
            self, "observation_ids", tuple(sorted(set(self.observation_ids)))
        )
        object.__setattr__(
            self,
            "ignored_or_rejected_ids",
            tuple(sorted(set(self.ignored_or_rejected_ids))),
        )
        expected = _digest(self._identity_payload())
        if self.result_hash != expected:
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
    if isinstance(observations, (str, bytes)) or not isinstance(
        observations, Sequence
    ):
        raise ContinuitySignalProducerError(
            "observations must be a sequence of ContinuitySignalObservation"
        )
    seen: dict[str, ContinuitySignalObservation] = {}
    for obs in observations:
        if not isinstance(obs, ContinuitySignalObservation):
            raise ContinuitySignalProducerError(
                "observations must contain only ContinuitySignalObservation values"
            )
        previous = seen.get(obs.observation_id)
        if previous is not None and previous != obs:
            raise ContinuitySignalProducerError(
                f"conflicting observation content for id {obs.observation_id}"
            )
        seen[obs.observation_id] = obs
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
    groups: dict[ContinuitySignalType, list[ContinuitySignalObservation]] = (
        defaultdict(list)
    )
    for observation in trusted:
        groups[observation.signal_type].append(observation)
    return {key: tuple(value) for key, value in groups.items()}


def _refs_union(observations: Iterable[ContinuitySignalObservation]) -> tuple[str, ...]:
    return tuple(sorted({ref for obs in observations for ref in obs.evidence_refs}))


def _producers(observations: Iterable[ContinuitySignalObservation]) -> tuple[str, ...]:
    return tuple(sorted({obs.producer for obs in observations}))


def _min_confidence(observations: tuple[ContinuitySignalObservation, ...]) -> float:
    return min((obs.confidence for obs in observations), default=0.0)


def _string_value(value: object) -> str:
    """Narrow a validated categorical observation value for dict lookups.

    Callers only reach this after grouping by a ``ContinuitySignalType``
    whose value shape ``observations.py`` already constrains to one of a
    fixed set of strings; this raises rather than silently coercing if that
    invariant is ever violated.
    """

    if not isinstance(value, str):
        raise ContinuitySignalProducerError(
            "expected a string-shaped observation value"
        )
    return value


def _required_scope(value: str | None) -> str:
    """Narrow a ``scope`` already guaranteed non-empty by trust filtering.

    ``_trust_reason`` rejects any ``ACTIVE_CONTRADICTION`` or
    ``EVIDENCE_COVERAGE_ITEM`` observation with an empty ``scope`` before it
    ever reaches aggregation, so this only raises if that invariant is
    violated.
    """

    if value is None:
        raise ContinuitySignalProducerError(
            "scope is required for this signal_type and must not be None here"
        )
    return value


def _aggregate_boolean_confirmed(
    group: tuple[ContinuitySignalObservation, ...],
    policy: ContinuitySignalPolicy,
    signal_type: ContinuitySignalType,
) -> tuple[bool, ContinuitySignalProvenance]:
    true_obs = tuple(obs for obs in group if obs.value is True)
    producers = _producers(true_obs)
    confirmed = len(producers) >= policy.minimum_confirmations
    rule = (
        f"{len(producers)}_distinct_producers_of_{policy.minimum_confirmations}_required"
        if true_obs
        else "no_trusted_true_observations"
    )
    provenance = ContinuitySignalProvenance(
        signal_type=signal_type,
        observation_ids=tuple(obs.observation_id for obs in true_obs),
        evidence_refs=_refs_union(true_obs),
        producers=producers,
        confidence=_min_confidence(true_obs),
        rule=rule,
        value=confirmed,
    )
    return confirmed, provenance


def _aggregate_continuity_available(
    group: tuple[ContinuitySignalObservation, ...],
    policy: ContinuitySignalPolicy,
) -> tuple[bool, ContinuitySignalProvenance, bool]:
    true_obs = tuple(obs for obs in group if obs.value is True)
    false_obs = tuple(obs for obs in group if obs.value is False)
    producers = _producers(true_obs)
    conflict = bool(true_obs) and bool(false_obs)

    if conflict:
        value = False
        rule = "conflicting_positive_and_negative_observations_fail_conservative"
        contributing = true_obs + false_obs
    elif len(producers) >= policy.minimum_confirmations:
        value = True
        rule = f"{len(producers)}_distinct_producers_of_{policy.minimum_confirmations}_required"
        contributing = true_obs
    else:
        value = False
        rule = "no_trusted_true_observations" if not true_obs else "insufficient_confirmations"
        contributing = true_obs

    provenance = ContinuitySignalProvenance(
        signal_type=ContinuitySignalType.CONTINUITY_AVAILABLE,
        observation_ids=tuple(obs.observation_id for obs in contributing),
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
        provenance = ContinuitySignalProvenance(
            signal_type=signal_type,
            observation_ids=(),
            evidence_refs=(),
            producers=(),
            confidence=0.0,
            rule="no_trusted_observations_default_applied",
            value=default_value,
        )
        return default_value, provenance

    top_priority = max(priority_table[_string_value(obs.value)] for obs in group)
    contributing = tuple(
        obs
        for obs in group
        if priority_table[_string_value(obs.value)] == top_priority
    )
    value = _string_value(contributing[0].value)
    rule = f"most_severe_among_{len(group)}_trusted_observations"
    provenance = ContinuitySignalProvenance(
        signal_type=signal_type,
        observation_ids=tuple(obs.observation_id for obs in contributing),
        evidence_refs=_refs_union(contributing),
        producers=_producers(contributing),
        confidence=_min_confidence(contributing),
        rule=rule,
        value=value,
    )
    return value, provenance


def _aggregate_contradictions(
    group: tuple[ContinuitySignalObservation, ...],
    policy: ContinuitySignalPolicy,
) -> tuple[int, ContinuitySignalProvenance, bool]:
    if not group:
        provenance = ContinuitySignalProvenance(
            signal_type=ContinuitySignalType.ACTIVE_CONTRADICTION,
            observation_ids=(),
            evidence_refs=(),
            producers=(),
            confidence=0.0,
            rule="no_trusted_observations",
            value=0,
        )
        return 0, provenance, False

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

    provenance = ContinuitySignalProvenance(
        signal_type=ContinuitySignalType.ACTIVE_CONTRADICTION,
        observation_ids=tuple(obs.observation_id for obs in unique),
        evidence_refs=_refs_union(unique),
        producers=_producers(unique),
        confidence=_min_confidence(unique),
        rule=rule,
        value=count,
    )
    return count, provenance, capped


def _aggregate_evidence_coverage(
    group: tuple[ContinuitySignalObservation, ...],
    *,
    globally_empty: bool,
) -> tuple[float, ContinuitySignalProvenance]:
    if globally_empty:
        provenance = ContinuitySignalProvenance(
            signal_type=ContinuitySignalType.EVIDENCE_COVERAGE_ITEM,
            observation_ids=(),
            evidence_refs=(),
            producers=(),
            confidence=0.0,
            rule="no_observations_at_all_matches_shadow_off_default",
            value=1.0,
        )
        return 1.0, provenance
    if not group:
        provenance = ContinuitySignalProvenance(
            signal_type=ContinuitySignalType.EVIDENCE_COVERAGE_ITEM,
            observation_ids=(),
            evidence_refs=(),
            producers=(),
            confidence=0.0,
            rule="no_trusted_evidence_observations_fail_closed",
            value=0.0,
        )
        return 0.0, provenance

    by_scope: dict[str, tuple[ContinuitySignalObservation, ...]] = defaultdict(tuple)
    for observation in sorted(group, key=lambda item: item.observation_id):
        scope = _required_scope(observation.scope)
        by_scope[scope] = by_scope[scope] + (observation,)

    considered: list[ContinuitySignalObservation] = []
    covered = 0
    for scope_key in sorted(by_scope):
        items = by_scope[scope_key]
        considered.extend(items)
        values = {item.value for item in items}
        if True in values and False not in values:
            covered += 1
    total = len(by_scope)
    value = round(covered / total, 6)
    rule = f"{covered}_of_{total}_unique_scopes_covered"

    provenance = ContinuitySignalProvenance(
        signal_type=ContinuitySignalType.EVIDENCE_COVERAGE_ITEM,
        observation_ids=tuple(obs.observation_id for obs in considered),
        evidence_refs=_refs_union(considered),
        producers=_producers(considered),
        confidence=_min_confidence(tuple(considered)),
        rule=rule,
        value=value,
    )
    return value, provenance


def produce_continuity_compute_signals(
    observations: Sequence[ContinuitySignalObservation],
    *,
    policy: ContinuitySignalPolicy,
) -> ContinuitySignalProductionResult:
    """Turn validated observations into one reproducible signal production result.

    Fully deterministic and permutation-invariant: the input is sorted by
    content-addressed ``observation_id`` before anything else runs, so the
    caller's input order never affects the output. Rejects (via
    ``ContinuitySignalProducerError``) rather than guesses when ``policy`` or
    ``observations`` are malformed; individual malformed/untrusted
    observations are reported in ``rejected_observations`` instead of
    raising, so one bad input never blocks the rest of a batch.
    """

    if not isinstance(policy, ContinuitySignalPolicy):
        raise ContinuitySignalProducerError("policy must be a ContinuitySignalPolicy")

    ordered = _ordered_unique(observations)
    globally_empty = len(ordered) == 0

    trusted: list[ContinuitySignalObservation] = []
    rejected: list[RejectedObservation] = []
    for observation in ordered:
        reason = _trust_reason(observation, policy)
        if reason is None:
            trusted.append(observation)
        else:
            rejected.append(
                RejectedObservation(
                    observation.observation_id, reason, _REJECTION_MESSAGES[reason]
                )
            )

    by_type = _group_by_type(tuple(trusted))
    reason_codes: set[str] = set()
    provenance: list[ContinuitySignalProvenance] = []

    context_degraded, prov = _aggregate_boolean_confirmed(
        by_type.get(ContinuitySignalType.CONTEXT_DEGRADED, ()),
        policy,
        ContinuitySignalType.CONTEXT_DEGRADED,
    )
    provenance.append(prov)

    important_claim, prov = _aggregate_boolean_confirmed(
        by_type.get(ContinuitySignalType.IMPORTANT_CLAIM, ()),
        policy,
        ContinuitySignalType.IMPORTANT_CLAIM,
    )
    provenance.append(prov)

    requires_current_state, prov = _aggregate_boolean_confirmed(
        by_type.get(ContinuitySignalType.REQUIRES_CURRENT_STATE, ()),
        policy,
        ContinuitySignalType.REQUIRES_CURRENT_STATE,
    )
    provenance.append(prov)

    continuity_available, prov, conflict = _aggregate_continuity_available(
        by_type.get(ContinuitySignalType.CONTINUITY_AVAILABLE, ()), policy
    )
    provenance.append(prov)
    if conflict:
        reason_codes.add("continuity_available_conflict")

    freshness_value, prov = _aggregate_priority_categorical(
        by_type.get(ContinuitySignalType.CONTEXT_FRESHNESS, ()),
        _FRESHNESS_PRIORITY,
        ContextFreshness.UNKNOWN.value,
        ContinuitySignalType.CONTEXT_FRESHNESS,
    )
    provenance.append(prov)

    sensitivity_value, prov = _aggregate_priority_categorical(
        by_type.get(ContinuitySignalType.SENSITIVITY, ()),
        _SENSITIVITY_PRIORITY,
        ComputeSensitivity.LOW.value,
        ContinuitySignalType.SENSITIVITY,
    )
    provenance.append(prov)

    active_contradictions, prov, capped = _aggregate_contradictions(
        by_type.get(ContinuitySignalType.ACTIVE_CONTRADICTION, ()), policy
    )
    provenance.append(prov)
    if capped:
        reason_codes.add("contradiction_count_capped")

    evidence_coverage, prov = _aggregate_evidence_coverage(
        by_type.get(ContinuitySignalType.EVIDENCE_COVERAGE_ITEM, ()),
        globally_empty=globally_empty,
    )
    provenance.append(prov)

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

    observation_ids = tuple(obs.observation_id for obs in trusted)
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
    result_hash = _digest(identity_payload)

    return ContinuitySignalProductionResult(
        result_hash=result_hash,
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
