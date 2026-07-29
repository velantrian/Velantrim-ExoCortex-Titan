"""Round 5 fix (Codex P2): ForgettingEngine.forget_all() must honor
self._db_path.

The deprecated forget_all() compatibility shim used to delegate to
core.erasure_batch_coordinator's module-level forget_all_durable()/
get_batch_coordinator() singleton — both always operate on the
process-global memory._GLOBAL_STORE, regardless of what `db_path` the
ForgettingEngine instance was constructed with. A caller doing
ForgettingEngine(db_path="tenant.db").forget_all(...) therefore ran the
operation against the GLOBAL database: it could report success (or zero
matching items) while "tenant.db" was never touched.

Every test here constructs two REAL, separate, temp-file-backed SQLite
databases (a "global" one patched in as memory._GLOBAL_STORE, and a
"tenant" one passed explicitly via db_path) — no fakes/mocks — and proves
isolation by querying both files directly afterward.
"""
from __future__ import annotations

import sqlite3

import pytest

from core import forgetting as forgetting_mod
from core import memory
from core.memory import make_store


def _fact(fid, source="userA"):
    return {"fact_id": fid, "claim": "some claim", "source": source, "confidence": 0.9}


@pytest.fixture
def two_dbs(tmp_path, monkeypatch):
    """global_db is wired in as the process-global singleton; tenant_db_path
    is a second, independent SQLite file that only ForgettingEngine's own
    db_path=... constructor argument should ever touch. tenant_embedding_path
    (Round 5.4 sixth-order fix, Codex P2) is a third, also-tenant-scoped
    SQLite file for the embeddings backend; tenant_ngram_path (Round 5.4
    seventh-order fix, Codex P2) is a fourth for the ngram FTS5 index — a
    custom db_path now requires explicit embedding_db_path=/embedding_store=
    AND ngram_db_path=/ngram_index=, so every test that constructs a
    tenant-scoped ForgettingEngine passes both."""
    global_db = make_store(str(tmp_path / "global.db"))
    monkeypatch.setattr(memory, "_GLOBAL_STORE", global_db)
    tenant_db_path = str(tmp_path / "tenant.db")
    tenant_embedding_path = str(tmp_path / "tenant_embeddings.db")
    tenant_ngram_path = str(tmp_path / "tenant_ngram.db")
    return global_db, tenant_db_path, tenant_embedding_path, tenant_ngram_path


def test_forget_all_only_touches_configured_tenant_db(two_dbs):
    """C + D: forget_all() on a tenant-scoped engine must erase only
    tenant.db's matching facts — global.db (the process-global store) must
    remain completely unchanged."""
    global_db, tenant_db_path, tenant_embedding_path, tenant_ngram_path = two_dbs
    global_db.store_fact(_fact("f_global"))

    tenant_store = make_store(tenant_db_path)
    tenant_store.store_fact(_fact("f_tenant"))

    engine = forgetting_mod.ForgettingEngine(
        db_path=tenant_db_path, embedding_db_path=tenant_embedding_path,
        ngram_db_path=tenant_ngram_path,
    )
    with pytest.deprecated_call():
        verdict = engine.forget_all(user_id="userA", reason="dsr")

    assert verdict.allowed is True
    assert verdict.affected_facts == 1

    # Read back via a FRESH SQLiteGraphStore against the same file, not
    # `tenant_store` itself — that object's own in-process L0 read-cache
    # has no way to know about a DELETE committed through the shim's
    # separate store instance (a pre-existing, per-instance-cache
    # characteristic of this codebase, not part of this fix's scope).
    assert make_store(tenant_db_path).get_fact("f_tenant") is None
    assert global_db.get_fact("f_global") is not None


def test_forget_all_batch_registry_written_to_tenant_db_only(two_dbs):
    """D: the durable batch registry (erasure_batches) must be written to
    tenant.db — never accidentally created/populated on global.db."""
    global_db, tenant_db_path, tenant_embedding_path, tenant_ngram_path = two_dbs
    tenant_store = make_store(tenant_db_path)
    tenant_store.store_fact(_fact("f_tenant"))

    engine = forgetting_mod.ForgettingEngine(
        db_path=tenant_db_path, embedding_db_path=tenant_embedding_path,
        ngram_db_path=tenant_ngram_path,
    )
    with pytest.deprecated_call():
        engine.forget_all(user_id="userA", reason="dsr")

    with sqlite3.connect(tenant_db_path) as conn:
        tenant_count = conn.execute("SELECT COUNT(*) FROM erasure_batches").fetchone()[0]
    assert tenant_count == 1

    with sqlite3.connect(global_db.db_path) as conn:
        has_table = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='erasure_batches'"
        ).fetchone()
        global_count = (
            conn.execute("SELECT COUNT(*) FROM erasure_batches").fetchone()[0]
            if has_table else 0
        )
    assert global_count == 0


def test_forget_all_dry_run_sees_only_tenant_db(two_dbs):
    """E: dry_run=True must preview only tenant.db's matching facts and
    must not inspect or act on global.db — and, being a dry run, must not
    delete anything from either."""
    global_db, tenant_db_path, tenant_embedding_path, tenant_ngram_path = two_dbs
    global_db.store_fact(_fact("f_global"))
    tenant_store = make_store(tenant_db_path)
    tenant_store.store_fact(_fact("f_tenant"))

    engine = forgetting_mod.ForgettingEngine(
        db_path=tenant_db_path, embedding_db_path=tenant_embedding_path,
        ngram_db_path=tenant_ngram_path,
    )
    with pytest.deprecated_call():
        verdict = engine.forget_all(user_id="userA", reason="dsr", dry_run=True)

    assert verdict.allowed is True
    assert verdict.reason == "dry_run"
    assert verdict.affected_facts == 1  # only f_tenant, never f_global

    assert tenant_store.get_fact("f_tenant") is not None  # dry-run: nothing deleted
    assert global_db.get_fact("f_global") is not None


