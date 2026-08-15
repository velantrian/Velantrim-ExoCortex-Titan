"""
Фасад выбора L3-бэкенда: memory | sqlite | ladybug | neo4j.
`kuzu` принимается как устаревший псевдоним → ladybug (Kuzu заархивирован окт. 2025).
"""

from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import Literal

from core.graph_store import GraphStoreBackend

logger = logging.getLogger(__name__)

StorageKind = Literal["memory", "sqlite", "kuzu", "ladybug", "neo4j"]

_backend_singleton: GraphStoreBackend | None = None


def get_storage_kind() -> StorageKind:
    raw = (os.getenv("STORAGE_BACKEND", "sqlite") or "sqlite").strip().lower()
    if raw in ("memory", "sqlite", "kuzu", "ladybug", "neo4j", "graphiti"):
        return "neo4j" if raw in ("neo4j", "graphiti") else raw  # type: ignore[return-value]
    logger.warning("Неизвестный STORAGE_BACKEND=%s → sqlite", raw)
    return "sqlite"


def is_neo4j_required() -> bool:
    return get_storage_kind() == "neo4j"


def is_local_graph_store() -> bool:
    return get_storage_kind() in ("memory", "sqlite", "kuzu", "ladybug")


def reset_graph_store() -> None:
    """Reset the graph-store lifecycle and its cached observability snapshot."""
    global _backend_singleton
    _backend_singleton = None
    storage_info.cache_clear()


def get_graph_store(force_new: bool = False) -> GraphStoreBackend:
    """Локальный граф (Etir / ImmutableCore). Для neo4j — sqlite sidecar."""
    global _backend_singleton
    if _backend_singleton is not None and not force_new:
        return _backend_singleton

    from core.backends.factory import create_graph_store

    kind = get_storage_kind()
    if kind == "neo4j":
        _backend_singleton = create_graph_store("sqlite")
    else:
        _backend_singleton = create_graph_store(kind)
    logger.info("GraphStore: %s", type(_backend_singleton).__name__)
    return _backend_singleton


@lru_cache(maxsize=1)
def storage_info() -> dict:
    from core.backends.factory import backend_capabilities

    kind = get_storage_kind()
    store = get_graph_store()
    return {
        "backend": kind,
        "local_store": type(store).__name__,
        "neo4j_required": is_neo4j_required(),
        "sqlite_path": os.getenv("SQLITE_GRAPH_PATH", "./data/exocortex_graph.db"),
        "kuzu_path": os.getenv("KUZU_DB_PATH", "./data/exocortex.kuzu"),
        "ladybug_path": os.getenv("LADYBUG_DB_PATH", "./data/exocortex.lbug"),
        "capabilities": backend_capabilities(),
    }


__all__ = [
    "get_graph_store",
    "get_storage_kind",
    "is_local_graph_store",
    "is_neo4j_required",
    "reset_graph_store",
    "storage_info",
]
