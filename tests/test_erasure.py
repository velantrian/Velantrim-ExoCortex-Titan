"""GDPR Art. 17 erasure — legacy core.erasure shim, delegating to
core.erasure_coordinator (see tests/test_erasure_coordinator.py for the
coordinator's own job/step/resumability/residual test suite).
"""
import pytest

from core import memory
from core.memory import make_store, store_fact, get_fact
from core import erasure


@pytest.fixture
def store(tmp_path, monkeypatch):
    """Isolated SQLite store per test (Titan has no autouse isolated-db fixture).

    erasure.erase_fact() delegates to core.erasure_coordinator.get_coordinator(),
    which (deliberately, see erasure_coordinator.py) builds a fresh
    ErasureCoordinator from the current `memory._GLOBAL_STORE` on every call
    rather than caching one — so patching `_GLOBAL_STORE` here is all that's
    needed for facts-layer isolation. The embeddings/ngram side of that fresh
    coordinator still defaults to bare EmbeddingStore()/NGramIndex(); those
    are redirected away from the real ./data/*.db files for the whole test
    session by tests/conftest.py (SQLITE_GRAPH_PATH / VELANTRIM_NGRAM_DB).
    """
    st = make_store(str(tmp_path / "erase.db"))
    monkeypatch.setattr(memory, "_GLOBAL_STORE", st)
    monkeypatch.setattr(memory, "_L0", st._l0)
    monkeypatch.setattr(memory, "_DDL_INITIALIZED", st._ddl_initialized_paths)
    return st


def _fact(fid, claim="user contact is a@b.com"):
    return {"fact_id": fid, "claim": claim, "source": "test", "confidence": 0.9}


def test_erase_removes_fact_and_writes_tombstone(store):
    store_fact(_fact("f1"))
    assert get_fact("f1") is not None

    receipt = erasure.erase_fact("f1", reason="dsr", actor="tester")

    assert receipt["erased_now"] is True
    assert get_fact("f1") is None
    assert erasure.is_erased("f1") is True
    assert receipt["content_hash"].startswith("sha256:")
    # The Art. 30 log records the erasure, content-free (hash, not the claim).
    log = erasure.erasure_log()
    entry = next(t for t in log if t["fact_id"] == "f1")
    assert entry["reason"] == "dsr" and entry["actor"] == "tester"
    assert "a@b.com" not in (entry["content_hash"] or "")


def test_erase_is_idempotent(store):
    store_fact(_fact("f2"))
    erasure.erase_fact("f2")
    again = erasure.erase_fact("f2")
    assert again["erased_now"] is False  # already gone
    # Tombstone is not duplicated (first erasure wins).
    assert sum(1 for t in erasure.erasure_log() if t["fact_id"] == "f2") == 1


def test_erase_cascades_to_relations(store):
    store_fact(_fact("a"))
    store_fact(_fact("b"))
    store._release_stray_locks()  # commit stray pool txns before a manual write
    with store._db() as conn:
        # `relations` comes from migration 008; create it here so the isolated
        # store (which has no migrations applied) can exercise relation cleanup.
        conn.execute(
            "CREATE TABLE IF NOT EXISTS relations ("
            "relation_id TEXT PRIMARY KEY, from_fact_id TEXT NOT NULL, "
            "to_fact_id TEXT NOT NULL, relation_type TEXT NOT NULL)")
        conn.execute(
            "INSERT INTO relations (relation_id, from_fact_id, to_fact_id, relation_type) "
            "VALUES (?,?,?,?)", ("r1", "a", "b", "causes"))
    erasure.erase_fact("a")
    with store._db() as conn:
        remaining = conn.execute(
            "SELECT COUNT(*) FROM relations WHERE from_fact_id='a' OR to_fact_id='a'"
        ).fetchone()[0]
    assert remaining == 0


def test_erase_removes_from_fts_index(store):
    store_fact(_fact("f_fts", claim="quantum entanglement links particles"))
    store._release_stray_locks()  # commit store_fact's pending FTS write
    with store._db() as conn:
        before = conn.execute(
            "SELECT COUNT(*) FROM facts_fts WHERE fact_id='f_fts'").fetchone()[0]
    erasure.erase_fact("f_fts")
    with store._db() as conn:
        after = conn.execute(
            "SELECT COUNT(*) FROM facts_fts WHERE fact_id='f_fts'").fetchone()[0]
    assert before >= 1 and after == 0


def test_ring_zero_not_erasable(store):
    with pytest.raises(memory.ImmutableStateError):
        erasure.erase_fact("RING_ZERO")
    # No tombstone written for a refused erasure.
    assert erasure.is_erased("RING_ZERO") is False


def test_erase_fact_is_deprecated_and_delegates_to_coordinator(store):
    store_fact(_fact("f_dep"))

    with pytest.deprecated_call():
        receipt = erasure.erase_fact("f_dep")

    # The shim narrows the coordinator's full job report — but it's the
    # SAME report, not a re-implementation: outcome/residual carry through.
    assert receipt["outcome"] == "COMPLETE"
    assert receipt["residual"] == "none"
    assert receipt["erased_now"] is True
