"""Спринт 1: checksum, episode_hash dedup, ConsolidationEngine."""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture
def mem_db(tmp_path, monkeypatch):
    import core.memory as mem

    db = str(tmp_path / "sprint1.db")
    monkeypatch.setenv("VELANTRIM_DB_PATH", db)
    store = mem.make_store(db)
    monkeypatch.setattr(mem, "_GLOBAL_STORE", store)
    monkeypatch.setattr(mem, "_L0", store._l0)
    return store


def test_checksum_stable():
    from core.fact_integrity import compute_content_checksum

    a = compute_content_checksum("Тест", "src", 0.9, "Observed")
    b = compute_content_checksum("Тест", "src", 0.9, "Observed")
    assert a == b
    assert len(a) == 32


def test_episode_hash_dedup(mem_db):
    from core.fact_integrity import compute_episode_hash
    from core.memory import find_fact_id_by_episode_hash, get_fact, store_fact

    claim = "Velantrim использует Kuzu для графа"
    eh = compute_episode_hash(claim, "manual")
    store_fact(
        {
            "fact_id": "f_dedup_1",
            "claim": claim,
            "source": "manual",
            "confidence": 0.9,
        }
    )
    found = find_fact_id_by_episode_hash(eh)
    assert found == "f_dedup_1"
    meta = get_fact("f_dedup_1")["metadata"]
    assert meta.get("episode_hash") == eh
    assert meta.get("content_checksum")


def test_protected_claim_change_drift_contradicted(mem_db):
    """Смена claim у Validated → TASK-02 drift protection, не тихий overwrite."""
    from core.memory import get_fact, store_fact, transition_esm

    store_fact(
        {
            "fact_id": "f_prot",
            "claim": "Исходный факт",
            "source": "t",
            "confidence": 0.95,
        }
    )
    transition_esm("f_prot", "Validated", by="test")
    store_fact(
        {
            "fact_id": "f_prot",
            "claim": "Другой текст",
            "source": "t",
            "confidence": 0.95,
        }
    )
    assert get_fact("f_prot")["epistemic_state"] == "Contradicted"


def test_consolidation_promotes_high_confidence(mem_db):
    from core.consolidation_engine import run_consolidation
    from core.memory import get_fact, store_fact

    store_fact(
        {
            "fact_id": "f_cons",
            "claim": "Длинный факт для консолидации в Validated",
            "source": "test",
            "confidence": 0.88,
        }
    )
    report = run_consolidation(mem_db)
    assert report.promoted_validated >= 1
    assert get_fact("f_cons")["epistemic_state"] == "Validated"
