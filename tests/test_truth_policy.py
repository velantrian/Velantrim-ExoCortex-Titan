"""Unit tests for core/truth_policy.py (P2 spine, T1.1)."""
from __future__ import annotations

from core.truth_policy import (
    ALLOW,
    GAP_NOTICE,
    REJECT,
    decide,
    fact_admissible,
    fact_evidence_ref,
)


def _fact(fid, conf, source="src:test", evidence=None):
    f = {"fact_id": fid, "claim": f"claim {fid}", "confidence": conf, "source": source}
    if evidence is not None:
        f["metadata"] = {"evidence_refs": evidence}
    return f


# ── fact_admissible ────────────────────────────────────────────────────────────

def test_admissible_high_conf_with_source():
    ok, reason = fact_admissible(_fact("a", 0.9))
    assert ok and reason == "admissible"


def test_inadmissible_low_conf():
    ok, reason = fact_admissible(_fact("b", 0.3))  # < BALANCED 0.7
    assert not ok and reason == "below_confidence_threshold"


def test_inadmissible_no_source():
    ok, reason = fact_admissible(_fact("c", 0.9, source=""))
    assert not ok and reason == "no_source"


def test_inadmissible_bad_confidence():
    ok, reason = fact_admissible({"fact_id": "d", "source": "s", "confidence": "high"})
    assert not ok and reason == "invalid_confidence"


def test_require_evidence_flag():
    assert fact_admissible(_fact("e", 0.9), require_evidence=True)[0] is False
    ev = [{"source_id": "doc1", "span": "10-40", "quote": "..."}]
    assert fact_admissible(_fact("e", 0.9, evidence=ev), require_evidence=True)[0] is True


# ── fact_evidence_ref ────────────────────────────────────────────────────────────

def test_evidence_ref_plain_string_is_invalid():
    # per canon T1.3 — a plain string is a source tag, NOT a citation
    assert fact_evidence_ref(_fact("f", 0.9, evidence=["just a string"])) is None


def test_evidence_ref_structured():
    ev = [{"source_id": "doc1", "chunk_id": "c7", "span": "120-340", "quote": "q"}]
    ref = fact_evidence_ref(_fact("g", 0.9, evidence=ev))
    assert ref is not None and ref.source_id == "doc1" and ref.span == "120-340"


# ── decide ────────────────────────────────────────────────────────────────────

def test_decide_reject_empty():
    v = decide("q", [])
    assert v.decision == REJECT and v.reason == "no_facts" and v.admissible_count == 0


def test_decide_reject_all_below_threshold():
    v = decide("q", [_fact("a", 0.1), _fact("b", 0.2)])
    assert v.decision == REJECT and v.reason == "all_below_threshold"


def test_decide_gap_when_no_structured_evidence():
    v = decide("q", [_fact("a", 0.9), _fact("b", 0.8)])  # admissible, source-only
    assert v.decision == GAP_NOTICE and v.admissible_count == 2


def test_decide_allow_with_evidence():
    ev = [{"source_id": "doc1", "span": "10-40"}]
    v = decide("q", [_fact("a", 0.9, evidence=ev)])
    assert v.decision == ALLOW and "doc1" in v.evidence_ids
