"""
Pytest test-isolation safety net for the global memory store.

Several legacy tests reassign the module-level singleton
``core.memory._GLOBAL_STORE`` to exercise budget/MHI/contradiction paths
(e.g. ``test_adversarial`` sets it to ``None`` in a ``finally``; ``test_mhi``
swaps in a pre-populated store). When such a test fails to restore the
original, the leaked value bleeds into every later test in collection order:

  * leaked ``None``      → ``memory_budget.count_facts`` hits ``None._db``
                           (AttributeError) on the next ``store_fact``;
  * leaked populated     → budget evaluates to ``warn`` and skews verdicts
                           (e.g. ``test_observer`` sees ``warn`` != ``allow``).

This autouse fixture snapshots ``_GLOBAL_STORE`` before each test and restores
it afterwards, so no test can leak that global state into another. It does not
change any test's within-test behavior — a test may still reassign the global
and use it; only cross-test leakage is prevented.
"""
from __future__ import annotations

import os

import pytest

# Тесты проверяют функциональную корректность, а не дюрабилити при потере питания.
# Продакшен-дефолт facts-store = synchronous=FULL (медленнее из-за fsync); для тестовой
# сессии понижаем до NORMAL, чтобы write-heavy сьют не тормозил. setdefault — уважает
# явный VELANTRIM_SQLITE_SYNCHRONOUS, если он задан в окружении.
os.environ.setdefault("VELANTRIM_SQLITE_SYNCHRONOUS", "NORMAL")
os.environ.setdefault("VELANTRIM_VERSION_SNAPSHOTS", "true")


@pytest.fixture(autouse=True)
def _preserve_global_store():
    from core import memory as _mem

    saved = _mem._GLOBAL_STORE
    try:
        yield
    finally:
        _mem._GLOBAL_STORE = saved
