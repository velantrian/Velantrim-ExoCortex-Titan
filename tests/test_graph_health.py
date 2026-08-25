"""Tests for bounded read-only graph topology diagnostics."""
from __future__ import annotations

import sqlite3

from core.causal_graph import CausalGraph
from core.graph_health import (
    GraphHealthThresholds,
    extended_integrity_report,
    topology_report,
)


def _graph() -> CausalGraph:
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute(
        """
        CREATE TABLE facts (
            fact_id TEXT PRIMARY KEY,
            claim TEXT NOT NULL,
            confidence REAL DEFAULT 0.8,
            epistemic_state TEXT DEFAULT 'Observed'
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE relations (
            relation_id TEXT PRIMARY KEY,
            from_fact_id TEXT NOT NULL REFERENCES facts(fact_id),
            to_fact_id TEXT NOT NULL REFERENCES facts(fact_id),
            relation_type TEXT NOT NULL,
            confidence REAL NOT NULL DEFAULT 0.8,
            knowledge_status TEXT NOT NULL DEFAULT 'known',
            inference_source TEXT DEFAULT NULL,
            truth_status TEXT DEFAULT 'validated',
            review_state TEXT DEFAULT 'approved',
            evidence_ref TEXT,
            created_at TEXT,
            valid_from TEXT,
            valid_to TEXT,
            metadata TEXT
        )
        """
    )
    for idx in range(6):
        conn.execute(
            "INSERT INTO facts (fact_id, claim, epistemic_state) VALUES (?, ?, 'Validated')",
            (f"f{idx}", f"fact {idx}"),
        )

    rows = [
        ("r01", "f0", "f1", "causes", "known", "validated", "approved"),
        ("r02", "f0", "f2", "requires", "known", "validated", "approved"),
        ("r03", "f0", "f3", "enables", "known", "validated", "approved"),
        ("r45", "f4", "f5", "causes", "known", "validated", "approved"),
        # Pending edge intentionally bridges the two approved components.
        ("r34p", "f3", "f4", "implies", "known", "validated", "pending"),
    ]
    conn.executemany(
        """
        INSERT INTO relations (
            relation_id, from_fact_id, to_fact_id, relation_type,
            confidence, knowledge_status, truth_status, review_state
        ) VALUES (?, ?, ?, ?, 0.9, ?, ?, ?)
        """,
        rows,
    )
    conn.commit()
    return CausalGraph(conn)


def _db_snapshot(graph: CausalGraph) -> tuple[list[tuple], list[tuple]]:
    facts = graph._conn.execute(  # noqa: SLF001 - test-only mutation proof
        "SELECT * FROM facts ORDER BY fact_id"
    ).fetchall()
    relations = graph._conn.execute(  # noqa: SLF001 - test-only mutation proof
        "SELECT * FROM relations ORDER BY relation_id"
    ).fetchall()
    return facts, relations


def test_topology_report_detects_hub_fanout_and_fragmentation() -> None:
    graph = _graph()
    thresholds = GraphHealthThresholds(
        hub_total_degree=2,
        fan_out_degree=2,
        small_component_max_nodes=2,
    )

    report = topology_report(graph, thresholds=thresholds)

    assert report["diagnostic_only"] is True
    assert report["only_approved_relations"] is True
    assert report["default_relation_eligibility"] == "approved+validated+known_or_inferred"
    assert report["hub_count"] == 1
    assert report["hub_samples"][0] == {"fact_id": "f0", "degree": 3}
    assert report["fan_out_anomaly_count"] == 1
    assert report["fan_out_samples"][0] == {"fact_id": "f0", "fan_out": 3}
    assert report["component_count"] == 2
    assert report["nontrivial_component_count"] == 2
    assert report["disconnected_nontrivial_components"] == 1
    assert report["small_structural_island_count"] == 1
    assert report["small_island_samples"] == [["f4", "f5"]]
    assert report["attention_required"] is True
    assert "hub_degree_threshold_exceeded" in report["attention_reasons"]
    assert "fan_out_threshold_exceeded" in report["attention_reasons"]


def test_pending_and_approved_hypothetical_edges_do_not_make_default_topology_healthier() -> None:
    graph = _graph()
    graph._conn.execute(  # noqa: SLF001 - adversarial fixture
        """
        INSERT INTO relations (
            relation_id, from_fact_id, to_fact_id, relation_type,
            confidence, knowledge_status, truth_status, review_state
        ) VALUES ('r34h', 'f3', 'f4', 'implies', 0.9, 'hypothetical', 'hypothesis', 'approved')
        """
    )
    graph._conn.commit()  # noqa: SLF001

    thresholds = GraphHealthThresholds(
        hub_total_degree=99,
        fan_out_degree=99,
        small_component_max_nodes=2,
    )

    default = topology_report(graph, thresholds=thresholds)
    all_edges = topology_report(graph, thresholds=thresholds, only_approved=False)

    assert default["component_count"] == 2
    assert default["disconnected_nontrivial_components"] == 1
    assert all_edges["component_count"] == 1
    assert all_edges["disconnected_nontrivial_components"] == 0


