from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from core.memory import SQLiteGraphStore

_ROOT = os.path.join(os.path.dirname(__file__), "..")
_APPLY_MIGRATIONS = os.path.join(_ROOT, "scripts", "apply_migrations.py")


def _migrate(db_path: Path) -> None:
    subprocess.run(
        [sys.executable, _APPLY_MIGRATIONS, "--db", str(db_path), "--no-backup"],
        check=True,
        capture_output=True,
    )


def _seed_promotable_fact(store: SQLiteGraphStore, fact_id: str) -> None:
    assert store.store_fact(
        {
            "fact_id": fact_id,
            "claim": "Issue 347 fresh-store bootstrap serialization regression",
            "source": "manual",
            "confidence": 0.95,
            "metadata": {"evidence_refs": ["source-a", "source-b"]},
        }
    ) is True
    assert store.promote_esm_to(fact_id, "Supported", by="issue347_setup") is True


def _integrity_ok(db_path: Path) -> bool:
    with sqlite3.connect(str(db_path), timeout=5.0) as conn:
        return conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def _outbox_count(db_path: Path, fact_id: str) -> int:
    with sqlite3.connect(str(db_path), timeout=5.0) as conn:
        return int(
            conn.execute(
                "SELECT COUNT(*) FROM projection_outbox WHERE aggregate_id = ?",
                (fact_id,),
            ).fetchone()[0]
        )


def _fact_version(db_path: Path, fact_id: str) -> int:
    with sqlite3.connect(str(db_path), timeout=5.0) as conn:
        return int(
            conn.execute(
                "SELECT fact_version FROM facts WHERE fact_id = ?",
                (fact_id,),
            ).fetchone()[0]
        )


def _outbox_version(db_path: Path, fact_id: str) -> int:
    with sqlite3.connect(str(db_path), timeout=5.0) as conn:
        return int(
            conn.execute(
                "SELECT canonical_version FROM projection_outbox WHERE aggregate_id = ?",
                (fact_id,),
            ).fetchone()[0]
        )


def test_concurrent_fresh_stores_serialize_bootstrap_before_real_cas(tmp_path: Path) -> None:
    """Independent never-opened stores may bootstrap concurrently without SQLITE_SCHEMA.

    The gate is deliberately installed immediately before the real CAS. Therefore every
    contender must first survive its normal lazy schema bootstrap. This locks the #347
    boundary: bootstrap is serialized, while the later CAS race remains genuinely
    concurrent and must still yield one canonical transition and one outbox intent.
    """

    db_path = tmp_path / "fresh-store-race.db"
    fact_id = "f_issue347_fresh_store"
    contenders = 10

    _migrate(db_path)
    bootstrap = SQLiteGraphStore(str(db_path))
    _seed_promotable_fact(bootstrap, fact_id)
    bootstrap.close()

    stores = [SQLiteGraphStore(str(db_path)) for _ in range(contenders)]
    gate = threading.Barrier(contenders, timeout=30.0)

    for store in stores:
        original = store._promote_to_validated_cas

        def gated(*args, _original=original, **kwargs):
            gate.wait(timeout=30.0)
            return _original(*args, **kwargs)

        store._promote_to_validated_cas = gated  # type: ignore[method-assign]

    def promote(index: int):
        return stores[index].validate_and_promote(fact_id, by=f"issue347_{index}")

    try:
        with ThreadPoolExecutor(max_workers=contenders) as executor:
            verdicts = list(executor.map(promote, range(contenders)))
    finally:
        for store in stores:
            store.close()

    winners = [verdict for verdict in verdicts if verdict.passed and verdict.reason == "passed"]
    assert len(winners) == 1, [(verdict.passed, verdict.reason) for verdict in verdicts]

    post_race = SQLiteGraphStore(str(db_path))
    try:
        final = post_race.get_fact(fact_id)
        assert final is not None
        assert final["epistemic_state"] == "Validated"
        assert _outbox_count(db_path, fact_id) == 1
        assert _outbox_version(db_path, fact_id) == _fact_version(db_path, fact_id)

        retry = post_race.validate_and_promote(fact_id, by="issue347_post_race")
        assert retry.passed is True
        assert retry.reason == "already_validated"
        assert _outbox_count(db_path, fact_id) == 1
    finally:
        post_race.close()

    assert _integrity_ok(db_path)


def test_failed_lazy_bootstrap_releases_writer_transaction_and_connection(tmp_path: Path) -> None:
    """A real bootstrap failure must not strand the BEGIN IMMEDIATE writer lock."""

    db_path = tmp_path / "bootstrap-failure.db"
    with sqlite3.connect(str(db_path)) as conn:
        conn.execute("CREATE VIEW facts AS SELECT 1 AS incompatible")
        conn.commit()

    store = SQLiteGraphStore(str(db_path))
    try:
        with pytest.raises(sqlite3.OperationalError):
            store.ensure_schema()
        assert store._sqlite_conn is None

        with sqlite3.connect(str(db_path), timeout=1.0) as probe:
            probe.execute("BEGIN IMMEDIATE")
            probe.rollback()
    finally:
        store.close()
