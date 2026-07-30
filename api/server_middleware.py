"""
HTTP middleware extracted from server.py (security headers + opt-in rate limit).
"""
from __future__ import annotations

import asyncio
import json

from fastapi import FastAPI
from fastapi.responses import JSONResponse, Response


def _response_headers(response) -> dict[str, str]:
    headers = dict(response.headers)
    headers.pop("content-length", None)
    return headers


async def _response_body(response) -> bytes:
    body = getattr(response, "body", None)
    if isinstance(body, bytes):
        return body
    iterator = getattr(response, "body_iterator", None)
    if iterator is None:
        return b""
    chunks: list[bytes] = []
    async for chunk in iterator:
        chunks.append(chunk if isinstance(chunk, bytes) else str(chunk).encode("utf-8"))
    return b"".join(chunks)


def _restore_response(response, body: bytes) -> Response:
    return Response(
        content=body,
        status_code=response.status_code,
        headers=_response_headers(response),
        media_type=response.media_type,
        background=response.background,
    )


def register_server_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def _security_headers_mw(request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("X-XSS-Protection", "0")
        host = (request.client.host if request.client else "") or ""
        if host not in ("127.0.0.1", "::1", "localhost"):
            response.headers.setdefault(
                "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
            )
        return response

    @app.middleware("http")
    async def _rate_limit_mw(request, call_next):
        try:
            from core.runtime_flags import is_rate_limit_enabled
        except Exception:  # noqa: BLE001
            return await call_next(request)
        if not is_rate_limit_enabled():
            return await call_next(request)
        from core.rate_limit import check_rate_limit

        host = (request.client.host if request.client else "") or "unknown"
        allowed, retry_after = check_rate_limit(host)
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={"error": "rate_limited", "retry_after": retry_after},
                headers={"Retry-After": str(retry_after)},
            )
        return await call_next(request)

    @app.middleware("http")
    async def _synaptic_shadow_mw(request, call_next):
        response = await call_next(request)
        try:
            from core.runtime_flags import env_flag

            enabled = env_flag("ENABLE_SYNAPTIC_SHADOW")
        except Exception:  # noqa: BLE001
            enabled = False
        content_type = response.headers.get("content-type", "").lower()
        if (
            not enabled
            or request.method != "POST"
            or request.url.path != "/query"
            or response.status_code != 200
            or "application/json" not in content_type
        ):
            return response

        body = await _response_body(response)
        try:
            payload = json.loads(body)
        except (TypeError, ValueError):
            return _restore_response(response, body)
        if not isinstance(payload, dict):
            return _restore_response(response, body)

        try:
            from core.synaptic_shadow import build_synaptic_shadow_preview

            facts = payload.get("facts")
            if not isinstance(facts, list):
                facts = []
            shadow = await asyncio.to_thread(build_synaptic_shadow_preview, facts)
        except Exception as exc:  # noqa: BLE001 — shadow must never break legacy
            shadow = {
                "schema_version": "synaptic.shadow-preview.v1",
                "status": "error",
                "mode": "shadow_only",
                "legacy_answer_authoritative": True,
                "source_mode": "legacy_fact_projection",
                "error_code": type(exc).__name__,
            }

        augmented = dict(payload)
        augmented["synaptic_shadow"] = shadow
        return JSONResponse(
            status_code=response.status_code,
            content=augmented,
            headers=_response_headers(response),
            background=response.background,
        )
