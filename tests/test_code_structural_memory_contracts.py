from dataclasses import FrozenInstanceError

import pytest

from core.code_structural_memory.contracts import (
    RepositoryRegistration,
    RepositorySnapshot,
    ScanBudget,
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


def _snapshot_identity(
    *,
    source_state: SourceState | None = None,
    parser_profile_id: str = "python-v1",
    parser_versions: tuple[tuple[str, str], ...] = (("python", "3.14"),),
    scan_config_digest: str = "config",
    structural_graph_digest: str = "graph",
) -> str:
    return make_snapshot_id(
        repository_id="repo-1",
        source_state=source_state
        or SourceState(manifest_digest="manifest", dirty=False, commit_sha="abc123"),
        parser_profile_id=parser_profile_id,
        parser_versions=parser_versions,
        scan_config_digest=scan_config_digest,
        structural_graph_digest=structural_graph_digest,
    )


def _receipt(
    *,
    source_state: SourceState | None = None,
    candidate_snapshot_id: str | None = None,
    omitted_count: int = 0,
    omission_reason_counts: tuple[tuple[str, int], ...] = (),
    error_count: int = 0,
    error_reason_counts: tuple[tuple[str, int], ...] = (),
) -> ScanReceipt:
    state = source_state or SourceState(
        manifest_digest="manifest",
        dirty=False,
        commit_sha="abc123",
    )
    snapshot_id = candidate_snapshot_id or _snapshot_identity(source_state=state)
    return ScanReceipt(
        receipt_id="receipt-1",
        repository_id="repo-1",
        generation=1,
        candidate_snapshot_id=snapshot_id,
        source_state=state,
        parser_profile_id="python-v1",
        parser_versions=(("python", "3.14"),),
        scan_config_digest="config",
        discovered_file_count=1,
        discovered_byte_count=10,
        omitted_count=omitted_count,
        omission_reason_counts=omission_reason_counts,
        error_count=error_count,
        error_reason_counts=error_reason_counts,
        structural_graph_digest="graph",
        lease_cas_result="NOT_IMPLEMENTED_STAGE_B",
        final_disposition="SCHEMA_FIXTURE",
        started_at="2026-08-15T10:00:00Z",
        completed_at="2026-08-15T10:00:01Z",
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


def test_source_state_requires_boolean_dirty_marker() -> None:
    with pytest.raises(TypeError, match="dirty must be a bool"):
        SourceState(manifest_digest="manifest", dirty=1)  # type: ignore[arg-type]


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


def test_snapshot_identity_is_canonical_and_parser_order_independent() -> None:
    first = _snapshot_identity(
        parser_versions=(("tree-sitter", "1"), ("python", "3.14"))
    )
    second = _snapshot_identity(
        parser_versions=(("python", "3.14"), ("tree-sitter", "1"))
    )
    assert first == second


def test_snapshot_identity_excludes_generation_and_promoted_at() -> None:
    snapshot_id = _snapshot_identity()
    common = dict(
        snapshot_id=snapshot_id,
        repository_id="repo-1",
        source_state=SourceState(
            manifest_digest="manifest",
            dirty=False,
            commit_sha="abc123",
        ),
        parser_profile_id="python-v1",
        parser_versions=(("python", "3.14"),),
        scan_config_digest="config",
        discovered_file_count=1,
        discovered_byte_count=10,
        structural_graph_digest="graph",
        scan_receipt_id="receipt-1",
    )
    generation_seven = RepositorySnapshot(generation=7, promoted_at=None, **common)
    generation_eight = RepositorySnapshot(
        generation=8,
        promoted_at="2026-08-15T10:00:02Z",
        **common,
    )
    assert generation_seven.snapshot_id == generation_eight.snapshot_id == snapshot_id


def test_snapshot_identity_changes_with_semantic_inputs() -> None:
    clean_without_commit = SourceState(manifest_digest="manifest", dirty=False)
    dirty = SourceState(manifest_digest="manifest", dirty=True)
    base = _snapshot_identity(source_state=clean_without_commit)

    assert _snapshot_identity(
        source_state=SourceState(manifest_digest="manifest-2", dirty=False)
    ) != base
    assert _snapshot_identity(source_state=dirty) != base
    assert _snapshot_identity(
        source_state=SourceState(
            manifest_digest="manifest",
            dirty=False,
            commit_sha="commit-a",
        )
    ) != _snapshot_identity(
        source_state=SourceState(
            manifest_digest="manifest",
            dirty=False,
            commit_sha="commit-b",
        )
    )
    assert _snapshot_identity(parser_profile_id="python-v2") != base
    assert _snapshot_identity(parser_versions=(("python", "3.15"),)) != base
    assert _snapshot_identity(scan_config_digest="config-2") != base
    assert _snapshot_identity(structural_graph_digest="graph-2") != base


def test_repository_snapshot_rejects_wrong_supplied_snapshot_id() -> None:
    with pytest.raises(ValueError, match="content-addressed identity"):
        RepositorySnapshot(
            snapshot_id="fabricated",
            repository_id="repo-1",
            generation=1,
            source_state=SourceState(
                manifest_digest="manifest",
                dirty=False,
                commit_sha="abc123",
            ),
            parser_profile_id="python-v1",
            parser_versions=(("python", "3.14"),),
            scan_config_digest="config",
            discovered_file_count=1,
            discovered_byte_count=10,
            structural_graph_digest="graph",
            scan_receipt_id="receipt-1",
        )


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


def test_receipt_clean_source_state_with_commit_is_valid() -> None:
    receipt = _receipt()
    assert receipt.source_state.commit_sha == "abc123"
    assert receipt.source_state.dirty is False


def test_receipt_dirty_source_state_with_commit_is_rejected() -> None:
    with pytest.raises(ValueError, match="dirty source state"):
        _receipt(
            source_state=SourceState(
                manifest_digest="manifest",
                dirty=True,
                commit_sha="abc123",
            )
        )


def test_receipt_source_state_is_bound_to_candidate_snapshot_identity() -> None:
    clean = SourceState(manifest_digest="manifest", dirty=False, commit_sha="abc123")
    dirty = SourceState(manifest_digest="manifest", dirty=True)
    clean_snapshot_id = _snapshot_identity(source_state=clean)
    assert clean_snapshot_id != _snapshot_identity(source_state=dirty)

    with pytest.raises(ValueError, match="candidate_snapshot_id"):
        _receipt(source_state=dirty, candidate_snapshot_id=clean_snapshot_id)


def test_reason_counts_are_sorted_and_reconciled() -> None:
    receipt = _receipt(
        omitted_count=3,
        omission_reason_counts=(("zeta", 1), ("alpha", 2)),
        error_count=2,
        error_reason_counts=(("parse", 2),),
    )
    assert receipt.omission_reason_counts == (("alpha", 2), ("zeta", 1))
    assert receipt.error_reason_counts == (("parse", 2),)


def test_zero_reason_totals_require_empty_collections() -> None:
    receipt = _receipt()
    assert receipt.omission_reason_counts == ()
    assert receipt.error_reason_counts == ()

    with pytest.raises(ValueError, match="sum to omitted_count"):
        _receipt(omitted_count=0, omission_reason_counts=(("ignored", 1),))


def test_reason_count_sum_mismatch_is_rejected() -> None:
    with pytest.raises(ValueError, match="sum to omitted_count"):
        _receipt(omitted_count=2, omission_reason_counts=(("ignored", 1),))
    with pytest.raises(ValueError, match="sum to error_count"):
        _receipt(error_count=2, error_reason_counts=(("parse", 1),))


def test_negative_reason_totals_are_rejected() -> None:
    with pytest.raises(ValueError, match="omitted_count must be non-negative"):
        _receipt(omitted_count=-1)
    with pytest.raises(ValueError, match="error_count must be non-negative"):
        _receipt(error_count=-1)


def test_invalid_reason_entries_are_rejected() -> None:
    with pytest.raises(ValueError, match="positive integers"):
        _receipt(omitted_count=1, omission_reason_counts=(("ignored", -1),))
    with pytest.raises(ValueError, match="non-empty"):
        _receipt(omitted_count=1, omission_reason_counts=((" ", 1),))
    with pytest.raises(ValueError, match="duplicate reasons"):
        _receipt(
            omitted_count=2,
            omission_reason_counts=(("ignored", 1), ("ignored", 1)),
        )


def test_reason_count_serialization_is_deterministic() -> None:
    first = serialize_reason_counts((("zeta", 1), ("alpha", 2)))
    second = serialize_reason_counts((("alpha", 2), ("zeta", 1)))
    assert first == second == '[["alpha",2],["zeta",1]]'
