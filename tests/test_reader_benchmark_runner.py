from dataclasses import replace
import json
from pathlib import Path
import subprocess
import sys

import pytest

from core.reader_benchmark_runner import (
    ReaderBenchmarkError,
    ReaderBenchmarkInput,
    ReaderBenchmarkRunner,
    ReaderBenchmarkSigner,
    canonical_json_bytes,
    load_benchmark_input,
    load_evaluation_manifest,
    load_promotion_thresholds,
    write_canonical_json,
)
from core.reader_evaluation import PromotionDecision


REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "reader_core"
MANIFEST_PATH = FIXTURE_ROOT / "rdr_09_synthetic_evaluation.json"
INPUT_PATH = FIXTURE_ROOT / "rdr_10_benchmark_input.json"
THRESHOLDS_PATH = FIXTURE_ROOT / "rdr_10_thresholds.json"
CLI_PATH = REPO_ROOT / "scripts" / "run_reader_benchmark.py"


def _bundle():
    manifest = load_evaluation_manifest(MANIFEST_PATH)
    benchmark_input = load_benchmark_input(INPUT_PATH)
    thresholds = load_promotion_thresholds(THRESHOLDS_PATH)
    bundle = ReaderBenchmarkRunner().run(
        manifest,
        benchmark_input,
        thresholds,
    )
    return manifest, benchmark_input, thresholds, bundle


def test_synthetic_benchmark_is_reproducible_but_not_production_evidence() -> None:
    _, benchmark_input, _, bundle = _bundle()
    reversed_input = ReaderBenchmarkInput(
        environment=benchmark_input.environment,
        observations=tuple(reversed(benchmark_input.observations)),
    )
    manifest = load_evaluation_manifest(MANIFEST_PATH)
    thresholds = load_promotion_thresholds(THRESHOLDS_PATH)
    repeated = ReaderBenchmarkRunner().run(
        manifest,
        reversed_input,
        thresholds,
    )

    assert bundle == repeated
    assert canonical_json_bytes(bundle) == canonical_json_bytes(repeated)
    assert bundle.report.metrics.total_case_count == 4
    assert bundle.report.metrics.synthetic_case_count == 4
    assert bundle.report.metrics.real_case_count == 0
    assert bundle.report.metrics.human_labelled_case_count == 0
    assert bundle.report.metrics.replay_match_rate == 1.0
    assert bundle.review.decision is PromotionDecision.INSUFFICIENT_EVIDENCE
    assert bundle.review.live_integration_authorized is False
    assert bundle.review.operator_go_required is True
    assert bundle.review.insufficient_evidence_codes == (
        "human_labelled_case_count_below_minimum",
        "real_case_count_below_minimum",
    )


def test_runner_requires_exact_manifest_coverage() -> None:
    manifest, benchmark_input, thresholds, _ = _bundle()
    incomplete = ReaderBenchmarkInput(
        environment=benchmark_input.environment,
        observations=benchmark_input.observations[:-1],
    )

    with pytest.raises(ReaderBenchmarkError, match="exactly cover"):
        ReaderBenchmarkRunner().run(manifest, incomplete, thresholds)


def test_replay_order_mismatch_becomes_no_go_when_evidence_counts_are_met() -> None:
    manifest, benchmark_input, thresholds, _ = _bundle()
    original = benchmark_input.observations[0]
    reordered = replace(
        original,
        observation_id="",
        second_artifact_ids=tuple(reversed(original.second_artifact_ids)),
    )
    changed_input = ReaderBenchmarkInput(
        environment=benchmark_input.environment,
        observations=(reordered, *benchmark_input.observations[1:]),
    )
    synthetic_thresholds = replace(
        thresholds,
        thresholds_id="",
        min_real_cases=0,
        min_human_labelled_cases=0,
    )

    bundle = ReaderBenchmarkRunner().run(
        manifest,
        changed_input,
        synthetic_thresholds,
    )

    assert bundle.report.metrics.replay_match_rate == 0.75
    assert bundle.review.decision is PromotionDecision.NO_GO
    assert bundle.review.failed_gate_codes == (
        "replay_match_rate_below_threshold",
    )


def test_hmac_signature_verifies_and_never_authorizes_live_integration() -> None:
    _, _, _, bundle = _bundle()
    secret = b"rdr10-test-secret-material-32-bytes-minimum"
    signature = ReaderBenchmarkSigner.sign(
        bundle,
        key_id="fixture-key-v1",
        secret=secret,
    )

    assert ReaderBenchmarkSigner.verify(bundle, signature, secret=secret)
    assert not ReaderBenchmarkSigner.verify(
        bundle,
        signature,
        secret=b"wrong-secret-material-32-bytes-minimum!",
    )
    assert bundle.review.live_integration_authorized is False
    with pytest.raises(ReaderBenchmarkError, match="signature_id"):
        replace(signature, signature_hex="0" * 64)


def test_canonical_writer_round_trips_without_nondeterministic_whitespace(
    tmp_path: Path,
) -> None:
    _, _, _, bundle = _bundle()
    output = tmp_path / "nested" / "bundle.json"
    write_canonical_json(output, bundle)

    raw = output.read_bytes()
    assert raw == canonical_json_bytes(bundle) + b"\n"
    payload = json.loads(raw)
    assert payload["bundle_id"] == bundle.bundle_id
    assert payload["review"]["decision"] == "insufficient_evidence"


def test_duplicate_json_keys_are_rejected(tmp_path: Path) -> None:
    duplicate = tmp_path / "duplicate.json"
    duplicate.write_text(
        '{"schema_version":"reader-core.benchmark-input.v1",'
        '"schema_version":"forged","environment":{},"observations":[]}',
        encoding="utf-8",
    )

    with pytest.raises(ReaderBenchmarkError, match="duplicate JSON key"):
        load_benchmark_input(duplicate)


def test_cli_writes_bundle_and_detached_signature(tmp_path: Path) -> None:
    output = tmp_path / "bundle.json"
    signature = tmp_path / "bundle.signature.json"
    env = {
        "PATH": str(Path(sys.executable).parent),
        "PYTHONPATH": str(REPO_ROOT),
        "RDR10_TEST_HMAC_KEY": "fixture-secret-material-that-is-long-enough",
    }
    proc = subprocess.run(
        [
            sys.executable,
            str(CLI_PATH),
            "--manifest",
            str(MANIFEST_PATH),
            "--input",
            str(INPUT_PATH),
            "--thresholds",
            str(THRESHOLDS_PATH),
            "--output",
            str(output),
            "--signature-output",
            str(signature),
            "--hmac-key-env",
            "RDR10_TEST_HMAC_KEY",
            "--key-id",
            "fixture-cli-key",
            "--require-eligible",
        ],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 3
    assert output.is_file()
    assert signature.is_file()
    summary = json.loads(proc.stdout)
    assert summary["decision"] == "insufficient_evidence"
    assert summary["signature_written"] is True
    assert "fixture-secret-material" not in output.read_text(encoding="utf-8")
    assert "fixture-secret-material" not in signature.read_text(encoding="utf-8")
