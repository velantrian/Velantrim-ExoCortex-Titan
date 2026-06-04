"""
AttentionRouter - transparent fact-focus scoring for Velantrim.

Transformer attention weighs tokens inside a model. This router weighs facts
outside the model. Its job is to decide which retrieved candidates deserve to
enter FactsPack / NoeticCore / answer construction.
"""
from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any

from core.goal_frame import GoalFrame, infer_goal_frame

_TOKEN_RE = re.compile(r"[\w\-]{3,}", re.UNICODE)


TRUST_BY_STATE = {
    "ImmutableCore": 1.00,
    "Validated": 0.95,
    "Supported": 0.75,
    "Hypothesized": 0.35,
    "Observed": 0.25,
    "Unverified": 0.20,
    "Contradicted": 0.0,
    "Collapsed": 0.0,
    "Deprecated": 0.0,
    "Retracted": 0.0,
}


@dataclass(frozen=True)
class AttentionWeights:
    goal_fit: float = 0.25
    relevance: float = 0.20
    trust: float = 0.20
    graph: float = 0.15
    memory: float = 0.10
    lens: float = 0.10
    risk: float = 0.20
    noise: float = 0.10


@dataclass(frozen=True)
class RoutedFact:
    fact_id: str
    claim: str
    score: float
    components: dict[str, float]
    source: str = ""
    epistemic_state: str = "Observed"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "fact_id": self.fact_id,
            "claim": self.claim,
            "score": self.score,
            "components": dict(self.components),
            "source": self.source,
            "epistemic_state": self.epistemic_state,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class AttentionRoute:
    query: str
    goal: dict
    selected: list[RoutedFact]
    discarded: list[dict]
    weights: dict
    route_note: str

    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "goal": self.goal,
            "selected": [x.to_dict() for x in self.selected],
            "discarded": list(self.discarded),
            "weights": dict(self.weights),
            "route_note": self.route_note,
        }


def _tokens(text: str) -> set[str]:
    return {m.group(0).lower() for m in _TOKEN_RE.finditer(text or "")}


def _clamp01(value: Any, default: float = 0.0) -> float:
    try:
        x = float(value)
    except (TypeError, ValueError):
        return default
    return min(1.0, max(0.0, x))


def _goal_fit(goal: GoalFrame, fact: dict, query_tokens: set[str]) -> float:
    claim = str(fact.get("claim") or "")
    claim_tokens = _tokens(claim)
    if not query_tokens or not claim_tokens:
        overlap = 0.0
    else:
        overlap = len(query_tokens & claim_tokens) / max(1, len(query_tokens))

    metadata = fact.get("metadata") or {}
    domain = str(fact.get("domain") or metadata.get("domain") or "").lower()
    domain_bonus = 0.15 if goal.domain_hint != "general" and goal.domain_hint in domain else 0.0

    return _clamp01(overlap + domain_bonus)


def score_candidate(
    query: str,
    fact: dict,
    *,
    goal: GoalFrame | None = None,
    weights: AttentionWeights | None = None,
) -> RoutedFact:
    """Score one candidate fact for transparent attention routing."""
    g = goal or infer_goal_frame(query)
    w = weights or AttentionWeights()
    query_tokens = _tokens(query)

    state = str(fact.get("epistemic_state") or fact.get("truth_status") or "Observed")
    trust = TRUST_BY_STATE.get(state, _clamp01(fact.get("confidence"), 0.5))
    confidence = _clamp01(fact.get("confidence"), 0.5)

    components = {
        "goal_fit": _goal_fit(g, fact, query_tokens),
        "relevance": _clamp01(fact.get("retrieval_score"), confidence),
        "trust": trust,
        "graph": _clamp01(fact.get("graph_score") or fact.get("graph_proximity"), 0.0),
        "memory": _clamp01(fact.get("memory_priority") or fact.get("salience"), 0.0),
        "lens": _clamp01(fact.get("lens_boost"), 0.0),
        "risk": _clamp01(fact.get("risk"), 0.0),
        "noise": _clamp01(fact.get("noise"), 0.0),
    }
    score = (
        w.goal_fit * components["goal_fit"]
        + w.relevance * components["relevance"]
        + w.trust * components["trust"]
        + w.graph * components["graph"]
        + w.memory * components["memory"]
        + w.lens * components["lens"]
        - w.risk * components["risk"]
        - w.noise * components["noise"]
    )
    score = round(max(0.0, score), 4)

    return RoutedFact(
        fact_id=str(fact.get("fact_id") or fact.get("id") or "unknown"),
        claim=str(fact.get("claim") or ""),
        score=score,
        components={k: round(v, 4) for k, v in components.items()},
        source=str(fact.get("source") or ""),
        epistemic_state=state,
        metadata=dict(fact.get("metadata") or {}),
    )


def route_attention(
    query: str,
    candidates: Iterable[dict],
    *,
    goal: GoalFrame | None = None,
    weights: AttentionWeights | None = None,
    top_k: int = 12,
    min_score: float = 0.15,
) -> AttentionRoute:
    """Rank candidate facts and return an explainable route."""
    g = goal or infer_goal_frame(query)
    w = weights or AttentionWeights()
    routed = [score_candidate(query, c, goal=g, weights=w) for c in candidates]
    routed.sort(key=lambda x: x.score, reverse=True)

    selected = [x for x in routed if x.score >= min_score][:top_k]
    selected_ids = {x.fact_id for x in selected}
    discarded = [
        {
            "fact_id": x.fact_id,
            "score": x.score,
            "reason": "below_min_score" if x.score < min_score else "outside_top_k",
        }
        for x in routed
        if x.fact_id not in selected_ids
    ]

    note = (
        f"selected={len(selected)} discarded={len(discarded)} "
        f"intent={g.intent.value} risk={g.risk_level.value}"
    )
    return AttentionRoute(
        query=query,
        goal=g.to_dict(),
        selected=selected,
        discarded=discarded,
        weights=w.__dict__,
        route_note=note,
    )


__all__ = [
    "AttentionRoute",
    "AttentionWeights",
    "RoutedFact",
    "route_attention",
    "score_candidate",
]
