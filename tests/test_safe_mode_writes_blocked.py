"""Regression: MetaSupervisor SAFE_MODE must block L3 writes.

Closes the Critical audit finding: writes_blocked existed but was never
enforced on store_fact / transition_esm / invalidate_edge / batch paths.

Note: some tests (e.g. test_cognitive_fact) delete sys.modules['core.*'] and
reload them. All imports of meta_supervisor/write_gate here are therefore
done *inside* each test / fixture so we always patch the live module.
"""
from __future__ import annotations

import asyncio
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]


def _run_apply(db_path: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(REPO / "scripts" / "apply_migrations.py"),
            "--db",
            db_path,
            "--no-backup",
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO),
        check=False,
    )


@pytest.fixture
def store(tmp_path, monkeypatch):
    from core import memory

    db_path = str(tmp_path / "safe_mode.db")
    bootstrap = memory.SQLiteGraphStore(db_path)
    bootstrap.get_fact("__bootstrap__")
    bootstrap.close()
    result = _run_apply(db_path)
    assert result.returncode == 0, result.stderr

    fresh = memory.make_store(db_path)
    monkeypatch.setattr(memory, "_GLOBAL_STORE", fresh)
    monkeypatch.setattr(memory, "_L0", fresh._l0)
    monkeypatch.setattr(memory, "_DDL_INITIALIZED", fresh._ddl_initialized_paths)
    monkeypatch.setattr(memory, "SQLITE_PATH", db_path)
    yield fresh
    fresh.close()


@pytest.fixture(autouse=True)
def _reset_supervisor():
    import core.meta_supervisor as ms_mod
    ms_mod.reset_meta_supervisor()
    yield
    ms_mod.reset_meta_supervisor()


def _force_safe_mode(monkeypatch):
    """Patch the *live* singleton into SAFE_MODE (survives core.* reloads)."""
    import core.meta_supervisor as ms_mod
    ms = ms_mod.get_meta_supervisor()
    monkeypatch.setattr(ms, "_mode", ms_mod.SystemMode.SAFE_MODE)
    assert ms.writes_blocked is True
    return ms


def test_check_writes_allowed_when_healthy():
    from core.write_gate import check_writes_allowed
    ok, reason = check_writes_allowed()
    assert ok is True
    assert reason == "ok"


def test_policy_dependency_failure_blocks_write(store, monkeypatch):
    import core.policy_kernel as policy_kernel
    from core.write_result import WriteStatus

    policy_kernel.reset_policy_kernel()

    def _unavailable() -> str:
        raise RuntimeError("simulated policy dependency failure")

    monkeypatch.setattr(
        policy_kernel.PolicyKernel,
        "_supervisor_mode",
        staticmethod(_unavailable),
    )

    result = store.store_fact_result({
        "fact_id": "f_policy_down",
        "claim": "must not be written",
        "source": "test",
        "confidence": 0.8,
    })

    assert result.status is WriteStatus.REJECTED_POLICY
    assert result.safe_reason_code == "policy_dependency_unavailable"
    assert result.durable_write is False
    assert store.get_fact("f_policy_down") is None


def test_ensure_writes_allowed_raises_in_safe_mode(monkeypatch):
    from core.write_gate import WritesBlockedError, ensure_writes_allowed
    _force_safe_mode(monkeypatch)
    with pytest.raises(WritesBlockedError, match="SAFE_MODE"):
        ensure_writes_allowed()


def test_store_fact_blocked_in_safe_mode(store, monkeypatch):
    from core.write_gate import WritesBlockedError
    _force_safe_mode(monkeypatch)

    with pytest.raises(WritesBlockedError):
        store.store_fact(
            {"fact_id": "f_safe_1", "claim": "c", "source": "s", "confidence": 0.5}
        )
    assert store.get_fact("f_safe_1") is None


def test_store_fact_result_rejected_safe_mode(store, monkeypatch):
    from core.write_result import WriteStatus
    _force_safe_mode(monkeypatch)

    result = store.store_fact_result(
        {"fact_id": "f_safe_2", "claim": "c", "source": "s", "confidence": 0.5}
    )
    assert result.status is WriteStatus.REJECTED_SAFE_MODE
    assert result.durable_write is False
    assert result.safe_reason_code == "safe_mode_writes_blocked"
    assert store.get_fact("f_safe_2") is None


def test_transition_esm_blocked_in_safe_mode(store, monkeypatch):
    from core.write_gate import WritesBlockedError
    store.store_fact(
        {"fact_id": "f_safe_3", "claim": "c", "source": "s", "confidence": 0.5}
    )
    _force_safe_mode(monkeypatch)

    with pytest.raises(WritesBlockedError):
        store.transition_esm("f_safe_3", "Hypothesized", by="truth_gate")
    assert store.get_fact("f_safe_3")["epistemic_state"] == "Observed"


def test_invalidate_edge_blocked_in_safe_mode(store, monkeypatch):
    from core.write_gate import WritesBlockedError
    store.store_fact(
        {"fact_id": "f_safe_4", "claim": "c", "source": "s", "confidence": 0.5}
    )
    _force_safe_mode(monkeypatch)

    with pytest.raises(WritesBlockedError):
        store.invalidate_edge("f_safe_4")
    assert store.get_fact("f_safe_4")["t_event_valid_end"] is None


def test_store_facts_batch_blocked_in_safe_mode(store, monkeypatch):
    from core.write_gate import WritesBlockedError
    _force_safe_mode(monkeypatch)

    with pytest.raises(WritesBlockedError):
        store.store_facts_batch(
            [{"fact_id": "f_safe_5", "claim": "c", "source": "s", "confidence": 0.5}]
        )
    assert store.get_fact("f_safe_5") is None


def test_ims3_safe_mode_actually_blocks_store(store, monkeypatch):
    """Strengthen I-MS3: flag alone is not enough — write must fail."""
    import core.meta_supervisor as ms_mod
    from core.write_gate import WritesBlockedError

    cfg = ms_mod.SupervisorConfig(
        mhi_degraded=0.50,
        mhi_safe_mode=0.30,
        dlq_warn=10,
        dlq_safe_mode=50,
    )
    ms = ms_mod.MetaSupervisor(config=cfg)
    ms._mhi_cache = 0.25
    ms._dlq_cache = 55
    asyncio.run(ms._evaluate(0.0))
    assert ms.writes_blocked

    monkeypatch.setattr(ms_mod, "get_meta_supervisor", lambda: ms)

    with pytest.raises(WritesBlockedError):
        store.store_fact(
            {"fact_id": "f_safe_ims3", "claim": "c", "source": "s", "confidence": 0.5}
        )
    assert store.get_fact("f_safe_ims3") is None
