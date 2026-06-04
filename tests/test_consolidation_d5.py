"""
Tests for D5 (consolidation correctness):

- M4 fix: a fact recognized as part of a contradiction is NOT promoted to Validated
  in the same cycle (promotion is told about contradictions before it runs).
- H2/M3 fix: the contradiction winner is chosen TRUST-AWARE (epistemic_state,
  trust, confidence), with recency only as a tie-break — a newer low-trust fact
  no longer demotes an older Validated trusted fact.
"""
from core.contradiction_resolver import detect_contradictions
from core.promotion_policy import Evidence, recommend_transition


# ── H2/M3: trust-aware winner ────────────────────────────────────────────────
def test_winner_is_trusted_validated_not_newer_noise():
    facts = [
        {"fact_id": "old_validated", "claim": "дерево подходит для постройки",
         "epistemic_state": "Validated", "source": "domain_seed", "confidence": 0.95,
         "t_ingestion_start": "2026-01-01T00:00:00+00:00"},
        {"fact_id": "new_observed", "claim": "дерево не подходит для постройки",
         "epistemic_state": "Observed", "source": "random_user", "confidence": 0.4,
         "t_ingestion_start": "2026-02-01T00:00:00+00:00"},  # newer, but weak
    ]
    cs = detect_contradictions(facts)
    assert len(cs) == 1
    # loser (older_id) must be the newer-but-weaker Observed fact, NOT the Validated one
    assert cs[0].older_id == "new_observed"
    assert cs[0].newer_id == "old_validated"


def test_winner_recency_tiebreak_when_equal_strength():
    # equal state + equal trust → newer wins (legitimate correction)
    facts = [
        {"fact_id": "a", "claim": "встреча в понедельник", "epistemic_state": "Observed",
         "source": "user", "confidence": 0.6, "t_ingestion_start": "2026-01-01T00:00:00+00:00"},
        {"fact_id": "b", "claim": "встреча не в понедельник", "epistemic_state": "Observed",
         "source": "user", "confidence": 0.6, "t_ingestion_start": "2026-03-01T00:00:00+00:00"},
    ]
    cs = detect_contradictions(facts)
    assert len(cs) == 1
    assert cs[0].newer_id == "b"      # newer wins on tie
    assert cs[0].older_id == "a"


# ── M4: contradicted facts not promoted ──────────────────────────────────────
def test_recommend_transition_holds_contradicted_low_state():
    ev = Evidence(corroboration=5, source_trusted=True, age_seconds=10**6,
                  confidence=0.99, has_contradiction=True)
    # would normally promote Observed→Supported, but contradiction holds it
    assert recommend_transition("Observed", "достаточно длинный claim", ev) is None
    assert recommend_transition("Hypothesized", "достаточно длинный claim", ev) is None


def test_recommend_transition_demotes_contradicted_supported():
    ev = Evidence(corroboration=5, source_trusted=True, age_seconds=10**6,
                  confidence=0.99, has_contradiction=True)
    assert recommend_transition("Supported", "достаточно длинный claim", ev) == "Contradicted"
    assert recommend_transition("Validated", "достаточно длинный claim", ev) == "Contradicted"


def test_contradicted_fact_not_validated_without_flag():
    # control: same strong evidence WITHOUT contradiction → Supported can reach Validated
    ev = Evidence(corroboration=5, source_trusted=True, age_seconds=10**6,
                  confidence=0.99, has_contradiction=False)
    assert recommend_transition("Supported", "достаточно длинный claim", ev) == "Validated"
