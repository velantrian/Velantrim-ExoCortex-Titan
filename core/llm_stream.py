"""
Потоковые ответы LLM и контекстный кэш (DeepSeek KV / Gemini).

DeepSeek: Context Caching on Disk включён по умолчанию — передаём стабильный
префикс messages[] (system + история).

Gemini 2.5+: implicit caching при повторяющемся префиксе; при длинном system —
explicit cachedContents.

Every remote execution path acquires a PolicyKernel egress lease first.
"""

from __future__ import annotations

import hashlib
import json
import logging
from collections.abc import AsyncIterator
from typing import Any

import httpx

from core.llm_context_budget import (
    CONTEXT_LIMIT_CODE,
    CONTEXT_OVERFLOW_CODE,
    HISTORY_MAX_TURNS_ENV,
    ContextReport,
    LlmContextLimitError,
    context_overflow_message,
    history_max_turns,
    looks_like_context_overflow,
)
from core.llm_router import (
    LlmCallConfig,
    LlmContextOverflowError,
    _deepseek_request_body,
    _gemini_post,
    _http_error,
    _openai_message_text,
    _openai_stream_delta_parts,
    _openai_stream_delta_text,
    _resolve_model,
    assert_model_allowed,
)
from core.remote_egress import (
    ensure_remote_egress_allowed,
    sanitize_remote_system_prompt,
)

logger = logging.getLogger(__name__)

_GEMINI_API_BASE = "https://generativelanguage.googleapis.com"

# Кэш explicit Gemini: ключ → имя cachedContents
_gemini_explicit_cache: dict[str, str] = {}


def normalize_chat_history(
    history: list[dict[str, str]] | None,
    *,
    report: ContextReport | None = None,
) -> list[dict[str, str]]:
    """[{role: user|assistant, content}] → OpenAI-формат.

    Keeps the most recent ``LLM_CHAT_HISTORY_MAX_TURNS`` turns (default 20,
    ``off`` = all). Turns are kept or left out whole; when older turns are left
    out this is recorded in ``report``.
    """
    out: list[dict[str, str]] = []
    if not history:
        return out
    for turn in history:
        role = (turn.get("role") or "user").lower()
        if role == "assistant":
            role = "assistant"
        elif role in ("bot", "model"):
            role = "assistant"
        else:
            role = "user"
        content = (turn.get("content") or "").strip()
        if content:
            out.append({"role": role, "content": content})
    cap = history_max_turns()
    kept = out if cap is None or len(out) <= cap else out[-cap:]
    if report is not None:
        report.history_turns_total = len(out)
        report.history_turns_sent = len(kept)
        if len(kept) < len(out) and cap is not None:
            report.record_applied(
                setting=HISTORY_MAX_TURNS_ENV,
                value=cap,
                affected="history_turns",
                omitted=len(out) - len(kept),
            )
    return kept


def build_openai_messages(
    system: str,
    user_message: str,
    history: list[dict[str, str]] | None,
    *,
    provider: str | None = None,
    report: ContextReport | None = None,
) -> list[dict[str, str]]:
    """Build a stable and epistemically safe remote messages prefix.

    Nothing is truncated. With a configured per-message limit for ``provider``
    (``DEEPSEEK_MESSAGE_CHAR_LIMIT``) the current question and the system
    message must fit or ``LlmContextLimitError`` is raised; a history turn that
    does not fit is left out whole and recorded in ``report``.
    """
    rep = report if report is not None else ContextReport.for_provider(provider)
    limit = rep.message_char_limit
    setting = rep.message_char_limit_setting or "message_char_limit"
    messages: list[dict[str, str]] = []
    safe_system = sanitize_remote_system_prompt(system)
    if limit is not None and len(user_message) > limit:
        raise LlmContextLimitError(
            setting=setting, limit=limit, role="user",
            length=len(user_message), part="current question",
        )
    if limit is not None and len(safe_system) > limit:
        raise LlmContextLimitError(
            setting=setting, limit=limit, role="system",
            length=len(safe_system), part="system instructions and memory",
        )
    if safe_system:
        messages.append({"role": "system", "content": safe_system})
    history_msgs = normalize_chat_history(history, report=rep)
    if limit is not None:
        fitting = [turn for turn in history_msgs if len(turn["content"]) <= limit]
        if len(fitting) < len(history_msgs):
            rep.record_applied(
                setting=setting,
                value=limit,
                affected="history_turns",
                omitted=len(history_msgs) - len(fitting),
            )
            rep.history_turns_sent = len(fitting)
        history_msgs = fitting
    messages.extend(history_msgs)
    messages.append({"role": "user", "content": user_message})
    return messages


