"""
Causal Bridge — связи между episode/entity при ingest (RFC requires).
"""

from __future__ import annotations

import logging
import re
from typing import Any

from core.causal_graph import get_causal_graph

logger = logging.getLogger(__name__)

_REQUIRES_RE = re.compile(
    r"(?:требует|requires|зависит от|depends on|нужен|нужна|нужно)\s+(.+)",
    re.IGNORECASE | re.UNICODE,
)


async def infer_requires_from_chunk(
    chunk: str,
    episode_uuid: str,
    entity_names: list[str],
) -> list[str]:
    """
    Эвристика: если в тексте «требует X» — requires(episode, entity_X).
    MVP без LLM.
    """
    if not chunk or not entity_names:
        return []

    relation_ids: list[str] = []
    try:
        from core.causal_graph import is_causal_graph_enabled

        if not is_causal_graph_enabled():
            return []

        graph = get_causal_graph()
        lower_chunk = chunk.lower()

        for ent in entity_names:
            ent_l = ent.strip().lower()
            if len(ent_l) < 3:
                continue
            if ent_l in lower_chunk and any(
                kw in lower_chunk
                for kw in ("требует", "requires", "зависит", "depends", "нужен")
            ):
                rid = graph.add_relation(
                    episode_uuid,
                    ent,
                    "requires",
                    confidence=0.55,
                    knowledge_status="inferred",
                    inference_source="llm_extraction",
                    metadata={"source": "ingest_heuristic"},
                )
                relation_ids.append(rid)

        if len(entity_names) >= 2:
            for i in range(len(entity_names) - 1):
                a, b = entity_names[i], entity_names[i + 1]
                rid = graph.add_relation(
                    a,
                    b,
                    "precedes",
                    confidence=0.45,
                    knowledge_status="inferred",
                    inference_source="llm_extraction",
                    metadata={"co_occurrence": True},
                )
                relation_ids.append(rid)

    except Exception as exc:  # noqa: BLE001
        logger.warning("infer_requires failed (non-blocking): %s", exc)

    return relation_ids


async def observe_causal_from_ingest(
    *,
    episode_uuid: str,
    chunk: str,
    entity_names: list[str],
    graphiti=None,
) -> dict[str, Any]:
    """Вызывается после Velum на ingest chunk."""
    result: dict[str, Any] = {"relations_added": 0, "relation_ids": []}

    if not episode_uuid:
        return result

    rids = await infer_requires_from_chunk(
        chunk, episode_uuid, entity_names
    )
    result["relation_ids"] = rids
    result["relations_added"] = len(rids)

    if rids:
        try:
            from core.event_bridge import on_causal_relation

            for rid in rids[:5]:
                rel = get_causal_graph().get_relation(rid)
                if rel:
                    await on_causal_relation(
                        rid,
                        rel.from_fact_id,
                        rel.to_fact_id,
                        rel.relation_type,
                    )
        except Exception as exc:  # noqa: BLE001
            logger.debug("causal event publish: %s", exc)

        if graphiti:
            try:
                from core.causal_persistence import persist_relations_to_graph

                await persist_relations_to_graph(graphiti, rids)
            except Exception as exc:  # noqa: BLE001
                logger.debug("causal persist: %s", exc)

    return result


def format_causal_context_section(fact_id: str) -> str:
    """Секция explain для context builder."""
    try:
        from core.causal_graph import get_causal_graph, is_causal_graph_enabled

        if not is_causal_graph_enabled() or not fact_id:
            return ""

        expl = get_causal_graph().explain(fact_id)
        if not expl.get("has_explanation"):
            return ""

        lines = ["## Каузальные связи (CausalGraph):"]
        for key in ("caused_by", "required_by", "implied_by"):
            items = expl.get(key) or []
            if items:
                parts = [
                    f"{x['fact_id']} ({x['confidence']:.2f})" for x in items[:3]
                ]
                lines.append(f"- {key}: " + ", ".join(parts))
        return "\n".join(lines)
    except Exception as exc:  # noqa: BLE001
        logger.debug("causal context: %s", exc)
        return ""


__all__ = [
    "format_causal_context_section",
    "infer_requires_from_chunk",
    "observe_causal_from_ingest",
]
