"""
Confirmed issue #1: MCP capability must be authorized server-side. A client
header may only downgrade the effective capability, never elevate it above
the server-side ceiling (VELANTRIM_MCP_MAX_CAPABILITY, default "reader").
"""
from __future__ import annotations

import pytest

from core.mcp_transport import (
    McpHandler,
    _server_max_capability,
    normalize_capability,
    resolve_authorized_capability,
)


@pytest.fixture(autouse=True)
def _clean_ceiling_env(monkeypatch):
    monkeypatch.delenv("VELANTRIM_MCP_MAX_CAPABILITY", raising=False)


def test_default_ceiling_is_reader():
    assert _server_max_capability() == "reader"


def test_client_cannot_elevate_above_default_ceiling():
    # A client requesting "admin" with no server override gets clamped to "reader".
    assert resolve_authorized_capability("admin") == "reader"
    assert resolve_authorized_capability("guardian") == "reader"


def test_client_can_still_downgrade(monkeypatch):
    monkeypatch.setenv("VELANTRIM_MCP_MAX_CAPABILITY", "admin")
    # Ceiling raised to admin, but a client explicitly asking for less gets less.
    assert resolve_authorized_capability("reader") == "reader"
    assert resolve_authorized_capability("ingester") == "ingester"


def test_server_can_opt_into_higher_ceiling(monkeypatch):
    monkeypatch.setenv("VELANTRIM_MCP_MAX_CAPABILITY", "admin")
    assert resolve_authorized_capability("admin") == "admin"


def test_invalid_ceiling_env_falls_back_to_default(monkeypatch):
    monkeypatch.setenv("VELANTRIM_MCP_MAX_CAPABILITY", "not-a-real-capability")
    assert _server_max_capability() == "reader"
    assert resolve_authorized_capability("admin") == "reader"


def test_unknown_requested_capability_still_raises():
    with pytest.raises(ValueError):
        normalize_capability("not-a-real-capability")


def test_handler_tools_list_hides_destructive_tools_when_clamped():
    handler = McpHandler()
    # Client asks for admin, server ceiling stays default "reader" — the
    # destructive admin-only tools (reset_graph, forget_all, forget_fact)
    # must be physically absent from the manifest, not merely blocked later.
    resp = handler.handle(
        {"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
        capability="admin",
    )
    names = {t["name"] for t in resp["result"]["tools"]}
    assert "reset_graph" not in names
    assert "forget_all" not in names
    assert "search_facts" in names


def test_handler_tools_call_rejects_clamped_destructive_tool():
    handler = McpHandler()
    resp = handler.handle(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "reset_graph", "arguments": {"confirm": True}},
        },
        capability="admin",
    )
    assert resp["error"]["code"] == -32602
