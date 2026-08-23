from __future__ import annotations

import hashlib
import os
from pathlib import Path

import pytest

from core.sandbox import (
    EphemeralWorkspaceError,
    EphemeralWorkspaceWriter,
    VerifiedWorkspace,
    VerifiedWorkspaceBlob,
    WorkspaceFile,
    WorkspaceManifest,
)


def _verified_workspace() -> VerifiedWorkspace:
    first_payload = b"print('safe input')\n"
    second_payload = b"data\n"
    first = WorkspaceFile(
        path="bin/run.py",
        sha256=hashlib.sha256(first_payload).hexdigest(),
        size_bytes=len(first_payload),
        executable=True,
    )
    second = WorkspaceFile(
        path="data/input.txt",
        sha256=hashlib.sha256(second_payload).hexdigest(),
        size_bytes=len(second_payload),
    )
    manifest = WorkspaceManifest(files=(first, second))
    return VerifiedWorkspace(
        manifest=manifest,
        files=(
            VerifiedWorkspaceBlob(file=first, payload=first_payload),
            VerifiedWorkspaceBlob(file=second, payload=second_payload),
        ),
    )


def test_writer_materializes_verified_files_and_rechecks_integrity() -> None:
    verified = _verified_workspace()
    workspace = EphemeralWorkspaceWriter().materialize(verified)
    try:
        assert workspace.root.is_dir()
        assert workspace.manifest_id == verified.manifest_id
        assert (workspace.root / "bin" / "run.py").read_bytes() == b"print('safe input')\n"
        assert (workspace.root / "data" / "input.txt").read_bytes() == b"data\n"
        if os.name != "nt":
            assert (workspace.root.stat().st_mode & 0o777) == 0o700
            assert ((workspace.root / "bin" / "run.py").stat().st_mode & 0o777) == 0o700
            assert ((workspace.root / "data" / "input.txt").stat().st_mode & 0o777) == 0o600
    finally:
        workspace.close()


def test_context_manager_verifies_cleanup_and_close_is_idempotent() -> None:
    verified = _verified_workspace()
    with EphemeralWorkspaceWriter().materialize(verified) as workspace:
        root = workspace.root
        assert root.exists()

    assert not root.exists()
    assert workspace.closed is True
    workspace.close()


def test_closed_workspace_cannot_be_reentered() -> None:
    workspace = EphemeralWorkspaceWriter().materialize(_verified_workspace())
    workspace.close()

    with pytest.raises(EphemeralWorkspaceError, match="already closed"):
        workspace.__enter__()


def test_partial_materialization_failure_removes_allocated_root(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    allocated: list[Path] = []

    def fail_write(root: Path, *args: object, **kwargs: object) -> None:
        allocated.append(root)
        raise EphemeralWorkspaceError("synthetic write failure")

    monkeypatch.setattr(
        EphemeralWorkspaceWriter,
        "_write_blob",
        staticmethod(fail_write),
    )

    with pytest.raises(EphemeralWorkspaceError, match="synthetic"):
        EphemeralWorkspaceWriter().materialize(_verified_workspace())

    assert len(allocated) == 1
    assert not allocated[0].exists()
