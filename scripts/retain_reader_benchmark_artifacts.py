#!/usr/bin/env python3
"""Build and sign a local Reader Core benchmark artifact retention manifest.

The command first verifies the RDR-22 bundle/signature/evidence set through the
RDR-23 verifier, then requires exact local-file coverage for every signed
artifact ID. It writes metadata only; artifact bytes and HMAC secrets are never
embedded in outputs.
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

from core.reader_benchmark_artifact_retention import (  # noqa: E402
    DEFAULT_MAX_ARTIFACT_BYTES,
    DEFAULT_MAX_TOTAL_BYTES,
    ReaderArtifactRetentionError,
    ReaderArtifactRetentionSigner,
    ReaderBenchmarkArtifactRetentionBuilder,
    extract_verified_evidence_artifact_index,
    load_artifact_retention_source_spec,
)
from core.reader_benchmark_artifact_retention_verification import (  # noqa: E402
    ReaderBenchmarkArtifactRetentionVerifier,
)
from core.reader_benchmark_evidence_verification import (  # noqa: E402
    ReaderBenchmarkEvidenceVerificationError,
    ReaderBenchmarkEvidenceVerifier,
)
from core.reader_benchmark_runner import write_canonical_json  # noqa: E402


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Verify signed benchmark evidence, bind every artifact ID to a local "
            "regular file, and write a signed retention manifest."
        )
    )
    parser.add_argument("--bundle", required=True, type=Path)
    parser.add_argument("--benchmark-signature", required=True, type=Path)
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--artifact-root", required=True, type=Path)
    parser.add_argument("--spec", required=True, type=Path)
    parser.add_argument("--manifest-output", required=True, type=Path)
    parser.add_argument("--retention-signature-output", required=True, type=Path)
    parser.add_argument("--verification-output", required=True, type=Path)
    parser.add_argument("--hmac-key-env", required=True)
    parser.add_argument("--key-id", required=True)
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


def _validate_outputs(paths: tuple[Path, ...]) -> None:
    resolved = tuple(path.resolve() for path in paths)
    if len(set(resolved)) != len(resolved):
        raise ReaderArtifactRetentionError(
            "manifest, signature, and verification outputs must be distinct"
        )
    existing = tuple(str(path) for path in paths if path.exists())
    if existing:
        raise ReaderArtifactRetentionError(
            f"refusing to overwrite existing output files: {existing}"
        )


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    outputs = (
        args.manifest_output,
        args.retention_signature_output,
        args.verification_output,
    )
    created: list[Path] = []
    try:
        _validate_outputs(outputs)
        secret_text = os.environ.get(str(args.hmac_key_env))
        if secret_text is None:
            raise ReaderArtifactRetentionError(
                f"HMAC environment variable is not set: {args.hmac_key_env}"
            )
        secret = secret_text.encode("utf-8")
        benchmark_verification = ReaderBenchmarkEvidenceVerifier().verify_files(
            bundle_path=args.bundle,
            signature_path=args.benchmark_signature,
            evidence_path=args.evidence,
            secret=secret,
        )
        artifact_index = extract_verified_evidence_artifact_index(
            evidence_path=args.evidence,
            verification=benchmark_verification,
        )
        source_spec = load_artifact_retention_source_spec(args.spec)
        manifest = ReaderBenchmarkArtifactRetentionBuilder().build(
            root=args.artifact_root,
            artifact_index=artifact_index,
            source_spec=source_spec,
            max_artifact_bytes=args.max_artifact_bytes,
            max_total_bytes=args.max_total_bytes,
        )
        signature = ReaderArtifactRetentionSigner.sign(
            manifest,
            key_id=str(args.key_id),
            secret=secret,
        )
        verification = ReaderBenchmarkArtifactRetentionVerifier().verify(
            root=args.artifact_root,
            manifest=manifest,
            signature=signature,
            secret=secret,
            max_artifact_bytes=args.max_artifact_bytes,
            max_total_bytes=args.max_total_bytes,
        )
        for path, value in (
            (args.manifest_output, manifest),
            (args.retention_signature_output, signature),
            (args.verification_output, verification),
        ):
            write_canonical_json(path, value)
            created.append(path)
    except (
        ReaderArtifactRetentionError,
        ReaderBenchmarkEvidenceVerificationError,
        OSError,
        UnicodeError,
    ) as exc:
        for path in created:
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass
        print(f"reader artifact retention error: {exc}", file=sys.stderr)
        return 2

    summary = {
        "artifact_count": len(manifest.artifacts),
        "decision": manifest.decision.value,
        "evidence_id": manifest.evidence_id,
        "live_integration_authorized": manifest.live_integration_authorized,
        "manifest_id": manifest.manifest_id,
        "manifest_output": str(args.manifest_output),
        "operator_go_required": manifest.operator_go_required,
        "retention_signature_id": signature.signature_id,
        "retention_signature_output": str(args.retention_signature_output),
        "total_byte_size": manifest.total_byte_size,
        "verification_id": verification.verification_id,
        "verification_output": str(args.verification_output),
    }
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
