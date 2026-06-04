"""
tests/test_eval_golden.py — Evaluation harness over the golden dataset ("the ruler").

Why this exists
---------------
A small, deterministic quality gate that measures RETRIEVAL quality on the fixed
golden dataset (tests/golden_dataset.py). Purpose:
  • the knowledge base is growing fast — this catches silent quality regressions;
  • the upcoming truth_policy / EvidenceRef work (P2) can be MEASURED, not guessed.

It exercises the REAL production retriever (HybridRetriever). The thresholds are
conservative regression FLOORS (worst case = BM25-only on Russian morphology),
NOT perfection targets — raise them as retrieval improves (e.g. after lemmatized
BM25 or P2 lands). Being under tests/, it runs as part of the normal suite/CI.

Metrics
-------
  • recall@k   — fraction of facts retrieved in the top-k for a query built from
                 their own salient terms (can the system find what it stored?).
  • MRR@k      — mean reciprocal rank of that self-retrieval (ranking quality).
  • contradiction-pair recall — both sides of each golden contradiction pair are
                 retrievable (diagnostic; ranking-who-wins is printed for P2).

Run:
  pytest tests/test_eval_golden.py -o addopts="" -q -s
"""
from __future__ import annotations

import re

import pytest

from core.hybrid_retriever import HybridRetriever
from core.observer import observe as observe_answer
from core.truth_policy import ALLOW, GAP_NOTICE, REJECT
from core.truth_policy import decide as truth_decide
from tests.golden_dataset import GOLDEN_FACTS

TOP_K = 5
RECALL_FLOOR = 0.70   # recall@5 — worst case (BM25-only, RU morphology)
MRR_FLOOR = 0.55      # mean reciprocal rank @5

_WORD = re.compile(r"[А-Яа-яЁёA-Za-z0-9]{4,}")


def _query_from_claim(claim: str, n: int = 4) -> str:
    """Deterministic pseudo-query: the n longest content-ish tokens of the claim.

    Uses a PARTIAL query (not the whole claim) so retrieval is genuinely exercised
    rather than trivially echoing the full text back.
    """
    words = _WORD.findall(claim.lower())
    longest = set(sorted(set(words), key=len, reverse=True)[:n])
    ordered = list(dict.fromkeys(w for w in words if w in longest))
    return " ".join(ordered) or claim


@pytest.fixture(scope="module")
def report():
    retriever = HybridRetriever(GOLDEN_FACTS, use_reranker=False)
    try:
        dense_on = retriever._dense.available
    except Exception:
        dense_on = False

    hits = 0
    rr_sum = 0.0
    misses: list[str] = []
    for f in GOLDEN_FACTS:
        results = retriever.retrieve(_query_from_claim(f["claim"]), top_k=TOP_K)
        ids = [r.fact_id for r in results]
        if f["fact_id"] in ids:
            hits += 1
            rr_sum += 1.0 / (ids.index(f["fact_id"]) + 1)
        else:
            misses.append(f["fact_id"])

    n = len(GOLDEN_FACTS)
    return {
        "retriever": retriever,
        "n": n,
        "recall": hits / n,
        "mrr": rr_sum / n,
        "misses": misses,
        "mode": "BM25+Dense" if dense_on else "BM25-only",
    }


def test_golden_retrieval_recall(report):
    print(
        f"\n[eval] mode={report['mode']} facts={report['n']} "
        f"recall@{TOP_K}={report['recall']:.3f} MRR@{TOP_K}={report['mrr']:.3f} "
        f"misses={report['misses']}"
    )
    assert report["recall"] >= RECALL_FLOOR, (
        f"retrieval recall@{TOP_K}={report['recall']:.3f} fell below floor "
        f"{RECALL_FLOOR} — misses: {report['misses']}"
    )


def test_golden_retrieval_mrr(report):
    assert report["mrr"] >= MRR_FLOOR, (
        f"retrieval MRR@{TOP_K}={report['mrr']:.3f} fell below floor {MRR_FLOOR}"
    )


def test_golden_contradiction_pairs_retrievable(report):
    """Both sides of each golden contradiction pair must be retrievable.

    Which side ranks higher is printed as a diagnostic: raw retrieval does NOT
    enforce truth (that is truth_policy / P2's job). Once P2 lands, this becomes
    the hook for a hard 'Validated outranks Contradicted' gate.
    """
    by_id = {f["fact_id"]: f for f in GOLDEN_FACTS}
    retriever = report["retriever"]
    pairs = [(f["fact_id"], f["contradicts"]) for f in GOLDEN_FACTS if f.get("contradicts")]
    assert pairs, "golden dataset should contain contradiction pairs"

    both_retrievable = 0
    truth_wins = 0
    for con_id, val_id in pairs:
        claim = by_id[con_id]["claim"]
        ids = [r.fact_id for r in retriever.retrieve(_query_from_claim(claim), top_k=TOP_K)]
        if con_id in ids and val_id in ids:
            both_retrievable += 1
            if ids.index(val_id) < ids.index(con_id):
                truth_wins += 1
    print(
        f"\n[eval] contradiction pairs={len(pairs)} both_retrievable={both_retrievable} "
        f"truth_outranks_false={truth_wins} (diagnostic; hard gate arrives with P2)"
    )
    # Soft, honest floor: at least half of the pairs surface both sides together.
    assert both_retrievable >= len(pairs) // 2, (
        f"only {both_retrievable}/{len(pairs)} contradiction pairs had both sides in top-{TOP_K}"
    )


