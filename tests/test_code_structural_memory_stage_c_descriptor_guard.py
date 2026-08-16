from __future__ import annotations

import os
import sqlite3
from pathlib import Path

import pytest

import core.code_structural_memory.scanner as scanner
from core.code_structural_memory.contracts import RepositoryRegistration, ScanBudget
from core.code_structural_memory.schema import connect_database


def _budget(**overrides: object) -> ScanBudget:
    values: dict[str, object] = {
        "max_files": 20,
        "max_file_bytes": 100_000,
        "max_total_bytes": 1_000_000,
        "max_path_depth": 12,
        "max_scan_seconds": 5.0,
    }
    values.update(overrides)
    return ScanBudget(**values)  # type: ignore[arg-type]


def _registered(tmp_path: Path) -> tuple[sqlite3.Connection, Path]:
    root = tmp_path / "repo"
    root.mkdir()
    conn = connect_database(tmp_path / "csm.sqlite3")
    registration = RepositoryRegistration(
        repository_id="repo-a",
        local_root_fingerprint=scanner.local_root_fingerprint(root),
        registration_policy_id="stage-c-descriptor-guard-test-policy",
        tenant_or_project_scope="stage-c-descriptor-guard-tests",
        created_at="2026-08-16T04:40:00Z",
    )
    scanner.register_repository(conn, registration=registration, root=root)
    return conn, root


def _require_symlinks(tmp_path: Path) -> None:
    target = tmp_path / "symlink-target"
    target.write_text("ok", encoding="utf-8")
    probe = tmp_path / "symlink-probe"
    try:
        probe.symlink_to(target)
    except (NotImplementedError, OSError):
        pytest.skip("symlinks are unavailable in this test environment")
    finally:
        if probe.is_symlink():
            probe.unlink()


def _preserve_real_descriptor_capability_during_open_patch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if not scanner._descriptor_anchored_read_supported():
        pytest.skip("descriptor-anchored no-follow reads are unavailable")
    # The race harness intentionally wraps os.open. Production capability detection
    # uses the real os.open object's membership in os.supports_dir_fd, so replacing
    # that object would otherwise make the test fail closed before the injected race.
    monkeypatch.setattr(scanner, "_descriptor_anchored_read_supported", lambda: True)


def _qualified_names(conn: sqlite3.Connection) -> set[str]:
    return {
        row[0]
        for row in conn.execute(
            "SELECT qualified_name FROM csm_nodes WHERE repository_id='repo-a'"
        )
    }


