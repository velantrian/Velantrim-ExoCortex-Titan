"""causal_bridge + get_causal_graph (V8.6)."""

from __future__ import annotations

import asyncio
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture
def causal_db(tmp_path, monkeypatch):
    import core.memory as mem

    db = str(tmp_path / "causal.db")
    monkeypatch.setenv("VELANTRIM_DB_PATH", db)
    monkeypatch.setenv("ENABLE_CAUSAL_GRAPH", "1")
    from core.feature_config import clear_config_cache

    clear_config_cache()
    store = mem.make_store(db)
    monkeypatch.setattr(mem, "_GLOBAL_STORE", store)
    monkeypatch.setattr(mem, "_L0", store._l0)
    yield db


def test_causal_persistence_import():
    from core.causal_persistence import (
        is_causal_persist_enabled,
        persist_relations_to_graph,
    )

    assert is_causal_persist_enabled() is False

    async def _noop():
        return await persist_relations_to_graph(None, [])

    assert asyncio.run(_noop()) == 0


def test_infer_requires_from_chunk(causal_db):
    from core.causal_graph import get_causal_graph, is_causal_graph_enabled
    from core.memory import store_fact

    assert is_causal_graph_enabled()
    store_fact(
        {
            "fact_id": "fact_a",
            "claim": "A",
            "source": "t",
            "confidence": 0.9,
            "epistemic_state": "Observed",
        }
    )
    store_fact(
        {
            "fact_id": "fact_b",
            "claim": "B",
            "source": "t",
            "confidence": 0.9,
            "epistemic_state": "Observed",
        }
    )

    rids = asyncio.run(
        __import__("core.causal_bridge", fromlist=["infer_requires_from_chunk"]).infer_requires_from_chunk(
            "Система требует Velantrim и память",
            "ep_1",
            ["Velantrim", "память"],
        )
    )
    assert isinstance(rids, list)
    graph = get_causal_graph()
    assert graph is not None
