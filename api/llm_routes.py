"""
Маршруты LLM для веб-консоли.

Дублируют /llm/* под префиксом /console/llm/* — работают даже если
старый процесс не подхватил обновления server.py (достаточно перезагрузить static).
"""

from __future__ import annotations

import base64
import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator

# AUDIT-FIX P1: split into two routers.
#  • public_router  — read-only catalog/diagnostics (GET). No secret, no quota.
#  • secure_router  — routes that accept a provider api_key in the body and make a
#    real outbound call (Gemini/OpenAI/DeepSeek). These require VELANTRIM_API_KEY
#    (see register_llm_routes), closing the unauthenticated key-validation oracle
#    and the quota/open-proxy abuse identified in the audit.
public_router = APIRouter(tags=["LLM", "Console"])
secure_router = APIRouter(tags=["LLM", "Console"])


class LlmTestBody(BaseModel):
    """Connectivity probe. Carries NO user payload — by contract, not by habit.

    The probe runs under an egress lease with ``data_mode="none"``, which skips
    the remote-data policy check (see docs/REMOTE_EGRESS_POLICY.ru.md). That is
    only sound while the request genuinely cannot carry user content, so the
    body admits provider/key/model and nothing else: no prompt, no text, no
    system, no memory, no attachment. The prompt sent upstream is a fixed
    repository-owned string in ``core.llm_router.test_connection``.

    ``extra="forbid"`` makes an attempt to smuggle a payload a 422 instead of a
    silently dropped field — the guarantee should be refusal, not luck.
    """

    model_config = ConfigDict(extra="forbid")

    provider: str = Field(..., min_length=2)
    api_key:  str = Field(..., min_length=4)
    model:    str | None = None

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        from core.llm_router import get_provider_info

        pid = v.strip().lower()
        if not get_provider_info(pid):
            raise ValueError(f"provider неизвестен: {v}")
        return pid


class SttTranscribeBody(BaseModel):
    provider: str = Field(default="gemini", min_length=2)
    api_key: str = Field(..., min_length=4)
    model: str | None = None
    audio_base64: str = Field(..., min_length=16)
    mime_type: str = Field(default="audio/webm")
    language: str = Field(default="ru", max_length=16)

    @field_validator("provider")
    @classmethod
    def validate_stt_provider(cls, v: str) -> str:
        return _normalize_stt_provider(v)


class GeminiDiscoverBody(BaseModel):
    api_key: str = Field(..., min_length=4)


class SttTestBody(BaseModel):
    provider: str = Field(..., min_length=2)
    api_key: str = Field(..., min_length=4)
    model: str | None = None
    language: str = Field(default="ru", max_length=16)

    @field_validator("provider")
    @classmethod
    def validate_stt_test_provider(cls, v: str) -> str:
        return _normalize_stt_provider(v)


def _normalize_stt_provider(v: str) -> str:
    from core.llm_router import get_provider_info

    pid = v.strip().lower()
    if pid not in ("gemini", "openai"):
        raise ValueError("provider должен быть gemini или openai")
    if not get_provider_info(pid):
        raise ValueError(f"provider неизвестен: {v}")
    return pid


def _llm_test_http_status(exc: Exception) -> int:
    msg = str(exc).lower()
    if "http 401" in msg or "invalid_api_key" in msg or "authentication" in msg:
        return 401
    if "http 402" in msg:
        return 402
    if "http 404" in msg or ("model" in msg and "not found" in msg):
        return 404
    if "http 429" in msg:
        return 429
    return 400


