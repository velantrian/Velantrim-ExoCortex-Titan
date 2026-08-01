from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import subprocess
import sys

import pytest

from core.reader_benchmark_artifact_retention import (
    ArtifactRetentionClass,
    ReaderArtifactRetentionError,
    ReaderArtifactRetentionSigner,
    ReaderArtifactRetentionSourceEntry,
    ReaderArtifactRetentionSourceSpec,
    ReaderBenchmarkArtifactRetentionBuilder,
    ReaderBenchmarkArtifactRetentionVerifier,
    extract_verified_evidence_artifact_index,
    load_artifact_retention_manifest,
    load_artifact_retention_signature,
    load_artifact_retention_source_spec,
    write_artifact_retention_source_spec,
)
from core.reader_benchmark_batch import (
    BatchCaseStatus,
    ReaderBenchmarkBatchCheckpoint,
    ReaderBenchmarkBatchPlan,
    ReaderBenchmarkCaseReceipt,
)
from core.reader_benchmark_evidence_verification import (
    ReaderBenchmarkEvidenceVerifier,
)
from core.reader_benchmark_finalization import ReaderSignedBenchmarkEvidence
from core.reader_benchmark_runner import (
    ReaderBenchmarkRunner,
    ReaderBenchmarkSigner,
    write_canonical_json,
)
from core.reader_benchmark_scoring import ReaderBenchmarkObservation
from core.reader_evaluation import (
    EvaluationCorpusKind,
    EvaluationCorpusManifest,
    EvaluationEnvironment,
    ReaderEvaluationCaseManifest,
    ReaderPromotionThresholds,
)
from core.reader_prepared_batch_runner import ReaderPreparedBatchExecutionState

REPO_ROOT = Path(__file__).resolve().parent.parent
BUILD_CLI = REPO_ROOT / "scripts" / "retain_reader_benchmark_artifacts.py"
VERIFY_CLI = (
    REPO_ROOT / "scripts" / "verify_reader_benchmark_artifact_retention.py"
)
SECRET = b"0123456789abcdef0123456789abcdef"
WRONG_SECRET = b"abcdef0123456789abcdef0123456789"
ARTIFACT_IDS = ("artifact-alpha", "artifact-beta")


def _thresholds() -> ReaderPromotionThresholds:
    return ReaderPromotionThresholds(
        min_total_cases=1,
        min_synthetic_cases=0,
        min_real_cases=0,
        min_human_labelled_cases=1,
        min_claim_fidelity=1.0,
        min_source_span_precision=1.0,
        min_source_span_recall=1.0,
        min_critical_exception_recall=0.0,
        min_relation_recall=0.0,
        max_false_relation_rate=1.0,
        min_contradiction_recall=0.0,
        max_orphan_claim_rate=1.0,
        min_qualifier_connectivity=0.0,
        max_unsupported_synthesis_rate=1.0,
        min_replay_match_rate=1.0,
        min_resume_reuse_ratio=0.0,
        max_query_path_latency_delta_ms=0,
    )


