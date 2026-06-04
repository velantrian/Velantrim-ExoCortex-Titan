"""
Статус слоёв и Horizons (Velantrim V8.6 Complex).
"""

from __future__ import annotations

from typing import Any

from core.feature_config import get_config
from core.horizons_catalog import build_horizons_block


def build_layers_status() -> dict[str, Any]:
    cfg = get_config().app
    from core.graphiti_adapter import is_graphiti_backend
    return {
        "product": "VELANTRIM V8.6 Complex",
        "legend": {
            "on": "включено в runtime",
            "available_off": "код есть, выключено ENV",
            "research": "только спека/docs, нет runtime-модуля",
            "experimental": "частичная реализация, не production",
        },
        "layers": {
            "L0_raw_memory": {"status": "on", "enabled": True},
            "L1_esm_truth_gate": {"status": "on", "enabled": True},
            "L1_5_velum": {
                "status": "on" if cfg.enable_velum else "available_off",
                "enabled": cfg.enable_velum,
            },
            "L1_5_salience": {
                "status": "on" if cfg.enable_salience else "available_off",
                "enabled": cfg.enable_salience,
            },
            "L2_concept_emergence": {
                "status": "on" if cfg.enable_concept_emergence else "available_off",
                "enabled": cfg.enable_concept_emergence,
            },
            "L2_5_staging": {
                "status": "research",
                "enabled": False,
                "docs": "docs/horizons/L2_5_STAGING.md",
            },
            "L3_sqlite_graph": {"status": "on", "enabled": True},
            "L3_5a_etir": {
                "status": "on" if cfg.enable_etir else "available_off",
                "enabled": cfg.enable_etir,
            },
            "L3_5b_immutable_core": {
                "status": "on" if cfg.enable_immutable_core else "available_off",
                "enabled": cfg.enable_immutable_core,
            },
            "L4_reasoning_bank": {
                "status": "on" if cfg.enable_reasoning_bank else "available_off",
                "enabled": cfg.enable_reasoning_bank,
            },
            "L4_causal_graph": {
                "status": "on" if cfg.enable_causal_graph else "available_off",
                "enabled": cfg.enable_causal_graph,
            },
            "L4_5_response_audit": {
                "status": "on" if cfg.enable_response_audit else "available_off",
                "enabled": cfg.enable_response_audit,
            },
            "L4_5_focus_engine": {
                "status": "on" if cfg.enable_focus_engine else "available_off",
                "enabled": cfg.enable_focus_engine,
            },
            "L4_5_memory_volition": {
                "status": "on" if cfg.enable_memory_volition else "available_off",
                "enabled": cfg.enable_memory_volition,
            },
            "L5_5_predictive_fusion": {
                "status": "on" if cfg.enable_predictive_fusion else "available_off",
                "enabled": cfg.enable_predictive_fusion,
            },
            "decay_orchestrator": {
                "status": "on" if cfg.enable_decay_orchestrator else "available_off",
                "enabled": cfg.enable_decay_orchestrator,
            },
            "L6_welfare_mvp": {
                "status": "on" if cfg.enable_l6_welfare else "available_off",
                "enabled": cfg.enable_l6_welfare,
                "note": "полный RFC0069 — horizons.research.L6_full_rfc0069",
            },
            "Innenwelt_mvp": {
                "status": "on" if cfg.enable_innenwelt else "available_off",
                "enabled": cfg.enable_innenwelt,
                "note": "goals, gaps, somatic_marker — docs/ORGANIC_MEMORY_AND_WELTS.ru.md",
            },
            "ModeRouter_mvp": {
                "status": "on" if cfg.enable_mode_router else "available_off",
                "enabled": cfg.enable_mode_router,
                "note": "PERSONAL | VELANTRIM | UMWELT — core/router/",
            },
            "Umwelt_store_mvp": {
                "status": "on" if cfg.enable_umwelt_store else "available_off",
                "enabled": cfg.enable_umwelt_store,
                "note": "layer 99 perceptions — docs/seed/umwelt_mvp_seed.json",
            },
            "telegram_l0_ingest": {
                "status": "on" if cfg.enable_telegram_ingest else "available_off",
                "enabled": cfg.enable_telegram_ingest,
                "note": "POST /telegram/webhook, python -m app.telegram_bot",
            },
            "domain_tags": {
                "status": "on" if cfg.enable_domain_tags else "available_off",
                "enabled": cfg.enable_domain_tags,
                "note": "metadata.domain — science|engineering|...",
            },
            "cognitive_fact_v91": {
                "status": "on" if cfg.enable_cognitive_fact else "available_off",
                "enabled": cfg.enable_cognitive_fact,
                "note": "core/cognitive_fact.py — маппер dict↔CognitiveFact",
            },
            "cognitive_store_v92": {
                "status": "on" if cfg.enable_cognitive_store else "available_off",
                "enabled": cfg.enable_cognitive_store,
                "note": "core/cognitive_store.py — единый save/get/list",
            },
            "relations_preview_v97": {
                "status": "on"
                if cfg.enable_cognitive_fact and cfg.enable_causal_graph
                else "available_off",
                "enabled": cfg.enable_cognitive_fact and cfg.enable_causal_graph,
                "note": "GET /facts/{id}/relations, include_relations в CognitiveFact",
            },
            "graphiti_adapter_25": {
                "status": "on"
                if is_graphiti_backend()
                else "available_off",
                "enabled": is_graphiti_backend(),
                "note": "POST /causal/reload-from-graph — Neo4j→CausalGraph",
            },
            "cognitive_runtime_v10": {
                "status": "on" if cfg.enable_cognitive_runtime else "available_off",
                "enabled": cfg.enable_cognitive_runtime,
                "note": "GET /runtime/status — store + fact_* → retriever dirty",
            },
            "poly_welt_registry": {
                "status": "on" if cfg.enable_umwelt_store else "available_off",
                "enabled": cfg.enable_umwelt_store,
                "note": "GET /umwelt/agents — 6 перцепторов",
            },
            "cross_domain_v3": {
                "status": "on" if cfg.enable_cross_domain else "available_off",
                "enabled": cfg.enable_cross_domain,
                "note": "bridges + smart route + causal edges + LLM routing",
                "causal_edges": cfg.enable_cross_domain_causal,
                "llm_routing": cfg.enable_cross_domain_llm_routing,
            },
            "event_bus": {
                "status": "on" if cfg.enable_event_bus else "available_off",
                "enabled": cfg.enable_event_bus,
            },
            "sleep_time_worker": {"status": "on", "enabled": True},
            "titan_output_faithfulness": {
                "status": "on" if cfg.enable_output_faithfulness else "available_off",
                "enabled": cfg.enable_output_faithfulness,
                "note": "F6.5 extractive — Titan HYPERIA-6",
            },
            "titan_memory_budget": {
                "status": "on" if cfg.enable_memory_budget else "available_off",
                "enabled": cfg.enable_memory_budget,
                "note": f"facts limit {cfg.memory_budget_fact_hard}",
            },
            "titan_circuit_breaker": {
                "status": "on" if cfg.enable_circuit_breaker else "available_off",
                "enabled": cfg.enable_circuit_breaker,
                "note": "LLM / Neo4j cascading failures",
            },
            "titan_response_guardian": {
                "status": "on" if cfg.enable_response_guardian else "available_off",
                "enabled": cfg.enable_response_guardian,
                "note": "post-LLM quality gate — Titan HYPERIA-2",
            },
            "titan_actr_activation": {
                "status": "on" if cfg.enable_actr_activation else "available_off",
                "enabled": cfg.enable_actr_activation,
                "note": "retrieval boost B=ln(Σt^-0.5)",
            },
        },
        "horizons": build_horizons_block(cfg),
        "docs": {
            "horizons_index": "docs/HORIZONS.md",
            "layers_map": "docs/LAYERS_AND_HORIZONS.ru.md",
        },
    }


__all__ = ["build_layers_status"]
