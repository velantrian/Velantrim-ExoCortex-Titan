"""
Линза PERSONAL — ответ с учётом целей и контекста пользователя.
"""

from __future__ import annotations

import re
from typing import Any

_WS = re.compile(r"\s+")


def _terms_from_goals(user_id: str) -> list[str]:
    try:
        from core.goal_stack import get_goal_stack

        goals = get_goal_stack().list_goals(user_id, status="active", limit=20)
    except Exception:
        return []
    terms: list[str] = []
    for g in goals:
        terms.extend(g.search_terms())
    return list(dict.fromkeys(terms))


def filter_facts(
    facts: list[dict[str, Any]],
    query: str,
    user_id: str = "default",
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Приоритет фактам, связанным с запросом и активными целями."""
    q = _WS.sub(" ", (query or "").lower())
    goal_terms = _terms_from_goals(user_id)

    scored: list[tuple[float, dict[str, Any]]] = []
    for f in facts:
        claim = (f.get("claim") or "").lower()
        src = (f.get("source") or "").lower()
        score = float(f.get("retrieval_score") or f.get("confidence") or 0.5)
        if q and any(t in claim for t in q.split() if len(t) >= 4):
            score += 0.15
        for gt in goal_terms:
            if len(gt) >= 3 and gt in claim:
                score += 0.2
        if "user" in src or "personal" in src or "telegram" in src:
            score += 0.1
        scored.append((score, f))

    scored.sort(key=lambda x: -x[0])
    ranked = [f for _, f in scored]
    if not ranked:
        ranked = facts

    meta = {
        "goal_terms_used": goal_terms[:12],
        "facts_ranked": len(ranked),
    }
    return ranked, meta


def system_instructions(user_id: str = "default") -> str:
    try:
        from core.goal_stack import get_goal_stack

        goals = get_goal_stack().list_goals(user_id, status="active", limit=5)
        titles = [g.title for g in goals]
    except Exception:
        titles = []
    base = (
        "Режим PERSONAL: отвечай как персональный помощник пользователя. "
        "Тон — ясный и поддерживающий. Связывай ответ с текущими целями, если они релевантны."
    )
    if titles:
        base += f"\nАктивные цели пользователя: {', '.join(titles)}."
    return base


__all__ = ["filter_facts", "system_instructions"]
