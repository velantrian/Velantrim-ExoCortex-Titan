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
    ReaderOperatorDecisionBuilder,
    ReaderOperatorDecisionSigner,
    ReaderOperatorDecisionSource,
    ReaderOperatorRevocationSigner,
    ReaderOperatorRevocationSource,
)
from core.reader_shadow_burn_in import (
    ReaderShadowBurnInController,
    ReaderShadowBurnInControlSigner,
    ReaderShadowBurnInControlSource,
    ReaderShadowBurnInError,
    ReaderShadowBurnInEvaluator,
    ReaderShadowBurnInPlanBuilder,
    ReaderShadowBurnInPlanSigner,
    ReaderShadowBurnInSource,
    ShadowBurnInControlAction,
    ShadowBurnInControlState,
    ShadowBurnInStatus,
    load_shadow_burn_in_control_receipt,
    load_shadow_burn_in_control_signature,
    load_shadow_burn_in_control_source,
    load_shadow_burn_in_plan,
    load_shadow_burn_in_plan_signature,
    load_shadow_burn_in_source,
    load_shadow_burn_in_status,
    write_shadow_burn_in_control_source,
    write_shadow_burn_in_source,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
CREATE_PLAN_CLI = REPO_ROOT / "scripts" / "create_reader_shadow_burn_in_plan.py"
CONTROL_CLI = REPO_ROOT / "scripts" / "control_reader_shadow_burn_in.py"
EVALUATE_CLI = REPO_ROOT / "scripts" / "evaluate_reader_shadow_burn_in.py"
SECRET = b"0123456789abcdef0123456789abcdef"
WRONG_SECRET = b"abcdef0123456789abcdef0123456789"


def _evidence_chain():
    evidence_id = "shadow-evidence-001"
    benchmark = ReaderBenchmarkEvidenceVerificationReceipt(
        envelope_id="shadow-envelope-001",
        evidence_id=evidence_id,
        benchmark_bundle_id="shadow-bundle-001",
        signature_id="shadow-benchmark-signature-001",
        key_id="benchmark-key-001",
        bundle_file_sha256="1" * 64,
        signature_file_sha256="2" * 64,
        evidence_file_sha256="3" * 64,
        decision=PromotionDecision.ELIGIBLE_FOR_OPERATOR_REVIEW,
        operator_go_required=True,
        live_integration_authorized=False,
    )
    retained = ReaderRetainedBenchmarkArtifact(
        artifact_id="shadow-artifact-001",
        relative_path="artifacts/shadow-artifact-001.bin",
        media_type="application/octet-stream",
        retention_class=ArtifactRetentionClass.BENCHMARK_OUTPUT,
        content_sha256=sha256(b"shadow artifact").hexdigest(),
        byte_size=len(b"shadow artifact"),
    )
    manifest = ReaderBenchmarkArtifactRetentionManifest(
        evidence_id=evidence_id,
        evidence_verification_id=benchmark.verification_id,
        benchmark_bundle_id=benchmark.benchmark_bundle_id,
        benchmark_signature_id=benchmark.signature_id,
        evidence_file_sha256=benchmark.evidence_file_sha256,
        source_spec_id="shadow-retention-source-001",
        artifact_index_id="shadow-artifact-index-001",
        artifacts=(retained,),
        total_byte_size=retained.byte_size,
        decision=PromotionDecision.ELIGIBLE_FOR_OPERATOR_REVIEW,
        operator_go_required=True,
        live_integration_authorized=False,
    )
    retention = ReaderArtifactRetentionVerificationReceipt(
        manifest_id=manifest.manifest_id,
        retention_signature_id="shadow-retention-signature-001",
        evidence_id=evidence_id,
        evidence_verification_id=benchmark.verification_id,
        verified_record_ids=(retained.record_id,),
        verified_artifact_count=1,
        verified_total_byte_size=retained.byte_size,
        decision=PromotionDecision.ELIGIBLE_FOR_OPERATOR_REVIEW,
        operator_go_required=True,
        live_integration_authorized=False,
    )
    return benchmark, manifest, retention


def _operator_decision():
    benchmark, manifest, retention = _evidence_chain()
    source = ReaderOperatorDecisionSource(
        operator_id="operator-shadow-alpha",
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
    decision = ReaderOperatorDecisionBuilder().build(
        benchmark_verification=benchmark,
        retention_manifest=manifest,
        retention_verification=retention,
        source=source,
    )
    signature = ReaderOperatorDecisionSigner.sign(
        decision,
        key_id="operator-shadow-key-v1",
        secret=SECRET,
    )
    return decision, signature


def _campaign_source(
    *,
    planned_start_utc: str = "2026-08-01T10:30:00Z",
    planned_end_utc: str = "2026-08-01T12:00:00Z",
) -> ReaderShadowBurnInSource:
    return ReaderShadowBurnInSource(
        campaign_name="reader-shadow-burn-in-alpha",
        environment_id="shadow-environment-fixed-001",
        harness_digest="shadow-harness-digest-001",
        planned_start_utc=planned_start_utc,
        planned_end_utc=planned_end_utc,
        work_item_ids=("work-item-a", "work-item-b"),
        max_attempts_per_work_item=2,
        per_work_item_timeout_ms=30_000,
        max_total_wall_time_ms=3_600_000,
        max_total_model_tokens=200_000,
        max_total_artifact_bytes=50_000_000,
        max_consecutive_failures=3,
        condition_codes=(
            "kill_switch_required",
            "no_production_traffic",
            "no_user_visible_output",
        ),
    )


def _plan():
    decision, decision_signature = _operator_decision()
    plan = ReaderShadowBurnInPlanBuilder().build(
        source=_campaign_source(),
        decision=decision,
        decision_signature=decision_signature,
        secret=SECRET,
    )
    plan_signature = ReaderShadowBurnInPlanSigner.sign(
        plan,
        key_id="shadow-plan-key-v1",
        secret=SECRET,
    )
    return decision, decision_signature, plan, plan_signature


def _control_source(
    action: ShadowBurnInControlAction,
    issued_at_utc: str,
    *,
    previous_receipt_id: str | None = None,
) -> ReaderShadowBurnInControlSource:
    return ReaderShadowBurnInControlSource(
        operator_id="operator-shadow-control",
        action=action,
        issued_at_utc=issued_at_utc,
        reason_codes=(f"operator_{action.value}",),
        previous_receipt_id=previous_receipt_id,
    )


def _apply(
    *,
    plan,
    plan_signature,
    source: ReaderShadowBurnInControlSource,
    previous_receipt=None,
    previous_signature=None,
):
    receipt = ReaderShadowBurnInController().apply(
        plan=plan,
        plan_signature=plan_signature,
        source=source,
        secret=SECRET,
        previous_receipt=previous_receipt,
        previous_signature=previous_signature,
    )
    signature = ReaderShadowBurnInControlSigner.sign(
        receipt,
        key_id="shadow-control-key-v1",
        secret=SECRET,
    )
    return receipt, signature


def test_active_operator_decision_builds_bounded_shadow_only_plan() -> None:
    _, _, plan, signature = _plan()

    assert plan.shadow_evaluation_authorized is True
    assert plan.production_traffic_authorized is False
    assert plan.user_visible_output_authorized is False
    assert plan.background_scheduling_authorized is False
    assert plan.query_path_wiring_authorized is False
    assert plan.canon_write_authorized is False
    assert plan.memory_write_authorized is False
    assert plan.graph_write_authorized is False
    assert plan.tool_execution_authorized is False
    assert ReaderShadowBurnInPlanSigner.verify(
        plan,
        signature,
        secret=SECRET,
    ) is True
    assert ReaderShadowBurnInPlanSigner.verify(
        plan,
        signature,
        secret=WRONG_SECRET,
    ) is False


def test_campaign_window_must_remain_inside_operator_approval() -> None:
    decision, decision_signature = _operator_decision()

    with pytest.raises(ReaderShadowBurnInError, match="approval window"):
        ReaderShadowBurnInPlanBuilder().build(
            source=_campaign_source(
                planned_end_utc="2026-08-03T12:00:00Z"
            ),
            decision=decision,
            decision_signature=decision_signature,
            secret=SECRET,
        )


def test_revoked_approval_cannot_create_plan() -> None:
    decision, decision_signature = _operator_decision()
    revocation = ReaderOperatorRevocationSigner.create(
        decision=decision,
        decision_signature=decision_signature,
        source=ReaderOperatorRevocationSource(
            operator_id="operator-revoker",
            revoked_at_utc="2026-08-01T10:20:00Z",
            rationale_codes=("pre_burn_in_investigation",),
        ),
    )
    revocation_signature = ReaderOperatorRevocationSigner.sign(
        revocation,
        key_id="operator-revocation-key-v1",
        secret=SECRET,
    )

    with pytest.raises(ReaderShadowBurnInError, match="active shadow approval"):
        ReaderShadowBurnInPlanBuilder().build(
            source=_campaign_source(),
            decision=decision,
            decision_signature=decision_signature,
            secret=SECRET,
            revocation=revocation,
            revocation_signature=revocation_signature,
        )


def test_arm_status_is_time_bounded_and_never_grants_other_authority() -> None:
    decision, decision_signature, plan, plan_signature = _plan()
    receipt, signature = _apply(
        plan=plan,
        plan_signature=plan_signature,
        source=_control_source(
            ShadowBurnInControlAction.ARM,
            "2026-08-01T10:20:00Z",
        ),
    )
    evaluator = ReaderShadowBurnInEvaluator()

    not_yet = evaluator.evaluate(
        plan=plan,
        plan_signature=plan_signature,
        decision=decision,
        decision_signature=decision_signature,
        control_receipt=receipt,
        control_signature=signature,
        secret=SECRET,
        as_of_utc="2026-08-01T10:29:59Z",
    )
    ready = evaluator.evaluate(
        plan=plan,
        plan_signature=plan_signature,
        decision=decision,
        decision_signature=decision_signature,
        control_receipt=receipt,
        control_signature=signature,
        secret=SECRET,
        as_of_utc="2026-08-01T10:30:00Z",
    )
    expired = evaluator.evaluate(
        plan=plan,
        plan_signature=plan_signature,
        decision=decision,
        decision_signature=decision_signature,
        control_receipt=receipt,
        control_signature=signature,
        secret=SECRET,
        as_of_utc="2026-08-01T12:00:00Z",
    )

    assert not_yet.status is ShadowBurnInStatus.NOT_YET_VALID
    assert ready.status is ShadowBurnInStatus.READY
    assert ready.shadow_evaluation_authorized is True
    assert expired.status is ShadowBurnInStatus.EXPIRED
    for status in (not_yet, ready, expired):
        assert status.production_traffic_authorized is False
        assert status.user_visible_output_authorized is False
        assert status.background_scheduling_authorized is False
        assert status.query_path_wiring_authorized is False
        assert status.canon_write_authorized is False
        assert status.memory_write_authorized is False
        assert status.graph_write_authorized is False
        assert status.tool_execution_authorized is False


def test_pause_resume_and_stop_form_exact_signed_chain() -> None:
    decision, decision_signature, plan, plan_signature = _plan()
    armed, armed_signature = _apply(
        plan=plan,
        plan_signature=plan_signature,
        source=_control_source(
            ShadowBurnInControlAction.ARM,
            "2026-08-01T10:20:00Z",
        ),
    )
    paused, paused_signature = _apply(
        plan=plan,
        plan_signature=plan_signature,
        source=_control_source(
            ShadowBurnInControlAction.PAUSE,
            "2026-08-01T10:40:00Z",
            previous_receipt_id=armed.receipt_id,
        ),
        previous_receipt=armed,
        previous_signature=armed_signature,
    )
    resumed, resumed_signature = _apply(
        plan=plan,
        plan_signature=plan_signature,
        source=_control_source(
            ShadowBurnInControlAction.RESUME,
            "2026-08-01T10:50:00Z",
            previous_receipt_id=paused.receipt_id,
        ),
        previous_receipt=paused,
        previous_signature=paused_signature,
    )
    stopped, stopped_signature = _apply(
        plan=plan,
        plan_signature=plan_signature,
        source=_control_source(
            ShadowBurnInControlAction.STOP,
            "2026-08-01T11:00:00Z",
            previous_receipt_id=resumed.receipt_id,
        ),
        previous_receipt=resumed,
        previous_signature=resumed_signature,
    )

    assert armed.state is ShadowBurnInControlState.ARMED
    assert paused.state is ShadowBurnInControlState.PAUSED
    assert resumed.state is ShadowBurnInControlState.ARMED
    assert stopped.state is ShadowBurnInControlState.STOPPED
    assert stopped.control_allows_shadow is False
    status = ReaderShadowBurnInEvaluator().evaluate(
        plan=plan,
        plan_signature=plan_signature,
        decision=decision,
        decision_signature=decision_signature,
        control_receipt=stopped,
        control_signature=stopped_signature,
        secret=SECRET,
        as_of_utc="2026-08-01T11:01:00Z",
    )
    assert status.status is ShadowBurnInStatus.STOPPED

    with pytest.raises(ReaderShadowBurnInError, match="cannot transition"):
        _apply(
            plan=plan,
            plan_signature=plan_signature,
            source=_control_source(
                ShadowBurnInControlAction.RESUME,
                "2026-08-01T11:02:00Z",
                previous_receipt_id=stopped.receipt_id,
            ),
            previous_receipt=stopped,
            previous_signature=stopped_signature,
        )


def test_kill_switch_is_immediate_and_terminal() -> None:
    _, _, plan, plan_signature = _plan()
    killed, killed_signature = _apply(
        plan=plan,
        plan_signature=plan_signature,
        source=_control_source(
            ShadowBurnInControlAction.KILL,
            "2026-08-01T10:20:00Z",
        ),
    )

    assert killed.state is ShadowBurnInControlState.KILLED
    assert killed.control_allows_shadow is False
    assert ReaderShadowBurnInControlSigner.verify(
        killed,
        killed_signature,
        secret=SECRET,
    ) is True
    with pytest.raises(ReaderShadowBurnInError, match="cannot transition"):
        _apply(
            plan=plan,
            plan_signature=plan_signature,
            source=_control_source(
                ShadowBurnInControlAction.ARM,
                "2026-08-01T10:21:00Z",
                previous_receipt_id=killed.receipt_id,
            ),
            previous_receipt=killed,
            previous_signature=killed_signature,
        )


def test_later_operator_revocation_disables_armed_campaign() -> None:
    decision, decision_signature, plan, plan_signature = _plan()
    armed, armed_signature = _apply(
        plan=plan,
        plan_signature=plan_signature,
        source=_control_source(
            ShadowBurnInControlAction.ARM,
            "2026-08-01T10:20:00Z",
        ),
    )
    revocation = ReaderOperatorRevocationSigner.create(
        decision=decision,
        decision_signature=decision_signature,
        source=ReaderOperatorRevocationSource(
            operator_id="operator-revoker",
            revoked_at_utc="2026-08-01T11:00:00Z",
            rationale_codes=("shadow_anomaly_detected",),
        ),
    )
    revocation_signature = ReaderOperatorRevocationSigner.sign(
        revocation,
        key_id="operator-revocation-key-v1",
        secret=SECRET,
    )
    status = ReaderShadowBurnInEvaluator().evaluate(
        plan=plan,
        plan_signature=plan_signature,
        decision=decision,
        decision_signature=decision_signature,
        control_receipt=armed,
        control_signature=armed_signature,
        secret=SECRET,
        as_of_utc="2026-08-01T11:00:00Z",
        revocation=revocation,
        revocation_signature=revocation_signature,
    )

    assert status.status is ShadowBurnInStatus.APPROVAL_REVOKED
    assert status.shadow_evaluation_authorized is False


def test_foreign_signatures_and_forbidden_authority_fail_closed() -> None:
    _, _, plan, plan_signature = _plan()

    with pytest.raises(
        ReaderShadowBurnInError,
        match="plan signature verification failed",
    ):
        ReaderShadowBurnInController().apply(
            plan=plan,
            plan_signature=plan_signature,
            source=_control_source(
                ShadowBurnInControlAction.ARM,
                "2026-08-01T10:20:00Z",
            ),
            secret=WRONG_SECRET,
        )
    with pytest.raises(
        ReaderShadowBurnInError,
        match="production_traffic_authorized must remain false",
    ):
        replace(
            plan,
            production_traffic_authorized=True,
            plan_id="",
        )


def test_canonical_loaders_round_trip_all_public_artifacts(
    tmp_path: Path,
) -> None:
    decision, decision_signature, plan, plan_signature = _plan()
    source = plan.source
    control_source = _control_source(
        ShadowBurnInControlAction.ARM,
        "2026-08-01T10:20:00Z",
    )
    control_receipt, control_signature = _apply(
        plan=plan,
        plan_signature=plan_signature,
        source=control_source,
    )
    status = ReaderShadowBurnInEvaluator().evaluate(
        plan=plan,
        plan_signature=plan_signature,
        decision=decision,
        decision_signature=decision_signature,
        control_receipt=control_receipt,
        control_signature=control_signature,
        secret=SECRET,
        as_of_utc="2026-08-01T10:30:00Z",
    )
    source_path = tmp_path / "source.json"
    plan_path = tmp_path / "plan.json"
    plan_signature_path = tmp_path / "plan-signature.json"
    control_source_path = tmp_path / "control-source.json"
    control_receipt_path = tmp_path / "control-receipt.json"
    control_signature_path = tmp_path / "control-signature.json"
    status_path = tmp_path / "status.json"

    write_shadow_burn_in_source(source_path, source)
    write_canonical_json(plan_path, plan)
    write_canonical_json(plan_signature_path, plan_signature)
    write_shadow_burn_in_control_source(control_source_path, control_source)
    write_canonical_json(control_receipt_path, control_receipt)
    write_canonical_json(control_signature_path, control_signature)
    write_canonical_json(status_path, status)

    assert load_shadow_burn_in_source(source_path) == source
    assert load_shadow_burn_in_plan(plan_path) == plan
    assert load_shadow_burn_in_plan_signature(
        plan_signature_path
    ) == plan_signature
    assert load_shadow_burn_in_control_source(
        control_source_path
    ) == control_source
    assert load_shadow_burn_in_control_receipt(
        control_receipt_path
    ) == control_receipt
    assert load_shadow_burn_in_control_signature(
        control_signature_path
    ) == control_signature
    assert load_shadow_burn_in_status(status_path) == status


def test_cli_lifecycle_creates_ready_then_paused_status(tmp_path: Path) -> None:
    decision, decision_signature = _operator_decision()
    decision_path = tmp_path / "decision.json"
    decision_signature_path = tmp_path / "decision-signature.json"
    source_path = tmp_path / "campaign-source.json"
    plan_path = tmp_path / "plan.json"
    plan_signature_path = tmp_path / "plan-signature.json"
    arm_source_path = tmp_path / "arm-source.json"
    arm_receipt_path = tmp_path / "arm-receipt.json"
    arm_signature_path = tmp_path / "arm-signature.json"
    ready_status_path = tmp_path / "ready-status.json"
    pause_source_path = tmp_path / "pause-source.json"
    pause_receipt_path = tmp_path / "pause-receipt.json"
    pause_signature_path = tmp_path / "pause-signature.json"
    paused_status_path = tmp_path / "paused-status.json"
    write_canonical_json(decision_path, decision)
    write_canonical_json(decision_signature_path, decision_signature)
    write_shadow_burn_in_source(source_path, _campaign_source())

    env = {
        "PATH": str(Path(sys.executable).parent),
        "PYTHONPATH": str(REPO_ROOT),
        "RDR26_HMAC_KEY": SECRET.decode("utf-8"),
    }
    create_plan = subprocess.run(
        [
            sys.executable,
            str(CREATE_PLAN_CLI),
            "--decision",
            str(decision_path),
            "--decision-signature",
            str(decision_signature_path),
            "--source",
            str(source_path),
            "--plan-output",
            str(plan_path),
            "--signature-output",
            str(plan_signature_path),
            "--hmac-key-env",
            "RDR26_HMAC_KEY",
            "--key-id",
            "shadow-plan-cli-key",
        ],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert create_plan.returncode == 0, create_plan.stderr
    plan = load_shadow_burn_in_plan(plan_path)
    plan_signature = load_shadow_burn_in_plan_signature(plan_signature_path)

    arm_source = _control_source(
        ShadowBurnInControlAction.ARM,
        "2026-08-01T10:20:00Z",
    )
    write_shadow_burn_in_control_source(arm_source_path, arm_source)
    arm = subprocess.run(
        [
            sys.executable,
            str(CONTROL_CLI),
            "--plan",
            str(plan_path),
            "--plan-signature",
            str(plan_signature_path),
            "--source",
            str(arm_source_path),
            "--receipt-output",
            str(arm_receipt_path),
            "--signature-output",
            str(arm_signature_path),
            "--hmac-key-env",
            "RDR26_HMAC_KEY",
            "--key-id",
            "shadow-control-cli-key",
        ],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert arm.returncode == 0, arm.stderr
    arm_receipt = load_shadow_burn_in_control_receipt(arm_receipt_path)
    assert ReaderShadowBurnInPlanSigner.verify(
        plan,
        plan_signature,
        secret=SECRET,
    ) is True

    ready = subprocess.run(
        [
            sys.executable,
            str(EVALUATE_CLI),
            "--plan",
            str(plan_path),
            "--plan-signature",
            str(plan_signature_path),
            "--decision",
            str(decision_path),
            "--decision-signature",
            str(decision_signature_path),
            "--control-receipt",
            str(arm_receipt_path),
            "--control-signature",
            str(arm_signature_path),
            "--as-of-utc",
            "2026-08-01T10:30:00Z",
            "--status-output",
            str(ready_status_path),
            "--hmac-key-env",
            "RDR26_HMAC_KEY",
            "--require-ready",
        ],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert ready.returncode == 0, ready.stderr
    assert json.loads(ready.stdout)["status"] == "ready"

    pause_source = _control_source(
        ShadowBurnInControlAction.PAUSE,
        "2026-08-01T10:40:00Z",
        previous_receipt_id=arm_receipt.receipt_id,
    )
    write_shadow_burn_in_control_source(pause_source_path, pause_source)
    pause = subprocess.run(
        [
            sys.executable,
            str(CONTROL_CLI),
            "--plan",
            str(plan_path),
            "--plan-signature",
            str(plan_signature_path),
            "--source",
            str(pause_source_path),
            "--previous-receipt",
            str(arm_receipt_path),
            "--previous-signature",
            str(arm_signature_path),
            "--receipt-output",
            str(pause_receipt_path),
            "--signature-output",
            str(pause_signature_path),
            "--hmac-key-env",
            "RDR26_HMAC_KEY",
            "--key-id",
            "shadow-control-cli-key",
        ],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert pause.returncode == 0, pause.stderr

    paused = subprocess.run(
        [
            sys.executable,
            str(EVALUATE_CLI),
            "--plan",
            str(plan_path),
            "--plan-signature",
            str(plan_signature_path),
            "--decision",
            str(decision_path),
            "--decision-signature",
            str(decision_signature_path),
            "--control-receipt",
            str(pause_receipt_path),
            "--control-signature",
            str(pause_signature_path),
            "--as-of-utc",
            "2026-08-01T10:41:00Z",
            "--status-output",
            str(paused_status_path),
            "--hmac-key-env",
            "RDR26_HMAC_KEY",
            "--require-ready",
        ],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert paused.returncode == 3, paused.stderr
    assert json.loads(paused.stdout)["status"] == "paused"

    secret_text = SECRET.decode("utf-8")
    for path in (
        plan_path,
        plan_signature_path,
        arm_receipt_path,
        arm_signature_path,
        ready_status_path,
        pause_receipt_path,
        pause_signature_path,
        paused_status_path,
    ):
        assert secret_text not in path.read_text(encoding="utf-8")

    repeated = subprocess.run(
        [
            sys.executable,
            str(CREATE_PLAN_CLI),
            "--decision",
            str(decision_path),
            "--decision-signature",
            str(decision_signature_path),
            "--source",
            str(source_path),
            "--plan-output",
            str(plan_path),
            "--signature-output",
            str(plan_signature_path),
            "--hmac-key-env",
            "RDR26_HMAC_KEY",
            "--key-id",
            "shadow-plan-cli-key",
        ],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert repeated.returncode == 2
    assert "refusing to overwrite" in repeated.stderr
