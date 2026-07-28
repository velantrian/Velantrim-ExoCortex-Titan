"""ExperienceReplay must stay analysis-only (post-merge review of PR #66).

History, because the shape of these tests only makes sense with it:

PR #66 fixed a genuinely dead bridge — wrong import, phantom methods, sync/async
mismatch — but in making it live it activated a path that violates
AGENTS.md §"Canonical memory boundary": a background read path mutating
projection state. Review raised four P1s and two P2s against it:

  • cross-loop mutation: `run()` executes in an `asyncio.to_thread` worker while
    the Velum singleton belongs to the server loop; a second `asyncio.run` loop
    around a foreign `asyncio.Lock` races or hangs;
  • `fact_id` values written where ingest writes *entity names*, creating a
    UUID keyspace retrieval never visits;
  • `ENABLE_VELUM=0` ignored, so a disabled feature ran;
  • unbounded pair enumeration, quadratic in eligible facts.

The corrective posture is containment: keep the analysis, emit a bounded
proposal, apply nothing, and say so truthfully in the report. These tests pin
that containment so the mutation cannot creep back in.
"""
from __future__ import annotations

import ast
import inspect

import pytest


def _replay():
    """Return the *live* core.experience_replay module.

    tests/test_cognitive_fact.py purges sys.modules['core.*'], so a module or
    class captured at import time can be stale by the time these tests run and
    a stub patched onto it would silently miss. Same convention as
    tests/test_safe_mode_writes_blocked.py.
    """
    import core.experience_replay as mod

    return mod


def _fact(fact_id: str, *, contexts: list[str], confidence: float = 0.9) -> dict:
    """A fact shaped the way replay's filter expects (usage_count > 0, conf >= 0.6)."""
    return {
        "fact_id": fact_id,
        "confidence": confidence,
        "metadata": {"usage_count": 3, "usage_contexts": contexts},
    }


@pytest.fixture(autouse=True)
def _fresh_velum():
    """Isolate the process-wide Velum singleton per test."""
    from core.velum_bridge import reset_velum

    reset_velum()
    yield
    reset_velum()


def _facts(monkeypatch: pytest.MonkeyPatch, facts: list[dict]) -> None:
    import core.memory as memory_mod

    monkeypatch.setattr(memory_mod, "get_all_facts", lambda *a, **k: facts)


def _shared_pair() -> list[dict]:
    return [
        _fact("f_a", contexts=["ctx:shared"]),
        _fact("f_b", contexts=["ctx:shared"]),
    ]


# ── the mutation path is gone, structurally ─────────────────────────────────

def _called_names(mod) -> set[str]:
    """Every attribute accessed and every bare name called in the module.

    Asserted over the AST rather than the source text: the module docstring
    necessarily names the very symbols that must not be *called*, so a substring
    check would match the prose explaining the fix.
    """
    tree = ast.parse(inspect.getsource(mod))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            names.add(node.attr)
        elif isinstance(node, ast.Name):
            names.add(node.id)
    return names


def test_replay_does_not_mutate_velum_anywhere_in_the_module():
    """No boost, no decay, no sync-bridging of the shared singleton."""
    forbidden = {
        "get_velum",              # singleton lookup → would create it
        "observe_episode",        # boost → projection mutation
        "on_session_end",         # decay/promote → projection mutation
        "run_coroutine_sync",     # cross-loop bridge for a foreign lock
        "observe_entities",       # the original phantom method
        "_decay_weak_edges",      # the original phantom method
    }
    present = _called_names(_replay()) & forbidden
    assert not present, f"replay still reaches for mutation APIs: {sorted(present)}"


def test_replay_does_not_import_the_async_bridge():
    """run_coroutine_sync must not even be imported."""
    tree = ast.parse(inspect.getsource(_replay()))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            imported.update(a.name for a in node.names)
        elif isinstance(node, ast.Import):
            imported.update(a.name for a in node.names)
    assert "run_coroutine_sync" not in imported
    assert "core.async_utils" not in imported


