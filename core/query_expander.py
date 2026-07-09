"""
💡 core/query_expander.py — Query Decomposition + Expansion (V8.8)
===================================================================

Проблема: запросы идут «как есть». Сложный запрос «как связаны
термодинамика и квантовая механика» → один retrieval, который теряет
специфику каждой части.

Решение:
  1. Decompose: разбить сложный запрос на атомарные подзапросы
  2. Expand: добавить синонимы и связанные термины (RU↔EN)
  3. Multi-query retrieval: собрать результаты по всем подзапросам → RRF-fuse

Использование:
    expander = QueryExpander()
    subqueries = expander.decompose("термодинамика цикл Карно")
    # → ["термодинамика цикл Карно закон энтропия",
    #     "thermodynamics Carnot cycle entropy"]

    all_results = []
    for sq in subqueries:
        all_results.extend(retriever.retrieve(sq, top_k=5))
    fused = rrf_fuse(all_results, top_k=10)
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Sequence


# RU→EN научные синонимы (самые частые в World Skills KB)
_BILINGUAL_SYNONYMS: dict[str, str] = {
    "термодинамик": "thermodynamics",
    "квантов": "quantum",
    "электродинамик": "electrodynamics",
    "механик": "mechanics",
    "оптик": "optics",
    "ядерн": "nuclear",
    "гравитац": "gravitation",
    "энтроп": "entropy",
    "энтальп": "enthalpy",
    "дифференциал": "differential",
    "интеграл": "integral",
    "матриц": "matrix",
    "вектор": "vector",
    "алгоритм": "algorithm",
    "структур": "structure",
    "нейрон": "neural",
    "генетик": "genetics",
    "эволюци": "evolution",
    "катализ": "catalysis",
    "полимер": "polymer",
    "органическ": "organic",
    "неорганическ": "inorganic",
}

# Связки: "как связаны X и Y" → decompose на X и Y
_RELATION_PATTERNS = [
    re.compile(r"как\s+связан[ыо]?\s+(.+?)\s+и\s+(.+)", re.IGNORECASE),
    re.compile(r"связь\s+между\s+(.+?)\s+и\s+(.+)", re.IGNORECASE),
    re.compile(r"взаимосвязь\s+(.+?)\s+и\s+(.+)", re.IGNORECASE),
    re.compile(r"(?:отличие|разница)\s+между\s+(.+?)\s+и\s+(.+)", re.IGNORECASE),
    re.compile(r"(?:сравнени[ея])\s+(.+?)\s+и\s+(.+)", re.IGNORECASE),
    re.compile(r"(.+?)\s+(?:vs|versus)\s+(.+)", re.IGNORECASE),
]

# Простые разделители: "X и Y" в общем контексте
_CONJUNCTION_RE = re.compile(r"(.+?)\s+и\s+(.+)", re.IGNORECASE)


class QueryExpander:
    """
    Разложение и расширение запросов для улучшения recall.

    Без LLM. Чистый rule-based. Для русского и английского.
    """

    def __init__(
        self,
        *,
        synonyms: Dict[str, str] | None = None,
        max_subqueries: int = 5,
    ) -> None:
        self._synonyms = synonyms or _BILINGUAL_SYNONYMS
        self._max_subqueries = max_subqueries

    def decompose(self, query: str) -> list[str]:
        """
        Разложить сложный запрос на атомарные подзапросы.

        "как связаны термодинамика и квантовая механика"
        → ["термодинамика законы энтропия", "квантовая механика принципы",
           "связь термодинамики и квантовой механики"]
        """
        if not query or not query.strip():
            return []

        query = query.strip()
        subqueries: list[str] = []

        # 1. Попробовать relation-паттерны ("как связаны X и Y")
        for pattern in _RELATION_PATTERNS:
            match = pattern.search(query)
            if match:
                part_a = match.group(1).strip()
                part_b = match.group(2).strip()
                # Отдельные подзапросы для каждой части
                subqueries.append(part_a)
                subqueries.append(part_b)
                # Исходный запрос (для контекста связи)
                subqueries.append(f"связь {part_a} {part_b}")
                break

        # 2. Простое разделение по "и" если длинный запрос
        if not subqueries and " и " in query and len(query) > 30:
            parts = [p.strip() for p in query.split(" и ") if len(p.strip()) > 5]
            if len(parts) >= 2:
                subqueries.extend(parts[: self._max_subqueries])

        # 3. Всегда добавляем исходный запрос
        if query not in subqueries:
            subqueries.append(query)

        # 4. Расширение: для каждого подзапроса → EN-версия
        expanded: list[str] = []
        for sq in subqueries[: self._max_subqueries]:
            expanded.append(sq)
            en = self._to_english(sq)
            if en and en != sq.lower():
                expanded.append(en)

        # Дедупликация с сохранением порядка
        seen: set[str] = set()
        result: list[str] = []
        for q in expanded:
            norm = q.lower().strip()
            if norm and norm not in seen:
                seen.add(norm)
                result.append(q)

        return result[: self._max_subqueries]

    def expand(self, query: str) -> str:
        """
        Расширить один запрос синонимами/переводом.

        "термодинамика" → "термодинамика thermodynamics entropy"
        """
        if not query:
            return ""

        parts = [query]

        # Добавить EN-синонимы
        en_keys = set()
        for ru, en in self._synonyms.items():
            if ru in query.lower() and en not in en_keys:
                parts.append(en)
                en_keys.add(en)

        return " ".join(parts)

    def _to_english(self, query: str) -> str:
        """Перевести русские научные термины в запросе на английский."""
        tokens = query.lower().split()
        en_tokens: list[str] = []
        for token in tokens:
            translated = token
            for ru, en in self._synonyms.items():
                if ru in token:
                    translated = en
                    break
            en_tokens.append(translated)
        en = " ".join(en_tokens)
        return en if en != query.lower() else ""

    def decompose_and_expand(self, query: str) -> list[str]:
        """Decompose + expand → все подзапросы."""
        return self.decompose(query)


# ─── Глобальный экземпляр ────────────────────────────────────────────────────

_expander: Optional[QueryExpander] = None


def get_query_expander() -> QueryExpander:
    global _expander
    if _expander is None:
        _expander = QueryExpander()
    return _expander


__all__ = [
    "QueryExpander",
    "get_query_expander",
]
