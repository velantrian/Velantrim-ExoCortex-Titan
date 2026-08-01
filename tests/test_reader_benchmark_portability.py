from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

import pytest

from core.knowledge_capsule import ClaimModality, SourceSpan
from core.reader_benchmark_batch import ReaderBenchmarkBatchPlanner
from core.reader_benchmark_executor import (
    ReaderLocalBenchmarkCase,
    ReaderLocalPipelineResult,
)
from core.reader_benchmark_finalization import ReaderCompletedBatchFinalizer
from core.reader_benchmark_portability import (
    ReaderBenchmarkFinalizationEnvelope,
    ReaderBenchmarkPortabilityError,
    load_finalization_envelope,
    write_finalization_envelope,
)
from core.reader_benchmark_preparation import (
    ReaderBenchmarkPreparationBundle,
    ReaderPreparedBenchmarkCase,
)
from core.reader_benchmark_runner import canonical_json_bytes
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
    ReaderEvaluationCaseManifest,
    ReaderPromotionThresholds,
)
from core.reader_prepared_batch_runner import ReaderPreparedBatchRunner

REPO_ROOT = Path(__file__).resolve().parent.parent
CLI_PATH = REPO_ROOT / "scripts" / "finalize_reader_benchmark_evidence.py"
SECRET_TEXT = "0123456789abcdef0123456789abcdef"
RAW_TEXT = "Portable finalization claim."


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
            artifact_ids=(f"prediction:{replay_index}",),
        )
        measurement = ReaderExecutionMeasurement(
            section_latencies_ms=(4,),
            session_wall_time_ms=8,
            model_tokens=0,
            projection_bytes=96,
            rebuild_time_ms=1,
            query_path_latency_delta_ms=0,
            resume_reused_units=0,
            resume_eligible_units=0,
        )
        return ReaderLocalPipelineResult(
            prediction=prediction,
            measurement=measurement,
            run_artifact_ids=(f"run:{replay_index}",),
        )


