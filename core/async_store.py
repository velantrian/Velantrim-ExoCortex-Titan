"""
🔄 core/async_store.py — Async SQLite Store (V8.7 Titan)

Опциональный async-обёртка над SQLiteGraphStore.
Включается через VELANTRIM_ASYNC_DB=1.

Для обратной совместимости все синхронные вызовы
оборачиваются в asyncio.to_thread() / run_in_executor.

Инвариант: те же данные, те же индексы, тот же WAL.
Изменяется ТОЛЬКО способ вызова — синхронный → async.
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional

import sqlite3

logger = logging.getLogger("velantrim.async_store")

# ─── Проверка доступности aiosqlite ──────────────────────────────────────────

_AIOSQLITE_AVAILABLE: Optional[bool] = None


def _check_aiosqlite() -> bool:
    global _AIOSQLITE_AVAILABLE
    if _AIOSQLITE_AVAILABLE is None:
        try:
            import aiosqlite  # noqa: F401
            _AIOSQLITE_AVAILABLE = True
        except ImportError:
            logger.info("aiosqlite не установлен — async будет через run_in_executor")
            _AIOSQLITE_AVAILABLE = False
    return _AIOSQLITE_AVAILABLE


def is_async_db_enabled() -> bool:
    """Читает VELANTRIM_ASYNC_DB из окружения."""
    raw = os.getenv("VELANTRIM_ASYNC_DB", "0").strip().lower()
    if raw in ("1", "true", "yes", "on"):
        if not _check_aiosqlite():
            logger.warning(
                "VELANTRIM_ASYNC_DB=1 но aiosqlite не установлен. "
                "Установи: pip install aiosqlite. Использую fallback."
            )
            return False
        return True
    return False


# ─── Async Wrapper ────────────────────────────────────────────────────────────


class AsyncSQLiteStore:
    """
    Async-обёртка над синхронным store.

    Два пути выполнения:
      1. aiosqlite (если VELANTRIM_ASYNC_DB=1 и пакет установлен)
      2. run_in_executor (fallback — синхронный sqlite3 в thread pool)

    Оба пути safe для FastAPI event loop.
    """

    def __init__(self, sync_store, use_native_async: Optional[bool] = None):
        """
        sync_store: экземпляр SQLiteGraphStore (или совместимый).
        use_native_async: None → автоопределение по ENV.
        """
        self._sync = sync_store
        self._native = (
            use_native_async if use_native_async is not None
            else is_async_db_enabled()
        )
        self._db_path = getattr(sync_store, "db_path", "./data/velantrim_house.db")
        logger.info(
            "AsyncSQLiteStore: native=%s path=%s", self._native, self._db_path
        )

    # ── Выполнитель ───────────────────────────────────────────────────────

    async def _run(self, sync_fn, *args, **kwargs):
        """
        Выполнить синхронную функцию без блокировки event loop.

        Если aiosqlite включён — использует нативное async-соединение.
        Иначе — run_in_executor (thread pool).
        """
        if self._native:
            return await self._aiosqlite_call(sync_fn.__name__, *args, **kwargs)
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: sync_fn(*args, **kwargs))

    async def _aiosqlite_call(self, method_name: str, *args, **kwargs):
        """Прямой вызов через aiosqlite (без run_in_executor)."""
        import aiosqlite

        async with aiosqlite.connect(self._db_path, timeout=30.0) as conn:
            conn.row_factory = sqlite3.Row
            await conn.execute("PRAGMA journal_mode=WAL")
            await conn.execute("PRAGMA busy_timeout=30000")

            if method_name == "store_fact":
                return await self._aiosqlite_store_fact(conn, *args, **kwargs)
            elif method_name == "get_fact":
                return await self._aiosqlite_get_fact(conn, *args, **kwargs)
            elif method_name == "get_all_facts":
                return await self._aiosqlite_get_all_facts(conn, *args, **kwargs)
            elif method_name == "store_facts_batch":
                return await self._aiosqlite_store_batch(conn, *args, **kwargs)
            else:
                # Неизвестный метод → fallback на run_in_executor
                loop = asyncio.get_event_loop()
                fn = getattr(self._sync, method_name)
                return await loop.run_in_executor(None, lambda: fn(*args, **kwargs))

    async def _aiosqlite_store_fact(self, conn, fact) -> None:
        # FIX P0: INSERT OR REPLACE в SQLite = DELETE + INSERT, что вызывает
        # ON DELETE CASCADE в таблице relations (миграция 008) → все рёбра факта
        # теряются при обновлении. Заменено на INSERT ... ON CONFLICT UPSERT.
        q = """
            INSERT INTO facts
                (fact_id, claim, source, confidence, epistemic_state,
                 created_at, updated_at, metadata, history,
                 t_event_valid_start, t_event_valid_end,
                 t_ingestion_start, t_ingestion_end)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(fact_id) DO UPDATE SET
                claim               = excluded.claim,
                source              = excluded.source,
                confidence          = excluded.confidence,
                epistemic_state     = excluded.epistemic_state,
                updated_at          = excluded.updated_at,
                metadata            = excluded.metadata,
                history             = excluded.history,
                t_event_valid_start = excluded.t_event_valid_start,
                t_event_valid_end   = excluded.t_event_valid_end,
                t_ingestion_start   = excluded.t_ingestion_start,
                t_ingestion_end     = excluded.t_ingestion_end
        """
        await conn.execute(q, (
            fact.get("fact_id"),
            fact.get("claim", ""),
            fact.get("source", ""),
            fact.get("confidence", 0.5),
            fact.get("epistemic_state", "Observed"),
            fact.get("created_at", ""),
            fact.get("updated_at", ""),
            fact.get("metadata", "{}"),
            fact.get("history", "[]"),
            fact.get("t_event_valid_start"),
            fact.get("t_event_valid_end"),
            fact.get("t_ingestion_start"),
            fact.get("t_ingestion_end"),
        ))
        await conn.commit()

    async def _aiosqlite_get_fact(self, conn, fact_id: str) -> Optional[Dict]:
        cur = await conn.execute(
            "SELECT * FROM facts WHERE fact_id = ?", (fact_id,)
        )
        row = await cur.fetchone()
        if row is None:
            return None
        return dict(row)

    async def _aiosqlite_get_all_facts(self, conn, epistemic_state=None):
        if epistemic_state:
            cur = await conn.execute(
                "SELECT * FROM facts WHERE epistemic_state = ?",
                (epistemic_state,),
            )
        else:
            cur = await conn.execute("SELECT * FROM facts")
        rows = await cur.fetchall()
        return [dict(r) for r in rows]

    async def _aiosqlite_store_batch(self, conn, facts: list) -> None:
        # FIX P0: INSERT OR REPLACE заменено на UPSERT (та же причина что в store_fact:
        # DELETE + INSERT → CASCADE удаляет relations).
        q = """
            INSERT INTO facts
                (fact_id, claim, source, confidence, epistemic_state,
                 created_at, updated_at, metadata, history,
                 t_event_valid_start, t_event_valid_end,
                 t_ingestion_start, t_ingestion_end)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(fact_id) DO UPDATE SET
                claim               = excluded.claim,
                source              = excluded.source,
                confidence          = excluded.confidence,
                epistemic_state     = excluded.epistemic_state,
                updated_at          = excluded.updated_at,
                metadata            = excluded.metadata,
                history             = excluded.history,
                t_event_valid_start = excluded.t_event_valid_start,
                t_event_valid_end   = excluded.t_event_valid_end,
                t_ingestion_start   = excluded.t_ingestion_start,
                t_ingestion_end     = excluded.t_ingestion_end
        """
        rows = [
            (
                f.get("fact_id"),
                f.get("claim", ""),
                f.get("source", ""),
                f.get("confidence", 0.5),
                f.get("epistemic_state", "Observed"),
                f.get("created_at", ""),
                f.get("updated_at", ""),
                f.get("metadata", "{}"),
                f.get("history", "[]"),
                f.get("t_event_valid_start"),
                f.get("t_event_valid_end"),
                f.get("t_ingestion_start"),
                f.get("t_ingestion_end"),
            )
            for f in facts
        ]
        await conn.executemany(q, rows)
        await conn.commit()

    # ── Публичный async API ───────────────────────────────────────────────

    async def store_fact(self, fact: Dict[str, Any]) -> None:
        """Асинхронно сохранить факт."""
        return await self._run(self._sync.store_fact, fact)

    async def get_fact(self, fact_id: str) -> Optional[Dict[str, Any]]:
        """Асинхронно получить факт по ID."""
        return await self._run(self._sync.get_fact, fact_id)

    async def get_all_facts(
        self, epistemic_state: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Асинхронно получить все факты."""
        return await self._run(self._sync.get_all_facts, epistemic_state)

    async def store_facts_batch(self, facts: List[Dict[str, Any]]) -> None:
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

    Если sync_store=None → создаётся из get_store() (DI + fallback).
    """
    if sync_store is None:
        from core.memory import get_store

        sync_store = get_store()
    return AsyncSQLiteStore(sync_store, use_native_async=use_native)


__all__ = [
    "AsyncSQLiteStore",
    "create_async_store",
    "is_async_db_enabled",
]
