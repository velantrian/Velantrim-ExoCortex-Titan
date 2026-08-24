from core.backends.memory_graph import MemoryGraphStore
from core.graph_retrieval_projection import GraphProjectionBudget, GraphRetrievalProjection


def _store() -> MemoryGraphStore:
    store = MemoryGraphStore()
    for left, right in (
        ("a", "b"),
        ("b", "c"),
        ("c", "a"),
        ("c", "bridge"),
        ("bridge", "x"),
        ("x", "y"),
        ("y", "z"),
        ("z", "x"),
    ):
        store.upsert_edge(left, right)
    return store


def test_projection_is_read_side_and_deterministic() -> None:
    store = _store()
    before_nodes = dict(store._nodes)
    before_edges = dict(store._edges)
    projection = GraphRetrievalProjection(
        store,
        budget=GraphProjectionBudget(max_hops=3, max_nodes=16, max_neighbors_per_node=8),
    )

    first = projection.expand(["a"])
    second = projection.expand(["a"])

    assert first == second
    assert first.seeds == ("a",)
    assert {node.node_id for node in first.nodes} >= {"a", "b", "c", "bridge"}
    assert all(node.hop <= 3 for node in first.nodes)
    assert dict(store._nodes) == before_nodes
    assert dict(store._edges) == before_edges


def test_projection_preserves_discovery_provenance() -> None:
    result = GraphRetrievalProjection(_store()).expand(["a"])
    nodes = {node.node_id: node for node in result.nodes}

    assert nodes["a"].discovered_from is None
    assert nodes["b"].discovered_from == "a"
    assert nodes["c"].discovered_from == "a"
    assert nodes["a"].activation_score == 1.0
    assert nodes["b"].activation_score > 0.0


def test_projection_fails_bounded_on_node_budget() -> None:
    result = GraphRetrievalProjection(
        _store(),
        budget=GraphProjectionBudget(max_hops=4, max_nodes=3, max_neighbors_per_node=8),
    ).expand(["a"])

    assert result.truncated is True
    assert len(result.nodes) <= 3


def test_projection_fails_bounded_on_neighbor_budget() -> None:
    store = MemoryGraphStore()
    for index in range(10):
        store.upsert_edge("root", f"n{index}")

    result = GraphRetrievalProjection(
        store,
        budget=GraphProjectionBudget(max_hops=1, max_nodes=32, max_neighbors_per_node=3),
    ).expand(["root"])

    assert result.truncated is True
    assert len(result.nodes) <= 4


def test_empty_seed_set_is_empty_projection() -> None:
    result = GraphRetrievalProjection(_store()).expand(["", ""])

    assert result.seeds == ()
    assert result.nodes == ()
    assert result.communities == ()
    assert result.truncated is False


def test_budget_rejects_non_positive_values() -> None:
    try:
        GraphProjectionBudget(max_nodes=0)
    except ValueError as exc:
        assert "max_nodes" in str(exc)
    else:
        raise AssertionError("expected ValueError")
