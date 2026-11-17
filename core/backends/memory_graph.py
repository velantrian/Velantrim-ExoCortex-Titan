"""
In-memory граф для тестов и STORAGE_BACKEND=memory.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from core.graph_store import GraphStoreBackend


class MemoryGraphStore(GraphStoreBackend):
    def __init__(self) -> None:
        self._nodes: dict[str, dict[str, Any]] = {}
        self._edges: dict[tuple[str, str], float] = defaultdict(float)
        self._snapshots: dict[str, dict[str, Any]] = {}

    def upsert_node(self, node_id: str, *, label: str = "Entity", **props: Any) -> None:
        row = self._nodes.setdefault(node_id, {"label": label})
        row.update(props)
        row["label"] = label

    def upsert_edge(
        self,
        from_id: str,
        to_id: str,
        *,
        relation: str = "RELATED",
        weight: float = 1.0,
    ) -> None:
        if from_id == to_id:
            return
        key = (from_id, to_id)
        self._edges[key] = max(self._edges[key], weight)
        self._edges[(to_id, from_id)] = max(self._edges[(to_id, from_id)], weight * 0.9)
        self.upsert_node(from_id)
        self.upsert_node(to_id)

    def get_neighbors(self, node_id: str, *, limit: int = 50) -> list[str]:
        out: list[str] = []
        for (a, b), _w in self._edges.items():
            if a == node_id and b not in out:
                out.append(b)
            elif b == node_id and a not in out:
                out.append(a)
            if len(out) >= limit:
                break
        return out


    def create_snapshot(
        self,
        snapshot_id: str,
        *,
        reason: str = "",
        node_ids: list[str] | None = None,
    ) -> str:
        import time

        self._snapshots[snapshot_id] = {
            "snapshot_id": snapshot_id,
            "reason": reason,
            "node_ids": list(node_ids or []),
            "created_at": time.time(),
        }
        return snapshot_id

    def list_snapshots(self, *, limit: int = 20) -> list[dict[str, Any]]:
        items = sorted(
            self._snapshots.values(),
            key=lambda x: x.get("created_at", 0),
            reverse=True,
        )
        return items[:limit]
