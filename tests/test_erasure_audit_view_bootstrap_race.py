"""
tests/test_erasure_audit_view_bootstrap_race.py — erasure_audit bootstrap race
================================================================================

Issue #182 originally used a test-only barrier immediately before
``CREATE VIEW erasure_audit`` to force multiple fresh SQLite connections into
that DDL statement together. Issue #347 intentionally changes the bootstrap
contract: the complete lazy DDL/bootstrap region is serialized by SQLite with
``BEGIN IMMEDIATE``. A rendezvous *inside* that serialized region is therefore
invalid and deadlocks by construction.

This regression now places the rendezvous immediately before each contender's
real ``BEGIN IMMEDIATE`` acquisition. Every contender reaches the serialization
boundary concurrently, then SQLite admits them one writer at a time. The test
still verifies the original erasure-audit guarantees (exactly one correct view,
append-only triggers, projection semantics, repeated fresh bootstrap safety),
without requiring peers to coexist inside the serialized DDL region.
"""

from __future__ import annotations

import re
import sqlite3
import threading
from pathlib import Path
from unittest import mock

import pytest

from core.memory import SQLiteGraphStore

_EXPECTED_COLUMNS = [
    "erasure_id", "fact_id", "user_id", "reason",
    "claim_hash", "erased_at", "request_ref",
]
_APPEND_ONLY_TRIGGERS = {
    "prevent_erasure_delete",
    "prevent_erasure_update",
    "prevent_erasure_log_subject_corrections_delete",
    "prevent_erasure_log_subject_corrections_update",
}
_BEGIN_IMMEDIATE_RE = re.compile(r"^BEGIN IMMEDIATE\b")


class _BootstrapBoundaryBarrierConnection:
    """Test-only proxy that gates only the bootstrap serialization boundary.

    SQL is never rewritten or swallowed. The first ``BEGIN IMMEDIATE`` on each
    contender waits at the shared barrier *before* SQLite tries to acquire the
    writer transaction. Once released, the real statement executes normally,
    so SQLite itself serializes entry into the DDL region.
    """

    def __init__(self, real_conn: sqlite3.Connection, barrier: threading.Barrier, timeout: float):
        object.__setattr__(self, "_real", real_conn)
        object.__setattr__(self, "_barrier", barrier)
        object.__setattr__(self, "_timeout", timeout)
        object.__setattr__(self, "_gated", False)

    def execute(self, sql, *args, **kwargs):
        if not object.__getattribute__(self, "_gated"):
            normalized = " ".join(str(sql).split()).upper()
            if _BEGIN_IMMEDIATE_RE.match(normalized):
                object.__setattr__(self, "_gated", True)
                object.__getattribute__(self, "_barrier").wait(
                    timeout=object.__getattribute__(self, "_timeout"),
                )
        return object.__getattribute__(self, "_real").execute(sql, *args, **kwargs)

    def __enter__(self):
        object.__getattribute__(self, "_real").__enter__()
        return self

    def __exit__(self, exc_type, exc, tb):
        return object.__getattribute__(self, "_real").__exit__(exc_type, exc, tb)

    def __getattr__(self, name):
        return getattr(object.__getattribute__(self, "_real"), name)

    def __setattr__(self, name, value):
        setattr(object.__getattribute__(self, "_real"), name, value)


def _seed_full_schema(db_path: Path) -> None:
    seed = SQLiteGraphStore(str(db_path))
    try:
        seed.ensure_schema()
    finally:
        seed.close()


def _assert_seed_complete(db_path: Path) -> None:
    with sqlite3.connect(str(db_path), timeout=5.0) as conn:
        facts_cols = {r[1] for r in conn.execute("PRAGMA table_info(facts)").fetchall()}
        erasure_log_cols = {r[1] for r in conn.execute("PRAGMA table_info(erasure_log)").fetchall()}
        tables = {
            r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'",
            ).fetchall()
        }
        triggers = {
            r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'trigger'",
            ).fetchall()
        }
        views = {
            r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'view'",
            ).fetchall()
        }
    for col in (
        "history", "t_event_valid_start", "t_event_valid_end",
        "t_ingestion_start", "t_ingestion_end", "audit_subject_id",
        "claim_type", "origin_type", "derived_from",
    ):
        assert col in facts_cols, f"seed did not add facts.{col}"
    assert "job_id" in erasure_log_cols, "seed did not add erasure_log.job_id"
    assert "erasure_log_subject_corrections" in tables
    assert _APPEND_ONLY_TRIGGERS.issubset(triggers)
    assert "erasure_audit" in views