def test_only_the_flag_helper_is_imported_from_velum_bridge():
    """The bridge is touched for `is_velum_enabled` and nothing else."""
    tree = ast.parse(inspect.getsource(_replay()))
    from_bridge: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "core.velum_bridge":
            from_bridge.update(a.name for a in node.names)
    assert from_bridge == {"is_velum_enabled"}, from_bridge


# ── ENABLE_VELUM is respected ───────────────────────────────────────────────

def test_disabled_velum_creates_no_singleton_and_no_error(monkeypatch: pytest.MonkeyPatch):
    """ENABLE_VELUM=0: no singleton, no boost, no decay, no mutation, no error."""
    import core.velum_bridge as bridge

    monkeypatch.setattr(bridge, "is_velum_enabled", lambda: False)
    _facts(monkeypatch, _shared_pair())

    report = _replay().ExperienceReplayEngine().run()

    assert bridge._velum_singleton is None, "Velum was instantiated while disabled"
    assert report["velum_apply_status"] == "skipped"
    assert report["velum_apply_reason"] == "velum_disabled"
    assert report["velum_edges_boosted"] == 0
    assert report["velum_edges_decayed"] == 0
    assert report["errors"] == 0


def test_enabled_velum_still_performs_no_direct_mutation(monkeypatch: pytest.MonkeyPatch):
    """ENABLE_VELUM=1 may analyse, but must not apply in this contained state."""
    import core.velum_bridge as bridge

    monkeypatch.setattr(bridge, "is_velum_enabled", lambda: True)
    _facts(monkeypatch, _shared_pair())

    report = _replay().ExperienceReplayEngine().run()

    assert bridge._velum_singleton is None, "enabled must still not touch the singleton"
    assert report["velum_apply_status"] == "deferred"
    assert report["velum_apply_reason"] == "canonical_async_apply_not_implemented"
    assert report["velum_edges_boosted"] == 0
    assert report["velum_edges_decayed"] == 0
    # The analysis itself still happened — containment is not a silent no-op.
    assert report["facts_reactivated"] == 2
    assert report["proposal_pairs"] == 1


def test_unreadable_flag_fails_closed(monkeypatch: pytest.MonkeyPatch):
    """If the flag cannot be read, treat Velum as off and report it."""
    import core.velum_bridge as bridge

    def boom() -> bool:
        raise RuntimeError("config unavailable")

    monkeypatch.setattr(bridge, "is_velum_enabled", boom)
    _facts(monkeypatch, _shared_pair())

    report = _replay().ExperienceReplayEngine().run()

    assert report["velum_apply_status"] == "skipped"
    assert report["errors"] >= 1, "a failure to read the flag must be visible"


# ── the report tells the truth ──────────────────────────────────────────────

def test_report_never_claims_reinforcement_that_did_not_happen(monkeypatch: pytest.MonkeyPatch):
    """The two edge counters stay zero and the status explains why."""
    import core.velum_bridge as bridge

    monkeypatch.setattr(bridge, "is_velum_enabled", lambda: True)
    _facts(
        monkeypatch,
        [
            _fact("f_a", contexts=["ctx:shared"]),
            _fact("f_b", contexts=["ctx:shared"]),
            _fact("f_c", contexts=["ctx:shared"]),
        ],
    )

    report = _replay().ExperienceReplayEngine().run()

    assert report["velum_edges_boosted"] == 0
    assert report["velum_edges_decayed"] == 0
    assert report["candidate_pairs"] == 3
    assert report["velum_apply_status"] in {"deferred", "skipped"}
    assert report["velum_apply_reason"]


