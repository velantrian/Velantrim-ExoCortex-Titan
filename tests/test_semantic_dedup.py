"""
Тесты семантической дедупликации → корроборации (core/semantic_dedup.py).
Детерминированно: инъектируем фейковый embed_fn (без загрузки sentence-transformers).
"""
from core.semantic_dedup import (
    cluster_by_meaning,
    compute_semantic_corroboration,
    is_semantic_dedup_enabled,
    plan_dedup,
)

# Фейковые векторы: f1≈f2 (cosine ~0.98), f3 — ортогонален.
_VEC = {
    "Water boils at 100C": [1.0, 0.0, 0.0],
    "Boiling point of water is 100C": [0.98, 0.2, 0.0],
    "Grass is green": [0.0, 1.0, 0.0],
}


def _fake_embed(claims):
    return [_VEC[c] for c in claims]


def _facts():
    return [
        {"fact_id": "f1", "claim": "Water boils at 100C", "source": "physics",
         "epistemic_state": "Validated", "confidence": 0.9},
        {"fact_id": "f2", "claim": "Boiling point of water is 100C", "source": "chemistry",
         "epistemic_state": "Supported", "confidence": 0.8},
        {"fact_id": "f3", "claim": "Grass is green", "source": "botany",
         "epistemic_state": "Observed", "confidence": 0.7},
    ]


# ── flag ──────────────────────────────────────────────────────────────────────

def test_flag_off_by_default(monkeypatch):
    monkeypatch.delenv("ENABLE_SEMANTIC_DEDUP", raising=False)
    assert is_semantic_dedup_enabled() is False


# ── clustering ──────────────────────────────────────────────────────────────────

def test_meaning_clusters_merge_synonyms_separate_others():
    clusters = cluster_by_meaning(_facts(), threshold=0.92, embed_fn=_fake_embed)
    # привести к множествам fact_id для устойчивого сравнения
    ids = _facts()
    as_sets = sorted(
        ({ids[i]["fact_id"] for i in cl} for cl in clusters), key=lambda s: sorted(s)
    )
    assert {"f1", "f2"} in as_sets      # «вода кипит» ≈ «boiling point» → один кластер
    assert {"f3"} in as_sets            # «трава» — отдельно


def test_high_threshold_keeps_them_separate():
    # порог 0.999 — даже близкие не сливаются
    clusters = cluster_by_meaning(_facts(), threshold=0.999, embed_fn=_fake_embed)
    assert len(clusters) == 3


def test_lexical_fallback_without_embedder():
    facts = [
        {"fact_id": "a", "claim": "Вода кипит.", "source": "s1"},
        {"fact_id": "b", "claim": "вода кипит", "source": "s2"},   # тот же нормализованный claim
        {"fact_id": "c", "claim": "Трава зелёная", "source": "s3"},
    ]
    clusters = cluster_by_meaning(facts, embed_fn=None)
    sizes = sorted(len(cl) for cl in clusters)
    assert sizes == [1, 2]              # a+b слиты лексически, c отдельно


def test_empty_claims_skipped():
    facts = [{"fact_id": "x", "claim": "   ", "source": "s"},
             {"fact_id": "y", "claim": "Real claim here", "source": "s"}]
    clusters = cluster_by_meaning(facts, embed_fn=None)
    flat = [i for cl in clusters for i in cl]
    assert 0 not in flat               # пустой claim не попал ни в один кластер


# ── corroboration ────────────────────────────────────────────────────────────────

def test_semantic_corroboration_counts_distinct_sources():
    corr = compute_semantic_corroboration(_facts(), threshold=0.92, embed_fn=_fake_embed)
    assert corr["f1"] == 2 and corr["f2"] == 2    # 2 разных источника об одном смысле
    assert corr["f3"] == 1


def test_corroboration_feeds_promotion():
    # связка: семантическая корроборация → promotion рекомендует первый шаг лестницы
    from core.promotion_policy import Evidence, recommend_transition
    corr = compute_semantic_corroboration(_facts(), threshold=0.92, embed_fn=_fake_embed)
    ev = Evidence(corroboration=corr["f1"])        # =2
    assert recommend_transition("Observed", "Water boils at 100C long enough", ev) == "Hypothesized"
    assert recommend_transition("Hypothesized", "Water boils at 100C long enough", ev) == "Supported"


# ── merge plan ────────────────────────────────────────────────────────────────────

def test_plan_dedup_picks_canonical_and_lists_absorbed():
    plans = plan_dedup(_facts(), threshold=0.92, embed_fn=_fake_embed)
    assert len(plans) == 1
    p = plans[0]
    assert p.canonical_id == "f1"               # Validated > Supported
    assert p.absorbed_ids == ["f2"]
    assert p.sources_after == ["chemistry", "physics"]
    assert p.size == 2


def test_plan_dedup_empty_when_all_distinct():
    plans = plan_dedup(_facts(), threshold=0.999, embed_fn=_fake_embed)
    assert plans == []


def test_opposite_polarity_not_corroborated():
    # «X подходит» и «X не подходит» в одном смысловом кластере НЕ корроборируют друг друга
    facts = [
        {"fact_id": "p", "claim": "Дерево подходит для дома", "source": "s1"},
        {"fact_id": "n", "claim": "Дерево не подходит для дома", "source": "s2"},
    ]
    same_vec = lambda claims: [[1.0, 0.0] for _ in claims]   # оба в одном кластере
    corr = compute_semantic_corroboration(facts, threshold=0.5, embed_fn=same_vec)
    assert corr["p"] == 1 and corr["n"] == 1                 # каждый сам по себе, НЕ 2
