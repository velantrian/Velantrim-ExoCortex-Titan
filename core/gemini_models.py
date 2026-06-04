"""
Каталог моделей Google Gemini (Gemini API / AI Studio).

Источник ID и жизненного цикла:
https://ai.google.dev/gemini-api/docs/models
https://ai.google.dev/gemini-api/docs/caching
"""

from __future__ import annotations

import logging
import re
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_GEMINI_API_BASE = "https://generativelanguage.googleapis.com"

# Устаревшие (отключение 2.0 — июнь 2026); не предлагаем в UI.
_GEMINI_DEPRECATED_IDS: set[str] = {
    "gemini-2.0-flash",
    "gemini-2.0-flash-001",
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash-lite-001",
    "gemini-1.5-pro",
    "gemini-1.5-flash",
    "gemini-pro",
}

# Спецификация: id → метаданные для консоли и бэкенда.
GEMINI_MODEL_SPECS: dict[str, dict[str, Any]] = {
  # --- Gemini 3.x (текст) ---
    "gemini-3.5-flash": {
        "label": "Gemini 3.5 Flash",
        "group": "gemini-3",
        "stage": "stable",
        "role": "chat",
        "implicit_cache": True,
        "explicit_cache": True,
        "cache_min_tokens": 4096,
        "thinking": True,
        "modalities": ["text", "code", "pdf", "image", "video", "audio"],
    },
    "gemini-3-flash-preview": {
        "label": "Gemini 3 Flash (preview)",
        "group": "gemini-3",
        "stage": "preview",
        "role": "chat",
        "implicit_cache": True,
        "explicit_cache": True,
        "cache_min_tokens": 4096,
        "thinking": True,
        "modalities": ["text", "code", "pdf", "image", "video", "audio"],
    },
    "gemini-3.1-pro-preview": {
        "label": "Gemini 3.1 Pro (preview)",
        "group": "gemini-3",
        "stage": "preview",
        "role": "chat",
        "implicit_cache": True,
        "explicit_cache": True,
        "cache_min_tokens": 4096,
        "thinking": True,
        "modalities": ["text", "code", "pdf", "image", "video", "audio"],
    },
    "gemini-3.1-flash-lite": {
        "label": "Gemini 3.1 Flash-Lite",
        "group": "gemini-3",
        "stage": "stable",
        "role": "chat",
        "implicit_cache": True,
        "explicit_cache": True,
        "cache_min_tokens": 4096,
        "thinking": True,
        "modalities": ["text", "code", "pdf", "image", "video", "audio"],
    },
    "gemini-3.1-flash-lite-preview": {
        "label": "Gemini 3.1 Flash-Lite (preview)",
        "group": "gemini-3",
        "stage": "preview",
        "role": "chat",
        "implicit_cache": True,
        "explicit_cache": True,
        "cache_min_tokens": 4096,
        "thinking": True,
        "modalities": ["text", "code", "pdf", "image", "video", "audio"],
        "note": "preview; Google планирует отключение — см. документацию",
    },
    # --- Gemini 2.5 (текст) ---
    "gemini-2.5-pro": {
        "label": "Gemini 2.5 Pro",
        "group": "gemini-2.5",
        "stage": "stable",
        "role": "chat",
        "implicit_cache": True,
        "explicit_cache": True,
        "cache_min_tokens": 2048,
        "thinking": True,
        "modalities": ["text", "code", "pdf", "image", "video", "audio"],
    },
    "gemini-2.5-flash": {
        "label": "Gemini 2.5 Flash",
        "group": "gemini-2.5",
        "stage": "stable",
        "role": "chat",
        "implicit_cache": True,
        "explicit_cache": True,
        "cache_min_tokens": 2048,
        "thinking": True,
        "modalities": ["text", "code", "pdf", "image", "video", "audio"],
    },
    "gemini-2.5-flash-lite": {
        "label": "Gemini 2.5 Flash-Lite",
        "group": "gemini-2.5",
        "stage": "stable",
        "role": "chat",
        "implicit_cache": True,
        "explicit_cache": True,
        "cache_min_tokens": 2048,
        "thinking": True,
        "modalities": ["text", "code", "pdf", "image", "video", "audio"],
    },
    # --- Изображения (Nano Banana) — generateContent, ответы с картинками ---
    "gemini-3-pro-image-preview": {
        "label": "Gemini 3 Pro Image (Nano Banana Pro)",
        "group": "gemini-3-image",
        "stage": "preview",
        "role": "image",
        "implicit_cache": False,
        "explicit_cache": False,
        "cache_min_tokens": 4096,
        "thinking": True,
        "modalities": ["text", "image"],
        "note": "генерация/редактирование изображений; нужен биллинг",
    },
    "gemini-3.1-flash-image-preview": {
        "label": "Gemini 3.1 Flash Image (Nano Banana 2)",
        "group": "gemini-3-image",
        "stage": "preview",
        "role": "image",
        "implicit_cache": False,
        "explicit_cache": False,
        "cache_min_tokens": 4096,
        "thinking": True,
        "modalities": ["text", "image"],
        "note": "быстрая генерация изображений; нужен биллинг",
    },
    "gemini-2.5-flash-image": {
        "label": "Gemini 2.5 Flash Image (Nano Banana)",
        "group": "gemini-2.5-image",
        "stage": "stable",
        "role": "image",
        "implicit_cache": False,
        "explicit_cache": False,
        "cache_min_tokens": 2048,
        "thinking": False,
        "modalities": ["text", "image"],
        "note": "генерация изображений; нужен биллинг",
    },
    # --- Live / native audio (отдельный сценарий; в чате Velantrim — опционально) ---
    "gemini-2.5-flash-native-audio-preview-12-2025": {
        "label": "Gemini 2.5 Flash Live (native audio)",
        "group": "gemini-live",
        "stage": "preview",
        "role": "live",
        "implicit_cache": False,
        "explicit_cache": False,
        "cache_min_tokens": 2048,
        "thinking": False,
        "modalities": ["audio", "text"],
        "note": "Gemini Live API; не для обычного текстового чата",
    },
}

