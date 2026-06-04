"""run_coroutine_sync — sync и nested async loop."""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


async def _echo(value: int) -> int:
    return value + 1


def test_run_coroutine_sync_no_loop():
    from core.async_utils import run_coroutine_sync

    assert run_coroutine_sync(_echo(3)) == 4


@pytest.mark.asyncio
async def test_run_coroutine_sync_inside_running_loop():
    from core.async_utils import run_coroutine_sync

    assert run_coroutine_sync(_echo(10)) == 11
