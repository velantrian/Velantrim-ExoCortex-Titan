"""Authority-boundary regressions for issue #286 / PR #287."""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

import core.causal_graph as causal_graph_module
import core.pipeline as pipeline
from core.causal_graph import CausalGraph


def _db() -> sqlite3.Connection:
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
    conn.executemany(
        "INSERT INTO facts (fact_id, claim) VALUES (?, ?)",
        [("a", "A"), ("b", "B"), ("c", "C")],
    )
    conn.executescript(
        """
        CREATE TABLE relations (
            relation_id TEXT PRIMARY KEY,
            from_fact_id TEXT NOT NULL REFERENCES facts(fact_id) ON DELETE CASCADE,
            to_fact_id TEXT NOT NULL REFERENCES facts(fact_id) ON DELETE CASCADE,
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
            metadata TEXT,
            CHECK (from_fact_id != to_fact_id),
            UNIQUE (from_fact_id, to_fact_id, relation_type, inference_source)
        );
        """
    )
    conn.commit()
    return conn


def _event_count(conn: sqlite3.Connection) -> int:
    has_table = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='memory_events'"
    ).fetchone()
    if not has_table:
        return 0
    return int(conn.execute("SELECT COUNT(*) FROM memory_events").fetchone()[0])


def test_write_gate_denial_prevents_relation_and_audit(monkeypatch):
    conn = _db()
    graph = CausalGraph(conn)

    def deny() -> None:
        raise RuntimeError("writes disabled")

    monkeypatch.setattr(causal_graph_module, "ensure_writes_allowed", deny)

    with pytest.raises(RuntimeError, match="writes disabled"):
        graph.add_relation("a", "b", "causes")

    assert conn.execute("SELECT COUNT(*) FROM relations").fetchone()[0] == 0
    assert _event_count(conn) == 0


def test_snapshot_import_is_local_admission_and_defaults_pending():
    conn = _db()
    graph = CausalGraph(conn)

    created = graph.import_snapshots([
        {
            "from_fact_id": "a",
            "to_fact_id": "b",
            "relation_type": "causes",
            "confidence": 0.77,
        }
    ])

    assert created == 1
    row = conn.execute(
        """
        SELECT knowledge_status, inference_source, truth_status, review_state
        FROM relations
        WHERE from_fact_id='a' AND to_fact_id='b' AND relation_type='causes'
        """
    ).fetchone()
    assert row == ("inferred", "atlas_sync", "hypothesis", "pending")
    assert graph.get_relations_from("a", relation_type="causes") == []


def test_snapshot_import_propagates_write_gate_denial(monkeypatch):
    conn = _db()
    graph = CausalGraph(conn)

    def deny() -> None:
        raise RuntimeError("writes disabled")

    monkeypatch.setattr(causal_graph_module, "ensure_writes_allowed", deny)

    with pytest.raises(RuntimeError, match="writes disabled"):
        graph.import_snapshots([
            {
                "from_fact_id": "a",
                "to_fact_id": "b",
                "relation_type": "causes",
            }
        ])

    assert conn.execute("SELECT COUNT(*) FROM relations").fetchone()[0] == 0


def test_snapshot_import_propagates_audit_failure_and_rolls_back(monkeypatch):
    conn = _db()
    graph = CausalGraph(conn)

    def fail_audit(*args, **kwargs) -> None:
        raise RuntimeError("forced snapshot audit failure")

    monkeypatch.setattr(causal_graph_module, "append_relation_event", fail_audit)

    with pytest.raises(RuntimeError, match="forced snapshot audit failure"):
        graph.import_snapshots([
            {
                "from_fact_id": "a",
                "to_fact_id": "b",
                "relation_type": "causes",
            }
        ])

    assert conn.execute("SELECT COUNT(*) FROM relations").fetchone()[0] == 0


def test_snapshot_import_rejects_incomplete_rows_instead_of_reporting_zero():
    conn = _db()
    graph = CausalGraph(conn)

    with pytest.raises(ValueError, match="snapshot row requires"):
        graph.import_snapshots([{"from_fact_id": "a", "to_fact_id": "b"}])


def test_failed_audited_reset_detaches_closed_singleton(monkeypatch):
    conn = _db()
    graph = CausalGraph(conn)

    def fail_reset() -> int:
        raise RuntimeError("forced audited reset failure")

    monkeypatch.setattr(graph, "reset_relations", fail_reset)
    monkeypatch.setattr(pipeline, "_CAUSAL_GRAPH", graph)
    monkeypatch.setattr(pipeline, "_CAUSAL_GRAPH_DB_PATH", "stale.db")

    with pytest.raises(RuntimeError, match="forced audited reset failure"):
        pipeline.reset_causal_graph()

    assert pipeline._CAUSAL_GRAPH is None
    assert pipeline._CAUSAL_GRAPH_DB_PATH == ""
    with pytest.raises(sqlite3.ProgrammingError, match="closed database"):
        conn.execute("SELECT 1")


def test_pipeline_reset_has_no_raw_relation_delete_owner():
    source = Path("core/pipeline.py").read_text(encoding="utf-8")
    start = source.index("def reset_causal_graph()")
    end = source.index("\ndef _extract_conflicts", start)
    reset_source = source[start:end]

    assert "DELETE FROM relations" not in reset_source
    assert ".reset_relations()" in reset_source


def test_relation_store_is_not_reclassified_as_causal_canon():
    source = Path("core/relations.py").read_text(encoding="utf-8")
    causal_source = Path("core/causal_graph.py").read_text(encoding="utf-8")

    assert "fact_relations" in source
    assert "fact_relations" not in causal_source
    assert "class RelationStore" in source


def test_networkx_and_neo4j_surfaces_remain_non_authoritative():
    graph_lab = Path("core/graph_lab.py").read_text(encoding="utf-8")
    neo4j = Path("core/causal_persistence.py").read_text(encoding="utf-8")

    assert "FROM relations" in graph_lab
    assert "INSERT INTO relations" not in graph_lab
    assert "UPDATE relations" not in graph_lab
    assert "DELETE FROM relations" not in graph_lab

    # Neo4j remains derived persistence. A reverse load must pass through the
    # local CausalGraph admission API rather than mutating SQLite relations SQL.
    assert "get_causal_graph().import_snapshots" in neo4j
    assert "INSERT INTO relations" not in neo4j
    assert "DELETE FROM relations" not in neo4j