def test_proposal_uses_fact_fields_not_velum_entity_names(monkeypatch: pytest.MonkeyPatch):
    """fact_id must never be presented as a Velum entity identifier.

    Ingest populates Velum with entity *names*; the review found replay writing
    UUID-like fact ids into that same keyspace. The proposal therefore names its
    fields `fact_a`/`fact_b`, leaving the mapping to a future apply service.
    """
    import core.velum_bridge as bridge

    monkeypatch.setattr(bridge, "is_velum_enabled", lambda: True)
    _facts(monkeypatch, _shared_pair())

    engine = _replay().ExperienceReplayEngine()
    engine.run()
    proposal = engine.last_proposal()

    assert proposal == [{"fact_a": "f_a", "fact_b": "f_b", "cooccurrence": 1}]
    for entry in proposal:
        assert "entity" not in " ".join(entry.keys()), (
            "fact ids must not be labelled as entity names"
        )


def test_last_proposal_is_a_copy(monkeypatch: pytest.MonkeyPatch):
    """A caller mutating the returned list must not corrupt engine state."""
    import core.velum_bridge as bridge

    monkeypatch.setattr(bridge, "is_velum_enabled", lambda: True)
    _facts(monkeypatch, _shared_pair())

    engine = _replay().ExperienceReplayEngine()
    engine.run()
    engine.last_proposal().clear()

    assert len(engine.last_proposal()) == 1


# ── bounded work ────────────────────────────────────────────────────────────

def test_proposal_is_bounded_and_says_so(monkeypatch: pytest.MonkeyPatch):
    """Pair enumeration is quadratic; the proposal must cap and admit it."""
    import core.velum_bridge as bridge

    mod = _replay()
    monkeypatch.setattr(bridge, "is_velum_enabled", lambda: True)
    monkeypatch.setattr(mod, "_MAX_PROPOSAL_PAIRS", 5)
    # 8 facts in one shared context → 28 candidate pairs.
    _facts(monkeypatch, [_fact(f"f_{i}", contexts=["ctx:shared"]) for i in range(8)])

    report = mod.ExperienceReplayEngine().run()

    assert report["candidate_pairs"] == 28
    assert report["proposal_pairs"] == 5
    assert report["proposal_truncated"] is True


def test_fact_intake_is_bounded_and_says_so(monkeypatch: pytest.MonkeyPatch):
    """The fact set feeding the quadratic loop is capped, highest confidence first."""
    import core.velum_bridge as bridge

    mod = _replay()
    monkeypatch.setattr(bridge, "is_velum_enabled", lambda: True)
    monkeypatch.setattr(mod, "_MAX_REPLAY_FACTS", 3)
    _facts(
        monkeypatch,
        [
            _fact("f_low", contexts=["ctx:shared"], confidence=0.61),
            _fact("f_hi1", contexts=["ctx:shared"], confidence=0.99),
            _fact("f_hi2", contexts=["ctx:shared"], confidence=0.98),
            _fact("f_hi3", contexts=["ctx:shared"], confidence=0.97),
        ],
    )

    engine = mod.ExperienceReplayEngine()
    report = engine.run()

    assert report["facts_reactivated"] == 4, "the true eligible count is still reported"
    assert report["facts_truncated"] is True
    # 3 kept → 3 pairs, and the least-confident fact is the one dropped.
    assert report["candidate_pairs"] == 3
    seen = {f for p in engine.last_proposal() for f in (p["fact_a"], p["fact_b"])}
    assert "f_low" not in seen


def test_no_truncation_flags_when_within_limits(monkeypatch: pytest.MonkeyPatch):
    import core.velum_bridge as bridge

    monkeypatch.setattr(bridge, "is_velum_enabled", lambda: True)
    _facts(monkeypatch, _shared_pair())

    report = _replay().ExperienceReplayEngine().run()

    assert report["proposal_truncated"] is False
    assert report["facts_truncated"] is False


