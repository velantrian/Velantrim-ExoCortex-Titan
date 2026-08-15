import json
import sqlite3

import pytest

from core.code_structural_memory.contracts import serialize_reason_counts
from core.code_structural_memory.schema import (
    SCHEMA_VERSION,
    CSMDatabaseError,
    UnsupportedSchemaVersionError,
    _apply_statements_transactionally,
    connect_database,
    initialize_schema,
    schema_version,
)


def _insert_repository(conn: sqlite3.Connection, repository_id: str) -> None:
    conn.execute(
        """
        INSERT INTO csm_repositories (
            repository_id,
            canonical_origin,
            local_root_fingerprint,
            registration_policy_id,
            tenant_or_project_scope,
            created_at,
            status,
            retention_policy_id
        ) VALUES (?, NULL, ?, ?, ?, ?, 'ACTIVE', NULL)
        """,
        (
            repository_id,
            f"root-{repository_id}",
            "policy-1",
            "project-1",
            "2026-08-15T10:00:00Z",
        ),
    )


def _insert_receipt(
    conn: sqlite3.Connection,
    repository_id: str,
    receipt_id: str,
    snapshot_id: str,
    generation: int,
    *,
    source_manifest_digest: str = "manifest",
    source_dirty: int = 0,
    source_commit_sha: str | None = "abc123",
    omitted_count: int = 0,
    omission_reason_counts_json: str = "[]",
    error_count: int = 0,
    error_reason_counts_json: str = "[]",
) -> None:
    conn.execute(
        """
        INSERT INTO csm_scan_receipts (
            receipt_id,
            repository_id,
            generation,
            previous_snapshot_id,
            candidate_snapshot_id,
            source_manifest_digest,
            source_dirty,
            source_commit_sha,
            parser_profile_id,
            parser_versions_json,
            scan_config_digest,
            discovered_file_count,
            discovered_byte_count,
            omitted_count,
            omission_reason_counts_json,
            error_count,
            error_reason_counts_json,
            structural_graph_digest,
            lease_cas_result,
            final_disposition,
            started_at,
            completed_at,
            no_runtime_authority
        ) VALUES (
            ?, ?, ?, NULL, ?, ?, ?, ?, 'python-v1', '[]', 'config', 1, 10,
            ?, ?, ?, ?, 'graph', 'NOT_IMPLEMENTED_STAGE_B', 'SCHEMA_FIXTURE',
            '2026-08-15T10:00:00Z', '2026-08-15T10:00:01Z', 1
        )
        """,
        (
            receipt_id,
            repository_id,
            generation,
            snapshot_id,
            source_manifest_digest,
            source_dirty,
            source_commit_sha,
            omitted_count,
            omission_reason_counts_json,
            error_count,
            error_reason_counts_json,
        ),
    )


def _insert_snapshot(
    conn: sqlite3.Connection,
    repository_id: str,
    snapshot_id: str,
    receipt_id: str,
    generation: int,
    *,
    manifest_digest: str = "manifest",
    dirty: int = 0,
    commit_sha: str | None = "abc123",
) -> None:
    conn.execute(
        """
        INSERT INTO csm_snapshots (
            repository_id,
            snapshot_id,
            generation,
            manifest_digest,
            dirty,
            commit_sha,
            parser_profile_id,
            parser_versions_json,
            scan_config_digest,
            discovered_file_count,
            discovered_byte_count,
            structural_graph_digest,
            scan_receipt_id,
            promoted_at
        ) VALUES (?, ?, ?, ?, ?, ?, 'python-v1', '[]', 'config',
                  1, 10, 'graph', ?, NULL)
        """,
        (
            repository_id,
            snapshot_id,
            generation,
            manifest_digest,
            dirty,
            commit_sha,
            receipt_id,
        ),
    )


def _insert_node(
    conn: sqlite3.Connection,
    repository_id: str,
    snapshot_id: str,
    node_id: str,
    generation: int,
) -> None:
    conn.execute(
        """
        INSERT INTO csm_nodes (
            repository_id,
            snapshot_id,
            node_id,
            generation,
            node_kind,
            relative_path,
            qualified_name,
            start_byte,
            end_byte,
            parser_profile_id,
            parser_adapter_id
        ) VALUES (?, ?, ?, ?, 'FUNCTION', 'core/example.py', ?, 0, 10, 'python-v1', 'ast-v1')
        """,
        (repository_id, snapshot_id, node_id, generation, node_id),
    )


