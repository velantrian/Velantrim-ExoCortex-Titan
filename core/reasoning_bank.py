"""
ReasoningBank L4 — паттерны рассуждения + Thompson Sampling (MVP).

In-memory strategies. Опционально обучается из EventBus (TRUTH_GATE_VERDICT).
Не пишет в L3 граф напрямую — только read/write через feature-flag hooks.
"""

from __future__ import annotations

import logging
import random
import time as _time_module
import uuid
from collections import deque, OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Deque, Dict, List, Optional

logger = logging.getLogger(__name__)


class Outcome(Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"


@dataclass
class Experience:
    task_description: str
    action_taken: str
    outcome: Outcome
    reasoning: str
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    context: Dict = field(default_factory=dict)
    error_message: Optional[str] = None


@dataclass
class Strategy:
    """Стратегия рассуждения с байесовским счётчиком."""

    description: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    applicable_contexts: List[str] = field(default_factory=list)
    success_count: int = 0
    failure_count: int = 0
    confidence: float = 0.5
    failure_penalty: float = 0.1
    success_boost: float = 0.05

    @property
    def success_rate(self) -> float:
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 0.0

    def thompson_sample(self) -> float:
        """Beta(success+1, failure+1) через random.betavariate."""
        a = self.success_count + 1
        b = self.failure_count + 1
        return random.betavariate(a, b)

    def update_confidence(self, outcome: Outcome) -> None:
        if outcome == Outcome.SUCCESS:
            self.success_count += 1
            self.confidence = min(1.0, self.confidence + self.success_boost)
        elif outcome == Outcome.FAILURE:
            self.failure_count += 1
            self.confidence = max(0.0, self.confidence - self.failure_penalty)
        if self.failure_count > 5:
            self.failure_penalty = min(0.3, self.failure_penalty * 1.2)


class ReasoningBank:
    """In-memory банк стратегий (RFC L4 MVP)."""

    def __init__(self, *, max_experiences: int = 1000):
        self.experience_buffer: Deque[Experience] = deque(maxlen=max_experiences)
        self.strategies: Dict[str, Strategy] = OrderedDict()  # V8.7 HYPERIA: LRU order
        self._strategy_access: Dict[str, float] = {}  # V8.7: timestamp последнего использования
        self._STRATEGIES_MAX = 500  # V8.7 HYPERIA V5.5: защита от OOM при долгом аптайме
        self._seed_default_strategies()

    def _seed_default_strategies(self) -> None:
        defaults = [
            ("hybrid_retrieval", "Гибридный поиск entity+episode", ["recall"]),
            ("causal_explain", "Объяснение через causal_chain", ["explain"]),
            ("velum_expand", "Расширение контекста через Velum", ["context"]),
            ("truth_gate_strict", "Строгий TruthGate BALANCED", ["ingest"]),
        ]
        for sid, desc, ctx in defaults:
            self.strategies[sid] = Strategy(
                id=sid,
                description=desc,
                applicable_contexts=ctx,
            )

    async def log_experience(
        self,
        task: str,
        action: str,
        outcome: Outcome,
        reasoning: str,
        *,
        context: Optional[Dict] = None,
        error: Optional[str] = None,
    ) -> None:
        exp = Experience(
            task_description=task,
            action_taken=action,
            outcome=outcome,
            reasoning=reasoning,
            context=context or {},
            error_message=error,
        )
        self.experience_buffer.append(exp)

        for strategy in self.strategies.values():
            if any(c in (task or "").lower() for c in strategy.applicable_contexts):
                strategy.update_confidence(outcome)

        if len(self.experience_buffer) >= 10:
            await self.distill_strategies()

    async def distill_strategies(self) -> int:
        """
        Упрощённая дистилляция: поднять confidence лучших контекстов.
        Без LLM (0 токенов).
        """
        by_ctx: Dict[str, List[Experience]] = {}
        for exp in self.experience_buffer:
            key = exp.action_taken or "general"
            by_ctx.setdefault(key, []).append(exp)

        created = 0
        for action, exps in by_ctx.items():
            if len(exps) < 3:
                continue
            successes = sum(1 for e in exps if e.outcome == Outcome.SUCCESS)
            rate = successes / len(exps)
            if rate >= 0.7 and action not in self.strategies:
                self.strategies[action] = Strategy(
                    id=action,
                    description=f"Auto: {action} (success {rate:.0%})",
                    applicable_contexts=[action],
                    confidence=rate,
                )
                created += 1
        return created

    def select_strategy(
        self,
        context: str = "",
        *,
        exploration: bool = True,
    ) -> Optional[Strategy]:
        """
        Thompson Sampling: выбор стратегии по контексту.
        """
        candidates = [
            s
            for s in self.strategies.values()
            if not context
            or not s.applicable_contexts
            or any(c in context.lower() for c in s.applicable_contexts)
        ]
        if not candidates:
            candidates = list(self.strategies.values())
        if not candidates:
            return None

        if exploration:
            best = max(candidates, key=lambda s: s.thompson_sample())
        else:
            best = max(candidates, key=lambda s: s.confidence)

        # V8.7 HYPERIA V5.5: LRU tracking + eviction при переполнении
        self._strategy_access[best.id] = _time_module.time()
        self._evict_if_needed()

        return best

    def _evict_if_needed(self) -> None:
        """V8.7 HYPERIA V5.5: LRU eviction — защита от OOM при долгом аптайме."""
        if len(self.strategies) <= self._STRATEGIES_MAX:
            return
        # Удалить стратегию, к которой дольше всего не обращались
        oldest_id = min(
            self._strategy_access,
            key=lambda sid: self._strategy_access.get(sid, 0.0),
            default=None,
        )
        if oldest_id and oldest_id in self.strategies:
            del self.strategies[oldest_id]
            self._strategy_access.pop(oldest_id, None)
            logger.info("ReasoningBank: LRU evicted strategy '%s' (%d/%d)", oldest_id, len(self.strategies), self._STRATEGIES_MAX)

    def format_context_section(self, context: str = "") -> str:
        """Секция для LLM context (read-only подсказка)."""
        strategy = self.select_strategy(context)
        if not strategy:
            return ""
        lines = [
            "## ReasoningBank (L4):",
            f"- Рекомендуемая стратегия: **{strategy.description}**",
            f"- Уверенность: {strategy.confidence:.2f} "
            f"(успехов {strategy.success_count}, провалов {strategy.failure_count})",
        ]
        return "\n".join(lines)


_bank_singleton: Optional[ReasoningBank] = None


def get_reasoning_bank() -> ReasoningBank:
    global _bank_singleton
    if _bank_singleton is None:
        _bank_singleton = ReasoningBank()
    return _bank_singleton


def reset_reasoning_bank() -> None:
    global _bank_singleton
    _bank_singleton = None


def is_reasoning_bank_enabled() -> bool:
    from core.feature_config import get_config

    return bool(get_config().app.enable_reasoning_bank)


async def log_reasoning_experience(
    task: str,
    action: str,
    outcome: Outcome,
    reasoning: str,
    **kwargs,
) -> None:
    if not is_reasoning_bank_enabled():
        return
    await get_reasoning_bank().log_experience(
        task, action, outcome, reasoning, **kwargs
    )


__all__ = [
    "Experience",
    "Outcome",
    "ReasoningBank",
    "Strategy",
    "get_reasoning_bank",
    "is_reasoning_bank_enabled",
    "log_reasoning_experience",
    "reset_reasoning_bank",
]
