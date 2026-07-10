"""
Confirmed issues #3 and #4 (core/tool_handlers.py):

  #3 propose_hypothesis must insert as Observed, then transition to
     Hypothesized — store_fact()'s I50 invariant rejects any new fact
     inserted directly as a non-Observed epistemic_state.
  #4 get_living_context must return None (not raise) when the
     fact_living_context table is absent (unmigrated store).

NOTE: some other tests in this suite (e.g. test_server_integration.py,
test_memory_ops.py) purge `core.*` entries from sys.modules and reimport
them, which can leave a different core.memory module object canonical for
the rest of the run than whatever was current at this file's collection
time. Production code that does a fresh `import core.memory` at CALL time
(e.g. core.truth_maintenance.supersede()) always sees whatever's currently
canonical — so these tests fetch core.memory the same way (inside each
fixture/test body, via _memory()) rather than relying on a module-level
`from core import memory` bound once at collection time.
"""
from __future__ import annotations

import sqlite3
import uuid
from pathlib import Path

import pytest

from core.living_context import LivingContextStore
from core.memory import SQLiteGraphStore


def _memory():
    import core.memory as m
    return m


def _handlers():
    from core import tool_handlers as h
    return h


@pytest.fixture(autouse=True)
def isolated_db(monkeypatch, tmp_path):
    """Same isolation pattern as tests/test_esm.py — swap _GLOBAL_STORE for a
    fresh per-test SQLite file so these tests don't depend on (or corrupt)
    whatever the repo's checked-in data/velantrim.db currently contains.

    core/tool_handlers.py binds `memory_api = core.memory` once, at whatever
    time core.tool_handlers was last (re)imported — if some other test's
    sys.modules purge reimported core.memory more recently than
    core.tool_handlers, that binding can silently diverge from
    sys.modules["core.memory"]. Patch both references so every call path
    (tool_handlers' module-level memory_api, and truth_maintenance.supersede()'s
    fresh per-call `import core.memory`) sees the same isolated store."""
    memory = _memory()
    fresh = memory.make_store(str(tmp_path / "test.db"))
    targets = {memory, getattr(_handlers(), "memory_api", memory)}
    for target in targets:
        monkeypatch.setattr(target, "_GLOBAL_STORE", fresh)
        monkeypatch.setattr(target, "_L0", fresh._l0)
        monkeypatch.setattr(target, "_DDL_INITIALIZED", fresh._ddl_initialized_paths)
        monkeypatch.setattr(target, "SQLITE_PATH", str(tmp_path / "test.db"))
    yield fresh
    fresh.close()


# ─── #3: propose_hypothesis ──────────────────────────────────────────────────

def test_propose_hypothesis_inserts_observed_then_promotes():
    result = _handlers().propose_hypothesis("test claim " + uuid.uuid4().hex)
    assert result["inserted"] is True
    assert result["epistemic_state"] == "Hypothesized"

    stored = _memory().get_fact(result["fact_id"])
    assert stored is not None
    assert stored["epistemic_state"] == "Hypothesized"