# ── Truth-policy verdicts over the golden set (P2 spine, T1.4) ──────────────────
# These assert the read-path verdict logic that /query exposes when ENABLE_TRUTH_POLICY
# is on. decide() is a pure function, so no flag/env is needed to test it here.

def test_golden_contradicted_only_rejected():
    contradicted = [f for f in GOLDEN_FACTS if f.get("epistemic_state") == "Contradicted"]
    assert contradicted, "golden set must contain Contradicted facts"
    verdict = truth_decide("q", contradicted, mode="BALANCED")
    # confidence 0.0 ⇒ nothing admissible ⇒ reject (do not fabricate an answer)
    assert verdict.decision == REJECT


def test_golden_validated_facts_gap_without_evidence():
    validated = [f for f in GOLDEN_FACTS if f.get("epistemic_state") == "Validated"][:5]
    verdict = truth_decide("q", validated, mode="BALANCED")
    # high-confidence, source-tagged, but no structural EvidenceRef ⇒ honest gap_notice
    assert verdict.decision == GAP_NOTICE and verdict.admissible_count >= 1


def test_golden_fact_with_evidence_allowed():
    f = dict(GOLDEN_FACTS[0])  # ImmutableCore axiom, confidence 1.0
    f["metadata"] = {"evidence_refs": [{"source_id": "codata", "span": "1-10"}]}
    verdict = truth_decide("q", [f], mode="BALANCED")
    assert verdict.decision == ALLOW and "codata" in verdict.evidence_ids


# ── Observer P0 over the golden set ──────────────────────────────────────────────

def test_golden_observer_rejects_contradicted_answer(monkeypatch):
    monkeypatch.setattr("core.gap_detector.query_goal_alignment", lambda q, u="default": 0.5)
    contradicted = [f for f in GOLDEN_FACTS if f.get("epistemic_state") == "Contradicted"]
    v = observe_answer("q", contradicted, "ответ на основе противоречивых фактов")
    assert v.decision == REJECT and "no_admissible_evidence" in v.flags


def test_golden_observer_allows_grounded_evidenced_answer(monkeypatch):
    monkeypatch.setattr("core.gap_detector.query_goal_alignment", lambda q, u="default": 0.5)
    f = dict(GOLDEN_FACTS[0])  # ImmutableCore axiom, conf 1.0
    f["metadata"] = {"evidence_refs": [{"source_id": "codata", "span": "1-10"}]}
    v = observe_answer("q", [f], f["claim"])  # answer == claim → grounded
    assert v.decision == ALLOW and v.flags == []


# ── CognitiveDistance re-rank — measurement gate (the decision number) ───────────
# Does re-ranking by cognitive_distance improve truth-ordering (Validated above
# Contradicted) WITHOUT collapsing distinct facts? This is the number to read (-s)
# before ever flipping ENABLE_COGNITIVE_DISTANCE on by default.

def test_cogdist_improves_truth_ordering_on_golden():
    from core.cognitive_distance import rank_by_distance

    # mixed pack: contradiction pairs (Contradicted) + their Validated/Immutable targets
    pack = [f for f in GOLDEN_FACTS
            if f.get("epistemic_state") in ("Validated", "ImmutableCore", "Contradicted")]
    ranked = rank_by_distance(pack, query_vector=None, top_k=len(pack))
    states = [r.get("epistemic_state") for r in ranked]

    # position of the first Contradicted vs the last trusted fact
    first_contra = next((i for i, s in enumerate(states) if s == "Contradicted"), len(states))
    trusted_above = sum(1 for s in states[:first_contra]
                        if s in ("Validated", "ImmutableCore"))
    print(f"\n[eval] cogdist re-rank: {trusted_above} trusted facts ranked above the first "
          f"Contradicted (of {len([s for s in states if s != 'Contradicted'])} trusted total)")
    # epistemic axis must put every trusted fact strictly above every Contradicted one
    contra_idx = [i for i, s in enumerate(states) if s == "Contradicted"]
    trust_idx = [i for i, s in enumerate(states) if s in ("Validated", "ImmutableCore")]
    if contra_idx and trust_idx:
        assert max(trust_idx) < min(contra_idx), "trusted facts must outrank Contradicted"


def test_cogdist_preserves_distinct_facts():
    from core.cognitive_distance import rank_by_distance

    pack = [f for f in GOLDEN_FACTS[:10]]
    ranked = rank_by_distance(pack, query_vector=None, top_k=10)
    assert len({r["fact_id"] for r in ranked}) == len(ranked)  # no collapse/dedup
