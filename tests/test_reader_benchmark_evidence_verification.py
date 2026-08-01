from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

import pytest

from core.knowledge_capsule import ClaimModality, SourceSpan
from core.reader_benchmark_batch import ReaderBenchmarkBatchPlanner
from core.reader_benchmark_evidence_verification import (
    ReaderBenchmarkEvidenceVerificationError,
    ReaderBenchmarkEvidenceVerifier,
)
from core.reader_benchmark_executor import (
    ReaderLocalBenchmarkCase,
    ReaderLocalPipelineResult,
)
from core.reader_benchmark_finalization import ReaderCompletedBatchFinalizer
from core.reader_benchmark_preparation import (
    ReaderBenchmarkPreparationBundle,
    ReaderPreparedBenchmarkCase,
)
from core.reader_benchmark_runner import write_canonical_json
from core.reader_benchmark_scoring import (
    ReaderClaimPrediction,
    ReaderDocumentPrediction,
    ReaderExecutionMeasurement,
)
from core.reader_corpus_adjudication import (
    CorpusDocumentDescriptor,
    CorpusPrivacyClass,
    CorpusUsageBasis,
    HumanClaimLabel,
    HumanLabelSet,
    LabelSetRole,
)
from core.reader_evaluation import (
    EvaluationCorpusKind,
    EvaluationCorpusManifest,
    EvaluationEnvironment,
    PromotionDecision,
    ReaderEvaluationCaseManifest,
    ReaderPromotionThresholds,
)
from core.reader_prepared_batch_runner import ReaderPreparedBatchRunner

REPO_ROOT = Path(__file__).resolve().parent.parent
CLI_PATH = REPO_ROOT / "scripts" / "verify_reader_benchmark_evidence.py"
SECRET = b"0123456789abcdef0123456789abcdef"
WRONG_SECRET = b"abcdef0123456789abcdef0123456789"


class _Pipeline:
    def run_case(
        self,
        case: ReaderLocalBenchmarkCase,
        *,
        replay_index: int,
    ) -> ReaderLocalPipelineResult:
        claims = tuple(
            ReaderClaimPrediction.create(
                source_claim_id=claim.label_id,
                document_id=case.descriptor.document_id,
                source_revision=case.descriptor.source_revision,
                modality=claim.modality,
                source_spans=claim.source_spans,
                qualifier_codes=claim.qualifier_codes,
                applicability_codes=claim.applicability_codes,
            )
            for claim in case.gold.claims
        )
        prediction = ReaderDocumentPrediction(
            document_descriptor_id=case.descriptor.descriptor_id,
            document_id=case.descriptor.document_id,
            source_revision=case.descriptor.source_revision,
            claims=claims,
            artifact_ids=("verification-prediction",),
        )
        measurement = ReaderExecutionMeasurement(
            section_latencies_ms=(3,),
            session_wall_time_ms=6,
            model_tokens=0,
            projection_bytes=64,
            rebuild_time_ms=1,
            query_path_latency_delta_ms=0,
            resume_reused_units=0,
            resume_eligible_units=0,
        )
        return ReaderLocalPipelineResult(
            prediction=prediction,
            measurement=measurement,
            run_artifact_ids=(f"verification-run-{replay_index}",),
        )


def _environment() -> EvaluationEnvironment:
    return EvaluationEnvironment(
        commit_sha="verification-commit-001",
        runner_id="verification-runner-001",
        python_version="3.11",
        hardware_profile="test-cpu",
        config_digest="verification-config-001",
    )


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


