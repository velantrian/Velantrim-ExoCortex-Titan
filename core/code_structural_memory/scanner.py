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


def _parser_versions() -> tuple[tuple[str, str], ...]:
    version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    return ((PARSER_ADAPTER_ID, version),)


def _scan_config_digest(budget: ScanBudget) -> str:
    return _canonical_digest(
        {
            "version": SCANNER_CONTRACT_VERSION,
            "parser_profile_id": PARSER_PROFILE_ID,
            "parser_versions": _parser_versions(),
            "supported_extensions": [SUPPORTED_EXTENSION],
            "explicit_manifest_only": True,
            "reject_symlinks": True,
            "strict_complete_promotion": True,
            "persist_source_body": False,
            "node_kinds": ["MODULE", "CLASS", "FUNCTION", "METHOD"],
            "edge_kinds": ["CONTAINS", "IMPORTS"],
            "budget": {
                "max_files": budget.max_files,
                "max_file_bytes": budget.max_file_bytes,
                "max_total_bytes": budget.max_total_bytes,
                "max_path_depth": budget.max_path_depth,
                "max_scan_seconds": budget.max_scan_seconds,
            },
        }
    )


def resolve_repository_root(root: str | Path) -> Path:
    """Resolve and freeze a non-symlink repository directory."""
    raw = Path(root).expanduser()
    try:
        if raw.is_symlink():
            raise RepositoryRegistrationError("repository root must not be a symlink")
        resolved = raw.resolve(strict=True)
    except (FileNotFoundError, OSError) as exc:
        raise RepositoryRegistrationError("repository root cannot be resolved") from exc
    if not resolved.is_dir():
        raise RepositoryRegistrationError("repository root must be a directory")
    return resolved


def local_root_fingerprint(root: str | Path) -> str:
    """Hash local deployment root identity without exposing the path in CSM rows."""
    resolved = resolve_repository_root(root)
    normalized = os.path.normcase(str(resolved)).replace("\\", "/")
    return "sha256:" + hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def register_repository(
    conn: sqlite3.Connection,
    *,
    registration: RepositoryRegistration,
    root: str | Path,
) -> None:
    """Persist one exact repository registration or prove an identical one exists."""
    _require_idle_connection(conn)
    initialize_schema(conn)
    resolved = resolve_repository_root(root)
    expected_fingerprint = local_root_fingerprint(resolved)
    if registration.local_root_fingerprint != expected_fingerprint:
        raise RepositoryRegistrationError(
            "registration local_root_fingerprint does not match the resolved root"
        )
    if registration.status != "ACTIVE":
        raise RepositoryRegistrationError("new scanner registrations must be ACTIVE")

    row = conn.execute(
        "SELECT * FROM csm_repositories WHERE repository_id = ?",
        (registration.repository_id,),
    ).fetchone()
    expected = (
        registration.canonical_origin,
        registration.local_root_fingerprint,
        registration.registration_policy_id,
        registration.tenant_or_project_scope,
        registration.created_at,
        registration.status,
        registration.retention_policy_id,
    )
    if row is not None:
        actual = (
            row["canonical_origin"],
            row["local_root_fingerprint"],
            row["registration_policy_id"],
            row["tenant_or_project_scope"],
            row["created_at"],
            row["status"],
            row["retention_policy_id"],
        )
        if actual != expected:
            raise RepositoryRegistrationError(
                "repository_id is already bound to different registration metadata"
            )
        state = conn.execute(
            "SELECT 1 FROM csm_repository_scan_state WHERE repository_id = ?",
            (registration.repository_id,),
        ).fetchone()
        if state is None:
            raise CSMScannerError("repository registration exists without scan state")
        return

    try:
        conn.execute("BEGIN IMMEDIATE")
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
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                registration.repository_id,
                registration.canonical_origin,
                registration.local_root_fingerprint,
                registration.registration_policy_id,
                registration.tenant_or_project_scope,
                registration.created_at,
                registration.status,
                registration.retention_policy_id,
            ),
        )
        state = conn.execute(
            "SELECT next_generation FROM csm_repository_scan_state WHERE repository_id = ?",
            (registration.repository_id,),
        ).fetchone()
        if state is None or int(state[0]) != 1:
            raise CSMScannerError("repository scan state was not initialized deterministically")
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def _repository_registration_row(
    conn: sqlite3.Connection,
    *,
    repository_id: str,
    root: Path,
) -> sqlite3.Row:
    row = conn.execute(
        "SELECT * FROM csm_repositories WHERE repository_id = ?",
        (repository_id,),
    ).fetchone()
    if row is None:
        raise RepositoryRegistrationError("repository_id is not registered")
    if row["status"] != "ACTIVE":
        raise RepositoryRegistrationError("repository registration is not ACTIVE")
    if row["local_root_fingerprint"] != local_root_fingerprint(root):
        raise RepositoryRegistrationError(
            "resolved repository root does not match the registered fingerprint"
        )
    return row


