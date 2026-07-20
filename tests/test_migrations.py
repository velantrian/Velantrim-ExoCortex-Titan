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
from pathlib import Path

import pytest

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "scripts")
APPLY_MIGRATIONS = os.path.join(SCRIPTS_DIR, "apply_migrations.py")
MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), "..", "migrations")


def _run_apply(db_path: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, APPLY_MIGRATIONS, "--db", db_path],
        capture_output=True, text=True,
    )


def _run_apply_upto(db_path: str, max_version: int) -> subprocess.CompletedProcess:
    """Run scripts/apply_migrations.py but stop after `max_version` — used
    to construct a REALISTIC v15 database (via the real migration chain,
    not a hand-rolled approximation) before seeding historical rows and
    continuing the upgrade in a separate, later _run_apply() call."""
    runner_script = f"""
import sys
sys.path.insert(0, {SCRIPTS_DIR!r})
import apply_migrations as am
from pathlib import Path
am.MIGRATIONS = [m for m in am.MIGRATIONS if m[0] <= {max_version}]
am.apply_migrations(Path({db_path!r}), skip_backup=True)
"""
    return subprocess.run([sys.executable, "-c", runner_script], capture_output=True, text=True)


def _seed_historical_batch_erasure(
    db_path: str, *, batch_id: str, user_id: str, actor: str,
    fact_id: str, job_id: str, erasure_id: str, wrong_user_id: str,
    now: str = "2026-01-01T00:00:00Z",
) -> None:
    """Seed a v15-shaped completed FORGET_ALL batch whose erasure_log
    tombstone was (pre-Round-5) wrongly keyed to `wrong_user_id` (the
    operator) instead of the batch's real subject `user_id` — the exact
    historical defect migration 016's backfill must repair."""
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO erasure_batches (batch_id, user_id, reason, actor, force, scope, "
        "idempotency_key, request_fingerprint, status, items_total, snapshot_hash, "
        "snapshot_at, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (batch_id, user_id, "dsr", actor, 0, None, None, f"fp_{batch_id}", "COMPLETE", 1,
         f"hash_{batch_id}", now, now, now),
    )
    conn.execute(
        "INSERT INTO erasure_batch_items (item_id, batch_id, fact_id, "
        "epistemic_state_at_snapshot, status, job_id, created_at, updated_at) "
        "VALUES (?,?,?,?,?,?,?,?)",
        (f"item_{fact_id}", batch_id, fact_id, "Validated", "COMPLETE", job_id, now, now),
    )
    conn.execute(
        "INSERT INTO erasure_jobs (job_id, fact_id, generation, reason, actor, status, "
        "created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)",
        (job_id, fact_id, 1, "dsr", actor, "COMPLETE", now, now),
    )
    conn.execute(
        "INSERT INTO erasure_log (erasure_id, fact_id, user_id, reason, claim_hash, "
        "erased_at, job_id) VALUES (?,?,?,?,?,?,?)",
        (erasure_id, fact_id, wrong_user_id, "dsr", f"h_{fact_id}", now, job_id),
    )
    conn.commit()
    conn.close()