async def _run_llm_test(req: LlmTestBody):
    from core.gemini_models import (
        is_gemini_model_deprecated,
        normalize_gemini_model_id,
    )
    from core.llm_router import LlmCallConfig, get_provider_info, test_connection

    model = (req.model or "").strip() or None
    provider = (req.provider or "").strip().lower()
    if model:
        if provider == "gemini":
            mid = normalize_gemini_model_id(model)
            if is_gemini_model_deprecated(mid):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Модель «{model}» снята Google (2.0/1.x). "
                        "Используйте gemini-3.5-flash, gemini-3.1-flash-lite или gemini-2.5-flash."
                    ),
                )
            # Любой gemini-* ID допустим — проверка на стороне Google API (не устаревший каталог в памяти)
        else:
            info = get_provider_info(provider)
            allowed = set((info or {}).get("models") or [])
            if allowed and model not in allowed:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Модель «{model}» не в каталоге {provider}. "
                        f"Доступны: {', '.join(sorted(allowed))}"
                    ),
                )

    cfg = LlmCallConfig(
        provider=req.provider,
        api_key=req.api_key.strip(),
        model=model,
        max_tokens=64,
        timeout=45.0,
    )
    try:
        result = await test_connection(cfg)
        result["verified"] = True
        return result
    except Exception as exc:
        raise HTTPException(
            status_code=_llm_test_http_status(exc),
            detail=str(exc),
        ) from exc


@public_router.get("/llm/providers")
async def llm_providers_list():
    from core.provider_catalog import (
        CATALOG_BUILD_ID,
        catalog_debug_info,
        list_providers,
    )

    meta = catalog_debug_info()
    return {
        "providers": list_providers(),
        "catalog_build_id": CATALOG_BUILD_ID,
        "gemini_catalog_revision": meta.get("gemini_catalog_revision"),
        "catalog_module": meta.get("catalog_module"),
    }


@public_router.get("/debug/llm-catalog")
@public_router.get("/console/debug/llm-catalog")
async def debug_llm_catalog():
    """Диагностика: откуда берётся каталог (если старый — другой процесс/папка)."""
    from pathlib import Path

    import server as srv
    from core.provider_catalog import catalog_debug_info

    info = catalog_debug_info()
    info["server_module"] = str(Path(srv.__file__).resolve())
    info["stale_hint"] = (
        None
        if info.get("catalog_build_id") == "2026-05-velantrim-llm-v3"
        and info.get("gemini_catalog_revision") == "2026-05-gemini-v2"
        and "gemini-3.5-flash" in (info.get("gemini_models_sample") or [])
        else (
            "Устаревший каталог: остановите python на порту 8755 и запустите "
            "scripts\\start_console.ps1 из папки VELANTRIM_ExoCortex_V8.6"
        )
    )
    return info


@secure_router.post("/llm/test")
async def llm_test_route(req: LlmTestBody):
    """Проверка ключа LLM (без X-Api-Key)."""
    return await _run_llm_test(req)


@public_router.get("/console/llm/providers")
async def console_llm_providers():
    return await llm_providers_list()


@secure_router.post("/console/llm/gemini/discover")
@secure_router.post("/llm/gemini/discover")
async def gemini_discover_models(req: GeminiDiscoverBody):
    """
    Список моделей Gemini, доступных ключу (models.list API),
    объединённый с каталогом из документации.
    """
    from core.gemini_models import fetch_gemini_models_from_api, merge_gemini_catalog_with_api

    api_ids, warnings = await fetch_gemini_models_from_api(req.api_key.strip())
    provider = merge_gemini_catalog_with_api(api_ids)
    return {
        "ok": True,
        "provider": provider,
        "api_model_count": len(api_ids),
        "warnings": warnings,
    }


@secure_router.post("/console/llm/test")
async def console_llm_test(req: LlmTestBody):
    """Тот же тест — путь привязан к модулю консоли."""
    return await _run_llm_test(req)


