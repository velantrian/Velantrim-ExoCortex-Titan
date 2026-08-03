"""
tests/test_sqlite_schema_bootstrap_concurrency.py — concurrent first-use DDL bootstrap
========================================================================================

Issue #182: several independent, genuinely fresh `SQLiteGraphStore` instances
against the same new file-backed SQLite database can enter lazy schema
bootstrap (`SQLiteGraphStore._db()`) at the same time. The per-instance guard
(`self._ddl_initialized_paths`) does not synchronize across instances,
connections or processes. The vulnerable statement pair is:

    DROP VIEW IF EXISTS erasure_audit
    CREATE VIEW erasure_audit AS ...

with no `IF NOT EXISTS` on the `CREATE`. Two fresh instances can interleave:

    A: DROP VIEW IF EXISTS erasure_audit
    B: DROP VIEW IF EXISTS erasure_audit
    A: CREATE VIEW erasure_audit ...  -> success
    B: CREATE VIEW erasure_audit ...  -> OperationalError: already exists

This file pins that interleaving deterministically rather than hoping real
thread scheduling happens to reproduce it. A test-only connection proxy
(`_FirstStatementBarrierConnection`) wraps the real `sqlite3.Connection` each
fresh `SQLiteGraphStore` instance opens and pauses on a shared
`threading.Barrier` immediately before that connection's FIRST `execute()`
call — i.e. before any DDL statement in the lazy bootstrap block runs. It
never rewrites SQL, never swallows an exception, never performs the
CREATE/DROP itself, and never substitutes commit/rollback: it only
coordinates the moment execution of the real, unmodified production SQL
begins, so N independent connections start their entire bootstrap sequence
as close to simultaneously as real threads allow — maximizing genuine
overlap through the whole DDL block rather than gating one specific
statement (which would stop matching once a fix changes what runs there).
"""

from __future__ import annotations

import sqlite3
import threading
from pathlib import Path
from unittest import mock

import pytest

from core.memory import SQLiteGraphStore


class _FirstStatementBarrierConnection:
    """Test-only proxy: pauses on `barrier` immediately before this
    connection's first `execute()` call, then delegates everything —
    including that first call — unmodified to the real connection."""

    def __init__(self, real_conn: sqlite3.Connection, barrier: threading.Barrier, timeout: float):
        object.__setattr__(self, "_real", real_conn)
        object.__setattr__(self, "_barrier", barrier)
        object.__setattr__(self, "_timeout", timeout)
        object.__setattr__(self, "_gated", False)

    def execute(self, *args, **kwargs):
        if not object.__getattribute__(self, "_gated"):
            object.__setattr__(self, "_gated", True)
            object.__getattribute__(self, "_barrier").wait(
                timeout=object.__getattribute__(self, "_timeout"),
            )
        return object.__getattribute__(self, "_real").execute(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(object.__getattribute__(self, "_real"), name)

    def __setattr__(self, name, value):
        setattr(object.__getattribute__(self, "_real"), name, value)


def _race_fresh_bootstrap(
    db_path: Path, num_contenders: int, timeout: float = 20.0,
) -> tuple[dict[int, BaseException], list[SQLiteGraphStore]]:
    """Construct `num_contenders` genuinely fresh SQLiteGraphStore instances
    — none has run any prior operation — and race their first-ever
    `ensure_schema()` call, each gated at its connection's first statement."""
    barrier = threading.Barrier(num_contenders, timeout=timeout)
    errors: dict[int, BaseException] = {}
    errors_lock = threading.Lock()
    stores: list[SQLiteGraphStore | None] = [None] * num_contenders
    real_connect = sqlite3.connect

    def gated_connect(path, *args, **kwargs):
        real_conn = real_connect(path, *args, **kwargs)
        if str(path) == str(db_path):
            return _FirstStatementBarrierConnection(real_conn, barrier, timeout)
        return real_conn

    def make_and_bootstrap(index: int) -> None:
        try:
            store = SQLiteGraphStore(str(db_path))
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
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=timeout + 10)
            assert not t.is_alive(), "contender thread did not finish within timeout"

    return errors, [s for s in stores if s is not None]


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
    return {
        "prevent_erasure_delete",
        "prevent_erasure_update",
        "prevent_erasure_log_subject_corrections_delete",
        "prevent_erasure_log_subject_corrections_update",
    }.issubset(names)


