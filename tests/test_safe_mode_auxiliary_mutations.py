"""SAFE_MODE must freeze mutable user/projection stores outside Canon."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def reset_policy_state():
    import core.meta_supervisor as ms_mod
    import core.policy_kernel as policy_kernel

    ms_mod.reset_meta_supervisor()
    policy_kernel.reset_policy_kernel()
    yield
    ms_mod.reset_meta_supervisor()
    policy_kernel.reset_policy_kernel()


def _force_safe_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    import core.meta_supervisor as ms_mod

    supervisor = ms_mod.get_meta_supervisor()
    monkeypatch.setattr(supervisor, "_mode", ms_mod.SystemMode.SAFE_MODE)
    assert supervisor.writes_blocked is True


def test_mutation_gate_allows_healthy_and_blocks_safe_mode(monkeypatch) -> None:
    from core.mutation_gate import (
        UserMutationBlockedError,
        ensure_user_mutations_allowed,
    )

    ensure_user_mutations_allowed("goal_stack.create")
    _force_safe_mode(monkeypatch)
    with pytest.raises(UserMutationBlockedError) as caught:
        ensure_user_mutations_allowed("goal_stack.create")

    assert caught.value.reason_code == "safe_mode_writes_blocked"
    assert caught.value.scope == "goal_stack.create"
    assert caught.value.snapshot_id


def test_mutation_gate_fails_closed_when_policy_dependency_is_unavailable(monkeypatch) -> None:
    import core.policy_kernel as policy_kernel
    from core.mutation_gate import UserMutationBlockedError, ensure_user_mutations_allowed

    def unavailable() -> str:
        raise RuntimeError("supervisor unavailable")

    monkeypatch.setattr(
        policy_kernel.PolicyKernel,
        "_supervisor_mode",
        staticmethod(unavailable),
    )

    with pytest.raises(UserMutationBlockedError) as caught:
        ensure_user_mutations_allowed("console_notes.create")
    assert caught.value.reason_code == "policy_dependency_unavailable"


def test_goal_create_and_status_update_are_frozen(tmp_path, monkeypatch) -> None:
    from core.goal_stack import GoalStack
    from core.mutation_gate import UserMutationBlockedError

    db_path = str(tmp_path / "goals.db")
    goals = GoalStack(db_path)
    existing = goals.create(title="existing")
    _force_safe_mode(monkeypatch)

    with pytest.raises(UserMutationBlockedError):
        goals.create(title="must not persist")
    with pytest.raises(UserMutationBlockedError):
        goals.update_status(existing.goal_id, "done")

    assert goals.get(existing.goal_id).status == "active"
    with sqlite3.connect(db_path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM user_goals").fetchone()[0] == 1


def test_console_note_create_update_delete_are_frozen(tmp_path, monkeypatch) -> None:
    from core.console_notes import ConsoleNotesStore
    from core.mutation_gate import UserMutationBlockedError

    store = ConsoleNotesStore(str(tmp_path / "notes.db"))
    existing = store.create_note("original", title="note")
    _force_safe_mode(monkeypatch)

    with pytest.raises(UserMutationBlockedError):
        store.create_note("blocked")
    with pytest.raises(UserMutationBlockedError):
        store.update_note(existing["note_id"], content="changed")
    with pytest.raises(UserMutationBlockedError):
        store.delete_note(existing["note_id"])

    assert store.get_note(existing["note_id"])["content"] == "original"
    assert len(store.list_notes()) == 1


def test_operational_memory_mutations_are_frozen(tmp_path, monkeypatch) -> None:
    from core.memory_ops import MemoryOpsStore
    from core.mutation_gate import UserMutationBlockedError

    store = MemoryOpsStore(str(tmp_path / "memory-ops.db"))
    # Initialize technical schema while healthy; schema DDL is an explicit
    # startup/read exception and is not user-state mutation.
    assert store.list_sources()["total"] == 0
    _force_safe_mode(monkeypatch)

    calls = [
        lambda: store.register_source(source_type="user", label="blocked"),
        lambda: store.enqueue_fact(claim="blocked claim"),
        lambda: store.set_inbox_status("missing", "rejected"),
        lambda: store.promote_inbox_item("missing"),
        lambda: store.save_trace(query="blocked query"),
    ]
    for call in calls:
        with pytest.raises(UserMutationBlockedError):
            call()

    assert store.list_sources()["total"] == 0
    assert store.list_inbox(status=None)["total"] == 0
    assert store.list_traces()["total"] == 0


def test_promotion_gate_precedes_raw_or_fact_write() -> None:
    source = (
        Path(__file__).resolve().parents[1] / "core" / "memory_ops.py"
    ).read_text(encoding="utf-8")
    start = source.index("    def promote_inbox_item(")
    end = source.index("    def save_trace(", start)
    block = source[start:end]

    gate = block.index('ensure_user_mutations_allowed("memory_ops.promote_inbox_item")')
    inbox_read = block.index("item = self.get_inbox_item(inbox_id)")
    raw_write = block.index("raw_id = store_raw_text(")
    canonical_write = block.index("result = store_fact_result(fact)")
    assert gate < inbox_read < raw_write < canonical_write


def test_safety_and_compliance_ledgers_are_explicit_exceptions() -> None:
    # The auxiliary gate must not be imported into erasure coordinators: their
    # recovery/tombstone receipts may be required while SAFE_MODE is active.
    root = Path(__file__).resolve().parents[1]
    for relative in (
        "core/erasure_coordinator.py",
        "core/erasure_batch_coordinator.py",
        "core/erasure_startup_runner.py",
        "core/erasure_startup_runtime.py",
    ):
        source = (root / relative).read_text(encoding="utf-8")
        assert "ensure_user_mutations_allowed" not in source
