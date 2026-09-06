"""Регрессия: неожиданные 500 не раскрывают сырой текст исключения клиенту."""
from __future__ import annotations

import asyncio
import json
import logging
import os

os.environ.setdefault("VELANTRIM_API_KEY", "secret-test-key-exception-disclosure")
os.environ.setdefault("SLEEP_WORKER_ENABLED", "false")
os.environ.setdefault("LLM_PROVIDER", "none")

import importlib

from fastapi.testclient import TestClient

_SECRET = "SUPER_SECRET_INTERNAL_VALUE"
_KEY = "secret-test-key-exception-disclosure"


def _server():
    return importlib.import_module("server")


def _client(server) -> TestClient:
    return TestClient(server.app)


def test_generic_handler_hides_internal_exception_text(caplog):
    """A+B: глобальный handler отдаёт стабильный error id и логирует исключение."""
    server = _server()
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


def test_generic_handler_wired_through_fastapi():
    """A: RuntimeError через реальный ASGI-стек не попадает в тело ответа."""
    server = _server()

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
        # raise_server_exceptions=False: BaseHTTPMiddleware пробрасывает
        # исходное исключение наружу, но handler уже сформировал ответ.
        response = TestClient(server.app, raise_server_exceptions=False).get(path)
    finally:
        server.app.router.routes.remove(added)

    assert response.status_code == 500
    payload = response.json()
    assert payload == {"error": "internal_server_error"}
    assert _SECRET not in response.text
    assert "detail" not in payload


def test_query_invalid_profile_keeps_safe_validation_detail(monkeypatch):
    """C: ожидаемая валидация профиля по-прежнему возвращает понятный detail."""
    server = _server()
    monkeypatch.setattr(server, "API_KEY", _KEY)
    response = _client(server).post(
        "/query",
        headers={"X-Api-Key": _KEY},
        json={"query": "проверка валидации", "profile": "not-a-real-profile"},
    )

    assert response.status_code == 422
    body = response.text
    assert "Неизвестный profile" in body
    assert "not-a-real-profile" in body
    assert response.json().get("error") != "internal_server_error"
    assert _SECRET not in body


def test_agent_notebook_500_does_not_disclose_exception(monkeypatch, caplog):
    """D: локальный внутренний 5xx SleepTimeWorker не раскрывает str(exc)."""

    class _BoomWorker:
        async def get_notebook(self):
            raise RuntimeError(_SECRET)

    server = _server()
    monkeypatch.setattr(server, "API_KEY", _KEY)
    monkeypatch.setattr(server, "_sleep_worker", _BoomWorker())

    with caplog.at_level(logging.ERROR, logger="velantrim.server"):
        response = _client(server).get(
            "/agent/notebook",
            headers={"X-Api-Key": _KEY},
        )

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error"}
    assert _SECRET not in response.text
    assert "agent/notebook failed" in caplog.text
    assert _SECRET in caplog.text
