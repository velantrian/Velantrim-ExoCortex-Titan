"""Deterministic stdlib-only benchmark for the bounded graph retrieval projection.

This benchmark measures projection boundedness and multi-hop candidate recall on a
small frozen synthetic graph. It is not production evidence and does not activate
any runtime path.
"""

from __future__ import annotations

import json
import time

from core.backends.memory_graph import MemoryGraphStore
from core.graph_retrieval_projection import GraphProjectionBudget, GraphRetrievalProjection


def build_fixture() -> MemoryGraphStore:
    store = MemoryGraphStore()
    edges = (
        ("project", "retrieval"),
        ("retrieval", "graph"),
        ("graph", "community"),
        ("community", "louvain"),
        ("graph", "temporal"),
        ("temporal", "graphiti"),
        ("retrieval", "bm25"),
        ("retrieval", "dense"),
        ("dense", "embeddings"),
        ("project", "reader"),
        ("reader", "structure"),
        ("reader", "provenance"),
    )
    for left, right in edges:
        store.upsert_edge(left, right)
    return store


def main() -> None:
    expected = {"graph", "community", "louvain", "temporal", "graphiti"}
    projection = GraphRetrievalProjection(
        build_fixture(),
        budget=GraphProjectionBudget(
            max_hops=4,
            max_nodes=32,
            max_neighbors_per_node=8,
            max_communities=8,
            activation_top_k=32,
        ),
    )

    started = time.perf_counter()
    result = projection.expand(["retrieval"])
    elapsed_ms = (time.perf_counter() - started) * 1000.0
    returned = {node.node_id for node in result.nodes}
    recall = len(expected & returned) / len(expected)

    print(
        json.dumps(
            {
                "benchmark": "graph-retrieval-projection-v1-synthetic",
                "seed": "retrieval",
                "expected_multi_hop_nodes": sorted(expected),
                "returned_nodes": len(returned),
                "communities": len(result.communities),
                "truncated": result.truncated,
                "multi_hop_recall": recall,
                "elapsed_ms": round(elapsed_ms, 3),
                "projection_version": result.projection_version,
                "authority": "read-side-derived-only",
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
