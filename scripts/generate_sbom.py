#!/usr/bin/env python3
"""Generate a deterministic CycloneDX SBOM from Titan's authoritative uv.lock."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import tomllib
import uuid
from pathlib import Path
from typing import Any
from urllib.parse import quote

BOM_FORMAT = "CycloneDX"
SPEC_VERSION = "1.6"
SCOPE = "uv-lock-universe"
NAMESPACE_UUID = uuid.UUID("6530f2d3-0a74-5e9d-8df5-6f8afcf5043a")


def _normalize_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_identity(source: dict[str, Any]) -> tuple[str, str]:
    for key in ("registry", "editable", "git", "url", "path", "virtual"):
        if key in source:
            return key, str(source[key])
    raise ValueError(f"unsupported uv source metadata: {source!r}")


def _entry_ref(raw: dict[str, Any], name: str, version: str) -> str:
    canonical = json.dumps(raw, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    fingerprint = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:20]
    return (
        "urn:velantrim:uv:"
        f"{quote(_normalize_name(name), safe='')}:{quote(version, safe='')}:{fingerprint}"
    )


def _artifact_hash_properties(raw: dict[str, Any]) -> list[dict[str, str]]:
    values: list[tuple[str, str]] = []
    sdist = raw.get("sdist")
    if isinstance(sdist, dict) and isinstance(sdist.get("hash"), str):
        values.append(("velantrim:uv-sdist-hash", sdist["hash"]))

    wheels = raw.get("wheels", [])
    if isinstance(wheels, list):
        for wheel in wheels:
            if isinstance(wheel, dict) and isinstance(wheel.get("hash"), str):
                values.append(("velantrim:uv-wheel-hash", wheel["hash"]))

    return [
        {"name": name, "value": value}
        for name, value in sorted(set(values))
    ]


def generate_sbom_document(lock_path: Path, project_path: Path) -> dict[str, Any]:
    lock = tomllib.loads(lock_path.read_text(encoding="utf-8"))
    project = tomllib.loads(project_path.read_text(encoding="utf-8"))
    lock_digest = _sha256(lock_path)
    project_digest = _sha256(project_path)

    project_meta = project.get("project")
    if not isinstance(project_meta, dict):
        raise ValueError("pyproject.toml is missing [project]")
    project_name = project_meta.get("name")
    project_version = project_meta.get("version")
    if not isinstance(project_name, str) or not isinstance(project_version, str):
        raise ValueError("[project] must define string name and version")

    raw_packages = lock.get("package")
    if not isinstance(raw_packages, list) or not raw_packages:
        raise ValueError("uv.lock contains no [[package]] entries")

    components: list[dict[str, Any]] = []
    refs: set[str] = set()
    for raw in raw_packages:
        if not isinstance(raw, dict):
            raise ValueError("uv.lock package entry must be a table")
        name = raw.get("name")
        version = raw.get("version")
        source = raw.get("source", {})
        if not isinstance(name, str) or not isinstance(version, str):
            raise ValueError("every uv.lock package must have string name and version")
        if not isinstance(source, dict):
            raise ValueError(f"package {name!r} has invalid source metadata")

        source_kind, source_value = _source_identity(source)
        if (
            _normalize_name(name) == _normalize_name(project_name)
            and version == project_version
            and source_kind in {"editable", "path", "virtual"}
        ):
            continue

        ref = _entry_ref(raw, name, version)
        if ref in refs:
            raise ValueError(f"duplicate deterministic bom-ref: {ref}")
        refs.add(ref)

        properties = [
            {"name": "velantrim:uv-source-kind", "value": source_kind},
            {"name": "velantrim:uv-source", "value": source_value},
            *_artifact_hash_properties(raw),
        ]
        component: dict[str, Any] = {
            "type": "library",
            "bom-ref": ref,
            "name": name,
            "version": version,
            "properties": properties,
        }
        if source_kind == "registry" and "pypi.org" in source_value:
            component["purl"] = (
                f"pkg:pypi/{quote(_normalize_name(name), safe='')}"
                f"@{quote(version, safe='')}"
            )
        components.append(component)

    components.sort(
        key=lambda component: (
            _normalize_name(str(component["name"])),
            str(component["version"]),
            str(component["bom-ref"]),
        )
    )

    serial_seed = f"{lock_digest}\0{project_digest}"
    serial = uuid.uuid5(NAMESPACE_UUID, serial_seed)
    root_ref = (
        "urn:velantrim:project:"
        f"{quote(_normalize_name(project_name), safe='')}:{quote(project_version, safe='')}"
    )
    return {
        "bomFormat": BOM_FORMAT,
        "specVersion": SPEC_VERSION,
        "serialNumber": f"urn:uuid:{serial}",
        "version": 1,
        "metadata": {
            "component": {
                "type": "application",
                "bom-ref": root_ref,
                "name": project_name,
                "version": project_version,
            },
            "properties": [
                {"name": "velantrim:sbom-scope", "value": SCOPE},
                {"name": "velantrim:uv-lock-sha256", "value": lock_digest},
                {"name": "velantrim:pyproject-sha256", "value": project_digest},
                {"name": "velantrim:generator", "value": "scripts/generate_sbom.py"},
                {"name": "velantrim:reproducible", "value": "true"},
            ],
        },
        "components": components,
    }


def write_sbom(lock_path: Path, project_path: Path, output_path: Path) -> None:
    document = generate_sbom_document(lock_path, project_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(document, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lock", type=Path, default=Path("uv.lock"))
    parser.add_argument("--project", type=Path, default=Path("pyproject.toml"))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/titan-uv-lock.cdx.json"),
    )
    args = parser.parse_args()

    try:
        write_sbom(args.lock, args.project, args.output)
    except (OSError, ValueError, tomllib.TOMLDecodeError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
