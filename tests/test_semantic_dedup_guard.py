"""
Test the D4 over-merge guard (RU calibration): a connected component larger than
_MAX_CLUSTER_SIZE is NOT merged — it is split back to singletons. Without the guard,
a low threshold + transitivity chained 40+ unrelated facts into one cluster on the
real Russian corpus.
"""
import core.semantic_dedup as sd
from core.semantic_dedup import cluster_by_meaning


def _chain_embed(n):
    # vectors on a tight arc so each is similar to its neighbours (chain), forming
    # ONE connected component of size n at a moderate threshold
    import math
    vecs = {f"c{i}": [math.cos(i * 0.05), math.sin(i * 0.05)] for i in range(n)}
    return lambda claims: [vecs[c] for c in claims]


def _facts(n):
    return [{"fact_id": f"f{i:03d}", "claim": f"c{i}", "source": "s"} for i in range(n)]


def test_guard_blocks_giant_cluster(monkeypatch):
    monkeypatch.setattr(sd, "_MAX_CLUSTER_SIZE", 8)
    facts = _facts(30)
    emb = _chain_embed(30)
    clusters = cluster_by_meaning(facts, threshold=0.99, embed_fn=emb)
    # the 30-member chain exceeds the guard → split to singletons, no giant merge
    assert max(len(c) for c in clusters) <= 8
    # everything still present (no data lost), just not merged
    assert sum(len(c) for c in clusters) == 30


def test_guard_allows_small_clusters(monkeypatch):
    monkeypatch.setattr(sd, "_MAX_CLUSTER_SIZE", 8)
    # two clearly-identical facts (same vector) → a legit size-2 cluster survives
    emb = lambda claims: [[1.0, 0.0] for _ in claims]
    facts = [{"fact_id": "a", "claim": "вода кипит при 100", "source": "s1",
              "metadata": {"domain": "phys"}},
             {"fact_id": "b", "claim": "точка кипения воды 100", "source": "s2",
              "metadata": {"domain": "phys"}}]
    clusters = cluster_by_meaning(facts, threshold=0.9, embed_fn=emb)
    assert any(len(c) == 2 for c in clusters)