def test_fresh_apply_reaches_latest_version_with_expected_schema(tmp_path):
    db_path = str(tmp_path / "fresh.db")
    result = _run_apply(db_path)
    assert result.returncode == 0, result.stderr

    conn = sqlite3.connect(db_path)
    try:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 17
        job_cols = {r[1] for r in conn.execute("PRAGMA table_info(erasure_jobs)").fetchall()}
        assert "generation" in job_cols
        # migrations/016_erasure_job_subject.sql — Round 5 Codex fix:
        # preserve the data-subject user_id separately from operator/actor.
        assert "subject_user_id" in job_cols
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
        # migrations/015_erasure_batches.sql — FORGET_ALL durable batch registry.
        batch_tables = {
            r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'erasure_batch%'"
            ).fetchall()
        }
        assert batch_tables == {
            "erasure_batches", "erasure_batch_items", "erasure_batch_force_receipts",
        }
        batch_indexes = {
            r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='erasure_batches'"
            ).fetchall()
        }
        assert "idx_erasure_batches_idempotency" in batch_indexes

        # migrations/017_audit_chain_hash_v2.sql — Stage B: AuditChain Hash v2.
        event_cols = {r[1] for r in conn.execute("PRAGMA table_info(memory_events)").fetchall()}
        assert {"hash_version", "chain_id", "chain_sequence"} <= event_cols
        event_indexes = {
            r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='memory_events'"
            ).fetchall()
        }
        assert "idx_memory_events_chain_seq" in event_indexes
        assert conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='audit_chain_heads'"
        ).fetchone() is not None
        head = conn.execute(
            "SELECT last_sequence, last_event_hash FROM audit_chain_heads "
            "WHERE chain_id = 'memory_events'"
        ).fetchone()
        assert head == (0, None)  # fresh DB, no events yet
        # append-only triggers from migration 009 remain present
        triggers = {
            r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='trigger' AND tbl_name='memory_events'"
            ).fetchall()
        }
        assert {"prevent_audit_update", "prevent_audit_delete"} <= triggers
    finally:
        conn.close()


def test_v16_to_v17_upgrade_preserves_existing_v1_audit_events(tmp_path):
    """Stage B: upgrading a real v16 database that already has v1-hashed
    memory_events rows must add the v2 schema WITHOUT rewriting any
    existing row's hashed fields, and must seed audit_chain_heads from the
    actual last v1 event so the first v2 append chains onto it."""
    db_path = str(tmp_path / "v16_with_history.db")
    assert _run_apply_upto(db_path, 16).returncode == 0

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from core.audit_chain import compute_audit_hash_v1

    now1 = "2025-01-01T00:00:00+00:00"
    now2 = "2025-01-02T00:00:00+00:00"
    h1 = compute_audit_hash_v1(
        event_type="fact_created", fact_id="f_hist", from_state=None,
        to_state="Observed", actor="agent:legacy", payload={"claim_preview": "x"},
        created_at=now1, prev_event_hash=None,
    )
    h2 = compute_audit_hash_v1(
        event_type="esm_transition", fact_id="f_hist", from_state="Observed",
        to_state="Hypothesized", actor="agent:legacy", payload={},
        created_at=now2, prev_event_hash=h1,
    )
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO memory_events (event_id, event_type, fact_id, to_state, actor, "
        "payload, event_hash, prev_event_hash, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
        ("evt_hist1", "fact_created", "f_hist", "Observed", "agent:legacy",
         '{"claim_preview": "x"}', h1, None, now1),
    )
    conn.execute(
        "INSERT INTO memory_events (event_id, event_type, fact_id, from_state, to_state, "
        "actor, payload, event_hash, prev_event_hash, created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
        ("evt_hist2", "esm_transition", "f_hist", "Observed", "Hypothesized",
         "agent:legacy", "{}", h2, h1, now2),
    )
    conn.commit()
    conn.close()

    result = _run_apply(db_path)
    assert result.returncode == 0, result.stderr

    conn = sqlite3.connect(db_path)
    try:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 17
        rows = conn.execute(
            "SELECT event_id, event_hash, hash_version, chain_id, chain_sequence "
            "FROM memory_events WHERE fact_id = 'f_hist' ORDER BY rowid ASC"
        ).fetchall()
        assert rows == [
            ("evt_hist1", h1, 1, "memory_events", None),
            ("evt_hist2", h2, 1, "memory_events", None),
        ]
        head = conn.execute(
            "SELECT last_sequence, last_event_hash FROM audit_chain_heads "
            "WHERE chain_id = 'memory_events'"
        ).fetchone()
        assert head == (0, h2)  # seeded from the actual last durable event
    finally:
        conn.close()


