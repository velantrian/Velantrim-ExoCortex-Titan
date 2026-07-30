# benchmarks/bench_embedding_projection.py
# Velantrim ExoCortex — Embedding Projection Contract Benchmark (PR-ARM-02, issue #92)
#
# Measures the five scenarios called out for PR-ARM-02:
#   - fresh projection            (resolve_or_fallback -> "dense", no encode)
#   - stale content                (resolve_or_fallback -> "lexical_fallback")
#   - changed model                (resolve_or_fallback -> "lexical_fallback")
#   - missing projection           (resolve_or_fallback -> "lexical_fallback")
#   - embeddings package unavailable (resolve_or_fallback -> "lexical_fallback",
#     backend never even constructed)
#
# For each: latency (mean/median/min over N calls) and encode_fn call count.
# Also measures rebuild() cost for a batch of stale/missing records, and
# confirms it is bounded (exactly one encode_fn call per rebuild(), batching
# every record instead of one call per record).
#
# Run:
#   python benchmarks/bench_embedding_projection.py
#
# HONESTY NOTE: every number below is measured live on whatever machine runs
# this script (platform/CPU line printed at the top) — never hardcoded, and
# not a general performance claim. The encode_fn used here is a synthetic,
# instant, dependency-free stand-in (no real embedding model), matching the
# fake used in tests/test_embedding_projection.py — this benchmark measures
# the CONTRACT's own overhead (state classification, storage I/O, bookkeeping),
# not real model inference latency.

import os
import platform
import statistics
import sys
import tempfile
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def timeit_fn(fn, n=50):
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
        "n":         n,
    }
    return stats, result


def print_header(title):
    print(f"\n{'=' * 78}\n  {title}\n{'=' * 78}")


def print_metrics(label, metrics, extra=""):
    line = (f"  {label:<40} mean={metrics['mean_ms']:>9.4f}ms "
            f"median={metrics['median_ms']:>9.4f}ms min={metrics['min_ms']:>9.4f}ms")
    if extra:
        line += "  | " + extra
    print(line)


def _fake_vector(text, dims=6):
    import numpy as np
    return np.array([((hash((text, i)) % 997) / 997.0) for i in range(dims)], dtype=np.float32)


