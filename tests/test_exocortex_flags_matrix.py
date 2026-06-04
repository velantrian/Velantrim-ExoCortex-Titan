"""Матрица ENV-флагов ExoCortex: импорт и feature_config."""

from __future__ import annotations

import importlib
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

FLAG_CASES = [
    ("ENABLE_VELUM", "enable_velum"),
    ("ENABLE_ETIR", "enable_etir"),
    ("ENABLE_L45", "enable_l45"),
    ("ENABLE_L6_WELFARE", "enable_l6_welfare"),
    ("ENABLE_EVENT_BUS", "enable_event_bus"),
    ("ENABLE_PREDICTIVE_FUSION", "enable_predictive_fusion"),
]


@pytest.fixture(autouse=True)
def _clear_cfg():
    yield
    from core.feature_config import clear_config_cache

    clear_config_cache()


@pytest.mark.parametrize("env_name,attr", FLAG_CASES)
def test_feature_config_reads_flag(env_name: str, attr: str, monkeypatch):
    monkeypatch.setenv(env_name, "1")
    from core.feature_config import clear_config_cache, get_config

    clear_config_cache()
    assert getattr(get_config().app, attr) is True

    monkeypatch.setenv(env_name, "0")
    clear_config_cache()
    assert getattr(get_config().app, attr) is False


def test_causal_graph_enabled_helper(monkeypatch):
    monkeypatch.setenv("ENABLE_CAUSAL_GRAPH", "1")
    from core.causal_graph import is_causal_graph_enabled
    from core.feature_config import clear_config_cache

    clear_config_cache()
    assert is_causal_graph_enabled() is True


@pytest.mark.parametrize(
    "mod",
    [
        "core.causal_bridge",
        "core.horizons_catalog",
        "core.layers_status",
    ],
)
def test_import_with_l6_flags(monkeypatch, mod: str):
    monkeypatch.setenv("ENABLE_L6_WELFARE", "1")
    monkeypatch.setenv("ENABLE_EVENT_BUS", "1")
    from core.feature_config import clear_config_cache

    clear_config_cache()
    if mod in sys.modules:
        del sys.modules[mod]
    importlib.import_module(mod)
