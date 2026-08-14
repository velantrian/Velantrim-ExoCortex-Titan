#!/usr/bin/env python3
"""Verify that Titan's wheel build is byte-for-byte reproducible.

The verifier binds the PEP 517 build backend to the version and hashes already
recorded in ``uv.lock``, derives ``SOURCE_DATE_EPOCH`` from the exact source
commit, performs two clean wheel builds, and fails unless their bytes match.

This is intentionally a wheel-distribution reproducibility proof. It does not
claim that Docker/OCI image manifests, layer timestamps, external apt mirrors,
or arbitrary host environments are byte-for-byte reproducible.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import time
import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"
UV_LOCK = ROOT / "uv.lock"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _run(*args: str, env: dict[str, str] | None = None) -> str:
    completed = subprocess.run(
        args,
        cwd=ROOT,
        env=env,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    return completed.stdout.strip()


def _build_backend_requirements() -> list[str]:
    with PYPROJECT.open("rb") as handle:
        payload = tomllib.load(handle)
    build_system = payload.get("build-system")
    if not isinstance(build_system, dict):
        raise RuntimeError("pyproject.toml has no [build-system] table")
    requirements = build_system.get("requires")
    if not isinstance(requirements, list) or not requirements:
        raise RuntimeError("[build-system].requires must be a non-empty list")
    if requirements != ["setuptools>=83"]:
        raise RuntimeError(
            "C8 currently admits exactly one build backend requirement: setuptools>=83; "
            f"found {requirements!r}. Update the reproducibility contract deliberately."
        )
    return ["setuptools"]


def _locked_package(name: str) -> dict[str, Any]:
    with UV_LOCK.open("rb") as handle:
        lock = tomllib.load(handle)
    matches = [
        package
        for package in lock.get("package", [])
        if isinstance(package, dict) and package.get("name") == name
    ]
    if len(matches) != 1:
        raise RuntimeError(f"expected exactly one uv.lock package named {name!r}, found {len(matches)}")
    return matches[0]


def _locked_hashes(package: dict[str, Any]) -> list[str]:
    hashes: set[str] = set()
    sdist = package.get("sdist")
    if isinstance(sdist, dict) and isinstance(sdist.get("hash"), str):
        hashes.add(sdist["hash"])
    wheels = package.get("wheels", [])
    if isinstance(wheels, list):
        for wheel in wheels:
            if isinstance(wheel, dict) and isinstance(wheel.get("hash"), str):
                hashes.add(wheel["hash"])
    if not hashes:
        raise RuntimeError(f"locked build package {package.get('name')!r} has no artifact hashes")
    if any(not item.startswith("sha256:") for item in hashes):
        raise RuntimeError("build constraints currently require sha256 hashes only")
    return sorted(hashes)


def generate_build_constraints(path: Path) -> dict[str, str]:
    """Write hash-enforced uv build constraints from the authoritative lock."""

    versions: dict[str, str] = {}
    lines: list[str] = []
    for name in _build_backend_requirements():
        package = _locked_package(name)
        version = package.get("version")
        if not isinstance(version, str) or not version:
            raise RuntimeError(f"locked build package {name!r} has no version")
        versions[name] = version
        hashes = _locked_hashes(package)
        suffix = " ".join(f"--hash={item}" for item in hashes)
        lines.append(f"{name}=={version} {suffix}")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return versions


def _clean_local_build_state() -> None:
    for path in (ROOT / "build", ROOT / "dist"):
        if path.exists():
            shutil.rmtree(path)
    for pattern in ("*.egg-info", ".eggs"):
        for path in ROOT.glob(pattern):
            if path.is_dir():
                shutil.rmtree(path)
            elif path.exists():
                path.unlink()


def _build_once(output_dir: Path, constraints: Path, env: dict[str, str]) -> Path:
    _clean_local_build_state()
    output_dir.mkdir(parents=True, exist_ok=True)
    _run(
        "uv",
        "build",
        "--wheel",
        "--out-dir",
        str(output_dir),
        "--build-constraint",
        str(constraints),
        "--require-hashes",
        env=env,
    )
    wheels = sorted(output_dir.glob("*.whl"))
    if len(wheels) != 1:
        raise RuntimeError(f"expected exactly one wheel in {output_dir}, found {len(wheels)}")
    return wheels[0]


def verify(*, artifact_dir: Path, source_head_sha: str | None = None) -> dict[str, Any]:
    artifact_dir = artifact_dir.resolve()
    artifact_dir.mkdir(parents=True, exist_ok=True)

    actual_head = _run("git", "rev-parse", "HEAD")
    expected_head = source_head_sha or actual_head
    if actual_head != expected_head:
        raise RuntimeError(
            "working tree is not checked out at the requested exact source head: "
            f"HEAD={actual_head}, requested={expected_head}"
        )

    source_date_epoch = _run("git", "show", "-s", "--format=%ct", expected_head)
    if not source_date_epoch.isdigit():
        raise RuntimeError(f"invalid git commit timestamp: {source_date_epoch!r}")

    constraints = artifact_dir / "titan-build-constraints.txt"
    backend_versions = generate_build_constraints(constraints)

    env = os.environ.copy()
    env["SOURCE_DATE_EPOCH"] = source_date_epoch
    env["PYTHONDONTWRITEBYTECODE"] = "1"

    with tempfile.TemporaryDirectory(prefix="titan-repro-wheel-") as temp:
        temp_root = Path(temp)
        first = _build_once(temp_root / "first", constraints, env)
        # Ensure wall-clock timestamps would differ if the backend ignored
        # SOURCE_DATE_EPOCH. This makes the test adversarial rather than two
        # near-simultaneous builds that could accidentally share ZIP seconds.
        time.sleep(2.0)
        second = _build_once(temp_root / "second", constraints, env)

        first_hash = _sha256(first)
        second_hash = _sha256(second)
        first_bytes = first.read_bytes()
        second_bytes = second.read_bytes()
        if first.name != second.name:
            raise RuntimeError(f"wheel filenames differ: {first.name!r} != {second.name!r}")
        if first_hash != second_hash or first_bytes != second_bytes:
            raise RuntimeError(
                "wheel builds are not byte-for-byte reproducible: "
                f"first={first_hash}, second={second_hash}"
            )

        retained_wheel = artifact_dir / first.name
        retained_wheel.write_bytes(first_bytes)

    constraints_hash = _sha256(constraints)
    wheel_hash = _sha256(retained_wheel)
    metadata: dict[str, Any] = {
        "schema": "titan-reproducible-wheel-evidence-v1",
        "source_head_sha": expected_head,
        "source_date_epoch": int(source_date_epoch),
        "uv_version": _run("uv", "--version"),
        "build_backend": "setuptools.build_meta",
        "build_backend_versions": backend_versions,
        "constraints_sha256": constraints_hash,
        "wheel_filename": retained_wheel.name,
        "wheel_sha256": wheel_hash,
        "wheel_size_bytes": retained_wheel.stat().st_size,
        "build_count": 2,
        "byte_identical": True,
        "claim_scope": "python-wheel-distribution",
    }

    metadata_path = artifact_dir / "titan-reproducible-wheel.metadata.json"
    metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (artifact_dir / "titan-reproducible-wheel.sha256").write_text(
        f"{wheel_hash}  {retained_wheel.name}\n",
        encoding="utf-8",
    )
    return metadata


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--artifact-dir",
        type=Path,
        default=Path("artifacts/reproducible-wheel"),
        help="directory for retained wheel and reproducibility evidence",
    )
    parser.add_argument(
        "--source-head-sha",
        default=None,
        help="exact checked-out source SHA; fails if it differs from git HEAD",
    )
    args = parser.parse_args()

    metadata = verify(
        artifact_dir=args.artifact_dir,
        source_head_sha=args.source_head_sha,
    )
    print(json.dumps(metadata, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
