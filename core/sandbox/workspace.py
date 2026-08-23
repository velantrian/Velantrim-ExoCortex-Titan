"""Digest-addressed workspace manifest contracts for Titan Sandbox.

This module defines which files may be materialized into a future sandbox. It
never reads host paths, follows symlinks, opens files, mounts directories, or
starts processes.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import PurePosixPath


WORKSPACE_MANIFEST_SCHEMA_VERSION = "titan.sandbox-workspace-manifest.v0.1"
DEFAULT_MAX_WORKSPACE_FILES = 4096
DEFAULT_MAX_WORKSPACE_BYTES = 256 * 1024 * 1024


class WorkspaceManifestError(ValueError):
    """Raised when workspace materialization metadata is unsafe or ambiguous."""


def _validate_digest(value: str, field_name: str) -> str:
    digest = (value or "").strip().lower()
    if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
        raise WorkspaceManifestError(f"{field_name} must be a 64-character sha256 hex digest")
    return digest


def _normalize_relative_path(value: str) -> str:
    raw = (value or "").strip().replace("\\", "/")
    if not raw:
        raise WorkspaceManifestError("workspace path must be non-empty")
    if raw.startswith("/") or (len(raw) >= 2 and raw[0].isalpha() and raw[1] == ":"):
        raise WorkspaceManifestError("workspace path must be relative")
    parts = raw.split("/")
    if any(part in ("", ".", "..") for part in parts):
        raise WorkspaceManifestError("workspace path cannot contain traversal components")
    return str(PurePosixPath(*parts))


@dataclass(frozen=True, slots=True)
class WorkspaceFile:
    """One immutable input blob and its sandbox-relative destination path."""

    path: str
    sha256: str
    size_bytes: int
    executable: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", _normalize_relative_path(self.path))
        object.__setattr__(self, "sha256", _validate_digest(self.sha256, "sha256"))
        if isinstance(self.size_bytes, bool) or not isinstance(self.size_bytes, int):
            raise WorkspaceManifestError("size_bytes must be an integer")
        if self.size_bytes < 0:
            raise WorkspaceManifestError("size_bytes must be non-negative")
        if not isinstance(self.executable, bool):
            raise WorkspaceManifestError("executable must be a boolean")


@dataclass(frozen=True, slots=True)
class WorkspaceManifest:
    """Deterministic, bounded description of sandbox input materialization.

    The manifest references content by digest rather than host path. A future
    materializer must resolve each blob from an admitted content source, verify
    digest/size before exposing it to a workload, and must not fall back to host
    bind mounts when a blob cannot be resolved.
    """

    files: tuple[WorkspaceFile, ...]
    max_files: int = DEFAULT_MAX_WORKSPACE_FILES
    max_total_bytes: int = DEFAULT_MAX_WORKSPACE_BYTES
    schema_version: str = WORKSPACE_MANIFEST_SCHEMA_VERSION
    manifest_id: str = ""

    def __post_init__(self) -> None:
        if self.schema_version != WORKSPACE_MANIFEST_SCHEMA_VERSION:
            raise WorkspaceManifestError("unsupported workspace manifest schema")
        for name in ("max_files", "max_total_bytes"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise WorkspaceManifestError(f"{name} must be a positive integer")

        files = tuple(sorted(tuple(self.files), key=lambda item: item.path))
        if len(files) > self.max_files:
            raise WorkspaceManifestError("workspace file count exceeds max_files")
        seen_paths: set[str] = set()
        total_bytes = 0
        for item in files:
            if item.path in seen_paths:
                raise WorkspaceManifestError("workspace paths must be unique")
            seen_paths.add(item.path)
            total_bytes += item.size_bytes
            if total_bytes > self.max_total_bytes:
                raise WorkspaceManifestError("workspace bytes exceed max_total_bytes")
        object.__setattr__(self, "files", files)

        payload = {
            "schema_version": self.schema_version,
            "max_files": self.max_files,
            "max_total_bytes": self.max_total_bytes,
            "files": [
                {
                    "path": item.path,
                    "sha256": item.sha256,
                    "size_bytes": item.size_bytes,
                    "executable": item.executable,
                }
                for item in files
            ],
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        expected = "workspace-manifest:" + hashlib.sha256(encoded).hexdigest()
        if self.manifest_id and self.manifest_id != expected:
            raise WorkspaceManifestError("manifest_id does not match workspace manifest content")
        object.__setattr__(self, "manifest_id", expected)


__all__ = [
    "DEFAULT_MAX_WORKSPACE_BYTES",
    "DEFAULT_MAX_WORKSPACE_FILES",
    "WORKSPACE_MANIFEST_SCHEMA_VERSION",
    "WorkspaceFile",
    "WorkspaceManifest",
    "WorkspaceManifestError",
]