def test_forget_all_empty_tenant_db_reports_zero_and_ignores_global_matches(two_dbs):
    """F: an empty tenant DB reports zero tenant items, even though a
    same-user_id-matching fact genuinely exists in the (wrong) global DB —
    it must never be picked up from there."""
    global_db, tenant_db_path, tenant_embedding_path, tenant_ngram_path = two_dbs
    global_db.store_fact(_fact("f_global"))  # matches userA, but lives in global.db
    # tenant.db exists (schema bootstrapped) but has no facts rows for userA
    # — mirrors scripts/apply_migrations.py's own DDL-trigger pattern
    # (SQLiteGraphStore's `facts` table is created lazily on first access).
    make_store(tenant_db_path).get_fact("__ddl_trigger__")

    engine = forgetting_mod.ForgettingEngine(
        db_path=tenant_db_path, embedding_db_path=tenant_embedding_path,
        ngram_db_path=tenant_ngram_path,
    )
    with pytest.deprecated_call():
        verdict = engine.forget_all(user_id="userA", reason="dsr")

    assert verdict.affected_facts == 0
    assert global_db.get_fact("f_global") is not None  # untouched


def test_forget_all_closes_temporary_store_even_on_failure(two_dbs, monkeypatch):
    """G: the shim's own temporary SQLiteGraphStore/connection must be
    closed via try/finally even when forget_all_durable() raises — no
    leaked SQLite connection, and never a close() call against the shared
    global store.

    core.forgetting.ForgettingEngine.forget_all() imports SQLiteGraphStore/
    BatchErasureCoordinator LAZILY (inside the method body), so it always
    resolves them against sys.modules at CALL time. Some other test
    elsewhere in the full suite (e.g. test_cognitive_fact.py's `client`
    fixture, which deletes every `core.*` entry from sys.modules and
    re-imports `server` fresh to get a clean FastAPI app) can leave this
    test file's own OWN top-level `from core import memory` binding
    pointing at a stale, already-replaced module object. Patching THAT
    stale class would silently miss the actual class the shim uses —
    re-import both modules fresh, right here, immediately before patching,
    so this test always patches whatever core.forgetting's own lazy
    imports will resolve to moments later.
    """
    import core.erasure_batch_coordinator as ebc_mod
    import core.memory as memory_mod

    global_db, tenant_db_path, tenant_embedding_path, tenant_ngram_path = two_dbs
    make_store(tenant_db_path)

    closed_paths: list[str] = []
    real_close = memory_mod.SQLiteGraphStore.close

    def _tracking_close(self):
        closed_paths.append(self.db_path)
        return real_close(self)

    monkeypatch.setattr(memory_mod.SQLiteGraphStore, "close", _tracking_close)

    def _boom(self, *args, **kwargs):
        raise RuntimeError("simulated failure")

    monkeypatch.setattr(ebc_mod.BatchErasureCoordinator, "forget_all_durable", _boom)

    engine = forgetting_mod.ForgettingEngine(
        db_path=tenant_db_path, embedding_db_path=tenant_embedding_path,
        ngram_db_path=tenant_ngram_path,
    )
    with pytest.deprecated_call():
        with pytest.raises(RuntimeError):
            engine.forget_all(user_id="userA", reason="dsr")

    assert closed_paths == [tenant_db_path]  # only the shim's own temp store
    assert global_db.db_path not in closed_paths  # never the shared global store


# ── Round 5.2 fix (Codex P2): initialize a virgin tenant DB before ──────────
# snapshotting. SQLiteGraphStore's DDL is lazy (triggered on first _db()
# use) — but BatchErasureCoordinator._create_batch_snapshot() queries
# `facts` through its OWN raw connection, never through the `store` object,
# so a truly new/nonexistent db_path never got that lazy trigger. The fix
# is store.ensure_schema() — one explicit, deterministic call — invoked by
# the shim before either coordinator is constructed.

def test_forget_all_initializes_virgin_tenant_database(two_dbs):
    """1: a db_path pointing to a file that does not yet exist must be
    initialized (not raise OperationalError), and return a valid
    zero-item result."""
    global_db, _, tenant_embedding_path, tenant_ngram_path = two_dbs
    import os

    virgin_path = os.path.join(os.path.dirname(global_db.db_path), "virgin.db")
    assert not os.path.exists(virgin_path)

    engine = forgetting_mod.ForgettingEngine(
        db_path=virgin_path, embedding_db_path=tenant_embedding_path,
        ngram_db_path=tenant_ngram_path,
    )
    with pytest.deprecated_call():
        verdict = engine.forget_all(user_id="userA", reason="dsr")

    assert verdict.affected_facts == 0
    assert os.path.exists(virgin_path)
    with sqlite3.connect(virgin_path) as conn:
        has_facts = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='facts'"
        ).fetchone()
    assert has_facts is not None
    # The global store must never have been consulted for this virgin
    # tenant's request.
    assert global_db.get_fact("f_global") is None  # nothing stored there either


def test_forget_all_dry_run_on_virgin_database_returns_zero(two_dbs):
    """2: dry_run=True against a virgin (nonexistent-file) tenant database
    must return zero matching facts and must not raise — and, following
    the existing dry-run contract (_preview() never touches
    erasure_batches), must create no durable batch row."""
    global_db, _, tenant_embedding_path, tenant_ngram_path = two_dbs
    import os

    virgin_path = os.path.join(os.path.dirname(global_db.db_path), "virgin_dry.db")
    assert not os.path.exists(virgin_path)

    engine = forgetting_mod.ForgettingEngine(
        db_path=virgin_path, embedding_db_path=tenant_embedding_path,
        ngram_db_path=tenant_ngram_path,
    )
    with pytest.deprecated_call():
        verdict = engine.forget_all(user_id="userA", reason="dsr", dry_run=True)

    assert verdict.allowed is True
    assert verdict.reason == "dry_run"
    assert verdict.affected_facts == 0

    with sqlite3.connect(virgin_path) as conn:
        has_batches_table = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='erasure_batches'"
        ).fetchone()
        batch_count = (
            conn.execute("SELECT COUNT(*) FROM erasure_batches").fetchone()[0]
            if has_batches_table else 0
        )
    assert batch_count == 0


