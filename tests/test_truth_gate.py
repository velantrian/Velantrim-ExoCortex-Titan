"""Tests for core.truth_gate — реальный TruthGate v8.3.1."""

from __future__ import annotations

import os
import tempfile

import pytest

from core.memory import SQLiteGraphStore
from core.truth_gate import (
    CognitiveMode,
    TruthGate,
    TruthGateVerdict,
    truth_gate,
)


@pytest.fixture
def isolated_store():
    db_path = tempfile.mktemp(suffix=".db")
    store = SQLiteGraphStore(db_path=db_path)
    yield store
    store.close()
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def gate(isolated_store):
    return TruthGate(isolated_store)



_REF_DIGEST = "sha256:" + "a" * 64
_FRAGMENT_DIGEST = "sha256:" + "b" * 64


def _typed_ref(index: int) -> dict:
    return {
        "schema_version": 1,
        "reference_id": f"ref-{index}",
        "source_id": f"source-{index}",
        "source_digest": _REF_DIGEST,
        "fragment_id": f"fragment-{index}",
        "fragment_digest": _FRAGMENT_DIGEST,
        "span": f"chars:{index * 10}-{index * 10 + 5}",
        "lineage_id": f"lineage-{index}",
        "captured_at": "2026-09-23T00:00:00Z",
    }


@pytest.fixture
def good_fact():
    return {
        "fact_id": "f1",
        "claim": "Земля вращается вокруг Солнца",
        "source": "astronomy_textbook",
        "confidence": 0.95,
        "metadata": {"evidence_refs": [_typed_ref(1), _typed_ref(2), _typed_ref(3)]},
    }


# ─── Базовые проверки ──────────────────────────────────────────────────────

class TestBasics:
    def test_good_fact_passes(self, gate, good_fact):
        v = gate.evaluate(good_fact, mode=CognitiveMode.BALANCED)
        assert v.passed
        assert v.reason == "passed"
        assert v.fact_id == "f1"

    def test_verdict_bool_conversion(self, gate, good_fact):
        v = gate.evaluate(good_fact)
        assert bool(v) is True

    def test_returns_verdict_object(self, gate, good_fact):
        v = gate.evaluate(good_fact)
        assert isinstance(v, TruthGateVerdict)


# ─── Source check ──────────────────────────────────────────────────────────

class TestSourceCheck:
    def test_empty_source_rejected(self, gate, good_fact):
        good_fact["source"] = ""
        v = gate.evaluate(good_fact)
        assert not v.passed
        assert v.reason == "no_source"

    def test_whitespace_source_rejected(self, gate, good_fact):
        good_fact["source"] = "   "
        v = gate.evaluate(good_fact)
        assert not v.passed
        assert v.reason == "no_source"

    def test_missing_source_field_rejected(self, gate, good_fact):
        del good_fact["source"]
        v = gate.evaluate(good_fact)
        assert not v.passed
        assert v.reason == "no_source"


# ─── Confidence check ──────────────────────────────────────────────────────

class TestConfidenceCheck:
    def test_low_confidence_rejected_balanced(self, gate, good_fact):
        good_fact["confidence"] = 0.5  # BALANCED порог 0.7
        v = gate.evaluate(good_fact, mode=CognitiveMode.BALANCED)
        assert not v.passed
        assert v.reason == "low_confidence"

    def test_exploration_allows_lower_confidence(self, gate, good_fact):
        good_fact["confidence"] = 0.5  # EXPLORATION порог 0.4
        v = gate.evaluate(good_fact, mode=CognitiveMode.EXPLORATION)
        assert v.passed

    def test_precision_requires_high_confidence(self, gate, good_fact):
        good_fact["confidence"] = 0.85  # PRECISION порог 0.9
        good_fact["metadata"]["evidence_refs"] = [_typed_ref(i) for i in range(5)]
        v = gate.evaluate(good_fact, mode=CognitiveMode.PRECISION)
        assert not v.passed
        assert v.reason == "low_confidence"


# ─── Evidence count check ──────────────────────────────────────────────────

