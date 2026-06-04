"""Unified Cognitive Runtime V10 MVP."""

from __future__ import annotations

import asyncio
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture
def rt_db(tmp_path, monkeypatch):
    import core.memory as mem
    from core.cognitive_runtime import reset_cognitive_runtime
    from core.cognitive_store import reset_cognitive_store
    from core.event_bridge import reset_event_handlers
    from core.event_bus import reset_event_bus

    db = str(tmp_path / "rt.db")
    monkeypatch.setenv("VELANTRIM_DB_PATH", db)
    monkeypatch.setenv("ENABLE_COGNITIVE_STORE", "1")
    monkeypatch.setenv("ENABLE_COGNITIVE_RUNTIME", "1")
    monkeypatch.setenv("ENABLE_EVENT_BUS", "1")
    from core.feature_config import clear_config_cache

    clear_config_cache()
    reset_event_bus()
    reset_event_handlers()
    reset_cognitive_store()
    reset_cognitive_runtime()
    store = mem.make_store(db)
    monkeypatch.setattr(mem, "_GLOBAL_STORE", store)
    from core.pipeline import reset_causal_graph

    reset_causal_graph()
    yield store
    reset_cognitive_runtime()
    reset_event_handlers()
    reset_event_bus()
    reset_cognitive_store()
    clear_config_cache()


def test_runtime_write_and_status(rt_db):
    from core.cognitive_runtime import get_cognitive_runtime
    from core.memory import get_fact

    rt = get_cognitive_runtime()
    assert rt.status()["enabled"] is True
    rt.write(
        {
            "fact_id": "rt_1",
            "claim": "Runtime unified write",
            "source": "test",
            "confidence": 0.8,
        }
    )
    assert get_fact("rt_1") is not None
    cf = rt.read("rt_1", include_raw=False)
    assert cf is not None
    assert cf.canonical_text == "Runtime unified write"


def test_runtime_handler_marks_retriever_dirty(rt_db, monkeypatch):
    import core.pipeline as pipe
    from core.cognitive_runtime import register_cognitive_runtime_handlers
    from core.event_bridge import publish_event

    pipe._HYBRID_DIRTY = False
    register_cognitive_runtime_handlers()

    asyncio.run(
        publish_event("fact_created", {"fact_id": "evt_1", "via": "test"})
    )
    assert pipe._HYBRID_DIRTY is True


def test_poly_welt_six_agents():
    from core.poly_welt_registry import list_agents

    agents = list_agents()
    assert len(agents) == 6
    ids = {a["agent_id"] for a in agents}
    assert "agent:poet" in ids
    assert "agent:felis_catus" in ids
