"""
tests/test_sqlite_lazy_add_column_concurrency.py — lazy ADD COLUMN bootstrap concurrency
=====================================================================================

Issue #184 originally forced contenders to rendezvous immediately before the same
``ALTER TABLE ... ADD COLUMN`` statement. Issue #347 intentionally serializes the
complete lazy DDL/bootstrap region with ``BEGIN IMMEDIATE``. A barrier inside that
serialized region is therefore invalid and deadlocks by construction.

This regression now synchronizes genuinely fresh ``SQLiteGraphStore`` instances
immediately before their real ``BEGIN IMMEDIATE`` acquisition. SQLite then admits
one writer at a time. The test continues to verify the original ADD COLUMN
correctness guarantees across virgin and legacy schema shapes: no bootstrap errors,
exactly one correctly-shaped target column, idempotent repeated fresh bootstrap, and
``PRAGMA integrity_check`` success.
"""

from __future__ import annotations

import re
import sqlite3
import threading
from pathlib import Path
from unittest import mock

import pytest

from core.memory import SQLiteGraphStore

_BEGIN_IMMEDIATE_RE = re.compile(r"^BEGIN IMMEDIATE\b")


class _BootstrapBoundaryBarrierConnection:
    """Gate only the first real bootstrap ``BEGIN IMMEDIATE`` per contender."""

    def __init__(
        self,
        real_conn: sqlite3.Connection,
        barrier: threading.Barrier,
        timeout: float,
    ):
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


_FULL_FACTS_DDL_COLUMNS = {
    "fact_id": "TEXT PRIMARY KEY",
    "claim": "TEXT NOT NULL",
    "source": "TEXT NOT NULL",
    "confidence": "REAL DEFAULT 0.5",
    "epistemic_state": "TEXT DEFAULT 'Observed'",
    "created_at": "TEXT NOT NULL",
    "updated_at": "TEXT NOT NULL",
    "metadata": "TEXT DEFAULT '{}'",
    "history": "TEXT DEFAULT '[]'",
    "t_event_valid_start": "TEXT DEFAULT NULL",
    "t_event_valid_end": "TEXT DEFAULT NULL",
    "t_ingestion_start": "TEXT DEFAULT NULL",
    "t_ingestion_end": "TEXT DEFAULT NULL",
    "claim_type": "TEXT NOT NULL DEFAULT 'UNKNOWN'",
    "origin_type": "TEXT NOT NULL DEFAULT 'UNKNOWN'",
    "memory_type": "TEXT NOT NULL DEFAULT 'semantic'",
    "audit_subject_id": "TEXT DEFAULT NULL",
    "derived_from": "TEXT DEFAULT NULL",
}


def _build_legacy_facts_db(db_path: Path, missing: set[str]) -> None:
    columns_sql = ",\n            ".join(
        f"{name} {ddl}"
        for name, ddl in _FULL_FACTS_DDL_COLUMNS.items()
        if name not in missing
    )
    with sqlite3.connect(str(db_path), timeout=5.0) as conn:
        conn.execute(f"CREATE TABLE facts (\n            {columns_sql}\n        )")
        conn.commit()


def _build_legacy_erasure_log_db(db_path: Path, missing: set[str]) -> None:
    full_erasure_log_columns = {
        "erasure_id": "TEXT PRIMARY KEY",
        "fact_id": "TEXT NOT NULL",
        "user_id": "TEXT NOT NULL DEFAULT 'default'",
        "reason": "TEXT NOT NULL DEFAULT 'user_request'",
        "claim_hash": "TEXT NOT NULL",
        "erased_at": "TEXT NOT NULL",
        "request_ref": "TEXT DEFAULT NULL",
        "job_id": "TEXT DEFAULT NULL",
    }
    columns_sql = ",\n            ".join(
        f"{name} {ddl}"
        for name, ddl in full_erasure_log_columns.items()
        if name not in missing
    )
    _build_legacy_facts_db(db_path, missing=set())
    with sqlite3.connect(str(db_path), timeout=5.0) as conn:
        conn.execute(f"CREATE TABLE erasure_log (\n            {columns_sql}\n        )")
        conn.commit()


