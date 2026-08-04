"""Issue #183: include projection_outbox intents in the atomic same-DB
erasure proof.

Foundation status (see core/projection_outbox.py, migrations/020_*.sql):
no Canon caller writes rows into `projection_outbox` yet, and no dispatcher
reads them — this file proves ONLY that `SQLiteGraphStore`'s existing
same-DB dependent registry (`_SAME_DB_DEPENDENT_TABLES`,
`erase_fact_dependents_atomic()`, `same_db_dependents_present()`) already
owns `projection_outbox` rows the moment a caller starts writing them, with
no separate wiring — exactly as it already owns `relations`,
`fact_mentions`, etc.

Every test constructs a real, temp-file-backed SQLiteGraphStore — no
fakes/stubs/mocks for SQLite itself. `migrated_rig`/`migrated_store` run
the REAL migration chain via scripts/apply_migrations.py so
`projection_outbox` (migration 020) genuinely exists with the real
constraints from migrations/020_projection_outbox.sql.
"""
from __future__ import annotations

import os
import subprocess
import sys
import sqlite3

import pytest

from core.erasure_coordinator import COMPLETE, ErasureCoordinator
from core.embedding_store import EmbeddingStore
from core.memory import ImmutableStateError, IMMUTABLE_FACT_IDS, make_store
from core.ngram_index import NGramIndex
from core.projection_outbox import LOCAL_PROJECTION_SCOPE_REF

_ROOT = os.path.join(os.path.dirname(__file__), "..")
_APPLY_MIGRATIONS = os.path.join(_ROOT, "scripts", "apply_migrations.py")


def _fact(fid, claim="user contact is a@b.com", **extra):
    return {"fact_id": fid, "claim": claim, "source": "test", "confidence": 0.9, **extra}


def _insert_outbox_row(
    conn: sqlite3.Connection,
    *,
    outbox_id: str,
    aggregate_id: str,
    aggregate_type: str = "fact",
    canonical_version: int = 1,
) -> None:
    """Insert one real projection_outbox row directly (bypassing
    core.projection_outbox's transaction-ownership contract, which is
    irrelevant to what this file proves: erasure ownership of whatever
    rows exist, regardless of how they got there)."""
    conn.execute(
        "INSERT INTO projection_outbox ("
        "outbox_id, aggregate_type, aggregate_id, scope_ref, projection_kind, "
        "operation, canonical_version, policy_version, created_at"
        ") VALUES (?, ?, ?, ?, 'all', 'refresh', ?, 'projection-outbox-v1', "
        "'2026-08-03T00:00:00Z')",
        (outbox_id, aggregate_type, aggregate_id, LOCAL_PROJECTION_SCOPE_REF, canonical_version),
    )


@pytest.fixture
def migrated_store(tmp_path):
    """A SQLiteGraphStore whose facts DB has gone through the REAL
    migration chain (008-020), so `projection_outbox` genuinely exists
    with the real migrations/020_projection_outbox.sql constraints, and
    PRAGMA user_version == 20."""
    db_path = str(tmp_path / "facts.db")
    subprocess.run(
        [sys.executable, _APPLY_MIGRATIONS, "--db", db_path, "--no-backup"],
        check=True, capture_output=True,
    )
    return make_store(db_path)


@pytest.fixture
def migrated_rig(tmp_path, migrated_store):
    """Same shape as test_erasure_coordinator.py's `migrated_rig`: a real
    ErasureCoordinator wired to the migrated store plus real embeddings/
    ngram backends."""
    store = migrated_store
    embeddings = EmbeddingStore(str(tmp_path / "embeddings.db"))
    embeddings.ensure_table()
    ngram = NGramIndex(str(tmp_path / "ngram.db"))
    coordinator = ErasureCoordinator(
        store=store, embedding_store=embeddings, ngram_index=ngram
    )
    return coordinator, store, embeddings, ngram


