"""SleepTimeWorker must not change the owner's accepted goal on its own.

Every assertion reads the persisted SQLite rows (notebook and core blocks), not only
the worker's Python objects. Cross-process behaviour is in
``tests/test_sleep_worker_cross_process.py``.

    MODEL OUTPUT != OWNER DECISION        PROPOSAL != ADMISSION
    INITIATIVE != AUTHORIZATION           RESTORED STATE != RESTORED PERMISSION
    BACKGROUND ANALYSIS != RIGHT TO MUTATE

Authoritative source of the accepted goal: the notebook row in ``NotebookStore``.
The ``current_goals`` block in ``CoreMemoryBlocks`` is a derived projection.
"""

from __future__ import annotations

import asyncio
import importlib
import json
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from core.sleep_time_worker import OwnerGoalDecision, SleepTimeWorker

DEFAULT_BLOCK_TEXT = "Активные цели: не указано."
KEY_ID = "owner-key-1"
SECRET = b"k" * 32
GOAL_BLOCK_NAME = "current_goals"


def stw():
    """The worker module as currently loaded.

    Other tests re-import ``core.*``; resolving the module (and its ``mutation_gate``)
    at call time keeps monkeypatches and exception classes in the same module generation.
    """
    return importlib.import_module("core.sleep_time_worker")


def gate():
    return stw().mutation_gate


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


def _authority(secret: bytes = SECRET, key_id: str = KEY_ID, revoked=frozenset()):
    return stw().OwnerGoalAuthority(key_id=key_id, secret=secret, revoked_key_ids=frozenset(revoked))


def _worker(tmp_path: Path, project_id: str = "velantrim-core", llm_fn=None,
            authority: bool = True) -> SleepTimeWorker:
    blocks, notebook = _paths(tmp_path)
    return stw().make_sleep_time_worker(
        project_id=project_id, core_blocks_db=blocks, notebook_db=notebook, llm_fn=llm_fn,
        owner_authority=_authority() if authority else None,
    )


def _row(tmp_path: Path, project_id: str) -> dict | None:
    """The notebook exactly as stored in SQLite."""
    raw = _raw(tmp_path, project_id)
    return json.loads(raw) if raw else None


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


def _revision(tmp_path: Path, project_id: str = "velantrim-core") -> int:
    row = _row(tmp_path, project_id)
    return row["goal_revision"] if row else 0


def set_goal(tmp_path: Path, goal: str, *, project_id: str = "velantrim-core",
             decided_by: str = "owner:test", **overrides) -> OwnerGoalDecision:
    args = dict(key_id=KEY_ID, secret=SECRET, project_id=project_id, action="set_goal",
                expected_goal_revision=_revision(tmp_path, project_id), goal=goal,
                decided_by=decided_by)
    args.update(overrides)
    return stw().issue_owner_goal_decision(**args)


def accept_proposal(tmp_path: Path, *, project_id: str = "velantrim-core",
                    decided_by: str = "owner:test", **overrides) -> OwnerGoalDecision:
    row = _row(tmp_path, project_id)
    args = dict(key_id=KEY_ID, secret=SECRET, project_id=project_id, action="accept_proposal",
                expected_goal_revision=row["goal_revision"], proposal_id=row["proposed_goal_id"],
                decided_by=decided_by)
    args.update(overrides)
    return stw().issue_owner_goal_decision(**args)


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
    await w.accept_goal(set_goal(tmp_path, "Цель владельца"))
    await w.update_from_episode(EPISODE)
    await _drain(w)
    await w.think()

    stored = _row(tmp_path, "velantrim-core")
    assert stored["current_goal"] == "Цель владельца"
    assert stored["proposed_goal"] == "Цель, придуманная моделью"
    assert stored["proposed_goal_id"]
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


