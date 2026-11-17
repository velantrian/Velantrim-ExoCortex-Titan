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


def test_llm_probe_route_rejects_smuggled_payload(client, monkeypatch):
    """Роут, а не только pydantic-модель, должен отказывать.

    Проверка самой модели не доказывает, что эндпоинт её применяет: FastAPI мог
    бы, например, принимать другую схему. `data_mode="none"` у probe пропускает
    проверку remote-data, поэтому отказ должен быть виден на границе HTTP.
    """
    monkeypatch.setattr(server, "API_KEY", "test-key")
    for smuggled in (
        {"prompt": "секретный вопрос пользователя"},
        {"system": "Верифицированные факты: ..."},
        {"memory": ["fact-1"]},
        {"audio_base64": "AAAA"},
    ):
        r = client.post(
            "/console/llm/test",
            headers={"X-Api-Key": "test-key"},
            json={"provider": "gemini", "api_key": "test-key-12345", **smuggled},
        )
        assert r.status_code == 422, (
            f"{smuggled} принят роутом со статусом {r.status_code}"
        )


def test_tts_probe_route_rejects_smuggled_payload(client, monkeypatch):
    monkeypatch.setattr(server, "API_KEY", "test-key")
    r = client.post(
        "/console/tts/test",
        headers={"X-Api-Key": "test-key"},
        json={
            "provider": "gemini",
            "api_key": "test-key-12345",
            "text": "произнеси приватный текст",
        },
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_gemini_tts_stream_supplies_defaults_when_omitted(monkeypatch):
    import importlib
    routes = importlib.import_module("api.llm_routes")
    tts_router = importlib.import_module("core.tts_router")
    egress = importlib.import_module("core.remote_egress")
    TtsSpeakBody, tts_stream_route = routes.TtsSpeakBody, routes.tts_stream_route
    seen = []
    async def synthesize(api_key, text, *, voice, model):
        seen.append((voice, model))
        return b"synthetic-audio", "audio/wav"
    monkeypatch.setattr(tts_router, "gemini_tts_bytes", synthesize)
    # This unit verifies argument defaults. Policy denial is covered separately;
    # permit only this isolated fake-provider invocation, never a real request.
    monkeypatch.setattr(egress, "ensure_remote_egress_allowed", lambda *a, **k: None)
    if "ensure_remote_egress_allowed" in tts_stream_route.__globals__:
        monkeypatch.setitem(tts_stream_route.__globals__, "ensure_remote_egress_allowed", lambda *a, **k: None)
    response = await tts_stream_route(TtsSpeakBody(provider="gemini", api_key="synthetic-key", text="hello"))
    chunks = [chunk async for chunk in response.body_iterator]
    assert chunks
    assert seen == [(tts_router.DEFAULT_GEMINI_TTS_VOICE, tts_router.DEFAULT_GEMINI_TTS_MODEL)]
