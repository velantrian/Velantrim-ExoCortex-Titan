import json
from pathlib import Path
import subprocess
import sys


def test_synthetic_smoke_writes_non_authoritative_bundle(tmp_path: Path) -> None:
    output = tmp_path / "reader-synthetic-smoke.json"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_reader_synthetic_smoke.py",
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    summary = json.loads(result.stdout)
    assert summary["decision"] == "insufficient_evidence"
    assert summary["synthetic_case_count"] == 4
    assert summary["real_case_count"] == 0
    assert summary["human_labelled_case_count"] == 0
    assert summary["operator_go_required"] is True
    assert summary["live_integration_authorized"] is False

    bundle = json.loads(output.read_text(encoding="utf-8"))
    assert bundle["review"]["decision"] == "insufficient_evidence"
    assert bundle["review"]["operator_go_required"] is True
    assert bundle["review"]["live_integration_authorized"] is False


def test_synthetic_smoke_fails_closed_for_missing_input(tmp_path: Path) -> None:
    output = tmp_path / "missing-input.json"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_reader_synthetic_smoke.py",
            "--output",
            str(output),
            "--input",
            str(tmp_path / "does-not-exist.json"),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert "reader synthetic smoke error" in result.stderr
    assert not output.exists()
