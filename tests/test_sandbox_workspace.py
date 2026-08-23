from __future__ import annotations

import pytest

from core.sandbox import WorkspaceFile, WorkspaceManifest, WorkspaceManifestError


DIGEST_A = "a" * 64
DIGEST_B = "b" * 64


def test_workspace_manifest_is_deterministic_and_sorted() -> None:
    first = WorkspaceManifest(
        files=(
            WorkspaceFile(path="src/b.py", sha256=DIGEST_B, size_bytes=2),
            WorkspaceFile(path="src/a.py", sha256=DIGEST_A, size_bytes=1),
        )
    )
    second = WorkspaceManifest(
        files=(
            WorkspaceFile(path="src/a.py", sha256=DIGEST_A, size_bytes=1),
            WorkspaceFile(path="src/b.py", sha256=DIGEST_B, size_bytes=2),
        )
    )

    assert first.files == second.files
    assert first.manifest_id == second.manifest_id


@pytest.mark.parametrize(
    "path",
    [
        "../secret",
        "src/../../secret",
        "/etc/passwd",
        "./file.txt",
        "src/../file.txt",
        "",
    ],
)
def test_workspace_file_rejects_traversal_or_absolute_paths(path: str) -> None:
    with pytest.raises(WorkspaceManifestError):
        WorkspaceFile(path=path, sha256=DIGEST_A, size_bytes=1)


def test_workspace_manifest_rejects_duplicate_paths() -> None:
    with pytest.raises(WorkspaceManifestError, match="unique"):
        WorkspaceManifest(
            files=(
                WorkspaceFile(path="same.txt", sha256=DIGEST_A, size_bytes=1),
                WorkspaceFile(path="same.txt", sha256=DIGEST_B, size_bytes=1),
            )
        )


def test_workspace_manifest_enforces_file_count_limit() -> None:
    with pytest.raises(WorkspaceManifestError, match="file count"):
        WorkspaceManifest(
            files=(
                WorkspaceFile(path="a.txt", sha256=DIGEST_A, size_bytes=1),
                WorkspaceFile(path="b.txt", sha256=DIGEST_B, size_bytes=1),
            ),
            max_files=1,
        )


def test_workspace_manifest_enforces_total_byte_limit() -> None:
    with pytest.raises(WorkspaceManifestError, match="bytes"):
        WorkspaceManifest(
            files=(WorkspaceFile(path="a.txt", sha256=DIGEST_A, size_bytes=2),),
            max_total_bytes=1,
        )


def test_workspace_file_rejects_invalid_digest_and_negative_size() -> None:
    with pytest.raises(WorkspaceManifestError, match="sha256"):
        WorkspaceFile(path="a.txt", sha256="nope", size_bytes=1)
    with pytest.raises(WorkspaceManifestError, match="non-negative"):
        WorkspaceFile(path="a.txt", sha256=DIGEST_A, size_bytes=-1)
