"""
Tests for core/core3_adapter.py — the Dual Core Router subprocess bridge to Core-3.

Verifies the canon (§5.5) verdict vocabulary allow | gap_notice | reject and the
fail-safe behavior when the Truth Engine is unavailable. Skips the live-subprocess
cases when Core-3 is not present next to the repo.
"""
import pytest

from core import core3_adapter as adapter
from core.core3_adapter import ALLOW, GAP_NOTICE, REJECT, verify

core3_present = pytest.mark.skipif(
    not adapter.is_available(),
    reason="Core-3 (velantrim_core-3) not found next to the repo",
)


@core3_present
def test_allow_with_evidence():
    v = verify(
        "почему деревья важны для почвы?",
        facts=[{"fact_id": "f_roots", "claim": "Корни удерживают влагу в почве",
                "confidence": 0.9, "source": "forest_corpus:roots"}],
    )
    assert v.ok is True
    assert v.decision == ALLOW
    assert v.truth_status == "validated"
    assert "f_roots" in v.evidence_ids


@core3_present
def test_gap_notice_high_confidence_no_evidence():
    # high confidence but NO source ⇒ no evidence ⇒ honest gap_notice (canon §4.4)
    v = verify(
        "сколько лет вселенной?",
        facts=[{"fact_id": "f_x", "claim": "Вселенной 13.8 млрд лет",
                "confidence": 0.95, "source": ""}],
    )
    assert v.ok is True
    assert v.decision == GAP_NOTICE
    assert v.truth_status == "insufficient"
    assert any(r["reason"] == "no_evidence" for r in v.rejected)


@core3_present
def test_reject_on_contradiction():
    v = verify(
        "подходит ли дерево?",
        facts=[{"fact_id": "f_a", "claim": "дерево подходит",
                "confidence": 0.9, "source": "src_a"},
               {"fact_id": "f_b", "claim": "дерево не подходит",
                "confidence": 0.9, "source": "src_b"}],
        relations=[{"from_fact_id": "f_a", "to_fact_id": "f_b",
                    "relation_type": "contradicts", "confidence": 0.9, "source": "manual"}],
    )
    assert v.ok is True
    assert v.decision == REJECT
    assert v.truth_status == "contradicted"
    assert v.blocked_reason


def test_fail_safe_when_core3_missing(monkeypatch):
    # point the adapter at a non-existent Core-3 ⇒ conservative fallback, never a false allow
    monkeypatch.setenv("VELANTRIM_CORE3_PATH", "Z:/no/such/core3/path")
    assert adapter.is_available() is False
    v = verify("anything", facts=[{"fact_id": "f1", "claim": "c", "confidence": 0.9,
                                   "source": "s"}])
    assert v.ok is False
    assert v.decision == GAP_NOTICE          # default on_error is conservative
    assert v.error


def test_fail_safe_respects_on_error(monkeypatch):
    monkeypatch.setenv("VELANTRIM_CORE3_PATH", "Z:/no/such/core3/path")
    v = verify("anything", facts=[], on_error=REJECT)
    assert v.ok is False
    assert v.decision == REJECT


def test_build_contract_shape():
    c = adapter.build_contract("q", [{"fact_id": "f1"}], min_conf=0.6)
    assert c["query"] == "q"
    assert c["mode"] == "strict"
    assert c["min_conf"] == 0.6
    assert c["relations"] == []
