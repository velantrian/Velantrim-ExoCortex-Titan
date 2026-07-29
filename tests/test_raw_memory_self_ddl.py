"""
Regression test for the #25 self-DDL-guard fix (Claude audit 2026-07-28).

RawMemoryStore assumed migrations/010_raw_memory.sql had already created
l0_raw_memory/raw_derivation_chain — every other stateful class in this
codebase that owns its own tables (ProvenanceChain._init_db,
AuditChain._ensure_schema) creates them idempotently on construction
instead. Without that, constructing RawMemoryStore against a bare
connection (only `facts` present, no migration ever run) crashed with
"no such table: l0_raw_memory" on the very first call.
"""
from __future__ import annotations

import sqlite3

from core.raw_memory import RawMemoryStore


def _bare_conn():
    """A connection with ONLY `facts` present — no migration 010 ever run."""
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript("""
        CREATE TABLE facts (
            fact_id TEXT PRIMARY KEY,
            claim TEXT,
            epistemic_state TEXT DEFAULT 'Observed',
            confidence REAL DEFAULT 0.8,
            derived_from TEXT
        );
    """)
    return conn


def test_constructing_against_a_bare_db_self_heals_its_own_tables():
    conn = _bare_conn()
    store = RawMemoryStore(conn)  # must not raise

    cols = {row[0] for row in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()}
    assert "l0_raw_memory" in cols
    assert "raw_derivation_chain" in cols


def test_store_and_link_fact_work_end_to_end_on_a_bare_db():
    conn = _bare_conn()
    conn.execute(
        "INSERT INTO facts (fact_id, claim) VALUES (?, ?)",
        ("f1", "the forest has trees"),
    )
    conn.commit()

    store = RawMemoryStore(conn)
    raw_id = store.store("The forest has trees. Birds nest there.", source="doc.pdf")
    store.link_fact(raw_id, "f1")

    raw = store.get_raw_for_fact("f1")
    assert raw is not None
    assert raw.raw_id == raw_id
    assert "Birds nest" in raw.original_text


def test_immutability_triggers_are_self_healed_too():
    """The self-heal DDL must include the same UPDATE/DELETE guards
    migration 010 defines, not just the bare tables."""
    conn = _bare_conn()
    store = RawMemoryStore(conn)
    raw_id = store.store("original text", source="doc")

    import pytest
    with pytest.raises(sqlite3.IntegrityError, match="immutable"):
        conn.execute(
            "UPDATE l0_raw_memory SET original_text = 'tampered' WHERE raw_id = ?",
            (raw_id,),
        )
