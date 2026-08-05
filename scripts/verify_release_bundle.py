#!/usr/bin/env python3
"""Verify a Velantrim Titan production database bundle after extraction."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any

REQUIRED_PRODUCTION_PATHS = {
    "data/velantrim_kb_clean_20260710_graph.db",
    "data/exocortex_graph.db",
    "data/exocortex.lbug",
    "data/ngram_house.db",
    "kb_graph.json",
}


class BundleVerificationError(ValueError):
    """Raised when the manifest itself is malformed or unsafe."""


def _safe_relative_path(raw: Any) -> str:
    if not isinstance(raw, str) or not raw.strip():
        raise BundleVerificationError("manifest path must be a non-empty string")
    value = raw.replace("\\", "/")
    candidate = PurePosixPath(value)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise BundleVerificationError(f"unsafe manifest path: {raw!r}")
    normalized = candidate.as_posix()
    if normalized in {"", "."}:
        raise BundleVerificationError(f"unsafe manifest path: {raw!r}")
    return normalized


def _load_manifest(root: Path) -> tuple[list[dict[str, Any]], str]:
    path = root / "MANIFEST.json"
    if not path.is_file():
        raise BundleVerificationError("MANIFEST.json is missing")

    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BundleVerificationError(f"cannot read MANIFEST.json: {exc}") from exc

    if isinstance(data, list):
        entries = data
        schema = "legacy-list"
    elif isinstance(data, dict):
        if data.get("schema_version") != 1:
            raise BundleVerificationError("unsupported or missing manifest schema_version")
        if data.get("product") != "velantrim-titan":
            raise BundleVerificationError("manifest product must be 'velantrim-titan'")
        entries = data.get("files")
        schema = "v1"
    else:
        raise BundleVerificationError("manifest root must be an object or legacy list")

    if not isinstance(entries, list) or not entries:
        raise BundleVerificationError("manifest files must be a non-empty list")
    if not all(isinstance(item, dict) for item in entries):
        raise BundleVerificationError("every manifest file entry must be an object")
    return entries, schema


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_bundle(root: Path, *, require_production_set: bool = True) -> dict[str, Any]:
    """Verify manifest safety, file sizes and SHA-256 digests.

    Returns a structured report. Manifest-shape errors are reported as normal
    failures so CLI consumers receive a stable non-zero exit code rather than a
    traceback.
    """

    root = root.resolve()
    errors: list[str] = []
    verified = 0
    verified_bytes = 0

    try:
        entries, schema = _load_manifest(root)
    except BundleVerificationError as exc:
        return {
            "ok": False,
            "schema": None,
            "files_verified": 0,
            "bytes_verified": 0,
            "errors": [str(exc)],
        }

    seen: set[str] = set()
    manifest_paths: set[str] = set()

    for entry in entries:
        try:
            rel = _safe_relative_path(entry.get("path"))
        except BundleVerificationError as exc:
            errors.append(str(exc))
            continue

        if rel in seen:
            errors.append(f"duplicate manifest path: {rel}")
            continue
        seen.add(rel)
        manifest_paths.add(rel)

        expected_size = entry.get("bytes")
        expected_hash = entry.get("sha256")
        if not isinstance(expected_size, int) or expected_size < 0:
            errors.append(f"{rel}: bytes must be a non-negative integer")
            continue
        if (
            not isinstance(expected_hash, str)
            or len(expected_hash) != 64
            or any(ch not in "0123456789abcdefABCDEF" for ch in expected_hash)
        ):
            errors.append(f"{rel}: sha256 must be a 64-character hex string")
            continue

        candidate = (root / rel).resolve()
        try:
            candidate.relative_to(root)
        except ValueError:
            errors.append(f"{rel}: resolved path escapes bundle root")
            continue

        if not candidate.is_file():
            errors.append(f"{rel}: file is missing")
            continue
        actual_size = candidate.stat().st_size
        if actual_size != expected_size:
            errors.append(f"{rel}: size mismatch (expected {expected_size}, got {actual_size})")
            continue
        actual_hash = _sha256(candidate)
        if actual_hash.lower() != expected_hash.lower():
            errors.append(f"{rel}: sha256 mismatch")
            continue

        verified += 1
        verified_bytes += actual_size

    if require_production_set:
        for missing in sorted(REQUIRED_PRODUCTION_PATHS - manifest_paths):
            errors.append(f"required production asset missing from manifest: {missing}")

    return {
        "ok": not errors,
        "schema": schema,
        "files_verified": verified,
        "bytes_verified": verified_bytes,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify MANIFEST.json, file sizes and SHA-256 digests in an extracted bundle."
    )
    parser.add_argument("root", nargs="?", default=".", help="extracted bundle root")
    parser.add_argument(
        "--allow-partial",
        action="store_true",
        help="verify listed files without requiring the full production asset set",
    )
    parser.add_argument("--json", action="store_true", help="emit the report as JSON")
    args = parser.parse_args()

    report = verify_bundle(
        Path(args.root),
        require_production_set=not args.allow_partial,
    )
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif report["ok"]:
        mib = report["bytes_verified"] / (1024 * 1024)
        print(
            f"OK: verified {report['files_verified']} files "
            f"({mib:.1f} MiB), manifest schema={report['schema']}"
        )
    else:
        print("FAILED: production bundle verification errors:")
        for error in report["errors"]:
            print(f"  - {error}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
