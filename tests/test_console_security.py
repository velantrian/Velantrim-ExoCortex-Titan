"""P1 security regression tests (audit §Приоритет 1).

Covers three closed holes:
  1. Outbound LLM/STT/TTS routes (secure_router) require VELANTRIM_API_KEY.
  2. /console/bootstrap never returns the server key over HTTP.
  3. Velantrim key compare is constant-time (behavior preserved).
Read-only catalog routes (public_router) stay open.
"""

import pytest
from fastapi.testclient import TestClient

import server
from api.web_console import _velantrim_key_analysis

KEY = "secret-test-key-123"


@pytest.fixture
def client():
    return TestClient(server.app)


# ── 1. secure_router requires the server key ───────────────────────────────────

def test_secure_route_blocks_without_key(client, monkeypatch):
    """Key configured + no X-Api-Key → 401. Body is valid, so auth is the only failure."""
    monkeypatch.setattr(server, "API_KEY", KEY)
    r = client.post(
        "/console/llm/test",
        json={"provider": "deepseek", "api_key": "sk-fake-1234567890"},
    )
    assert r.status_code == 401


def test_secure_route_allows_with_key(client, monkeypatch):
    """Correct X-Api-Key passes auth — proven by reaching body validation (422, not 401)."""
    monkeypatch.setattr(server, "API_KEY", KEY)
    r = client.post(
        "/console/llm/test",
        headers={"X-Api-Key": KEY},
        json={"provider": "nope", "api_key": "sk-fake-1234567890"},
    )
    assert r.status_code == 422


def test_secure_route_open_when_no_server_key(client, monkeypatch):
    """Dev/open mode (no VELANTRIM_API_KEY): require_api_key is a no-op."""
    monkeypatch.setattr(server, "API_KEY", "")
    r = client.post(
        "/console/llm/test",
        json={"provider": "nope", "api_key": "sk-fake-1234567890"},
    )
    assert r.status_code == 422  # reached validation without any key


# ── 2. read-only catalog routes stay public even with a key set ────────────────

def test_public_catalog_open_with_key_set(client, monkeypatch):
    monkeypatch.setattr(server, "API_KEY", KEY)
    assert client.get("/tts/catalog").status_code == 200
    assert client.get("/console/llm/providers").status_code == 200


# ── 3. /console/bootstrap never leaks the server key ───────────────────────────

def test_bootstrap_never_leaks_key(client, monkeypatch):
    monkeypatch.setattr(server, "API_KEY", KEY)
    monkeypatch.setenv("VELANTRIM_API_KEY", KEY)
    r = client.get("/console/bootstrap")
    assert r.status_code == 200
    data = r.json()
    assert data["console_api_key"] is None
    assert KEY not in r.text


# ── 4. constant-time compare preserves behavior ───────────────────────────────

def test_key_analysis_matches():
    assert _velantrim_key_analysis("right-key", "right-key")["matches_env"] is True
    assert _velantrim_key_analysis("wrong-key", "right-key")["matches_env"] is False
    assert _velantrim_key_analysis("", "right-key")["matches_env"] is False
    # No expected key configured → auth not required.
    assert _velantrim_key_analysis("anything", "")["matches_env"] is True
