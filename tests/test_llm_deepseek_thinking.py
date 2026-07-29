# tests/test_llm_deepseek_thinking.py
import asyncio

import httpx
import pytest

import core.llm_router as router
from core.llm_router import (
    LlmCallConfig,
    LlmTransportTimeoutError,
    _deepseek_request_body,
    chat_complete,
    compact_messages_for_deepseek,
    normalize_deepseek_thinking,
)


def test_normalize_xhigh_to_max():
    assert normalize_deepseek_thinking("xhigh") == "max"
    assert normalize_deepseek_thinking("x-high") == "max"


def test_deepseek_thinking_body():
    cfg = LlmCallConfig(
        provider="deepseek",
        api_key="sk-test",
        model="deepseek-v4-pro",
        max_tokens=16000,
        deepseek_thinking="max",
    )
    body = _deepseek_request_body(cfg, [{"role": "user", "content": "hi"}], quick_ping=False)
    assert body["max_tokens"] == 16000
    assert body["thinking"]["type"] == "enabled"
    assert body["reasoning_effort"] == "max"


def test_deepseek_message_content_is_compacted_to_provider_limit():
    long_text = "x" * 5000
    messages = compact_messages_for_deepseek(
        [{"role": "system", "content": long_text}]
    )
    assert len(messages[0]["content"]) <= 4000
    assert "truncated by Velantrim" in messages[0]["content"]

    cfg = LlmCallConfig(provider="deepseek", api_key="sk-test")
    body = _deepseek_request_body(
        cfg,
        [{"role": "user", "content": long_text}],
        quick_ping=False,
    )
    assert len(body["messages"][0]["content"]) <= 4000


def test_chat_complete_normalizes_httpx_timeout(monkeypatch: pytest.MonkeyPatch):
    async def read_timeout(*args, **kwargs):
        raise httpx.ReadTimeout("provider read timed out")

    monkeypatch.setattr(router, "_openai_compatible_chat", read_timeout)
    cfg = LlmCallConfig(
        provider="deepseek",
        api_key="sk-test",
        model="deepseek-v4-flash",
    )

    with pytest.raises(LlmTransportTimeoutError):
        asyncio.run(chat_complete(cfg, "prompt", "system"))