# Порядок в выпадающем списке (сначала актуальные текстовые).
GEMINI_MODEL_ORDER: list[str] = [
    "gemini-3.5-flash",
    "gemini-3.1-pro-preview",
    "gemini-3.1-flash-lite",
    "gemini-3-flash-preview",
    "gemini-3.1-flash-lite-preview",
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-2.5-flash-lite",
    "gemini-3-pro-image-preview",
    "gemini-3.1-flash-image-preview",
    "gemini-2.5-flash-image",
    "gemini-2.5-flash-native-audio-preview-12-2025",
]

GEMINI_CATALOG_REVISION = "2026-05-gemini-v2"

GEMINI_DEFAULT_MODEL = "gemini-2.5-flash"
GEMINI_STT_DEFAULT_MODEL = "gemini-2.5-flash"
GEMINI_STT_FALLBACK_MODELS: tuple[str, ...] = (
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-3.5-flash",
    "gemini-3.1-flash-lite",
)


def normalize_gemini_model_id(raw: str) -> str:
    """models/gemini-2.5-flash → gemini-2.5-flash."""
    s = (raw or "").strip()
    if s.startswith("models/"):
        s = s.split("/", 1)[1]
    return s


def is_gemini_model_deprecated(model_id: str) -> bool:
    mid = normalize_gemini_model_id(model_id)
    if mid in _GEMINI_DEPRECATED_IDS:
        return True
    if mid.startswith("gemini-1."):
        return True
    return False


def gemini_model_meta(model_id: str) -> dict[str, Any]:
    mid = normalize_gemini_model_id(model_id)
    base = dict(GEMINI_MODEL_SPECS.get(mid) or {})
    if not base:
        base = {
            "label": mid,
            "group": "other",
            "stage": "unknown",
            "role": "chat",
            "implicit_cache": True,
            "explicit_cache": True,
            "cache_min_tokens": 2048,
            "thinking": mid.startswith("gemini-3"),
        }
    base["id"] = mid
    return base


def gemini_is_thinking_model(model_id: str) -> bool:
    return bool(gemini_model_meta(model_id).get("thinking"))


def gemini_explicit_cache_min_chars(model_id: str) -> int:
    """Грубая оценка: ~4 символа на токен для порога explicit cache."""
    tokens = int(gemini_model_meta(model_id).get("cache_min_tokens") or 2048)
    return max(8000, tokens * 4)


def gemini_generation_config(
    model_id: str,
    max_tokens: int,
    *,
    for_stt: bool = False,
) -> dict[str, Any]:
    """
    generationConfig для generateContent.
    Gemini 3.x: без temperature (рекомендация Google); STT — низкая temperature.
    """
    cap = min(max(int(max_tokens), 256), 65536)
    mid = normalize_gemini_model_id(model_id)
    cfg: dict[str, Any] = {"maxOutputTokens": cap}
    if for_stt:
        cfg["temperature"] = 0.1
        return cfg
    if mid.startswith("gemini-3"):
        # thinking_level по умолчанию medium для Pro/Flash 3.x
        if gemini_is_thinking_model(mid):
            # REST API: thinkingLevel — MINIMAL | LOW | MEDIUM | HIGH
            cfg["thinkingConfig"] = {"thinkingLevel": "MEDIUM"}
        return cfg
    if mid.startswith("gemini-2.5"):
        cfg["temperature"] = 1.0
        return cfg
    cfg["temperature"] = 0.7
    return cfg