class TestEvidenceCheck:
    def test_insufficient_evidence_balanced(self, gate, good_fact):
        good_fact["metadata"] = {}  # 0 refs stays 0
        v = gate.evaluate(good_fact, mode=CognitiveMode.BALANCED)
        # BALANCED min_evidence = 2, у нас 0 → reject
        assert not v.passed
        assert v.reason == "insufficient_evidence"

    def test_precision_requires_5_evidence(self, gate, good_fact):
        good_fact["metadata"] = {"evidence_refs": [_typed_ref(1), _typed_ref(2), _typed_ref(3)]}
        v = gate.evaluate(good_fact, mode=CognitiveMode.PRECISION)
        assert not v.passed
        assert v.reason == "insufficient_evidence"

    def test_exploration_rejects_missing_evidence(self, gate, good_fact):
        good_fact["metadata"] = {}
        v = gate.evaluate(good_fact, mode=CognitiveMode.EXPLORATION)
        assert not v.passed
        assert v.reason == "insufficient_evidence"
        assert v.evidence_count == 0

    def test_exploration_accepts_one_typed_reference(self, gate, good_fact):
        good_fact["metadata"] = {"evidence_refs": [_typed_ref(1)]}
        v = gate.evaluate(good_fact, mode=CognitiveMode.EXPLORATION)
        assert v.passed
        assert v.evidence_count == 1

    def test_legacy_string_refs_do_not_count_as_evidence(self, gate, good_fact):
        good_fact["metadata"] = {"evidence_refs": ["ref-a", "ref-b"]}
        v = gate.evaluate(good_fact, mode=CognitiveMode.BALANCED)
        assert not v.passed
        assert v.reason == "insufficient_evidence"
        assert v.evidence_count == 0

    def test_duplicate_typed_refs_do_not_inflate_cardinality(self, gate, good_fact):
        ref = _typed_ref(1)
        good_fact["metadata"] = {"evidence_refs": [ref, dict(ref)]}
        v = gate.evaluate(good_fact, mode=CognitiveMode.BALANCED)
        assert not v.passed
        assert v.reason == "insufficient_evidence"
        assert v.evidence_count == 1

    def test_two_typed_refs_satisfy_balanced_cardinality(self, gate, good_fact):
        good_fact["metadata"] = {"evidence_refs": [_typed_ref(1), _typed_ref(2)]}
        v = gate.evaluate(good_fact, mode=CognitiveMode.BALANCED)
        assert v.passed
        assert v.evidence_count == 2


# ─── Cognitive modes integration ───────────────────────────────────────────

class TestCognitiveModes:
    @pytest.mark.parametrize("mode,min_conf,min_ev", [
        (CognitiveMode.PRECISION,   0.9, 5),
        (CognitiveMode.BALANCED,    0.7, 2),
        (CognitiveMode.EXPLORATION, 0.4, 1),
        (CognitiveMode.CREATIVE,    0.7, 2),
    ])
    def test_mode_thresholds_applied(self, gate, good_fact, mode, min_conf, min_ev):
        # Точно на пороге — должно пройти с DISTINCT legacy evidence tokens.
        good_fact["confidence"] = min_conf
        good_fact["metadata"] = {"evidence_refs": [_typed_ref(i) for i in range(min_ev)]}
        v = gate.evaluate(good_fact, mode=mode)
        assert v.passed, f"{mode.value}: confidence={min_conf} evidence={min_ev} должно пройти"

    def test_below_threshold_rejected(self, gate, good_fact):
        good_fact["confidence"] = 0.7
        good_fact["metadata"] = {"evidence_refs": [_typed_ref(1)]}
        v = gate.evaluate(good_fact, mode=CognitiveMode.PRECISION)
        assert not v.passed


# ─── Backward-compatible function ──────────────────────────────────────────

class TestCompatFunction:
    def test_truth_gate_function_returns_bool(self, isolated_store, good_fact):
        result = truth_gate(good_fact, isolated_store)
        assert isinstance(result, bool)
        assert result is True

    def test_truth_gate_function_rejects(self, isolated_store, good_fact):
        good_fact["confidence"] = 0.1
        result = truth_gate(good_fact, isolated_store, mode=CognitiveMode.BALANCED)
        assert result is False


# ─── Audit trail ───────────────────────────────────────────────────────────

class TestAuditTrail:
    def test_verdict_has_by(self, gate, good_fact):
        v = gate.evaluate(good_fact, by="test_runner")
        assert v.by == "test_runner"

    def test_verdict_has_checked_at(self, gate, good_fact):
        v = gate.evaluate(good_fact)
        assert v.checked_at  # ISO timestamp

    def test_verdict_records_mode(self, gate, good_fact):
        v = gate.evaluate(good_fact, mode=CognitiveMode.CREATIVE)
        assert v.mode == CognitiveMode.CREATIVE

    def test_verdict_records_evidence_count(self, gate, good_fact):
        good_fact["metadata"] = {"evidence_refs": [_typed_ref(1), _typed_ref(2), _typed_ref(3)]}
        v = gate.evaluate(good_fact, mode=CognitiveMode.BALANCED)
        assert v.evidence_count == 3
