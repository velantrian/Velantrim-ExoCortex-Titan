from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path

import pytest

from core.memory import SQLiteGraphStore


def _fact(fact_id: str, *, padding_bytes: int = 0) -> dict[str, object]:
    metadata: dict[str, object] = {"disk_full_test": True}
    if padding_bytes:
        metadata["padding"] = "x" * padding_bytes
    return {
        "fact_id": fact_id,
        "claim": f"SQLite disk-full rollback fact {fact_id}",
        "source": "sqlite_disk_full_test",
        "confidence": 0.8,
        "metadata": metadata,
    }


def _install_connection_scoped_limit(
    store: SQLiteGraphStore,
) -> tuple[int, int, dict[str, bool]]:
    """Apply ``max_page_count`` to every real store connection while enabled.

    SQLiteGraphStore intentionally closes its connection at the end of each
    ``_db()`` context. ``PRAGMA max_page_count`` is connection-scoped, so
    setting it in a preliminary context does not constrain the later public
    ``store_fact()`` transaction. This test-only wrapper injects the fault into
    the exact connection used by each public operation without changing
    production code or bypassing the normal write path.
    """
    with store._db() as conn:
        page_count = int(conn.execute("PRAGMA page_count").fetchone()[0])
        page_size = int(conn.execute("PRAGMA page_size").fetchone()[0])

    target = page_count + 1
    fault = {"enabled": True}
    original_db = store._db

    @contextmanager
    def constrained_db():
        with original_db() as conn:
            if fault["enabled"]:
                applied = int(
                    conn.execute(f"PRAGMA max_page_count = {target}").fetchone()[0]
                )
                assert applied == target
            yield conn

    store._db = constrained_db  # type: ignore[method-assign]
    return page_size, target, fault


def _fact_reference_counts(db_path: Path, fact_id: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    with sqlite3.connect(str(db_path), timeout=5.0) as conn:
        tables = [
            str(row[0])
            for row in conn.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type = 'table' AND name NOT LIKE 'sqlite_%' "
                "ORDER BY name"
            ).fetchall()
        ]
        for table in tables:
            quoted_table = '"' + table.replace('"', '""') + '"'
            columns = {
                str(row[1])
                for row in conn.execute(
                    f"PRAGMA table_info({quoted_table})"
                ).fetchall()
            }
            for column in ("fact_id", "derived_fact_id"):
                if column not in columns:
                    continue
                quoted_column = '"' + column.replace('"', '""') + '"'
                count = int(
                    conn.execute(
                        f"SELECT COUNT(*) FROM {quoted_table} "
                        f"WHERE {quoted_column} = ?",
                        (fact_id,),
                    ).fetchone()[0]
                )
                counts[f"{table}.{column}"] = count
    return counts


def _integrity_check(db_path: Path) -> str:
    with sqlite3.connect(str(db_path), timeout=5.0) as conn:
        row = conn.execute("PRAGMA integrity_check").fetchone()
    return str(row[0]) if row else "missing"


def test_sqlite_full_rolls_back_fact_and_dependents_then_retry_succeeds(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "disk-full.db"
    store = SQLiteGraphStore(str(db_path))
    store.store_fact(_fact("preexisting"))
    seed_before = store.get_fact("preexisting")
    assert seed_before is not None

    page_size, max_page_count, fault = _install_connection_scoped_limit(store)
    oversized = _fact("must-rollback", padding_bytes=page_size * 256)

    try:
        with pytest.raises(sqlite3.OperationalError, match="full"):
            store.store_fact(oversized)

        # Public/cache-visible state and the previously committed row must both
        # remain correct after the failed transaction.
        assert store.get_fact("must-rollback") is None
        seed_after = store.get_fact("preexisting")
        assert seed_after is not None
        assert seed_after["claim"] == seed_before["claim"]
        assert float(seed_after["confidence"]) == float(seed_before["confidence"])
        assert seed_after["epistemic_state"] == seed_before["epistemic_state"]

        with store._db() as conn:
            assert int(conn.execute("PRAGMA page_count").fetchone()[0]) <= max_page_count

        durable_counts = _fact_reference_counts(db_path, "must-rollback")
        assert durable_counts
        assert all(count == 0 for count in durable_counts.values()), durable_counts
        assert _integrity_check(db_path) == "ok"

        # Capacity restoration is explicit. The store does not retry
        # automatically; a fresh public call is made only after the injected
        # connection-level capacity fault has been removed.
        fault["enabled"] = False
        store.store_fact(oversized)
        fact = store.get_fact("must-rollback")
        assert fact is not None
        assert fact["fact_id"] == "must-rollback"
        assert len(str(fact["metadata"]["padding"])) == page_size * 256
    finally:
        store.close()

    durable_counts = _fact_reference_counts(db_path, "must-rollback")
    assert durable_counts.get("facts.fact_id") == 1
    assert all(count >= 0 for count in durable_counts.values())
    assert _integrity_check(db_path) == "ok"
