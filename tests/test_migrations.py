"""P0-B post-merge hotfix — migration correctness tests.

Runs scripts/apply_migrations.py against real, temp-file SQLite databases
in every shape an operator could plausibly encounter: fresh, a genuine
013->014 upgrade with pre-existing jobs/tombstones, a re-apply (idempotent
no-op), the v12-self-healed scenario Codex review flagged (P2), and a
deliberately-broken migration to prove failure atomicity.
"""
from __future__ import annotations

import os
import sqlite3
import subprocess
import sys

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "scripts")
APPLY_MIGRATIONS = os.path.join(SCRIPTS_DIR, "apply_migrations.py")
MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), "..", "migrations")


def _run_apply(db_path: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, APPLY_MIGRATIONS, "--db", db_path],
        capture_output=True, text=True,
    )


def test_fresh_apply_reaches_v14_with_expected_schema(tmp_path):
    db_path = str(tmp_path / "fresh.db")
    result = _run_apply(db_path)
    assert result.returncode == 0, result.stderr

    conn = sqlite3.connect(db_path)
    try:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 14
        job_cols = {r[1] for r in conn.execute("PRAGMA table_info(erasure_jobs)").fetchall()}
        assert "generation" in job_cols
        log_cols = {r[1] for r in conn.execute("PRAGMA table_info(erasure_log)").fetchall()}
        assert "job_id" in log_cols
        indexes = {
            r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='erasure_jobs'"
            ).fetchall()
        }
        assert "idx_erasure_jobs_fact" not in indexes
        assert "idx_erasure_jobs_fact_active" in indexes
        assert "idx_erasure_jobs_fact_generation" in indexes
        log_indexes = {
            r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='erasure_log'"
            ).fetchall()
        }
        assert "idx_erasure_job_unique" in log_indexes
    finally:
        conn.close()


def test_reapply_is_idempotent_noop(tmp_path):
    db_path = str(tmp_path / "fresh.db")
    first = _run_apply(db_path)
    assert first.returncode == 0
    second = _run_apply(db_path)
    assert second.returncode == 0
    assert "уже применены" in second.stdout or "актуальна" in second.stdout


def test_v13_to_v14_upgrade_preserves_existing_jobs_and_legacy_tombstones(tmp_path):
    db_path = str(tmp_path / "up13.db")
    assert _run_apply(db_path).returncode == 0

    conn = sqlite3.connect(db_path)
    conn.execute("DROP INDEX IF EXISTS idx_erasure_job")
    conn.execute("DROP INDEX IF EXISTS idx_erasure_job_unique")
    conn.execute("DROP INDEX IF EXISTS idx_erasure_jobs_fact_active")
    conn.execute("DROP INDEX IF EXISTS idx_erasure_jobs_fact_generation")
    conn.execute("ALTER TABLE erasure_jobs DROP COLUMN generation")
    conn.execute("ALTER TABLE erasure_log DROP COLUMN job_id")
    conn.execute("CREATE UNIQUE INDEX idx_erasure_jobs_fact ON erasure_jobs(fact_id)")
    conn.execute("PRAGMA user_version = 13")
    conn.execute(
        "INSERT INTO erasure_jobs (job_id, fact_id, reason, actor, status, created_at, updated_at) "
        "VALUES ('erj_complete1', 'fact_complete', 'test', 'test', 'COMPLETE', 't0', 't0')"
    )
    conn.execute(
        "INSERT INTO erasure_jobs (job_id, fact_id, reason, actor, status, created_at, updated_at) "
        "VALUES ('erj_partial1', 'fact_partial', 'test', 'test', 'PARTIAL', 't0', 't0')"
    )
    conn.execute(
        "INSERT INTO erasure_log (erasure_id, fact_id, user_id, reason, claim_hash, erased_at) "
        "VALUES ('era_complete1', 'fact_complete', 'test', 'test', 'h1', 't0')"
    )
    conn.execute(
        "INSERT INTO erasure_log (erasure_id, fact_id, user_id, reason, claim_hash, erased_at) "
        "VALUES ('era_legacy_only', 'fact_legacy_only', 'test', 'test', 'h2', 't0')"
    )
    conn.commit()
    conn.close()

    result = _run_apply(db_path)
    assert result.returncode == 0, result.stderr

    conn = sqlite3.connect(db_path)
    try:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 14
        jobs = dict(conn.execute("SELECT job_id, status FROM erasure_jobs").fetchall())
        assert jobs == {"erj_complete1": "COMPLETE", "erj_partial1": "PARTIAL"}
        tombstones = {
            r[0] for r in conn.execute("SELECT erasure_id FROM erasure_log").fetchall()
        }
        assert tombstones == {"era_complete1", "era_legacy_only"}
        # PRAGMA integrity intact and append-only triggers still present.
        triggers = {
            r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='trigger' AND tbl_name='erasure_log'"
            ).fetchall()
        }
        assert "prevent_erasure_delete" in triggers
        assert "prevent_erasure_update" in triggers
    finally:
        conn.close()


