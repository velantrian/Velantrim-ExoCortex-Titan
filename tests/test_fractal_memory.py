from __future__ import annotations

import pytest

from core.fractal_memory import (
    CompressionStage,
    FractalMemoryNode,
    FractalNodeLevel,
    GuardianLayer,
    MemoryLayer,
    MemoryRecord,
    RecursiveRetrievalRequest,
    RetrievalDecisionReason,
    RetrievalPath,
    RetrievalPathDecision,
    RetrievalRouteStep,
    RetrievalStage,
    TraceRecord,
    TruthStatus,
    default_compression_strategy,
    default_guardian_policy,
)


def test_memory_record_l3_promotion_requires_provenance_guardian_and_truth() -> None:
    record = MemoryRecord(
        memory_id="episode_tree_001",
        layer=MemoryLayer.L2_EPISODIC,
        content="Trees are organisms that participate in ecosystems.",
        source_refs=["raw_tree_001"],
        truth_status=TruthStatus.VERIFIED,
        confidence=0.82,
    )

    assert record.can_enter_l3(guardian_verified=True) is True
    assert record.can_enter_l3(guardian_verified=False) is False

    no_source = MemoryRecord(
        memory_id="episode_tree_002",
        layer=MemoryLayer.L2_EPISODIC,
        content="Trees matter.",
        truth_status=TruthStatus.VERIFIED,
        confidence=0.82,
    )
    assert no_source.can_enter_l3(guardian_verified=True) is False

    raw = MemoryRecord(
        memory_id="raw_tree_001",
        layer=MemoryLayer.L0_RAW,
        content="Original raw text",
        source_refs=["file.pdf"],
        truth_status=TruthStatus.VERIFIED,
        confidence=0.9,
    )
    assert raw.can_enter_l3(guardian_verified=True) is False


def test_fractal_memory_node_keeps_tree_refs_without_duplicates() -> None:
    node = FractalMemoryNode(
        node_id="domain_biology",
        level=FractalNodeLevel.DOMAIN,
        summary="Biology domain",
        truth_status=TruthStatus.UNVERIFIED,
    )

    node.add_child("concept_tree")
    node.add_child("concept_tree")
    node.add_detail_ref("fact_tree_001")
    node.add_source_ref("raw_tree_001")

    data = node.to_dict()
    assert data["children"] == ["concept_tree"]
    assert data["details_refs"] == ["fact_tree_001"]
    assert data["source_refs"] == ["raw_tree_001"]

    restored = FractalMemoryNode.from_dict(data)
    assert restored.node_id == "domain_biology"
    assert restored.level == "domain"


def test_trace_record_serializes_recursive_route() -> None:
    path = RetrievalPath(
        start_node="root",
        traversed_nodes=["root", "domain_biology", "fact_tree_001"],
        decisions=[
            RetrievalPathDecision(
                node_id="domain_biology",
                reason=RetrievalDecisionReason.DOMAIN_MATCH,
                confidence=0.91,
                depth=1,
            ),
            RetrievalPathDecision(
                node_id="fact_tree_001",
                reason=RetrievalDecisionReason.EVIDENCE_FOUND,
                confidence=0.86,
                depth=2,
            ),
        ],
        time_ms=12.5,
    )
    trace = TraceRecord(trace_id="trace_tree_001", query="Why are trees important?")
    trace.retrieval_path = path
    trace.add_step(
        RetrievalRouteStep(
            stage=RetrievalStage.DOMAIN_SELECTION,
            level=FractalNodeLevel.DOMAIN,
            node_id="domain_biology",
            score=0.91,
            reason="biology terms matched",
            evidence_refs=["raw_tree_001"],
        )
    )
    trace.add_step(
        RetrievalRouteStep(
            stage=RetrievalStage.EVIDENCE_CHECK,
            level=FractalNodeLevel.EVIDENCE,
            node_id="fact_tree_001",
            score=0.86,
        )
    )

    data = trace.to_dict()
    assert data["retrieval_mode"] == "recursive"
    assert [step["stage"] for step in data["route"]] == [
        "domain_selection",
        "evidence_check",
    ]
    assert data["retrieval_path"]["reached_evidence"] is True
    assert data["retrieval_path"]["visited_count"] == 3

    restored = TraceRecord.from_dict(data)
    assert restored.route[0].node_id == "domain_biology"
    assert restored.retrieval_path is not None
    assert restored.retrieval_path.end_node == "fact_tree_001"


def test_recursive_retrieval_request_validates_contract() -> None:
    request = RecursiveRetrievalRequest(
        query="Why are trees important?",
        start_level="domain",
        max_depth=4,
        expand_if_confidence_below=0.72,
    )

    assert request.to_dict()["retrieval_mode"] == "recursive"
    assert request.to_dict()["start_level"] == "domain"

    with pytest.raises(ValueError):
        RecursiveRetrievalRequest(query="", max_depth=4)

    with pytest.raises(ValueError):
        RecursiveRetrievalRequest(query="x", max_depth=0)

    with pytest.raises(ValueError):
        RecursiveRetrievalRequest(query="x", expand_if_confidence_below=1.2)


def test_retrieval_path_tracks_decisions_and_depth() -> None:
    path = RetrievalPath(start_node="root")
    path.add_decision(
        RetrievalPathDecision(
            node_id="domain_science",
            reason="DOMAIN_MATCH",
            confidence=0.9,
            depth=1,
            stage=RetrievalStage.DOMAIN_SELECTION,
        )
    )
    path.add_decision(
        RetrievalPathDecision(
            node_id="concept_tree",
            reason="CONFIDENCE_LOW",
            confidence=0.62,
            depth=2,
            stage=RetrievalStage.DETAIL_EXPANSION,
        )
    )

    data = path.to_dict()
    assert data["traversed_nodes"] == ["root", "domain_science", "concept_tree"]
    assert data["total_depth"] == 2
    assert data["reached_evidence"] is False
    assert RetrievalPath.from_dict(data).end_node == "concept_tree"


def test_default_compression_strategy_keeps_truth_gate_boundary() -> None:
    strategy = default_compression_strategy()

    assert [rule.stage for rule in strategy] == [
        CompressionStage.L0_TO_L1.value,
        CompressionStage.L1_TO_L2.value,
        CompressionStage.L2_TO_PENDING.value,
        CompressionStage.PENDING_TO_L3.value,
    ]
    pending_rule = strategy[2].to_dict()
    assert pending_rule["input_layer"] == MemoryLayer.L2_EPISODIC.value
    assert pending_rule["output_layer"] == MemoryLayer.PENDING.value
    assert "truth_gate_required" in pending_rule["risk_controls"]


def test_default_guardian_policy_has_l1_l2_l3_scopes() -> None:
    policy = default_guardian_policy()

    assert [item.layer for item in policy] == [
        GuardianLayer.L1_RETRIEVAL.value,
        GuardianLayer.L2_GENERATION.value,
        GuardianLayer.L3_ACTION.value,
    ]
    assert policy[-1].blocks_l3_promotion is True
    assert "provenance_present" in policy[-1].checks
