"""COMPUTE_PROFILE: lite/standard/heavy поверх ENABLE_*."""

from __future__ import annotations

import pytest

from core.compute_profile import (
    PROFILE_HEAVY,
    PROFILE_LITE,
    PROFILE_STANDARD,
    describe_compute_profile,
    profile_flag_defaults,
    resolve_flag,
)
from core.feature_config import clear_config_cache, get_config


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    monkeypatch.delenv("COMPUTE_PROFILE", raising=False)
    for key in (
        "ENABLE_VELUM",
        "ENABLE_EDGE_SUGGESTER",
        "ENABLE_XAI",
        "ENABLE_CONCEPT_EMERGENCE",
        "ENABLE_CONCEPT_LLM_NAMING",
        "ENABLE_MEMORY_VOLITION",
        "ENABLE_L45",
        "ENABLE_WRITE_GATE",
    ):
        monkeypatch.delenv(key, raising=False)
    clear_config_cache()
    yield
    clear_config_cache()


def test_lite_is_default_local_first():
    assert profile_flag_defaults(PROFILE_LITE) == {}
    assert describe_compute_profile(PROFILE_LITE)["local_first"] is True


def test_standard_enables_physiology_not_llm_naming(monkeypatch):
    monkeypatch.setenv("COMPUTE_PROFILE", PROFILE_STANDARD)
    clear_config_cache()
    cfg = get_config().app
    assert cfg.compute_profile == PROFILE_STANDARD
    assert cfg.enable_velum is True
    assert cfg.enable_edge_suggester is True
    assert cfg.enable_xai is True
    assert cfg.enable_memory_volition is True
    assert cfg.enable_write_gate is True
    assert cfg.enable_concept_emergence is False
    assert cfg.enable_concept_llm_naming is False


def test_heavy_enables_research_layers(monkeypatch):
    monkeypatch.setenv("COMPUTE_PROFILE", PROFILE_HEAVY)
    clear_config_cache()
    cfg = get_config().app
    assert cfg.enable_concept_emergence is True
    assert cfg.enable_reasoning_bank is True
    assert cfg.enable_etir is True
    assert cfg.enable_l45 is True
    assert cfg.enable_analogy_hints is True
    assert cfg.enable_concept_llm_naming is False


def test_explicit_env_beats_profile(monkeypatch):
    monkeypatch.setenv("COMPUTE_PROFILE", PROFILE_STANDARD)
    monkeypatch.setenv("ENABLE_VELUM", "0")
    monkeypatch.setenv("ENABLE_EDGE_SUGGESTER", "0")
    clear_config_cache()
    cfg = get_config().app
    assert cfg.enable_velum is False
    assert cfg.enable_edge_suggester is False
    assert resolve_flag("ENABLE_XAI", profile=PROFILE_STANDARD) is True


def test_lite_config_keeps_layers_off(monkeypatch):
    monkeypatch.setenv("COMPUTE_PROFILE", PROFILE_LITE)
    clear_config_cache()
    cfg = get_config().app
    assert cfg.enable_velum is False
    assert cfg.enable_edge_suggester is False
    assert cfg.enable_xai is False
