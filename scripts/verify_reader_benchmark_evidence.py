#!/usr/bin/env python3
"""Offline verification of canonical Reader Core benchmark evidence artifacts.

Example:
    python scripts/verify_reader_benchmark_evidence.py \
      --bundle /secure/reader/benchmark-bundle.json \
      --signature /secure/reader/benchmark-signature.json \
      --evidence /secure/reader/signed-evidence.json \
      --hmac-key-env READER_BENCHMARK_HMAC_KEY \
      --verification-output /secure/reader/verification-receipt.json

The command is read-only with respect to the supplied benchmark artifacts. It
performs no model execution and grants no Operator or live authority.
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

from core.reader_benchmark_evidence_verification import (  # noqa: E402
    ReaderBenchmarkEvidenceVerificationError,
    ReaderBenchmarkEvidenceVerifier,
)
from core.reader_benchmark_runner import write_canonical_json  # noqa: E402
from core.reader_evaluation import PromotionDecision  # noqa: E402


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Reconstruct, authenticate, and verify canonical Reader Core "
            "benchmark bundle, signature, and signed-evidence files offline."
        )
    )
    parser.add_argument("--bundle", required=True, type=Path)
    parser.add_argument("--signature", required=True, type=Path)
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--hmac-key-env", required=True)
    parser.add_argument(
        "--verification-output",
        type=Path,
        help="Optional canonical verification receipt output.",
    )
    parser.add_argument(
        "--require-eligible",
        action="store_true",
        help=(
            "Exit 3 unless the verified review is eligible_for_operator_review. "
            "Eligibility still does not record Operator GO or authorize live use."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.verification_output is not None and args.verification_output.exists():
            raise ReaderBenchmarkEvidenceVerificationError(
                "refusing to overwrite existing verification output"
            )
        secret_text = os.environ.get(str(args.hmac_key_env))
        if secret_text is None:
            raise ReaderBenchmarkEvidenceVerificationError(
                f"HMAC environment variable is not set: {args.hmac_key_env}"
            )
        receipt = ReaderBenchmarkEvidenceVerifier().verify_files(
            bundle_path=args.bundle,
            signature_path=args.signature,
            evidence_path=args.evidence,
            secret=secret_text.encode("utf-8"),
        )
        if args.verification_output is not None:
            write_canonical_json(args.verification_output, receipt)
    except (
        ReaderBenchmarkEvidenceVerificationError,
        OSError,
        UnicodeError,
    ) as exc:
        print(f"reader benchmark verification error: {exc}", file=sys.stderr)
        return 2

    summary = {
        "benchmark_bundle_id": receipt.benchmark_bundle_id,
        "decision": receipt.decision.value,
        "evidence_id": receipt.evidence_id,
        "key_id": receipt.key_id,
        "live_integration_authorized": receipt.live_integration_authorized,
        "operator_go_required": receipt.operator_go_required,
        "signature_id": receipt.signature_id,
        "verification_id": receipt.verification_id,
        "verification_output": (
            str(args.verification_output)
            if args.verification_output is not None
            else None
        ),
    }
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    if (
        args.require_eligible
        and receipt.decision
        is not PromotionDecision.ELIGIBLE_FOR_OPERATOR_REVIEW
    ):
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
