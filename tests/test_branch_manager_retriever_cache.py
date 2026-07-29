"""
Regression test for the M15 retriever-cache fix (Claude audit 2026-07-28,
originally found as #18).

BranchManager._retrieve_with_hints() used to construct a fresh
HybridRetriever(facts) on every call — reloading the sentence-transformer
model and re-encoding the whole fact corpus each time (a "performance bomb",
per core/pipeline.py's own AUDIT-FIX v8.4.0 comment describing the identical
problem it already solved there with a dirty-flagged module singleton,
_get_hybrid_retriever()). branch_manager.py never adopted that singleton, so
every branch of every reason() call paid the full rebuild cost again.

This test proves _retrieve_with_hints() now goes through
core.pipeline._get_hybrid_retriever() and reuses the cached instance across
calls when the fact set hasn't changed.
"""
from __future__ import annotations

import pytest

import core.pipeline as pl
from core.branch_manager import BranchManager


@pytest.fixture(autouse=True)
def reset_hybrid_singleton():
    """Isolate this test's view of the module-level singleton from whatever
    other tests in the same session left behind."""
    saved = (pl._HYBRID_RETRIEVER, pl._HYBRID_DIRTY, pl._HYBRID_FACTS_COUNT, pl._HYBRID_FACT_IDS)
    pl._HYBRID_RETRIEVER = None
    pl._HYBRID_DIRTY = True
    pl._HYBRID_FACTS_COUNT = 0
    pl._HYBRID_FACT_IDS = frozenset()
    yield
    pl._HYBRID_RETRIEVER, pl._HYBRID_DIRTY, pl._HYBRID_FACTS_COUNT, pl._HYBRID_FACT_IDS = saved


class _FakeStore:
    def __init__(self, facts):
        self._facts = facts

    def get_all_facts(self):
        return list(self._facts)


def test_retrieve_with_hints_reuses_cached_retriever_across_calls(monkeypatch):
    facts = [
        {"fact_id": f"f{i}", "claim": f"claim number {i} about gravity",
         "source": "test", "confidence": 0.8, "epistemic_state": "Validated"}
        for i in range(5)
    ]

    import core.memory as mem
    monkeypatch.setattr(mem, "_GLOBAL_STORE", _FakeStore(facts))

    build_calls = []
    real_hybrid_retriever = pl.HybridRetriever

    class _CountingHybridRetriever(real_hybrid_retriever):
        def __init__(self, *a, **k):
            build_calls.append(1)
            super().__init__(*a, **k)

    monkeypatch.setattr(pl, "HybridRetriever", _CountingHybridRetriever)

    manager = BranchManager()
    hints = {"retrieval_k": "3", "use_ego": "false"}

    manager._retrieve_with_hints("gravity query one", hints)
    assert len(build_calls) == 1, "first call must build the retriever"

    manager._retrieve_with_hints("gravity query two", hints)
    assert len(build_calls) == 1, (
        "second call with the same fact set must reuse the cached "
        "singleton, not rebuild the retriever (M15)"
    )
