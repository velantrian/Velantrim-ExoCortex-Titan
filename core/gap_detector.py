"""
Innenwelt MVP — детектор пробелов: цели vs факты в памяти (и опционально граф).
"""

from __future__ import annotations

import re
from typing import Any

from core.goal_stack import get_goal_stack

_WS = re.compile(r"\s+")


def _claim_corpus(facts: list[dict[str, Any]]) -> str:
    parts = []
    for f in facts:
        parts.append((f.get("claim") or "").lower())
        meta = f.get("metadata") or {}
        if isinstance(meta, dict) and meta.get("domain"):
            parts.append(str(meta["domain"]).lower())
    return " ".join(parts)


def _count_term_hits(terms: list[str], corpus: str) -> int:
    if not terms or not corpus:
        return 0
    hits = 0
    for t in terms:
        if len(t) < 3:
            continue
        if t in corpus:
            hits += 1
    return hits


def detect_gaps(
    user_id: str = "default",
    *,
    max_goals: int = 20,
    min_hits: int = 1,
) -> list[dict[str, Any]]:
    """
    Для каждой активной цели: если в памяти мало совпадений по ключевым словам — gap.

    Возвращает список:
      goal_id, title, gap_type, missing_terms, fact_hits, suggestion
    """
    from core.memory import get_all_facts

    goals = get_goal_stack().list_goals(user_id, status="active", limit=max_goals)
    if not goals:
        return []

    facts = get_all_facts()
    corpus = _claim_corpus(facts)
    gaps: list[dict[str, Any]] = []

    for goal in goals:
        terms = goal.search_terms()
        if not terms:
            terms = [goal.title.lower()[:40]]
        hits = _count_term_hits(terms, corpus)
        if hits >= min_hits:
            continue
        missing = [t for t in terms if len(t) >= 3 and t not in corpus][:8]
        gaps.append(
            {
                "goal_id": goal.goal_id,
                "title": goal.title,
                "gap_type": "no_supporting_facts",
                "missing_terms": missing or terms[:5],
                "fact_hits": hits,
                "priority": goal.priority,
                "suggestion": (
                    f"Добавьте факты по теме «{goal.title}» "
                    f"(ключевые слова: {', '.join(missing[:3]) or '—'})"
                ),
            }
        )

    gaps.sort(key=lambda g: (-int(g.get("priority", 0)), g["title"]))
    return gaps


def query_goal_alignment(
    query: str,
    user_id: str = "default",
) -> float:
    """
    Насколько запрос пересекается с активными целями (0..1).
    Используется для welfare goal_alignment при query.
    """
    q = _WS.sub(" ", (query or "").lower())
    if not q:
        return 0.5
    goals = get_goal_stack().list_goals(user_id, status="active", limit=10)
    if not goals:
        return 0.5
    best = 0.0
    for goal in goals:
        for term in goal.search_terms():
            if len(term) >= 3 and term in q:
                best = max(best, 1.0)
            elif len(term) >= 4 and term[:4] in q:
                best = max(best, 0.6)
        if goal.title.lower() in q:
            best = max(best, 1.0)
    return best if best > 0 else 0.25


__all__ = ["detect_gaps", "query_goal_alignment"]
