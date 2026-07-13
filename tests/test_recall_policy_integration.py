"""
🧪 tests/test_recall_policy_integration.py — Storage-layer integration tests
for Recall Policy (P0-1 Fix).

Проверяет RecallPolicy против настоящего SQLiteGraphStore:
- legal ESM transitions (через store.transition_esm(), не прямой update_state
  с произвольным целевым состоянием);
- реальный store.set_restricted(True) / set_restricted(False);
- явное разделение raw/admin (store.get_all_facts()) от recall-policy view;
- malformed/edge-case данные, персистентные через реальный store.

FastAPI/server-layer тесты (реальные /chat, /chat/stream, console fallback,
BranchManager corpus) — в tests/test_recall_policy_server.py, не здесь.
"""

import os
import tempfile

import pytest

from core.memory import SQLiteGraphStore
from core.recall_policy import filter_facts_for_recall, get_facts_for_recall


# ─── Fixtures ───────────────────────────────────────────────────────────────

@pytest.fixture
def temp_db_path():
    """Создать временный путь для БД."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield os.path.join(tmpdir, "test_recall.db")


@pytest.fixture
def sqlite_store(temp_db_path):
    """Создать SQLiteGraphStore для тестов, закрыть соединение после теста."""
    store = SQLiteGraphStore(db_path=temp_db_path, l0_cap=10)
    yield store
    store.close()


def _store(store: SQLiteGraphStore, fact_id: str, claim: str, **overrides) -> None:
    """store_fact() takes ONE dict argument and returns bool (new-insert flag),
    not the fact_id — the fact_id must be supplied by the caller."""
    fact = {
        "fact_id": fact_id,
        "claim": claim,
        "source": "test",
        "confidence": 0.9,
        "metadata": {},
    }
    fact.update(overrides)
    store.store_fact(fact)


def _to_deprecated(store: SQLiteGraphStore, fact_id: str) -> None:
    """Legal ESM chain: Observed -> Hypothesized -> Deprecated."""
    assert store.transition_esm(fact_id, "Hypothesized") is True
    assert store.transition_esm(fact_id, "Deprecated") is True


def _to_collapsed(store: SQLiteGraphStore, fact_id: str) -> None:
    """Legal ESM chain: Observed -> Hypothesized -> Deprecated -> Collapsed."""
    _to_deprecated(store, fact_id)
    assert store.transition_esm(fact_id, "Collapsed") is True


# ─── SQLiteGraphStore Integration Tests ─────────────────────────────────────

class TestRecallPolicyWithSQLiteGraphStore:
    def test_filter_facts_with_sqlite_store(self, sqlite_store):
        """restricted/Collapsed факты, полученные через реальный store, отфильтрованы."""
        _store(sqlite_store, "valid_fact", "Valid test fact", metadata={"domain": "test"})
        _store(sqlite_store, "restricted_fact", "Restricted test fact", metadata={"domain": "test"})
        _store(sqlite_store, "collapsed_fact", "Collapsed test fact", metadata={"domain": "test"})

        assert sqlite_store.set_restricted("restricted_fact", True) is True
        _to_collapsed(sqlite_store, "collapsed_fact")

        all_facts = sqlite_store.get_all_facts()
        filtered = filter_facts_for_recall(all_facts)

        fact_ids = [f["fact_id"] for f in filtered]
        assert "valid_fact" in fact_ids
        assert "restricted_fact" not in fact_ids
        assert "collapsed_fact" not in fact_ids
        assert len(filtered) == 1

    def test_get_facts_for_recall_with_sqlite_store(self, sqlite_store):
        """get_facts_for_recall() с реальным хранилищем + реальным set_restricted()."""
        _store(sqlite_store, "valid_fact", "Valid fact")
        _store(sqlite_store, "restricted_fact", "Restricted fact")
        assert sqlite_store.set_restricted("restricted_fact", True) is True

        result = get_facts_for_recall(sqlite_store.get_all_facts)

        assert len(result) == 1
        assert result[0]["claim"] == "Valid fact"

    def test_recall_policy_with_erasure_status(self, sqlite_store):
        """Фильтрация по erasure_status (metadata) через реальный store."""
        _store(sqlite_store, "active_fact", "Active fact", metadata={"erasure_status": "active"})
        _store(sqlite_store, "erased_fact", "Erased fact", metadata={"erasure_status": "erased"})

        filtered = filter_facts_for_recall(sqlite_store.get_all_facts())

        assert len(filtered) == 1
        assert filtered[0]["fact_id"] == "active_fact"

    def test_recall_policy_with_epistemic_states(self, sqlite_store):
        """Deprecated/Collapsed через ЗАКОННЫЕ ESM-переходы исключены из recall."""
        _store(sqlite_store, "validated_fact", "Validated fact")
        _store(sqlite_store, "deprecated_fact", "Deprecated fact")
        _store(sqlite_store, "collapsed_fact", "Collapsed fact")

        _to_deprecated(sqlite_store, "deprecated_fact")
        _to_collapsed(sqlite_store, "collapsed_fact")

        filtered = filter_facts_for_recall(sqlite_store.get_all_facts())

        assert len(filtered) == 1
        assert filtered[0]["fact_id"] == "validated_fact"

    def test_illegal_esm_transition_raises(self, sqlite_store):
        """Observed -> Deprecated (пропуская Hypothesized) недопустимо и должно бросать."""
        _store(sqlite_store, "f1", "some claim")
        with pytest.raises(ValueError):
            sqlite_store.transition_esm("f1", "Deprecated")
        with pytest.raises(ValueError):
            sqlite_store.transition_esm("f1", "Collapsed")


# ─── Raw/admin separation ────────────────────────────────────────────────────

class TestRawAdminSeparation:
    def test_set_restricted_true_then_false_round_trip(self, sqlite_store):
        """set_restricted(True) removes from recall but not from raw storage;
        set_restricted(False) reverses it — the fact reappears in recall."""
        _store(sqlite_store, "toggle_fact", "Toggle fact")

        assert sqlite_store.set_restricted("toggle_fact", True) is True

        raw = sqlite_store.get_all_facts()
        assert any(f["fact_id"] == "toggle_fact" for f in raw), (
            "raw get_all_facts() must still see a restricted fact (admin/raw contract)"
        )

        recall_view = filter_facts_for_recall(sqlite_store.get_all_facts())
        assert not any(f["fact_id"] == "toggle_fact" for f in recall_view), (
            "policy-aware recall must NOT see a restricted fact"
        )

        assert sqlite_store.set_restricted("toggle_fact", False) is True

        recall_view_after = filter_facts_for_recall(sqlite_store.get_all_facts())
        assert any(f["fact_id"] == "toggle_fact" for f in recall_view_after), (
            "un-restricting must make the fact recall-visible again"
        )

    def test_set_restricted_unknown_fact_returns_false(self, sqlite_store):
        assert sqlite_store.set_restricted("does_not_exist", True) is False


# ─── Edge Cases Integration Tests ───────────────────────────────────────────

class TestRecallPolicyEdgeCasesIntegration:
    def test_empty_store(self, sqlite_store):
        assert filter_facts_for_recall(sqlite_store.get_all_facts()) == []

    def test_all_facts_restricted(self, sqlite_store):
        _store(sqlite_store, "r1", "Restricted 1")
        _store(sqlite_store, "r2", "Restricted 2")
        assert sqlite_store.set_restricted("r1", True) is True
        assert sqlite_store.set_restricted("r2", True) is True

        filtered = filter_facts_for_recall(sqlite_store.get_all_facts())
        assert filtered == []

    def test_normal_fact_roundtrips_through_real_store(self, sqlite_store):
        """A newly-stored fact (Observed, no restriction/erasure) is recall-visible."""
        _store(sqlite_store, "normal_fact", "Normal fact")

        filtered = filter_facts_for_recall(sqlite_store.get_all_facts())
        assert len(filtered) == 1
        assert filtered[0]["fact_id"] == "normal_fact"
