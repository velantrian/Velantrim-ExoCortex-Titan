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