def _signed_evidence_files(tmp_path: Path):
    environment = EvaluationEnvironment(
        commit_sha="retention-commit-001",
        runner_id="retention-runner-001",
        python_version="3.11",
        hardware_profile="test-cpu",
        config_digest="retention-config-001",
    )
    thresholds = _thresholds()
    case_manifest = ReaderEvaluationCaseManifest(
        case_id="retention-case-001",
        corpus_kind=EvaluationCorpusKind.HUMAN_LABELLED,
        label_version="retention-labels-v1",
        expected_claim_count=1,
        expected_source_span_count=1,
        expected_exception_count=0,
        expected_relation_count=0,
        expected_contradiction_count=0,
        expected_qualifier_count=0,
        tags=("human-adjudicated", "retention-test"),
    )
    manifest = EvaluationCorpusManifest(
        corpus_name="retention-fixture",
        corpus_version="1.0.0",
        cases=(case_manifest,),
    )
    plan = ReaderBenchmarkBatchPlan(
        corpus_id=manifest.corpus_id,
        environment_id=environment.environment_id,
        threshold_policy_id=thresholds.thresholds_id,
        case_ids=(case_manifest.case_id,),
        max_attempts_per_case=1,
    )
    observation = ReaderBenchmarkObservation(
        case_id=case_manifest.case_id,
        predicted_claim_count=1,
        matched_claim_count=1,
        predicted_source_span_count=1,
        correct_source_span_count=1,
        predicted_exception_count=0,
        matched_exception_count=0,
        predicted_relation_count=0,
        matched_relation_count=0,
        false_relation_count=0,
        matched_contradiction_count=0,
        connected_qualifier_count=0,
        source_claim_count=1,
        orphan_source_claim_count=1,
        synthesis_claim_count=0,
        unsupported_synthesis_claim_count=0,
        first_artifact_ids=("replay-stable",),
        second_artifact_ids=("replay-stable",),
        section_latencies_ms=(2,),
        session_wall_time_ms=4,
        model_tokens=0,
        projection_bytes=48,
        rebuild_time_ms=1,
        query_path_latency_delta_ms=0,
        resume_reused_units=0,
        resume_eligible_units=0,
    )
    receipt = ReaderBenchmarkCaseReceipt(
        plan_id=plan.plan_id,
        case_id=case_manifest.case_id,
        status=BatchCaseStatus.SUCCEEDED,
        attempt=1,
        observation_id=observation.observation_id,
        error_code=None,
        artifact_ids=ARTIFACT_IDS,
    )
    checkpoint = ReaderBenchmarkBatchCheckpoint(
        plan=plan,
        receipts=(receipt,),
    )
    state = ReaderPreparedBatchExecutionState(
        preparation_id="retention-preparation-001",
        environment=environment,
        checkpoint=checkpoint,
        observations=(observation,),
        pass_count=1,
    )
    benchmark_bundle = ReaderBenchmarkRunner().run(
        manifest,
        state.to_benchmark_input(),
        thresholds,
    )
    benchmark_signature = ReaderBenchmarkSigner.sign(
        benchmark_bundle,
        key_id="benchmark-key-v1",
        secret=SECRET,
    )
    evidence = ReaderSignedBenchmarkEvidence(
        preparation_id=state.preparation_id,
        execution_state=state,
        benchmark_bundle=benchmark_bundle,
        bundle_signature=benchmark_signature,
        receipt_ids=(receipt.receipt_id,),
        failed_attempt_receipt_ids=(),
        artifact_ids=ARTIFACT_IDS,
    )
    bundle_path = tmp_path / "bundle.json"
    benchmark_signature_path = tmp_path / "benchmark-signature.json"
    evidence_path = tmp_path / "evidence.json"
    write_canonical_json(bundle_path, benchmark_bundle)
    write_canonical_json(benchmark_signature_path, benchmark_signature)
    write_canonical_json(evidence_path, evidence)
    verification = ReaderBenchmarkEvidenceVerifier().verify_files(
        bundle_path=bundle_path,
        signature_path=benchmark_signature_path,
        evidence_path=evidence_path,
        secret=SECRET,
    )
    return bundle_path, benchmark_signature_path, evidence_path, verification


def _artifact_root_and_spec(
    tmp_path: Path,
    *,
    evidence_id: str,
    verification_id: str,
):
    root = tmp_path / "artifact-root"
    (root / "files").mkdir(parents=True)
    (root / "files" / "alpha.bin").write_bytes(b"alpha-artifact-bytes")
    (root / "files" / "beta.json").write_bytes(b'{"beta":true}\n')
    spec = ReaderArtifactRetentionSourceSpec(
        evidence_id=evidence_id,
        evidence_verification_id=verification_id,
        artifacts=(
            ReaderArtifactRetentionSourceEntry(
                artifact_id="artifact-alpha",
                relative_path="files/alpha.bin",
                media_type="application/octet-stream",
                retention_class=ArtifactRetentionClass.BENCHMARK_OUTPUT,
            ),
            ReaderArtifactRetentionSourceEntry(
                artifact_id="artifact-beta",
                relative_path="files/beta.json",
                media_type="application/json",
                retention_class=ArtifactRetentionClass.PIPELINE_TRACE,
            ),
        ),
    )
    return root, spec


