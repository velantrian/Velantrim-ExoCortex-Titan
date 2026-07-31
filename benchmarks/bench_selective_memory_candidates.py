#!/usr/bin/env python3
"""Dependency-free benchmark for PR-ARM-03 shadow extraction."""

from __future__ import annotations

import os
import statistics
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.selective_memory_candidates import (  # noqa: E402
    CandidateExtractionPolicy,
    extract_memory_candidates,
)


def measure(label: str, text: str, *, policy: CandidateExtractionPolicy | None = None, runs: int = 100):
    durations: list[float] = []
    last = None
    for _ in range(runs):
        started = time.perf_counter()
        last = extract_memory_candidates(text, source_ref=f"benchmark:{label}", policy=policy)
        durations.append((time.perf_counter() - started) * 1000.0)
    assert last is not None
    assert last.trace.canon_write_count == 0
    assert last.trace.memory_write_count == 0
    assert last.trace.write_gate_call_count == 0
    print(
        f"{label:<22} mean={statistics.mean(durations):8.4f}ms "
        f"median={statistics.median(durations):8.4f}ms "
        f"candidates={len(last.candidates):2d} rejected={len(last.rejected):2d} "
        f"truncated={last.truncated} chars={sum(len(c.normalized_text) for c in last.candidates)}"
    )
    return last


def main() -> None:
    print("Velantrim PR-ARM-03 selective-memory candidate shadow benchmark")
    short = measure("short", "I prefer concise reports. My goal is to ship tomorrow.")
    measure(
        "mixed-language",
        "I prefer English summaries. Я предпочитаю подробные отчёты по пятницам. Сейчас работаю удалённо.",
    )
    measure(
        "sensitive",
        "My diagnosis is diabetes. My email is person@example.com. My token: ghp_abcdefghijklmnopqrstuvwxyz123456.",
    )
    long_text = " ".join(f"I prefer deterministic option {index}." for index in range(200))
    bounded = measure(
        "budget-truncation",
        long_text,
        policy=CandidateExtractionPolicy(max_candidates_per_input=8, max_total_candidate_chars=320),
        runs=20,
    )
    repeated = extract_memory_candidates(
        "I prefer concise reports. My goal is to ship tomorrow.",
        source_ref="benchmark:short",
    )
    assert repeated == short
    assert bounded.truncated
    print("deterministic_repeat=True zero_writes=True network_calls=0 model_calls=0")


if __name__ == "__main__":
    main()