def test_v17_backfill_runs_when_columns_were_self_healed(tmp_path):
    """Starting from a v16 database where memory_events.hash_version/
    chain_id/chain_sequence ALREADY exist (runtime self-heal via
    AuditChain._ensure_schema(), mirroring the ErasureCoordinator
    precedent) — the ALTERs are skipped safely, but user_version still
    reaches 17 and audit_chain_heads/the unique index still get created."""
    db_path = str(tmp_path / "v16_selfheal.db")
    assert _run_apply_upto(db_path, 16).returncode == 0

    conn = sqlite3.connect(db_path)
    conn.execute("ALTER TABLE memory_events ADD COLUMN hash_version INTEGER NOT NULL DEFAULT 1")
    conn.execute(
        "ALTER TABLE memory_events ADD COLUMN chain_id TEXT NOT NULL DEFAULT 'memory_events'"
    )
    conn.execute("ALTER TABLE memory_events ADD COLUMN chain_sequence INTEGER")
    conn.commit()
    conn.close()

    result = _run_apply(db_path)
    assert result.returncode == 0, result.stderr
    assert "уже существует" in result.stdout

    conn = sqlite3.connect(db_path)
    try:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 17
        assert conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='audit_chain_heads'"
        ).fetchone() is not None
        indexes = {
            r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='memory_events'"
            ).fetchall()
        }
        assert "idx_memory_events_chain_seq" in indexes
    finally:
        conn.close()


def test_v17_reapply_is_idempotent_noop(tmp_path):
    """Re-running the full migration chain a second time after reaching
    v17 makes no further changes (no duplicate audit_chain_heads seed,
    no error)."""
    db_path = str(tmp_path / "v17_idem.db")
    assert _run_apply(db_path).returncode == 0
    conn = sqlite3.connect(db_path)
    before = conn.execute("SELECT * FROM audit_chain_heads").fetchall()
    conn.close()

    second = _run_apply(db_path)
    assert second.returncode == 0

    conn = sqlite3.connect(db_path)
    after = conn.execute("SELECT * FROM audit_chain_heads").fetchall()
    assert conn.execute("PRAGMA user_version").fetchone()[0] == 17
    conn.close()
    assert before == after


def test_migration_017_failure_is_fully_atomic(tmp_path):
    """A deliberately-broken migration 017 variant must leave the DB
    exactly as it was before the run — no partial column add, no
    audit_chain_heads table, no version bump. Mirrors
    test_migration_failure_is_fully_atomic's technique for migration 014."""
    db_path = str(tmp_path / "broken17.db")
    assert _run_apply_upto(db_path, 16).returncode == 0

    broken_017 = os.path.join(str(tmp_path), "017_broken.sql")
    original = Path(MIGRATIONS_DIR, "017_audit_chain_hash_v2.sql").read_text(encoding="utf-8")
    broken = original.replace(
        "CREATE TABLE IF NOT EXISTS audit_chain_heads",
        "INSERT INTO this_table_genuinely_does_not_exist VALUES (1);\n"
        "CREATE TABLE IF NOT EXISTS audit_chain_heads",
        1,
    )
    assert broken != original
    Path(broken_017).write_text(broken, encoding="utf-8")

    runner_script = f"""
import sys
sys.path.insert(0, {SCRIPTS_DIR!r})
import apply_migrations as am
from pathlib import Path
am.MIGRATIONS = [(17, Path({broken_017!r}))]
am.apply_migrations(Path({db_path!r}), skip_backup=True)
"""
    result = subprocess.run([sys.executable, "-c", runner_script], capture_output=True, text=True)
    assert result.returncode != 0

    conn = sqlite3.connect(db_path)
    try:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 16
        cols = {r[1] for r in conn.execute("PRAGMA table_info(memory_events)").fetchall()}
        assert "hash_version" not in cols
        assert conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='audit_chain_heads'"
        ).fetchone() is None
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
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
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 17
        job_cols = {r[1] for r in conn.execute("PRAGMA table_info(erasure_jobs)").fetchall()}
        assert "subject_user_id" in job_cols
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
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 17
        indexes = {
            r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='erasure_jobs'"
            ).fetchall()
        }
        assert "idx_erasure_jobs_fact" not in indexes
        assert "idx_erasure_jobs_fact_active" in indexes
        assert "idx_erasure_jobs_fact_generation" in indexes
        job_cols = {r[1] for r in conn.execute("PRAGMA table_info(erasure_jobs)").fetchall()}
        assert "subject_user_id" in job_cols
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


