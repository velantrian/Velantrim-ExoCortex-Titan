"""Backend-owned ephemeral filesystem materialization for Titan Sandbox.

This module writes only already-verified workspace blobs into a newly-created,
private temporary directory. Callers cannot supply a host root. It does not
mount the directory, start processes, access container runtimes, open networks,
or inject secrets.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import os
from pathlib import Path, PurePosixPath
import shutil
import tempfile

from .materializer import VerifiedWorkspace


_WORKSPACE_PREFIX = "velantrim-sandbox-"


class EphemeralWorkspaceError(RuntimeError):
    """Raised when secure workspace materialization or cleanup fails."""


@dataclass(slots=True)
class EphemeralWorkspace:
    """One backend-owned temporary workspace with explicit verified cleanup."""

    root: Path
    manifest_id: str
    _closed: bool = field(default=False, init=False, repr=False)

    @property
    def closed(self) -> bool:
        return self._closed

    def close(self) -> None:
        """Remove the complete workspace and verify that it is gone."""
        if self._closed:
            return
        try:
            shutil.rmtree(self.root)
        except FileNotFoundError:
            pass
        except OSError as exc:
            raise EphemeralWorkspaceError("failed to remove ephemeral workspace") from exc
        if self.root.exists():
            raise EphemeralWorkspaceError("ephemeral workspace remains after cleanup")
        self._closed = True

    def __enter__(self) -> EphemeralWorkspace:
        if self._closed:
            raise EphemeralWorkspaceError("ephemeral workspace is already closed")
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()


class EphemeralWorkspaceWriter:
    """Write a VerifiedWorkspace into private OS-managed temporary storage."""

    def materialize(self, verified: VerifiedWorkspace) -> EphemeralWorkspace:
        root = Path(tempfile.mkdtemp(prefix=_WORKSPACE_PREFIX))
        workspace = EphemeralWorkspace(root=root, manifest_id=verified.manifest_id)
        try:
            self._harden_root(root)
            for blob in verified.files:
                destination = root.joinpath(*PurePosixPath(blob.file.path).parts)
                self._write_blob(root, destination, blob.payload, blob.file.executable)
            self._verify_materialization(workspace, verified)
        except Exception:
            try:
                workspace.close()
            except EphemeralWorkspaceError:
                pass
            raise
        return workspace

    @staticmethod
    def _harden_root(root: Path) -> None:
        try:
            root.chmod(0o700)
        except OSError as exc:
            raise EphemeralWorkspaceError("failed to harden ephemeral workspace root") from exc

    @staticmethod
    def _write_blob(root: Path, destination: Path, payload: bytes, executable: bool) -> None:
        try:
            destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            resolved_root = root.resolve(strict=True)
            resolved_parent = destination.parent.resolve(strict=True)
            if not resolved_parent.is_relative_to(resolved_root):
                raise EphemeralWorkspaceError("workspace destination escaped ephemeral root")
            with destination.open("xb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            destination.chmod(0o700 if executable else 0o600)
        except EphemeralWorkspaceError:
            raise
        except OSError as exc:
            raise EphemeralWorkspaceError("failed to write ephemeral workspace blob") from exc

    @staticmethod
    def _verify_materialization(
        workspace: EphemeralWorkspace,
        verified: VerifiedWorkspace,
    ) -> None:
        for blob in verified.files:
            destination = workspace.root.joinpath(*PurePosixPath(blob.file.path).parts)
            try:
                payload = destination.read_bytes()
            except OSError as exc:
                raise EphemeralWorkspaceError(
                    "failed to verify ephemeral workspace blob"
                ) from exc
            if len(payload) != blob.file.size_bytes:
                raise EphemeralWorkspaceError("materialized workspace size mismatch")
            if hashlib.sha256(payload).hexdigest() != blob.file.sha256:
                raise EphemeralWorkspaceError("materialized workspace digest mismatch")


__all__ = [
    "EphemeralWorkspace",
    "EphemeralWorkspaceError",
    "EphemeralWorkspaceWriter",
]
