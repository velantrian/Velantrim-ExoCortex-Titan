"""SleepTimeWorker must not change the owner's accepted goal on its own.

Every assertion reads the persisted SQLite rows (notebook and core blocks), not only
the worker's Python objects.

    MODEL OUTPUT != OWNER DECISION        PROPOSAL != ADMISSION
    INITIATIVE != AUTHORIZATION           RESTORED STATE != RESTORED PERMISSION
    BACKGROUND ANALYSIS != RIGHT TO MUTATE
"""

from __future__ import annotations

import asyncio
import importlib
import json
import sqlite3
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from core.sleep_time_worker import SleepTimeWorker

DEFAULT_BLOCK_TEXT = "Активные цели: не указано."


def stw():
    """The worker module as currently loaded.

    Other tests re-import ``core.*``; resolving the module (and its ``mutation_gate``)
    at call time keeps monkeypatches and exception classes in the same module generation.
    """
    return importlib.import_module("core.sleep_time_worker")


def gate():
    return stw().mutation_gate


GOAL_BLOCK_NAME = "current_goals"


@pytest.fixture(autouse=True)
def reset_policy_state():
    import core.meta_supervisor as ms_mod
    import core.policy_kernel as policy_kernel

    ms_mod.reset_meta_supervisor()
    policy_kernel.reset_policy_kernel()
    yield
    ms_mod.reset_meta_supervisor()
    policy_kernel.reset_policy_kernel()


def _paths(tmp_path: Path) -> tuple[str, str]:
    return str(tmp_path / "blocks.db"), str(tmp_path / "notebook.db")


def _worker(tmp_path: Path, project_id: str = "velantrim-core", llm_fn=None) -> SleepTimeWorker:
    blocks, notebook = _paths(tmp_path)
    return stw().make_sleep_time_worker(
        project_id=project_id, core_blocks_db=blocks, notebook_db=notebook, llm_fn=llm_fn
    )


def _row(tmp_path: Path, project_id: str) -> dict | None:
    """The notebook exactly as stored in SQLite."""
    conn = sqlite3.connect(_paths(tmp_path)[1])
    try:
        row = conn.execute("SELECT data FROM notebooks WHERE project_id=?", (project_id,)).fetchone()
    finally:
        conn.close()
    return json.loads(row[0]) if row else None


def _raw(tmp_path: Path, project_id: str) -> str | None:
    conn = sqlite3.connect(_paths(tmp_path)[1])
    try:
        row = conn.execute("SELECT data FROM notebooks WHERE project_id=?", (project_id,)).fetchone()
    finally:
        conn.close()
    return row[0] if row else None


def _block(tmp_path: Path, name: str) -> str | None:
    conn = sqlite3.connect(_paths(tmp_path)[0])
    try:
        row = conn.execute("SELECT content FROM core_blocks WHERE name=?", (name,)).fetchone()
    finally:
        conn.close()
    return row[0] if row else None


async def _drain(worker: SleepTimeWorker) -> None:
    if worker._bg_tasks:
        await asyncio.gather(*list(worker._bg_tasks), return_exceptions=True)


def _proposing(goal: str):
    def llm(prompt: str) -> str:
        return goal if "ГЛАВНАЯ цель" in prompt else "[]"

    return llm


EPISODE = {"content": "Нужно обсудить направление проекта и сроки работы.", "source": "user"}


# ── LLM proposals never become the accepted goal ──────────────────────────────

async def test_llm_proposing_another_goal_leaves_the_accepted_goal(tmp_path):
    w = _worker(tmp_path, llm_fn=_proposing("Цель, придуманная моделью"))
    await w.start()
    await w.accept_goal("Цель владельца", decided_by="owner:test")
    await w.update_from_episode(EPISODE)
    await _drain(w)
    await w.think()

    stored = _row(tmp_path, "velantrim-core")
    assert stored["current_goal"] == "Цель владельца"
    assert stored["proposed_goal"] == "Цель, придуманная моделью"
    assert stored["goal_decided_by"] == "owner:test"
    assert stored["goal_revision"] == 1
    assert _block(tmp_path, GOAL_BLOCK_NAME) == "Активная цель: Цель владельца"
    await w.stop()


