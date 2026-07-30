"""
HTTP middleware extracted from server.py (security headers + opt-in rate limit).
"""
from __future__ import annotations

import json
import logging
from queue import Full, Queue
from threading import Lock, Thread
from typing import Mapping

from fastapi import FastAPI
from fastapi.responses import JSONResponse, Response

_LOG = logging.getLogger(__name__)
_SHADOW_QUEUE_CAPACITY = 4


def _response_with_body(response, body: bytes) -> Response:
    """Rebuild a consumed response without collapsing repeated raw headers."""

    restored = Response(
        content=body,
        status_code=response.status_code,
        background=response.background,
    )
    generated_length = next(
        (
            header
            for header in restored.raw_headers
            if header[0].lower() == b"content-length"
        ),
        None,
    )
    original_without_length = [
        header
        for header in response.raw_headers
        if header[0].lower() != b"content-length"
    ]
    restored.raw_headers = [
        *([generated_length] if generated_length is not None else []),
        *original_without_length,
    ]
    return restored


def _json_response_with_raw_headers(
    response, content: Mapping[str, object]
) -> JSONResponse:
    """Replace JSON body while preserving repeated legacy headers verbatim."""

    augmented = JSONResponse(
        status_code=response.status_code,
        content=content,
        background=response.background,
    )
    generated_length = next(
        (
            header
            for header in augmented.raw_headers
            if header[0].lower() == b"content-length"
        ),
        None,
    )
    original_without_length = [
        header
        for header in response.raw_headers
        if header[0].lower() != b"content-length"
    ]
    augmented.raw_headers = [
        *([generated_length] if generated_length is not None else []),
        *original_without_length,
    ]
    return augmented


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


class _SynapticShadowDispatcher:
    """One daemon worker with bounded pending work and explicit backpressure."""

    def __init__(self, *, capacity: int = _SHADOW_QUEUE_CAPACITY) -> None:
        self._queue: Queue[tuple[object, ...]] = Queue(maxsize=capacity)
        self._start_lock = Lock()
        self._worker: Thread | None = None

    def submit(self, facts: tuple[object, ...]) -> dict[str, object]:
        from core.synaptic_shadow import shadow_queue_preview

        try:
            self._queue.put_nowait(facts)
        except Full:
            return shadow_queue_preview(
                status="dropped",
                input_facts=len(facts),
                error_code="shadow_queue_full",
            )
        self._ensure_worker()
        return shadow_queue_preview(status="queued", input_facts=len(facts))

    def _ensure_worker(self) -> None:
        with self._start_lock:
            if self._worker is not None and self._worker.is_alive():
                return
            self._worker = Thread(
                target=self._run,
                name="synaptic-shadow",
                daemon=True,
            )
            self._worker.start()

    def _run(self) -> None:
        from core.synaptic_shadow import build_synaptic_shadow_preview

        while True:
            facts = self._queue.get()
            try:
                preview = build_synaptic_shadow_preview(facts)
                _LOG.info(
                    "synaptic shadow preview completed",
                    extra={"synaptic_shadow_metrics": preview.get("metrics", {})},
                )
            except Exception as exc:  # noqa: BLE001 — isolated daemon boundary
                _LOG.warning(
                    "synaptic shadow preview failed: %s",
                    type(exc).__name__,
                )
            finally:
                self._queue.task_done()


_SHADOW_DISPATCHER = _SynapticShadowDispatcher()


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
            return _response_with_body(response, body)
        if not isinstance(payload, dict):
            return _response_with_body(response, body)

        try:
            from core.synaptic_shadow import snapshot_synaptic_shadow_input

            facts = payload.get("facts")
            if not isinstance(facts, list):
                facts = []
            snapshot = snapshot_synaptic_shadow_input(facts)
            shadow = _SHADOW_DISPATCHER.submit(snapshot)
        except Exception as exc:  # noqa: BLE001 — shadow must never break legacy
            error_code = getattr(exc, "code", type(exc).__name__)
            if not isinstance(error_code, str) or not error_code.strip():
                error_code = type(exc).__name__
            shadow = {
                "schema_version": "synaptic.shadow-preview.v1",
                "status": "error",
                "mode": "shadow_only",
                "legacy_answer_authoritative": True,
                "source_mode": "legacy_fact_projection",
                "error_code": error_code,
            }

        augmented = dict(payload)
        augmented["synaptic_shadow"] = shadow
        return _json_response_with_raw_headers(response, augmented)
