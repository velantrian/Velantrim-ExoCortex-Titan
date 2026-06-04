"""
Озвучка (TTS): OpenAI Audio API и Google Gemini TTS.

OpenAI: потоковый audio/mpeg (stream=True).
Gemini: generateContent с responseModalities AUDIO (по предложениям для быстрого старта).
"""

from __future__ import annotations

import base64
import io
import logging
import re
import wave
from collections.abc import AsyncIterator
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_GEMINI_API_BASE = "https://generativelanguage.googleapis.com"

OPENAI_TTS_VOICES: list[str] = [
    "alloy",
    "ash",
    "ballad",
    "coral",
    "echo",
    "fable",
    "onyx",
    "nova",
    "sage",
    "shimmer",
    "verse",
]

OPENAI_TTS_MODELS: list[str] = [
    "gpt-4o-mini-tts",
    "tts-1",
    "tts-1-hd",
]

# 30 prebuilt voices — https://ai.google.dev/gemini-api/docs/speech-generation
GEMINI_TTS_VOICE_CATALOG: list[dict[str, str]] = [
    {"id": "Zephyr", "style": "Bright"},
    {"id": "Puck", "style": "Upbeat"},
    {"id": "Charon", "style": "Informative"},
    {"id": "Kore", "style": "Firm"},
    {"id": "Fenrir", "style": "Excitable"},
    {"id": "Leda", "style": "Youthful"},
    {"id": "Orus", "style": "Firm"},
    {"id": "Aoede", "style": "Breezy"},
    {"id": "Callirrhoe", "style": "Easy-going"},
    {"id": "Autonoe", "style": "Bright"},
    {"id": "Enceladus", "style": "Breathy"},
    {"id": "Iapetus", "style": "Clear"},
    {"id": "Umbriel", "style": "Easy-going"},
    {"id": "Algieba", "style": "Smooth"},
    {"id": "Despina", "style": "Smooth"},
    {"id": "Erinome", "style": "Clear"},
    {"id": "Algenib", "style": "Gravelly"},
    {"id": "Rasalgethi", "style": "Informative"},
    {"id": "Laomedeia", "style": "Upbeat"},
    {"id": "Achernar", "style": "Soft"},
    {"id": "Alnilam", "style": "Firm"},
    {"id": "Schedar", "style": "Even"},
    {"id": "Gacrux", "style": "Mature"},
    {"id": "Pulcherrima", "style": "Forward"},
    {"id": "Achird", "style": "Friendly"},
    {"id": "Zubenelgenubi", "style": "Casual"},
    {"id": "Vindemiatrix", "style": "Gentle"},
    {"id": "Sadachbia", "style": "Lively"},
    {"id": "Sadaltager", "style": "Knowledgeable"},
    {"id": "Sulafat", "style": "Warm"},
]

GEMINI_TTS_VOICES: list[str] = [v["id"] for v in GEMINI_TTS_VOICE_CATALOG]

OPENAI_TTS_VOICE_CATALOG: list[dict[str, str]] = [
    {"id": "alloy", "style": "Neutral"},
    {"id": "ash", "style": "Soft"},
    {"id": "ballad", "style": "Warm"},
    {"id": "coral", "style": "Clear"},
    {"id": "echo", "style": "Resonant"},
    {"id": "fable", "style": "Expressive"},
    {"id": "onyx", "style": "Deep"},
    {"id": "nova", "style": "Bright"},
    {"id": "sage", "style": "Calm"},
    {"id": "shimmer", "style": "Light"},
    {"id": "verse", "style": "Dynamic"},
]

GEMINI_TTS_MODELS: list[str] = [
    "gemini-2.5-flash-preview-tts",
    "gemini-2.5-pro-preview-tts",
    "gemini-3.1-flash-tts-preview",
]

DEFAULT_OPENAI_TTS_MODEL = "gpt-4o-mini-tts"
DEFAULT_OPENAI_TTS_VOICE = "alloy"
DEFAULT_GEMINI_TTS_MODEL = "gemini-2.5-flash-preview-tts"
DEFAULT_GEMINI_TTS_VOICE = "Kore"