def _install_real_failure_trigger(store, *, table: str, fact_id: str) -> None:
    """Real SQLite trigger that raises on DELETE from `table` for
    `fact_id` — a genuine DB-level failure, mirroring
    test_erasure_coordinator.py's helper of the same name."""
    trigger_name = f"simulate_{table}_delete_failure"
    with store._db() as conn:
        conn.execute(f"""
            CREATE TRIGGER IF NOT EXISTS {trigger_name}
            BEFORE DELETE ON {table}
            WHEN OLD.fact_id = '{fact_id}'
            BEGIN
                SELECT RAISE(ABORT, 'SIMULATED: real DB failure mid-transaction');
            END;
        """)


# ── A. Fact and associated projection intent removed together ──────────────

def test_atomic_erasure_deletes_projection_intent_and_reports_it(migrated_store):
    store = migrated_store
    store.store_fact(_fact("f_outbox_a"))
    with store._db() as conn:
        _insert_outbox_row(conn, outbox_id="ob_a", aggregate_id="f_outbox_a")
        conn.commit()

    result = store.erase_fact_dependents_atomic("f_outbox_a")

    assert result["tables"]["projection_outbox"] == {"applicable": True, "deleted": 1}
    with store._db() as conn:
        row = conn.execute(
            "SELECT 1 FROM projection_outbox WHERE aggregate_id = ?", ("f_outbox_a",)
        ).fetchone()
    assert row is None


def test_full_saga_reports_projection_outbox_deletion_in_l1_same_db_detail(migrated_rig):
    coordinator, store, _embeddings, _ngram = migrated_rig
    store.store_fact(_fact("f_outbox_full"))
    with store._db() as conn:
        _insert_outbox_row(conn, outbox_id="ob_full", aggregate_id="f_outbox_full")
        conn.commit()

    report = coordinator.erase_fact_durable("f_outbox_full", reason="dsr", actor="tester")

    assert report["outcome"] == COMPLETE
    tables = report["steps"]["l1_same_db"]["detail"]["tables"]
    assert tables["projection_outbox"] == {"applicable": True, "deleted": 1}
    assert coordinator.is_erased("f_outbox_full") is True


# ── B. Forced failure after outbox deletion rolls back the WHOLE transaction ─

def test_forced_facts_delete_failure_rolls_back_outbox_and_other_dependents(migrated_store):
    """facts DELETE happens strictly AFTER every _SAME_DB_DEPENDENT_TABLES
    delete (including projection_outbox) in erase_fact_dependents_atomic()'s
    single transaction — forcing the facts DELETE itself to fail exercises
    exactly "a real failure after the outbox row was deleted", and the
    whole transaction (fact + outbox + every other dependent) must roll
    back together, not partially."""
    store = migrated_store
    fact_id = "trig_fail_outbox_rollback"
    other_fact_id = "trig_fail_outbox_rollback_other"
    store.store_fact(_fact(other_fact_id, claim="other fact"))
    store.store_fact(_fact(fact_id, epistemic_state="Observed"))
    with store._db() as conn:
        _insert_outbox_row(conn, outbox_id="ob_rollback", aggregate_id=fact_id)
        conn.execute(
            "INSERT INTO relations (from_fact_id, to_fact_id, relation_type) "
            "VALUES (?, ?, ?)",
            (fact_id, other_fact_id, "supports"),
        )
        conn.commit()
    _install_real_failure_trigger(store, table="facts", fact_id=fact_id)

    with pytest.raises(Exception):  # sqlite3.IntegrityError from RAISE(ABORT, ...)
        store.erase_fact_dependents_atomic(fact_id)

    assert store.get_fact(fact_id) is not None, "fact must survive the rolled-back transaction"
    with store._db() as conn:
        outbox_row = conn.execute(
            "SELECT 1 FROM projection_outbox WHERE aggregate_id = ?", (fact_id,)
        ).fetchone()
        relation_row = conn.execute(
            "SELECT 1 FROM relations WHERE from_fact_id = ?", (fact_id,)
        ).fetchone()
    assert outbox_row is not None, "outbox intent must survive the rolled-back transaction"
    assert relation_row is not None, "other dependents must survive the rolled-back transaction"

    # Retry after removing the simulated failure must still work cleanly.
    with store._db() as conn:
        conn.execute("DROP TRIGGER IF EXISTS simulate_facts_delete_failure")
    result = store.erase_fact_dependents_atomic(fact_id)
    assert result["tables"]["projection_outbox"] == {"applicable": True, "deleted": 1}
    assert result["tables"]["relations"] == {"applicable": True, "deleted": 1}


