"""
Etir Bridge — ingest / recall hooks.
"""

from __future__ import annotations

import logging
from typing import Any

from core.etir import get_etir, is_etir_enabled

logger = logging.getLogger(__name__)


async def observe_entities_from_ingest(
    entity_names: list[str],
    *,
    episode_id: str = "",
) -> dict[str, Any]:
    if not is_etir_enabled():
        return {"skipped": True}
    try:
        n = get_etir().observe_cooccurrence(entity_names)
        if episode_id:
            from core.event_bridge import publish_event

            await publish_event(
                "ETIR_OBSERVED",
                {"episode_id": episode_id, "edges": n, "entities": len(entity_names)},
            )
        return {"edges": n, "entities": len(entity_names)}
    except Exception as exc:  # noqa: BLE001
        logger.debug("etir observe: %s", exc)
        return {"error": str(exc)}


async def build_etir_context_section(
    query: str,
    entity_names: list[str],
) -> tuple[str, int]:
    if not is_etir_enabled():
        return "", 0
    try:
        seeds = list(entity_names)[:5]
        if query.strip() and query.strip() not in seeds:
            seeds = [query.strip()[:80]] + seeds
        result = get_etir().activate(seeds)
        section = get_etir().format_context_section(result)
        return section, result.top_k
    except Exception as exc:  # noqa: BLE001
        logger.warning("Etir context failed (non-blocking): %s", exc)
        return "", 0


__all__ = ["build_etir_context_section", "observe_entities_from_ingest"]