def _lease_event_id(
    *,
    repository_id: str,
    holder_token: str,
    generation: int,
    event_type: str,
    observed_at: float,
    reason_code: str,
) -> str:
    return _canonical_digest(
        (
            "csm-lease-event-v1",
            repository_id,
            holder_token,
            generation,
            event_type,
            f"{observed_at:.9f}",
            reason_code,
        )
    )


def _insert_lease_event(
    conn: sqlite3.Connection,
    *,
    lease: ScanLease,
    event_type: str,
    observed_at: float,
    reason_code: str,
) -> None:
    conn.execute(
        """
        INSERT INTO csm_scan_lease_events (
            repository_id,
            event_id,
            generation,
            holder_token,
            event_type,
            observed_at,
            reason_code,
            no_runtime_authority
        ) VALUES (?, ?, ?, ?, ?, ?, ?, 1)
        """,
        (
            lease.repository_id,
            _lease_event_id(
                repository_id=lease.repository_id,
                holder_token=lease.holder_token,
                generation=lease.generation,
                event_type=event_type,
                observed_at=observed_at,
                reason_code=reason_code,
            ),
            lease.generation,
            lease.holder_token,
            event_type,
            observed_at,
            reason_code,
        ),
    )


def _acquire_scan_lease(
    conn: sqlite3.Connection,
    *,
    repository_id: str,
    lease_ttl_seconds: float,
    now: float,
    token_factory: Callable[[], str],
) -> ScanLease:
    ttl = _require_positive_seconds(lease_ttl_seconds, "lease_ttl_seconds")
    try:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT * FROM csm_repository_scan_state WHERE repository_id = ?",
            (repository_id,),
        ).fetchone()
        if row is None:
            raise RepositoryRegistrationError("repository scan state does not exist")

        old_token = row["lease_token"]
        old_generation = row["lease_generation"]
        old_expiry = row["lease_expires_at"]
        recovered = old_token is not None
        if old_token is not None and float(old_expiry) > now:
            raise ScanLeaseBusyError(
                f"repository scan lease is active for generation {old_generation}"
            )

        generation = int(row["next_generation"])
        holder_token = token_factory().strip()
        if not holder_token or "\x00" in holder_token:
            raise CSMScannerError("token_factory returned an invalid lease token")
        expires_at = now + ttl

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
        )
        if updated.rowcount != 1:
            raise ScanLeaseLostError("scan lease compare-and-swap failed")

        lease = ScanLease(
            repository_id=repository_id,
            holder_token=holder_token,
            generation=generation,
            issued_at=now,
            expires_at=expires_at,
            recovered_expired_lease=recovered,
        )
        _insert_lease_event(
            conn,
            lease=lease,
            event_type="RECOVERED" if recovered else "ACQUIRED",
            observed_at=now,
            reason_code=(
                "EXPIRED_PREVIOUS_LEASE" if recovered else "EXPLICIT_SCAN_INVOCATION"
            ),
        )
        conn.commit()
        return lease
    except Exception:
        conn.rollback()
        raise


def _assert_current_lease(
    conn: sqlite3.Connection,
    *,
    lease: ScanLease,
    now: float,
) -> sqlite3.Row:
    row = conn.execute(
        "SELECT * FROM csm_repository_scan_state WHERE repository_id = ?",
        (lease.repository_id,),
    ).fetchone()
    if row is None:
        raise ScanLeaseLostError("repository scan state disappeared")
    if row["lease_token"] != lease.holder_token:
        raise ScanLeaseLostError("scan lease token is no longer current")
    if row["lease_generation"] != lease.generation:
        raise ScanLeaseLostError("scan generation is no longer current")
    if row["lease_expires_at"] is None or float(row["lease_expires_at"]) <= now:
        raise ScanLeaseLostError("scan lease expired before finalization")
    if row["current_generation"] is not None and int(row["current_generation"]) >= lease.generation:
        raise ScanLeaseLostError("a newer or equal scan generation is already current")
    return row


def _release_scan_lease(
    conn: sqlite3.Connection,
    *,
    lease: ScanLease,
    now: float,
    event_type: str,
    reason_code: str,
) -> bool:
    """Best-effort exact-token release. Never clears a successor's lease."""
    try:
        conn.execute("BEGIN IMMEDIATE")
        updated = conn.execute(
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
            (lease.repository_id, lease.holder_token, lease.generation),
        )
        if updated.rowcount == 1:
            _insert_lease_event(
                conn,
                lease=lease,
                event_type=event_type,
                observed_at=now,
                reason_code=reason_code,
            )
            conn.commit()
            return True
        conn.rollback()
        return False
    except Exception:
        conn.rollback()
        raise


def _module_qualified_name(relative_path: str) -> str:
    parts = relative_path.split("/")
    last = parts[-1]
    stem = last[:-3] if last.endswith(SUPPORTED_EXTENSION) else last
    if stem == "__init__":
        parts = parts[:-1]
    else:
        parts[-1] = stem
    return ".".join(parts) if parts else "__root__"


