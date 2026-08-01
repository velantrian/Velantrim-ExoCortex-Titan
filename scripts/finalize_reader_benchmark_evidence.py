#!/usr/bin/env python3
"""Finalize one portable completed Reader Core benchmark envelope.

Example:
    python scripts/finalize_reader_benchmark_evidence.py \
      --envelope /secure/reader/finalization-envelope.json \
      --thresholds /secure/reader/thresholds.json \
      --bundle-output /secure/reader/benchmark-bundle.json \
      --signature-output /secure/reader/benchmark-signature.json \
      --evidence-output /secure/reader/signed-evidence.json \
      --hmac-key-env READER_BENCHMARK_HMAC_KEY \
      --key-id reader-benchmark-key-v1

The HMAC secret is read only from the named environment variable. The command
does not execute a pipeline, calibrate thresholds, record Operator GO, or
authorize shadow/live integration.
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

from core.reader_benchmark_finalization import (  # noqa: E402
    ReaderBenchmarkFinalizationError,
    ReaderCompletedBatchFinalizer,
)
from core.reader_benchmark_portability import (  # noqa: E402
    ReaderBenchmarkPortabilityError,
    load_finalization_envelope,
)
from core.reader_benchmark_runner import (  # noqa: E402
    ReaderBenchmarkError,
    load_promotion_thresholds,
    write_canonical_json,
)
from core.reader_evaluation import PromotionDecision  # noqa: E402


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Finalize a canonical complete-success Reader Core envelope into "
            "a benchmark bundle, detached signature, and signed evidence index."
        )
    )
    parser.add_argument("--envelope", required=True, type=Path)
    parser.add_argument("--thresholds", required=True, type=Path)
    parser.add_argument("--bundle-output", required=True, type=Path)
    parser.add_argument("--signature-output", required=True, type=Path)
    parser.add_argument("--evidence-output", required=True, type=Path)
    parser.add_argument("--hmac-key-env", required=True)
    parser.add_argument("--key-id", required=True)
    parser.add_argument(
        "--require-eligible",
        action="store_true",
        help=(
            "Exit 3 unless the result is eligible_for_operator_review. "
            "Eligibility still does not record Operator GO or authorize live use."
        ),
    )
    return parser


def _validate_outputs(paths: tuple[Path, ...]) -> None:
    resolved = tuple(path.resolve() for path in paths)
    if len(set(resolved)) != len(resolved):
        raise ReaderBenchmarkFinalizationError(
            "bundle, signature, and evidence outputs must be distinct"
        )
    existing = tuple(str(path) for path in paths if path.exists())
    if existing:
        raise ReaderBenchmarkFinalizationError(
            f"refusing to overwrite existing output files: {existing}"
        )


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    outputs = (
        args.bundle_output,
        args.signature_output,
        args.evidence_output,
    )
    try:
        _validate_outputs(outputs)
        envelope = load_finalization_envelope(args.envelope)
        thresholds = load_promotion_thresholds(args.thresholds)
        secret_text = os.environ.get(str(args.hmac_key_env))
        if secret_text is None:
            raise ReaderBenchmarkFinalizationError(
                f"HMAC environment variable is not set: {args.hmac_key_env}"
            )
        evidence = ReaderCompletedBatchFinalizer().finalize_envelope(
            envelope=envelope,
            thresholds=thresholds,
            key_id=str(args.key_id),
            secret=secret_text.encode("utf-8"),
        )
        write_canonical_json(args.bundle_output, evidence.benchmark_bundle)
        write_canonical_json(args.signature_output, evidence.bundle_signature)
        write_canonical_json(args.evidence_output, evidence)
    except (
        ReaderBenchmarkFinalizationError,
        ReaderBenchmarkPortabilityError,
        ReaderBenchmarkError,
        OSError,
        UnicodeError,
    ) as exc:
        print(f"reader benchmark finalization error: {exc}", file=sys.stderr)
        return 2

    summary = {
        "benchmark_bundle_id": evidence.benchmark_bundle.bundle_id,
        "bundle_output": str(args.bundle_output),
        "decision": evidence.decision.value,
        "envelope_id": envelope.envelope_id,
        "evidence_id": evidence.evidence_id,
        "evidence_output": str(args.evidence_output),
        "failed_attempt_receipt_count": len(
            evidence.failed_attempt_receipt_ids
        ),
        "live_integration_authorized": evidence.live_integration_authorized,
        "operator_go_required": evidence.operator_go_required,
        "receipt_count": len(evidence.receipt_ids),
        "signature_id": evidence.bundle_signature.signature_id,
        "signature_output": str(args.signature_output),
    }
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    if (
        args.require_eligible
        and evidence.decision
        is not PromotionDecision.ELIGIBLE_FOR_OPERATOR_REVIEW
    ):
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
