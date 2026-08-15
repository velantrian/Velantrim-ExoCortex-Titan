"""Bounded Code Structural Memory contracts and schema.

This package is Stage-B only and intentionally has no runtime wiring.
"""

from .contracts import (
    CONTRACT_VERSION,
    IDENTITY_SCHEMA_VERSION,
    RepositoryRegistration,
    RepositorySnapshot,
    ScanBudget,
    ScanOmission,
    ScanReceipt,
    SourceSpan,
    SourceState,
    StructuralEdge,
    StructuralNode,
    UnresolvedTarget,
    make_edge_id,
    make_node_id,
    normalize_qualified_name,
    normalize_relative_path,
    normalize_unresolved_target,
)
from .schema import (
    SCHEMA_VERSION,
    CSMDatabaseError,
    UnsupportedSchemaVersion,
    connect_database,
    initialize_schema,
    schema_version,
)

__all__ = [
    "CONTRACT_VERSION",
    "IDENTITY_SCHEMA_VERSION",
    "SCHEMA_VERSION",
    "CSMDatabaseError",
    "RepositoryRegistration",
    "RepositorySnapshot",
    "ScanBudget",
    "ScanOmission",
    "ScanReceipt",
    "SourceSpan",
    "SourceState",
    "StructuralEdge",
    "StructuralNode",
    "UnresolvedTarget",
    "UnsupportedSchemaVersion",
    "connect_database",
    "initialize_schema",
    "make_edge_id",
    "make_node_id",
    "normalize_qualified_name",
    "normalize_relative_path",
    "normalize_unresolved_target",
    "schema_version",
]
