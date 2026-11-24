"""PR #537 security fix (Manus audit 2026-11-24), P0: LLM provider exception leaks.

End-to-end over HTTP (FastAPI ``TestClient`` against ``server.app``): the
provider is the offline fake from ``test_llm_context_no_silent_truncation``
(real ``core.llm_router`` / ``core.llm_stream`` code builds the exception from
the provider's error body), or a patched call that raises. The synthetic
marker ``SENSITIVE_PROVIDER_ERROR_218`` stands for any provider-controlled
text. It must not reach the HTTP body, ``llm_answer``, ``llm_meta`` or any
log record (message, args or traceback), with ``ENABLE_SOURCE_X_GATE``
unset, ``0`` or ``1``. No network, no model calls, no real keys.
"""

from __future__ import annotations

import importlib
import json
import logging
from typing import Any

import pytest
from fastapi.testclient import TestClient

from tests.test_llm_context_no_silent_truncation import (
    _ALL_SETTINGS,
    DEEPSEEK_MESSAGE_CHAR_LIMIT_ENV,
    SYNTHETIC_KEY,
    _install_fake,
    _query_harness,
)

MARKER = "SENSITIVE_PROVIDER_ERROR_218"
HEADERS = {"X-Api-Key": "ci-test-key"}
FACTS = [{"fact_id": "f1", "claim": "Встреча во вторник.", "source": "memo", "confidence": 0.9}]


class _MarkedError(RuntimeError):
    """Provider-side failure whose message and ``code`` are attacker-controlled."""

    def __init__(self) -> None:
        super().__init__(f"upstream said: {MARKER}")
        self.code = MARKER



@pytest.fixture(autouse=True)
def _known_api_key(monkeypatch):
    # Another test module may re-import ``server`` with a different
    # VELANTRIM_API_KEY; pin the key this file sends (test-local only).
    monkeypatch.setattr(importlib.import_module("server"), "API_KEY", HEADERS["X-Api-Key"])

@pytest.fixture(params=[None, "0", "1"], ids=["flag-unset", "flag-0", "flag-1"])
def flag(request, monkeypatch):
    if request.param is None:
        monkeypatch.delenv("ENABLE_SOURCE_X_GATE", raising=False)
    else:
        monkeypatch.setenv("ENABLE_SOURCE_X_GATE", request.param)
    importlib.import_module("core.feature_config").clear_config_cache()
    yield request.param
    importlib.import_module("core.feature_config").clear_config_cache()


@pytest.fixture
def fake(monkeypatch):
    for n in _ALL_SETTINGS:
        monkeypatch.delenv(n, raising=False)
    monkeypatch.setenv("VELANTRIM_NETWORK_MODE", "allow")
    monkeypatch.setenv("VELANTRIM_REMOTE_DATA_MODE", "allowed")
    return _install_fake(monkeypatch)


@pytest.fixture
def logs(caplog):
    caplog.set_level(logging.DEBUG)
    return caplog


def _srv():
    return importlib.import_module("server")


def _client() -> TestClient:
    return TestClient(_srv().app, raise_server_exceptions=False)


def _log_text(caplog) -> str:
    parts = []
    for r in caplog.records:
        parts.append(r.getMessage())
        if r.exc_info:
            parts.append(logging.Formatter().formatException(r.exc_info))
        if r.exc_text:
            parts.append(r.exc_text)
    return "\n".join(parts)


def _chat_body(**over: Any) -> dict[str, Any]:
    body: dict[str, Any] = {
        "message": "Когда встреча?",
        "llm_provider": "deepseek",
        "llm_api_key": SYNTHETIC_KEY,
        "llm_model": "deepseek-v4-flash",
        "auto_save_memory": False,
        "use_memory": True,
    }
    body.update(over)
    return body


def _chat_setup(monkeypatch, *, offline: str | None):
    srv = _srv()
    monkeypatch.setattr(srv, "pipeline_run", lambda q, mode, domain: {"facts": FACTS, "error": None})
    monkeypatch.setattr(srv, "_console_offline_reply", lambda *a, **k: offline)
    return srv


def _no_marker(*texts: str) -> None:
    for t in texts:
        assert MARKER not in t


# ── /chat ────────────────────────────────────────────────────────────────────


def test_chat_provider_http_error_without_offline_is_safe(flag, fake, logs, monkeypatch):
    _chat_setup(monkeypatch, offline=None)
    fake.error = (500, {"error": {"message": MARKER}})
    r = _client().post("/chat", json=_chat_body(), headers=HEADERS)
    assert r.status_code == 400  # status kept for API compatibility
    _no_marker(r.text, _log_text(logs))
    assert r.json()["detail"].startswith("llm_provider_error")
    assert "HTTP 500" in r.json()["detail"]


def test_chat_provider_raises_without_offline_is_safe(flag, fake, logs, monkeypatch):
    _chat_setup(monkeypatch, offline=None)
    ls = importlib.import_module("core.llm_stream")

    async def boom(*a, **k):
        raise _MarkedError()
    monkeypatch.setattr(ls, "chat_complete_messages", boom)
    r = _client().post("/chat", json=_chat_body(), headers=HEADERS)
    assert r.status_code == 400
    _no_marker(r.text, _log_text(logs))
    assert r.json()["detail"].startswith("llm_provider_error")


def test_chat_offline_fallback_semantics_unchanged(flag, fake, logs, monkeypatch):
    _chat_setup(monkeypatch, offline="OFFLINE_MEMORY_REPLY")
    fake.error = (500, {"error": {"message": MARKER}})
    r = _client().post("/chat", json=_chat_body(), headers=HEADERS)
    assert r.status_code == 200
    data = r.json()
    assert data["reply"] == "OFFLINE_MEMORY_REPLY"
    assert data["from_llm"] is False
    _no_marker(r.text, _log_text(logs))


