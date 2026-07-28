"""
MemoryBudgetPlanner — лимит роста фактов (Titan HYPERIA-7, адаптация под SQLite L1).

По умолчанию считает строки в `facts`, не узлы Neo4j.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from core.feature_config import get_config

logger = logging.getLogger(__name__)


class MemoryBudgetExceededError(Exception):
    """Запись заблокирована: достигнут жёсткий лимит фактов."""


@dataclass
class BudgetStatus:
    fact_count: int
    limit: int
    utilization: float
    action: str

    def to_dict(self) -> dict:
        return {
            "fact_count": self.fact_count,
            "limit": self.limit,
            "utilization": round(self.utilization, 4),
            "action": self.action,
        }


def is_memory_budget_enabled() -> bool:
    return get_config().app.enable_memory_budget


def count_facts() -> int:
    from core.memory import _GLOBAL_STORE

    with _GLOBAL_STORE._db() as conn:
        row = conn.execute("SELECT COUNT(*) AS c FROM facts").fetchone()
        return int(row["c"]) if row else 0


def check_before_write(*, is_new_insert: bool = True) -> BudgetStatus:
    """
    Проверка перед INSERT нового факта.
    Raises MemoryBudgetExceededError при hard limit.
    """
    get_config().app
    status = evaluate_budget()
    if not is_memory_budget_enabled():
        return status
    if is_new_insert and status.action == "hard_limit":
        raise MemoryBudgetExceededError(
            f"Лимит фактов {status.fact_count}/{status.limit} — запись заблокирована"
        )
    return status


def evaluate_budget(*, quiet: bool = False) -> BudgetStatus:
    """Посчитать текущее состояние бюджета фактов.

    quiet=True подавляет только пороговое логирование, не меняя возвращаемое
    значение. Нужно для поллеров: пороговые WARNING/CRITICAL написаны для
    write-пути (один раз на запись), а MetaSupervisor опрашивает бюджет каждые
    10 c — без этого постоянно полный стор даёт 6 одинаковых сообщений
    critical-уровня в минуту и заглушает реальные алерты.
    """
    cfg = get_config().app
    hard = cfg.memory_budget_fact_hard
    gc_at = cfg.memory_budget_fact_gc
    warn_at = cfg.memory_budget_fact_warn
    n = count_facts()
    utilization = n / hard if hard > 0 else 0.0

    if n >= hard:
        if not quiet:
            logger.critical(
                "MemoryBudget: HARD LIMIT %d/%d (%.1f%%)",
                n,
                hard,
                utilization * 100,
            )
        action = "hard_limit"
    elif n >= gc_at:
        if not quiet:
            logger.warning(
                "MemoryBudget: GC threshold %d/%d (%.1f%%)",
                n,
                hard,
                utilization * 100,
            )
        action = "gc_triggered"
    elif n >= warn_at:
        if not quiet:
            logger.warning(
                "MemoryBudget: WARNING %d/%d (%.1f%%)",
                n,
                hard,
                utilization * 100,
            )
        action = "warn"
    else:
        action = "ok"

    return BudgetStatus(fact_count=n, limit=hard, utilization=utilization, action=action)


__all__ = [
    "BudgetStatus",
    "MemoryBudgetExceededError",
    "check_before_write",
    "count_facts",
    "evaluate_budget",
    "is_memory_budget_enabled",
]