async def _run_stt_test(req: SttTestBody):
    from core.llm_router import (
        LlmCallConfig,
        get_provider_info,
        transcribe_audio_gemini,
        transcribe_audio_openai,
    )
    from core.stt_test_audio import TEST_WAV_B64

    provider = req.provider
    cfg = LlmCallConfig(
        provider=provider,
        api_key=req.api_key.strip(),
        model=(req.model or "").strip() or None,
        max_tokens=2048,
        timeout=90.0,
    )
    lang = req.language or "ru"
    try:
        if provider == "gemini":
            text = await transcribe_audio_gemini(
                cfg,
                TEST_WAV_B64,
                mime_type="audio/wav",
                language_hint=lang,
            )
            model_out = cfg.model or get_provider_info(provider)["default_model"]
        else:
            text = await transcribe_audio_openai(
                cfg,
                TEST_WAV_B64,
                mime_type="audio/wav",
                language_hint=lang,
            )
            model_out = "whisper-1"
        preview = (text or "").strip()[:80]
        return {
            "ok": True,
            "verified": True,
            "provider": provider,
            "model": model_out,
            "text_preview": preview or "(API принял запрос, текст пустой)",
            "hint": f"Ключ {provider} для голоса проверен — STT API отвечает.",
        }
    except Exception as exc:
        raise HTTPException(
            status_code=_llm_test_http_status(exc),
            detail=str(exc),
        ) from exc


@secure_router.post("/console/stt/test")
@secure_router.post("/stt/test")
async def stt_test_route(req: SttTestBody):
    """Проверка ключа STT (реальный запрос к Gemini или OpenAI Whisper)."""
    return await _run_stt_test(req)


