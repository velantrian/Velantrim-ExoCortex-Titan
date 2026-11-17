"""
Абстракция L3-хранилища — Neo4j/Graphiti опциональны.

Локально: sqlite | memory | ladybug (встроенный граф, форк Kuzu).
`kuzu` — устаревший псевдоним → ladybug (Kuzu заархивирован окт. 2025).
Сервер: neo4j (+ Graphiti).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class GraphNode:
    node_id: str
    label: str = "Entity"
    props: dict[str, Any] = field(default_factory=dict)
    activation: float = 0.0


@dataclass
class ActivatedNode:
    node_id: str
    score: float
    hops: int = 0


class GraphStoreBackend(ABC):
    """Derived graph API. Node upsert replaces its label/properties; edge upsert
    preserves existing endpoints and creates missing endpoints as Entity nodes.
    Edges are traversed without direction; repeat insertion keeps the max weight.
    These operations never change canonical fact confidence or ESM state.
    """

    @abstractmethod
    def upsert_node(self, node_id: str, *, label: str = "Entity", **props: Any) -> None:
        ...

    @abstractmethod
    def upsert_edge(
        self,
        from_id: str,
        to_id: str,
        *,
        relation: str = "RELATED",
        weight: float = 1.0,
    ) -> None:
        ...

    @abstractmethod
    def get_neighbors(self, node_id: str, *, limit: int = 50) -> list[str]:
        ...

    def spreading_activation(
        self,
        seeds: list[str],
        *,
        max_hops: int = 2,
        top_k: int = 10,
        decay: float = 0.65,
    ) -> list[ActivatedNode]:
        """Return at most top_k nodes, seeds at hop zero, decaying each hop.

        Reuses each backend's undirected neighbors, never changes node/fact state,
        and preserves the historical insertion-order tie behavior. Activation is
        a retrieval score, not evidence confidence or epistemic promotion.
        """
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
        """L3.5b ImmutableCore — по умолчанию no-op."""
        return snapshot_id

    def list_snapshots(self, *, limit: int = 20) -> list[dict[str, Any]]:
        return []


class GraphStoreBackendProtocol(Protocol):
    def upsert_node(self, node_id: str, *, label: str = "Entity", **props: Any) -> None: ...
    def upsert_edge(
        self,
        from_id: str,
        to_id: str,
        *,
        relation: str = "RELATED",
        weight: float = 1.0,
    ) -> None: ...
    def get_neighbors(self, node_id: str, *, limit: int = 50) -> list[str]: ...
    def spreading_activation(
        self,
        seeds: list[str],
        *,
        max_hops: int = 2,
        top_k: int = 10,
        decay: float = 0.65,
    ) -> list[ActivatedNode]: ...


__all__ = [
    "ActivatedNode",
    "GraphNode",
    "GraphStoreBackend",
    "GraphStoreBackendProtocol",
]
