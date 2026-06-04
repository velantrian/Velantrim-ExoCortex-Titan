"""
SAE — Semantic Anticipation Engine (read-only, L5.5 вход).

Предсказание темы из Velum + результатов retrieval. Не пишет в граф (I35).
"""

from __future__ import annotations

import logging
import re
from collections.abc import Iterable
from typing import Any

logger = logging.getLogger(__name__)

_TOKEN_RE = re.compile(r"[\wА-Яа-яЁё]{3,}", re.UNICODE)


async def predict_semantic_topic(
    query: str,
    entities: Iterable[dict[str, Any]],
    *,
    graph_density: float | None = None,
) -> dict[str, Any]:
    """
    SAE prediction: {topic, confidence, graph_density}.

    topic — доминирующая сущность или токен запроса;
    confidence — нормализованный score retrieval / velum.
    """
    ent_list = list(entities)
    topic: str | None = None
    confidence = 0.35

    if ent_list:
        best = max(ent_list, key=lambda e: float(e.get("score") or 0.0))
        name = (best.get("name") or best.get("text") or "").strip()
        if name and name.lower() != "unknown":
            topic = name
            score = float(best.get("score") or 0.0)
            confidence = min(0.95, 0.4 + score * 0.15)

    if not topic:
        for tok in _TOKEN_RE.findall(query or ""):
            if len(tok) >= 4:
                topic = tok
                confidence = 0.45
                break

    density = graph_density
    if density is None:
        density = min(1.0, len(ent_list) / 8.0) if ent_list else 0.2

    try:
        from core.velum_bridge import get_velum, is_velum_enabled

        if is_velum_enabled() and topic:
            velum = get_velum()
            neighbors = await velum.get_neighbors(topic, min_weight=0.2, limit=3)
            if neighbors:
                confidence = min(0.98, confidence + 0.1 * len(neighbors))
                density = min(1.0, density + 0.1 * len(neighbors))
    except Exception as exc:  # noqa: BLE001
        logger.debug("SAE velum boost skipped: %s", exc)

    return {
        "topic": topic,
        "confidence": confidence,
        "graph_density": density,
        "source": "sae",
    }


__all__ = ["predict_semantic_topic"]