@secure_router.post("/console/stt/transcribe")
@secure_router.post("/stt/transcribe")
async def stt_transcribe(req: SttTranscribeBody):
    """Распознавание речи: gemini | openai (Whisper)."""
    from core.llm_router import (
        LlmCallConfig,
        get_provider_info,
        transcribe_audio_gemini,
        transcribe_audio_openai,
    )

    provider = req.provider.strip().lower()
    if provider not in ("gemini", "openai"):
        raise HTTPException(
            status_code=400,
            detail="Поддерживается provider=gemini или provider=openai",
        )
    if not get_provider_info(provider):
        raise HTTPException(status_code=400, detail=f"provider неизвестен: {provider}")

    cfg = LlmCallConfig(
        provider=provider,
        api_key=req.api_key.strip(),
        model=(req.model or "").strip() or None,
        max_tokens=2048,
        timeout=90.0,
    )
    mime = req.mime_type or "audio/webm"
    lang = req.language or "ru"
    try:
        if provider == "gemini":
            text = await transcribe_audio_gemini(
                cfg, req.audio_base64, mime_type=mime, language_hint=lang
            )
            model_out = cfg.model or get_provider_info(provider)["default_model"]
        else:
            text = await transcribe_audio_openai(
                cfg, req.audio_base64, mime_type=mime, language_hint=lang
            )
            model_out = "whisper-1"
        return {
            "ok": True,
            "provider": provider,
            "model": model_out,
            "text": text,
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


class TtsTestBody(BaseModel):
    """TTS connectivity probe. No user payload — but NOT a metadata-only lease.

    The phrase spoken during the probe is built inside
    ``core.tts_router.test_tts_connection``; the caller cannot supply text, and
    ``extra="forbid"`` refuses an attempt to.

    Deliberately asymmetric with :class:`LlmTestBody`, and the asymmetry is the
    point: the TTS probe still takes its lease as ``remote_tts`` with
    ``data_mode="raw"``, because synthesis returns audio and the capability is
    the same one /tts/speak uses for real user text. Consequence, measured:
    under ``network=allow`` + ``remote_data=never`` the LLM probe is allowed
    while this one is denied ``remote_data_forbidden``.

    That is the safe direction, so it is left alone. Adding a metadata-only
    ``remote_tts_test`` capability purely for symmetry would *widen* what the
    policy permits — not something to do for tidiness.
    """

    model_config = ConfigDict(extra="forbid")

    provider: str = Field(..., min_length=2)
    api_key: str = Field(..., min_length=4)
    voice: str | None = None
    model: str | None = None
    language: str = Field(default="ru", max_length=16)

    @field_validator("provider")
    @classmethod
    def validate_tts_provider(cls, v: str) -> str:
        p = v.strip().lower()
        if p not in ("gemini", "openai"):
            raise ValueError("provider должен быть gemini или openai")
        return p


class TtsSpeakBody(BaseModel):
    provider: str = Field(..., min_length=2)
    api_key: str = Field(..., min_length=4)
    text: str = Field(..., min_length=1, max_length=12000)
    voice: str | None = None
    model: str | None = None

    @field_validator("provider")
    @classmethod
    def validate_tts_speak_provider(cls, v: str) -> str:
        p = v.strip().lower()
        if p not in ("gemini", "openai"):
            raise ValueError("provider должен быть gemini или openai")
        return p


@public_router.get("/console/tts/catalog")
@public_router.get("/tts/catalog")
async def tts_catalog_route():
    from core.tts_router import tts_catalog

    return tts_catalog()


@secure_router.post("/console/tts/test")
@secure_router.post("/tts/test")
async def tts_test_route(req: TtsTestBody):
    from core.tts_router import test_tts_connection

    try:
        return await test_tts_connection(
            req.provider,
            req.api_key.strip(),
            voice=(req.voice or "").strip() or None,
            model=(req.model or "").strip() or None,
            language=req.language or "ru",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=_llm_test_http_status(exc),
            detail=str(exc),
        ) from exc


@secure_router.post("/console/tts/speak")
@secure_router.post("/tts/speak")
async def tts_speak_chunk(req: TtsSpeakBody):
    """Один фрагмент текста → audio (для Gemini по предложениям)."""
    from core.tts_router import synthesize_chunk

    try:
        audio, mime = await synthesize_chunk(
            req.provider,
            req.api_key.strip(),
            req.text,
            voice=(req.voice or "").strip() or None,
            model=(req.model or "").strip() or None,
        )
        return {
            "ok": True,
            "mime_type": mime,
            "audio_base64": base64.b64encode(audio).decode("ascii"),
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@secure_router.post("/console/tts/stream")
@secure_router.post("/tts/stream")
async def tts_stream_route(req: TtsSpeakBody):
    """OpenAI: поток mp3. Gemini: NDJSON с base64 по фразам."""
    from core.tts_router import (
        gemini_tts_bytes,
        openai_tts_stream,
        split_tts_chunks,
    )

    provider = req.provider.strip().lower()
    api_key = req.api_key.strip()
    voice = (req.voice or "").strip() or None
    model = (req.model or "").strip() or None

    if provider == "openai":
        from core.tts_router import (
            DEFAULT_OPENAI_TTS_MODEL,
            DEFAULT_OPENAI_TTS_VOICE,
        )

        v = voice or DEFAULT_OPENAI_TTS_VOICE
        m = model or DEFAULT_OPENAI_TTS_MODEL

        async def audio_iter():
            async for chunk in openai_tts_stream(
                api_key, req.text, voice=v, model=m
            ):
                yield chunk

        return StreamingResponse(audio_iter(), media_type="audio/mpeg")

    async def ndjson_iter():
        for piece in split_tts_chunks(req.text):
            audio, mime = await gemini_tts_bytes(
                api_key, piece, voice=voice, model=model
            )
            line = json.dumps(
                {
                    "mime_type": mime,
                    "audio_base64": base64.b64encode(audio).decode("ascii"),
                },
                ensure_ascii=False,
            )
            yield (line + "\n").encode("utf-8")

    return StreamingResponse(ndjson_iter(), media_type="application/x-ndjson")


def register_llm_routes(app, auth_dependency=None) -> None:
    """Подключить маршруты LLM.

    public_router (GET каталог/диагностика) подключается всегда — открыт.
    secure_router (routes с provider api_key + сетевой вызов) получает
    auth_dependency (server.require_api_key), если он передан. В open-режиме
    (VELANTRIM_API_KEY не задан) require_api_key сам по себе no-op, поэтому
    dev-сценарий не ломается.
    """
    app.include_router(public_router)
    deps = [Depends(auth_dependency)] if auth_dependency else []
    app.include_router(secure_router, dependencies=deps)
