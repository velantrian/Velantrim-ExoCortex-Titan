"""
SQLite-граф для локального режима (Etir, ImmutableCore snapshots).
"""

from __future__ import annotations

import json
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any

from core.graph_store import ActivatedNode, GraphStoreBackend


class SQLiteGraphStore(GraphStoreBackend):
    def __init__(self, db_path: str | Path) -> None:
        self._path = Path(db_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._lock:
            conn = self._connect()
            try:
                conn.executescript(
                    """
                    CREATE TABLE IF NOT EXISTS gs_nodes (
                        node_id TEXT PRIMARY KEY,
                        label TEXT NOT NULL DEFAULT 'Entity',
                        props_json TEXT NOT NULL DEFAULT '{}',
                        updated_at REAL NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS gs_edges (
                        from_id TEXT NOT NULL,
                        to_id TEXT NOT NULL,
                        relation TEXT NOT NULL DEFAULT 'RELATED',
                        weight REAL NOT NULL DEFAULT 1.0,
                        PRIMARY KEY (from_id, to_id, relation)
                    );
                    CREATE INDEX IF NOT EXISTS idx_gs_edges_from ON gs_edges(from_id);
                    CREATE INDEX IF NOT EXISTS idx_gs_edges_to ON gs_edges(to_id);
                    CREATE TABLE IF NOT EXISTS gs_snapshots (
                        snapshot_id TEXT PRIMARY KEY,
                        reason TEXT,
                        node_ids_json TEXT NOT NULL DEFAULT '[]',
                        created_at REAL NOT NULL
                    );
                    """
                )
                conn.commit()
            finally:
                conn.close()

    def upsert_node(self, node_id: str, *, label: str = "Entity", **props: Any) -> None:
        now = time.time()
        props_json = json.dumps(props, ensure_ascii=False)
        with self._lock:
            conn = self._connect()
            try:
                conn.execute(
                    """
                    INSERT INTO gs_nodes (node_id, label, props_json, updated_at)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(node_id) DO UPDATE SET
                        label=excluded.label,
                        props_json=excluded.props_json,
                        updated_at=excluded.updated_at
                    """,
                    (node_id, label, props_json, now),
                )
                conn.commit()
            finally:
                conn.close()

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
            conn = self._connect()
            try:
                conn.execute(
                    """
                    INSERT INTO gs_edges (from_id, to_id, relation, weight)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(from_id, to_id, relation) DO UPDATE SET
                        weight = MAX(gs_edges.weight, excluded.weight)
                    """,
                    (from_id, to_id, relation, weight),
                )
                conn.execute(
                    """
                    INSERT INTO gs_edges (from_id, to_id, relation, weight)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(from_id, to_id, relation) DO UPDATE SET
                        weight = MAX(gs_edges.weight, excluded.weight)
                    """,
                    (to_id, from_id, relation, weight * 0.9),
                )
                conn.commit()
            finally:
                conn.close()

    def get_neighbors(self, node_id: str, *, limit: int = 50) -> list[str]:
        with self._lock:
            conn = self._connect()
            try:
                rows = conn.execute(
                    """
                    SELECT to_id AS nid FROM gs_edges WHERE from_id = ?
                    UNION
                    SELECT from_id AS nid FROM gs_edges WHERE to_id = ?
                    LIMIT ?
                    """,
                    (node_id, node_id, limit),
                ).fetchall()
                return [r["nid"] for r in rows]
            finally:
                conn.close()

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
        now = time.time()
        with self._lock:
            conn = self._connect()
            try:
                conn.execute(
                    """
                    INSERT INTO gs_snapshots (snapshot_id, reason, node_ids_json, created_at)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(snapshot_id) DO NOTHING
                    """,
                    (
                        snapshot_id,
                        reason,
                        json.dumps(list(node_ids or []), ensure_ascii=False),
                        now,
                    ),
                )
                conn.commit()
            finally:
                conn.close()
        return snapshot_id

    def list_snapshots(self, *, limit: int = 20) -> list[dict[str, Any]]:
        with self._lock:
            conn = self._connect()
            try:
                rows = conn.execute(
                    """
                    SELECT snapshot_id, reason, node_ids_json, created_at
                    FROM gs_snapshots ORDER BY created_at DESC LIMIT ?
                    """,
                    (limit,),
                ).fetchall()
                out = []
                for r in rows:
                    out.append(
                        {
                            "snapshot_id": r["snapshot_id"],
                            "reason": r["reason"],
                            "node_ids": json.loads(r["node_ids_json"] or "[]"),
                            "created_at": r["created_at"],
                        }
                    )
                return out
            finally:
                conn.close()