def _environment() -> EvaluationEnvironment:
    return EvaluationEnvironment(
        commit_sha="portable-commit-001",
        runner_id="portable-runner-001",
        python_version="3.11",
        hardware_profile="test-cpu",
        config_digest="portable-config-001",
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


def _threshold_payload(thresholds: ReaderPromotionThresholds) -> dict[str, object]:
    return {
        "schema_version": "reader-core.promotion-thresholds.v1",
        "min_total_cases": thresholds.min_total_cases,
        "min_synthetic_cases": thresholds.min_synthetic_cases,
        "min_real_cases": thresholds.min_real_cases,
        "min_human_labelled_cases": thresholds.min_human_labelled_cases,
        "min_claim_fidelity": thresholds.min_claim_fidelity,
        "min_source_span_precision": thresholds.min_source_span_precision,
        "min_source_span_recall": thresholds.min_source_span_recall,
        "min_critical_exception_recall": (
            thresholds.min_critical_exception_recall
        ),
        "min_relation_recall": thresholds.min_relation_recall,
        "max_false_relation_rate": thresholds.max_false_relation_rate,
        "min_contradiction_recall": thresholds.min_contradiction_recall,
        "max_orphan_claim_rate": thresholds.max_orphan_claim_rate,
        "min_qualifier_connectivity": thresholds.min_qualifier_connectivity,
        "max_unsupported_synthesis_rate": (
            thresholds.max_unsupported_synthesis_rate
        ),
        "min_replay_match_rate": thresholds.min_replay_match_rate,
        "min_resume_reuse_ratio": thresholds.min_resume_reuse_ratio,
        "max_query_path_latency_delta_ms": (
            thresholds.max_query_path_latency_delta_ms
        ),
        "max_section_latency_p95_ms": thresholds.max_section_latency_p95_ms,
        "max_model_tokens_per_case": thresholds.max_model_tokens_per_case,
    }


def _preparation(
    environment: EvaluationEnvironment,
    thresholds: ReaderPromotionThresholds,
) -> ReaderBenchmarkPreparationBundle:
    document_id = "portable-document-001"
    revision = sha256(RAW_TEXT.encode("utf-8")).hexdigest()
    descriptor = CorpusDocumentDescriptor(
        document_id=document_id,
        relative_path="documents/portable-document-001.txt",
        source_revision=revision,
        content_sha256=revision,
        byte_size=len(RAW_TEXT.encode("utf-8")),
        char_count=len(RAW_TEXT),
        media_type="text/plain; charset=utf-8",
        usage_basis=CorpusUsageBasis.SYNTHETIC,
        rights_reference="project-authored-test-fixture",
        privacy_class=CorpusPrivacyClass.PUBLIC,
        redistribution_allowed=True,
    )
    span = SourceSpan.from_text(
        document_id=document_id,
        raw_text=RAW_TEXT,
        start_offset=0,
        end_offset=len(RAW_TEXT),
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
        annotator_id="portable-adjudicator",
        guideline_version="portable-guideline-v1",
        label_version="portable-labels-v1",
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
        tags=("human-adjudicated", "portable-test"),
    )
    prepared_case = ReaderPreparedBenchmarkCase(
        evidence_case_id="portable-evidence-case-001",
        benchmark_case=local_case,
        evaluation_manifest=case_manifest,
    )
    manifest = EvaluationCorpusManifest(
        corpus_name="portable-finalization-fixture",
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
        evidence_pack_id="portable-evidence-pack-001",
        evidence_import_bundle_id="portable-import-bundle-001",
        evaluation_manifest=manifest,
        prepared_cases=(prepared_case,),
        batch_plan=plan,
        initial_checkpoint=ReaderBenchmarkBatchPlanner.empty_checkpoint(plan),
    )


def _completed():
    environment = _environment()
    thresholds = _thresholds()
    preparation = _preparation(environment, thresholds)
    runner = ReaderPreparedBatchRunner()
    initial = runner.initial_state(
        preparation=preparation,
        environment=environment,
    )
    state = runner.run_pass(
        preparation=preparation,
        state=initial,
        pipeline=_Pipeline(),
    )
    envelope = ReaderBenchmarkFinalizationEnvelope.from_completed(
        preparation=preparation,
        state=state,
    )
    return preparation, state, thresholds, envelope


def test_envelope_round_trip_is_exact_and_excludes_raw_text(tmp_path: Path) -> None:
    _, _, _, envelope = _completed()
    output = tmp_path / "envelope.json"

    write_finalization_envelope(output, envelope)
    loaded = load_finalization_envelope(output)

    assert loaded == envelope
    assert output.read_bytes() == canonical_json_bytes(envelope) + b"\n"
    assert RAW_TEXT not in output.read_text(encoding="utf-8")


def test_typed_and_portable_finalization_are_identical() -> None:
    preparation, state, thresholds, envelope = _completed()
    finalizer = ReaderCompletedBatchFinalizer()

    typed = finalizer.finalize(
        preparation=preparation,
        state=state,
        thresholds=thresholds,
        key_id="portable-key",
        secret=SECRET_TEXT.encode("utf-8"),
    )
    portable = finalizer.finalize_envelope(
        envelope=envelope,
        thresholds=thresholds,
        key_id="portable-key",
        secret=SECRET_TEXT.encode("utf-8"),
    )

    assert typed == portable


def test_loader_rejects_duplicate_unknown_forged_and_noncanonical_json(
    tmp_path: Path,
) -> None:
    _, _, _, envelope = _completed()
    canonical = canonical_json_bytes(envelope).decode("utf-8")

    duplicate = tmp_path / "duplicate.json"
    duplicate.write_text(
        '{"preparation_id":"duplicate",' + canonical[1:] + "\n",
        encoding="utf-8",
    )
    with pytest.raises(ReaderBenchmarkPortabilityError, match="duplicate JSON key"):
        load_finalization_envelope(duplicate)

    payload = json.loads(canonical)
    payload["unknown"] = True
    unknown = tmp_path / "unknown.json"
    unknown.write_text(
        json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(ReaderBenchmarkPortabilityError, match="unknown"):
        load_finalization_envelope(unknown)

    del payload["unknown"]
    payload["envelope_id"] = "forged-envelope"
    forged = tmp_path / "forged.json"
    forged.write_text(
        json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(ReaderBenchmarkPortabilityError, match="envelope_id"):
        load_finalization_envelope(forged)

    noncanonical = tmp_path / "noncanonical.json"
    noncanonical.write_text(json.dumps(json.loads(canonical), indent=2), encoding="utf-8")
    with pytest.raises(ReaderBenchmarkPortabilityError, match="canonical JSON"):
        load_finalization_envelope(noncanonical)


def test_incomplete_state_cannot_be_exported() -> None:
    environment = _environment()
    thresholds = _thresholds()
    preparation = _preparation(environment, thresholds)
    state = ReaderPreparedBatchRunner.initial_state(
        preparation=preparation,
        environment=environment,
    )

    with pytest.raises(
        ReaderBenchmarkPortabilityError,
        match="complete successful",
    ):
        ReaderBenchmarkFinalizationEnvelope.from_completed(
            preparation=preparation,
            state=state,
        )


def test_cli_finalizes_envelope_and_refuses_overwrite(tmp_path: Path) -> None:
    _, _, thresholds, envelope = _completed()
    envelope_path = tmp_path / "envelope.json"
    thresholds_path = tmp_path / "thresholds.json"
    bundle_path = tmp_path / "bundle.json"
    signature_path = tmp_path / "signature.json"
    evidence_path = tmp_path / "evidence.json"
    write_finalization_envelope(envelope_path, envelope)
    thresholds_path.write_text(
        json.dumps(
            _threshold_payload(thresholds),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )
    env = {
        "PATH": str(Path(sys.executable).parent),
        "PYTHONPATH": str(REPO_ROOT),
        "RDR22_HMAC_KEY": SECRET_TEXT,
    }
    command = [
        sys.executable,
        str(CLI_PATH),
        "--envelope",
        str(envelope_path),
        "--thresholds",
        str(thresholds_path),
        "--bundle-output",
        str(bundle_path),
        "--signature-output",
        str(signature_path),
        "--evidence-output",
        str(evidence_path),
        "--hmac-key-env",
        "RDR22_HMAC_KEY",
        "--key-id",
        "portable-cli-key",
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
    assert bundle_path.is_file()
    assert signature_path.is_file()
    assert evidence_path.is_file()
    summary = json.loads(first.stdout)
    assert summary["decision"] == "insufficient_evidence"
    assert summary["operator_go_required"] is True
    assert summary["live_integration_authorized"] is False
    for path in (bundle_path, signature_path, evidence_path):
        assert SECRET_TEXT not in path.read_text(encoding="utf-8")

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
