"""Tests for scripts.verify_release_bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scripts.verify_release_bundle import REQUIRED_PRODUCTION_PATHS, verify_bundle


def _write_manifest(root: Path, paths: set[str]) -> None:
    entries = []
    for rel in sorted(paths):
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = f"payload:{rel}".encode()
        path.write_bytes(payload)
        entries.append(
            {
                "path": rel,
                "bytes": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        )
    manifest = {
        "schema_version": 1,
        "product": "velantrim-titan",
        "version": "9.0.0",
        "generated_at": "2026-07-12T00:00:00Z",
        "files": entries,
    }
    (root / "MANIFEST.json").write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )


def test_verify_complete_production_bundle(tmp_path: Path) -> None:
    _write_manifest(tmp_path, REQUIRED_PRODUCTION_PATHS)

    report = verify_bundle(tmp_path)

    assert report["ok"] is True
    assert report["schema"] == "v1"
    assert report["files_verified"] == len(REQUIRED_PRODUCTION_PATHS)
    assert report["errors"] == []


def test_verify_detects_tampered_file(tmp_path: Path) -> None:
    _write_manifest(tmp_path, REQUIRED_PRODUCTION_PATHS)
    target = tmp_path / "kb_graph.json"
    target.write_bytes(target.read_bytes() + b"tampered")

    report = verify_bundle(tmp_path)

    assert report["ok"] is False
    assert any("kb_graph.json: size mismatch" in error for error in report["errors"])


def test_verify_rejects_path_traversal(tmp_path: Path) -> None:
    manifest = {
        "schema_version": 1,
        "product": "velantrim-titan",
        "files": [
            {
                "path": "../outside.db",
                "bytes": 0,
                "sha256": "0" * 64,
            }
        ],
    }
    (tmp_path / "MANIFEST.json").write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )

    report = verify_bundle(tmp_path, require_production_set=False)

    assert report["ok"] is False
    assert report["errors"] == ["unsafe manifest path: '../outside.db'"]


def test_allow_partial_skips_required_asset_check(tmp_path: Path) -> None:
    _write_manifest(tmp_path, {"kb_graph.json"})

    strict = verify_bundle(tmp_path)
    partial = verify_bundle(tmp_path, require_production_set=False)

    assert strict["ok"] is False
    assert any("required production asset missing" in error for error in strict["errors"])
    assert partial["ok"] is True


def test_legacy_list_manifest_remains_verifiable(tmp_path: Path) -> None:
    payload = b"legacy"
    path = tmp_path / "kb_graph.json"
    path.write_bytes(payload)
    (tmp_path / "MANIFEST.json").write_text(
        json.dumps(
            [
                {
                    "path": "kb_graph.json",
                    "bytes": len(payload),
                    "sha256": hashlib.sha256(payload).hexdigest(),
                }
            ]
        ),
        encoding="utf-8",
    )

    report = verify_bundle(tmp_path, require_production_set=False)

    assert report["ok"] is True
    assert report["schema"] == "legacy-list"