def _usage_from_openai_payload(data: dict[str, Any]) -> dict[str, Any]:
    usage = data.get("usage") or {}
    hit = int(usage.get("prompt_cache_hit_tokens") or 0)
    miss = int(usage.get("prompt_cache_miss_tokens") or 0)
    return {
        "prompt_tokens": int(usage.get("prompt_tokens") or 0),
        "completion_tokens": int(usage.get("completion_tokens") or 0),
        "prompt_cache_hit_tokens": hit,
        "prompt_cache_miss_tokens": miss,
        "cache_note": (
            f"DeepSeek KV-cache: hit {hit}, miss {miss}"
            if hit or miss
            else "DeepSeek KV-cache: префикс messages (кэш при повторных запросах)"
        ),
    }


def _gemini_cache_key(cfg: LlmCallConfig, system: str) -> str:
    # Digest of the whole system text: a prefix-only key let two different system
    # prompts with the same first 8000 characters share one cached context.
    # The API key is not hashed here; a process-local hash() separates accounts
    # in this in-memory map only.
    content = f"{cfg.provider}:{_resolve_model(cfg)}:{system}"
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()[:32]
    return f"{digest}:{hash(cfg.api_key):x}"


async def _gemini_ensure_explicit_cache(
    cfg: LlmCallConfig,
    system: str,
) -> str | None:
    """Explicit cache для длинного system после успешного egress lease."""
    from core.gemini_models import (
        gemini_explicit_cache_min_chars,
        gemini_model_meta,
        normalize_gemini_model_id,
    )

    model = normalize_gemini_model_id(_resolve_model(cfg))
    meta = gemini_model_meta(model)
    if not meta.get("explicit_cache", True):
        return None
    min_chars = gemini_explicit_cache_min_chars(model)
    if len(system) < min_chars:
        return None
    key = _gemini_cache_key(cfg, system)
    if key in _gemini_explicit_cache:
        return _gemini_explicit_cache[key]

    body = {
        "model": f"models/{model}",
        # Whole system text: a cached context replaces systemInstruction in the
        # request, so a cut here would silently drop the rest of the system.
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [
            {
                "role": "user",
                "parts": [{"text": "(Velantrim console context)"}],
            }
        ],
        "ttl": "3600s",
        "displayName": "velantrim-console-system",
    }
    url = f"{_GEMINI_API_BASE}/v1beta/cachedContents"
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": cfg.api_key,
    }
    try:
        async with httpx.AsyncClient(timeout=cfg.timeout) as client:
            resp = await client.post(url, headers=headers, json=body)
            if resp.status_code >= 400:
                logger.info(
                    "Gemini explicit cache create: HTTP %s",
                    resp.status_code,
                )
                return None
            data = resp.json()
            name = data.get("name")
            if name:
                _gemini_explicit_cache[key] = name
                return name
    except Exception as exc:
        logger.info("Gemini explicit cache: %s", exc)
    return None


def _gemini_contents_from_history(
    history: list[dict[str, str]],
    user_message: str,
) -> list[dict[str, Any]]:
    contents: list[dict[str, Any]] = []
    for turn in history:
        role = "user" if turn["role"] == "user" else "model"
        contents.append(
            {"role": role, "parts": [{"text": turn["content"]}]}
        )
    contents.append({"role": "user", "parts": [{"text": user_message}]})
    return contents


def _usage_from_gemini_payload(data: dict[str, Any]) -> dict[str, Any]:
    meta = data.get("usageMetadata") or data.get("usage_metadata") or {}
    cached = int(meta.get("cachedContentTokenCount") or 0)
    prompt = int(meta.get("promptTokenCount") or 0)
    candidates = int(meta.get("candidatesTokenCount") or 0)
    note = (
        f"Gemini cache: {cached} cached tokens"
        if cached
        else "Gemini implicit cache (2.5+): стабильный префикс contents"
    )
    return {
        "prompt_tokens": prompt,
        "completion_tokens": candidates,
        "cached_content_token_count": cached,
        "cache_note": note,
    }