def test_forget_all_virgin_database_closes_temporary_store(two_dbs, monkeypatch):
    """4: the temporary tenant store must still be closed after the virgin-
    database path, exactly like the pre-existing (non-virgin) case."""
    import os

    import core.memory as memory_mod

    global_db, _, tenant_embedding_path, tenant_ngram_path = two_dbs
    virgin_path = os.path.join(os.path.dirname(global_db.db_path), "virgin_close.db")

    closed_paths: list[str] = []
    real_close = memory_mod.SQLiteGraphStore.close

    def _tracking_close(self):
        closed_paths.append(self.db_path)
        return real_close(self)

    monkeypatch.setattr(memory_mod.SQLiteGraphStore, "close", _tracking_close)

    engine = forgetting_mod.ForgettingEngine(
        db_path=virgin_path, embedding_db_path=tenant_embedding_path,
        ngram_db_path=tenant_ngram_path,
    )
    with pytest.deprecated_call():
        engine.forget_all(user_id="userA", reason="dsr")

    assert closed_paths == [virgin_path]


# ── Round 5.3 Codex finding (P2): runtime schema parity for tenant DBs ──────
# SQLiteGraphStore.ensure_schema()/_db() only ever created the bare
# erasure_log table + its plain indexes. It never created the append-only
# triggers (migration 012), the erasure_log_subject_corrections table
# (migration 016), or the correction-aware erasure_audit VIEW (migration
# 016) — so a virgin/tenant DB initialized ONLY through this runtime path
# (no scripts/apply_migrations.py ever run against it) supported durable
# tombstone writes but NOT durable, correction-aware audit reads: querying
# erasure_audit raised OperationalError: no such view, and the append-only
# guarantee was unenforced. These tests prove parity with a fully migrated
# database.

def test_virgin_tenant_schema_contains_erasure_audit_view(tmp_path):
    """A brand-new tenant DB, initialized only via ensure_schema() (no
    migration runner), must already have the erasure_audit view — not just
    the raw erasure_log table."""
    virgin_path = str(tmp_path / "virgin_audit.db")
    store = make_store(virgin_path)
    store.ensure_schema()

    with sqlite3.connect(virgin_path) as conn:
        view_row = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='view' AND name='erasure_audit'"
        ).fetchone()
        corrections_row = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' "
            "AND name='erasure_log_subject_corrections'"
        ).fetchone()

    assert view_row is not None
    assert "corrected_user_id" in view_row[0]
    assert corrections_row is not None


def test_virgin_tenant_erasure_is_immediately_auditable(tmp_path):
    """A tombstone written on a virgin tenant DB must be readable through
    erasure_audit immediately — the same query core.forgetting.
    ForgettingEngine.get_erasure_log() runs — with no migration step in
    between."""
    virgin_path = str(tmp_path / "virgin_readable.db")
    store = make_store(virgin_path)
    store.write_tombstone(
        "f1", reason="dsr", actor="userA", content_hash="deadbeef"
    )

    with sqlite3.connect(virgin_path) as conn:
        rows = conn.execute(
            "SELECT user_id FROM erasure_audit WHERE user_id = ?", ("userA",)
        ).fetchall()

    assert rows == [("userA",)]


def test_runtime_and_migrated_erasure_audit_schema_are_equivalent(tmp_path):
    """The set of columns exposed by erasure_audit, and the append-only
    trigger names guarding erasure_log/erasure_log_subject_corrections,
    must be identical whether the DB was built by the runtime DDL path or
    by running scripts/apply_migrations.py from scratch."""
    import scripts.apply_migrations as am

    runtime_path = str(tmp_path / "runtime.db")
    make_store(runtime_path).ensure_schema()

    migrated_path = tmp_path / "migrated.db"
    am.apply_migrations(migrated_path)
    migrated_path = str(migrated_path)

    def _schema_fingerprint(db_path):
        with sqlite3.connect(db_path) as conn:
            view_cols = tuple(r[1] for r in conn.execute("PRAGMA table_info(erasure_audit)"))
            triggers = frozenset(
                r[0] for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='trigger' "
                    "AND name IN ("
                    "'prevent_erasure_delete', 'prevent_erasure_update', "
                    "'prevent_erasure_log_subject_corrections_delete', "
                    "'prevent_erasure_log_subject_corrections_update')"
                )
            )
        return view_cols, triggers

    runtime_cols, runtime_triggers = _schema_fingerprint(runtime_path)
    migrated_cols, migrated_triggers = _schema_fingerprint(migrated_path)
    assert (runtime_cols, runtime_triggers) == (migrated_cols, migrated_triggers)
    assert len(runtime_triggers) == 4


def test_tenant_correction_table_is_append_only(tmp_path):
    """The runtime-created erasure_log_subject_corrections table must
    enforce the same append-only guarantee as the migrated one — direct
    UPDATE/DELETE must raise, not silently succeed."""
    virgin_path = str(tmp_path / "virgin_guard.db")
    store = make_store(virgin_path)
    store.write_tombstone(
        "f1", reason="dsr", actor="userA", content_hash="deadbeef"
    )

    with sqlite3.connect(virgin_path) as conn:
        erasure_id = conn.execute(
            "SELECT erasure_id FROM erasure_log WHERE fact_id = 'f1'"
        ).fetchone()[0]
        conn.execute(
            "INSERT INTO erasure_log_subject_corrections "
            "(correction_id, erasure_id, job_id, batch_id, corrected_user_id, "
            "original_user_id, created_at) "
            "VALUES ('c1', ?, NULL, 'b1', 'userB', 'userA', datetime('now'))",
            (erasure_id,),
        )
        conn.commit()

        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "UPDATE erasure_log_subject_corrections SET corrected_user_id = 'hacked' "
                "WHERE correction_id = 'c1'"
            )
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "DELETE FROM erasure_log_subject_corrections WHERE correction_id = 'c1'"
            )