async def test_owner_accepts_the_proposal_with_a_signed_decision_bound_to_it(tmp_path):
    w = _worker(tmp_path, llm_fn=_proposing("Предложенная цель"))
    await w.start()
    await w.update_from_episode(EPISODE)
    await _drain(w)
    await w.think()
    await w.accept_goal(accept_proposal(tmp_path))

    stored = _row(tmp_path, "velantrim-core")
    assert stored["current_goal"] == "Предложенная цель"
    assert stored["proposed_goal"] == "" and stored["proposed_goal_id"] == ""
    assert stored["goal_decided_by"] == "owner:test"
    intent = stored["extracted_intents"][-1]
    assert intent["kind"] == "owner_decision" and intent["key_id"] == KEY_ID
    assert intent["action"] == "accept_proposal" and intent["proposal_id"]
    assert _block(tmp_path, GOAL_BLOCK_NAME) == "Активная цель: Предложенная цель"
    await w.stop()


# ── Authority: a label is not a permission ────────────────────────────────────

async def test_accepting_a_goal_is_unavailable_without_a_configured_authority(tmp_path):
    w = _worker(tmp_path, authority=False)
    await w.start()
    before = _raw(tmp_path, "velantrim-core")
    with pytest.raises(stw().OwnerAuthorityError):
        await w.accept_goal(set_goal(tmp_path, "Цель"))
    with pytest.raises(stw().OwnerAuthorityError):
        await w.accept_goal("owner:test")  # type: ignore[arg-type]  # a bare label is not a decision
    assert _raw(tmp_path, "velantrim-core") == before
    assert _block(tmp_path, GOAL_BLOCK_NAME) == DEFAULT_BLOCK_TEXT
    await w.stop()


def _forgeries(tmp_path: Path):
    now = datetime.now(UTC)
    good = set_goal(tmp_path, "Подлинная цель")
    return {
        "plain-string-label": "owner:test",
        "wrong-secret": set_goal(tmp_path, "Цель", secret=b"x" * 32),
        "tampered-goal": stw().OwnerGoalDecision(**{**good.__dict__, "goal": "Подменённая цель"}),
        "tampered-author": stw().OwnerGoalDecision(**{**good.__dict__, "decided_by": "other"}),
        "another-project": set_goal(tmp_path, "Цель", project_id="project-other"),
        "expired": set_goal(tmp_path, "Цель", issued_at=now - timedelta(hours=1)),
        "from-the-future": set_goal(tmp_path, "Цель", issued_at=now + timedelta(hours=1)),
        "unknown-key": set_goal(tmp_path, "Цель", key_id="other-key"),
    }


async def test_untrusted_or_malformed_decisions_change_nothing(tmp_path):
    w = _worker(tmp_path)
    await w.start()
    await w.accept_goal(set_goal(tmp_path, "Исходная цель"))
    notebook_before = _raw(tmp_path, "velantrim-core")
    block_before = _block(tmp_path, GOAL_BLOCK_NAME)

    for name, decision in _forgeries(tmp_path).items():
        with pytest.raises(stw().OwnerAuthorityError):
            await w.accept_goal(decision)
        assert _raw(tmp_path, "velantrim-core") == notebook_before, name
    assert _block(tmp_path, GOAL_BLOCK_NAME) == block_before
    await w.stop()


async def test_a_revoked_key_is_rejected(tmp_path):
    blocks, notebook = _paths(tmp_path)
    w = stw().make_sleep_time_worker(
        project_id="velantrim-core", core_blocks_db=blocks, notebook_db=notebook,
        owner_authority=_authority(revoked={KEY_ID}),
    )
    await w.start()
    with pytest.raises(stw().OwnerAuthorityError):
        await w.accept_goal(set_goal(tmp_path, "Цель"))
    assert _row(tmp_path, "velantrim-core")["current_goal"] == "" if _row(tmp_path, "velantrim-core") else True
    await w.stop()


async def test_confirmation_is_bound_to_the_exact_proposal_and_revision(tmp_path):
    w = _worker(tmp_path, llm_fn=_proposing("Первое предложение"))
    await w.start()
    await w.update_from_episode(EPISODE)
    await _drain(w)
    await w.think()
    first = accept_proposal(tmp_path)

    # a newer proposal replaces the first one: a decision about the old one must fail
    w._llm_fn = _proposing("Второе предложение")
    await w.think()
    assert _row(tmp_path, "velantrim-core")["proposed_goal"] == "Второе предложение"
    before = _raw(tmp_path, "velantrim-core")
    with pytest.raises(stw().ProposalMismatchError):
        await w.accept_goal(first)
    assert _raw(tmp_path, "velantrim-core") == before

    second = accept_proposal(tmp_path)
    await w.accept_goal(second)
    assert _row(tmp_path, "velantrim-core")["current_goal"] == "Второе предложение"

    # replaying a signed decision after it was used fails: the goal revision moved on
    after = _raw(tmp_path, "velantrim-core")
    with pytest.raises(stw().GoalRevisionConflictError):
        await w.accept_goal(second)
    # a decision based on an outdated revision also fails
    with pytest.raises(stw().GoalRevisionConflictError):
        await w.accept_goal(set_goal(tmp_path, "Другая", expected_goal_revision=0))
    assert _raw(tmp_path, "velantrim-core") == after
    await w.stop()


