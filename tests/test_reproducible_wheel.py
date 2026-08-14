from __future__ import annotations

import tomllib
from pathlib import Path

from scripts.verify_reproducible_wheel import generate_build_constraints


ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"
CI_WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"


def test_build_backend_has_one_explicit_owner_without_redundant_wheel_dependency() -> None:
    with PYPROJECT.open("rb") as handle:
        payload = tomllib.load(handle)

    assert payload["build-system"] == {
        "requires": ["setuptools>=83"],
        "build-backend": "setuptools.build_meta",
    }


def test_build_constraints_are_derived_from_authoritative_uv_lock(tmp_path: Path) -> None:
    constraints = tmp_path / "constraints.txt"
    versions = generate_build_constraints(constraints)
    text = constraints.read_text(encoding="utf-8")

    assert versions == {"setuptools": "84.0.0"}
    assert text.startswith("setuptools==84.0.0 ")
    assert "--hash=sha256:51a52592b3b99e102b609654876bd65f19f999935166d1352678931132b0c670" in text
    assert "--hash=sha256:f4695c21257f0d9b537ec2692c941d02ee143b7cc1276941349a546573b2ef73" in text


def test_ci_enforces_two_build_byte_identity_and_keeps_evidence() -> None:
    text = CI_WORKFLOW.read_text(encoding="utf-8")

    assert "reproducible-wheel:" in text
    assert "name: Reproducible Titan wheel" in text
    assert "version: 0.12.3" in text
    assert "python scripts/verify_reproducible_wheel.py" in text
    assert "--source-head-sha \"${SOURCE_HEAD_SHA}\"" in text
    assert "name: titan-reproducible-wheel" in text
    assert "artifacts/reproducible-wheel" in text


def test_reproducibility_claim_is_wheel_scoped_not_oci_digest() -> None:
    verifier = (ROOT / "scripts" / "verify_reproducible_wheel.py").read_text(encoding="utf-8")

    assert '"claim_scope": "python-wheel-distribution"' in verifier
    assert "Docker/OCI image manifests" in verifier
    assert "byte-for-byte reproducible" in verifier