def test_forget_all_does_not_mask_corrupt_tenant_database(two_dbs):
    """5: a genuinely malformed/corrupt database file must surface its
    real sqlite3 error — never be silently treated as "zero facts"."""
    global_db, _, tenant_embedding_path, tenant_ngram_path = two_dbs
    import os

    corrupt_path = os.path.join(os.path.dirname(global_db.db_path), "corrupt.db")
    with open(corrupt_path, "wb") as f:
        f.write(b"this is not a sqlite database file, just garbage bytes\x00\x01\x02")

    engine = forgetting_mod.ForgettingEngine(
        db_path=corrupt_path, embedding_db_path=tenant_embedding_path,
        ngram_db_path=tenant_ngram_path,
    )
    with pytest.deprecated_call():
        with pytest.raises(sqlite3.DatabaseError):
            engine.forget_all(user_id="userA", reason="dsr")


# ── Round 5.4 Codex finding (P2): keep subject conflicts (and other ─────────
# non-successful terminal outcomes) out of legacy ForgetVerdict.allowed.
# The deprecated shim used to map allowed=operation_finished (or
# outcome=="PARTIAL") — since SUBJECT_CONFLICT is terminal too (so it never
# auto-retries forever), that mapping reported allowed=True for a batch
# where the conflicting fact was never actually erased.

def _insert_conflicting_job(store, *, fact_id, subject_user_id, actor="other-operator"):
    """Pre-create a durable PENDING erasure_jobs row already bound to
    `subject_user_id` — simulates a fact_id whose per-fact job belongs to
    a DIFFERENT data subject than the batch about to process it."""
    import time

    from core.erasure_coordinator import ErasureCoordinator

    ErasureCoordinator(store=store)  # triggers erasure_jobs/_steps DDL
    job_id = f"erj_conflict_{fact_id}"
    now = time.strftime("%Y-%m-%dT%H:%M:%S")
    with store._db() as conn:
        conn.execute(
            "INSERT INTO erasure_jobs (job_id, fact_id, generation, reason, actor, "
            "subject_user_id, status, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (job_id, fact_id, 1, "legacy", actor, subject_user_id, "PENDING", now, now),
        )
        for step_name in ("determine_raw", "l1_same_db", "embeddings", "ngram"):
            conn.execute(
                "INSERT INTO erasure_job_steps (step_id, job_id, step_name, status) "
                "VALUES (?, ?, ?, ?)",
                (f"{job_id}_{step_name}", job_id, step_name, "PENDING"),
            )
        conn.commit()


def test_legacy_forget_verdict_rejects_terminal_subject_conflict(two_dbs):
    """1: a SUBJECT_CONFLICT batch must return ForgetVerdict.allowed=False
    — never True just because the batch reached a terminal state."""
    _, tenant_db_path, tenant_embedding_path, tenant_ngram_path = two_dbs
    tenant_store = make_store(tenant_db_path)
    tenant_store.store_fact(_fact("f_conflict", source="userA"))
    _insert_conflicting_job(tenant_store, fact_id="f_conflict", subject_user_id="userB")

    engine = forgetting_mod.ForgettingEngine(
        db_path=tenant_db_path, embedding_db_path=tenant_embedding_path,
        ngram_db_path=tenant_ngram_path,
    )
    with pytest.deprecated_call():
        verdict = engine.forget_all(user_id="userA", reason="dsr", actor="api:newoperator")

    assert verdict.allowed is False
    assert verdict.reason == "subject_conflict"


def test_legacy_forget_verdict_allows_only_completed_erasure(two_dbs):
    """2: a fully COMPLETE batch (no conflict, no critical finding) still
    returns allowed=True — the fix must not regress the ordinary
    successful path."""
    _, tenant_db_path, tenant_embedding_path, tenant_ngram_path = two_dbs
    tenant_store = make_store(tenant_db_path)
    tenant_store.store_fact(_fact("f_ok", source="userA"))

    engine = forgetting_mod.ForgettingEngine(
        db_path=tenant_db_path, embedding_db_path=tenant_embedding_path,
        ngram_db_path=tenant_ngram_path,
    )
    with pytest.deprecated_call():
        verdict = engine.forget_all(user_id="userA", reason="dsr", actor="tester")

    assert verdict.allowed is True
    assert verdict.reason == "complete"


def test_legacy_forget_verdict_rejects_critical_compliance_violation(two_dbs):
    """3: a batch whose execution outcome is COMPLETE but whose
    compliance_status is CRITICAL_COMPLIANCE_VIOLATION must still return
    allowed=False — terminality (and even a COMPLETE execution outcome)
    is never enough on its own."""
    _, tenant_db_path, tenant_embedding_path, tenant_ngram_path = two_dbs
    tenant_store = make_store(tenant_db_path)
    tenant_store.store_fact(_fact("f_critical", source="userA"))
    with tenant_store._db() as conn:
        conn.execute(
            "UPDATE facts SET epistemic_state = 'ImmutableCore' WHERE fact_id = ?",
            ("f_critical",),
        )
        conn.commit()

    engine = forgetting_mod.ForgettingEngine(
        db_path=tenant_db_path, embedding_db_path=tenant_embedding_path,
        ngram_db_path=tenant_ngram_path,
    )
    with pytest.deprecated_call():
        verdict = engine.forget_all(user_id="userA", reason="dsr", actor="tester")

    assert verdict.allowed is False


