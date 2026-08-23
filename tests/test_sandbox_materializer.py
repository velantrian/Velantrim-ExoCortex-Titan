from __future__ import annotations

import hashlib

import pytest

from core.sandbox import (
    BlobResolutionError,
    BlobResolver,
    VerifiedWorkspace,
    VerifiedWorkspaceBlob,
    WorkspaceFile,
    WorkspaceManifest,
    WorkspaceMaterializationError,
    WorkspaceMaterializer,
)


class InMemoryResolver:
    def __init__(self, blobs: dict[str, bytes]) -> None:
        self._blobs = dict(blobs)
        self.requests: list[str] = []

    def resolve(self, sha256: str) -> bytes:
        self.requests.append(sha256)
        try:
            return self._blobs[sha256]
        except KeyError as exc:
            raise BlobResolutionError("missing digest") from exc


def _file(path: str, payload: bytes) -> WorkspaceFile:
    return WorkspaceFile(
        path=path,
        sha256=hashlib.sha256(payload).hexdigest(),
        size_bytes=len(payload),
    )


def test_materializer_resolves_by_digest_and_binds_exact_manifest() -> None:
    first_payload = b"alpha"
    second_payload = b"beta"
    first = _file("src/a.txt", first_payload)
    second = _file("src/b.txt", second_payload)
    manifest = WorkspaceManifest(files=(second, first))
    resolver = InMemoryResolver(
        {
            first.sha256: first_payload,
            second.sha256: second_payload,
        }
    )

    verified = WorkspaceMaterializer().resolve(manifest, resolver)

    assert isinstance(resolver, BlobResolver)
    assert verified.manifest is manifest
    assert verified.manifest_id == manifest.manifest_id
    assert tuple(item.file for item in verified.files) == manifest.files
    assert resolver.requests == [item.sha256 for item in manifest.files]


def test_materializer_fails_closed_when_digest_is_missing() -> None:
    payload = b"missing"
    manifest = WorkspaceManifest(files=(_file("missing.txt", payload),))

    with pytest.raises(WorkspaceMaterializationError, match="unable to resolve"):
        WorkspaceMaterializer().resolve(manifest, InMemoryResolver({}))


def test_verified_blob_rejects_size_mismatch() -> None:
    expected = _file("size.txt", b"abc")

    with pytest.raises(WorkspaceMaterializationError, match="size mismatch"):
        VerifiedWorkspaceBlob(file=expected, payload=b"ab")


def test_verified_blob_rejects_digest_mismatch_with_same_size() -> None:
    expected = _file("digest.txt", b"abc")

    with pytest.raises(WorkspaceMaterializationError, match="digest mismatch"):
        VerifiedWorkspaceBlob(file=expected, payload=b"abd")


def test_verified_blob_rejects_mutable_payload() -> None:
    expected = _file("mutable.txt", b"abc")

    with pytest.raises(WorkspaceMaterializationError, match="immutable bytes"):
        VerifiedWorkspaceBlob(file=expected, payload=bytearray(b"abc"))  # type: ignore[arg-type]


def test_verified_workspace_rejects_foreign_manifest_binding() -> None:
    payload = b"same-size"
    admitted = _file("admitted.txt", payload)
    foreign = _file("foreign.txt", payload)
    manifest = WorkspaceManifest(files=(admitted,))
    verified_foreign = VerifiedWorkspaceBlob(file=foreign, payload=payload)

    with pytest.raises(WorkspaceMaterializationError, match="bound manifest"):
        VerifiedWorkspace(manifest=manifest, files=(verified_foreign,))
