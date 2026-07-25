"""
COMPUTE_PROFILE — единый рычаг железа поверх ENABLE_*.

Профили (local-first по умолчанию):
  lite     — Truth Kernel only; LLM/embeddings не включаются
  standard — физиология памяти (Velum/FSRS/volition/audit) + EdgeSuggester + XAI
  heavy    — + emergence/reasoning/ETIR/L4.5/event-bus (мощное железо)

Явный ENABLE_*=0|1 всегда побеждает профиль.
LLM_PROVIDER / concept LLM naming профилем НЕ трогаются.
"""

from __future__ import annotations

import os
from typing import Any

PROFILE_LITE = "lite"
PROFILE_STANDARD = "standard"
PROFILE_HEAVY = "heavy"
VALID_PROFILES = frozenset({PROFILE_LITE, PROFILE_STANDARD, PROFILE_HEAVY})
DEFAULT_PROFILE = PROFILE_LITE

# Флаги, которые профиль может поднять, если ENV не задан явно.
# Значение True = "1" по умолчанию для этого профиля.
_STANDARD_FLAGS: dict[str, bool] = {
    "ENABLE_VELUM": True,
    "VELUM_USE_FSRS_DECAY": True,
    "ENABLE_SALIENCE": True,
    "ENABLE_MEMORY_VOLITION": True,
    "ENABLE_RESPONSE_AUDIT": True,
    "ENABLE_EDGE_SUGGESTER": True,
    "ENABLE_XAI": True,
    "ENABLE_WRITE_GATE": True,
}

_HEAVY_EXTRA: dict[str, bool] = {
    "ENABLE_CONCEPT_EMERGENCE": True,
    "ENABLE_REASONING_BANK": True,
    "ENABLE_ETIR": True,
    "ENABLE_PREDICTIVE_FUSION": True,
    "ENABLE_DECAY_ORCHESTRATOR": True,
    "ENABLE_L45": True,
    "ENABLE_FOCUS_ENGINE": True,
    "ENABLE_EVENT_BUS": True,
    "ENABLE_EDGE_SUGGESTER": True,
    "ENABLE_XAI": True,
    "ENABLE_ANALOGY_HINTS": True,
}


def normalize_compute_profile(raw: str | None) -> str:
    value = (raw or DEFAULT_PROFILE).strip().lower()
    if value not in VALID_PROFILES:
        return DEFAULT_PROFILE
    return value


def get_compute_profile() -> str:
    return normalize_compute_profile(os.getenv("COMPUTE_PROFILE"))


def profile_flag_defaults(profile: str | None = None) -> dict[str, bool]:
    """Дефолты флагов для профиля (без чтения ENV)."""
    p = normalize_compute_profile(profile)
    if p == PROFILE_LITE:
        return {}
    out = dict(_STANDARD_FLAGS)
    if p == PROFILE_HEAVY:
        out.update(_HEAVY_EXTRA)
    return out


def env_explicitly_set(name: str) -> bool:
    return os.getenv(name) is not None


def resolve_flag(name: str, *, default: str = "0", profile: str | None = None) -> bool:
    """Разрешить булев флаг: явный ENV > профиль > default."""
    raw = os.getenv(name)
    if raw is not None:
        return raw.strip().lower() in ("1", "true", "yes", "on")
    defaults = profile_flag_defaults(profile if profile is not None else get_compute_profile())
    if name in defaults:
        return bool(defaults[name])
    return default.strip().lower() in ("1", "true", "yes", "on")


def describe_compute_profile(profile: str | None = None) -> dict[str, Any]:
    p = normalize_compute_profile(profile if profile is not None else get_compute_profile())
    defaults = profile_flag_defaults(p)
    return {
        "compute_profile": p,
        "default": DEFAULT_PROFILE,
        "valid": sorted(VALID_PROFILES),
        "local_first": p == PROFILE_LITE,
        "profile_enables": sorted(k for k, v in defaults.items() if v),
        "notes": {
            PROFILE_LITE: "Truth Kernel; LLM/embeddings off unless explicit",
            PROFILE_STANDARD: "Physiology + HITL edges + XAI; still LLM_PROVIDER untouched",
            PROFILE_HEAVY: "Full research layers; still no forced LLM provider",
        }[p],
        "never_auto_enabled": [
            "LLM_PROVIDER",
            "ENABLE_CONCEPT_LLM_NAMING",
            "ENABLE_CROSS_DOMAIN_LLM_ROUTING",
        ],
    }


__all__ = [
    "DEFAULT_PROFILE",
    "PROFILE_HEAVY",
    "PROFILE_LITE",
    "PROFILE_STANDARD",
    "VALID_PROFILES",
    "describe_compute_profile",
    "env_explicitly_set",
    "get_compute_profile",
    "normalize_compute_profile",
    "profile_flag_defaults",
    "resolve_flag",
]
