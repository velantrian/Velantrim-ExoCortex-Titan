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


# --- provider outcome after possible send (2026-10-26) ---------------------

async def test_cancel_after_start_reports_unknown_provider_outcome(cfg, monkeypatch):
    calls, started = [], asyncio.Event()

    async def slow(*a, **k):
        calls.append(1)
        started.set()
        await asyncio.sleep(30)

    monkeypatch.setattr(lr, "_openai_compatible_chat", slow)
    ev = asyncio.Event()
    call = asyncio.create_task(lr.chat_complete(cfg, "hi", cancel_event=ev))
    await started.wait()
    ev.set()
    with pytest.raises(LlmCallCancelledError) as ei:
        await asyncio.wait_for(call, 2)
    assert ei.value.provider_outcome == lr.PROVIDER_OUTCOME_UNKNOWN
    assert calls == [1]  # no hidden retry


async def test_cancel_before_start_reports_not_sent(cfg, monkeypatch):
    monkeypatch.setattr(lr, "_openai_compatible_chat", lambda *a, **k: None)
    ev = asyncio.Event(); ev.set()
    with pytest.raises(LlmCallCancelledError) as ei:
        await lr.chat_complete(cfg, "hi", cancel_event=ev)
    assert ei.value.provider_outcome == lr.PROVIDER_OUTCOME_NOT_SENT


async def test_response_wins_race_with_simultaneous_cancel(cfg, monkeypatch):
    ev = asyncio.Event()

    async def answer(*a, **k):
        ev.set()  # cancel arrives in the same loop tick the response completes
        return "answer"

    monkeypatch.setattr(lr, "_openai_compatible_chat", answer)
    assert await lr.chat_complete(cfg, "hi", cancel_event=ev) == "answer"


@pytest.mark.parametrize(
    "exc, outcome",
    [
        (httpx.ConnectTimeout("c"), lr.PROVIDER_OUTCOME_NOT_SENT),
        (httpx.PoolTimeout("p"), lr.PROVIDER_OUTCOME_NOT_SENT),
        (httpx.ReadTimeout("r"), lr.PROVIDER_OUTCOME_UNKNOWN),
        (httpx.WriteTimeout("w"), lr.PROVIDER_OUTCOME_UNKNOWN),
    ],
)
async def test_timeout_provider_outcome(cfg, monkeypatch, exc, outcome):
    calls = []

    async def to(*a, **k):
        calls.append(1)
        raise exc

    monkeypatch.setattr(lr, "_openai_compatible_chat", to)
    with pytest.raises(LlmTransportTimeoutError) as ei:
        await lr.chat_complete(cfg, "hi", cancel_event=asyncio.Event())
    assert ei.value.provider_outcome == outcome
    assert calls == [1]


async def test_transport_failure_propagates_without_retry(cfg, monkeypatch):
    calls = []

    async def boom(*a, **k):
        calls.append(1)
        raise httpx.RemoteProtocolError("peer closed connection after request")

    monkeypatch.setattr(lr, "_openai_compatible_chat", boom)
    with pytest.raises(httpx.RemoteProtocolError):
        await lr.chat_complete(cfg, "hi", cancel_event=asyncio.Event())
    assert calls == [1]
