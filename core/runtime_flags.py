"""
Флаги runtime (Velantrim V8.6 Complex).

Делегирует в core.feature_config — единый источник ENV.
"""

from __future__ import annotations

from core.feature_config import get_config


def env_flag(name: str, default: str = "0") -> bool:
    """Обратная совместимость: читает ENV напрямую."""
    import os

    raw = (os.getenv(name, default) or "").strip().lower()
    return raw in ("1", "true", "yes", "on")


def is_event_bus_enabled() -> bool:
    return get_config().app.enable_event_bus


def is_truth_policy_enabled() -> bool:
    return get_config().app.enable_truth_policy


def is_observer_enabled() -> bool:
    return get_config().app.enable_observer


def is_graph_lab_enabled() -> bool:
    return get_config().app.enable_graph_lab


def is_rate_limit_enabled() -> bool:
    return get_config().app.enable_rate_limit


def is_cognitive_distance_enabled() -> bool:
    return get_config().app.enable_cognitive_distance


def is_budget_planner_enabled() -> bool:
    return get_config().app.enable_budget_planner


def is_embedding_projection_contract_enabled() -> bool:
    return get_config().app.enable_embedding_projection_contract


def is_l6_welfare_enabled() -> bool:
    return get_config().app.enable_l6_welfare


def is_innenwelt_enabled() -> bool:
    return get_config().app.enable_innenwelt


def is_mode_router_enabled() -> bool:
    return get_config().app.enable_mode_router


def is_umwelt_store_enabled() -> bool:
    return get_config().app.enable_umwelt_store


def is_memory_volition_enabled() -> bool:
    return get_config().app.enable_memory_volition


def use_event_bus_background() -> bool:
    cfg = get_config().app
    return cfg.enable_event_bus and cfg.enable_event_bus_background


class WelfareSettings:
    """Пороги L6 из feature_config."""

    @property
    def window_seconds(self) -> int:
        return get_config().app.welfare_window_seconds

    @property
    def max_volitions_per_window(self) -> int:
        return get_config().app.welfare_max_volitions_per_window

    @property
    def error_rate_yellow(self) -> float:
        return get_config().app.welfare_error_rate_yellow

    @property
    def error_rate_red(self) -> float:
        return get_config().app.welfare_error_rate_red

    @property
    def distress_yellow(self) -> float:
        return get_config().app.welfare_distress_yellow

    @property
    def distress_red(self) -> float:
        return get_config().app.welfare_distress_red

    @property
    def goal_alignment_yellow(self) -> float:
        return get_config().app.welfare_goal_alignment_yellow

    @property
    def truth_fail_rate_yellow(self) -> float:
        return get_config().app.welfare_truth_fail_rate_yellow

    # Алиасы для welfare_monitor (совместимость с AppSettings)
    @property
    def welfare_window_seconds(self) -> int:
        return self.window_seconds

    @property
    def welfare_max_volitions_per_window(self) -> int:
        return self.max_volitions_per_window

    @property
    def welfare_error_rate_yellow(self) -> float:
        return self.error_rate_yellow

    @property
    def welfare_error_rate_red(self) -> float:
        return self.error_rate_red

    @property
    def welfare_distress_yellow(self) -> float:
        return self.distress_yellow

    @property
    def welfare_distress_red(self) -> float:
        return self.distress_red

    @property
    def welfare_goal_alignment_yellow(self) -> float:
        return self.goal_alignment_yellow

    @property
    def welfare_truth_fail_rate_yellow(self) -> float:
        return self.truth_fail_rate_yellow


_welfare_settings = WelfareSettings()


def get_welfare_settings() -> WelfareSettings:
    return _welfare_settings


__all__ = [
    "WelfareSettings",
    "env_flag",
    "get_welfare_settings",
    "is_event_bus_enabled",
    "is_l6_welfare_enabled",
    "is_memory_volition_enabled",
    "is_budget_planner_enabled",
    "is_cognitive_distance_enabled",
    "is_embedding_projection_contract_enabled",
    "is_graph_lab_enabled",
    "is_observer_enabled",
    "is_rate_limit_enabled",
    "is_truth_policy_enabled",
    "use_event_bus_background",
]
