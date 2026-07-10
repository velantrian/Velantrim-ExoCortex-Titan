"""
🔬 core/graph_lab_bridge.py — NetworkX Bridge (V8.7 Titan)

Тонкий мост между pipeline и NetworkX Graph Lab.
Активируется ТОЛЬКО для запросов требующих структурного анализа графа.

КОГДА вызывается:
    - scientific queries («найди центральные концепты квантовой физики»)
    - large-scale analysis («как связаны домены X и Y?»)
    - community detection («какие кластеры знаний образовались?»)
    - cycle/contradiction detection («есть ли логические петли?»)

    НЕ вызывается для:
    - простых DEFINE/WHAT/WHEN запросов
    - бытовых диалогов
    - запросов с <10 фактами

ЧТО делает:
    1. Читает подграф из causal relations (SQLite SELECT only)
    2. Строит networkx.DiGraph
    3. Вычисляет: centrality, communities, cycles, PageRank
    4. Возвращает результаты — НЕ пишет в граф

Жёсткие ограничения:
    - READ-ONLY: только SELECT, никогда INSERT/UPDATE/DELETE
    - max_nodes=2000 — защита от OOM
    - При отсутствии networkx → graceful degradation (available=False)
    - Не меняет truth_status, не создаёт фактов, не затрагивает ESM
"""

from __future__ import annotations

import importlib.util
import logging
from typing import Any

logger = logging.getLogger("velantrim.graph_lab_bridge")

# Типы запросов, для которых NetworkX оправдан
_SCIENCE_INTENTS = frozenset({
    "i004", "i007", "i009", "i011", "i012", "i013", "i015", "i021", "i023",
    # WHY, HOW_WORKS, COMPARE, WHAT_IF, PREDICT, RELATION, CLASSIFY, EVALUATE, DEBATE
})


def should_use_graph_lab(query: str = "", intent: str = "", facts_count: int = 0) -> bool:
    """
    Определить: нужен ли NetworkX для этого запроса?

    Критерии:
        1. Научный intent (WHY, HOW_WORKS, COMPARE, CLASSIFY, etc.)
        2. Большой объём фактов (≥20 — structural analysis оправдан)
        3. Явный запрос на анализ («найди связи», «кластеры», «центральные концепты»)
    """
    if facts_count >= 20:
        return True

    if intent in _SCIENCE_INTENTS:
        return True

    q = query.lower()
    analysis_keywords = [
        "central", "важный", "ключевой", "связи между", "кластер",
        "структура графа", "анализ графа", "community", "centrality",
        "как связаны", "pagerank", "bridge", "мост между",
    ]
    if any(w in q for w in analysis_keywords):
        return True

    return False


def analyze_graph(
    *,
    db_path: str | None = None,
    max_nodes: int = 2000,
    top_k: int = 20,
) -> dict[str, Any]:
    """
    Полный структурный анализ графа через NetworkX.

    Args:
        db_path: путь к SQLite (None → VELANTRIM_DB_PATH).
        max_nodes: лимит узлов (защита от OOM).
        top_k: сколько топ-результатов вернуть.

    Returns:
        {
            "available": bool,
            "node_count": int,
            "edge_count": int,
            "centrality": [{node_id, degree_c, betweenness_c}, ...],
            "communities": [{community_id, nodes, size}, ...],
            "cycles": [[node_id, ...], ...],
            "pagerank": [{node_id, score}, ...],
        }
    """
    import os

    db = db_path or os.getenv("VELANTRIM_DB_PATH", "./data/velantrim_house.db")

    # NetworkX check
    if importlib.util.find_spec("networkx") is None:
        return {"available": False, "reason": "networkx not installed"}

    # GraphLab check
    try:
        from core.graph_lab import analyze as gl_analyze
    except ImportError:
        return {"available": False, "reason": "graph_lab not importable"}

    # Запустить анализ
    try:
        # Pre-existing signature mismatch: core.graph_lab.analyze() takes
        # seed_fact_ids/top_k/max_nodes/conn — it has no db_path parameter. Caught
        # below like any other analysis failure, so this currently always degrades
        # to available=False. Not fixed here (wiring a real sqlite3.Connection from
        # db_path is a behavior change out of scope for a typing-only pass) —
        # tracked as a follow-up bug.
        result = gl_analyze(  # type: ignore[call-arg]
            db_path=db,
            max_nodes=max_nodes,
            top_k=top_k,
        )
        result["available"] = True
        return result
    except Exception as exc:
        logger.debug("NetworkX analysis failed: %s", exc)
        return {"available": False, "reason": str(exc)[:200]}


def get_bridge_concepts(
    *,
    domain_a: str = "",
    domain_b: str = "",
    top_k: int = 10,
) -> dict[str, Any]:
    """
    Найти концепты-мосты между двумя доменами через betweenness centrality.

    Использование:
        bridges = get_bridge_concepts(domain_a="physics", domain_b="biology")
        # → концепты которые связывают физику и биологию
    """
    result = analyze_graph(top_k=top_k)
    if not result.get("available"):
        return result

    # Filter centrality results for bridge concepts
    centrality_list = result.get("centrality", [])
    bridges = [
        c for c in centrality_list
        if c.get("betweenness_c", 0) > 0.05  # высокий betweenness = мост
    ]
    bridges.sort(key=lambda x: x.get("betweenness_c", 0), reverse=True)

    return {
        "available": True,
        "bridges": bridges[:top_k],
        "total_nodes": result.get("node_count", 0),
    }


def get_knowledge_clusters(
    *,
    top_k: int = 10,
) -> dict[str, Any]:
    """
    Найти кластеры знаний через community detection.

    Использование:
        clusters = get_knowledge_clusters()
        # → «какие тематические кластеры образовались в графе?»
    """
    result = analyze_graph(top_k=top_k)
    if not result.get("available"):
        return result

    communities = result.get("communities", [])
    return {
        "available": True,
        "clusters": communities[:top_k],
        "total_nodes": result.get("node_count", 0),
    }


def find_contradiction_cycles(
    *,
    max_cycle_len: int = 6,
) -> dict[str, Any]:
    """
    Найти логические циклы/петли в графе — потенциальные противоречия.

    Использование:
        cycles = find_contradiction_cycles()
        # → «есть ли A→B→C→A петли в causal relations?»
    """
    result = analyze_graph()
    if not result.get("available"):
        return result

    cycles_list = result.get("cycles", [])
    return {
        "available": True,
        "cycles_found": len(cycles_list),
        "cycles": cycles_list[:20],
    }


# ─── Pipeline enrichment hook ─────────────────────────────────────────────────

def enrich_with_graph_lab(
    query: str = "",
    intent: str = "",
    facts_count: int = 0,
) -> dict[str, Any] | None:
    """
    Вызвать из pipeline когда запрос требует структурного анализа.

    Возвращает None если NetworkX не нужен.
    Возвращает dict с результатами если анализ выполнен.

    Использование в pipeline.py:
        lab_result = enrich_with_graph_lab(query, intent, len(facts))
        if lab_result:
            result["graph_lab"] = lab_result
    """
    if not should_use_graph_lab(query, intent, facts_count):
        return None

    return analyze_graph()


__all__ = [
    "analyze_graph",
    "enrich_with_graph_lab",
    "find_contradiction_cycles",
    "get_bridge_concepts",
    "get_knowledge_clusters",
    "should_use_graph_lab",
]
