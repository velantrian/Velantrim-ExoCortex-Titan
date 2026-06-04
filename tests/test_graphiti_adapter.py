"""Graphiti adapter (Спринт 2.5, no-op без Neo4j)."""

from __future__ import annotations

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_graphiti_unavailable_by_default(monkeypatch):
    from core.feature_config import clear_config_cache
    from core.graphiti_adapter import get_graphiti_client, reload_causal_from_graphiti

    monkeypatch.delenv("STORAGE_BACKEND", raising=False)
    clear_config_cache()
    assert get_graphiti_client() is None

    result = asyncio.run(reload_causal_from_graphiti())
    assert result["ok"] is False


def test_is_graphiti_backend_flag(monkeypatch):
    from core.graphiti_adapter import is_graphiti_backend

    monkeypatch.setenv("STORAGE_BACKEND", "sqlite")
    assert is_graphiti_backend() is False
    monkeypatch.setenv("STORAGE_BACKEND", "neo4j")
    assert is_graphiti_backend() is True
