"""FastAPI-owned polling for the existing local FTS projection dispatcher."""

from __future__ import annotations

import asyncio
import logging
import os
import sqlite3
import threading
import time
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from core.projection_dispatcher import dispatch_once

_logger = logging.getLogger(__name__)
_POLL_SECONDS = 1.0
_STALE_SECONDS = 10.0
_PASS_SECONDS = 3.0
_SQLITE_TIMEOUT_SECONDS = 0.2
_BATCH_SIZE = 8
_LEASE_SECONDS = 30
_COUNT_LIMIT = 1001


def projection_dispatch_enabled() -> bool:
    return os.getenv("VELANTRIM_PROJECTION_DISPATCH_ENABLED", "false").strip().lower() == "true"


class ProjectionDispatchRuntime:
    """Own one poll task and its content-free, process-local diagnostics."""

    def __init__(self, db_path: Path) -> None:
        self._db_uri = f"{db_path.resolve().as_uri()}?mode=rw"
        self._wake = asyncio.Event()
        self._interrupt = threading.Event()
        self._task: asyncio.Task[None] | None = None
        self._started_at = time.monotonic()
        self._last_success: float | None = None
        self._last_success_at: str | None = None
        self._consecutive_errors = 0
        self._last_pass: dict[str, Any] = {}

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._db_uri, uri=True, timeout=_SQLITE_TIMEOUT_SECONDS)

    def _verify_schema(self) -> None:
        required = {"projection_outbox", "projection_checkpoints", "projection_dispatch_state",
                    "facts_fts"}
        with closing(self._connect()) as conn:
            version = conn.execute("PRAGMA user_version").fetchone()[0]
            tables = {
                row[0] for row in conn.execute(
                    "SELECT name FROM sqlite_schema WHERE type = 'table' "
                    "AND name IN ('projection_outbox', 'projection_checkpoints', "
                    "'projection_dispatch_state', 'facts_fts')"
                )
            }
            if version < 22 or tables != required:
                raise RuntimeError("Projection dispatch requires migrations 020–022 and facts_fts")
            conn.execute("SELECT rowid FROM facts_fts LIMIT 0").fetchall()

    async def start(self) -> None:
        await asyncio.to_thread(self._verify_schema)
        self._started_at = time.monotonic()
        self._task = asyncio.create_task(self._run(), name="projection-dispatch")

    async def stop(self) -> None:
        self._interrupt.set()
        self._wake.set()
        if self._task is not None:
            await asyncio.shield(self._task)

    def _poll(self) -> dict[str, Any]:
        deadline = time.monotonic() + _PASS_SECONDS
        with closing(self._connect()) as conn:
            conn.set_progress_handler(
                lambda: int(self._interrupt.is_set() or time.monotonic() >= deadline), 1000,
            )
            summary = dispatch_once(
                conn, batch_size=_BATCH_SIZE, lease_duration_seconds=_LEASE_SECONDS,
                clock=lambda: datetime.now(UTC),
            )
            pending, oldest = conn.execute(
                "SELECT count(*), CAST(MAX(0, (julianday('now') - julianday(MIN(created_at))) "
                "* 86400) AS INTEGER) FROM ("
                "SELECT po.created_at FROM projection_outbox po "
                "LEFT JOIN projection_dispatch_state ds ON po.outbox_id = ds.outbox_id "
                "WHERE ds.lifecycle_state IS NULL OR ds.lifecycle_state IN ('leased', 'retry') "
                "ORDER BY po.created_at, po.outbox_id LIMIT ?)",
                (_COUNT_LIMIT,),
            ).fetchone()
            parked = conn.execute(
                "SELECT count(*) FROM (SELECT 1 FROM projection_dispatch_state "
                "WHERE lifecycle_state = 'parked' LIMIT ?)", (_COUNT_LIMIT,),
            ).fetchone()[0]
        return {
            "pending": pending,
            "parked": parked,
            "oldest_pending_age_seconds": oldest,
            "last_batch": {
                "claimed": summary.claimed,
                "acknowledged": summary.acknowledged,
                "retried": summary.retried,
                "parked": summary.parked,
                "rejected": summary.rejected,
            },
        }

    async def _run(self) -> None:
        while not self._interrupt.is_set():
            try:
                self._last_pass = await asyncio.to_thread(self._poll)
            except Exception as exc:
                if self._interrupt.is_set():
                    break
                self._consecutive_errors += 1
                if self._consecutive_errors == 1 or self._consecutive_errors % 60 == 0:
                    _logger.warning("Projection dispatch poll failed (%s)", type(exc).__name__)
            else:
                self._last_success = time.monotonic()
                self._last_success_at = datetime.now(UTC).isoformat()
                self._consecutive_errors = 0

            try:
                await asyncio.wait_for(self._wake.wait(), timeout=_POLL_SECONDS)
            except TimeoutError:
                pass

    def diagnostics(self) -> dict[str, Any]:
        if self._task is not None and self._task.done():
            status = "stopped" if self._interrupt.is_set() else "degraded"
        elif (
            self._consecutive_errors
            or time.monotonic() - (self._last_success or self._started_at) > _STALE_SECONDS
        ):
            status = "degraded"
        else:
            status = "starting" if self._last_success is None else "running"

        return {
            "status": status,
            "last_success_at": self._last_success_at,
            "consecutive_errors": self._consecutive_errors,
            "count_limit": _COUNT_LIMIT,
            "pending": None,
            "parked": None,
            "oldest_pending_age_seconds": None,
            "last_batch": None,
            **self._last_pass,
        }
