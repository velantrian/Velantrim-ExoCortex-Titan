"""
Confirmed issue #1: MCP capability must be authorized server-side. A client
header may only downgrade the effective capability, never elevate it above
the server-side ceiling (VELANTRIM_MCP_MAX_CAPABILITY, default "reader").
"""
from __future__ import annotations

import json

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


def test_handler_tools_call_supersede_fact_atomic_flow_end_to_end(monkeypatch, tmp_path):
    """Confirmed Codex finding: supersede_fact's (old_fact_id, new_fact dict)
    contract must work all the way through the MCP JSON-RPC tools/call path,
    not just as a direct Python call — routes through the atomic
    core.truth_maintenance.supersede() CAS flow built in PR #11."""
    import core.memory as memory_mod

    # Default server ceiling is "reader" (confirmed issue #1) — a real
    # deployment must opt in to "guardian" for this guardian-capability tool
    # to even be visible, same as any other MCP caller would need to.
    monkeypatch.setenv("VELANTRIM_MCP_MAX_CAPABILITY", "guardian")

    fresh = memory_mod.make_store(str(tmp_path / "mcp_supersede.db"))
    monkeypatch.setattr(memory_mod, "_GLOBAL_STORE", fresh)

    old_id, new_id = "old.mcp.fact", "new.mcp.fact"
    memory_mod.store_fact({
        "fact_id": old_id, "claim": "old", "source": "test", "confidence": 0.9,
        "metadata": {"evidence_refs": ["a", "b", "c", "d", "e"]},
    })
    memory_mod.transition_esm(old_id, "Hypothesized", by="test")
    memory_mod.transition_esm(old_id, "Supported", by="test")
    memory_mod.transition_esm(old_id, "Validated", by="test")

    handler = McpHandler()
    resp = handler.handle(
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "supersede_fact",
                "arguments": {
                    "old_fact_id": old_id,
                    "new_fact": {
                        "fact_id": new_id,
                        "claim": "new",
                        "source": "test",
                        "confidence": 0.95,
                        "metadata": {"evidence_refs": ["a", "b", "c", "d", "e"]},
                    },
                },
            },
        },
        capability="guardian",
    )

    assert resp["result"]["isError"] is False
    payload = json.loads(resp["result"]["content"][0]["text"])
    assert payload["superseded"] is True
    assert payload["new_fact_id"] == new_id
    assert memory_mod.get_fact(old_id)["epistemic_state"] == "Deprecated"
    assert memory_mod.get_fact(new_id)["epistemic_state"] == "Validated"