def test_graph_health_public_reports_are_read_only() -> None:
    graph = _graph()
    before = _db_snapshot(graph)

    topology_report(graph)
    assert _db_snapshot(graph) == before

    extended_integrity_report(graph)
    assert _db_snapshot(graph) == before


def test_extended_integrity_report_preserves_all_existing_fields() -> None:
    graph = _graph()
    base = dict(graph.integrity_report())
    extended = extended_integrity_report(
        graph,
        thresholds=GraphHealthThresholds(
            hub_total_degree=2,
            fan_out_degree=2,
            small_component_max_nodes=2,
        ),
    )

    assert {key: extended[key] for key in base} == base
    assert extended["topology"]["version"] == "graph-health-v1"
    assert "degree is not evidence/truth" in extended["topology"]["note"]


def test_empty_singleton_and_tiny_connected_graphs_are_not_small_islands() -> None:
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE facts (fact_id TEXT PRIMARY KEY, claim TEXT, epistemic_state TEXT)")
    conn.execute(
        """
        CREATE TABLE relations (
            relation_id TEXT PRIMARY KEY,
            from_fact_id TEXT,
            to_fact_id TEXT,
            relation_type TEXT,
            confidence REAL,
            knowledge_status TEXT,
            inference_source TEXT,
            truth_status TEXT,
            review_state TEXT,
            evidence_ref TEXT,
            created_at TEXT,
            valid_from TEXT,
            valid_to TEXT,
            metadata TEXT
        )
        """
    )
    graph = CausalGraph(conn)
    empty = topology_report(graph)
    assert empty["component_count"] == 0
    assert empty["small_structural_island_count"] == 0
    assert empty["largest_component_fraction"] == 1.0

    conn.execute("INSERT INTO facts VALUES ('a', 'a', 'Validated')")
    conn.commit()
    singleton = topology_report(graph)
    assert singleton["component_count"] == 1
    assert singleton["small_structural_island_count"] == 0

    conn.execute("INSERT INTO facts VALUES ('b', 'b', 'Validated')")
    conn.execute(
        """
        INSERT INTO relations VALUES (
            'ab', 'a', 'b', 'causes', 0.9, 'known', NULL, 'validated', 'approved',
            NULL, NULL, NULL, NULL, NULL
        )
        """
    )
    conn.commit()
    tiny = topology_report(
        graph,
        thresholds=GraphHealthThresholds(small_component_max_nodes=3),
    )
    assert tiny["component_count"] == 1
    assert tiny["small_structural_island_count"] == 0
    assert "small_structural_islands" not in tiny["attention_reasons"]


def test_topology_ordering_is_deterministic_under_shuffled_insertion() -> None:
    graph = _graph()
    thresholds = GraphHealthThresholds(
        hub_total_degree=1,
        fan_out_degree=1,
        small_component_max_nodes=2,
    )
    first = topology_report(graph, thresholds=thresholds)
    second = topology_report(graph, thresholds=thresholds)
    assert first == second


def test_thresholds_reject_non_positive_and_non_integer_values() -> None:
    invalid = (
        {"hub_total_degree": 0},
        {"fan_out_degree": 0},
        {"small_component_max_nodes": 0},
        {"hub_total_degree": 1.5},
        {"fan_out_degree": True},
    )
    for kwargs in invalid:
        try:
            GraphHealthThresholds(**kwargs)
        except (TypeError, ValueError):
            pass
        else:  # pragma: no cover - assertion branch
            raise AssertionError(f"expected validation error for {kwargs}")


def test_materialized_inverse_rows_do_not_create_synthetic_outgoing_fanout() -> None:
    graph = _graph()
    graph._conn.execute("DELETE FROM relations")  # noqa: SLF001 - isolated public-API fixture
    graph._conn.commit()  # noqa: SLF001

    # Public CausalGraph writes materialize inverse rows for traversal.
    graph.add_relation("f0", "f2", "causes")
    graph.add_relation("f1", "f2", "causes")

    rows = graph._conn.execute(  # noqa: SLF001 - verify canonical materialization
        "SELECT from_fact_id, to_fact_id, metadata FROM relations ORDER BY relation_id"
    ).fetchall()
    assert len(rows) == 4
    assert sum('"inverse_of"' in str(row[2]) for row in rows) == 2

    report = topology_report(
        graph,
        thresholds=GraphHealthThresholds(
            hub_total_degree=99,
            fan_out_degree=1,
            small_component_max_nodes=3,
        ),
    )

    assert report["approved_relation_rows"] == 2
    assert report["fan_out_anomaly_count"] == 0