def _race_fresh_bootstrap_on_seeded_db(
    db_path: Path, num_contenders: int, timeout: float = 20.0,
) -> tuple[dict[int, BaseException], list[SQLiteGraphStore]]:
    """Start genuinely fresh stores together at the BEGIN IMMEDIATE boundary."""
    barrier = threading.Barrier(num_contenders, timeout=timeout)
    errors: dict[int, BaseException] = {}
    errors_lock = threading.Lock()
    stores: list[SQLiteGraphStore | None] = [None] * num_contenders
    real_connect = sqlite3.connect

    def gated_connect(path, *args, **kwargs):
        real_conn = real_connect(path, *args, **kwargs)
        if str(path) == str(db_path):
            return _BootstrapBoundaryBarrierConnection(real_conn, barrier, timeout)
        return real_conn

    def make_and_bootstrap(index: int) -> None:
        try:
            store = SQLiteGraphStore(str(db_path))
            assert store._ddl_initialized_paths == set(), (
                "setup: contender store must start with an empty DDL guard"
            )
            stores[index] = store
            store.ensure_schema()
        except BaseException as exc:  # noqa: BLE001 - captured, not swallowed
            with errors_lock:
                errors[index] = exc

    with mock.patch("sqlite3.connect", side_effect=gated_connect):
        threads = [
            threading.Thread(target=make_and_bootstrap, args=(i,))
            for i in range(num_contenders)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=timeout + 10)
            assert not thread.is_alive(), "contender thread did not finish within timeout"

    return errors, [store for store in stores if store is not None]


def _erasure_audit_view_rows(db_path: Path) -> list[tuple]:
    with sqlite3.connect(str(db_path), timeout=5.0) as conn:
        return conn.execute(
            "SELECT name, sql FROM sqlite_master WHERE type = 'view' "
            "AND name = 'erasure_audit'",
        ).fetchall()


def _integrity_check(db_path: Path) -> str:
    with sqlite3.connect(str(db_path), timeout=5.0) as conn:
        row = conn.execute("PRAGMA integrity_check").fetchone()
    return str(row[0]) if row else "missing"


def _append_only_triggers_exist(db_path: Path) -> bool:
    with sqlite3.connect(str(db_path), timeout=5.0) as conn:
        names = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'trigger'",
            ).fetchall()
        }
    return _APPEND_ONLY_TRIGGERS.issubset(names)


def _assert_view_projection_semantics(db_path: Path) -> None:
    store = SQLiteGraphStore(str(db_path))
    try:
        with store._db() as conn:
            conn.execute(
                "INSERT INTO erasure_log "
                "(erasure_id, fact_id, user_id, reason, claim_hash, erased_at, request_ref) "
                "VALUES ('e1', 'f1', 'original-user', 'dsr', 'hash1', datetime('now'), 'ref1')",
            )
            conn.execute(
                "INSERT INTO erasure_log_subject_corrections "
                "(correction_id, erasure_id, batch_id, corrected_user_id, "
                " original_user_id, created_at) "
                "VALUES ('c1', 'e1', 'b1', 'corrected-user', 'original-user', datetime('now'))",
            )
            conn.commit()
            row = conn.execute(
                "SELECT erasure_id, fact_id, user_id, reason, claim_hash, "
                "erased_at, request_ref FROM erasure_audit WHERE erasure_id = ?",
                ("e1",),
            ).fetchone()
        assert row is not None
        erasure_id, fact_id, user_id, reason, claim_hash, erased_at, request_ref = row
        assert erasure_id == "e1"
        assert fact_id == "f1"
        assert user_id == "corrected-user"
        assert reason == "dsr"
        assert claim_hash == "hash1"
        assert erased_at is not None
        assert request_ref == "ref1"
    finally:
        store.close()


@pytest.mark.parametrize("num_contenders", [2, 5, 10])
def test_concurrent_fresh_bootstrap_on_seeded_db_creates_exactly_one_view(
    tmp_path: Path, num_contenders: int,
) -> None:
    db_path = tmp_path / f"erasure_audit_race_{num_contenders}.db"
    _seed_full_schema(db_path)
    _assert_seed_complete(db_path)

    errors, stores = _race_fresh_bootstrap_on_seeded_db(db_path, num_contenders)
    try:
        for index, exc in errors.items():
            message = str(exc)
            assert "duplicate column name" not in message, (
                f"contender {index} hit the separate ADD COLUMN race: {exc!r}"
            )
        assert not errors, (
            f"{len(errors)}/{num_contenders} contenders raised during concurrent bootstrap: "
            f"{errors!r}"
        )

        for store in stores:
            assert store.get_fact("nonexistent") is None

        rows = _erasure_audit_view_rows(db_path)
        assert len(rows) == 1, f"expected exactly one erasure_audit view, found {rows!r}"

        with sqlite3.connect(str(db_path), timeout=5.0) as conn:
            cols = [r[1] for r in conn.execute("PRAGMA table_info(erasure_audit)").fetchall()]
        assert cols == _EXPECTED_COLUMNS
        assert _integrity_check(db_path) == "ok"
        assert _append_only_triggers_exist(db_path)
    finally:
        for store in stores:
            store.close()

    _assert_view_projection_semantics(db_path)
    assert _integrity_check(db_path) == "ok"

    before_sql = _erasure_audit_view_rows(db_path)[0][1]
    errors2, stores2 = _race_fresh_bootstrap_on_seeded_db(db_path, num_contenders)
    try:
        assert not errors2, f"second bootstrap round raised: {errors2!r}"
        rows2 = _erasure_audit_view_rows(db_path)
        assert len(rows2) == 1
        assert rows2[0][1] == before_sql, "view definition changed on a later bootstrap"
        assert _integrity_check(db_path) == "ok"
    finally:
        for store in stores2:
            store.close()
