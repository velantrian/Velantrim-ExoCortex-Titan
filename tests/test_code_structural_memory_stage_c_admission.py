from pathlib import Path

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


def _registered(tmp_path: Path) -> tuple[object, Path]:
    root = tmp_path / "repo"
    root.mkdir()
    conn = connect_database(tmp_path / "csm.sqlite3")
    registration = RepositoryRegistration(
        repository_id="repo-a",
        local_root_fingerprint=scanner.local_root_fingerprint(root),
        registration_policy_id="stage-c-admission-test-policy",
        tenant_or_project_scope="stage-c-admission-tests",
        created_at="2026-08-15T19:00:00Z",
    )
    scanner.register_repository(conn, registration=registration, root=root)
    return conn, root


def test_parent_traversal_manifest_entry_fails_closed_without_promotion(tmp_path: Path) -> None:
    conn, root = _registered(tmp_path)
    try:
        outside = tmp_path / "outside.py"
        outside.write_text("def outside():\n    return 'must-not-read'\n", encoding="utf-8")

        outcome = scanner.scan_python_repository(
            conn,
            repository_id="repo-a",
            root=root,
            relative_paths=["../outside.py"],
            budget=_budget(),
            lease_ttl_seconds=10.0,
            token_factory=lambda: "lease-traversal",
        )

        assert outcome.promoted is False
        assert outcome.final_disposition == "INCOMPLETE_REJECTED"
        assert {problem.reason for problem in outcome.problems} == {
            "INVALID_RELATIVE_PATH"
        }
        assert conn.execute("SELECT COUNT(*) FROM csm_snapshots").fetchone()[0] == 0
        state = conn.execute(
            "SELECT current_snapshot_id, lease_token "
            "FROM csm_repository_scan_state WHERE repository_id='repo-a'"
        ).fetchone()
        assert tuple(state) == (None, None)
    finally:
        conn.close()


def test_scan_timeout_is_receipted_and_never_promoted(tmp_path: Path) -> None:
    conn, root = _registered(tmp_path)
    try:
        (root / "a.py").write_text("def a():\n    return 1\n", encoding="utf-8")
        monotonic_values = iter((0.0, 6.0))

        outcome = scanner.scan_python_repository(
            conn,
            repository_id="repo-a",
            root=root,
            relative_paths=["a.py"],
            budget=_budget(max_scan_seconds=5.0),
            lease_ttl_seconds=10.0,
            wall_clock=lambda: 100.0,
            monotonic_clock=lambda: next(monotonic_values),
            token_factory=lambda: "lease-timeout",
        )

        assert outcome.promoted is False
        assert outcome.final_disposition == "INCOMPLETE_REJECTED"
        assert outcome.omission_reason_counts == (("SCAN_TIMEOUT", 1),)
        assert outcome.error_reason_counts == ()
        assert {problem.reason for problem in outcome.problems} == {"SCAN_TIMEOUT"}
        assert conn.execute("SELECT COUNT(*) FROM csm_snapshots").fetchone()[0] == 0
        receipt = conn.execute(
            "SELECT final_disposition, omitted_count, omission_reason_counts_json "
            "FROM csm_scan_receipts WHERE repository_id='repo-a'"
        ).fetchone()
        assert tuple(receipt) == (
            "INCOMPLETE_REJECTED",
            1,
            '[["SCAN_TIMEOUT",1]]',
        )
    finally:
        conn.close()
