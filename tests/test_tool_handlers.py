"""
Confirmed issues #3 and #4 (core/tool_handlers.py):

  #3 propose_hypothesis must insert as Observed, then transition to
     Hypothesized — store_fact()'s I50 invariant rejects any new fact
     inserted directly as a non-Observed epistemic_state.
  #4 get_living_context must return None (not raise) when the
     fact_living_context table is absent (unmigrated store).
"""
from __future__ import annotations

import sqlite3
import uuid
from pathlib import Path

import pytest

from core import memory
from core import tool_handlers
from core.living_context import LivingContextStore
from core.memory import SQLiteGraphStore


@pytest.fixture(autouse=True)
def isolated_db(monkeypatch, tmp_path):
    """Same isolation pattern as tests/test_esm.py — swap _GLOBAL_STORE for a
    fresh per-test SQLite file so these tests don't depend on (or corrupt)
    whatever the repo's checked-in data/velantrim.db currently contains."""
    fresh = memory.make_store(str(tmp_path / "test.db"))
    monkeypatch.setattr(memory, "_GLOBAL_STORE", fresh)
    monkeypatch.setattr(memory, "_L0", fresh._l0)
    monkeypatch.setattr(memory, "_DDL_INITIALIZED", fresh._ddl_initialized_paths)
    monkeypatch.setattr(memory, "SQLITE_PATH", str(tmp_path / "test.db"))
    yield fresh
    fresh.close()


# ─── #3: propose_hypothesis ──────────────────────────────────────────────────

def test_propose_hypothesis_inserts_observed_then_promotes():
    result = tool_handlers.propose_hypothesis("test claim " + uuid.uuid4().hex)
    assert result["inserted"] is True
    assert result["epistemic_state"] == "Hypothesized"

    stored = memory.get_fact(result["fact_id"])
    assert stored is not None
    assert stored["epistemic_state"] == "Hypothesized"


def test_propose_hypothesis_direct_hypothesized_insert_is_rejected():
    """Negative control: proves *why* the fix is needed — store_fact() itself
    still enforces I50 and rejects a new fact inserted directly as
    Hypothesized (the bug this handler used to trigger on every call)."""
    from core.memory import store_fact

    with pytest.raises(ValueError):
        store_fact({
            "fact_id": f"hyp.{uuid.uuid4().hex[:12]}",
            "claim": "direct hypothesized insert",
            "source": "test",
            "confidence": 0.5,
            "epistemic_state": "Hypothesized",
        })


# ─── #4: get_living_context ──────────────────────────────────────────────────

def test_get_living_context_returns_none_when_table_missing(tmp_path, monkeypatch):
    fresh_store = SQLiteGraphStore(str(tmp_path / "unmigrated.db"))
    monkeypatch.setattr("core.memory.get_store", lambda: fresh_store)

    assert tool_handlers.get_living_context("anything.at.all") is None


def test_living_context_store_raises_on_unmigrated_table_directly(tmp_path):
    """Negative control: confirms the underlying failure mode this handler
    guards against — LivingContextStore.get() raises OperationalError when
    fact_living_context hasn't been created by migrations/008_add_relations.sql."""
    conn = sqlite3.connect(":memory:")
    with pytest.raises(sqlite3.OperationalError):
        LivingContextStore(conn).get("anything.at.all")


# ─── Codex finding: validate_fact must go through TruthGate ─────────────────

def _store_weak_fact_at_supported(fact_id: str) -> None:
    """A fact with confidence/evidence too low to pass BALANCED TruthGate
    (min_confidence=0.7, min_evidence=2), promoted to Supported — the only
    state Validated is a legal ESM transition from."""
    memory.store_fact({
        "fact_id": fact_id,
        "claim": "a weak unverified claim",
        "source": "test",
        "confidence": 0.5,
    })
    memory.transition_esm(fact_id, "Hypothesized", by="test")
    memory.transition_esm(fact_id, "Supported", by="test")


def test_validate_fact_rejects_weak_fact_via_truth_gate():
    fact_id = f"weak.{uuid.uuid4().hex[:12]}"
    _store_weak_fact_at_supported(fact_id)

    result = tool_handlers.validate_fact(fact_id)

    assert result["validated"] is False
    assert result["epistemic_state"] is None
    stored = memory.get_fact(fact_id)
    assert stored["epistemic_state"] == "Supported"


def test_promote_to_validated_bypasses_truth_gate_for_the_same_weak_fact():
    """Negative control: proves *why* the fix is needed — promote_to_validated()
    has no TruthGate check at all and would happily validate the exact same
    weak fact validate_fact() (correctly) rejects."""
    fact_id = f"weak.{uuid.uuid4().hex[:12]}"
    _store_weak_fact_at_supported(fact_id)

    ok = memory.promote_to_validated(fact_id, by="test")

    assert ok is True
    stored = memory.get_fact(fact_id)
    assert stored["epistemic_state"] == "Validated"


def test_get_living_context_returns_context_when_present(tmp_path, monkeypatch):
    fresh_store = SQLiteGraphStore(str(tmp_path / "migrated.db"))
    fresh_store.store_fact({
        "fact_id": "demo.fact",
        "claim": "demo",
        "source": "test",
        "confidence": 0.9,
    })
    with fresh_store._db() as conn:
        migration = Path("migrations/008_add_relations.sql").read_text(encoding="utf-8")
        conn.executescript(migration)
        conn.execute(
            "INSERT INTO fact_living_context (fact_id, ctx_where) VALUES (?, ?)",
            ("demo.fact", '["a place"]'),
        )
        conn.commit()

    monkeypatch.setattr("core.memory.get_store", lambda: fresh_store)
    ctx = tool_handlers.get_living_context("demo.fact")
    assert ctx is not None
    assert ctx["where"] == ["a place"]
