#!/usr/bin/env python3
"""Create and authenticate a Reader Core operator decision record."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.reader_benchmark_artifact_retention import (  # noqa: E402
    load_artifact_retention_manifest,
)
from core.reader_benchmark_runner import write_canonical_json  # noqa: E402
from core.reader_operator_decision import (  # noqa: E402
    ReaderOperatorDecisionBuilder,
    ReaderOperatorDecisionError,
    ReaderOperatorDecisionSigner,
    load_benchmark_verification_receipt,
    load_operator_decision_source,
    load_retention_verification_receipt,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Bind a canonical operator disposition to verified benchmark and "
            "retained-artifact evidence. Approval is shadow-only."
        )
    )
    parser.add_argument("--benchmark-verification", required=True, type=Path)
    parser.add_argument("--retention-manifest", required=True, type=Path)
    parser.add_argument("--retention-verification", required=True, type=Path)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--decision-output", required=True, type=Path)
    parser.add_argument("--signature-output", required=True, type=Path)
    parser.add_argument("--hmac-key-env", required=True)
    parser.add_argument("--key-id", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.decision_output.resolve() == args.signature_output.resolve():
            raise ReaderOperatorDecisionError(
                "decision and signature outputs must be distinct"
            )
        existing = tuple(
            str(path)
            for path in (args.decision_output, args.signature_output)
            if path.exists()
        )
        if existing:
            raise ReaderOperatorDecisionError(
                f"refusing to overwrite existing output files: {existing}"
            )
        secret_text = os.environ.get(str(args.hmac_key_env))
        if secret_text is None:
            raise ReaderOperatorDecisionError(
                f"HMAC environment variable is not set: {args.hmac_key_env}"
            )
        benchmark_verification = load_benchmark_verification_receipt(
            args.benchmark_verification
        )
        retention_manifest = load_artifact_retention_manifest(
            args.retention_manifest
        )
        retention_verification = load_retention_verification_receipt(
            args.retention_verification
        )
        source = load_operator_decision_source(args.source)
        decision = ReaderOperatorDecisionBuilder().build(
            benchmark_verification=benchmark_verification,
            retention_manifest=retention_manifest,
            retention_verification=retention_verification,
            source=source,
        )
        signature = ReaderOperatorDecisionSigner.sign(
            decision,
            key_id=str(args.key_id),
            secret=secret_text.encode("utf-8"),
        )
        write_canonical_json(args.decision_output, decision)
        try:
            write_canonical_json(args.signature_output, signature)
        except Exception:
            args.decision_output.unlink(missing_ok=True)
            raise
    except (ReaderOperatorDecisionError, OSError, UnicodeError, ValueError) as exc:
        print(f"reader operator decision error: {exc}", file=sys.stderr)
        return 2

    summary = {
        "decision_id": decision.decision_id,
        "decision_output": str(args.decision_output),
        "disposition": decision.disposition.value,
        "live_integration_authorized": decision.live_integration_authorized,
        "operator_id": decision.operator_id,
        "query_path_wiring_authorized": (
            decision.query_path_wiring_authorized
        ),
        "shadow_evaluation_authorized": (
            decision.shadow_evaluation_authorized
        ),
        "signature_id": signature.signature_id,
        "signature_output": str(args.signature_output),
    }
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
