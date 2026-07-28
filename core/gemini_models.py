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
    # --- Live / native audio ---
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
    value = (raw or "").strip()
    if value.startswith("models/"):
        value = value.split("/", 1)[1]
    return value


def is_gemini_model_deprecated(model_id: str) -> bool:
    model = normalize_gemini_model_id(model_id)
    if model in _GEMINI_DEPRECATED_IDS:
        return True
    return model.startswith("gemini-1.")


def gemini_model_meta(model_id: str) -> dict[str, Any]:
    model = normalize_gemini_model_id(model_id)
    base = dict(GEMINI_MODEL_SPECS.get(model) or {})
    if not base:
        base = {
            "label": model,
            "group": "other",
            "stage": "unknown",
            "role": "chat",
            "implicit_cache": True,
            "explicit_cache": True,
            "cache_min_tokens": 2048,
            "thinking": model.startswith("gemini-3"),
        }
    base["id"] = model
    return base


def gemini_is_thinking_model(model_id: str) -> bool:
    return bool(gemini_model_meta(model_id).get("thinking"))


def gemini_explicit_cache_min_chars(model_id: str) -> int:
    """Грубая оценка: ~4 символа на токен для порога explicit cache."""
    tokens = int(
        gemini_model_meta(model_id).get("cache_min_tokens") or 2048
    )
    return max(8000, tokens * 4)


def gemini_generation_config(
    model_id: str,
    max_tokens: int,
    *,
    for_stt: bool = False,
) -> dict[str, Any]:
    """Build generationConfig for generateContent."""
    cap = min(max(int(max_tokens), 256), 65536)
    model = normalize_gemini_model_id(model_id)
    config: dict[str, Any] = {"maxOutputTokens": cap}
    if for_stt:
        config["temperature"] = 0.1
        return config
    if model.startswith("gemini-3"):
        if gemini_is_thinking_model(model):
            config["thinkingConfig"] = {"thinkingLevel": "MEDIUM"}
        return config
    if model.startswith("gemini-2.5"):
        config["temperature"] = 1.0
        return config
    config["temperature"] = 0.7
    return config


def ordered_gemini_model_ids(
    extra_ids: list[str] | None = None,
) -> list[str]:
    """Упорядоченный список ID для каталога провайдера."""
    seen: set[str] = set()
    out: list[str] = []
    for model in GEMINI_MODEL_ORDER:
        if model not in seen and not is_gemini_model_deprecated(model):
            seen.add(model)
            out.append(model)
    if extra_ids:
        for raw in extra_ids:
            model = normalize_gemini_model_id(raw)
            if (
                not model
                or model in seen
                or is_gemini_model_deprecated(model)
            ):
                continue
            if not model.startswith("gemini-"):
                continue
            seen.add(model)
            out.append(model)
    return out


def build_gemini_provider_entry(
    extra_model_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Запись провайдера gemini для PROVIDER_CATALOG / API."""
    models = ordered_gemini_model_ids(extra_model_ids)
    model_meta = {model: gemini_model_meta(model) for model in models}
    chat_models = [
        model
        for model in models
        if model_meta[model].get("role") == "chat"
    ]
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
    """GET v1beta/models — models accessible to the supplied key."""
    key = (api_key or "").strip()
    if not key:
        return [], ["Пустой API ключ"]

    from core.remote_egress import ensure_remote_egress_allowed

    url = f"{_GEMINI_API_BASE}/v1beta/models"
    headers = {"x-goog-api-key": key}
    warnings: list[str] = []
    ids: list[str] = []
    try:
        ensure_remote_egress_allowed(
            "remote_model_discovery",
            provider="gemini",
            data_mode="none",
        )
        async with httpx.AsyncClient(timeout=timeout) as client:
            page_token: str | None = None
            for _ in range(8):
                params: dict[str, Any] = {"pageSize": 100}
                if page_token:
                    params["pageToken"] = page_token
                response = await client.get(
                    url,
                    headers=headers,
                    params=params,
                )
                if response.status_code >= 400:
                    warnings.append(
                        f"models.list HTTP {response.status_code}"
                    )
                    break
                data = response.json()
                for item in data.get("models") or []:
                    name = item.get("name") or ""
                    model = normalize_gemini_model_id(name)
                    if not model.startswith("gemini-"):
                        continue
                    methods = (
                        item.get("supportedGenerationMethods")
                        or []
                    )
                    if methods and "generateContent" not in methods:
                        continue
                    if is_gemini_model_deprecated(model):
                        continue
                    ids.append(model)
                page_token = data.get("nextPageToken")
                if not page_token:
                    break
    except Exception as exc:
        warnings.append(str(exc))
        logger.info("Gemini models.list: %s", exc)

    unique = ordered_gemini_model_ids(ids)
    return unique, warnings


def merge_gemini_catalog_with_api(
    api_ids: list[str],
) -> dict[str, Any]:
    """Каталог + модели с API (в конец, если новее документации)."""
    return build_gemini_provider_entry(api_ids)


_GEMINI_MODEL_ID_RE = re.compile(r"^gemini-[a-z0-9][a-z0-9.-]*$")


def assert_safe_gemini_model_id(raw: str) -> str:
    """Вернуть нормализованный model id, безопасный для подстановки в путь URL.

    Это СТРУКТУРНАЯ проверка, отдельная от политики (`model_allowed_for_provider`
    решает про deprecation/каталог). Разделены сознательно: изменение списка
    устаревших моделей не должно начать бросать исключения из глубины сборки URL.

    Зачем вообще: model приходит из тела запроса консоли (`llm_model`) и
    подставляется в *путь* Gemini-эндпоинта. httpx нормализует URL, и это
    измеримо опасно — проверено пробником:

        "../../v1beta/tunedModels"   → путь /v1beta/tunedModels:generateContent
        "gemini-2.5-flash?key=leak"  → query "key=leak:generateContent"
        "gemini-2.5-flash#"          → суффикс :generateContent отброшен

    Во всех случаях запрос уходит с ключом сервера в заголовке
    `x-goog-api-key`, т.е. вызывающий рулит credentialed-запросом (confused
    deputy). Регулярка допускает только один безопасный path-сегмент.
    """
    model_id = normalize_gemini_model_id(raw)
    if not _GEMINI_MODEL_ID_RE.match(model_id):
        raise ValueError(
            "Недопустимый Gemini model id "
            f"{model_id!r}: ожидается ^gemini-[a-z0-9][a-z0-9.-]*$ "
            "(model подставляется в путь URL, поэтому '/', '?', '#' и ':' запрещены)"
        )
    return model_id


def model_allowed_for_provider(provider: str, model: str) -> bool:
    if provider != "gemini":
        return True
    model_id = normalize_gemini_model_id(model)
    if is_gemini_model_deprecated(model_id):
        return False
    catalog = set(ordered_gemini_model_ids())
    if model_id in catalog:
        return True
    return bool(_GEMINI_MODEL_ID_RE.match(model_id))


__all__ = [
    "GEMINI_DEFAULT_MODEL",
    "GEMINI_MODEL_ORDER",
    "GEMINI_MODEL_SPECS",
    "GEMINI_STT_DEFAULT_MODEL",
    "GEMINI_STT_FALLBACK_MODELS",
    "assert_safe_gemini_model_id",
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
