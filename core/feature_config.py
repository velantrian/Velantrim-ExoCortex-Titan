"""
Конфигурация ExoCortex-слоёв (VELANTRIM V8.6 Complex).

Совместимость с API `get_config().app.*` из Graphiti_fractal.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache


def _flag(name: str, default: str = "0") -> bool:
    return (os.getenv(name, default) or "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def _float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default


@dataclass
class DatabaseSettings:
    storage_backend: str = "sqlite"
    sqlite_graph_path: str = "./data/exocortex_graph.db"


@dataclass
class AppSettings:
    # COMPUTE_PROFILE: lite|standard|heavy — единый рычаг железа (см. core/compute_profile.py).
    # Явный ENABLE_* всегда побеждает профиль. LLM_PROVIDER профилем не трогается.
    compute_profile: str = "lite"
    enable_edge_suggester: bool = False
    enable_xai: bool = False
    enable_analogy_hints: bool = False

    enable_truth_gate: bool = False
    # P2 (T1.4) — explicit truth_policy verdict on the read-path. Temporary scaffolding:
    # canon Definition-of-Done is "strong gates ON by default"; flip this default in a
    # later increment once the eval ruler validates behavior.
    enable_truth_policy: bool = False
    # Observer P0 — passive meta-monitor on the read-path (Essence Layer Completion).
    # Scaffolding toward on-by-default once calibrated.
    enable_observer: bool = False
    # Graph-expansion retrieval — when composing the Essence chain, pull in reliable
    # causal-graph neighbours of the retrieved facts so multi-hop reasoning emerges
    # (proven lever: edges + neighbour-expansion → causal chains). Additive, default OFF.
    enable_graph_expansion: bool = False
    # Task-type routing (L4 canon idea) — classify query intent (FACT/WHY/HOW/...) and
    # route reasoning: WHY/HOW/EXPLAIN/SOLVE/COMPARE → graph-expansion (chains), FACT →
    # direct answer. Additive, default OFF.
    enable_task_routing: bool = False
    # Compatibility/readout field for the mandatory Write Protocol Gate.
    # Explicit false is ignored by PolicyKernel and logged: a canonical
    # safety boundary is not a feature that a compute profile may disable.
    enable_write_gate: bool = True
    # Security tail — per-IP token-bucket rate limiting (default off). zero-dep stdlib.
    enable_rate_limit: bool = False
    rate_limit_capacity: int = 60
    rate_limit_refill_per_sec: float = 1.0
    # CognitiveDistance re-rank of retrieval (default off; measured via eval ruler).
    enable_cognitive_distance: bool = False
    # BudgetPlanner — adaptive retrieval k/mode by query complexity (default off).
    enable_budget_planner: bool = False
    # NetworkX Graph-Analysis Lab — read-only structural analytics over the causal graph
    # (centrality/communities/cycles/pagerank). Research/science mode; off by default.
    enable_graph_lab: bool = False
    truth_gate_mode: str = "BALANCED"
    default_fact_confidence: float = 0.8

    enable_velum: bool = False
    velum_use_fsrs_decay: bool = False
    velum_hint_min_weight: float = 0.15
    velum_hint_limit_per_entity: int = 3
    velum_hint_max_seeds: int = 5
    velum_persist: bool = False
    velum_decay_prune_below: float = 0.05   # FSRS-retention: синапс ниже этого прунится

    enable_concept_emergence: bool = False
    emergence_co_occur_min: int = 5
    emergence_cross_session_min: int = 3
    emergence_llm_name_min_confidence: float = 0.7   # мин. confidence для LLM-нейминга концепта
    emergence_promote_min_confidence: float = 0.7    # мин. confidence для промоушена прото-концепта
    knowledge_group_id: str = "velantrim_knowledge"  # Graphiti group_id для emergent-концептов
    enable_concept_promote: bool = False
    enable_salience: bool = False
    enable_concept_llm_naming: bool = False

    enable_decay_orchestrator: bool = False
    enable_predictive_fusion: bool = False

    # Salience-защита от FSRS-затухания (#26): узел с salience_weight >= порога НЕ тускнеет.
    # Отсутствие поля роняло DecayOrchestrator (AttributeError в salience_fsrs.protect_threshold).
    salience_fsrs_protect_threshold: float = 0.95

    enable_event_bus: bool = False
    enable_event_bus_background: bool = False
    enable_reasoning_bank: bool = False
    enable_causal_graph: bool = True
    causal_persist: bool = False

    enable_etir: bool = False
    etir_max_hops: int = 2
    etir_top_k: int = 10

    enable_immutable_core: bool = False

    enable_response_audit: bool = False
    enable_focus_engine: bool = False
    enable_memory_volition: bool = False
    enable_l45: bool = False

    enable_l6_welfare: bool = False
    enable_innenwelt: bool = False
    enable_mode_router: bool = False
    enable_umwelt_store: bool = False
    enable_telegram_ingest: bool = False
    enable_domain_tags: bool = True
    enable_cognitive_fact: bool = True
    enable_cognitive_store: bool = True
    enable_cognitive_runtime: bool = True
    enable_cross_domain: bool = False
    enable_cross_domain_causal: bool = True
    enable_cross_domain_llm_routing: bool = False
    enable_output_faithfulness: bool = False
    enable_memory_budget: bool = False
    enable_circuit_breaker: bool = False
    enable_response_guardian: bool = False
    enable_actr_activation: bool = False
    memory_budget_fact_hard: int = 100_000
    memory_budget_fact_gc: int = 85_000
    memory_budget_fact_warn: int = 80_000
    actr_decay_exponent: float = 0.5
    actr_retrieval_weight: float = 0.15
    welfare_window_seconds: int = 300
    welfare_max_volitions_per_window: int = 20
    welfare_error_rate_yellow: float = 0.25
    welfare_error_rate_red: float = 0.5
    welfare_distress_yellow: float = 0.45
    welfare_distress_red: float = 0.75
    welfare_goal_alignment_yellow: float = 0.25
    welfare_truth_fail_rate_yellow: float = 0.4

    @classmethod
    def from_env(cls) -> AppSettings:
        from core.compute_profile import get_compute_profile, resolve_flag

        a = cls()
        a.compute_profile = get_compute_profile()

        def flag(name: str, default: str = "0") -> bool:
            return resolve_flag(name, default=default, profile=a.compute_profile)

        a.enable_truth_gate = flag("ENABLE_TRUTH_GATE")
        a.enable_truth_policy = flag("ENABLE_TRUTH_POLICY")
        a.enable_observer = flag("ENABLE_OBSERVER")
        a.enable_graph_expansion = flag("ENABLE_GRAPH_EXPANSION")
        a.enable_task_routing = flag("ENABLE_TASK_ROUTING")
        a.enable_write_gate = flag("ENABLE_WRITE_GATE", "1")
        a.enable_graph_lab = flag("ENABLE_GRAPH_LAB")
        a.enable_rate_limit = flag("ENABLE_RATE_LIMIT")
        a.rate_limit_capacity = _int("RATE_LIMIT_CAPACITY", 60)
        a.rate_limit_refill_per_sec = _float("RATE_LIMIT_REFILL_PER_SEC", 1.0)
        a.enable_cognitive_distance = flag("ENABLE_COGNITIVE_DISTANCE")
        a.enable_budget_planner = flag("ENABLE_BUDGET_PLANNER")
        a.truth_gate_mode = os.getenv("TRUTH_GATE_MODE", "BALANCED")
        a.default_fact_confidence = _float("DEFAULT_FACT_CONFIDENCE", 0.8)

        a.enable_velum = flag("ENABLE_VELUM")
        a.velum_use_fsrs_decay = flag("VELUM_USE_FSRS_DECAY")
        a.velum_hint_min_weight = _float("VELUM_HINT_MIN_WEIGHT", 0.15)
        a.velum_hint_limit_per_entity = _int("VELUM_HINT_LIMIT", 3)
        a.velum_hint_max_seeds = _int("VELUM_HINT_MAX_SEEDS", 5)
        a.velum_persist = flag("VELUM_PERSIST")

        a.enable_concept_emergence = flag("ENABLE_CONCEPT_EMERGENCE")
        a.emergence_co_occur_min = _int("EMERGENCE_CO_OCCUR_MIN", 5)
        a.emergence_cross_session_min = _int("EMERGENCE_CROSS_SESSION_MIN", 3)
        a.emergence_llm_name_min_confidence = _float("EMERGENCE_LLM_NAME_MIN_CONFIDENCE", 0.7)
        a.emergence_promote_min_confidence = _float("EMERGENCE_PROMOTE_MIN_CONFIDENCE", 0.7)
        a.velum_decay_prune_below = _float("VELUM_DECAY_PRUNE_BELOW", 0.05)
        a.knowledge_group_id = os.getenv("KNOWLEDGE_GROUP_ID", "velantrim_knowledge")
        a.enable_concept_promote = flag("ENABLE_CONCEPT_PROMOTE")
        a.enable_salience = flag("ENABLE_SALIENCE")
        # Никогда не включается профилем — только явный ENV (local-first).
        a.enable_concept_llm_naming = _flag("ENABLE_CONCEPT_LLM_NAMING")

        a.enable_decay_orchestrator = flag("ENABLE_DECAY_ORCHESTRATOR")
        a.enable_predictive_fusion = flag("ENABLE_PREDICTIVE_FUSION")

        a.enable_event_bus = flag("ENABLE_EVENT_BUS")
        a.enable_event_bus_background = flag("ENABLE_EVENT_BUS_BACKGROUND")
        a.enable_reasoning_bank = flag("ENABLE_REASONING_BANK")
        a.enable_causal_graph = flag("ENABLE_CAUSAL_GRAPH", "1")
        a.causal_persist = flag("CAUSAL_PERSIST")

        a.enable_etir = flag("ENABLE_ETIR")
        a.etir_max_hops = _int("ETIR_MAX_HOPS", 2)
        a.etir_top_k = _int("ETIR_TOP_K", 10)

        a.enable_immutable_core = flag("ENABLE_IMMUTABLE_CORE")

        a.enable_l45 = flag("ENABLE_L45")
        a.enable_response_audit = flag("ENABLE_RESPONSE_AUDIT") or a.enable_l45
        a.enable_focus_engine = flag("ENABLE_FOCUS_ENGINE") or a.enable_l45
        a.enable_memory_volition = (
            flag("ENABLE_MEMORY_VOLITION") or a.enable_l45 or flag("ENABLE_L6_WELFARE")
        )

        a.enable_edge_suggester = flag("ENABLE_EDGE_SUGGESTER")
        a.enable_xai = flag("ENABLE_XAI")
        a.enable_analogy_hints = flag("ENABLE_ANALOGY_HINTS")

        a.enable_l6_welfare = flag("ENABLE_L6_WELFARE")
        a.enable_innenwelt = flag("ENABLE_INNENWELT", "1")
        a.enable_mode_router = flag("ENABLE_MODE_ROUTER", "1")
        a.enable_umwelt_store = flag("ENABLE_UMWELT_STORE", "1")
        a.enable_telegram_ingest = flag("ENABLE_TELEGRAM_INGEST", "0")
        a.enable_domain_tags = flag("ENABLE_DOMAIN_TAGS", "1")
        a.enable_cognitive_fact = flag("ENABLE_COGNITIVE_FACT", "1")
        a.enable_cognitive_store = flag("ENABLE_COGNITIVE_STORE", "1")
        a.enable_cognitive_runtime = flag("ENABLE_COGNITIVE_RUNTIME", "1")
        a.enable_cross_domain = flag("ENABLE_CROSS_DOMAIN", "0")
        a.enable_cross_domain_causal = flag("ENABLE_CROSS_DOMAIN_CAUSAL", "1")
        a.enable_cross_domain_llm_routing = _flag("ENABLE_CROSS_DOMAIN_LLM_ROUTING", "0")
        a.enable_output_faithfulness = flag("ENABLE_OUTPUT_FAITHFULNESS")
        a.enable_memory_budget = flag("ENABLE_MEMORY_BUDGET")
        a.enable_circuit_breaker = flag("ENABLE_CIRCUIT_BREAKER")
        a.enable_response_guardian = flag("ENABLE_RESPONSE_GUARDIAN")
        a.enable_actr_activation = flag("ENABLE_ACTR_ACTIVATION")
        a.memory_budget_fact_hard = _int("MEMORY_BUDGET_FACT_HARD", 100_000)
        a.memory_budget_fact_gc = _int("MEMORY_BUDGET_FACT_GC", 85_000)
        a.memory_budget_fact_warn = _int("MEMORY_BUDGET_FACT_WARN", 80_000)
        a.actr_decay_exponent = _float("ACTR_DECAY_EXPONENT", 0.5)
        a.actr_retrieval_weight = _float("ACTR_RETRIEVAL_WEIGHT", 0.15)
        a.welfare_window_seconds = _int("WELFARE_WINDOW_SECONDS", 300)
        a.welfare_max_volitions_per_window = _int("WELFARE_MAX_VOLITIONS_PER_WINDOW", 20)
        a.welfare_error_rate_yellow = _float("WELFARE_ERROR_RATE_YELLOW", 0.25)
        a.welfare_error_rate_red = _float("WELFARE_ERROR_RATE_RED", 0.5)
        a.welfare_distress_yellow = _float("WELFARE_DISTRESS_YELLOW", 0.45)
        a.welfare_distress_red = _float("WELFARE_DISTRESS_RED", 0.75)
        a.welfare_goal_alignment_yellow = _float("WELFARE_GOAL_ALIGNMENT_YELLOW", 0.25)
        a.welfare_truth_fail_rate_yellow = _float("WELFARE_TRUTH_FAIL_RATE_YELLOW", 0.4)

        return a


@dataclass
class FeatureConfig:
    app: AppSettings = field(default_factory=AppSettings)
    db: DatabaseSettings = field(default_factory=DatabaseSettings)

    @classmethod
    def from_env(cls) -> FeatureConfig:
        # SECURITY/CORRECTNESS (confirmed issue: canonical DB path): this used
        # to default to its own literal ("./data/exocortex_graph.db") via
        # SQLITE_GRAPH_PATH, completely independent of core.memory.SQLITE_PATH
        # (VELANTRIM_DB_PATH). core.app.get_app()'s singleton builds app.store
        # from this value — so with two unrelated defaults, app.store and
        # core.memory._GLOBAL_STORE (and get_store()'s fallback) could silently
        # point at two different SQLite files. Default now derives from the
        # SAME canonical path core.memory.SQLITE_PATH resolves to; SQLITE_GRAPH_PATH
        # remains available as an explicit opt-in override for a genuinely
        # separate graph DB (e.g. isolated tests constructing their own
        # VelantrimApp with a custom FeatureConfig).
        from core.memory import SQLITE_PATH

        db = DatabaseSettings(
            storage_backend=(os.getenv("STORAGE_BACKEND", "sqlite") or "sqlite").strip().lower(),
            sqlite_graph_path=os.getenv("SQLITE_GRAPH_PATH", SQLITE_PATH),
        )
        return cls(app=AppSettings.from_env(), db=db)


@lru_cache(maxsize=1)
def get_config() -> FeatureConfig:
    return FeatureConfig.from_env()


def clear_config_cache() -> None:
    get_config.cache_clear()


__all__ = ["AppSettings", "DatabaseSettings", "FeatureConfig", "clear_config_cache", "get_config"]
