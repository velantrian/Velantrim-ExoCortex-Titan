"""
Маршрутизатор LLM для консоли: OpenAI, DeepSeek, Gemini, OpenRouter, Anthropic.

Ключи передаются в запросе (консоль) или из ENV сервера.
Любой серверный remote-вызов проходит обязательный PolicyKernel egress lease.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import httpx

from core.remote_egress import (
    ensure_remote_egress_allowed,
    sanitize_remote_system_prompt,
)

logger = logging.getLogger(__name__)

_DEEPSEEK_MESSAGE_CHAR_LIMIT = 4000
_TRUNCATED_SUFFIX = "\n...[truncated by Velantrim console]"


def _format_api_error_detail(data: Any) -> str:
    """Человекочитаемое сообщение из JSON ошибки провайдера."""
    if isinstance(data, dict):
        err = data.get("error")
        if isinstance(err, dict):
            msg = err.get("message") or err.get("msg")
            code = err.get("code") or err.get("type")
            if msg and code:
                return f"{code}: {msg}"
            if msg:
                return str(msg)
        if data.get("message"):
            return str(data["message"])
        if data.get("detail"):
            return str(data["detail"])
    return str(data)[:500]


def _gemini_403_hints(detail: str = "") -> str:
    """Подсказки при блокировке Generative Language API (часто настройки GCP, не код)."""
    blocked = "blocked" in (detail or "").lower()
    intro = (
        "Запрос к Generative Language API заблокирован (HTTP 403). "
        "Обычно это настройки Google Cloud, а не ошибка Velantrim."
    )
    if blocked:
        intro = (
            "Метод generateContent заблокирован для вашего проекта/ключа (HTTP 403). "
            "Проверьте настройки Google Cloud и ключа API."
        )
    steps = (
        " Шаги: (1) В Google Cloud Console для проекта ключа включите API "
        "«Generative Language API» "
        "(console.cloud.google.com/apis/library/generativelanguage.googleapis.com). "
        "(2) Создайте ключ на https://aistudio.google.com/apikey (Server key, не OAuth). "
        "(3) В ограничениях ключа разрешите только «Generative Language API»; "
        "для серверных запросов не используйте ограничение HTTP referrer / IP, "
        "если клиент не с браузера. "
        "(4) Для gemini-2.5-pro и gemini-3.1-pro-preview может потребоваться биллинг. "
        "(5) Модели 2.0 (gemini-2.0-flash) сняты с поддержки — "
        "используйте gemini-2.5-flash или gemini-3.5-flash. "
        "(6) Если регион блокирует Google AI — OpenRouter → google/gemini-3.5-flash."
    )
    return intro + steps


def _http_error(provider: str, resp: httpx.Response) -> ValueError:
    try:
        payload = resp.json()
        detail = _format_api_error_detail(payload)
    except Exception:
        detail = (resp.text or "")[:400] or resp.reason_phrase
    hints = {
        401: " (неверный или просроченный API ключ)",
        402: " (недостаточно баланса на аккаунте)",
        404: " (модель не найдена — проверьте имя модели)",
        429: " (лимит запросов — повторите позже)",
    }
    hint = hints.get(resp.status_code, "")
    extra = ""
    if provider == "gemini" and resp.status_code == 403:
        extra = " — " + _gemini_403_hints(detail)
    return ValueError(f"{provider}: HTTP {resp.status_code}{hint}{extra} — {detail}")


# Каталог провайдеров: core/provider_catalog.py (единый источник для API)
from core.provider_catalog import (  # noqa: E402,F401
    CATALOG_BUILD_ID,
    PROVIDER_CATALOG,
    get_provider_info,
    list_providers,
)


def normalize_deepseek_thinking(mode: str | None) -> str:
    """off | high | max (xhigh / x-high → max)."""
    m = (mode or "off").strip().lower().replace("-", "").replace("_", "")
    if m in ("off", "disabled", "none", "0", "false"):
        return "off"
    if m in ("max", "xhigh", "xh", "extreme", "thinkmax"):
        return "max"
    if m in ("high", "on", "enabled", "think", "thinking"):
        return "high"
    return "off"


def llm_timeout_for_max_tokens(max_tokens: int, base: float = 90.0) -> float:
    """Длинный ответ — увеличенный таймаут HTTP (до 10 мин)."""
    mt = max(256, min(int(max_tokens or 8192), 40000))
    return min(600.0, base + mt / 64.0)


@dataclass
class LlmCallConfig:
    provider: str
    api_key: str
    model: str | None = None
    max_tokens: int = 8192
    timeout: float = 120.0
    deepseek_thinking: str = "off"


def _resolve_model(cfg: LlmCallConfig) -> str:
    if cfg.model and str(cfg.model).strip():
        return str(cfg.model).strip()
    info = get_provider_info(cfg.provider)
    return info["default_model"] if info else "chat-latest"


def _openai_message_text(message: dict[str, Any]) -> str:
    content = message.get("content")
    if isinstance(content, str) and content.strip():
        return content.strip()
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text", "")))
        joined = "\n".join(p for p in parts if p).strip()
        if joined:
            return joined
    reasoning = message.get("reasoning_content")
    if isinstance(reasoning, str) and reasoning.strip():
        return reasoning.strip()
    return ""


def _openai_stream_delta_parts(delta: dict[str, Any]) -> tuple[str, str]:
    """(content_delta, reasoning_delta) — раздельно для UI thinking."""
    if not isinstance(delta, dict):
        return "", ""
    content = delta.get("content")
    c = content if isinstance(content, str) else ""
    reasoning = delta.get("reasoning_content")
    r = reasoning if isinstance(reasoning, str) else ""
    return c, r


def _openai_stream_delta_text(delta: dict[str, Any]) -> str:
    """Текст из SSE delta (content или reasoning_content у DeepSeek v4)."""
    if not isinstance(delta, dict):
        return ""
    content = delta.get("content")
    if isinstance(content, str) and content:
        return content
    reasoning = delta.get("reasoning_content")
    if isinstance(reasoning, str) and reasoning:
        return reasoning
    return ""


def _deepseek_request_body(
    cfg: LlmCallConfig,
    messages: list[dict[str, str]],
    *,
    quick_ping: bool,
    stream: bool = False,
) -> dict[str, Any]:
    model = _resolve_model(cfg)
    cap = 256 if quick_ping else min(max(int(cfg.max_tokens), 256), 131072)
    body: dict[str, Any] = {
        "model": model,
        "messages": compact_messages_for_deepseek(messages),
        "max_tokens": cap,
        "stream": stream,
    }
    thinking = normalize_deepseek_thinking(getattr(cfg, "deepseek_thinking", "off"))
    if quick_ping or thinking == "off":
        body["thinking"] = {"type": "disabled"}
    else:
        body["thinking"] = {"type": "enabled"}
        body["reasoning_effort"] = "max" if thinking == "max" else "high"
    return body


def _truncate_message_content(
    text: str,
    limit: int = _DEEPSEEK_MESSAGE_CHAR_LIMIT,
) -> str:
    value = str(text or "")
    if len(value) <= limit:
        return value
    keep = max(0, limit - len(_TRUNCATED_SUFFIX))
    return value[:keep].rstrip() + _TRUNCATED_SUFFIX


def compact_messages_for_deepseek(
    messages: list[dict[str, str]],
    *,
    limit: int = _DEEPSEEK_MESSAGE_CHAR_LIMIT,
) -> list[dict[str, str]]:
    """DeepSeek rejects overlong string fields; keep every content string bounded."""
    compacted: list[dict[str, str]] = []
    for msg in messages or []:
        role = str(msg.get("role") or "user")
        content = _truncate_message_content(str(msg.get("content") or ""), limit)
        if content.strip():
            compacted.append({"role": role, "content": content})
    return compacted


def _llm_capability(data_mode: str, *, quick_ping: bool = False) -> str:
    """Название capability для lease.

    `data_mode="none"` разрешён только metadata-only capability (см.
    `remote_egress._METADATA_ONLY_CAPABILITIES`), поэтому connectivity probe
    обязан называться `remote_llm_test` у ВСЕХ провайдеров, а не только там, где
    исторически передавался `quick_ping`. Иначе probe уходил бы под именем
    `remote_llm` с data_mode="none" — то есть обычный чат-путь формально имел бы
    право пропускать проверку remote-data.
    """
    if quick_ping or data_mode == "none":
        return "remote_llm_test"
    return "remote_llm"


async def _openai_compatible_chat(
    cfg: LlmCallConfig,
    prompt: str,
    system: str,
    base_url: str,
    *,
    quick_ping: bool = False,
    data_mode: str = "raw",
) -> str:
    ensure_remote_egress_allowed(
        _llm_capability(data_mode, quick_ping=quick_ping),
        provider=cfg.provider,
        data_mode=data_mode,
    )
    safe_system = (
        system.strip()
        if data_mode == "none"
        else sanitize_remote_system_prompt(system)
    )
    messages: list[dict[str, str]] = []
    if safe_system:
        messages.append({"role": "system", "content": safe_system})
    messages.append({"role": "user", "content": prompt})
    url = base_url.rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {cfg.api_key}",
        "Content-Type": "application/json",
    }
    if cfg.provider == "openrouter":
        headers["HTTP-Referer"] = "https://velantrim.local/console"
        headers["X-Title"] = "VELANTRIM Console"

    if cfg.provider == "deepseek":
        body = _deepseek_request_body(cfg, messages, quick_ping=quick_ping)
    else:
        body = {
            "model": _resolve_model(cfg),
            "messages": messages,
            "max_tokens": cfg.max_tokens,
        }
    async with httpx.AsyncClient(timeout=cfg.timeout) as client:
        resp = await client.post(url, headers=headers, json=body)
        if resp.status_code >= 400:
            raise _http_error(cfg.provider, resp)
        data = resp.json()
        message = data["choices"][0]["message"]
        text = _openai_message_text(message)
        if not text:
            raise ValueError(f"{cfg.provider}: пустой ответ модели")
        return text


_GEMINI_API_BASE = "https://generativelanguage.googleapis.com"


_GEMINI_API_VERSIONS = ("v1beta", "v1")


def _gemini_generate_url(api_version: str, model: str) -> str:
    """Собрать generateContent URL, провалидировав оба path-сегмента.

    Валидация живёт здесь, а не у вызывающих: это точка, где `model` попадает
    в путь, и проверка у вызывающего обходится следующим вызывающим. См.
    `assert_safe_gemini_model_id` о том, что именно и почему запрещено.
    """
    from core.gemini_models import assert_safe_gemini_model_id

    if api_version not in _GEMINI_API_VERSIONS:
        raise ValueError(
            f"Недопустимая версия Gemini API: {api_version!r} "
            f"(ожидается одна из {_GEMINI_API_VERSIONS})"
        )
    safe_model = assert_safe_gemini_model_id(model)
    return f"{_GEMINI_API_BASE}/{api_version}/models/{safe_model}:generateContent"


async def _gemini_post(
    cfg: LlmCallConfig,
    *,
    api_version: str,
    model: str,
    body: dict[str, Any],
) -> httpx.Response:
    """POST generateContent after the caller has acquired an egress lease."""
    url = _gemini_generate_url(api_version, model)
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": cfg.api_key,
    }
    async with httpx.AsyncClient(timeout=cfg.timeout) as client:
        return await client.post(url, headers=headers, json=body)


async def _gemini_chat(
    cfg: LlmCallConfig,
    prompt: str,
    system: str,
    *,
    data_mode: str = "raw",
) -> str:
    from core.gemini_models import (
        gemini_generation_config,
        normalize_gemini_model_id,
    )

    ensure_remote_egress_allowed(
        _llm_capability(data_mode),
        provider=cfg.provider,
        data_mode=data_mode,
    )
    safe_system = (
        system.strip()
        if data_mode == "none"
        else sanitize_remote_system_prompt(system)
    )
    model = normalize_gemini_model_id(_resolve_model(cfg))
    parts = [{"text": prompt}]
    body: dict[str, Any] = {
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": gemini_generation_config(model, cfg.max_tokens),
    }
    if safe_system:
        body["systemInstruction"] = {"parts": [{"text": safe_system}]}

    resp: httpx.Response | None = None
    for api_version in ("v1beta", "v1"):
        resp = await _gemini_post(
            cfg,
            api_version=api_version,
            model=model,
            body=body,
        )
        if resp.status_code < 400:
            break
        if api_version == "v1beta" and resp.status_code in (403, 404):
            logger.info(
                "Gemini %s вернул HTTP %s, пробуем v1",
                api_version,
                resp.status_code,
            )
            continue
        break

    if resp is None or resp.status_code >= 400:
        raise _http_error("gemini", resp)  # type: ignore[arg-type]

    data = resp.json()
    candidates = data.get("candidates") or []
    if not candidates:
        raise ValueError("Gemini: пустой ответ")
    parts_out = candidates[0].get("content", {}).get("parts") or []
    texts = [p.get("text", "") for p in parts_out if p.get("text")]
    return "\n".join(texts).strip() or "(пустой ответ Gemini)"


async def _anthropic_chat(
    cfg: LlmCallConfig,
    prompt: str,
    system: str,
    *,
    data_mode: str = "raw",
) -> str:
    ensure_remote_egress_allowed(
        _llm_capability(data_mode),
        provider=cfg.provider,
        data_mode=data_mode,
    )
    safe_system = (
        system.strip()
        if data_mode == "none"
        else sanitize_remote_system_prompt(system)
    )
    body: dict[str, Any] = {
        "model": _resolve_model(cfg),
        "max_tokens": cfg.max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }
    if safe_system:
        body["system"] = safe_system
    async with httpx.AsyncClient(timeout=cfg.timeout) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": cfg.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json=body,
        )
        if resp.status_code >= 400:
            raise _http_error("anthropic", resp)
        data = resp.json()
        return data["content"][0]["text"]


def assert_model_allowed(cfg: LlmCallConfig) -> None:
    """Отклонить устаревшую/некаталожную модель ДО получения egress-lease.

    `model_allowed_for_provider` была написана и экспортирована, но не имела ни
    одного вызова вне тестов (находка аудита H5) — политика была декоративной.
    Проверка идёт до lease: незачем брать разрешение на вызов, который мы всё
    равно отклоняем.
    """
    from core.gemini_models import model_allowed_for_provider

    provider = (cfg.provider or "").strip().lower()
    model = _resolve_model(cfg)
    if not model_allowed_for_provider(provider, model):
        raise ValueError(
            f"Модель {model!r} недопустима для провайдера {provider!r}: "
            "она устарела либо не проходит проверку идентификатора"
        )


async def chat_complete(
    cfg: LlmCallConfig,
    prompt: str,
    system: str = "",
    *,
    data_mode: str = "raw",
) -> str:
    """Единая точка вызова LLM по провайдеру.

    ``data_mode`` is ``raw`` for normal user/memory prompts and ``none`` for
    provider connectivity tests that contain no user data.
    """
    provider = (cfg.provider or "none").strip().lower()
    if not cfg.api_key:
        raise ValueError("LLM API key не задан")
    assert_model_allowed(cfg)

    if provider == "openai":
        return await _openai_compatible_chat(
            cfg,
            prompt,
            system,
            "https://api.openai.com/v1",
            data_mode=data_mode,
        )
    if provider == "deepseek":
        return await _openai_compatible_chat(
            cfg,
            prompt,
            system,
            "https://api.deepseek.com",
            data_mode=data_mode,
        )
    if provider == "openrouter":
        return await _openai_compatible_chat(
            cfg,
            prompt,
            system,
            "https://openrouter.ai/api/v1",
            data_mode=data_mode,
        )
    if provider == "gemini":
        return await _gemini_chat(
            cfg,
            prompt,
            system,
            data_mode=data_mode,
        )
    if provider == "anthropic":
        return await _anthropic_chat(
            cfg,
            prompt,
            system,
            data_mode=data_mode,
        )
    raise ValueError(f"Неизвестный LLM provider: {provider}")


async def transcribe_audio_gemini(
    cfg: LlmCallConfig,
    audio_base64: str,
    *,
    mime_type: str = "audio/webm",
    language_hint: str = "ru",
) -> str:
    """Распознавание речи через Gemini (inline audio в generateContent)."""
    import base64

    ensure_remote_egress_allowed(
        "remote_stt",
        provider=cfg.provider,
        data_mode="raw",
    )
    raw = (audio_base64 or "").strip()
    if not raw:
        raise ValueError("Пустое аудио")
    try:
        base64.b64decode(raw, validate=True)
    except Exception as exc:
        raise ValueError("Некорректные данные audio_base64") from exc

    from core.gemini_models import (
        GEMINI_STT_DEFAULT_MODEL,
        GEMINI_STT_FALLBACK_MODELS,
        gemini_generation_config,
        normalize_gemini_model_id,
    )

    model = normalize_gemini_model_id(_resolve_model(cfg))
    if "flash" not in model and "pro" not in model and "lite" not in model:
        model = GEMINI_STT_DEFAULT_MODEL

    lang = (language_hint or "ru").split("-")[0].lower()
    lang_names = {
        "ru": "Russian",
        "en": "English",
        "uk": "Ukrainian",
        "de": "German",
    }
    lang_label = lang_names.get(lang, language_hint or "auto")

    prompt = (
        "Transcribe all spoken words in this audio accurately. "
        f"The speech is likely in {lang_label}. "
        "Return ONLY the transcription text, without quotes, labels, or commentary."
    )
    body: dict[str, Any] = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"inline_data": {"mime_type": mime_type, "data": raw}},
                    {"text": prompt},
                ],
            }
        ],
        "generationConfig": gemini_generation_config(
            model,
            2048,
            for_stt=True,
        ),
    }

    models_try = [model]
    for fallback in GEMINI_STT_FALLBACK_MODELS:
        if fallback not in models_try:
            models_try.append(fallback)

    last_err: Exception | None = None
    for try_model in models_try:
        try:
            resp: httpx.Response | None = None
            for api_version in ("v1beta", "v1"):
                resp = await _gemini_post(
                    cfg,
                    api_version=api_version,
                    model=try_model,
                    body=body,
                )
                if resp.status_code < 400:
                    break
                if api_version == "v1beta" and resp.status_code in (403, 404):
                    continue
                break
            if resp is None or resp.status_code >= 400:
                raise _http_error("gemini", resp)  # type: ignore[arg-type]
            data = resp.json()
            candidates = data.get("candidates") or []
            if not candidates:
                raise ValueError("Gemini: пустой ответ транскрипции")
            parts_out = candidates[0].get("content", {}).get("parts") or []
            texts = [p.get("text", "") for p in parts_out if p.get("text")]
            text = "\n".join(texts).strip()
            if not text:
                raise ValueError("Gemini: не удалось распознать речь")
            return text
        except Exception as exc:
            last_err = exc
            logger.info("Gemini STT model %s: %s", try_model, exc)
            continue
    raise ValueError(
        f"Gemini STT: {last_err}"
        if last_err
        else "распознавание не удалось"
    )


async def transcribe_audio_openai(
    cfg: LlmCallConfig,
    audio_base64: str,
    *,
    mime_type: str = "audio/webm",
    language_hint: str = "ru",
) -> str:
    """Распознавание речи через OpenAI Whisper API."""
    import base64

    ensure_remote_egress_allowed(
        "remote_stt",
        provider=cfg.provider,
        data_mode="raw",
    )
    raw = (audio_base64 or "").strip()
    if not raw:
        raise ValueError("Пустое аудио")
    audio_bytes = base64.b64decode(raw)
    if not audio_bytes:
        raise ValueError("Некорректные данные audio_base64")

    lang = (language_hint or "ru").split("-")[0].lower()
    ext = "webm"
    if "ogg" in mime_type:
        ext = "ogg"
    elif "wav" in mime_type:
        ext = "wav"
    elif "mp4" in mime_type or "m4a" in mime_type:
        ext = "mp4"

    files = {
        "file": (
            f"audio.{ext}",
            audio_bytes,
            mime_type or "audio/webm",
        )
    }
    data: dict[str, Any] = {"model": "whisper-1"}
    if lang in (
        "ru",
        "en",
        "uk",
        "de",
        "fr",
        "es",
        "it",
        "pt",
        "pl",
        "tr",
        "zh",
        "ja",
        "ko",
    ):
        data["language"] = lang

    async with httpx.AsyncClient(timeout=cfg.timeout) as client:
        resp = await client.post(
            "https://api.openai.com/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {cfg.api_key}"},
            files=files,
            data=data,
        )
        if resp.status_code >= 400:
            raise _http_error("openai", resp)
        payload = resp.json()
        text = (payload.get("text") or "").strip()
        if not text:
            raise ValueError("OpenAI Whisper: пустой ответ")
        return text


async def test_connection(cfg: LlmCallConfig) -> dict[str, Any]:
    """Короткий ping для кнопки «Подтвердить ключ» в консоли."""
    provider = (cfg.provider or "").strip().lower()
    if provider == "deepseek":
        reply = await _openai_compatible_chat(
            cfg,
            "Ответь одним словом: OK",
            "Ты помощник Velantrim.",
            "https://api.deepseek.com",
            quick_ping=True,
            data_mode="none",
        )
    else:
        reply = await chat_complete(
            cfg,
            "Ответь одним словом: OK",
            system="Ты помощник Velantrim.",
            data_mode="none",
        )
    return {
        "ok": True,
        "provider": cfg.provider,
        "model": _resolve_model(cfg),
        "reply_preview": (reply or "")[:120],
    }


__all__ = [
    "LlmCallConfig",
    "chat_complete",
    "get_provider_info",
    "list_providers",
    "llm_timeout_for_max_tokens",
    "normalize_deepseek_thinking",
    "test_connection",
    "transcribe_audio_gemini",
    "transcribe_audio_openai",
    "_deepseek_request_body",
    "compact_messages_for_deepseek",
    "_openai_stream_delta_parts",
]
