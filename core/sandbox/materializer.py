"""Pure content-resolution contract for Titan Sandbox workspaces.

This layer resolves digest-addressed blobs and verifies their bytes against a
WorkspaceManifest. It does not read host paths, write files, follow symlinks,
mount directories, start processes, access container runtimes, or open networks.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Protocol, runtime_checkable

from .workspace import WorkspaceFile, WorkspaceManifest


class BlobResolutionError(RuntimeError):
    """Raised by a resolver when an admitted digest cannot be resolved."""


class WorkspaceMaterializationError(RuntimeError):
    """Raised when resolved content does not exactly match the manifest."""


@runtime_checkable
class BlobResolver(Protocol):
    """Resolve immutable content by digest only.

    Implementations must not interpret a workspace path as a source path. A
    resolver that cannot provide the exact digest must fail closed with
    BlobResolutionError rather than falling back to arbitrary host content.
    """

    def resolve(self, sha256: str) -> bytes:
        """Return immutable bytes for one sha256 digest."""
        ...


@dataclass(frozen=True, slots=True)
class VerifiedWorkspaceBlob:
    """One manifest file whose resolved bytes have been verified exactly."""

    file: WorkspaceFile
    payload: bytes

    def __post_init__(self) -> None:
        if not isinstance(self.payload, bytes):
            raise WorkspaceMaterializationError("resolved payload must be immutable bytes")
        if len(self.payload) != self.file.size_bytes:
            raise WorkspaceMaterializationError(
                f"resolved size mismatch for {self.file.path}"
            )
        digest = hashlib.sha256(self.payload).hexdigest()
        if digest != self.file.sha256:
            raise WorkspaceMaterializationError(
                f"resolved digest mismatch for {self.file.path}"
            )


@dataclass(frozen=True, slots=True)
class VerifiedWorkspace:
    """Fully verified in-memory inputs bound to one exact manifest."""

    manifest: WorkspaceManifest
    files: tuple[VerifiedWorkspaceBlob, ...]

    def __post_init__(self) -> None:
        files = tuple(sorted(tuple(self.files), key=lambda item: item.file.path))
        descriptors = tuple(item.file for item in files)
        if descriptors != self.manifest.files:
            raise WorkspaceMaterializationError(
                "verified workspace files do not match the bound manifest"
            )
        object.__setattr__(self, "files", files)

    @property
    def manifest_id(self) -> str:
        return self.manifest.manifest_id


class WorkspaceMaterializer:
    """Resolve and verify a manifest without touching a filesystem."""

    def resolve(self, manifest: WorkspaceManifest, resolver: BlobResolver) -> VerifiedWorkspace:
        verified: list[VerifiedWorkspaceBlob] = []
        for item in manifest.files:
            try:
                payload = resolver.resolve(item.sha256)
            except BlobResolutionError as exc:
                raise WorkspaceMaterializationError(
                    f"unable to resolve admitted blob for {item.path}"
                ) from exc
            verified.append(VerifiedWorkspaceBlob(file=item, payload=payload))
        return VerifiedWorkspace(manifest=manifest, files=tuple(verified))


__all__ = [
    "BlobResolutionError",
    "BlobResolver",
    "VerifiedWorkspace",
    "VerifiedWorkspaceBlob",
    "WorkspaceMaterializationError",
    "WorkspaceMaterializer",
]
