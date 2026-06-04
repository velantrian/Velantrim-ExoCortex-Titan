"""Tests for the opt-in cognitive_distance re-rank in pipeline retrieval."""
from __future__ import annotations

import core.pipeline as pipeline


def _rows():
    # two retrieval rows with EQUAL retrieval_score; differ only by stored epistemic_state
    return [
        {"id": "f_contra", "text": "x", "source": "s", "confidence": 0.9,
         "retrieval_score": 1.0, "epistemic_state": "Observed", "origin": "test"},
        {"id": "f_valid", "text": "y", "source": "s", "confidence": 0.9,
         "retrieval_score": 1.0, "epistemic_state": "Observed", "origin": "test"},
    ]


def test_rerank_noop_when_flag_off(monkeypatch):
    monkeypatch.setattr(pipeline, "_cogdist_enabled", lambda: False)
    rows = _rows()
    out = pipeline._maybe_cognitive_rerank(rows, k=2)
    assert [r["id"] for r in out] == ["f_contra", "f_valid"]  # original order, untouched
    assert "cognitive_distance" not in out[0]


def test_rerank_promotes_validated_over_contradicted(monkeypatch):
    monkeypatch.setattr(pipeline, "_cogdist_enabled", lambda: True)
    # enrichment source: real epistemic states from "store"
    enriched = {
        "f_contra": {"fact_id": "f_contra", "epistemic_state": "Contradicted", "confidence": 0.9},
        "f_valid": {"fact_id": "f_valid", "epistemic_state": "Validated", "confidence": 0.9},
    }
    monkeypatch.setattr(pipeline, "get_facts_by_ids",
                        lambda ids: [enriched[i] for i in ids if i in enriched])
    out = pipeline._maybe_cognitive_rerank(_rows(), k=2)
    assert [r["id"] for r in out][0] == "f_valid"  # epistemic axis lifts Validated
    assert out[0]["cognitive_distance"] >= out[1]["cognitive_distance"]


def test_rerank_truncates_to_k(monkeypatch):
    monkeypatch.setattr(pipeline, "_cogdist_enabled", lambda: True)
    monkeypatch.setattr(pipeline, "get_facts_by_ids", lambda ids: [])
    out = pipeline._maybe_cognitive_rerank(_rows(), k=1)
    assert len(out) == 1


def test_rerank_never_raises_on_store_error(monkeypatch):
    monkeypatch.setattr(pipeline, "_cogdist_enabled", lambda: True)

    def _boom(ids):
        raise RuntimeError("store down")

    monkeypatch.setattr(pipeline, "get_facts_by_ids", _boom)
    out = pipeline._maybe_cognitive_rerank(_rows(), k=2)  # must fall back, not raise
    assert len(out) == 2


def test_flag_default_off():
    from core.runtime_flags import is_cognitive_distance_enabled

    assert is_cognitive_distance_enabled() is False
