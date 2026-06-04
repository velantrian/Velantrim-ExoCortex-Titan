"""
Интеграция ExoCortex-слоёв в pipeline и ingest (V8.6).
"""

from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

_TOKEN_RE = re.compile(r"[\wА-Яа-яЁё]{3,}", re.UNICODE)


def extract_entity_names(text: str, limit: int = 20) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for t in _TOKEN_RE.findall(text or ""):
        key = t.lower()
        if key in seen or len(key) < 3:
            continue
        seen.add(key)
        out.append(t)
        if len(out) >= limit:
            break
    return out


async def observe_ingest_chunk(
    *,
    chunk: str,
    episode_id: str = "",
) -> dict[str, Any]:
    """Velum + Etir + Causal observe после записи факта/чанка."""
    result: dict[str, Any] = {}
    entities = extract_entity_names(chunk)
    if not entities:
        return result

    try:
        from core.velum_bridge import is_velum_enabled, observe_episode_from_ingest

        if is_velum_enabled():
            r = await observe_episode_from_ingest(
                episode_id=episode_id or "local",
                entity_names=entities,
                graphiti=None,
                episode_text=chunk,
            )
            result["velum"] = r
    except Exception as exc:  # noqa: BLE001
        logger.debug("velum observe: %s", exc)

    try:
        from core.etir import is_etir_enabled
        from core.etir_bridge import observe_entities_from_ingest

        if is_etir_enabled():
            result["etir"] = await observe_entities_from_ingest(
                entities, episode_id=episode_id
            )
    except Exception as exc:  # noqa: BLE001
        logger.debug("etir observe: %s", exc)

    try:
        from core.causal_bridge import observe_causal_from_ingest
        from core.feature_config import get_config

        if get_config().app.enable_causal_graph:
            result["causal"] = await observe_causal_from_ingest(
                episode_uuid=episode_id,
                chunk=chunk,
                entity_names=entities,
                graphiti=None,
            )
    except Exception as exc:  # noqa: BLE001
        logger.debug("causal observe: %s", exc)

    return result


async def enrich_query_context(
    query: str,
    facts: list[dict[str, Any]],
) -> dict[str, Any]:
    """Подмешать Velum hints, Etir, Fusion (read-only) в ответ pipeline."""
    extra: dict[str, Any] = {"sections": []}
    entity_names = extract_entity_names(query)
    for f in facts[:5]:
        entity_names.extend(extract_entity_names(str(f.get("claim", ""))))
    seeds = list(dict.fromkeys(entity_names))[:8]

    entity_dicts = [{"name": s, "content": s} for s in seeds]

    try:
        from core.velum_bridge import is_velum_enabled
        from core.velum_context import build_velum_context_section

        if is_velum_enabled() and entity_dicts:
            section, n = await build_velum_context_section(query, entity_dicts)
            if section:
                extra["sections"].append({"kind": "velum", "text": section, "count": n})
    except Exception as exc:  # noqa: BLE001
        logger.debug("velum context: %s", exc)

    try:
        from core.etir import is_etir_enabled
        from core.etir_bridge import build_etir_context_section

        if is_etir_enabled():
            section, n = await build_etir_context_section(query, seeds)
            if section:
                extra["sections"].append({"kind": "etir", "text": section, "count": n})
    except Exception as exc:  # noqa: BLE001
        logger.debug("etir context: %s", exc)

    try:
        from core.fusion_bridge import build_fusion_for_query, format_fusion_context_section
        from core.predictive_fusion import is_predictive_fusion_enabled

        if is_predictive_fusion_enabled():
            fused, _ = await build_fusion_for_query(
                query, entities=entity_dicts, episodes=[]
            )
            if fused:
                section = format_fusion_context_section(fused)
                if section:
                    extra["sections"].append({"kind": "fusion", "text": section})
    except Exception as exc:  # noqa: BLE001
        logger.debug("fusion context: %s", exc)

    return extra


def register_exocortex_handlers() -> None:
    from core.event_bridge import register_default_handlers

    register_default_handlers()


__all__ = [
    "enrich_query_context",
    "extract_entity_names",
    "observe_ingest_chunk",
    "register_exocortex_handlers",
]
