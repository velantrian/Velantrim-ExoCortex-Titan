"""
Graph-level Ring Zero — защита I6 на стороне Neo4j через application-layer.

Sprint 1 / T5. Парный к `core/esm.py`: Python-side state machine защищает
по fact_id, этот модуль — по graph entity uuid.

Принципы:
  - I6 необратим: функция `unmark_ring_zero()` намеренно отсутствует.
  - Защита реализуется через атомарный read-then-write в одной Cypher
    транзакции: 1) MATCH → 2) check ring_zero → 3) SET only if not protected.
  - В Neo4j Community Edition conditional constraints на UPDATE не работают.
    Это application-level enforcement, что явно отражено в docstring API.
  - Все операции idempotent: повторный вызов mark_ring_zero даёт тот же эффект.

Связка:
  - `core/esm.py` — fact_id уровень
  - `core/epistemic_pipeline.py` — оркестрация TruthGate + Trace
  - этот модуль — graph entity uuid уровень
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)


# ─── Структуры результатов ────────────────────────────────────────────────────


@dataclass
class GraphTransitionResult:
    """Результат попытки изменения epistemic_state на graph entity."""

    ok: bool
    entity_uuid: str
    previous_state: str | None
    new_state: str | None
    reason: str
    blocked_by_ring_zero: bool = False


# ─── Mark / Unmark / Check ────────────────────────────────────────────────────


async def mark_ring_zero(
    graphiti,
    entity_uuid: str,
    *,
    reason: str = "",
    by: str = "system",
) -> bool:
    """
    Пометить Entity как Ring Zero (I6).

    NB: операция необратима — функция `unmark_ring_zero` намеренно
    не существует в этом модуле. Удалить Ring Zero можно только через
    прямой Cypher администратором БД.

    Возвращает True если узел найден и помечен (или уже был помечен).
    """
    if not entity_uuid:
        raise ValueError("mark_ring_zero: entity_uuid обязателен")

    driver = graphiti.driver
    now = datetime.now(UTC).isoformat()
    try:
        result = await driver.execute_query(
            """
            MATCH (e:Entity {uuid: $uuid})
            SET e.ring_zero = true,
                e.ring_zero_marked_at = coalesce(e.ring_zero_marked_at, $now),
                e.ring_zero_marked_by = coalesce(e.ring_zero_marked_by, $by),
                e.ring_zero_reason = coalesce(e.ring_zero_reason, $reason)
            RETURN e.uuid AS uuid
            """,
            uuid=entity_uuid,
            now=now,
            by=by,
            reason=reason,
        )
        return len(result.records) > 0
    except Exception as exc:  # noqa: BLE001
        logger.error("mark_ring_zero failed for %s: %s", entity_uuid, exc)
        return False


async def is_entity_ring_zero(graphiti, entity_uuid: str) -> bool:
    """True, если Entity помечен Ring Zero."""
    if not entity_uuid:
        return False
    driver = graphiti.driver
    try:
        result = await driver.execute_query(
            """
            MATCH (e:Entity {uuid: $uuid})
            RETURN coalesce(e.ring_zero, false) AS ring_zero
            """,
            uuid=entity_uuid,
        )
        if not result.records:
            return False
        return bool(result.records[0]["ring_zero"])
    except Exception as exc:  # noqa: BLE001
        logger.warning("is_entity_ring_zero failed for %s: %s", entity_uuid, exc)
        return False


async def list_ring_zero_entities(
    graphiti,
    *,
    group_id: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """Список всех Entity, помеченных Ring Zero."""
    driver = graphiti.driver
    cypher = """
        MATCH (e:Entity)
        WHERE e.ring_zero = true
        {group_filter}
        RETURN e.uuid AS uuid, e.name AS name,
               e.group_id AS group_id,
               e.epistemic_state AS epistemic_state,
               e.ring_zero_reason AS reason,
               e.ring_zero_marked_at AS marked_at,
               e.ring_zero_marked_by AS marked_by
        ORDER BY e.ring_zero_marked_at DESC
        LIMIT $limit
    """
    group_filter = "AND e.group_id = $gid" if group_id else ""
    cypher = cypher.format(group_filter=group_filter)

    params: dict[str, Any] = {"limit": int(limit)}
    if group_id:
        params["gid"] = group_id

    try:
        result = await driver.execute_query(cypher, **params)
        return [dict(rec) for rec in result.records]
    except Exception as exc:  # noqa: BLE001
        logger.warning("list_ring_zero_entities failed: %s", exc)
        return []


# ─── Безопасный переход state ─────────────────────────────────────────────────


async def safe_transition_entity_state(
    graphiti,
    entity_uuid: str,
    new_state: str,
    *,
    by: str = "system",
) -> GraphTransitionResult:
    """
    Перевести Entity в новое epistemic_state с проверкой I6.

    Атомарность: в одной Cypher операции:
      1. Прочитать current state + ring_zero
      2. Если ring_zero=true → отказ (blocked_by_ring_zero=True)
      3. Иначе записать new_state + audit поля

    Возвращает GraphTransitionResult с подробной диагностикой.

    NB: ESM-матрица переходов проверяется на Python-стороне через
    `core.esm.validate_transition()`. Здесь — только I6 enforcement
    на graph-уровне. Полная защита = вызов validate_transition()
    в Python + вызов этой функции (которая делает финальный graph-check).
    """
    if not entity_uuid:
        return GraphTransitionResult(
            ok=False,
            entity_uuid="",
            previous_state=None,
            new_state=new_state,
            reason="missing_uuid",
        )

    if not isinstance(new_state, str) or not new_state.strip():
        return GraphTransitionResult(
            ok=False,
            entity_uuid=entity_uuid,
            previous_state=None,
            new_state=new_state,
            reason="invalid_new_state",
        )

    driver = graphiti.driver
    now = datetime.now(UTC).isoformat()

    try:
        result = await driver.execute_query(
            """
            MATCH (e:Entity {uuid: $uuid})
            WITH e,
                 coalesce(e.epistemic_state, 'Observed') AS prev_state,
                 coalesce(e.ring_zero, false) AS rz
            FOREACH (
                _ IN CASE WHEN rz = false THEN [1] ELSE [] END |
                SET e.epistemic_state = $new_state,
                    e.epistemic_state_updated_at = $now,
                    e.epistemic_state_updated_by = $by
            )
            RETURN prev_state AS prev_state,
                   rz AS ring_zero,
                   e.epistemic_state AS current_state
            """,
            uuid=entity_uuid,
            new_state=new_state,
            now=now,
            by=by,
        )
        if not result.records:
            return GraphTransitionResult(
                ok=False,
                entity_uuid=entity_uuid,
                previous_state=None,
                new_state=new_state,
                reason="not_found",
            )

        rec = result.records[0]
        ring_zero = bool(rec["ring_zero"])
        prev_state = rec["prev_state"]
        current_state = rec["current_state"]

        if ring_zero:
            return GraphTransitionResult(
                ok=False,
                entity_uuid=entity_uuid,
                previous_state=prev_state,
                new_state=new_state,
                reason="ring_zero_i6",
                blocked_by_ring_zero=True,
            )

        return GraphTransitionResult(
            ok=True,
            entity_uuid=entity_uuid,
            previous_state=prev_state,
            new_state=current_state,
            reason="ok",
        )
    except Exception as exc:  # noqa: BLE001
        logger.error(
            "safe_transition_entity_state failed for %s → %s: %s",
            entity_uuid, new_state, exc,
        )
        return GraphTransitionResult(
            ok=False,
            entity_uuid=entity_uuid,
            previous_state=None,
            new_state=new_state,
            reason=f"graph_error:{type(exc).__name__}",
        )


__all__ = [
    "GraphTransitionResult",
    "mark_ring_zero",
    "is_entity_ring_zero",
    "list_ring_zero_entities",
    "safe_transition_entity_state",
]
