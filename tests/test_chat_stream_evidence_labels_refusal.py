"""POST /chat/stream refuses evidence_labels=true (stream labels are not implemented).

The refusal happens before retrieval, before any provider HTTP call and before auto-save.
With evidence_labels false or absent the stream is unchanged. Fake HTTP client only; no
model or network is called; the API key is synthetic.
"""
from __future__ import annotations

import asyncio
import copy
import importlib
import json
from typing import Any

import httpx
import pytest

SYNTHETIC_KEY = "sk-synthetic-chat-stream-refusal-0001"
FACTS = [{"fact_id": "f-alpha", "claim": "Логи хранятся 30 дней", "source": "ops",
          "confidence": 0.9}]
_LIMIT_ENVS = (
    "DEEPSEEK_MESSAGE_CHAR_LIMIT",
    "LLM_CHAT_HISTORY_MAX_TURNS",
    "CONSOLE_HISTORY_TURN_MAX_CHARS",
    "CONSOLE_PREVIOUS_SUMMARY_MAX_CHARS",
    "CONSOLE_BLOCK_MEMORY_MAX_ITEMS",
)


class _Stream:
    status_code = 200

    async def __aenter__(self) -> _Stream:
        return self

    async def __aexit__(self, *exc: object) -> bool:
        return False

    async def aiter_lines(self):
        yield 'data: {"choices":[{"delta":{"content":"ok"}}]}'
        yield "data: [DONE]"


@pytest.fixture
def harness(monkeypatch: pytest.MonkeyPatch):
    for name in _LIMIT_ENVS:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("VELANTRIM_NETWORK_MODE", "allow")
    monkeypatch.setenv("VELANTRIM_REMOTE_DATA_MODE", "allowed")
    calls: list[dict[str, Any]] = []

    class FakeAsyncClient:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        async def __aenter__(self) -> FakeAsyncClient:
            return self

        async def __aexit__(self, *exc: object) -> bool:
            return False

        async def post(self, url: str, headers: Any = None, json: Any = None, **kw: Any):
            calls.append({"kind": "post", "url": url, "body": copy.deepcopy(json)})
            raise AssertionError("/chat/stream must not post")

        def stream(self, method: str, url: str, headers: Any = None, json: Any = None, **kw):
            calls.append({"kind": "stream", "url": url, "body": copy.deepcopy(json)})
            return _Stream()

    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)
    srv = importlib.import_module("server")
    pipeline_calls: list[str] = []

    def pipeline(q, mode, domain):
        pipeline_calls.append(q)
        return {"facts": copy.deepcopy(FACTS), "error": None}

    monkeypatch.setattr(srv, "pipeline_run", pipeline)
    saves: list[str] = []
    orig = srv._console_autosave_memory

    async def autosave(req, *a, **k):
        saves.append(req.message)
        return await orig(req, *a, **k)

    monkeypatch.setattr(srv, "_console_autosave_memory", autosave)
    return srv, calls, pipeline_calls, saves


def _req(srv, **overrides: Any):
    data: dict[str, Any] = {
        "message": "Меня зовут Руслан. Что с логами?",
        "llm_provider": "deepseek",
        "llm_api_key": SYNTHETIC_KEY,
        "llm_model": "deepseek-v4-flash",
        "auto_save_memory": True,
        "persist_to_system": False,
    }
    data.update(overrides)
    return srv.ChatRequest(**data)


def _events(response) -> list[dict[str, Any]]:
    async def collect() -> list[Any]:
        return [chunk async for chunk in response.body_iterator]

    out = []
    for chunk in asyncio.run(collect()):
        text = chunk.decode() if isinstance(chunk, bytes) else chunk
        out += [json.loads(line[6:]) for line in text.splitlines() if line.startswith("data: ")]
    return out


def test_stream_with_evidence_labels_true_is_refused_before_any_work(harness):
    srv, calls, pipeline_calls, saves = harness
    with pytest.raises(Exception) as info:
        asyncio.run(srv.chat_stream_endpoint(_req(srv, evidence_labels=True)))
    assert getattr(info.value, "status_code", None) == 400
    assert info.value.detail["error_code"] == "evidence_labels_stream_unsupported"
    assert "только в POST /chat" in info.value.detail["message"]
    assert calls == [] and pipeline_calls == [] and saves == []


def test_stream_refusal_over_http_is_a_plain_400_json(harness, monkeypatch):
    srv, calls, pipeline_calls, saves = harness
    from fastapi.testclient import TestClient

    # API-key auth is not under test here; keep the check independent of VELANTRIM_API_KEY.
    monkeypatch.setitem(srv.app.dependency_overrides, srv.require_api_key, lambda: None)

    body = _req(srv, evidence_labels=True).model_dump(exclude_none=True)
    resp = TestClient(srv.app).post("/chat/stream", json=body)
    assert resp.status_code == 400
    assert resp.headers["content-type"].startswith("application/json")
    assert resp.json()["detail"]["error_code"] == "evidence_labels_stream_unsupported"
    assert calls == [] and pipeline_calls == [] and saves == []


@pytest.mark.parametrize("overrides", [{"evidence_labels": False}, {}])
def test_stream_without_evidence_labels_is_unchanged(harness, overrides):
    srv, calls, pipeline_calls, saves = harness
    events = _events(asyncio.run(srv.chat_stream_endpoint(_req(srv, **overrides))))
    assert [e["type"] for e in events] == [
        "essence", "essence", "context", "token", "done", "essence", "final"]
    final = events[-1]
    assert not any(k.startswith(("evidence", "reference")) for k in final)
    assert len(final["memory_saved"]) == 2 and saves == ["Меня зовут Руслан. Что с логами?"]
    assert len(calls) == 1 and calls[0]["kind"] == "stream"
    body = calls[0]["body"]
    assert body["stream"] is True
    system = body["messages"][0]["content"]
    assert "\n- [ops | conf=0.90] Логи хранятся 30 дней" in system
    assert "[ev_" not in system


def test_stream_body_is_identical_for_false_and_absent(harness):
    srv, calls, _, _ = harness
    _events(asyncio.run(srv.chat_stream_endpoint(_req(srv, evidence_labels=False))))
    _events(asyncio.run(srv.chat_stream_endpoint(_req(srv))))
    assert len(calls) == 2
    assert json.dumps(calls[0]["body"], ensure_ascii=False, sort_keys=True) == json.dumps(
        calls[1]["body"], ensure_ascii=False, sort_keys=True)
