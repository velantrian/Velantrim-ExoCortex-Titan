"""Typed SHADOW_ONLY learning proposals inspired by Velantrim EITI.

No storage, TruthGate, graph, retrieval configuration, or Canon writes occur
here. A patch is a proposal for later validation/evaluation, not evidence.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field, replace
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4

MODES = frozenset({"hybrid", "bm25", "vector", "graph", "lexical"})
CHARGE_SIGNALS = frozenset(
    {"REPETITION", "RECENCY", "SUCCESSFUL_USE", "EXPLICIT_PRIORITY", "TASK_RELEVANCE"}
)
MAX_ITEMS = 256
MAX_TEXT = 4096
MAX_PATTERN = 512


class PatchStatus(str, Enum):
    PROPOSED = "PROPOSED"
    SHADOW_VALID = "SHADOW_VALID"
    SHADOW_REJECTED = "SHADOW_REJECTED"


@dataclass(frozen=True)
class PatchProvenance:
    conversation_id: str
    actor: str
    model: str | None = None
    message_ids: tuple[str, ...] = ()
    observed_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


@dataclass(frozen=True)
class ClaimProposal:
    text: str
    confidence: float
    evidence_refs: tuple[str, ...] = ()
    knowledge_type: str = "unknown"


@dataclass(frozen=True)
class LexicalAssociationProposal:
    surface: str
    concept: str
    weight: float
    language: str = "und"
    domain: str = "general"


@dataclass(frozen=True)
class IntentPatternProposal:
    intent: str
    pattern: str
    confidence: float = 0.5
    language: str = "und"


@dataclass(frozen=True)
class RetrievalPolicyProposal:
    mode: str | None = None
    threshold: float | None = None
    max_items: int | None = None
    graph_depth: int | None = None
    reason: str = ""


@dataclass(frozen=True)
class ChargeSignalProposal:
    target_id: str
    signal_type: str
    magnitude: float
    note: str = ""


@dataclass(frozen=True)
class Finding:
    code: str
    path: str
    message: str


@dataclass(frozen=True)
class ValidationReport:
    findings: tuple[Finding, ...] = ()

    @property
    def is_valid(self) -> bool:
        return not self.findings


@dataclass(frozen=True)
class LearningPatch:
    provenance: PatchProvenance
    claims: tuple[ClaimProposal, ...] = ()
    lexical_associations: tuple[LexicalAssociationProposal, ...] = ()
    intent_patterns: tuple[IntentPatternProposal, ...] = ()
    retrieval_policy: RetrievalPolicyProposal | None = None
    charge_signals: tuple[ChargeSignalProposal, ...] = ()
    patch_id: str = field(default_factory=lambda: f"lp_{uuid4().hex}")
    schema_version: str = "1.0"
    status: PatchStatus = PatchStatus.PROPOSED

    def validate(self) -> ValidationReport:
        out: list[Finding] = []
        _required(out, "provenance.conversation_id", self.provenance.conversation_id)
        _required(out, "provenance.actor", self.provenance.actor)
        _required(out, "provenance.observed_at", self.provenance.observed_at)
        for i, value in enumerate(self.provenance.message_ids):
            _required(out, f"provenance.message_ids[{i}]", value)

        count = (
            len(self.claims)
            + len(self.lexical_associations)
            + len(self.intent_patterns)
            + len(self.charge_signals)
            + int(self.retrieval_policy is not None)
        )
        if count == 0:
            out.append(Finding("LP_EMPTY", "patch", "at least one proposal is required"))
        if count > MAX_ITEMS:
            out.append(Finding("LP_TOO_LARGE", "patch", f"maximum is {MAX_ITEMS} items"))

        for i, item in enumerate(self.claims):
            base = f"claims[{i}]"
            _required(out, f"{base}.text", item.text)
            _unit(out, f"{base}.confidence", item.confidence)
            _required(out, f"{base}.knowledge_type", item.knowledge_type)
            for j, ref in enumerate(item.evidence_refs):
                _required(out, f"{base}.evidence_refs[{j}]", ref)

        for i, item in enumerate(self.lexical_associations):
            base = f"lexical_associations[{i}]"
            for name in ("surface", "concept", "language", "domain"):
                _required(out, f"{base}.{name}", getattr(item, name))
            _unit(out, f"{base}.weight", item.weight)

        for i, item in enumerate(self.intent_patterns):
            base = f"intent_patterns[{i}]"
            _required(out, f"{base}.intent", item.intent)
            _required(out, f"{base}.pattern", item.pattern, MAX_PATTERN)
            _unit(out, f"{base}.confidence", item.confidence)
            if _text_ok(item.pattern, MAX_PATTERN):
                try:
                    re.compile(item.pattern)
                except re.error as exc:
                    out.append(Finding("LP_PATTERN_INVALID", f"{base}.pattern", str(exc)))

        policy = self.retrieval_policy
        if policy is not None:
            values = (policy.mode, policy.threshold, policy.max_items, policy.graph_depth)
            if all(value is None for value in values):
                out.append(Finding("LP_RETRIEVAL_EMPTY", "retrieval_policy", "no change proposed"))
            if policy.mode is not None and policy.mode not in MODES:
                out.append(Finding("LP_RETRIEVAL_MODE", "retrieval_policy.mode", "unsupported mode"))
            if policy.threshold is not None:
                _unit(out, "retrieval_policy.threshold", policy.threshold)
            if policy.max_items is not None and not 1 <= policy.max_items <= 256:
                out.append(Finding("LP_RETRIEVAL_MAX_ITEMS", "retrieval_policy.max_items", "use 1..256"))
            if policy.graph_depth is not None and not 0 <= policy.graph_depth <= 8:
                out.append(Finding("LP_RETRIEVAL_GRAPH_DEPTH", "retrieval_policy.graph_depth", "use 0..8"))

        for i, item in enumerate(self.charge_signals):
            base = f"charge_signals[{i}]"
            _required(out, f"{base}.target_id", item.target_id)
            if item.signal_type not in CHARGE_SIGNALS:
                out.append(Finding("LP_CHARGE_TYPE", f"{base}.signal_type", "unsupported signal"))
            _unit(out, f"{base}.magnitude", item.magnitude)

        return ValidationReport(tuple(out))

    def assert_valid(self) -> None:
        report = self.validate()
        if not report.is_valid:
            detail = "; ".join(f"{x.path}: {x.message}" for x in report.findings)
            raise ValueError(f"invalid LearningPatch: {detail}")

    def normalized(self) -> LearningPatch:
        associations: dict[tuple[str, str, str, str], LexicalAssociationProposal] = {}
        for item in self.lexical_associations:
            candidate = replace(
                item,
                surface=item.surface.strip().casefold(),
                concept=item.concept.strip().casefold(),
                language=item.language.strip().casefold() or "und",
                domain=item.domain.strip().casefold() or "general",
            )
            key = (candidate.surface, candidate.concept, candidate.language, candidate.domain)
            if key not in associations or candidate.weight > associations[key].weight:
                associations[key] = candidate
        return replace(self, lexical_associations=tuple(associations.values()))

    def with_shadow_result(self, *, accepted: bool) -> LearningPatch:
        status = PatchStatus.SHADOW_VALID if accepted else PatchStatus.SHADOW_REJECTED
        return replace(self, status=status)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["status"] = self.status.value
        return payload


def _text_ok(value: object, limit: int = MAX_TEXT) -> bool:
    return isinstance(value, str) and bool(value.strip()) and len(value) <= limit


def _required(out: list[Finding], path: str, value: object, limit: int = MAX_TEXT) -> None:
    if not _text_ok(value, limit):
        out.append(Finding("LP_REQUIRED_TEXT", path, "non-empty bounded text required"))


def _unit(out: list[Finding], path: str, value: object) -> None:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not 0.0 <= float(value) <= 1.0
    ):
        out.append(Finding("LP_UNIT_INTERVAL", path, "number in [0,1] required"))


__all__ = [
    "CHARGE_SIGNALS",
    "MODES",
    "ChargeSignalProposal",
    "ClaimProposal",
    "Finding",
    "IntentPatternProposal",
    "LearningPatch",
    "LexicalAssociationProposal",
    "PatchProvenance",
    "PatchStatus",
    "RetrievalPolicyProposal",
    "ValidationReport",
]
