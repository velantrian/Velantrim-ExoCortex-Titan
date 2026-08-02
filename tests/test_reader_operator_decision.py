from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

import pytest

from core.reader_benchmark_artifact_retention import (
    ArtifactRetentionClass,
    ReaderArtifactRetentionVerificationReceipt,
    ReaderBenchmarkArtifactRetentionManifest,
    ReaderRetainedBenchmarkArtifact,
)
from core.reader_benchmark_evidence_verification import (
    ReaderBenchmarkEvidenceVerificationReceipt,
)
from core.reader_benchmark_runner import write_canonical_json
from core.reader_evaluation import PromotionDecision
from core.reader_operator_decision import (
    OperatorDecisionDisposition,
    OperatorDecisionStatus,
    ReaderOperatorDecisionBuilder,
    ReaderOperatorDecisionError,
    ReaderOperatorDecisionEvaluator,
    ReaderOperatorDecisionSigner,
    ReaderOperatorDecisionSource,
    ReaderOperatorRevocationSigner,
    ReaderOperatorRevocationSource,
    load_benchmark_verification_receipt,
    load_operator_decision,
    load_operator_decision_signature,
    load_operator_decision_source,
    load_operator_revocation,
    load_operator_revocation_signature,
    load_operator_revocation_source,
    load_retention_verification_receipt,
    write_operator_decision_source,
    write_operator_revocation_source,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
CREATE_CLI = REPO_ROOT / "scripts" / "create_reader_operator_decision.py"
REVOKE_CLI = REPO_ROOT / "scripts" / "revoke_reader_operator_decision.py"
EVALUATE_CLI = REPO_ROOT / "scripts" / "evaluate_reader_operator_decision.py"
SECRET = b"0123456789abcdef0123456789abcdef"
WRONG_SECRET = b"abcdef0123456789abcdef0123456789"


def _evidence_chain(
    *,
    decision: PromotionDecision = PromotionDecision.ELIGIBLE_FOR_OPERATOR_REVIEW,
):
    evidence_id = "operator-evidence-001"
    benchmark_verification = ReaderBenchmarkEvidenceVerificationReceipt(
        envelope_id="operator-envelope-001",
        evidence_id=evidence_id,
        benchmark_bundle_id="operator-bundle-001",
        signature_id="operator-benchmark-signature-001",
        key_id="benchmark-key-001",
        bundle_file_sha256="1" * 64,
        signature_file_sha256="2" * 64,
        evidence_file_sha256="3" * 64,
        decision=decision,
        operator_go_required=True,
        live_integration_authorized=False,
    )
    retained = ReaderRetainedBenchmarkArtifact(
        artifact_id="operator-artifact-001",
        relative_path="artifacts/operator-artifact-001.bin",
        media_type="application/octet-stream",
        retention_class=ArtifactRetentionClass.BENCHMARK_OUTPUT,
        content_sha256=sha256(b"operator artifact").hexdigest(),
        byte_size=len(b"operator artifact"),
    )
    manifest = ReaderBenchmarkArtifactRetentionManifest(
        evidence_id=evidence_id,
        evidence_verification_id=benchmark_verification.verification_id,
        benchmark_bundle_id=benchmark_verification.benchmark_bundle_id,
        benchmark_signature_id=benchmark_verification.signature_id,
        evidence_file_sha256=benchmark_verification.evidence_file_sha256,
        source_spec_id="operator-source-spec-001",
        artifact_index_id="operator-artifact-index-001",
        artifacts=(retained,),
        total_byte_size=retained.byte_size,
        decision=decision,
        operator_go_required=True,
        live_integration_authorized=False,
    )
    retention_verification = ReaderArtifactRetentionVerificationReceipt(
        manifest_id=manifest.manifest_id,
        retention_signature_id="operator-retention-signature-001",
        evidence_id=evidence_id,
        evidence_verification_id=benchmark_verification.verification_id,
        verified_record_ids=(retained.record_id,),
        verified_artifact_count=1,
        verified_total_byte_size=retained.byte_size,
        decision=decision,
        operator_go_required=True,
        live_integration_authorized=False,
    )
    return benchmark_verification, manifest, retention_verification


def _approval_source() -> ReaderOperatorDecisionSource:
    return ReaderOperatorDecisionSource(
        operator_id="operator-alpha",
        disposition=OperatorDecisionDisposition.APPROVE_SHADOW_ONLY,
        decided_at_utc="2026-08-01T10:00:00Z",
        valid_from_utc="2026-08-01T10:15:00Z",
        valid_until_utc="2026-08-02T10:15:00Z",
        rationale_codes=(),
        condition_codes=(
            "isolated_shadow_only",
            "no_persistent_writes",
        ),
    )


def _decision(
    *,
    review: PromotionDecision = PromotionDecision.ELIGIBLE_FOR_OPERATOR_REVIEW,
):
    benchmark, manifest, retention = _evidence_chain(decision=review)
    decision = ReaderOperatorDecisionBuilder().build(
        benchmark_verification=benchmark,
        retention_manifest=manifest,
        retention_verification=retention,
        source=_approval_source(),
    )
    signature = ReaderOperatorDecisionSigner.sign(
        decision,
        key_id="operator-key-v1",
        secret=SECRET,
    )
    return benchmark, manifest, retention, decision, signature


def test_eligible_evidence_can_create_shadow_only_decision() -> None:
    _, _, _, decision, signature = _decision()

    assert decision.shadow_evaluation_authorized is True
    assert decision.live_integration_authorized is False
    assert decision.query_path_wiring_authorized is False
    assert decision.canon_write_authorized is False
    assert decision.memory_write_authorized is False
    assert ReaderOperatorDecisionSigner.verify(
        decision,
        signature,
        secret=SECRET,
    ) is True
    assert ReaderOperatorDecisionSigner.verify(
        decision,
        signature,
        secret=WRONG_SECRET,
    ) is False


def test_shadow_approval_requires_eligible_review() -> None:
    benchmark, manifest, retention = _evidence_chain(
        decision=PromotionDecision.INSUFFICIENT_EVIDENCE
    )

    with pytest.raises(
        ReaderOperatorDecisionError,
        match="eligible benchmark evidence",
    ):
        ReaderOperatorDecisionBuilder().build(
            benchmark_verification=benchmark,
            retention_manifest=manifest,
            retention_verification=retention,
            source=_approval_source(),
        )


def test_explicit_time_statuses_are_deterministic() -> None:
    _, _, _, decision, signature = _decision()
    evaluator = ReaderOperatorDecisionEvaluator()

    not_yet = evaluator.evaluate(
        decision=decision,
        decision_signature=signature,
        secret=SECRET,
        as_of_utc="2026-08-01T10:14:59Z",
    )
    active = evaluator.evaluate(
        decision=decision,
        decision_signature=signature,
        secret=SECRET,
        as_of_utc="2026-08-01T10:15:00Z",
    )
    expired = evaluator.evaluate(
        decision=decision,
        decision_signature=signature,
        secret=SECRET,
        as_of_utc="2026-08-02T10:15:00Z",
    )

    assert not_yet.status is OperatorDecisionStatus.NOT_YET_VALID
    assert active.status is OperatorDecisionStatus.ACTIVE_SHADOW_APPROVAL
    assert active.shadow_evaluation_authorized is True
    assert expired.status is OperatorDecisionStatus.EXPIRED
    assert expired.shadow_evaluation_authorized is False
    for receipt in (not_yet, active, expired):
        assert receipt.live_integration_authorized is False
        assert receipt.query_path_wiring_authorized is False
        assert receipt.canon_write_authorized is False
        assert receipt.memory_write_authorized is False


def test_defer_and_no_go_require_reasons_and_never_authorize_shadow() -> None:
    benchmark, manifest, retention = _evidence_chain()
    for disposition in (
        OperatorDecisionDisposition.DEFER,
        OperatorDecisionDisposition.NO_GO,
    ):
        source = ReaderOperatorDecisionSource(
            operator_id="operator-alpha",
            disposition=disposition,
            decided_at_utc="2026-08-01T10:00:00Z",
            valid_from_utc="2026-08-01T10:00:00Z",
            valid_until_utc="2026-08-02T10:00:00Z",
            rationale_codes=("manual_review_required",),
            condition_codes=(),
        )
        decision = ReaderOperatorDecisionBuilder().build(
            benchmark_verification=benchmark,
            retention_manifest=manifest,
            retention_verification=retention,
            source=source,
        )
        signature = ReaderOperatorDecisionSigner.sign(
            decision,
            key_id="operator-key-v1",
            secret=SECRET,
        )
        status = ReaderOperatorDecisionEvaluator().evaluate(
            decision=decision,
            decision_signature=signature,
            secret=SECRET,
            as_of_utc="2026-08-01T12:00:00Z",
        )
        assert decision.shadow_evaluation_authorized is False
        assert status.status is OperatorDecisionStatus.NON_APPROVING
        assert status.shadow_evaluation_authorized is False

    with pytest.raises(ReaderOperatorDecisionError, match="rationale codes"):
        ReaderOperatorDecisionSource(
            operator_id="operator-alpha",
            disposition=OperatorDecisionDisposition.NO_GO,
            decided_at_utc="2026-08-01T10:00:00Z",
            valid_from_utc="2026-08-01T10:00:00Z",
            valid_until_utc="2026-08-02T10:00:00Z",
            rationale_codes=(),
            condition_codes=(),
        )


def test_foreign_retention_chain_and_forbidden_authority_fail_closed() -> None:
    benchmark, manifest, retention = _evidence_chain()

    with pytest.raises(ReaderOperatorDecisionError, match="different manifest"):
        ReaderOperatorDecisionBuilder().build(
            benchmark_verification=benchmark,
            retention_manifest=manifest,
            retention_verification=replace(
                retention,
                manifest_id="foreign-manifest",
                verification_id="",
            ),
            source=_approval_source(),
        )

    _, _, _, decision, _ = _decision()
    with pytest.raises(
        ReaderOperatorDecisionError,
        match="live_integration_authorized must remain false",
    ):
        replace(
            decision,
            live_integration_authorized=True,
            decision_id="",
        )


def test_signed_revocation_disables_active_approval() -> None:
    _, _, _, decision, decision_signature = _decision()
    source = ReaderOperatorRevocationSource(
        operator_id="operator-beta",
        revoked_at_utc="2026-08-01T12:00:00Z",
        rationale_codes=("artifact_investigation_opened",),
    )
    revocation = ReaderOperatorRevocationSigner.create(
        decision=decision,
        decision_signature=decision_signature,
        source=source,
    )
    revocation_signature = ReaderOperatorRevocationSigner.sign(
        revocation,
        key_id="operator-revocation-key-v1",
        secret=SECRET,
    )
    evaluator = ReaderOperatorDecisionEvaluator()

    before = evaluator.evaluate(
        decision=decision,
        decision_signature=decision_signature,
        secret=SECRET,
        as_of_utc="2026-08-01T11:59:59Z",
        revocation=revocation,
        revocation_signature=revocation_signature,
    )
    after = evaluator.evaluate(
        decision=decision,
        decision_signature=decision_signature,
        secret=SECRET,
        as_of_utc="2026-08-01T12:00:00Z",
        revocation=revocation,
        revocation_signature=revocation_signature,
    )

    assert before.status is OperatorDecisionStatus.ACTIVE_SHADOW_APPROVAL
    assert after.status is OperatorDecisionStatus.REVOKED
    assert after.shadow_evaluation_authorized is False


def test_canonical_loaders_and_clis_cover_full_lifecycle(tmp_path: Path) -> None:
    benchmark, manifest, retention = _evidence_chain()
    source = _approval_source()
    benchmark_path = tmp_path / "benchmark-verification.json"
    manifest_path = tmp_path / "retention-manifest.json"
    retention_path = tmp_path / "retention-verification.json"
    source_path = tmp_path / "decision-source.json"
    decision_path = tmp_path / "decision.json"
    decision_signature_path = tmp_path / "decision-signature.json"
    revocation_source_path = tmp_path / "revocation-source.json"
    revocation_path = tmp_path / "revocation.json"
    revocation_signature_path = tmp_path / "revocation-signature.json"
    active_status_path = tmp_path / "active-status.json"
    revoked_status_path = tmp_path / "revoked-status.json"
    write_canonical_json(benchmark_path, benchmark)
    write_canonical_json(manifest_path, manifest)
    write_canonical_json(retention_path, retention)
    write_operator_decision_source(source_path, source)

    assert load_benchmark_verification_receipt(benchmark_path) == benchmark
    assert load_retention_verification_receipt(retention_path) == retention
    assert load_operator_decision_source(source_path) == source

    env = {
        "PATH": str(Path(sys.executable).parent),
        "PYTHONPATH": str(REPO_ROOT),
        "RDR25_HMAC_KEY": SECRET.decode("utf-8"),
    }
    create = subprocess.run(
        [
            sys.executable,
            str(CREATE_CLI),
            "--benchmark-verification",
            str(benchmark_path),
            "--retention-manifest",
            str(manifest_path),
            "--retention-verification",
            str(retention_path),
            "--source",
            str(source_path),
            "--decision-output",
            str(decision_path),
            "--signature-output",
            str(decision_signature_path),
            "--hmac-key-env",
            "RDR25_HMAC_KEY",
            "--key-id",
            "operator-cli-key",
        ],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert create.returncode == 0, create.stderr
    decision = load_operator_decision(decision_path)
    decision_signature = load_operator_decision_signature(
        decision_signature_path
    )
    assert decision.shadow_evaluation_authorized is True

    active = subprocess.run(
        [
            sys.executable,
            str(EVALUATE_CLI),
            "--decision",
            str(decision_path),
            "--decision-signature",
            str(decision_signature_path),
            "--as-of-utc",
            "2026-08-01T11:00:00Z",
            "--hmac-key-env",
            "RDR25_HMAC_KEY",
            "--status-output",
            str(active_status_path),
            "--require-active-shadow-approval",
        ],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert active.returncode == 0, active.stderr
    assert json.loads(active.stdout)["status"] == "active_shadow_approval"

    revocation_source = ReaderOperatorRevocationSource(
        operator_id="operator-beta",
        revoked_at_utc="2026-08-01T12:00:00Z",
        rationale_codes=("manual_revocation",),
    )
    write_operator_revocation_source(
        revocation_source_path,
        revocation_source,
    )
    assert load_operator_revocation_source(
        revocation_source_path
    ) == revocation_source
    revoke = subprocess.run(
        [
            sys.executable,
            str(REVOKE_CLI),
            "--decision",
            str(decision_path),
            "--decision-signature",
            str(decision_signature_path),
            "--source",
            str(revocation_source_path),
            "--revocation-output",
            str(revocation_path),
            "--signature-output",
            str(revocation_signature_path),
            "--hmac-key-env",
            "RDR25_HMAC_KEY",
            "--key-id",
            "operator-revocation-cli-key",
        ],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert revoke.returncode == 0, revoke.stderr
    assert load_operator_revocation(revocation_path).decision_id == decision.decision_id
    assert load_operator_revocation_signature(
        revocation_signature_path
    ).revocation_id == load_operator_revocation(revocation_path).revocation_id

    revoked = subprocess.run(
        [
            sys.executable,
            str(EVALUATE_CLI),
            "--decision",
            str(decision_path),
            "--decision-signature",
            str(decision_signature_path),
            "--revocation",
            str(revocation_path),
            "--revocation-signature",
            str(revocation_signature_path),
            "--as-of-utc",
            "2026-08-01T12:00:00Z",
            "--hmac-key-env",
            "RDR25_HMAC_KEY",
            "--status-output",
            str(revoked_status_path),
            "--require-active-shadow-approval",
        ],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert revoked.returncode == 3, revoked.stderr
    assert json.loads(revoked.stdout)["status"] == "revoked"
    secret_text = SECRET.decode("utf-8")
    for path in (
        decision_path,
        decision_signature_path,
        revocation_path,
        revocation_signature_path,
        active_status_path,
        revoked_status_path,
    ):
        assert secret_text not in path.read_text(encoding="utf-8")

    repeated = subprocess.run(
        [
            sys.executable,
            str(CREATE_CLI),
            "--benchmark-verification",
            str(benchmark_path),
            "--retention-manifest",
            str(manifest_path),
            "--retention-verification",
            str(retention_path),
            "--source",
            str(source_path),
            "--decision-output",
            str(decision_path),
            "--signature-output",
            str(decision_signature_path),
            "--hmac-key-env",
            "RDR25_HMAC_KEY",
            "--key-id",
            "operator-cli-key",
        ],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert repeated.returncode == 2
    assert "refusing to overwrite" in repeated.stderr
