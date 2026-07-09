"""Тесты маршрутизатора LLM (без реальных API)."""

import httpx
import pytest

from core.llm_router import (
    LlmCallConfig,
    _gemini_403_hints,
    _gemini_generate_url,
    _http_error,
    get_provider_info,
    list_providers,
)


def test_list_providers_has_five():
    providers = list_providers()
    ids = {p["id"] for p in providers}
    assert ids >= {"openai", "deepseek", "gemini", "openrouter", "anthropic"}


def test_get_provider_info():
    p = get_provider_info("deepseek")
    assert p is not None
    assert p["default_model"] == "deepseek-v4-flash"
    assert set(p["models"]) == {"deepseek-v4-flash", "deepseek-v4-pro"}
    assert "deepseek-chat" not in p["models"]
    assert get_provider_info("unknown") is None


def test_openai_catalog_uses_current_models():
    p = get_provider_info("openai")
    assert p is not None
    assert p["default_model"] == "chat-latest"
    assert p["models"][:3] == ["chat-latest", "gpt-5.5", "gpt-5.5-2026-04-23"]
    assert "gpt-5.5" in p["models"]
    assert "gpt-4o-mini" not in p["models"]
    assert "gpt-4.1-mini" not in p["models"]


def test_llm_config_model():
    cfg = LlmCallConfig(provider="openai", api_key="sk-test", model="chat-latest")
    assert cfg.provider == "openai"


@pytest.mark.asyncio
async def test_chat_complete_unknown_provider():
    from core.llm_router import chat_complete

    cfg = LlmCallConfig(provider="nope", api_key="x", model="m")
    with pytest.raises(ValueError, match="Неизвестный"):
        await chat_complete(cfg, "hi")


def test_gemini_generate_url():
    url = _gemini_generate_url("v1beta", "gemini-2.5-flash")
    assert url.endswith("/v1beta/models/gemini-2.5-flash:generateContent")
    assert "generativelanguage.googleapis.com" in url


def test_gemini_403_hints_mention_cloud_and_openrouter():
    text = _gemini_403_hints("Requests are blocked")
    assert "Generative Language API" in text
    assert "aistudio.google.com" in text
    assert "OpenRouter" in text


def test_http_error_gemini_403_includes_hints():
    resp = httpx.Response(
        403,
        json={
            "error": {
                "code": 403,
                "message": (
                    "Requests to this API generativelanguage.googleapis.com method "
                    "google.ai.generativelanguage.v1beta.GenerativeService.GenerateContent "
                    "are blocked."
                ),
            }
        },
    )
    err = _http_error("gemini", resp)
    msg = str(err)
    assert "HTTP 403" in msg
    assert "Generative Language API" in msg
    assert "blocked" in msg.lower()


def test_get_provider_info_gemini_models():
    p = get_provider_info("gemini")
    assert p is not None
    assert p["default_model"] == "gemini-2.5-flash"
    assert "gemini-2.5-pro" in p["models"]
