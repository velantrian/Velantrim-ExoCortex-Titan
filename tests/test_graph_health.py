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
        ("r01", "f0", "f1", "causes", "approved"),
        ("r02", "f0", "f2", "requires", "approved"),
        ("r03", "f0", "f3", "enables", "approved"),
        ("r45", "f4", "f5", "causes", "approved"),
        # Pending edge intentionally bridges the two approved components.
        ("r34p", "f3", "f4", "implies", "pending"),
    ]
    conn.executemany(
        """
        INSERT INTO relations (
            relation_id, from_fact_id, to_fact_id, relation_type,
            confidence, knowledge_status, truth_status, review_state
        ) VALUES (?, ?, ?, ?, 0.9, 'known', 'validated', ?)
        """,
        rows,
    )
    conn.commit()
    return CausalGraph(conn)


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


def test_pending_edges_do_not_make_approved_topology_look_healthier() -> None:
    graph = _graph()
    thresholds = GraphHealthThresholds(
        hub_total_degree=99,
        fan_out_degree=99,
        small_component_max_nodes=2,
    )

    approved = topology_report(
        graph,
        thresholds=thresholds,
        only_approved=True,
    )
    all_edges = topology_report(
        graph,
        thresholds=thresholds,
        only_approved=False,
    )

    assert approved["component_count"] == 2
    assert approved["disconnected_nontrivial_components"] == 1
    assert all_edges["component_count"] == 1
    assert all_edges["disconnected_nontrivial_components"] == 0


def test_extended_integrity_report_preserves_existing_score_semantics() -> None:
    graph = _graph()
    base = graph.integrity_report()
    extended = extended_integrity_report(
        graph,
        thresholds=GraphHealthThresholds(
            hub_total_degree=2,
            fan_out_degree=2,
            small_component_max_nodes=2,
        ),
    )

    assert extended["integrity_score"] == base["integrity_score"]
    assert extended["healthy"] == base["healthy"]
    assert extended["recommendation"] == base["recommendation"]
    assert extended["topology"]["version"] == "graph-health-v1"
    assert "degree is not evidence/truth" in extended["topology"]["note"]


def test_thresholds_reject_non_positive_values() -> None:
    for kwargs in (
        {"hub_total_degree": 0},
        {"fan_out_degree": 0},
        {"small_component_max_nodes": 0},
    ):
        try:
            GraphHealthThresholds(**kwargs)
        except ValueError:
            pass
        else:  # pragma: no cover - assertion branch
            raise AssertionError(f"expected ValueError for {kwargs}")
