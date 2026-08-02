"""Runtime activation and observation evidence contracts.

The module deliberately carries no feature activation authority. It only records
what a caller requested, what the runtime actually prepared, and whether a
measurement was observed. Consumers must not infer PASS from missing evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


RUNTIME_EVIDENCE_SCHEMA_VERSION = "titan.runtime-evidence.v1"


class RuntimeEvidenceError(ValueError):
    """Raised when a runtime evidence contract violates its invariants."""


class ObservationState(str, Enum):
    """Explicit availability/result state for one runtime observer."""

    OBSERVED_ZERO = "observed_zero"
    OBSERVED_NONZERO = "observed_nonzero"
    NOT_OBSERVED = "not_observed"
    OBSERVER_FAILED = "observer_failed"
    NOT_APPLICABLE = "not_applicable"


class ActivationStage(str, Enum):
    """Highest stage that a feature can prove it reached."""

    NOT_REQUESTED = "not_requested"
    REQUESTED = "requested"
    CONFIGURED = "configured"
    DEPENDENCIES_READY = "dependencies_ready"
    REGISTERED = "registered"
    STARTED = "started"
    OBSERVED = "observed"
    EFFECTIVE = "effective"


def _required_text(value: str, name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise RuntimeEvidenceError(f"{name} must be non-empty")
    return normalized


def _canonical_refs(values: Iterable[str]) -> tuple[str, ...]:
    refs = tuple(sorted({_required_text(value, "source_ref") for value in values}))
    return refs


def _is_zero(value: object) -> bool:
    if isinstance(value, bool):
        return value is False
    if isinstance(value, (int, float)):
        return value == 0
    return False


@dataclass(frozen=True, slots=True)
class ObservationResult:
    """One observer result with explicit missing/failed semantics."""

    feature_name: str
    metric_name: str
    state: ObservationState
    observed_value: int | float | bool | str | None = None
    reason_code: str | None = None
    source_refs: tuple[str, ...] = ()
    schema_version: str = RUNTIME_EVIDENCE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "feature_name", _required_text(self.feature_name, "feature_name")
        )
        object.__setattr__(
            self, "metric_name", _required_text(self.metric_name, "metric_name")
        )
        if not isinstance(self.state, ObservationState):
            raise RuntimeEvidenceError("state must be an ObservationState")
        if self.schema_version != RUNTIME_EVIDENCE_SCHEMA_VERSION:
            raise RuntimeEvidenceError("unsupported runtime evidence schema")
        object.__setattr__(self, "source_refs", _canonical_refs(self.source_refs))

        if self.state is ObservationState.OBSERVED_ZERO:
            if not _is_zero(self.observed_value):
                raise RuntimeEvidenceError(
                    "OBSERVED_ZERO requires numeric zero or false observed_value"
                )
        elif self.state is ObservationState.OBSERVED_NONZERO:
            if self.observed_value is None or _is_zero(self.observed_value):
                raise RuntimeEvidenceError(
                    "OBSERVED_NONZERO requires a non-zero observed_value"
                )
        else:
            if self.observed_value is not None:
                raise RuntimeEvidenceError(
                    f"{self.state.value} cannot carry observed_value"
                )
            if self.reason_code is None:
                raise RuntimeEvidenceError(
                    f"{self.state.value} requires an explicit reason_code"
                )

        if self.reason_code is not None:
            object.__setattr__(
                self, "reason_code", _required_text(self.reason_code, "reason_code")
            )

    @property
    def was_observed(self) -> bool:
        return self.state in {
            ObservationState.OBSERVED_ZERO,
            ObservationState.OBSERVED_NONZERO,
        }

    @property
    def hard_gate_satisfied(self) -> bool:
        """Return true only for measured zero or an explicit non-applicable result."""

        return self.state in {
            ObservationState.OBSERVED_ZERO,
            ObservationState.NOT_APPLICABLE,
        }


@dataclass(frozen=True, slots=True)
class FeatureActivationReceipt:
    """Evidence that distinguishes requested configuration from effective runtime."""

    feature_name: str
    requested: bool
    configured: bool
    dependencies_ready: bool
    registered: bool
    started: bool
    observation: ObservationResult
    effective: bool
    failure_reason: str | None = None
    schema_version: str = RUNTIME_EVIDENCE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "feature_name", _required_text(self.feature_name, "feature_name")
        )
        if self.schema_version != RUNTIME_EVIDENCE_SCHEMA_VERSION:
            raise RuntimeEvidenceError("unsupported runtime evidence schema")
        if self.observation.feature_name != self.feature_name:
            raise RuntimeEvidenceError(
                "observation feature_name must match activation receipt"
            )

        ordered = (
            self.requested,
            self.configured,
            self.dependencies_ready,
            self.registered,
            self.started,
        )
        seen_false = False
        for value in ordered:
            if seen_false and value:
                raise RuntimeEvidenceError(
                    "activation stages cannot skip an earlier failed stage"
                )
            if not value:
                seen_false = True

        if self.observation.was_observed and not self.started:
            raise RuntimeEvidenceError(
                "observed runtime result requires the feature to have started"
            )

        if self.effective:
            if not all(ordered):
                raise RuntimeEvidenceError(
                    "effective feature requires every activation stage"
                )
            if not self.observation.was_observed:
                raise RuntimeEvidenceError(
                    "effective feature requires an observed runtime result"
                )
            if self.failure_reason is not None:
                raise RuntimeEvidenceError(
                    "effective feature cannot carry failure_reason"
                )
        elif self.requested and self.failure_reason is None:
            raise RuntimeEvidenceError(
                "requested but ineffective feature requires failure_reason"
            )

        if self.failure_reason is not None:
            object.__setattr__(
                self,
                "failure_reason",
                _required_text(self.failure_reason, "failure_reason"),
            )

    @property
    def highest_stage(self) -> ActivationStage:
        if self.effective:
            return ActivationStage.EFFECTIVE
        if self.observation.was_observed:
            return ActivationStage.OBSERVED
        if self.started:
            return ActivationStage.STARTED
        if self.registered:
            return ActivationStage.REGISTERED
        if self.dependencies_ready:
            return ActivationStage.DEPENDENCIES_READY
        if self.configured:
            return ActivationStage.CONFIGURED
        if self.requested:
            return ActivationStage.REQUESTED
        return ActivationStage.NOT_REQUESTED


def evaluate_hard_gates(
    observations: Iterable[ObservationResult],
) -> tuple[bool, tuple[str, ...]]:
    """Evaluate observer evidence without treating missing measurement as PASS."""

    failures = tuple(
        sorted(
            f"{item.feature_name}:{item.metric_name}:{item.state.value}"
            for item in observations
            if not item.hard_gate_satisfied
        )
    )
    return not failures, failures


__all__ = [
    "ActivationStage",
    "FeatureActivationReceipt",
    "ObservationResult",
    "ObservationState",
    "RUNTIME_EVIDENCE_SCHEMA_VERSION",
    "RuntimeEvidenceError",
    "evaluate_hard_gates",
]
