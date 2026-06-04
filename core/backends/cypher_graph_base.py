"""
База для встроенного Cypher-движка (LadybugDB; форк Kuzu) — Cypher + spreading activation.
"""

from __future__ import annotations

import base64
import json
import logging
import threading
import time
from abc import abstractmethod
from pathlib import Path
from typing import Any

from core.graph_store import ActivatedNode, GraphStoreBackend

logger = logging.getLogger(__name__)

SCHEMA = """
CREATE NODE TABLE IF NOT EXISTS GsNode (
    node_id STRING PRIMARY KEY,
    label STRING,
    props_json STRING,
    updated_at INT64
);
CREATE REL TABLE IF NOT EXISTS GsEdge (
    FROM GsNode TO GsNode,
    relation STRING,
    weight DOUBLE
);
CREATE NODE TABLE IF NOT EXISTS GsSnapshot (
    snapshot_id STRING PRIMARY KEY,
    reason STRING,
    node_ids_json STRING,
    created_at INT64
);
"""


def _encode_json(obj: Any) -> str:
    """JSON → base64-ASCII для хранения в STRING-поле.

    LadybugDB/Kuzu коэрсит строки вида `["a","b"]` в LIST и теряет кавычки/пробелы
    при round-trip (проверено: `["s1","s2"]` → `[s1,s2]`). base64 даёт чистый ASCII
    без скобок/кавычек, который движок не трогает.
    """
    raw = json.dumps(obj, ensure_ascii=False)
    return base64.b64encode(raw.encode("utf-8")).decode("ascii")


def _decode_json(blob: str | None, default: Any = None) -> Any:
    """base64-ASCII → JSON. Терпим к legacy/сырым значениям (старые БД)."""
    if not blob:
        return [] if default is None else default
    try:
        raw = base64.b64decode(blob.encode("ascii")).decode("utf-8")
        return json.loads(raw)
    except Exception:  # noqa: BLE001 — fallback на сырой JSON (до base64-формата)
        try:
            return json.loads(blob)
        except Exception:  # noqa: BLE001
            return [] if default is None else default