def _line_byte_offsets(raw: bytes) -> tuple[int, ...]:
    offsets = [0]
    cursor = 0
    for line in raw.splitlines(keepends=True):
        cursor += len(line)
        offsets.append(cursor)
    if not offsets:
        return (0,)
    return tuple(offsets)


def _ast_span(node: ast.AST, *, raw: bytes, offsets: Sequence[int]) -> SourceSpan:
    lineno = getattr(node, "lineno", None)
    col = getattr(node, "col_offset", None)
    end_lineno = getattr(node, "end_lineno", None)
    end_col = getattr(node, "end_col_offset", None)
    if lineno is None or col is None:
        return SourceSpan(0, len(raw))
    if lineno < 1 or lineno > len(offsets):
        raise ValueError("AST start line is outside source bounds")
    start = offsets[lineno - 1] + int(col)
    if end_lineno is None or end_col is None:
        end = start
    else:
        if end_lineno < 1 or end_lineno > len(offsets):
            raise ValueError("AST end line is outside source bounds")
        end = offsets[end_lineno - 1] + int(end_col)
    if start < 0 or end < start or end > len(raw):
        raise ValueError("AST source span is outside source bounds")
    return SourceSpan(start, end)


class _PythonStructureVisitor(ast.NodeVisitor):
    def __init__(self, *, repository_id: str, relative_path: str, raw: bytes) -> None:
        self._repository_id = repository_id
        self._relative_path = relative_path
        self._raw = raw
        self._offsets = _line_byte_offsets(raw)
        module_qname = _module_qualified_name(relative_path)
        module_draft = _NodeDraft(
            node_kind="MODULE",
            relative_path=relative_path,
            qualified_name=module_qname,
            source_span=SourceSpan(0, len(raw)),
        )
        self.nodes: list[_NodeDraft] = [module_draft]
        self.edges: list[_EdgeDraft] = []
        self._scope_stack: list[_Scope] = [
            _Scope(
                node_id=module_draft.node_id(repository_id),
                qualified_name=module_qname,
                node_kind="MODULE",
            )
        ]

    @property
    def _scope(self) -> _Scope:
        return self._scope_stack[-1]

    def _add_declaration(self, node: ast.AST, *, name: str, kind: str) -> _Scope:
        qname = f"{self._scope.qualified_name}.{name}"
        draft = _NodeDraft(
            node_kind=kind,
            relative_path=self._relative_path,
            qualified_name=qname,
            source_span=_ast_span(node, raw=self._raw, offsets=self._offsets),
        )
        node_id = draft.node_id(self._repository_id)
        self.nodes.append(draft)
        self.edges.append(
            _EdgeDraft(
                edge_kind="CONTAINS",
                source_node_id=self._scope.node_id,
                target_node_id=node_id,
                source_span=draft.source_span,
                resolution_rule="lexical-containment-v1",
            )
        )
        return _Scope(node_id=node_id, qualified_name=qname, node_kind=kind)

    def _visit_scoped_body(self, scope: _Scope, body: Sequence[ast.stmt]) -> None:
        self._scope_stack.append(scope)
        try:
            for statement in body:
                self.visit(statement)
        finally:
            self._scope_stack.pop()

    def visit_ClassDef(self, node: ast.ClassDef) -> None:  # noqa: N802
        scope = self._add_declaration(node, name=node.name, kind="CLASS")
        self._visit_scoped_body(scope, node.body)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: N802
        kind = "METHOD" if self._scope.node_kind == "CLASS" else "FUNCTION"
        scope = self._add_declaration(node, name=node.name, kind=kind)
        self._visit_scoped_body(scope, node.body)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:  # noqa: N802
        kind = "METHOD" if self._scope.node_kind == "CLASS" else "FUNCTION"
        scope = self._add_declaration(node, name=node.name, kind=kind)
        self._visit_scoped_body(scope, node.body)

    def _add_import_target(self, node: ast.AST, normalized_target: str) -> None:
        unresolved = UnresolvedTarget(
            target_kind="IMPORT_TARGET",
            normalized_target=normalized_target,
        )
        self.edges.append(
            _EdgeDraft(
                edge_kind="IMPORTS",
                source_node_id=self._scope.node_id,
                unresolved_target=unresolved,
                source_span=_ast_span(node, raw=self._raw, offsets=self._offsets),
                resolution_rule="python-import-unresolved-v1",
            )
        )

    def visit_Import(self, node: ast.Import) -> None:  # noqa: N802
        for target in sorted({alias.name for alias in node.names}):
            self._add_import_target(node, target)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:  # noqa: N802
        prefix = "." * node.level
        if node.module:
            self._add_import_target(node, prefix + node.module)
            return
        for target in sorted({alias.name for alias in node.names}):
            self._add_import_target(node, prefix + target)