# ── Round 5.2 fix (Codex P2): migration 016 historical subject backfill ────
#
# erasure_log has genuine append-only enforcement (prevent_erasure_delete/
# prevent_erasure_update, migration 012) — inspected before choosing a
# strategy. Rather than UPDATE historical erasure_log rows (which would
# require dropping/reinstalling those triggers), migration 016 adds a
# SEPARATE, ALSO append-only correction table
# (erasure_log_subject_corrections) and redefines the erasure_audit VIEW
# (the one thing ForgettingEngine.get_erasure_log() actually queries) to
# resolve the EFFECTIVE subject through it via COALESCE. The original
# erasure_log.user_id value is never touched.

def test_v16_backfills_completed_batch_subject_and_audit_lookup(tmp_path):
    """1-3: a v15 database with a completed FORGET_ALL batch whose
    tombstone was wrongly keyed to the operator (api:deadbeef) instead of
    the batch's real subject (userA) must, after upgrading to v16, make
    that erasure discoverable under userA — never under the operator —
    while leaving the raw erasure_log row and operator provenance intact,
    and backfilling erasure_jobs.subject_user_id itself."""
    db_path = str(tmp_path / "v15_hist.db")
    assert _run_apply_upto(db_path, 15).returncode == 0

    _seed_historical_batch_erasure(
        db_path, batch_id="eb_hist1", user_id="userA", actor="api:deadbeef",
        fact_id="fact1", job_id="job1", erasure_id="era_hist1",
        wrong_user_id="api:deadbeef",
    )

    result = _run_apply(db_path)
    assert result.returncode == 0, result.stderr

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 17

        # get_erasure_log(user_id="userA") -> ForgettingEngine queries
        # exactly this view.
        rows = conn.execute(
            "SELECT * FROM erasure_audit WHERE user_id = ?", ("userA",)
        ).fetchall()
        assert {r["erasure_id"] for r in rows} == {"era_hist1"}

        # api:deadbeef must never itself be treated as the data subject.
        assert conn.execute(
            "SELECT * FROM erasure_audit WHERE user_id = ?", ("api:deadbeef",)
        ).fetchall() == []

        # The ORIGINAL recorded evidence is completely untouched.
        raw = conn.execute(
            "SELECT user_id FROM erasure_log WHERE erasure_id = ?", ("era_hist1",)
        ).fetchone()
        assert raw["user_id"] == "api:deadbeef"

        # Operator provenance remains available, and subject_user_id is
        # backfilled onto the job itself.
        job_row = conn.execute(
            "SELECT actor, subject_user_id FROM erasure_jobs WHERE job_id = ?", ("job1",)
        ).fetchone()
        assert job_row["actor"] == "api:deadbeef"
        assert job_row["subject_user_id"] == "userA"

        # erasure_batches.actor (the operator) is also untouched.
        batch_actor = conn.execute(
            "SELECT actor FROM erasure_batches WHERE batch_id = ?", ("eb_hist1",)
        ).fetchone()
        assert batch_actor["actor"] == "api:deadbeef"
    finally:
        conn.close()


