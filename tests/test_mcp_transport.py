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
from core.tool_registry import PrincipalContext, ToolRegistry


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


# ── Blocker #4: real PrincipalContext injection, not a fake handler-side check ──

def test_tools_call_injects_real_principal_for_needs_principal_tools(monkeypatch):
    """A tool registered with needs_principal=True must receive a
    PrincipalContext whose `capability` is the value THIS call's
    resolve_authorized_capability() actually computed (never a hardcoded
    literal), and whose `credential_fingerprint` is whatever the transport
    passed through — never something the handler invents or assumes for
    itself."""
    monkeypatch.setenv("VELANTRIM_MCP_MAX_CAPABILITY", "admin")

    captured: dict = {}

    def _echo_principal(*, principal: PrincipalContext):
        captured["principal"] = principal
        return {
            "capability": principal.capability,
            "credential_fingerprint": principal.credential_fingerprint,
        }

    registry = ToolRegistry()
    registry.register(
        "echo_principal", _echo_principal, capability="admin",
        destructive=True, needs_principal=True,
    )
    handler = McpHandler(registry=registry)

    resp = handler.handle(
        {
            "jsonrpc": "2.0", "id": 1, "method": "tools/call",
            "params": {"name": "echo_principal", "arguments": {}},
        },
        capability="admin",
        credential_fingerprint="api:realcallerhash",
    )

    assert resp["result"]["isError"] is False
    payload = json.loads(resp["result"]["content"][0]["text"])
    assert payload["capability"] == "admin"
    assert payload["credential_fingerprint"] == "api:realcallerhash"
    assert isinstance(captured["principal"], PrincipalContext)


def test_tools_call_clamps_principal_capability_to_real_ceiling(monkeypatch):
    """A client requesting a higher capability than the server ceiling
    allows must never let a needs_principal tool see the ELEVATED value —
    it must see the SAME clamped capability every other gate in this
    request saw."""
    monkeypatch.delenv("VELANTRIM_MCP_MAX_CAPABILITY", raising=False)  # ceiling stays "reader"

    def _echo_principal(*, principal: PrincipalContext):
        return {"capability": principal.capability}

    registry = ToolRegistry()
    registry.register(
        "echo_principal", _echo_principal, capability="reader", needs_principal=True,
    )
    handler = McpHandler(registry=registry)

    # capability="admin" here mimics a client header BEFORE any transport
    # clamp; handler.handle() itself re-clamps via resolve_authorized_
    # capability() (see McpHandler.handle()'s own docstring/comment).
    resp = handler.handle(
        {
            "jsonrpc": "2.0", "id": 2, "method": "tools/call",
            "params": {"name": "echo_principal", "arguments": {}},
        },
        capability="admin",
        credential_fingerprint="api:someone",
    )

    assert resp["result"]["isError"] is False
    payload = json.loads(resp["result"]["content"][0]["text"])
    assert payload["capability"] == "reader"


def test_credential_fingerprint_defaults_to_anon_when_not_supplied():
    """A caller of McpHandler.handle() (e.g. a future non-HTTP transport)
    that doesn't pass credential_fingerprint must not crash or silently
    invent a fake identity — it gets the same 'api:anon' fallback
    api/mcp_gateway.py itself uses for a request with no API key
    configured."""
    def _echo_principal(*, principal: PrincipalContext):
        return {"credential_fingerprint": principal.credential_fingerprint}

    registry = ToolRegistry()
    registry.register(
        "echo_principal", _echo_principal, capability="reader", needs_principal=True,
    )
    handler = McpHandler(registry=registry)

    resp = handler.handle(
        {
            "jsonrpc": "2.0", "id": 3, "method": "tools/call",
            "params": {"name": "echo_principal", "arguments": {}},
        },
        capability="reader",
    )

    payload = json.loads(resp["result"]["content"][0]["text"])
    assert payload["credential_fingerprint"] == "api:anon"


def test_gateway_derives_credential_fingerprint_from_api_key_hash_not_client_claim():
    """api/mcp_gateway.py._derive_credential_fingerprint() mirrors
    server.py's existing PATCH /facts/{fact_id}/transition precedent: a
    pseudonymous value derived server-side from the API key, never a
    client-suppliable value. Same key -> same fingerprint (deterministic);
    different keys -> different fingerprints; no key -> the same
    'api:anon' fallback used elsewhere."""
    import hashlib

    from api.mcp_gateway import _derive_credential_fingerprint

    assert _derive_credential_fingerprint("") == "api:anon"
    a = _derive_credential_fingerprint("secret-key-one")
    b = _derive_credential_fingerprint("secret-key-two")
    assert a != b
    assert a == _derive_credential_fingerprint("secret-key-one")
    assert a == "api:" + hashlib.sha256(b"secret-key-one").hexdigest()[:8]
