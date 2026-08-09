"""
HTTP middleware extracted from server.py (security headers + opt-in rate limit).
"""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
import json
import logging
from queue import Full, Queue
from threading import Lock, Thread
from time import perf_counter
from typing import Mapping

from fastapi import FastAPI
from fastapi.responses import JSONResponse, Response

_LOG = logging.getLogger(__name__)
_SHADOW_QUEUE_CAPACITY = 4
_CONTINUITY_LIFESPAN_MARKER = "_continuity_runtime_lifespan_installed"


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
        self._queue: Queue[tuple[str, tuple[object, ...]]] = Queue(maxsize=capacity)
        self._start_lock = Lock()
        self._worker: Thread | None = None

    def submit(
        self,
        facts: tuple[object, ...],
        *,
        query: str = "",
    ) -> dict[str, object]:
        from core.synaptic_shadow import shadow_queue_preview

        try:
            self._queue.put_nowait((query, facts))
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
            query, facts = self._queue.get()
            try:
                preview = build_synaptic_shadow_preview(facts)
                _LOG.info(
                    "synaptic shadow preview completed",
                    extra={"synaptic_shadow_metrics": preview.get("metrics", {})},
                )
                try:
                    from core.runtime_flags import env_flag

                    rco_enabled = env_flag("ENABLE_RCO_SHADOW")
                except Exception:  # noqa: BLE001
                    rco_enabled = False
                if rco_enabled:
                    started = perf_counter()
                    try:
                        from core.policy_kernel import get_policy_kernel
                        from core.rapid_orientation import (
                            build_rapid_orientation_receipt,
                        )

                        policy_snapshot = get_policy_kernel().capture_snapshot()
                        receipt = build_rapid_orientation_receipt(
                            query,
                            preview,
                            policy_snapshot,
                        )
                        metrics = dict(_mapping_or_empty(receipt.get("metrics")))
                        metrics["latency_ms"] = round(
                            (perf_counter() - started) * 1000,
                            3,
                        )
                        _LOG.info(
                            "rapid orientation shadow receipt completed",
                            extra={
                                "rapid_orientation_receipt": receipt,
                                "rapid_orientation_metrics": metrics,
                            },
                        )
                    except Exception as exc:  # noqa: BLE001 — isolated experiment
                        _LOG.warning(
                            "rapid orientation shadow failed: %s",
                            type(exc).__name__,
                        )
            except Exception as exc:  # noqa: BLE001 — isolated daemon boundary
                _LOG.warning(
                    "synaptic shadow preview failed: %s",
                    type(exc).__name__,
                )
            finally:
                self._queue.task_done()


_SHADOW_DISPATCHER = _SynapticShadowDispatcher()


def _mapping_or_empty(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _install_continuity_runtime_lifespan(app: FastAPI) -> None:
    """Compose bounded Continuity ownership around the existing server lifespan."""

    if getattr(app.state, _CONTINUITY_LIFESPAN_MARKER, False):
        return
    original_lifespan = app.router.lifespan_context

    @asynccontextmanager
    async def _composed_lifespan(app: FastAPI):
        async with original_lifespan(app):
            from core.continuity.runtime_composition import (
                compose_continuity_runtime_from_environment,
            )

            owner = compose_continuity_runtime_from_environment()
            app.state.continuity_runtime_owner = None
            if owner is not None:
                try:
                    await asyncio.to_thread(owner.startup)
                except Exception:
                    await asyncio.to_thread(owner.shutdown)
                    raise
                app.state.continuity_runtime_owner = owner
            try:
                yield
            finally:
                if owner is not None:
                    await asyncio.to_thread(owner.shutdown)
                app.state.continuity_runtime_owner = None

    app.router.lifespan_context = _composed_lifespan
    setattr(app.state, _CONTINUITY_LIFESPAN_MARKER, True)


def register_server_middleware(app: FastAPI) -> None:
    _install_continuity_runtime_lifespan(app)

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
            query = payload.get("query")
            if not isinstance(query, str):
                query = ""
            snapshot = snapshot_synaptic_shadow_input(facts)
            shadow = _SHADOW_DISPATCHER.submit(snapshot, query=query)
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
