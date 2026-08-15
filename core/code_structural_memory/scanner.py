"""Explicit, bounded Python scanner for Titan Code Structural Memory (CSM).

Stage C only. This module is intentionally default-off and runtime-unwired. The
caller must explicitly register a repository root and explicitly provide the
repository-relative Python paths to scan. Repository code is never imported or
executed, no shell command is run, and scan output remains a rebuildable,
non-canonical structural projection.

INDEXED != UNDERSTOOD != CORRECT != SAFE != CANONICAL.
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import secrets
import sqlite3
import sys
import time
from collections import Counter
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .contracts import (
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
    make_snapshot_id,
    normalize_relative_path,
    serialize_reason_counts,
)
from .schema import initialize_schema


SCANNER_CONTRACT_VERSION = "csm-python-scanner-v1"
PARSER_PROFILE_ID = "python-stdlib-ast-v1"
PARSER_ADAPTER_ID = "python-stdlib-ast-v1"
SUPPORTED_EXTENSION = ".py"
DEFAULT_LEASE_TTL_SECONDS = 60.0


class CSMScannerError(RuntimeError):
    """Base error for bounded Stage-C scanner operations."""


class RepositoryRegistrationError(CSMScannerError):
    """Raised when a repository registration/root binding is absent or drifts."""


class ScanLeaseBusyError(CSMScannerError):
    """Raised when another non-expired scanner owns the repository lease."""


class ScanLeaseLostError(CSMScannerError):
    """Raised when a scanner no longer owns the generation/lease it started with."""


@dataclass(frozen=True, slots=True)
class ScanLease:
    repository_id: str
    holder_token: str
    generation: int
    issued_at: float
    expires_at: float
    recovered_expired_lease: bool = False


@dataclass(frozen=True, slots=True)
class ScanOutcome:
    repository_id: str
    generation: int
    receipt_id: str
    snapshot_id: str
    structural_graph_digest: str
    final_disposition: str
    promoted: bool
    reused_snapshot: bool
    source_state: SourceState
    discovered_file_count: int
    discovered_byte_count: int
    problems: tuple[ScanOmission, ...]
    omission_reason_counts: tuple[tuple[str, int], ...]
    error_reason_counts: tuple[tuple[str, int], ...]


@dataclass(frozen=True, slots=True)
class _NodeDraft:
    node_kind: str
    relative_path: str
    qualified_name: str
    source_span: SourceSpan

    def node_id(self, repository_id: str) -> str:
        return make_node_id(
            repository_id=repository_id,
            node_kind=self.node_kind,
            relative_path=self.relative_path,
            qualified_name=self.qualified_name,
        )


@dataclass(frozen=True, slots=True)
class _EdgeDraft:
    edge_kind: str
    source_node_id: str
    source_span: SourceSpan
    resolution_rule: str
    target_node_id: str | None = None
    unresolved_target: UnresolvedTarget | None = None

    def edge_id(self, repository_id: str) -> str:
        return make_edge_id(
            repository_id=repository_id,
            edge_kind=self.edge_kind,
            source_node_id=self.source_node_id,
            target_node_id=self.target_node_id,
            unresolved_target=(
                self.unresolved_target.normalized_target
                if self.unresolved_target is not None
                else None
            ),
        )


@dataclass(frozen=True, slots=True)
class _ParsedFile:
    relative_path: str
    size_bytes: int
    content_digest: str
    nodes: tuple[_NodeDraft, ...]
    edges: tuple[_EdgeDraft, ...]


@dataclass(frozen=True, slots=True)
class _ObservedProblem:
    relative_path: str
    reason: str
    observed_bytes: int | None
    is_error: bool


@dataclass(frozen=True, slots=True)
class _ScanCandidate:
    source_state: SourceState
    parser_versions: tuple[tuple[str, str], ...]
    scan_config_digest: str
    structural_graph_digest: str
    snapshot_id: str
    discovered_file_count: int
    discovered_byte_count: int
    nodes: tuple[StructuralNode, ...]
    edges: tuple[StructuralEdge, ...]
    problems: tuple[_ObservedProblem, ...]
    omissions: tuple[ScanOmission, ...]
    omission_reason_counts: tuple[tuple[str, int], ...]
    error_reason_counts: tuple[tuple[str, int], ...]


@dataclass(frozen=True, slots=True)
class _Scope:
    node_id: str
    qualified_name: str
    node_kind: str


def _require_idle_connection(conn: sqlite3.Connection) -> None:
    if conn.in_transaction:
        raise CSMScannerError(
            "CSM scanner operations require a connection with no active transaction"
        )


def _require_positive_seconds(value: float, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
        raise ValueError(f"{field_name} must be a positive number")
    return float(value)


def _canonical_digest(value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _utc_iso(epoch_seconds: float) -> str:
    return (
        datetime.fromtimestamp(epoch_seconds, tz=timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def _default_token_factory() -> str:
    return secrets.token_hex(16)


def _db_bool(value: object) -> bool:
    if value in (0, False):
        return False
    if value in (1, True):
        return True
    raise CSMScannerError(f"invalid SQLite boolean value: {value!r}")


def local_root_fingerprint(root: str | Path) -> str:
    """Return a local-only root binding fingerprint without persisting the path."""
    resolved = Path(root).expanduser().resolve(strict=True)
    if not resolved.is_dir():
        raise RepositoryRegistrationError("registered CSM root must be a directory")
    payload = os.fsencode(str(resolved))
    return hashlib.sha256(b"csm-local-root-v1\x00" + payload).hexdigest()


def resolve_repository_root(root: str | Path) -> Path:
    """Resolve and validate one caller-supplied repository root."""
    resolved = Path(root).expanduser().resolve(strict=True)
    if not resolved.is_dir():
        raise RepositoryRegistrationError("CSM repository root must be a directory")
    return resolved


def _fetch_repository(conn: sqlite3.Connection, repository_id: str) -> sqlite3.Row:
    row = conn.execute(
        "SELECT * FROM csm_repositories WHERE repository_id = ?",
        (repository_id,),
    ).fetchone()
    if row is None:
        raise RepositoryRegistrationError(
            f"CSM repository is not registered: {repository_id}"
        )
    return row


def _registration_from_row(row: sqlite3.Row) -> RepositoryRegistration:
    return RepositoryRegistration(
        repository_id=row["repository_id"],
        local_root_fingerprint=row["local_root_fingerprint"],
        canonical_origin=row["canonical_origin"],
        registration_policy_id=row["registration_policy_id"],
        tenant_or_project_scope=row["tenant_or_project_scope"],
        created_at=row["created_at"],
        status=row["status"],
        retention_policy_id=row["retention_policy_id"],
    )


def _require_registered_root(
    conn: sqlite3.Connection,
    *,
    repository_id: str,
    root: str | Path,
) -> tuple[RepositoryRegistration, Path]:
    registration = _registration_from_row(_fetch_repository(conn, repository_id))
    if registration.status != "ACTIVE":
        raise RepositoryRegistrationError(
            f"CSM repository is not active: {repository_id}"
        )
    resolved_root = resolve_repository_root(root)
    observed_fingerprint = local_root_fingerprint(resolved_root)
    if observed_fingerprint != registration.local_root_fingerprint:
        raise RepositoryRegistrationError(
            "CSM repository root does not match registered local root fingerprint"
        )
    return registration, resolved_root


def register_repository(
    conn: sqlite3.Connection,
    *,
    registration: RepositoryRegistration,
    root: str | Path,
) -> None:
    """Register exactly one repository/root binding for explicit Stage-C scans."""
    initialize_schema(conn)
    _require_idle_connection(conn)
    resolved_root = resolve_repository_root(root)
    observed_fingerprint = local_root_fingerprint(resolved_root)
    if registration.local_root_fingerprint != observed_fingerprint:
        raise RepositoryRegistrationError(
            "registration local_root_fingerprint does not match caller root"
        )
    existing = conn.execute(
        "SELECT * FROM csm_repositories WHERE repository_id = ?",
        (registration.repository_id,),
    ).fetchone()
    if existing is not None:
        if _registration_from_row(existing) != registration:
            raise RepositoryRegistrationError(
                "repository registration is immutable once persisted"
            )
        state = conn.execute(
            "SELECT repository_id FROM csm_repository_scan_state WHERE repository_id = ?",
            (registration.repository_id,),
        ).fetchone()
        if state is None:
            raise RepositoryRegistrationError(
                "repository registration exists without Stage-C scan state"
            )
        return
    try:
        conn.execute("BEGIN IMMEDIATE")
        conn.execute(
            """
            INSERT INTO csm_repositories(
                repository_id,
                local_root_fingerprint,
                canonical_origin,
                registration_policy_id,
                tenant_or_project_scope,
                created_at,
                status,
                retention_policy_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                registration.repository_id,
                registration.local_root_fingerprint,
                registration.canonical_origin,
                registration.registration_policy_id,
                registration.tenant_or_project_scope,
                registration.created_at,
                registration.status,
                registration.retention_policy_id,
            ),
        )
        conn.execute(
            """
            INSERT INTO csm_repository_scan_state(
                repository_id,
                next_generation,
                current_snapshot_id,
                current_scan_generation,
                current_scan_receipt_id,
                lease_token,
                lease_generation,
                lease_issued_at,
                lease_expires_at
            ) VALUES (?, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
            """,
            (registration.repository_id,),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def _lease_event(
    conn: sqlite3.Connection,
    *,
    repository_id: str,
    generation: int,
    lease_token: str,
    event_type: str,
    observed_at: float,
    recovered_from_generation: int | None = None,
) -> None:
    conn.execute(
        """
        INSERT INTO csm_scan_lease_events(
            event_id,
            repository_id,
            generation,
            lease_token,
            event_type,
            observed_at,
            recovered_from_generation
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            _canonical_digest(
                (
                    "csm-lease-event-v1",
                    repository_id,
                    generation,
                    lease_token,
                    event_type,
                    observed_at,
                    recovered_from_generation,
                )
            ),
            repository_id,
            generation,
            lease_token,
            event_type,
            observed_at,
            recovered_from_generation,
        ),
    )


def _acquire_scan_lease(
    conn: sqlite3.Connection,
    *,
    repository_id: str,
    now: float,
    lease_ttl_seconds: float,
    holder_token: str,
) -> ScanLease:
    lease_ttl_seconds = _require_positive_seconds(
        lease_ttl_seconds,
        "lease_ttl_seconds",
    )
    try:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT * FROM csm_repository_scan_state WHERE repository_id = ?",
            (repository_id,),
        ).fetchone()
        if row is None:
            raise RepositoryRegistrationError(
                f"missing CSM scan state for repository: {repository_id}"
            )
        existing_token = row["lease_token"]
        existing_generation = row["lease_generation"]
        existing_expires = row["lease_expires_at"]
        recovered = False
        recovered_from_generation: int | None = None
        if existing_token is not None:
            if existing_expires is None or float(existing_expires) > now:
                raise ScanLeaseBusyError(
                    f"repository scan lease is already held: {repository_id}"
                )
            recovered = True
            recovered_from_generation = (
                None
                if existing_generation is None
                else int(existing_generation)
            )

        generation = int(row["next_generation"])
        expires_at = now + lease_ttl_seconds
        updated = conn.execute(
            """
            UPDATE csm_repository_scan_state
            SET next_generation = ?,
                lease_token = ?,
                lease_generation = ?,
                lease_issued_at = ?,
                lease_expires_at = ?
            WHERE repository_id = ?
              AND next_generation = ?
              AND (
                    lease_token IS NULL
                    OR lease_expires_at <= ?
              )
            """,
            (
                generation + 1,
                holder_token,
                generation,
                now,
                expires_at,
                repository_id,
                generation,
                now,
            ),
        ).rowcount
        if updated != 1:
            raise ScanLeaseBusyError(
                f"repository scan lease acquisition raced: {repository_id}"
            )
        _lease_event(
            conn,
            repository_id=repository_id,
            generation=generation,
            lease_token=holder_token,
            event_type="RECOVERED" if recovered else "ACQUIRED",
            observed_at=now,
            recovered_from_generation=recovered_from_generation,
        )
        conn.commit()
        return ScanLease(
            repository_id=repository_id,
            holder_token=holder_token,
            generation=generation,
            issued_at=now,
            expires_at=expires_at,
            recovered_expired_lease=recovered,
        )
    except Exception:
        conn.rollback()
        raise


def _release_scan_lease_best_effort(
    conn: sqlite3.Connection,
    *,
    lease: ScanLease,
    now: float,
) -> None:
    if conn.in_transaction:
        conn.rollback()
    try:
        conn.execute("BEGIN IMMEDIATE")
        cleared = conn.execute(
            """
            UPDATE csm_repository_scan_state
            SET lease_token = NULL,
                lease_generation = NULL,
                lease_issued_at = NULL,
                lease_expires_at = NULL
            WHERE repository_id = ?
              AND lease_token = ?
              AND lease_generation = ?
            """,
            (
                lease.repository_id,
                lease.holder_token,
                lease.generation,
            ),
        ).rowcount
        if cleared == 1:
            _lease_event(
                conn,
                repository_id=lease.repository_id,
                generation=lease.generation,
                lease_token=lease.holder_token,
                event_type="RELEASED_AFTER_FAILURE",
                observed_at=now,
            )
        conn.commit()
    except Exception:
        conn.rollback()


def _path_has_symlink_component(root: Path, relative_path: str) -> bool:
    current = root
    for component in relative_path.split("/"):
        current = current / component
        try:
            if current.is_symlink():
                return True
        except OSError:
            return True
    return False


def _scan_config_digest(budget: ScanBudget) -> str:
    return _canonical_digest(
        (
            SCANNER_CONTRACT_VERSION,
            PARSER_PROFILE_ID,
            PARSER_ADAPTER_ID,
            budget.max_files,
            budget.max_file_bytes,
            budget.max_total_bytes,
            budget.max_path_depth,
            budget.max_scan_seconds,
        )
    )


def _source_span(node: ast.AST) -> SourceSpan:
    start = int(getattr(node, "lineno", 0) or 0)
    end = int(getattr(node, "end_lineno", start) or start)
    return SourceSpan(start_byte=max(start, 0), end_byte=max(end, start, 0))


def _module_node(repository_id: str, relative_path: str) -> _NodeDraft:
    return _NodeDraft(
        node_kind="MODULE",
        relative_path=relative_path,
        qualified_name=relative_path,
        source_span=SourceSpan(start_byte=0, end_byte=0),
    )


def _qualified(parent: _Scope, name: str) -> str:
    if parent.node_kind == "MODULE":
        return name
    return f"{parent.qualified_name}.{name}"


def _parse_python_file(
    *,
    repository_id: str,
    relative_path: str,
    raw: bytes,
) -> tuple[tuple[_NodeDraft, ...], tuple[_EdgeDraft, ...]]:
    text = raw.decode("utf-8", errors="strict")
    tree = ast.parse(text, filename=relative_path, mode="exec", type_comments=True)
    module = _module_node(repository_id, relative_path)
    nodes: list[_NodeDraft] = [module]
    edges: list[_EdgeDraft] = []
    module_id = module.node_id(repository_id)

    def visit_body(body: Sequence[ast.stmt], parent: _Scope) -> None:
        for statement in body:
            if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
                node_kind = "METHOD" if parent.node_kind == "CLASS" else "FUNCTION"
                qualified_name = _qualified(parent, statement.name)
                draft = _NodeDraft(
                    node_kind=node_kind,
                    relative_path=relative_path,
                    qualified_name=qualified_name,
                    source_span=_source_span(statement),
                )
                node_id = draft.node_id(repository_id)
                nodes.append(draft)
                edges.append(
                    _EdgeDraft(
                        edge_kind="CONTAINS",
                        source_node_id=parent.node_id,
                        target_node_id=node_id,
                        source_span=_source_span(statement),
                        resolution_rule="LEXICAL_CONTAINMENT",
                    )
                )
                visit_body(
                    statement.body,
                    _Scope(
                        node_id=node_id,
                        qualified_name=qualified_name,
                        node_kind=node_kind,
                    ),
                )
            elif isinstance(statement, ast.ClassDef):
                qualified_name = _qualified(parent, statement.name)
                draft = _NodeDraft(
                    node_kind="CLASS",
                    relative_path=relative_path,
                    qualified_name=qualified_name,
                    source_span=_source_span(statement),
                )
                node_id = draft.node_id(repository_id)
                nodes.append(draft)
                edges.append(
                    _EdgeDraft(
                        edge_kind="CONTAINS",
                        source_node_id=parent.node_id,
                        target_node_id=node_id,
                        source_span=_source_span(statement),
                        resolution_rule="LEXICAL_CONTAINMENT",
                    )
                )
                visit_body(
                    statement.body,
                    _Scope(
                        node_id=node_id,
                        qualified_name=qualified_name,
                        node_kind="CLASS",
                    ),
                )
            else:
                for child in ast.iter_child_nodes(statement):
                    if isinstance(child, ast.stmt):
                        visit_body([child], parent)

    visit_body(
        tree.body,
        _Scope(
            node_id=module_id,
            qualified_name=relative_path,
            node_kind="MODULE",
        ),
    )

    for candidate in ast.walk(tree):
        if isinstance(candidate, ast.Import):
            for alias in candidate.names:
                unresolved = UnresolvedTarget(
                    normalized_target=alias.name,
                    resolution_rule="PYTHON_IMPORT_UNRESOLVED",
                    ambiguity_reason="STAGE_C_DOES_NOT_RESOLVE_IMPORT_TARGETS",
                )
                edges.append(
                    _EdgeDraft(
                        edge_kind="IMPORTS",
                        source_node_id=module_id,
                        unresolved_target=unresolved,
                        source_span=_source_span(candidate),
                        resolution_rule=unresolved.resolution_rule,
                    )
                )
        elif isinstance(candidate, ast.ImportFrom):
            module_name = candidate.module or ""
            level_prefix = "." * int(candidate.level or 0)
            normalized = f"{level_prefix}{module_name}" or level_prefix
            if normalized:
                unresolved = UnresolvedTarget(
                    normalized_target=normalized,
                    resolution_rule="PYTHON_IMPORT_FROM_UNRESOLVED",
                    ambiguity_reason="STAGE_C_DOES_NOT_RESOLVE_IMPORT_TARGETS",
                )
                edges.append(
                    _EdgeDraft(
                        edge_kind="IMPORTS",
                        source_node_id=module_id,
                        unresolved_target=unresolved,
                        source_span=_source_span(candidate),
                        resolution_rule=unresolved.resolution_rule,
                    )
                )

    unique_nodes: dict[str, _NodeDraft] = {}
    for draft in nodes:
        unique_nodes[draft.node_id(repository_id)] = draft
    unique_edges: dict[str, _EdgeDraft] = {}
    for draft in edges:
        edge_id = draft.edge_id(repository_id)
        current = unique_edges.get(edge_id)
        if current is None or (
            draft.source_span.start_byte,
            draft.source_span.end_byte,
        ) < (
            current.source_span.start_byte,
            current.source_span.end_byte,
        ):
            unique_edges[edge_id] = draft
    return (
        tuple(
            sorted(
                unique_nodes.values(),
                key=lambda item: (
                    item.relative_path,
                    item.node_kind,
                    item.qualified_name,
                ),
            )
        ),
        tuple(
            sorted(
                unique_edges.values(),
                key=lambda item: (
                    item.edge_kind,
                    item.source_node_id,
                    item.target_node_id or "",
                    (
                        item.unresolved_target.normalized_target
                        if item.unresolved_target is not None
                        else ""
                    ),
                ),
            )
        ),
    )


def _problem(
    *,
    relative_path: str,
    reason: str,
    observed_bytes: int | None = None,
    is_error: bool = False,
) -> _ObservedProblem:
    return _ObservedProblem(
        relative_path=relative_path,
        reason=reason,
        observed_bytes=observed_bytes,
        is_error=is_error,
    )


def _safe_manifest_paths(
    relative_paths: Iterable[str],
    *,
    budget: ScanBudget,
) -> tuple[list[str], list[_ObservedProblem]]:
    observed: list[str] = []
    problems: list[_ObservedProblem] = []
    for raw_path in relative_paths:
        if len(observed) >= budget.max_files:
            problems.append(
                _problem(relative_path="<manifest>", reason="FILE_COUNT_BUDGET_EXCEEDED")
            )
            break
        try:
            normalized = normalize_relative_path(raw_path)
        except (TypeError, ValueError):
            problems.append(
                _problem(relative_path="<invalid>", reason="INVALID_RELATIVE_PATH")
            )
            continue
        observed.append(normalized)
    if len(set(observed)) < len(observed):
        observed = list(dict.fromkeys(observed))
    if len(observed) > budget.max_files:
        overflow = observed.pop()
        problems.append(
            _problem(relative_path=overflow, reason="FILE_COUNT_BUDGET_EXCEEDED")
        )
    return sorted(set(observed)), problems


def _discover_and_parse(
    *,
    repository_id: str,
    root: Path,
    relative_paths: Iterable[str],
    budget: ScanBudget,
    monotonic_clock: Callable[[], float],
    started_monotonic: float,
) -> tuple[tuple[_ParsedFile, ...], tuple[_ObservedProblem, ...]]:
    paths, initial_problems = _safe_manifest_paths(relative_paths, budget=budget)
    parsed: list[_ParsedFile] = []
    problems = list(initial_problems)
    total_bytes = 0

    for relative_path in paths:
        if monotonic_clock() - started_monotonic > budget.max_scan_seconds:
            problems.append(_problem(relative_path=relative_path, reason="SCAN_TIMEOUT"))
            break
        if not relative_path.endswith(SUPPORTED_EXTENSION):
            problems.append(
                _problem(relative_path=relative_path, reason="UNSUPPORTED_EXTENSION")
            )
            continue
        if len(relative_path.split("/")) > budget.max_path_depth:
            problems.append(_problem(relative_path=relative_path, reason="PATH_DEPTH_LIMIT"))
            continue
        if _path_has_symlink_component(root, relative_path):
            problems.append(_problem(relative_path=relative_path, reason="SYMLINK_REJECTED"))
            continue

        candidate = root.joinpath(*relative_path.split("/"))
        try:
            resolved = candidate.resolve(strict=True)
        except FileNotFoundError:
            problems.append(
                _problem(relative_path=relative_path, reason="MISSING_FILE", is_error=True)
            )
            continue
        except OSError:
            problems.append(
                _problem(relative_path=relative_path, reason="PATH_RESOLUTION_ERROR", is_error=True)
            )
            continue
        if not resolved.is_relative_to(root):
            problems.append(_problem(relative_path=relative_path, reason="ROOT_ESCAPE"))
            continue
        try:
            file_stat = resolved.stat()
        except OSError:
            problems.append(
                _problem(relative_path=relative_path, reason="STAT_ERROR", is_error=True)
            )
            continue
        if not resolved.is_file():
            problems.append(_problem(relative_path=relative_path, reason="NOT_REGULAR_FILE"))
            continue
        size = int(file_stat.st_size)
        if size > budget.max_file_bytes:
            problems.append(
                _problem(
                    relative_path=relative_path,
                    reason="FILE_SIZE_LIMIT",
                    observed_bytes=size,
                )
            )
            continue
        remaining_total_bytes = budget.max_total_bytes - total_bytes
        if remaining_total_bytes <= 0 or size > remaining_total_bytes:
            problems.append(
                _problem(
                    relative_path=relative_path,
                    reason="TOTAL_BYTE_LIMIT",
                    observed_bytes=size,
                )
            )
            continue

        # Bound the actual read, not only the successful-parse accounting. One
        # look-ahead byte is permitted solely to detect growth beyond either the
        # per-file or remaining total-byte budget after stat().
        read_cap = min(budget.max_file_bytes, remaining_total_bytes)
        try:
            with resolved.open("rb") as source:
                raw = source.read(read_cap + 1)
        except OSError:
            problems.append(
                _problem(relative_path=relative_path, reason="READ_ERROR", is_error=True)
            )
            # A failed read has unknown partial-consumption semantics. Stop
            # conservatively rather than allowing later reads to exceed the
            # declared aggregate budget.
            break

        total_bytes += len(raw)
        if len(raw) > read_cap:
            overflow_reason = (
                "FILE_SIZE_LIMIT"
                if budget.max_file_bytes <= remaining_total_bytes
                else "TOTAL_BYTE_LIMIT"
            )
            problems.append(
                _problem(
                    relative_path=relative_path,
                    reason=overflow_reason,
                    observed_bytes=len(raw),
                    is_error=True,
                )
            )
            continue
        if len(raw) != size:
            problems.append(
                _problem(
                    relative_path=relative_path,
                    reason="FILE_CHANGED_DURING_SCAN",
                    observed_bytes=len(raw),
                    is_error=True,
                )
            )
            continue
        if _path_has_symlink_component(root, relative_path):
            problems.append(
                _problem(relative_path=relative_path, reason="SYMLINK_RACE_DETECTED", is_error=True)
            )
            continue
        if b"\x00" in raw:
            problems.append(
                _problem(
                    relative_path=relative_path,
                    reason="BINARY_NUL_PAYLOAD",
                    observed_bytes=len(raw),
                )
            )
            continue
        try:
            raw.decode("utf-8", errors="strict")
        except UnicodeDecodeError:
            problems.append(
                _problem(
                    relative_path=relative_path,
                    reason="NON_UTF8_SOURCE",
                    observed_bytes=len(raw),
                    is_error=True,
                )
            )
            continue
        try:
            nodes, edges = _parse_python_file(
                repository_id=repository_id,
                relative_path=relative_path,
                raw=raw,
            )
        except (
            SyntaxError,
            UnicodeError,
            ValueError,
            RecursionError,
            MemoryError,
            OverflowError,
        ):
            problems.append(
                _problem(
                    relative_path=relative_path,
                    reason="PARSER_ERROR",
                    observed_bytes=len(raw),
                    is_error=True,
                )
            )
            continue
        if monotonic_clock() - started_monotonic > budget.max_scan_seconds:
            problems.append(
                _problem(
                    relative_path=relative_path,
                    reason="SCAN_TIMEOUT",
                    observed_bytes=len(raw),
                )
            )
            break

        parsed.append(
            _ParsedFile(
                relative_path=relative_path,
                size_bytes=len(raw),
                content_digest=hashlib.sha256(raw).hexdigest(),
                nodes=nodes,
                edges=edges,
            )
        )

    return tuple(sorted(parsed, key=lambda item: item.relative_path)), tuple(problems)


def _materialize_candidate(
    *,
    repository_id: str,
    generation: int,
    receipt_id: str,
    parsed_files: Sequence[_ParsedFile],
    problems: Sequence[_ObservedProblem],
    budget: ScanBudget,
) -> _ScanCandidate:
    manifest_records = [
        (item.relative_path, item.size_bytes, item.content_digest) for item in parsed_files
    ]
    problem_records = sorted(
        (
            item.relative_path,
            item.reason,
            item.observed_bytes,
            item.is_error,
        )
        for item in problems
    )
    manifest_digest = _canonical_digest(
        (
            "csm-filesystem-manifest-v1",
            tuple(sorted(manifest_records)),
            tuple(problem_records),
        )
    )
    source_state = SourceState(
        manifest_digest=manifest_digest,
        dirty=True,
        commit_sha=None,
    )
    parser_versions = ((PARSER_ADAPTER_ID, sys.version.split()[0]),)
    scan_config_digest = _scan_config_digest(budget)

    node_drafts: dict[str, _NodeDraft] = {}
    edge_drafts: dict[str, _EdgeDraft] = {}
    for parsed_file in parsed_files:
        for node in parsed_file.nodes:
            node_drafts[node.node_id(repository_id)] = node
        for edge in parsed_file.edges:
            edge_drafts[edge.edge_id(repository_id)] = edge

    graph_payload = (
        tuple(
            sorted(
                (
                    node_id,
                    draft.node_kind,
                    draft.relative_path,
                    draft.qualified_name,
                    draft.source_span.start_byte,
                    draft.source_span.end_byte,
                )
                for node_id, draft in node_drafts.items()
            )
        ),
        tuple(
            sorted(
                (
                    edge_id,
                    draft.edge_kind,
                    draft.source_node_id,
                    draft.target_node_id,
                    (
                        None
                        if draft.unresolved_target is None
                        else draft.unresolved_target.normalized_target
                    ),
                    draft.resolution_rule,
                    draft.source_span.start_byte,
                    draft.source_span.end_byte,
                )
                for edge_id, draft in edge_drafts.items()
            )
        ),
        tuple(problem_records),
    )
    structural_graph_digest = _canonical_digest(graph_payload)
    snapshot_id = make_snapshot_id(
        repository_id=repository_id,
        source_state=source_state,
        parser_profile_id=PARSER_PROFILE_ID,
        parser_versions=parser_versions,
        scan_config_digest=scan_config_digest,
        structural_graph_digest=structural_graph_digest,
    )

    nodes = tuple(
        StructuralNode(
            node_id=node_id,
            repository_id=repository_id,
            snapshot_id=snapshot_id,
            generation=generation,
            node_kind=draft.node_kind,
            relative_path=draft.relative_path,
            qualified_name=draft.qualified_name,
            source_span=draft.source_span,
            parser_profile_id=PARSER_PROFILE_ID,
            parser_adapter_id=PARSER_ADAPTER_ID,
        )
        for node_id, draft in sorted(node_drafts.items())
    )
    edges = tuple(
        StructuralEdge(
            edge_id=edge_id,
            repository_id=repository_id,
            snapshot_id=snapshot_id,
            generation=generation,
            edge_kind=draft.edge_kind,
            source_node_id=draft.source_node_id,
            target_node_id=draft.target_node_id,
            source_span=draft.source_span,
            resolution_rule=draft.resolution_rule,
            unresolved_target=draft.unresolved_target,
        )
        for edge_id, draft in sorted(edge_drafts.items())
    )

    omission_counter = Counter(
        item.reason for item in problems if not item.is_error
    )
    error_counter = Counter(item.reason for item in problems if item.is_error)
    omission_counts = tuple(sorted(omission_counter.items()))
    error_counts = tuple(sorted(error_counter.items()))
    omissions = tuple(
        ScanOmission(
            omission_id=_canonical_digest(
                (
                    "csm-scan-omission-v1",
                    repository_id,
                    snapshot_id,
                    item.relative_path,
                    item.reason,
                    item.observed_bytes,
                    item.is_error,
                )
            ),
            repository_id=repository_id,
            snapshot_id=snapshot_id,
            relative_path=item.relative_path,
            reason=item.reason,
            observed_bytes=item.observed_bytes,
        )
        for item in sorted(
            problems,
            key=lambda problem: (
                problem.relative_path,
                problem.reason,
                problem.is_error,
            ),
        )
    )
    return _ScanCandidate(
        source_state=source_state,
        parser_versions=parser_versions,
        scan_config_digest=scan_config_digest,
        structural_graph_digest=structural_graph_digest,
        snapshot_id=snapshot_id,
        discovered_file_count=len(parsed_files) + len(problems),
        discovered_byte_count=(
            sum(item.size_bytes for item in parsed_files)
            + sum(item.observed_bytes or 0 for item in problems)
        ),
        nodes=nodes,
        edges=edges,
        problems=tuple(problems),
        omissions=omissions,
        omission_reason_counts=omission_counts,
        error_reason_counts=error_counts,
    )


def _receipt_id(
    *,
    repository_id: str,
    generation: int,
    candidate: _ScanCandidate,
) -> str:
    return _canonical_digest(
        (
            "csm-scan-receipt-v1",
            repository_id,
            generation,
            candidate.snapshot_id,
            candidate.source_state.manifest_digest,
            candidate.scan_config_digest,
            candidate.structural_graph_digest,
            candidate.omission_reason_counts,
            candidate.error_reason_counts,
        )
    )


def _scan_receipt(
    *,
    repository_id: str,
    generation: int,
    receipt_id: str,
    candidate: _ScanCandidate,
    final_disposition: str,
) -> ScanReceipt:
    return ScanReceipt(
        receipt_id=receipt_id,
        repository_id=repository_id,
        generation=generation,
        candidate_snapshot_id=candidate.snapshot_id,
        source_state=candidate.source_state,
        scan_config_digest=candidate.scan_config_digest,
        structural_graph_digest=candidate.structural_graph_digest,
        discovered_file_count=candidate.discovered_file_count,
        discovered_byte_count=candidate.discovered_byte_count,
        omitted_count=len(candidate.omission_reason_counts) and sum(
            count for _, count in candidate.omission_reason_counts
        ) or 0,
        error_count=len(candidate.error_reason_counts) and sum(
            count for _, count in candidate.error_reason_counts
        ) or 0,
        omission_reason_counts=candidate.omission_reason_counts,
        error_reason_counts=candidate.error_reason_counts,
        final_disposition=final_disposition,
    )


def _insert_receipt(
    conn: sqlite3.Connection,
    receipt: ScanReceipt,
) -> None:
    conn.execute(
        """
        INSERT INTO csm_scan_receipts(
            receipt_id,
            repository_id,
            generation,
            candidate_snapshot_id,
            source_manifest_digest,
            source_dirty,
            source_commit_sha,
            scan_config_digest,
            structural_graph_digest,
            discovered_file_count,
            discovered_byte_count,
            omitted_count,
            error_count,
            omission_reason_counts_json,
            error_reason_counts_json,
            final_disposition
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            receipt.receipt_id,
            receipt.repository_id,
            receipt.generation,
            receipt.candidate_snapshot_id,
            receipt.source_state.manifest_digest,
            int(receipt.source_state.dirty),
            receipt.source_state.commit_sha,
            receipt.scan_config_digest,
            receipt.structural_graph_digest,
            receipt.discovered_file_count,
            receipt.discovered_byte_count,
            receipt.omitted_count,
            receipt.error_count,
            serialize_reason_counts(receipt.omission_reason_counts),
            serialize_reason_counts(receipt.error_reason_counts),
            receipt.final_disposition,
        ),
    )


def _snapshot_from_candidate(
    *,
    repository_id: str,
    generation: int,
    receipt_id: str,
    candidate: _ScanCandidate,
    promoted_at: str,
) -> RepositorySnapshot:
    return RepositorySnapshot(
        snapshot_id=candidate.snapshot_id,
        repository_id=repository_id,
        generation=generation,
        source_state=candidate.source_state,
        parser_profile_id=PARSER_PROFILE_ID,
        parser_versions=candidate.parser_versions,
        scan_config_digest=candidate.scan_config_digest,
        discovered_file_count=candidate.discovered_file_count,
        discovered_byte_count=candidate.discovered_byte_count,
        structural_graph_digest=candidate.structural_graph_digest,
        scan_receipt_id=receipt_id,
        promoted_at=promoted_at,
    )


def _snapshot_semantically_matches(
    conn: sqlite3.Connection,
    *,
    repository_id: str,
    candidate: _ScanCandidate,
) -> bool:
    snapshot = conn.execute(
        "SELECT * FROM csm_snapshots WHERE snapshot_id = ?",
        (candidate.snapshot_id,),
    ).fetchone()
    if snapshot is None:
        return False
    if snapshot["repository_id"] != repository_id:
        raise CSMScannerError("snapshot_id collision crossed repository scope")
    expected_header = (
        candidate.source_state.manifest_digest,
        int(candidate.source_state.dirty),
        candidate.source_state.commit_sha,
        PARSER_PROFILE_ID,
        json.dumps(candidate.parser_versions, separators=(",", ":")),
        candidate.scan_config_digest,
        candidate.structural_graph_digest,
        candidate.discovered_file_count,
        candidate.discovered_byte_count,
    )
    observed_header = (
        snapshot["source_manifest_digest"],
        snapshot["source_dirty"],
        snapshot["source_commit_sha"],
        snapshot["parser_profile_id"],
        snapshot["parser_versions_json"],
        snapshot["scan_config_digest"],
        snapshot["structural_graph_digest"],
        snapshot["discovered_file_count"],
        snapshot["discovered_byte_count"],
    )
    if observed_header != expected_header:
        raise CSMScannerError("content-addressed snapshot header mismatch")

    expected_nodes = {
        (
            node.node_id,
            node.node_kind,
            node.relative_path,
            node.qualified_name,
            node.source_span.start_byte,
            node.source_span.end_byte,
            node.parser_profile_id,
            node.parser_adapter_id,
        )
        for node in candidate.nodes
    }
    observed_nodes = {
        (
            row["node_id"],
            row["node_kind"],
            row["relative_path"],
            row["qualified_name"],
            row["source_start_byte"],
            row["source_end_byte"],
            row["parser_profile_id"],
            row["parser_adapter_id"],
        )
        for row in conn.execute(
            "SELECT * FROM csm_nodes WHERE snapshot_id = ?",
            (candidate.snapshot_id,),
        )
    }
    if observed_nodes != expected_nodes:
        raise CSMScannerError("content-addressed snapshot node materialization mismatch")

    expected_edges = {
        (
            edge.edge_id,
            edge.edge_kind,
            edge.source_node_id,
            edge.target_node_id,
            edge.source_span.start_byte,
            edge.source_span.end_byte,
            edge.resolution_rule,
            None if edge.unresolved_target is None else edge.unresolved_target.normalized_target,
            None if edge.unresolved_target is None else edge.unresolved_target.ambiguity_reason,
        )
        for edge in candidate.edges
    }
    observed_edges = {
        (
            row["edge_id"],
            row["edge_kind"],
            row["source_node_id"],
            row["target_node_id"],
            row["source_start_byte"],
            row["source_end_byte"],
            row["resolution_rule"],
            row["unresolved_target"],
            row["ambiguity_reason"],
        )
        for row in conn.execute(
            "SELECT * FROM csm_edges WHERE snapshot_id = ?",
            (candidate.snapshot_id,),
        )
    }
    if observed_edges != expected_edges:
        raise CSMScannerError("content-addressed snapshot edge materialization mismatch")
    return True


def _insert_snapshot_materialization(
    conn: sqlite3.Connection,
    *,
    snapshot: RepositorySnapshot,
    candidate: _ScanCandidate,
) -> None:
    conn.execute(
        """
        INSERT INTO csm_snapshots(
            snapshot_id,
            repository_id,
            generation,
            source_manifest_digest,
            source_dirty,
            source_commit_sha,
            parser_profile_id,
            parser_versions_json,
            scan_config_digest,
            discovered_file_count,
            discovered_byte_count,
            structural_graph_digest,
            scan_receipt_id,
            promoted_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            snapshot.snapshot_id,
            snapshot.repository_id,
            snapshot.generation,
            snapshot.source_state.manifest_digest,
            int(snapshot.source_state.dirty),
            snapshot.source_state.commit_sha,
            snapshot.parser_profile_id,
            json.dumps(snapshot.parser_versions, separators=(",", ":")),
            snapshot.scan_config_digest,
            snapshot.discovered_file_count,
            snapshot.discovered_byte_count,
            snapshot.structural_graph_digest,
            snapshot.scan_receipt_id,
            snapshot.promoted_at,
        ),
    )
    conn.executemany(
        """
        INSERT INTO csm_nodes(
            node_id,
            repository_id,
            snapshot_id,
            generation,
            node_kind,
            relative_path,
            qualified_name,
            source_start_byte,
            source_end_byte,
            parser_profile_id,
            parser_adapter_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            (
                node.node_id,
                node.repository_id,
                node.snapshot_id,
                node.generation,
                node.node_kind,
                node.relative_path,
                node.qualified_name,
                node.source_span.start_byte,
                node.source_span.end_byte,
                node.parser_profile_id,
                node.parser_adapter_id,
            )
            for node in candidate.nodes
        ),
    )
    conn.executemany(
        """
        INSERT INTO csm_edges(
            edge_id,
            repository_id,
            snapshot_id,
            generation,
            edge_kind,
            source_node_id,
            target_node_id,
            source_start_byte,
            source_end_byte,
            resolution_rule,
            unresolved_target,
            ambiguity_reason
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            (
                edge.edge_id,
                edge.repository_id,
                edge.snapshot_id,
                edge.generation,
                edge.edge_kind,
                edge.source_node_id,
                edge.target_node_id,
                edge.source_span.start_byte,
                edge.source_span.end_byte,
                edge.resolution_rule,
                None if edge.unresolved_target is None else edge.unresolved_target.normalized_target,
                None if edge.unresolved_target is None else edge.unresolved_target.ambiguity_reason,
            )
            for edge in candidate.edges
        ),
    )


def _finalize_incomplete(
    conn: sqlite3.Connection,
    *,
    lease: ScanLease,
    candidate: _ScanCandidate,
    receipt_id: str,
    now: float,
) -> ScanOutcome:
    try:
        conn.execute("BEGIN IMMEDIATE")
        state = conn.execute(
            "SELECT * FROM csm_repository_scan_state WHERE repository_id = ?",
            (lease.repository_id,),
        ).fetchone()
        if state is None:
            raise ScanLeaseLostError("repository scan state disappeared")
        if (
            state["lease_token"] != lease.holder_token
            or state["lease_generation"] != lease.generation
            or state["lease_expires_at"] is None
            or float(state["lease_expires_at"]) <= now
        ):
            raise ScanLeaseLostError("scan lease was lost before incomplete finalization")
        receipt = _scan_receipt(
            repository_id=lease.repository_id,
            generation=lease.generation,
            receipt_id=receipt_id,
            candidate=candidate,
            final_disposition="INCOMPLETE_REJECTED",
        )
        _insert_receipt(conn, receipt)
        cleared = conn.execute(
            """
            UPDATE csm_repository_scan_state
            SET lease_token = NULL,
                lease_generation = NULL,
                lease_issued_at = NULL,
                lease_expires_at = NULL
            WHERE repository_id = ?
              AND lease_token = ?
              AND lease_generation = ?
            """,
            (
                lease.repository_id,
                lease.holder_token,
                lease.generation,
            ),
        ).rowcount
        if cleared != 1:
            raise ScanLeaseLostError("scan lease changed during incomplete finalization")
        _lease_event(
            conn,
            repository_id=lease.repository_id,
            generation=lease.generation,
            lease_token=lease.holder_token,
            event_type="FINALIZED_INCOMPLETE",
            observed_at=now,
        )
        conn.commit()
        return ScanOutcome(
            repository_id=lease.repository_id,
            generation=lease.generation,
            receipt_id=receipt_id,
            snapshot_id=candidate.snapshot_id,
            structural_graph_digest=candidate.structural_graph_digest,
            final_disposition="INCOMPLETE_REJECTED",
            promoted=False,
            reused_snapshot=False,
            source_state=candidate.source_state,
            discovered_file_count=candidate.discovered_file_count,
            discovered_byte_count=candidate.discovered_byte_count,
            problems=candidate.omissions,
            omission_reason_counts=candidate.omission_reason_counts,
            error_reason_counts=candidate.error_reason_counts,
        )
    except Exception:
        conn.rollback()
        raise


def _finalize_complete(
    conn: sqlite3.Connection,
    *,
    lease: ScanLease,
    candidate: _ScanCandidate,
    receipt_id: str,
    now: float,
) -> ScanOutcome:
    try:
        conn.execute("BEGIN IMMEDIATE")
        state = conn.execute(
            "SELECT * FROM csm_repository_scan_state WHERE repository_id = ?",
            (lease.repository_id,),
        ).fetchone()
        if state is None:
            raise ScanLeaseLostError("repository scan state disappeared")
        if (
            state["lease_token"] != lease.holder_token
            or state["lease_generation"] != lease.generation
            or state["lease_expires_at"] is None
            or float(state["lease_expires_at"]) <= now
        ):
            raise ScanLeaseLostError("scan lease was lost before complete finalization")
        current_generation = state["current_scan_generation"]
        if current_generation is not None and int(current_generation) >= lease.generation:
            raise ScanLeaseLostError(
                "scan generation is not newer than the current repository scan generation"
            )

        exists = _snapshot_semantically_matches(
            conn,
            repository_id=lease.repository_id,
            candidate=candidate,
        )
        disposition = "REUSED_SNAPSHOT" if exists else "PROMOTED"
        receipt = _scan_receipt(
            repository_id=lease.repository_id,
            generation=lease.generation,
            receipt_id=receipt_id,
            candidate=candidate,
            final_disposition=disposition,
        )
        _insert_receipt(conn, receipt)
        promoted_at = _utc_iso(time.time())
        if not exists:
            snapshot = _snapshot_from_candidate(
                repository_id=lease.repository_id,
                generation=lease.generation,
                receipt_id=receipt_id,
                candidate=candidate,
                promoted_at=promoted_at,
            )
            _insert_snapshot_materialization(
                conn,
                snapshot=snapshot,
                candidate=candidate,
            )

        updated = conn.execute(
            """
            UPDATE csm_repository_scan_state
            SET current_snapshot_id = ?,
                current_scan_generation = ?,
                current_scan_receipt_id = ?,
                lease_token = NULL,
                lease_generation = NULL,
                lease_issued_at = NULL,
                lease_expires_at = NULL
            WHERE repository_id = ?
              AND lease_token = ?
              AND lease_generation = ?
              AND (
                    current_scan_generation IS NULL
                    OR current_scan_generation < ?
              )
            """,
            (
                candidate.snapshot_id,
                lease.generation,
                receipt_id,
                lease.repository_id,
                lease.holder_token,
                lease.generation,
                lease.generation,
            ),
        ).rowcount
        if updated != 1:
            raise ScanLeaseLostError("current snapshot CAS rejected stale scan finalizer")
        _lease_event(
            conn,
            repository_id=lease.repository_id,
            generation=lease.generation,
            lease_token=lease.holder_token,
            event_type="FINALIZED_REUSED" if exists else "FINALIZED_PROMOTED",
            observed_at=now,
        )
        conn.commit()
        return ScanOutcome(
            repository_id=lease.repository_id,
            generation=lease.generation,
            receipt_id=receipt_id,
            snapshot_id=candidate.snapshot_id,
            structural_graph_digest=candidate.structural_graph_digest,
            final_disposition=disposition,
            promoted=True,
            reused_snapshot=exists,
            source_state=candidate.source_state,
            discovered_file_count=candidate.discovered_file_count,
            discovered_byte_count=candidate.discovered_byte_count,
            problems=(),
            omission_reason_counts=(),
            error_reason_counts=(),
        )
    except Exception:
        conn.rollback()
        raise


def scan_python_repository(
    conn: sqlite3.Connection,
    *,
    repository_id: str,
    root: str | Path,
    relative_paths: Iterable[str],
    budget: ScanBudget,
    lease_ttl_seconds: float = DEFAULT_LEASE_TTL_SECONDS,
    monotonic_clock: Callable[[], float] = time.monotonic,
    token_factory: Callable[[], str] = _default_token_factory,
) -> ScanOutcome:
    """Explicitly scan a bounded Python manifest into one CSM candidate.

    The function never imports or executes repository code. It stages parse results
    in memory, persists an incomplete immutable receipt on any omission/error, and
    promotes/reuses a semantic snapshot only for a complete scan.
    """
    initialize_schema(conn)
    _require_idle_connection(conn)
    _require_registered_root(
        conn,
        repository_id=repository_id,
        root=root,
    )
    if not isinstance(budget, ScanBudget):
        raise TypeError("budget must be a ScanBudget")
    lease_ttl_seconds = _require_positive_seconds(
        lease_ttl_seconds,
        "lease_ttl_seconds",
    )
    if lease_ttl_seconds <= budget.max_scan_seconds:
        raise ValueError(
            "lease_ttl_seconds must be greater than budget.max_scan_seconds"
        )
    holder_token = token_factory()
    if not isinstance(holder_token, str) or not holder_token.strip():
        raise ValueError("token_factory must return a non-empty string")
    started_monotonic = monotonic_clock()
    lease = _acquire_scan_lease(
        conn,
        repository_id=repository_id,
        now=started_monotonic,
        lease_ttl_seconds=lease_ttl_seconds,
        holder_token=holder_token,
    )
    try:
        parsed_files, problems = _discover_and_parse(
            repository_id=repository_id,
            root=resolve_repository_root(root),
            relative_paths=relative_paths,
            budget=budget,
            monotonic_clock=monotonic_clock,
            started_monotonic=started_monotonic,
        )
        candidate = _materialize_candidate(
            repository_id=repository_id,
            generation=lease.generation,
            receipt_id="pending",
            parsed_files=parsed_files,
            problems=problems,
            budget=budget,
        )
        receipt_id = _receipt_id(
            repository_id=repository_id,
            generation=lease.generation,
            candidate=candidate,
        )
        final_monotonic = monotonic_clock()
        if final_monotonic > lease.expires_at:
            raise ScanLeaseLostError("scan lease expired before finalization")
        if problems:
            return _finalize_incomplete(
                conn,
                lease=lease,
                candidate=candidate,
                receipt_id=receipt_id,
                now=final_monotonic,
            )
        return _finalize_complete(
            conn,
            lease=lease,
            candidate=candidate,
            receipt_id=receipt_id,
            now=final_monotonic,
        )
    except Exception:
        _release_scan_lease_best_effort(
            conn,
            lease=lease,
            now=monotonic_clock(),
        )
        raise


__all__ = [
    "SCANNER_CONTRACT_VERSION",
    "PARSER_PROFILE_ID",
    "PARSER_ADAPTER_ID",
    "DEFAULT_LEASE_TTL_SECONDS",
    "CSMScannerError",
    "RepositoryRegistrationError",
    "ScanLeaseBusyError",
    "ScanLeaseLostError",
    "ScanLease",
    "ScanOutcome",
    "local_root_fingerprint",
    "register_repository",
    "resolve_repository_root",
    "scan_python_repository",
]
