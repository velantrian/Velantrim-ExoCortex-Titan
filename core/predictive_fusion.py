"""
L5.5 PredictiveFusion — арбитр SAE (семантика) и LSM (ритм).

Инвариант I35: не пишет в граф — только читает и возвращает FusedPrediction.
CPU-only, 0 токенов LLM.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

DIVERGENT_PENALTY = 0.6
WEIGHT_SHIFT = 0.15
RHYTHM_STABILITY_THRESHOLD = 0.7
GRAPH_DENSITY_THRESHOLD = 0.6


@dataclass(frozen=True)
class FusedPrediction:
    """Результат fusion для retrieval / context."""

    topic: str | None
    confidence: float
    source: str  # consensus | divergent
    timing: dict[str, Any] | None = None
    candidates: list[tuple[dict[str, Any], float]] | None = None
    w_sae: float = 0.6
    w_lsm: float = 0.4

    def to_dict(self) -> dict[str, Any]:
        return {
            "topic": self.topic,
            "confidence": self.confidence,
            "source": self.source,
            "timing": self.timing,
            "w_sae": self.w_sae,
            "w_lsm": self.w_lsm,
        }


@dataclass(frozen=True)
class PredictionError:
    """Сигнал ошибки предсказания для обучения весов."""

    source: str  # sae | lsm
    magnitude: float  # 0..1


@dataclass
class FusionContext:
    """Контекст для динамических весов."""

    lsm_rhythm_stability: float = 0.5
    sae_graph_density: float = 0.5


class PredictiveFusionLayer:
    """
    L5.5: комбинирует SAE и LSM с адаптивными весами.
    """

    def __init__(
        self,
        w_sae: float = 0.6,
        w_lsm: float = 0.4,
        *,
        learning_rate: float = 0.05,
        w_min: float = 0.2,
    ) -> None:
        self.w_sae = w_sae
        self.w_lsm = w_lsm
        self._learning_rate = learning_rate
        self._w_min = w_min
        self.consensus_count = 0
        self.divergent_count = 0

    def _dynamic_weights(self, ctx: FusionContext) -> tuple[float, float]:
        w_s, w_l = self.w_sae, self.w_lsm
        if ctx.lsm_rhythm_stability > RHYTHM_STABILITY_THRESHOLD:
            w_l += WEIGHT_SHIFT
        if ctx.sae_graph_density > GRAPH_DENSITY_THRESHOLD:
            w_s += WEIGHT_SHIFT
        total = w_s + w_l
        if total <= 0:
            return 0.5, 0.5
        return w_s / total, w_l / total

    async def fuse(
        self,
        sae_prediction: dict[str, Any],
        lsm_prediction: dict[str, Any],
        context: FusionContext | None = None,
    ) -> FusedPrediction:
        ctx = context or FusionContext()
        w_sae, w_lsm = self._dynamic_weights(ctx)

        sae_topic = _norm_topic(sae_prediction.get("topic"))
        lsm_topic = _norm_topic(lsm_prediction.get("topic"))
        sae_conf = _clamp_conf(sae_prediction.get("confidence", 0.0))
        lsm_conf = _clamp_conf(lsm_prediction.get("confidence", 0.0))

        if sae_topic and sae_topic == lsm_topic:
            combined = (sae_conf**w_sae) * (lsm_conf**w_lsm)
            self.consensus_count += 1
            logger.debug(
                "L5.5 consensus: %s conf=%.3f", sae_topic, combined
            )
            return FusedPrediction(
                topic=sae_topic,
                confidence=combined,
                source="consensus",
                timing=lsm_prediction.get("timing"),
                w_sae=w_sae,
                w_lsm=w_lsm,
            )

        self.divergent_count += 1
        logger.debug(
            "L5.5 divergent: SAE=%s vs LSM=%s", sae_topic, lsm_topic
        )
        return FusedPrediction(
            topic=None,
            confidence=max(w_sae, w_lsm) * DIVERGENT_PENALTY,
            source="divergent",
            candidates=[
                (dict(sae_prediction), w_sae),
                (dict(lsm_prediction), w_lsm),
            ],
            w_sae=w_sae,
            w_lsm=w_lsm,
        )

    async def update_from_error(self, error: PredictionError) -> None:
        """Медленная коррекция весов по prediction error."""
        mag = max(0.0, min(1.0, float(error.magnitude)))
        if error.source == "sae":
            self.w_sae = max(self._w_min, self.w_sae - self._learning_rate * mag)
        elif error.source == "lsm":
            self.w_lsm = max(self._w_min, self.w_lsm - self._learning_rate * mag)
        total = self.w_sae + self.w_lsm
        if total > 0:
            self.w_sae /= total
            self.w_lsm /= total
        logger.debug(
            "L5.5 weights: w_sae=%.3f w_lsm=%.3f", self.w_sae, self.w_lsm
        )

    @property
    def consensus_rate(self) -> float:
        total = self.consensus_count + self.divergent_count
        if total == 0:
            return 0.0
        return self.consensus_count / total


def _norm_topic(raw: Any) -> str | None:
    if raw is None:
        return None
    s = str(raw).strip().lower()
    return s or None


def _clamp_conf(value: Any) -> float:
    try:
        v = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, v))


_fusion_singleton: PredictiveFusionLayer | None = None


def get_predictive_fusion() -> PredictiveFusionLayer:
    global _fusion_singleton
    if _fusion_singleton is None:
        _fusion_singleton = PredictiveFusionLayer()
    return _fusion_singleton


def reset_predictive_fusion() -> None:
    global _fusion_singleton
    _fusion_singleton = None


def is_predictive_fusion_enabled() -> bool:
    from core.feature_config import get_config

    return bool(get_config().app.enable_predictive_fusion)


__all__ = [
    "FusedPrediction",
    "FusionContext",
    "PredictionError",
    "PredictiveFusionLayer",
    "get_predictive_fusion",
    "is_predictive_fusion_enabled",
    "reset_predictive_fusion",
]
