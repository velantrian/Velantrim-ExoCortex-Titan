"""Cross-process regressions for SleepTimeWorker goal authority.

Real OS processes (``tests/fixtures/sleep_worker_child.py``) share file-backed SQLite
databases. Nothing here is simulated in memory: races are real concurrent writers, and
"failure between the two writes" is a process that dies (``os._exit``) or a write that
raises, after the notebook commit and before the core block write.

The accepted goal lives in the notebook row; the ``current_goals`` block is a derived
projection (see ``tests/test_sleep_worker_goal_authority.py``).
"""

from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

import pytest

CHILD = Path(__file__).resolve().parent / "fixtures" / "sleep_worker_child.py"
GOAL_BLOCK = "current_goals"
DEFAULT_BLOCK_TEXT = "Активные цели: не указано."
TIMEOUT = 120


class Env:
    """Database paths and helpers shared by the parent test and its children."""

    def __init__(self, tmp_path: Path):
        self.tmp = tmp_path
        self.blocks_db = str(tmp_path / "blocks.db")
        self.notebook_db = str(tmp_path / "notebook.db")

    def cfg(self, mode: str, project: str = "velantrim-core", **extra) -> dict:
        return {"mode": mode, "project": project, "blocks_db": self.blocks_db,
                "notebook_db": self.notebook_db, **extra}

    def spawn(self, cfg: dict) -> subprocess.Popen:
        return subprocess.Popen([sys.executable, str(CHILD), json.dumps(cfg)],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    @staticmethod
    def collect(proc: subprocess.Popen) -> tuple[int, dict | None, str]:
        out, err = proc.communicate(timeout=TIMEOUT)
        result = None
        for line in out.splitlines():
            if line.startswith("RESULT:"):
                result = json.loads(line[len("RESULT:"):])
        return proc.returncode, result, err

    def run(self, cfg: dict) -> dict:
        code, result, err = self.collect(self.spawn(cfg))
        assert code == 0 and result is not None, err[-2000:]
        return result

    # ── raw SQLite reads, bypassing the worker ──
    def notebook(self, project: str = "velantrim-core") -> dict | None:
        conn = sqlite3.connect(self.notebook_db)
        try:
            row = conn.execute("SELECT data FROM notebooks WHERE project_id=?", (project,)).fetchone()
        finally:
            conn.close()
        return json.loads(row[0]) if row else None

    def raw_notebook(self, project: str = "velantrim-core") -> str | None:
        conn = sqlite3.connect(self.notebook_db)
        try:
            row = conn.execute("SELECT data FROM notebooks WHERE project_id=?", (project,)).fetchone()
        finally:
            conn.close()
        return row[0] if row else None

    def block(self, name: str) -> str | None:
        conn = sqlite3.connect(self.blocks_db)
        try:
            row = conn.execute("SELECT content FROM core_blocks WHERE name=?", (name,)).fetchone()
        finally:
            conn.close()
        return row[0] if row else None


@pytest.fixture
def env(tmp_path: Path) -> Env:
    return Env(tmp_path)


def _wait_all(paths: list[Path], timeout: float = 60.0) -> None:
    deadline = time.monotonic() + timeout
    while not all(p.exists() for p in paths):
        assert time.monotonic() < deadline, "children did not become ready"
        time.sleep(0.02)


# ── Concurrent acceptance of goals ────────────────────────────────────────────

def test_concurrent_acceptance_has_exactly_one_winner_and_a_consistent_projection(env):
    env.run(env.cfg("start_only"))                       # creates both databases
    gate = env.tmp / "gate"
    goals = [f"Цель процесса {i}" for i in range(6)]
    ready = [env.tmp / f"ready.{i}" for i in range(len(goals))]
    procs = [
        env.spawn(env.cfg("accept", goal=goal, expected_revision=0, gate=str(gate),
                          ready=str(ready[i]), decided_by=f"owner:proc-{i}"))
        for i, goal in enumerate(goals)
    ]
    _wait_all(ready)
    gate.touch()                                         # release all writers at the same moment
    results = []
    for proc in procs:
        code, result, err = env.collect(proc)
        assert code == 0 and result is not None, err[-2000:]
        results.append(result)

    winners = [r for r in results if r["ok"]]
    losers = [r for r in results if not r["ok"]]
    assert len(winners) == 1, results
    assert {r["error"] for r in losers} == {"GoalRevisionConflictError"}, results

    stored = env.notebook()
    assert stored["goal_revision"] == 1
    assert stored["current_goal"] in goals
    assert stored["goal_decided_by"] == f"owner:proc-{goals.index(stored['current_goal'])}"
    decisions = [i for i in stored["extracted_intents"] if i.get("kind") == "owner_decision"]
    assert len(decisions) == 1 and decisions[0]["goal"] == stored["current_goal"]

    # the projection follows the single authoritative decision
    assert env.block(GOAL_BLOCK) == f"Активная цель: {stored['current_goal']}"
    context = env.run(env.cfg("context_only"))["context"]
    assert stored["current_goal"] in context
    assert not [g for g in goals if g != stored["current_goal"] and g in context]


def test_concurrent_episodes_and_a_goal_decision_lose_nothing(env):
    env.run(env.cfg("start_only"))
    gate = env.tmp / "gate"
    writers = 4
    per_writer = 8
    ready = [env.tmp / f"ready.{i}" for i in range(writers + 1)]
    procs = [
        env.spawn(env.cfg("episodes", tag=f"писатель{i}", count=per_writer, gate=str(gate)))
        for i in range(writers)
    ]
    procs.append(env.spawn(env.cfg("accept", goal="Цель среди потока записей", expected_revision=0,
                                   gate=str(gate), ready=str(ready[writers]))))
    _wait_all([ready[writers]])
    time.sleep(0.5)                                      # let the episode writers reach the gate
    gate.touch()
    for proc in procs:
        code, result, err = env.collect(proc)
        assert code == 0 and result is not None and result["ok"], (result, err[-2000:])

    stored = env.notebook()
    contents = [f["content"] for f in stored["known_facts"]]
    for i in range(writers):
        for n in range(per_writer):
            assert any(f"писатель{i} факт номер {n} " in c for c in contents), (i, n)
    assert stored["current_goal"] == "Цель среди потока записей"
    assert stored["goal_revision"] == 1 and stored["goal_decided_by"].startswith("owner:child-")
    assert env.block(GOAL_BLOCK) == "Активная цель: Цель среди потока записей"


# ── Failure between the notebook write and the core block write ───────────────

def test_a_process_dying_between_the_writes_leaves_one_authority_and_is_repaired(env):
    env.run(env.cfg("start_only"))
    proc = env.spawn(env.cfg("accept_then_die", goal="Цель до сбоя", expected_revision=0))
    code, result, _ = env.collect(proc)
    assert code == 17 and result is None                 # died after the first write

    stored = env.notebook()
    assert stored["current_goal"] == "Цель до сбоя"      # the decision is the notebook row
    assert stored["goal_revision"] == 1
    assert env.block(GOAL_BLOCK) == DEFAULT_BLOCK_TEXT   # the projection never happened

    # a reader in another process is not misled by the stale projection
    context = env.run(env.cfg("context_only"))["context"]
    assert "Цель до сбоя" in context and DEFAULT_BLOCK_TEXT not in context

    # the next start repairs the projection from the authoritative record
    assert env.run(env.cfg("start_only"))["in_sync"] is True
    assert env.block(GOAL_BLOCK) == "Активная цель: Цель до сбоя"
    assert env.notebook()["goal_revision"] == 1          # repair did not make a new decision


def test_a_failed_block_write_does_not_undo_or_duplicate_the_decision(env):
    env.run(env.cfg("start_only"))
    first = env.run(env.cfg("accept", goal="Первая цель", expected_revision=0))
    assert first["ok"] and first["in_sync"] is True
    assert env.block(GOAL_BLOCK) == "Активная цель: Первая цель"

    second = env.run(env.cfg("accept_projection_error", goal="Вторая цель", expected_revision=1))
    assert second["ok"] is True and second["in_sync"] is False

    stored = env.notebook()
    assert stored["current_goal"] == "Вторая цель" and stored["goal_revision"] == 2
    assert env.block(GOAL_BLOCK) == "Активная цель: Первая цель"
    context = env.run(env.cfg("context_only"))["context"]
    assert "Вторая цель" in context and "Первая цель" not in context

    assert env.run(env.cfg("start_only"))["in_sync"] is True
    assert env.block(GOAL_BLOCK) == "Активная цель: Вторая цель"
    assert len([i for i in env.notebook()["extracted_intents"] if i.get("kind") == "owner_decision"]) == 2


# ── Stale background analysis from another process ────────────────────────────

def test_analysis_computed_before_a_goal_decision_in_another_process_is_dropped(env):
    env.run(env.cfg("start_only"))
    started, go = env.tmp / "started", env.tmp / "go"
    slow = env.spawn(env.cfg("slow_think", goal="Устаревшее предложение", gap="Устаревший пробел",
                             synthesis="Устаревший синтез", started=str(started), go=str(go)))
    _wait_all([started])                                 # the analysis is in flight, state captured

    decided = env.run(env.cfg("accept", goal="Решение пока считалось", expected_revision=0))
    assert decided["ok"]
    go.touch()                                           # the slow process now finishes and tries to write
    code, result, err = env.collect(slow)
    assert code == 0 and result is not None, err[-2000:]

    stored = env.notebook()
    assert stored["current_goal"] == "Решение пока считалось"
    assert stored["goal_revision"] == 1
    assert stored["proposed_goal"] == ""
    assert not [g for g in stored["open_gaps"] if "Устаревший" in g["gap"]]
    assert not [h for h in stored["synthesis_history"] if "Устаревший" in h["content"]]
    assert env.block(GOAL_BLOCK) == "Активная цель: Решение пока считалось"


def test_analysis_is_kept_when_another_process_only_adds_facts(env):
    env.run(env.cfg("start_only"))
    started, go = env.tmp / "started", env.tmp / "go"
    slow = env.spawn(env.cfg("slow_think", goal="Актуальное предложение", gap="Актуальный пробел",
                             synthesis="Актуальный синтез", started=str(started), go=str(go)))
    _wait_all([started])
    assert env.run(env.cfg("episodes", tag="параллельный", count=3))["ok"]
    go.touch()
    code, result, err = env.collect(slow)
    assert code == 0 and result is not None, err[-2000:]

    stored = env.notebook()
    assert stored["proposed_goal"] == "Актуальное предложение" and stored["proposed_goal_id"]
    assert any(g["gap"] == "Актуальный пробел" for g in stored["open_gaps"])
    assert any(h["content"] == "Актуальный синтез" for h in stored["synthesis_history"])
    assert sum("параллельный" in f["content"] for f in stored["known_facts"]) == 3
    assert stored["current_goal"] == "" and stored["goal_revision"] == 0   # still not accepted


# ── Authority across processes ────────────────────────────────────────────────

@pytest.mark.parametrize(
    "overrides",
    [
        {"sign_secret": "x" * 32},                       # signed with a key the worker does not trust
        {"sign_key_id": "unknown-key"},
    ],
    ids=["wrong-secret", "unknown-key"],
)
def test_a_decision_not_signed_by_the_deployment_key_is_refused(env, overrides):
    env.run(env.cfg("start_only"))
    before = env.raw_notebook()
    result = env.run(env.cfg("accept", goal="Подделка", expected_revision=0, **overrides))
    assert result == {"ok": False, "error": "OwnerAuthorityError"}
    assert env.raw_notebook() == before
    assert env.block(GOAL_BLOCK) == DEFAULT_BLOCK_TEXT


# ── Reads stay inside the project, across processes ───────────────────────────

def test_context_of_one_project_never_contains_the_goal_of_another(env):
    env.run(env.cfg("start_only"))
    for project, goal in (("project-a", "СЕКРЕТНАЯ ЦЕЛЬ А"), ("project-b", "СЕКРЕТНАЯ ЦЕЛЬ Б"),
                          ("velantrim-core", "СЕКРЕТНАЯ ЦЕЛЬ ПО УМОЛЧАНИЮ")):
        assert env.run(env.cfg("accept", project, goal=goal, expected_revision=0))["ok"]

    secrets = {"project-a": "ЦЕЛЬ А", "project-b": "ЦЕЛЬ Б", "velantrim-core": "ПО УМОЛЧАНИЮ"}
    for project, own in secrets.items():
        context = env.run(env.cfg("context_only", project))["context"]
        assert own in context
        assert not [other for p, other in secrets.items() if p != project and other in context], project
    assert env.notebook("project-a")["current_goal"] == "СЕКРЕТНАЯ ЦЕЛЬ А"
