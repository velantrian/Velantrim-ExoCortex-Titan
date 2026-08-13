"""Adversarial evidence for issue #286 / parent #50.

These tests use real SQLite transactions. They prove canonical causal relation mutation
and AuditChain evidence fail or commit together, while inferred proposals stay outside
approved reasoning until explicit acceptance.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

import core.causal_graph as causal_graph_module
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


def _audit_count(conn: sqlite3.Connection) -> int:
    row = conn.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='memory_events'"
    ).fetchone()
    if not row or row[0] == 0:
        return 0
    return int(conn.execute("SELECT COUNT(*) FROM memory_events").fetchone()[0])


def test_forward_inverse_and_audit_commit_atomically():
    conn = _db()
    graph = CausalGraph(conn)

    rid = graph.add_relation("a", "b", "causes", confidence=0.9)

    rows = conn.execute(
        "SELECT relation_id, relation_type FROM relations ORDER BY relation_type"
    ).fetchall()
    assert len(rows) == 2
    assert {row[1] for row in rows} == {"causes", "caused_by"}
    assert graph.get_relation(rid) is not None
    events = conn.execute(
        "SELECT event_type, chain_id FROM memory_events ORDER BY chain_id"
    ).fetchall()
    assert len(events) == 2
    assert all(row[0] == "relation_created" for row in events)
    assert all(row[1].startswith("causal-relation:rel_") for row in events)


def test_forced_audit_failure_rolls_back_forward_and_inverse(monkeypatch):
    conn = _db()
    graph = CausalGraph(conn)

    def fail_audit(*args, **kwargs):
        raise RuntimeError("forced relation audit failure")

    monkeypatch.setattr(causal_graph_module, "append_relation_event", fail_audit)
    with pytest.raises(RuntimeError, match="forced relation audit failure"):
        graph.add_relation("a", "b", "causes")

    assert conn.execute("SELECT COUNT(*) FROM relations").fetchone()[0] == 0
    assert _audit_count(conn) == 0


def test_duplicate_returns_durable_identity_without_false_audit():
    conn = _db()
    graph = CausalGraph(conn)

    rid1 = graph.add_relation("a", "b", "causes", inference_source="manual")
    first_events = _audit_count(conn)
    rid2 = graph.add_relation("a", "b", "causes", inference_source="manual")

    assert rid2 == rid1
    assert _audit_count(conn) == first_events
    assert conn.execute(
        "SELECT COUNT(*) FROM relations WHERE from_fact_id='a' AND to_fact_id='b' "
        "AND relation_type='causes' AND inference_source='manual'"
    ).fetchone()[0] == 1


def test_automatic_inference_is_pending_and_excluded_from_approved_reads():
    conn = _db()
    graph = CausalGraph(conn)

    rid = graph.add_relation(
        "a",
        "b",
        "causes",
        knowledge_status="inferred",
        inference_source="llm_extraction",
    )
    rel = graph.get_relation(rid)
    assert rel is not None
    assert rel.truth_status == "hypothesis"
    assert rel.review_state == "pending"
    assert graph.get_relations_from("a", relation_type="causes") == []
    pending = graph.get_relations_from(
        "a", relation_type="causes", only_approved=False
    )
    assert [row.relation_id for row in pending] == [rid]


def test_explicit_accepted_inference_can_be_approved():
    conn = _db()
    graph = CausalGraph(conn)

    rid = graph.add_relation(
        "a",
        "b",
        "causes",
        knowledge_status="inferred",
        inference_source="manual",
        truth_status="validated",
        review_state="approved",
    )

    rel = graph.get_relation(rid)
    assert rel is not None
    assert rel.truth_status == "validated"
    assert rel.review_state == "approved"
    assert [row.relation_id for row in graph.get_relations_from("a", "causes")] == [rid]


def test_remove_relation_and_inverse_share_audited_transaction():
    conn = _db()
    graph = CausalGraph(conn)
    rid = graph.add_relation("a", "b", "causes")
    before = _audit_count(conn)

    assert graph.remove_relation(rid) is True

    assert conn.execute("SELECT COUNT(*) FROM relations").fetchone()[0] == 0
    assert _audit_count(conn) == before + 2
    removed = conn.execute(
        "SELECT COUNT(*) FROM memory_events WHERE event_type='relation_removed'"
    ).fetchone()[0]
    assert removed == 2


def test_remove_uses_explicit_inverse_identity_with_null_source_duplicates():
    conn = _db()
    graph = CausalGraph(conn)
    conn.executemany(
        """
        INSERT INTO relations (
            relation_id, from_fact_id, to_fact_id, relation_type,
            confidence, knowledge_status, inference_source,
            truth_status, review_state, metadata
        ) VALUES (?, ?, ?, ?, 0.8, 'known', NULL, 'validated', 'approved', ?)
        """,
        [
            ("forward_1", "a", "b", "causes", None),
            ("forward_2", "a", "b", "causes", None),
            ("inverse_1", "b", "a", "caused_by", '{"inverse_of":"forward_1"}'),
            ("inverse_2", "b", "a", "caused_by", '{"inverse_of":"forward_2"}'),
        ],
    )
    conn.commit()

    assert graph.remove_relation("forward_1") is True

    remaining = {
        row[0] for row in conn.execute(
            "SELECT relation_id FROM relations ORDER BY relation_id"
        ).fetchall()
    }
    assert remaining == {"forward_2", "inverse_2"}


def test_remove_fails_closed_for_stale_forward_inverse_pointer():
    conn = _db()
    graph = CausalGraph(conn)
    conn.executemany(
        """
        INSERT INTO relations (
            relation_id, from_fact_id, to_fact_id, relation_type,
            confidence, knowledge_status, inference_source,
            truth_status, review_state, metadata
        ) VALUES (?, ?, ?, ?, 0.8, 'known', NULL, 'validated', 'approved', ?)
        """,
        [
            ("forward_1", "a", "b", "causes", '{"inverse_of":"inverse_2"}'),
            ("forward_2", "a", "b", "causes", None),
            ("inverse_1", "b", "a", "caused_by", '{"inverse_of":"forward_1"}'),
            ("inverse_2", "b", "a", "caused_by", '{"inverse_of":"forward_2"}'),
        ],
    )
    conn.commit()

    with pytest.raises(RuntimeError, match="inverse identity"):
        graph.remove_relation("forward_1")

    assert conn.execute("SELECT COUNT(*) FROM relations").fetchone()[0] == 4


def test_add_rejects_caller_owned_inverse_identity_metadata():
    conn = _db()
    graph = CausalGraph(conn)

    with pytest.raises(ValueError, match="inverse_of.*reserved"):
        graph.add_relation(
            "a",
            "b",
            "causes",
            metadata={"inverse_of": "caller-selected-row"},
        )

    assert conn.execute("SELECT COUNT(*) FROM relations").fetchone()[0] == 0


def test_remove_fails_closed_for_unlinked_null_source_duplicates():
    conn = _db()
    graph = CausalGraph(conn)
    conn.executemany(
        """
        INSERT INTO relations (
            relation_id, from_fact_id, to_fact_id, relation_type,
            confidence, knowledge_status, inference_source,
            truth_status, review_state
        ) VALUES (?, ?, ?, ?, 0.8, 'known', NULL, 'validated', 'approved')
        """,
        [
            ("forward_1", "a", "b", "causes"),
            ("forward_2", "a", "b", "causes"),
            ("inverse_1", "b", "a", "caused_by"),
            ("inverse_2", "b", "a", "caused_by"),
        ],
    )
    conn.commit()

    with pytest.raises(RuntimeError, match="ambiguous legacy inverse companions"):
        graph.remove_relation("forward_1")

    assert conn.execute("SELECT COUNT(*) FROM relations").fetchone()[0] == 4


def test_remove_audit_failure_rolls_back_delete(monkeypatch):
    conn = _db()
    graph = CausalGraph(conn)
    rid = graph.add_relation("a", "b", "causes")
    before_events = _audit_count(conn)

    def fail_audit(*args, **kwargs):
        raise RuntimeError("forced remove audit failure")

    monkeypatch.setattr(causal_graph_module, "append_relation_event", fail_audit)
    with pytest.raises(RuntimeError, match="forced remove audit failure"):
        graph.remove_relation(rid)

    assert conn.execute("SELECT COUNT(*) FROM relations").fetchone()[0] == 2
    assert _audit_count(conn) == before_events


def test_remove_miss_is_true_noop_without_false_audit():
    conn = _db()
    graph = CausalGraph(conn)
    before = _audit_count(conn)

    assert graph.remove_relation("rel_missing") is False

    assert conn.execute("SELECT COUNT(*) FROM relations").fetchone()[0] == 0
    assert _audit_count(conn) == before


def test_reset_relations_audits_every_removed_physical_row():
    conn = _db()
    graph = CausalGraph(conn)
    graph.add_relation("a", "b", "causes")
    graph.add_relation("b", "c", "enables")
    before_events = _audit_count(conn)
    before_rows = conn.execute("SELECT COUNT(*) FROM relations").fetchone()[0]

    removed = graph.reset_relations()

    assert removed == before_rows == 4
    assert conn.execute("SELECT COUNT(*) FROM relations").fetchone()[0] == 0
    assert _audit_count(conn) == before_events + before_rows


def test_kb_and_admin_surfaces_have_no_raw_relation_mutation_owner():
    kb = Path("core/kb_graph_build.py").read_text(encoding="utf-8")
    tools = Path("core/tool_handlers.py").read_text(encoding="utf-8")

    assert "INSERT OR IGNORE INTO relations" not in kb
    assert "DELETE FROM relations" not in kb
    assert "DELETE FROM relations" not in tools
    assert "add_relations_batch" in kb
    assert "reset_relations" in tools


def test_networkx_graph_lab_remains_read_only_projection():
    source = Path("core/graph_lab.py").read_text(encoding="utf-8")
    assert "FROM relations" in source
    assert "INSERT INTO relations" not in source
    assert "UPDATE relations" not in source
    assert "DELETE FROM relations" not in source