def test_legacy_forget_verdict_does_not_equate_terminal_with_allowed(two_dbs):
    """4: a still-retryable (PARTIAL) batch — here produced by a live
    RUNNING per-fact job with subject_user_id still NULL (Round 5.4
    finding 4) — must return allowed=False, never True."""
    import time

    from core.erasure_coordinator import ErasureCoordinator

    _, tenant_db_path, tenant_embedding_path, tenant_ngram_path = two_dbs
    tenant_store = make_store(tenant_db_path)
    tenant_store.store_fact(_fact("f_running", source="userA"))
    ErasureCoordinator(store=tenant_store)  # triggers erasure_jobs DDL

    job_id = "erj_running_f_running"
    now = time.strftime("%Y-%m-%dT%H:%M:%S")
    with tenant_store._db() as conn:
        conn.execute(
            "INSERT INTO erasure_jobs (job_id, fact_id, generation, reason, actor, "
            "subject_user_id, status, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (job_id, "f_running", 1, "legacy", "legacy-operator", None, "RUNNING", now, now),
        )
        conn.commit()

    engine = forgetting_mod.ForgettingEngine(
        db_path=tenant_db_path, embedding_db_path=tenant_embedding_path,
        ngram_db_path=tenant_ngram_path,
    )
    with pytest.deprecated_call():
        verdict = engine.forget_all(user_id="userA", reason="dsr", actor="tester")

    assert verdict.allowed is False
    assert verdict.reason == "partial"


# ── Round 5.4 sixth-order Codex finding (P2): bind tenant erasure to the ────
# tenant embedding store. A custom, non-global db_path left ErasureCoordinator
# with NO tenant-scoped embeddings backend — it lazily defaulted to the
# process-global EmbeddingStore(), completely unrelated to the tenant's own
# storage. A tenant's real gs_vectors row could then survive erasure
# undetected (checked against the wrong file) while the batch still reported
# COMPLETE — a GDPR Art. 17 false-success condition.

def test_tenant_forget_all_erases_tenant_facts_and_embeddings(two_dbs):
    """1: a real tenant fact + its real tenant embedding are BOTH erased,
    and the global embeddings DB is never touched."""
    global_db, tenant_db_path, tenant_embedding_path, tenant_ngram_path = two_dbs
    import numpy as np

    from core.embedding_store import EXOCORTEX_DB, EmbeddingStore

    tenant_store = make_store(tenant_db_path)
    tenant_store.store_fact(_fact("f_tenant"))

    tenant_embeddings = EmbeddingStore(tenant_embedding_path)
    tenant_embeddings.ensure_table()
    tenant_embeddings.store("f_tenant", np.array([0.1, 0.2, 0.3], dtype=np.float32))
    assert tenant_embeddings.has_any("f_tenant") is True

    # tests/conftest.py redirects the real global default (EXOCORTEX_DB) to
    # an isolated, session-fixed temp path — safe to open directly here.
    global_embeddings = EmbeddingStore(EXOCORTEX_DB)
    global_embeddings.ensure_table()

    engine = forgetting_mod.ForgettingEngine(
        db_path=tenant_db_path, embedding_db_path=tenant_embedding_path,
        ngram_db_path=tenant_ngram_path,
    )
    with pytest.deprecated_call():
        verdict = engine.forget_all(user_id="userA", reason="dsr")

    assert verdict.allowed is True
    assert verdict.affected_facts == 1
    assert make_store(tenant_db_path).get_fact("f_tenant") is None
    assert tenant_embeddings.has_any("f_tenant") is False
    assert global_embeddings.has_any("f_tenant") is False  # never had it; never touched


def test_tenant_erasure_does_not_use_global_embedding_store(two_dbs):
    """2: the SAME fact_id also has a row in the GLOBAL embeddings store
    (e.g. a coincidental collision, or a leftover from the bug this fix
    closes). Erasure must target the real TENANT row — never be satisfied
    by, and never mutate, the global one."""
    global_db, tenant_db_path, tenant_embedding_path, tenant_ngram_path = two_dbs
    import numpy as np

    from core.embedding_store import EXOCORTEX_DB, EmbeddingStore

    tenant_store = make_store(tenant_db_path)
    tenant_store.store_fact(_fact("f_dup"))

    tenant_embeddings = EmbeddingStore(tenant_embedding_path)
    tenant_embeddings.ensure_table()
    tenant_embeddings.store("f_dup", np.array([1.0, 2.0], dtype=np.float32))

    global_embeddings = EmbeddingStore(EXOCORTEX_DB)
    global_embeddings.ensure_table()
    global_embeddings.store("f_dup", np.array([9.0, 9.0], dtype=np.float32))

    engine = forgetting_mod.ForgettingEngine(
        db_path=tenant_db_path, embedding_db_path=tenant_embedding_path,
        ngram_db_path=tenant_ngram_path,
    )
    with pytest.deprecated_call():
        verdict = engine.forget_all(user_id="userA", reason="dsr")

    assert verdict.allowed is True
    assert tenant_embeddings.has_any("f_dup") is False  # the real tenant row purged
    assert global_embeddings.has_any("f_dup") is True  # the global row untouched


def test_custom_tenant_db_requires_explicit_embedding_store(two_dbs):
    """3: a custom tenant db_path with NO embedding configuration must fail
    closed — before any fact is touched, before any durable batch row is
    created — never a silent fall-back to the global embeddings store."""
    global_db, tenant_db_path, _, _ = two_dbs
    tenant_store = make_store(tenant_db_path)
    tenant_store.store_fact(_fact("f_tenant"))

    engine = forgetting_mod.ForgettingEngine(db_path=tenant_db_path)  # no embedding config
    with pytest.deprecated_call():
        with pytest.raises(ValueError, match="tenant embedding"):
            engine.forget_all(user_id="userA", reason="dsr")

    # No partial destructive mutation.
    assert make_store(tenant_db_path).get_fact("f_tenant") is not None
    with sqlite3.connect(tenant_db_path) as conn:
        has_table = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='erasure_batches'"
        ).fetchone()
        batch_count = (
            conn.execute("SELECT COUNT(*) FROM erasure_batches").fetchone()[0]
            if has_table else 0
        )
    assert batch_count == 0