def test_v16_does_not_rewrite_unlinked_legacy_tombstones(tmp_path):
    """4 + 5: an ordinary legacy per-fact tombstone with NO batch linkage
    at all must be left completely unchanged; a job_id ambiguously
    referenced by batches for TWO DIFFERENT subjects must also be left
    unchanged (never guessed) rather than rewritten."""
    db_path = str(tmp_path / "v15_legacy_and_ambiguous.db")
    assert _run_apply_upto(db_path, 15).returncode == 0

    now = "2026-01-01T00:00:00Z"
    conn = sqlite3.connect(db_path)

    # Case A: no batch linkage at all (core.erasure.erase_fact()'s shim /
    # the forget_fact MCP tool).
    conn.execute(
        "INSERT INTO erasure_jobs (job_id, fact_id, generation, reason, actor, status, "
        "created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)",
        ("job_legacy", "fact_legacy", 1, "user_request", "legacy-actor", "COMPLETE", now, now),
    )
    conn.execute(
        "INSERT INTO erasure_log (erasure_id, fact_id, user_id, reason, claim_hash, "
        "erased_at, job_id) VALUES (?,?,?,?,?,?,?)",
        ("era_legacy", "fact_legacy", "legacy-actor", "user_request", "h2", now, "job_legacy"),
    )

    # Case B: ambiguous — the SAME job_id referenced by items from batches
    # for TWO distinct subjects (a pre-Round-5.2 possibility this backfill
    # must never resolve by guessing).
    conn.execute(
        "INSERT INTO erasure_jobs (job_id, fact_id, generation, reason, actor, status, "
        "created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)",
        ("job_ambiguous", "fact_ambiguous", 1, "dsr", "api:deadbeef", "COMPLETE", now, now),
    )
    conn.execute(
        "INSERT INTO erasure_log (erasure_id, fact_id, user_id, reason, claim_hash, "
        "erased_at, job_id) VALUES (?,?,?,?,?,?,?)",
        ("era_ambiguous", "fact_ambiguous", "api:deadbeef", "dsr", "h3", now, "job_ambiguous"),
    )
    for suffix, uid in (("x", "userX"), ("y", "userY")):
        conn.execute(
            "INSERT INTO erasure_batches (batch_id, user_id, reason, actor, force, scope, "
            "idempotency_key, request_fingerprint, status, items_total, snapshot_hash, "
            "snapshot_at, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (f"eb_ambig_{suffix}", uid, "dsr", "api:deadbeef", 0, None, None,
             f"fp_ambig_{suffix}", "COMPLETE", 1, f"hash_ambig_{suffix}", now, now, now),
        )
        conn.execute(
            "INSERT INTO erasure_batch_items (item_id, batch_id, fact_id, "
            "epistemic_state_at_snapshot, status, job_id, created_at, updated_at) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (f"item_ambig_{suffix}", f"eb_ambig_{suffix}", "fact_ambiguous", "Validated",
             "COMPLETE", "job_ambiguous", now, now),
        )
    conn.commit()
    conn.close()

    result = _run_apply(db_path)
    assert result.returncode == 0, result.stderr

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        # Case A: unchanged.
        row = conn.execute(
            "SELECT user_id FROM erasure_audit WHERE erasure_id = ?", ("era_legacy",)
        ).fetchone()
        assert row["user_id"] == "legacy-actor"
        assert conn.execute(
            "SELECT COUNT(*) FROM erasure_log_subject_corrections WHERE erasure_id = ?",
            ("era_legacy",),
        ).fetchone()[0] == 0
        job_row = conn.execute(
            "SELECT subject_user_id FROM erasure_jobs WHERE job_id = ?", ("job_legacy",)
        ).fetchone()
        assert job_row["subject_user_id"] is None

        # Case B: unchanged — ambiguous, never guessed.
        row = conn.execute(
            "SELECT user_id FROM erasure_audit WHERE erasure_id = ?", ("era_ambiguous",)
        ).fetchone()
        assert row["user_id"] == "api:deadbeef"
        assert conn.execute(
            "SELECT COUNT(*) FROM erasure_log_subject_corrections WHERE erasure_id = ?",
            ("era_ambiguous",),
        ).fetchone()[0] == 0
        job_row = conn.execute(
            "SELECT subject_user_id FROM erasure_jobs WHERE job_id = ?", ("job_ambiguous",)
        ).fetchone()
        assert job_row["subject_user_id"] is None
    finally:
        conn.close()


