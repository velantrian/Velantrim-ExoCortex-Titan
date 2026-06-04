"""
Regression tests for the batch split-brain fix (audit finding C2).

store_facts_batch previously wrote the L0 cache INSIDE the per-fact loop, BEFORE
the single L1 transaction. If the L1 `executemany` failed and rolled back, the
facts were already in L0 → reads returned phantom facts absent from the durable
store (split-brain), and they vanished on restart. The fix moves all L0 writes
to AFTER a successful L1 commit (parity with store_fact).
"""
import contextlib
import sqlite3

import pytest

from core.memory import SQLiteGraphStore


def _facts(prefix, n, conf=0.6):
    return [{"fact_id": f"{prefix}{i}", "claim": f"{prefix} claim {i}",
             "source": "test_src", "confidence": conf} for i in range(n)]


class _FailExecuteMany:
    """Proxy that delegates everything to a real sqlite3 connection EXCEPT
    executemany (read-only on the real object), which we force to fail — so the
    batch's L1 write rolls back while per-fact get_fact reads still work."""
    def __init__(self, conn):
        object.__setattr__(self, "_c", conn)

    def executemany(self, *a, **k):
        raise sqlite3.OperationalError("simulated disk-full during batch")

    def __getattr__(self, name):
        return getattr(self._c, name)

    def __setattr__(self, name, value):
        setattr(self._c, name, value)


def test_batch_rollback_keeps_l0_clean(tmp_path, monkeypatch):
    """If the L1 transaction fails, NO fact may remain in the L0 cache."""
    store = SQLiteGraphStore(str(tmp_path / "t.db"))
    facts = _facts("f", 5)

    orig_db = store._db

    @contextlib.contextmanager
    def boom_db():
        with orig_db() as conn:
            yield _FailExecuteMany(conn)      # only executemany fails → rollback

    monkeypatch.setattr(store, "_db", boom_db)
    with pytest.raises(sqlite3.OperationalError):
        store.store_facts_batch(facts)

    monkeypatch.setattr(store, "_db", orig_db)   # restore real DB for reads
    for f in facts:
        assert store._l0_get(f["fact_id"]) is None, "C2: L0 must not be poisoned on rollback"
        assert store.get_fact(f["fact_id"]) is None, "nothing should be persisted either"


def test_batch_success_populates_l0_and_persists_l1(tmp_path):
    """On success, facts live in L0 AND are durable in L1 (read via a fresh store)."""
    path = str(tmp_path / "t.db")
    store = SQLiteGraphStore(path)
    facts = _facts("g", 3)

    stats = store.store_facts_batch(facts)
    assert stats["stored"] == 3
    for f in facts:
        assert store._l0_get(f["fact_id"]) is not None   # L0 populated AFTER commit

    # fresh instance has an empty L0 → must read from durable L1
    store2 = SQLiteGraphStore(path)
    for f in facts:
        row = store2.get_fact(f["fact_id"])
        assert row is not None and row["claim"] == f["claim"]


def test_l0_lock_exists():
    """C1: the L0 cache is guarded by a lock for cross-thread safety."""
    store = SQLiteGraphStore(":memory:")
    assert hasattr(store, "_l0_lock")
    # lock is reentrant so nested store calls under the lock don't deadlock
    with store._l0_lock:
        with store._l0_lock:
            store._l0_put("x", {"fact_id": "x", "claim": "c"})
    assert store._l0_get("x") is not None