def _race_bootstrap(
    db_path: Path,
    num_contenders: int,
    timeout: float = 20.0,
) -> tuple[dict[int, BaseException], list[SQLiteGraphStore]]:
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
            assert store._ddl_initialized_paths == set()
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


def _integrity_check(db_path: Path) -> str:
    with sqlite3.connect(str(db_path), timeout=5.0) as conn:
        row = conn.execute("PRAGMA integrity_check").fetchone()
    return str(row[0]) if row else "missing"


def _column_row(db_path: Path, table: str, column: str) -> tuple | None:
    with sqlite3.connect(str(db_path), timeout=5.0) as conn:
        return next(
            (
                row
                for row in conn.execute(f"PRAGMA table_info({table})").fetchall()
                if row[1] == column
            ),
            None,
        )


def _column_occurrence_count(db_path: Path, table: str, column: str) -> int:
    with sqlite3.connect(str(db_path), timeout=5.0) as conn:
        rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return sum(1 for row in rows if row[1] == column)


_CASES = [
    ("virgin_audit_subject_id", "facts", "audit_subject_id", None, "TEXT", 0, "NULL"),
    ("virgin_derived_from", "facts", "derived_from", None, "TEXT", 0, "NULL"),
    ("legacy_erasure_log_job_id", "erasure_log", "job_id", "erasure_log", "TEXT", 0, "NULL"),
    ("legacy_t_ingestion_start", "facts", "t_ingestion_start", "facts", "TEXT", 0, "NULL"),
    ("legacy_history", "facts", "history", "facts", "TEXT", 0, "NULL"),
    ("legacy_claim_type", "facts", "claim_type", "facts", "TEXT", 1, "'UNKNOWN'"),
]


def _prepare_db(
    tmp_path: Path,
    case_id: str,
    column: str,
    legacy_kind: str | None,
) -> Path:
    db_path = tmp_path / f"{case_id}.db"
    if legacy_kind == "erasure_log":
        _build_legacy_erasure_log_db(db_path, missing={column})
    elif legacy_kind == "facts":
        _build_legacy_facts_db(db_path, missing={column})
    return db_path


@pytest.mark.parametrize("num_contenders", [2, 5, 10])
@pytest.mark.parametrize(
    "case_id,table,column,legacy_kind,expected_type,expected_notnull,expected_default",
    _CASES,
)
def test_concurrent_fresh_bootstrap_add_column_no_duplicate_error(
    tmp_path: Path,
    case_id: str,
    table: str,
    column: str,
    legacy_kind: str | None,
    expected_type: str,
    expected_notnull: int,
    expected_default: str,
    num_contenders: int,
) -> None:
    db_path = _prepare_db(tmp_path, f"{case_id}_{num_contenders}", column, legacy_kind)

    errors, stores = _race_bootstrap(db_path, num_contenders)
    try:
        for index, exc in errors.items():
            message = str(exc)
            assert "view erasure_audit already exists" not in message, (
                f"contender {index} hit issue #182's VIEW race, not #184's ADD "
                f"COLUMN race — isolation failed: {exc!r}"
            )
        assert not errors, (
            f"{len(errors)}/{num_contenders} contenders raised during concurrent "
            f"{table}.{column} bootstrap: {errors!r}"
        )

        for store in stores:
            assert store.get_fact("nonexistent") is None

        assert _column_occurrence_count(db_path, table, column) == 1
        row = _column_row(db_path, table, column)
        assert row is not None
        _cid, _name, decl_type, notnull, dflt_value, pk = row
        assert decl_type == expected_type
        assert notnull == expected_notnull
        assert dflt_value == expected_default
        assert pk == 0
        assert _integrity_check(db_path) == "ok"
    finally:
        for store in stores:
            store.close()

    errors2, stores2 = _race_bootstrap(db_path, num_contenders)
    try:
        assert not errors2, f"second bootstrap round raised: {errors2!r}"
        assert _column_occurrence_count(db_path, table, column) == 1
        assert _integrity_check(db_path) == "ok"
    finally:
        for store in stores2:
            store.close()