def ordered_gemini_model_ids(extra_ids: list[str] | None = None) -> list[str]:
    """Упорядоченный список ID для каталога провайдера."""
    seen: set[str] = set()
    out: list[str] = []
    for mid in GEMINI_MODEL_ORDER:
        if mid not in seen and not is_gemini_model_deprecated(mid):
            seen.add(mid)
            out.append(mid)
    if extra_ids:
        for raw in extra_ids:
            mid = normalize_gemini_model_id(raw)
            if not mid or mid in seen or is_gemini_model_deprecated(mid):
                continue
            if not mid.startswith("gemini-"):
                continue
            seen.add(mid)
            out.append(mid)
    return out


def build_gemini_provider_entry(
    extra_model_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Запись провайдера gemini для PROVIDER_CATALOG / API."""
    models = ordered_gemini_model_ids(extra_model_ids)
    model_meta = {mid: gemini_model_meta(mid) for mid in models}
    chat_models = [m for m in models if model_meta[m].get("role") == "chat"]
    return {
        "id": "gemini",
        "title": "Google Gemini",
        "default_model": GEMINI_DEFAULT_MODEL,
        "models": models,
        "chat_models": chat_models or models,
        "stt_default_model": GEMINI_STT_DEFAULT_MODEL,
        "stt_models": list(GEMINI_STT_FALLBACK_MODELS),
        "model_meta": model_meta,
        "docs_url": "https://ai.google.dev/gemini-api/docs/models?hl=ru",
        "cache_docs_url": "https://ai.google.dev/gemini-api/docs/caching?hl=ru",
        "catalog_revision": GEMINI_CATALOG_REVISION,
    }


async def fetch_gemini_models_from_api(
    api_key: str,
    *,
    timeout: float = 25.0,
) -> tuple[list[str], list[str]]:
    """
    GET v1beta/models — модели с generateContent, доступные ключу.
    Возвращает (ids, warnings).
    """
    key = (api_key or "").strip()
    if not key:
        return [], ["Пустой API ключ"]
    url = f"{_GEMINI_API_BASE}/v1beta/models"
    headers = {"x-goog-api-key": key}
    warnings: list[str] = []
    ids: list[str] = []
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            page_token: str | None = None
            for _ in range(8):
                params: dict[str, Any] = {"pageSize": 100}
                if page_token:
                    params["pageToken"] = page_token
                resp = await client.get(url, headers=headers, params=params)
                if resp.status_code >= 400:
                    warnings.append(f"models.list HTTP {resp.status_code}")
                    break
                data = resp.json()
                for item in data.get("models") or []:
                    name = item.get("name") or ""
                    mid = normalize_gemini_model_id(name)
                    if not mid.startswith("gemini-"):
                        continue
                    methods = item.get("supportedGenerationMethods") or []
                    if methods and "generateContent" not in methods:
                        continue
                    if is_gemini_model_deprecated(mid):
                        continue
                    ids.append(mid)
                page_token = data.get("nextPageToken")
                if not page_token:
                    break
    except Exception as exc:
        warnings.append(str(exc))
        logger.info("Gemini models.list: %s", exc)
    # Уникальные, стабильный порядок
    unique = ordered_gemini_model_ids(ids)
    return unique, warnings


def merge_gemini_catalog_with_api(
    api_ids: list[str],
) -> dict[str, Any]:
    """Каталог + модели с API (в конец, если новее документации)."""
    return build_gemini_provider_entry(api_ids)


def model_allowed_for_provider(provider: str, model: str) -> bool:
    if provider != "gemini":
        return True
    mid = normalize_gemini_model_id(model)
    if is_gemini_model_deprecated(mid):
        return False
    catalog = set(ordered_gemini_model_ids())
    if mid in catalog:
        return True
    # Допускаем новые gemini-* с API до обновления статического каталога
    return bool(re.match(r"^gemini-[a-z0-9][a-z0-9.-]*$", mid))


__all__ = [
    "GEMINI_DEFAULT_MODEL",
    "GEMINI_MODEL_ORDER",
    "GEMINI_MODEL_SPECS",
    "GEMINI_STT_DEFAULT_MODEL",
    "GEMINI_STT_FALLBACK_MODELS",
    "build_gemini_provider_entry",
    "fetch_gemini_models_from_api",
    "gemini_explicit_cache_min_chars",
    "gemini_generation_config",
    "gemini_is_thinking_model",
    "gemini_model_meta",
    "merge_gemini_catalog_with_api",
    "model_allowed_for_provider",
    "normalize_gemini_model_id",
    "ordered_gemini_model_ids",
]
