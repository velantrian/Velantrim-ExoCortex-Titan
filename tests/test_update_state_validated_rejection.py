"""R1 remainder: SQLiteGraphStore.update_state(..., "Validated") fails closed.

Direct low-level Validated writes must reject before any durable mutation.
Legitimate Validated admission remains:

    TruthGate.evaluate → validate_and_promote → _promote_to_validated_cas
"""
from __future__ import annotations

import json

import pytest


@pytest.fixture
def isolated_store(tmp_path, monkeypatch):
    from core import memory

    db_path = str(tmp_path / "update-state-validated.db")
    fresh = memory.make_store(db_path)
    monkeypatch.setattr(memory, "_GLOBAL_STORE", fresh)
    monkeypatch.setattr(memory, "_L0", fresh._l0)
    monkeypatch.setattr(memory, "_DDL_INITIALIZED", fresh._ddl_initialized_paths)
    monkeypatch.setattr(memory, "SQLITE_PATH", db_path)
    yield fresh
    fresh.close()


def _table_exists(conn, name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (name,),
    ).fetchone()
    return row is not None


def _columns(conn, table: str) -> set[str]:
    return {r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}


def _count_or_zero(conn, sql: str, params=()):
    try:
        return conn.execute(sql, params).fetchone()[0]
    except Exception:
        return 0


def _snapshot(store, fact_id: str) -> dict:
    fact = store.get_fact(fact_id)
    assert fact is not None
    with store._db() as conn:
        cols = _columns(conn, "facts")
        select_cols = ["epistemic_state", "updated_at", "history", "metadata"]
        if "fact_version" in cols:
            select_cols.append("fact_version")
        row = conn.execute(
            f"SELECT {', '.join(select_cols)} FROM facts WHERE fact_id = ?",
            (fact_id,),
        ).fetchone()
        versions = (
            _count_or_zero(
                conn,
                "SELECT COUNT(*) FROM fact_versions WHERE fact_id = ?",
                (fact_id,),
            )
            if _table_exists(conn, "fact_versions")
            else 0
        )
        events = (
            _count_or_zero(conn, "SELECT COUNT(*) FROM memory_events")
            if _table_exists(conn, "memory_events")
            else 0
        )
        outbox = (
            _count_or_zero(conn, "SELECT COUNT(*) FROM projection_outbox")
            if _table_exists(conn, "projection_outbox")
            else 0
        )
        l1_version = row[4] if "fact_version" in cols else None
    return {
        "l0_state": fact.get("epistemic_state"),
        "l0_updated_at": fact.get("updated_at"),
        "l0_history": list(fact.get("history") or []),
        "l0_version": fact.get("fact_version"),
        "l1_state": row[0],
        "l1_updated_at": row[1],
        "l1_history": json.loads(row[2] or "[]"),
        "l1_metadata": row[3],
        "l1_version": l1_version,
        "versions": versions,
        "events": events,
        "outbox": outbox,
    }


def test_direct_update_state_validated_rejected_without_mutation(isolated_store):
    store = isolated_store
    fact_id = "obs.validated.bypass"
    store.store_fact({
        "fact_id": fact_id,
        "claim": "ordinary observed claim",
        "source": "test",
        "confidence": 0.5,
    })
    before = _snapshot(store, fact_id)
    assert before["l1_state"] == "Observed"

    with pytest.raises(ValueError, match="protected admission"):
        store.update_state(
            fact_id,
            "Validated",
            {"state": "Validated", "at": "2026-09-18T00:00:00Z", "by": "test"},
            "2026-09-18T00:00:00Z",
        )

    after = _snapshot(store, fact_id)
    assert after == before
    assert after["l1_state"] == "Observed"
    assert after["l0_state"] == "Observed"


def test_direct_update_state_validated_keyword_rejected(isolated_store):
    store = isolated_store
    fact_id = "obs.validated.keyword"
    store.store_fact({
        "fact_id": fact_id,
        "claim": "ordinary observed claim",
        "source": "test",
        "confidence": 0.5,
    })
    before = _snapshot(store, fact_id)

    with pytest.raises(ValueError, match="protected admission"):
        store.update_state(
            fact_id,
            new_state="Validated",
            history_entry={"state": "Validated", "at": "2026-09-18T00:00:00Z", "by": "test"},
            now="2026-09-18T00:00:00Z",
        )

    assert _snapshot(store, fact_id) == before


def test_async_update_state_inherits_validated_rejection(isolated_store):
    import asyncio

    from core.async_store import AsyncSQLiteStore

    store = isolated_store
    fact_id = "obs.validated.async"
    store.store_fact({
        "fact_id": fact_id,
        "claim": "ordinary observed claim",
        "source": "test",
        "confidence": 0.5,
    })
    before = _snapshot(store, fact_id)
    async_store = AsyncSQLiteStore(store)

    async def _call() -> None:
        await async_store.update_state(
            fact_id,
            "Validated",
            {"state": "Validated", "at": "2026-09-18T00:00:00Z", "by": "test"},
            "2026-09-18T00:00:00Z",
        )

    with pytest.raises(ValueError, match="protected admission"):
        asyncio.run(_call())

    assert _snapshot(store, fact_id) == before


def test_protected_admission_still_reaches_validated(isolated_store):
    store = isolated_store
    fact_id = "elig.validated.ok"
    store.store_fact({
        "fact_id": fact_id,
        "claim": "well evidenced claim",
        "source": "test",
        "confidence": 0.85,
        "metadata": {"evidence_refs": ["e1", "e2"]},
    })
    assert store.transition_esm(fact_id, "Hypothesized", by="test")
    assert store.transition_esm(fact_id, "Supported", by="test")
    ok = store.promote_to_validated(fact_id, by="test")
    assert ok is True
    assert store.get_fact(fact_id)["epistemic_state"] == "Validated"