def tts_catalog() -> dict[str, Any]:
    return {
        "catalog_revision": "2026-05-gemini-tts-voices-30",
        "openai": {
            "models": OPENAI_TTS_MODELS,
            "voices": OPENAI_TTS_VOICES,
            "voice_catalog": OPENAI_TTS_VOICE_CATALOG,
            "default_model": DEFAULT_OPENAI_TTS_MODEL,
            "default_voice": DEFAULT_OPENAI_TTS_VOICE,
            "streaming": True,
        },
        "gemini": {
            "models": GEMINI_TTS_MODELS,
            "voices": GEMINI_TTS_VOICES,
            "voice_catalog": GEMINI_TTS_VOICE_CATALOG,
            "default_model": DEFAULT_GEMINI_TTS_MODEL,
            "default_voice": DEFAULT_GEMINI_TTS_VOICE,
            "streaming": False,
            "note": "30 голосов prebuiltVoiceConfig — документация Google Gemini API Speech",
            "docs": "https://ai.google.dev/gemini-api/docs/speech-generation",
        },
    }


def split_tts_chunks(text: str, max_first: int = 220) -> list[str]:
    """Разбивка на фразы — первый фрагмент короче для быстрого старта."""
    clean = re.sub(r"\s+", " ", (text or "").strip())
    if not clean:
        return []
    if len(clean) <= max_first:
        return [clean]
    parts = re.split(r"(?<=[.!?…])\s+|[\n;]+", clean)
    parts = [p.strip() for p in parts if p.strip()]
    if not parts:
        return [clean[:max_first]]
    out: list[str] = []
    buf = ""
    for p in parts:
        if not out and len(buf) + len(p) + 1 <= max_first:
            buf = (buf + " " + p).strip() if buf else p
        else:
            if buf:
                out.append(buf)
                buf = ""
            out.append(p)
    if buf:
        out.append(buf)
    return out or [clean[:max_first]]


def pcm16_to_wav(pcm: bytes, rate: int = 24000, channels: int = 1) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(pcm)
    return buf.getvalue()


def _mime_to_wav(audio_bytes: bytes, mime: str) -> tuple[bytes, str]:
    mt = (mime or "").lower()
    if "wav" in mt:
        return audio_bytes, "audio/wav"
    if "mpeg" in mt or "mp3" in mt:
        return audio_bytes, "audio/mpeg"
    if "ogg" in mt:
        return audio_bytes, "audio/ogg"
    # Gemini часто отдаёт L16 PCM
    if "l16" in mt or "pcm" in mt or not mt:
        rate = 24000
        m = re.search(r"rate=(\d+)", mt)
        if m:
            rate = int(m.group(1))
        return pcm16_to_wav(audio_bytes, rate=rate), "audio/wav"
    return audio_bytes, mime or "application/octet-stream"


async def openai_tts_stream(
    api_key: str,
    text: str,
    *,
    voice: str = DEFAULT_OPENAI_TTS_VOICE,
    model: str = DEFAULT_OPENAI_TTS_MODEL,
    timeout: float = 120.0,
) -> AsyncIterator[bytes]:
    url = "https://api.openai.com/v1/audio/speech"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": model,
        "input": text[:4096],
        "voice": voice,
        "response_format": "mp3",
        "stream": True,
    }
    async with httpx.AsyncClient(timeout=timeout) as client:
        async with client.stream("POST", url, headers=headers, json=body) as resp:
            if resp.status_code >= 400:
                detail = (await resp.aread())[:400]
                raise ValueError(f"openai TTS: HTTP {resp.status_code} — {detail.decode('utf-8', errors='replace')}")
            async for chunk in resp.aiter_bytes():
                if chunk:
                    yield chunk


async def openai_tts_bytes(
    api_key: str,
    text: str,
    *,
    voice: str = DEFAULT_OPENAI_TTS_VOICE,
    model: str = DEFAULT_OPENAI_TTS_MODEL,
    timeout: float = 120.0,
) -> tuple[bytes, str]:
    parts: list[bytes] = []
    async for chunk in openai_tts_stream(
        api_key, text, voice=voice, model=model, timeout=timeout
    ):
        parts.append(chunk)
    return b"".join(parts), "audio/mpeg"