async def chat_complete_messages(
    cfg: LlmCallConfig,
    system: str,
    user_message: str,
    history: list[dict[str, str]] | None = None,
    *,
    report: ContextReport | None = None,
) -> tuple[str, dict[str, Any]]:
    """Нестриминговый remote-вызов с обязательным policy lease.

    ``report`` (optional) is filled with what was actually sent and which
    limits were applied; see ``core.llm_context_budget``.
    """
    provider = (cfg.provider or "").strip().lower()
    assert_model_allowed(cfg)
    ensure_remote_egress_allowed(
        "remote_llm",
        provider=provider,
        data_mode="raw",
    )
    safe_system = sanitize_remote_system_prompt(system)
    rep = report if report is not None else ContextReport.for_provider(provider)
    messages = build_openai_messages(
        safe_system, user_message, history, provider=provider, report=rep
    )
    # The exact history that went into ``messages`` (after whole-turn limits).
    sent_history = [m for m in messages if m["role"] != "system"][:-1]
    usage_meta: dict[str, Any] = {}

    if provider in ("openai", "deepseek", "openrouter"):
        base = {
            "openai": "https://api.openai.com/v1",
            "deepseek": "https://api.deepseek.com",
            "openrouter": "https://openrouter.ai/api/v1",
        }[provider]
        url = base.rstrip("/") + "/chat/completions"
        headers = {
            "Authorization": f"Bearer {cfg.api_key}",
            "Content-Type": "application/json",
        }
        if provider == "openrouter":
            headers["HTTP-Referer"] = "https://velantrim.local/console"
            headers["X-Title"] = "VELANTRIM Console"
        if provider == "deepseek":
            body = _deepseek_request_body(
                cfg,
                messages,
                quick_ping=False,
            )
        else:
            body = {
                "model": _resolve_model(cfg),
                "messages": messages,
                "max_tokens": cfg.max_tokens,
                "stream": False,
            }
        async with httpx.AsyncClient(timeout=cfg.timeout) as client:
            resp = await client.post(url, headers=headers, json=body)
            if resp.status_code >= 400:
                raise _http_error(provider, resp)
            data = resp.json()
            text = _openai_message_text(data["choices"][0]["message"])
            if not text:
                raise ValueError(f"{provider}: пустой ответ модели")
            usage_meta = _usage_from_openai_payload(data)
            return text, usage_meta

    if provider == "gemini":
        return await _gemini_complete_messages(
            cfg,
            safe_system,
            user_message,
            sent_history,
        )

    if provider == "anthropic":
        from core.llm_router import _anthropic_chat

        hist_text = ""
        for turn in sent_history:
            hist_text += f"\n{turn['role']}: {turn['content']}"
        prompt = user_message
        if hist_text:
            prompt = (
                f"История диалога:{hist_text}\n\n"
                f"Текущий вопрос: {user_message}"
            )
        text = await _anthropic_chat(
            cfg,
            prompt,
            safe_system,
            data_mode="raw",
        )
        return text, {
            "cache_note": "Anthropic: история в prompt (без отдельного KV API)"
        }

    from core.llm_router import chat_complete

    text = await chat_complete(
        cfg,
        user_message,
        safe_system,
        data_mode="raw",
    )
    return text, {}


async def _gemini_complete_messages(
    cfg: LlmCallConfig,
    system: str,
    user_message: str,
    history: list[dict[str, str]] | None,
) -> tuple[str, dict[str, Any]]:
    from core.gemini_models import (
        gemini_generation_config,
        normalize_gemini_model_id,
    )

    model = normalize_gemini_model_id(_resolve_model(cfg))
    hist = normalize_chat_history(history)
    cached_name = await _gemini_ensure_explicit_cache(cfg, system)
    body: dict[str, Any] = {
        "contents": _gemini_contents_from_history(hist, user_message),
        "generationConfig": gemini_generation_config(
            model,
            cfg.max_tokens,
        ),
    }
    if cached_name:
        body["cachedContent"] = cached_name
    elif system:
        body["systemInstruction"] = {"parts": [{"text": system}]}

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
            continue
        break
    if resp is None or resp.status_code >= 400:
        raise _http_error("gemini", resp)  # type: ignore[arg-type]
    data = resp.json()
    candidates = data.get("candidates") or []
    if not candidates:
        raise ValueError("Gemini: пустой ответ")
    parts_out = candidates[0].get("content", {}).get("parts") or []
    texts = [part.get("text", "") for part in parts_out if part.get("text")]
    text = "\n".join(texts).strip() or "(пустой ответ Gemini)"
    return text, _usage_from_gemini_payload(data)


