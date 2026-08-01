#!/usr/bin/env python3
"""Run the committed Reader Core synthetic benchmark as an end-to-end smoke test.

This proves that source-controlled manifests, observations, thresholds, report
aggregation, promotion review, and canonical bundle serialization remain wired
together. Synthetic success is not production evidence and never authorizes live
integration.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.reader_benchmark_runner import (  # noqa: E402
    ReaderBenchmarkError,
    ReaderBenchmarkRunner,
    load_benchmark_input,
    load_evaluation_manifest,
    load_promotion_thresholds,
    write_canonical_json,
)
from core.reader_evaluation import PromotionDecision  # noqa: E402

FIXTURE_ROOT = REPO_ROOT / "tests" / "fixtures" / "reader_core"
DEFAULT_MANIFEST = FIXTURE_ROOT / "rdr_09_synthetic_evaluation.json"
DEFAULT_INPUT = FIXTURE_ROOT / "rdr_10_benchmark_input.json"
DEFAULT_THRESHOLDS = FIXTURE_ROOT / "rdr_10_thresholds.json"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the committed Reader Core synthetic end-to-end smoke benchmark."
    )
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--thresholds", type=Path, default=DEFAULT_THRESHOLDS)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        manifest = load_evaluation_manifest(args.manifest)
        benchmark_input = load_benchmark_input(args.input)
        thresholds = load_promotion_thresholds(args.thresholds)
        bundle = ReaderBenchmarkRunner().run(
            manifest,
            benchmark_input,
            thresholds,
        )
        if bundle.review.decision is not PromotionDecision.INSUFFICIENT_EVIDENCE:
            raise ReaderBenchmarkError(
                "synthetic-only smoke must remain insufficient_evidence"
            )
        if bundle.review.live_integration_authorized:
            raise ReaderBenchmarkError(
                "synthetic smoke cannot authorize live integration"
            )
        if not bundle.review.operator_go_required:
            raise ReaderBenchmarkError(
                "synthetic smoke must preserve Operator GO requirement"
            )
        if bundle.report.metrics.synthetic_case_count != len(manifest.cases):
            raise ReaderBenchmarkError(
                "synthetic case count must equal committed manifest size"
            )
        if bundle.report.metrics.real_case_count != 0:
            raise ReaderBenchmarkError(
                "synthetic smoke must not claim real-corpus evidence"
            )
        if bundle.report.metrics.human_labelled_case_count != 0:
            raise ReaderBenchmarkError(
                "synthetic smoke must not claim human-labelled evidence"
            )
        write_canonical_json(args.output, bundle)
    except ReaderBenchmarkError as exc:
        print(f"reader synthetic smoke error: {exc}", file=sys.stderr)
        return 2

    summary = {
        "bundle_id": bundle.bundle_id,
        "decision": bundle.review.decision.value,
        "human_labelled_case_count": (
            bundle.report.metrics.human_labelled_case_count
        ),
        "live_integration_authorized": (
            bundle.review.live_integration_authorized
        ),
        "operator_go_required": bundle.review.operator_go_required,
        "output": str(args.output),
        "real_case_count": bundle.report.metrics.real_case_count,
        "synthetic_case_count": bundle.report.metrics.synthetic_case_count,
    }
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