def test_default_forgetting_engine_preserves_global_store_behavior(tmp_path, monkeypatch):
    """4: when db_path matches the (global) default, no embedding
    configuration is required — the pre-existing lazy-default behavior is
    preserved exactly. Uses a monkeypatched SQLITE_PATH pointed at a safe
    temp file rather than the real repo default, so this test never risks
    touching real project data."""
    safe_default_path = str(tmp_path / "would_be_global.db")
    monkeypatch.setattr(forgetting_mod, "SQLITE_PATH", safe_default_path)

    make_store(safe_default_path).store_fact(_fact("f1"))

    engine = forgetting_mod.ForgettingEngine(db_path=safe_default_path)
    with pytest.deprecated_call():
        verdict = engine.forget_all(user_id="userA", reason="dsr")

    assert verdict.allowed is True
    assert verdict.affected_facts == 1
    assert make_store(safe_default_path).get_fact("f1") is None


def test_forgetting_engine_does_not_close_injected_embedding_store(two_dbs, tmp_path, monkeypatch):
    """5a: an externally injected embedding_store must never be closed by
    forget_all() — its lifecycle belongs to whoever created/injected it."""
    global_db, tenant_db_path, _, tenant_ngram_path = two_dbs
    from core.embedding_store import EmbeddingStore

    tenant_store = make_store(tenant_db_path)
    tenant_store.store_fact(_fact("f1"))

    injected = EmbeddingStore(str(tmp_path / "injected_embeddings.db"))
    injected.ensure_table()

    closed = {"called": False}
    monkeypatch.setattr(injected, "close", lambda: closed.__setitem__("called", True))

    engine = forgetting_mod.ForgettingEngine(
        db_path=tenant_db_path, embedding_store=injected, ngram_db_path=tenant_ngram_path,
    )
    with pytest.deprecated_call():
        engine.forget_all(user_id="userA", reason="dsr")

    assert closed["called"] is False


def test_forgetting_engine_never_imports_embedding_store_for_path_only_dry_run(
    two_dbs, monkeypatch,
):
    """5b (Round 5.4 seventh-order fix, Codex P2): a path-only tenant
    embedding configuration (embedding_db_path=, not a real object) must
    never force core.embedding_store — and therefore numpy — to be
    importable for a dry-run, which never touches embeddings at all.
    Simulates core.embedding_store being genuinely unimportable (e.g. numpy
    missing) via sys.modules and proves dry_run still succeeds cleanly.

    This replaces the sixth-order version of this test
    (test_forgetting_engine_closes_internal_tenant_embedding_store_on_error):
    that test asserted forget_all() itself constructed-and-closed a real
    EmbeddingStore for the path-only case — exactly the eager construction
    this seventh-order fix removes, since merely IMPORTING the class (even
    to hold an unused instance) already forces the numpy dependency this
    fix exists to defer."""
    import sys

    global_db, tenant_db_path, tenant_embedding_path, tenant_ngram_path = two_dbs
    tenant_store = make_store(tenant_db_path)
    tenant_store.store_fact(_fact("f_tenant"))

    monkeypatch.setitem(sys.modules, "core.embedding_store", None)

    engine = forgetting_mod.ForgettingEngine(
        db_path=tenant_db_path, embedding_db_path=tenant_embedding_path,
        ngram_db_path=tenant_ngram_path,
    )
    with pytest.deprecated_call():
        verdict = engine.forget_all(user_id="userA", reason="dsr", dry_run=True)

    assert verdict.allowed is True
    assert verdict.reason == "dry_run"
    assert verdict.affected_facts == 1


def test_tenant_embedding_path_only_erasure_works_without_numpy(two_dbs, monkeypatch):
    """5c (Round 5.4 seventh-order fix, Codex P2): a REAL (non-dry-run)
    tenant erasure for a fact with NO embeddings row must also succeed
    even when core.embedding_store (numpy) cannot be imported at all.
    ErasureCoordinator's pre-existing stdlib-only no-row proof
    (_embeddings_row_present_for()) — now correctly scoped to the TENANT
    path via embedding_db_path (see core/erasure_coordinator.py) rather
    than the process-global default — makes this an honest, provable
    COMPLETE rather than a crash."""
    import sys

    global_db, tenant_db_path, tenant_embedding_path, tenant_ngram_path = two_dbs
    tenant_store = make_store(tenant_db_path)
    tenant_store.store_fact(_fact("f_no_embeddings"))

    monkeypatch.setitem(sys.modules, "core.embedding_store", None)

    engine = forgetting_mod.ForgettingEngine(
        db_path=tenant_db_path, embedding_db_path=tenant_embedding_path,
        ngram_db_path=tenant_ngram_path,
    )
    with pytest.deprecated_call():
        verdict = engine.forget_all(user_id="userA", reason="dsr")

    assert verdict.allowed is True
    assert verdict.affected_facts == 1
    assert make_store(tenant_db_path).get_fact("f_no_embeddings") is None