async def test_first_goal_from_llm_is_only_a_proposal(tmp_path):
    w = _worker(tmp_path, llm_fn=_proposing("Первая цель от модели"))
    await w.start()
    await w.update_from_episode(EPISODE)
    await _drain(w)
    await w.think()

    stored = _row(tmp_path, "velantrim-core")
    assert stored["current_goal"] == ""
    assert stored["proposed_goal"] == "Первая цель от модели"
    assert stored["goal_revision"] == 0 and stored["goal_decided_by"] == ""
    assert _block(tmp_path, GOAL_BLOCK_NAME) == DEFAULT_BLOCK_TEXT
    await w.stop()


async def test_owner_can_accept_the_proposal_explicitly(tmp_path):
    w = _worker(tmp_path, llm_fn=_proposing("Предложенная цель"))
    await w.start()
    await w.update_from_episode(EPISODE)
    await _drain(w)
    await w.think()
    await w.accept_goal(decided_by="owner:test")

    stored = _row(tmp_path, "velantrim-core")
    assert stored["current_goal"] == "Предложенная цель"
    assert stored["proposed_goal"] == ""
    assert stored["goal_decided_by"] == "owner:test"
    assert stored["extracted_intents"][-1]["kind"] == "owner_decision"
    assert _block(tmp_path, GOAL_BLOCK_NAME) == "Активная цель: Предложенная цель"
    await w.stop()


async def test_owner_decision_needs_a_named_source_and_a_current_revision(tmp_path):
    w = _worker(tmp_path, llm_fn=_proposing("Предложение"))
    await w.start()
    with pytest.raises(ValueError):
        await w.accept_goal("Цель", decided_by="  ")
    await w.accept_goal("Цель", decided_by="owner:test")
    before = _raw(tmp_path, "velantrim-core")
    with pytest.raises(stw().GoalRevisionConflictError):
        await w.accept_goal("Другая цель", decided_by="owner:test", expected_goal_revision=0)
    assert _raw(tmp_path, "velantrim-core") == before
    await w.stop()


# ── A stale background result cannot overwrite a fresher owner decision ───────

async def test_owner_changes_goal_while_the_model_is_thinking(tmp_path):
    holder: dict = {}
    fired = {"done": False}

    async def llm(prompt: str):
        if "ГЛАВНАЯ цель" in prompt and not fired["done"]:
            fired["done"] = True
            # the owner decides while the background computation is in flight
            await holder["w"].accept_goal("Новое решение владельца", decided_by="owner:test")
            return "Устаревшее предложение модели"
        return "[]"

    w = _worker(tmp_path, llm_fn=llm)
    holder["w"] = w
    await w.start()
    await w.update_from_episode(EPISODE)
    await _drain(w)
    await w.think()

    stored = _row(tmp_path, "velantrim-core")
    assert stored["current_goal"] == "Новое решение владельца"
    assert stored["proposed_goal"] != "Устаревшее предложение модели"
    assert _block(tmp_path, GOAL_BLOCK_NAME) == "Активная цель: Новое решение владельца"
    await w.stop()


async def test_a_stale_second_process_cannot_revert_the_owner_goal(tmp_path):
    """Two workers share the same databases; the first one holds an outdated cache."""
    first = _worker(tmp_path, llm_fn=_proposing("Предложение первого"))
    second = _worker(tmp_path)
    await first.start()
    await second.start()
    await second.accept_goal("Цель из другого процесса", decided_by="owner:test")

    assert first.notebook.current_goal == ""          # outdated in-memory copy
    await first.update_from_episode(EPISODE)
    await _drain(first)
    await first.think()

    stored = _row(tmp_path, "velantrim-core")
    assert stored["current_goal"] == "Цель из другого процесса"
    assert stored["goal_decided_by"] == "owner:test"
    assert any("направление проекта" in f["content"] for f in stored["known_facts"])  # its own write survived too
    await first.stop()
    await second.stop()


