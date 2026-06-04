"""Smoke-тесты маршрутов LLM консоли."""

import pytest
from fastapi.testclient import TestClient

import server


@pytest.fixture
def client():
    return TestClient(server.app)


def test_console_llm_providers(client):
    r = client.get("/console/llm/providers")
    assert r.status_code == 200
    data = r.json()
    ids = {p["id"] for p in data["providers"]}
    assert "deepseek" in ids
    assert "gemini" in ids
    ds = next(p for p in data["providers"] if p["id"] == "deepseek")
    assert "deepseek-chat" not in ds["models"]
    assert "deepseek-v4-flash" in ds["models"]


def test_console_llm_test_validation(client, monkeypatch):
    # AUDIT-FIX P1: /console/llm/test now requires the Velantrim key; authenticate
    # so the request reaches body validation (bad provider → 422, not a 401 gate).
    monkeypatch.setattr(server, "API_KEY", "test-key")
    r = client.post(
        "/console/llm/test",
        headers={"X-Api-Key": "test-key"},
        json={"provider": "nope", "api_key": "test-key-12345"},
    )
    assert r.status_code == 422


def test_llm_test_route_exists(client):
    r = client.post(
        "/llm/test",
        json={"provider": "openai", "api_key": "invalid"},
    )
    assert r.status_code in (400, 401, 422)
