"""H2 regression: the ExperienceReplay → Velum bridge must actually be wired.

The bridge was dead through three independent layers of drift, each masked by
the next:

1. Both blocks did `from core.velum import get_velum`, but `get_velum()` lives
   in `core/velum_bridge.py`. The wrong import was duplicated, so the two
   copies could drift apart independently.
2. Even with the import fixed, the called methods did not exist: Velum has no
   `observe_entities()` and no `_decay_weak_edges()`. Its real API is
   `observe_episode()` / `on_session_end()`.
3. Both are async, and `run()` is synchronous — invoked via
   `asyncio.to_thread` from the sleep worker.

Every failure was funnelled into a `logger.debug` or a bare `except: pass`, so
`velum_edges_boosted` / `velum_edges_decayed` read 0 forever and looked like
"no eligible pairs" rather than "nothing works".

These tests pin: the real singleton is reached, boosting counts real edges,
decay actually lowers the weight of an existing weak edge, failures stay
non-fatal but are counted consistently in both branches, nothing is written to
memory, and no feature default changes.
"""
from __future__ import annotations

import logging

import pytest



def _replay():
    """Return the *live* core.experience_replay module.

    tests/test_cognitive_fact.py purges sys.modules['core.*'], so a module
    object (or a class) captured at import time can be stale by the time these
    tests run: patching the reimported module would then silently miss the
    globals `run()` actually resolves against, and the assertions would pass
    against the real bridge instead of the stub. Resolving at call time is the
    convention tests/test_safe_mode_writes_blocked.py already documents.
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


# ── the bridge resolves to the real module ──────────────────────────────────

def test_get_velum_resolves_from_velum_bridge():
    """The resolver must reach core.velum_bridge, not core.velum."""
    from core.velum_bridge import get_velum as bridge_get_velum

    velum = _replay()._get_velum()
    assert velum is not None
    assert velum is bridge_get_velum(), "must return the process-wide singleton"


def test_get_velum_is_defined_in_velum_bridge_only():
    """Guard the actual defect: core.velum must not be the import source."""
    import core.velum as velum_mod
    import core.velum_bridge as bridge_mod

    assert hasattr(bridge_mod, "get_velum")
    assert not hasattr(velum_mod, "get_velum"), (
        "core.velum unexpectedly exports get_velum — the resolver's assumption changed"
    )


def test_wrong_import_path_is_not_reintroduced():
    """The duplicated bad import must stay gone, in both blocks."""
    import inspect

    source = inspect.getsource(_replay())
    assert "from core.velum import get_velum" not in source
    # A single resolver, not two copies of the lazy import.
    assert source.count("from core.velum_bridge import get_velum") == 1


def test_replay_calls_only_methods_that_exist_on_velum():
    """The second layer of drift: the called methods must be real.

    Fixing the import alone was not enough — `observe_entities()` and
    `_decay_weak_edges()` never existed on `Velum`, so both calls raised
    AttributeError into a swallowing handler. Pin the real API.
    """
    import ast
    import inspect

    from core.velum import Velum

    # Assert over the AST, not the raw text: the prose above names the phantom
    # methods deliberately, and a substring check would match its own docstring.
    tree = ast.parse(inspect.getsource(_replay()))
    accessed = {
        node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)
    }

    for phantom in ("observe_entities", "_decay_weak_edges"):
        assert phantom not in accessed, f"{phantom}() does not exist on Velum"

    for real in ("observe_episode", "on_session_end"):
        assert real in accessed, f"replay no longer calls Velum.{real}"
        assert callable(getattr(Velum, real)), f"Velum.{real} disappeared"


# ── boosting reaches the real singleton ─────────────────────────────────────

def test_cooccurring_facts_invoke_the_real_velum_singleton(monkeypatch: pytest.MonkeyPatch):
    from core.velum import ObserveResult
    from core.velum_bridge import get_velum

    observed: list[list[str]] = []
    velum = get_velum()

    async def spy(episode_id, entities, **kwargs):
        observed.append(list(entities))
        return ObserveResult(
            episode_id=episode_id, entities_seen=len(list(entities)), edges_touched=1
        )

    monkeypatch.setattr(velum, "observe_episode", spy)

    import core.memory as memory_mod

    monkeypatch.setattr(
        memory_mod,
        "get_all_facts",
        lambda *a, **k: [
            _fact("f_a", contexts=["chat:1", "chat:2"]),
            _fact("f_b", contexts=["chat:1", "chat:2"]),
        ],
    )

    report = _replay().ExperienceReplayEngine().run()

    assert report["facts_reactivated"] == 2
    assert observed, "the real Velum singleton was never invoked"
    assert report["errors"] == 0


def test_velum_edges_boosted_is_non_zero_for_eligible_pairs(monkeypatch: pytest.MonkeyPatch):
    import core.memory as memory_mod

    monkeypatch.setattr(
        memory_mod,
        "get_all_facts",
        lambda *a, **k: [
            _fact("f_a", contexts=["ctx:shared"]),
            _fact("f_b", contexts=["ctx:shared"]),
            _fact("f_c", contexts=["ctx:shared"]),
        ],
    )

    report = _replay().ExperienceReplayEngine().run()

    assert report["velum_edges_boosted"] > 0, (
        "boosting still no-ops — the bridge is not reaching Velum"
    )
    assert report["errors"] == 0


def test_no_boost_when_facts_share_no_context(monkeypatch: pytest.MonkeyPatch):
    """Absence of overlap must produce zero, not an error."""
    import core.memory as memory_mod

    monkeypatch.setattr(
        memory_mod,
        "get_all_facts",
        lambda *a, **k: [
            _fact("f_a", contexts=["ctx:one"]),
            _fact("f_b", contexts=["ctx:two"]),
        ],
    )

    report = _replay().ExperienceReplayEngine().run()

    assert report["velum_edges_boosted"] == 0
    assert report["errors"] == 0


# ── decay runs against existing weak edges ──────────────────────────────────

def test_decay_executes_against_existing_weak_edges(monkeypatch: pytest.MonkeyPatch):
    """A weak edge present before the run must actually lose weight."""
    from core.async_utils import run_coroutine_sync
    from core.velum_bridge import get_velum

    velum = get_velum()
    # Seed a genuinely weak edge (one observation → weight 0.12, well below
    # promote_weight=0.6, so on_session_end() decays rather than promotes it).
    run_coroutine_sync(velum.observe_episode("seed", ["stale_a", "stale_b"]))
    seeded = velum._edges[frozenset(("stale_a", "stale_b"))]
    weight_before = seeded.weight
    assert weight_before < velum.params.promote_weight

    import core.memory as memory_mod

    monkeypatch.setattr(
        memory_mod,
        "get_all_facts",
        lambda *a, **k: [
            _fact("f_a", contexts=["ctx:shared"]),
            _fact("f_b", contexts=["ctx:shared"]),
        ],
    )

    report = _replay().ExperienceReplayEngine().run()

    assert report["velum_edges_decayed"] >= 1, "decay never reached Velum"
    assert seeded.weight < weight_before, "the weak edge was not decayed"
    assert report["errors"] == 0


def test_decay_runs_even_when_no_pairs_co_occur(monkeypatch: pytest.MonkeyPatch):
    """Decay is not gated on boosting: an unrelated pair still ages edges."""
    from core.async_utils import run_coroutine_sync
    from core.velum_bridge import get_velum

    velum = get_velum()
    run_coroutine_sync(velum.observe_episode("seed", ["stale_a", "stale_b"]))
    weight_before = velum._edges[frozenset(("stale_a", "stale_b"))].weight

    import core.memory as memory_mod

    monkeypatch.setattr(
        memory_mod,
        "get_all_facts",
        lambda *a, **k: [
            _fact("f_a", contexts=["ctx:one"]),
            _fact("f_b", contexts=["ctx:two"]),
        ],
    )

    report = _replay().ExperienceReplayEngine().run()

    assert report["velum_edges_boosted"] == 0
    assert report["velum_edges_decayed"] >= 1
    assert velum._edges[frozenset(("stale_a", "stale_b"))].weight < weight_before


# ── failures stay non-fatal and are counted consistently ────────────────────

@pytest.mark.parametrize("failing_stage", ["boost", "decay"])
def test_bridge_failure_is_non_fatal_and_counted(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    failing_stage: str,
):
    """Both branches must survive a broken bridge and report it identically.

    Before the fix the decay branch logged at DEBUG and did NOT increment
    errors, while the boost branch did — inconsistent accounting on top of a
    dead path.
    """
    replay_mod = _replay()
    import core.memory as memory_mod

    monkeypatch.setattr(
        memory_mod,
        "get_all_facts",
        lambda *a, **k: [
            _fact("f_a", contexts=["ctx:shared"]),
            _fact("f_b", contexts=["ctx:shared"]),
        ],
    )

    calls = {"n": 0}

    def flaky() -> object:
        calls["n"] += 1
        # boost resolves first, decay second
        if (failing_stage == "boost" and calls["n"] == 1) or (
            failing_stage == "decay" and calls["n"] == 2
        ):
            raise RuntimeError(f"{failing_stage} bridge down")
        from core.velum_bridge import get_velum

        return get_velum()

    monkeypatch.setattr(replay_mod, "_get_velum", flaky)

    with caplog.at_level(logging.WARNING, logger="velantrim.experience_replay"):
        report = replay_mod.ExperienceReplayEngine().run()  # must not raise

    assert report["errors"] >= 1, "a bridge failure must be counted in both branches"
    messages = [r.getMessage() for r in caplog.records if r.levelno >= logging.WARNING]
    assert any(f"{failing_stage} bridge down" in m for m in messages), messages


# ── invariants that must not change ─────────────────────────────────────────

def test_replay_writes_no_facts_and_no_truth_transitions(monkeypatch: pytest.MonkeyPatch):
    """Replay is a Slow Path reinforcement pass, not a writer."""
    import core.memory as memory_mod

    forbidden: list[str] = []
    for name in ("store_fact", "store_facts_batch", "transition_esm", "promote_to_validated"):
        if hasattr(memory_mod, name):
            monkeypatch.setattr(
                memory_mod, name, lambda *a, _n=name, **k: forbidden.append(_n)
            )

    monkeypatch.setattr(
        memory_mod,
        "get_all_facts",
        lambda *a, **k: [
            _fact("f_a", contexts=["ctx:shared"]),
            _fact("f_b", contexts=["ctx:shared"]),
        ],
    )

    _replay().ExperienceReplayEngine().run()

    assert forbidden == [], f"replay performed canonical writes: {forbidden}"


def test_feature_defaults_are_unchanged():
    """The fix must not enable Velum, the sleep worker or replay by default."""
    import os

    from core.feature_config import AppSettings

    defaults = AppSettings()
    assert defaults.enable_velum is False
    assert defaults.velum_persist is False
    # SLEEP_WORKER_ENABLED's code default is read in server.py; assert the env
    # is not being mutated by importing these modules.
    assert os.getenv("ENABLE_VELUM") in (None, "0", "false", "")


def test_production_profile_still_pins_velum_off():
    """docker-compose.prod.yml must not have gained an enable as a side effect."""
    from pathlib import Path

    compose = Path(__file__).resolve().parent.parent / "docker-compose.prod.yml"
    if not compose.is_file():  # pragma: no cover - profile is optional
        pytest.skip("production profile not present")
    text = compose.read_text(encoding="utf-8")
    assert "ENABLE_VELUM=0" in text
    assert "SLEEP_WORKER_ENABLED=false" in text
