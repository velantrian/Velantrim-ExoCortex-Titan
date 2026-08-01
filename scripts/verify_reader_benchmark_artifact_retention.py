#!/usr/bin/env python3
"""Verify a signed Reader Core artifact-retention manifest and backing files."""

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
    DEFAULT_MAX_ARTIFACT_BYTES,
    DEFAULT_MAX_TOTAL_BYTES,
    ReaderArtifactRetentionError,
    load_artifact_retention_manifest,
    load_artifact_retention_signature,
)
from core.reader_benchmark_artifact_retention_verification import (  # noqa: E402
    ReaderBenchmarkArtifactRetentionVerifier,
)
from core.reader_benchmark_runner import write_canonical_json  # noqa: E402


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Authenticate a Reader Core artifact-retention manifest and "
            "re-hash every referenced local backing file."
        )
    )
    parser.add_argument("--artifact-root", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--signature", required=True, type=Path)
    parser.add_argument("--hmac-key-env", required=True)
    parser.add_argument("--verification-output", type=Path)
    parser.add_argument(
        "--max-artifact-bytes",
        type=int,
        default=DEFAULT_MAX_ARTIFACT_BYTES,
    )
    parser.add_argument(
        "--max-total-bytes",
        type=int,
        default=DEFAULT_MAX_TOTAL_BYTES,
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.verification_output is not None and args.verification_output.exists():
            raise ReaderArtifactRetentionError(
                "refusing to overwrite existing verification output"
            )
        secret_text = os.environ.get(str(args.hmac_key_env))
        if secret_text is None:
            raise ReaderArtifactRetentionError(
                f"HMAC environment variable is not set: {args.hmac_key_env}"
            )
        manifest = load_artifact_retention_manifest(args.manifest)
        signature = load_artifact_retention_signature(args.signature)
        receipt = ReaderBenchmarkArtifactRetentionVerifier().verify(
            root=args.artifact_root,
            manifest=manifest,
            signature=signature,
            secret=secret_text.encode("utf-8"),
            max_artifact_bytes=args.max_artifact_bytes,
            max_total_bytes=args.max_total_bytes,
        )
        if args.verification_output is not None:
            write_canonical_json(args.verification_output, receipt)
    except (ReaderArtifactRetentionError, OSError, UnicodeError) as exc:
        print(f"reader artifact retention verification error: {exc}", file=sys.stderr)
        return 2

    summary = {
        "artifact_count": receipt.verified_artifact_count,
        "decision": receipt.decision.value,
        "evidence_id": receipt.evidence_id,
        "live_integration_authorized": receipt.live_integration_authorized,
        "manifest_id": receipt.manifest_id,
        "operator_go_required": receipt.operator_go_required,
        "total_byte_size": receipt.verified_total_byte_size,
        "verification_id": receipt.verification_id,
        "verification_output": (
            str(args.verification_output)
            if args.verification_output is not None
            else None
        ),
    }
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
