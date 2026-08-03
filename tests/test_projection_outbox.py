from __future__ import annotations

import sqlite3
from dataclasses import fields
from pathlib import Path

import pytest

from core.projection_outbox import (
    ProjectionIntent,
    ProjectionKind,
    ProjectionOperation,
    ProjectionOutboxContractError,
    append_projection_intent_in_transaction,
)

MIGRATION = (
    Path(__file__).resolve().parent.parent
    / "migrations"
    / "020_projection_outbox.sql"
)


def _connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path), timeout=5.0)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(MIGRATION.read_text(encoding="utf-8"))
    conn.execute(
        "CREATE TABLE IF NOT EXISTS canonical_probe ("
        "probe_id TEXT PRIMARY KEY, value TEXT NOT NULL)"
    )
    conn.commit()


def _intent(*, version: int = 7) -> ProjectionIntent:
    return ProjectionIntent(
        aggregate_id="fact-alpha",
        scope_ref="local:owner",
        canonical_version=version,
        projection_kind=ProjectionKind.ALL,
        operation=ProjectionOperation.REFRESH,
    )


def test_intent_id_is_deterministic_and_contract_is_content_minimized() -> None:
    first = _intent()
    second = _intent()
    assert first.outbox_id == second.outbox_id

    field_names = {field.name for field in fields(ProjectionIntent)}
    forbidden = {
        "claim",
        "justification",
        "evidence",
        "evidence_refs",
        "payload",
        "model_output",
        "prompt",
    }
    assert field_names.isdisjoint(forbidden)


def test_append_requires_an_active_caller_owned_transaction(tmp_path: Path) -> None:
    db_path = tmp_path / "requires-transaction.db"
    conn = _connect(db_path)
    try:
        _create_schema(conn)
        assert conn.in_transaction is False
        with pytest.raises(ProjectionOutboxContractError, match="active"):
            append_projection_intent_in_transaction(conn, _intent())
    finally:
        conn.close()


def test_append_does_not_commit_and_exact_duplicate_is_idempotent(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "no-internal-commit.db"
    writer = _connect(db_path)
    observer = _connect(db_path)
    try:
        _create_schema(writer)
        writer.execute("BEGIN IMMEDIATE")
        first = append_projection_intent_in_transaction(
            writer,
            _intent(),
            created_at="2026-08-03T00:00:00+00:00",
        )
        second = append_projection_intent_in_transaction(
            writer,
            _intent(),
            created_at="2026-08-03T00:00:01+00:00",
        )

        assert first.inserted is True and first.idempotent is False
        assert second.inserted is False and second.idempotent is True
        assert first.outbox_id == second.outbox_id
        assert writer.in_transaction is True
        assert observer.execute(
            "SELECT COUNT(*) FROM projection_outbox"
        ).fetchone()[0] == 0

        writer.commit()
        assert observer.execute(
            "SELECT COUNT(*) FROM projection_outbox"
        ).fetchone()[0] == 1
    finally:
        writer.close()
        observer.close()


def test_canonical_mutation_and_intent_rollback_together(tmp_path: Path) -> None:
    db_path = tmp_path / "shared-rollback.db"
    conn = _connect(db_path)
    try:
        _create_schema(conn)
        conn.execute(
            "INSERT INTO canonical_probe (probe_id, value) VALUES ('p1', 'before')"
        )
        conn.commit()

        conn.execute("BEGIN IMMEDIATE")
        conn.execute(
            "UPDATE canonical_probe SET value = 'after' WHERE probe_id = 'p1'"
        )
        receipt = append_projection_intent_in_transaction(conn, _intent())
        assert receipt.inserted is True
        conn.rollback()

        assert conn.execute(
            "SELECT value FROM canonical_probe WHERE probe_id = 'p1'"
        ).fetchone()[0] == "before"
        assert conn.execute(
            "SELECT COUNT(*) FROM projection_outbox"
        ).fetchone()[0] == 0
    finally:
        conn.close()


def test_outbox_contract_failure_can_roll_back_canonical_mutation(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "contract-failure-rollback.db"
    conn = _connect(db_path)
    intent = _intent()
    try:
        _create_schema(conn)
        conn.execute(
            "INSERT INTO canonical_probe (probe_id, value) VALUES ('p1', 'before')"
        )
        # Seed an impossible semantic collision manually. The public append
        # primitive must detect it instead of treating the row as idempotent.
        conn.execute(
            "INSERT INTO projection_outbox ("
            "outbox_id, aggregate_type, aggregate_id, scope_ref, "
            "projection_kind, operation, canonical_version, policy_version, created_at"
            ") VALUES (?,?,?,?,?,?,?,?,?)",
            (
                intent.outbox_id,
                "fact",
                "different-fact",
                intent.scope_ref,
                intent.projection_kind.value,
                intent.operation.value,
                intent.canonical_version,
                intent.policy_version,
                "2026-08-03T00:00:00+00:00",
            ),
        )
        conn.commit()

        conn.execute("BEGIN IMMEDIATE")
        conn.execute(
            "UPDATE canonical_probe SET value = 'after' WHERE probe_id = 'p1'"
        )
        with pytest.raises(ProjectionOutboxContractError, match="mismatch"):
            append_projection_intent_in_transaction(conn, intent)
        conn.rollback()

        assert conn.execute(
            "SELECT value FROM canonical_probe WHERE probe_id = 'p1'"
        ).fetchone()[0] == "before"
        assert conn.execute(
            "SELECT COUNT(*) FROM projection_outbox"
        ).fetchone()[0] == 1
    finally:
        conn.close()


def test_schema_contains_only_immutable_technical_intent_fields(tmp_path: Path) -> None:
    db_path = tmp_path / "schema-shape.db"
    conn = _connect(db_path)
    try:
        _create_schema(conn)
        columns = {
            str(row[1])
            for row in conn.execute("PRAGMA table_info(projection_outbox)").fetchall()
        }
        assert columns == {
            "outbox_id",
            "aggregate_type",
            "aggregate_id",
            "scope_ref",
            "projection_kind",
            "operation",
            "canonical_version",
            "policy_version",
            "created_at",
        }
        assert columns.isdisjoint(
            {
                "claim",
                "justification",
                "evidence",
                "payload",
                "attempt_count",
                "claimed_by",
                "dispatched_at",
                "last_error",
            }
        )
    finally:
        conn.close()
