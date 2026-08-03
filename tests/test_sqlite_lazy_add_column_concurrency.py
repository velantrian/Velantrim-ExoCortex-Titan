"""
tests/test_sqlite_lazy_add_column_concurrency.py — lazy ADD COLUMN TOCTOU race
================================================================================

Issue #184: `SQLiteGraphStore._db()`'s lazy schema bootstrap performs, for several
`facts`/`erasure_log` columns, a Python-side check-then-act upgrade:

    existing_cols = {r[1] for r in conn.execute("PRAGMA table_info(table)").fetchall()}
    if column not in existing_cols:
        conn.execute(f"ALTER TABLE table ADD COLUMN {column} ...")

guarded only by the per-**instance** `self._ddl_initialized_paths` — never shared
across independent instances/connections/processes. Two fresh instances can both read
the same pre-alter snapshot, both decide the column is absent, and then race the same
`ALTER TABLE ... ADD COLUMN`:

    A: PRAGMA table_info(facts) -> audit_subject_id absent
    B: PRAGMA table_info(facts) -> audit_subject_id absent
    A: ALTER TABLE facts ADD COLUMN audit_subject_id ...  -> success
    B: ALTER TABLE facts ADD COLUMN audit_subject_id ...  -> OperationalError:
                                                              duplicate column name

This was discovered during issue #182's investigation (branch
`agent/erasure-audit-ddl-bootstrap-race`, commit
`58b20d950a915813c9bdbc4e7f6d63ee9589e9bc`) and is tracked independently here — it is
NOT the `erasure_audit` VIEW race (issue #182, fixed in PR #185) and does not touch it.

Two schema shapes exercise different code paths:

- **Virgin/current schema** (no pre-existing database file): `facts.audit_subject_id`
  and `facts.derived_from` are the only two of the nine guarded columns NOT already
  present in the current `CREATE TABLE IF NOT EXISTS facts (...)` statement, so their
  `ALTER TABLE ADD COLUMN` unconditionally fires even for a brand-new database.
- **Legacy schema** (a pre-existing database file built with an older, narrower column
  set — simulating a database created by an older version of this code, or by the
  formal migrations before some of these columns were added at the runtime-bootstrap
  layer): every other guarded column (`history`, the four bi-temporal columns,
  `claim_type`, `origin_type`, `erasure_log.job_id`) only ever attempts its
  `ALTER TABLE` when the column is genuinely absent from a pre-existing database —
  which the current `CREATE TABLE IF NOT EXISTS` never produces by itself.

A test-only connection proxy pauses each fresh contender on a shared
`threading.Barrier` immediately before a statement matching a specific
`ALTER TABLE {table} ADD COLUMN {column}` boundary. It never rewrites SQL, never
swallows an exception, never performs the ALTER itself, and never substitutes
commit/rollback.
"""

from __future__ import annotations

import re
import sqlite3
import threading
from pathlib import Path
from unittest import mock

import pytest

from core.memory import SQLiteGraphStore

_ALTER_RE_TEMPLATE = r"^ALTER TABLE {table} ADD COLUMN {column}\b"


class _AlterColumnBarrierConnection:
    """Test-only proxy: every statement runs unmodified; only a statement
    whose normalized text matches `ALTER TABLE {table} ADD COLUMN {column}`
    pauses on `barrier` first. All other statements — including every OTHER
    column's ALTER TABLE, and every PRAGMA table_info read — are never
    gated, and run exactly as they otherwise would."""

    def __init__(
        self, real_conn: sqlite3.Connection, pattern: re.Pattern[str],
        barrier: threading.Barrier, timeout: float,
    ):
        object.__setattr__(self, "_real", real_conn)
        object.__setattr__(self, "_pattern", pattern)
        object.__setattr__(self, "_barrier", barrier)
        object.__setattr__(self, "_timeout", timeout)
        object.__setattr__(self, "_gated", False)

    def execute(self, sql, *args, **kwargs):
        if not object.__getattribute__(self, "_gated"):
            normalized = " ".join(str(sql).split())
            if object.__getattribute__(self, "_pattern").match(normalized):
                object.__setattr__(self, "_gated", True)
                object.__getattribute__(self, "_barrier").wait(
                    timeout=object.__getattribute__(self, "_timeout"),
                )
        return object.__getattribute__(self, "_real").execute(sql, *args, **kwargs)

    def __getattr__(self, name):
        return getattr(object.__getattribute__(self, "_real"), name)

    def __setattr__(self, name, value):
        setattr(object.__getattribute__(self, "_real"), name, value)


# Full current-schema facts column set (excluding the two ALTER-only columns
# audit_subject_id/derived_from, which are never part of CREATE TABLE), used
# to build a legacy fixture missing exactly one target column while keeping
# every other guarded column already present -- so only the ONE column under
# test is ever raced by a given legacy scenario.
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
    """Create a pre-existing `facts` table with every guarded column present
    EXCEPT `missing` — so a racer's own lazy bootstrap only ever attempts
    the ALTER for the column(s) under test, never any other."""
    columns_sql = ",\n            ".join(
        f"{name} {ddl}" for name, ddl in _FULL_FACTS_DDL_COLUMNS.items()
        if name not in missing
    )
    with sqlite3.connect(str(db_path), timeout=5.0) as conn:
        conn.execute(f"CREATE TABLE facts (\n            {columns_sql}\n        )")
        conn.commit()


