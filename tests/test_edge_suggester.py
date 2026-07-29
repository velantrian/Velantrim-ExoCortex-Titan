"""EdgeSuggester HITL: scan не пишет в relations; approve — hypothetical."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from core.dual_process import DualProcessError, slow_path
from core.edge_suggester import EdgeSuggester, reset_edge_suggester

REPO = Path(__file__).resolve().parents[1]


def _run_apply(db_path: str) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(REPO / "scripts" / "apply_migrations.py"),
            "--db",
            db_path,
            "--no-backup",
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO),
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout


@pytest.fixture
def store(tmp_path, monkeypatch):
    from core import memory

    reset_edge_suggester()
    db_path = str(tmp_path / "edges.db")
    bootstrap = memory.SQLiteGraphStore(db_path)
    bootstrap.get_fact("__bootstrap__")
    bootstrap.close()
    _run_apply(db_path)

    fresh = memory.make_store(db_path)
    monkeypatch.setattr(memory, "_GLOBAL_STORE", fresh)
    monkeypatch.setattr(memory, "_L0", fresh._l0)
    monkeypatch.setattr(memory, "_DDL_INITIALIZED", fresh._ddl_initialized_paths)
    monkeypatch.setattr(memory, "SQLITE_PATH", db_path)
    yield fresh
    fresh.close()
    reset_edge_suggester()


def _fact(fid: str, claim: str, domain: str = "science") -> dict:
    return {
        "fact_id": fid,
        "claim": claim,
        "source": "test",
        "confidence": 0.9,
        "epistemic_state": "Observed",
        "metadata": {"domain": domain},
    }


def test_scan_requires_slow_path(store, tmp_path):
    suggester = EdgeSuggester(str(tmp_path / "edges.db"))
    facts = [
        _fact("f1", "quantum memory consolidation protocol alpha"),
        _fact("f2", "quantum memory consolidation protocol beta"),
    ]
    with pytest.raises(DualProcessError):
        suggester.scan(facts)


def test_scan_writes_suggestions_not_relations(store):
    from core.memory import SQLITE_PATH, store_fact

    store_fact(_fact("f1", "quantum memory consolidation protocol alpha"))
    store_fact(_fact("f2", "quantum memory consolidation protocol beta"))
    suggester = EdgeSuggester(SQLITE_PATH)

    with slow_path():
        created = suggester.scan(
            [
                store.get_fact("f1"),
                store.get_fact("f2"),
            ],
            min_shared_tokens=2,
            min_score=0.2,
        )

    assert len(created) >= 1
    assert created[0]["status"] == "pending"

    import sqlite3

    conn = sqlite3.connect(SQLITE_PATH)
    n_rel = conn.execute("SELECT COUNT(*) FROM relations").fetchone()[0]
    n_sugg = conn.execute(
        "SELECT COUNT(*) FROM suggested_edges WHERE status='pending'"
    ).fetchone()[0]
    conn.close()
    assert n_rel == 0
    assert n_sugg >= 1


def test_approve_creates_hypothetical_relation(store):
    from core.memory import SQLITE_PATH, store_fact

    store_fact(_fact("f1", "neural plasticity memory encoding pathway"))
    store_fact(_fact("f2", "neural plasticity memory encoding circuit"))
    suggester = EdgeSuggester(SQLITE_PATH)
    with slow_path():
        created = suggester.scan(
            [store.get_fact("f1"), store.get_fact("f2")],
            min_shared_tokens=2,
            min_score=0.2,
        )
    sid = created[0]["suggestion_id"]
    result = suggester.approve(sid, by="tester", write_relation=True)
    assert result["status"] == "approved"
    assert result["relation_id"]

    import sqlite3

    conn = sqlite3.connect(SQLITE_PATH)
    row = conn.execute(
        "SELECT knowledge_status, truth_status, review_state, relation_type "
        "FROM relations WHERE relation_id = ?",
        (result["relation_id"],),
    ).fetchone()
    conn.close()
    assert row is not None
    assert row[0] == "hypothetical"
    assert row[1] == "hypothesis"
    assert row[2] == "pending"
    assert row[3] == "analogous_to"


def test_approve_of_duplicate_pending_suggestion_does_not_leave_phantom_relation_id(store):
    """M6 (Claude audit 2026-07-28): two pending suggested_edges rows for
    the same (from, to, type) pair — e.g. created by a race between two
    concurrent scan() calls — must not let a second approve() report a
    relation_id that was never actually written. add_relation() uses
    INSERT OR IGNORE against the relations UNIQUE constraint, so the second
    approve() used to generate a fresh uuid, report it as the relation_id,
    and silently no-op the insert — leaving suggested_edges pointing at a
    row that doesn't exist in relations."""
    import sqlite3

    from core.memory import SQLITE_PATH, store_fact

    store_fact(_fact("f1", "neural plasticity memory encoding pathway"))
    store_fact(_fact("f2", "neural plasticity memory encoding circuit"))
    suggester = EdgeSuggester(SQLITE_PATH)

    # Simulate the race directly: two pending rows for the identical pair,
    # as two concurrent scan() calls (each blind to the other's in-flight
    # insert) would produce — scan() itself de-dupes against a single
    # snapshot, so this can't be reproduced through scan() alone.
    conn = sqlite3.connect(SQLITE_PATH)
    conn.execute(
        "INSERT INTO suggested_edges "
        "(suggestion_id, from_fact_id, to_fact_id, relation_type, score, status, created_at) "
        "VALUES ('dup1', 'f1', 'f2', 'analogous_to', 0.9, 'pending', datetime('now'))"
    )
    conn.execute(
        "INSERT INTO suggested_edges "
        "(suggestion_id, from_fact_id, to_fact_id, relation_type, score, status, created_at) "
        "VALUES ('dup2', 'f1', 'f2', 'analogous_to', 0.9, 'pending', datetime('now'))"
    )
    conn.commit()
    conn.close()

    r1 = suggester.approve("dup1", by="tester")
    r2 = suggester.approve("dup2", by="tester")

    assert r1["relation_id"] and r2["relation_id"]

    conn = sqlite3.connect(SQLITE_PATH)
    real_ids = {
        row[0] for row in conn.execute(
            "SELECT relation_id FROM relations WHERE from_fact_id='f1' AND to_fact_id='f2'"
        ).fetchall()
    }
    suggested_ids = {
        row[0] for row in conn.execute(
            "SELECT relation_id FROM suggested_edges WHERE suggestion_id IN ('dup1', 'dup2')"
        ).fetchall()
    }
    conn.close()

    assert real_ids, "no relation row was ever written"
    assert suggested_ids <= real_ids, (
        f"suggested_edges references a relation_id that doesn't exist in "
        f"relations: {suggested_ids - real_ids}"
    )
    # Both approvals must converge on the SAME real relation, not two
    # different (one phantom) ids.
    assert r1["relation_id"] == r2["relation_id"]


def test_reject_keeps_relations_empty(store):
    from core.memory import SQLITE_PATH, store_fact

    store_fact(_fact("f1", "synaptic weight update rule gamma"))
    store_fact(_fact("f2", "synaptic weight update rule delta"))
    suggester = EdgeSuggester(SQLITE_PATH)
    with slow_path():
        created = suggester.scan(
            [store.get_fact("f1"), store.get_fact("f2")],
            min_shared_tokens=2,
            min_score=0.2,
        )
    sid = created[0]["suggestion_id"]
    out = suggester.reject(sid, by="tester")
    assert out["status"] == "rejected"

    import sqlite3

    conn = sqlite3.connect(SQLITE_PATH)
    n_rel = conn.execute("SELECT COUNT(*) FROM relations").fetchone()[0]
    conn.close()
    assert n_rel == 0
