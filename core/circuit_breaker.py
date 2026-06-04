"""
CircuitBreaker — защита от каскадных сбоев (Titan HYPERIA-8).

CLOSED → OPEN → HALF_OPEN → CLOSED
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreakerOpenError(Exception):
    pass


class CircuitBreaker:
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        timeout: float = 60.0,
        success_threshold: int = 2,
    ) -> None:
        self.name = name
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.success_threshold = success_threshold
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: float | None = None
        self.state = CircuitState.CLOSED
        self._locks: dict[int, asyncio.Lock] = {}

    def _get_lock(self) -> asyncio.Lock:
        loop = asyncio.get_running_loop()
        loop_id = id(loop)
        if loop_id not in self._locks:
            self._locks[loop_id] = asyncio.Lock()
            if len(self._locks) > 10:
                for k in list(self._locks):
                    if k != loop_id:
                        del self._locks[k]
        return self._locks[loop_id]

    async def call(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        async with self._get_lock():
            if self.state == CircuitState.OPEN:
                if (
                    self.last_failure_time is not None
                    and time.monotonic() - self.last_failure_time > self.timeout
                ):
                    logger.info("%s: OPEN → HALF_OPEN", self.name)
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                else:
                    raise CircuitBreakerOpenError(
                        f"Circuit '{self.name}' is OPEN. Retry after {self.timeout}s"
                    )
        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except Exception:
            await self._on_failure()
            raise

    async def _on_success(self) -> None:
        async with self._get_lock():
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.success_threshold:
                    logger.info("%s: HALF_OPEN → CLOSED", self.name)
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                    self.success_count = 0
            elif self.state == CircuitState.CLOSED:
                self.failure_count = max(0, self.failure_count - 1)

    async def _on_failure(self) -> None:
        async with self._get_lock():
            self.failure_count += 1
            self.last_failure_time = time.monotonic()
            if self.state == CircuitState.HALF_OPEN:
                logger.error("%s: HALF_OPEN → OPEN (recovery failed)", self.name)
                self.state = CircuitState.OPEN
            elif self.failure_count >= self.failure_threshold:
                logger.error(
                    "%s: CLOSED → OPEN (%d failures)",
                    self.name,
                    self.failure_count,
                )
                self.state = CircuitState.OPEN

    def get_state(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "last_failure": self.last_failure_time,
        }


_breakers: dict[str, CircuitBreaker] = {}


def get_circuit_breaker(name: str) -> CircuitBreaker:
    if name not in _breakers:
        _breakers[name] = CircuitBreaker(name)
    return _breakers[name]


def reset_circuit_breakers() -> None:
    _breakers.clear()


def list_circuit_breakers() -> dict[str, dict[str, Any]]:
    """Снимок всех зарегистрированных circuit breaker (для /titan/status)."""
    return {name: cb.get_state() for name, cb in _breakers.items()}


__all__ = [
    "CircuitBreaker",
    "CircuitBreakerOpenError",
    "CircuitState",
    "get_circuit_breaker",
    "list_circuit_breakers",
    "reset_circuit_breakers",
]