def _parse_python_file(
    *,
    repository_id: str,
    relative_path: str,
    raw: bytes,
) -> tuple[tuple[_NodeDraft, ...], tuple[_EdgeDraft, ...]]:
    text = raw.decode("utf-8", errors="strict")
    tree = ast.parse(text, filename=relative_path, mode="exec", type_comments=True)
    visitor = _PythonStructureVisitor(
        repository_id=repository_id,
        relative_path=relative_path,
        raw=raw,
    )
    visitor.visit(tree)
    node_ids = [node.node_id(repository_id) for node in visitor.nodes]
    if len(node_ids) != len(set(node_ids)):
        raise ValueError("parser produced duplicate deterministic node identity")

    # Stable edge identity intentionally excludes source line/alias spelling. Repeated
    # equivalent imports therefore collapse to one structural edge. Keep the earliest
    # source span deterministically rather than fabricating a second identity.
    edges_by_id: dict[str, _EdgeDraft] = {}
    for edge in visitor.edges:
        edge_id = edge.edge_id(repository_id)
        existing = edges_by_id.get(edge_id)
        if existing is None or (
            edge.source_span.start_byte,
            edge.source_span.end_byte,
        ) < (
            existing.source_span.start_byte,
            existing.source_span.end_byte,
        ):
            edges_by_id[edge_id] = edge
    return (
        tuple(sorted(visitor.nodes, key=lambda item: item.node_id(repository_id))),
        tuple(edges_by_id[key] for key in sorted(edges_by_id)),
    )


def _path_has_symlink_component(root: Path, relative_path: str) -> bool:
    current = root
    for part in relative_path.split("/"):
        current = current / part
        try:
            if current.is_symlink():
                return True
        except OSError:
            return True
    return False


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
    iterator = iter(relative_paths)
    for _ in range(budget.max_files + 1):
        try:
            raw_path = next(iterator)
        except StopIteration:
            break
        try:
            normalized = normalize_relative_path(raw_path)
        except (AttributeError, TypeError, ValueError):
            problems.append(
                _problem(
                    relative_path="__invalid_manifest_entry__.py",
                    reason="INVALID_RELATIVE_PATH",
                )
            )
            continue
        observed.append(normalized)
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
        if total_bytes + size > budget.max_total_bytes:
            problems.append(
                _problem(
                    relative_path=relative_path,
                    reason="TOTAL_BYTE_LIMIT",
                    observed_bytes=size,
                )
            )
            continue

        try:
            raw = resolved.read_bytes()
        except OSError:
            problems.append(
                _problem(relative_path=relative_path, reason="READ_ERROR", is_error=True)
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

        total_bytes += len(raw)
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
        {
            "version": "csm-explicit-manifest-v1",
            "files": manifest_records,
            "problems": problem_records,
        }
    )
    source_state = SourceState(
        manifest_digest=manifest_digest,
        dirty=True,
        commit_sha=None,
    )
    parser_versions = _parser_versions()
    scan_config_digest = _scan_config_digest(budget)

    node_drafts = [node for item in parsed_files for node in item.nodes]
    edge_drafts = [edge for item in parsed_files for edge in item.edges]
    node_records = sorted(
        (
            node.node_id(repository_id),
            node.node_kind,
            node.relative_path,
            node.qualified_name,
            node.source_span.start_byte,
            node.source_span.end_byte,
            PARSER_PROFILE_ID,
            PARSER_ADAPTER_ID,
        )
        for node in node_drafts
    )
    edge_records = sorted(
        (
            edge.edge_id(repository_id),
            edge.edge_kind,
            edge.source_node_id,
            edge.target_node_id,
            (
                edge.unresolved_target.target_kind
                if edge.unresolved_target is not None
                else None
            ),
            (
                edge.unresolved_target.normalized_target
                if edge.unresolved_target is not None
                else None
            ),
            edge.source_span.start_byte,
            edge.source_span.end_byte,
            PARSER_ADAPTER_ID,
            edge.resolution_rule,
        )
        for edge in edge_drafts
    )
    omission_counter = Counter(item.reason for item in problems if not item.is_error)
    error_counter = Counter(item.reason for item in problems if item.is_error)
    omission_counts = tuple(sorted(omission_counter.items()))
    error_counts = tuple(sorted(error_counter.items()))
    structural_graph_digest = _canonical_digest(
        {
            "version": "csm-structural-graph-v1",
            "repository_id": repository_id,
            "manifest_digest": manifest_digest,
            "parser_profile_id": PARSER_PROFILE_ID,
            "parser_versions": parser_versions,
            "scan_config_digest": scan_config_digest,
            "nodes": node_records,
            "edges": edge_records,
            "omissions": omission_counts,
            "errors": error_counts,
        }
    )
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
            node_id=node.node_id(repository_id),
            repository_id=repository_id,
            snapshot_id=snapshot_id,
            generation=generation,
            node_kind=node.node_kind,
            relative_path=node.relative_path,
            qualified_name=node.qualified_name,
            source_span=node.source_span,
            parser_profile_id=PARSER_PROFILE_ID,
            parser_adapter_id=PARSER_ADAPTER_ID,
        )
        for node in sorted(node_drafts, key=lambda item: item.node_id(repository_id))
    )
    edges = tuple(
        StructuralEdge(
            edge_id=edge.edge_id(repository_id),
            repository_id=repository_id,
            snapshot_id=snapshot_id,
            generation=generation,
            edge_kind=edge.edge_kind,
            source_node_id=edge.source_node_id,
            target_node_id=edge.target_node_id,
            unresolved_target=edge.unresolved_target,
            source_span=edge.source_span,
            parser_adapter_id=PARSER_ADAPTER_ID,
            resolution_rule=edge.resolution_rule,
        )
        for edge in sorted(edge_drafts, key=lambda item: item.edge_id(repository_id))
    )
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
    lease: ScanLease,
    candidate_snapshot_id: str,
    started_at: float,
) -> str:
    return _canonical_digest(
        (
            "csm-scan-receipt-v1",
            lease.repository_id,
            lease.generation,
            lease.holder_token,
            candidate_snapshot_id,
            f"{started_at:.9f}",
        )
    )


