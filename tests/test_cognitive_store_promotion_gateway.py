from __future__ import annotations

import ast
from pathlib import Path

import pytest


COGNITIVE_STORE = Path(__file__).resolve().parents[1] / "core" / "cognitive_store.py"


def _transition_node() -> ast.FunctionDef:
    tree = ast.parse(COGNITIVE_STORE.read_text(encoding="utf-8"), filename=str(COGNITIVE_STORE))
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "transition":
            return node
    raise AssertionError("CognitiveFactStore.transition was not found")


@pytest.fixture
def isolated_cognitive_store(tmp_path, monkeypatch):
    import core.memory as memory
    import core.cognitive_store as cognitive_store
    from core.feature_config import clear_config_cache

    db_path = str(tmp_path / "cognitive-promotion.db")
    monkeypatch.setenv("VELANTRIM_DB_PATH", db_path)
    monkeypatch.setenv("ENABLE_COGNITIVE_STORE", "1")
    monkeypatch.setenv("ENABLE_EVENT_BUS", "0")
    clear_config_cache()
    cognitive_store.reset_cognitive_store()

    store = memory.make_store(db_path)
    monkeypatch.setattr(memory, "_GLOBAL_STORE", store)
    monkeypatch.setattr(memory, "_L0", store._l0)

    yield cognitive_store, cognitive_store.get_cognitive_store()

    cognitive_store.reset_cognitive_store()
    clear_config_cache()
    store.close()


def _save_observed(cognitive_store, facade, fact_id: str, *, strong: bool) -> None:
    metadata = {"evidence_refs": ["source-a", "source-b"]} if strong else {}
    confidence = 0.95 if strong else 0.4
    fact = cognitive_store.CognitiveFactStore.create_observed(
        f"claim for {fact_id}",
        "test",
        fact_id=fact_id,
        confidence=confidence,
        metadata=metadata,
    )
    assert facade.save(fact) is True


def test_validated_target_uses_gateway_without_plain_final_ladder_step() -> None:
    node = _transition_node()

    gateway_calls = [
        child
        for child in ast.walk(node)
        if isinstance(child, ast.Call)
        and isinstance(child.func, ast.Attribute)
        and child.func.attr == "promote"
        and isinstance(child.func.value, ast.Name)
        and child.func.value.id == "_cognitive_promotion_gateway"
    ]
    direct_validated_ladder_calls = [
        child
        for child in ast.walk(node)
        if isinstance(child, ast.Call)
        and (
            isinstance(child.func, ast.Name)
            and child.func.id == "promote_esm_to"
            or isinstance(child.func, ast.Attribute)
            and child.func.attr == "promote_esm_to"
        )
        and len(child.args) >= 2
        and isinstance(child.args[1], ast.Constant)
        and child.args[1].value == "Validated"
    ]

    assert len(gateway_calls) == 1
    assert direct_validated_ladder_calls == []


def test_weak_direct_validated_attempt_stops_at_supported_without_event(
    isolated_cognitive_store, monkeypatch
) -> None:
    cognitive_store, facade = isolated_cognitive_store
    fact_id = "cognitive.weak"
    _save_observed(cognitive_store, facade, fact_id, strong=False)

    events = []
    monkeypatch.setattr(
        cognitive_store,
        "_emit_fact_event",
        lambda *args, **kwargs: events.append((args, kwargs)),
    )

    result = facade.transition(fact_id, "Validated", by="cognitive_store")

    assert result is not None
    assert result.epistemic_state == "Supported"
    assert events == []


def test_strong_direct_validated_attempt_commits_and_emits_once(
    isolated_cognitive_store, monkeypatch
) -> None:
    cognitive_store, facade = isolated_cognitive_store
    fact_id = "cognitive.strong"
    _save_observed(cognitive_store, facade, fact_id, strong=True)

    events = []
    monkeypatch.setattr(
        cognitive_store,
        "_emit_fact_event",
        lambda *args, **kwargs: events.append((args, kwargs)),
    )

    result = facade.transition(fact_id, "Validated", by="cognitive_store")

    assert result is not None
    assert result.epistemic_state == "Validated"
    assert len(events) == 1
    assert events[0][0] == (fact_id,)
    assert events[0][1]["event_type"] == "fact_esm_transition"


def test_idempotent_validated_replay_does_not_emit_duplicate_event(
    isolated_cognitive_store, monkeypatch
) -> None:
    cognitive_store, facade = isolated_cognitive_store
    fact_id = "cognitive.idempotent"
    _save_observed(cognitive_store, facade, fact_id, strong=True)
    assert facade.transition(fact_id, "Validated") is not None

    events = []
    monkeypatch.setattr(
        cognitive_store,
        "_emit_fact_event",
        lambda *args, **kwargs: events.append((args, kwargs)),
    )

    replay = facade.transition(fact_id, "Validated")

    assert replay is not None
    assert replay.epistemic_state == "Validated"
    assert events == []


def test_non_validated_ladder_behavior_is_unchanged(isolated_cognitive_store) -> None:
    cognitive_store, facade = isolated_cognitive_store
    fact_id = "cognitive.lower-state"
    _save_observed(cognitive_store, facade, fact_id, strong=False)

    result = facade.transition(fact_id, "Supported", by="cognitive_store")

    assert result is not None
    assert result.epistemic_state == "Supported"


def test_cognitive_runtime_inherits_validated_gate(isolated_cognitive_store) -> None:
    cognitive_store, facade = isolated_cognitive_store
    fact_id = "cognitive.runtime-weak"
    _save_observed(cognitive_store, facade, fact_id, strong=False)

    from core.cognitive_runtime import CognitiveRuntime

    result = CognitiveRuntime().transition(fact_id, "Validated")

    assert result is not None
    assert result.epistemic_state == "Supported"
