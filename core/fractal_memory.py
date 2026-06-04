"""
Fractal Memory contracts for Velantrim ExoCortex.

This module is intentionally additive. It formalizes the L0 -> L1 -> L2 ->
Pending -> TruthGate -> L3 path and the recursive retrieval trace shape, but it
does not replace memory.py, pipeline.py, HybridRetriever, TRACE, or TruthGate.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any, TypeVar


class MemoryLayer(str, Enum):
    """Canonical Fractal Memory layers."""

    L0_RAW = "L0_RAW"
    L1_WORKING = "L1_WORKING"
    L2_EPISODIC = "L2_EPISODIC"
    PENDING = "PENDING"
    L3_CANONICAL = "L3_CANONICAL"


class TruthStatus(str, Enum):
    """Truth lifecycle status used by Fractal Memory contracts."""

    RAW = "RAW"
    PENDING = "PENDING"
    UNVERIFIED = "UNVERIFIED"
    HYPOTHESIS = "HYPOTHESIS"
    VERIFIED = "VERIFIED"
    CONTESTED = "CONTESTED"
    RETRACTED = "RETRACTED"
    CANON = "CANON"


class FractalNodeLevel(str, Enum):
    """Levels used by a MemTree-like hierarchy."""

    ROOT = "root"
    DOMAIN = "domain"
    SUBJECT = "subject"
    CONCEPT = "concept"
    RELATION = "relation"
    MECHANISM = "mechanism"
    EVIDENCE = "evidence"
    PRINCIPLE = "principle"
    DETAIL = "detail"


class RetrievalStage(str, Enum):
    """Stages of the future Hierarchical Memory Router."""

    INTENT_DETECTION = "intent_detection"
    DOMAIN_SELECTION = "domain_selection"
    LEVEL_SELECTION = "level_selection"
    RECURSIVE_RETRIEVAL = "recursive_retrieval"
    DETAIL_EXPANSION = "detail_expansion"
    EVIDENCE_CHECK = "evidence_check"
    TRACE = "trace"


class RetrievalDecisionReason(str, Enum):
    """Why the router moved through a node."""

    SEMANTIC_MATCH = "SEMANTIC_MATCH"
    DOMAIN_MATCH = "DOMAIN_MATCH"
    LEVEL_MATCH = "LEVEL_MATCH"
    HIERARCHICAL_DESCENT = "HIERARCHICAL_DESCENT"
    EVIDENCE_FOUND = "EVIDENCE_FOUND"
    CONFIDENCE_LOW = "CONFIDENCE_LOW"
    PRUNED = "PRUNED"


class CompressionStage(str, Enum):
    """Compression stages across Fractal Memory layers."""

    L0_TO_L1 = "L0_TO_L1"
    L1_TO_L2 = "L1_TO_L2"
    L2_TO_PENDING = "L2_TO_PENDING"
    PENDING_TO_L3 = "PENDING_TO_L3"


class GuardianLayer(str, Enum):
    """Multi-level Guardian scopes."""

    L1_RETRIEVAL = "L1_RETRIEVAL"
    L2_GENERATION = "L2_GENERATION"
    L3_ACTION = "L3_ACTION"


EnumT = TypeVar("EnumT", bound=Enum)


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _enum_value(value: str | EnumT, enum_cls: type[EnumT], field_name: str) -> str:
    if isinstance(value, enum_cls):
        return str(value.value)
    if isinstance(value, str):
        for item in enum_cls:
            if value == item.value or value == item.name:
                return str(item.value)
            if value.lower() == str(item.value).lower():
                return str(item.value)
            if value.upper() == item.name.upper():
                return str(item.value)
    allowed = ", ".join(str(item.value) for item in enum_cls)
    raise ValueError(f"{field_name} must be one of: {allowed}")


def _check_probability(value: float, field_name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a number") from exc
    if number < 0.0 or number > 1.0:
        raise ValueError(f"{field_name} must be between 0.0 and 1.0")
    return number


@dataclass
class MemoryRecord:
    """
    Minimal record shape for L0/L1/L2/Pending/L3 movement.

    The key contract: L3 is canonical graph memory. A record can enter L3 only
    after provenance, Guardian, and TruthGate checks are visible.
    """

    memory_id: str
    layer: str | MemoryLayer
    content: str
    source_refs: list[str] = field(default_factory=list)
    derived_from: str | None = None
    parent_id: str | None = None
    truth_status: str | TruthStatus = TruthStatus.RAW
    confidence: float = 0.5
    created_at: str = field(default_factory=_utc_now)
    updated_at: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.memory_id:
            raise ValueError("memory_id is required")
        if not self.content:
            raise ValueError("content is required")
        self.layer = _enum_value(self.layer, MemoryLayer, "layer")
        self.truth_status = _enum_value(self.truth_status, TruthStatus, "truth_status")
        self.confidence = _check_probability(self.confidence, "confidence")
        self.source_refs = [str(ref) for ref in self.source_refs if ref]

    @property
    def provenance_refs(self) -> list[str]:
        refs = list(self.source_refs)
        if self.derived_from:
            refs.append(self.derived_from)
        return refs

    def can_enter_l3(self, *, guardian_verified: bool) -> bool:
        """
        Return True only when promotion to L3 is contractually allowed.

        This is a guardrail, not a write path. Runtime promotion still belongs to
        TruthGate/pipeline/store code.
        """

        allowed_layer = self.layer in {
            MemoryLayer.L2_EPISODIC.value,
            MemoryLayer.PENDING.value,
            MemoryLayer.L3_CANONICAL.value,
        }
        allowed_status = self.truth_status in {
            TruthStatus.VERIFIED.value,
            TruthStatus.CANON.value,
        }
        return (
            allowed_layer
            and allowed_status
            and guardian_verified
            and bool(self.provenance_refs)
            and self.confidence >= 0.5
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MemoryRecord:
        return cls(**data)


@dataclass
class FractalMemoryNode:
    """MemTree-like node for hierarchical memory navigation."""

    node_id: str
    level: str | FractalNodeLevel
    summary: str
    parent_id: str | None = None
    children: list[str] = field(default_factory=list)
    details_refs: list[str] = field(default_factory=list)
    source_refs: list[str] = field(default_factory=list)
    truth_status: str | TruthStatus = TruthStatus.UNVERIFIED
    guardian_verified: bool = False
    last_accessed: str = field(default_factory=_utc_now)
    compression_level: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.node_id:
            raise ValueError("node_id is required")
        if not self.summary:
            raise ValueError("summary is required")
        self.level = _enum_value(self.level, FractalNodeLevel, "level")
        self.truth_status = _enum_value(self.truth_status, TruthStatus, "truth_status")
        if self.compression_level < 0:
            raise ValueError("compression_level must be >= 0")
        self.children = [str(child) for child in self.children if child]
        self.details_refs = [str(ref) for ref in self.details_refs if ref]
        self.source_refs = [str(ref) for ref in self.source_refs if ref]

    def add_child(self, child_id: str) -> None:
        if child_id and child_id not in self.children:
            self.children.append(str(child_id))

    def add_detail_ref(self, ref_id: str) -> None:
        if ref_id and ref_id not in self.details_refs:
            self.details_refs.append(str(ref_id))

    def add_source_ref(self, ref_id: str) -> None:
        if ref_id and ref_id not in self.source_refs:
            self.source_refs.append(str(ref_id))

    def touch(self) -> None:
        self.last_accessed = _utc_now()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FractalMemoryNode:
        return cls(**data)


@dataclass
class RetrievalRouteStep:
    """One step in recursive retrieval navigation."""

    stage: str | RetrievalStage
    level: str | FractalNodeLevel | None = None
    node_id: str | None = None
    action: str = "visit"
    score: float = 0.0
    reason: str | None = None
    evidence_refs: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.stage = _enum_value(self.stage, RetrievalStage, "stage")
        if self.level is not None:
            self.level = _enum_value(self.level, FractalNodeLevel, "level")
        self.score = _check_probability(self.score, "score")
        self.evidence_refs = [str(ref) for ref in self.evidence_refs if ref]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RetrievalRouteStep:
        return cls(**data)


@dataclass
class RetrievalPathDecision:
    """A decision made while traversing the memory tree."""

    node_id: str
    reason: str | RetrievalDecisionReason
    confidence: float
    depth: int = 0
    stage: str | RetrievalStage | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        if not self.node_id:
            raise ValueError("node_id is required")
        self.reason = _enum_value(self.reason, RetrievalDecisionReason, "reason")
        if self.stage is not None:
            self.stage = _enum_value(self.stage, RetrievalStage, "stage")
        self.confidence = _check_probability(self.confidence, "confidence")
        if self.depth < 0:
            raise ValueError("depth must be >= 0")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RetrievalPathDecision:
        return cls(**data)


@dataclass
class RetrievalPath:
    """
    Analyzable path through Fractal Memory.

    TraceRecord answers "what evidence was used"; RetrievalPath answers "how the
    router moved through the tree to find that evidence".
    """

    start_node: str
    traversed_nodes: list[str] = field(default_factory=list)
    decisions: list[RetrievalPathDecision] = field(default_factory=list)
    end_node: str | None = None
    total_depth: int = 0
    time_ms: float = 0.0

    def __post_init__(self) -> None:
        if not self.start_node:
            raise ValueError("start_node is required")
        self.traversed_nodes = [str(node) for node in self.traversed_nodes if node]
        if not self.traversed_nodes:
            self.traversed_nodes = [self.start_node]
        if self.start_node not in self.traversed_nodes:
            self.traversed_nodes.insert(0, self.start_node)
        self.decisions = [
            decision
            if isinstance(decision, RetrievalPathDecision)
            else RetrievalPathDecision.from_dict(decision)
            for decision in self.decisions
        ]
        if self.end_node is None:
            self.end_node = self.traversed_nodes[-1]
        if self.total_depth < 0:
            raise ValueError("total_depth must be >= 0")
        if self.total_depth == 0 and self.decisions:
            self.total_depth = max(decision.depth for decision in self.decisions)
        if self.time_ms < 0:
            raise ValueError("time_ms must be >= 0")

    @property
    def reached_evidence(self) -> bool:
        return any(
            decision.reason == RetrievalDecisionReason.EVIDENCE_FOUND.value
            for decision in self.decisions
        )

    @property
    def visited_count(self) -> int:
        return len(set(self.traversed_nodes))

    def add_decision(self, decision: RetrievalPathDecision) -> None:
        if decision.node_id not in self.traversed_nodes:
            self.traversed_nodes.append(decision.node_id)
        self.decisions.append(decision)
        self.end_node = decision.node_id
        self.total_depth = max(self.total_depth, decision.depth)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["decisions"] = [decision.to_dict() for decision in self.decisions]
        data["reached_evidence"] = self.reached_evidence
        data["visited_count"] = self.visited_count
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RetrievalPath:
        clean = dict(data)
        clean.pop("reached_evidence", None)
        clean.pop("visited_count", None)
        return cls(**clean)


@dataclass
class CompressionRule:
    """Contract for one Fractal Memory compression step."""

    stage: str | CompressionStage
    input_layer: str | MemoryLayer
    output_layer: str | MemoryLayer
    operations: list[str]
    risk_controls: list[str] = field(default_factory=list)
    max_ratio: float | None = None

    def __post_init__(self) -> None:
        self.stage = _enum_value(self.stage, CompressionStage, "stage")
        self.input_layer = _enum_value(self.input_layer, MemoryLayer, "input_layer")
        self.output_layer = _enum_value(self.output_layer, MemoryLayer, "output_layer")
        self.operations = [str(item) for item in self.operations if item]
        self.risk_controls = [str(item) for item in self.risk_controls if item]
        if not self.operations:
            raise ValueError("operations are required")
        if self.max_ratio is not None and self.max_ratio <= 0:
            raise ValueError("max_ratio must be > 0")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GuardianPolicy:
    """Contract for a Guardian layer without runtime enforcement."""

    layer: str | GuardianLayer
    scope: str
    checks: list[str]
    blocks_l3_promotion: bool = False

    def __post_init__(self) -> None:
        self.layer = _enum_value(self.layer, GuardianLayer, "layer")
        if not self.scope:
            raise ValueError("scope is required")
        self.checks = [str(item) for item in self.checks if item]
        if not self.checks:
            raise ValueError("checks are required")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def default_compression_strategy() -> list[CompressionRule]:
    """Canonical non-runtime compression strategy for L0 -> L3."""

    return [
        CompressionRule(
            stage=CompressionStage.L0_TO_L1,
            input_layer=MemoryLayer.L0_RAW,
            output_layer=MemoryLayer.L1_WORKING,
            operations=["noise_filtering", "deduplication", "tokenization"],
            risk_controls=["keep_raw_immutable", "preserve_source_refs"],
            max_ratio=1.0,
        ),
        CompressionRule(
            stage=CompressionStage.L1_TO_L2,
            input_layer=MemoryLayer.L1_WORKING,
            output_layer=MemoryLayer.L2_EPISODIC,
            operations=["episode_summary", "entity_extraction", "relation_extraction"],
            risk_controls=["store_derivation_chain", "mark_unverified"],
        ),
        CompressionRule(
            stage=CompressionStage.L2_TO_PENDING,
            input_layer=MemoryLayer.L2_EPISODIC,
            output_layer=MemoryLayer.PENDING,
            operations=["generalization", "principle_candidate", "conflict_scan"],
            risk_controls=["truth_gate_required", "guardian_required"],
        ),
        CompressionRule(
            stage=CompressionStage.PENDING_TO_L3,
            input_layer=MemoryLayer.PENDING,
            output_layer=MemoryLayer.L3_CANONICAL,
            operations=["verification", "graph_integration", "trace_persist"],
            risk_controls=["provenance_required", "contestable_status"],
        ),
    ]


def default_guardian_policy() -> list[GuardianPolicy]:
    """Canonical non-runtime policy for multi-level Guardian checks."""

    return [
        GuardianPolicy(
            layer=GuardianLayer.L1_RETRIEVAL,
            scope="retrieval",
            checks=["source_reliability", "dangerous_content_filter", "stale_context_check"],
        ),
        GuardianPolicy(
            layer=GuardianLayer.L2_GENERATION,
            scope="generation",
            checks=["trace_coverage", "faithfulness_check", "contradiction_disclosure"],
        ),
        GuardianPolicy(
            layer=GuardianLayer.L3_ACTION,
            scope="action_or_canon_promotion",
            checks=["truth_gate_passed", "provenance_present", "policy_boundary_check"],
            blocks_l3_promotion=True,
        ),
    ]


@dataclass
class TraceRecord:
    """
    High-level TRACE envelope for recursive retrieval.

    It complements core.trace.build_trace(), which remains the runtime fact-level
    provenance builder.
    """

    trace_id: str
    query: str
    retrieval_mode: str = "recursive"
    route: list[RetrievalRouteStep] = field(default_factory=list)
    retrieval_path: RetrievalPath | None = None
    source_refs: list[str] = field(default_factory=list)
    guardian_decision: str = "not_run"
    truth_gate_status: str = "not_run"
    created_at: str = field(default_factory=_utc_now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.trace_id:
            raise ValueError("trace_id is required")
        if not self.query:
            raise ValueError("query is required")
        self.source_refs = [str(ref) for ref in self.source_refs if ref]
        self.route = [
            step if isinstance(step, RetrievalRouteStep) else RetrievalRouteStep.from_dict(step)
            for step in self.route
        ]
        if self.retrieval_path is not None and not isinstance(self.retrieval_path, RetrievalPath):
            self.retrieval_path = RetrievalPath.from_dict(self.retrieval_path)

    def add_step(self, step: RetrievalRouteStep) -> None:
        self.route.append(step)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["route"] = [step.to_dict() for step in self.route]
        if self.retrieval_path is not None:
            data["retrieval_path"] = self.retrieval_path.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TraceRecord:
        return cls(**data)


@dataclass
class RecursiveRetrievalRequest:
    """Request contract for the future recursive retrieval mode."""

    query: str
    retrieval_mode: str = "recursive"
    start_level: str | FractalNodeLevel = FractalNodeLevel.DOMAIN
    max_depth: int = 4
    expand_if_confidence_below: float = 0.72
    return_trace: bool = True
    domain: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.query:
            raise ValueError("query is required")
        if self.retrieval_mode != "recursive":
            raise ValueError("retrieval_mode must be 'recursive'")
        self.start_level = _enum_value(self.start_level, FractalNodeLevel, "start_level")
        if self.max_depth < 1:
            raise ValueError("max_depth must be >= 1")
        self.expand_if_confidence_below = _check_probability(
            self.expand_if_confidence_below,
            "expand_if_confidence_below",
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


__all__ = [
    "CompressionRule",
    "CompressionStage",
    "FractalMemoryNode",
    "FractalNodeLevel",
    "GuardianLayer",
    "GuardianPolicy",
    "MemoryLayer",
    "MemoryRecord",
    "RecursiveRetrievalRequest",
    "RetrievalDecisionReason",
    "RetrievalPath",
    "RetrievalPathDecision",
    "RetrievalRouteStep",
    "RetrievalStage",
    "TraceRecord",
    "TruthStatus",
    "default_compression_strategy",
    "default_guardian_policy",
]