def test_equal_size_swap_read_restore_reads_original_opened_object(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _require_symlinks(tmp_path)
    conn, root = _registered(tmp_path)
    try:
        alpha = b"def alpha():\n    return 1\n"
        bravo = b"def bravo():\n    return 1\n"
        assert len(alpha) == len(bravo)

        victim = root / "victim.py"
        outside = tmp_path / "outside.py"
        victim.write_bytes(alpha)
        outside.write_bytes(bravo)
        backup = root / ".victim-original"

        real_read = scanner.os.read
        swapped = False

        def swap_during_read(fd: int, count: int) -> bytes:
            nonlocal swapped
            if not swapped:
                swapped = True
                victim.rename(backup)
                victim.symlink_to(outside)
                try:
                    return real_read(fd, count)
                finally:
                    victim.unlink()
                    backup.rename(victim)
            return real_read(fd, count)

        monkeypatch.setattr(scanner.os, "read", swap_during_read)

        outcome = scanner.scan_python_repository(
            conn,
            repository_id="repo-a",
            root=root,
            relative_paths=["victim.py"],
            budget=_budget(),
            lease_ttl_seconds=10.0,
            token_factory=lambda: "lease-swap-read-restore",
        )

        assert swapped is True
        assert victim.read_bytes() == alpha
        assert outcome.promoted is True
        assert outcome.final_disposition == "PROMOTED"
        names = _qualified_names(conn)
        assert "victim.alpha" in names
        assert "victim.bravo" not in names
    finally:
        conn.close()


def test_swap_before_final_descriptor_open_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _require_symlinks(tmp_path)
    _preserve_real_descriptor_capability_during_open_patch(monkeypatch)
    conn, root = _registered(tmp_path)
    try:
        alpha = b"def alpha():\n    return 1\n"
        bravo = b"def bravo():\n    return 1\n"
        victim = root / "victim.py"
        outside = tmp_path / "outside.py"
        victim.write_bytes(alpha)
        outside.write_bytes(bravo)
        backup = root / ".victim-original"

        real_open = scanner.os.open
        swapped = False

        def swap_before_open(
            path: os.PathLike[str] | str,
            flags: int,
            mode: int = 0o777,
            *,
            dir_fd: int | None = None,
        ) -> int:
            nonlocal swapped
            if path == "victim.py" and dir_fd is not None and not swapped:
                swapped = True
                victim.rename(backup)
                victim.symlink_to(outside)
                try:
                    return real_open(path, flags, mode, dir_fd=dir_fd)
                finally:
                    victim.unlink()
                    backup.rename(victim)
            if dir_fd is None:
                return real_open(path, flags, mode)
            return real_open(path, flags, mode, dir_fd=dir_fd)

        monkeypatch.setattr(scanner.os, "open", swap_before_open)

        outcome = scanner.scan_python_repository(
            conn,
            repository_id="repo-a",
            root=root,
            relative_paths=["victim.py"],
            budget=_budget(),
            lease_ttl_seconds=10.0,
            token_factory=lambda: "lease-swap-before-open",
        )

        assert swapped is True
        assert victim.read_bytes() == alpha
        assert outcome.promoted is False
        assert outcome.final_disposition == "INCOMPLETE_REJECTED"
        assert "victim.bravo" not in _qualified_names(conn)
        assert conn.execute("SELECT COUNT(*) FROM csm_snapshots").fetchone()[0] == 0
        assert {problem.reason for problem in outcome.problems} == {
            "SYMLINK_RACE_DETECTED"
        }
    finally:
        conn.close()


def test_intermediate_directory_swap_to_external_symlink_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _require_symlinks(tmp_path)
    _preserve_real_descriptor_capability_during_open_patch(monkeypatch)
    conn, root = _registered(tmp_path)
    try:
        package = root / "pkg"
        package.mkdir()
        (package / "victim.py").write_text(
            "def alpha():\n    return 1\n",
            encoding="utf-8",
        )
        outside_dir = tmp_path / "outside-dir"
        outside_dir.mkdir()
        (outside_dir / "victim.py").write_text(
            "def bravo():\n    return 1\n",
            encoding="utf-8",
        )
        backup = root / ".pkg-original"

        real_open = scanner.os.open
        swapped = False

        def swap_directory_before_open(
            path: os.PathLike[str] | str,
            flags: int,
            mode: int = 0o777,
            *,
            dir_fd: int | None = None,
        ) -> int:
            nonlocal swapped
            if path == "pkg" and dir_fd is not None and not swapped:
                swapped = True
                package.rename(backup)
                package.symlink_to(outside_dir, target_is_directory=True)
                try:
                    return real_open(path, flags, mode, dir_fd=dir_fd)
                finally:
                    package.unlink()
                    backup.rename(package)
            if dir_fd is None:
                return real_open(path, flags, mode)
            return real_open(path, flags, mode, dir_fd=dir_fd)

        monkeypatch.setattr(scanner.os, "open", swap_directory_before_open)

        outcome = scanner.scan_python_repository(
            conn,
            repository_id="repo-a",
            root=root,
            relative_paths=["pkg/victim.py"],
            budget=_budget(),
            lease_ttl_seconds=10.0,
            token_factory=lambda: "lease-directory-swap",
        )

        assert swapped is True
        assert outcome.promoted is False
        assert outcome.final_disposition == "INCOMPLETE_REJECTED"
        assert "pkg.victim.bravo" not in _qualified_names(conn)
        assert conn.execute("SELECT COUNT(*) FROM csm_snapshots").fetchone()[0] == 0
        assert {problem.reason for problem in outcome.problems} <= {
            "SYMLINK_RACE_DETECTED",
            "PATH_COMPONENT_NOT_DIRECTORY",
        }
    finally:
        conn.close()


def test_root_path_replacement_after_root_fd_open_cannot_redirect_scan(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _require_symlinks(tmp_path)
    _preserve_real_descriptor_capability_during_open_patch(monkeypatch)
    conn, root = _registered(tmp_path)
    backup_root = tmp_path / "repo-original"
    outside_root = tmp_path / "outside-root"
    outside_root.mkdir()
    try:
        alpha = b"def alpha():\n    return 1\n"
        bravo = b"def bravo():\n    return 1\n"
        (root / "victim.py").write_bytes(alpha)
        (outside_root / "victim.py").write_bytes(bravo)

        real_open = scanner.os.open
        swapped = False

        def replace_root_after_open(
            path: os.PathLike[str] | str,
            flags: int,
            mode: int = 0o777,
            *,
            dir_fd: int | None = None,
        ) -> int:
            nonlocal swapped
            if Path(path) == root and dir_fd is None and not swapped:
                fd = real_open(path, flags, mode)
                swapped = True
                root.rename(backup_root)
                root.symlink_to(outside_root, target_is_directory=True)
                return fd
            if dir_fd is None:
                return real_open(path, flags, mode)
            return real_open(path, flags, mode, dir_fd=dir_fd)

        monkeypatch.setattr(scanner.os, "open", replace_root_after_open)

        outcome = scanner.scan_python_repository(
            conn,
            repository_id="repo-a",
            root=root,
            relative_paths=["victim.py"],
            budget=_budget(),
            lease_ttl_seconds=10.0,
            token_factory=lambda: "lease-root-replacement",
        )

        assert swapped is True
        assert outcome.promoted is True
        names = _qualified_names(conn)
        assert "victim.alpha" in names
        assert "victim.bravo" not in names
    finally:
        if root.is_symlink():
            root.unlink()
        if backup_root.exists():
            backup_root.rename(root)
        conn.close()


def test_missing_descriptor_capability_fails_closed_without_path_read_fallback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    conn, root = _registered(tmp_path)
    try:
        (root / "victim.py").write_text(
            "def alpha():\n    return 1\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(
            scanner,
            "_descriptor_anchored_read_supported",
            lambda: False,
        )

        outcome = scanner.scan_python_repository(
            conn,
            repository_id="repo-a",
            root=root,
            relative_paths=["victim.py"],
            budget=_budget(),
            lease_ttl_seconds=10.0,
            token_factory=lambda: "lease-no-descriptor-capability",
        )

        assert outcome.promoted is False
        assert outcome.final_disposition == "INCOMPLETE_REJECTED"
        assert {problem.reason for problem in outcome.problems} == {
            "DESCRIPTOR_ANCHORED_READ_UNAVAILABLE"
        }
        assert conn.execute("SELECT COUNT(*) FROM csm_snapshots").fetchone()[0] == 0
    finally:
        conn.close()