def test_proposal_is_ranked_by_cooccurrence(monkeypatch: pytest.MonkeyPatch):
    """Strongest overlap first, so a cap keeps the most useful candidates."""
    import core.velum_bridge as bridge

    monkeypatch.setattr(bridge, "is_velum_enabled", lambda: True)
    _facts(
        monkeypatch,
        [
            _fact("f_a", contexts=["c1", "c2", "c3"]),
            _fact("f_b", contexts=["c1", "c2", "c3"]),  # overlap 3 with f_a
            _fact("f_c", contexts=["c1"]),              # overlap 1 with each
        ],
    )

    engine = _replay().ExperienceReplayEngine()
    engine.run()
    strengths = [p["cooccurrence"] for p in engine.last_proposal()]

    assert strengths == sorted(strengths, reverse=True)
    assert engine.last_proposal()[0]["cooccurrence"] == 3


# ── nothing is written ──────────────────────────────────────────────────────

def test_replay_writes_no_facts_and_no_truth_transitions(monkeypatch: pytest.MonkeyPatch):
    """Replay is a Slow Path read, not a writer (I-ER2/I-ER3/I-ER4)."""
    import core.memory as memory_mod
    import core.velum_bridge as bridge

    monkeypatch.setattr(bridge, "is_velum_enabled", lambda: True)

    forbidden: list[str] = []
    for name in (
        "store_fact",
        "store_facts_batch",
        "store_fact_result",
        "transition_esm",
        "promote_to_validated",
        "invalidate_edge",
    ):
        if hasattr(memory_mod, name):
            monkeypatch.setattr(
                memory_mod, name, lambda *a, _n=name, **k: forbidden.append(_n)
            )

    _facts(monkeypatch, _shared_pair())

    _replay().ExperienceReplayEngine().run()

    assert forbidden == [], f"replay performed canonical writes: {forbidden}"


def test_sleep_worker_invocation_creates_no_event_loop_for_velum(monkeypatch: pytest.MonkeyPatch):
    """The cross-loop hazard: run() must not start a loop of its own.

    SleepTimeWorker calls `run()` via `asyncio.to_thread`, so any `asyncio.run`
    inside it builds a second loop in a worker thread — the exact condition that
    races the server loop's Velum lock. Assert no new loop is created, from the
    worker-thread context the sleep worker actually uses.
    """
    import asyncio

    import core.velum_bridge as bridge

    monkeypatch.setattr(bridge, "is_velum_enabled", lambda: True)
    _facts(monkeypatch, _shared_pair())

    created: list[object] = []
    real_new_event_loop = asyncio.new_event_loop
    real_run = asyncio.run

    def spy_new_event_loop(*a, **k):
        created.append("new_event_loop")
        return real_new_event_loop(*a, **k)

    def spy_run(coro, *a, **k):
        created.append("asyncio.run")
        return real_run(coro, *a, **k)

    monkeypatch.setattr(asyncio, "new_event_loop", spy_new_event_loop)
    monkeypatch.setattr(asyncio, "run", spy_run)

    engine = _replay().ExperienceReplayEngine()

    async def as_sleep_worker_does():
        return await asyncio.to_thread(engine.run)

    report = real_run(as_sleep_worker_does())

    assert created == [], f"replay created an event loop: {created}"
    assert report["velum_edges_boosted"] == 0
    assert bridge._velum_singleton is None


# ── defaults and the production profile are untouched ───────────────────────

def test_feature_defaults_are_unchanged():
    """The fix must not enable Velum, the sleep worker or replay by default."""
    from core.feature_config import AppSettings

    defaults = AppSettings()
    assert defaults.enable_velum is False
    assert defaults.velum_persist is False


def test_production_profile_still_pins_velum_off():
    """docker-compose.prod.yml must not have gained an enable as a side effect."""
    from pathlib import Path

    compose = Path(__file__).resolve().parent.parent / "docker-compose.prod.yml"
    if not compose.is_file():  # pragma: no cover - profile is optional
        pytest.skip("production profile not present")
    text = compose.read_text(encoding="utf-8")
    assert "ENABLE_VELUM=0" in text
    assert "SLEEP_WORKER_ENABLED=false" in text