def _built(tmp_path: Path):
    bundle, benchmark_signature, evidence, verification = _signed_evidence_files(
        tmp_path
    )
    artifact_index = extract_verified_evidence_artifact_index(
        evidence_path=evidence,
        verification=verification,
    )
    root, spec = _artifact_root_and_spec(
        tmp_path,
        evidence_id=artifact_index.evidence_id,
        verification_id=artifact_index.evidence_verification_id,
    )
    manifest = ReaderBenchmarkArtifactRetentionBuilder().build(
        root=root,
        artifact_index=artifact_index,
        source_spec=spec,
    )
    signature = ReaderArtifactRetentionSigner.sign(
        manifest,
        key_id="retention-key-v1",
        secret=SECRET,
    )
    return (
        bundle,
        benchmark_signature,
        evidence,
        verification,
        artifact_index,
        root,
        spec,
        manifest,
        signature,
    )


def test_manifest_binds_exact_artifact_files_and_verifies(tmp_path: Path) -> None:
    *_, root, spec, manifest, signature = _built(tmp_path)
    verifier = ReaderBenchmarkArtifactRetentionVerifier()

    first = verifier.verify(
        root=root,
        manifest=manifest,
        signature=signature,
        secret=SECRET,
    )
    second = verifier.verify(
        root=root,
        manifest=manifest,
        signature=signature,
        secret=SECRET,
    )

    assert first == second
    assert manifest.artifact_ids == ARTIFACT_IDS
    assert manifest.source_spec_id == spec.spec_id
    assert manifest.total_byte_size == sum(
        item.byte_size for item in manifest.artifacts
    )
    assert first.verified_artifact_count == 2
    assert first.verified_total_byte_size == manifest.total_byte_size
    assert first.operator_go_required is True
    assert first.live_integration_authorized is False


def test_source_spec_requires_exact_evidence_artifact_coverage(
    tmp_path: Path,
) -> None:
    *_, artifact_index, root, spec, _, _ = _built(tmp_path)
    missing = replace(spec, artifacts=spec.artifacts[:-1], spec_id="")
    extra = ReaderArtifactRetentionSourceEntry(
        artifact_id="artifact-extra",
        relative_path="files/extra.bin",
        media_type="application/octet-stream",
        retention_class=ArtifactRetentionClass.OTHER,
    )
    (root / "files" / "extra.bin").write_bytes(b"extra")
    extra_spec = replace(
        spec,
        artifacts=(*spec.artifacts, extra),
        spec_id="",
    )

    for candidate in (missing, extra_spec):
        with pytest.raises(ReaderArtifactRetentionError, match="exactly cover"):
            ReaderBenchmarkArtifactRetentionBuilder().build(
                root=root,
                artifact_index=artifact_index,
                source_spec=candidate,
            )


def test_path_traversal_symlinks_and_size_bounds_fail_closed(
    tmp_path: Path,
) -> None:
    with pytest.raises(ReaderArtifactRetentionError, match="parent segments"):
        ReaderArtifactRetentionSourceEntry(
            artifact_id="artifact-alpha",
            relative_path="../escape.bin",
            media_type="application/octet-stream",
            retention_class=ArtifactRetentionClass.OTHER,
        )

    *_, artifact_index, root, spec, _, _ = _built(tmp_path)
    target = root / "files" / "alpha.bin"
    target.unlink()
    target.symlink_to(root / "files" / "beta.json")
    with pytest.raises(ReaderArtifactRetentionError, match="symlink"):
        ReaderBenchmarkArtifactRetentionBuilder().build(
            root=root,
            artifact_index=artifact_index,
            source_spec=spec,
        )

    target.unlink()
    target.write_bytes(b"too-large")
    with pytest.raises(
        ReaderArtifactRetentionError,
        match="max_artifact_bytes",
    ):
        ReaderBenchmarkArtifactRetentionBuilder().build(
            root=root,
            artifact_index=artifact_index,
            source_spec=spec,
            max_artifact_bytes=4,
        )


def test_modified_file_and_wrong_key_are_rejected(tmp_path: Path) -> None:
    *_, root, _, manifest, signature = _built(tmp_path)
    verifier = ReaderBenchmarkArtifactRetentionVerifier()

    with pytest.raises(
        ReaderArtifactRetentionError,
        match="signature verification failed",
    ):
        verifier.verify(
            root=root,
            manifest=manifest,
            signature=signature,
            secret=WRONG_SECRET,
        )

    (root / "files" / "alpha.bin").write_bytes(b"modified")
    with pytest.raises(
        ReaderArtifactRetentionError,
        match="mismatch",
    ):
        verifier.verify(
            root=root,
            manifest=manifest,
            signature=signature,
            secret=SECRET,
        )


