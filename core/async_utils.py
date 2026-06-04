"""
Безопасный запуск coroutine из синхронного кода (pipeline, тесты).
"""

from __future__ import annotations

import asyncio
import concurrent.futures
from collections.abc import Coroutine
from typing import TypeVar

T = TypeVar("T")


def run_coroutine_sync(coro: Coroutine[object, object, T]) -> T:
    """
    asyncio.run, если нет активного loop; иначе — отдельный поток с новым loop.
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, coro).result()


__all__ = ["run_coroutine_sync"]
