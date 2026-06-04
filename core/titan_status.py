"""
Сводный статус компонентов Titan v7.5 → V8.6 (для GET /titan/status).
"""

from __future__ import annotations

from typing import Any

from core.feature_config import get_config


def build_titan_status() -> dict[str, Any]:
    cfg = get_config().app

    flags = {
        "output_faithfulness": cfg.enable_output_faithfulness,
        "memory_budget": cfg.enable_memory_budget,
        "circuit_breaker": cfg.enable_circuit_breaker,
        "response_guardian": cfg.enable_response_guardian,
        "actr_activation": cfg.enable_actr_activation,
    }
    any_enabled = any(flags.values())

    budget_block: dict[str, Any] = {"enabled": cfg.enable_memory_budget}
    if cfg.enable_memory_budget:
        from core.memory_budget import evaluate_budget

        st = evaluate_budget()
        budget_block.update(
            {
                "fact_count": st.fact_count,
                "limit": st.limit,
                "utilization": st.utilization,
                "action": st.action,
                "thresholds": {
                    "warn": cfg.memory_budget_fact_warn,
                    "gc": cfg.memory_budget_fact_gc,
                    "hard": cfg.memory_budget_fact_hard,
                },
            }
        )

    breakers_block: dict[str, Any] = {"enabled": cfg.enable_circuit_breaker}
    if cfg.enable_circuit_breaker:
        from core.circuit_breaker import get_circuit_breaker, list_circuit_breakers

        get_circuit_breaker("llm")
        breakers_block["circuits"] = list_circuit_breakers()

    actr_block: dict[str, Any] = {
        "enabled": cfg.enable_actr_activation,
        "decay_exponent": cfg.actr_decay_exponent,
        "retrieval_weight": cfg.actr_retrieval_weight,
    }
    if cfg.enable_actr_activation:
        from core.actr_activation import actr_stats

        actr_block["stats"] = actr_stats()

    return {
        "product": "VELANTRIM V8.6 Complex",
        "source": "Velantrim_v7.5_Titan.md (HYPERIA-2,6,7,8,3)",
        "any_enabled": any_enabled,
        "flags": flags,
        "memory_budget": budget_block,
        "circuit_breakers": breakers_block,
        "actr_activation": actr_block,
        "hints": {
            "enable_all": (
                "ENABLE_OUTPUT_FAITHFULNESS=1 ENABLE_MEMORY_BUDGET=1 "
                "ENABLE_CIRCUIT_BREAKER=1 ENABLE_RESPONSE_GUARDIAN=1 "
                "ENABLE_ACTR_ACTIVATION=1"
            ),
            "dev_profile": "config/exocortex-dev.env",
        },
    }


__all__ = ["build_titan_status"]