def test_blank_tenant_embedding_and_ngram_paths_fail_closed(two_dbs):
    """Round 5.4 seventh-order fix (Codex P2): a blank/whitespace-only
    tenant embedding or ngram path must be treated exactly like a missing
    one — never silently accepted. sqlite3.connect("") happily opens a
    throwaway temporary database, so an unnormalized blank path would let
    the tenant's real storage go unchecked while a scratch file reports a
    clean, empty result."""
    global_db, tenant_db_path, tenant_embedding_path, tenant_ngram_path = two_dbs
    tenant_store = make_store(tenant_db_path)
    tenant_store.store_fact(_fact("f_tenant"))

    blank_embedding_engine = forgetting_mod.ForgettingEngine(
        db_path=tenant_db_path, embedding_db_path="   ", ngram_db_path=tenant_ngram_path,
    )
    with pytest.deprecated_call():
        with pytest.raises(ValueError, match="tenant embedding"):
            blank_embedding_engine.forget_all(user_id="userA", reason="dsr")
    assert make_store(tenant_db_path).get_fact("f_tenant") is not None

    blank_ngram_engine = forgetting_mod.ForgettingEngine(
        db_path=tenant_db_path, embedding_db_path=tenant_embedding_path, ngram_db_path="",
    )
    with pytest.deprecated_call():
        with pytest.raises(ValueError, match="tenant ngram"):
            blank_ngram_engine.forget_all(user_id="userA", reason="dsr")
    assert make_store(tenant_db_path).get_fact("f_tenant") is not None


def test_custom_tenant_db_requires_explicit_ngram_index(two_dbs):
    """A custom tenant db_path with embeddings configured but NO ngram
    configuration must ALSO fail closed — before any fact is touched,
    mirroring test_custom_tenant_db_requires_explicit_embedding_store."""
    global_db, tenant_db_path, tenant_embedding_path, _ = two_dbs
    tenant_store = make_store(tenant_db_path)
    tenant_store.store_fact(_fact("f_tenant"))

    engine = forgetting_mod.ForgettingEngine(
        db_path=tenant_db_path, embedding_db_path=tenant_embedding_path,
    )  # no ngram config
    with pytest.deprecated_call():
        with pytest.raises(ValueError, match="tenant ngram"):
            engine.forget_all(user_id="userA", reason="dsr")

    assert make_store(tenant_db_path).get_fact("f_tenant") is not None


def test_tenant_forget_all_erases_tenant_ngram_index(two_dbs):
    """Round 5.4 seventh-order fix (Codex P2): a tenant fact indexed in
    its OWN ngram FTS5 index must have that index entry purged too — not
    just the (unrelated) global ngram index."""
    global_db, tenant_db_path, tenant_embedding_path, tenant_ngram_path = two_dbs
    from core.ngram_index import NGRAM_DB_PATH, NGramIndex

    tenant_store = make_store(tenant_db_path)
    tenant_store.store_fact(_fact("f_tenant"))

    tenant_ngram = NGramIndex(tenant_ngram_path)
    tenant_ngram.index("f_tenant", "some claim")
    assert tenant_ngram.contains("f_tenant") is True

    # tests/conftest.py redirects the real global default (VELANTRIM_NGRAM_DB)
    # to an isolated, session-fixed temp path — safe to open directly here.
    global_ngram = NGramIndex(NGRAM_DB_PATH)

    engine = forgetting_mod.ForgettingEngine(
        db_path=tenant_db_path, embedding_db_path=tenant_embedding_path,
        ngram_db_path=tenant_ngram_path,
    )
    with pytest.deprecated_call():
        verdict = engine.forget_all(user_id="userA", reason="dsr")

    assert verdict.allowed is True
    assert tenant_ngram.contains("f_tenant") is False
    assert global_ngram.contains("f_tenant") is False  # never had it; never touched


def test_tenant_ngram_erasure_does_not_use_global_ngram_index(two_dbs):
    """The SAME fact_id also has an entry in the GLOBAL ngram index.
    Erasure must target the real TENANT index entry — never be satisfied
    by, and never mutate, the global one."""
    global_db, tenant_db_path, tenant_embedding_path, tenant_ngram_path = two_dbs
    from core.ngram_index import NGRAM_DB_PATH, NGramIndex

    tenant_store = make_store(tenant_db_path)
    tenant_store.store_fact(_fact("f_dup"))

    tenant_ngram = NGramIndex(tenant_ngram_path)
    tenant_ngram.index("f_dup", "tenant claim text")

    global_ngram = NGramIndex(NGRAM_DB_PATH)
    global_ngram.index("f_dup", "global claim text")

    engine = forgetting_mod.ForgettingEngine(
        db_path=tenant_db_path, embedding_db_path=tenant_embedding_path,
        ngram_db_path=tenant_ngram_path,
    )
    with pytest.deprecated_call():
        verdict = engine.forget_all(user_id="userA", reason="dsr")

    assert verdict.allowed is True
    assert tenant_ngram.contains("f_dup") is False  # the real tenant entry purged
    assert global_ngram.contains("f_dup") is True  # the global entry untouched


def test_tenant_embedding_failure_prevents_complete_erasure(two_dbs, monkeypatch):
    """6: the tenant embeddings backend genuinely failing to delete must
    never let the batch report COMPLETE — the surviving vector stays a
    visible, retryable failure under the existing per-fact state contract,
    exactly like any other embeddings backend outage."""
    global_db, tenant_db_path, tenant_embedding_path, tenant_ngram_path = two_dbs
    import numpy as np

    import core.embedding_store as embedding_store_mod
    from core.embedding_store import EmbeddingStore

    tenant_store = make_store(tenant_db_path)
    tenant_store.store_fact(_fact("f_tenant"))

    tenant_embeddings = EmbeddingStore(tenant_embedding_path)
    tenant_embeddings.ensure_table()
    tenant_embeddings.store("f_tenant", np.array([1.0, 2.0], dtype=np.float32))

    def _flaky_purge_node(self, node_id):
        raise RuntimeError("simulated embeddings backend failure")

    monkeypatch.setattr(embedding_store_mod.EmbeddingStore, "purge_node", _flaky_purge_node)

    engine = forgetting_mod.ForgettingEngine(
        db_path=tenant_db_path, embedding_db_path=tenant_embedding_path,
        ngram_db_path=tenant_ngram_path,
    )
    with pytest.deprecated_call():
        verdict = engine.forget_all(user_id="userA", reason="dsr")

    assert verdict.allowed is False
    assert tenant_embeddings.has_any("f_tenant") is True  # never purged