def _parse_openai_sse_chunk(line: str) -> str | None:
    if not line.startswith("data:"):
        return None
    payload = line[5:].strip()
    if payload == "[DONE]":
        return None
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        return None
    choices = data.get("choices") or []
    if not choices:
        return None
    delta = choices[0].get("delta") or {}
    return _openai_stream_delta_text(delta) or None


async def stream_chat_events(
    cfg: LlmCallConfig,
    system: str,
    user_message: str,
    history: list[dict[str, str]] | None = None,
    *,
    report: ContextReport | None = None,
) -> AsyncIterator[dict[str, Any]]:
    """
    События SSE для консоли:
      {"type":"context","report":{...}}   (before tokens: what is sent, limits applied)
      {"type":"token","text":"..."}
      {"type":"done","reply":"...","usage":{...}}
      {"type":"error","message":"..."}
    """
    provider = (cfg.provider or "").strip().lower()
    rep = report if report is not None else ContextReport.for_provider(provider)

    try:
        assert_model_allowed(cfg)
        ensure_remote_egress_allowed(
            "remote_llm",
            provider=provider,
            data_mode="raw",
        )
        safe_system = sanitize_remote_system_prompt(system)
        messages = build_openai_messages(
            safe_system,
            user_message,
            history,
            provider=provider,
            report=rep,
        )
        sent_history = [m for m in messages if m["role"] != "system"][:-1]
        yield {"type": "context", "report": rep.to_dict()}

        if provider in ("openai", "deepseek", "openrouter"):
            async for event in _stream_openai_compatible(
                cfg,
                messages,
                provider,
            ):
                yield event
            return
        if provider == "gemini":
            async for event in _stream_gemini(
                cfg,
                safe_system,
                user_message,
                sent_history,
            ):
                yield event
            return
        text, usage = await chat_complete_messages(
            cfg,
            safe_system,
            user_message,
            sent_history,
        )
        yield {"type": "token", "text": text}
        yield {"type": "done", "reply": text, "usage": usage}
    except Exception as exc:
        err_event: dict[str, Any] = {"type": "error", "message": str(exc)}
        code = getattr(exc, "code", None)
        if code in (CONTEXT_LIMIT_CODE, CONTEXT_OVERFLOW_CODE):
            err_event["code"] = code
        yield err_event


