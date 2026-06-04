# benchmarks/bench_pipeline.py
# Velantrim ExoCortex — Performance Benchmarks
# v1.0.0
#
# Запуск:
#   pip install pytest-benchmark
#   pytest benchmarks/bench_pipeline.py -v --benchmark-sort=mean
#   pytest benchmarks/bench_pipeline.py -v --benchmark-json=results.json
#
# Или без pytest-benchmark (простой timeit):
#   python benchmarks/bench_pipeline.py
#
# Что меряем:
#   1. store_fact vs store_facts_batch  (главная оптимизация v8.2.1)
#   2. retrieve: NGram+Hybrid vs full BM25
#   3. TruthGate: MVP vs BALANCED vs PRECISION
#   4. MHI: с кэшем vs без
#   5. Pipeline.run() end-to-end при разных размерах store

import os
import statistics
import tempfile
import time
from contextlib import contextmanager
from typing import Any

# ─── HELPERS ──────────────────────────────────────────────────────────────────

@contextmanager
def tmp_store():
    with tempfile.TemporaryDirectory() as d:
        from core.memory import make_store
        s = make_store(os.path.join(d, "bench.db"))
        try:
            yield s
        finally:
            s.close()


def make_facts(n: int, prefix: str = "fact") -> list[dict[str, Any]]:
    return [
        {
            "fact_id":    f"{prefix}_{i}",
            "claim":      f"Fact number {i}: this is a claim about topic {i % 20}",
            "source":     f"source_{i % 5}",
            "confidence": 0.5 + (i % 50) / 100,
        }
        for i in range(n)
    ]


def timeit_fn(fn, n: int = 100) -> dict[str, float]:
    """Простой таймер: n вызовов, возвращает статистику в мс."""
    times = []
    for _ in range(n):
        t0 = time.perf_counter()
        fn()
        times.append((time.perf_counter() - t0) * 1000)
    return {
        "mean_ms":   round(statistics.mean(times), 3),
        "median_ms": round(statistics.median(times), 3),
        "min_ms":    round(min(times), 3),
        "max_ms":    round(max(times), 3),
        "stdev_ms":  round(statistics.stdev(times) if len(times) > 1 else 0, 3),
        "n":         n,
    }


def print_result(name: str, result: dict[str, float], compare: dict = None):
    "█" * int(result["mean_ms"] / 2)
    print(f"  {name:<45} mean={result['mean_ms']:>8.2f}ms  "
          f"median={result['median_ms']:>8.2f}ms  "
          f"min={result['min_ms']:>6.2f}ms")
    if compare:
        speedup = compare["mean_ms"] / result["mean_ms"]
        print(f"    {'→ speedup vs baseline:':<43} {speedup:.1f}x faster")


def section(title: str):
    print(f"\n{'═'*70}")
    print(f"  {title}")
    print(f"{'═'*70}")


# ═══════════════════════════════════════════════════════════════════════════════
# 1. store_fact vs store_facts_batch
# ═══════════════════════════════════════════════════════════════════════════════

def bench_store_individual_vs_batch():
    section("1. store_fact (N×1) vs store_facts_batch (1×N)")

    # AUDIT-FIX v8.4.0: уникальные fact_id на каждой итерации (через iter-suffix),
    # иначе после первой итерации идут UPDATE'ы через ON CONFLICT, и бенчмарк
    # меряет смесь INSERT+UPDATE, а не чистый INSERT как заявлено в названии.
    iter_counter = {"i": 0}

    def fresh_facts(n: int) -> list:
        iter_counter["i"] += 1
        return [
            {
                "fact_id":    f"bench_{iter_counter['i']}_{i}",
                "claim":      f"Fact number {i}: about topic {i % 20}",
                "source":     f"source_{i % 5}",
                "confidence": 0.5 + (i % 50) / 100,
            }
            for i in range(n)
        ]

    for n in [10, 100, 500]:
        print(f"\n  N = {n} фактов:")

        # Baseline: N отдельных store_fact (каждый — отдельный connection)
        with tmp_store() as s:
            baseline = timeit_fn(
                lambda: [s.store_fact(f) for f in fresh_facts(n)],
                n=10
            )
        print_result(f"  store_fact × {n} (N connections, чистый INSERT)", baseline)

        # Оптимизированный: один store_facts_batch (1 transaction)
        with tmp_store() as s:
            optimized = timeit_fn(
                lambda: s.store_facts_batch(fresh_facts(n)),
                n=10
            )
        print_result(f"  store_facts_batch × {n} (1 connection, batch)", optimized, baseline)


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Retrieval: NGram+Hybrid vs plain BM25
# ═══════════════════════════════════════════════════════════════════════════════

