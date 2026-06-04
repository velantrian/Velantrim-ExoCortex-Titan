"""
EventBus — асинхронная шина Slow Path (Velantrim V8.6 Complex).
"""

from __future__ import annotations

import asyncio
import logging
from collections import deque
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from core.feature_config import get_config


def is_event_bus_enabled() -> bool:
    return get_config().app.enable_event_bus


def use_event_bus_background() -> bool:
    return get_config().app.enable_event_bus and get_config().app.enable_event_bus_background

logger = logging.getLogger(__name__)

MAX_QUEUE_SIZE = 10_000
DLQ_MAX_SIZE = 1_000
DEFAULT_PUBLISH_TIMEOUT = 30.0

EventHandler = Callable[[dict[str, Any]], Awaitable[None]]


@dataclass
class QueueMetrics:
    size: int
    peak_size: int
    overflow_count: int
    dlq_size: int
    published_total: int
    consumed_total: int


@dataclass
class EventBus:
    max_queue_size: int = MAX_QUEUE_SIZE
    dlq_max_size: int = DLQ_MAX_SIZE
    _queue: deque[dict[str, Any]] = field(default_factory=deque)
    _dlq: deque[dict[str, Any]] = field(default_factory=deque)
    _handlers: dict[str, list[EventHandler]] = field(default_factory=dict)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    _not_full: asyncio.Condition | None = None
    peak_size: int = 0
    overflow_count: int = 0
    published_total: int = 0
    consumed_total: int = 0

    def __post_init__(self) -> None:
        self._not_full = asyncio.Condition(self._lock)

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    async def publish(
        self,
        event: dict[str, Any],
        *,
        timeout_sec: float = DEFAULT_PUBLISH_TIMEOUT,
        dispatch: bool = True,
    ) -> bool:
        if not event.get("type"):
            return False

        enriched = dict(event)
        enriched.setdefault("_enqueued_at", datetime.now(UTC).isoformat())

        async with self._not_full:  # type: ignore[union-attr]
            start = datetime.now(UTC)
            while len(self._queue) >= self.max_queue_size:
                elapsed = (datetime.now(UTC) - start).total_seconds()
                if elapsed > timeout_sec:
                    self.overflow_count += 1
                    return False
                try:
                    await asyncio.wait_for(
                        self._not_full.wait(),  # type: ignore[union-attr]
                        timeout=max(0.01, timeout_sec - elapsed),
                    )
                except TimeoutError:
                    self.overflow_count += 1
                    return False

            if not dispatch:
                self._queue.append(enriched)
                self.peak_size = max(self.peak_size, len(self._queue))
            self.published_total += 1
            self._not_full.notify_all()  # type: ignore[union-attr]

        if dispatch:
            await self._dispatch(enriched)
        return True

    async def _dispatch(self, event: dict[str, Any]) -> None:
        event_type = event.get("type", "")
        handlers = list(self._handlers.get(event_type, []))
        handlers.extend(self._handlers.get("*", []))
        for handler in handlers:
            try:
                await handler(event)
            except Exception as exc:  # noqa: BLE001
                await self.handle_failure(event, exc)
        async with self._lock:
            self.consumed_total += 1

    async def handle_failure(self, event: dict[str, Any], error: Exception) -> None:
        failed = dict(event)
        failed["_failed_at"] = datetime.now(UTC).isoformat()
        failed["_error"] = str(error)
        failed["_retry_count"] = int(failed.get("_retry_count", 0)) + 1
        if failed["_retry_count"] <= 3:
            async with self._lock:
                if len(self._dlq) >= self.dlq_max_size:
                    self._dlq.popleft()
                self._dlq.append(failed)
        logger.error("EventBus: %s — %s", event.get("type"), error)

    def get_metrics(self) -> QueueMetrics:
        return QueueMetrics(
            size=len(self._queue),
            peak_size=self.peak_size,
            overflow_count=self.overflow_count,
            dlq_size=len(self._dlq),
            published_total=self.published_total,
            consumed_total=self.consumed_total,
        )


_bus_singleton: EventBus | None = None


def get_event_bus() -> EventBus:
    global _bus_singleton
    if _bus_singleton is None:
        _bus_singleton = EventBus()
    return _bus_singleton


def reset_event_bus() -> None:
    global _bus_singleton
    _bus_singleton = None


def use_background_dispatch() -> bool:
    return use_event_bus_background()


__all__ = [
    "EventBus",
    "QueueMetrics",
    "get_event_bus",
    "is_event_bus_enabled",
    "reset_event_bus",
    "use_background_dispatch",
]
