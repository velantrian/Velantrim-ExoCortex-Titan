"""Canonical backing-file verification for Reader Core artifact retention.

This module is the operator-facing verifier for PR-RDR-24. It reuses the signed
manifest and safe file primitives from ``reader_benchmark_artifact_retention``
while canonicalizing content-addressed record IDs independently of artifact-ID
ordering.
"""

from __future__ import annotations

from pathlib import Path

from core.reader_benchmark_artifact_retention import (
    DEFAULT_MAX_ARTIFACT_BYTES,
    DEFAULT_MAX_TOTAL_BYTES,
    BatchCaseStatus,
    ReaderArtifactRetentionError,
    ReaderArtifactRetentionSignature,
    ReaderArtifactRetentionSigner,
    ReaderArtifactRetentionVerificationReceipt,
    ReaderBenchmarkArtifactRetentionManifest,
    _hash_regular_file,
    _positive_int,
    _secure_artifact_path,
)


class ReaderBenchmarkArtifactRetentionVerifier:
    """Authenticate a retention manifest and re-hash every backing file."""

    def verify(
        self,
        *,
        root: str | Path,
        manifest: ReaderBenchmarkArtifactRetentionManifest,
        signature: ReaderArtifactRetentionSignature,
        secret: bytes,
        max_artifact_bytes: int = DEFAULT_MAX_ARTIFACT_BYTES,
        max_total_bytes: int = DEFAULT_MAX_TOTAL_BYTES,
    ) -> ReaderArtifactRetentionVerificationReceipt:
        if not ReaderArtifactRetentionSigner.verify(
            manifest,
            signature,
            secret=secret,
        ):
            raise ReaderArtifactRetentionError(
                "artifact retention signature verification failed"
            )
        _positive_int(max_artifact_bytes, "max_artifact_bytes")
        _positive_int(max_total_bytes, "max_total_bytes")
        if manifest.total_byte_size > max_total_bytes:
            raise ReaderArtifactRetentionError(
                "manifest total exceeds max_total_bytes"
            )
        root_path = Path(root)
        if root_path.is_symlink():
            raise ReaderArtifactRetentionError("artifact root must not be a symlink")
        root_path = root_path.resolve()
        if not root_path.is_dir():
            raise ReaderArtifactRetentionError(
                "artifact root must be an existing directory"
            )
        verified_total = 0
        for record in manifest.artifacts:
            path = _secure_artifact_path(root_path, record.relative_path)
            digest, byte_size = _hash_regular_file(
                path,
                max_artifact_bytes=max_artifact_bytes,
            )
            if byte_size != record.byte_size:
                raise ReaderArtifactRetentionError(
                    f"artifact size mismatch: {record.artifact_id}"
                )
            if digest != record.content_sha256:
                raise ReaderArtifactRetentionError(
                    f"artifact digest mismatch: {record.artifact_id}"
                )
            verified_total += byte_size
        if verified_total != manifest.total_byte_size:
            raise ReaderArtifactRetentionError(
                "verified total does not match retention manifest"
            )
        return ReaderArtifactRetentionVerificationReceipt(
            manifest_id=manifest.manifest_id,
            retention_signature_id=signature.signature_id,
            evidence_id=manifest.evidence_id,
            evidence_verification_id=manifest.evidence_verification_id,
            verified_record_ids=tuple(
                sorted(item.record_id for item in manifest.artifacts)
            ),
            verified_artifact_count=len(manifest.artifacts),
            verified_total_byte_size=verified_total,
            decision=manifest.decision,
            operator_go_required=manifest.operator_go_required,
            live_integration_authorized=manifest.live_integration_authorized,
        )


__all__ = ["ReaderBenchmarkArtifactRetentionVerifier"]
