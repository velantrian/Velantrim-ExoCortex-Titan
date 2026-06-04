"""
core/cognitive_distance.py — unified fact↔query relevance (v0 baseline).

Ported from a DeepSeek design. A weighted blend of five axes
(semantic + temporal + epistemic + relational + usage) intended as an eventual
replacement for raw RRF(bm25, dense). v0 BASELINE — axes correlate; calibrate later
(learning-to-rank) and validate via tests/test_eval_golden.py before wiring into retrieval.

This increment lands the PURE FUNCTION only (no pipeline wiring) — side-effect-free,
easy to test and measure. The epistemic ladder reuses canon's truth thresholds spirit
(ImmutableCore > Validated > … > Collapsed).
"""
from __future__ import annotations

import math
from datetime import UTC, datetime
from typing import Any

DEFAULT_WEIGHTS = {
    "semantic": 0.40,
    "temporal": 0.20,
    "epistemic": 0.20,
    "relational": 0.10,
    "usage": 0.10,
}

EPISTEMIC_WEIGHTS: dict[str, float] = {
    "ImmutableCore": 1.00,
    "Validated": 0.90,
    "Supported": 0.70,
    "Hypothesized": 0.40,
    "Observed": 0.30,
    "Contradicted": 0.05,
    "Deprecated": 0.02,
    "Collapsed": 0.00,
}


def _now_ts() -> datetime:
    return datetime.now(UTC)


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def _parse_iso(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt
    except (ValueError, TypeError):
        return None


def semantic_similarity(fact_vector, query_vector) -> float:
    if fact_vector is None or query_vector is None:
        return 0.0
    return max(0.0, min(1.0, _cosine(fact_vector, query_vector)))


def temporal_relevance(t_start: str | None, t_end: str | None, *,
                       half_life_days: float = 30.0, now: datetime | None = None) -> float:
    now = now or _now_ts()
    if now.tzinfo is None:
        now = now.replace(tzinfo=UTC)
    if t_end:
        end_dt = _parse_iso(t_end)
        if end_dt and end_dt < now:
            return 0.01
    start_dt = _parse_iso(t_start)
    if start_dt is None:
        return 0.5
    age_days = (now - start_dt).days
    if age_days < 0:
        return 1.0
    return math.exp(-age_days / half_life_days)


def epistemic_weight(state: str) -> float:
    return EPISTEMIC_WEIGHTS.get(state, 0.0)


def relational_density(relations_count: int,
                       query_context_ids: list[str] | None = None) -> float:
    denom = 5.0 if query_context_ids is not None else 10.0
    return min(1.0, relations_count / denom)


def usage_weight(usage_count: int, last_used_at: str | None = None, *,
                 recency_half_life_hours: float = 24.0, now: datetime | None = None) -> float:
    now = now or _now_ts()
    base = min(1.0, math.log10(usage_count + 1) / math.log10(11))
    if last_used_at:
        last_dt = _parse_iso(last_used_at)
        if last_dt:
            hours = (now - last_dt).total_seconds() / 3600
            base = 0.7 * base + 0.3 * math.exp(-hours / recency_half_life_hours)
    return base


def cognitive_distance(fact: dict[str, Any], query_vector: list[float] | None = None, *,
                       query_context_ids: list[str] | None = None,
                       weights: dict[str, float] | None = None,
                       now: datetime | None = None) -> float:
    """Relevance of `fact` to a query in [0,1] (1=best). Never raises."""
    w = weights or DEFAULT_WEIGHTS
    now = now or _now_ts()
    sem = semantic_similarity(fact.get("semantic_vector"), query_vector)
    temp = temporal_relevance(fact.get("t_event_valid_start"),
                              fact.get("t_event_valid_end"), now=now)
    epi = epistemic_weight(fact.get("epistemic_state", "Observed"))
    rels = fact.get("relations", [])
    rel = relational_density(len(rels) if isinstance(rels, list) else 0, query_context_ids)
    use = usage_weight(int(fact.get("usage_count", 0) or 0), fact.get("last_used_at"), now=now)
    score = (w.get("semantic", 0.40) * sem
             + w.get("temporal", 0.20) * temp
             + w.get("epistemic", 0.20) * epi
             + w.get("relational", 0.10) * rel
             + w.get("usage", 0.10) * use)
    return round(max(0.0, min(1.0, score)), 4)


def rank_by_distance(facts: list[dict[str, Any]], query_vector: list[float] | None = None, *,
                     query_context_ids: list[str] | None = None,
                     weights: dict[str, float] | None = None,
                     top_k: int = 20) -> list[dict[str, Any]]:
    scored = []
    for f in facts:
        c = dict(f)
        c["cognitive_distance"] = cognitive_distance(
            f, query_vector=query_vector, query_context_ids=query_context_ids, weights=weights)
        scored.append(c)
    scored.sort(key=lambda x: x["cognitive_distance"], reverse=True)
    return scored[:top_k]


__all__ = [
    "DEFAULT_WEIGHTS", "EPISTEMIC_WEIGHTS", "cognitive_distance", "rank_by_distance",
    "semantic_similarity", "temporal_relevance", "epistemic_weight",
    "relational_density", "usage_weight",
]
