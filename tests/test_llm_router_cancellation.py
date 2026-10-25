"""User/session cancellation of LLM calls is distinct from transport timeout."""
import asyncio

import httpx
import pytest

import core.llm_router as lr
from core.llm_router import LlmCallCancelledError, LlmCallConfig, LlmTransportTimeoutError


@pytest.fixture
def cfg(monkeypatch):
    monkeypatch.setattr(lr, "assert_model_allowed", lambda c: None)
    return LlmCallConfig(provider="openai", api_key="sk-test", model="chat-latest")


async def test_cancel_aborts_inflight_call(cfg, monkeypatch):
    started, aborted = asyncio.Event(), asyncio.Event()

    async def slow(*a, **k):
        started.set()
        try:
            await asyncio.sleep(30)
        except asyncio.CancelledError:
            aborted.set()
            raise
        return "late"

    monkeypatch.setattr(lr, "_openai_compatible_chat", slow)
    ev = asyncio.Event()
    call = asyncio.create_task(lr.chat_complete(cfg, "hi", cancel_event=ev))
    await started.wait()
    ev.set()
    with pytest.raises(LlmCallCancelledError) as ei:
        await asyncio.wait_for(call, 2)
    assert not isinstance(ei.value, TimeoutError)
    assert aborted.is_set()


async def test_cancel_before_start_never_calls_provider(cfg, monkeypatch):
    called = []

    async def fn(*a, **k):
        called.append(1)
        return "x"

    monkeypatch.setattr(lr, "_openai_compatible_chat", fn)
    ev = asyncio.Event(); ev.set()
    with pytest.raises(LlmCallCancelledError):
        await lr.chat_complete(cfg, "hi", cancel_event=ev)
    assert called == []


async def test_timeout_still_timeout_not_cancel(cfg, monkeypatch):
    async def to(*a, **k):
        raise httpx.ReadTimeout("t")

    monkeypatch.setattr(lr, "_openai_compatible_chat", to)
    with pytest.raises(LlmTransportTimeoutError):
        await lr.chat_complete(cfg, "hi", cancel_event=asyncio.Event())


async def test_no_event_unchanged(cfg, monkeypatch):
    async def ok(*a, **k):
        return "ok"

    monkeypatch.setattr(lr, "_openai_compatible_chat", ok)
    assert await lr.chat_complete(cfg, "hi") == "ok"
