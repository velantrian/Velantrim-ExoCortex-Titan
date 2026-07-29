"""
Regression test for the memory_graph.py reverse-edge weight cleanup
(Claude audit 2026-07-28, Low).

upsert_edge() used to store the reverse (to_id, from_id) edge at
weight*0.9 — a directional decay with no actual effect, since neither
get_neighbors() nor spreading_activation() ever reads a stored edge
weight. Stored symmetrically now.
"""
from __future__ import annotations

from core.backends.memory_graph import MemoryGraphStore


def test_reverse_edge_weight_matches_forward_edge_weight():
    store = MemoryGraphStore()
    store.upsert_edge("a", "b", weight=0.8)

    assert store._edges[("a", "b")] == 0.8
    assert store._edges[("b", "a")] == 0.8, (
        "reverse edge must carry the same weight as the forward edge, "
        "not an inert weight*0.9 decay"
    )


def test_get_neighbors_is_bidirectional():
    store = MemoryGraphStore()
    store.upsert_edge("a", "b", weight=0.8)

    assert "b" in store.get_neighbors("a")
    assert "a" in store.get_neighbors("b")
