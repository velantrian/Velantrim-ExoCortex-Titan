"""Immutable value contracts for Titan Code Structural Memory (CSM).

This module is intentionally pure and runtime-unwired. It defines only bounded
structural-memory value objects and deterministic identity helpers.

INDEXED != UNDERSTOOD != CORRECT != SAFE != CANONICAL.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import PurePosixPath, PureWindowsPath
from typing import Iterable


CONTRACT_VERSION = "csm-contract-v1"
IDENTITY_SCHEMA_VERSION = "csm-identity-v1"
SNAPSHOT_IDENTITY_VERSION = "csm-snapshot-identity-v1"


def _require_text(value: str, field_name: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError(f"{field_name} must be non-empty")
    if "\x00" in value:
        raise ValueError(f"{field_name} must not contain NUL")
    return value


def normalize_relative_path(value: str) -> str:
    """Return a portable repository-relative POSIX path or fail closed."""
    raw = _require_text(value, "relative_path").replace("\\", "/")
    if PureWindowsPath(raw).drive:
        raise ValueError("relative_path must not be drive-qualified")
    path = PurePosixPath(raw)
    if path.is_absolute():
        raise ValueError("relative_path must not be absolute")
    parts: list[str] = []
    for part in path.parts:
        if part in ("", "."):
            continue
        if part == "..":
            raise ValueError("relative_path must not escape the repository root")
        parts.append(part)
    if not parts:
        raise ValueError("relative_path must identify a repository entry")
    return "/".join(parts)


def normalize_qualified_name(value: str) -> str:
    return _require_text(value, "qualified_name")


def normalize_unresolved_target(value: str) -> str:
    return _require_text(value, "normalized_target")


def _canonical_digest(parts: Iterable[object]) -> str:
    encoded = json.dumps(
        list(parts),
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _normalize_parser_versions(
    parser_versions: Iterable[tuple[str, str]],
) -> tuple[tuple[str, str], ...]:
    return tuple(
        sorted(
            (
                _require_text(name, "parser_name"),
                _require_text(version, "parser_version"),
            )
            for name, version in parser_versions
        )
    )


def _normalize_reason_counts(
    reason_counts: Iterable[tuple[str, int]],
    field_name: str,
) -> tuple[tuple[str, int], ...]:
    normalized: list[tuple[str, int]] = []
    seen: set[str] = set()
    for reason, count in reason_counts:
        reason = _require_text(reason, f"{field_name}.reason")
        if reason in seen:
            raise ValueError(f"{field_name} must not contain duplicate reasons")
        if isinstance(count, bool) or not isinstance(count, int) or count <= 0:
            raise ValueError(f"{field_name} counts must be positive integers")
        seen.add(reason)
        normalized.append((reason, count))
    return tuple(sorted(normalized))


def serialize_reason_counts(reason_counts: Iterable[tuple[str, int]]) -> str:
    """Serialize reason accounting deterministically for bounded persistence."""
    normalized = _normalize_reason_counts(reason_counts, "reason_counts")
    return json.dumps(normalized, ensure_ascii=False, separators=(",", ":"))


def make_node_id(
    *,
    repository_id: str,
    node_kind: str,
    relative_path: str,
    qualified_name: str,
) -> str:
    """Create the accepted stable node identity.

    Snapshot, timestamps and source line numbers are intentionally excluded.
    """
    return _canonical_digest(
        (
            IDENTITY_SCHEMA_VERSION,
            _require_text(repository_id, "repository_id"),
            _require_text(node_kind, "node_kind"),
            normalize_relative_path(relative_path),
            normalize_qualified_name(qualified_name),
        )
    )


def make_edge_id(
    *,
    repository_id: str,
    edge_kind: str,
    source_node_id: str,
    target_node_id: str | None = None,
    unresolved_target: str | None = None,
) -> str:
    """Create a directed structural edge identity.

    Exactly one resolved target node or normalized unresolved target is required.
    """
    if (target_node_id is None) == (unresolved_target is None):
        raise ValueError(
            "exactly one of target_node_id or unresolved_target must be provided"
        )
    target = (
        _require_text(target_node_id, "target_node_id")
        if target_node_id is not None
        else normalize_unresolved_target(unresolved_target or "")
    )
    return _canonical_digest(
        (
            IDENTITY_SCHEMA_VERSION,
            _require_text(repository_id, "repository_id"),
            _require_text(edge_kind, "edge_kind"),
            _require_text(source_node_id, "source_node_id"),
            target,
        )
    )


@dataclass(frozen=True, slots=True)
class SourceState:
    manifest_digest: str
    dirty: bool
    commit_sha: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "manifest_digest",
            _require_text(self.manifest_digest, "manifest_digest"),
        )
        if not isinstance(self.dirty, bool):
            raise TypeError("dirty must be a bool")
        if self.commit_sha is not None:
            object.__setattr__(
                self,
                "commit_sha",
                _require_text(self.commit_sha, "commit_sha"),
            )
        if self.dirty and self.commit_sha is not None:
            raise ValueError(
                "dirty source state must not claim exact clean-commit identity"
            )


def make_snapshot_id(
    *,
    repository_id: str,
    source_state: SourceState,
    parser_profile_id: str,
    parser_versions: Iterable[tuple[str, str]],
    scan_config_digest: str,
    structural_graph_digest: str,
) -> str:
    """Create the semantic/content identity of one repository snapshot.

    Generation, receipt/lease identity and wall-clock metadata are custody data,
    not semantic content, and are intentionally excluded.
    """
    if not isinstance(source_state, SourceState):
        raise TypeError("source_state must be a SourceState")
    normalized_versions = _normalize_parser_versions(parser_versions)
    return _canonical_digest(
        (
            SNAPSHOT_IDENTITY_VERSION,
            _require_text(repository_id, "repository_id"),
            (
                source_state.manifest_digest,
                source_state.dirty,
                source_state.commit_sha,
            ),
            _require_text(parser_profile_id, "parser_profile_id"),
            normalized_versions,
            _require_text(scan_config_digest, "scan_config_digest"),
            _require_text(structural_graph_digest, "structural_graph_digest"),
        )
    )


@dataclass(frozen=True, slots=True)
class RepositoryRegistration:
    repository_id: str
    local_root_fingerprint: str
    registration_policy_id: str
    tenant_or_project_scope: str
    created_at: str
    canonical_origin: str | None = None
    status: str = "ACTIVE"
    retention_policy_id: str | None = None

    def __post_init__(self) -> None:
        for field_name in (
            "repository_id",
            "local_root_fingerprint",
            "registration_policy_id",
            "tenant_or_project_scope",
            "created_at",
            "status",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_text(getattr(self, field_name), field_name),
            )
        if self.canonical_origin is not None:
            object.__setattr__(
                self,
                "canonical_origin",
                _require_text(self.canonical_origin, "canonical_origin"),
            )
        if self.retention_policy_id is not None:
            object.__setattr__(
                self,
                "retention_policy_id",
                _require_text(self.retention_policy_id, "retention_policy_id"),
            )


@dataclass(frozen=True, slots=True)
class RepositorySnapshot:
    snapshot_id: str
    repository_id: str
    generation: int
    source_state: SourceState
    parser_profile_id: str
    parser_versions: tuple[tuple[str, str], ...]
    scan_config_digest: str
    discovered_file_count: int
    discovered_byte_count: int
    structural_graph_digest: str
    scan_receipt_id: str
    promoted_at: str | None = None

    def __post_init__(self) -> None:
        for field_name in (
            "snapshot_id",
            "repository_id",
            "parser_profile_id",
            "scan_config_digest",
            "structural_graph_digest",
            "scan_receipt_id",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_text(getattr(self, field_name), field_name),
            )
        if not isinstance(self.source_state, SourceState):
            raise TypeError("source_state must be a SourceState")
        if self.generation < 1:
            raise ValueError("generation must be >= 1")
        if self.discovered_file_count < 0 or self.discovered_byte_count < 0:
            raise ValueError("discovered counts must be non-negative")
        normalized_versions = _normalize_parser_versions(self.parser_versions)
        object.__setattr__(self, "parser_versions", normalized_versions)
        expected = make_snapshot_id(
            repository_id=self.repository_id,
            source_state=self.source_state,
            parser_profile_id=self.parser_profile_id,
            parser_versions=normalized_versions,
            scan_config_digest=self.scan_config_digest,
            structural_graph_digest=self.structural_graph_digest,
        )
        if self.snapshot_id != expected:
            raise ValueError(
                "snapshot_id does not match the content-addressed identity contract"
            )
        if self.promoted_at is not None:
            object.__setattr__(
                self,
                "promoted_at",
                _require_text(self.promoted_at, "promoted_at"),
            )


@dataclass(frozen=True, slots=True)
class SourceSpan:
    start_byte: int
    end_byte: int

    def __post_init__(self) -> None:
        if self.start_byte < 0 or self.end_byte < self.start_byte:
            raise ValueError("source span must be ordered and non-negative")


@dataclass(frozen=True, slots=True)
class StructuralNode:
    node_id: str
    repository_id: str
    snapshot_id: str
    generation: int
    node_kind: str
    relative_path: str
    qualified_name: str
    source_span: SourceSpan
    parser_profile_id: str
    parser_adapter_id: str

    def __post_init__(self) -> None:
        for field_name in (
            "node_id",
            "repository_id",
            "snapshot_id",
            "node_kind",
            "parser_profile_id",
            "parser_adapter_id",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_text(getattr(self, field_name), field_name),
            )
        if self.generation < 1:
            raise ValueError("generation must be >= 1")
        object.__setattr__(
            self,
            "relative_path",
            normalize_relative_path(self.relative_path),
        )
        object.__setattr__(
            self,
            "qualified_name",
            normalize_qualified_name(self.qualified_name),
        )
        expected = make_node_id(
            repository_id=self.repository_id,
            node_kind=self.node_kind,
            relative_path=self.relative_path,
            qualified_name=self.qualified_name,
        )
        if self.node_id != expected:
            raise ValueError("node_id does not match the deterministic identity contract")


@dataclass(frozen=True, slots=True)
class UnresolvedTarget:
    target_kind: str
    normalized_target: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "target_kind",
            _require_text(self.target_kind, "target_kind"),
        )
        object.__setattr__(
            self,
            "normalized_target",
            normalize_unresolved_target(self.normalized_target),
        )


@dataclass(frozen=True, slots=True)
class StructuralEdge:
    edge_id: str
    repository_id: str
    snapshot_id: str
    generation: int
    edge_kind: str
    source_node_id: str
    source_span: SourceSpan
    parser_adapter_id: str
    resolution_rule: str
    target_node_id: str | None = None
    unresolved_target: UnresolvedTarget | None = None

    def __post_init__(self) -> None:
        for field_name in (
            "edge_id",
            "repository_id",
            "snapshot_id",
            "edge_kind",
            "source_node_id",
            "parser_adapter_id",
            "resolution_rule",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_text(getattr(self, field_name), field_name),
            )
        if self.generation < 1:
            raise ValueError("generation must be >= 1")
        if (self.target_node_id is None) == (self.unresolved_target is None):
            raise ValueError(
                "edge must have exactly one resolved or unresolved target"
            )
        if self.target_node_id is not None:
            object.__setattr__(
                self,
                "target_node_id",
                _require_text(self.target_node_id, "target_node_id"),
            )
        expected = make_edge_id(
            repository_id=self.repository_id,
            edge_kind=self.edge_kind,
            source_node_id=self.source_node_id,
            target_node_id=self.target_node_id,
            unresolved_target=(
                self.unresolved_target.normalized_target
                if self.unresolved_target is not None
                else None
            ),
        )
        if self.edge_id != expected:
            raise ValueError("edge_id does not match the deterministic identity contract")


@dataclass(frozen=True, slots=True)
class ScanBudget:
    max_files: int
    max_file_bytes: int
    max_total_bytes: int
    max_path_depth: int
    max_scan_seconds: float

    def __post_init__(self) -> None:
        values = (
            self.max_files,
            self.max_file_bytes,
            self.max_total_bytes,
            self.max_path_depth,
            self.max_scan_seconds,
        )
        if any(value <= 0 for value in values):
            raise ValueError("all scan budget values must be positive")
        if self.max_file_bytes > self.max_total_bytes:
            raise ValueError("max_file_bytes must not exceed max_total_bytes")


@dataclass(frozen=True, slots=True)
class ScanOmission:
    omission_id: str
    repository_id: str
    snapshot_id: str
    relative_path: str
    reason: str
    observed_bytes: int | None = None

    def __post_init__(self) -> None:
        for field_name in ("omission_id", "repository_id", "snapshot_id", "reason"):
            object.__setattr__(
                self,
                field_name,
                _require_text(getattr(self, field_name), field_name),
            )
        object.__setattr__(
            self,
            "relative_path",
            normalize_relative_path(self.relative_path),
        )
        if self.observed_bytes is not None and self.observed_bytes < 0:
            raise ValueError("observed_bytes must be non-negative")


@dataclass(frozen=True, slots=True)
class ScanReceipt:
    receipt_id: str
    repository_id: str
    generation: int
    candidate_snapshot_id: str
    source_state: SourceState
    parser_profile_id: str
    parser_versions: tuple[tuple[str, str], ...]
    scan_config_digest: str
    discovered_file_count: int
    discovered_byte_count: int
    omitted_count: int
    omission_reason_counts: tuple[tuple[str, int], ...]
    error_count: int
    error_reason_counts: tuple[tuple[str, int], ...]
    structural_graph_digest: str
    lease_cas_result: str
    final_disposition: str
    started_at: str
    completed_at: str
    previous_snapshot_id: str | None = None
    no_runtime_authority: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "receipt_id",
            "repository_id",
            "candidate_snapshot_id",
            "parser_profile_id",
            "scan_config_digest",
            "structural_graph_digest",
            "lease_cas_result",
            "final_disposition",
            "started_at",
            "completed_at",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_text(getattr(self, field_name), field_name),
            )
        if not isinstance(self.source_state, SourceState):
            raise TypeError("source_state must be a SourceState")
        if self.previous_snapshot_id is not None:
            object.__setattr__(
                self,
                "previous_snapshot_id",
                _require_text(self.previous_snapshot_id, "previous_snapshot_id"),
            )
        if self.generation < 1:
            raise ValueError("generation must be >= 1")
        for name in (
            "discovered_file_count",
            "discovered_byte_count",
            "omitted_count",
            "error_count",
        ):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} must be non-negative")
        normalized_versions = _normalize_parser_versions(self.parser_versions)
        object.__setattr__(self, "parser_versions", normalized_versions)

        omission_counts = _normalize_reason_counts(
            self.omission_reason_counts,
            "omission_reason_counts",
        )
        error_counts = _normalize_reason_counts(
            self.error_reason_counts,
            "error_reason_counts",
        )
        if sum(count for _, count in omission_counts) != self.omitted_count:
            raise ValueError("omission reason counts must sum to omitted_count")
        if sum(count for _, count in error_counts) != self.error_count:
            raise ValueError("error reason counts must sum to error_count")
        object.__setattr__(self, "omission_reason_counts", omission_counts)
        object.__setattr__(self, "error_reason_counts", error_counts)

        expected_snapshot_id = make_snapshot_id(
            repository_id=self.repository_id,
            source_state=self.source_state,
            parser_profile_id=self.parser_profile_id,
            parser_versions=normalized_versions,
            scan_config_digest=self.scan_config_digest,
            structural_graph_digest=self.structural_graph_digest,
        )
        if self.candidate_snapshot_id != expected_snapshot_id:
            raise ValueError(
                "candidate_snapshot_id does not match receipt snapshot identity inputs"
            )
        if self.no_runtime_authority is not True:
            raise ValueError("CSM scan receipts cannot claim runtime authority")
