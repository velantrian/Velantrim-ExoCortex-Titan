"""
PR-C1 — truthful write results, no phantom provenance/success (unit level).

This file covers the unit-level (no HTTP, no FastAPI TestClient) defects
described in the PR-C1 evidence report: phantom l0_fact_provenance from
link_raw_to_fact(), phantom fact_inbox promotion, and the legacy
store_fact() bool contract that the fix must not break.

HTTP-level coverage for the console auto-save and POST /facts false-success
paths lives in tests/test_server_integration.py instead of here — reusing
its existing `test_client` TestClient fixture rather than bootstrapping a
second, independent FastAPI TestClient fixture in this file, which caused
spurious cross-test failures when the two ran together across the full
suite (each TestClient boot is expensive; the two independent instances
appear to have tipped a shared resource — likely process memory/fd/thread-
pool pressure across ~2000 collected test items — enough to destabilize
unrelated tests elsewhere in the run, even though every test in this file
passed individually and in small combinations).

Test classes are marked in their docstrings as either:
  - RED today (demonstrate the bug; must go green after the PR-C1 fix), or
  - BASELINE (already correct today; pins the contract so the refactor in
    this PR cannot regress it).
"""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ─── Direct-store fixtures (no HTTP) ──────────────────────────────────────────

@pytest.fixture
def isolated_store(tmp_path, monkeypatch):
    """Fresh SQLiteGraphStore, isolated per test (mirrors test_write_gate.py)."""
    from core import memory

    fresh = memory.make_store(str(tmp_path / "wr.db"))
    monkeypatch.setattr(memory, "_GLOBAL_STORE", fresh)
    monkeypatch.setattr(memory, "_L0", fresh._l0)
    monkeypatch.setattr(memory, "_DDL_INITIALIZED", fresh._ddl_initialized_paths)
    monkeypatch.setattr(memory, "SQLITE_PATH", str(tmp_path / "wr.db"))
    yield fresh
    fresh.close()


def _provenance_row_exists(fact_id: str) -> bool:
    from core.memory import _GLOBAL_STORE

    with _GLOBAL_STORE._db() as conn:
        row = conn.execute(
            "SELECT 1 FROM l0_fact_provenance WHERE fact_id = ?", (fact_id,)
        ).fetchone()
    return row is not None


# ─── Item 5: link_raw_to_fact on a nonexistent fact_id (RED today) ────────────

class TestLinkRawToFactPhantomProvenance:
    """RED today: link_raw_to_fact() writes a provenance row (and can touch
    `facts`) even when fact_id does not exist in `facts` — nothing enforces
    the FK (PRAGMA foreign_keys is off for this connection), so this
    currently succeeds silently and creates a phantom row."""

    def test_nonexistent_fact_creates_no_provenance_row(self, isolated_store):
        from core.memory import link_raw_to_fact, store_raw_text

        raw_id = store_raw_text("orphan raw text for pr-c1 test", "test", "user_input")

        link_raw_to_fact(raw_id, "fact_does_not_exist_pr_c1")

        assert not _provenance_row_exists("fact_does_not_exist_pr_c1"), (
            "link_raw_to_fact must not create a provenance row pointing at a "
            "fact_id that does not exist in `facts`"
        )

    def test_success_case_still_links(self, isolated_store):
        """BASELINE (already correct today): linking a real raw_id to a real
        fact_id must keep working after the fix."""
        from core.memory import get_fact, link_raw_to_fact, store_fact, store_raw_text

        raw_id = store_raw_text("real raw text for pr-c1 test", "test", "user_input")
        store_fact({
            "fact_id": "fact_real_pr_c1",
            "claim": "a real fact for provenance linking",
            "source": "test",
            "confidence": 0.9,
        })
        link_raw_to_fact(raw_id, "fact_real_pr_c1")

        assert _provenance_row_exists("fact_real_pr_c1")
        fact = get_fact("fact_real_pr_c1")
        assert fact["derived_from"] == raw_id


# ─── Item 7: legacy store_fact() bool contract (BASELINE — already green) ────

