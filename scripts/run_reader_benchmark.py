#!/usr/bin/env python3
"""Run the local Reader Core benchmark and write a canonical report bundle.

Example:
    python scripts/run_reader_benchmark.py \
      --manifest tests/fixtures/reader_core/rdr_09_synthetic_evaluation.json \
      --input tests/fixtures/reader_core/rdr_10_benchmark_input.json \
      --thresholds tests/fixtures/reader_core/rdr_10_thresholds.json \
      --output artifacts/reader-core/benchmark-bundle.json

Optional detached authentication reads the secret only from an environment
variable; the secret is never accepted as a command-line value or written to
an artifact.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.reader_benchmark_runner import (  # noqa: E402
    ReaderBenchmarkError,
    ReaderBenchmarkRunner,
    ReaderBenchmarkSigner,
    load_benchmark_input,
    load_evaluation_manifest,
    load_promotion_thresholds,
    write_canonical_json,
)
from core.reader_evaluation import PromotionDecision  # noqa: E402


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Build a deterministic Reader Core evaluation bundle from local "
            "manifest, observation, and threshold JSON files."
        )
    )
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--thresholds", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--signature-output",
        type=Path,
        help="Optional detached signature JSON output path.",
    )
    parser.add_argument(
        "--hmac-key-env",
        help="Environment variable containing the HMAC secret.",
    )
    parser.add_argument(
        "--key-id",
        help="Non-secret identifier for the HMAC key.",
    )
    parser.add_argument(
        "--require-eligible",
        action="store_true",
        help=(
            "Exit 3 unless the review is eligible_for_operator_review. "
            "This never authorizes live integration."
        ),
    )
    return parser


def _signature_requested(args: argparse.Namespace) -> bool:
    values = (
        args.signature_output,
        args.hmac_key_env,
        args.key_id,
    )
    requested = any(value is not None for value in values)
    if requested and not all(value is not None for value in values):
        raise ReaderBenchmarkError(
            "--signature-output, --hmac-key-env, and --key-id must be used together"
        )
    return requested


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
        write_canonical_json(args.output, bundle)

        signature_written = False
        if _signature_requested(args):
            env_name = str(args.hmac_key_env)
            secret_text = os.environ.get(env_name)
            if secret_text is None:
                raise ReaderBenchmarkError(
                    f"HMAC environment variable is not set: {env_name}"
                )
            signature = ReaderBenchmarkSigner.sign(
                bundle,
                key_id=str(args.key_id),
                secret=secret_text.encode("utf-8"),
            )
            write_canonical_json(args.signature_output, signature)
            signature_written = True
    except ReaderBenchmarkError as exc:
        print(f"reader benchmark error: {exc}", file=sys.stderr)
        return 2

    summary = {
        "bundle_id": bundle.bundle_id,
        "decision": bundle.review.decision.value,
        "live_integration_authorized": (
            bundle.review.live_integration_authorized
        ),
        "operator_go_required": bundle.review.operator_go_required,
        "output": str(args.output),
        "report_id": bundle.report.report_id,
        "signature_written": signature_written,
    }
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    if (
        args.require_eligible
        and bundle.review.decision
        is not PromotionDecision.ELIGIBLE_FOR_OPERATOR_REVIEW
    ):
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
