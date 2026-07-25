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
