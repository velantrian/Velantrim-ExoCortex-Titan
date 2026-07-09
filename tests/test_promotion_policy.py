"""
Тесты градуированной петли обучения (core/promotion_policy.py).
Покрывают: лестницу Observed→Hypothesized→Supported→Validated по доказательствам,
корроборацию, доверие источнику, выдержку во времени, противоречия, и КЛЮЧЕВОЙ
контраст с наивным ConsolidationEngine (одиночный непроверенный факт НЕ становится
Validated).
"""


from core.promotion_policy import (
    Evidence,
    PromotionConfig,
    compute_corroboration,
    is_graduated_promotion_enabled,
    recommend_transition,
    run_graduated_promotion,
)

# ── flag ────────────────────────────────────────────────────────────────────

def test_flag_off_by_default(monkeypatch):
    monkeypatch.delenv("ENABLE_GRADUATED_PROMOTION", raising=False)
    assert is_graduated_promotion_enabled() is False


def test_flag_on_when_set(monkeypatch):
    monkeypatch.setenv("ENABLE_GRADUATED_PROMOTION", "true")
    assert is_graduated_promotion_enabled() is True


# ── recommend_transition: лестница ────────────────────────────────────────────

CLAIM = "A sufficiently long claim about the world"


def test_observed_lonely_untrusted_goes_to_hypothesized():
    # одиночный непроверенный источник → лишь гипотеза, НЕ истина
    ev = Evidence(corroboration=1, source_trusted=False, confidence=0.9)
    assert recommend_transition("Observed", CLAIM, ev) == "Hypothesized"


def test_observed_trusted_goes_to_hypothesized():
    ev = Evidence(corroboration=1, source_trusted=True, confidence=0.5)
    assert recommend_transition("Observed", CLAIM, ev) == "Hypothesized"


def test_observed_with_corroboration_goes_to_hypothesized():
    ev = Evidence(corroboration=2, source_trusted=False, confidence=0.5)
    assert recommend_transition("Observed", CLAIM, ev) == "Hypothesized"


def test_hypothesized_needs_evidence_for_supported():
    lonely = Evidence(corroboration=1, source_trusted=False)
    assert recommend_transition("Hypothesized", CLAIM, lonely) is None
    corrob = Evidence(corroboration=2)
    assert recommend_transition("Hypothesized", CLAIM, corrob) == "Supported"


def test_supported_to_validated_requires_all_conditions():
    cfg = PromotionConfig()
    ok = Evidence(corroboration=3, age_seconds=cfg.validate_min_age_s + 1, confidence=0.8)
    assert recommend_transition("Supported", CLAIM, ok, cfg) == "Validated"


def test_supported_blocked_when_too_young():
    cfg = PromotionConfig()
    young = Evidence(corroboration=3, age_seconds=10, confidence=0.9)
    assert recommend_transition("Supported", CLAIM, young, cfg) is None


def test_supported_blocked_when_low_confidence():
    cfg = PromotionConfig()
    lowconf = Evidence(corroboration=3, age_seconds=cfg.validate_min_age_s + 1, confidence=0.4)
    assert recommend_transition("Supported", CLAIM, lowconf, cfg) is None


def test_supported_blocked_when_no_corroboration_and_untrusted():
    cfg = PromotionConfig()
    weak = Evidence(corroboration=1, source_trusted=False,
                    age_seconds=cfg.validate_min_age_s + 1, confidence=0.9)
    assert recommend_transition("Supported", CLAIM, weak, cfg) is None


def test_trusted_source_reaches_validated_without_corroboration():
    cfg = PromotionConfig(validate_min_age_s=0)
    ev = Evidence(corroboration=1, source_trusted=True, age_seconds=0, confidence=0.8)
    assert recommend_transition("Supported", CLAIM, ev, cfg) == "Validated"


# ── противоречия (демоушен) ────────────────────────────────────────────────

def test_contradiction_demotes_validated():
    ev = Evidence(has_contradiction=True)
    assert recommend_transition("Validated", CLAIM, ev) == "Contradicted"
    assert recommend_transition("Supported", CLAIM, ev) == "Contradicted"


def test_contradicted_low_state_is_held_not_promoted():
    # M4 fix: факт, помеченный как сторона противоречия, НЕ повышается, пока спорный
    # (раньше Observed с противоречием шёл «обычным путём» в Hypothesized).
    ev = Evidence(has_contradiction=True, corroboration=1)
    assert recommend_transition("Observed", CLAIM, ev) is None
    assert recommend_transition("Hypothesized", CLAIM, ev) is None


# ── граничные ───────────────────────────────────────────────────────────────

def test_short_claim_blocked():
    assert recommend_transition("Observed", "short", Evidence(corroboration=5)) is None


