from __future__ import annotations

import copy

from scripts.validate_kb_graph import validate_graph


def _graph() -> dict:
    return {
        "meta": {"schema_version": "kb_graph_v1", "total_nodes": 2, "total_edges": 1},
        "nodes": [
            {"id": "a", "claim": "A"},
            {"id": "b", "claim": "B"},
        ],
        "edges": [
            {
                "source_id": "a",
                "target_id": "b",
                "relation_type": "enables",
                "edge_basis": "curated_explicit",
            }
        ],
    }


def test_valid_graph_passes_without_granting_authority() -> None:
    report = validate_graph(_graph())

    assert report["ok"] is True
    assert report["nodes"] == 2
    assert report["edges"] == 1
    assert report["authority"] == "ARTIFACT_INTEGRITY_ONLY"


def test_dangling_edge_fails_closed() -> None:
    graph = _graph()
    graph["edges"][0]["target_id"] = "missing"

    report = validate_graph(graph)

    assert report["ok"] is False
    assert report["dangling_edges"] == 1


def test_duplicate_node_and_edge_are_reported() -> None:
    graph = _graph()
    graph["nodes"].append({"id": "a", "claim": "duplicate"})
    graph["meta"]["total_nodes"] = 3
    graph["edges"].append(copy.deepcopy(graph["edges"][0]))
    graph["meta"]["total_edges"] = 2

    report = validate_graph(graph)

    assert report["ok"] is False
    assert report["duplicate_node_ids"] == 1
    assert report["duplicate_edges"] == 1


def test_metadata_count_mismatch_is_not_silently_accepted() -> None:
    graph = _graph()
    graph["meta"]["total_edges"] = 999

    report = validate_graph(graph)

    assert report["ok"] is False
    assert report["count_mismatches"] == 1


def test_legacy_database_endpoint_names_remain_supported() -> None:
    graph = _graph()
    graph["edges"] = [
        {
            "from_fact_id": "a",
            "to_fact_id": "b",
            "relation_type": "requires",
        }
    ]

    report = validate_graph(graph)

    assert report["ok"] is True