# ── A stale background result cannot overwrite a fresher owner decision ───────

class _Scripted:
    """An LLM stand-in that says nothing useful unless armed for one chosen ``think()``.

    ``on_goal`` runs once, in the middle of the armed computation (after the snapshot,
    before the result is written), which is exactly when a concurrent writer can act.
    """

    def __init__(self, *, goal="", gap="", synthesis="", on_goal=None):
        self.armed = False
        self.goal, self.gap, self.synthesis, self.on_goal = goal, gap, synthesis, on_goal

    async def __call__(self, prompt: str):
        if not self.armed:
            return "[]" if "Какие важные аспекты" in prompt else ""
        if "ГЛАВНАЯ цель" in prompt:
            if self.on_goal is not None:
                hook, self.on_goal = self.on_goal, None
                await hook()
            return self.goal
        if "Какие важные аспекты" in prompt:
            return json.dumps([{"gap": self.gap, "priority": "high"}]) if self.gap else "[]"
        if "Составь" in prompt:
            return self.synthesis
        return ""


async def _armed_think(w: SleepTimeWorker, llm: _Scripted) -> None:
    await w.update_from_episode(EPISODE)
    await _drain(w)                                    # background cycles run unarmed
    w._facts_since_synthesis = stw().SYNTHESIS_EVERY_N_FACTS
    llm.armed = True
    await w.think()
    llm.armed = False
    await _drain(w)


async def test_owner_changes_goal_while_the_model_is_thinking(tmp_path):
    holder: dict = {}

    async def owner_decides():
        await holder["w"].accept_goal(set_goal(tmp_path, "Новое решение владельца"))

    llm = _Scripted(goal="Устаревшее предложение модели", gap="Пробел для старой цели",
                    synthesis="Синтез для старой цели", on_goal=owner_decides)
    w = _worker(tmp_path, llm_fn=llm)
    holder["w"] = w
    await w.start()
    await _armed_think(w, llm)

    stored = _row(tmp_path, "velantrim-core")
    assert stored["current_goal"] == "Новое решение владельца"
    assert stored["proposed_goal"] == ""                       # stale proposal dropped
    assert not [g for g in stored["open_gaps"] if g["gap"] == "Пробел для старой цели"]
    assert not stored["synthesis_history"]                     # synthesis of the old framing dropped
    assert _block(tmp_path, GOAL_BLOCK_NAME) == "Активная цель: Новое решение владельца"
    await w.stop()


async def test_analysis_is_dropped_when_its_source_facts_disappear(tmp_path):
    holder: dict = {}

    async def facts_are_erased():
        # another writer rewrites the notebook without the facts the analysis was based on
        store = holder["w"]._nb_store
        nb = store.load("velantrim-core")
        nb.known_facts = []
        nb.version += 1
        store.save(nb)

    llm = _Scripted(goal="Предложение по исчезнувшим фактам", gap="Пробел по исчезнувшим фактам",
                    synthesis="Синтез по исчезнувшим фактам", on_goal=facts_are_erased)
    w = _worker(tmp_path, llm_fn=llm)
    holder["w"] = w
    await w.start()
    await _armed_think(w, llm)

    stored = _row(tmp_path, "velantrim-core")
    assert stored["known_facts"] == []
    assert stored["proposed_goal"] == ""
    assert not [g for g in stored["open_gaps"] if "исчезнувшим" in g["gap"]]
    assert not stored["synthesis_history"]
    await w.stop()


