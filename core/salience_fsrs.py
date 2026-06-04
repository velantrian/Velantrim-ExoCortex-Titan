"""
Salience + FSRS защита (#26).

Узлы/рёбра с высоким salience_weight ослабляются медленнее или
не затрагиваются batch decay (RFC0016 + RFC0017).
"""

from __future__ import annotations

import logging
from collections.abc import Iterable

from core.feature_config import get_config

logger = logging.getLogger(__name__)


def protect_threshold() -> float:
    return float(get_config().app.salience_fsrs_protect_threshold)


def should_protect_from_decay(salience_weight: float) -> bool:
    """True → пропустить FSRS decay для synapse/entity."""
    if not salience_weight:
        return False
    return float(salience_weight) >= protect_threshold()


def effective_decay_weight(
    old_weight: float,
    new_weight: float,
    salience_weight: float,
) -> float:
    """
    При высоком salience сохраняем старый вес (полная защита).
    Иначе — стандартный decayed new_weight.
    """
    if should_protect_from_decay(salience_weight):
        return old_weight
    return new_weight


async def persist_entity_salience(
    graphiti,
    entity_names: Iterable[str],
    salience_weight: float,
) -> int:
    """
    Поднять salience_weight на Entity в Neo4j (max с текущим).
    """
    if graphiti is None or not entity_names:
        return 0

    driver = getattr(graphiti, "driver", None) or getattr(graphiti, "_driver", None)
    if not driver:
        return 0

    names = [n.strip() for n in entity_names if isinstance(n, str) and n.strip()]
    if not names:
        return 0

    protected = should_protect_from_decay(salience_weight)
    try:
        res = await driver.execute_query(
            """
            UNWIND $names AS nm
            MATCH (e:Entity {name: nm})
            SET e.salience_weight = CASE
                WHEN e.salience_weight IS NULL THEN $sw
                ELSE CASE WHEN $sw > e.salience_weight THEN $sw ELSE e.salience_weight END
            END,
            e.salience_fsrs_protected = $protected
            RETURN count(e) AS updated
            """,
            names=names,
            sw=float(salience_weight),
            protected=protected,
        )
        if res.records:
            return int(res.records[0].get("updated") or 0)
    except Exception as exc:  # noqa: BLE001
        logger.debug("persist_entity_salience: %s", exc)
    return 0


__all__ = [
    "effective_decay_weight",
    "persist_entity_salience",
    "protect_threshold",
    "should_protect_from_decay",
]