def test_v16_backfill_is_idempotent(tmp_path):
    """6: re-running the backfill logic a second time must create no
    additional correction records and leave the correction table's
    contents byte-for-byte identical."""
    db_path = str(tmp_path / "v15_idem.db")
    assert _run_apply_upto(db_path, 15).returncode == 0
    _seed_historical_batch_erasure(
        db_path, batch_id="eb_idem1", user_id="userA", actor="api:deadbeef",
        fact_id="fact_idem", job_id="job_idem", erasure_id="era_idem",
        wrong_user_id="api:deadbeef",
    )
    assert _run_apply(db_path).returncode == 0

    conn = sqlite3.connect(db_path)
    before_count = conn.execute(
        "SELECT COUNT(*) FROM erasure_log_subject_corrections"
    ).fetchone()[0]
    before_rows = conn.execute(
        "SELECT * FROM erasure_log_subject_corrections ORDER BY erasure_id"
    ).fetchall()
    conn.close()
    assert before_count == 1

    # Re-run the migration BODY directly (apply_migrations.py itself would
    # just no-op on a version check alone) — proves the backfill SQL
    # itself is idempotent, not merely "skipped because already at v16".
    sql = Path(MIGRATIONS_DIR, "016_erasure_job_subject.sql").read_text(encoding="utf-8")
    sql = "\n".join(
        line for line in sql.split("\n")
        if "ALTER TABLE erasure_jobs ADD COLUMN subject_user_id" not in line
    )
    conn = sqlite3.connect(db_path)
    conn.executescript(sql)
    conn.commit()
    after_count = conn.execute(
        "SELECT COUNT(*) FROM erasure_log_subject_corrections"
    ).fetchone()[0]
    after_rows = conn.execute(
        "SELECT * FROM erasure_log_subject_corrections ORDER BY erasure_id"
    ).fetchall()
    conn.close()

    assert after_count == before_count == 1
    assert after_rows == before_rows


def test_v16_backfill_runs_when_subject_column_was_self_healed(tmp_path):
    """7: starting from a v15 database where erasure_jobs.subject_user_id
    ALREADY exists (runtime self-heal, mirroring
    ErasureCoordinator._ensure_schema()) — the ALTER is skipped safely, but
    the backfill still executes and user_version still reaches 16."""
    db_path = str(tmp_path / "v15_selfheal.db")
    assert _run_apply_upto(db_path, 15).returncode == 0

    conn = sqlite3.connect(db_path)
    conn.execute("ALTER TABLE erasure_jobs ADD COLUMN subject_user_id TEXT")
    conn.commit()
    conn.close()

    _seed_historical_batch_erasure(
        db_path, batch_id="eb_sh1", user_id="userA", actor="api:deadbeef",
        fact_id="fact_sh", job_id="job_sh", erasure_id="era_sh",
        wrong_user_id="api:deadbeef",
    )

    result = _run_apply(db_path)
    assert result.returncode == 0, result.stderr
    assert "уже существует" in result.stdout  # the ALTER-skip message fired

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 17
        job_row = conn.execute(
            "SELECT subject_user_id FROM erasure_jobs WHERE job_id = ?", ("job_sh",)
        ).fetchone()
        assert job_row["subject_user_id"] == "userA"
        audit_row = conn.execute(
            "SELECT user_id FROM erasure_audit WHERE erasure_id = ?", ("era_sh",)
        ).fetchone()
        assert audit_row["user_id"] == "userA"
    finally:
        conn.close()


def test_v16_preserves_erasure_log_append_only_guards(tmp_path):
    """8: erasure_log's pre-existing append-only UPDATE/DELETE triggers
    (migration 012) remain active after upgrading to v16, and the NEW
    erasure_log_subject_corrections table is itself equally append-only —
    this migration adds a corrective mechanism without ever weakening
    the existing audit-trail protections."""
    db_path = str(tmp_path / "v16_guards.db")
    assert _run_apply(db_path).returncode == 0

    now = "2026-01-01T00:00:00Z"
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO erasure_log (erasure_id, fact_id, user_id, reason, claim_hash, erased_at) "
        "VALUES (?,?,?,?,?,?)",
        ("era_guard", "fact_guard", "userX", "dsr", "hguard", now),
    )
    conn.execute(
        "INSERT INTO erasure_batches (batch_id, user_id, reason, actor, force, scope, "
        "idempotency_key, request_fingerprint, status, items_total, snapshot_hash, "
        "snapshot_at, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        ("eb_guard", "userX", "dsr", "tester", 0, None, None, "fp_guard", "COMPLETE", 1,
         "hash_guard", now, now, now),
    )
    conn.execute(
        "INSERT INTO erasure_log_subject_corrections "
        "(correction_id, erasure_id, job_id, batch_id, corrected_user_id, original_user_id, "
        "created_at) VALUES (?,?,?,?,?,?,?)",
        ("elc_guard", "era_guard", None, "eb_guard", "userX", "userX", now),
    )
    conn.commit()

    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "UPDATE erasure_log SET user_id = 'hacked' WHERE erasure_id = ?", ("era_guard",),
        )
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("DELETE FROM erasure_log WHERE erasure_id = ?", ("era_guard",))
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "UPDATE erasure_log_subject_corrections SET corrected_user_id = 'hacked' "
            "WHERE erasure_id = ?", ("era_guard",),
        )
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "DELETE FROM erasure_log_subject_corrections WHERE erasure_id = ?", ("era_guard",),
        )
    conn.close()