async def gemini_tts_bytes(
    api_key: str,
    text: str,
    *,
    voice: str = DEFAULT_GEMINI_TTS_VOICE,
    model: str = DEFAULT_GEMINI_TTS_MODEL,
    timeout: float = 120.0,
) -> tuple[bytes, str]:
    url = f"{_GEMINI_API_BASE}/v1beta/models/{model}:generateContent"
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key,
    }
    body = {
        "contents": [{"role": "user", "parts": [{"text": text[:4096]}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {
                "voiceConfig": {
                    "prebuiltVoiceConfig": {"voiceName": voice},
                }
            },
        },
    }
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(url, headers=headers, json=body)
        if resp.status_code >= 400:
            raise ValueError(
                f"gemini TTS: HTTP {resp.status_code} — "
                f"{(resp.text or '')[:400]}"
            )
        data = resp.json()
    candidates = data.get("candidates") or []
    if not candidates:
        raise ValueError("gemini TTS: пустой ответ")
    parts_out = candidates[0].get("content", {}).get("parts") or []
    for part in parts_out:
        inline = part.get("inlineData") or part.get("inline_data")
        if not inline:
            continue
        raw_b64 = inline.get("data") or ""
        mime = inline.get("mimeType") or inline.get("mime_type") or "audio/L16"
        audio = base64.b64decode(raw_b64)
        return _mime_to_wav(audio, mime)
    raise ValueError("gemini TTS: нет аудио в ответе")


async def synthesize_chunk(
    provider: str,
    api_key: str,
    text: str,
    *,
    voice: str,
    model: str | None = None,
) -> tuple[bytes, str]:
    p = (provider or "").strip().lower()
    if p == "openai":
        return await openai_tts_bytes(
            api_key,
            text,
            voice=voice or DEFAULT_OPENAI_TTS_VOICE,
            model=model or DEFAULT_OPENAI_TTS_MODEL,
        )
    if p == "gemini":
        return await gemini_tts_bytes(
            api_key,
            text,
            voice=voice or DEFAULT_GEMINI_TTS_VOICE,
            model=model or DEFAULT_GEMINI_TTS_MODEL,
        )
    raise ValueError(f"Неизвестный TTS provider: {provider}")


async def test_tts_connection(
    provider: str,
    api_key: str,
    *,
    voice: str | None = None,
    model: str | None = None,
    language: str = "ru",
) -> dict[str, Any]:
    """Короткая фраза для кнопки «Подтвердить ключ озвучки»."""
    p = (provider or "").strip().lower()
    if p == "openai":
        v = voice or DEFAULT_OPENAI_TTS_VOICE
        m = model or DEFAULT_OPENAI_TTS_MODEL
        phrase = "Ключ OpenAI для озвучки подтверждён." if language.startswith("ru") else "OpenAI speech key verified."
    elif p == "gemini":
        v = voice or DEFAULT_GEMINI_TTS_VOICE
        m = model or DEFAULT_GEMINI_TTS_MODEL
        phrase = "Ключ Gemini для озвучки подтверждён." if language.startswith("ru") else "Gemini speech key verified."
    else:
        raise ValueError("provider должен быть openai или gemini")
    audio, mime = await synthesize_chunk(p, api_key, phrase, voice=v, model=m)
    return {
        "ok": True,
        "verified": True,
        "provider": p,
        "model": m,
        "voice": v,
        "mime_type": mime,
        "audio_bytes": len(audio),
        "audio_base64": base64.b64encode(audio).decode("ascii"),
        "hint": f"Ключ {p} для озвучки проверен — TTS API отвечает.",
    }


__all__ = [
    "DEFAULT_GEMINI_TTS_MODEL",
    "DEFAULT_GEMINI_TTS_VOICE",
    "DEFAULT_OPENAI_TTS_MODEL",
    "DEFAULT_OPENAI_TTS_VOICE",
    "GEMINI_TTS_MODELS",
    "GEMINI_TTS_VOICES",
    "OPENAI_TTS_MODELS",
    "OPENAI_TTS_VOICES",
    "gemini_tts_bytes",
    "openai_tts_stream",
    "split_tts_chunks",
    "synthesize_chunk",
    "test_tts_connection",
    "tts_catalog",
]
