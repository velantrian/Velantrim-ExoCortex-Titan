"""Derived causal persistence may re-enter local admission, never replace local Canon.

Issue #286 / PR #287. Neo4j/Graphiti is a downstream projection. Availability,
emptiness, or stale remote state is therefore not authority to erase SQLite relations.
"""
from __future__ import annotations

import asyncio
from pathlib import Path

import core.causal_persistence as causal_persistence


class _StatsGraph:
    def __init__(self, total_relations: int) -> None:
        self.total_relations = total_relations

    def stats(self) -> dict[str, int]:
        return {"total_relations": self.total_relations}


def test_reload_re_admits_without_destructive_reset(monkeypatch):
    calls: list[bool] = []

    async def fake_import(graphiti, *, merge: bool = True) -> int:
        calls.append(merge)
        return 0

    monkeypatch.setattr(causal_persistence, "import_graph_to_causal", fake_import)
    monkeypatch.setattr(
        causal_persistence,
        "get_causal_graph",
        lambda: _StatsGraph(total_relations=7),
    )

    result = asyncio.run(causal_persistence.reload_causal_from_graph(object()))

    assert calls == [True]
    assert result == {"imported": 0, "relation_count": 7}


def test_derived_reload_surfaces_contain_no_local_reset_call():
    persistence = Path("core/causal_persistence.py").read_text(encoding="utf-8")
    adapter = Path("core/graphiti_adapter.py").read_text(encoding="utf-8")

    persistence_start = persistence.index("async def reload_causal_from_graph(")
    persistence_end = persistence.index("\n\n__all__", persistence_start)
    adapter_start = adapter.index("async def reload_causal_from_graphiti(")
    adapter_end = adapter.index("\n\n__all__", adapter_start)

    assert "reset_causal_graph" not in persistence[persistence_start:persistence_end]
    assert "reset_causal_graph" not in adapter[adapter_start:adapter_end]
    assert "merge=True" in persistence[persistence_start:persistence_end]
