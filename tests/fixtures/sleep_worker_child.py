"""Child process for tests/test_sleep_worker_cross_process.py (not a test module).

Runs ONE scripted action of a SleepTimeWorker against file-backed SQLite databases and
prints a single ``RESULT:{json}`` line. Several of these run at the same time as real,
separate OS processes. The configuration is a JSON string in argv[1].

Modes:
  accept                accept a goal (decision signed here with the test key)
  accept_then_die       as accept, but the process dies right after the notebook commit,
                        before the core block is written
  accept_projection_error  as accept, but the core-block write fails with an OSError
  episodes              append N episodes
  slow_think            run think() whose LLM answer is held until a "go" file appears
  context_only          print the authoritative system_context without starting the worker
  start_only            start and stop (start reconciles the goal projection)
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core import sleep_time_worker as stw  # noqa: E402


def _wait_for(path: str, timeout: float = 60.0) -> None:
    deadline = time.monotonic() + timeout
    while not os.path.exists(path):
        if time.monotonic() > deadline:
            raise TimeoutError(path)
        time.sleep(0.01)


def _worker(cfg: dict, llm_fn=None) -> stw.SleepTimeWorker:
    authority = stw.OwnerGoalAuthority(
        key_id=cfg.get("authority_key_id", "owner-key-1"),
        secret=cfg.get("authority_secret", "k" * 32).encode(),
    )
    return stw.make_sleep_time_worker(
        project_id=cfg["project"], core_blocks_db=cfg["blocks_db"], notebook_db=cfg["notebook_db"],
        llm_fn=llm_fn, owner_authority=authority,
    )


def _decision(cfg: dict) -> stw.OwnerGoalDecision:
    return stw.issue_owner_goal_decision(
        key_id=cfg.get("sign_key_id", "owner-key-1"),
        secret=cfg.get("sign_secret", "k" * 32).encode(),
        project_id=cfg["project"], action="set_goal",
        expected_goal_revision=cfg["expected_revision"], goal=cfg["goal"],
        decided_by=cfg.get("decided_by", f"owner:child-{os.getpid()}"),
    )


async def _drain(w: stw.SleepTimeWorker) -> None:
    if w._bg_tasks:
        await asyncio.gather(*list(w._bg_tasks), return_exceptions=True)


async def run(cfg: dict) -> dict:
    mode = cfg["mode"]

    if mode in ("accept", "accept_then_die", "accept_projection_error"):
        w = _worker(cfg)
        await w.start()
        if cfg.get("ready"):
            Path(cfg["ready"]).touch()
        if cfg.get("gate"):
            _wait_for(cfg["gate"])
        if mode == "accept_then_die":
            def die(self, name, content):  # the process disappears between the two writes
                os._exit(17)
            stw.CoreMemoryBlocks.update = die  # type: ignore[method-assign]
        if mode == "accept_projection_error":
            def broken(self, name, content):
                raise OSError("simulated core block write failure")
            stw.CoreMemoryBlocks.update = broken  # type: ignore[method-assign]
        try:
            nb = await w.accept_goal(_decision(cfg))
        except Exception as exc:  # noqa: BLE001 - reported to the parent
            await w.stop()
            return {"ok": False, "error": type(exc).__name__}
        result = {"ok": True, "goal_revision": nb.goal_revision, "in_sync": w.goal_projection_in_sync}
        await w.stop()
        return result

    if mode == "episodes":
        w = _worker(cfg)
        await w.start()
        if cfg.get("gate"):
            _wait_for(cfg["gate"])
        errors = []
        for i in range(cfg["count"]):
            try:
                await w.update_from_episode(
                    {"content": f"{cfg['tag']} факт номер {i} достаточно длинный для записи", "source": "user"})
            except Exception as exc:  # noqa: BLE001
                errors.append(type(exc).__name__)
        await _drain(w)
        await w.stop()
        return {"ok": not errors, "errors": errors}

    if mode == "slow_think":
        state = {"armed": False}

        async def llm(prompt: str):
            if not state["armed"]:
                return "[]" if "Какие важные аспекты" in prompt else ""
            if "ГЛАВНАЯ цель" in prompt:
                Path(cfg["started"]).touch()
                _wait_for(cfg["go"])          # held here while another process changes the state
                return cfg["goal"]
            if "Какие важные аспекты" in prompt:
                return json.dumps([{"gap": cfg["gap"], "priority": "high"}])
            if "Составь" in prompt:
                return cfg["synthesis"]
            return ""

        w = _worker(cfg, llm_fn=llm)
        await w.start()
        await w.update_from_episode(
            {"content": "Исходный факт, на котором считается анализ проекта.", "source": "user"})
        await _drain(w)                       # background cycles run unarmed
        w._facts_since_synthesis = stw.SYNTHESIS_EVERY_N_FACTS
        state["armed"] = True
        await w.think()
        state["armed"] = False
        await _drain(w)
        await w.stop()
        return {"ok": True}

    if mode == "context_only":
        w = _worker(cfg)
        return {"ok": True, "context": w.system_context()}

    if mode == "start_only":
        w = _worker(cfg)
        await w.start()
        await w.stop()
        return {"ok": True, "in_sync": w.goal_projection_in_sync}

    raise SystemExit(f"unknown mode {mode}")


if __name__ == "__main__":
    out = asyncio.run(run(json.loads(sys.argv[1])))
    print("RESULT:" + json.dumps(out, ensure_ascii=False), flush=True)