async def test_analysis_survives_new_facts_arriving_meanwhile(tmp_path):
    holder: dict = {}

    async def new_fact_arrives():
        # normal Fast Path traffic during the computation is additive, not a new basis
        await holder["w"].update_from_episode(
            {"content": "Ещё один факт, поступивший во время анализа.", "source": "user"})

    llm = _Scripted(goal="Предложение, актуальное при новых фактах", gap="Актуальный пробел",
                    synthesis="Актуальный синтез", on_goal=new_fact_arrives)
    w = _worker(tmp_path, llm_fn=llm)
    holder["w"] = w
    await w.start()
    await _armed_think(w, llm)

    stored = _row(tmp_path, "velantrim-core")
    assert stored["proposed_goal"] == "Предложение, актуальное при новых фактах"
    assert any(g["gap"] == "Актуальный пробел" and g["basis_goal_revision"] == 0
               for g in stored["open_gaps"])
    assert stored["synthesis_history"][-1]["content"] == "Актуальный синтез"
    assert any("во время анализа" in f["content"] for f in stored["known_facts"])
    await w.stop()


async def test_a_stale_second_process_cannot_revert_the_owner_goal(tmp_path):
    """Two workers share the same databases; the first one holds an outdated cache."""
    first = _worker(tmp_path, llm_fn=_proposing("Предложение первого"))
    second = _worker(tmp_path)
    await first.start()
    await second.start()
    await second.accept_goal(set_goal(tmp_path, "Цель из другого процесса"))

    assert first.notebook.current_goal == ""          # outdated in-memory copy
    await first.update_from_episode(EPISODE)
    await _drain(first)
    await first.think()

    stored = _row(tmp_path, "velantrim-core")
    assert stored["current_goal"] == "Цель из другого процесса"
    assert stored["goal_decided_by"] == "owner:test"
    assert any("направление проекта" in f["content"] for f in stored["known_facts"])
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
    await w.accept_goal(set_goal(tmp_path, "Цель"))
    before = _raw(tmp_path, "velantrim-core")
    monkeypatch.setattr(stw().NotebookStore, "compare_and_save", lambda self, nb, expected: False)
    with pytest.raises(stw().NotebookConflictError):
        await w.update_from_episode(EPISODE)
    assert _raw(tmp_path, "velantrim-core") == before
    await w.stop()


# ── The notebook row is the authority; the core block is a projection ─────────

async def test_failed_projection_does_not_undo_the_decision_and_is_repaired(tmp_path, monkeypatch):
    w = _worker(tmp_path)
    await w.start()
    await w.accept_goal(set_goal(tmp_path, "Первая цель"))
    assert _block(tmp_path, GOAL_BLOCK_NAME) == "Активная цель: Первая цель"

    real_update = w.core_blocks.update
    calls = {"n": 0}

    def failing_update(name, content):
        calls["n"] += 1
        raise sqlite3.OperationalError("disk I/O error")

    monkeypatch.setattr(w.core_blocks, "update", failing_update)
    await w.accept_goal(set_goal(tmp_path, "Вторая цель"))             # the decision still stands

    assert _row(tmp_path, "velantrim-core")["current_goal"] == "Вторая цель"
    assert _block(tmp_path, GOAL_BLOCK_NAME) == "Активная цель: Первая цель"   # stale projection
    assert w.goal_projection_in_sync is False and calls["n"] >= 1
    # readers do not see the stale projection
    context = w.system_context()
    assert "Вторая цель" in context and "Первая цель" not in context

    monkeypatch.setattr(w.core_blocks, "update", real_update)
    await w.think()                                                    # reconciliation
    assert _block(tmp_path, GOAL_BLOCK_NAME) == "Активная цель: Вторая цель"
    assert w.goal_projection_in_sync is True
    await w.stop()


async def test_restart_repairs_a_projection_left_stale_by_a_crash(tmp_path):
    first = _worker(tmp_path)
    await first.start()
    await first.accept_goal(set_goal(tmp_path, "Цель до сбоя"))
    await first.stop()
    # simulate "notebook committed, block write never happened"
    conn = sqlite3.connect(_paths(tmp_path)[0])
    conn.execute("UPDATE core_blocks SET content=? WHERE name=?", (DEFAULT_BLOCK_TEXT, GOAL_BLOCK_NAME))
    conn.commit()
    conn.close()

    second = _worker(tmp_path)
    await second.start()
    assert _block(tmp_path, GOAL_BLOCK_NAME) == "Активная цель: Цель до сбоя"
    await second.stop()


