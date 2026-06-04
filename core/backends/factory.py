"""
Фабрика бэкендов с fallback при отсутствии опциональных пакетов.

L3-граф: sqlite (default) | memory | ladybug (встроенный граф, форк Kuzu).
`kuzu` принимается как УСТАРЕВШИЙ псевдоним → LadybugDB: Kùzu Inc. заархивировала
Kuzu в октябре 2025; LadybugDB — поддерживаемый, API-совместимый форк.
"""

from __future__ import annotations

import logging
import os

from core.graph_store import GraphStoreBackend

logger = logging.getLogger(__name__)


def _create_ladybug(path_env: str, fallback_db: str) -> GraphStoreBackend:
    """LadybugDB по пути из env; при отсутствии пакета/ошибке — sqlite sidecar."""
    try:
        from core.backends.ladybug_graph import LadybugGraphStore

        path = os.getenv(path_env, "./data/exocortex.lbug")
        return LadybugGraphStore(path)
    except (ImportError, OSError, RuntimeError) as exc:
        logger.warning("LadybugDB недоступен (%s) → sqlite", exc)
        from core.backends.sqlite_graph import SQLiteGraphStore

        path = os.getenv("SQLITE_GRAPH_PATH", fallback_db)
        return SQLiteGraphStore(path)


def create_graph_store(kind: str) -> GraphStoreBackend:
    if kind == "memory":
        from core.backends.memory_graph import MemoryGraphStore

        return MemoryGraphStore()

    if kind == "sqlite":
        from core.backends.sqlite_graph import SQLiteGraphStore

        path = os.getenv("SQLITE_GRAPH_PATH", "./data/exocortex_graph.db")
        return SQLiteGraphStore(path)

    if kind == "ladybug":
        return _create_ladybug(
            "LADYBUG_DB_PATH", "./data/exocortex_graph_ladybug_fallback.db"
        )

    if kind == "kuzu":
        # Устаревший псевдоним: Kuzu заархивирован (окт. 2025) → LadybugDB.
        logger.warning(
            "STORAGE_BACKEND=kuzu устарел (Kuzu заархивирован Kùzu Inc. в окт. 2025). "
            "Использую LadybugDB. Обновите конфиг: STORAGE_BACKEND=ladybug."
        )
        # KUZU_DB_PATH поддерживается для совместимости старых .env.
        path_env = "LADYBUG_DB_PATH" if os.getenv("LADYBUG_DB_PATH") else "KUZU_DB_PATH"
        return _create_ladybug(path_env, "./data/exocortex_graph_kuzu_fallback.db")

    from core.backends.sqlite_graph import SQLiteGraphStore

    path = os.getenv("SQLITE_GRAPH_PATH", "./data/exocortex_graph_sidecar.db")
    return SQLiteGraphStore(path)


def _probe_ladybug() -> bool:
    try:
        import ladybug as lb

        db = lb.Database(":memory:")
        conn = lb.Connection(db)
        conn.execute("RETURN 1")
        return True
    except Exception:
        return False


def _probe_neo4j() -> bool:
    # neo4j доступен только через graphiti_adapter (нужен пакет graphiti-core). Честная проверка.
    try:
        import graphiti_core  # noqa: F401

        return True
    except Exception:
        return False


def backend_capabilities() -> dict:
    ladybug_ok = _probe_ladybug()
    return {
        "sqlite": True,
        "memory": True,
        "neo4j": _probe_neo4j(),   # было безусловно True → вводило в заблуждение (аудит-фикс)
        "ladybug": ladybug_ok,
        "kuzu": ladybug_ok,        # устаревший псевдоним → LadybugDB
    }


__all__ = ["backend_capabilities", "create_graph_store"]