async def _stream_openai_compatible(
    cfg: LlmCallConfig,
    messages: list[dict[str, str]],
    provider: str,
) -> AsyncIterator[dict[str, Any]]:
    base = {
        "openai": "https://api.openai.com/v1",
        "deepseek": "https://api.deepseek.com",
        "openrouter": "https://openrouter.ai/api/v1",
    }[provider]
    url = base.rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {cfg.api_key}",
        "Content-Type": "application/json",
    }
    if provider == "openrouter":
        headers["HTTP-Referer"] = "https://velantrim.local/console"
        headers["X-Title"] = "VELANTRIM Console"
    if provider == "deepseek":
        body = _deepseek_request_body(
            cfg,
            messages,
            quick_ping=False,
            stream=True,
        )
    else:
        body = {
            "model": _resolve_model(cfg),
            "messages": messages,
            "max_tokens": cfg.max_tokens,
            "stream": True,
        }
        if provider == "openai":
            body["stream_options"] = {"include_usage": True}

    full_parts: list[str] = []
    usage_meta: dict[str, Any] = {}

    async with httpx.AsyncClient(timeout=cfg.timeout) as client:
        async with client.stream(
            "POST",
            url,
            headers=headers,
            json=body,
        ) as resp:
            if resp.status_code >= 400:
                err_body = await resp.aread()
                try:
                    detail = err_body.decode(
                        "utf-8",
                        errors="replace",
                    )[:400]
                    if looks_like_context_overflow(resp.status_code, detail):
                        raise LlmContextOverflowError(
                            provider=provider,
                            status_code=resp.status_code,
                            detail=detail,
                            message=context_overflow_message(provider, resp.status_code),
                        )
                    raise ValueError(
                        f"{provider}: HTTP {resp.status_code} — {detail}"
                    )
                except ValueError:
                    raise
                except Exception:
                    raise _http_error(provider, resp)
            async for line in resp.aiter_lines():
                if not line:
                    continue
                if line.startswith("data:"):
                    payload = line[5:].strip()
                    if payload == "[DONE]":
                        break
                    try:
                        data = json.loads(payload)
                        usage_meta = _usage_from_openai_payload(data)
                        choices = data.get("choices") or []
                        if choices:
                            delta = choices[0].get("delta") or {}
                            content_piece, reasoning_piece = (
                                _openai_stream_delta_parts(delta)
                            )
                            if reasoning_piece:
                                yield {
                                    "type": "thinking",
                                    "text": reasoning_piece,
                                }
                            if content_piece:
                                full_parts.append(content_piece)
                                yield {
                                    "type": "token",
                                    "text": content_piece,
                                }
                    except json.JSONDecodeError:
                        continue

    full = "".join(full_parts)
    yield {"type": "done", "reply": full, "usage": usage_meta}


async def _stream_gemini(
    cfg: LlmCallConfig,
    system: str,
    user_message: str,
    history: list[dict[str, str]] | None,
) -> AsyncIterator[dict[str, Any]]:
    from core.gemini_models import (
        gemini_generation_config,
        normalize_gemini_model_id,
    )

    model = normalize_gemini_model_id(_resolve_model(cfg))
    hist = normalize_chat_history(history)
    cached_name = await _gemini_ensure_explicit_cache(cfg, system)
    body: dict[str, Any] = {
        "contents": _gemini_contents_from_history(hist, user_message),
        "generationConfig": gemini_generation_config(
            model,
            cfg.max_tokens,
        ),
    }
    if cached_name:
        body["cachedContent"] = cached_name
    elif system:
        body["systemInstruction"] = {"parts": [{"text": system}]}

    # model уходит в путь URL — валидируем структурно перед подстановкой.
    # Здесь это особенно важно: строка уже несёт "?alt=sse", поэтому '?' или '#'
    # внутри model перекроили бы query, а не только путь.
    from core.gemini_models import assert_safe_gemini_model_id

    url = (
        f"{_GEMINI_API_BASE}/v1beta/models/"
        f"{assert_safe_gemini_model_id(model)}:streamGenerateContent?alt=sse"
    )
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": cfg.api_key,
    }

    full_parts: list[str] = []
    usage_meta: dict[str, Any] = {}

    async with httpx.AsyncClient(timeout=cfg.timeout) as client:
        async with client.stream(
            "POST",
            url,
            headers=headers,
            json=body,
        ) as resp:
            if resp.status_code >= 400:
                text, usage = await _gemini_complete_messages(
                    cfg,
                    system,
                    user_message,
                    history,
                )
                yield {"type": "token", "text": text}
                yield {
                    "type": "done",
                    "reply": text,
                    "usage": usage,
                }
                return
            async for line in resp.aiter_lines():
                if not line or not line.startswith("data:"):
                    continue
                payload = line[5:].strip()
                if not payload:
                    continue
                try:
                    data = json.loads(payload)
                except json.JSONDecodeError:
                    continue
                usage_meta = _usage_from_gemini_payload(data)
                candidates = data.get("candidates") or []
                if not candidates:
                    continue
                parts = (
                    candidates[0]
                    .get("content", {})
                    .get("parts")
                    or []
                )
                for part in parts:
                    piece = part.get("text") or ""
                    if piece:
                        full_parts.append(piece)
                        yield {"type": "token", "text": piece}

    full = "".join(full_parts)
    yield {"type": "done", "reply": full, "usage": usage_meta}


__all__ = [
    "build_openai_messages",
    "chat_complete_messages",
    "normalize_chat_history",
    "stream_chat_events",
]