def test_source_manifest_and_signature_codecs_are_strict(tmp_path: Path) -> None:
    *_, spec, manifest, signature = _built(tmp_path)[5:]
    spec_path = tmp_path / "spec.json"
    manifest_path = tmp_path / "manifest.json"
    signature_path = tmp_path / "retention-signature.json"
    write_artifact_retention_source_spec(spec_path, spec)
    write_canonical_json(manifest_path, manifest)
    write_canonical_json(signature_path, signature)

    assert load_artifact_retention_source_spec(spec_path) == spec
    assert load_artifact_retention_manifest(manifest_path) == manifest
    assert load_artifact_retention_signature(signature_path) == signature

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["manifest_id"] = "forged-manifest"
    manifest_path.write_text(
        json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(ReaderArtifactRetentionError, match="manifest_id"):
        load_artifact_retention_manifest(manifest_path)

    signature_text = signature_path.read_text(encoding="utf-8")
    signature_path.write_text(
        '{"key_id":"duplicate",' + signature_text[1:],
        encoding="utf-8",
    )
    with pytest.raises(ReaderArtifactRetentionError, match="duplicate JSON key"):
        load_artifact_retention_signature(signature_path)


def test_build_and_verify_clis_are_end_to_end_and_secret_free(
    tmp_path: Path,
) -> None:
    bundle, benchmark_signature, evidence, verification = _signed_evidence_files(
        tmp_path
    )
    artifact_index = extract_verified_evidence_artifact_index(
        evidence_path=evidence,
        verification=verification,
    )
    root, spec = _artifact_root_and_spec(
        tmp_path,
        evidence_id=artifact_index.evidence_id,
        verification_id=artifact_index.evidence_verification_id,
    )
    spec_path = tmp_path / "retention-spec.json"
    manifest_path = tmp_path / "retention-manifest.json"
    retention_signature_path = tmp_path / "retention-signature.json"
    build_verification_path = tmp_path / "build-verification.json"
    later_verification_path = tmp_path / "later-verification.json"
    write_artifact_retention_source_spec(spec_path, spec)
    env = {
        "PATH": str(Path(sys.executable).parent),
        "PYTHONPATH": str(REPO_ROOT),
        "RDR24_HMAC_KEY": SECRET.decode("utf-8"),
    }
    build_command = [
        sys.executable,
        str(BUILD_CLI),
        "--bundle",
        str(bundle),
        "--benchmark-signature",
        str(benchmark_signature),
        "--evidence",
        str(evidence),
        "--artifact-root",
        str(root),
        "--spec",
        str(spec_path),
        "--manifest-output",
        str(manifest_path),
        "--retention-signature-output",
        str(retention_signature_path),
        "--verification-output",
        str(build_verification_path),
        "--hmac-key-env",
        "RDR24_HMAC_KEY",
        "--key-id",
        "retention-cli-key",
    ]

    build = subprocess.run(
        build_command,
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert build.returncode == 0, build.stderr
    assert manifest_path.is_file()
    assert retention_signature_path.is_file()
    assert build_verification_path.is_file()

    verify = subprocess.run(
        [
            sys.executable,
            str(VERIFY_CLI),
            "--artifact-root",
            str(root),
            "--manifest",
            str(manifest_path),
            "--signature",
            str(retention_signature_path),
            "--hmac-key-env",
            "RDR24_HMAC_KEY",
            "--verification-output",
            str(later_verification_path),
        ],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert verify.returncode == 0, verify.stderr
    assert later_verification_path.is_file()
    assert json.loads(build.stdout)["artifact_count"] == 2
    assert json.loads(verify.stdout)["artifact_count"] == 2
    secret_text = SECRET.decode("utf-8")
    for path in (
        manifest_path,
        retention_signature_path,
        build_verification_path,
        later_verification_path,
    ):
        assert secret_text not in path.read_text(encoding="utf-8")

    repeated = subprocess.run(
        build_command,
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert repeated.returncode == 2
    assert "refusing to overwrite" in repeated.stderr