# ═══════════════════════════════════════════════════════════════════════════════
# M2 (Claude audit 2026-07-28): forget_one() migrated to erase_fact_durable()
# ═══════════════════════════════════════════════════════════════════════════════
#
# forget_one() had zero production callers, but was never migrated the way
# forget_all() above was — it kept its own non-durable delete with per-table
# exceptions swallowed via bare `except: pass`, no embeddings/ngram cleanup,
# and a false-success report for a fact_id that never existed. These tests
# exercise the migrated shim the same way the forget_all() tests above
# exercise theirs.

def test_forget_one_only_touches_configured_tenant_db(two_dbs):
    """Tenant isolation must hold for forget_one() exactly like forget_all()
    above — a custom db_path must never reach into the global store."""
    global_db, tenant_db_path, tenant_embedding_path, tenant_ngram_path = two_dbs
    global_db.store_fact(_fact("f_global"))

    tenant_store = make_store(tenant_db_path)
    tenant_store.store_fact(_fact("f_tenant"))

    engine = forgetting_mod.ForgettingEngine(
        db_path=tenant_db_path, embedding_db_path=tenant_embedding_path,
        ngram_db_path=tenant_ngram_path,
    )
    with pytest.deprecated_call():
        verdict = engine.forget_one("f_tenant", user_id="userA", reason="dsr")

    assert verdict.allowed is True
    assert verdict.reason == "complete"
    assert make_store(tenant_db_path).get_fact("f_tenant") is None
    assert global_db.get_fact("f_global") is not None


def test_forget_one_actually_removes_fact_versions_history(two_dbs):
    """erase_fact_durable() purges fact_versions atomically as part of its
    erasure — prove the row is actually gone on the migrated path, not just
    that a truthy verdict came back. (The old code additionally never
    called ensure_schema() on this exact tenant db_path shape and would
    raise before even reaching its own — separately swallowed —
    fact_versions delete; see forget_one()'s docstring.)"""
    global_db, tenant_db_path, tenant_embedding_path, tenant_ngram_path = two_dbs

    tenant_store = make_store(tenant_db_path)
    tenant_store.store_fact(_fact("f_tenant", source="userA"))
    # A content-changing update creates a fact_versions row for the pre-image.
    tenant_store.store_fact(_fact("f_tenant", source="userA_updated"))

    with sqlite3.connect(tenant_db_path) as conn:
        before = conn.execute(
            "SELECT COUNT(*) FROM fact_versions WHERE fact_id = ?", ("f_tenant",)
        ).fetchone()[0]
    assert before > 0, "test setup did not actually create a fact_versions row"

    engine = forgetting_mod.ForgettingEngine(
        db_path=tenant_db_path, embedding_db_path=tenant_embedding_path,
        ngram_db_path=tenant_ngram_path,
    )
    with pytest.deprecated_call():
        verdict = engine.forget_one("f_tenant", user_id="userA", reason="dsr")

    assert verdict.allowed is True
    with sqlite3.connect(tenant_db_path) as conn:
        after = conn.execute(
            "SELECT COUNT(*) FROM fact_versions WHERE fact_id = ?", ("f_tenant",)
        ).fetchone()[0]
    assert after == 0, "fact_versions row survived forget_one() — PII still recoverable"


def test_forget_one_rejects_ring_zero_immutable_fact(two_dbs):
    """The old check() heuristic is replaced by the enforced
    memory.IMMUTABLE_FACT_IDS guard erase_fact_durable() raises on."""
    _, tenant_db_path, tenant_embedding_path, tenant_ngram_path = two_dbs

    tenant_store = make_store(tenant_db_path)
    tenant_store.store_fact(_fact("VALUES_CORE", source="system"))

    engine = forgetting_mod.ForgettingEngine(
        db_path=tenant_db_path, embedding_db_path=tenant_embedding_path,
        ngram_db_path=tenant_ngram_path,
    )
    with pytest.deprecated_call():
        verdict = engine.forget_one("VALUES_CORE", user_id="userA", reason="dsr")

    assert verdict.allowed is False
    assert verdict.reason == "immutable"
    assert make_store(tenant_db_path).get_fact("VALUES_CORE") is not None


def test_forget_one_reports_not_found_instead_of_false_success(two_dbs):
    """The old code inserted an erasure_log row and reported
    allowed=True/reason="deleted" even for a fact_id that never existed —
    a silent false success. The migrated shim must report it honestly."""
    _, tenant_db_path, tenant_embedding_path, tenant_ngram_path = two_dbs

    engine = forgetting_mod.ForgettingEngine(
        db_path=tenant_db_path, embedding_db_path=tenant_embedding_path,
        ngram_db_path=tenant_ngram_path,
    )
    with pytest.deprecated_call():
        verdict = engine.forget_one("never_existed", user_id="userA", reason="dsr")

    assert verdict.allowed is False
    assert verdict.reason == "not_found"


def test_log_forgetting_helper_was_removed_as_dead_code():
    """FIX #22 (Claude audit 2026-07-28): _log_forgetting() wrote a
    provenance_chain event on its own connection, non-atomic with the
    DELETE — but had zero callers once forget_one()/forget_all() were both
    migrated to the durable erasure_coordinator/erasure_batch_coordinator
    paths (whose own erasure_log write is already atomic within their
    saga). Tripwire so it isn't silently reintroduced without the same
    scrutiny applied here."""
    assert not hasattr(forgetting_mod.ForgettingEngine, "_log_forgetting")
