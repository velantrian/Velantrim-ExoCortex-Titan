"""
ComputeController - adaptive compute policy for Velantrim.

This is an external routing policy, not a neural-network modification. It
decides which pipeline profile should be used for a query: fast, normal, deep,
verify, or creative.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from core.goal_frame import GoalFrame, GoalIntent, RiskLevel, infer_goal_frame


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
    """Return a conservative compute profile for a query."""
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


__all__ = [
    "ComputeDecision",
    "ComputePath",
    "decide_compute_path",
]
