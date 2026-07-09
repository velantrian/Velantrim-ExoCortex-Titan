"""
LadybugDB — встроенный граф (STORAGE_BACKEND=ladybug).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List

from core.backends.cypher_graph_base import CypherGraphStore, rows_from_ladybug_result

logger = logging.getLogger(__name__)


def _require_ladybug():
    """V8.7: ladybug>=0.17 (Kuzu archived Oct 2025, LadybugDB is the active MIT fork)."""
    try:
        import ladybug  # noqa: F401

        return ladybug
    except ImportError as exc:
        raise ImportError(
            "LadybugDB не установлен. Выполните: python -m pip install 'ladybug>=0.17'"
        ) from exc


class LadybugGraphStore(CypherGraphStore):
    def __init__(self, db_path: str | Path) -> None:
        self._lb = _require_ladybug()
        self._db = None
        self._conn = None
        super().__init__(db_path)

    def _init_db(self) -> None:
        path = str(self._path)
        if path.endswith((".lbug", ".db")):
            db_file = path
        else:
            db_file = str(self._path / "exocortex.lbug")
        self._db = self._lb.Database(db_file)
        self._conn = self._lb.Connection(self._db)

    def _execute(self, cypher: str, params: Dict[str, Any] | None = None) -> None:
        self._conn.execute(cypher, parameters=params or {})

    def _query(self, cypher: str, params: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
        result = self._conn.execute(cypher, parameters=params or {})
        return rows_from_ladybug_result(result)

    def close(self) -> None:
        """Закрыть соединение и БД (фикстуры тестов вызывают в teardown)."""
        try:
            if self._conn is not None:
                self._conn.close()
        except Exception:  # noqa: BLE001
            pass
        self._conn = None
        self._db = None


__all__ = ["LadybugGraphStore"]
