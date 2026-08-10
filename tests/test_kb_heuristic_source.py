"""Schema compatibility for generated World Skills heuristic relations.

The migration-level insert test prevents future drift between generated edge
metadata and the canonical SQLite CHECK constraint.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from core.curated_causal import build_ops_sequence_edges
from core.kb_graph_build import batch_insert_edges


def _ops_facts():
    filename = "ELECTRICAL_INSTALLATION_OPS.ru.md"
    return [
        {
            "fact_id": "electric.ops.step_one",
            "type": "METHOD",
            "metadata": {"knowledge_file": filename},
        },
        {
            "fact_id": "electric.ops.step_two",
            "type": "METHOD",
            "metadata": {"knowledge_file": filename},
        },
    ]


def test_generated_heuristic_uses_schema_valid_inference_source():
    edge = build_ops_sequence_edges(_ops_facts())[0]
    assert edge["inference_source"] == "autolinker"
    assert edge["edge_basis"] == "heuristic_ops_sequence"


def test_generated_heuristic_inserts_into_migrated_relations_schema():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE facts (fact_id TEXT PRIMARY KEY)")
    conn.executemany(
        "INSERT INTO facts VALUES (?)",
        [("electric.ops.step_one",), ("electric.ops.step_two",)],
    )
    migration = Path("migrations/008_add_relations.sql").read_text(encoding="utf-8")
    conn.executescript(migration)

    edge = build_ops_sequence_edges(_ops_facts())[0]
    result = batch_insert_edges(conn, [edge])

    assert result["inserted"] == 1
    forward = conn.execute(
        """
        SELECT inference_source, truth_status, review_state
        FROM relations
        WHERE from_fact_id = ? AND to_fact_id = ? AND relation_type = ?
        """,
        (edge["source_id"], edge["target_id"], edge["relation_type"]),
    ).fetchone()
    assert forward == ("autolinker", "hypothesis", "pending")
    assert conn.execute("SELECT COUNT(*) FROM relations").fetchone()[0] == 2
