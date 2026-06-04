"""
Каталог Horizons — research / experimental / vision (V8.6).

Единый источник для docs и GET /layers/status.
"""

from __future__ import annotations

from typing import Any, TypedDict


class HorizonEntry(TypedDict, total=False):
    id: str
    title: str
    status: str  # research | experimental | vision | mvp_partial
    enabled: bool
    runtime: bool  # есть ли код в репозитории
    rfc: str
    docs: str
    env_flag: str
    note: str


def research_entries() -> list[HorizonEntry]:
    """Спека есть, production-кода нет (или только заготовки)."""
    return [
        {
            "id": "L2_5_staging",
            "title": "L2.5 Staging Layer",
            "status": "research",
            "enabled": False,
            "runtime": False,
            "rfc": "RFC0014",
            "docs": "docs/horizons/L2_5_STAGING.md",
            "note": "Буфер гипотез между L2 и L3; Resource-Aware Scheduler — в исследовании.",
        },
        {
            "id": "L6_full_rfc0069",
            "title": "L6 Values Core (полный RFC0069)",
            "status": "research",
            "enabled": False,
            "runtime": False,
            "rfc": "RFC0069",
            "docs": "docs/horizons/L6_VALUES_WELFARE.md",
            "note": "IntrospectionProbe, RingZeroProtector — после MVP WelfareMonitor.",
        },
        {
            "id": "R2_category_truth_gate",
            "title": "Category-Theoretic Truth Gate",
            "status": "research",
            "enabled": False,
            "runtime": False,
            "rfc": "—",
            "docs": "docs/horizons/R2_CATEGORY_TRUTH_GATE.md",
            "note": "Compile-time формализация ESM; Catlab / mypy stubs.",
        },
        {
            "id": "R3_evo_memory",
            "title": "Evo-Memory (Think → Act → Refine)",
            "status": "research",
            "enabled": False,
            "runtime": False,
            "rfc": "—",
            "docs": "docs/horizons/R3_EVO_MEMORY.md",
            "note": "Цикл Think→Act→Refine: стратегии L4, ESM, эпизоды L1.5.",
        },
        {
            "id": "R4_global_workspace",
            "title": "Global Workspace (LIDA-style)",
            "status": "research",
            "enabled": False,
            "runtime": False,
            "rfc": "—",
            "docs": "docs/horizons/R4_GLOBAL_WORKSPACE.md",
            "note": "LIDA-style broadcast сцены между L4 и L5.",
        },
        {
            "id": "R5_k_lines",
            "title": "K-Lines (Minsky)",
            "status": "research",
            "enabled": False,
            "runtime": False,
            "rfc": "—",
            "docs": "docs/horizons/R5_K_LINES.md",
            "note": "K-узлы Minsky: reinstatement контекста задач.",
        },
        {
            "id": "kde",
            "title": "Knowledge Distillation Engine",
            "status": "research",
            "enabled": False,
            "runtime": False,
            "rfc": "—",
            "docs": "docs/horizons/KDE_DISTILLATION.md",
            "note": "Knowledge Distillation Engine — gist без потери provenance.",
        },
    ]


