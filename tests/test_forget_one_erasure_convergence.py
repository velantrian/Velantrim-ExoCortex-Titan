"""Focused regression tests for issue #279.

The legacy ForgettingEngine.forget_one() API must remain a compatibility
surface only. Physical single-fact erasure is owned by ErasureCoordinator.
These tests use real temporary SQLite databases for the integration/isolation
proofs and only mock the coordinator for explicit legacy-result mapping tests.
"""
from __future__ import annotations

import inspect
import sqlite3

import pytest

from core import memory
from core.erasure_coordinator import (
    FAILED,
    PARTIAL,
    RESIDUAL_IMMUTABLE_DATA,
    SUBJECT_CONFLICT,
    ErasureCoordinator,
)
from core.forgetting import ForgettingEngine
from core.memory import make_store


def _fact(fact_id: str, *, source: str = "userA") -> dict[str, object]:
    return {
        "fact_id": fact_id,
        "claim": "some claim",
        "source": source,
        "confidence": 0.9,
    }


def _tenant_engine(tmp_path, db_path: str) -> ForgettingEngine:
    return ForgettingEngine(
        db_path=db_path,
        embedding_db_path=str(tmp_path / "tenant_embeddings.db"),
        ngram_db_path=str(tmp_path / "tenant_ngram.db"),
    )


def test_forget_one_uses_durable_coordinator_and_preserves_tenant_isolation(
    tmp_path, monkeypatch
):
    """A tenant-scoped erase must touch only that tenant and leave durable proof."""
    global_store = make_store(str(tmp_path / "global.db"))
    monkeypatch.setattr(memory, "_GLOBAL_STORE", global_store)
    global_store.store_fact(_fact("f_global"))

    tenant_db_path = str(tmp_path / "tenant.db")
    tenant_store = make_store(tenant_db_path)
    tenant_store.store_fact(_fact("f_tenant"))

    engine = _tenant_engine(tmp_path, tenant_db_path)
    verdict = engine.forget_one("f_tenant", user_id="userA", reason="dsr")

    assert verdict.allowed is True
    assert verdict.reason == "deleted"
    assert verdict.affected_facts == 1

    assert make_store(tenant_db_path).get_fact("f_tenant") is None
    assert global_store.get_fact("f_global") is not None

    with sqlite3.connect(tenant_db_path) as conn:
        job = conn.execute(
            "SELECT status, actor, subject_user_id FROM erasure_jobs WHERE fact_id = ?",
            ("f_tenant",),
        ).fetchone()
        tombstone = conn.execute(
            "SELECT user_id, reason FROM erasure_log WHERE fact_id = ?",
            ("f_tenant",),
        ).fetchone()

    assert job == ("COMPLETE", "userA", "userA")
    assert tombstone == ("userA", "dsr")


def test_forget_one_repeat_reuses_durable_completion_without_second_job(tmp_path):
    """A repeated request must reuse the completed generation, not delete again."""
    tenant_db_path = str(tmp_path / "tenant.db")
    tenant_store = make_store(tenant_db_path)
    tenant_store.store_fact(_fact("f_repeat"))
    engine = _tenant_engine(tmp_path, tenant_db_path)

    first = engine.forget_one("f_repeat", user_id="userA", reason="dsr")
    second = engine.forget_one("f_repeat", user_id="userA", reason="dsr")

    assert first.allowed is True
    assert first.reason == "deleted"
    assert first.affected_facts == 1
    assert second.allowed is True
    assert second.reason == "already_deleted"
    assert second.affected_facts == 0

    with sqlite3.connect(tenant_db_path) as conn:
        job_count = conn.execute(
            "SELECT COUNT(*) FROM erasure_jobs WHERE fact_id = ?", ("f_repeat",)
        ).fetchone()[0]
        tombstone_count = conn.execute(
            "SELECT COUNT(*) FROM erasure_log WHERE fact_id = ?", ("f_repeat",)
        ).fetchone()[0]

    assert job_count == 1
    assert tombstone_count == 1


def test_forget_one_not_found_creates_no_durable_job(tmp_path):
    tenant_db_path = str(tmp_path / "tenant.db")
    store = make_store(tenant_db_path)
    store.ensure_schema()
    engine = _tenant_engine(tmp_path, tenant_db_path)

    verdict = engine.forget_one("missing", user_id="userA", reason="dsr")

    assert verdict.allowed is False
    assert verdict.reason == "fact_not_found"
    with sqlite3.connect(tenant_db_path) as conn:
        job_count = conn.execute("SELECT COUNT(*) FROM erasure_jobs").fetchone()[0]
    assert job_count == 0


def test_forget_one_ring_zero_denial_happens_before_opening_tenant_store(tmp_path):
    tenant_db_path = str(tmp_path / "tenant.db")
    engine = _tenant_engine(tmp_path, tenant_db_path)

    verdict = engine.forget_one("RING_ZERO", user_id="userA", reason="dsr")

    assert verdict.allowed is False
    assert verdict.reason == "immutable_fact_protected"
    assert not (tmp_path / "tenant.db").exists()
    assert not (tmp_path / "tenant_embeddings.db").exists()
    assert not (tmp_path / "tenant_ngram.db").exists()


def test_forget_one_has_no_independent_raw_fact_delete():
    source = inspect.getsource(ForgettingEngine.forget_one)
    assert "erase_fact_durable" in source
    assert "DELETE FROM facts" not in source
    assert "DROP TRIGGER" not in source


@pytest.mark.parametrize(
    ("outcome", "residual"),
    [
        (PARTIAL, "undetermined"),
        (FAILED, None),
        (RESIDUAL_IMMUTABLE_DATA, "raw_original_present"),
        (SUBJECT_CONFLICT, None),
    ],
)
def test_forget_one_never_maps_non_complete_durable_outcome_to_success(
    tmp_path, monkeypatch, outcome, residual
):
    """Legacy compatibility must not turn PARTIAL/FAILED/residual/conflict into success."""
    tenant_db_path = str(tmp_path / "tenant.db")
    tenant_store = make_store(tenant_db_path)
    tenant_store.store_fact(_fact("f_pending"))

    def _report_only(self, fact_id, *, reason, actor, subject_user_id=None):
        return {
            "fact_id": fact_id,
            "job_id": "erase_job_test",
            "outcome": outcome,
            "erased_now": False,
            "residual": residual,
            "reason": reason,
            "actor": actor,
            "subject_user_id": subject_user_id,
            "content_hash": None,
            "erased_at": None,
            "steps": {},
        }

    monkeypatch.setattr(ErasureCoordinator, "erase_fact_durable", _report_only)
    engine = _tenant_engine(tmp_path, tenant_db_path)

    verdict = engine.forget_one("f_pending", user_id="userA", reason="dsr")

    assert verdict.allowed is False
    assert verdict.reason == outcome.lower()
    assert verdict.affected_facts == 0
    assert make_store(tenant_db_path).get_fact("f_pending") is not None
