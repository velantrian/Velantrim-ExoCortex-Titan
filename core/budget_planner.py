"""
core/budget_planner.py — adaptive retrieval budget (Adaptive-RAG / DRAGIN inspired).

Retrieval is "always-on" today. The deep-research report (doc-1, real papers: Adaptive-RAG,
DRAGIN, Self-RAG) argues the retrieval *mode* should scale with query complexity — trivial
questions need little/no retrieval, complex ones need more. This module estimates complexity
from cheap stdlib features (no LLM, no deps) and returns a plan.

Pure function; never raises. Wired into pipeline.retrieve() behind ENABLE_BUDGET_PLANNER
(default off ⇒ current fixed-k behavior). Measured by the eval ruler before any default flip.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

_WORD = re.compile(r"[А-Яа-яЁёA-Za-z0-9]+")
# crude "rare/technical token" signal: long tokens or ALL-CAPS acronyms / digits
_RARE = re.compile(r"[A-ZА-Я]{3,}|\w{12,}|\d")

# question words hint at multi-hop / reasoning needs
_COMPLEX_CUES = ("почему", "зачем", "сравни", "如何", "why", "how", "compare",
                 "что будет", "what if", "которые", "связан")


@dataclass(frozen=True)
class RetrievalPlan:
    mode: str        # none | lexical | hybrid
    k: int           # how many candidates to fetch
    max_hops: int    # graph expansion depth hint
    complexity: float  # 0..1 (for observability)

    def to_dict(self) -> dict:
        return {"mode": self.mode, "k": self.k, "max_hops": self.max_hops,
                "complexity": round(self.complexity, 3)}


def estimate_complexity(query: str) -> float:
    """Cheap [0,1] complexity score from length, rare tokens, and reasoning cues."""
    q = (query or "").strip()
    if not q:
        return 0.0
    tokens = _WORD.findall(q)
    n = len(tokens)
    length_sig = min(1.0, n / 20.0)                       # 20+ tokens → saturated
    rare_sig = min(1.0, len(_RARE.findall(q)) / 4.0)      # technical density
    low = q.lower()
    cue_sig = 1.0 if any(c in low for c in _COMPLEX_CUES) else 0.0
    score = 0.45 * length_sig + 0.30 * rare_sig + 0.25 * cue_sig
    return round(max(0.0, min(1.0, score)), 4)


def plan(query: str, *, base_k: int = 3) -> RetrievalPlan:
    """Pick retrieval mode/k by complexity. Never raises.

    trivial (<0.25)  → lexical, k=base_k (cheap; 'none' reserved for empty/echo)
    moderate (<0.60) → lexical, k=base_k+2
    complex (>=0.60) → hybrid,  k=base_k*2, deeper graph hops
    """
    c = estimate_complexity(query)
    if not query or not query.strip():
        return RetrievalPlan(mode="none", k=base_k, max_hops=0, complexity=0.0)
    if c < 0.25:
        return RetrievalPlan(mode="lexical", k=base_k, max_hops=1, complexity=c)
    if c < 0.60:
        return RetrievalPlan(mode="lexical", k=base_k + 2, max_hops=1, complexity=c)
    return RetrievalPlan(mode="hybrid", k=base_k * 2, max_hops=2, complexity=c)


__all__ = ["RetrievalPlan", "estimate_complexity", "plan"]