class CypherGraphStore(GraphStoreBackend):
    """Общая логика Etir-графа на встроенном Cypher-движке."""

    def __init__(self, db_path: str | Path) -> None:
        self._path = Path(db_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._init_db()
        self._ensure_schema()

    @abstractmethod
    def _init_db(self) -> None:
        ...

    @abstractmethod
    def _execute(self, cypher: str, params: dict[str, Any] | None = None) -> None:
        ...

    @abstractmethod
    def _query(self, cypher: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        ...

    def _ensure_schema(self) -> None:
        for stmt in SCHEMA.strip().split(";"):
            s = stmt.strip()
            if s:
                try:
                    self._execute(s)
                except Exception as exc:  # noqa: BLE001
                    logger.debug("schema stmt: %s", exc)

    def upsert_node(self, node_id: str, *, label: str = "Entity", **props: Any) -> None:
        now = int(time.time())
        props_json = _encode_json(props)
        with self._lock:
            self._execute(
                """
                MERGE (n:GsNode {node_id: $node_id})
                SET n.label = $label, n.props_json = $props_json, n.updated_at = $now
                """,
                {
                    "node_id": node_id,
                    "label": label,
                    "props_json": props_json,
                    "now": now,
                },
            )

    def upsert_edge(
        self,
        from_id: str,
        to_id: str,
        *,
        relation: str = "RELATED",
        weight: float = 1.0,
    ) -> None:
        if not from_id or not to_id or from_id == to_id:
            return
        self.upsert_node(from_id)
        self.upsert_node(to_id)
        with self._lock:
            # MERGE, не CREATE: повторный upsert одного и того же ребра НЕ плодит
            # дубликаты (на архивном Kuzu/LadybugDB это вызывало неограниченный рост
            # рёбер и искажало веса spreading-activation — аудит-фикс). Вес поднимается
            # до максимума. Обход в get_neighbors/spreading_activation ненаправленный
            # (-[e:GsEdge]-), поэтому одного ребра на пару достаточно.
            self._execute(
                """
                MATCH (a:GsNode {node_id: $from_id}), (b:GsNode {node_id: $to_id})
                MERGE (a)-[e:GsEdge {relation: $relation}]->(b)
                SET e.weight = CASE WHEN e.weight IS NULL OR e.weight < $weight
                                    THEN $weight ELSE e.weight END
                """,
                {
                    "from_id": from_id,
                    "to_id": to_id,
                    "relation": relation,
                    "weight": float(weight),
                },
            )

    def get_neighbors(self, node_id: str, *, limit: int = 50) -> list[str]:
        rows = self._query(
            """
            MATCH (a:GsNode {node_id: $node_id})-[e:GsEdge]-(b:GsNode)
            RETURN DISTINCT b.node_id AS nid
            LIMIT $limit
            """,
            {"node_id": node_id, "limit": limit},
        )
        return [r["nid"] for r in rows if r.get("nid")]

    def spreading_activation(
        self,
        seeds: list[str],
        *,
        max_hops: int = 2,
        top_k: int = 10,
        decay: float = 0.65,
    ) -> list[ActivatedNode]:
        scores: dict[str, tuple[float, int]] = {}
        frontier: dict[str, tuple[float, int]] = {s: (1.0, 0) for s in seeds if s}
        visited: set[str] = set()

        for hop in range(max_hops + 1):
            if not frontier:
                break
            nxt: dict[str, tuple[float, int]] = {}
            for nid, (act, h) in frontier.items():
                if nid in visited:
                    continue
                visited.add(nid)
                prev = scores.get(nid)
                if prev is None or act > prev[0]:
                    scores[nid] = (act, h)
                if hop >= max_hops:
                    continue
                for nb in self.get_neighbors(nid):
                    na = act * decay
                    if na < 0.01:
                        continue
                    old = nxt.get(nb)
                    if old is None or na > old[0]:
                        nxt[nb] = (na, hop + 1)
            frontier = nxt

        ranked = sorted(scores.items(), key=lambda x: x[1][0], reverse=True)
        return [
            ActivatedNode(node_id=n, score=s, hops=h)
            for n, (s, h) in ranked[:top_k]
        ]

    def create_snapshot(
        self,
        snapshot_id: str,
        *,
        reason: str = "",
        node_ids: list[str] | None = None,
    ) -> str:
        now = int(time.time())
        with self._lock:
            self._execute(
                """
                MERGE (s:GsSnapshot {snapshot_id: $snapshot_id})
                SET s.reason = $reason,
                    s.node_ids_json = $node_ids_json,
                    s.created_at = $now
                """,
                {
                    "snapshot_id": snapshot_id,
                    "reason": reason,
                    "node_ids_json": _encode_json(list(node_ids or [])),
                    "now": now,
                },
            )
        return snapshot_id

    def list_snapshots(self, *, limit: int = 20) -> list[dict[str, Any]]:
        rows = self._query(
            """
            MATCH (s:GsSnapshot)
            RETURN s.snapshot_id AS snapshot_id, s.reason AS reason,
                   s.node_ids_json AS node_ids_json, s.created_at AS created_at
            ORDER BY s.created_at DESC
            LIMIT $limit
            """,
            {"limit": limit},
        )
        out = []
        for r in rows:
            out.append(
                {
                    "snapshot_id": r.get("snapshot_id"),
                    "reason": r.get("reason"),
                    "node_ids": _decode_json(r.get("node_ids_json")),
                    "created_at": r.get("created_at"),
                }
            )
        return out


def rows_from_result(result: Any) -> list[dict[str, Any]]:
    """Материализует QueryResult (LadybugDB/Kuzu) в список dict-ов.

    Предпочитает rows_as_dict() (без зависимости от pandas; проверено на
    LadybugDB 0.17 — возвращает итерируемый QueryResult с dict-строками).
    Фоллбэк — has_next()/get_next() + get_column_names().
    """
    if result is None:
        return []
    if hasattr(result, "rows_as_dict"):
        try:
            return [dict(r) for r in result.rows_as_dict()]
        except Exception:  # noqa: BLE001 — деградируем на ручную итерацию
            pass
    out: list[dict[str, Any]] = []
    if hasattr(result, "has_next"):
        cols = list(result.get_column_names()) if hasattr(result, "get_column_names") else []
        while result.has_next():
            row = result.get_next()
            if cols and isinstance(row, (list, tuple)):
                out.append(dict(zip(cols, row)))
            elif isinstance(row, dict):
                out.append(row)
    return out


# Back-compat алиасы (Kuzu заархивирован окт. 2025 → LadybugDB-форк; QueryResult-API тот же).
rows_from_kuzu_result = rows_from_result
rows_from_ladybug_result = rows_from_result
