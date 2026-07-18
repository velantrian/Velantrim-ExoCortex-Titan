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
