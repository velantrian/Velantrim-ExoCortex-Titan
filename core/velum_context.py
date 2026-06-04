"""
Velum Context Hints — F1.5 (Sprint 2 / T4).

Расширяет retrieval и context builder соседями из in-memory Velum pre-graph.
Работает только при ENABLE_VELUM=1.

Поток:
    query + top entities из search
        → seed entities
        → Velum.get_neighbors(seed)
        → секция контекста + опционально доп. fulltext hits
"""

from __future__ import annotations

import logging
import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any

from core.feature_config import get_config
from core.velum_bridge import get_velum, is_velum_enabled

logger = logging.getLogger(__name__)

_TOKEN_RE = re.compile(r"[\wА-Яа-яЁё]{3,}", re.UNICODE)


@dataclass(frozen=True)
class VelumHintEntry:
    """Одна подсказка: seed → neighbor с весом synapse."""

    seed: str
    neighbor: str
    weight: float


@dataclass
class VelumHintsBundle:
    """Собранные hints для одного запроса."""

    seeds: list[str] = field(default_factory=list)
    entries: list[VelumHintEntry] = field(default_factory=list)

    @property
    def neighbor_names(self) -> list[str]:
        seen: set[str] = set()
        out: list[str] = []
        for e in self.entries:
            if e.neighbor not in seen:
                seen.add(e.neighbor)
                out.append(e.neighbor)
        return out

    def format_context_section(self) -> str:
        if not self.entries:
            return ""
        lines = ["## Связанные сущности (Velum L1.5):"]
        by_seed: dict[str, list[VelumHintEntry]] = {}
        for entry in self.entries:
            by_seed.setdefault(entry.seed, []).append(entry)
        for seed, group in by_seed.items():
            parts = [
                f"{e.neighbor} (вес {e.weight:.2f})"
                for e in sorted(group, key=lambda x: x.weight, reverse=True)
            ]
            lines.append(f"- {seed} ↔ " + ", ".join(parts))
        return "\n".join(lines)


def _velum_hint_params() -> tuple[float, int, int]:
    cfg = get_config().app
    return (
        getattr(cfg, "velum_hint_min_weight", 0.15),
        getattr(cfg, "velum_hint_limit_per_entity", 3),
        getattr(cfg, "velum_hint_max_seeds", 5),
    )


def seed_entities_from_query_and_hits(
    query: str,
    entities: Iterable[dict[str, Any]],
    *,
    max_seeds: int | None = None,
) -> list[str]:
    """
    Seed-сущности для Velum: топ из search + значимые токены запроса.
    """
    if max_seeds is None:
        max_seeds = _velum_hint_params()[2]

    seeds: list[str] = []
    seen: set[str] = set()

    sorted_ents = sorted(
        list(entities),
        key=lambda e: float(e.get("score") or 0.0),
        reverse=True,
    )
    for ent in sorted_ents:
        name = (ent.get("name") or "").strip()
        if not name or name.lower() == "unknown" or name in seen:
            continue
        seen.add(name)
        seeds.append(name)
        if len(seeds) >= max_seeds:
            return seeds

    q = (query or "").strip()
    for tok in _TOKEN_RE.findall(q):
        if len(tok) < 4:
            continue
        key = tok.strip()
        if not key or key.lower() in seen:
            continue
        seen.add(key.lower())
        seeds.append(key)
        if len(seeds) >= max_seeds:
            break

    return seeds[:max_seeds]


async def collect_velum_hints(
    seed_entities: list[str],
    *,
    min_weight: float | None = None,
    limit_per_entity: int | None = None,
    episode_id: str | None = None,
) -> VelumHintsBundle:
    """Собрать neighbor hints из process-wide Velum."""
    if not seed_entities:
        return VelumHintsBundle()

    cfg_min, cfg_limit, _ = _velum_hint_params()
    if min_weight is None:
        min_weight = cfg_min
    if limit_per_entity is None:
        limit_per_entity = cfg_limit

    velum = get_velum()
    entries: list[VelumHintEntry] = []
    seen_pairs: set[tuple[str, str]] = set()

    for seed in seed_entities:
        neighbors = await velum.get_neighbors(
            seed,
            min_weight=min_weight,
            limit=limit_per_entity,
            episode_id=episode_id,
        )
        for neighbor, weight in neighbors:
            pair = (min(seed, neighbor), max(seed, neighbor))
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)
            entries.append(
                VelumHintEntry(seed=seed, neighbor=neighbor, weight=weight)
            )

    return VelumHintsBundle(seeds=list(seed_entities), entries=entries)


async def fetch_entity_snippets_from_graph(
    graphiti,
    names: list[str],
    *,
    limit: int = 8,
) -> list[dict[str, str]]:
    """
    Подтянуть summary сущностей из Neo4j для neighbor hints (если есть граф).
    """
    if not graphiti or not names:
        return []

    driver = getattr(graphiti, "driver", None) or getattr(graphiti, "_driver", None)
    if not driver:
        return []

    unique = []
    seen: set[str] = set()
    for n in names:
        s = (n or "").strip()
        if not s or s.lower() in seen:
            continue
        seen.add(s.lower())
        unique.append(s)
    if not unique:
        return []

    try:
        res = await driver.execute_query(
            """
            MATCH (e:Entity)
            WHERE coalesce(e.deleted, false) = false
              AND e.name IN $names
            RETURN e.name AS name, coalesce(e.summary, '') AS summary
            LIMIT $limit
            """,
            names=unique[:limit],
            limit=limit,
        )
        rows = []
        for rec in res.records or []:
            name = (rec.get("name") or "").strip()
            summary = (rec.get("summary") or "").strip()
            if name:
                rows.append({"name": name, "summary": summary})
        return rows
    except Exception as exc:  # noqa: BLE001
        logger.debug("fetch_entity_snippets_from_graph: %s", exc)
        return []


