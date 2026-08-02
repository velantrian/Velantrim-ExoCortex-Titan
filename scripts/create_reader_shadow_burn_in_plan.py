#!/usr/bin/env python3
"""Create and authenticate a bounded Reader Core shadow burn-in plan."""

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
    ReaderShadowBurnInPlanBuilder,
    ReaderShadowBurnInPlanSigner,
    load_shadow_burn_in_source,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Bind an active signed shadow-only operator decision to a bounded, "
            "non-executing Reader Core burn-in plan."
        )
    )
    parser.add_argument("--decision", required=True, type=Path)
    parser.add_argument("--decision-signature", required=True, type=Path)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--revocation", type=Path)
    parser.add_argument("--revocation-signature", type=Path)
    parser.add_argument("--plan-output", required=True, type=Path)
    parser.add_argument("--signature-output", required=True, type=Path)
    parser.add_argument("--hmac-key-env", required=True)
    parser.add_argument("--key-id", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if (args.revocation is None) != (args.revocation_signature is None):
            raise ReaderShadowBurnInError(
                "revocation and revocation signature must be provided together"
            )
        if args.plan_output.resolve() == args.signature_output.resolve():
            raise ReaderShadowBurnInError(
                "plan and signature outputs must be distinct"
            )
        existing = tuple(
            str(path)
            for path in (args.plan_output, args.signature_output)
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
        decision = load_operator_decision(args.decision)
        decision_signature = load_operator_decision_signature(
            args.decision_signature
        )
        source = load_shadow_burn_in_source(args.source)
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
        plan = ReaderShadowBurnInPlanBuilder().build(
            source=source,
            decision=decision,
            decision_signature=decision_signature,
            secret=secret,
            revocation=revocation,
            revocation_signature=revocation_signature,
        )
        signature = ReaderShadowBurnInPlanSigner.sign(
            plan,
            key_id=str(args.key_id),
            secret=secret,
        )
        write_canonical_json(args.plan_output, plan)
        try:
            write_canonical_json(args.signature_output, signature)
        except Exception:
            args.plan_output.unlink(missing_ok=True)
            raise
    except (ReaderShadowBurnInError, OSError, UnicodeError, ValueError) as exc:
        print(f"reader shadow burn-in plan error: {exc}", file=sys.stderr)
        return 2

    summary = {
        "campaign_name": plan.source.campaign_name,
        "environment_id": plan.source.environment_id,
        "plan_id": plan.plan_id,
        "plan_output": str(args.plan_output),
        "planned_end_utc": plan.source.planned_end_utc,
        "planned_start_utc": plan.source.planned_start_utc,
        "production_traffic_authorized": (
            plan.production_traffic_authorized
        ),
        "query_path_wiring_authorized": plan.query_path_wiring_authorized,
        "shadow_evaluation_authorized": plan.shadow_evaluation_authorized,
        "signature_id": signature.signature_id,
        "signature_output": str(args.signature_output),
        "work_item_count": len(plan.source.work_item_ids),
    }
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
