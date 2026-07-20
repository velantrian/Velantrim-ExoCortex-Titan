"""
PR-C1 — truthful write results, no phantom provenance/success.

This file pins down the current defects described in the PR-C1 evidence
report (console auto-save false success, POST /facts false success + orphan
raw, phantom fact_inbox promotion, phantom l0_fact_provenance) as regression
tests, alongside baseline tests for the happy path and the legacy
store_fact() bool contract that the fix must not break.

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


# ─── HTTP-level: console auto-save + POST /facts (RED today) ─────────────────

@pytest.fixture
def http_client(tmp_path, monkeypatch):
    """FastAPI TestClient, isolated DB, raise_server_exceptions=False so an
    uncaught exception in a handler surfaces as a real 500 response instead
    of propagating as a Python exception into the test — needed to assert
    on today's (buggy) uncaught-exception behavior and tomorrow's (fixed)
    controlled-response behavior with the same assertion.
    """
    db_path = str(tmp_path / "wr_integration.db")
    ngram_db_path = str(tmp_path / "wr_integration_ngram.db")
    blocks_db_path = str(tmp_path / "wr_blocks.db")
    notebook_db = str(tmp_path / "wr_notebook.db")

    monkeypatch.setenv("VELANTRIM_API_KEY", "test-key")
    monkeypatch.setenv("VELANTRIM_DB_PATH", db_path)
    monkeypatch.setenv("VELANTRIM_NGRAM_DB", ngram_db_path)
    monkeypatch.setenv("CORE_BLOCKS_DB", blocks_db_path)
    monkeypatch.setenv("NOTEBOOK_DB", notebook_db)
    monkeypatch.setenv("LLM_PROVIDER", "none")
    monkeypatch.setenv("SLEEP_WORKER_ENABLED", "false")
    monkeypatch.setenv("VELANTRIM_ALLOW_OPEN", "false")
    monkeypatch.setenv("ENABLE_CAUSAL_GRAPH", "0")
    monkeypatch.setenv("ENABLE_VELUM", "0")

    for mod in list(sys.modules.keys()):
        if mod.startswith(("server", "core.")):
            del sys.modules[mod]

    try:
        from fastapi.testclient import TestClient

        import server as srv
        from core.feature_config import clear_config_cache
    except ImportError as exc:
        pytest.skip(f"Сервер недоступен ({exc})")

    clear_config_cache()

    with TestClient(srv.app, raise_server_exceptions=False) as client:
        client.headers.update({"X-Api-Key": "test-key"})
        yield client, srv


class TestConsoleAutoSaveTruthfulness:
    """RED today: a WriteGate-rejected auto-save candidate ends up in
    memory_saved with a phantom fact_id instead of memory_suggestions."""

    def test_write_gate_rejection_not_reported_as_saved(self, http_client, monkeypatch):
        client, _srv = http_client
        import core.write_gate as wg

        monkeypatch.setattr(wg, "is_write_gate_enabled", lambda: True)
        monkeypatch.setattr(wg, "admit_fact", lambda **kw: (False, "test_forced_rejection"))

        r = client.post("/chat", json={
            "message": "remember that pr-c1 write gate rejection test claim",
            "profile": "citizen",
            "use_memory": False,
            "llm_enabled": False,
            "ui_lang": "en",
            "auto_save_memory": True,
            "persist_to_system": True,
            "block_memory": [],
            "chat_history": [],
        })
        assert r.status_code == 200, r.text
        data = r.json()

        assert data["memory_saved"] == [], (
            f"a rejected candidate must not appear in memory_saved: {data['memory_saved']}"
        )
        assert len(data["memory_suggestions"]) == 1

        from core.memory import get_all_facts

        claims = [f["claim"] for f in get_all_facts()]
        assert "pr-c1 write gate rejection test claim" not in claims

    def test_successful_autosave_baseline(self, http_client):
        """BASELINE: an ordinary auto-save (no rejection) must keep working
        and land in memory_saved with a real fact_id."""
        client, _srv = http_client

        r = client.post("/chat", json={
            "message": "remember that pr-c1 successful autosave baseline claim",
            "profile": "citizen",
            "use_memory": False,
            "llm_enabled": False,
            "ui_lang": "en",
            "auto_save_memory": True,
            "persist_to_system": True,
            "block_memory": [],
            "chat_history": [],
        })
        assert r.status_code == 200, r.text
        data = r.json()
        assert len(data["memory_saved"]) == 1
        fact_id = data["memory_saved"][0]["fact_id"]
        assert fact_id

        from core.memory import get_fact

        assert get_fact(fact_id) is not None


class TestPostFactsTruthfulness:
    """RED today: POST /facts returns HTTP 201 with a `null` body when
    store_fact() is rejected by WriteGate, and an uncaught 500 when
    MemoryBudgetExceededError is raised — in both cases the L0 raw text
    write already committed before the failure."""

    def test_write_gate_rejection_is_not_201(self, http_client, monkeypatch):
        client, _srv = http_client
        import core.write_gate as wg

        monkeypatch.setattr(wg, "is_write_gate_enabled", lambda: True)
        monkeypatch.setattr(wg, "admit_fact", lambda **kw: (False, "test_forced_rejection"))

        r = client.post("/facts", json={
            "fact_id": "facts_wg_reject_1",
            "claim": "pr-c1 post facts write gate rejection",
            "source": "test",
            "confidence": 0.9,
        })
        assert r.status_code != 201, (
            f"a rejected write must not return 201 Created (body={r.text!r})"
        )
        assert r.status_code < 500

        from core.memory import get_fact

        assert get_fact("facts_wg_reject_1") is None
        assert not _provenance_row_exists("facts_wg_reject_1")

    def test_budget_rejection_is_controlled_not_uncaught(self, http_client, monkeypatch):
        client, _srv = http_client
        from core.feature_config import clear_config_cache

        monkeypatch.setenv("ENABLE_MEMORY_BUDGET", "1")
        monkeypatch.setenv("MEMORY_BUDGET_FACT_HARD", "0")
        clear_config_cache()

        r = client.post("/facts", json={
            "fact_id": "facts_budget_reject_1",
            "claim": "pr-c1 post facts budget rejection",
            "source": "test",
            "confidence": 0.9,
        })
        assert r.status_code != 500, (
            f"a budget rejection must be a controlled response, not an "
            f"uncaught internal error (body={r.text!r})"
        )
        assert r.status_code < 500

        from core.memory import get_fact

        assert get_fact("facts_budget_reject_1") is None
        assert not _provenance_row_exists("facts_budget_reject_1")

    def test_successful_create_baseline(self, http_client):
        """BASELINE: an ordinary successful POST /facts must keep working —
        201, canonical fact exists, provenance linked."""
        client, _srv = http_client

        r = client.post("/facts", json={
            "fact_id": "facts_ok_1",
            "claim": "pr-c1 post facts successful baseline",
            "source": "test",
            "confidence": 0.9,
        })
        assert r.status_code == 201, r.text

        from core.memory import get_fact

        fact = get_fact("facts_ok_1")
        assert fact is not None
        assert fact.get("derived_from")
        assert _provenance_row_exists("facts_ok_1")
