"""Compute routing and continuity-aware shadow assessment for Velantrim.

The legacy ``decide_compute_path()`` API remains the sole owner of the normal
compute-route decision and is intentionally preserved byte-for-byte at its
public contract boundary: the same five ``ComputePath`` values, the same
``ComputeDecision`` fields/serialization, and the same function signature and
legacy behaviour.

Continuity R4 adds a separate, explicit ``assess_compute_with_continuity()``
shadow API. It may conservatively raise an already-computed legacy decision to
VERIFY or cap a DEEP decision when context is degraded. It does not add a new
compute path, mutate memory, retrieve data, write Canon, generate answers,
authorize actions, or wire itself into runtime.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import math

from core.goal_frame import GoalFrame, GoalIntent, RiskLevel, infer_goal_frame

CONTINUITY_COMPUTE_POLICY_VERSION = "continuity.compute.assessment.v1"


class ComputePath(str, Enum):
    FAST_PATH = "fast_path"
    NORMAL_PATH = "normal_path"
    DEEP_PATH = "deep_path"
    VERIFY_PATH = "verify_path"
    CREATIVE_PATH = "creative_path"


@dataclass(frozen=True)
class ComputeDecision:
    path: ComputePath
    retrieval_k: int
    require_truth_gate: bool
    require_reflection: bool
    require_noetic_pass: bool
    max_reasoning_steps: int
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "path": self.path.value,
            "retrieval_k": self.retrieval_k,
            "require_truth_gate": self.require_truth_gate,
            "require_reflection": self.require_reflection,
            "require_noetic_pass": self.require_noetic_pass,
            "max_reasoning_steps": self.max_reasoning_steps,
            "reasons": list(self.reasons),
        }


def decide_compute_path(
    query: str,
    *,
    goal: GoalFrame | None = None,
    candidate_count: int = 0,
    uncertainty: float = 0.0,
) -> ComputeDecision:
    """Return the existing conservative compute profile for a query."""
    g = goal or infer_goal_frame(query)
    reasons = list(g.reasons)

    if g.risk_level == RiskLevel.HIGH or g.intent == GoalIntent.VERIFY:
        reasons.append("verification or high-risk query")
        return ComputeDecision(
            path=ComputePath.VERIFY_PATH,
            retrieval_k=16,
            require_truth_gate=True,
            require_reflection=True,
            require_noetic_pass=True,
            max_reasoning_steps=6,
            reasons=reasons,
        )

    if g.intent == GoalIntent.CREATE:
        reasons.append("creative generation requested")
        return ComputeDecision(
            path=ComputePath.CREATIVE_PATH,
            retrieval_k=10,
            require_truth_gate=True,
            require_reflection=False,
            require_noetic_pass=True,
            max_reasoning_steps=4,
            reasons=reasons,
        )

    if (
        g.output_style == "deep"
        or g.intent in {GoalIntent.ANALYZE, GoalIntent.COMPARE, GoalIntent.EXPLAIN}
        or uncertainty >= 0.45
    ):
        reasons.append("deep analysis or elevated uncertainty")
        return ComputeDecision(
            path=ComputePath.DEEP_PATH,
            retrieval_k=14,
            require_truth_gate=True,
            require_reflection=True,
            require_noetic_pass=True,
            max_reasoning_steps=5,
            reasons=reasons,
        )

    if g.prefers_short_answer and candidate_count <= 4 and uncertainty < 0.25:
        reasons.append("short low-risk query")
        return ComputeDecision(
            path=ComputePath.FAST_PATH,
            retrieval_k=6,
            require_truth_gate=True,
            require_reflection=False,
            require_noetic_pass=False,
            max_reasoning_steps=2,
            reasons=reasons,
        )

    reasons.append("default balanced route")
    return ComputeDecision(
        path=ComputePath.NORMAL_PATH,
        retrieval_k=10,
        require_truth_gate=True,
        require_reflection=False,
        require_noetic_pass=True,
        max_reasoning_steps=3,
        reasons=reasons,
    )


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
    """Typed read-only continuity facts supplied by a separately trusted caller."""

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
class ContinuityComputeAssessment:
    """Shadow-only assessment around one unchanged legacy compute decision."""

    base_decision: ComputeDecision
    decision: ComputeDecision
    context_rebuild_required: bool
    reason_codes: tuple[str, ...]
    policy_version: str = CONTINUITY_COMPUTE_POLICY_VERSION
    shadow_only: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.base_decision, ComputeDecision):
            raise ValueError("base_decision must be a ComputeDecision")
        if not isinstance(self.decision, ComputeDecision):
            raise ValueError("decision must be a ComputeDecision")
        object.__setattr__(
            self,
            "context_rebuild_required",
            _strict_bool(
                self.context_rebuild_required,
                "context_rebuild_required",
            ),
        )
        normalized = tuple(sorted({str(value).strip() for value in self.reason_codes}))
        if any(not value for value in normalized):
            raise ValueError("reason_codes cannot contain empty values")
        object.__setattr__(self, "reason_codes", normalized)
        if not isinstance(self.policy_version, str) or not self.policy_version.strip():
            raise ValueError("policy_version must be a non-empty string")
        if self.shadow_only is not True:
            raise ValueError("continuity compute assessment must remain shadow-only")

    @property
    def changed_legacy_decision(self) -> bool:
        return self.decision != self.base_decision

    def to_dict(self) -> dict[str, object]:
        return {
            "policy_version": self.policy_version,
            "shadow_only": self.shadow_only,
            "base_decision": self.base_decision.to_dict(),
            "decision": self.decision.to_dict(),
            "changed_legacy_decision": self.changed_legacy_decision,
            "context_rebuild_required": self.context_rebuild_required,
            "reason_codes": list(self.reason_codes),
        }


def _with_continuity_reasons(
    decision: ComputeDecision,
    reason_codes: tuple[str, ...],
) -> list[str]:
    return [
        *decision.reasons,
        *(f"continuity:{reason}" for reason in reason_codes),
    ]


def _verify_decision(
    base: ComputeDecision,
    reason_codes: tuple[str, ...],
) -> ComputeDecision:
    return ComputeDecision(
        path=ComputePath.VERIFY_PATH,
        retrieval_k=16,
        require_truth_gate=True,
        require_reflection=True,
        require_noetic_pass=True,
        max_reasoning_steps=6,
        reasons=_with_continuity_reasons(base, reason_codes),
    )


def _cap_degraded_deep_decision(
    base: ComputeDecision,
    reason_codes: tuple[str, ...],
) -> ComputeDecision:
    if base.path is not ComputePath.DEEP_PATH:
        return base
    return ComputeDecision(
        path=ComputePath.NORMAL_PATH,
        retrieval_k=min(base.retrieval_k, 8),
        require_truth_gate=base.require_truth_gate,
        require_reflection=False,
        require_noetic_pass=base.require_noetic_pass,
        max_reasoning_steps=min(base.max_reasoning_steps, 3),
        reasons=_with_continuity_reasons(base, reason_codes),
    )


def assess_compute_with_continuity(
    query: str,
    *,
    signals: ContinuityComputeSignals,
    goal: GoalFrame | None = None,
    candidate_count: int = 0,
    uncertainty: float = 0.0,
) -> ContinuityComputeAssessment:
    """Assess typed continuity signals without changing the legacy API.

    The result is shadow-only. It can conservatively raise a route to VERIFY
    or cap a DEEP route under degraded context. It never introduces a new
    ``ComputePath`` value, so existing exhaustive consumers remain valid.
    """

    if not isinstance(signals, ContinuityComputeSignals):
        raise ValueError("signals must be ContinuityComputeSignals")

    base = decide_compute_path(
        query,
        goal=goal,
        candidate_count=candidate_count,
        uncertainty=uncertainty,
    )

    reasons: set[str] = set()
    rebuild_required = False

    if signals.context_degraded:
        reasons.add("context_degraded")
    if not signals.continuity_available and signals.requires_current_state:
        reasons.add("required_state_unavailable")
        rebuild_required = True
    if signals.context_freshness is ContextFreshness.CRITICAL_STALE:
        reasons.add("critical_state_staleness")
        rebuild_required = signals.requires_current_state
    elif signals.context_freshness is ContextFreshness.STALE:
        reasons.add("stale_state")
        rebuild_required = signals.requires_current_state
    if signals.active_contradictions:
        reasons.add("active_contradictions")
    if signals.evidence_coverage < 0.35:
        reasons.add("low_evidence_coverage")

    decision = base
    if signals.active_contradictions > 0 and signals.important_claim:
        reasons.add("important_claim_requires_conflict_verification")
        decision = _verify_decision(base, tuple(sorted(reasons)))
    elif rebuild_required:
        reasons.add("context_rebuild_required")
        decision = _verify_decision(base, tuple(sorted(reasons)))
    elif (
        signals.sensitivity in {ComputeSensitivity.HIGH, ComputeSensitivity.CRITICAL}
        and signals.evidence_coverage < 0.35
    ):
        if (
            signals.sensitivity is ComputeSensitivity.CRITICAL
            and signals.evidence_coverage < 0.15
        ):
            reasons.add("critical_sensitivity_insufficient_evidence")
        reasons.add("sensitive_claim_requires_verification")
        decision = _verify_decision(base, tuple(sorted(reasons)))
    elif signals.context_degraded and base.path is ComputePath.DEEP_PATH:
        reasons.add("degraded_context_depth_cap")
        decision = _cap_degraded_deep_decision(base, tuple(sorted(reasons)))

    return ContinuityComputeAssessment(
        base_decision=base,
        decision=decision,
        context_rebuild_required=rebuild_required,
        reason_codes=tuple(sorted(reasons)),
    )


__all__ = [
    "CONTINUITY_COMPUTE_POLICY_VERSION",
    "ComputeDecision",
    "ComputePath",
    "ComputeSensitivity",
    "ContextFreshness",
    "ContinuityComputeAssessment",
    "ContinuityComputeSignals",
    "assess_compute_with_continuity",
    "decide_compute_path",
]