def _make_receipt(
    *,
    lease: ScanLease,
    candidate: _ScanCandidate,
    receipt_id: str,
    previous_snapshot_id: str | None,
    started_at: float,
    completed_at: float,
    disposition: str,
    lease_cas_result: str,
) -> ScanReceipt:
    return ScanReceipt(
        receipt_id=receipt_id,
        repository_id=lease.repository_id,
        generation=lease.generation,
        previous_snapshot_id=previous_snapshot_id,
        candidate_snapshot_id=candidate.snapshot_id,
        source_state=candidate.source_state,
        parser_profile_id=PARSER_PROFILE_ID,
        parser_versions=candidate.parser_versions,
        scan_config_digest=candidate.scan_config_digest,
        discovered_file_count=candidate.discovered_file_count,
        discovered_byte_count=candidate.discovered_byte_count,
        omitted_count=sum(count for _, count in candidate.omission_reason_counts),
        omission_reason_counts=candidate.omission_reason_counts,
        error_count=sum(count for _, count in candidate.error_reason_counts),
        error_reason_counts=candidate.error_reason_counts,
        structural_graph_digest=candidate.structural_graph_digest,
        lease_cas_result=lease_cas_result,
        final_disposition=disposition,
        started_at=_utc_iso(started_at),
        completed_at=_utc_iso(completed_at),
    )


def _insert_receipt(conn: sqlite3.Connection, receipt: ScanReceipt) -> None:
    conn.execute(
        """
        INSERT INTO csm_scan_receipts (
            repository_id,
            receipt_id,
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
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        """,
        (
            receipt.repository_id,
            receipt.receipt_id,
            receipt.generation,
            receipt.previous_snapshot_id,
            receipt.candidate_snapshot_id,
            receipt.source_state.manifest_digest,
            1 if receipt.source_state.dirty else 0,
            receipt.source_state.commit_sha,
            receipt.parser_profile_id,
            json.dumps(receipt.parser_versions, separators=(",", ":")),
            receipt.scan_config_digest,
            receipt.discovered_file_count,
            receipt.discovered_byte_count,
            receipt.omitted_count,
            serialize_reason_counts(receipt.omission_reason_counts),
            receipt.error_count,
            serialize_reason_counts(receipt.error_reason_counts),
            receipt.structural_graph_digest,
            receipt.lease_cas_result,
            receipt.final_disposition,
            receipt.started_at,
            receipt.completed_at,
        ),
    )


