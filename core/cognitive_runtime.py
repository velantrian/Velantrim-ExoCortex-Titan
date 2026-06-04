"""
Unified Cognitive Runtime — V10 MVP (V1).

Единая точка write/read поверх CognitiveFactStore + EventBus-подписчики
для инвалидации производных индексов (hybrid retriever и др.).
"""

from __future__ import annotations

import builtins
import logging
from typing import Any

from core.cognitive_fact import CognitiveFact

logger = logging.getLogger(__name__)

_runtime: CognitiveRuntime | None = None
_handlers_registered = False


def is_cognitive_runtime_enabled() -> bool:
    from core.feature_config import get_config

    cfg = get_config().app
    return bool(cfg.enable_cognitive_runtime and cfg.enable_cognitive_store)


class CognitiveRuntime:
    """Фасад V10: store + события + подписчики."""

    def write(
        self,
        fact: CognitiveFact | dict[str, Any],
        *,
        ensure_raw: bool = True,
        link_provenance: bool = True,
    ) -> bool:
        from core.cognitive_fact import cognitive_fact_from_store
        from core.cognitive_store import get_cognitive_store

        if isinstance(fact, CognitiveFact):
            cf = fact
        else:
            cf = cognitive_fact_from_store(
                fact,
                raw_input=fact.get("raw_input") or fact.get("claim"),
            )
            if fact.get("derived_from"):
                cf.derived_from = str(fact["derived_from"])
        return get_cognitive_store().save(
            cf,
            ensure_raw=ensure_raw and not cf.derived_from,
            link_provenance=link_provenance,
        )

    def read(
        self,
        fact_id: str,
        *,
        include_relations: bool = False,
        include_raw: bool = True,
    ) -> CognitiveFact | None:
        from core.cognitive_store import get_cognitive_store

        return get_cognitive_store().get(
            fact_id,
            include_relations=include_relations,
            include_raw=include_raw,
        )

    def list(
        self,
        *,
        epistemic_state: str | None = None,
        domain: str | None = None,
        include_relations: bool = False,
    ) -> builtins.list[CognitiveFact]:
        from core.cognitive_store import get_cognitive_store

        return get_cognitive_store().list(
            epistemic_state=epistemic_state,
            domain=domain,
            include_relations=include_relations,
            include_raw=False,
        )

    def transition(
        self,
        fact_id: str,
        new_state: str,
        *,
        by: str = "cognitive_runtime",
    ) -> CognitiveFact | None:
        from core.cognitive_store import get_cognitive_store

        return get_cognitive_store().transition(fact_id, new_state, by=by)

    def status(self) -> dict[str, Any]:
        from core.cognitive_store import is_cognitive_store_enabled
        from core.event_bus import get_event_bus
        from core.runtime_flags import is_event_bus_enabled

        bus = get_event_bus() if is_event_bus_enabled() else None
        metrics = bus.get_metrics() if bus else None
        return {
            "enabled": is_cognitive_runtime_enabled(),
            "cognitive_store": is_cognitive_store_enabled(),
            "event_bus": is_event_bus_enabled(),
            "handlers_registered": _handlers_registered,
            "event_bus_metrics": (
                {
                    "published_total": metrics.published_total,
                    "consumed_total": metrics.consumed_total,
                    "queue_size": metrics.size,
                }
                if metrics
                else None
            ),
        }


async def _on_fact_changed(event: dict[str, Any]) -> None:
    """Slow path: инвалидация retriever + инкрементальный NGram."""
    payload = event.get("payload") or {}
    fact_id = payload.get("fact_id")

    try:
        from core.pipeline import mark_retriever_dirty

        mark_retriever_dirty()
    except Exception as exc:  # noqa: BLE001
        logger.debug("runtime mark_retriever_dirty: %s", exc)

    if fact_id:
        try:
            from core.memory import get_fact
            from core.ngram_index import ngram_index_fact, ngram_remove_fact

            fact = get_fact(str(fact_id))
            if fact:
                claim = str(fact.get("claim") or "")
                etype = event.get("type", "")
                if etype == "fact_esm_transition" and str(
                    fact.get("epistemic_state", "")
                ).lower() in ("collapsed", "deprecated"):
                    ngram_remove_fact(str(fact_id))
                elif claim:
                    ngram_index_fact(str(fact_id), claim)
        except Exception as exc:  # noqa: BLE001
            logger.debug("runtime ngram index: %s", exc)
        logger.debug("CognitiveRuntime: fact event %s %s", event.get("type"), fact_id)


def register_cognitive_runtime_handlers() -> None:
    """Подписать fact_* → mark_retriever_dirty (идемпотентно)."""
    global _handlers_registered

    if _handlers_registered:
        return
    if not is_cognitive_runtime_enabled():
        return
    from core.runtime_flags import is_event_bus_enabled

    if not is_event_bus_enabled():
        logger.debug("CognitiveRuntime: EventBus выключен — handlers пропущены")
        return

    from core.event_bus import get_event_bus

    bus = get_event_bus()
    for etype in ("fact_created", "fact_updated", "fact_esm_transition"):
        bus.subscribe(etype, _on_fact_changed)
    _handlers_registered = True
    logger.info("CognitiveRuntime: подписчики fact_* зарегистрированы")


def reset_cognitive_runtime() -> None:
    global _runtime, _handlers_registered
    _runtime = None
    _handlers_registered = False


def get_cognitive_runtime() -> CognitiveRuntime:
    global _runtime
    if _runtime is None:
        _runtime = CognitiveRuntime()
    return _runtime


__all__ = [
    "CognitiveRuntime",
    "get_cognitive_runtime",
    "is_cognitive_runtime_enabled",
    "register_cognitive_runtime_handlers",
    "reset_cognitive_runtime",
]