def test_store_rejects_a_write_based_on_an_old_version(tmp_path):
    store = stw().NotebookStore(str(tmp_path / "n.db"))
    nb = stw().ResearchNotebook(project_id="p", version=2)
    assert store.compare_and_save(nb, None) is True
    assert store.compare_and_save(nb, None) is False            # row exists
    newer = stw().ResearchNotebook(project_id="p", current_goal="fresh", version=3)
    assert store.compare_and_save(newer, 2) is True
    stale = stw().ResearchNotebook(project_id="p", current_goal="stale", version=3)
    assert store.compare_and_save(stale, 2) is False
    assert store.load("p").current_goal == "fresh"


async def test_exhausted_retries_raise_instead_of_overwriting(tmp_path, monkeypatch):
    w = _worker(tmp_path)
    await w.start()
    await w.accept_goal("Цель", decided_by="owner:test")
    before = _raw(tmp_path, "velantrim-core")
    monkeypatch.setattr(stw().NotebookStore, "compare_and_save", lambda self, nb, expected: False)
    with pytest.raises(stw().NotebookConflictError):
        await w.update_from_episode(EPISODE)
    assert _raw(tmp_path, "velantrim-core") == before
    await w.stop()


# ── Revoked authority and SAFE_MODE ───────────────────────────────────────────

def _revoke(monkeypatch):
    g = gate()

    def deny(scope: str) -> None:
        raise g.UserMutationBlockedError("authority_revoked", scope=scope)

    monkeypatch.setattr(g, "ensure_user_mutations_allowed", deny)


def _safe_mode(monkeypatch):
    import core.meta_supervisor as ms_mod

    supervisor = ms_mod.get_meta_supervisor()
    monkeypatch.setattr(supervisor, "_mode", ms_mod.SystemMode.SAFE_MODE)
    assert supervisor.writes_blocked is True


@pytest.mark.parametrize("freeze", [_revoke, _safe_mode], ids=["authority-revoked", "safe-mode"])
async def test_blocked_mutations_leave_sqlite_untouched(tmp_path, monkeypatch, freeze):
    UserMutationBlockedError = gate().UserMutationBlockedError

    w = _worker(tmp_path, llm_fn=_proposing("Предложение в запрещённый момент"))
    await w.start()
    await w.accept_goal("Цель до запрета", decided_by="owner:test")
    notebook_before = _raw(tmp_path, "velantrim-core")
    block_before = _block(tmp_path, GOAL_BLOCK_NAME)
    freeze(monkeypatch)

    await w.think()                                           # background analysis: result dropped
    assert _raw(tmp_path, "velantrim-core") == notebook_before
    with pytest.raises(UserMutationBlockedError):
        await w.update_from_episode(EPISODE)
    with pytest.raises(UserMutationBlockedError):
        await w.accept_goal("Цель после запрета", decided_by="owner:test")
    with pytest.raises(UserMutationBlockedError):
        w.core_blocks.update(GOAL_BLOCK_NAME, "обход")
    with pytest.raises(UserMutationBlockedError):
        w._nb_store.save(stw().ResearchNotebook(project_id="velantrim-core", current_goal="обход"))

    assert _raw(tmp_path, "velantrim-core") == notebook_before
    assert _block(tmp_path, GOAL_BLOCK_NAME) == block_before == "Активная цель: Цель до запрета"
    await w.stop()


# ── Work on project B does not change project A ───────────────────────────────

async def test_work_on_project_b_does_not_change_project_a(tmp_path):
    a = _worker(tmp_path, "project-a", llm_fn=_proposing("Предложение для A"))
    b = _worker(tmp_path, "project-b", llm_fn=_proposing("Предложение для B"))
    await a.start()
    await b.start()
    await a.accept_goal("Цель A", decided_by="owner:test")
    a_notebook = _raw(tmp_path, "project-a")
    a_block = _block(tmp_path, a._goal_block_name())

    await b.update_from_episode(EPISODE)
    await _drain(b)
    await b.think()
    await b.accept_goal("Цель B", decided_by="owner:test")

    assert _raw(tmp_path, "project-a") == a_notebook
    assert _block(tmp_path, a._goal_block_name()) == a_block == "Активная цель: Цель A"
    assert _block(tmp_path, b._goal_block_name()) == "Активная цель: Цель B"
    assert a._goal_block_name() != b._goal_block_name()
    assert _row(tmp_path, "project-b")["current_goal"] == "Цель B"
    await a.stop()
    await b.stop()


