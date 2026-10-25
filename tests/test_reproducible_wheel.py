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

    assert versions == {"setuptools": "84.1.0"}
    assert text.startswith("setuptools==84.1.0 ")
    assert "--hash=sha256:5231689c6ac8156cd155cfb98c3fd6fb252c3e7e9bd3d78b64d3c55f132624c9" in text
    assert "--hash=sha256:23657205b63d4d31395ab917815247f694aafad28cd21316bf5fd45a51048ea0" in text


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