def _assert_view_projection_semantics(db_path: Path) -> None:
    """Insert one erasure_log row plus a subject correction and confirm the
    view still resolves the EFFECTIVE user_id via COALESCE, exposing all
    seven documented columns (migration 016's contract)."""
    store = SQLiteGraphStore(str(db_path))
    try:
        with store._db() as conn:
            # erasure_log_subject_corrections.batch_id REFERENCES
            # erasure_batches(batch_id), but that table is created only by
            # migration 015 — not by this runtime lazy-DDL bootstrap path
            # under test — and SQLite does not enforce foreign keys unless
            # `PRAGMA foreign_keys=ON` (which this codebase does not set),
            # so an arbitrary batch_id value here is sufficient to exercise
            # the view's own projection semantics without needing that
            # unrelated table.
            conn.execute(
                "INSERT INTO erasure_log "
                "(erasure_id, fact_id, user_id, reason, claim_hash, erased_at, "
                " request_ref) "
                "VALUES ('e1', 'f1', 'original-user', 'dsr', 'hash1', "
                "datetime('now'), 'ref1')",
            )
            conn.execute(
                "INSERT INTO erasure_log_subject_corrections "
                "(correction_id, erasure_id, batch_id, corrected_user_id, "
                " original_user_id, created_at) "
                "VALUES ('c1', 'e1', 'b1', 'corrected-user', 'original-user', "
                "datetime('now'))",
            )
            conn.commit()
            row = conn.execute(
                "SELECT erasure_id, fact_id, user_id, reason, claim_hash, "
                "erased_at, request_ref FROM erasure_audit WHERE erasure_id = ?",
                ("e1",),
            ).fetchone()
        assert row is not None
        (erasure_id, fact_id, user_id, reason, claim_hash, erased_at, request_ref) = row
        assert erasure_id == "e1"
        assert fact_id == "f1"
        # Correction-aware resolution: the VIEW must expose the CORRECTED
        # subject, not the original recorded one (migration 016's contract).
        assert user_id == "corrected-user"
        assert reason == "dsr"
        assert claim_hash == "hash1"
        assert erased_at is not None
        assert request_ref == "ref1"
    finally:
        store.close()


@pytest.mark.parametrize("num_contenders", [2, 5, 10])
def test_concurrent_fresh_bootstrap_creates_exactly_one_erasure_audit_view(
    tmp_path: Path, num_contenders: int,
) -> None:
    db_path = tmp_path / f"bootstrap_race_{num_contenders}.db"

    errors, stores = _race_fresh_bootstrap(db_path, num_contenders)

    try:
        # 1/2/3: every contender finished, none hit the DDL race (or any
        # other exception) during concurrent first-use bootstrap.
        assert not errors, (
            f"{len(errors)}/{num_contenders} contenders raised during "
            f"concurrent bootstrap: {errors!r}"
        )

        # 4: every instance can perform ordinary reads afterward.
        for store in stores:
            assert store.get_fact("nonexistent") is None

        # 5: exactly one erasure_audit VIEW exists.
        rows = _erasure_audit_view_rows(db_path)
        assert len(rows) == 1, f"expected exactly one erasure_audit view, found {rows!r}"

        # 6/7: the view has the expected structure/columns and preserves
        # correction-aware projection semantics (migration 016 contract).
        with sqlite3.connect(str(db_path), timeout=5.0) as conn:
            cols = [r[1] for r in conn.execute("PRAGMA table_info(erasure_audit)").fetchall()]
        assert cols == [
            "erasure_id", "fact_id", "user_id", "reason",
            "claim_hash", "erased_at", "request_ref",
        ]

        # 10: PRAGMA integrity_check is ok.
        assert _integrity_check(db_path) == "ok"

        # 11: append-only erasure triggers still exist.
        assert _append_only_triggers_exist(db_path)
    finally:
        for store in stores:
            store.close()

    # Projection semantics, exercised on a fresh connection after all
    # racers have closed.
    _assert_view_projection_semantics(db_path)
    assert _integrity_check(db_path) == "ok"

    # 8/9: a further round of concurrent first-use bootstrap (new stores,
    # same already-initialized database) must remain safe and must not
    # change the view unexpectedly.
    before_sql = _erasure_audit_view_rows(db_path)[0][1]
    errors2, stores2 = _race_fresh_bootstrap(
        db_path, num_contenders, timeout=20.0,
    )
    try:
        assert not errors2, f"second bootstrap round raised: {errors2!r}"
        rows2 = _erasure_audit_view_rows(db_path)
        assert len(rows2) == 1
        assert rows2[0][1] == before_sql, "view definition changed on a later bootstrap"
        assert _integrity_check(db_path) == "ok"
    finally:
        for store in stores2:
            store.close()


def test_concurrent_first_use_on_already_bootstrapped_database(tmp_path: Path) -> None:
    """A database that already has a fully-bootstrapped schema (via one
    ordinary sequential store) must remain safe when several brand-new
    store instances race their own first-ever ensure_schema() against it —
    the realistic multi-worker-process-opens-an-existing-DB scenario."""
    db_path = tmp_path / "already_bootstrapped.db"

    seed = SQLiteGraphStore(str(db_path))
    try:
        seed.ensure_schema()
    finally:
        seed.close()

    before_sql = _erasure_audit_view_rows(db_path)[0][1]

    errors, stores = _race_fresh_bootstrap(db_path, num_contenders=5)
    try:
        assert not errors, f"unexpected errors: {errors!r}"
        rows = _erasure_audit_view_rows(db_path)
        assert len(rows) == 1
        assert rows[0][1] == before_sql
        assert _integrity_check(db_path) == "ok"
        assert _append_only_triggers_exist(db_path)
    finally:
        for store in stores:
            store.close()
