"""
🔄 core/async_store.py — canonical async adapter (Titan P0 / issue #50)

Async is an execution adapter over SQLiteGraphStore, never an independent
SQL implementation. Every mutation runs the exact synchronous canonical
method in a worker thread, so WriteProtocolGate, ESM/CAS checks, VersionStore,
AuditChain, migrations, cache publication, and rollback semantics cannot
diverge between sync and async entry points.

The former VELANTRIM_ASYNC_DB=1 "native aiosqlite" path duplicated a subset
of store_fact SQL and bypassed those invariants. It is deliberately disabled
until a native implementation can prove observable equivalence at the same
canonical protocol boundary.
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger("velantrim.async_store")

def is_async_db_enabled() -> bool:
    """Return whether the removed native-SQL path is enabled.

    Always False by design. The environment variable is retained only as a
    migration signal so existing deployments receive an explicit warning
    instead of silently believing they are on an equivalent aiosqlite path.
    AsyncSQLiteStore itself remains fully asynchronous to callers via
    ``asyncio.to_thread``.
    """
    raw = os.getenv("VELANTRIM_ASYNC_DB", "0").strip().lower()
    if raw in ("1", "true", "yes", "on"):
        logger.warning(
            "VELANTRIM_ASYNC_DB is ignored: native aiosqlite writes are "
            "disabled until they satisfy canonical write equivalence; "
            "using the thread-backed canonical adapter"
        )
    return False


# ─── Async Wrapper ────────────────────────────────────────────────────────────


class AsyncSQLiteStore:
    """
    Async façade over one canonical synchronous store.

    ``use_native_async`` remains in the constructor for source compatibility,
    but cannot enable a second write implementation. Cancellation of the
    awaiting coroutine does not cancel a SQLite transaction halfway through:
    the worker finishes according to the synchronous store's commit/rollback
    contract, and a later read observes one complete outcome.
    """

    def __init__(self, sync_store, use_native_async: Optional[bool] = None):
        """
        sync_store: экземпляр SQLiteGraphStore (или совместимый).
        use_native_async: deprecated compatibility argument; ignored.
        """
        self._sync = sync_store
        requested_native = (
            use_native_async if use_native_async is not None
            else is_async_db_enabled()
        )
        self._native = False
        self._db_path = getattr(sync_store, "db_path", "./data/velantrim.db")
        if requested_native:
            logger.warning(
                "use_native_async=True is ignored; canonical thread adapter is enforced"
            )
        logger.info(
            "AsyncSQLiteStore: canonical_adapter=true native=false path=%s",
            self._db_path,
        )

    # ── Выполнитель ───────────────────────────────────────────────────────

    async def _run(self, sync_fn, *args, **kwargs):
        """Run one canonical sync operation without blocking the event loop."""
        return await asyncio.to_thread(sync_fn, *args, **kwargs)

    # ── Публичный async API ───────────────────────────────────────────────

    async def store_fact(self, fact: Dict[str, Any]) -> bool:
        """Store through SQLiteGraphStore.store_fact() with identical result."""
        return await self._run(self._sync.store_fact, fact)

    async def store_fact_result(self, fact: Dict[str, Any]):
        """Structured non-raising counterpart with the sync result contract."""
        return await self._run(self._sync.store_fact_result, fact)

    async def get_fact(self, fact_id: str) -> Optional[Dict[str, Any]]:
        """Асинхронно получить факт по ID."""
        return await self._run(self._sync.get_fact, fact_id)

    async def get_all_facts(
        self, epistemic_state: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Асинхронно получить все факты."""
        return await self._run(self._sync.get_all_facts, epistemic_state)

    async def store_facts_batch(self, facts: List[Dict[str, Any]]) -> Dict[str, int]:
        """Асинхронно сохранить пачку фактов (одна транзакция)."""
        return await self._run(self._sync.store_facts_batch, facts)

    async def update_state(
        self,
        fact_id: str,
        new_state: str,
        history_entry: Dict[str, Any],
        now: str,
    ) -> bool:
        """Асинхронно обновить эпистемическое состояние."""
        return await self._run(
            self._sync.update_state, fact_id, new_state, history_entry, now
        )

    async def transition_esm(
        self,
        fact_id: str,
        new_state: str,
        by: str = "transition_esm",
    ) -> bool:
        """Run the canonical ESM legality/CAS/version/audit path."""
        return await self._run(self._sync.transition_esm, fact_id, new_state, by)

    async def invalidate_edge(
        self,
        fact_id: str,
        t_event_valid_end: str | None = None,
        t_ingestion_end: str | None = None,
    ) -> bool:
        """Run canonical temporal invalidation with the sync semantics."""
        return await self._run(
            self._sync.invalidate_edge,
            fact_id,
            t_event_valid_end,
            t_ingestion_end,
        )

    async def set_restricted(self, fact_id: str, restricted: bool) -> bool:
        """Run the canonical processing-restriction mutation."""
        return await self._run(self._sync.set_restricted, fact_id, restricted)

    async def close(self) -> None:
        """Закрыть соединение (идемпотентный)."""
        return await self._run(self._sync.close)


# ─── Фабрика ─────────────────────────────────────────────────────────────────

def create_async_store(
    sync_store=None,
    *,
    use_native: Optional[bool] = None,
) -> AsyncSQLiteStore:
    """
    Создать async-обёртку над хранилищем.

    Если sync_store=None → создаётся из _GLOBAL_STORE (обратная совместимость).
    """
    if sync_store is None:
        from core.memory import _GLOBAL_STORE
        sync_store = _GLOBAL_STORE
    return AsyncSQLiteStore(sync_store, use_native_async=use_native)


__all__ = [
    "AsyncSQLiteStore",
    "create_async_store",
    "is_async_db_enabled",
]
