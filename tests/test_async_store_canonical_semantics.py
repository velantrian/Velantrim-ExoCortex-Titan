"""Issue #50 — async calls are adapters over canonical sync semantics."""

from __future__ import annotations

import asyncio
import threading

import pytest


@pytest.fixture
def sync_store(tmp_path):
    from core.memory import SQLiteGraphStore

    store = SQLiteGraphStore(str(tmp_path / "async-canonical.db"))
    store.ensure_schema()
    yield store
    store.close()


def _durable_counts(store, fact_id: str) -> tuple[int, int]:
    with store._db() as conn:
        versions = conn.execute(
            "SELECT COUNT(*) FROM fact_versions WHERE fact_id = ?",
            (fact_id,),
        ).fetchone()[0]
        subject = conn.execute(
            "SELECT audit_subject_id FROM facts WHERE fact_id = ?",
            (fact_id,),
        ).fetchone()
        events = 0 if subject is None else conn.execute(
            "SELECT COUNT(*) FROM memory_events WHERE chain_id = ?",
            (f"fact-transition:{subject[0]}",),
        ).fetchone()[0]
    return int(versions), int(events)


def test_native_sql_switch_is_explicitly_disabled(monkeypatch, sync_store):
    from core.async_store import AsyncSQLiteStore, is_async_db_enabled

    monkeypatch.setenv("VELANTRIM_ASYNC_DB", "1")
    assert is_async_db_enabled() is False
    assert AsyncSQLiteStore(sync_store, use_native_async=True)._native is False


@pytest.mark.asyncio
async def test_async_create_update_and_transition_match_canonical_receipts(sync_store):
    from core.async_store import AsyncSQLiteStore
    from core.write_result import WriteStatus

    store = AsyncSQLiteStore(sync_store, use_native_async=True)
    fact_id = "async_equivalent"

    assert await store.store_fact({
        "fact_id": fact_id,
        "claim": "before",
        "source": "test",
        "confidence": 0.5,
    }) is True

    update = await store.store_fact_result({
        "fact_id": fact_id,
        "claim": "after",
        "source": "test",
        "confidence": 0.5,
    })
    assert update.status is WriteStatus.UPDATED
    assert await store.transition_esm(fact_id, "Hypothesized", by="test") is True

    fact = await store.get_fact(fact_id)
    assert fact["claim"] == "after"
    assert fact["epistemic_state"] == "Hypothesized"
    # update closes "before"; transition closes Observed.
    assert _durable_counts(sync_store, fact_id) == (2, 3)


@pytest.mark.asyncio
async def test_async_batch_uses_write_gate_instead_of_direct_sql(sync_store, monkeypatch):
    import core.write_gate as write_gate
    from core.async_store import AsyncSQLiteStore

    monkeypatch.setattr(write_gate, "is_write_gate_enabled", lambda: True)
    store = AsyncSQLiteStore(sync_store)

    result = await store.store_facts_batch([
        {
            "fact_id": "async_rejected",
            "claim": "Unproven world assertion",
            "source": "unknown",
            "claim_type": "WORLD_FACT",
            "origin_type": "EXTERNAL",
        }
    ])

    assert result == {"stored": 0, "updated": 0, "drift": 0, "errors": 1}
    assert await store.get_fact("async_rejected") is None


@pytest.mark.asyncio
async def test_cancelling_awaiter_does_not_interrupt_canonical_transaction(
    sync_store,
):
    """asyncio cancellation cannot stop the worker between SQL statements.

    The caller may stop waiting, but the synchronous canonical method still
    reaches exactly one complete commit/rollback outcome.
    """
    from core.async_store import AsyncSQLiteStore

    started = threading.Event()
    release = threading.Event()
    finished = threading.Event()
    real_store_fact = sync_store.store_fact

    def delayed_store_fact(fact):
        started.set()
        assert release.wait(timeout=5), "test worker was never released"
        try:
            return real_store_fact(fact)
        finally:
            finished.set()

    sync_store.store_fact = delayed_store_fact
    store = AsyncSQLiteStore(sync_store)
    task = asyncio.create_task(store.store_fact({
        "fact_id": "cancelled_waiter",
        "claim": "commits completely",
        "source": "test",
        "confidence": 0.5,
    }))

    assert await asyncio.to_thread(started.wait, 2)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    release.set()
    assert await asyncio.to_thread(finished.wait, 5)
    assert sync_store.get_fact_durable("cancelled_waiter") is not None
    assert _durable_counts(sync_store, "cancelled_waiter") == (0, 1)
