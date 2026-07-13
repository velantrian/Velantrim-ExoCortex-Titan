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
import tempfile

import pytest

# Тесты проверяют функциональную корректность, а не дюрабилити при потере питания.
# Продакшен-дефолт facts-store = synchronous=FULL (медленнее из-за fsync); для тестовой
# сессии понижаем до NORMAL, чтобы write-heavy сьют не тормозил. setdefault — уважает
# явный VELANTRIM_SQLITE_SYNCHRONOUS, если он задан в окружении.
os.environ.setdefault("VELANTRIM_SQLITE_SYNCHRONOUS", "NORMAL")
os.environ.setdefault("VELANTRIM_VERSION_SNAPSHOTS", "true")

# core.embedding_store.EXOCORTEX_DB / core.ngram_index.NGRAM_DB_PATH are
# module-level constants read once via os.getenv() at import time, then bound
# as default constructor arguments — so they can only be redirected here,
# before either module is first imported anywhere in the session. Without
# this, any test that builds a bare EmbeddingStore()/NGramIndex() (directly,
# or transitively via core.erasure_coordinator.get_coordinator()) would
# write into the real ./data/exocortex_graph.db / ./data/velantrim_ngram.db.
_TEST_STORES_DIR = tempfile.mkdtemp(prefix="velantrim-test-stores-")
os.environ.setdefault("SQLITE_GRAPH_PATH", os.path.join(_TEST_STORES_DIR, "exocortex_graph.db"))
os.environ.setdefault("VELANTRIM_NGRAM_DB", os.path.join(_TEST_STORES_DIR, "ngram.db"))


@pytest.fixture(autouse=True)
def _preserve_global_store():
    from core import memory as _mem

    saved = _mem._GLOBAL_STORE
    try:
        yield
    finally:
        _mem._GLOBAL_STORE = saved


@pytest.fixture(autouse=True)
def _preserve_erasure_coordinator():
    """Same leakage guard as _preserve_global_store, for the erasure
    coordinator singleton (core.erasure_coordinator._default_coordinator).

    A test that binds it to a temp-file-backed coordinator (so
    core.erasure.erase_fact()/erase_fact_durable() don't touch the real
    ./data/exocortex_graph.db or ./data/velantrim_ngram.db) via
    monkeypatch.setattr is already auto-restored by pytest; this fixture
    only protects against a test that assigns the module attribute
    directly and forgets to reset it.
    """
    from core import erasure_coordinator as _ec

    saved = _ec._default_coordinator
    try:
        yield
    finally:
        _ec._default_coordinator = saved