async def test_default_project_keeps_the_established_goal_slot(tmp_path):
    w = _worker(tmp_path)
    assert w._goal_block_name() == GOAL_BLOCK_NAME
    assert _worker(tmp_path, "other")._goal_block_name() == f"{GOAL_BLOCK_NAME}:other"


# ── Restart ───────────────────────────────────────────────────────────────────

async def test_restart_keeps_the_accepted_goal_and_the_proposal_stays_a_proposal(tmp_path):
    first = _worker(tmp_path, llm_fn=_proposing("Предложение до перезапуска"))
    await first.start()
    await first.accept_goal("Принятая цель", decided_by="owner:test")
    await first.update_from_episode(EPISODE)
    await _drain(first)
    await first.think()
    await first.stop()

    second = _worker(tmp_path, llm_fn=_proposing("Предложение после перезапуска"))
    await second.start()
    assert second.notebook.current_goal == "Принятая цель"
    assert second.notebook.proposed_goal == "Предложение до перезапуска"
    await second.think()

    stored = _row(tmp_path, "velantrim-core")
    assert stored["current_goal"] == "Принятая цель"
    assert stored["proposed_goal"] == "Предложение после перезапуска"
    assert stored["goal_decided_by"] == "owner:test"
    assert _block(tmp_path, GOAL_BLOCK_NAME) == "Активная цель: Принятая цель"
    await second.stop()


async def test_restart_does_not_restore_permission(tmp_path, monkeypatch):
    first = _worker(tmp_path)
    await first.start()
    await first.accept_goal("Цель", decided_by="owner:test")
    await first.stop()

    _revoke(monkeypatch)
    UserMutationBlockedError = gate().UserMutationBlockedError

    second = _worker(tmp_path)
    await second.start()                                  # reading the stored state is allowed
    assert second.notebook.current_goal == "Цель"
    with pytest.raises(UserMutationBlockedError):
        await second.accept_goal("Цель после рестарта", decided_by="owner:test")
    assert _row(tmp_path, "velantrim-core")["current_goal"] == "Цель"
    await second.stop()


# ── Useful analysis stays available within existing authority ─────────────────

async def test_analysis_gaps_synthesis_and_next_step_still_work(tmp_path):
    SYNTHESIS_EVERY_N_FACTS = stw().SYNTHESIS_EVERY_N_FACTS

    def llm(prompt: str) -> str:
        if "Какие важные аспекты" in prompt:
            return json.dumps([{"gap": "Не освещены сроки", "priority": "high"}])
        if "Составь" in prompt or "синтез" in prompt.lower():
            return "Синтез: проект движется."
        return "[]"

    w = _worker(tmp_path, llm_fn=llm)
    await w.start()
    await w.accept_goal("Цель", decided_by="owner:test")
    await w.update_from_episode({"content": "Как нам закрыть этот вопрос по проекту?", "source": "user"})
    await _drain(w)
    w._facts_since_synthesis = SYNTHESIS_EVERY_N_FACTS
    await w.think()

    stored = _row(tmp_path, "velantrim-core")
    assert stored["synthesis_history"], "synthesis is still produced and stored"
    assert any(g["gap"] == "Не освещены сроки" for g in stored["open_gaps"]), "gap detection still works"
    assert stored["current_goal"] == "Цель"
    assert isinstance(await w.suggest_next_step(), str)
    snapshot = await w.get_notebook()
    assert snapshot["current_goal"] == "Цель" and "proposed_goal" in snapshot
    await w.stop()