def _snapshot_semantics_match(
    conn: sqlite3.Connection,
    *,
    candidate: _ScanCandidate,
    repository_id: str,
) -> bool:
    snapshot = conn.execute(
        """
        SELECT *
        FROM csm_snapshots
        WHERE repository_id = ? AND snapshot_id = ?
        """,
        (repository_id, candidate.snapshot_id),
    ).fetchone()
    if snapshot is None:
        return False
    if snapshot["promoted_at"] is None:
        raise CSMScannerError("existing semantic snapshot is not a promoted snapshot")
    expected_header = (
        candidate.source_state.manifest_digest,
        1,
        None,
        PARSER_PROFILE_ID,
        json.dumps(candidate.parser_versions, separators=(",", ":")),
        candidate.scan_config_digest,
        candidate.discovered_file_count,
        candidate.discovered_byte_count,
        candidate.structural_graph_digest,
    )
    actual_header = (
        snapshot["manifest_digest"],
        snapshot["dirty"],
        snapshot["commit_sha"],
        snapshot["parser_profile_id"],
        snapshot["parser_versions_json"],
        snapshot["scan_config_digest"],
        snapshot["discovered_file_count"],
        snapshot["discovered_byte_count"],
        snapshot["structural_graph_digest"],
    )
    if actual_header != expected_header:
        raise CSMScannerError("existing snapshot identity has conflicting semantic metadata")

    stored_nodes = [
        tuple(row)
        for row in conn.execute(
            """
            SELECT
                node_id, node_kind, relative_path, qualified_name,
                start_byte, end_byte, parser_profile_id, parser_adapter_id
            FROM csm_nodes
            WHERE repository_id = ? AND snapshot_id = ?
            ORDER BY node_id
            """,
            (repository_id, candidate.snapshot_id),
        ).fetchall()
    ]
    expected_nodes = [
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
    ]
    if stored_nodes != expected_nodes:
        raise CSMScannerError("existing snapshot node materialization does not match digest")

    stored_edges = [
        tuple(row)
        for row in conn.execute(
            """
            SELECT
                edge.edge_id,
                edge.edge_kind,
                edge.source_node_id,
                edge.target_node_id,
                target.target_kind,
                target.normalized_target,
                edge.source_start_byte,
                edge.source_end_byte,
                edge.parser_adapter_id,
                edge.resolution_rule
            FROM csm_edges AS edge
            LEFT JOIN csm_unresolved_targets AS target
              ON target.repository_id = edge.repository_id
             AND target.snapshot_id = edge.snapshot_id
             AND target.unresolved_target_id = edge.unresolved_target_id
            WHERE edge.repository_id = ? AND edge.snapshot_id = ?
            ORDER BY edge.edge_id
            """,
            (repository_id, candidate.snapshot_id),
        ).fetchall()
    ]
    expected_edges = [
        (
            edge.edge_id,
            edge.edge_kind,
            edge.source_node_id,
            edge.target_node_id,
            edge.unresolved_target.target_kind if edge.unresolved_target else None,
            edge.unresolved_target.normalized_target if edge.unresolved_target else None,
            edge.source_span.start_byte,
            edge.source_span.end_byte,
            edge.parser_adapter_id,
            edge.resolution_rule,
        )
        for edge in candidate.edges
    ]
    if stored_edges != expected_edges:
        raise CSMScannerError("existing snapshot edge materialization does not match digest")
    return True


def _unresolved_target_id(
    *,
    repository_id: str,
    snapshot_id: str,
    unresolved: UnresolvedTarget,
) -> str:
    return _canonical_digest(
        (
            "csm-unresolved-target-v1",
            repository_id,
            snapshot_id,
            unresolved.target_kind,
            unresolved.normalized_target,
        )
    )


def _insert_new_snapshot(
    conn: sqlite3.Connection,
    *,
    lease: ScanLease,
    candidate: _ScanCandidate,
    receipt: ScanReceipt,
    promoted_at: float,
) -> None:
    snapshot = RepositorySnapshot(
        snapshot_id=candidate.snapshot_id,
        repository_id=lease.repository_id,
        generation=lease.generation,
        source_state=candidate.source_state,
        parser_profile_id=PARSER_PROFILE_ID,
        parser_versions=candidate.parser_versions,
        scan_config_digest=candidate.scan_config_digest,
        discovered_file_count=candidate.discovered_file_count,
        discovered_byte_count=candidate.discovered_byte_count,
        structural_graph_digest=candidate.structural_graph_digest,
        scan_receipt_id=receipt.receipt_id,
        promoted_at=_utc_iso(promoted_at),
    )
    conn.execute(
        """
        INSERT INTO csm_snapshots (
            repository_id, snapshot_id, generation, manifest_digest, dirty, commit_sha,
            parser_profile_id, parser_versions_json, scan_config_digest,
            discovered_file_count, discovered_byte_count, structural_graph_digest,
            scan_receipt_id, promoted_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            snapshot.repository_id,
            snapshot.snapshot_id,
            snapshot.generation,
            snapshot.source_state.manifest_digest,
            1 if snapshot.source_state.dirty else 0,
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
    for node in candidate.nodes:
        conn.execute(
            """
            INSERT INTO csm_nodes (
                repository_id, snapshot_id, node_id, generation, node_kind,
                relative_path, qualified_name, start_byte, end_byte,
                parser_profile_id, parser_adapter_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                node.repository_id,
                node.snapshot_id,
                node.node_id,
                node.generation,
                node.node_kind,
                node.relative_path,
                node.qualified_name,
                node.source_span.start_byte,
                node.source_span.end_byte,
                node.parser_profile_id,
                node.parser_adapter_id,
            ),
        )

    unresolved_ids: dict[tuple[str, str], str] = {}
    for edge in candidate.edges:
        if edge.unresolved_target is None:
            continue
        key = (
            edge.unresolved_target.target_kind,
            edge.unresolved_target.normalized_target,
        )
        unresolved_ids.setdefault(
            key,
            _unresolved_target_id(
                repository_id=lease.repository_id,
                snapshot_id=candidate.snapshot_id,
                unresolved=edge.unresolved_target,
            ),
        )
    for (target_kind, normalized_target), target_id in sorted(unresolved_ids.items()):
        conn.execute(
            """
            INSERT INTO csm_unresolved_targets (
                repository_id, snapshot_id, unresolved_target_id,
                target_kind, normalized_target
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                lease.repository_id,
                candidate.snapshot_id,
                target_id,
                target_kind,
                normalized_target,
            ),
        )
    for edge in candidate.edges:
        unresolved_target_id = None
        if edge.unresolved_target is not None:
            unresolved_target_id = unresolved_ids[
                (
                    edge.unresolved_target.target_kind,
                    edge.unresolved_target.normalized_target,
                )
            ]
        conn.execute(
            """
            INSERT INTO csm_edges (
                repository_id, snapshot_id, edge_id, generation, edge_kind,
                source_node_id, target_node_id, unresolved_target_id,
                source_start_byte, source_end_byte, parser_adapter_id, resolution_rule
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                edge.repository_id,
                edge.snapshot_id,
                edge.edge_id,
                edge.generation,
                edge.edge_kind,
                edge.source_node_id,
                edge.target_node_id,
                unresolved_target_id,
                edge.source_span.start_byte,
                edge.source_span.end_byte,
                edge.parser_adapter_id,
                edge.resolution_rule,
            ),
        )