def experimental_entries() -> list[HorizonEntry]:
    """Черновой код или partial MVP; по умолчанию выкл."""
    return [
        {
            "id": "E1_neurocore",
            "title": "NeuroCore (Plastic Memory)",
            "status": "experimental",
            "enabled": False,
            "runtime": False,
            "rfc": "RFC0068",
            "docs": "docs/horizons/E1_NEUROCORE.md",
            "env_flag": "NEUROCORE_ENABLED",
            "note": "Plastic memory RFC0068; Phase 0 log → shadow Hebbian.",
        },
        {
            "id": "E2_mhi_phase2",
            "title": "MHICalculator Phase 2",
            "status": "experimental",
            "enabled": False,
            "runtime": True,
            "rfc": "RFC0070",
            "docs": "docs/horizons/E2_MHI_PHASE2.md",
            "note": "Phase 1 в core/mhi.py 🟢; Phase 2 topology/ML — Horizons.",
        },
        {
            "id": "E6_shadow_state",
            "title": "CQRS Shadow State (DuckDB)",
            "status": "experimental",
            "enabled": False,
            "runtime": False,
            "rfc": "RFC0040",
            "docs": "docs/horizons/E6_SHADOW_STATE.md",
            "note": "DuckDB read-only OLAP поверх EventBus; writes только в граф истины.",
        },
        {
            "id": "E7_lens_engine_bae",
            "title": "LensEngine + BAE",
            "status": "experimental",
            "enabled": False,
            "runtime": False,
            "rfc": "RFC0045, RFC0051",
            "docs": "docs/horizons/E7_LENS_ENGINE_BAE.md",
            "env_flag": "ENABLE_LENS_ENGINE",
            "note": "Детерминированные линзы для LLM_MODE=offline (RFC0044).",
        },
        {
            "id": "E3_hebbian_stdp",
            "title": "3-Factor Hebbian / STDP",
            "status": "experimental",
            "enabled": False,
            "runtime": False,
            "rfc": "—",
            "docs": "docs/horizons/E3_HEBBIAN_STDP.md",
            "note": "Δw = pre × post × reward; ядро для NeuroCore.",
        },
        {
            "id": "E4_virf_pattern",
            "title": "VIRF (System 1 ↔ System 2)",
            "status": "experimental",
            "enabled": False,
            "runtime": False,
            "rfc": "—",
            "docs": "docs/horizons/E4_VIRF_PATTERN.md",
            "note": "LLM draft + formal verifier + педагогический feedback.",
        },
        {
            "id": "E5_scallop_dpp",
            "title": "Scallop / DeepProbLog (L4)",
            "status": "experimental",
            "enabled": False,
            "runtime": False,
            "rfc": "—",
            "docs": "docs/horizons/E5_SCALLOP_DPP.md",
            "note": "Верифицируемое рассуждение вместо CoT.",
        },
    ]


def optional_runtime_layers(cfg: Any) -> dict[str, dict[str, Any]]:
    """Модули с кодом в V8.6, но выключены ENV (не research — Beta/optional)."""
    flags = {
        "L1_5_velum": ("ENABLE_VELUM", cfg.enable_velum),
        "L1_5_salience": ("ENABLE_SALIENCE", cfg.enable_salience),
        "L2_concept_emergence": ("ENABLE_CONCEPT_EMERGENCE", cfg.enable_concept_emergence),
        "L3_5a_etir": ("ENABLE_ETIR", cfg.enable_etir),
        "L3_5b_immutable_core": ("ENABLE_IMMUTABLE_CORE", cfg.enable_immutable_core),
        "L4_reasoning_bank": ("ENABLE_REASONING_BANK", cfg.enable_reasoning_bank),
        "L4_5_bundle": ("ENABLE_L45", cfg.enable_l45),
        "L5_5_predictive_fusion": ("ENABLE_PREDICTIVE_FUSION", cfg.enable_predictive_fusion),
        "decay_orchestrator": ("ENABLE_DECAY_ORCHESTRATOR", cfg.enable_decay_orchestrator),
        "L6_welfare_mvp": ("ENABLE_L6_WELFARE", cfg.enable_l6_welfare),
        "event_bus": ("ENABLE_EVENT_BUS", cfg.enable_event_bus),
    }
    out: dict[str, dict[str, Any]] = {}
    for key, (env_flag, on) in flags.items():
        out[key] = {
            "status": "on" if on else "available_off",
            "enabled": on,
            "runtime": True,
            "env_flag": env_flag,
            "category": "optional_runtime",
        }
    return out


def build_horizons_block(cfg: Any) -> dict[str, Any]:
    l6_mvp = cfg.enable_l6_welfare
    research = research_entries()
    # L6 MVP — отдельная строка: код есть, полный L6 — research
    research_with_l6_note = list(research)
    return {
        "summary": {
            "research_count": len(research),
            "experimental_count": len(experimental_entries()),
            "message": (
                "Horizons — исследования и будущие слои. "
                "Не включены в runtime, пока не активированы флаги или не реализованы."
            ),
        },
        "research": research_with_l6_note,
        "experimental": experimental_entries(),
        "optional_runtime": optional_runtime_layers(cfg),
        "L6_mvp": {
            "status": "mvp" if l6_mvp else "available_off",
            "enabled": l6_mvp,
            "runtime": True,
            "env_flag": "ENABLE_L6_WELFARE",
            "docs": "docs/horizons/L6_VALUES_WELFARE.md",
            "note": "WelfareMonitor + VolitionGate; полный RFC0069 — в research.L6_full_rfc0069.",
        },
        "docs_index": "docs/HORIZONS.md",
    }


__all__ = [
    "build_horizons_block",
    "experimental_entries",
    "optional_runtime_layers",
    "research_entries",
]
