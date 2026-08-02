#!/usr/bin/env python3
"""Apply and authenticate one Reader Core shadow burn-in control action."""

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
from core.reader_shadow_burn_in import (  # noqa: E402
    ReaderShadowBurnInController,
    ReaderShadowBurnInControlSigner,
    ReaderShadowBurnInError,
    load_shadow_burn_in_control_receipt,
    load_shadow_burn_in_control_signature,
    load_shadow_burn_in_control_source,
    load_shadow_burn_in_plan,
    load_shadow_burn_in_plan_signature,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Apply one explicit ARM, PAUSE, RESUME, STOP, or KILL action to a "
            "signed Reader Core shadow burn-in plan."
        )
    )
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--plan-signature", required=True, type=Path)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--previous-receipt", type=Path)
    parser.add_argument("--previous-signature", type=Path)
    parser.add_argument("--receipt-output", required=True, type=Path)
    parser.add_argument("--signature-output", required=True, type=Path)
    parser.add_argument("--hmac-key-env", required=True)
    parser.add_argument("--key-id", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if (args.previous_receipt is None) != (
            args.previous_signature is None
        ):
            raise ReaderShadowBurnInError(
                "previous receipt and signature must be provided together"
            )
        if args.receipt_output.resolve() == args.signature_output.resolve():
            raise ReaderShadowBurnInError(
                "receipt and signature outputs must be distinct"
            )
        existing = tuple(
            str(path)
            for path in (args.receipt_output, args.signature_output)
            if path.exists()
        )
        if existing:
            raise ReaderShadowBurnInError(
                f"refusing to overwrite existing output files: {existing}"
            )
        secret_text = os.environ.get(str(args.hmac_key_env))
        if secret_text is None:
            raise ReaderShadowBurnInError(
                f"HMAC environment variable is not set: {args.hmac_key_env}"
            )
        secret = secret_text.encode("utf-8")
        plan = load_shadow_burn_in_plan(args.plan)
        plan_signature = load_shadow_burn_in_plan_signature(
            args.plan_signature
        )
        source = load_shadow_burn_in_control_source(args.source)
        previous_receipt = (
            load_shadow_burn_in_control_receipt(args.previous_receipt)
            if args.previous_receipt is not None
            else None
        )
        previous_signature = (
            load_shadow_burn_in_control_signature(args.previous_signature)
            if args.previous_signature is not None
            else None
        )
        receipt = ReaderShadowBurnInController().apply(
            plan=plan,
            plan_signature=plan_signature,
            source=source,
            secret=secret,
            previous_receipt=previous_receipt,
            previous_signature=previous_signature,
        )
        signature = ReaderShadowBurnInControlSigner.sign(
            receipt,
            key_id=str(args.key_id),
            secret=secret,
        )
        write_canonical_json(args.receipt_output, receipt)
        try:
            write_canonical_json(args.signature_output, signature)
        except Exception:
            args.receipt_output.unlink(missing_ok=True)
            raise
    except (ReaderShadowBurnInError, OSError, UnicodeError, ValueError) as exc:
        print(f"reader shadow burn-in control error: {exc}", file=sys.stderr)
        return 2

    summary = {
        "action": source.action.value,
        "control_allows_shadow": receipt.control_allows_shadow,
        "issued_at_utc": source.issued_at_utc,
        "plan_id": receipt.plan_id,
        "receipt_id": receipt.receipt_id,
        "receipt_output": str(args.receipt_output),
        "signature_id": signature.signature_id,
        "signature_output": str(args.signature_output),
        "state": receipt.state.value,
    }
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