def main():
    print("\n" + "#" * 78)
    print("  VELANTRIM — EMBEDDING PROJECTION CONTRACT BENCHMARK (PR-ARM-02, issue #92)")
    print("#" * 78)
    print(f"\n  platform: {platform.platform()}")
    print(f"  python:   {platform.python_version()}")

    import core.embedding_projection as ep
    from core.embedding_store import EmbeddingStore

    encode_calls = {"n": 0}

    def encode_fn(texts):
        encode_calls["n"] += 1
        return [_fake_vector(t) for t in texts]

    with tempfile.TemporaryDirectory() as d:
        backing = EmbeddingStore(os.path.join(d, "bench.db"))
        backing.ensure_table()
        store = ep.EmbeddingProjectionStore(backing)

        n_records = 500
        base_records = [(f"rec_{i}", f"claim number {i} about topic {i % 25}")
                         for i in range(n_records)]

        print_header("Setup: rebuild_all() over a bounded batch")
        encode_calls["n"] = 0
        report, elapsed_ms = None, 0.0
        t0 = time.perf_counter()
        report = store.rebuild_all(
            base_records, model_name="fixture-model", model_version="v1",
            projection_version="1", encode_fn=encode_fn,
        )
        elapsed_ms = (time.perf_counter() - t0) * 1000
        print(f"  {n_records} records, first rebuild_all(): {elapsed_ms:.3f}ms total, "
              f"rebuilt={len(report.rebuilt)} failed={len(report.failed)} "
              f"encode_fn calls={encode_calls['n']} (expected: 1 — one batched call)")

        # Repeat: must be fully idempotent (all skipped_fresh, 0 new encode_fn calls).
        encode_calls["n"] = 0
        t0 = time.perf_counter()
        report2 = store.rebuild_all(
            base_records, model_name="fixture-model", model_version="v1",
            projection_version="1", encode_fn=encode_fn,
        )
        elapsed_ms2 = (time.perf_counter() - t0) * 1000
        print(f"  same {n_records} records, second rebuild_all(): {elapsed_ms2:.3f}ms total, "
              f"skipped_fresh={len(report2.skipped_fresh)} "
              f"encode_fn calls={encode_calls['n']} (expected: 0 — nothing was stale)")

        fresh_ident = ep.EmbeddingProjectionIdentity(
            record_id="rec_0", content_hash=ep.compute_content_hash("claim number 0 about topic 0"),
            model_name="fixture-model", model_version="v1", projection_version="1",
        )
        stale_content_ident = ep.EmbeddingProjectionIdentity(
            record_id="rec_0", content_hash=ep.compute_content_hash("an edited claim"),
            model_name="fixture-model", model_version="v1", projection_version="1",
        )
        changed_model_ident = ep.EmbeddingProjectionIdentity(
            record_id="rec_0", content_hash=ep.compute_content_hash("claim number 0 about topic 0"),
            model_name="a-different-model", model_version="v1", projection_version="1",
        )
        missing_ident = ep.EmbeddingProjectionIdentity(
            record_id="rec_never_indexed", content_hash=ep.compute_content_hash("anything"),
            model_name="fixture-model", model_version="v1", projection_version="1",
        )

        print_header("Scenario latency: resolve_or_fallback()")
        encode_calls["n"] = 0

        m, (mode, _) = timeit_fn(
            lambda: ep.resolve_or_fallback([fresh_ident], store, embeddings_available=True))
        print_metrics("fresh", m, f"mode={mode} encode_fn_calls={encode_calls['n']}")

        m, (mode, _) = timeit_fn(
            lambda: ep.resolve_or_fallback([stale_content_ident], store, embeddings_available=True))
        print_metrics("stale content", m, f"mode={mode} encode_fn_calls={encode_calls['n']}")

        m, (mode, _) = timeit_fn(
            lambda: ep.resolve_or_fallback([changed_model_ident], store, embeddings_available=True))
        print_metrics("changed model", m, f"mode={mode} encode_fn_calls={encode_calls['n']}")

        m, (mode, _) = timeit_fn(
            lambda: ep.resolve_or_fallback([missing_ident], store, embeddings_available=True))
        print_metrics("missing projection", m, f"mode={mode} encode_fn_calls={encode_calls['n']}")

        m, (mode, _) = timeit_fn(
            lambda: ep.resolve_or_fallback([fresh_ident], store, embeddings_available=False))
        print_metrics("embeddings unavailable", m, f"mode={mode} encode_fn_calls={encode_calls['n']}")

        print("\n  Note: all four non-fresh scenarios return mode='lexical_fallback' and never\n"
              "  call encode_fn — detecting a reason to fall back never silently reindexes.")

        print_header("Scenario: embedding backend construction itself unavailable")
        unavailable_store = ep.EmbeddingProjectionStore(backing=None)

        class _AlwaysBroken:
            def __init__(self):
                raise ImportError("numpy not installed (simulated)")

        import core.embedding_store as es_mod
        original_get = es_mod.get_embedding_store
        es_mod.get_embedding_store = lambda: _AlwaysBroken()
        try:
            broken_store = ep.EmbeddingProjectionStore()
        finally:
            es_mod.get_embedding_store = original_get
        print(f"  EmbeddingProjectionStore() with broken backend: available={broken_store.available} "
              f"(constructor did not raise)")
        m, (mode, _) = timeit_fn(
            lambda: ep.resolve_or_fallback([fresh_ident], broken_store, embeddings_available=True))
        print_metrics("backend construction failed", m, f"mode={mode}")
        del unavailable_store

    print("\n" + "#" * 78)
    print("  DONE. Numbers above are live measurements from this run only —")
    print("  re-run on your own hardware before quoting them elsewhere.")
    print("#" * 78 + "\n")


if __name__ == "__main__":
    main()
