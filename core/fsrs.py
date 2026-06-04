"""
FSRS — Free Spaced Repetition Scheduler.

Sprint 2 / T1. Power-law формула retention (RFC0017), заменяющая
экспоненциальный decay Эббингауза:

    R(t, S) = (1 + 19/81 * t / S)^(-0.5)

где:
  - R: вероятность recall (∈ [0, 1])
  - t: время с последнего review (дни)
  - S: stability факта (дни) — текущая «прочность» памяти

Принципы:
  - Backend-agnostic: чистая математика + datetime, никаких графов.
  - Идемпотентность: повторный вызов retention(t, S) даёт тот же результат.
  - Безопасность: edge cases (t<0, S<=0, NaN, Inf) обрабатываются явно.
  - Конфигурируемость: все коэффициенты через FSRSParams (frozen dataclass).

Применение:
  - Decay edge weights в Velum (Sprint 2 T2): weight *= retention(t, S).
  - Scheduler для review: time_to_threshold(S, R=0.9) → когда повторить.
  - ESM Deprecated promotion: при R < 0.2 факт можно перевести в Deprecated.

Связь с другими модулями:
  - core/velum.py    — использует decay_edge_weight() для синапсов.
  - scripts/...      — периодический decay job (T5).
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime

# ─── Параметры FSRS ───────────────────────────────────────────────────────────


@dataclass(frozen=True)
class FSRSParams:
    """Параметры FSRS power-law формулы (RFC0017)."""

    factor: float = 19.0 / 81.0      # ≈ 0.2346 — каноничная константа FSRS
    exponent: float = -0.5            # power-law показатель

    # Правила обновления stability после review:
    success_stability_multiplier: float = 1.5
    failure_stability_multiplier: float = 0.5

    # Жёсткие ограничения stability (защита от взрыва/обнуления):
    min_stability_days: float = 0.1
    max_stability_days: float = 36_500.0   # ≈ 100 лет

    # Минимально допустимая retention (защита от деления на ноль).
    min_retention: float = 0.0
    max_retention: float = 1.0


_DEFAULT_PARAMS = FSRSParams()


# ─── Базовая формула ──────────────────────────────────────────────────────────


def retention(
    t_days: float,
    stability: float,
    params: FSRSParams = _DEFAULT_PARAMS,
) -> float:
    """
    Вероятность recall через t_days дней после последнего review.

    Свойства:
      - retention(0, S) = 1.0 для любого S > 0
      - retention(t, S) → 0  при t → ∞
      - retention монотонно убывает по t
      - retention монотонно возрастает по S (более стабильный факт помнится дольше)

    Edge cases:
      - t < 0           → traktovat' как 0 (возвращает 1.0)
      - stability <= 0  → возвращает 0.0 (факт уже забыт)
      - NaN / Inf       → возвращает 0.0 (fail-soft)
    """
    if not math.isfinite(t_days) or not math.isfinite(stability):
        return params.min_retention
    if t_days <= 0.0:
        return params.max_retention
    if stability <= 0.0:
        return params.min_retention

    ratio = params.factor * t_days / stability
    value = (1.0 + ratio) ** params.exponent

    if not math.isfinite(value):
        return params.min_retention
    # Зажимаем в [min_retention, max_retention] для безопасности.
    return max(params.min_retention, min(params.max_retention, value))


def time_to_threshold(
    stability: float,
    threshold: float,
    params: FSRSParams = _DEFAULT_PARAMS,
) -> float | None:
    """
    Когда retention упадёт до threshold (в днях) при заданной stability.

    Решение уравнения:
        threshold = (1 + factor * t / S)^(-0.5)
        → t = (threshold^(-2) - 1) * S / factor

    Возвращает:
      - float (дни)        — корректное время
      - None               — если threshold >= 1.0 (never) или некорректный input
    """
    if not math.isfinite(stability) or stability <= 0.0:
        return None
    if not math.isfinite(threshold):
        return None
    if threshold >= params.max_retention:
        return None  # retention никогда не дойдёт до 1.0 для t > 0
    if threshold <= 0.0:
        return math.inf  # стремится к ∞

    try:
        t = (threshold ** (-2.0) - 1.0) * stability / params.factor
    except (OverflowError, ZeroDivisionError, ValueError):
        return None
    if not math.isfinite(t) or t < 0.0:
        return None
    return t


def decay_edge_weight(
    weight: float,
    t_days: float,
    stability: float,
    params: FSRSParams = _DEFAULT_PARAMS,
) -> float:
    """
    Применить retention к synapse weight (для Velum L1.5).

        decayed = weight * retention(t, S)

    Зажимается в [0, |weight|]. Знак weight сохраняется.
    """
    if not math.isfinite(weight):
        return 0.0
    r = retention(t_days, stability, params)
    decayed = weight * r
    if not math.isfinite(decayed):
        return 0.0
    return decayed


# ─── Heterogeneous decay (deep-research: "Not All Memories Age the Same") ──────
# Different facts should age at different rates by volatility, not a single TTL.
# stable facts (math, definitions) keep memory longer; volatile facts (prices,
# news) decay fast. Implemented as a multiplier on stability (higher S = slower
# decay via retention()). Default class "medium" → ×1.0 ⇒ identical to current math.

VOLATILITY_MULTIPLIERS: dict[str, float] = {
    "stable":   3.0,   # axioms, definitions — age slowly
    "medium":   1.0,   # default — unchanged behavior
    "volatile": 0.33,  # prices, news, status — age fast
}


def volatility_stability(base_stability: float, volatility_class: str = "medium") -> float:
    """Scale base FSRS stability by a fact's volatility class. Never raises.

    medium → returns base unchanged (backward-compatible). Unknown class → medium.
    """
    mult = VOLATILITY_MULTIPLIERS.get((volatility_class or "medium").lower(), 1.0)
    s = base_stability * mult
    return s if math.isfinite(s) and s > 0 else base_stability


def decay_edge_weight_v(
    weight: float,
    t_days: float,
    stability: float,
    volatility_class: str = "medium",
    params: FSRSParams = _DEFAULT_PARAMS,
) -> float:
    """Volatility-aware variant of decay_edge_weight. With class='medium' it is
    EXACTLY decay_edge_weight(weight, t_days, stability) (backward-compatible)."""
    return decay_edge_weight(
        weight, t_days, volatility_stability(stability, volatility_class), params
    )


# ─── Обновление stability после review ───────────────────────────────────────


def next_stability(
    prev_stability: float,
    success: bool,
    params: FSRSParams = _DEFAULT_PARAMS,
) -> float:
    """
    Обновить stability после события recall.

    Упрощённое правило (RFC0017 MVP):
      - success → S' = S * success_multiplier
      - failure → S' = S * failure_multiplier
      - Зажимается в [min_stability_days, max_stability_days]

    Полная формула FSRS зависит от difficulty/elapsed/retention; в Sprint 2
    оставляем простой множитель. Более точная модель — Sprint 3+.
    """
    if not math.isfinite(prev_stability) or prev_stability <= 0:
        prev_stability = params.min_stability_days

    multiplier = (
        params.success_stability_multiplier
        if success
        else params.failure_stability_multiplier
    )
    new_S = prev_stability * multiplier
    return max(params.min_stability_days, min(params.max_stability_days, new_S))


# ─── Состояние FSRS на одной сущности ────────────────────────────────────────


@dataclass
class FSRSState:
    """Состояние FSRS для одной memory-сущности (fact, edge, entity)."""

    stability: float                                  # дни
    last_review: datetime
    review_count: int = 0
    success_count: int = 0

    def __post_init__(self) -> None:
        # Приводим к UTC, если timezone не указана.
        if self.last_review.tzinfo is None:
            self.last_review = self.last_review.replace(tzinfo=UTC)

    def days_since(self, now: datetime | None = None) -> float:
        """Сколько дней прошло с последнего review."""
        if now is None:
            now = datetime.now(UTC)
        if now.tzinfo is None:
            now = now.replace(tzinfo=UTC)
        delta = (now - self.last_review).total_seconds() / 86_400.0
        return max(0.0, delta)

    def current_retention(
        self,
        now: datetime | None = None,
        params: FSRSParams = _DEFAULT_PARAMS,
    ) -> float:
        """R сейчас."""
        return retention(self.days_since(now), self.stability, params)

    def review(
        self,
        success: bool,
        now: datetime | None = None,
        params: FSRSParams = _DEFAULT_PARAMS,
    ) -> FSRSState:
        """
        Регистрирует событие recall, возвращает НОВЫЙ FSRSState.
        Immutable-стиль: не мутирует self.
        """
        if now is None:
            now = datetime.now(UTC)
        if now.tzinfo is None:
            now = now.replace(tzinfo=UTC)

        new_stability = next_stability(self.stability, success, params)
        return FSRSState(
            stability=new_stability,
            last_review=now,
            review_count=self.review_count + 1,
            success_count=self.success_count + (1 if success else 0),
        )


# ─── Batch helpers ────────────────────────────────────────────────────────────


def apply_decay_batch(
    rows: Iterable[tuple[float, float, float]],
    params: FSRSParams = _DEFAULT_PARAMS,
) -> list[float]:
    """
    Применить decay к набору (weight, t_days, stability).

    Удобно для batch-скрипта (Sprint 2 T5): получает данные из Cypher
    и возвращает обновлённые веса.
    """
    return [decay_edge_weight(w, t, s, params) for (w, t, s) in rows]


__all__ = [
    "FSRSParams",
    "FSRSState",
    "retention",
    "next_stability",
    "time_to_threshold",
    "decay_edge_weight",
    "decay_edge_weight_v",
    "volatility_stability",
    "VOLATILITY_MULTIPLIERS",
    "apply_decay_batch",
]
