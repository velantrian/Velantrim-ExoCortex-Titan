"""
Fusion Bridge — L5.5 в retrieval / context (I35: read-only).

Подключает PredictiveFusion к build_context_for_query.
"""

from __future__ import annotations

import logging
from typing import Any

from core.lsm_prediction import predict_rhythm_topic
from core.predictive_fusion import (
    FusedPrediction,
    FusionContext,
    get_predictive_fusion,
    is_predictive_fusion_enabled,
)
from core.sae_prediction import predict_semantic_topic

logger = logging.getLogger(__name__)

_graph_write_guard = {"write_count": 0}


def assert_i35_no_graph_write() -> None:
    """Для тестов I35: fusion не должен писать в граф."""
    if _graph_write_guard["write_count"] > 0:
        raise RuntimeError("I35 VIOLATION: L5.5 пишет в граф")


def format_fusion_context_section(fused: FusedPrediction) -> str:
    if fused.source == "consensus" and fused.topic:
        lines = [
            "## Предсказание контекста (L5.5, консенсус):",
            f"- Тема: **{fused.topic}** (уверенность {fused.confidence:.2f})",
        ]
        if fused.timing:
            lines.append(f"- Ритм: {fused.timing}")
        return "\n".join(lines)

    if fused.source == "divergent" and fused.candidates:
        lines = ["## Предсказание контекста (L5.5, расхождение):"]
        for pred, w in fused.candidates:
            t = pred.get("topic") or "—"
            c = pred.get("confidence", 0.0)
            src = pred.get("source", "?")
            lines.append(f"- {src}: {t} (вес {w:.2f}, conf {c:.2f})")
        lines.append(
            f"- Итоговая осторожность: conf={fused.confidence:.2f} (×0.6)"
        )
        return "\n".join(lines)

    return ""


async def build_fusion_for_query(
    query: str,
    *,
    entities: list[dict[str, Any]],
    episodes: list[dict[str, Any]],
) -> tuple[FusedPrediction | None, str]:
    """
    Собрать FusedPrediction и текст секции для LLM context.

    Returns:
        (fused или None, section_text)
    """
    if not is_predictive_fusion_enabled():
        return None, ""

    sae = await predict_semantic_topic(query, entities)
    lsm = await predict_rhythm_topic(episodes, query=query)

    ctx = FusionContext(
        lsm_rhythm_stability=float(lsm.get("rhythm_stability", 0.5)),
        sae_graph_density=float(sae.get("graph_density", 0.5)),
    )

    fusion = get_predictive_fusion()
    fused = await fusion.fuse(sae, lsm, ctx)
    section = format_fusion_context_section(fused)

    logger.debug(
        "L5.5 fusion: source=%s topic=%s conf=%.3f",
        fused.source,
        fused.topic,
        fused.confidence,
    )
    return fused, section


async def notify_proto_candidate(
    proto_id: str,
    entity_cluster: list[str],
    confidence: float,
) -> None:
    """
    A3 scaffold: сигнал Concept Emergence → L5.5 (только in-memory, без графа).
    """
    if not is_predictive_fusion_enabled():
        return
    logger.debug(
        "L5.5 proto signal: id=%s entities=%s conf=%.3f",
        proto_id,
        entity_cluster[:5],
        confidence,
    )


__all__ = [
    "assert_i35_no_graph_write",
    "build_fusion_for_query",
    "format_fusion_context_section",
    "notify_proto_candidate",
]
