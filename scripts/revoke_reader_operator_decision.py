#!/usr/bin/env python3
"""Create and authenticate a revocation for one Reader Core operator decision."""

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
    ReaderOperatorDecisionSigner,
    ReaderOperatorRevocationSigner,
    load_operator_decision,
    load_operator_decision_signature,
    load_operator_revocation_source,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create a signed revocation for one signed operator decision."
    )
    parser.add_argument("--decision", required=True, type=Path)
    parser.add_argument("--decision-signature", required=True, type=Path)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--revocation-output", required=True, type=Path)
    parser.add_argument("--signature-output", required=True, type=Path)
    parser.add_argument("--hmac-key-env", required=True)
    parser.add_argument("--key-id", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.revocation_output.resolve() == args.signature_output.resolve():
            raise ReaderOperatorDecisionError(
                "revocation and signature outputs must be distinct"
            )
        existing = tuple(
            str(path)
            for path in (args.revocation_output, args.signature_output)
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
        secret = secret_text.encode("utf-8")
        decision = load_operator_decision(args.decision)
        decision_signature = load_operator_decision_signature(
            args.decision_signature
        )
        if not ReaderOperatorDecisionSigner.verify(
            decision,
            decision_signature,
            secret=secret,
        ):
            raise ReaderOperatorDecisionError(
                "operator decision signature verification failed"
            )
        source = load_operator_revocation_source(args.source)
        revocation = ReaderOperatorRevocationSigner.create(
            decision=decision,
            decision_signature=decision_signature,
            source=source,
        )
        signature = ReaderOperatorRevocationSigner.sign(
            revocation,
            key_id=str(args.key_id),
            secret=secret,
        )
        write_canonical_json(args.revocation_output, revocation)
        try:
            write_canonical_json(args.signature_output, signature)
        except Exception:
            args.revocation_output.unlink(missing_ok=True)
            raise
    except (ReaderOperatorDecisionError, OSError, UnicodeError, ValueError) as exc:
        print(f"reader operator revocation error: {exc}", file=sys.stderr)
        return 2

    summary = {
        "decision_id": decision.decision_id,
        "operator_id": revocation.source.operator_id,
        "revocation_id": revocation.revocation_id,
        "revocation_output": str(args.revocation_output),
        "signature_id": signature.signature_id,
        "signature_output": str(args.signature_output),
    }
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
