"""Regression: /health must not materialize all facts or leak exception text."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import server


@pytest.fixture
def client():
    return TestClient(server.app)


def test_health_uses_count_not_get_all_facts(client, monkeypatch):
    called = {"get_all": 0, "count": 0}

    def _boom_get_all(*a, **k):
        called["get_all"] += 1
        raise AssertionError("get_all_facts must not be called from /health")

    def _count():
        called["count"] += 1
        return {"Observed": 2, "Validated": 1}

    monkeypatch.setattr(server, "get_all_facts", _boom_get_all)
    monkeypatch.setattr(server._store, "count_facts_by_epistemic_state", _count)
    # Avoid MHI noise / cache from prior calls
    monkeypatch.setattr(server, "_mhi_cache", {"data": None, "at": 0.0})

    r = client.get("/health")
    assert r.status_code in (200, 500, 503)
    data = r.json()
    assert called["get_all"] == 0
    assert called["count"] == 1
    assert data.get("facts") == {"Observed": 2, "Validated": 1}


def test_health_mhi_error_is_generic(client, monkeypatch):
    monkeypatch.setattr(server, "_mhi_cache", {"data": None, "at": 0.0})

    class _Boom:
        def calculate(self):
            raise RuntimeError("secret/path/to/db.sqlite leaked")

    def _fake_calc(*a, **k):
        return _Boom()

    monkeypatch.setattr(server, "MHICalculator", _fake_calc)
    monkeypatch.setattr(
        server._store, "count_facts_by_epistemic_state", lambda: {}
    )

    r = client.get("/health")
    assert r.status_code == 500
    body = r.text
    assert "secret/path" not in body
    assert "leaked" not in body
    assert r.json()["mhi"]["error"] == "mhi_unavailable"
