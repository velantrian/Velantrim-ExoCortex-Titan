"""
Dual-Process guard — Fast Path vs Slow Path (Crystal invariant).

По умолчанию контекст = FAST (запрос пользователя).
Тяжёлая физиология/ингест/скан рёбер обязаны вызываться под slow_path().

I-DP1: попасть в Fast Path операцию Slow-only — DualProcessError.
"""

from __future__ import annotations

import contextvars
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from enum import Enum
from functools import wraps
from typing import Any, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


class PathKind(str, Enum):
    FAST = "fast"
    SLOW = "slow"


class DualProcessError(RuntimeError):
    """Операция Slow-only вызвана на Fast Path."""


_current_path: contextvars.ContextVar[PathKind] = contextvars.ContextVar(
    "velantrim_path_kind",
    default=PathKind.FAST,
)


def current_path() -> PathKind:
    return _current_path.get()


def is_slow_path() -> bool:
    return current_path() is PathKind.SLOW


def is_fast_path() -> bool:
    return current_path() is PathKind.FAST


@contextmanager
def slow_path() -> Iterator[None]:
    """Пометить блок как Slow Path (фон / admin / workers)."""
    token = _current_path.set(PathKind.SLOW)
    try:
        yield
    finally:
        _current_path.reset(token)


@contextmanager
def fast_path() -> Iterator[None]:
    """Явно пометить блок как Fast Path (обычно уже default)."""
    token = _current_path.set(PathKind.FAST)
    try:
        yield
    finally:
        _current_path.reset(token)


def require_slow_path(operation: str) -> None:
    if not is_slow_path():
        raise DualProcessError(
            f"Dual-Process: '{operation}' — только Slow Path "
            f"(сейчас: {current_path().value})"
        )


def slow_only(operation: str | None = None) -> Callable[[F], F]:
    """Декоратор: функция разрешена только на Slow Path."""

    def decorator(fn: F) -> F:
        op = operation or fn.__qualname__

        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any):
            require_slow_path(op)
            return fn(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator


__all__ = [
    "DualProcessError",
    "PathKind",
    "current_path",
    "fast_path",
    "is_fast_path",
    "is_slow_path",
    "require_slow_path",
    "slow_only",
    "slow_path",
]
