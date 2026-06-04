"""
Causal Persistence — Neo4j :CausalRelation ↔ in-memory CausalGraph (V8.6).

Без graphiti/Neo4j — no-op; при graphiti!=None и CAUSAL_PERSIST=1 — MERGE в Neo4j.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from core.causal_graph import (
    BACKWARD_RELATION_TYPES,
    get_causal_graph,
    is_causal_graph_enabled,
)
from core.feature_config import get_config

logger = logging.getLogger(__name__)


def is_causal_persist_enabled() -> bool:
    return bool(get_config().app.causal_persist)


def should_load_causal_on_startup() -> bool:
    get_config().app
    load = (os.getenv("CAUSAL_LOAD_ON_STARTUP", "0") or "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )
    return bool(is_causal_graph_enabled() and load)


def _driver(graphiti: Any):
    return getattr(graphiti, "driver", None) or getattr(graphiti, "_driver", None)


async def fetch_relation_rows(graphiti: Any) -> list[dict[str, Any]]:
    """Прочитать все :CausalRelation из Neo4j."""
    driver = _driver(graphiti)
    if not driver:
        return []

    try:
        res = await driver.execute_query(
            """
            MATCH (r:CausalRelation)
            RETURN r.relation_id AS relation_id,
                   r.from_fact_id AS from_fact_id,
                   r.to_fact_id AS to_fact_id,
                   r.relation_type AS relation_type,
                   r.confidence AS confidence,
                   r.knowledge_status AS knowledge_status
            """
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("fetch_relation_rows: %s", exc)
        return []

    rows: list[dict[str, Any]] = []
    for rec in res.records or []:
        rtype = rec.get("relation_type")
        if rtype in BACKWARD_RELATION_TYPES:
            continue
        rows.append(
            {
                "relation_id": rec.get("relation_id"),
                "from_fact_id": rec.get("from_fact_id"),
                "to_fact_id": rec.get("to_fact_id"),
                "relation_type": rtype,
                "confidence": float(rec.get("confidence") or 0.8),
                "knowledge_status": rec.get("knowledge_status") or "known",
            }
        )
    return rows


async def import_graph_to_causal(graphiti: Any, *, merge: bool = True) -> int:
    """Загрузить Neo4j → process singleton CausalGraph."""
    if not is_causal_graph_enabled():
        return 0

    rows = await fetch_relation_rows(graphiti)
    if not rows:
        return 0

    n = get_causal_graph().import_snapshots(rows, merge=merge)
    logger.info("causal_persist: imported %d relations from Neo4j", n)
    return n


async def persist_relations_to_graph(
    graphiti: Any,
    relation_ids: list[str],
) -> int:
    if not graphiti or not relation_ids or not is_causal_persist_enabled():
        return 0

    driver = _driver(graphiti)
    if not driver:
        return 0

    graph = get_causal_graph()
    written = 0
    for rid in relation_ids:
        rel = graph.get_relation(rid)
        if not rel:
            continue
        try:
            await driver.execute_query(
                """
                MERGE (r:CausalRelation {relation_id: $rid})
                SET r.from_fact_id = $from_id,
                    r.to_fact_id = $to_id,
                    r.relation_type = $rtype,
                    r.confidence = $conf,
                    r.knowledge_status = $kstatus,
                    r.updated_at = datetime()
                """,
                rid=rel.relation_id,
                from_id=rel.from_fact_id,
                to_id=rel.to_fact_id,
                rtype=rel.relation_type,
                conf=rel.confidence,
                kstatus=rel.knowledge_status,
            )
            written += 1
        except Exception as exc:  # noqa: BLE001
            logger.debug("persist relation %s: %s", rid, exc)
    return written


async def reload_causal_from_graph(graphiti: Any) -> dict[str, int]:
    """Полная перезагрузка snapshot из Neo4j (для API admin)."""
    from core.causal_graph import reset_causal_graph

    reset_causal_graph()
    imported = await import_graph_to_causal(graphiti, merge=False)
    return {
        "imported": imported,
        "relation_count": get_causal_graph().stats()["total_relations"],
    }


__all__ = [
    "fetch_relation_rows",
    "import_graph_to_causal",
    "is_causal_persist_enabled",
    "persist_relations_to_graph",
    "reload_causal_from_graph",
    "should_load_causal_on_startup",
]
