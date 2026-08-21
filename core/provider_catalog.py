"""
Единый каталог LLM-провайдеров для API консоли.

Все маршруты /llm/providers должны импортировать ТОЛЬКО отсюда,
чтобы не подхватывать устаревший PROVIDER_CATALOG из кэша llm_router.

V1 product rule: every top-level provider advertised here must be a direct
server backend actually executable by ``core.llm_router.chat_complete``.
Provider-specific models can still be reached through OpenRouter without
pretending that Titan implements another direct transport.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from core.gemini_models import GEMINI_CATALOG_REVISION, build_gemini_provider_entry

# Меняйте при обновлении списков моделей — видно в GET /console/llm/providers
CATALOG_BUILD_ID = "2026-08-titan-v1-executable-provider-catalog"
_CATALOG_FILE = Path(__file__).resolve()

OPENAI_MODELS: List[str] = [
    "chat-latest",
    "gpt-5.5",
    "gpt-5.5-2026-04-23",
]

OPENAI_MODEL_META: Dict[str, Dict[str, str]] = {
    "chat-latest": {
        "label": "GPT-5.5 Instant (chat-latest)",
        "mode": "instant",
    },
    "gpt-5.5": {
        "label": "GPT-5.5 Thinking",
        "mode": "thinking",
    },
    "gpt-5.5-2026-04-23": {
        "label": "GPT-5.5 Thinking snapshot 2026-04-23",
        "mode": "thinking",
    },
}

# Direct transports implemented by core.llm_router.chat_complete().
# Keep ids unique. Qwen models are intentionally available through OpenRouter
# until/unless a separate direct Qwen transport is implemented and tested.
PROVIDER_CATALOG: List[Dict[str, Any]] = [
    {
        "id": "openai",
        "title": "OpenAI",
        "default_model": "chat-latest",
        "models": OPENAI_MODELS,
        "model_meta": OPENAI_MODEL_META,
    },
    {
        "id": "deepseek",
        "title": "DeepSeek",
        "default_model": "deepseek-v4-flash",
        "models": [
            "deepseek-v4-flash",
            "deepseek-v4-pro",
        ],
        "thinking_modes": ["off", "medium", "high"],
    },
    build_gemini_provider_entry(),
    {
        "id": "openrouter",
        "title": "OpenRouter",
        "default_model": "openai/chat-latest",
        "models": [
            "openai/chat-latest",
            "openai/gpt-5.5",
            "google/gemini-3.5-flash",
            "deepseek/deepseek-v4-flash",
            "deepseek/deepseek-v4-pro",
            "anthropic/claude-sonnet-4-6",
            "anthropic/claude-opus-4-8",
            "qwen/qwen3.7-max",
            "qwen/qwen3.7-plus",
            "meta-llama/llama-4-maverick",
        ],
    },
    {
        "id": "anthropic",
        "title": "Anthropic Claude",
        "default_model": "claude-sonnet-4-6",
        "models": [
            "claude-sonnet-4-6",
            "claude-opus-4-8",
        ],
    },
]


def list_providers() -> List[Dict[str, Any]]:
    """Актуальный каталог; Gemini пересобирается при каждом вызове."""
    out: List[Dict[str, Any]] = []
    for provider in PROVIDER_CATALOG:
        if provider.get("id") == "gemini":
            out.append(build_gemini_provider_entry())
        else:
            out.append(dict(provider))
    return out


def get_provider_info(provider_id: str) -> Optional[Dict[str, Any]]:
    key = (provider_id or "").strip().lower()
    for provider in PROVIDER_CATALOG:
        if provider.get("id") == key:
            if key == "gemini":
                return build_gemini_provider_entry()
            return dict(provider)
    return None


def catalog_debug_info() -> Dict[str, Any]:
    """Метаданные для /debug/llm-catalog — проверка, что сервер новый."""
    gem = get_provider_info("gemini") or {}
    return {
        "catalog_build_id": CATALOG_BUILD_ID,
        "gemini_catalog_revision": GEMINI_CATALOG_REVISION,
        "catalog_module": str(_CATALOG_FILE),
        "catalog_mtime": _CATALOG_FILE.stat().st_mtime,
        "gemini_default_model": gem.get("default_model"),
        "gemini_model_count": len(gem.get("models") or []),
        "gemini_models_sample": (gem.get("models") or [])[:6],
        "openai_models": (get_provider_info("openai") or {}).get("models"),
        "deepseek_models": (get_provider_info("deepseek") or {}).get("models"),
    }


__all__ = [
    "CATALOG_BUILD_ID",
    "PROVIDER_CATALOG",
    "catalog_debug_info",
    "get_provider_info",
    "list_providers",
]
