"""
🧭 core/task_type.py — детерминированный классификатор ТИПА запроса (ru-first, без LLM).

Идея из канона L4 (Velantrim Brain): «Task Type Classifier» определяет, КАК думать над
запросом, и роутит стратегию reasoning:

    WHY / HOW / EXPLAIN / SOLVE / COMPARE  → рассуждение по графу (graph-expansion → цепочки)
    FACT                                   → прямой ответ (без расширения, быстрее)
    UNKNOWN                                → консервативно как не-рассуждение

Отдельно от `claim_type` (что ЗА утверждение факт) и от CognitiveMode (PRECISION/BALANCED —
насколько строго). Здесь — про НАМЕРЕНИЕ запроса. Аддитивно, чистые функции, stdlib-only.
"""
from __future__ import annotations

import re

FACT    = "FACT"
WHY     = "WHY"
HOW     = "HOW"
SOLVE   = "SOLVE"
EXPLAIN = "EXPLAIN"
COMPARE = "COMPARE"
UNKNOWN = "UNKNOWN"

# Типы, которым полезно рассуждение по причинному графу (graph-expansion).
REASONING_TYPES: frozenset = frozenset({WHY, HOW, SOLVE, EXPLAIN, COMPARE})

# Порядок важен: более специфичные намерения проверяются раньше общих.
_PATTERNS = (
    (COMPARE, re.compile(
        r"(сравн|чем\s+.*\s+отлич|отлича[ею]|в\s+чём\s+разниц|\bразниц|\bлучше\b|\bхуже\b|"
        r"\bversus\b|\bvs\b|\bпротив\b|\bили\b.*\?|\bcompare\b)", re.I)),
    (WHY, re.compile(
        r"(почему|зачем|отчего|по\s+как(ой|им)\s+причин|с\s+чем\s+связан|\bwhy\b|\bпричина\b)", re.I)),
    (SOLVE, re.compile(
        r"(\bреши\b|\bрешить\b|вычисли|посчита|рассчита|найди\s+решени|\bsolve\b|\bcalculate\b)", re.I)),
    (EXPLAIN, re.compile(
        r"(объясни|расскажи|\bопиши\b|что\s+так(ое|ие)|\bexplain\b|\bdescribe\b)", re.I)),
    (HOW, re.compile(
        # «как» как наречие образа действия, но НЕ «какой/какая/какое/какие/каков»
        r"(\bкак(?!ой|ая|ое|ие|ого|им|ом|ову|ова)\b|каким\s+образом|\bhow\b)", re.I)),
    (FACT, re.compile(
        r"(\bсколько\b|\bкогда\b|\bгде\b|\bкто\b|\bкак(ой|ая|ое|ие|ов)\b|\bwhen\b|\bwhere\b|"
        r"\bwho\b|how\s+many)", re.I)),
)


def classify_task_type(query: str) -> str:
    """Определить тип запроса. Возвращает FACT|WHY|HOW|SOLVE|EXPLAIN|COMPARE|UNKNOWN."""
    q = (query or "").strip().lower()
    if not q:
        return UNKNOWN
    for ttype, pat in _PATTERNS:
        if pat.search(q):
            return ttype
    return UNKNOWN


def is_reasoning_query(query: str) -> bool:
    """True, если тип запроса требует рассуждения (→ включать graph-expansion)."""
    return classify_task_type(query) in REASONING_TYPES


__all__ = [
    "classify_task_type", "is_reasoning_query", "REASONING_TYPES",
    "FACT", "WHY", "HOW", "SOLVE", "EXPLAIN", "COMPARE", "UNKNOWN",
]
