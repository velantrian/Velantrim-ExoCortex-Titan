"""
Graphiti / Neo4j adapter (Спринт 2.5, опционально).

Без установленного graphiti и STORAGE_BACKEND=neo4j|graphiti — no-op.
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

_client: Any = None
_checked = False


def is_graphiti_backend() -> bool:
    raw = (os.getenv("STORAGE_BACKEND") or "").strip().lower()
    return raw in ("neo4j", "graphiti")


def get_graphiti_client() -> Any | None:
    """
    Ленивая инициализация Graphiti-клиента.

    Ожидается объект с атрибутом driver (Neo4j async driver).
  """
    global _client, _checked
    if _checked:
        return _client
    _checked = True

    if not is_graphiti_backend():
        return None

    try:
        from graphiti_core import Graphiti  # type: ignore[import-untyped]
    except ImportError:
        logger.debug("graphiti_core не установлен — adapter no-op")
        return None

    uri = os.getenv("NEO4J_URI") or os.getenv("GRAPHITI_NEO4J_URI")
    user = os.getenv("NEO4J_USER") or os.getenv("GRAPHITI_NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD") or os.getenv("GRAPHITI_NEO4J_PASSWORD")
    if not uri:
        logger.warning("graphiti_adapter: NEO4J_URI не задан")
        return None

    try:
        _client = Graphiti(uri, user, password)
    except Exception as exc:  # noqa: BLE001
        logger.warning("graphiti_adapter init: %s", exc)
        _client = None
    return _client


async def reload_causal_from_graphiti() -> dict[str, Any]:
    """Re-admit derived :CausalRelation rows without resetting local Canon."""
    from core.causal_graph import is_causal_graph_enabled
    from core.causal_persistence import is_causal_persist_enabled, reload_causal_from_graph

    if not is_causal_graph_enabled():
        return {"ok": False, "reason": "ENABLE_CAUSAL_GRAPH=0"}

    graphiti = get_graphiti_client()
    if graphiti is None:
        return {
            "ok": False,
            "reason": "graphiti_unavailable",
            "hint": "STORAGE_BACKEND=neo4j и graphiti_core + NEO4J_URI",
        }

    stats = await reload_causal_from_graph(graphiti)
    return {
        "ok": True,
        "persist_enabled": is_causal_persist_enabled(),
        **stats,
    }


__all__ = [
    "get_graphiti_client",
    "is_graphiti_backend",
    "reload_causal_from_graphiti",
]
