from __future__ import annotations

import builtins
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
        registration_policy_id="stage-c-budget-admission-test-policy",
        tenant_or_project_scope="stage-c-budget-admission-tests",
        created_at="2026-08-15T22:00:00Z",
    )
    scanner.register_repository(conn, registration=registration, root=root)
    return conn, root


def test_rejected_files_consume_total_budget_before_later_reads(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    conn, root = _registered(tmp_path)
    try:
        (root / "a_nonutf.py").write_bytes(b"\xffabcdefg")
        (root / "b_nul.py").write_bytes(b"\x00abcdefg")
        (root / "c_parser.py").write_bytes(b"def bad(")
        (root / "d_valid.py").write_bytes(b"x = 1\n")

        opened_for_read: list[str] = []
        original_open = Path.open

        def tracking_open(path: Path, *args: object, **kwargs: object):
            mode = args[0] if args else kwargs.get("mode", "r")
            if path.parent == root and mode == "rb":
                opened_for_read.append(path.name)
            return original_open(path, *args, **kwargs)  # type: ignore[arg-type]

        monkeypatch.setattr(Path, "open", tracking_open)

        outcome = scanner.scan_python_repository(
            conn,
            repository_id="repo-a",
            root=root,
            relative_paths=[
                "a_nonutf.py",
                "b_nul.py",
                "c_parser.py",
                "d_valid.py",
            ],
            budget=_budget(max_file_bytes=20, max_total_bytes=26),
            lease_ttl_seconds=10.0,
            token_factory=lambda: "lease-total-invalid",
        )

        assert outcome.promoted is False
        assert outcome.final_disposition == "INCOMPLETE_REJECTED"
        assert opened_for_read == ["a_nonutf.py", "b_nul.py", "c_parser.py"]
        assert {problem.reason for problem in outcome.problems} == {
            "NON_UTF8_SOURCE",
            "BINARY_NUL_PAYLOAD",
            "PARSER_ERROR",
            "TOTAL_BYTE_LIMIT",
        }
        state = conn.execute(
            "SELECT current_snapshot_id FROM csm_repository_scan_state "
            "WHERE repository_id='repo-a'"
        ).fetchone()
        assert state[0] is None
    finally:
        conn.close()


def test_growth_after_stat_reads_only_to_file_budget_plus_detection_byte(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    conn, root = _registered(tmp_path)
    try:
        victim = root / "victim.py"
        victim.write_bytes(b"x=1\n")
        original_open = Path.open
        swapped = False

        def grow_before_read(path: Path, *args: object, **kwargs: object):
            nonlocal swapped
            mode = args[0] if args else kwargs.get("mode", "r")
            if path == victim and mode == "rb" and not swapped:
                swapped = True
                with builtins.open(victim, "wb") as handle:
                    handle.write(b"x=1\n" + (b"#" * 100))
            return original_open(path, *args, **kwargs)  # type: ignore[arg-type]

        monkeypatch.setattr(Path, "open", grow_before_read)

        outcome = scanner.scan_python_repository(
            conn,
            repository_id="repo-a",
            root=root,
            relative_paths=["victim.py"],
            budget=_budget(max_file_bytes=16, max_total_bytes=64),
            lease_ttl_seconds=10.0,
            token_factory=lambda: "lease-growth-budget",
        )

        assert swapped is True
        assert outcome.promoted is False
        assert outcome.final_disposition == "INCOMPLETE_REJECTED"
        assert victim.stat().st_size > 17
        assert len(outcome.problems) == 1
        problem = outcome.problems[0]
        assert problem.reason == "FILE_SIZE_LIMIT"
        assert problem.observed_bytes == 17
        assert conn.execute("SELECT COUNT(*) FROM csm_snapshots").fetchone()[0] == 0
    finally:
        conn.close()
