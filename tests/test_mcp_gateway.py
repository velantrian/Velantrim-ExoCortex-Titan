"""MCP gateway acceptance tests (RFC 05)."""
from __future__ import annotations

import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.mcp_gateway import register_mcp_routes
from core.mcp_transport import McpHandler, normalize_capability
from core.tool_registry import get_tool_registry, reset_tool_registry


@pytest.fixture
def mcp_client():
    app = FastAPI()
    register_mcp_routes(app)
    with TestClient(app) as client:
        yield client


def test_normalize_capability_defaults_reader():
    assert normalize_capability(None) == "reader"
    assert normalize_capability("guardian") == "guardian"


def test_normalize_capability_rejects_unknown():
    with pytest.raises(ValueError):
        normalize_capability("superuser")


def test_reader_manifest_excludes_write_tools():
    reset_tool_registry()
    reg = get_tool_registry()
    reader = reg.for_capability("reader")
    assert "search_facts" in reader
    assert "store_fact" not in reader
    assert "forget_fact" not in reader


def test_mcp_initialize_and_tools_list(mcp_client):
    init = mcp_client.post(
        "/mcp",
        headers={"X-MCP-Capability": "reader"},
        json={
            "jsonrpc": "2.0",
            "id": "init",
            "method": "initialize",
            "params": {"protocolVersion": "2024-11-05", "capabilities": {}},
        },
    )
    assert init.status_code == 200
    body = init.json()
    assert body["result"]["serverInfo"]["name"] == "velantrim-titan"
    session_id = init.headers.get("Mcp-Session-Id") or body["result"].get("sessionId")
    assert session_id

    listed = mcp_client.post(
        "/mcp",
        headers={
            "X-MCP-Capability": "reader",
            "Mcp-Session-Id": session_id,
        },
        json={
            "jsonrpc": "2.0",
            "id": "listed",
            "method": "tools/list",
            "params": {},
        },
    )
    assert listed.status_code == 200
    names = {t["name"] for t in listed.json()["result"]["tools"]}
    assert "search_facts" in names
    assert "store_fact" not in names


def test_mcp_tools_call_hidden_for_reader(mcp_client):
    resp = mcp_client.post(
        "/mcp",
        headers={"X-MCP-Capability": "reader"},
        json={
            "jsonrpc": "2.0",
            "id": "call",
            "method": "tools/call",
            "params": {
                "name": "store_fact",
                "arguments": {
                    "fact": {"claim": "x", "source": "t"},
                },
            },
        },
    )
    assert resp.status_code == 200
    assert "error" in resp.json()


def test_mcp_sse_returns_session_header(mcp_client):
    with mcp_client.stream(
        "GET",
        "/mcp/sse",
        headers={"X-MCP-Capability": "reader"},
    ) as resp:
        assert resp.headers.get("Mcp-Session-Id")
        chunk = next(resp.iter_text())
        assert "event: endpoint" in chunk
        resp.close()


def test_mcp_handler_tools_call_search():
    reset_tool_registry()
    handler = McpHandler()
    out = handler.handle(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": "search_facts", "arguments": {"query": ""}},
        },
        capability="reader",
    )
    assert out is not None
    assert "result" in out
    content = out["result"]["content"][0]["text"]
    assert json.loads(content) is not None