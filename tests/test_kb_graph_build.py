import json
import sqlite3

from core.kb_graph_build import batch_insert_edges, delete_kb_generated_edges


def _relations_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.execute("""
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
            metadata TEXT,
            UNIQUE (from_fact_id, to_fact_id, relation_type, inference_source)
        )
    """)
    return conn


def test_delete_kb_generated_edges_keeps_manual_relations():
    conn = _relations_db()
    conn.executemany(
        "INSERT INTO relations (relation_id, metadata, inference_source) VALUES (?, ?, ?)",
        [
            ("manual", "{}", "manual"),
            ("generated", '{"kb_build": true}', "autolinker"),
        ],
    )

    assert delete_kb_generated_edges(conn) == 1
    remaining = conn.execute("SELECT relation_id FROM relations").fetchall()
    assert remaining == [("manual",)]


def test_delete_kb_generated_edges_initializes_fresh_relations_table():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE facts (fact_id TEXT PRIMARY KEY)")
    assert delete_kb_generated_edges(conn) == 0
    assert conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='relations'"
    ).fetchone() == ("relations",)


def test_inverse_edge_preserves_edge_basis():
    conn = _relations_db()
    result = batch_insert_edges(conn, [{
        "source_id": "source.fact",
        "target_id": "target.fact",
        "relation_type": "enables",
        "confidence": 0.9,
        "knowledge_status": "inferred",
        "inference_source": "autolinker",
        "edge_basis": "semantic_similarity",
    }])
    assert result["inserted"] == 1
    metadata = [json.loads(row[0]) for row in conn.execute("SELECT metadata FROM relations")]
    assert len(metadata) == 2
    assert all(meta["edge_basis"] == "semantic_similarity" for meta in metadata)
