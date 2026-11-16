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


def test_deepseek_message_content_is_not_truncated_by_default(
    monkeypatch: pytest.MonkeyPatch,
):
    """The former fixed 4000-character cut is gone (no Titan limit unless configured)."""
    monkeypatch.delenv("DEEPSEEK_MESSAGE_CHAR_LIMIT", raising=False)
    long_text = "x" * 5000
    messages = compact_messages_for_deepseek(
        [{"role": "system", "content": long_text}]
    )
    assert messages == [{"role": "system", "content": long_text}]

    cfg = LlmCallConfig(provider="deepseek", api_key="sk-test")
    body = _deepseek_request_body(
        cfg,
        [{"role": "user", "content": long_text}],
        quick_ping=False,
    )
    assert body["messages"][0]["content"] == long_text


def test_configured_deepseek_message_limit_refuses_instead_of_truncating(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("DEEPSEEK_MESSAGE_CHAR_LIMIT", "4000")
    cfg = LlmCallConfig(provider="deepseek", api_key="sk-test")
    # ValueError base: other tests reload core.* modules mid-session.
    with pytest.raises(ValueError, match="llm_context_limit: .*DEEPSEEK_MESSAGE_CHAR_LIMIT=4000"):
        _deepseek_request_body(
            cfg,
            [{"role": "user", "content": "x" * 5000}],
            quick_ping=False,
        )
    fits = _deepseek_request_body(
        cfg, [{"role": "user", "content": "x" * 4000}], quick_ping=False
    )
    assert fits["messages"][0]["content"] == "x" * 4000


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
