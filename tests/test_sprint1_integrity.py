"""Спринт 1: checksum, episode_hash dedup, ConsolidationEngine."""

from __future__ import annotations

import os
import sys

import pytest

from tests.helpers import typed_evidence_refs

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))



def _r1_promote_to_validated(fact_id, by="test", store=None):
    """TEST-ONLY: enrich to BALANCED TruthGate bar, then protected admission."""
    from core import memory as memory_mod
    api = store or memory_mod
    get = api.get_fact if hasattr(api, "get_fact") else memory_mod.get_fact
    put = api.store_fact if hasattr(api, "store_fact") else memory_mod.store_fact
    promote = api.promote_to_validated if hasattr(api, "promote_to_validated") else memory_mod.promote_to_validated
    fact = get(fact_id)
    if fact is not None:
        meta = dict(fact.get("metadata") or {})
        # TruthGate._count_evidence only counts STRING refs (dicts are ignored).
        refs = [r for r in (meta.get("evidence_refs") or []) if isinstance(r, str)]
        while len(refs) < 2:
            refs.append(f"test_ev_{len(refs)+1}")
        meta["evidence_refs"] = refs
        payload = {
            "fact_id": fact_id,
            "claim": fact.get("claim", ""),
            "source": fact.get("source") or "test",
            "confidence": max(float(fact.get("confidence") or 0.0), 0.8),
            "metadata": meta,
        }
        for extra in ("claim_type", "origin_type", "raw_input", "derived_from"):
            if fact.get(extra) is not None:
                payload[extra] = fact.get(extra)
        put(payload)
    try:
        ok = promote(fact_id, by=by)
    except TypeError:
        ok = promote(fact_id)
    assert ok is True, (
        f"expected TruthGate Validated for {fact_id}; "
        f"fact={get(fact_id)!r}"
    )
    return True

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
    from core.memory import find_fact_id_by_episode_hash, get_fact, store_fact, promote_to_validated

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
    from core.memory import get_fact, promote_to_validated, store_fact, transition_esm

    store_fact(
        {
            "fact_id": "f_prot",
            "claim": "Исходный факт",
            "source": "t",
            "confidence": 0.95,
        }
    )
    _r1_promote_to_validated("f_prot", by="test")
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
            "source": "manual",
            "confidence": 0.88,
            # P0-D: the final Supported -> Validated hop now also goes
            # through validate_and_promote() (TruthGate + CAS) on top of
            # ConsolidationEngine's own confidence/utility gate — needs
            # evidence_refs to clear TruthGate's BALANCED mode (min_evidence=2).
            "metadata": {"evidence_refs": typed_evidence_refs(2, prefix="test_sprint1_integrity")},
        }
    )
    report = run_consolidation(mem_db)
    assert report.promoted_validated >= 1
    assert get_fact("f_cons")["epistemic_state"] == "Validated"
