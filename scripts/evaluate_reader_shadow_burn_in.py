#!/usr/bin/env python3
"""Evaluate one signed Reader Core shadow burn-in state at an explicit time."""

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
    load_operator_decision,
    load_operator_decision_signature,
    load_operator_revocation,
    load_operator_revocation_signature,
)
from core.reader_shadow_burn_in import (  # noqa: E402
    ReaderShadowBurnInError,
    ReaderShadowBurnInEvaluator,
    ShadowBurnInStatus,
    load_shadow_burn_in_control_receipt,
    load_shadow_burn_in_control_signature,
    load_shadow_burn_in_plan,
    load_shadow_burn_in_plan_signature,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate a signed shadow burn-in plan/control chain. READY grants "
            "only isolated shadow evaluation to a separate reviewed harness."
        )
    )
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--plan-signature", required=True, type=Path)
    parser.add_argument("--decision", required=True, type=Path)
    parser.add_argument("--decision-signature", required=True, type=Path)
    parser.add_argument("--control-receipt", required=True, type=Path)
    parser.add_argument("--control-signature", required=True, type=Path)
    parser.add_argument("--revocation", type=Path)
    parser.add_argument("--revocation-signature", type=Path)
    parser.add_argument("--as-of-utc", required=True)
    parser.add_argument("--status-output", required=True, type=Path)
    parser.add_argument("--hmac-key-env", required=True)
    parser.add_argument("--require-ready", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if (args.revocation is None) != (args.revocation_signature is None):
            raise ReaderShadowBurnInError(
                "revocation and revocation signature must be provided together"
            )
        if args.status_output.exists():
            raise ReaderShadowBurnInError(
                f"refusing to overwrite existing output file: {args.status_output}"
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
        decision = load_operator_decision(args.decision)
        decision_signature = load_operator_decision_signature(
            args.decision_signature
        )
        control_receipt = load_shadow_burn_in_control_receipt(
            args.control_receipt
        )
        control_signature = load_shadow_burn_in_control_signature(
            args.control_signature
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
        status = ReaderShadowBurnInEvaluator().evaluate(
            plan=plan,
            plan_signature=plan_signature,
            decision=decision,
            decision_signature=decision_signature,
            control_receipt=control_receipt,
            control_signature=control_signature,
            secret=secret,
            as_of_utc=str(args.as_of_utc),
            revocation=revocation,
            revocation_signature=revocation_signature,
        )
        write_canonical_json(args.status_output, status)
    except (ReaderShadowBurnInError, OSError, UnicodeError, ValueError) as exc:
        print(f"reader shadow burn-in status error: {exc}", file=sys.stderr)
        return 2

    summary = {
        "as_of_utc": status.as_of_utc,
        "background_scheduling_authorized": (
            status.background_scheduling_authorized
        ),
        "plan_id": status.plan_id,
        "production_traffic_authorized": (
            status.production_traffic_authorized
        ),
        "query_path_wiring_authorized": status.query_path_wiring_authorized,
        "shadow_evaluation_authorized": (
            status.shadow_evaluation_authorized
        ),
        "status": status.status.value,
        "status_id": status.status_id,
        "status_output": str(args.status_output),
        "user_visible_output_authorized": (
            status.user_visible_output_authorized
        ),
    }
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    if args.require_ready and status.status is not ShadowBurnInStatus.READY:
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
