"""Tests for Source Authenticity Score + truth_policy surfacing (Increment 1)."""
from __future__ import annotations

from core.evidence import compute_source_authenticity
from core.truth_policy import decide

# ── compute_source_authenticity ─────────────────────────────────────────────────

def test_authenticity_in_range_and_default():
    a = compute_source_authenticity("unknown")
    assert 0.0 <= a <= 1.0
    assert a == 0.50  # default reliability, no verify, no contradiction


def test_authenticity_monotonic_in_reliability():
    hi = compute_source_authenticity("peer_reviewed_paper")
    lo = compute_source_authenticity("unknown")
    assert hi > lo


def test_authenticity_rises_with_verification():
    base = compute_source_authenticity("reuters_ap", verification_count=0)
    more = compute_source_authenticity("reuters_ap", verification_count=5)
    assert more > base


def test_authenticity_falls_with_contradiction():
    clean = compute_source_authenticity("reuters_ap", contradiction_rate=0.0)
    dirty = compute_source_authenticity("reuters_ap", contradiction_rate=0.8)
    assert dirty < clean


def test_authenticity_clamped():
    a = compute_source_authenticity("meta_analysis", verification_count=10_000,
                                    contradiction_rate=0.0)
    assert a <= 1.0
    z = compute_source_authenticity("meta_analysis", contradiction_rate=1.0)
    assert z == 0.0


# ── truth_policy surfaces authenticity without changing verdicts ──────────────────

def _fact(fid, conf, evidence=None):
    f = {"fact_id": fid, "claim": f"c{fid}", "confidence": conf, "source": "src"}
    if evidence is not None:
        f["metadata"] = {"evidence_refs": evidence}
    return f


def test_decide_surfaces_authenticity_in_trace():
    ev = [{"source_id": "doc1", "source_type": "peer_reviewed_paper",
           "span": "1-10", "verification_count": 4, "contradiction_rate": 0.0}]
    v = decide("q", [_fact("a", 0.9, evidence=ev)])
    assert v.decision == "allow"
    assert "avg_authenticity=" in v.trace_note


def test_decide_unchanged_when_no_refs():
    # source-only fact ⇒ still gap_notice, no authenticity note
    v = decide("q", [_fact("a", 0.9)])
    assert v.decision == "gap_notice"
    assert "avg_authenticity" not in v.trace_note
