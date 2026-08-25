"""Bounded, read-side graph retrieval projection.

This module never mutates the graph and never promotes truth. It only derives
rebuildable retrieval candidates from an existing GraphStoreBackend.
"""

from __future__ import annotations

from collections import Counter, deque
from dataclasses import dataclass

from core.graph_store import GraphStoreBackendProtocol


@dataclass(frozen=True)
class GraphProjectionBudget:
    max_hops: int = 2
    max_nodes: int = 128
    max_neighbors_per_node: int = 32
    max_communities: int = 16
    activation_top_k: int = 64
    label_iterations: int = 4

    def __post_init__(self) -> None:
        for name, value in (
            ("max_hops", self.max_hops),
            ("max_nodes", self.max_nodes),
            ("max_neighbors_per_node", self.max_neighbors_per_node),
            ("max_communities", self.max_communities),
            ("activation_top_k", self.activation_top_k),
            ("label_iterations", self.label_iterations),
        ):
            if value < 1:
                raise ValueError(f"{name} must be >= 1")


@dataclass(frozen=True)
class GraphProjectionNode:
    node_id: str
    hop: int
    activation_score: float
    community_id: str
    discovered_from: str | None


@dataclass(frozen=True)
class GraphProjectionCommunity:
    community_id: str
    node_ids: tuple[str, ...]


@dataclass(frozen=True)
class GraphProjectionResult:
    seeds: tuple[str, ...]
    nodes: tuple[GraphProjectionNode, ...]
    communities: tuple[GraphProjectionCommunity, ...]
    truncated: bool
    projection_version: str = "graph-retrieval-projection-v1"


class GraphRetrievalProjection:
    """Provider-neutral read-side projection over the existing graph contract."""

    def __init__(
        self,
        store: GraphStoreBackendProtocol,
        *,
        budget: GraphProjectionBudget | None = None,
    ) -> None:
        self._store = store
        self._budget = budget or GraphProjectionBudget()

    def expand(self, seed_ids: list[str]) -> GraphProjectionResult:
        seeds = tuple(dict.fromkeys(seed for seed in seed_ids if seed))
        if not seeds:
            return GraphProjectionResult((), (), (), False)

        discovered: dict[str, tuple[int, str | None]] = {}
        adjacency: dict[str, set[str]] = {}
        queue: deque[tuple[str, int, str | None]] = deque(
            (seed, 0, None) for seed in seeds
        )
        truncated = False

        while queue:
            node_id, hop, parent = queue.popleft()
            if node_id in discovered:
                continue
            if len(discovered) >= self._budget.max_nodes:
                truncated = True
                break

            discovered[node_id] = (hop, parent)
            adjacency.setdefault(node_id, set())
            if hop >= self._budget.max_hops:
                continue

            raw_neighbors = self._store.get_neighbors(
                node_id, limit=self._budget.max_neighbors_per_node + 1
            )
            unique_neighbors = sorted(set(raw_neighbors))
            if len(unique_neighbors) > self._budget.max_neighbors_per_node:
                truncated = True
            for neighbor in unique_neighbors[: self._budget.max_neighbors_per_node]:
                if neighbor == node_id:
                    continue
                adjacency[node_id].add(neighbor)
                adjacency.setdefault(neighbor, set()).add(node_id)
                if neighbor not in discovered:
                    queue.append((neighbor, hop + 1, node_id))

        allowed = set(discovered)
        bounded_adjacency = {
            node_id: {neighbor for neighbor in neighbors if neighbor in allowed}
            for node_id, neighbors in adjacency.items()
            if node_id in allowed
        }
        labels = self._labels(bounded_adjacency)

        activation = self._bounded_activation(
            seeds,
            discovered,
            bounded_adjacency,
        )

        grouped: dict[str, list[str]] = {}
        for node_id in sorted(allowed):
            grouped.setdefault(labels[node_id], []).append(node_id)

        ordered_communities = sorted(
            grouped.items(),
            key=lambda item: (-len(item[1]), item[0]),
        )
        if len(ordered_communities) > self._budget.max_communities:
            truncated = True
        communities = tuple(
            GraphProjectionCommunity(community_id=label, node_ids=tuple(nodes))
            for label, nodes in ordered_communities[: self._budget.max_communities]
        )
        visible_communities = {community.community_id for community in communities}

        nodes = tuple(
            GraphProjectionNode(
                node_id=node_id,
                hop=discovered[node_id][0],
                activation_score=activation.get(node_id, 0.0),
                community_id=labels[node_id],
                discovered_from=discovered[node_id][1],
            )
            for node_id in sorted(
                (node for node in allowed if labels[node] in visible_communities),
                key=lambda node: (
                    -activation.get(node, 0.0),
                    discovered[node][0],
                    node,
                ),
            )
        )
        return GraphProjectionResult(seeds, nodes, communities, truncated)

    def _bounded_activation(
        self,
        seeds: tuple[str, ...],
        discovered: dict[str, tuple[int, str | None]],
        adjacency: dict[str, set[str]],
    ) -> dict[str, float]:
        """Return deterministic seed-proximity scores from the bounded projection only.

        This deliberately does not delegate to a backend activation routine: such a
        routine may traverse storage outside this projection's node and neighbor
        budget.  Scores express bounded local proximity, never truth or confidence.
        """
        candidates = [
            node_id
            for node_id in discovered
            if node_id in adjacency
        ]
        ranked = sorted(
            candidates,
            key=lambda node_id: (
                discovered[node_id][0],
                0 if node_id in seeds else 1,
                node_id,
            ),
        )[: self._budget.activation_top_k]
        return {
            node_id: 1.0 / (1.0 + discovered[node_id][0])
            for node_id in ranked
        }

    def _labels(self, adjacency: dict[str, set[str]]) -> dict[str, str]:
        labels = {node_id: node_id for node_id in adjacency}
        for _ in range(self._budget.label_iterations):
            changed = False
            for node_id in sorted(adjacency):
                neighbor_labels = [labels[n] for n in adjacency[node_id] if n in labels]
                if not neighbor_labels:
                    continue
                counts = Counter(neighbor_labels)
                best_count = max(counts.values())
                candidate = min(label for label, count in counts.items() if count == best_count)
                if candidate != labels[node_id]:
                    labels[node_id] = candidate
                    changed = True
            if not changed:
                break
        return labels


__all__ = [
    "GraphProjectionBudget",
    "GraphProjectionCommunity",
    "GraphProjectionNode",
    "GraphProjectionResult",
    "GraphRetrievalProjection",
]
