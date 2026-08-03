"""
tests/test_sqlite_lazy_add_column_error_classification.py
===========================================================

Focused unit tests for `core.memory._safe_add_column_if_missing()`'s exact
error-classification boundary (issue #184, PR #187 Copilot follow-up
`discussion_r3704361642`): the benign-duplicate recovery path must trigger
on an EXACT `"duplicate column name: {column}"` match, never a substring
match — a prefix collision (e.g. checking `history` against a real
duplicate for `history_extra`) or a duplicate reported for a genuinely
different column must both re-raise the original, unmodified
`sqlite3.OperationalError`, not be misclassified as this column's own
benign race.

These are pure message/behavior-classification unit tests against a
minimal test-only fake connection — not `sqlite3.Connection` and not real
SQLite I/O. They intentionally do NOT touch, replace, or duplicate the real
concurrency harness in `tests/test_sqlite_lazy_add_column_concurrency.py`,
which continues to prove the same boundary against genuine concurrent
`SQLiteGraphStore` instances and real SQLite connections.
"""

from __future__ import annotations

import sqlite3

import pytest

from core.memory import _safe_add_column_if_missing


class _FakeCursor:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows


class _FakeConnection:
    """Test-only double: not `sqlite3.Connection`. Its `execute()` raises a
    caller-supplied `sqlite3.OperationalError` on the first call (standing
    in for a real `ALTER TABLE` losing a concurrent race) and, only if a
    second call is actually made, returns a caller-supplied `PRAGMA
    table_info(...)` result set. Any call this test does not expect raises
    `AssertionError` immediately, so an unexpected extra PRAGMA consultation
    (e.g. for a prefix-collision or different-column case, which must
    re-raise before ever reaching the PRAGMA re-check) fails loudly rather
    than silently passing."""

    def __init__(self, alter_error: sqlite3.OperationalError, pragma_rows=None):
        self._alter_error = alter_error
        self._pragma_rows = pragma_rows if pragma_rows is not None else []
        self.calls: list[str] = []

    def execute(self, sql, *args, **kwargs):
        self.calls.append(sql)
        if sql.startswith("ALTER TABLE"):
            raise self._alter_error
        if sql.startswith("PRAGMA table_info"):
            return _FakeCursor(self._pragma_rows)
        raise AssertionError(f"unexpected SQL passed to fake connection: {sql!r}")


def _pragma_row(column: str, decl_type: str, notnull: int, dflt_value, pk: int = 0):
    # PRAGMA table_info(table) row shape: (cid, name, type, notnull, dflt_value, pk)
    return (0, column, decl_type, notnull, dflt_value, pk)


# ── A. Exact expected message ───────────────────────────────────────────────

def test_exact_message_match_with_compatible_schema_is_accepted_as_benign():
    exc = sqlite3.OperationalError("duplicate column name: history")
    conn = _FakeConnection(
        exc, pragma_rows=[_pragma_row("history", "TEXT", 0, "NULL")],
    )

    _safe_add_column_if_missing(
        conn, "facts", "history",
        sql_type="TEXT", not_null=False, default_literal="NULL",
    )

    assert conn.calls == [
        "ALTER TABLE facts ADD COLUMN history TEXT DEFAULT NULL",
        "PRAGMA table_info(facts)",
    ], "must enter benign-race verification: ALTER attempted, then re-checked"


def test_exact_message_match_with_incompatible_schema_is_rejected():
    exc = sqlite3.OperationalError("duplicate column name: history")
    # A pre-existing column with the RIGHT name but the WRONG type.
    conn = _FakeConnection(
        exc, pragma_rows=[_pragma_row("history", "INTEGER", 0, "NULL")],
    )

    with pytest.raises(RuntimeError, match="incompatible definition"):
        _safe_add_column_if_missing(
            conn, "facts", "history",
            sql_type="TEXT", not_null=False, default_literal="NULL",
        )

    assert conn.calls == [
        "ALTER TABLE facts ADD COLUMN history TEXT DEFAULT NULL",
        "PRAGMA table_info(facts)",
    ], "must only reject after actually consulting PRAGMA table_info, not assume"


# ── B. Prefix collision ─────────────────────────────────────────────────────

def test_prefix_collision_reraises_original_error_without_pragma_check():
    exc = sqlite3.OperationalError("duplicate column name: history_extra")
    conn = _FakeConnection(
        exc,
        # If the implementation ever regresses to substring matching, it
        # would consult this and could wrongly "recover" — a compatible row
        # here would mask that regression, so it is intentionally absent.
        pragma_rows=[_pragma_row("history_extra", "TEXT", 0, "NULL")],
    )

    with pytest.raises(sqlite3.OperationalError) as excinfo:
        _safe_add_column_if_missing(
            conn, "facts", "history",
            sql_type="TEXT", not_null=False, default_literal="NULL",
        )

    assert excinfo.value is exc, "the ORIGINAL exception object must propagate"
    assert not isinstance(excinfo.value, RuntimeError)
    assert conn.calls == ["ALTER TABLE facts ADD COLUMN history TEXT DEFAULT NULL"], (
        "PRAGMA table_info must never be consulted for a prefix-collision "
        "duplicate that does not name this exact column"
    )


# ── C. Different column ─────────────────────────────────────────────────────

def test_different_column_duplicate_reraises_original_error_unchanged():
    exc = sqlite3.OperationalError("duplicate column name: derived_from")
    conn = _FakeConnection(exc)

    with pytest.raises(sqlite3.OperationalError) as excinfo:
        _safe_add_column_if_missing(
            conn, "facts", "history",
            sql_type="TEXT", not_null=False, default_literal="NULL",
        )

    assert excinfo.value is exc
    assert conn.calls == ["ALTER TABLE facts ADD COLUMN history TEXT DEFAULT NULL"]


# ── D. Unrelated SQLite error ────────────────────────────────────────────────

def test_unrelated_operational_error_propagates_unchanged():
    exc = sqlite3.OperationalError("database disk image is malformed")
    conn = _FakeConnection(exc)

    with pytest.raises(sqlite3.OperationalError) as excinfo:
        _safe_add_column_if_missing(
            conn, "facts", "history",
            sql_type="TEXT", not_null=False, default_literal="NULL",
        )

    assert excinfo.value is exc
    assert conn.calls == ["ALTER TABLE facts ADD COLUMN history TEXT DEFAULT NULL"]
