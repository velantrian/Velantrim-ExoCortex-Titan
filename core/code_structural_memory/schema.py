"""Repository-scoped SQLite schema for Titan Code Structural Memory (CSM).

Stage B only: this module owns schema bootstrap/compatibility checks. It does not
scan repositories, expose query APIs, promote runtime state, or receive Canon,
Truth, Policy, TRACE, Audit, answer, action, or production authority.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from pathlib import Path


SCHEMA_VERSION = 1


class CSMDatabaseError(RuntimeError):
    """Base error for bounded CSM schema operations."""


class UnsupportedSchemaVersionError(CSMDatabaseError):
    """Raised when the database schema is outside the admitted compatibility set."""


_V1_STATEMENTS = (
    """
    CREATE TABLE csm_schema_meta (
        singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
        schema_version INTEGER NOT NULL CHECK (schema_version >= 1)
    )
    """,
    """
    CREATE TABLE csm_repositories (
        repository_id TEXT PRIMARY KEY,
        canonical_origin TEXT,
        local_root_fingerprint TEXT NOT NULL,
        registration_policy_id TEXT NOT NULL,
        tenant_or_project_scope TEXT NOT NULL,
        created_at TEXT NOT NULL,
        status TEXT NOT NULL,
        retention_policy_id TEXT
    )
    """,
    """
    CREATE TABLE csm_scan_receipts (
        repository_id TEXT NOT NULL,
        receipt_id TEXT NOT NULL,
        generation INTEGER NOT NULL CHECK (generation >= 1),
        previous_snapshot_id TEXT,
        candidate_snapshot_id TEXT NOT NULL,
        source_manifest_digest TEXT NOT NULL,
        source_dirty INTEGER NOT NULL CHECK (source_dirty IN (0, 1)),
        source_commit_sha TEXT,
        parser_profile_id TEXT NOT NULL,
        parser_versions_json TEXT NOT NULL,
        scan_config_digest TEXT NOT NULL,
        discovered_file_count INTEGER NOT NULL CHECK (discovered_file_count >= 0),
        discovered_byte_count INTEGER NOT NULL CHECK (discovered_byte_count >= 0),
        omitted_count INTEGER NOT NULL CHECK (omitted_count >= 0),
        omission_reason_counts_json TEXT NOT NULL,
        error_count INTEGER NOT NULL CHECK (error_count >= 0),
        error_reason_counts_json TEXT NOT NULL,
        structural_graph_digest TEXT NOT NULL,
        lease_cas_result TEXT NOT NULL,
        final_disposition TEXT NOT NULL,
        started_at TEXT NOT NULL,
        completed_at TEXT NOT NULL,
        no_runtime_authority INTEGER NOT NULL DEFAULT 1
            CHECK (no_runtime_authority = 1),
        PRIMARY KEY (repository_id, receipt_id),
        UNIQUE (repository_id, receipt_id, generation, candidate_snapshot_id),
        CHECK (source_dirty = 0 OR source_commit_sha IS NULL),
        FOREIGN KEY (repository_id)
            REFERENCES csm_repositories(repository_id)
            ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE csm_snapshots (
        repository_id TEXT NOT NULL,
        snapshot_id TEXT NOT NULL,
        generation INTEGER NOT NULL CHECK (generation >= 1),
        manifest_digest TEXT NOT NULL,
        dirty INTEGER NOT NULL CHECK (dirty IN (0, 1)),
        commit_sha TEXT,
        parser_profile_id TEXT NOT NULL,
        parser_versions_json TEXT NOT NULL,
        scan_config_digest TEXT NOT NULL,
        discovered_file_count INTEGER NOT NULL CHECK (discovered_file_count >= 0),
        discovered_byte_count INTEGER NOT NULL CHECK (discovered_byte_count >= 0),
        structural_graph_digest TEXT NOT NULL,
        scan_receipt_id TEXT NOT NULL,
        promoted_at TEXT,
        PRIMARY KEY (repository_id, snapshot_id),
        UNIQUE (repository_id, generation),
        UNIQUE (repository_id, snapshot_id, generation),
        CHECK (dirty = 0 OR commit_sha IS NULL),
        FOREIGN KEY (repository_id)
            REFERENCES csm_repositories(repository_id)
            ON DELETE CASCADE,
        FOREIGN KEY (
            repository_id,
            scan_receipt_id,
            generation,
            snapshot_id
        ) REFERENCES csm_scan_receipts(
            repository_id,
            receipt_id,
            generation,
            candidate_snapshot_id
        )
    )
    """,
    """
    CREATE TRIGGER csm_snapshot_receipt_source_state_guard
    BEFORE INSERT ON csm_snapshots
    FOR EACH ROW
    WHEN NOT EXISTS (
        SELECT 1
        FROM csm_scan_receipts AS receipt
        WHERE receipt.repository_id = NEW.repository_id
          AND receipt.receipt_id = NEW.scan_receipt_id
          AND receipt.generation = NEW.generation
          AND receipt.candidate_snapshot_id = NEW.snapshot_id
          AND receipt.source_manifest_digest = NEW.manifest_digest
          AND receipt.source_dirty = NEW.dirty
          AND receipt.source_commit_sha IS NEW.commit_sha
    )
    BEGIN
        SELECT RAISE(ABORT, 'snapshot source state must match scan receipt');
    END
    """,
    """
    CREATE TRIGGER csm_snapshot_record_immutable_except_promotion
    BEFORE UPDATE OF
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
        scan_receipt_id
    ON csm_snapshots
    FOR EACH ROW
    BEGIN
        SELECT RAISE(ABORT, 'snapshot record is immutable except promoted_at');
    END
    """,
    """
    CREATE TRIGGER csm_scan_receipt_immutable
    BEFORE UPDATE ON csm_scan_receipts
    FOR EACH ROW
    BEGIN
        SELECT RAISE(ABORT, 'scan receipt is immutable');
    END
    """,
    """
    CREATE TABLE csm_nodes (
        repository_id TEXT NOT NULL,
        snapshot_id TEXT NOT NULL,
        node_id TEXT NOT NULL,
        generation INTEGER NOT NULL CHECK (generation >= 1),
        node_kind TEXT NOT NULL,
        relative_path TEXT NOT NULL,
        qualified_name TEXT NOT NULL,
        start_byte INTEGER NOT NULL CHECK (start_byte >= 0),
        end_byte INTEGER NOT NULL CHECK (end_byte >= start_byte),
        parser_profile_id TEXT NOT NULL,
        parser_adapter_id TEXT NOT NULL,
        PRIMARY KEY (repository_id, snapshot_id, node_id),
        UNIQUE (repository_id, snapshot_id, node_id, generation),
        FOREIGN KEY (repository_id, snapshot_id, generation)
            REFERENCES csm_snapshots(repository_id, snapshot_id, generation)
            ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE csm_unresolved_targets (
        repository_id TEXT NOT NULL,
        snapshot_id TEXT NOT NULL,
        unresolved_target_id TEXT NOT NULL,
        target_kind TEXT NOT NULL,
        normalized_target TEXT NOT NULL,
        PRIMARY KEY (repository_id, snapshot_id, unresolved_target_id),
        UNIQUE (repository_id, snapshot_id, target_kind, normalized_target),
        FOREIGN KEY (repository_id, snapshot_id)
            REFERENCES csm_snapshots(repository_id, snapshot_id)
            ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE csm_edges (
        repository_id TEXT NOT NULL,
        snapshot_id TEXT NOT NULL,
        edge_id TEXT NOT NULL,
        generation INTEGER NOT NULL CHECK (generation >= 1),
        edge_kind TEXT NOT NULL,
        source_node_id TEXT NOT NULL,
        target_node_id TEXT,
        unresolved_target_id TEXT,
        source_start_byte INTEGER NOT NULL CHECK (source_start_byte >= 0),
        source_end_byte INTEGER NOT NULL CHECK (source_end_byte >= source_start_byte),
        parser_adapter_id TEXT NOT NULL,
        resolution_rule TEXT NOT NULL,
        PRIMARY KEY (repository_id, snapshot_id, edge_id),
        CHECK (
            (target_node_id IS NOT NULL AND unresolved_target_id IS NULL)
            OR
            (target_node_id IS NULL AND unresolved_target_id IS NOT NULL)
        ),
        FOREIGN KEY (repository_id, snapshot_id, generation)
            REFERENCES csm_snapshots(repository_id, snapshot_id, generation)
            ON DELETE CASCADE,
        FOREIGN KEY (repository_id, snapshot_id, source_node_id, generation)
            REFERENCES csm_nodes(repository_id, snapshot_id, node_id, generation)
            ON DELETE CASCADE,
        FOREIGN KEY (repository_id, snapshot_id, target_node_id, generation)
            REFERENCES csm_nodes(repository_id, snapshot_id, node_id, generation)
            ON DELETE CASCADE,
        FOREIGN KEY (repository_id, snapshot_id, unresolved_target_id)
            REFERENCES csm_unresolved_targets(
                repository_id,
                snapshot_id,
                unresolved_target_id
            )
            ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE csm_scan_omissions (
        repository_id TEXT NOT NULL,
        snapshot_id TEXT NOT NULL,
        omission_id TEXT NOT NULL,
        relative_path TEXT NOT NULL,
        reason TEXT NOT NULL,
        observed_bytes INTEGER CHECK (observed_bytes IS NULL OR observed_bytes >= 0),
        PRIMARY KEY (repository_id, snapshot_id, omission_id),
        FOREIGN KEY (repository_id, snapshot_id)
            REFERENCES csm_snapshots(repository_id, snapshot_id)
            ON DELETE CASCADE
    )
    """,
    """
    CREATE INDEX idx_csm_nodes_qualified_name
        ON csm_nodes(repository_id, snapshot_id, qualified_name)
    """,
    """
    CREATE INDEX idx_csm_nodes_relative_path
        ON csm_nodes(repository_id, snapshot_id, relative_path)
    """,
    """
    CREATE INDEX idx_csm_edges_source
        ON csm_edges(repository_id, snapshot_id, source_node_id, edge_kind)
    """,
    """
    CREATE INDEX idx_csm_edges_target
        ON csm_edges(repository_id, snapshot_id, target_node_id, edge_kind)
    """,
    """
    CREATE INDEX idx_csm_receipts_generation
        ON csm_scan_receipts(repository_id, generation)
    """,
)


def connect_database(path: str | Path) -> sqlite3.Connection:
    """Open a CSM SQLite database with fail-closed foreign-key enforcement."""
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    row = conn.execute("PRAGMA foreign_keys").fetchone()
    if row is None or int(row[0]) != 1:
        conn.close()
        raise CSMDatabaseError("SQLite foreign-key enforcement could not be enabled")
    return conn


def schema_version(conn: sqlite3.Connection) -> int:
    """Return the admitted schema version, checking both SQLite and table metadata."""
    pragma_row = conn.execute("PRAGMA user_version").fetchone()
    pragma_version = 0 if pragma_row is None else int(pragma_row[0])

    meta_exists = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='csm_schema_meta'"
    ).fetchone()
    if meta_exists is None:
        if pragma_version != 0:
            raise CSMDatabaseError(
                "CSM schema metadata is missing while PRAGMA user_version is nonzero"
            )
        return 0

    meta_row = conn.execute(
        "SELECT schema_version FROM csm_schema_meta WHERE singleton = 1"
    ).fetchone()
    if meta_row is None:
        raise CSMDatabaseError("CSM schema metadata row is missing")
    meta_version = int(meta_row[0])
    if meta_version != pragma_version:
        raise CSMDatabaseError(
            "CSM schema metadata disagrees with PRAGMA user_version"
        )
    return meta_version


def _apply_statements_transactionally(
    conn: sqlite3.Connection,
    *,
    statements: Iterable[str],
    target_version: int,
) -> None:
    """Apply one bounded migration atomically; rollback on every failure."""
    try:
        conn.execute("BEGIN IMMEDIATE")
        for statement in statements:
            conn.execute(statement)
        conn.execute(
            "INSERT INTO csm_schema_meta(singleton, schema_version) VALUES (1, ?)",
            (target_version,),
        )
        conn.execute(f"PRAGMA user_version = {target_version}")
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def initialize_schema(conn: sqlite3.Connection) -> int:
    """Bootstrap or validate the currently admitted CSM schema.

    Stage B admits only an empty database -> v1 transition. Unknown older or
    newer nonzero versions fail closed until a separately reviewed migration is
    added.
    """
    current = schema_version(conn)
    if current == SCHEMA_VERSION:
        return current
    if current > SCHEMA_VERSION:
        raise UnsupportedSchemaVersionError(
            f"database schema v{current} is newer than supported v{SCHEMA_VERSION}"
        )
    if current != 0:
        raise UnsupportedSchemaVersionError(
            f"no admitted migration path from schema v{current} to v{SCHEMA_VERSION}"
        )

    _apply_statements_transactionally(
        conn,
        statements=_V1_STATEMENTS,
        target_version=SCHEMA_VERSION,
    )
    return schema_version(conn)
