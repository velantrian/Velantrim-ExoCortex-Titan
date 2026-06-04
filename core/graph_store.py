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
    """Минимальный контракт для Etir, Causal persist (local), ImmutableCore."""

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

    @abstractmethod
    def spreading_activation(
        self,
        seeds: list[str],
        *,
        max_hops: int = 2,
        top_k: int = 10,
        decay: float = 0.65,
    ) -> list[ActivatedNode]:
        ...

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
