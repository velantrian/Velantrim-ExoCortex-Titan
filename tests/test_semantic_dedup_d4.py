"""
Tests for D4 (semantic dedup correctness/scale):
- determinism: clustering is independent of input order (fix audit M3);
- transitivity: A≈B, B≈C (but A≉C) collapse into ONE cluster (connected components);
- domain blocking: facts in different domains are not merged even if similar.
"""
from core.semantic_dedup import cluster_by_meaning, compute_semantic_corroboration


def _ids(facts, clusters):
    return sorted(
        (tuple(sorted(facts[i]["fact_id"] for i in cl)) for cl in clusters),
    )


def test_clustering_is_order_independent():
    # chain A≈B≈C via vectors; shuffle input → identical clustering (M3 determinism)
    vecs = {"A": [1.0, 0.0], "B": [0.985, 0.174], "C": [0.94, 0.342]}  # ~10° apart each

    def emb(claims):
        return [vecs[c] for c in claims]

    base = [{"fact_id": "a", "claim": "A", "source": "s1"},
            {"fact_id": "b", "claim": "B", "source": "s2"},
            {"fact_id": "c", "claim": "C", "source": "s3"}]
    rev = list(reversed(base))
    c1 = _ids(base, cluster_by_meaning(base, threshold=0.9, embed_fn=emb))
    c2 = _ids(rev, cluster_by_meaning(rev, threshold=0.9, embed_fn=emb))
    assert c1 == c2  # same result regardless of order


def test_transitivity_chain_one_cluster():
    # A≈B (0.985) and B≈C (0.985) but A≉C (0.94 < 0.95) → connected components still merge all 3
    vecs = {"A": [1.0, 0.0], "B": [0.985, 0.174], "C": [0.94, 0.342]}

    def emb(claims):
        return [vecs[c] for c in claims]

    facts = [{"fact_id": "a", "claim": "A", "source": "s1"},
             {"fact_id": "b", "claim": "B", "source": "s2"},
             {"fact_id": "c", "claim": "C", "source": "s3"}]
    clusters = cluster_by_meaning(facts, threshold=0.95, embed_fn=emb)
    # A-B edge (0.985) and B-C edge (0.985) ≥ 0.95; A-C (0.94) < 0.95 — but chain connects all
    assert len(clusters) == 1 and len(clusters[0]) == 3


def test_domain_blocking_prevents_cross_domain_merge():
    # identical vectors but DIFFERENT domains → must NOT merge
    def emb(claims):
        return [[1.0, 0.0] for _ in claims]

    facts = [
        {"fact_id": "p1", "claim": "ток это поток заряда", "source": "s1",
         "metadata": {"domain": "physics"}},
        {"fact_id": "e1", "claim": "ток это поток заряда", "source": "s2",
         "metadata": {"domain": "economics"}},
    ]
    clusters = cluster_by_meaning(facts, threshold=0.5, embed_fn=emb)
    assert len(clusters) == 2  # blocked by domain despite identical meaning


def test_corroboration_still_counts_distinct_sources_same_domain():
    def emb(claims):
        return [[1.0, 0.0] for _ in claims]

    facts = [
        {"fact_id": "a", "claim": "вода кипит при 100", "source": "s1",
         "metadata": {"domain": "physics"}},
        {"fact_id": "b", "claim": "точка кипения воды 100", "source": "s2",
         "metadata": {"domain": "physics"}},
    ]
    corr = compute_semantic_corroboration(facts, threshold=0.5, embed_fn=emb)
    assert corr["a"] == 2 and corr["b"] == 2   # same domain + meaning → corroborate
