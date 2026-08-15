from dataclasses import FrozenInstanceError

import pytest

from core.code_structural_memory.contracts import (
    RepositoryRegistration,
    ScanBudget,
    SourceSpan,
    SourceState,
    StructuralEdge,
    StructuralNode,
    UnresolvedTarget,
    make_edge_id,
    make_node_id,
    normalize_relative_path,
)


def test_node_identity_is_portable_across_path_separators() -> None:
    posix = make_node_id(
        repository_id="repo-1",
        node_kind="FUNCTION",
        relative_path="core/example.py",
        qualified_name="example.run",
    )
    windows = make_node_id(
        repository_id="repo-1",
        node_kind="FUNCTION",
        relative_path=r"core\example.py",
        qualified_name="example.run",
    )
    assert posix == windows


def test_node_identity_is_repository_scoped() -> None:
    first = make_node_id(
        repository_id="repo-1",
        node_kind="FUNCTION",
        relative_path="core/example.py",
        qualified_name="example.run",
    )
    second = make_node_id(
        repository_id="repo-2",
        node_kind="FUNCTION",
        relative_path="core/example.py",
        qualified_name="example.run",
    )
    assert first != second


@pytest.mark.parametrize(
    "path",
    [
        "../escape.py",
        "/absolute.py",
        "core/../../escape.py",
        r"C:\repository\absolute.py",
        "C:/repository/absolute.py",
        r"\\server\share\absolute.py",
    ],
)
def test_repository_relative_path_fails_closed_on_escape(path: str) -> None:
    with pytest.raises(ValueError):
        normalize_relative_path(path)


def test_dirty_source_state_cannot_claim_exact_commit_identity() -> None:
    with pytest.raises(ValueError, match="dirty source state"):
        SourceState(manifest_digest="manifest", dirty=True, commit_sha="abc123")


def test_contracts_are_immutable() -> None:
    registration = RepositoryRegistration(
        repository_id="repo-1",
        local_root_fingerprint="root-fingerprint",
        registration_policy_id="policy-1",
        tenant_or_project_scope="project-1",
        created_at="2026-08-15T10:00:00Z",
    )
    with pytest.raises(FrozenInstanceError):
        registration.status = "REVOKED"  # type: ignore[misc]


def test_structural_node_requires_deterministic_identity() -> None:
    node_id = make_node_id(
        repository_id="repo-1",
        node_kind="FUNCTION",
        relative_path="core/example.py",
        qualified_name="example.run",
    )
    node = StructuralNode(
        node_id=node_id,
        repository_id="repo-1",
        snapshot_id="snapshot-1",
        generation=1,
        node_kind="FUNCTION",
        relative_path="core/example.py",
        qualified_name="example.run",
        source_span=SourceSpan(0, 12),
        parser_profile_id="python-v1",
        parser_adapter_id="stdlib-ast-v1",
    )
    assert node.node_id == node_id

    with pytest.raises(ValueError, match="deterministic identity"):
        StructuralNode(
            node_id="fabricated",
            repository_id="repo-1",
            snapshot_id="snapshot-1",
            generation=1,
            node_kind="FUNCTION",
            relative_path="core/example.py",
            qualified_name="example.run",
            source_span=SourceSpan(0, 12),
            parser_profile_id="python-v1",
            parser_adapter_id="stdlib-ast-v1",
        )


def test_edge_identity_preserves_direction() -> None:
    forward = make_edge_id(
        repository_id="repo-1",
        edge_kind="IMPORTS",
        source_node_id="node-a",
        target_node_id="node-b",
    )
    reverse = make_edge_id(
        repository_id="repo-1",
        edge_kind="IMPORTS",
        source_node_id="node-b",
        target_node_id="node-a",
    )
    assert forward != reverse


def test_edge_identity_requires_exactly_one_target_form() -> None:
    with pytest.raises(ValueError, match="exactly one"):
        make_edge_id(
            repository_id="repo-1",
            edge_kind="IMPORTS",
            source_node_id="node-a",
        )

    with pytest.raises(ValueError, match="exactly one"):
        make_edge_id(
            repository_id="repo-1",
            edge_kind="IMPORTS",
            source_node_id="node-a",
            target_node_id="node-b",
            unresolved_target="pkg.missing",
        )


def test_unresolved_structural_edge_uses_typed_normalized_target() -> None:
    unresolved = UnresolvedTarget(
        target_kind="IMPORT_TARGET",
        normalized_target="pkg.missing",
    )
    edge_id = make_edge_id(
        repository_id="repo-1",
        edge_kind="IMPORTS",
        source_node_id="node-a",
        unresolved_target=unresolved.normalized_target,
    )
    edge = StructuralEdge(
        edge_id=edge_id,
        repository_id="repo-1",
        snapshot_id="snapshot-1",
        generation=1,
        edge_kind="IMPORTS",
        source_node_id="node-a",
        unresolved_target=unresolved,
        source_span=SourceSpan(0, 9),
        parser_adapter_id="stdlib-ast-v1",
        resolution_rule="unresolved-import-v1",
    )
    assert edge.unresolved_target == unresolved
    assert edge.target_node_id is None


def test_scan_budget_is_bounded_and_internally_consistent() -> None:
    ScanBudget(
        max_files=100,
        max_file_bytes=1_000_000,
        max_total_bytes=10_000_000,
        max_path_depth=20,
        max_scan_seconds=30.0,
    )

    with pytest.raises(ValueError, match="positive"):
        ScanBudget(
            max_files=0,
            max_file_bytes=1,
            max_total_bytes=1,
            max_path_depth=1,
            max_scan_seconds=1.0,
        )

    with pytest.raises(ValueError, match="must not exceed"):
        ScanBudget(
            max_files=1,
            max_file_bytes=10,
            max_total_bytes=5,
            max_path_depth=1,
            max_scan_seconds=1.0,
        )
