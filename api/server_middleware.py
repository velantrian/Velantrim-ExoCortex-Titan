"""
HTTP middleware extracted from server.py (security headers + opt-in rate limit).
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import JSONResponse


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