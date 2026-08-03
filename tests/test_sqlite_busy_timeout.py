from __future__ import annotations

import sqlite3
import time

import pytest

from core.memory import SQLiteGraphStore, _sqlite_busy_timeout_ms


def _fact(fact_id: str) -> dict[str, object]:
    return {
        "fact_id": fact_id,
        "claim": f"SQLite bounded busy timeout fact {fact_id}",
        "source": "sqlite_busy_timeout_test",
        "confidence": 0.8,
    }


def test_default_busy_timeout_remains_30_seconds(monkeypatch) -> None:
    monkeypatch.delenv("VELANTRIM_SQLITE_BUSY_TIMEOUT_MS", raising=False)
    assert _sqlite_busy_timeout_ms() == 30_000


@pytest.mark.parametrize("raw", ["", "invalid", "0", "-1", "120001"])
def test_invalid_or_out_of_range_timeout_falls_back_closed(
    monkeypatch, raw: str
) -> None:
    monkeypatch.setenv("VELANTRIM_SQLITE_BUSY_TIMEOUT_MS", raw)
    assert _sqlite_busy_timeout_ms() == 30_000


def test_valid_timeout_is_bound_to_connection_and_pragma(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("VELANTRIM_SQLITE_BUSY_TIMEOUT_MS", "250")
    store = SQLiteGraphStore(str(tmp_path / "pragma.db"))
    try:
        with store._db() as conn:
            pragma_value = int(conn.execute("PRAGMA busy_timeout").fetchone()[0])
        assert store._busy_timeout_ms == 250
        assert pragma_value == 250
    finally:
        store.close()


def test_write_lock_times_out_rolls_back_and_retry_succeeds(
    tmp_path, monkeypatch
) -> None:
    db_path = tmp_path / "locked.db"
    monkeypatch.setenv("VELANTRIM_SQLITE_BUSY_TIMEOUT_MS", "100")

    store = SQLiteGraphStore(str(db_path))
    store.ensure_schema()

    blocker = sqlite3.connect(str(db_path), timeout=1.0, isolation_level=None)
    blocker.execute("PRAGMA journal_mode = WAL")
    blocker.execute("BEGIN IMMEDIATE")

    began = time.perf_counter()
    try:
        with pytest.raises(sqlite3.OperationalError, match="locked"):
            store.store_fact(_fact("blocked-write"))
        elapsed = time.perf_counter() - began

        assert 0.05 <= elapsed < 2.0
        assert store.get_fact("blocked-write") is None
    finally:
        blocker.execute("ROLLBACK")
        blocker.close()

    try:
        store.store_fact(_fact("blocked-write"))
        fact = store.get_fact("blocked-write")
        assert fact is not None
        assert fact["fact_id"] == "blocked-write"
    finally:
        store.close()

    with sqlite3.connect(str(db_path), timeout=1.0) as verifier:
        assert verifier.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert verifier.execute(
            "SELECT COUNT(*) FROM facts WHERE fact_id = ?",
            ("blocked-write",),
        ).fetchone()[0] == 1