# ── C. Residual checker detects a surviving projection intent ──────────────

def test_residual_checker_detects_surviving_projection_intent_after_legacy_deletion(migrated_store):
    """A clean erasure first proves no OTHER same-DB dependent (facts_fts,
    fact_versions, etc.) is left over — isolating the signal — then an
    orphaned projection_outbox row is added back on its own (the shape a
    legacy/out-of-band deletion would leave once a Canon caller starts
    writing intents), and must be detected on its own."""
    store = migrated_store
    fact_id = "f_outbox_orphan"
    store.store_fact(_fact(fact_id, claim="will be legacy-erased"))
    store.erase_fact_dependents_atomic(fact_id)
    assert store.same_db_dependents_present(fact_id) is False, (
        "sanity check: no unrelated dependent must already be residual "
        "before the orphaned outbox row is added"
    )

    with store._db() as conn:
        _insert_outbox_row(conn, outbox_id="ob_orphan", aggregate_id=fact_id)
        conn.commit()

    assert store.same_db_dependents_present(fact_id) is True


# ── D. Reappeared intent after completion makes the result untrusted ───────

def test_reappeared_projection_intent_after_complete_opens_new_generation(migrated_rig):
    """Mirrors test_erasure_coordinator.py's
    test_l1_same_db_complete_then_new_orphaned_dependent_opens_new_generation,
    but for a projection_outbox intent specifically: after a COMPLETE
    erasure, a new outbox row appears for the SAME fact_id (no facts row) —
    the completed job must stop being trusted, and the next erase call must
    detect this and clean it under a NEW generation."""
    coordinator, store, _embeddings, _ngram = migrated_rig
    fact_id = "f_outbox_reappear"
    store.store_fact(_fact(fact_id, claim="original"))

    first = coordinator.erase_fact_durable(fact_id, reason="test", actor="A")
    assert first["outcome"] == COMPLETE
    assert coordinator.is_erased(fact_id) is True

    with store._db() as conn:
        _insert_outbox_row(conn, outbox_id="ob_reappear", aggregate_id=fact_id)
        conn.commit()

    assert coordinator.is_erased(fact_id) is False, (
        "a reappeared projection intent must make a previously-COMPLETE "
        "erasure untrusted"
    )
    assert store.same_db_dependents_present(fact_id) is True

    second = coordinator.erase_fact_durable(fact_id, reason="test", actor="B")
    assert second["job_id"] != first["job_id"], (
        "a COMPLETE l1_same_db receipt going stale on a reappeared intent "
        "must open a new generation"
    )
    assert second["steps"]["l1_same_db"]["detail"]["tables"]["projection_outbox"] == {
        "applicable": True, "deleted": 1,
    }
    assert store.same_db_dependents_present(fact_id) is False, (
        "the new generation must clean the reappeared outbox intent"
    )
    # NOTE: this scenario's overall outcome legitimately stays PARTIAL /
    # residual="undetermined" (determine_raw cannot re-confirm raw-origin
    # absence once the facts row is already gone — see
    # core/erasure_coordinator.py's own comment on this exact shape,
    # unrelated to and unchanged by this issue's projection_outbox fix) —
    # is_erased() is intentionally NOT asserted True here, matching
    # test_erasure_coordinator.py's identical-shape reference test.
    #
    # The FIRST job's own status is intentionally not asserted here either:
    # unlike a still-resumable (PARTIAL/PENDING/FAILED) predecessor — which
    # genuinely gets superseded — a predecessor that had already reached
    # the terminal COMPLETE status stays COMPLETE as an honest historical
    # record of that earlier generation; only a brand new job_id (asserted
    # above) proves a fresh generation actually ran.
    with coordinator._jobs_db() as conn:
        first_status = conn.execute(
            "SELECT status FROM erasure_jobs WHERE job_id = ?", (first["job_id"],)
        ).fetchone()["status"]
    assert first_status == COMPLETE