def _preparation(
    environment: EvaluationEnvironment,
    thresholds: ReaderPromotionThresholds,
) -> ReaderBenchmarkPreparationBundle:
    raw_text = "Offline evidence verification claim."
    document_id = "verification-document-001"
    revision = sha256(raw_text.encode("utf-8")).hexdigest()
    descriptor = CorpusDocumentDescriptor(
        document_id=document_id,
        relative_path="documents/verification-document-001.txt",
        source_revision=revision,
        content_sha256=revision,
        byte_size=len(raw_text.encode("utf-8")),
        char_count=len(raw_text),
        media_type="text/plain; charset=utf-8",
        usage_basis=CorpusUsageBasis.SYNTHETIC,
        rights_reference="project-authored-test-fixture",
        privacy_class=CorpusPrivacyClass.PUBLIC,
        redistribution_allowed=True,
    )
    span = SourceSpan.from_text(
        document_id=document_id,
        raw_text=raw_text,
        start_offset=0,
        end_offset=len(raw_text),
        source_revision=revision,
    )
    claim = HumanClaimLabel.create(
        document_id=document_id,
        source_revision=revision,
        modality=ClaimModality.WORLD_FACT,
        source_spans=(span,),
    )
    gold = HumanLabelSet(
        document_descriptor_id=descriptor.descriptor_id,
        document_id=document_id,
        source_revision=revision,
        annotator_id="verification-adjudicator",
        guideline_version="verification-guideline-v1",
        label_version="verification-labels-v1",
        role=LabelSetRole.ADJUDICATED,
        claims=(claim,),
    )
    local_case = ReaderLocalBenchmarkCase(
        case_id=document_id,
        descriptor=descriptor,
        gold=gold,
    )
    case_manifest = ReaderEvaluationCaseManifest(
        case_id=document_id,
        corpus_kind=EvaluationCorpusKind.HUMAN_LABELLED,
        label_version=gold.label_version,
        expected_claim_count=1,
        expected_source_span_count=1,
        expected_exception_count=0,
        expected_relation_count=0,
        expected_contradiction_count=0,
        expected_qualifier_count=0,
        tags=("human-adjudicated", "verification-test"),
    )
    prepared = ReaderPreparedBenchmarkCase(
        evidence_case_id="verification-evidence-case-001",
        benchmark_case=local_case,
        evaluation_manifest=case_manifest,
    )
    manifest = EvaluationCorpusManifest(
        corpus_name="verification-fixture",
        corpus_version="1.0.0",
        cases=(case_manifest,),
    )
    plan = ReaderBenchmarkBatchPlanner.create_plan(
        corpus_id=manifest.corpus_id,
        environment_id=environment.environment_id,
        threshold_policy_id=thresholds.thresholds_id,
        case_ids=(document_id,),
    )
    return ReaderBenchmarkPreparationBundle(
        evidence_pack_id="verification-evidence-pack-001",
        evidence_import_bundle_id="verification-import-bundle-001",
        evaluation_manifest=manifest,
        prepared_cases=(prepared,),
        batch_plan=plan,
        initial_checkpoint=ReaderBenchmarkBatchPlanner.empty_checkpoint(plan),
    )


def _artifact_paths(tmp_path: Path) -> tuple[Path, Path, Path]:
    environment = _environment()
    thresholds = _thresholds()
    preparation = _preparation(environment, thresholds)
    runner = ReaderPreparedBatchRunner()
    initial = runner.initial_state(
        preparation=preparation,
        environment=environment,
    )
    completed = runner.run_pass(
        preparation=preparation,
        state=initial,
        pipeline=_Pipeline(),
    )
    evidence = ReaderCompletedBatchFinalizer().finalize(
        preparation=preparation,
        state=completed,
        thresholds=thresholds,
        key_id="verification-key-v1",
        secret=SECRET,
    )
    bundle_path = tmp_path / "bundle.json"
    signature_path = tmp_path / "signature.json"
    evidence_path = tmp_path / "evidence.json"
    write_canonical_json(bundle_path, evidence.benchmark_bundle)
    write_canonical_json(signature_path, evidence.bundle_signature)
    write_canonical_json(evidence_path, evidence)
    return bundle_path, signature_path, evidence_path


def _write_canonical_payload(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )


def test_valid_artifacts_reconstruct_and_verify_deterministically(
    tmp_path: Path,
) -> None:
    bundle, signature, evidence = _artifact_paths(tmp_path)
    verifier = ReaderBenchmarkEvidenceVerifier()

    first = verifier.verify_files(
        bundle_path=bundle,
        signature_path=signature,
        evidence_path=evidence,
        secret=SECRET,
    )
    second = verifier.verify_files(
        bundle_path=bundle,
        signature_path=signature,
        evidence_path=evidence,
        secret=SECRET,
    )

    assert first == second
    assert first.decision is PromotionDecision.INSUFFICIENT_EVIDENCE
    assert first.operator_go_required is True
    assert first.live_integration_authorized is False
    assert len(first.bundle_file_sha256) == 64
    assert len(first.signature_file_sha256) == 64
    assert len(first.evidence_file_sha256) == 64


def test_wrong_secret_is_rejected(tmp_path: Path) -> None:
    bundle, signature, evidence = _artifact_paths(tmp_path)

    with pytest.raises(
        ReaderBenchmarkEvidenceVerificationError,
        match="signature verification failed",
    ):
        ReaderBenchmarkEvidenceVerifier().verify_files(
            bundle_path=bundle,
            signature_path=signature,
            evidence_path=evidence,
            secret=WRONG_SECRET,
        )


