"""
🧭 core/query_router.py — Query Router (V8.8, Codex audit)
============================================================

Классифицирует запросы по ТИПУ — чтобы retrieval выбирал правильную стратегию.
Без LLM, rule-based с лексическими маркерами (RU + EN).

Типы запросов:
  factual      — «что такое X?», «сколько стоит Y?» → lexical + dense + graph
  causal       — «почему X?», «как связано X и Y?» → causal graph traversal
  personal     — «что я говорил про X?», «мои заметки о Y» → episodic memory
  procedural   — «как сделать X?», «шаги для Y» → procedural + graph
  contradiction— «противоречит ли X Y?», «это правда что...?» → truth check
  summary      — «расскажи о X», «обзор Y» → multi-fact synthesis

Использование:
    router = QueryRouter()
    qtype = router.classify("почему вода кипит при 100 градусах")
    # → QueryType.CAUSAL
    strategy = router.routing_strategy(qtype)
    # → {"retrieval_mode": "causal_graph", "top_k": 15, "diversity": True}
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional


class QueryType(str, Enum):
    FACTUAL = "factual"           # «что такое X?», определение
    CAUSAL = "causal"             # «почему X?», причинность
    RELATIONAL = "relational"     # «как связаны X и Y?»
    PERSONAL = "personal"         # «что я говорил о X?», личная память
    PROCEDURAL = "procedural"     # «как сделать X?», шаги
    CONTRADICTION = "contradiction"  # «противоречит ли X Y?»
    SUMMARY = "summary"           # «расскажи о X», обзор
    COMPARISON = "comparison"     # «сравни X и Y», «отличие X от Y»
    UNKNOWN = "unknown"           # не классифицирован


# Лексические маркеры для каждого типа (RU + EN)
_TYPE_MARKERS: dict[QueryType, list[re.Pattern]] = {
    QueryType.CAUSAL: [
        re.compile(r"почему|причин|из-за|благодаря|вследствие|отчего", re.I),
        re.compile(r"why|cause|because|due to|reason", re.I),
        re.compile(r"что (вызвал|привел|приводит|обуслов)", re.I),
    ],
    QueryType.RELATIONAL: [
        re.compile(r"как\s+связан|связь\s+между|взаимосвязь", re.I),
        re.compile(r"how\s+(is|are)\s+.+\s+(related|connected|linked)", re.I),
        re.compile(r"отношение\s+между|зависимость\s+между", re.I),
    ],
    QueryType.PERSONAL: [
        re.compile(r"\b(я|мой|моя|моё|мои|мне|меня)\b.*\b(говорил|сказал|писал|думал|считал|помню|замет)", re.I),
        re.compile(r"\b(I|my|me|mine)\b.*\b(said|wrote|thought|remember|noted)", re.I),
        re.compile(r"что\s+(ты|вы)\s+(знаешь|помнишь|записал)", re.I),
    ],
    QueryType.PROCEDURAL: [
        re.compile(r"как\s+(сделать|построить|написать|реализовать|настроить|установить)", re.I),
        re.compile(r"how\s+(to|do I|can I|should I)\s+(make|build|write|implement|set|configure)", re.I),
        re.compile(r"шаги|инструкци|рецепт|алгоритм\s+действ", re.I),
        re.compile(r"пошагов|step.by.step|tutorial", re.I),
    ],
    QueryType.CONTRADICTION: [
        re.compile(r"противореч|опроверг|правда\s+ли|верно\s+ли|ошибк", re.I),
        re.compile(r"contradict|refute|is it true|is it correct|wrong|mistake", re.I),
        re.compile(r"это\s+(так|правда|верно|ошибка)", re.I),
    ],
    QueryType.SUMMARY: [
        re.compile(r"расскажи\s+(о|об|про)|обзор|опиши|что\s+ты\s+знаешь\s+(о|об|про)", re.I),
        re.compile(r"tell\s+(me\s+)?about|overview|summar|describe|what\s+(do\s+you\s+)?know\s+about", re.I),
    ],
    QueryType.COMPARISON: [
        re.compile(r"сравни|отличие|разница|сходство|vs\.?|versus", re.I),
        re.compile(r"compar|differen|similar|vs\.?|versus|better.*or", re.I),
    ],
    QueryType.FACTUAL: [
        re.compile(r"что\s+(такое|значит|означает|это|есть)\s+\S", re.I),
        re.compile(r"what\s+(is|are|does|do)\s+\S", re.I),
        re.compile(r"определи|определение|дефиниция|сколько|когда|где|кто", re.I),
        re.compile(r"defin|how many|how much|when|where|who", re.I),
    ],
}


@dataclass
class RoutingStrategy:
    """Стратегия retrieval для типа запроса."""
    query_type: QueryType
    retrieval_mode: str           # lexical / dense / causal_graph / hybrid / personal
    top_k: int                    # сколько фактов извлекать
    diversity: bool               # использовать MMR diversity?
    use_causal_graph: bool        # обходить causal graph?
    use_ego_net: bool             # расширять ego-net?
    use_working_memory: bool      # сначала проверить Working Memory?
    memory_type_filter: str | None  # фильтр по memory_type
    min_confidence: float         # минимальный confidence
    description: str              # человекочитаемое описание


# Стратегии retrieval для каждого типа запроса
ROUTING_STRATEGIES: dict[QueryType, RoutingStrategy] = {
    QueryType.CAUSAL: RoutingStrategy(
        query_type=QueryType.CAUSAL,
        retrieval_mode="causal_graph",
        top_k=15,
        diversity=True,
        use_causal_graph=True,
        use_ego_net=True,
        use_working_memory=False,
        memory_type_filter="semantic",
        min_confidence=0.4,
        description="Causal graph traversal: ищем цепочки причин, а не отдельные факты",
    ),
    QueryType.RELATIONAL: RoutingStrategy(
        query_type=QueryType.RELATIONAL,
        retrieval_mode="causal_graph",
        top_k=15,
        diversity=True,
        use_causal_graph=True,
        use_ego_net=True,
        use_working_memory=False,
        memory_type_filter="semantic",
        min_confidence=0.4,
        description="Graph path: ищем путь между концептами в графе с explain_path()",
    ),
    QueryType.PERSONAL: RoutingStrategy(
        query_type=QueryType.PERSONAL,
        retrieval_mode="hybrid",
        top_k=20,
        diversity=False,
        use_causal_graph=False,
        use_ego_net=False,
        use_working_memory=True,   # сначала кэш недавних фактов
        memory_type_filter="episodic",
        min_confidence=0.3,
        description="Personal memory: эпизодическая память + недавние факты из WorkingMemory",
    ),
    QueryType.PROCEDURAL: RoutingStrategy(
        query_type=QueryType.PROCEDURAL,
        retrieval_mode="hybrid",
        top_k=10,
        diversity=False,
        use_causal_graph=True,
        use_ego_net=True,
        use_working_memory=False,
        memory_type_filter="procedural",
        min_confidence=0.5,
        description="Procedural: ищем how-to и workflows, ego-net для связанных шагов",
    ),
    QueryType.CONTRADICTION: RoutingStrategy(
        query_type=QueryType.CONTRADICTION,
        retrieval_mode="hybrid",
        top_k=20,
        diversity=True,
        use_causal_graph=True,
        use_ego_net=False,
        use_working_memory=False,
        memory_type_filter=None,    # все типы — противоречия могут быть где угодно
        min_confidence=0.3,
        description="Contradiction check: ищем противоречащие факты через find_contradictions()",
    ),
    QueryType.SUMMARY: RoutingStrategy(
        query_type=QueryType.SUMMARY,
        retrieval_mode="hybrid",
        top_k=20,
        diversity=True,             # разнообразие важно для обзора
        use_causal_graph=True,
        use_ego_net=True,
        use_working_memory=False,
        memory_type_filter="semantic",
        min_confidence=0.4,
        description="Summary: широкий обзор с diversity + graph expansion",
    ),
    QueryType.COMPARISON: RoutingStrategy(
        query_type=QueryType.COMPARISON,
        retrieval_mode="hybrid",
        top_k=15,
        diversity=True,
        use_causal_graph=True,
        use_ego_net=True,
        use_working_memory=False,
        memory_type_filter="semantic",
        min_confidence=0.4,
        description="Comparison: извлекаем факты по обеим темам + связи между ними",
    ),
    QueryType.FACTUAL: RoutingStrategy(
        query_type=QueryType.FACTUAL,
        retrieval_mode="lexical",
        top_k=10,
        diversity=False,
        use_causal_graph=False,
        use_ego_net=False,
        use_working_memory=True,
        memory_type_filter="semantic",
        min_confidence=0.5,
        description="Factual: точный поиск (BM25 предпочтительнее dense)",
    ),
    QueryType.UNKNOWN: RoutingStrategy(
        query_type=QueryType.UNKNOWN,
        retrieval_mode="hybrid",
        top_k=10,
        diversity=True,
        use_causal_graph=True,
        use_ego_net=True,
        use_working_memory=True,
        memory_type_filter=None,
        min_confidence=0.4,
        description="Unknown: гибридный retrieval, всё включено",
    ),
}


class QueryRouter:
    """
    Классификатор запросов по типу → выбор стратегии retrieval.

    Без LLM. Rule-based на лексических маркерах.
    При конфликте (несколько типов) — приоритет: personal > causal > contradiction > procedural > comparison > relational > summary > factual.
    """

    # Приоритет типов при конфликте маркеров
    TYPE_PRIORITY: tuple[QueryType, ...] = (
        QueryType.PERSONAL,
        QueryType.CONTRADICTION,
        QueryType.CAUSAL,
        QueryType.PROCEDURAL,
        QueryType.COMPARISON,
        QueryType.RELATIONAL,
        QueryType.SUMMARY,
        QueryType.FACTUAL,
    )

    def classify(self, query: str) -> QueryType:
        """Классифицировать запрос по типу."""
        if not query or not query.strip():
            return QueryType.UNKNOWN

        query = query.strip()

        # Ищем все подходящие типы
        matches: list[QueryType] = []
        for qtype, patterns in _TYPE_MARKERS.items():
            for pat in patterns:
                if pat.search(query):
                    matches.append(qtype)
                    break

        if not matches:
            return QueryType.UNKNOWN

        if len(matches) == 1:
            return matches[0]

        # Конфликт: выбираем по приоритету
        for priority_type in self.TYPE_PRIORITY:
            if priority_type in matches:
                return priority_type

        return matches[0]

    def routing_strategy(self, query: str) -> RoutingStrategy:
        """Полная стратегия: classify → strategy."""
        qtype = self.classify(query)
        return ROUTING_STRATEGIES[qtype]

    def classify_with_confidence(self, query: str) -> dict[str, Any]:
        """Классификация с метаданными для диагностики."""
        qtype = self.classify(query)
        strategy = ROUTING_STRATEGIES[qtype]
        return {
            "query": query,
            "query_type": qtype.value,
            **strategy.__dict__,
        }


# ─── Глобальный экземпляр ────────────────────────────────────────────────────

_router: Optional[QueryRouter] = None


def get_query_router() -> QueryRouter:
    global _router
    if _router is None:
        _router = QueryRouter()
    return _router


__all__ = [
    "QueryRouter",
    "QueryType",
    "RoutingStrategy",
    "ROUTING_STRATEGIES",
    "get_query_router",
]
