"""Derived causal snapshots must never become accepted local truth by metadata alone.

Issue #286 / PR #287. Neo4j/external graph persistence is a downstream copy, not an
authority token. Importing a snapshot therefore re-enters local admission as an inferred
hypothesis even when the derived row carries stale/previous `validated/approved` labels.
"""
from __future__ import annotations

import sqlite3

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
        [("a", "A"), ("b", "B")],
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


def test_derived_snapshot_cannot_replay_validated_approved_labels():
    conn = _db()
    graph = CausalGraph(conn)

    created = graph.import_snapshots([
        {
            "relation_id": "remote_rel_1",
            "from_fact_id": "a",
            "to_fact_id": "b",
            "relation_type": "causes",
            "confidence": 0.95,
            "knowledge_status": "known",
            "inference_source": "manual",
            "truth_status": "validated",
            "review_state": "approved",
            "metadata": {"derived_store": "neo4j"},
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

    # Derived persistence is evidence/input, not an authority grant.
    assert row == ("inferred", "atlas_sync", "hypothesis", "pending")
    assert graph.get_relations_from("a", relation_type="causes") == []
