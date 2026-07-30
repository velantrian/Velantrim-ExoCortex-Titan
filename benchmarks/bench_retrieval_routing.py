# benchmarks/bench_retrieval_routing.py
# Velantrim ExoCortex — Retrieval Routing Benchmark (PR #91, Increment 2)
#
# Compares:
#   - lexical vs hybrid query cost
#   - first (cold) call vs a warmed repeat call
#   - NGram candidate-set churn (different queries -> different ~50-fact
#     subsets out of a much larger corpus) and its effect on HybridRetriever
#     rebuilds / DenseRetriever encode calls
#
# Measures (minimum required by PR #91):
#   - latency (mean/median/min over N runs)
#   - number of DenseRetriever.retrieve() calls
#   - number of HybridRetriever singleton (re)constructions
#   - number of candidates fed to ranking for each call
#   - final top-k size returned
#
# Run:
#   python benchmarks/bench_retrieval_routing.py
#
# HONESTY NOTE: numbers printed below are only ever measured, live, on
# whatever machine runs this script (printed platform/CPU line) — never
# hardcoded. This repo's core has zero required third-party dependencies;
# `sentence-transformers` (real Dense embeddings) is an opt-in extra. Section
# A reports whichever backend is actually available in the running
# environment. Section B additionally uses a synthetic (non-ML) stand-in for
# SentenceTransformer so the rebuild/encode-count fix is verifiable even in
# environments without the optional embeddings extra installed — those
# numbers are clearly synthetic-instrumentation counts, not model latency.

import os
import platform
import statistics
import sys
import tempfile
import time
import types

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def timeit_fn(fn, n=20):
    """Runs fn() n times, returns (stats_dict, last_result)."""
    times = []
    result = None
    for _ in range(n):
        t0 = time.perf_counter()
        result = fn()
        times.append((time.perf_counter() - t0) * 1000)
    stats = {
        "mean_ms":   round(statistics.mean(times), 4),
        "median_ms": round(statistics.median(times), 4),
        "min_ms":    round(min(times), 4),
        "max_ms":    round(max(times), 4),
        "n":         n,
    }
    return stats, result


def make_facts(n, prefix="fact"):
    return [
        {
            "fact_id":    f"{prefix}_{i}",
            "claim":      f"Факт номер {i} про тему {i % 25} с деталями {i % 7}",
            "source":     f"source_{i % 5}",
            "confidence": 0.5 + (i % 50) / 100,
        }
        for i in range(n)
    ]


def print_header(title):
    print(f"\n{'=' * 78}\n  {title}\n{'=' * 78}")


def print_metrics(label, metrics, extra=""):
    line = (f"  {label:<42} mean={metrics['mean_ms']:>9.4f}ms "
            f"median={metrics['median_ms']:>9.4f}ms min={metrics['min_ms']:>9.4f}ms")
    if extra:
        line += "  | " + extra
    print(line)


class _CountingDense:
    """Wraps DenseRetriever.retrieve to count real calls, without changing behavior."""

    def __init__(self, dense_cls):
        self._cls = dense_cls
        self._original = dense_cls.retrieve
        self.calls = 0

    def install(self):
        counter = self

        def _wrapped(self_, *a, **kw):
            counter.calls += 1
            return counter._original(self_, *a, **kw)

        self._cls.retrieve = _wrapped

    def uninstall(self):
        self._cls.retrieve = self._original


class _CountingHybridClass:
    """Wraps pipeline's bound HybridRetriever name to count singleton (re)builds."""

    def __init__(self, real_cls):
        self.real_cls = real_cls
        self.rebuilds = 0
        outer = self

        class _Counting(real_cls):
            def __init__(self, *a, **kw):
                outer.rebuilds += 1
                super().__init__(*a, **kw)

        self.wrapper_cls = _Counting


