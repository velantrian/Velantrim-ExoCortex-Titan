import sqlite3

import pytest

from core.code_structural_memory.schema import (
    SCHEMA_VERSION,
    _V1_STATEMENTS,
    _apply_statements_transactionally,
    _apply_versioned_migration,
    connect_database,
    initialize_schema,
    schema_version,
)


def _insert_v1_repository_receipt_snapshot(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        INSERT INTO csm_repositories (
            repository_id, canonical_origin, local_root_fingerprint,
            registration_policy_id, tenant_or_project_scope, created_at,
            status, retention_policy_id
        ) VALUES ('repo-a', NULL, 'root-a', 'policy-a', 'project-a',
                  '2026-08-15T10:00:00Z', 'ACTIVE', NULL)
        """
    )
    conn.execute(
        """
        INSERT INTO csm_scan_receipts (
            repository_id, receipt_id, generation, previous_snapshot_id,
            candidate_snapshot_id, source_manifest_digest, source_dirty,
            source_commit_sha, parser_profile_id, parser_versions_json,
            scan_config_digest, discovered_file_count, discovered_byte_count,
            omitted_count, omission_reason_counts_json, error_count,
            error_reason_counts_json, structural_graph_digest, lease_cas_result,
            final_disposition, started_at, completed_at, no_runtime_authority
        ) VALUES (
            'repo-a', 'receipt-3', 3, NULL, 'snapshot-3', 'manifest', 0,
            'abc123', 'python-v1', '[]', 'config', 1, 10, 0, '[]', 0,
            '[]', 'graph', 'STAGE_B_FIXTURE', 'PROMOTED',
            '2026-08-15T10:00:00Z', '2026-08-15T10:00:01Z', 1
        )
        """
    )
    conn.execute(
        """
        INSERT INTO csm_snapshots (
            repository_id, snapshot_id, generation, manifest_digest, dirty,
            commit_sha, parser_profile_id, parser_versions_json,
            scan_config_digest, discovered_file_count, discovered_byte_count,
            structural_graph_digest, scan_receipt_id, promoted_at
        ) VALUES (
            'repo-a', 'snapshot-3', 3, 'manifest', 0, 'abc123',
            'python-v1', '[]', 'config', 1, 10, 'graph', 'receipt-3',
            '2026-08-15T10:00:01Z'
        )
        """
    )
    conn.commit()


def test_v1_to_v2_migration_preserves_rows_and_backfills_scan_state(tmp_path) -> None:
    conn = connect_database(tmp_path / "stage-c-migrate.sqlite3")
    try:
        _apply_statements_transactionally(
            conn,
            statements=_V1_STATEMENTS,
            target_version=1,
        )
        _insert_v1_repository_receipt_snapshot(conn)
        assert schema_version(conn) == 1

        assert initialize_schema(conn) == SCHEMA_VERSION == 2
        state = conn.execute(
            "SELECT * FROM csm_repository_scan_state WHERE repository_id='repo-a'"
        ).fetchone()
        assert state is not None
        assert state["next_generation"] == 4
        assert state["current_snapshot_id"] == "snapshot-3"
        assert state["current_generation"] == 3
        assert state["current_receipt_id"] == "receipt-3"
        assert state["lease_token"] is None
        assert conn.execute(
            "SELECT COUNT(*) FROM csm_snapshots WHERE repository_id='repo-a'"
        ).fetchone()[0] == 1
    finally:
        conn.close()


def test_stage_c_migration_rolls_back_on_failure(tmp_path) -> None:
    conn = connect_database(tmp_path / "stage-c-rollback.sqlite3")
    try:
        _apply_statements_transactionally(
            conn,
            statements=_V1_STATEMENTS,
            target_version=1,
        )
        with pytest.raises(sqlite3.OperationalError):
            _apply_versioned_migration(
                conn,
                statements=(
                    "CREATE TABLE stage_c_probe(value TEXT NOT NULL)",
                    "THIS IS NOT VALID SQL",
                ),
                expected_current=1,
                target_version=2,
            )
        assert schema_version(conn) == 1
        assert conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='stage_c_probe'"
        ).fetchone() is None
    finally:
        conn.close()


def test_new_repository_gets_scan_state_after_v2_bootstrap(tmp_path) -> None:
    conn = connect_database(tmp_path / "stage-c-new-repo.sqlite3")
    try:
        initialize_schema(conn)
        conn.execute(
            """
            INSERT INTO csm_repositories (
                repository_id, canonical_origin, local_root_fingerprint,
                registration_policy_id, tenant_or_project_scope, created_at,
                status, retention_policy_id
            ) VALUES ('repo-new', NULL, 'root', 'policy', 'project',
                      '2026-08-15T10:00:00Z', 'ACTIVE', NULL)
            """
        )
        state = conn.execute(
            "SELECT * FROM csm_repository_scan_state WHERE repository_id='repo-new'"
        ).fetchone()
        assert state is not None
        assert state["next_generation"] == 1
        assert state["current_snapshot_id"] is None
        assert state["lease_token"] is None
    finally:
        conn.close()


def test_scan_receipt_generation_is_unique_per_repository(tmp_path) -> None:
    conn = connect_database(tmp_path / "stage-c-generation.sqlite3")
    try:
        initialize_schema(conn)
        conn.execute(
            """
            INSERT INTO csm_repositories (
                repository_id, local_root_fingerprint, registration_policy_id,
                tenant_or_project_scope, created_at, status
            ) VALUES ('repo-a', 'root', 'policy', 'project', 'z', 'ACTIVE')
            """
        )
        base_sql = """
            INSERT INTO csm_scan_receipts (
                repository_id, receipt_id, generation, candidate_snapshot_id,
                source_manifest_digest, source_dirty, source_commit_sha,
                parser_profile_id, parser_versions_json, scan_config_digest,
                discovered_file_count, discovered_byte_count, omitted_count,
                omission_reason_counts_json, error_count, error_reason_counts_json,
                structural_graph_digest, lease_cas_result, final_disposition,
                started_at, completed_at, no_runtime_authority
            ) VALUES (
                'repo-a', ?, 1, ?, 'manifest', 1, NULL, 'python-v1', '[]',
                'config', 0, 0, 1, '[["test",1]]', 0, '[]', 'graph',
                'CAS_REJECTED_INCOMPLETE', 'INCOMPLETE_REJECTED', 'a', 'b', 1
            )
        """
        conn.execute(base_sql, ("receipt-a", "snapshot-a"))
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(base_sql, ("receipt-b", "snapshot-b"))
    finally:
        conn.close()


def test_scan_lease_event_rows_are_immutable(tmp_path) -> None:
    conn = connect_database(tmp_path / "stage-c-events.sqlite3")
    try:
        initialize_schema(conn)
        conn.execute(
            """
            INSERT INTO csm_repositories (
                repository_id, local_root_fingerprint, registration_policy_id,
                tenant_or_project_scope, created_at, status
            ) VALUES ('repo-a', 'root', 'policy', 'project', 'z', 'ACTIVE')
            """
        )
        conn.execute(
            """
            INSERT INTO csm_scan_lease_events (
                repository_id, event_id, generation, holder_token, event_type,
                observed_at, reason_code, no_runtime_authority
            ) VALUES ('repo-a', 'event-a', 1, 'token-a', 'ACQUIRED', 1.0,
                      'EXPLICIT_SCAN_INVOCATION', 1)
            """
        )
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            conn.execute(
                "UPDATE csm_scan_lease_events SET event_type='CHANGED' "
                "WHERE repository_id='repo-a' AND event_id='event-a'"
            )
    finally:
        conn.close()
