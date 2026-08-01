from __future__ import annotations

from hashlib import sha256
from pathlib import Path

from core.reader_benchmark_artifact_retention import (
    ArtifactRetentionClass,
    ReaderArtifactRetentionSigner,
    ReaderBenchmarkArtifactRetentionManifest,
    ReaderRetainedBenchmarkArtifact,
)
from core.reader_benchmark_artifact_retention_verification import (
    ReaderBenchmarkArtifactRetentionVerifier,
)
from core.reader_evaluation import PromotionDecision

SECRET = b"0123456789abcdef0123456789abcdef"


def _descending_record_pair(
    root: Path,
) -> tuple[ReaderRetainedBenchmarkArtifact, ReaderRetainedBenchmarkArtifact]:
    for index in range(256):
        alpha_bytes = f"alpha-{index}".encode("utf-8")
        beta_bytes = f"beta-{index}".encode("utf-8")
        alpha_path = f"alpha-{index}.bin"
        beta_path = f"beta-{index}.bin"
        alpha = ReaderRetainedBenchmarkArtifact(
            artifact_id="artifact-alpha",
            relative_path=alpha_path,
            media_type="application/octet-stream",
            retention_class=ArtifactRetentionClass.BENCHMARK_OUTPUT,
            content_sha256=sha256(alpha_bytes).hexdigest(),
            byte_size=len(alpha_bytes),
        )
        beta = ReaderRetainedBenchmarkArtifact(
            artifact_id="artifact-beta",
            relative_path=beta_path,
            media_type="application/octet-stream",
            retention_class=ArtifactRetentionClass.PIPELINE_TRACE,
            content_sha256=sha256(beta_bytes).hexdigest(),
            byte_size=len(beta_bytes),
        )
        if alpha.record_id > beta.record_id:
            (root / alpha_path).write_bytes(alpha_bytes)
            (root / beta_path).write_bytes(beta_bytes)
            return alpha, beta
    raise AssertionError("could not construct descending deterministic record IDs")


def test_verifier_canonicalizes_record_ids_independently_of_artifact_order(
    tmp_path: Path,
) -> None:
    alpha, beta = _descending_record_pair(tmp_path)
    assert alpha.artifact_id < beta.artifact_id
    assert alpha.record_id > beta.record_id
    manifest = ReaderBenchmarkArtifactRetentionManifest(
        evidence_id="evidence-ordering-test",
        evidence_verification_id="evidence-verification-ordering-test",
        benchmark_bundle_id="bundle-ordering-test",
        benchmark_signature_id="benchmark-signature-ordering-test",
        evidence_file_sha256="0" * 64,
        source_spec_id="source-spec-ordering-test",
        artifact_index_id="artifact-index-ordering-test",
        artifacts=(alpha, beta),
        total_byte_size=alpha.byte_size + beta.byte_size,
        decision=PromotionDecision.INSUFFICIENT_EVIDENCE,
        operator_go_required=True,
        live_integration_authorized=False,
    )
    signature = ReaderArtifactRetentionSigner.sign(
        manifest,
        key_id="retention-ordering-key",
        secret=SECRET,
    )

    receipt = ReaderBenchmarkArtifactRetentionVerifier().verify(
        root=tmp_path,
        manifest=manifest,
        signature=signature,
        secret=SECRET,
    )

    assert receipt.verified_record_ids == tuple(
        sorted((alpha.record_id, beta.record_id))
    )