# ── E. Ring Zero protections are unchanged ──────────────────────────────────

def test_ring_zero_protection_unchanged(migrated_store):
    store = migrated_store
    ring_zero_id = next(iter(IMMUTABLE_FACT_IDS))
    with pytest.raises(ImmutableStateError):
        store.erase_fact_dependents_atomic(ring_zero_id)


# ── F. Migration-020 gating: absence is safe pre-activation, fails closed
#      after schema version 20 ─────────────────────────────────────────────

def test_bare_unmigrated_store_treats_missing_projection_outbox_as_not_applicable(tmp_path):
    """A database that has never gone through scripts/apply_migrations.py
    (make_store()'s bare runtime bootstrap, PRAGMA user_version == 0) is
    the ordinary "older install missing a later migration" case — absence
    is legitimate and must not be reported as residual."""
    store = make_store(str(tmp_path / "facts.db"))
    store.store_fact(_fact("f_outbox_bare"))
    with store._db() as conn:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 0
        assert store._table_exists(conn, "projection_outbox") is False

    result = store.erase_fact_dependents_atomic("f_outbox_bare")

    assert result["tables"]["projection_outbox"] == {"applicable": False, "deleted": 0}
    assert store.same_db_dependents_present("f_outbox_bare") is False


def test_schema_version_20_with_missing_table_fails_closed_not_silently_clean(tmp_path):
    """Adversarial/corruption shape: the migration runner's own bookkeeping
    (PRAGMA user_version) claims migration 020 is applied, but the table
    itself is absent (e.g. dropped out-of-band). This must never be
    silently treated as "no residual" — it fails CLOSED.

    The fact is erased first (cleaning every OTHER same-DB dependent,
    including facts_fts, which would otherwise independently make
    same_db_dependents_present() return True and mask whether the
    version-gated check itself is actually doing anything) so the only
    remaining residual signal possible is the missing-but-activated
    projection_outbox table."""
    store = make_store(str(tmp_path / "facts.db"))
    fact_id = "f_outbox_corrupt"
    store.store_fact(_fact(fact_id))
    store.erase_fact_dependents_atomic(fact_id)
    assert store.same_db_dependents_present(fact_id) is False, (
        "sanity check: no unrelated dependent must already be residual "
        "before PRAGMA user_version is bumped"
    )

    with store._db() as conn:
        conn.execute("PRAGMA user_version = 20")
        conn.commit()
        assert store._table_exists(conn, "projection_outbox") is False

    assert store.same_db_dependents_present(fact_id) is True, (
        "PRAGMA user_version >= 20 with projection_outbox missing must "
        "fail closed, never be treated as a clean absence"
    )


# ── G. Rows for a different aggregate_id are never deleted ─────────────────

def test_other_aggregate_id_outbox_rows_are_untouched(migrated_store):
    store = migrated_store
    store.store_fact(_fact("f_outbox_target"))
    store.store_fact(_fact("f_outbox_other"))
    with store._db() as conn:
        _insert_outbox_row(conn, outbox_id="ob_target", aggregate_id="f_outbox_target")
        _insert_outbox_row(conn, outbox_id="ob_other", aggregate_id="f_outbox_other")
        conn.commit()

    result = store.erase_fact_dependents_atomic("f_outbox_target")

    assert result["tables"]["projection_outbox"] == {"applicable": True, "deleted": 1}
    with store._db() as conn:
        survivor = conn.execute(
            "SELECT aggregate_id FROM projection_outbox"
        ).fetchall()
    assert [r[0] for r in survivor] == ["f_outbox_other"]