def test_unknown_or_terminal_state_returns_none():
    assert recommend_transition("Validated", CLAIM, Evidence(corroboration=9)) is None
    assert recommend_transition("Collapsed", CLAIM, Evidence()) is None
    assert recommend_transition("ImmutableCore", CLAIM, Evidence()) is None


# ── corroboration ─────────────────────────────────────────────────────────────

def test_corroboration_counts_distinct_sources():
    facts = [
        {"fact_id": "a", "claim": "The sky is blue", "source": "s1"},
        {"fact_id": "b", "claim": "the sky is blue.", "source": "s2"},  # та же суть, др. источник
        {"fact_id": "c", "claim": "Grass is green", "source": "s1"},
    ]
    corr = compute_corroboration(facts)
    assert corr["a"] == 2 and corr["b"] == 2   # 2 разных источника об одном
    assert corr["c"] == 1


def test_corroboration_same_source_counts_once():
    facts = [
        {"fact_id": "a", "claim": "Water is wet", "source": "s1"},
        {"fact_id": "b", "claim": "water is wet", "source": "s1"},  # тот же источник
    ]
    corr = compute_corroboration(facts)
    assert corr["a"] == 1 and corr["b"] == 1


# ── engine integration (реальный store) ───────────────────────────────────────

def _store(tmp_path):
    from core.memory import SQLiteGraphStore
    return SQLiteGraphStore(db_path=str(tmp_path / "promo.db"))


def test_engine_lonely_untrusted_fact_stops_at_hypothesized(tmp_path):
    """КЛЮЧЕВОЙ КОНТРАСТ: наивный движок сделал бы Validated; здесь — Hypothesized."""
    s = _store(tmp_path)
    s.store_fact({"fact_id": "x1", "claim": "Some random unverified claim from one source",
                  "source": "random_blog", "confidence": 0.8})
    rep = run_graduated_promotion(s)
    assert s.get_fact("x1")["epistemic_state"] == "Hypothesized"
    assert rep.promoted.get("Observed->Hypothesized") == 1
    # повторный прогон не двигает дальше без новых доказательств
    run_graduated_promotion(s)
    assert s.get_fact("x1")["epistemic_state"] == "Hypothesized"


def test_engine_trusted_fact_climbs_to_validated_over_runs(tmp_path):
    s = _store(tmp_path)
    s.store_fact({"fact_id": "t1", "claim": "A trusted seed axiom about the domain",
                  "source": "domain_seed", "confidence": 0.9})
    cfg = PromotionConfig(validate_min_age_s=0)  # без выдержки для теста
    run_graduated_promotion(s, cfg=cfg)                    # Observed -> Hypothesized
    assert s.get_fact("t1")["epistemic_state"] == "Hypothesized"
    run_graduated_promotion(s, cfg=cfg)                    # Hypothesized -> Supported
    assert s.get_fact("t1")["epistemic_state"] == "Supported"
    run_graduated_promotion(s, cfg=cfg)                    # Supported -> Validated
    assert s.get_fact("t1")["epistemic_state"] == "Validated"


def test_engine_short_claim_unchanged(tmp_path):
    s = _store(tmp_path)
    s.store_fact({"fact_id": "s1", "claim": "tiny", "source": "x", "confidence": 0.9})
    run_graduated_promotion(s)
    assert s.get_fact("s1")["epistemic_state"] == "Observed"


# ── wiring: run_consolidation dispatch по флагу (option «б») ───────────────────

_LONELY = {"fact_id": "d1", "claim": "Some random unverified claim from one source",
           "source": "random_blog", "confidence": 0.8}


def test_dispatch_naive_when_flag_off(tmp_path, monkeypatch):
    """Флаг ВЫКЛ → run_consolidation остаётся наивным (fallback, прежнее поведение)."""
    monkeypatch.delenv("ENABLE_GRADUATED_PROMOTION", raising=False)
    from core.consolidation_engine import run_consolidation
    s = _store(tmp_path)
    s.store_fact({
        "fact_id": "d1",
        "claim": "Some random unverified claim from one source",
        "source": "manual",
        "confidence": 0.8,
    })
    report = run_consolidation(s)
    assert s.get_fact("d1")["epistemic_state"] == "Validated"      # наивный штамп
    assert "promoted_validated" in report.to_dict()                # ConsolidationReport


def test_dispatch_graduated_when_flag_on(tmp_path, monkeypatch):
    """Флаг ВКЛ → run_consolidation маршрутизирует в градуированную петлю."""
    monkeypatch.setenv("ENABLE_GRADUATED_PROMOTION", "true")
    from core.consolidation_engine import run_consolidation
    s = _store(tmp_path)
    s.store_fact(dict(_LONELY))
    report = run_consolidation(s)
    assert s.get_fact("d1")["epistemic_state"] == "Hypothesized"   # честно: лишь гипотеза
    assert "promoted" in report.to_dict()                          # PromotionReport
