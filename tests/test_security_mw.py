"""Security tail: headers always-on, CORS tightened, rate-limit gated by flag."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import server
from core import rate_limit


@pytest.fixture
def client():
    return TestClient(server.app)


# ── security headers (always-on) ────────────────────────────────────────────────

def test_security_headers_present(client):
    r = client.get("/health")
    assert r.headers.get("X-Content-Type-Options") == "nosniff"
    assert r.headers.get("X-Frame-Options") == "DENY"
    assert "Referrer-Policy" in r.headers


def test_csp_header_present_and_locks_down_key_directives(client):
    """Low finding (Claude audit 2026-07-28): no CSP anywhere. Verified live
    against the actual console pages (static/console/*.html) with
    Playwright — zero CSP violations, page fully interactive — before
    adding this; 'unsafe-inline' is required by the console's existing
    inline <script>/<style>, so this checks the directives that ARE
    meaningfully locked down rather than asserting the whole policy string."""
    r = client.get("/health")
    csp = r.headers.get("Content-Security-Policy", "")
    assert "default-src 'self'" in csp
    assert "frame-ancestors 'none'" in csp
    assert "object-src 'none'" in csp
    assert "base-uri 'self'" in csp
    assert "form-action 'self'" in csp


# ── rate-limit core: token bucket ────────────────────────────────────────────────

def test_rate_limit_core_allows_then_blocks(monkeypatch):
    rate_limit.reset()
    # tiny bucket: capacity 2, no refill within the test window. Patch the get_config
    # name that core.rate_limit actually bound at import time.
    class _App:
        enable_rate_limit = True
        rate_limit_capacity = 2
        rate_limit_refill_per_sec = 0.0

    monkeypatch.setattr(rate_limit, "get_config",
                        lambda: type("C", (), {"app": _App()})())

    t = 1000.0
    assert rate_limit.check_rate_limit("1.2.3.4", now=t)[0] is True
    assert rate_limit.check_rate_limit("1.2.3.4", now=t)[0] is True
    allowed, retry = rate_limit.check_rate_limit("1.2.3.4", now=t)
    assert allowed is False and retry >= 1


def test_rate_limit_disabled_by_default(client):
    # flag off (default) → many rapid requests never 429
    rate_limit.reset()
    codes = {client.get("/health").status_code for _ in range(20)}
    assert 429 not in codes


def test_is_rate_limit_flag_default_off():
    from core.runtime_flags import is_rate_limit_enabled

    assert is_rate_limit_enabled() is False


# ── XFF-aware client host resolution (Low finding, Claude audit 2026-07-28) ──

class _FakeClient:
    def __init__(self, host):
        self.host = host


class _FakeRequest:
    def __init__(self, *, client_host, headers=None):
        self.client = _FakeClient(client_host) if client_host else None
        self.headers = headers or {}


def test_client_host_ignores_xff_by_default(monkeypatch):
    """TRUST_PROXY_HEADERS is off by default — the reverse-proxy's own
    address must never be silently overridden by a client-supplied header
    (that would let any client bypass rate limiting by spoofing XFF)."""
    from api.server_middleware import _client_host

    req = _FakeRequest(client_host="10.0.0.1", headers={"x-forwarded-for": "1.2.3.4"})
    assert _client_host(req) == "10.0.0.1"


def test_client_host_honors_xff_when_trust_proxy_headers_enabled(monkeypatch):
    from api import server_middleware
    from core import runtime_flags

    monkeypatch.setattr(runtime_flags, "is_trust_proxy_headers_enabled", lambda: True)

    fake_req = _FakeRequest(
        client_host="10.0.0.1",
        headers={"x-forwarded-for": "203.0.113.7, 10.0.0.1"},
    )
    assert server_middleware._client_host(fake_req) == "203.0.113.7"


def test_client_host_falls_back_when_xff_missing_even_if_trusted(monkeypatch):
    from api import server_middleware
    from core import runtime_flags

    monkeypatch.setattr(runtime_flags, "is_trust_proxy_headers_enabled", lambda: True)

    fake_req = _FakeRequest(client_host="10.0.0.1", headers={})
    assert server_middleware._client_host(fake_req) == "10.0.0.1"
