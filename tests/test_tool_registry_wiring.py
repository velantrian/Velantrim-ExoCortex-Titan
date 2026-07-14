"""
core/tool_registry.py used to register every MCP tool as a `lambda: None`
placeholder — the manifest existed but calling any tool silently returned
None instead of doing real work. This locks in that every registered tool
now resolves to its real core.tool_handlers implementation.

NOTE: some other tests in this suite purge `core.*` entries from
sys.modules and reimport them, which can leave a different core.tool_handlers
module object canonical for the rest of the run than the one bound at this
file's collection time. register_velantrim_tools() re-imports tool_handlers
internally at call time, so these tests fetch `handlers` the same way
(inside each test body) to compare against whatever is currently canonical.
"""
from __future__ import annotations

from core.tool_registry import ToolRegistry, register_velantrim_tools


def _handlers():
    from core import tool_handlers as h
    return h


def test_all_registered_tools_are_real_handlers_not_stubs():
    registry = ToolRegistry()
    register_velantrim_tools(registry)

    for name, tool in registry._tools.items():
        assert tool.fn is not None
        # A bare `lambda: None` stub takes zero required arguments and is
        # anonymous; every real handler is either a named function from
        # core.tool_handlers or core.erasure_coordinator.erase_fact_durable.
        assert tool.fn.__name__ != "<lambda>", f"{name} is still a stub lambda"


def test_search_facts_tool_resolves_to_real_handler():
    registry = ToolRegistry()
    register_velantrim_tools(registry)
    assert registry.get_tool("search_facts").fn is _handlers().search_facts


def test_propose_hypothesis_tool_resolves_to_real_handler():
    registry = ToolRegistry()
    register_velantrim_tools(registry)
    assert registry.get_tool("propose_hypothesis").fn is _handlers().propose_hypothesis


def test_forget_fact_tool_resolves_to_durable_coordinator_not_legacy_shim():
    """P0-B: production tools must never reach core.erasure.erase_fact() (the
    deprecated, non-atomic, non-resumable shim) — only the enforced saga
    entrypoint, core.erasure_coordinator.erase_fact_durable().
    """
    from core.erasure_coordinator import erase_fact_durable

    registry = ToolRegistry()
    register_velantrim_tools(registry)
    assert registry.get_tool("forget_fact").fn is erase_fact_durable
