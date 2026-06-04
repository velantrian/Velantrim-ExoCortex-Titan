"""Импорт ExoCortex-модулей после переноса из Graphiti (V8.6)."""

from __future__ import annotations

import importlib
import sys

import pytest

MODULES = [
    "core.feature_config",
    "core.storage_facade",
    "core.graph_store",
    "core.velum",
    "core.velum_bridge",
    "core.etir",
    "core.etir_bridge",
    "core.immutable_core",
    "core.concept_emergence",
    "core.reasoning_bank",
    "core.causal_bridge",
    "core.focus_engine",
    "core.response_audit",
    "core.l45_bridge",
    "core.predictive_fusion",
    "core.fusion_bridge",
    "core.decay_orchestrator",
    "core.exocortex_hooks",
    "api.exocortex_api",
]


@pytest.mark.parametrize("mod", MODULES)
def test_import_exocortex_module(mod: str):
    if mod in sys.modules:
        del sys.modules[mod]
    importlib.import_module(mod)