def _finalize_complete_scan(
    conn: sqlite3.Connection,
    *,
    lease: ScanLease,
    candidate: _ScanCandidate,
    receipt_id: str,
    started_at: float,
    completed_at: float,
) -> tuple[ScanReceipt, bool]:
    try:
        conn.execute("BEGIN IMMEDIATE")
        state = _assert_current_lease(conn, lease=lease, now=completed_at)
        registration = conn.execute(
            "SELECT status FROM csm_repositories WHERE repository_id = ?",
            (lease.repository_id,),
        ).fetchone()
        if registration is None or registration["status"] != "ACTIVE":
            raise RepositoryRegistrationError(
                "repository registration is not ACTIVE at finalization"
            )
        previous_snapshot_id = state["current_snapshot_id"]
        existing = conn.execute(
            "SELECT 1 FROM csm_snapshots WHERE repository_id = ? AND snapshot_id = ?",
            (lease.repository_id, candidate.snapshot_id),
        ).fetchone()
        reused = existing is not None
        disposition = "REUSED_SNAPSHOT" if reused else "PROMOTED"
        receipt = _make_receipt(
            lease=lease,
            candidate=candidate,
            receipt_id=receipt_id,
            previous_snapshot_id=previous_snapshot_id,
            started_at=started_at,
            completed_at=completed_at,
            disposition=disposition,
            lease_cas_result="CAS_ACCEPTED",
        )
        _insert_receipt(conn, receipt)
        if reused:
            _snapshot_semantics_match(
                conn,
                candidate=candidate,
                repository_id=lease.repository_id,
            )
        else:
            _insert_new_snapshot(
                conn,
                lease=lease,
                candidate=candidate,
                receipt=receipt,
                promoted_at=completed_at,
            )

        updated = conn.execute(
            """
            UPDATE csm_repository_scan_state
            SET current_snapshot_id = ?,
                current_generation = ?,
                current_receipt_id = ?,
                lease_token = NULL,
                lease_generation = NULL,
                lease_issued_at = NULL,
                lease_expires_at = NULL
            WHERE repository_id = ?
              AND lease_token = ?
              AND lease_generation = ?
              AND (current_generation IS NULL OR current_generation < ?)
            """,
            (
                candidate.snapshot_id,
                lease.generation,
                receipt.receipt_id,
                lease.repository_id,
                lease.holder_token,
                lease.generation,
                lease.generation,
            ),
        )
        if updated.rowcount != 1:
            raise ScanLeaseLostError("current-snapshot CAS rejected stale scanner")
        _insert_lease_event(
            conn,
            lease=lease,
            event_type="FINALIZED",
            observed_at=completed_at,
            reason_code=disposition,
        )
        conn.commit()
        return receipt, reused
    except Exception:
        conn.rollback()
        raise