def section_a_real_components():
    print_header("A. Real components installed in THIS environment")
    print(f"  platform:  {platform.platform()}")
    print(f"  python:    {platform.python_version()}")
    try:
        import multiprocessing
        print(f"  cpu_count: {multiprocessing.cpu_count()}")
    except Exception:
        pass

    import core.hybrid_retriever as hr
    import core.memory as mem
    import core.pipeline as pipeline
    from core.memory import make_store
    from core.ngram_index import NGramIndex

    dense_probe = hr.DenseRetriever([])
    print(f"  DenseRetriever real backend available: {dense_probe.available}")
    if not dense_probe.available:
        print("  (sentence-transformers not installed here -> hybrid falls back to "
              "BM25-only; dense_calls below will be 0 for this section, which is the "
              "honest fallback behavior, not a bug. See Section B for instrumented "
              "dense-lifecycle counts using a synthetic backend.)")

    dense_counter = _CountingDense(hr.DenseRetriever)
    dense_counter.install()
    hybrid_counter = _CountingHybridClass(pipeline.HybridRetriever)
    old_pipeline_hybrid_cls = pipeline.HybridRetriever
    pipeline.HybridRetriever = hybrid_counter.wrapper_cls

    with tempfile.TemporaryDirectory() as d:
        store = make_store(os.path.join(d, "bench.db"))
        old_store, old_l0 = mem._GLOBAL_STORE, mem._L0
        mem._GLOBAL_STORE, mem._L0 = store, store._l0

        ngram = NGramIndex(os.path.join(d, "bench_ngram.db"))
        old_ngram = pipeline._NGRAM_INDEX
        pipeline._NGRAM_INDEX = ngram

        try:
            n_facts = 2000
            facts = make_facts(n_facts)
            store.store_facts_batch(facts)
            ngram.rebuild(facts)

            queries = [
                "Факт номер 3 про тему 3",
                "Факт номер 900 про тему 0",
                "Факт номер 1500 про тему 15",
                "Факт номер 42 про тему 17",
                "Факт номер 777 про тему 2",
            ]

            print(f"\n  corpus size: {n_facts} facts, NGram candidate limit=50\n")

            # ── Lexical: first call vs warmed repeat (same query) ──────────────
            first_lex, res_first = timeit_fn(
                lambda: pipeline._retrieve_from_store(queries[0], k=5, retrieval_mode="lexical"), n=1)
            warm_lex, res_warm = timeit_fn(
                lambda: pipeline._retrieve_from_store(queries[0], k=5, retrieval_mode="lexical"), n=20)
            print_metrics("lexical: first call", first_lex, f"top_k_returned={len(res_first)}")
            print_metrics("lexical: warmed repeat x20", warm_lex, f"top_k_returned={len(res_warm)}")

            # ── Hybrid: first call (cold singleton) vs warmed repeat ───────────
            pipeline._HYBRID_RETRIEVER = None
            pipeline._HYBRID_DIRTY = True
            hybrid_counter.rebuilds = 0
            dense_counter.calls = 0

            first_hyb, res_first_h = timeit_fn(
                lambda: pipeline._retrieve_from_store(queries[0], k=5, retrieval_mode="hybrid"), n=1)
            rebuilds_after_first = hybrid_counter.rebuilds
            dense_after_first = dense_counter.calls

            warm_hyb, res_warm_h = timeit_fn(
                lambda: pipeline._retrieve_from_store(queries[0], k=5, retrieval_mode="hybrid"), n=20)
            rebuilds_after_warm = hybrid_counter.rebuilds
            dense_after_warm = dense_counter.calls

            print_metrics("hybrid: first call (cold)", first_hyb,
                          f"rebuilds={rebuilds_after_first} dense_calls={dense_after_first} "
                          f"top_k_returned={len(res_first_h)}")
            print_metrics("hybrid: warmed repeat x20 (same query)", warm_hyb,
                          f"rebuilds+={rebuilds_after_warm - rebuilds_after_first} "
                          f"dense_calls+={dense_after_warm - dense_after_first} "
                          f"top_k_returned={len(res_warm_h)}")

            # ── Hybrid: NGram candidate-set churn (5 distinct queries) ─────────
            hybrid_counter.rebuilds = 0
            dense_counter.calls = 0
            churn_stats = []
            for q in queries:
                m, res = timeit_fn(
                    lambda q=q: pipeline._retrieve_from_store(q, k=5, retrieval_mode="hybrid"), n=5)
                churn_stats.append((q, m["mean_ms"], len(res)))

            print("\n  hybrid: 5 distinct queries x 5 reps each (NGram candidate churn):")
            for q, mean_ms, topk in churn_stats:
                print(f"    {q:<32} mean={mean_ms:>9.4f}ms  top_k_returned={topk}")
            print(f"  hybrid: HybridRetriever singleton rebuilds across those 25 calls: "
                  f"{hybrid_counter.rebuilds}")
            print(f"  hybrid: DenseRetriever.retrieve() calls across those 25 calls: "
                  f"{dense_counter.calls}")
        finally:
            pipeline._NGRAM_INDEX = old_ngram
            mem._GLOBAL_STORE, mem._L0 = old_store, old_l0
            store.close()
            dense_counter.uninstall()
            pipeline.HybridRetriever = old_pipeline_hybrid_cls


