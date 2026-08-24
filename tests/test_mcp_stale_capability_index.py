from __future__ import annotations

import json

from core.mcp_transport import McpHandler
from core.tool_registry import ToolRegistry


def test_reregistered_higher_capability_tool_is_hidden_and_blocked(monkeypatch) -> None:
    """A stale derived index must not let a lower capability call a tool
    whose canonical ToolDef was re-registered at a higher capability.

    ToolRegistry currently retains derived visibility membership on same-name
    re-registration. MCP therefore re-checks canonical minimum capability via
    has_tool() and fails closed instead of trusting the stale index alone.
    """
    monkeypatch.setenv("VELANTRIM_MCP_MAX_CAPABILITY", "admin")
    calls = {"count": 0}

    def low_version() -> dict[str, str]:
        return {"version": "reader"}

    def elevated_version() -> dict[str, str]:
        calls["count"] += 1
        return {"version": "admin"}

    registry = ToolRegistry()
    registry.register("same_name", low_version, capability="reader")
    registry.register("same_name", elevated_version, capability="admin")

    # Demonstrate the pre-existing stale derived-index shape explicitly.
    assert "same_name" in registry.for_capability("reader")
    assert registry.has_tool("same_name", "reader") is False

    handler = McpHandler(registry=registry)

    listed = handler.handle(
        {"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
        capability="reader",
    )
    assert listed is not None
    assert [tool["name"] for tool in listed["result"]["tools"]] == []

    blocked = handler.handle(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "same_name", "arguments": {}},
        },
        capability="reader",
    )
    assert blocked is not None
    assert blocked["error"]["code"] == -32602
    assert calls["count"] == 0

    allowed = handler.handle(
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "same_name", "arguments": {}},
        },
        capability="admin",
    )
    assert allowed is not None
    assert allowed["result"]["isError"] is False
    assert json.loads(allowed["result"]["content"][0]["text"]) == {"version": "admin"}
    assert calls["count"] == 1


def test_destructive_tool_is_not_listed_below_admin_even_if_misregistered(monkeypatch) -> None:
    monkeypatch.setenv("VELANTRIM_MCP_MAX_CAPABILITY", "admin")

    registry = ToolRegistry()
    registry.register(
        "danger",
        lambda: {"ran": True},
        capability="reader",
        destructive=True,
    )
    handler = McpHandler(registry=registry)

    listed = handler.handle(
        {"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
        capability="reader",
    )
    assert listed is not None
    assert [tool["name"] for tool in listed["result"]["tools"]] == []

    blocked = handler.handle(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "danger", "arguments": {}},
        },
        capability="reader",
    )
    assert blocked is not None
    assert blocked["error"]["code"] == -32603
