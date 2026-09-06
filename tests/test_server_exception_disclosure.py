"""Регрессия: неожиданные 500 не раскрывают сырой текст исключения клиенту."""
from __future__ import annotations

import asyncio
import json
import logging

from fastapi.testclient import TestClient

import server

_SECRET = "SUPER_SECRET_INTERNAL_VALUE"
_KEY = "secret-test-key-exception-disclosure"


@pytest.fixture
def client():
    return TestClient(server.app)


def test_generic_handler_hides_internal_exception_text(caplog):
    """A+B: глобальный handler отдаёт стабильный error id и логирует исключение."""
    with caplog.at_level(logging.ERROR, logger="velantrim.server"):
        response = asyncio.run(
            server.generic_exception_handler(object(), RuntimeError(_SECRET))
        )

    assert response.status_code == 500
    payload = json.loads(response.body)
    body_text = response.body.decode("utf-8")
    assert payload == {"error": "internal_server_error"}
    assert "detail" not in payload
    assert _SECRET not in body_text
    assert "internal_server_error" in body_text
    assert "Unhandled exception" in caplog.text
    assert _SECRET in caplog.text


def test_generic_handler_wired_through_fastapi(client):
    """A: RuntimeError через реальный ASGI-стек не попадает в тело ответа."""

    async def _boom():
        raise RuntimeError(_SECRET)

    path = "/__test_only_internal_exception_disclosure__"
    server.app.add_api_route(path, _boom, methods=["GET"])
    added = next(
        route
        for route in server.app.router.routes
        if getattr(route, "path", None) == path
    )
    try:
        response = client.get(path)
    finally:
        server.app.router.routes.remove(added)

    assert response.status_code == 500
    payload = response.json()
    assert payload == {"error": "internal_server_error"}
    assert _SECRET not in response.text
    assert "detail" not in payload


def test_query_invalid_profile_keeps_safe_validation_detail(client, monkeypatch):
    """C: ожидаемая 400-валидация по-прежнему возвращает понятный detail."""
    monkeypatch.setattr(server, "API_KEY", _KEY)
    response = client.post(
        "/query",
        headers={"X-Api-Key": _KEY},
        json={"query": "проверка валидации", "profile": "not-a-real-profile"},
    )

    assert response.status_code == 400
    detail = response.json().get("detail", "")
    assert "Неизвестный profile" in detail
    assert "not-a-real-profile" in detail
    assert response.json().get("error") != "internal_server_error"
    assert _SECRET not in response.text


def test_agent_notebook_500_does_not_disclose_exception(client, monkeypatch, caplog):
    """D: локальный внутренний 5xx SleepTimeWorker не раскрывает str(exc)."""

    class _BoomWorker:
        async def get_notebook(self):
            raise RuntimeError(_SECRET)

    monkeypatch.setattr(server, "API_KEY", _KEY)
    monkeypatch.setattr(server, "_sleep_worker", _BoomWorker())

    with caplog.at_level(logging.ERROR, logger="velantrim.server"):
        response = client.get("/agent/notebook", headers={"X-Api-Key": _KEY})

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error"}
    assert _SECRET not in response.text
    assert "agent/notebook failed" in caplog.text
    assert _SECRET in caplog.text