def test_propose_hypothesis_direct_hypothesized_insert_is_rejected():
    """Negative control: proves *why* the fix is needed — store_fact() itself
    still enforces I50 and rejects a new fact inserted directly as
    Hypothesized (the bug this handler used to trigger on every call)."""
    with pytest.raises(ValueError):
        _memory().store_fact({
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

    assert _handlers().get_living_context("anything.at.all") is None


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
    memory = _memory()
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

    result = _handlers().validate_fact(fact_id)

    assert result["validated"] is False
    assert result["epistemic_state"] is None
    stored = _memory().get_fact(fact_id)
    assert stored["epistemic_state"] == "Supported"


def test_promote_to_validated_bypasses_truth_gate_for_the_same_weak_fact():
    """Negative control: proves *why* the fix is needed — promote_to_validated()
    has no TruthGate check at all and would happily validate the exact same
    weak fact validate_fact() (correctly) rejects."""
    fact_id = f"weak.{uuid.uuid4().hex[:12]}"
    _store_weak_fact_at_supported(fact_id)

    ok = _memory().promote_to_validated(fact_id, by="test")

    assert ok is True
    stored = _memory().get_fact(fact_id)
    assert stored["epistemic_state"] == "Validated"


# ─── Codex finding: supersede_fact must go through the atomic CAS flow ──────

def _make_old_validated_fact(fact_id: str) -> None:
    memory = _memory()
    memory.store_fact({
        "fact_id": fact_id,
        "claim": "old claim",
        "source": "test",
        "confidence": 0.9,
        "metadata": {"evidence_refs": ["a", "b", "c", "d", "e"]},
    })
    memory.transition_esm(fact_id, "Hypothesized", by="test")
    memory.transition_esm(fact_id, "Supported", by="test")
    memory.transition_esm(fact_id, "Validated", by="test")


def _strong_new_fact(new_id: str) -> dict:
    """Passes PRECISION (min_confidence=0.9, min_evidence=5) — the mode
    truth_maintenance.supersede() evaluates candidates under."""
    return {
        "fact_id": new_id,
        "claim": "new claim",
        "source": "test",
        "confidence": 0.95,
        "metadata": {"evidence_refs": ["a", "b", "c", "d", "e"]},
    }


def _weak_new_fact(new_id: str) -> dict:
    """Fails PRECISION on both confidence and evidence."""
    return {
        "fact_id": new_id,
        "claim": "weak new claim",
        "source": "test",
        "confidence": 0.5,
        "metadata": {"evidence_refs": ["a"]},
    }


def test_supersede_fact_strong_replacement_succeeds():
    old_id = f"old.{uuid.uuid4().hex[:12]}"
    new_id = f"new.{uuid.uuid4().hex[:12]}"
    _make_old_validated_fact(old_id)

    result = _handlers().supersede_fact(old_id, _strong_new_fact(new_id))

    assert result["superseded"] is True
    assert result["new_fact_id"] == new_id
    memory = _memory()
    old = memory.get_fact(old_id)
    new = memory.get_fact(new_id)
    assert old["epistemic_state"] == "Deprecated"
    assert new is not None
    assert new["epistemic_state"] == "Validated"


def test_supersede_fact_weak_replacement_rejected_old_fact_unchanged():
    old_id = f"old.{uuid.uuid4().hex[:12]}"
    new_id = f"new.{uuid.uuid4().hex[:12]}"
    _make_old_validated_fact(old_id)

    result = _handlers().supersede_fact(old_id, _weak_new_fact(new_id))

    assert result["superseded"] is False
    assert result["new_fact_id"] == new_id
    memory = _memory()
    old = memory.get_fact(old_id)
    assert old["epistemic_state"] == "Validated"
    assert memory.get_fact(new_id) is None


def test_supersede_fact_rejects_malformed_new_fact_payload():
    old_id = f"old.{uuid.uuid4().hex[:12]}"
    _make_old_validated_fact(old_id)

    result = _handlers().supersede_fact(old_id, {"claim": "missing fact_id"})

    assert result["superseded"] is False
    assert result["error"] == "invalid_new_fact"
    old = _memory().get_fact(old_id)
    assert old["epistemic_state"] == "Validated"


def test_supersede_fact_new_id_collision_does_not_mutate_old_fact():
    old_id = f"old.{uuid.uuid4().hex[:12]}"
    colliding_id = f"existing.{uuid.uuid4().hex[:12]}"
    _make_old_validated_fact(old_id)
    _memory().store_fact({
        "fact_id": colliding_id,
        "claim": "already exists as its own fact",
        "source": "test",
        "confidence": 0.9,
    })

    result = _handlers().supersede_fact(old_id, _strong_new_fact(colliding_id))

    assert result["superseded"] is False
    old = _memory().get_fact(old_id)
    assert old["epistemic_state"] == "Validated"


def test_supersede_fact_old_transition_esm_bypass_is_no_longer_used():
    """Negative control: proves *why* the fix is needed — the previous
    version transitioned old_fact_id to Deprecated directly and never
    touched new_fact_id at all, so it "succeeded" even for a replacement
    that never existed. Direct transition_esm() still allows this — the
    fix must not rely on it for supersede_fact."""
    old_id = f"old.{uuid.uuid4().hex[:12]}"
    _make_old_validated_fact(old_id)

    memory = _memory()
    ok = memory.transition_esm(old_id, "Deprecated", by="test")

    assert ok is True
    assert memory.get_fact("fact.that.was.never.created") is None


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
    ctx = _handlers().get_living_context("demo.fact")
    assert ctx is not None
    assert ctx["where"] == ["a place"]