def test_empty_database_bootstraps_v1_idempotently(tmp_path) -> None:
    conn = connect_database(tmp_path / "csm.sqlite3")
    try:
        assert schema_version(conn) == 0
        assert initialize_schema(conn) == SCHEMA_VERSION
        assert initialize_schema(conn) == SCHEMA_VERSION
        assert schema_version(conn) == SCHEMA_VERSION
        assert int(conn.execute("PRAGMA foreign_keys").fetchone()[0]) == 1
    finally:
        conn.close()


def test_newer_schema_version_fails_closed(tmp_path) -> None:
    conn = connect_database(tmp_path / "newer.sqlite3")
    try:
        conn.execute(
            "CREATE TABLE csm_schema_meta (singleton INTEGER PRIMARY KEY, schema_version INTEGER NOT NULL)"
        )
        conn.execute(
            "INSERT INTO csm_schema_meta(singleton, schema_version) VALUES (1, ?)",
            (SCHEMA_VERSION + 1,),
        )
        conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION + 1}")
        with pytest.raises(UnsupportedSchemaVersionError, match="newer"):
            initialize_schema(conn)
    finally:
        conn.close()


def test_schema_metadata_mismatch_fails_closed(tmp_path) -> None:
    conn = connect_database(tmp_path / "mismatch.sqlite3")
    try:
        conn.execute(
            "CREATE TABLE csm_schema_meta (singleton INTEGER PRIMARY KEY, schema_version INTEGER NOT NULL)"
        )
        conn.execute(
            "INSERT INTO csm_schema_meta(singleton, schema_version) VALUES (1, 1)"
        )
        conn.execute("PRAGMA user_version = 2")
        with pytest.raises(CSMDatabaseError, match="disagrees"):
            schema_version(conn)
    finally:
        conn.close()


def test_failed_migration_rolls_back_ddl_and_version(tmp_path) -> None:
    conn = connect_database(tmp_path / "rollback.sqlite3")
    try:
        with pytest.raises(sqlite3.OperationalError):
            _apply_statements_transactionally(
                conn,
                statements=(
                    "CREATE TABLE csm_schema_meta (singleton INTEGER PRIMARY KEY, schema_version INTEGER NOT NULL)",
                    "CREATE TABLE migration_probe (value TEXT NOT NULL)",
                    "THIS IS NOT VALID SQL",
                ),
                target_version=1,
            )
        assert conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='migration_probe'"
        ).fetchone() is None
        assert int(conn.execute("PRAGMA user_version").fetchone()[0]) == 0
    finally:
        conn.close()


def test_dirty_receipt_with_commit_identity_is_rejected(tmp_path) -> None:
    conn = connect_database(tmp_path / "dirty-receipt.sqlite3")
    try:
        initialize_schema(conn)
        _insert_repository(conn, "repo-a")
        with pytest.raises(sqlite3.IntegrityError):
            _insert_receipt(
                conn,
                "repo-a",
                "receipt-a",
                "snapshot-a",
                1,
                source_dirty=1,
                source_commit_sha="abc123",
            )
    finally:
        conn.close()


def test_snapshot_cannot_attach_receipt_from_another_repository(tmp_path) -> None:
    conn = connect_database(tmp_path / "receipt-repository-custody.sqlite3")
    try:
        initialize_schema(conn)
        _insert_repository(conn, "repo-a")
        _insert_repository(conn, "repo-b")
        _insert_receipt(conn, "repo-b", "receipt-b", "snapshot-a", 1)

        with pytest.raises(sqlite3.IntegrityError):
            _insert_snapshot(conn, "repo-a", "snapshot-a", "receipt-b", 1)
    finally:
        conn.close()


def test_snapshot_generation_must_match_receipt_generation(tmp_path) -> None:
    conn = connect_database(tmp_path / "receipt-generation-custody.sqlite3")
    try:
        initialize_schema(conn)
        _insert_repository(conn, "repo-a")
        _insert_receipt(conn, "repo-a", "receipt-a", "snapshot-a", 1)

        with pytest.raises(sqlite3.IntegrityError):
            _insert_snapshot(conn, "repo-a", "snapshot-a", "receipt-a", 2)
    finally:
        conn.close()


