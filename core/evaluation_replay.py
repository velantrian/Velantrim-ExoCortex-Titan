"""Offline deterministic replay evaluation primitives for Titan.

This module is deliberately disconnected from the production query and write paths.
It compares recorded, fixture-bound evaluation receipts and never invokes providers,
tools, storage backends, Canon writes, ESM transitions, or irreversible effects.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, fields, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Self

PROTOCOL_VERSION = "erp-1"


class StabilityClass(str, Enum):
    """Comparison result classification."""

    BIT_IDENTICAL = "BIT_IDENTICAL"
    STRUCTURALLY_EQUIVALENT = "STRUCTURALLY_EQUIVALENT"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    REGRESSION = "REGRESSION"
    INVALID_RUN = "INVALID_RUN"


def _canonicalize(value: Any) -> Any:
    """Convert supported values into deterministic JSON-compatible primitives."""
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value) and not isinstance(value, type):
        return {item.name: _canonicalize(getattr(value, item.name)) for item in fields(value)}
    if isinstance(value, Mapping):
        return {
            str(key): _canonicalize(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (list, tuple)):
        return [_canonicalize(item) for item in value]
    if isinstance(value, (set, frozenset)):
        normalized = [_canonicalize(item) for item in value]
        return sorted(normalized, key=canonical_json)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("canonical JSON does not allow NaN or infinite floats")
        return value
    if value is None or isinstance(value, (bool, int, str)):
        return value
    raise TypeError(f"unsupported canonical JSON value: {type(value).__name__}")


def canonical_json(value: Any) -> str:
    """Return UTF-8-safe canonical JSON with sorted keys and compact separators."""
    return json.dumps(
        _canonicalize(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def stable_digest(value: Any) -> str:
    """Return a SHA-256 digest of canonical JSON."""
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _require_text(value: str, field_name: str) -> None:
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")


def _require_unique(values: Sequence[str], field_name: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{field_name} must not contain duplicates")


def _require_mapping(value: Any, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{field_name} must be a JSON object")
    return value


def _string_tuple(value: Any, field_name: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise TypeError(f"{field_name} must be a JSON array")
    result = tuple(str(item) for item in value)
    _require_unique(result, field_name)
    return result


def _string_mapping(value: Any, field_name: str) -> dict[str, str]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise TypeError(f"{field_name} must be a JSON object")
    return {str(key): str(item) for key, item in value.items()}


def _bool_mapping(value: Any, field_name: str) -> dict[str, bool]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise TypeError(f"{field_name} must be a JSON object")
    result: dict[str, bool] = {}
    for key, item in value.items():
        if not isinstance(item, bool):
            raise TypeError(f"{field_name}.{key} must be boolean")
        result[str(key)] = item
    return result


def _number_mapping(value: Any, field_name: str) -> dict[str, float]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise TypeError(f"{field_name} must be a JSON object")
    result: dict[str, float] = {}
    for key, item in value.items():
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            raise TypeError(f"{field_name}.{key} must be numeric")
        number = float(item)
        if not math.isfinite(number):
            raise ValueError(f"{field_name}.{key} must be finite")
        result[str(key)] = number
    return result


@dataclass(frozen=True, slots=True)
class EvaluationCase:
    """One fixed evaluation question and its expected structural references."""

    case_id: str
    task_class: str
    risk_class: str
    question: str
    source_refs: tuple[str, ...] = ()
    expected_claim_refs: tuple[str, ...] = ()
    expected_evidence_span_refs: tuple[str, ...] = ()
    expected_memory_dispositions: tuple[str, ...] = ()
    expected_route_set: tuple[str, ...] = ()
    forbidden_outputs: tuple[str, ...] = ()
    deterministic_seed: int = 0
    tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_text(self.case_id, "case_id")
        _require_text(self.task_class, "task_class")
        _require_text(self.risk_class, "risk_class")
        _require_text(self.question, "question")
        if self.deterministic_seed < 0:
            raise ValueError("deterministic_seed must be non-negative")
        for field_name in (
            "source_refs",
            "expected_claim_refs",
            "expected_evidence_span_refs",
            "expected_memory_dispositions",
            "expected_route_set",
            "forbidden_outputs",
            "tags",
        ):
            _require_unique(getattr(self, field_name), field_name)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Self:
        return cls(
            case_id=str(data["case_id"]),
            task_class=str(data["task_class"]),
            risk_class=str(data["risk_class"]),
            question=str(data["question"]),
            source_refs=_string_tuple(data.get("source_refs"), "source_refs"),
            expected_claim_refs=_string_tuple(
                data.get("expected_claim_refs"), "expected_claim_refs"
            ),
            expected_evidence_span_refs=_string_tuple(
                data.get("expected_evidence_span_refs"), "expected_evidence_span_refs"
            ),
            expected_memory_dispositions=_string_tuple(
                data.get("expected_memory_dispositions"), "expected_memory_dispositions"
            ),
            expected_route_set=_string_tuple(
                data.get("expected_route_set"), "expected_route_set"
            ),
            forbidden_outputs=_string_tuple(data.get("forbidden_outputs"), "forbidden_outputs"),
            deterministic_seed=int(data.get("deterministic_seed", 0)),
            tags=_string_tuple(data.get("tags"), "tags"),
        )


@dataclass(frozen=True, slots=True)
class EvaluationPackage:
    """Versioned collection of fixed evaluation cases and policy fixtures."""

    package_id: str
    cases: tuple[EvaluationCase, ...]
    protocol_version: str = PROTOCOL_VERSION
    corpus_snapshot: Mapping[str, Any] = field(default_factory=dict)
    policy_fixture: Mapping[str, Any] = field(default_factory=dict)
    provider_tool_fixtures: Mapping[str, Any] = field(default_factory=dict)
    redaction_manifest: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_text(self.package_id, "package_id")
        _require_text(self.protocol_version, "protocol_version")
        if not self.cases:
            raise ValueError("evaluation package must contain at least one case")
        case_ids = tuple(case.case_id for case in self.cases)
        _require_unique(case_ids, "cases.case_id")

    @property
    def package_digest(self) -> str:
        return stable_digest(self)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Self:
        raw_cases = data.get("cases")
        if not isinstance(raw_cases, list):
            raise TypeError("package.cases must be a JSON array")
        cases = tuple(
            EvaluationCase.from_dict(_require_mapping(item, "package.cases[]"))
            for item in raw_cases
        )
        return cls(
            package_id=str(data["package_id"]),
            cases=cases,
            protocol_version=str(data.get("protocol_version", PROTOCOL_VERSION)),
            corpus_snapshot=dict(
                _require_mapping(data.get("corpus_snapshot", {}), "corpus_snapshot")
            ),
            policy_fixture=dict(
                _require_mapping(data.get("policy_fixture", {}), "policy_fixture")
            ),
            provider_tool_fixtures=dict(
                _require_mapping(
                    data.get("provider_tool_fixtures", {}), "provider_tool_fixtures"
                )
            ),
            redaction_manifest=dict(
                _require_mapping(data.get("redaction_manifest", {}), "redaction_manifest")
            ),
        )


@dataclass(frozen=True, slots=True)
class CaseEvaluationReceipt:
    """Recorded structured output for one fixture-bound evaluation case."""

    case_id: str
    input_digest: str
    extracted_claims: tuple[str, ...] = ()
    rejected_claims: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    retrieval_result: tuple[str, ...] = ()
    memory_dispositions: Mapping[str, str] = field(default_factory=dict)
    temporal_relations: tuple[str, ...] = ()
    conflicts: tuple[str, ...] = ()
    route: str = ""
    answer: str = ""
    policy_reason_codes: tuple[str, ...] = ()
    latency_ms: Mapping[str, float] = field(default_factory=dict)
    resource_counts: Mapping[str, float] = field(default_factory=dict)
    truth_gate_bypass_count: int = 0
    query_path_write_count: int = 0
    unrecorded_external_call_count: int = 0
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_text(self.case_id, "case_id")
        _require_text(self.input_digest, "input_digest")
        for field_name in (
            "extracted_claims",
            "rejected_claims",
            "evidence_refs",
            "retrieval_result",
            "temporal_relations",
            "conflicts",
            "policy_reason_codes",
            "warnings",
        ):
            _require_unique(getattr(self, field_name), field_name)
        for field_name in (
            "truth_gate_bypass_count",
            "query_path_write_count",
            "unrecorded_external_call_count",
        ):
            if getattr(self, field_name) < 0:
                raise ValueError(f"{field_name} must be non-negative")
        _number_mapping(self.latency_ms, "latency_ms")
        _number_mapping(self.resource_counts, "resource_counts")

    @property
    def output_digest(self) -> str:
        return stable_digest(self)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Self:
        return cls(
            case_id=str(data["case_id"]),
            input_digest=str(data["input_digest"]),
            extracted_claims=_string_tuple(data.get("extracted_claims"), "extracted_claims"),
            rejected_claims=_string_tuple(data.get("rejected_claims"), "rejected_claims"),
            evidence_refs=_string_tuple(data.get("evidence_refs"), "evidence_refs"),
            retrieval_result=_string_tuple(data.get("retrieval_result"), "retrieval_result"),
            memory_dispositions=_string_mapping(
                data.get("memory_dispositions"), "memory_dispositions"
            ),
            temporal_relations=_string_tuple(
                data.get("temporal_relations"), "temporal_relations"
            ),
            conflicts=_string_tuple(data.get("conflicts"), "conflicts"),
            route=str(data.get("route", "")),
            answer=str(data.get("answer", "")),
            policy_reason_codes=_string_tuple(
                data.get("policy_reason_codes"), "policy_reason_codes"
            ),
            latency_ms=_number_mapping(data.get("latency_ms"), "latency_ms"),
            resource_counts=_number_mapping(data.get("resource_counts"), "resource_counts"),
            truth_gate_bypass_count=int(data.get("truth_gate_bypass_count", 0)),
            query_path_write_count=int(data.get("query_path_write_count", 0)),
            unrecorded_external_call_count=int(
                data.get("unrecorded_external_call_count", 0)
            ),
            warnings=_string_tuple(data.get("warnings"), "warnings"),
        )


@dataclass(frozen=True, slots=True)
class EvaluationRun:
    """One deterministic evaluation execution over a fixed package."""

    run_id: str
    package_id: str
    code_revision: str
    case_receipts: tuple[CaseEvaluationReceipt, ...]
    configuration_snapshot: Mapping[str, Any] = field(default_factory=dict)
    feature_flags: Mapping[str, bool] = field(default_factory=dict)
    policy_snapshot_fixture: Mapping[str, Any] = field(default_factory=dict)
    provider_fixture_versions: Mapping[str, str] = field(default_factory=dict)
    environment_manifest: Mapping[str, str] = field(default_factory=dict)
    started_at: str = ""
    completed_at: str = ""

    def __post_init__(self) -> None:
        _require_text(self.run_id, "run_id")
        _require_text(self.package_id, "package_id")
        _require_text(self.code_revision, "code_revision")
        if not self.case_receipts:
            raise ValueError("evaluation run must contain at least one case receipt")
        case_ids = tuple(receipt.case_id for receipt in self.case_receipts)
        _require_unique(case_ids, "case_receipts.case_id")

    def semantic_payload(self) -> dict[str, Any]:
        """Return identity-bearing fields, excluding wall-clock timestamps and run_id."""
        return {
            "package_id": self.package_id,
            "code_revision": self.code_revision,
            "case_receipts": self.case_receipts,
            "configuration_snapshot": self.configuration_snapshot,
            "feature_flags": self.feature_flags,
            "policy_snapshot_fixture": self.policy_snapshot_fixture,
            "provider_fixture_versions": self.provider_fixture_versions,
            "environment_manifest": self.environment_manifest,
        }

    @property
    def result_digest(self) -> str:
        return stable_digest(self.semantic_payload())

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Self:
        raw_receipts = data.get("case_receipts")
        if not isinstance(raw_receipts, list):
            raise TypeError("run.case_receipts must be a JSON array")
        receipts = tuple(
            CaseEvaluationReceipt.from_dict(_require_mapping(item, "case_receipts[]"))
            for item in raw_receipts
        )
        return cls(
            run_id=str(data["run_id"]),
            package_id=str(data["package_id"]),
            code_revision=str(data["code_revision"]),
            case_receipts=receipts,
            configuration_snapshot=dict(
                _require_mapping(
                    data.get("configuration_snapshot", {}), "configuration_snapshot"
                )
            ),
            feature_flags=_bool_mapping(data.get("feature_flags"), "feature_flags"),
            policy_snapshot_fixture=dict(
                _require_mapping(
                    data.get("policy_snapshot_fixture", {}), "policy_snapshot_fixture"
                )
            ),
            provider_fixture_versions=_string_mapping(
                data.get("provider_fixture_versions"), "provider_fixture_versions"
            ),
            environment_manifest=_string_mapping(
                data.get("environment_manifest"), "environment_manifest"
            ),
            started_at=str(data.get("started_at", "")),
            completed_at=str(data.get("completed_at", "")),
        )


@dataclass(frozen=True, slots=True)
class ExperimentFork:
    """Declared single-change relationship between baseline and candidate runs."""

    parent_run_id: str
    fork_id: str
    changed_dimension: str
    before_value: Any
    after_value: Any
    secondary_changes: tuple[str, ...] = ()
    justification: str = ""
    expected_effect: str = ""

    def __post_init__(self) -> None:
        _require_text(self.parent_run_id, "parent_run_id")
        _require_text(self.fork_id, "fork_id")
        _require_text(self.changed_dimension, "changed_dimension")
        _require_unique(self.secondary_changes, "secondary_changes")
        if stable_digest(self.before_value) == stable_digest(self.after_value):
            raise ValueError("fork before_value and after_value must differ")

    @property
    def fork_digest(self) -> str:
        return stable_digest(self)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Self:
        return cls(
            parent_run_id=str(data["parent_run_id"]),
            fork_id=str(data["fork_id"]),
            changed_dimension=str(data["changed_dimension"]),
            before_value=data.get("before_value"),
            after_value=data.get("after_value"),
            secondary_changes=_string_tuple(
                data.get("secondary_changes"), "secondary_changes"
            ),
            justification=str(data.get("justification", "")),
            expected_effect=str(data.get("expected_effect", "")),
        )


@dataclass(frozen=True, slots=True)
class CaseStructuralDiff:
    """Structured difference for one case receipt."""

    case_id: str
    claims_added: tuple[str, ...] = ()
    claims_removed: tuple[str, ...] = ()
    evidence_added: tuple[str, ...] = ()
    evidence_removed: tuple[str, ...] = ()
    memory_disposition_changes: Mapping[str, Mapping[str, str | None]] = field(
        default_factory=dict
    )
    temporal_relations_added: tuple[str, ...] = ()
    temporal_relations_removed: tuple[str, ...] = ()
    conflicts_added: tuple[str, ...] = ()
    conflicts_removed: tuple[str, ...] = ()
    policy_reason_codes_added: tuple[str, ...] = ()
    policy_reason_codes_removed: tuple[str, ...] = ()
    route_before: str = ""
    route_after: str = ""
    answer_changed: bool = False
    metric_delta: Mapping[str, float] = field(default_factory=dict)
    critical_regressions: tuple[str, ...] = ()
    stability: StabilityClass = StabilityClass.BIT_IDENTICAL


@dataclass(frozen=True, slots=True)
class StructuralDiff:
    """Comparison of two complete evaluation runs."""

    baseline_run_id: str
    candidate_run_id: str
    fork_id: str
    case_diffs: tuple[CaseStructuralDiff, ...]
    aggregate_delta: Mapping[str, float] = field(default_factory=dict)
    critical_regressions: tuple[str, ...] = ()
    observations: tuple[str, ...] = ()
    stability: StabilityClass = StabilityClass.BIT_IDENTICAL

    def to_dict(self) -> dict[str, Any]:
        return _canonicalize(self)


def _ordered_added(before: Sequence[str], after: Sequence[str]) -> tuple[str, ...]:
    before_set = set(before)
    return tuple(item for item in after if item not in before_set)


def _ordered_removed(before: Sequence[str], after: Sequence[str]) -> tuple[str, ...]:
    after_set = set(after)
    return tuple(item for item in before if item not in after_set)


def _mapping_changes(
    before: Mapping[str, str],
    after: Mapping[str, str],
) -> dict[str, dict[str, str | None]]:
    changes: dict[str, dict[str, str | None]] = {}
    for key in sorted(set(before) | set(after)):
        old = before.get(key)
        new = after.get(key)
        if old != new:
            changes[key] = {"baseline": old, "candidate": new}
    return changes


def _numeric_delta(
    before: Mapping[str, float],
    after: Mapping[str, float],
    prefix: str,
) -> dict[str, float]:
    delta: dict[str, float] = {}
    for key in sorted(set(before) | set(after)):
        change = float(after.get(key, 0.0)) - float(before.get(key, 0.0))
        if change:
            delta[f"{prefix}.{key}"] = round(change, 6)
    return delta


def _case_critical_regressions(receipt: CaseEvaluationReceipt) -> tuple[str, ...]:
    failures: list[str] = []
    if receipt.truth_gate_bypass_count > 0:
        failures.append(
            f"{receipt.case_id}: truth_gate_bypass_count={receipt.truth_gate_bypass_count}"
        )
    if receipt.query_path_write_count > 0:
        failures.append(
            f"{receipt.case_id}: query_path_write_count={receipt.query_path_write_count}"
        )
    if receipt.unrecorded_external_call_count > 0:
        failures.append(
            f"{receipt.case_id}: "
            f"unrecorded_external_call_count={receipt.unrecorded_external_call_count}"
        )
    return tuple(failures)


def compare_case_receipts(
    baseline: CaseEvaluationReceipt,
    candidate: CaseEvaluationReceipt,
) -> CaseStructuralDiff:
    """Compare two receipts for the same evaluation case."""
    if baseline.case_id != candidate.case_id:
        raise ValueError("cannot compare receipts from different case IDs")

    claims_added = _ordered_added(baseline.extracted_claims, candidate.extracted_claims)
    claims_removed = _ordered_removed(baseline.extracted_claims, candidate.extracted_claims)
    evidence_added = _ordered_added(baseline.evidence_refs, candidate.evidence_refs)
    evidence_removed = _ordered_removed(baseline.evidence_refs, candidate.evidence_refs)
    temporal_added = _ordered_added(
        baseline.temporal_relations, candidate.temporal_relations
    )
    temporal_removed = _ordered_removed(
        baseline.temporal_relations, candidate.temporal_relations
    )
    conflicts_added = _ordered_added(baseline.conflicts, candidate.conflicts)
    conflicts_removed = _ordered_removed(baseline.conflicts, candidate.conflicts)
    policy_added = _ordered_added(
        baseline.policy_reason_codes, candidate.policy_reason_codes
    )
    policy_removed = _ordered_removed(
        baseline.policy_reason_codes, candidate.policy_reason_codes
    )
    memory_changes = _mapping_changes(
        baseline.memory_dispositions, candidate.memory_dispositions
    )
    metric_delta = {
        **_numeric_delta(baseline.latency_ms, candidate.latency_ms, "latency_ms"),
        **_numeric_delta(
            baseline.resource_counts, candidate.resource_counts, "resource_counts"
        ),
    }
    critical = _case_critical_regressions(candidate)

    structural_changed = any(
        (
            claims_added,
            claims_removed,
            evidence_added,
            evidence_removed,
            memory_changes,
            temporal_added,
            temporal_removed,
            conflicts_added,
            conflicts_removed,
            policy_added,
            policy_removed,
            baseline.route != candidate.route,
            metric_delta,
        )
    )
    answer_changed = baseline.answer != candidate.answer

    if critical:
        stability = StabilityClass.REGRESSION
    elif baseline.output_digest == candidate.output_digest:
        stability = StabilityClass.BIT_IDENTICAL
    elif not structural_changed and answer_changed:
        stability = StabilityClass.STRUCTURALLY_EQUIVALENT
    else:
        stability = StabilityClass.REVIEW_REQUIRED

    return CaseStructuralDiff(
        case_id=baseline.case_id,
        claims_added=claims_added,
        claims_removed=claims_removed,
        evidence_added=evidence_added,
        evidence_removed=evidence_removed,
        memory_disposition_changes=memory_changes,
        temporal_relations_added=temporal_added,
        temporal_relations_removed=temporal_removed,
        conflicts_added=conflicts_added,
        conflicts_removed=conflicts_removed,
        policy_reason_codes_added=policy_added,
        policy_reason_codes_removed=policy_removed,
        route_before=baseline.route,
        route_after=candidate.route,
        answer_changed=answer_changed,
        metric_delta=metric_delta,
        critical_regressions=critical,
        stability=stability,
    )


def compare_runs(
    baseline: EvaluationRun,
    candidate: EvaluationRun,
    fork: ExperimentFork,
) -> StructuralDiff:
    """Compare baseline and candidate runs from the same package."""
    if baseline.package_id != candidate.package_id:
        raise ValueError("baseline and candidate must use the same package")
    if fork.parent_run_id != baseline.run_id:
        raise ValueError("fork.parent_run_id must match baseline.run_id")

    baseline_by_case = {receipt.case_id: receipt for receipt in baseline.case_receipts}
    candidate_by_case = {receipt.case_id: receipt for receipt in candidate.case_receipts}
    if baseline_by_case.keys() != candidate_by_case.keys():
        missing_candidate = sorted(baseline_by_case.keys() - candidate_by_case.keys())
        extra_candidate = sorted(candidate_by_case.keys() - baseline_by_case.keys())
        raise ValueError(
            "run case sets differ: "
            f"missing_candidate={missing_candidate}, extra_candidate={extra_candidate}"
        )

    case_diffs = tuple(
        compare_case_receipts(baseline_by_case[case_id], candidate_by_case[case_id])
        for case_id in sorted(baseline_by_case)
    )
    critical = tuple(
        failure for case_diff in case_diffs for failure in case_diff.critical_regressions
    )

    aggregate: dict[str, float] = {}
    for case_diff in case_diffs:
        for key, value in case_diff.metric_delta.items():
            aggregate[key] = round(aggregate.get(key, 0.0) + value, 6)

    observations: list[str] = []
    latency_delta = aggregate.get("latency_ms.total")
    if latency_delta is not None:
        if latency_delta < 0:
            observations.append(f"candidate total latency decreased by {-latency_delta:.3f} ms")
        elif latency_delta > 0:
            observations.append(f"candidate total latency increased by {latency_delta:.3f} ms")

    if critical:
        stability = StabilityClass.REGRESSION
    elif all(item.stability is StabilityClass.BIT_IDENTICAL for item in case_diffs):
        stability = StabilityClass.BIT_IDENTICAL
    elif all(
        item.stability
        in (StabilityClass.BIT_IDENTICAL, StabilityClass.STRUCTURALLY_EQUIVALENT)
        for item in case_diffs
    ):
        stability = StabilityClass.STRUCTURALLY_EQUIVALENT
    else:
        stability = StabilityClass.REVIEW_REQUIRED

    return StructuralDiff(
        baseline_run_id=baseline.run_id,
        candidate_run_id=candidate.run_id,
        fork_id=fork.fork_id,
        case_diffs=case_diffs,
        aggregate_delta=aggregate,
        critical_regressions=critical,
        observations=tuple(observations),
        stability=stability,
    )


def load_fixture(
    path: str | Path,
) -> tuple[EvaluationPackage, EvaluationRun, EvaluationRun, ExperimentFork]:
    """Load one local JSON fixture without network or runtime dependencies."""
    fixture_path = Path(path)
    with fixture_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    root = _require_mapping(payload, "fixture")
    package = EvaluationPackage.from_dict(
        _require_mapping(root.get("package"), "fixture.package")
    )
    baseline = EvaluationRun.from_dict(
        _require_mapping(root.get("baseline_run"), "fixture.baseline_run")
    )
    candidate = EvaluationRun.from_dict(
        _require_mapping(root.get("candidate_run"), "fixture.candidate_run")
    )
    fork = ExperimentFork.from_dict(
        _require_mapping(root.get("fork"), "fixture.fork")
    )

    expected_case_ids = {case.case_id for case in package.cases}
    for run_name, run in (("baseline", baseline), ("candidate", candidate)):
        if run.package_id != package.package_id:
            raise ValueError(f"{run_name} run package_id does not match package")
        run_case_ids = {receipt.case_id for receipt in run.case_receipts}
        if run_case_ids != expected_case_ids:
            raise ValueError(
                f"{run_name} run case IDs do not match package: "
                f"expected={sorted(expected_case_ids)}, got={sorted(run_case_ids)}"
            )
    return package, baseline, candidate, fork


def evaluate_fixture(path: str | Path) -> dict[str, Any]:
    """Evaluate a local fixture and return a deterministic machine-readable report."""
    package, baseline, candidate, fork = load_fixture(path)
    diff = compare_runs(baseline, candidate, fork)
    return {
        "protocol_version": package.protocol_version,
        "package_id": package.package_id,
        "package_digest": package.package_digest,
        "baseline_run_id": baseline.run_id,
        "baseline_result_digest": baseline.result_digest,
        "candidate_run_id": candidate.run_id,
        "candidate_result_digest": candidate.result_digest,
        "fork_id": fork.fork_id,
        "fork_digest": fork.fork_digest,
        "diff": diff,
    }


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point for deterministic local fixture evaluation."""
    parser = argparse.ArgumentParser(
        description="Compare fixture-bound Titan evaluation runs without network or writes."
    )
    parser.add_argument("fixture", type=Path, help="Path to an evaluation fixture JSON file")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional output path; stdout is used when omitted",
    )
    args = parser.parse_args(argv)
    report_json = canonical_json(evaluate_fixture(args.fixture)) + "\n"
    if args.output is None:
        print(report_json, end="")
    else:
        args.output.write_text(report_json, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
