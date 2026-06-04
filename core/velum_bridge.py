"""
Velum Bridge — подключение L1.5 к ingest (Sprint 2 / T3).

Поток:
    add_episode → filter_graphiti_results → entity names
        → Velum.observe_episode(episode_uuid, entities)
        → опционально persist_velum_metadata в Episodic
    конец ingest_text_document → Velum.on_session_end() (decay / promote)

Принципы:
  - Feature-flag ENABLE_VELUM (default off).
  - Non-blocking: ошибки Velum не ломают ingest.
  - Process-singleton Velum (in-memory, Velum.I4).
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

from core.feature_config import get_config
from core.velum import ObserveResult, SessionEndResult, Velum, VelumSignal

logger = logging.getLogger(__name__)

_velum_singleton: Velum | None = None


def get_velum() -> Velum:
    """Process-wide singleton (in-memory pre-graph)."""
    global _velum_singleton
    if _velum_singleton is None:
        _velum_singleton = Velum()
    return _velum_singleton


def reset_velum() -> None:
    """Сброс singleton (только для тестов)."""
    global _velum_singleton
    _velum_singleton = None


def entity_names_from_safe_results(safe_results: dict[str, Any]) -> list[str]:
    """
    Извлечь имена сущностей из результата filter_graphiti_results.

    Используем name (не uuid) — Velum отслеживает co-occurrence по ярлыкам
    сущностей в эпизоде, как в RFC0016.
    """
    names: list[str] = []
    seen: set[str] = set()
    for ent in safe_results.get("entities") or []:
        if not isinstance(ent, dict):
            continue
        raw = ent.get("name")
        if not isinstance(raw, str):
            continue
        name = raw.strip()
        if not name or name in seen:
            continue
        seen.add(name)
        names.append(name)
    return names


@dataclass
class VelumIngestResult:
    """Результат observe для одного episode/chunk."""

    episode_id: str
    observe: ObserveResult
    neighbor_hints: dict[str, list[str]] = field(default_factory=dict)

    @property
    def edges_touched(self) -> int:
        return self.observe.edges_touched

    @property
    def entities_seen(self) -> int:
        return self.observe.entities_seen

    @property
    def signals(self) -> list[VelumSignal]:
        return self.observe.signals

    def to_metadata(self) -> dict[str, Any]:
        return {
            "velum_edges_touched": self.edges_touched,
            "velum_entities_seen": self.entities_seen,
            "velum_signals_count": len(self.signals),
            "velum_neighbor_hints": json.dumps(
                self.neighbor_hints, ensure_ascii=False
            ),
        }


async def observe_episode_from_ingest(
    *,
    episode_id: str,
    entity_names: list[str],
    neighbor_hint_limit: int = 3,
    graphiti=None,
    salience_weight: float = 1.0,
    episode_text: str | None = None,
) -> VelumIngestResult:
    """
    Зафиксировать co-occurrence после успешного add_episode.

    neighbor_hints: для каждой сущности эпизода — топ соседей из Velum
    (для F1.5 / context builder, записывается в metadata опционально).
    """
    weight = salience_weight
    if episode_text:
        try:
            from core.salience import analyze_episode_salience, is_salience_enabled

            if is_salience_enabled():
                salience = analyze_episode_salience(episode_text, episode_id)
                weight = salience.weight
                if graphiti:
                    from core.salience import persist_salience_metadata

                    await persist_salience_metadata(
                        graphiti, episode_uuid=episode_id, result=salience
                    )
                if graphiti and entity_names:
                    from core.salience_fsrs import persist_entity_salience

                    await persist_entity_salience(
                        graphiti, entity_names, salience.weight
                    )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Salience analyze failed (non-blocking): %s", exc)

    velum = get_velum()
    observe = await velum.observe_episode(
        episode_id, entity_names, salience_weight=weight
    )

    hints: dict[str, list[str]] = {}
    if neighbor_hint_limit > 0 and len(entity_names) >= 1:
        for name in entity_names:
            neighbors = await velum.get_neighbors(
                name,
                min_weight=0.0,
                limit=neighbor_hint_limit,
                episode_id=episode_id,
            )
            if neighbors:
                hints[name] = [n for n, _ in neighbors]

    result = VelumIngestResult(
        episode_id=episode_id,
        observe=observe,
        neighbor_hints=hints,
    )

    if observe.signals:
        logger.info(
            "velum: episode=%s signals=%d edges=%d entities=%d",
            episode_id,
            len(observe.signals),
            observe.edges_touched,
            observe.entities_seen,
        )
    else:
        logger.debug(
            "velum: episode=%s edges=%d entities=%d",
            episode_id,
            observe.edges_touched,
            observe.entities_seen,
        )

    try:
        from core.concept_emergence import (
            is_concept_emergence_enabled,
            observe_concept_emergence,
        )

        if is_concept_emergence_enabled() and entity_names:
            emergence = await observe_concept_emergence(
                entity_names, episode_id, salience_weight=weight
            )
            if graphiti and emergence.protos_born:
                from core.concept_promote import try_promote_born_protos

                await try_promote_born_protos(graphiti, emergence.protos_born)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Concept emergence failed (non-blocking) episode=%s: %s",
            episode_id,
            exc,
        )

    return result


async def strengthen_velum_cluster(
    entities: list[str],
    *,
    factor: float = 1.3,
) -> int:
    """Усилить все synapse внутри кластера сущностей (RFC0066 → Velum LTP)."""
    return await get_velum().strengthen_cluster(entities, factor=factor)


async def persist_velum_metadata(
    graphiti,
    *,
    episode_uuid: str,
    result: VelumIngestResult,
) -> bool:
    """
    Записать Velum-метаданные в Episodic (опционально, non-blocking).
    """
    if not episode_uuid or graphiti is None:
        return False

    try:
        driver = graphiti.driver
        meta = result.to_metadata()
        await driver.execute_query(
            """
            MATCH (e:Episodic {uuid: $uuid})
            SET e.velum_edges_touched = $edges,
                e.velum_entities_seen = $entities,
                e.velum_signals_count = $signals,
                e.velum_neighbor_hints = $hints
            """,
            uuid=episode_uuid,
            edges=meta["velum_edges_touched"],
            entities=meta["velum_entities_seen"],
            signals=meta["velum_signals_count"],
            hints=meta["velum_neighbor_hints"],
        )
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "persist_velum_metadata: не удалось для %s: %s",
            episode_uuid,
            exc,
        )
        return False


async def finalize_ingest_session(
    *,
    use_fsrs_decay: bool | None = None,
) -> SessionEndResult:
    """
    Конец ingest-документа = граница «сессии» для Velum decay/promote.

    Вызывается один раз в конце ingest_text_document.
    """
    if use_fsrs_decay is None:
        use_fsrs_decay = get_config().app.velum_use_fsrs_decay
    velum = get_velum()
    result = await velum.on_session_end(use_fsrs_decay=use_fsrs_decay)
    if result.promoted:
        logger.info(
            "velum session_end: promoted=%d decayed=%d gc_removed=%d",
            len(result.promoted),
            result.decayed_edges,
            result.gc_removed,
        )
    return result


def is_velum_enabled() -> bool:
    return get_config().app.enable_velum


__all__ = [
    "VelumIngestResult",
    "entity_names_from_safe_results",
    "finalize_ingest_session",
    "get_velum",
    "is_velum_enabled",
    "observe_episode_from_ingest",
    "persist_velum_metadata",
    "reset_velum",
]
