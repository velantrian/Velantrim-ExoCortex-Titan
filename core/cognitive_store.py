"""
CognitiveFactStore v9.2–9.3 — единая запись/чтение через CognitiveFact.

Делегирует persistence в core.memory (SQLite L1 + L0); не ломает store_fact().
"""

from __future__ import annotations

import builtins
import logging
import uuid
from typing import Any

from core.cognitive_fact import (
    CognitiveFact,
    cognitive_fact_from_store,
    load_relations_for_fact,
)

logger = logging.getLogger(__name__)

_store: CognitiveFactStore | None = None


def is_cognitive_store_enabled() -> bool:
    from core.feature_config import get_config

    return get_config().app.enable_cognitive_store


class CognitiveFactStore:
    """Фасад read/write для CognitiveFact поверх L1/L0."""

    def save(
        self,
        fact: CognitiveFact,
        *,
        ensure_raw: bool = True,
        link_provenance: bool = True,
    ) -> bool:
        """
        Сохранить факт. Возвращает True если был новый INSERT.

        Если ensure_raw и есть raw_input без derived_from — создаёт L0 запись.
        """
        from core.memory import link_raw_to_fact, store_fact, store_raw_text

        if ensure_raw and fact.raw_input and not fact.derived_from:
            fact.derived_from = store_raw_text(
                fact.raw_input,
                source=fact.source,
                source_type=str(fact.metadata.get("source_type", "cognitive_store")),
            )

        payload = fact.to_store_dict()
        is_new = store_fact(payload)

        if link_provenance and fact.derived_from:
            try:
                link_raw_to_fact(fact.derived_from, fact.id)
            except Exception as exc:  # noqa: BLE001
                logger.debug("cognitive_store link_raw: %s", exc)

        _emit_fact_event(fact.id, is_new=is_new)
        return is_new

    def save_many(self, facts: builtins.list[CognitiveFact]) -> dict[str, int]:
        from core.memory import store_facts_batch

        payloads = [f.to_store_dict() for f in facts]
        stats = store_facts_batch(payloads)
        for f in facts:
            _emit_fact_event(f.id, is_new=False)
        return stats

    def get(
        self,
        fact_id: str,
        *,
        include_relations: bool = False,
        include_raw: bool = True,
    ) -> CognitiveFact | None:
        from core.memory import get_fact

        row = get_fact(fact_id)
        if not row:
            return None
        return self._hydrate(row, include_relations=include_relations, include_raw=include_raw)

    def list(
        self,
        *,
        epistemic_state: str | None = None,
        domain: str | None = None,
        include_relations: bool = False,
        include_raw: bool = False,
    ) -> builtins.list[CognitiveFact]:
        from core.memory import get_all_facts

        rows = get_all_facts(epistemic_state, domain=domain)
        return [
            self._hydrate(
                r,
                include_relations=include_relations,
                include_raw=include_raw,
            )
            for r in rows
        ]

    def transition(
        self,
        fact_id: str,
        new_state: str,
        *,
        by: str = "cognitive_store",
    ) -> CognitiveFact | None:
        from core.memory import promote_esm_to

        promote_esm_to(fact_id, new_state, by=by)
        _emit_fact_event(fact_id, is_new=False, event_type="fact_esm_transition")
        return self.get(fact_id)

    @staticmethod
    def create_observed(
        claim: str,
        source: str,
        *,
        fact_id: str | None = None,
        confidence: float = 0.8,
        metadata: dict[str, Any] | None = None,
        raw_input: str | None = None,
        derived_from: str | None = None,
    ) -> CognitiveFact:
        """Фабрика нового Observed-факта."""
        fid = fact_id or f"fact_{uuid.uuid4().hex[:12]}"
        meta = dict(metadata or {})
        return CognitiveFact(
            id=fid,
            canonical_text=claim.strip(),
            source=source.strip(),
            epistemic_state="Observed",
            confidence=confidence,
            metadata=meta,
            raw_input=raw_input or claim.strip(),
            derived_from=derived_from,
        )

    def _hydrate(
        self,
        row: dict[str, Any],
        *,
        include_relations: bool,
        include_raw: bool,
    ) -> CognitiveFact:
        raw_text: str | None = None
        if include_raw:
            raw_text = _load_raw_input(str(row.get("fact_id", "")), row.get("derived_from"))
        rels = (
            load_relations_for_fact(str(row.get("fact_id", "")))
            if include_relations
            else []
        )
        return cognitive_fact_from_store(
            row,
            raw_input=raw_text,
            relations=rels,
        )


def _load_raw_input(fact_id: str, derived_from: str | None) -> str | None:
    try:
        from core.memory import get_raw_text_for_fact

        text = get_raw_text_for_fact(fact_id)
        if text:
            return text
        if derived_from:
            from core.memory import _GLOBAL_STORE

            with _GLOBAL_STORE._db() as conn:
                row = conn.execute(
                    "SELECT original_text FROM l0_raw_memory WHERE raw_id = ?",
                    (derived_from,),
                ).fetchone()
                if row:
                    return row[0]
    except Exception as exc:  # noqa: BLE001
        logger.debug("load raw_input: %s", exc)
    return None


def _emit_fact_event(
    fact_id: str,
    *,
    is_new: bool,
    event_type: str | None = None,
) -> None:
    try:
        from core.runtime_flags import is_event_bus_enabled

        if not is_event_bus_enabled():
            return
        from core.async_utils import run_coroutine_sync
        from core.event_bridge import publish_event

        etype = event_type or ("fact_created" if is_new else "fact_updated")
        run_coroutine_sync(
            publish_event(
                etype,
                {"fact_id": fact_id, "via": "cognitive_store", "is_new": is_new},
            )
        )
    except Exception as exc:  # noqa: BLE001
        logger.debug("cognitive_store event: %s", exc)


def get_cognitive_store() -> CognitiveFactStore:
    global _store
    if _store is None:
        _store = CognitiveFactStore()
    return _store


def reset_cognitive_store() -> None:
    global _store
    _store = None


def save_fact_dict(
    fact: dict[str, Any],
    *,
    ensure_raw: bool = True,
    link_provenance: bool = True,
) -> bool:
    """
    Единая точка записи L1: CognitiveFactStore или legacy store_fact.

    Используется Telegram, Umwelt sync и другими ingest-путями.
    """
    if is_cognitive_store_enabled():
        from core.cognitive_fact import cognitive_fact_from_store
        from core.cognitive_runtime import get_cognitive_runtime, is_cognitive_runtime_enabled

        if is_cognitive_runtime_enabled():
            return get_cognitive_runtime().write(
                fact,
                ensure_raw=ensure_raw,
                link_provenance=link_provenance,
            )

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

    from core.memory import store_fact

    return store_fact(fact)


__all__ = [
    "CognitiveFactStore",
    "get_cognitive_store",
    "is_cognitive_store_enabled",
    "reset_cognitive_store",
    "save_fact_dict",
]
