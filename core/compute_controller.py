"""Adaptive compute policy for Velantrim.

ComputeController remains the sole owner of compute-path selection. Continuity
signals can conservatively raise a route to VERIFY or DEFER, request context
rebuild, or cap work under degraded context. This module does not retrieve,
write memory, change truth status, authorize actions, or generate answers.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math

from core.goal_frame import GoalFrame, GoalIntent, RiskLevel, infer_goal_frame

COMPUTE_POLICY_VERSION = "compute.controller.v2"


class ComputePath(str, Enum):
    FAST_PATH = "fast_path"
    NORMAL_PATH = "normal_path"
    DEEP_PATH = "deep_path"
    VERIFY_PATH = "verify_path"
    CREATIVE_PATH = "creative_path"
    DEFER_PATH = "defer_path"


class ContextFreshness(str, Enum):
    UNKNOWN = "unknown"
    FRESH = "fresh"
    STALE = "stale"
    CRITICAL_STALE = "critical_stale"


class ComputeSensitivity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


def _strict_bool(value: object, name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{name} must be a bool")
    return value


def _bounded_score(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite number in [0, 1]")
    result = float(value)
    if not math.isfinite(result) or not 0.0 <= result <= 1.0:
        raise ValueError(f"{name} must be a finite number in [0, 1]")
    return result


def _non_negative_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative int")
    return value


@dataclass(frozen=True, slots=True)
class ContinuityComputeSignals:
    """Typed read-only signals supplied to the existing ComputeController."""

    context_degraded: bool = False
    context_freshness: ContextFreshness = ContextFreshness.UNKNOWN
    evidence_coverage: float = 1.0
    active_contradictions: int = 0
    sensitivity: ComputeSensitivity = ComputeSensitivity.LOW
    continuity_available: bool = False
    important_claim: bool = False
    requires_current_state: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "context_degraded",
            _strict_bool(self.context_degraded, "context_degraded"),
        )
        if not isinstance(self.context_freshness, ContextFreshness):
            raise ValueError("context_freshness must be a ContextFreshness")
        object.__setattr__(
            self,
            "evidence_coverage",
            _bounded_score(self.evidence_coverage, "evidence_coverage"),
        )
        object.__setattr__(
            self,
            "active_contradictions",
            _non_negative_int(
                self.active_contradictions,
                "active_contradictions",
            ),
        )
        if not isinstance(self.sensitivity, ComputeSensitivity):
            raise ValueError("sensitivity must be a ComputeSensitivity")
        for field_name in (
            "continuity_available",
            "important_claim",
            "requires_current_state",
        ):
            object.__setattr__(
                self,
                field_name,
                _strict_bool(getattr(self, field_name), field_name),
            )


@dataclass(frozen=True, slots=True)
class ComputeDecision:
    path: ComputePath
    retrieval_k: int
    require_truth_gate: bool
    require_reflection: bool
    require_noetic_pass: bool
    max_reasoning_steps: int
    reasons: tuple[str, ...] = ()
    context_rebuild_required: bool = False
    defer_reason: str | None = None
    policy_version: str = COMPUTE_POLICY_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.path, ComputePath):
            raise ValueError("path must be a ComputePath")
        if (
            isinstance(self.retrieval_k, bool)
            or not isinstance(self.retrieval_k, int)
            or self.retrieval_k < 0
        ):
            raise ValueError("retrieval_k must be a non-negative int")
        if (
            isinstance(self.max_reasoning_steps, bool)
            or not isinstance(self.max_reasoning_steps, int)
            or self.max_reasoning_steps < 0
        ):
            raise ValueError("max_reasoning_steps must be a non-negative int")
        for field_name in (
            "require_truth_gate",
            "require_reflection",
            "require_noetic_pass",
            "context_rebuild_required",
        ):
            object.__setattr__(
                self,
                field_name,
                _strict_bool(getattr(self, field_name), field_name),
            )
        normalized_reasons = tuple(str(value) for value in self.reasons)
        if any(not value.strip() for value in normalized_reasons):
            raise ValueError("reasons cannot contain empty values")
        object.__setattr__(self, "reasons", normalized_reasons)
        if not isinstance(self.policy_version, str) or not self.policy_version.strip():
            raise ValueError("policy_version must be a non-empty string")
        if self.path is ComputePath.DEFER_PATH:
            if self.retrieval_k != 0 or self.max_reasoning_steps != 0:
                raise ValueError("DEFER_PATH must not allocate retrieval or reasoning")
            if not isinstance(self.defer_reason, str) or not self.defer_reason.strip():
                raise ValueError("DEFER_PATH requires defer_reason")
        elif self.defer_reason is not None:
            raise ValueError("defer_reason is only valid for DEFER_PATH")

    def to_dict(self) -> dict[str, object]:
        return {
            "path": self.path.value,
            "retrieval_k": self.retrieval_k,
            "require_truth_gate": self.require_truth_gate,
            "require_reflection": self.require_reflection,
            "require_noetic_pass": self.require_noetic_pass,
            "max_reasoning_steps": self.max_reasoning_steps,
            "reasons": list(self.reasons),
            "context_rebuild_required": self.context_rebuild_required,
            "defer_reason": self.defer_reason,
            "policy_version": self.policy_version,
        }


def _decision(
    path: ComputePath,
    *,
    retrieval_k: int,
    require_truth_gate: bool,
    require_reflection: bool,
    require_noetic_pass: bool,
    max_reasoning_steps: int,
    reasons: list[str],
    context_rebuild_required: bool = False,
    defer_reason: str | None = None,
) -> ComputeDecision:
    return ComputeDecision(
        path=path,
        retrieval_k=retrieval_k,
        require_truth_gate=require_truth_gate,
        require_reflection=require_reflection,
        require_noetic_pass=require_noetic_pass,
        max_reasoning_steps=max_reasoning_steps,
        reasons=tuple(reasons),
        context_rebuild_required=context_rebuild_required,
        defer_reason=defer_reason,
    )


def _continuity_override(
    signals: ContinuityComputeSignals,
    reasons: list[str],
) -> ComputeDecision | None:
    rebuild_required = False

    if signals.context_degraded:
        reasons.append("continuity:context_degraded")
    if not signals.continuity_available and signals.requires_current_state:
        reasons.append("continuity:required_state_unavailable")
        rebuild_required = True
    if signals.context_freshness is ContextFreshness.CRITICAL_STALE:
        reasons.append("continuity:critical_state_staleness")
        rebuild_required = signals.requires_current_state
    elif signals.context_freshness is ContextFreshness.STALE:
        reasons.append("continuity:stale_state")
        rebuild_required = signals.requires_current_state
    if signals.active_contradictions:
        reasons.append("continuity:active_contradictions")
    if signals.evidence_coverage < 0.35:
        reasons.append("continuity:low_evidence_coverage")

    if (
        signals.sensitivity is ComputeSensitivity.CRITICAL
        and signals.evidence_coverage < 0.15
    ):
        reasons.append("continuity:critical_sensitivity_insufficient_evidence")
        return _decision(
            ComputePath.DEFER_PATH,
            retrieval_k=0,
            require_truth_gate=True,
            require_reflection=False,
            require_noetic_pass=False,
            max_reasoning_steps=0,
            reasons=reasons,
            context_rebuild_required=rebuild_required,
            defer_reason="critical_sensitivity_insufficient_evidence",
        )

    if signals.active_contradictions > 0 and signals.important_claim:
        reasons.append("continuity:important_claim_requires_conflict_verification")
        return _decision(
            ComputePath.VERIFY_PATH,
            retrieval_k=16,
            require_truth_gate=True,
            require_reflection=True,
            require_noetic_pass=True,
            max_reasoning_steps=6,
            reasons=reasons,
            context_rebuild_required=rebuild_required,
        )

    if rebuild_required:
        reasons.append("continuity:context_rebuild_required")
        return _decision(
            ComputePath.VERIFY_PATH,
            retrieval_k=16,
            require_truth_gate=True,
            require_reflection=True,
            require_noetic_pass=True,
            max_reasoning_steps=6,
            reasons=reasons,
            context_rebuild_required=True,
        )

    if (
        signals.sensitivity in {ComputeSensitivity.HIGH, ComputeSensitivity.CRITICAL}
        and signals.evidence_coverage < 0.35
    ):
        reasons.append("continuity:sensitive_claim_requires_verification")
        return _decision(
            ComputePath.VERIFY_PATH,
            retrieval_k=16,
            require_truth_gate=True,
            require_reflection=True,
            require_noetic_pass=True,
            max_reasoning_steps=6,
            reasons=reasons,
        )

    return None


def _base_decision(
    goal: GoalFrame,
    *,
    candidate_count: int,
    uncertainty: float,
    reasons: list[str],
) -> ComputeDecision:
    if goal.risk_level == RiskLevel.HIGH or goal.intent == GoalIntent.VERIFY:
        reasons.append("verification or high-risk query")
        return _decision(
            ComputePath.VERIFY_PATH,
            retrieval_k=16,
            require_truth_gate=True,
            require_reflection=True,
            require_noetic_pass=True,
            max_reasoning_steps=6,
            reasons=reasons,
        )

    if goal.intent == GoalIntent.CREATE:
        reasons.append("creative generation requested")
        return _decision(
            ComputePath.CREATIVE_PATH,
            retrieval_k=10,
            require_truth_gate=True,
            require_reflection=False,
            require_noetic_pass=True,
            max_reasoning_steps=4,
            reasons=reasons,
        )

    if (
        goal.output_style == "deep"
        or goal.intent in {GoalIntent.ANALYZE, GoalIntent.COMPARE, GoalIntent.EXPLAIN}
        or uncertainty >= 0.45
    ):
        reasons.append("deep analysis or elevated uncertainty")
        return _decision(
            ComputePath.DEEP_PATH,
            retrieval_k=14,
            require_truth_gate=True,
            require_reflection=True,
            require_noetic_pass=True,
            max_reasoning_steps=5,
            reasons=reasons,
        )

    if goal.prefers_short_answer and candidate_count <= 4 and uncertainty < 0.25:
        reasons.append("short low-risk query")
        return _decision(
            ComputePath.FAST_PATH,
            retrieval_k=6,
            require_truth_gate=True,
            require_reflection=False,
            require_noetic_pass=False,
            max_reasoning_steps=2,
            reasons=reasons,
        )

    reasons.append("default balanced route")
    return _decision(
        ComputePath.NORMAL_PATH,
        retrieval_k=10,
        require_truth_gate=True,
        require_reflection=False,
        require_noetic_pass=True,
        max_reasoning_steps=3,
        reasons=reasons,
    )


def _apply_degraded_cap(
    decision: ComputeDecision,
    signals: ContinuityComputeSignals,
) -> ComputeDecision:
    if not signals.context_degraded or decision.path in {
        ComputePath.VERIFY_PATH,
        ComputePath.DEFER_PATH,
    }:
        return decision
    path = decision.path
    if path is ComputePath.DEEP_PATH:
        path = ComputePath.NORMAL_PATH
    return _decision(
        path,
        retrieval_k=min(decision.retrieval_k, 8),
        require_truth_gate=decision.require_truth_gate,
        require_reflection=False,
        require_noetic_pass=decision.require_noetic_pass,
        max_reasoning_steps=min(decision.max_reasoning_steps, 3),
        reasons=[*decision.reasons, "continuity:degraded_context_depth_cap"],
        context_rebuild_required=decision.context_rebuild_required,
    )


def decide_compute_path(
    query: str,
    *,
    goal: GoalFrame | None = None,
    candidate_count: int = 0,
    uncertainty: float = 0.0,
    continuity: ContinuityComputeSignals | None = None,
) -> ComputeDecision:
    """Return a deterministic conservative compute profile for a query."""
    if not isinstance(query, str):
        raise ValueError("query must be a string")
    candidate_total = _non_negative_int(candidate_count, "candidate_count")
    uncertainty_value = _bounded_score(uncertainty, "uncertainty")
    if continuity is not None and not isinstance(
        continuity, ContinuityComputeSignals
    ):
        raise ValueError("continuity must be ContinuityComputeSignals or None")

    goal_frame = goal or infer_goal_frame(query)
    reasons = list(goal_frame.reasons)

    if continuity is not None:
        override = _continuity_override(continuity, reasons)
        if override is not None:
            return override

    decision = _base_decision(
        goal_frame,
        candidate_count=candidate_total,
        uncertainty=uncertainty_value,
        reasons=reasons,
    )
    if continuity is None:
        return decision
    return _apply_degraded_cap(decision, continuity)


__all__ = [
    "COMPUTE_POLICY_VERSION",
    "ComputeDecision",
    "ComputePath",
    "ComputeSensitivity",
    "ContextFreshness",
    "ContinuityComputeSignals",
    "decide_compute_path",
]