def _enrich_section_with_summaries(
    section: str,
    snippets: list[dict[str, str]],
) -> str:
    if not snippets:
        return section
    extra = ["", "## Детали соседей (граф):"]
    for row in snippets:
        name = row.get("name", "")
        summary = (row.get("summary") or "").strip()
        if summary:
            extra.append(f"- {name}: {summary[:200]}")
        else:
            extra.append(f"- {name}")
    return section + "\n".join(extra)


async def build_velum_context_section(
    query: str,
    entities: Iterable[dict[str, Any]],
    graphiti=None,
    *,
    episode_id: str | None = None,
) -> tuple[str, int]:
    """
    Построить секцию Velum для build_context_for_query.

    Returns:
        (текст секции или "", число hint-записей)
    """
    if not is_velum_enabled():
        return "", 0

    seeds = seed_entities_from_query_and_hits(query, entities)
    if not seeds:
        return "", 0

    bundle = await collect_velum_hints(seeds, episode_id=episode_id)
    if not bundle.entries:
        return "", 0

    section = bundle.format_context_section()

    if is_velum_enabled():
        try:
            from core.concept_emergence import (
                format_proto_context_section,
                get_concept_detector,
                is_concept_emergence_enabled,
            )

            if is_concept_emergence_enabled():
                detector = get_concept_detector()
                proto_seen: set[str] = set()
                proto_list = []
                for seed in seeds:
                    for proto in detector.get_protos_for_entity(seed):
                        if proto.proto_id not in proto_seen:
                            proto_seen.add(proto.proto_id)
                            proto_list.append(proto)
                proto_section = format_proto_context_section(proto_list)
                if proto_section:
                    section = (
                        (section + "\n\n" + proto_section) if section else proto_section
                    )
        except Exception as exc:  # noqa: BLE001
            logger.debug("proto context hints skipped: %s", exc)

    if graphiti and bundle.neighbor_names:
        snippets = await fetch_entity_snippets_from_graph(
            graphiti, bundle.neighbor_names
        )
        section = _enrich_section_with_summaries(section, snippets)

    logger.debug(
        "velum F1.5: seeds=%d hints=%d query=%s",
        len(bundle.seeds),
        len(bundle.entries),
        (query or "")[:40],
    )
    return section, len(bundle.entries)


async def expand_knowledge_items_with_velum(
    graphiti,
    query: str,
    items: list[dict],
    *,
    extra_limit: int = 5,
) -> list[dict]:
    """
    Расширить результаты search_knowledge соседями Velum (доп. fulltext).
    """
    if not is_velum_enabled() or not items:
        return items

    entity_items = [it for it in items if it.get("kind") == "Entity"]
    seeds = seed_entities_from_query_and_hits(query, _items_as_entities(entity_items))
    bundle = await collect_velum_hints(seeds)
    if not bundle.neighbor_names:
        return items

    existing_names = {
        (it.get("name") or it.get("text") or "").strip().lower()
        for it in items
    }

    driver = getattr(graphiti, "driver", None) if graphiti else None
    if not driver:
        return items

    expanded = list(items)
    added = 0
    for neighbor in bundle.neighbor_names:
        if neighbor.lower() in existing_names:
            continue
        try:
            res = await driver.execute_query(
                """
                CALL db.index.fulltext.queryNodes(
                    'node_name_and_summary', $q
                ) YIELD node, score
                WHERE coalesce(node.deleted, false) = false
                  AND node.name = $exact_name
                RETURN 'Entity' AS kind, node.uuid AS uuid,
                       node.name AS name, node.summary AS summary,
                       score * 0.35 AS score
                LIMIT 1
                """,
                q=neighbor,
                exact_name=neighbor,
            )
            for rec in res.records or []:
                text = (rec.get("summary") or rec.get("name") or "").strip()
                if not text:
                    continue
                expanded.append(
                    {
                        "kind": "Entity",
                        "uuid": rec.get("uuid"),
                        "score": float(rec.get("score") or 0.3),
                        "text": text[:500],
                        "velum_expanded": True,
                        "velum_seed": bundle.seeds[0] if bundle.seeds else "",
                    }
                )
                existing_names.add(neighbor.lower())
                added += 1
                if added >= extra_limit:
                    return expanded
        except Exception as exc:  # noqa: BLE001
            logger.debug("velum expand knowledge for %s: %s", neighbor, exc)

    return expanded


def _items_as_entities(items: list[dict]) -> list[dict[str, Any]]:
    return [
        {"name": it.get("name") or it.get("text"), "score": it.get("score", 0.5)}
        for it in items
    ]


async def velum_hints_for_entity(
    entity_name: str,
    *,
    min_weight: float | None = None,
    limit: int | None = None,
) -> VelumHintsBundle:
    """F1.5 для build_agent_context(entity_name)."""
    if not is_velum_enabled():
        return VelumHintsBundle()
    name = (entity_name or "").strip()
    if not name:
        return VelumHintsBundle()
    _, cfg_limit, _ = _velum_hint_params()
    if limit is None:
        limit = cfg_limit
    return await collect_velum_hints(
        [name],
        min_weight=min_weight,
        limit_per_entity=limit,
    )


__all__ = [
    "VelumHintEntry",
    "VelumHintsBundle",
    "build_velum_context_section",
    "collect_velum_hints",
    "expand_knowledge_items_with_velum",
    "seed_entities_from_query_and_hits",
    "velum_hints_for_entity",
]