def test_snapshot_source_state_must_match_receipt_source_state(tmp_path) -> None:
    conn = connect_database(tmp_path / "source-state-custody.sqlite3")
    try:
        initialize_schema(conn)
        _insert_repository(conn, "repo-a")
        _insert_receipt(conn, "repo-a", "receipt-a", "snapshot-a", 1)

        with pytest.raises(sqlite3.IntegrityError, match="source state"):
            _insert_snapshot(
                conn,
                "repo-a",
                "snapshot-a",
                "receipt-a",
                1,
                manifest_digest="different-manifest",
            )
    finally:
        conn.close()


def test_dirty_source_state_matches_null_commit_across_receipt_and_snapshot(
    tmp_path,
) -> None:
    conn = connect_database(tmp_path / "dirty-source-state-custody.sqlite3")
    try:
        initialize_schema(conn)
        _insert_repository(conn, "repo-a")
        _insert_receipt(
            conn,
            "repo-a",
            "receipt-a",
            "snapshot-a",
            1,
            source_dirty=1,
            source_commit_sha=None,
        )
        _insert_snapshot(
            conn,
            "repo-a",
            "snapshot-a",
            "receipt-a",
            1,
            dirty=1,
            commit_sha=None,
        )
        row = conn.execute(
            "SELECT dirty, commit_sha FROM csm_snapshots WHERE repository_id='repo-a'"
        ).fetchone()
        assert row is not None
        assert tuple(row) == (1, None)
    finally:
        conn.close()


def test_snapshot_identity_inputs_cannot_drift_after_insert(tmp_path) -> None:
    conn = connect_database(tmp_path / "snapshot-identity-immutable.sqlite3")
    try:
        initialize_schema(conn)
        _insert_repository(conn, "repo-a")
        _insert_receipt(conn, "repo-a", "receipt-a", "snapshot-a", 1)
        _insert_snapshot(conn, "repo-a", "snapshot-a", "receipt-a", 1)

        with pytest.raises(sqlite3.IntegrityError, match="snapshot identity inputs"):
            conn.execute(
                "UPDATE csm_snapshots SET parser_profile_id='python-v2' "
                "WHERE repository_id='repo-a' AND snapshot_id='snapshot-a'"
            )

        conn.execute(
            "UPDATE csm_snapshots SET promoted_at='2026-08-15T10:00:02Z' "
            "WHERE repository_id='repo-a' AND snapshot_id='snapshot-a'"
        )
        assert conn.execute(
            "SELECT promoted_at FROM csm_snapshots "
            "WHERE repository_id='repo-a' AND snapshot_id='snapshot-a'"
        ).fetchone()[0] == "2026-08-15T10:00:02Z"
    finally:
        conn.close()


def test_receipt_snapshot_identity_inputs_cannot_drift_after_insert(tmp_path) -> None:
    conn = connect_database(tmp_path / "receipt-identity-immutable.sqlite3")
    try:
        initialize_schema(conn)
        _insert_repository(conn, "repo-a")
        _insert_receipt(conn, "repo-a", "receipt-a", "snapshot-a", 1)
        _insert_snapshot(conn, "repo-a", "snapshot-a", "receipt-a", 1)

        with pytest.raises(sqlite3.IntegrityError, match="receipt snapshot identity inputs"):
            conn.execute(
                "UPDATE csm_scan_receipts SET source_manifest_digest='other' "
                "WHERE repository_id='repo-a' AND receipt_id='receipt-a'"
            )
    finally:
        conn.close()


def test_reason_count_json_round_trips_deterministically(tmp_path) -> None:
    conn = connect_database(tmp_path / "reason-counts.sqlite3")
    try:
        initialize_schema(conn)
        _insert_repository(conn, "repo-a")
        omission_json = serialize_reason_counts((("zeta", 1), ("alpha", 2)))
        error_json = serialize_reason_counts((("parse", 1),))
        _insert_receipt(
            conn,
            "repo-a",
            "receipt-a",
            "snapshot-a",
            1,
            omitted_count=3,
            omission_reason_counts_json=omission_json,
            error_count=1,
            error_reason_counts_json=error_json,
        )
        row = conn.execute(
            """
            SELECT omission_reason_counts_json, error_reason_counts_json
            FROM csm_scan_receipts
            WHERE repository_id = 'repo-a' AND receipt_id = 'receipt-a'
            """
        ).fetchone()
        assert row is not None
        assert row[0] == '[["alpha",2],["zeta",1]]'
        assert json.loads(row[0]) == [["alpha", 2], ["zeta", 1]]
        assert row[1] == '[["parse",1]]'
    finally:
        conn.close()


