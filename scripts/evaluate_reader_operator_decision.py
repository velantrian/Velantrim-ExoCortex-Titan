#!/usr/bin/env python3
"""Evaluate one signed Reader Core operator decision at an explicit UTC time."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.reader_benchmark_runner import write_canonical_json  # noqa: E402
from core.reader_operator_decision import (  # noqa: E402
    ReaderOperatorDecisionError,
    ReaderOperatorDecisionEvaluator,
    OperatorDecisionStatus,
    load_operator_decision,
    load_operator_decision_signature,
    load_operator_revocation,
    load_operator_revocation_signature,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Authenticate and evaluate one operator decision at an explicit "
            "canonical UTC instant."
        )
    )
    parser.add_argument("--decision", required=True, type=Path)
    parser.add_argument("--decision-signature", required=True, type=Path)
    parser.add_argument("--as-of-utc", required=True)
    parser.add_argument("--hmac-key-env", required=True)
    parser.add_argument("--status-output", type=Path)
    parser.add_argument("--revocation", type=Path)
    parser.add_argument("--revocation-signature", type=Path)
    parser.add_argument(
        "--require-active-shadow-approval",
        action="store_true",
        help="Exit 3 unless the signed decision is actively shadow-approved.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if (args.revocation is None) != (args.revocation_signature is None):
            raise ReaderOperatorDecisionError(
                "revocation and revocation signature must be supplied together"
            )
        if args.status_output is not None and args.status_output.exists():
            raise ReaderOperatorDecisionError(
                "refusing to overwrite existing status output"
            )
        secret_text = os.environ.get(str(args.hmac_key_env))
        if secret_text is None:
            raise ReaderOperatorDecisionError(
                f"HMAC environment variable is not set: {args.hmac_key_env}"
            )
        decision = load_operator_decision(args.decision)
        decision_signature = load_operator_decision_signature(
            args.decision_signature
        )
        revocation = (
            load_operator_revocation(args.revocation)
            if args.revocation is not None
            else None
        )
        revocation_signature = (
            load_operator_revocation_signature(args.revocation_signature)
            if args.revocation_signature is not None
            else None
        )
        status = ReaderOperatorDecisionEvaluator().evaluate(
            decision=decision,
            decision_signature=decision_signature,
            secret=secret_text.encode("utf-8"),
            as_of_utc=str(args.as_of_utc),
            revocation=revocation,
            revocation_signature=revocation_signature,
        )
        if args.status_output is not None:
            write_canonical_json(args.status_output, status)
    except (ReaderOperatorDecisionError, OSError, UnicodeError, ValueError) as exc:
        print(f"reader operator decision status error: {exc}", file=sys.stderr)
        return 2

    summary = {
        "canon_write_authorized": status.canon_write_authorized,
        "decision_id": status.decision_id,
        "live_integration_authorized": status.live_integration_authorized,
        "memory_write_authorized": status.memory_write_authorized,
        "query_path_wiring_authorized": status.query_path_wiring_authorized,
        "shadow_evaluation_authorized": status.shadow_evaluation_authorized,
        "status": status.status.value,
        "status_id": status.status_id,
        "status_output": (
            str(args.status_output) if args.status_output is not None else None
        ),
    }
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    if (
        args.require_active_shadow_approval
        and status.status is not OperatorDecisionStatus.ACTIVE_SHADOW_APPROVAL
    ):
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
