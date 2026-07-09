"""
🔄 core/reconsolidation.py — Reconsolidation Engine (V8.7 Titan)

Реализует принцип «каждое воспоминание переосмысливается при активации».
Как в мозге: когда ты вспоминаешь событие — оно СНОВА становится пластичным.
Новый контекст добавляется. Эмоциональная окраска обновляется.

При retrieval факта:
    1. Факт извлечён из L3
    2. Использован в ответе пользователю
    3. ReconsolidationSignal:
        - Обновить usage_count++
        - Если контекст запроса отличается от контекста создания → добавить новый контекст
        - Если эмоциональная окраска изменилась → обновить PAD-ассоциацию
        - Перезаписать в L3 с обновлёнными метаданными

Инварианты:
    I-RC1: Reconsolidation НЕ меняет epistemic_state. Только метаданные.
    I-RC2: Только Slow Path. Никогда не блокирует ответ.
    I-RC3: confidence меняется не более чем на ±0.05 за один retrieval.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("velantrim.reconsolidation")


@dataclass
class ReconsolidationSignal:
    """Сигнал к переосмыслению факта после использования."""
    fact_id: str
    query_context: str = ""           # контекст запроса в котором использовался
    pad_state: Optional[Dict[str, float]] = None  # эмоциональная окраска запроса
    user_satisfaction: Optional[float] = None     # 0..1 реакция пользователя
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fact_id": self.fact_id,
            "query_context": self.query_context[:200],
            "pad_state": self.pad_state,
            "user_satisfaction": self.user_satisfaction,
            "timestamp": self.timestamp,
        }


@dataclass
class ReconsolidationReport:
    """Отчёт о переосмыслении фактов."""
    processed: int = 0
    updated: int = 0
    conflicted: int = 0     # факты с противоречивым контекстом
    skipped: int = 0        # факты без изменений
    facts: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "processed": self.processed,
            "updated": self.updated,
            "conflicted": self.conflicted,
            "skipped": self.skipped,
            "facts": self.facts[:10],
        }


class ReconsolidationEngine:
    """
    Движок переосмысления памяти.

    Вызывается ПОСЛЕ retrieval (Slow Path).
    Получает сигналы: какие факты использовались, в каком контексте, какая реакция.

    Использование:
        engine = ReconsolidationEngine()

        # После каждого ответа:
        await engine.process([
            ReconsolidationSignal(fact_id="fact_abc", query_context="architecture design"),
        ])
    """

    MAX_CONFIDENCE_DELTA = 0.05
    MAX_CONTEXTS_PER_FACT = 10

    def __init__(self):
        self._processed_count = 0

    async def process(self, signals: List[ReconsolidationSignal]) -> ReconsolidationReport:
        """
        Обработать сигналы переосмысления. Slow Path, не блокирует.
        """
        report = ReconsolidationReport(processed=len(signals))

        for signal in signals:
            try:
                self._reconsolidate_one(signal, report)
            except Exception as exc:
                logger.debug("Reconsolidation skipped for %s: %s", signal.fact_id, exc)
                report.skipped += 1

        self._processed_count += report.processed
        if report.updated:
            logger.info("Reconsolidation: %d/%d фактов обновлены", report.updated, report.processed)
        return report

    def _reconsolidate_one(self, signal: ReconsolidationSignal, report: ReconsolidationReport) -> None:
        """Переосмыслить один факт."""
        # 1. Получить факт из store
        fact = None
        try:
            from core.memory import get_fact
            fact = get_fact(signal.fact_id)
        except Exception:
            pass

        if fact is None:
            report.skipped += 1
            return

        updated = False

        # 2. Обновить usage_count
        metadata = fact.get("metadata", {})
        if isinstance(metadata, str):
            import json
            try:
                metadata = json.loads(metadata)
            except json.JSONDecodeError:
                metadata = {}

        usage = metadata.get("usage_count", 0)
        metadata["usage_count"] = usage + 1
        metadata["last_used_at"] = signal.timestamp
        updated = True

        # 3. Добавить контекст если он новый
        contexts: List[str] = metadata.get("usage_contexts", [])
        ctx = signal.query_context[:200]
        if ctx and ctx not in contexts:
            contexts.append(ctx)
            if len(contexts) > self.MAX_CONTEXTS_PER_FACT:
                contexts = contexts[-self.MAX_CONTEXTS_PER_FACT:]
            metadata["usage_contexts"] = contexts
            updated = True

            # Проверить конфликт контекстов
            if len(set(contexts)) >= 3:
                report.conflicted += 1

        # 4. Обновить PAD-ассоциацию
        if signal.pad_state:
            pad_history: List[Dict] = metadata.get("pad_history", [])
            pad_history.append({
                "valence": round(signal.pad_state.get("valence", 0.5), 2),
                "arousal": round(signal.pad_state.get("arousal", 0.5), 2),
                "at": signal.timestamp,
            })
            if len(pad_history) > 20:
                pad_history = pad_history[-20:]
            metadata["pad_history"] = pad_history
            updated = True

        # 5. V8.8: Bayesian confidence update (Beta-binomial conjugate)
        # вместо линейного delta. Учитывает prior confidence и количество
        # наблюдений — более устойчив к выбросам.
        if signal.user_satisfaction is not None:
            sat = max(0.0, min(1.0, signal.user_satisfaction))
            old_conf = float(fact.get("confidence", 0.5))
            total_uses = usage + 1  # включая текущий

            # Bayesian: Beta(α, β) posterior
            # α = prior_conf * prior_strength + successes
            # β = (1-prior_conf) * prior_strength + failures
            prior_strength = 10.0  # вес prior (чем выше — тем медленнее меняется)
            if sat > 0.7:
                success = 1
                failure = 0
            elif sat < 0.3:
                success = 0
                failure = 1
            else:
                # Нейтральная реакция — не меняем confidence
                success = 0
                failure = 0

            if success + failure > 0:
                alpha = old_conf * prior_strength + success
                beta_param = (1.0 - old_conf) * prior_strength + failure
                new_conf = alpha / (alpha + beta_param)
                # Ограничить delta для плавности
                new_conf = old_conf + max(-0.05, min(0.05, new_conf - old_conf))
                new_conf = max(0.1, min(1.0, new_conf))

            if abs(new_conf - old_conf) > 0.001:
                fact["confidence"] = round(new_conf, 4)
                updated = True

        # 6. Записать обновлённый факт
        if updated:
            fact["metadata"] = metadata
            fact["updated_at"] = signal.timestamp
            try:
                from core.memory import store_fact
                store_fact(fact)
                report.updated += 1
                report.facts.append(signal.fact_id)
            except Exception:
                report.skipped += 1
        else:
            report.skipped += 1

    def stats(self) -> Dict[str, Any]:
        return {"processed_total": self._processed_count}


# Глобальный экземпляр
_engine: Optional[ReconsolidationEngine] = None


def get_reconsolidation_engine() -> ReconsolidationEngine:
    global _engine
    if _engine is None:
        _engine = ReconsolidationEngine()
    return _engine


__all__ = ["ReconsolidationEngine", "ReconsolidationSignal", "ReconsolidationReport", "get_reconsolidation_engine"]