def _finalize_incomplete_scan(
    conn: sqlite3.Connection,
    *,
    lease: ScanLease,
    candidate: _ScanCandidate,
    receipt_id: str,
    started_at: float,
    completed_at: float,
) -> ScanReceipt:
    try:
        conn.execute("BEGIN IMMEDIATE")
        state = _assert_current_lease(conn, lease=lease, now=completed_at)
        receipt = _make_receipt(
            lease=lease,
            candidate=candidate,
            receipt_id=receipt_id,
            previous_snapshot_id=state["current_snapshot_id"],
            started_at=started_at,
            completed_at=completed_at,
            disposition="INCOMPLETE_REJECTED",
            lease_cas_result="CAS_REJECTED_INCOMPLETE",
        )
        _insert_receipt(conn, receipt)
        updated = conn.execute(
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
            (lease.repository_id, lease.holder_token, lease.generation),
        )
        if updated.rowcount != 1:
            raise ScanLeaseLostError("incomplete-scan lease release lost ownership")
        _insert_lease_event(
            conn,
            lease=lease,
            event_type="RELEASED_INCOMPLETE",
            observed_at=completed_at,
            reason_code="INCOMPLETE_SCAN_NOT_PROMOTED",
        )
        conn.commit()
        return receipt
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
    wall_clock: Callable[[], float] = time.time,
    monotonic_clock: Callable[[], float] = time.monotonic,
    token_factory: Callable[[], str] = _default_token_factory,
) -> ScanOutcome:
    """Explicitly scan a bounded caller-provided Python manifest.

    The filesystem-only Stage-C source attestation is deliberately conservative:
    every candidate is marked ``dirty=True`` with no ``commit_sha``. A future
    separately reviewed Git-aware adapter may prove a clean commit; this scanner
    never invents that claim.
    """
    _require_idle_connection(conn)
    initialize_schema(conn)
    if lease_ttl_seconds <= budget.max_scan_seconds:
        raise ValueError(
            "lease_ttl_seconds must exceed max_scan_seconds; Stage C v1 does not renew leases"
        )
    resolved_root = resolve_repository_root(root)
    _repository_registration_row(
        conn,
        repository_id=repository_id,
        root=resolved_root,
    )
    started_at = float(wall_clock())
    started_monotonic = float(monotonic_clock())
    lease = _acquire_scan_lease(
        conn,
        repository_id=repository_id,
        lease_ttl_seconds=lease_ttl_seconds,
        now=started_at,
        token_factory=token_factory,
    )

    try:
        parsed_files, problems = _discover_and_parse(
            repository_id=repository_id,
            root=resolved_root,
            relative_paths=relative_paths,
            budget=budget,
            monotonic_clock=monotonic_clock,
            started_monotonic=started_monotonic,
        )
        provisional_receipt = _canonical_digest(
            (
                "csm-provisional-receipt-v1",
                repository_id,
                lease.generation,
                lease.holder_token,
            )
        )
        candidate = _materialize_candidate(
            repository_id=repository_id,
            generation=lease.generation,
            receipt_id=provisional_receipt,
            parsed_files=parsed_files,
            problems=problems,
            budget=budget,
        )
        receipt_id = _receipt_id(
            lease=lease,
            candidate_snapshot_id=candidate.snapshot_id,
            started_at=started_at,
        )
        completed_at = float(wall_clock())
        if completed_at >= lease.expires_at:
            raise ScanLeaseLostError("scan lease expired before persistence")

        if candidate.problems:
            receipt = _finalize_incomplete_scan(
                conn,
                lease=lease,
                candidate=candidate,
                receipt_id=receipt_id,
                started_at=started_at,
                completed_at=completed_at,
            )
            return ScanOutcome(
                repository_id=repository_id,
                generation=lease.generation,
                receipt_id=receipt.receipt_id,
                snapshot_id=candidate.snapshot_id,
                structural_graph_digest=candidate.structural_graph_digest,
                final_disposition=receipt.final_disposition,
                promoted=False,
                reused_snapshot=False,
                source_state=candidate.source_state,
                discovered_file_count=candidate.discovered_file_count,
                discovered_byte_count=candidate.discovered_byte_count,
                problems=candidate.omissions,
                omission_reason_counts=candidate.omission_reason_counts,
                error_reason_counts=candidate.error_reason_counts,
            )

        receipt, reused = _finalize_complete_scan(
            conn,
            lease=lease,
            candidate=candidate,
            receipt_id=receipt_id,
            started_at=started_at,
            completed_at=completed_at,
        )
        return ScanOutcome(
            repository_id=repository_id,
            generation=lease.generation,
            receipt_id=receipt.receipt_id,
            snapshot_id=candidate.snapshot_id,
            structural_graph_digest=candidate.structural_graph_digest,
            final_disposition=receipt.final_disposition,
            promoted=True,
            reused_snapshot=reused,
            source_state=candidate.source_state,
            discovered_file_count=candidate.discovered_file_count,
            discovered_byte_count=candidate.discovered_byte_count,
            problems=(),
            omission_reason_counts=(),
            error_reason_counts=(),
        )
    except Exception:
        # A real process crash would skip this cleanup and leave a lease that can only
        # be recovered after expiry. Ordinary Python failures release only this exact
        # token and can never clear a successor's lease.
        try:
            if not conn.in_transaction:
                _release_scan_lease(
                    conn,
                    lease=lease,
                    now=float(wall_clock()),
                    event_type="RELEASED_ERROR",
                    reason_code="SCAN_EXCEPTION",
                )
        except Exception:
            # Preserve the original scanner failure. Expiry recovery remains the
            # fail-closed path when bounded cleanup itself cannot complete.
            pass
        raise


__all__ = [
    "DEFAULT_LEASE_TTL_SECONDS",
    "PARSER_ADAPTER_ID",
    "PARSER_PROFILE_ID",
    "SCANNER_CONTRACT_VERSION",
    "CSMScannerError",
    "RepositoryRegistrationError",
    "ScanLease",
    "ScanLeaseBusyError",
    "ScanLeaseLostError",
    "ScanOutcome",
    "local_root_fingerprint",
    "register_repository",
    "resolve_repository_root",
    "scan_python_repository",
]