def test_v16_migration_failure_is_fully_atomic(tmp_path):
    """Second-order review requirement: a failure partway through migration
    016 (after the column ALTER and the backfill INSERT/UPDATE, but before
    COMMIT) must roll back the ENTIRE migration — no partial column add,
    no partial correction rows, no partially-redefined view, no version
    bump. Mirrors test_migration_failure_is_fully_atomic's technique for
    migration 014."""
    db_path = str(tmp_path / "broken16.db")
    assert _run_apply_upto(db_path, 15).returncode == 0

    _seed_historical_batch_erasure(
        db_path, batch_id="eb_atomic1", user_id="userA", actor="api:deadbeef",
        fact_id="fact_atomic", job_id="job_atomic", erasure_id="era_atomic",
        wrong_user_id="api:deadbeef",
    )

    broken_016 = os.path.join(str(tmp_path), "016_broken.sql")
    original = Path(MIGRATIONS_DIR, "016_erasure_job_subject.sql").read_text(encoding="utf-8")
    broken = original.replace(
        "COMMIT;",
        "INSERT INTO this_table_genuinely_does_not_exist VALUES (1);\nCOMMIT;",
        1,
    )
    assert broken != original, "the migration file's COMMIT marker must still be present"
    Path(broken_016).write_text(broken, encoding="utf-8")

    runner_script = f"""
import sys
sys.path.insert(0, {SCRIPTS_DIR!r})
import apply_migrations as am
from pathlib import Path
am.MIGRATIONS = [(16, Path({broken_016!r}))]
am.apply_migrations(Path({db_path!r}), skip_backup=True)
"""
    result = subprocess.run([sys.executable, "-c", runner_script], capture_output=True, text=True)
    assert result.returncode != 0

    conn = sqlite3.connect(db_path)
    try:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 15
        cols = {r[1] for r in conn.execute("PRAGMA table_info(erasure_jobs)").fetchall()}
        assert "subject_user_id" not in cols
        # The corrections table/view themselves may already exist — Round
        # 5.3's runtime-schema-parity fix means SQLiteGraphStore's own DDL
        # bootstrap (invoked unconditionally at the top of apply_migrations(),
        # same as it always has for erasure_log itself) creates them
        # idempotently regardless of migration version, exactly like it
        # already did for erasure_log/its indexes pre-Round-5.3. What
        # atomicity actually requires is that migration 016's OWN unique
        # work — the backfill correction row for THIS historical erasure —
        # was never committed.
        no_correction_row = conn.execute(
            "SELECT 1 FROM erasure_log_subject_corrections WHERE erasure_id = ?",
            ("era_atomic",),
        ).fetchone()
        assert no_correction_row is None
        # The historical row seeded above is exactly as seeded — untouched.
        raw = conn.execute(
            "SELECT user_id FROM erasure_log WHERE erasure_id = ?", ("era_atomic",)
        ).fetchone()
        assert raw[0] == "api:deadbeef"
        # erasure_audit resolves to the ORIGINAL value too — no correction
        # was ever applied for this row, so COALESCE falls through.
        audited = conn.execute(
            "SELECT user_id FROM erasure_audit WHERE erasure_id = ?", ("era_atomic",)
        ).fetchone()
        assert audited[0] == "api:deadbeef"
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    finally:
        conn.close()