def test_semantically_tampered_bundle_is_rejected(tmp_path: Path) -> None:
    bundle, signature, evidence = _artifact_paths(tmp_path)
    bundle_payload = json.loads(bundle.read_text(encoding="utf-8"))
    evidence_payload = json.loads(evidence.read_text(encoding="utf-8"))
    bundle_payload["review"]["operator_go_required"] = False
    evidence_payload["benchmark_bundle"] = bundle_payload
    _write_canonical_payload(bundle, bundle_payload)
    _write_canonical_payload(evidence, evidence_payload)

    with pytest.raises(
        ReaderBenchmarkEvidenceVerificationError,
        match="deterministic reconstruction",
    ):
        ReaderBenchmarkEvidenceVerifier().verify_files(
            bundle_path=bundle,
            signature_path=signature,
            evidence_path=evidence,
            secret=SECRET,
        )


def test_evidence_index_and_cross_file_mismatch_are_rejected(
    tmp_path: Path,
) -> None:
    bundle, signature, evidence = _artifact_paths(tmp_path)
    payload = json.loads(evidence.read_text(encoding="utf-8"))
    payload["artifact_ids"] = []
    _write_canonical_payload(evidence, payload)

    with pytest.raises(
        ReaderBenchmarkEvidenceVerificationError,
        match="artifact index",
    ):
        ReaderBenchmarkEvidenceVerifier().verify_files(
            bundle_path=bundle,
            signature_path=signature,
            evidence_path=evidence,
            secret=SECRET,
        )

    bundle, signature, evidence = _artifact_paths(tmp_path / "cross")
    payload = json.loads(evidence.read_text(encoding="utf-8"))
    payload["benchmark_bundle"]["bundle_id"] = "foreign-bundle"
    _write_canonical_payload(evidence, payload)
    with pytest.raises(
        ReaderBenchmarkEvidenceVerificationError,
        match="does not match bundle file",
    ):
        ReaderBenchmarkEvidenceVerifier().verify_files(
            bundle_path=bundle,
            signature_path=signature,
            evidence_path=evidence,
            secret=SECRET,
        )


def test_duplicate_and_noncanonical_json_are_rejected(tmp_path: Path) -> None:
    bundle, signature, evidence = _artifact_paths(tmp_path)
    signature_text = signature.read_text(encoding="utf-8")
    signature.write_text(
        '{"key_id":"duplicate",' + signature_text[1:],
        encoding="utf-8",
    )
    with pytest.raises(
        ReaderBenchmarkEvidenceVerificationError,
        match="duplicate JSON key",
    ):
        ReaderBenchmarkEvidenceVerifier().verify_files(
            bundle_path=bundle,
            signature_path=signature,
            evidence_path=evidence,
            secret=SECRET,
        )

    bundle, signature, evidence = _artifact_paths(tmp_path / "pretty")
    payload = json.loads(evidence.read_text(encoding="utf-8"))
    evidence.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    with pytest.raises(
        ReaderBenchmarkEvidenceVerificationError,
        match="canonical JSON",
    ):
        ReaderBenchmarkEvidenceVerifier().verify_files(
            bundle_path=bundle,
            signature_path=signature,
            evidence_path=evidence,
            secret=SECRET,
        )


def test_cli_writes_verification_receipt_and_refuses_overwrite(
    tmp_path: Path,
) -> None:
    bundle, signature, evidence = _artifact_paths(tmp_path)
    receipt_path = tmp_path / "verification.json"
    env = {
        "PATH": str(Path(sys.executable).parent),
        "PYTHONPATH": str(REPO_ROOT),
        "RDR23_HMAC_KEY": SECRET.decode("utf-8"),
    }
    command = [
        sys.executable,
        str(CLI_PATH),
        "--bundle",
        str(bundle),
        "--signature",
        str(signature),
        "--evidence",
        str(evidence),
        "--hmac-key-env",
        "RDR23_HMAC_KEY",
        "--verification-output",
        str(receipt_path),
        "--require-eligible",
    ]

    first = subprocess.run(
        command,
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert first.returncode == 3
    assert receipt_path.is_file()
    summary = json.loads(first.stdout)
    assert summary["decision"] == "insufficient_evidence"
    assert summary["operator_go_required"] is True
    assert summary["live_integration_authorized"] is False
    assert SECRET.decode("utf-8") not in receipt_path.read_text(encoding="utf-8")

    second = subprocess.run(
        command,
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert second.returncode == 2
    assert "refusing to overwrite" in second.stderr
