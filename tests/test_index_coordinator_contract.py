from __future__ import annotations

import pytest

from core.index_coordinator import IndexCoordinator
from core.ngram_index import NGramIndex


def _real_ngram(tmp_path) -> NGramIndex:
    ngram = NGramIndex(str(tmp_path / "coordinator_ngram.db"))
    if not ngram.available:
        pytest.skip("SQLite build does not provide FTS5 trigram")
    return ngram


def test_store_uses_real_ngram_public_api_and_marks_hybrid_dirty(tmp_path):
    ngram = _real_ngram(tmp_path)
    coordinator = IndexCoordinator()
    coordinator.set_ngram(ngram)
    coordinator.mark_hybrid_clean()

    coordinator.on_store_fact(
        {"fact_id": "fact-1", "claim": "SQLite serializes explicit writes."}
    )

    assert ngram.contains("fact-1") is True
    assert ngram.count() == 1
    assert coordinator.is_hybrid_dirty is True
    assert coordinator.status() == {
        "ngram_available": True,
        "ngram_degraded": False,
        "last_ngram_error": None,
        "hybrid_dirty": True,
    }


def test_repeated_store_updates_existing_ngram_document(tmp_path):
    ngram = _real_ngram(tmp_path)
    coordinator = IndexCoordinator()
    coordinator.set_ngram(ngram)

    coordinator.on_store_fact({"fact_id": "fact-1", "claim": "first content"})
    coordinator.on_store_fact({"fact_id": "fact-1", "claim": "updated content"})

    assert ngram.contains("fact-1") is True
    assert ngram.count() == 1


def test_batch_indexes_every_fact_with_real_ngram_contract(tmp_path):
    ngram = _real_ngram(tmp_path)
    coordinator = IndexCoordinator()
    coordinator.set_ngram(ngram)
    coordinator.mark_hybrid_clean()

    coordinator.on_store_batch(
        [
            {"fact_id": "fact-a", "claim": "alpha projection content"},
            {"fact_id": "fact-b", "claim": "beta projection content"},
        ]
    )

    assert ngram.contains("fact-a") is True
    assert ngram.contains("fact-b") is True
    assert ngram.count() == 2
    assert coordinator.is_hybrid_dirty is True
    assert coordinator.status()["ngram_degraded"] is False


def test_delete_uses_real_ngram_remove_contract(tmp_path):
    ngram = _real_ngram(tmp_path)
    coordinator = IndexCoordinator()
    coordinator.set_ngram(ngram)
    coordinator.on_store_fact({"fact_id": "fact-1", "claim": "temporary content"})
    coordinator.mark_hybrid_clean()

    coordinator.on_delete_fact("fact-1")

    assert ngram.contains("fact-1") is False
    assert coordinator.is_hybrid_dirty is True
    assert coordinator.status()["ngram_degraded"] is False


class _FailingNGram:
    def index(self, doc_id: str, content: str) -> None:
        raise RuntimeError("synthetic derived-index failure")

    def remove(self, doc_id: str) -> None:
        raise OSError("synthetic derived-index failure")


def test_ngram_store_failure_is_observable_but_bounded():
    coordinator = IndexCoordinator()
    coordinator.set_ngram(_FailingNGram())
    coordinator.mark_hybrid_clean()

    coordinator.on_store_fact({"fact_id": "fact-1", "claim": "content"})

    assert coordinator.is_hybrid_dirty is True
    assert coordinator.status() == {
        "ngram_available": True,
        "ngram_degraded": True,
        "last_ngram_error": "RuntimeError",
        "hybrid_dirty": True,
    }


def test_ngram_delete_failure_is_observable_but_bounded():
    coordinator = IndexCoordinator()
    coordinator.set_ngram(_FailingNGram())

    coordinator.on_delete_fact("fact-1")

    assert coordinator.status()["ngram_degraded"] is True
    assert coordinator.status()["last_ngram_error"] == "OSError"


class _PartlyFailingNGram:
    def __init__(self) -> None:
        self.indexed: list[str] = []

    def index(self, doc_id: str, content: str) -> None:
        if doc_id == "bad":
            raise ValueError("synthetic one-item failure")
        self.indexed.append(doc_id)

    def remove(self, doc_id: str) -> None:
        return None


def test_batch_continues_derived_indexing_and_retains_degraded_status():
    ngram = _PartlyFailingNGram()
    coordinator = IndexCoordinator()
    coordinator.set_ngram(ngram)

    coordinator.on_store_batch(
        [
            {"fact_id": "first", "claim": "first"},
            {"fact_id": "bad", "claim": "bad"},
            {"fact_id": "last", "claim": "last"},
        ]
    )

    assert ngram.indexed == ["first", "last"]
    assert coordinator.status()["ngram_degraded"] is True
    assert coordinator.status()["last_ngram_error"] == "ValueError"
    assert coordinator.is_hybrid_dirty is True


def test_replacing_ngram_resets_only_projection_health_snapshot():
    coordinator = IndexCoordinator()
    coordinator.set_ngram(_FailingNGram())
    coordinator.on_store_fact({"fact_id": "fact-1", "claim": "content"})
    assert coordinator.status()["ngram_degraded"] is True

    replacement = _PartlyFailingNGram()
    coordinator.set_ngram(replacement)

    assert coordinator.status()["ngram_degraded"] is False
    assert coordinator.status()["last_ngram_error"] is None
    assert coordinator.is_hybrid_dirty is True
