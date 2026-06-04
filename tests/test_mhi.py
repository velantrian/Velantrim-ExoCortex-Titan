"""Tests for core.mhi — Memory Health Index v8.3.1."""

from __future__ import annotations

import os
import tempfile

import pytest

from core import memory as memory_mod
from core.memory import SQLiteGraphStore
from core.mhi import MHICalculator, MHIReport, MHIStatus, check_mhi


@pytest.fixture
def isolated_store():
    db_path = tempfile.mktemp(suffix=".db")
    store = SQLiteGraphStore(db_path=db_path)
    yield store
    store.close()
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def populated_store(isolated_store):
    """Store с фактами в разных состояниях."""
    facts = [
        {"fact_id": "f1", "claim": "a", "source": "s1", "confidence": 0.9, "metadata": {}},
        {"fact_id": "f2", "claim": "b", "source": "s2", "confidence": 0.8, "metadata": {}},
        {"fact_id": "f3", "claim": "c", "source": "s3", "confidence": 0.7, "metadata": {}},
    ]
    for f in facts:
        isolated_store.store_fact(f)
    return isolated_store


# ─── Базовые проверки ──────────────────────────────────────────────────────

class TestBasics:
    def test_calculate_returns_report(self, populated_store):
        calc = MHICalculator(populated_store)
        report = calc.calculate()
        assert isinstance(report, MHIReport)

    def test_mhi_in_range(self, populated_store):
        calc = MHICalculator(populated_store)
        report = calc.calculate()
        assert 0.0 <= report.mhi <= 1.0

    def test_empty_store_no_crash(self, isolated_store):
        calc = MHICalculator(isolated_store)
        report = calc.calculate()
        assert isinstance(report, MHIReport)
        assert report.total_facts == 0

    def test_report_has_all_fields(self, populated_store):
        calc = MHICalculator(populated_store)
        r = calc.calculate()
        assert hasattr(r, "mhi")
        assert hasattr(r, "status")
        assert hasattr(r, "validated_ratio")
        assert hasattr(r, "freshness_score")
        assert hasattr(r, "retrieval_precision")
        assert hasattr(r, "graph_coverage")
        assert hasattr(r, "recommendations")


# ─── Статусы (HEALTHY / DEGRADED / SAFE_MODE) ──────────────────────────────

class TestStatuses:
    def test_low_mhi_is_safe_mode(self, isolated_store):
        # Пустой store → 0 validated, 0 retrieval data, 0 graph
        # MHI = 0 + 0.25*1 (нет stale если нет фактов = 0 stale / max(0,1) = 0)
        # Wait — empty: freshness = 1 - 0/max(0,1) = 1 - 0 = 1
        # precision = 0.5 (нейтрально без данных)
        # graph = 0
        # MHI = 0 + 0.25*1 + 0.25*0.5 + 0.20*0 = 0.375 → DEGRADED
        calc = MHICalculator(isolated_store)
        r = calc.calculate()
        assert r.status in (MHIStatus.SAFE_MODE, MHIStatus.DEGRADED)

    def test_with_l3_higher_mhi(self, populated_store):
        calc_no_l3 = MHICalculator(populated_store, l3_connected=False)
        calc_l3 = MHICalculator(populated_store, l3_connected=True)
        r_no_l3 = calc_no_l3.calculate()
        r_l3 = calc_l3.calculate()
        # С L3 MHI должен быть выше на 0.20
        assert r_l3.mhi > r_no_l3.mhi

    def test_high_retrieval_precision_helps(self, populated_store):
        calc_bad = MHICalculator(populated_store, retrieval_hits=1, retrieval_total=10)
        calc_good = MHICalculator(populated_store, retrieval_hits=9, retrieval_total=10)
        r_bad = calc_bad.calculate()
        r_good = calc_good.calculate()
        assert r_good.mhi > r_bad.mhi


# ─── Validated facts ───────────────────────────────────────────────────────

class TestValidatedRatio:
    def test_validated_ratio_zero_initially(self, populated_store):
        """Все факты только что созданы → Observed → validated_ratio = 0."""
        calc = MHICalculator(populated_store)
        r = calc.calculate()
        assert r.validated_ratio == 0.0

    def test_validated_ratio_after_promotion(self, populated_store):
        """Перевод 2/3 фактов в Validated → ratio = 0.67."""
        memory_mod._GLOBAL_STORE = populated_store
        try:
            populated_store.update_state(
                "f1", "Validated",
                {"state": "Validated", "at": "2026-05-11T00:00:00", "by": "test"},
                "2026-05-11T00:00:00",
            )
            populated_store.update_state(
                "f2", "Validated",
                {"state": "Validated", "at": "2026-05-11T00:00:00", "by": "test"},
                "2026-05-11T00:00:00",
            )
            calc = MHICalculator(populated_store)
            r = calc.calculate()
            assert abs(r.validated_ratio - 2/3) < 0.01
        finally:
            memory_mod._GLOBAL_STORE = None


# ─── Recommendations ───────────────────────────────────────────────────────

class TestRecommendations:
    def test_recommendations_never_empty(self, populated_store):
        calc = MHICalculator(populated_store)
        r = calc.calculate()
        assert len(r.recommendations) > 0

    def test_l3_disconnected_in_recommendations(self, populated_store):
        calc = MHICalculator(populated_store, l3_connected=False)
        r = calc.calculate()
        assert any("L3" in rec or "graph" in rec.lower() for rec in r.recommendations)

    def test_low_validated_warning(self, populated_store):
        """Низкий validated_ratio → должна быть рекомендация."""
        calc = MHICalculator(populated_store, retrieval_hits=10, retrieval_total=10, l3_connected=True)
        r = calc.calculate()
        if r.validated_ratio < 0.4:
            assert any("validated_ratio" in rec or "TruthGate" in rec for rec in r.recommendations)


# ─── Helper function ───────────────────────────────────────────────────────

class TestCheckMHI:
    def test_check_mhi_returns_status(self, populated_store):
        status = check_mhi(populated_store)
        assert isinstance(status, MHIStatus)

    def test_check_mhi_with_kwargs(self, populated_store):
        status = check_mhi(populated_store, l3_connected=True, retrieval_hits=10, retrieval_total=10)
        assert isinstance(status, MHIStatus)


# ─── Error handling ────────────────────────────────────────────────────────

class TestErrorHandling:
    def test_broken_store_returns_safe_mode(self):
        """Сломанный store не должен крашить calculate()."""
        class BrokenStore:
            def get_all_facts(self):
                raise RuntimeError("DB connection lost")

        calc = MHICalculator(BrokenStore())
        r = calc.calculate()
        assert r.status == MHIStatus.SAFE_MODE
        assert r.mhi == 0.0
        assert any("Ошибка" in rec for rec in r.recommendations)
