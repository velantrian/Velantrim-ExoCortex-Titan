from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest import mock

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


class _BootstrapTxnProbe:
    """Shared test probe for the real SQLite writer-transaction boundary."""

    def __init__(self, contenders: int) -> None:
        self.barrier = threading.Barrier(contenders, timeout=20.0)
        self.lock = threading.Lock()
        self.active = 0
        self.max_active = 0
        self.begin_attempts = 0
        self.begin_returns = 0

    def before_begin(self) -> None:
        with self.lock:
            self.begin_attempts += 1
        self.barrier.wait(timeout=20.0)

    def after_begin(self) -> None:
        with self.lock:
            self.begin_returns += 1
            self.active += 1
            self.max_active = max(self.max_active, self.active)

    def after_end(self) -> None:
        with self.lock:
            if self.active:
                self.active -= 1


class _BootstrapTxnProbeConnection:
    """Proxy real SQLite calls; observe but never replace transaction semantics."""

    def __init__(self, real_conn: sqlite3.Connection, probe: _BootstrapTxnProbe) -> None:
        object.__setattr__(self, "_real", real_conn)
        object.__setattr__(self, "_probe", probe)
        object.__setattr__(self, "_owns_bootstrap_txn", False)

    def execute(self, sql, *args, **kwargs):
        normalized = " ".join(str(sql).split()).upper()
        if normalized == "BEGIN IMMEDIATE":
            probe = object.__getattribute__(self, "_probe")
            probe.before_begin()
            result = object.__getattribute__(self, "_real").execute(sql, *args, **kwargs)
            object.__setattr__(self, "_owns_bootstrap_txn", True)
            probe.after_begin()
            return result
        return object.__getattribute__(self, "_real").execute(sql, *args, **kwargs)

    def commit(self):
        try:
            return object.__getattribute__(self, "_real").commit()
        finally:
            if object.__getattribute__(self, "_owns_bootstrap_txn"):
                object.__setattr__(self, "_owns_bootstrap_txn", False)
                object.__getattribute__(self, "_probe").after_end()

    def rollback(self):
        try:
            return object.__getattribute__(self, "_real").rollback()
        finally:
            if object.__getattribute__(self, "_owns_bootstrap_txn"):
                object.__setattr__(self, "_owns_bootstrap_txn", False)
                object.__getattribute__(self, "_probe").after_end()

    def __enter__(self):
        object.__getattribute__(self, "_real").__enter__()
        return self

    def __exit__(self, exc_type, exc, tb):
        return object.__getattribute__(self, "_real").__exit__(exc_type, exc, tb)

    def __getattr__(self, name):
        return getattr(object.__getattribute__(self, "_real"), name)

    def __setattr__(self, name, value):
        setattr(object.__getattribute__(self, "_real"), name, value)


def test_fresh_store_bootstrap_uses_single_writer_transaction_under_contention(
    tmp_path: Path,
) -> None:
    """Deterministically prove the #347 serialization boundary.

    Two genuinely fresh stores rendezvous immediately before the real
    ``BEGIN IMMEDIATE`` call. Both attempt acquisition together, but only one
    writer transaction may return at a time. This is differential evidence:
    the historical implementation has no ``BEGIN IMMEDIATE`` at this boundary,
    so ``begin_attempts``/``begin_returns`` remain zero and this test fails
    deterministically instead of depending on a rare SQLITE_SCHEMA interleave.
    """

    db_path = tmp_path / "fresh-store-bootstrap-boundary.db"
    seed = SQLiteGraphStore(str(db_path))
    try:
        seed.ensure_schema()
    finally:
        seed.close()

    contenders = 2
    stores = [SQLiteGraphStore(str(db_path)) for _ in range(contenders)]
    probe = _BootstrapTxnProbe(contenders)
    real_connect = sqlite3.connect
    errors: list[BaseException] = []
    errors_lock = threading.Lock()

    def probed_connect(path, *args, **kwargs):
        conn = real_connect(path, *args, **kwargs)
        if str(path) == str(db_path):
            return _BootstrapTxnProbeConnection(conn, probe)
        return conn

    def bootstrap(index: int) -> None:
        try:
            stores[index].ensure_schema()
        except BaseException as exc:  # noqa: BLE001 - surfaced after all workers join
            with errors_lock:
                errors.append(exc)

    try:
        with mock.patch("sqlite3.connect", side_effect=probed_connect):
            threads = [threading.Thread(target=bootstrap, args=(index,)) for index in range(contenders)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(timeout=30.0)
                assert not thread.is_alive(), "bootstrap contender did not finish"
    finally:
        for store in stores:
            store.close()

    assert not errors, errors
    assert probe.begin_attempts == contenders
    assert probe.begin_returns == contenders
    assert probe.max_active == 1, "fresh-store bootstrap writer transactions overlapped"
    assert probe.active == 0
    assert _integrity_ok(db_path)


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
