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
    db_path=... constructor argument should ever touch."""
    global_db = make_store(str(tmp_path / "global.db"))
    monkeypatch.setattr(memory, "_GLOBAL_STORE", global_db)
    tenant_db_path = str(tmp_path / "tenant.db")
    return global_db, tenant_db_path


def test_forget_all_only_touches_configured_tenant_db(two_dbs):
    """C + D: forget_all() on a tenant-scoped engine must erase only
    tenant.db's matching facts — global.db (the process-global store) must
    remain completely unchanged."""
    global_db, tenant_db_path = two_dbs
    global_db.store_fact(_fact("f_global"))

    tenant_store = make_store(tenant_db_path)
    tenant_store.store_fact(_fact("f_tenant"))

    engine = forgetting_mod.ForgettingEngine(db_path=tenant_db_path)
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
    global_db, tenant_db_path = two_dbs
    tenant_store = make_store(tenant_db_path)
    tenant_store.store_fact(_fact("f_tenant"))

    engine = forgetting_mod.ForgettingEngine(db_path=tenant_db_path)
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
    global_db, tenant_db_path = two_dbs
    global_db.store_fact(_fact("f_global"))
    tenant_store = make_store(tenant_db_path)
    tenant_store.store_fact(_fact("f_tenant"))

    engine = forgetting_mod.ForgettingEngine(db_path=tenant_db_path)
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
    global_db, tenant_db_path = two_dbs
    global_db.store_fact(_fact("f_global"))  # matches userA, but lives in global.db
    # tenant.db exists (schema bootstrapped) but has no facts rows for userA
    # — mirrors scripts/apply_migrations.py's own DDL-trigger pattern
    # (SQLiteGraphStore's `facts` table is created lazily on first access).
    make_store(tenant_db_path).get_fact("__ddl_trigger__")

    engine = forgetting_mod.ForgettingEngine(db_path=tenant_db_path)
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

    global_db, tenant_db_path = two_dbs
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

    engine = forgetting_mod.ForgettingEngine(db_path=tenant_db_path)
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
    global_db, _ = two_dbs
    import os

    virgin_path = os.path.join(os.path.dirname(global_db.db_path), "virgin.db")
    assert not os.path.exists(virgin_path)

    engine = forgetting_mod.ForgettingEngine(db_path=virgin_path)
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
    global_db, _ = two_dbs
    import os

    virgin_path = os.path.join(os.path.dirname(global_db.db_path), "virgin_dry.db")
    assert not os.path.exists(virgin_path)

    engine = forgetting_mod.ForgettingEngine(db_path=virgin_path)
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

    global_db, _ = two_dbs
    virgin_path = os.path.join(os.path.dirname(global_db.db_path), "virgin_close.db")

    closed_paths: list[str] = []
    real_close = memory_mod.SQLiteGraphStore.close

    def _tracking_close(self):
        closed_paths.append(self.db_path)
        return real_close(self)

    monkeypatch.setattr(memory_mod.SQLiteGraphStore, "close", _tracking_close)

    engine = forgetting_mod.ForgettingEngine(db_path=virgin_path)
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
    global_db, _ = two_dbs
    import os

    corrupt_path = os.path.join(os.path.dirname(global_db.db_path), "corrupt.db")
    with open(corrupt_path, "wb") as f:
        f.write(b"this is not a sqlite database file, just garbage bytes\x00\x01\x02")

    engine = forgetting_mod.ForgettingEngine(db_path=corrupt_path)
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
    _, tenant_db_path = two_dbs
    tenant_store = make_store(tenant_db_path)
    tenant_store.store_fact(_fact("f_conflict", source="userA"))
    _insert_conflicting_job(tenant_store, fact_id="f_conflict", subject_user_id="userB")

    engine = forgetting_mod.ForgettingEngine(db_path=tenant_db_path)
    with pytest.deprecated_call():
        verdict = engine.forget_all(user_id="userA", reason="dsr", actor="api:newoperator")

    assert verdict.allowed is False
    assert verdict.reason == "subject_conflict"


def test_legacy_forget_verdict_allows_only_completed_erasure(two_dbs):
    """2: a fully COMPLETE batch (no conflict, no critical finding) still
    returns allowed=True — the fix must not regress the ordinary
    successful path."""
    _, tenant_db_path = two_dbs
    tenant_store = make_store(tenant_db_path)
    tenant_store.store_fact(_fact("f_ok", source="userA"))

    engine = forgetting_mod.ForgettingEngine(db_path=tenant_db_path)
    with pytest.deprecated_call():
        verdict = engine.forget_all(user_id="userA", reason="dsr", actor="tester")

    assert verdict.allowed is True
    assert verdict.reason == "complete"


def test_legacy_forget_verdict_rejects_critical_compliance_violation(two_dbs):
    """3: a batch whose execution outcome is COMPLETE but whose
    compliance_status is CRITICAL_COMPLIANCE_VIOLATION must still return
    allowed=False — terminality (and even a COMPLETE execution outcome)
    is never enough on its own."""
    _, tenant_db_path = two_dbs
    tenant_store = make_store(tenant_db_path)
    tenant_store.store_fact(_fact("f_critical", source="userA"))
    with tenant_store._db() as conn:
        conn.execute(
            "UPDATE facts SET epistemic_state = 'ImmutableCore' WHERE fact_id = ?",
            ("f_critical",),
        )
        conn.commit()

    engine = forgetting_mod.ForgettingEngine(db_path=tenant_db_path)
    with pytest.deprecated_call():
        verdict = engine.forget_all(user_id="userA", reason="dsr", actor="tester")

    assert verdict.allowed is False


def test_legacy_forget_verdict_does_not_equate_terminal_with_allowed(two_dbs):
    """4: a still-retryable (PARTIAL) batch — here produced by a live
    RUNNING per-fact job with subject_user_id still NULL (Round 5.4
    finding 4) — must return allowed=False, never True."""
    import time

    from core.erasure_coordinator import ErasureCoordinator

    _, tenant_db_path = two_dbs
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

    engine = forgetting_mod.ForgettingEngine(db_path=tenant_db_path)
    with pytest.deprecated_call():
        verdict = engine.forget_all(user_id="userA", reason="dsr", actor="tester")

    assert verdict.allowed is False
    assert verdict.reason == "partial"