def test_node_generation_must_match_snapshot_generation(tmp_path) -> None:
    conn = connect_database(tmp_path / "node-generation-custody.sqlite3")
    try:
        initialize_schema(conn)
        _insert_repository(conn, "repo-a")
        _insert_receipt(conn, "repo-a", "receipt-a", "snapshot-a", 1)
        _insert_snapshot(conn, "repo-a", "snapshot-a", "receipt-a", 1)

        with pytest.raises(sqlite3.IntegrityError):
            _insert_node(conn, "repo-a", "snapshot-a", "node-a", 2)
    finally:
        conn.close()


def test_cross_repository_resolved_edge_is_rejected(tmp_path) -> None:
    conn = connect_database(tmp_path / "repo-isolation.sqlite3")
    try:
        initialize_schema(conn)
        _insert_repository(conn, "repo-a")
        _insert_repository(conn, "repo-b")
        _insert_receipt(conn, "repo-a", "receipt-a", "snapshot-a", 1)
        _insert_receipt(conn, "repo-b", "receipt-b", "snapshot-b", 1)
        _insert_snapshot(conn, "repo-a", "snapshot-a", "receipt-a", 1)
        _insert_snapshot(conn, "repo-b", "snapshot-b", "receipt-b", 1)
        _insert_node(conn, "repo-a", "snapshot-a", "source-a", 1)
        _insert_node(conn, "repo-b", "snapshot-b", "target-b", 1)

        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                """
                INSERT INTO csm_edges (
                    repository_id, snapshot_id, edge_id, generation, edge_kind,
                    source_node_id, target_node_id, unresolved_target_id,
                    source_start_byte, source_end_byte, parser_adapter_id, resolution_rule
                ) VALUES (
                    'repo-a', 'snapshot-a', 'edge-1', 1, 'IMPORTS',
                    'source-a', 'target-b', NULL, 0, 1, 'ast-v1', 'static-v1'
                )
                """
            )
    finally:
        conn.close()


def test_cross_snapshot_resolved_edge_is_rejected(tmp_path) -> None:
    conn = connect_database(tmp_path / "snapshot-isolation.sqlite3")
    try:
        initialize_schema(conn)
        _insert_repository(conn, "repo-a")
        _insert_receipt(conn, "repo-a", "receipt-1", "snapshot-1", 1)
        _insert_receipt(conn, "repo-a", "receipt-2", "snapshot-2", 2)
        _insert_snapshot(conn, "repo-a", "snapshot-1", "receipt-1", 1)
        _insert_snapshot(conn, "repo-a", "snapshot-2", "receipt-2", 2)
        _insert_node(conn, "repo-a", "snapshot-1", "source-1", 1)
        _insert_node(conn, "repo-a", "snapshot-2", "target-2", 2)

        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                """
                INSERT INTO csm_edges (
                    repository_id, snapshot_id, edge_id, generation, edge_kind,
                    source_node_id, target_node_id, unresolved_target_id,
                    source_start_byte, source_end_byte, parser_adapter_id, resolution_rule
                ) VALUES (
                    'repo-a', 'snapshot-1', 'edge-1', 1, 'IMPORTS',
                    'source-1', 'target-2', NULL, 0, 1, 'ast-v1', 'static-v1'
                )
                """
            )
    finally:
        conn.close()


def test_dirty_snapshot_with_commit_identity_is_rejected(tmp_path) -> None:
    conn = connect_database(tmp_path / "dirty.sqlite3")
    try:
        initialize_schema(conn)
        _insert_repository(conn, "repo-a")
        _insert_receipt(conn, "repo-a", "receipt-a", "snapshot-a", 1)

        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                """
                INSERT INTO csm_snapshots (
                    repository_id, snapshot_id, generation, manifest_digest, dirty, commit_sha,
                    parser_profile_id, parser_versions_json, scan_config_digest,
                    discovered_file_count, discovered_byte_count, structural_graph_digest,
                    scan_receipt_id, promoted_at
                ) VALUES (
                    'repo-a', 'snapshot-a', 1, 'manifest', 1, 'abc123',
                    'python-v1', '[]', 'config', 1, 10, 'graph', 'receipt-a', NULL
                )
                """
            )
    finally:
        conn.close()