def _build_legacy_erasure_log_db(db_path: Path, missing: set[str]) -> None:
    """Create a pre-existing minimal `erasure_log` table missing `job_id`
    (current `CREATE TABLE IF NOT EXISTS erasure_log` always includes it, so
    only a genuinely pre-existing legacy table can exercise this path).
    Also creates `facts` with the FULL current column set so the facts-side
    ADD COLUMN loop takes no action and cannot interfere with this test."""
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
        f"{name} {ddl}" for name, ddl in full_erasure_log_columns.items()
        if name not in missing
    )
    _build_legacy_facts_db(db_path, missing=set())
    with sqlite3.connect(str(db_path), timeout=5.0) as conn:
        conn.execute(f"CREATE TABLE erasure_log (\n            {columns_sql}\n        )")
        conn.commit()


def _race_add_column(
    db_path: Path, table: str, column: str, num_contenders: int, timeout: float = 20.0,
) -> tuple[dict[int, BaseException], list[SQLiteGraphStore]]:
    """Race `num_contenders` genuinely fresh SQLiteGraphStore instances
    (each with an empty `_ddl_initialized_paths`) against `db_path`. Every
    contender performs a real, uncoordinated first-use bootstrap — only the
    `ALTER TABLE {table} ADD COLUMN {column}` statement is barrier-gated."""
    pattern = re.compile(_ALTER_RE_TEMPLATE.format(table=re.escape(table), column=re.escape(column)))
    barrier = threading.Barrier(num_contenders, timeout=timeout)
    errors: dict[int, BaseException] = {}
    errors_lock = threading.Lock()
    stores: list[SQLiteGraphStore | None] = [None] * num_contenders
    real_connect = sqlite3.connect

    def gated_connect(path, *args, **kwargs):
        real_conn = real_connect(path, *args, **kwargs)
        if str(path) == str(db_path):
            return _AlterColumnBarrierConnection(real_conn, pattern, barrier, timeout)
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
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=timeout + 10)
            assert not t.is_alive(), "contender thread did not finish within timeout"

    return errors, [s for s in stores if s is not None]


def _integrity_check(db_path: Path) -> str:
    with sqlite3.connect(str(db_path), timeout=5.0) as conn:
        row = conn.execute("PRAGMA integrity_check").fetchone()
    return str(row[0]) if row else "missing"


def _column_row(db_path: Path, table: str, column: str) -> tuple | None:
    with sqlite3.connect(str(db_path), timeout=5.0) as conn:
        return next(
            (r for r in conn.execute(f"PRAGMA table_info({table})").fetchall()
             if r[1] == column),
            None,
        )


def _column_occurrence_count(db_path: Path, table: str, column: str) -> int:
    with sqlite3.connect(str(db_path), timeout=5.0) as conn:
        rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return sum(1 for r in rows if r[1] == column)


_CASES = [
    # (case_id, table, column, legacy_missing_or_None, expected_type, expected_notnull, expected_default)
    ("virgin_audit_subject_id", "facts", "audit_subject_id", None, "TEXT", 0, "NULL"),
    ("virgin_derived_from", "facts", "derived_from", None, "TEXT", 0, "NULL"),
    ("legacy_erasure_log_job_id", "erasure_log", "job_id", "erasure_log", "TEXT", 0, "NULL"),
    ("legacy_t_ingestion_start", "facts", "t_ingestion_start", "facts", "TEXT", 0, "NULL"),
    ("legacy_history", "facts", "history", "facts", "TEXT", 0, "NULL"),
    ("legacy_claim_type", "facts", "claim_type", "facts", "TEXT", 1, "'UNKNOWN'"),
]


def _prepare_db(tmp_path: Path, case_id: str, table: str, column: str, legacy_kind: str | None) -> Path:
    db_path = tmp_path / f"{case_id}.db"
    if legacy_kind == "erasure_log":
        _build_legacy_erasure_log_db(db_path, missing={column})
    elif legacy_kind == "facts":
        _build_legacy_facts_db(db_path, missing={column})
    # legacy_kind is None -> virgin: no pre-existing file at all.
    return db_path


@pytest.mark.parametrize("num_contenders", [2, 5, 10])
@pytest.mark.parametrize(
    "case_id,table,column,legacy_kind,expected_type,expected_notnull,expected_default",
    _CASES,
)
def test_concurrent_fresh_bootstrap_add_column_no_duplicate_error(
    tmp_path: Path,
    case_id: str, table: str, column: str, legacy_kind: str | None,
    expected_type: str, expected_notnull: int, expected_default: str,
    num_contenders: int,
) -> None:
    db_path = _prepare_db(tmp_path, f"{case_id}_{num_contenders}", table, column, legacy_kind)

    errors, stores = _race_add_column(db_path, table, column, num_contenders)

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

    # A further round of concurrent first-use bootstrap (new stores, same
    # already-initialized database) must remain idempotent and safe.
    errors2, stores2 = _race_add_column(db_path, table, column, num_contenders)
    try:
        assert not errors2, f"second bootstrap round raised: {errors2!r}"
        assert _column_occurrence_count(db_path, table, column) == 1
        assert _integrity_check(db_path) == "ok"
    finally:
        for store in stores2:
            store.close()