class TestLegacyStoreFactBoolContract:
    """BASELINE: store_fact()'s existing bool contract must survive the
    PR-C1 refactor byte-for-byte:
      - True only for a genuine new INSERT
      - False for no-op-existing, for a real update of an existing fact,
        and for WriteGate rejection
      - ValueError / MemoryBudgetExceededError still raise
    """

    def test_true_for_new_insert(self, isolated_store):
        from core.memory import store_fact

        assert store_fact({
            "fact_id": "legacy_new_1", "claim": "x", "source": "test", "confidence": 0.5,
        }) is True

    def test_false_for_noop_existing(self, isolated_store):
        from core.memory import store_fact

        fact = {"fact_id": "legacy_noop_1", "claim": "x", "source": "test", "confidence": 0.5}
        assert store_fact(fact) is True
        assert store_fact(dict(fact)) is False  # identical re-post → no-op

    def test_false_for_real_update(self, isolated_store):
        from core.memory import store_fact

        assert store_fact({
            "fact_id": "legacy_upd_1", "claim": "original", "source": "test", "confidence": 0.5,
        }) is True
        assert store_fact({
            "fact_id": "legacy_upd_1", "claim": "original", "source": "test", "confidence": 0.9,
        }) is False  # confidence changed → real upsert, still legacy False

    def test_false_for_write_gate_rejection(self, isolated_store, monkeypatch):
        import core.write_gate as wg
        from core.memory import get_fact, store_fact

        monkeypatch.setattr(wg, "is_write_gate_enabled", lambda: True)
        monkeypatch.setattr(wg, "admit_fact", lambda **kw: (False, "test_forced_rejection"))

        assert store_fact({
            "fact_id": "legacy_wg_1", "claim": "x", "source": "test", "confidence": 0.5,
        }) is False
        assert get_fact("legacy_wg_1") is None

    def test_value_error_still_raises(self, isolated_store):
        from core.memory import store_fact

        with pytest.raises(ValueError):
            store_fact({"claim": "no fact_id"})  # missing fact_id

    def test_budget_exceeded_still_raises(self, isolated_store, monkeypatch):
        from core.feature_config import clear_config_cache
        from core.memory import store_fact
        from core.memory_budget import MemoryBudgetExceededError

        monkeypatch.setenv("ENABLE_MEMORY_BUDGET", "1")
        monkeypatch.setenv("MEMORY_BUDGET_FACT_HARD", "0")
        clear_config_cache()
        try:
            with pytest.raises(MemoryBudgetExceededError):
                store_fact({
                    "fact_id": "legacy_budget_1", "claim": "x", "source": "test", "confidence": 0.5,
                })
        finally:
            monkeypatch.delenv("ENABLE_MEMORY_BUDGET", raising=False)
            monkeypatch.delenv("MEMORY_BUDGET_FACT_HARD", raising=False)
            clear_config_cache()


# ─── promote_inbox_item rejection handling (RED today) ────────────────────────

class TestPromoteInboxItemRejection:
    """RED today: promote_inbox_item() sets status='promoted' and a
    promoted_fact_id even when store_fact() rejected the write (WriteGate) —
    the inbox item becomes permanently stuck (the early-return guard treats
    any 'promoted' status as terminal), and link_raw_to_fact() is called
    with the phantom fact_id regardless."""

    @pytest.fixture
    def ops_store(self, tmp_path, monkeypatch):
        import core.memory as mem
        from core.memory_ops import reset_memory_ops

        db = str(tmp_path / "promote.db")
        monkeypatch.setenv("VELANTRIM_DB_PATH", db)
        store = mem.make_store(db)
        monkeypatch.setattr(mem, "_GLOBAL_STORE", store)
        monkeypatch.setattr(mem, "_L0", store._l0)
        reset_memory_ops()
        yield store
        reset_memory_ops()

    def test_rejected_promotion_stays_pending_and_retryable(self, ops_store, monkeypatch):
        import core.write_gate as wg
        from core.memory_ops import get_memory_ops

        ops = get_memory_ops(ops_store.db_path)
        item = ops.enqueue_fact(claim="a claim that will be rejected by write-gate", confidence=0.8)

        monkeypatch.setattr(wg, "is_write_gate_enabled", lambda: True)
        monkeypatch.setattr(wg, "admit_fact", lambda **kw: (False, "test_forced_rejection"))

        result = ops.promote_inbox_item(item["inbox_id"], fact_id="fact_promo_reject_1")

        assert result["created"] is False
        assert result["fact"] is None
        assert result["inbox_item"]["status"] != "promoted", (
            "a rejected promotion must not mark the inbox item as promoted"
        )
        assert result["inbox_item"].get("promoted_fact_id") is None, (
            "a rejected promotion must not set promoted_fact_id to a phantom fact_id"
        )
        assert not _provenance_row_exists("fact_promo_reject_1")

        # Retry must be possible — a second promote (write-gate now off)
        # should succeed instead of hitting the "already promoted" terminal
        # branch.
        monkeypatch.setattr(wg, "is_write_gate_enabled", lambda: False)
        retry = ops.promote_inbox_item(item["inbox_id"], fact_id="fact_promo_reject_1")
        assert retry["created"] is True
        assert retry["inbox_item"]["status"] == "promoted"
        assert retry["fact"] is not None

    def test_successful_promotion_baseline(self, ops_store):
        """BASELINE: an ordinary successful promotion must keep working."""
        from core.memory import get_fact
        from core.memory_ops import get_memory_ops

        ops = get_memory_ops(ops_store.db_path)
        item = ops.enqueue_fact(claim="a normal claim to promote", confidence=0.8)
        result = ops.promote_inbox_item(item["inbox_id"], fact_id="fact_promo_ok_1")

        assert result["created"] is True
        assert result["inbox_item"]["status"] == "promoted"
        assert result["inbox_item"]["promoted_fact_id"] == "fact_promo_ok_1"
        assert get_fact("fact_promo_ok_1") is not None
        assert _provenance_row_exists("fact_promo_ok_1")