# ── Reads are isolated per project ────────────────────────────────────────────

async def test_system_context_never_discloses_the_goals_of_other_projects(tmp_path):
    a = _worker(tmp_path, "project-a")
    b = _worker(tmp_path, "project-b")
    default = _worker(tmp_path)
    for w in (a, b, default):
        await w.start()
    await a.accept_goal(set_goal(tmp_path, "СЕКРЕТНАЯ ЦЕЛЬ А", project_id="project-a"))
    await b.accept_goal(set_goal(tmp_path, "СЕКРЕТНАЯ ЦЕЛЬ Б", project_id="project-b"))
    await default.accept_goal(set_goal(tmp_path, "СЕКРЕТНАЯ ЦЕЛЬ ПО УМОЛЧАНИЮ"))

    for worker, own, foreign in (
        (a, "ЦЕЛЬ А", ("ЦЕЛЬ Б", "ПО УМОЛЧАНИЮ")),
        (b, "ЦЕЛЬ Б", ("ЦЕЛЬ А", "ПО УМОЛЧАНИЮ")),
        (default, "ПО УМОЛЧАНИЮ", ("ЦЕЛЬ А", "ЦЕЛЬ Б")),
    ):
        views = (
            worker.system_context(),
            worker.core_blocks.get_system_context(worker.project_id),
            "\n".join(worker.core_blocks.all_as_dict(worker.project_id).values()),
        )
        for text in views:
            assert own in text
            assert not any(f in text for f in foreign)
    # no project argument means the default project, never someone else's slot
    plain = default.core_blocks.get_system_context()
    assert "ЦЕЛЬ А" not in plain and "ЦЕЛЬ Б" not in plain
    for w in (a, b, default):
        await w.stop()


async def test_a_project_without_a_goal_does_not_inherit_the_default_projects_goal(tmp_path):
    default = _worker(tmp_path)
    other = _worker(tmp_path, "project-new")
    await default.start()
    await other.start()
    await default.accept_goal(set_goal(tmp_path, "Цель проекта по умолчанию"))
    assert "Цель проекта по умолчанию" not in other.system_context()
    assert DEFAULT_BLOCK_TEXT in other.system_context()
    await default.stop()
    await other.stop()


# ── Legacy goals without a confirmed origin ───────────────────────────────────

def _write_legacy_notebook(tmp_path: Path) -> str:
    """A row as the old background overwrite left it: a goal, no owner decision."""
    stw().NotebookStore(_paths(tmp_path)[1])
    legacy = {
        "project_id": "velantrim-core", "current_goal": "Цель из старого фонового процесса",
        "extracted_intents": [{"goal": "Цель из старого фонового процесса", "prev_goal": "",
                               "confidence": 0.85, "at": "2026-11-01T00:00:00+00:00"}],
        "key_questions": [], "known_facts": [], "open_gaps": [], "synthesis_history": [],
        "user_style": "стиль", "last_thought": "2026-11-01T00:00:00+00:00", "version": 7,
    }
    raw = json.dumps(legacy, ensure_ascii=False)
    conn = sqlite3.connect(_paths(tmp_path)[1])
    conn.execute("INSERT INTO notebooks (project_id, data, updated_at) VALUES (?,?,?)",
                 ("velantrim-core", raw, "2026-11-01T00:00:00+00:00"))
    conn.commit()
    conn.close()
    return raw


