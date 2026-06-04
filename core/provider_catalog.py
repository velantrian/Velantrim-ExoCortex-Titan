"""
Единый каталог LLM-провайдеров для API консоли.

Все маршруты /llm/providers должны импортировать ТОЛЬКО отсюда,
чтобы не подхватывать устаревший PROVIDER_CATALOG из кэша llm_router.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from core.gemini_models import GEMINI_CATALOG_REVISION, build_gemini_provider_entry

# Меняйте при обновлении списков моделей — видно в GET /console/llm/providers
CATALOG_BUILD_ID = "2026-06-velantrim-v87-titan-qwen37-deepseekv4"
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
            "deepseek-v4-flash",       # 284B, быстрый, 1M контекст · апрель 2026
            "deepseek-v4-pro",         # 1.6T, флагманский reasoning · апрель 2026
        ],
        "thinking_modes": ["off", "medium", "high"],
    },
    {
        "id": "qwen",
        "title": "Qwen (Alibaba)",
        "default_model": "qwen3.7-max",
        "models": [
            "qwen3.7-max",             # текстовый флагман, 1M контекст, агентный · 21 мая 2026
            "qwen3.7-plus",            # мультимодальный (текст+изображение+видео) · 1 июня 2026
        ],
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
            "claude-sonnet-4-6",       # флагманский эффективный · 17 фев 2026 · 1M контекст
            "claude-opus-4-8",         # самый мощный, reasoning · 28 мая 2026 · 1M контекст
        ],
    },
    {
        "id": "gemini",
        "title": "Google Gemini",
        "default_model": "gemini-3.5-flash",
        "models": [
            "gemini-3.5-flash",        # мультимодальный (текст+изобр+видео+аудио+PDF) · 19 мая 2026 · 1M контекст · GA
        ],
    },
]


def list_providers() -> List[Dict[str, Any]]:
    """Актуальный каталог; Gemini пересобирается при каждом вызове."""
    out: List[Dict[str, Any]] = []
    for p in PROVIDER_CATALOG:
        if p.get("id") == "gemini":
            out.append(build_gemini_provider_entry())
        else:
            out.append(dict(p))
    return out


def get_provider_info(provider_id: str) -> Optional[Dict[str, Any]]:
    key = (provider_id or "").strip().lower()
    for p in PROVIDER_CATALOG:
        if p.get("id") == key:
            if key == "gemini":
                return build_gemini_provider_entry()
            return dict(p)
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