def test_chat_success_unchanged(flag, fake, logs, monkeypatch):
    _chat_setup(monkeypatch, offline=None)
    r = _client().post("/chat", json=_chat_body(), headers=HEADERS)
    assert r.status_code == 200
    assert r.json()["reply"] == "ok"
    assert r.json()["from_llm"] is True


def test_chat_provider_context_overflow_is_safe_413(flag, fake, logs, monkeypatch):
    _chat_setup(monkeypatch, offline="OFFLINE_MEMORY_REPLY")
    fake.error = (400, {"error": {"message": f"maximum context length is exceeded {MARKER}"}})
    r = _client().post("/chat", json=_chat_body(), headers=HEADERS)
    assert r.status_code == 413
    assert r.json()["detail"].startswith("llm_context_overflow")
    _no_marker(r.text, _log_text(logs))


def test_chat_context_limit_is_safe_413(flag, fake, logs, monkeypatch):
    _chat_setup(monkeypatch, offline="OFFLINE_MEMORY_REPLY")
    monkeypatch.setenv(DEEPSEEK_MESSAGE_CHAR_LIMIT_ENV, "4000")
    r = _client().post("/chat", json=_chat_body(message=MARKER + " " + "q" * 4500), headers=HEADERS)
    assert r.status_code == 413
    assert r.json()["detail"].startswith("llm_context_limit")
    _no_marker(r.text, _log_text(logs))
    assert fake.requests == []


# ── /chat/stream ─────────────────────────────────────────────────────────────


def _sse(text: str) -> list[dict[str, Any]]:
    return [json.loads(line[6:]) for line in text.splitlines() if line.startswith("data: ")]


def test_chat_stream_provider_error_without_offline_is_safe(flag, fake, logs, monkeypatch):
    _chat_setup(monkeypatch, offline=None)
    fake.error = (500, {"error": {"message": MARKER}})
    r = _client().post("/chat/stream", json=_chat_body(), headers=HEADERS)
    assert r.status_code == 200
    events = _sse(r.text)
    assert events[-1]["type"] == "error"
    assert events[-1]["message"].startswith("llm_provider_error")
    _no_marker(r.text, _log_text(logs))


def test_chat_stream_provider_raises_without_offline_is_safe(flag, fake, logs, monkeypatch):
    _chat_setup(monkeypatch, offline=None)
    ls = importlib.import_module("core.llm_stream")

    async def boom(*a, **k):
        raise _MarkedError()
        yield  # pragma: no cover
    monkeypatch.setattr(ls, "stream_chat_events", boom)
    r = _client().post("/chat/stream", json=_chat_body(), headers=HEADERS)
    events = _sse(r.text)
    assert events[-1]["type"] == "error"
    _no_marker(r.text, _log_text(logs))


def test_chat_stream_offline_fallback_unchanged(flag, fake, logs, monkeypatch):
    _chat_setup(monkeypatch, offline="OFFLINE_MEMORY_REPLY")
    fake.error = (500, {"error": {"message": MARKER}})
    r = _client().post("/chat/stream", json=_chat_body(), headers=HEADERS)
    events = _sse(r.text)
    assert events[-1]["type"] == "final"
    assert events[-1]["reply"] == "OFFLINE_MEMORY_REPLY"
    assert events[-1]["from_llm"] is False
    _no_marker(r.text, _log_text(logs))


# ── /query ───────────────────────────────────────────────────────────────────


def _query_post(monkeypatch):
    _query_harness(monkeypatch, FACTS)
    return _client().post("/query", json={"query": "Когда встреча?", "use_llm": True}, headers=HEADERS)


def test_query_provider_http_error_is_safe(flag, fake, logs, monkeypatch):
    fake.error = (500, {"error": {"message": MARKER}})
    r = _query_post(monkeypatch)
    assert r.status_code == 200
    data = r.json()
    _no_marker(r.text, json.dumps(data.get("llm_meta")), str(data.get("llm_answer")), _log_text(logs))
    assert data["llm_meta"]["error"] == "llm_provider_error"
    assert data["llm_meta"]["status_code"] == 500
    assert data["llm_answer"].startswith("[LLM error: llm_provider_error")


def test_query_arbitrary_exception_code_is_not_forwarded(flag, fake, logs, monkeypatch):
    srv = _srv()

    async def boom(q, system=None, override=None):
        raise _MarkedError()
    monkeypatch.setattr(srv, "_llm_generate", boom)
    r = _query_post(monkeypatch)
    data = r.json()
    _no_marker(r.text, json.dumps(data.get("llm_meta")), str(data.get("llm_answer")), _log_text(logs))
    assert data["llm_meta"]["error"] == "llm_provider_error"
    assert "code" not in data["llm_meta"]


def test_query_context_overflow_code_is_kept(flag, fake, logs, monkeypatch):
    fake.error = (400, {"error": {"message": f"maximum context length is exceeded {MARKER}"}})
    r = _query_post(monkeypatch)
    data = r.json()
    _no_marker(r.text, _log_text(logs))
    assert data["llm_meta"]["error"] == "llm_context_overflow"


def test_query_success_unchanged(flag, fake, logs, monkeypatch):
    r = _query_post(monkeypatch)
    data = r.json()
    assert r.status_code == 200
    assert data["llm_answer"] == "ok"
    assert "error" not in (data.get("llm_meta") or {})