async def test_legacy_goal_is_marked_unconfirmed_and_its_data_is_preserved(tmp_path):
    original = _write_legacy_notebook(tmp_path)
    w = _worker(tmp_path)
    await w.start()
    assert w.notebook.goal_provenance == "UNCONFIRMED_LEGACY"
    assert _raw(tmp_path, "velantrim-core") == original            # loading rewrites nothing

    context = w.system_context()
    assert "НЕ подтверждена" in context and "Цель из старого фонового процесса" in context
    assert _block(tmp_path, GOAL_BLOCK_NAME) == DEFAULT_BLOCK_TEXT  # never projected as accepted
    assert (await w.get_notebook())["goal_status"] == "UNCONFIRMED_LEGACY"

    stored = _row(tmp_path, "velantrim-core")                      # background analysis kept the data
    assert stored["current_goal"] == "Цель из старого фонового процесса"
    assert stored["extracted_intents"][0]["confidence"] == 0.85
    assert stored["goal_revision"] == 0 and stored["goal_decided_by"] == ""

    await w.accept_goal(set_goal(tmp_path, "Цель из старого фонового процесса", decided_by="owner:review"))
    confirmed = _row(tmp_path, "velantrim-core")
    assert confirmed["goal_decided_by"] == "owner:review" and confirmed["goal_revision"] == 1
    assert confirmed["extracted_intents"][0]["confidence"] == 0.85   # history kept
    assert w.notebook.goal_provenance == "OWNER_CONFIRMED"
    assert "НЕ подтверждена" not in w.system_context()
    await w.stop()


async def test_background_analysis_never_confirms_a_legacy_goal(tmp_path):
    _write_legacy_notebook(tmp_path)
    w = _worker(tmp_path, llm_fn=_proposing("Что-то другое"))
    await w.start()
    await w.update_from_episode(EPISODE)
    await _drain(w)
    await w.think()
    stored = _row(tmp_path, "velantrim-core")
    assert stored["goal_decided_by"] == "" and stored["goal_revision"] == 0
    assert stored["current_goal"] == "Цель из старого фонового процесса"
    assert w.notebook.goal_provenance == "UNCONFIRMED_LEGACY"
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
    await w.accept_goal(set_goal(tmp_path, "Цель до запрета"))
    notebook_before = _raw(tmp_path, "velantrim-core")
    block_before = _block(tmp_path, GOAL_BLOCK_NAME)
    valid_decision = set_goal(tmp_path, "Цель после запрета")
    freeze(monkeypatch)

    await w.think()                                           # background analysis: result dropped
    assert _raw(tmp_path, "velantrim-core") == notebook_before
    with pytest.raises(UserMutationBlockedError):
        await w.update_from_episode(EPISODE)
    with pytest.raises(UserMutationBlockedError):
        await w.accept_goal(valid_decision)                   # valid signature, still no write
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
    await a.accept_goal(set_goal(tmp_path, "Цель A", project_id="project-a"))
    a_notebook = _raw(tmp_path, "project-a")
    a_block = _block(tmp_path, a._goal_block_name())

    await b.update_from_episode(EPISODE)
    await _drain(b)
    await b.think()
    await b.accept_goal(set_goal(tmp_path, "Цель B", project_id="project-b"))
    # a decision signed for project B cannot be used on project A
    with pytest.raises(stw().OwnerAuthorityError):
        await a.accept_goal(set_goal(tmp_path, "Цель B для A", project_id="project-b"))

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
    await first.accept_goal(set_goal(tmp_path, "Принятая цель"))
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
    await first.accept_goal(set_goal(tmp_path, "Цель"))
    await first.stop()

    decision = set_goal(tmp_path, "Цель после рестарта")
    _revoke(monkeypatch)
    UserMutationBlockedError = gate().UserMutationBlockedError

    second = _worker(tmp_path)
    await second.start()                                  # reading the stored state is allowed
    assert second.notebook.current_goal == "Цель"
    with pytest.raises(UserMutationBlockedError):
        await second.accept_goal(decision)
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
    await w.accept_goal(set_goal(tmp_path, "Цель"))
    await w.update_from_episode({"content": "Как нам закрыть этот вопрос по проекту?", "source": "user"})
    await _drain(w)
    w._facts_since_synthesis = SYNTHESIS_EVERY_N_FACTS
    await w.think()

    stored = _row(tmp_path, "velantrim-core")
    assert stored["synthesis_history"][-1]["basis_goal_revision"] == 1
    assert any(g["gap"] == "Не освещены сроки" for g in stored["open_gaps"]), "gap detection still works"
    assert stored["current_goal"] == "Цель"
    assert isinstance(await w.suggest_next_step(), str)
    snapshot = await w.get_notebook()
    assert snapshot["current_goal"] == "Цель" and snapshot["goal_status"] == "OWNER_CONFIRMED"
    assert "proposed_goal_id" in snapshot
    await w.stop()
