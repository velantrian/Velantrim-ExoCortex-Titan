"""
In-memory граф для тестов и STORAGE_BACKEND=memory.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from core.graph_store import ActivatedNode, GraphStoreBackend


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
        # Cleanup (Claude audit 2026-07-28, Low): the reverse edge previously
        # stored weight*0.9 — a directional decay that had no effect, since
        # neither get_neighbors() nor spreading_activation() below ever reads
        # a stored edge weight (get_neighbors() explicitly discards it as
        # `_w`; spreading_activation() uses a fixed `decay` parameter
        # instead). Stored symmetrically now to stop implying a weighting
        # decision this class doesn't actually make.
        self._edges[(from_id, to_id)] = max(self._edges[(from_id, to_id)], weight)
        self._edges[(to_id, from_id)] = max(self._edges[(to_id, from_id)], weight)
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

    def spreading_activation(
        self,
        seeds: list[str],
        *,
        max_hops: int = 2,
        top_k: int = 10,
        decay: float = 0.65,
    ) -> list[ActivatedNode]:
        scores: dict[str, tuple[float, int]] = {}
        frontier: dict[str, tuple[float, int]] = {
            s: (1.0, 0) for s in seeds if s
        }
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
