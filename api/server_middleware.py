"""
HTTP middleware extracted from server.py (security headers + opt-in rate limit).
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import JSONResponse


def _client_host(request) -> str:
    """Resolve the client's address for rate-limiting/HSTS-skip purposes.

    Low finding (Claude audit 2026-07-28): both call sites keyed on
    request.client.host — correct and unspoofable for a direct deployment,
    but that's the load balancer's own address once behind a reverse proxy,
    putting every real client in one shared bucket. Only honors
    X-Forwarded-For when TRUST_PROXY_HEADERS is explicitly set (default
    off) — an operator opts in only once their proxy is actually the one
    setting/overwriting that header, at which point the leftmost entry is
    the original client.
    """
    direct = (request.client.host if request.client else "") or ""
    from core.runtime_flags import is_trust_proxy_headers_enabled

    if not is_trust_proxy_headers_enabled():
        return direct
    forwarded = request.headers.get("x-forwarded-for", "")
    first = forwarded.split(",")[0].strip()
    return first or direct


# Low finding (Claude audit 2026-07-28): no Content-Security-Policy anywhere.
# The console (static/console/*.html) does client-side markdown rendering
# with escapeHtml() as its only injection guard — CSP is meant to be a
# second line of defense if that escaping ever has a gap.
#
# NOT a full lockdown: the console's HTML ships inline <script>/<style>
# blocks and per-element style="" attributes with no nonce infrastructure
# (verified: 2 inline <script> blocks, 1 inline <style> block, 18 inline
# style attributes in static/console/index.html, same pattern across the
# other console pages) — a strict script-src/style-src without
# 'unsafe-inline' would break the console outright, and refactoring six
# HTML files onto nonces isn't something to do without live-browser
# verification across every route. 'unsafe-inline' therefore does NOT stop
# an attacker-injected inline <script> from running (this pass doesn't
# close that specific gap) — but it does stop loading an external script
# (<script src="https://attacker...">), image/style/connect exfiltration to
# a foreign origin, framing (belt-and-suspenders with the existing
# X-Frame-Options), plugin-based content (object-src), and base-tag/
# form-action hijacking. Verified against every static/console/*.html file:
# no external <script>/<link> src, no data: URIs, no WebSocket/EventSource,
# only same-origin fetch() calls and a few plain <a href> links (CSP never
# restricts navigation via anchor clicks).
_CSP_POLICY = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline'; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data:; "
    "connect-src 'self'; "
    "frame-ancestors 'none'; "
    "object-src 'none'; "
    "base-uri 'self'; "
    "form-action 'self'"
)


def register_server_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def _security_headers_mw(request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("X-XSS-Protection", "0")
        response.headers.setdefault("Content-Security-Policy", _CSP_POLICY)
        host = _client_host(request) or ""
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

        host = _client_host(request) or "unknown"
        allowed, retry_after = check_rate_limit(host)
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={"error": "rate_limited", "retry_after": retry_after},
                headers={"Retry-After": str(retry_after)},
            )
        return await call_next(request)
