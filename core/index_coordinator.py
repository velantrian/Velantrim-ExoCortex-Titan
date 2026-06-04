"""
🔗 core/index_coordinator.py — Index Coordinator (V8.7 Titan)

Гарантирует консистентность между NGramIndex (FTS5) и HybridRetriever (BM25+Dense).
При store_fact() атомарно обновляет оба индекса.

До V8.7: факт мог попасть в FTS5 но не в BM25 (или наоборот) → pre-filter
пропускал релевантный факт, который BM25 мог бы найти.

Инвариант: координатор не хранит содержимое — только синхронизирует индексы.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("velantrim.index_coordinator")


class IndexCoordinator:
    """
    Единый координатор индексов: NGram + Hybrid.

    При store_fact():
      1. Обновить NGram (FTS5)
      2. Пометить Hybrid как dirty → пересборка при следующем retrieve
      3. Опционально: записать метрику в EventBus
    """

    def __init__(self):
        self._ngram = None
        self._hybrid_dirty = True

    def set_ngram(self, ngram) -> None:
        self._ngram = ngram

    def on_store_fact(self, fact: Dict[str, Any]) -> None:
        """Вызвать после каждого store_fact()."""
        # 1. NGram — индексировать новый факт
        if self._ngram is not None:
            try:
                self._ngram.index_fact(
                    fact.get("fact_id", ""),
                    fact.get("claim", ""),
                )
            except Exception:
                logger.debug("NGram index_fact failed (graceful)")

        # 2. Hybrid — пометить грязным
        self._hybrid_dirty = True

    def on_store_batch(self, facts: List[Dict[str, Any]]) -> None:
        """Вызвать после store_facts_batch()."""
        if self._ngram is not None:
            try:
                for f in facts:
                    self._ngram.index_fact(
                        f.get("fact_id", ""),
                        f.get("claim", ""),
                    )
            except Exception:
                logger.debug("NGram batch index failed (graceful)")

        self._hybrid_dirty = True

    def on_delete_fact(self, fact_id: str) -> None:
        """Вызвать при удалении факта."""
        if self._ngram is not None:
            try:
                self._ngram.remove_fact(fact_id)
            except Exception:
                pass
        self._hybrid_dirty = True

    @property
    def is_hybrid_dirty(self) -> bool:
        return self._hybrid_dirty

    def mark_hybrid_clean(self) -> None:
        self._hybrid_dirty = False

    def status(self) -> Dict[str, Any]:
        return {
            "ngram_available": self._ngram is not None,
            "hybrid_dirty": self._hybrid_dirty,
        }


# ─── Глобальный координатор ──────────────────────────────────────────────────

_coordinator: Optional[IndexCoordinator] = None


def get_index_coordinator() -> IndexCoordinator:
    global _coordinator
    if _coordinator is None:
        _coordinator = IndexCoordinator()
    return _coordinator


def reset_index_coordinator() -> None:
    global _coordinator
    _coordinator = None


# ─── Хук для store_fact ──────────────────────────────────────────────────────

def hook_store_fact(fact: Dict[str, Any]) -> None:
    """Вызвать в store_fact() для синхронизации индексов."""
    get_index_coordinator().on_store_fact(fact)


def hook_store_batch(facts: List[Dict[str, Any]]) -> None:
    """Вызвать в store_facts_batch() для синхронизации."""
    get_index_coordinator().on_store_batch(facts)


__all__ = [
    "IndexCoordinator",
    "get_index_coordinator",
    "reset_index_coordinator",
    "hook_store_fact",
    "hook_store_batch",
]
