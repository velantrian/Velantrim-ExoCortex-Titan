"""Smoke tests for core.tool_handlers + tool_registry wiring."""
from __future__ import annotations

from core.tool_registry import get_tool_registry, reset_tool_registry


def test_registry_tools_are_callable_not_stubs():
    reset_tool_registry()
    reg = get_tool_registry()
    names = [
        "search_facts",
        "get_fact",
        "graph_stats",
        "propose_hypothesis",
        "validate_fact",
        "forget_all",
        "reset_graph",
    ]
    for name in names:
        tools = reg.for_capability("admin")
        assert name in tools
        fn = tools[name].fn
        assert fn is not None
        assert fn.__name__ != "<lambda>"


def test_reset_graph_requires_confirm():
    from core.tool_handlers import reset_graph

    out = reset_graph(confirm=False)
    assert out["ok"] is False


def test_search_facts_empty_query_returns_list():
    from core.tool_handlers import search_facts

    assert isinstance(search_facts(""), list)