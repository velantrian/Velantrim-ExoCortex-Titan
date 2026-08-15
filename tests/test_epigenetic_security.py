"""Security regressions for the /system/epigenetic diagnostic endpoint.

Issue #52 requires this public diagnostic surface to follow the same API-key and
error-sanitization boundary as the rest of Titan's protected operational API.
"""

import importlib

from fastapi.testclient import TestClient

KEY = "secret-test-key-epigenetic"


def _runtime_modules():
    """Resolve modules at test time because integration tests reload server/core."""

    server = importlib.import_module("server")
    epigenetic = importlib.import_module("core.epigenetic_adaptation")
    return server, epigenetic


def _client(server) -> TestClient:
    return TestClient(server.app)


def test_epigenetic_requires_api_key(monkeypatch):
    server, _ = _runtime_modules()
    monkeypatch.setattr(server, "API_KEY", KEY)

    response = _client(server).get("/system/epigenetic")

    assert response.status_code == 401


def test_epigenetic_allows_authorized_read(monkeypatch):
    server, epigenetic = _runtime_modules()
    monkeypatch.setattr(server, "API_KEY", KEY)

    class _Engine:
        def stats(self):
            return {"status": "ok", "writes": 0}

    monkeypatch.setattr(epigenetic, "get_epigenetic_engine", lambda: _Engine())

    response = _client(server).get(
        "/system/epigenetic",
        headers={"X-Api-Key": KEY},
    )

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "writes": 0}


def test_epigenetic_internal_error_is_sanitized(monkeypatch):
    server, epigenetic = _runtime_modules()
    monkeypatch.setattr(server, "API_KEY", KEY)

    def _boom():
        raise RuntimeError("private-diagnostic-sentinel")

    monkeypatch.setattr(epigenetic, "get_epigenetic_engine", _boom)

    response = _client(server).get(
        "/system/epigenetic",
        headers={"X-Api-Key": KEY},
    )

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error"}
    assert "private-diagnostic-sentinel" not in response.text