def bench_retrieval():
    section("2. Retrieval: NGram+Hybrid vs plain BM25")
    print("  ⚠️ ВНИМАНИЕ: HybridRetriever меряется как SINGLETON (создан один раз).")
    print("  Это идеальный случай, соответствует v8.4.0 поведению pipeline.")
    print("  До v8.4.0 pipeline создавал HybridRetriever на каждый запрос.")

    try:
        from core.hybrid_retriever import HybridRetriever
        from core.pipeline import BM25, DATABASE, tokenize
    except ImportError as e:
        print(f"  SKIP: {e}")
        return

    print("\n  Размер базы: DATABASE (5 фактов) — TODO: расширить до 1000+ для prod-данных")

    # Plain BM25 — тот же объём работы что и HybridRetriever (tokenize + score + sort)
    # AUDIT-FIX v8.4.0: добавлен tokenize в baseline, иначе сравнение нечестное
    def baseline_fn():
        terms = tokenize("quantum entanglement physics")
        corpus = [tokenize(item["text"]) for item in DATABASE]
        bm25_local = BM25(corpus)
        return sorted(
            [(i, bm25_local.score(i, terms)) for i in range(len(DATABASE))],
            key=lambda x: -x[1]
        )[:3]

    baseline = timeit_fn(baseline_fn, n=1000)
    print_result("  Plain BM25 (полный flow: tokenize+score+sort)", baseline)

    # HybridRetriever (singleton — создан ОДИН раз, как в v8.4.0 pipeline)
    facts = [{"fact_id": d["id"], "claim": d["text"],
              "source": d["source"], "confidence": d["confidence"]}
             for d in DATABASE]
    try:
        retriever = HybridRetriever(facts)
        optimized = timeit_fn(
            lambda: retriever.retrieve("quantum entanglement physics", top_k=3),
            n=1000  # AUDIT-FIX v8.4.0: одинаковое n с baseline для честного сравнения
        )
        print_result("  HybridRetriever singleton (BM25+RRF)", optimized, baseline)

        # Дополнительно — измерим per-request init (как было до v8.4.0)
        def per_request_init():
            r = HybridRetriever(facts)
            return r.retrieve("quantum entanglement physics", top_k=3)

        per_req = timeit_fn(per_request_init, n=10)  # медленно — n=10 хватит
        print_result("  HybridRetriever per-request init (старое поведение)", per_req, baseline)
        print("  → разница singleton vs per-request показывает выигрыш фикса v8.4.0")
    except Exception as e:
        print(f"  HybridRetriever: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# 3. TruthGate: MVP vs BALANCED vs PRECISION
# ═══════════════════════════════════════════════════════════════════════════════

def bench_truth_gate_modes():
    section("3. TruthGate: MVP vs BALANCED vs PRECISION")

    from core.pipeline import truth_gate

    facts_pack = {"facts": [
        {"fact_id": f"f{i}", "claim": f"claim {i}", "source": "bench",
         "confidence": 0.9,
         "metadata": {"evidence_refs": [f"ref{j}" for j in range(3)]}}
        for i in range(5)
    ]}

    print("\n  5 фактов с evidence_refs × 3:")

    mvp = timeit_fn(lambda: truth_gate(facts_pack, mode=None), n=5000)
    print_result("  truth_gate(mode=None) — MVP", mvp)

    try:
        import core.memory as mem
        with tempfile.TemporaryDirectory() as d:
            from core.memory import make_store
            s = make_store(os.path.join(d, "tg.db"))
            old_store = mem._GLOBAL_STORE
            mem._GLOBAL_STORE = s
            try:
                balanced = timeit_fn(lambda: truth_gate(facts_pack, mode="BALANCED"), n=500)
                print_result("  truth_gate(mode=BALANCED)", balanced, mvp)

                precision = timeit_fn(lambda: truth_gate(facts_pack, mode="PRECISION"), n=500)
                print_result("  truth_gate(mode=PRECISION)", precision, mvp)
            finally:
                mem._GLOBAL_STORE = old_store
                s.close()
    except Exception as e:
        print(f"  Real TruthGate modes: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# 4. MHI: с кэшем vs без
# ═══════════════════════════════════════════════════════════════════════════════

def bench_mhi():
    section("4. MHI: calculate() vs кэшированный /health")

    try:
        from core.mhi import MHICalculator
    except ImportError as e:
        print(f"  SKIP: {e}")
        return

    with tmp_store() as s:
        # Заполняем 100 фактов
        s.store_facts_batch(make_facts(100))

        calc = MHICalculator(s)
        baseline = timeit_fn(lambda: calc.calculate(), n=50)
        print_result("  MHICalculator.calculate() без кэша", baseline)

        # AUDIT-FIX v8.4.0: честное сравнение кэша.
        # Раньше: TTL=60s + n=1000 → 1 cache miss + 999 hits → mean доминируется
        # cache hit'ами, "speedup" в 1000x — артефакт методологии.
        # Сейчас: 2 режима — full hits (только hot path) и cache_miss (только cold).
        cache = {"data": None, "at": 0.0}
        TTL = 60.0

        def cached_mhi_hot():
            """Чистый hot-path: кэш всегда заполнен."""
            now = time.time()
            if cache["data"] is not None and (now - cache["at"]) < TTL:
                return cache["data"]
            result = calc.calculate()
            cache["data"] = result
            cache["at"] = now
            return result

        cached_mhi_hot()  # прогрев
        hot = timeit_fn(cached_mhi_hot, n=1000)
        print_result("  MHI cache HOT (cache hit only)", hot, baseline)

        def cached_mhi_cold():
            """Чистый cold-path: invalidation между вызовами."""
            cache["data"] = None  # форсируем miss
            now = time.time()
            result = calc.calculate()
            cache["data"] = result
            cache["at"] = now
            return result

        cold = timeit_fn(cached_mhi_cold, n=50)
        print_result("  MHI cache COLD (cache miss)", cold, baseline)
        print("  → HOT/COLD сравнение показывает реальную ценность кэша")


# ═══════════════════════════════════════════════════════════════════════════════
# 5. Pipeline.run() end-to-end
# ═══════════════════════════════════════════════════════════════════════════════

def bench_pipeline_end_to_end():
    section("5. pipeline.run() end-to-end (DATABASE mock)")

    try:
        import core.memory as mem
        from core.pipeline import run
    except ImportError as e:
        print(f"  SKIP: {e}")
        return

    queries = [
        "quantum entanglement",
        "DNA genetic information",
        "Earth revolves Sun",
        "human brain neurons",
        "water boils temperature",
    ]

    print("\n  5 разных запросов × 20 итераций:")

    with tempfile.TemporaryDirectory() as d:
        from core.memory import make_store
        s = make_store(os.path.join(d, "pipe.db"))
        old_store = mem._GLOBAL_STORE
        old_l0    = mem._L0
        mem._GLOBAL_STORE = s
        mem._L0           = s._l0

        try:
            for query in queries:
                result = timeit_fn(lambda q=query: run(q), n=20)
                status = "✅" if not run(query).get("error") else "⚠️"
                print_result(f"  {status} '{query}'", result)
        finally:
            mem._GLOBAL_STORE = old_store
            mem._L0           = old_l0
            s.close()


# ═══════════════════════════════════════════════════════════════════════════════
# 6. store_facts_batch stress test
# ═══════════════════════════════════════════════════════════════════════════════

def bench_batch_stress():
    section("6. store_facts_batch — stress test (большие объёмы)")

    print()
    for n in [100, 500, 1_000, 5_000]:
        with tmp_store() as s:
            facts = make_facts(n)
            t0 = time.perf_counter()
            result = s.store_facts_batch(facts)
            elapsed_ms = (time.perf_counter() - t0) * 1000
            per_fact_us = elapsed_ms / n * 1000

            print(f"  N={n:<6}  total={elapsed_ms:>8.1f}ms  "
                  f"per_fact={per_fact_us:>6.1f}μs  "
                  f"stored={result['stored']}  errors={result['errors']}")


# ═══════════════════════════════════════════════════════════════════════════════
# pytest-benchmark интеграция
# ═══════════════════════════════════════════════════════════════════════════════

try:
    import pytest

    @pytest.fixture
    def bench_store(tmp_path):
        from core.memory import make_store
        s = make_store(str(tmp_path / "bench.db"))
        yield s
        s.close()

    def test_bench_store_fact_single(benchmark, bench_store):
        fact = {"fact_id": "b1", "claim": "test claim",
                "source": "bench", "confidence": 0.8}
        benchmark(bench_store.store_fact, fact)

    def test_bench_store_facts_batch_100(benchmark, bench_store):
        facts = make_facts(100)
        benchmark(bench_store.store_facts_batch, facts)

    def test_bench_get_fact(benchmark, bench_store):
        bench_store.store_fact({"fact_id": "get1", "claim": "x",
                                "source": "s", "confidence": 0.5})
        benchmark(bench_store.get_fact, "get1")

    def test_bench_get_all_facts_100(benchmark, bench_store):
        bench_store.store_facts_batch(make_facts(100))
        benchmark(bench_store.get_all_facts)

    def test_bench_truth_gate_mvp(benchmark):
        from core.pipeline import truth_gate
        pack = {"facts": [{"fact_id": "t1", "claim": "x",
                           "source": "s", "confidence": 0.9}]}
        benchmark(truth_gate, pack)

    def test_bench_pipeline_run(benchmark, tmp_path, monkeypatch):
        import core.memory as mem
        from core.memory import make_store
        from core.pipeline import run
        s = make_store(str(tmp_path / "p.db"))
        monkeypatch.setattr(mem, "_GLOBAL_STORE", s)
        monkeypatch.setattr(mem, "_L0", s._l0)
        benchmark(run, "quantum entanglement")
        s.close()

except ImportError:
    pass  # pytest не установлен — только standalone режим


# ─── STANDALONE RUNNER ────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "▓" * 70)
    print("  VELANTRIM EXOCORTEX — PERFORMANCE BENCHMARKS v1.0.0")
    print("▓" * 70)

    bench_store_individual_vs_batch()
    bench_retrieval()
    bench_truth_gate_modes()
    bench_mhi()
    bench_pipeline_end_to_end()
    bench_batch_stress()

    print("\n" + "▓" * 70)
    print("  ГОТОВО. Для подробного отчёта:")
    print("  pytest benchmarks/bench_pipeline.py -v --benchmark-sort=mean")
    print("▓" * 70 + "\n")