def section_b_instrumented_dense_lifecycle():
    """Environment-independent proof of the PR #91 lifecycle fix: install a
    synthetic (non-ML) SentenceTransformer stand-in, then send many *different*
    NGram-narrowed candidate sets at the same corpus and count model loads /
    encode() calls directly — this is what the fix bounds."""
    print_header("B. Instrumented DenseRetriever lifecycle (synthetic backend)")
    print("  Purpose: prove the rebuild-storm fix numerically, independent of whether\n"
          "  the optional `sentence-transformers` extra is installed here. Not a\n"
          "  latency measurement — these are call counters against a fake, instant\n"
          "  model so the test is deterministic and dependency-free.\n")

    import core.hybrid_retriever as hr
    import core.pipeline as pipeline

    class _FakeSentenceTransformer:
        instances = 0
        encoded_texts = []

        def __init__(self, model_name):
            type(self).instances += 1

        def encode(self, texts, normalize_embeddings=True):
            type(self).encoded_texts.extend(texts)
            return [[((hash((t, i)) % 997) / 997.0) for i in range(6)] for t in texts]

    fake_module = types.ModuleType("sentence_transformers")
    fake_module.SentenceTransformer = _FakeSentenceTransformer
    old_module = sys.modules.get("sentence_transformers")
    sys.modules["sentence_transformers"] = fake_module

    old_available = hr.DenseRetriever._AVAILABLE
    old_model_cache = hr.DenseRetriever._MODEL_CACHE
    old_vector_cache = hr.DenseRetriever._VECTOR_CACHE
    hr.DenseRetriever._AVAILABLE = None
    hr.DenseRetriever._MODEL_CACHE = {}
    hr.DenseRetriever._VECTOR_CACHE = {}

    old_singleton = pipeline._HYBRID_RETRIEVER
    old_dirty = pipeline._HYBRID_DIRTY
    old_count = pipeline._HYBRID_FACTS_COUNT
    old_ids = pipeline._HYBRID_FACT_IDS
    pipeline._HYBRID_RETRIEVER = None
    pipeline._HYBRID_DIRTY = True
    pipeline._HYBRID_FACTS_COUNT = 0
    pipeline._HYBRID_FACT_IDS = frozenset()

    try:
        n_corpus = 5000
        corpus = make_facts(n_corpus)
        candidate_size = 50
        n_distinct_queries = 40  # 40 different NGram-narrowed 50-fact subsets

        for i in range(n_distinct_queries):
            start = (i * candidate_size) % (n_corpus - candidate_size)
            candidates = corpus[start:start + candidate_size]
            pipeline._get_hybrid_retriever(candidates)

        print(f"  corpus size: {n_corpus} synthetic facts")
        print(f"  distinct NGram-narrowed candidate sets sent: {n_distinct_queries} "
              f"({candidate_size} facts each, all disjoint)")
        print(f"  model constructions (_FakeSentenceTransformer.__init__ calls): "
              f"{_FakeSentenceTransformer.instances}  (expected: 1 — loaded once, ever)")
        print(f"  total texts ever encoded: {len(_FakeSentenceTransformer.encoded_texts)}  "
              f"(expected: {n_distinct_queries * candidate_size} — each of the "
              f"{n_distinct_queries * candidate_size} distinct facts encoded exactly once)")

        # Now revisit an already-seen candidate set — must cost zero new encodes.
        before = len(_FakeSentenceTransformer.encoded_texts)
        pipeline._get_hybrid_retriever(corpus[0:candidate_size])
        after = len(_FakeSentenceTransformer.encoded_texts)
        print(f"  re-visiting the first candidate set again: "
              f"{after - before} new encodes (expected: 0)")
    finally:
        pipeline._HYBRID_RETRIEVER = old_singleton
        pipeline._HYBRID_DIRTY = old_dirty
        pipeline._HYBRID_FACTS_COUNT = old_count
        pipeline._HYBRID_FACT_IDS = old_ids
        hr.DenseRetriever._AVAILABLE = old_available
        hr.DenseRetriever._MODEL_CACHE = old_model_cache
        hr.DenseRetriever._VECTOR_CACHE = old_vector_cache
        if old_module is not None:
            sys.modules["sentence_transformers"] = old_module
        else:
            sys.modules.pop("sentence_transformers", None)


if __name__ == "__main__":
    print("\n" + "#" * 78)
    print("  VELANTRIM — RETRIEVAL ROUTING BENCHMARK (PR #91 Increment 2)")
    print("#" * 78)

    section_a_real_components()
    section_b_instrumented_dense_lifecycle()

    print("\n" + "#" * 78)
    print("  DONE. Numbers above are live measurements from this run only —")
    print("  re-run on your own hardware before quoting them elsewhere.")
    print("#" * 78 + "\n")
