"""
🔗 core/index_coordinator.py — Index Coordinator (V8.7 Titan)

Координирует derived NGramIndex (FTS5) и HybridRetriever (BM25+Dense).
Координатор не является Canon/write owner и сам не подключён к runtime write path.

Инварианты:
- NGram и Hybrid остаются derived/rebuildable projections;
- ошибки NGram не отменяют canonical write и не скрываются как healthy status;
- Hybrid dirty отмечается независимо от NGram outcome;
- этот модуль не добавляет runtime wiring сам по себе.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("velantrim.index_coordinator")


class IndexCoordinator:
    """Bounded coordinator for derived NGram + Hybrid projection freshness."""

    def __init__(self):
        self._ngram = None
        self._hybrid_dirty = True
        self._ngram_degraded = False
        self._last_ngram_error: Optional[str] = None

    def set_ngram(self, ngram) -> None:
        """Attach/replace the derived NGram surface and reset its health snapshot."""
        self._ngram = ngram
        self._ngram_degraded = False
        self._last_ngram_error = None

    def _mark_ngram_healthy(self) -> None:
        self._ngram_degraded = False
        self._last_ngram_error = None

    def _mark_ngram_degraded(self, operation: str, exc: Exception) -> None:
        error_class = type(exc).__name__
        self._ngram_degraded = True
        self._last_ngram_error = error_class
        # Keep diagnostics content-free: exception type is enough for this derived surface.
        logger.warning("NGram %s degraded: %s", operation, error_class)

    def on_store_fact(self, fact: Dict[str, Any]) -> None:
        """Update the attached derived NGram projection after a fact store event."""
        if self._ngram is not None:
            try:
                self._ngram.index(
                    fact.get("fact_id", ""),
                    fact.get("claim", ""),
                )
            except Exception as exc:
                self._mark_ngram_degraded("index", exc)
            else:
                self._mark_ngram_healthy()

        self._hybrid_dirty = True

    def on_store_batch(self, facts: List[Dict[str, Any]]) -> None:
        """Best-effort derived indexing for a batch; any failure remains observable."""
        batch_failed = False
        last_error: Exception | None = None

        if self._ngram is not None:
            for fact in facts:
                try:
                    self._ngram.index(
                        fact.get("fact_id", ""),
                        fact.get("claim", ""),
                    )
                except Exception as exc:
                    batch_failed = True
                    last_error = exc
                    logger.warning(
                        "NGram batch index item degraded: %s",
                        type(exc).__name__,
                    )

            if batch_failed and last_error is not None:
                self._ngram_degraded = True
                self._last_ngram_error = type(last_error).__name__
            else:
                self._mark_ngram_healthy()

        self._hybrid_dirty = True

    def on_delete_fact(self, fact_id: str) -> None:
        """Remove a fact from the attached derived NGram projection."""
        if self._ngram is not None:
            try:
                self._ngram.remove(fact_id)
            except Exception as exc:
                self._mark_ngram_degraded("remove", exc)
            else:
                self._mark_ngram_healthy()
        self._hybrid_dirty = True

    @property
    def is_hybrid_dirty(self) -> bool:
        return self._hybrid_dirty

    def mark_hybrid_clean(self) -> None:
        self._hybrid_dirty = False

    def status(self) -> Dict[str, Any]:
        return {
            "ngram_available": self._ngram is not None,
            "ngram_degraded": self._ngram_degraded,
            "last_ngram_error": self._last_ngram_error,
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


# ─── Dormant compatibility hooks ─────────────────────────────────────────────

def hook_store_fact(fact: Dict[str, Any]) -> None:
    """Forward to the coordinator if an explicit caller chooses this hook."""
    get_index_coordinator().on_store_fact(fact)


def hook_store_batch(facts: List[Dict[str, Any]]) -> None:
    """Forward a batch if an explicit caller chooses this hook."""
    get_index_coordinator().on_store_batch(facts)


__all__ = [
    "IndexCoordinator",
    "get_index_coordinator",
    "reset_index_coordinator",
    "hook_store_fact",
    "hook_store_batch",
]