def test_v12_self_healed_schema_does_not_block_migration_013(tmp_path):
    """Codex review finding (P2): if ErasureCoordinator's own runtime
    _ensure_schema() self-heals a v12 DB into the generation-aware shape
    (multiple terminal generations for one fact_id) BEFORE the operator
    ever runs this script, migration 013's obsolete unconditional
    UNIQUE(fact_id) index must not block the run — it has to be
    neutralized and the run must still reach 014."""
    db_path = str(tmp_path / "prod.db")
    assert _run_apply(db_path).returncode == 0

    conn = sqlite3.connect(db_path)
    conn.execute("DROP INDEX IF EXISTS idx_erasure_job")
    conn.execute("DROP INDEX IF EXISTS idx_erasure_job_unique")
    conn.execute("DROP INDEX IF EXISTS idx_erasure_jobs_fact_active")
    conn.execute("DROP INDEX IF EXISTS idx_erasure_jobs_fact_generation")
    conn.execute("DROP TABLE IF EXISTS erasure_jobs")
    conn.execute("DROP TABLE IF EXISTS erasure_job_steps")
    conn.execute("ALTER TABLE erasure_log DROP COLUMN job_id")
    conn.execute("PRAGMA user_version = 12")
    conn.commit()
    conn.close()

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from core.memory import make_store
    from core.ngram_index import NGramIndex
    from core.erasure_coordinator import ErasureCoordinator, COMPLETE

    store = make_store(db_path)
    ngram = NGramIndex(str(tmp_path / "ngram.db"))
    coord = ErasureCoordinator(store=store, ngram_index=ngram)

    fact_id = "self_healed_fact"
    store.store_fact({"fact_id": fact_id, "claim": "gen1", "source": "test", "confidence": 0.9})
    gen1 = coord.erase_fact_durable(fact_id, reason="test", actor="A")
    assert gen1["outcome"] == COMPLETE
    store.store_fact({"fact_id": fact_id, "claim": "gen2", "source": "test", "confidence": 0.9})
    gen2 = coord.erase_fact_durable(fact_id, reason="test", actor="B")
    assert gen2["outcome"] == COMPLETE
    assert gen2["job_id"] != gen1["job_id"]

    conn = sqlite3.connect(db_path)
    job_count = conn.execute(
        "SELECT COUNT(*) FROM erasure_jobs WHERE fact_id = ?", (fact_id,)
    ).fetchone()[0]
    conn.close()
    assert job_count == 2, "runtime self-heal must have created 2 terminal generations"

    result = _run_apply(db_path)
    assert result.returncode == 0, (
        f"migration run must succeed against a self-healed v12 DB:\n"
        f"stdout={result.stdout}\nstderr={result.stderr}"
    )

    conn = sqlite3.connect(db_path)
    try:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 14
        indexes = {
            r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='erasure_jobs'"
            ).fetchall()
        }
        assert "idx_erasure_jobs_fact" not in indexes
        assert "idx_erasure_jobs_fact_active" in indexes
        assert "idx_erasure_jobs_fact_generation" in indexes
        # Both self-healed generations must have survived the migration.
        remaining = conn.execute(
            "SELECT COUNT(*) FROM erasure_jobs WHERE fact_id = ?", (fact_id,)
        ).fetchone()[0]
        assert remaining == 2
    finally:
        conn.close()


def test_migration_failure_is_fully_atomic(tmp_path):
    """A deliberately-broken migration 014 variant must leave the DB
    exactly as it was before the run — no partial schema change, no
    version bump."""
    db_path = str(tmp_path / "broken13.db")
    assert _run_apply(db_path).returncode == 0

    conn = sqlite3.connect(db_path)
    conn.execute("DROP INDEX IF EXISTS idx_erasure_job")
    conn.execute("DROP INDEX IF EXISTS idx_erasure_job_unique")
    conn.execute("DROP INDEX IF EXISTS idx_erasure_jobs_fact_active")
    conn.execute("DROP INDEX IF EXISTS idx_erasure_jobs_fact_generation")
    conn.execute("ALTER TABLE erasure_jobs DROP COLUMN generation")
    conn.execute("ALTER TABLE erasure_log DROP COLUMN job_id")
    conn.execute("CREATE UNIQUE INDEX idx_erasure_jobs_fact ON erasure_jobs(fact_id)")
    conn.execute("PRAGMA user_version = 13")
    conn.commit()
    conn.close()

    broken_014 = os.path.join(str(tmp_path), "014_broken.sql")
    original = open(os.path.join(MIGRATIONS_DIR, "014_erasure_job_generations.sql")).read()
    broken = original.replace(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_erasure_jobs_fact_generation",
        "INSERT INTO this_table_genuinely_does_not_exist VALUES (1);\n"
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_erasure_jobs_fact_generation",
        1,
    )
    with open(broken_014, "w") as f:
        f.write(broken)

    runner_script = f"""
import sys
sys.path.insert(0, {SCRIPTS_DIR!r})
import apply_migrations as am
from pathlib import Path
am.MIGRATIONS = [(14, Path({broken_014!r}))]
am.apply_migrations(Path({db_path!r}), skip_backup=True)
"""
    result = subprocess.run([sys.executable, "-c", runner_script], capture_output=True, text=True)
    assert result.returncode != 0

    conn = sqlite3.connect(db_path)
    try:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 13
        cols = {r[1] for r in conn.execute("PRAGMA table_info(erasure_jobs)").fetchall()}
        assert "generation" not in cols
        indexes = {
            r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='erasure_jobs'"
            ).fetchall()
        }
        assert "idx_erasure_jobs_fact" in indexes
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    finally:
        conn.close()
