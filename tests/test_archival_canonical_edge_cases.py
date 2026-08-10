"""Issue #284: additional fail-closed archival edge cases."""

from __future__ import annotations

import os
import subprocess
import sys

import pytest

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "scripts")
APPLY_MIGRATIONS = os.path.join(SCRIPTS_DIR, "apply_migrations.py")


def _run_apply(db_path: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, APPLY_MIGRATIONS, "--db", db_path, "--no-backup"],
        capture_output=True,
        text=True,
    )


@pytest.fixture
def migrated_store(tmp_path):
    from core.memory import SQLiteGraphStore, make_store

    db_path = str(tmp_path / "archive-edge.db")
    bootstrap = SQLiteGraphStore(db_path)
    bootstrap.ensure_schema()
    bootstrap.close()
    result = _run_apply(db_path)
    assert result.returncode == 0, (
        f"apply_migrations failed:\nstdout={result.stdout}\nstderr={result.stderr}"
    )
    store = make_store(db_path)
    yield store
    store.close()


def _seed(store, fact_id: str) -> None:
    result = store.store_fact_result(
        {
            "fact_id": fact_id,
            "claim": "archival edge case",
            "source": "user",
            "confidence": 0.67,
        }
    )
    assert result.durable_write is True


def _row(store, fact_id: str):
    with store._db() as conn:
        return conn.execute(
            "SELECT claim, epistemic_state, fact_version, updated_at "
            "FROM facts WHERE fact_id = ?",
            (fact_id,),
        ).fetchone()


def _evidence_counts(store, fact_id: str) -> tuple[int, int]:
    with store._db() as conn:
        versions = int(
            conn.execute(
                "SELECT COUNT(*) FROM fact_versions WHERE fact_id = ?", (fact_id,)
            ).fetchone()[0]
        )
        marker_table = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='archived_facts'"
        ).fetchone()
        archived = (
            int(
                conn.execute(
                    "SELECT COUNT(*) FROM archived_facts WHERE fact_id = ?", (fact_id,)
                ).fetchone()[0]
            )
            if marker_table
            else 0
        )
    return versions, archived


def _candidate(store, tmp_path, fact_id: str, *, state_override: str | None = None):
    from core.archival_mutation import ArchivalCandidate

    snapshot = store.get_fact_durable(fact_id)
    assert snapshot is not None
    if state_override is not None:
        snapshot = dict(snapshot)
        snapshot["epistemic_state"] = state_override
    payload = tmp_path / f"{fact_id}.json"
    payload.write_text('{"facts": []}', encoding="utf-8")
    return ArchivalCandidate.from_snapshot(
        snapshot,
        archive_key=f"archive://{payload.name}#{fact_id}",
        archive_file=str(payload),
    )


def test_immutable_core_candidate_fails_closed_before_canonical_rewrite(
    migrated_store, tmp_path,
):
    from core.archival_mutation import CanonicalArchivalRewriter

    store = migrated_store
    _seed(store, "immutable-archive")
    before = tuple(_row(store, "immutable-archive"))
    before_evidence = _evidence_counts(store, "immutable-archive")
    candidate = _candidate(
        store,
        tmp_path,
        "immutable-archive",
        state_override="ImmutableCore",
    )

    with pytest.raises(ValueError, match="ImmutableCore"):
        CanonicalArchivalRewriter(store).rewrite_batch([candidate])

    assert tuple(_row(store, "immutable-archive")) == before
    assert _evidence_counts(store, "immutable-archive") == before_evidence


def test_active_migration_with_missing_outbox_rolls_back_canonical_batch(
    migrated_store, tmp_path,
):
    from core.archival_mutation import CanonicalArchivalRewriter

    store = migrated_store
    _seed(store, "corrupt-outbox")
    before = tuple(_row(store, "corrupt-outbox"))
    before_evidence = _evidence_counts(store, "corrupt-outbox")
    candidate = _candidate(store, tmp_path, "corrupt-outbox")

    with store._db() as conn:
        assert int(conn.execute("PRAGMA user_version").fetchone()[0]) >= 20
        conn.execute("DROP TABLE projection_dispatch_state")
        conn.execute("DROP TABLE projection_checkpoints")
        conn.execute("DROP TABLE projection_outbox")

    with pytest.raises(Exception):
        CanonicalArchivalRewriter(store).rewrite_batch([candidate])

    assert tuple(_row(store, "corrupt-outbox")) == before
    assert _evidence_counts(store, "corrupt-outbox") == before_evidence
