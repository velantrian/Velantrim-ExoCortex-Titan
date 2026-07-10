"""
Confirmed issue #5: CORS must allow the MCP-specific headers a browser-based
MCP client sends/reads (X-MCP-Capability, Mcp-Session-Id) — otherwise the
browser blocks the request/response before it ever reaches api/mcp_gateway.py.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import server


@pytest.fixture
def client():
    return TestClient(server.app)


def test_cors_preflight_allows_mcp_headers(client):
    r = client.options(
        "/mcp",
        headers={
            "Origin": "https://example.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "X-MCP-Capability, Mcp-Session-Id",
        },
    )
    allow_headers = r.headers.get("access-control-allow-headers", "")
    assert "X-MCP-Capability" in allow_headers
    assert "Mcp-Session-Id" in allow_headers


def test_cors_exposes_mcp_session_id_header(client):
    r = client.get("/health", headers={"Origin": "https://example.com"})
    expose = r.headers.get("access-control-expose-headers", "")
    assert "Mcp-Session-Id" in expose


def test_mcp_routes_registered(client):
    r = client.get(
        "/mcp",
        headers={"X-Api-Key": server.API_KEY} if server.API_KEY else {},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["protocol"] == "streamable-http"
