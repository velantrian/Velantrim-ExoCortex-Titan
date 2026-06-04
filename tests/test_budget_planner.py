"""Tests for core/budget_planner.py (adaptive retrieval) + pipeline hook (Increment 2)."""
from __future__ import annotations

import core.pipeline as pipeline
from core.budget_planner import RetrievalPlan, estimate_complexity, plan

# ── estimate_complexity ──────────────────────────────────────────────────────────

def test_empty_is_zero():
    assert estimate_complexity("") == 0.0


def test_trivial_below_complex():
    trivial = estimate_complexity("вода")
    complex_q = estimate_complexity(
        "почему использование закалённого металла снижает энергозатраты при сравнении с бетоном"
    )
    assert trivial < complex_q


# ── plan ─────────────────────────────────────────────────────────────────────────

def test_plan_empty_is_none_mode():
    p = plan("   ")
    assert p.mode == "none"


def test_plan_trivial_is_lexical():
    p = plan("вода", base_k=3)
    assert p.mode == "lexical" and p.k == 3


def test_plan_complex_is_hybrid_with_more_k():
    # genuinely complex: reasoning cue + length + technical tokens (>=0.60)
    p = plan("почему использование закалённого металла снижает энергозатраты "
             "при сравнении с бетоном и какие риски пожара возникают", base_k=3)
    assert p.mode == "hybrid" and p.k > 3 and p.max_hops >= 2


def test_plan_returns_dataclass_with_dict():
    p = plan("test")
    assert isinstance(p, RetrievalPlan) and "mode" in p.to_dict()


# ── pipeline hook: flag-gated, off ⇒ no change ──────────────────────────────────

def test_retrieve_flag_off_passes_base_k(monkeypatch):
    monkeypatch.setattr("core.runtime_flags.is_budget_planner_enabled", lambda: False)
    captured = {}

    def _fake_from_db(query, k, db):
        captured["k"] = k
        return [{"id": "x"}]

    monkeypatch.setattr(pipeline, "_retrieve_from_database", _fake_from_db)
    pipeline.retrieve("почему сравни всё подряд очень длинный сложный запрос", k=3,
                      database=[{"fact_id": "x", "claim": "y", "confidence": 0.5}])
    assert captured["k"] == 3  # flag off → base k unchanged


def test_retrieve_flag_on_scales_k(monkeypatch):
    monkeypatch.setattr("core.runtime_flags.is_budget_planner_enabled", lambda: True)
    captured = {}

    def _fake_from_db(query, k, db):
        captured["k"] = k
        return [{"id": "x"}]

    monkeypatch.setattr(pipeline, "_retrieve_from_database", _fake_from_db)
    pipeline.retrieve("почему сравни дерево и бетон по рискам пожара и теплоизоляции", k=3,
                      database=[{"fact_id": "x", "claim": "y", "confidence": 0.5}])
    assert captured["k"] > 3  # complex query → planner widened k


def test_flag_default_off():
    from core.runtime_flags import is_budget_planner_enabled

    assert is_budget_planner_enabled() is False
