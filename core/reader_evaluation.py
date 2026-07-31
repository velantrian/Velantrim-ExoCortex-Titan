"""Deterministic Reader Core evaluation and promotion review for PR-RDR-09.

The module aggregates labelled observations, compares replay digests, computes
transparent metrics, and produces a non-authoritative promotion review. It does
not run Reader Core, select models, authorize live integration, or grant Canon,
memory, policy, graph, tool, TruthGate, or Write Gate authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math
from typing import Iterable

from core.reader_core_contracts import stable_reader_core_id

READER_EVALUATION_SCHEMA_VERSION = "reader-core.evaluation.v1"
READER_EVALUATION_MANIFEST_SCHEMA_VERSION = "reader-core.evaluation-manifest.v1"


class ReaderEvaluationError(ValueError):
    """Raised when evaluation data or promotion invariants are invalid."""


class EvaluationCorpusKind(str, Enum):
    SYNTHETIC = "synthetic"
    REAL = "real"
    HUMAN_LABELLED = "human_labelled"


class PromotionDecision(str, Enum):
    ELIGIBLE_FOR_OPERATOR_REVIEW = "eligible_for_operator_review"
    NO_GO = "no_go"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


@dataclass(frozen=True, slots=True)
class EvaluationEnvironment:
    commit_sha: str
    runner_id: str
    python_version: str
    hardware_profile: str
    config_digest: str
    model_id: str | None = None
    model_version: str | None = None
    environment_id: str = ""

    def __post_init__(self) -> None:
        for name in (
            "commit_sha",
            "runner_id",
            "python_version",
            "hardware_profile",
            "config_digest",
        ):
            _require_text(getattr(self, name), name)
        if (self.model_id is None) != (self.model_version is None):
            raise ReaderEvaluationError(
                "model_id and model_version must be both present or both absent"
            )
        if self.model_id is not None:
            _require_text(self.model_id, "model_id")
            _require_text(self.model_version, "model_version")
        expected = stable_reader_core_id(
            "reader-evaluation-environment",
            self.identity_payload(include_id=False),
        )
        if self.environment_id:
            if self.environment_id != expected:
                raise ReaderEvaluationError(
                    "environment_id does not match environment content"
                )
        else:
            object.__setattr__(self, "environment_id", expected)

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "commit_sha": self.commit_sha,
            "runner_id": self.runner_id,
            "python_version": self.python_version,
            "hardware_profile": self.hardware_profile,
            "config_digest": self.config_digest,
            "model_id": self.model_id,
            "model_version": self.model_version,
        }
        if include_id:
            payload["environment_id"] = self.environment_id
        return payload


@dataclass(frozen=True, slots=True)
class ReaderEvaluationCaseManifest:
    case_id: str
    corpus_kind: EvaluationCorpusKind
    label_version: str
    expected_claim_count: int
    expected_source_span_count: int
    expected_exception_count: int
    expected_relation_count: int
    expected_contradiction_count: int
    expected_qualifier_count: int
    tags: tuple[str, ...] = ()
    manifest_id: str = ""

    def __post_init__(self) -> None:
        _require_text(self.case_id, "case_id")
        if not isinstance(self.corpus_kind, EvaluationCorpusKind):
            raise ReaderEvaluationError(
                "corpus_kind must be an EvaluationCorpusKind"
            )
        _require_text(self.label_version, "label_version")
        for name in (
            "expected_claim_count",
            "expected_source_span_count",
            "expected_exception_count",
            "expected_relation_count",
            "expected_contradiction_count",
            "expected_qualifier_count",
        ):
            _nonnegative_int(getattr(self, name), name)
        tags = _unique_sorted_text(self.tags, "tag")
        object.__setattr__(self, "tags", tags)
        expected = stable_reader_core_id(
            "reader-evaluation-case-manifest",
            self.identity_payload(include_id=False),
        )
        if self.manifest_id:
            if self.manifest_id != expected:
                raise ReaderEvaluationError(
                    "manifest_id does not match case manifest content"
                )
        else:
            object.__setattr__(self, "manifest_id", expected)

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "case_id": self.case_id,
            "corpus_kind": self.corpus_kind.value,
            "label_version": self.label_version,
            "expected_claim_count": self.expected_claim_count,
            "expected_source_span_count": self.expected_source_span_count,
            "expected_exception_count": self.expected_exception_count,
            "expected_relation_count": self.expected_relation_count,
            "expected_contradiction_count": self.expected_contradiction_count,
            "expected_qualifier_count": self.expected_qualifier_count,
            "tags": list(self.tags),
        }
        if include_id:
            payload["manifest_id"] = self.manifest_id
        return payload


@dataclass(frozen=True, slots=True)
class EvaluationCorpusManifest:
    corpus_name: str
    corpus_version: str
    cases: tuple[ReaderEvaluationCaseManifest, ...]
    schema_version: str = READER_EVALUATION_MANIFEST_SCHEMA_VERSION
    corpus_id: str = ""

    def __post_init__(self) -> None:
        _require_text(self.corpus_name, "corpus_name")
        _require_text(self.corpus_version, "corpus_version")
        if self.schema_version != READER_EVALUATION_MANIFEST_SCHEMA_VERSION:
            raise ReaderEvaluationError("unsupported evaluation manifest schema")
        cases = tuple(self.cases)
        if not cases or any(
            not isinstance(case, ReaderEvaluationCaseManifest) for case in cases
        ):
            raise ReaderEvaluationError(
                "cases require at least one ReaderEvaluationCaseManifest"
            )
        ordered = tuple(sorted(cases, key=lambda item: item.case_id))
        if len({case.case_id for case in ordered}) != len(ordered):
            raise ReaderEvaluationError("evaluation case IDs must be unique")
        object.__setattr__(self, "cases", ordered)
        expected = stable_reader_core_id(
            "reader-evaluation-corpus-manifest",
            self.identity_payload(include_id=False),
        )
        if self.corpus_id:
            if self.corpus_id != expected:
                raise ReaderEvaluationError(
                    "corpus_id does not match corpus manifest content"
                )
        else:
            object.__setattr__(self, "corpus_id", expected)

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema_version": self.schema_version,
            "corpus_name": self.corpus_name,
            "corpus_version": self.corpus_version,
            "case_manifest_ids": [case.manifest_id for case in self.cases],
        }
        if include_id:
            payload["corpus_id"] = self.corpus_id
        return payload


@dataclass(frozen=True, slots=True)
class ReplayComparison:
    case_id: str
    first_digest: str
    second_digest: str
    matched: bool
    comparison_id: str = ""

    def __post_init__(self) -> None:
        _require_text(self.case_id, "case_id")
        _require_text(self.first_digest, "first_digest")
        _require_text(self.second_digest, "second_digest")
        if not isinstance(self.matched, bool):
            raise ReaderEvaluationError("matched must be a boolean")
        if self.matched != (self.first_digest == self.second_digest):
            raise ReaderEvaluationError(
                "matched must equal digest equality"
            )
        expected = stable_reader_core_id(
            "reader-replay-comparison",
            self.identity_payload(include_id=False),
        )
        if self.comparison_id:
            if self.comparison_id != expected:
                raise ReaderEvaluationError(
                    "comparison_id does not match replay content"
                )
        else:
            object.__setattr__(self, "comparison_id", expected)

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "case_id": self.case_id,
            "first_digest": self.first_digest,
            "second_digest": self.second_digest,
            "matched": self.matched,
        }
        if include_id:
            payload["comparison_id"] = self.comparison_id
        return payload


class ReaderReplayComparator:
    """Compare two ordered replay artifact sequences without executing them."""

    @staticmethod
    def compare(
        case_id: str,
        first_artifact_ids: Iterable[str],
        second_artifact_ids: Iterable[str],
    ) -> ReplayComparison:
        _require_text(case_id, "case_id")
        first = _text_tuple(first_artifact_ids, "first_artifact_id")
        second = _text_tuple(second_artifact_ids, "second_artifact_id")
        first_digest = stable_reader_core_id(
            "reader-replay-output",
            {"case_id": case_id, "artifact_ids": list(first)},
        )
        second_digest = stable_reader_core_id(
            "reader-replay-output",
            {"case_id": case_id, "artifact_ids": list(second)},
        )
        return ReplayComparison(
            case_id=case_id,
            first_digest=first_digest,
            second_digest=second_digest,
            matched=first_digest == second_digest,
        )


@dataclass(frozen=True, slots=True)
class ReaderEvaluationCaseResult:
    manifest: ReaderEvaluationCaseManifest
    predicted_claim_count: int
    matched_claim_count: int
    predicted_source_span_count: int
    correct_source_span_count: int
    predicted_exception_count: int
    matched_exception_count: int
    predicted_relation_count: int
    matched_relation_count: int
    false_relation_count: int
    matched_contradiction_count: int
    connected_qualifier_count: int
    source_claim_count: int
    orphan_source_claim_count: int
    synthesis_claim_count: int
    unsupported_synthesis_claim_count: int
    replay: ReplayComparison
    section_latencies_ms: tuple[int, ...]
    session_wall_time_ms: int
    model_tokens: int
    projection_bytes: int
    rebuild_time_ms: int
    query_path_latency_delta_ms: int
    resume_reused_units: int
    resume_eligible_units: int
    truth_gate_bypass_count: int = 0
    query_path_write_count: int = 0
    direct_canon_write_count: int = 0
    untrusted_instruction_execution_count: int = 0
    warnings: tuple[str, ...] = ()
    case_result_id: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.manifest, ReaderEvaluationCaseManifest):
            raise ReaderEvaluationError(
                "manifest must be a ReaderEvaluationCaseManifest"
            )
        for name in (
            "predicted_claim_count",
            "matched_claim_count",
            "predicted_source_span_count",
            "correct_source_span_count",
            "predicted_exception_count",
            "matched_exception_count",
            "predicted_relation_count",
            "matched_relation_count",
            "false_relation_count",
            "matched_contradiction_count",
            "connected_qualifier_count",
            "source_claim_count",
            "orphan_source_claim_count",
            "synthesis_claim_count",
            "unsupported_synthesis_claim_count",
            "session_wall_time_ms",
            "model_tokens",
            "projection_bytes",
            "rebuild_time_ms",
            "resume_reused_units",
            "resume_eligible_units",
            "truth_gate_bypass_count",
            "query_path_write_count",
            "direct_canon_write_count",
            "untrusted_instruction_execution_count",
        ):
            _nonnegative_int(getattr(self, name), name)
        if (
            isinstance(self.query_path_latency_delta_ms, bool)
            or not isinstance(self.query_path_latency_delta_ms, int)
        ):
            raise ReaderEvaluationError(
                "query_path_latency_delta_ms must be an integer"
            )
        self._validate_count_bounds()
        if not isinstance(self.replay, ReplayComparison):
            raise ReaderEvaluationError("replay must be a ReplayComparison")
        if self.replay.case_id != self.manifest.case_id:
            raise ReaderEvaluationError("replay case_id must match manifest")
        latencies = tuple(self.section_latencies_ms)
        for latency in latencies:
            _nonnegative_int(latency, "section_latency_ms")
        warnings = _unique_text_tuple(self.warnings, "warning")
        object.__setattr__(self, "section_latencies_ms", latencies)
        object.__setattr__(self, "warnings", warnings)
        expected = stable_reader_core_id(
            "reader-evaluation-case-result",
            self.identity_payload(include_id=False),
        )
        if self.case_result_id:
            if self.case_result_id != expected:
                raise ReaderEvaluationError(
                    "case_result_id does not match case result content"
                )
        else:
            object.__setattr__(self, "case_result_id", expected)

    def _validate_count_bounds(self) -> None:
        expected = self.manifest
        checks = (
            (
                self.matched_claim_count,
                expected.expected_claim_count,
                "matched_claim_count",
            ),
            (
                self.matched_claim_count,
                self.predicted_claim_count,
                "matched_claim_count",
            ),
            (
                self.correct_source_span_count,
                expected.expected_source_span_count,
                "correct_source_span_count",
            ),
            (
                self.correct_source_span_count,
                self.predicted_source_span_count,
                "correct_source_span_count",
            ),
            (
                self.matched_exception_count,
                expected.expected_exception_count,
                "matched_exception_count",
            ),
            (
                self.matched_exception_count,
                self.predicted_exception_count,
                "matched_exception_count",
            ),
            (
                self.matched_relation_count,
                expected.expected_relation_count,
                "matched_relation_count",
            ),
            (
                self.matched_relation_count,
                self.predicted_relation_count,
                "matched_relation_count",
            ),
            (
                self.false_relation_count,
                self.predicted_relation_count,
                "false_relation_count",
            ),
            (
                self.matched_contradiction_count,
                expected.expected_contradiction_count,
                "matched_contradiction_count",
            ),
            (
                self.connected_qualifier_count,
                expected.expected_qualifier_count,
                "connected_qualifier_count",
            ),
            (
                self.orphan_source_claim_count,
                self.source_claim_count,
                "orphan_source_claim_count",
            ),
            (
                self.unsupported_synthesis_claim_count,
                self.synthesis_claim_count,
                "unsupported_synthesis_claim_count",
            ),
            (
                self.resume_reused_units,
                self.resume_eligible_units,
                "resume_reused_units",
            ),
        )
        for actual, maximum, label in checks:
            if actual > maximum:
                raise ReaderEvaluationError(
                    f"{label} cannot exceed its observable denominator"
                )

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "manifest_id": self.manifest.manifest_id,
            "predicted_claim_count": self.predicted_claim_count,
            "matched_claim_count": self.matched_claim_count,
            "predicted_source_span_count": self.predicted_source_span_count,
            "correct_source_span_count": self.correct_source_span_count,
            "predicted_exception_count": self.predicted_exception_count,
            "matched_exception_count": self.matched_exception_count,
            "predicted_relation_count": self.predicted_relation_count,
            "matched_relation_count": self.matched_relation_count,
            "false_relation_count": self.false_relation_count,
            "matched_contradiction_count": self.matched_contradiction_count,
            "connected_qualifier_count": self.connected_qualifier_count,
            "source_claim_count": self.source_claim_count,
            "orphan_source_claim_count": self.orphan_source_claim_count,
            "synthesis_claim_count": self.synthesis_claim_count,
            "unsupported_synthesis_claim_count": (
                self.unsupported_synthesis_claim_count
            ),
            "replay_comparison_id": self.replay.comparison_id,
            "section_latencies_ms": list(self.section_latencies_ms),
            "session_wall_time_ms": self.session_wall_time_ms,
            "model_tokens": self.model_tokens,
            "projection_bytes": self.projection_bytes,
            "rebuild_time_ms": self.rebuild_time_ms,
            "query_path_latency_delta_ms": self.query_path_latency_delta_ms,
            "resume_reused_units": self.resume_reused_units,
            "resume_eligible_units": self.resume_eligible_units,
            "truth_gate_bypass_count": self.truth_gate_bypass_count,
            "query_path_write_count": self.query_path_write_count,
            "direct_canon_write_count": self.direct_canon_write_count,
            "untrusted_instruction_execution_count": (
                self.untrusted_instruction_execution_count
            ),
            "warnings": list(self.warnings),
        }
        if include_id:
            payload["case_result_id"] = self.case_result_id
        return payload


@dataclass(frozen=True, slots=True)
class ReaderEvaluationMetrics:
    total_case_count: int
    synthetic_case_count: int
    real_case_count: int
    human_labelled_case_count: int
    expected_claim_count: int
    predicted_claim_count: int
    matched_claim_count: int
    expected_source_span_count: int
    predicted_source_span_count: int
    correct_source_span_count: int
    expected_exception_count: int
    matched_exception_count: int
    expected_relation_count: int
    predicted_relation_count: int
    matched_relation_count: int
    false_relation_count: int
    expected_contradiction_count: int
    matched_contradiction_count: int
    expected_qualifier_count: int
    connected_qualifier_count: int
    source_claim_count: int
    orphan_source_claim_count: int
    synthesis_claim_count: int
    unsupported_synthesis_claim_count: int
    replay_match_count: int
    resume_reused_units: int
    resume_eligible_units: int
    section_latency_p50_ms: int | None
    section_latency_p95_ms: int | None
    total_session_wall_time_ms: int
    total_model_tokens: int
    total_projection_bytes: int
    rebuild_time_p95_ms: int | None
    max_query_path_latency_delta_ms: int
    truth_gate_bypass_count: int
    query_path_write_count: int
    direct_canon_write_count: int
    untrusted_instruction_execution_count: int
    metrics_id: str = ""

    def __post_init__(self) -> None:
        for name in (
            "total_case_count",
            "synthetic_case_count",
            "real_case_count",
            "human_labelled_case_count",
            "expected_claim_count",
            "predicted_claim_count",
            "matched_claim_count",
            "expected_source_span_count",
            "predicted_source_span_count",
            "correct_source_span_count",
            "expected_exception_count",
            "matched_exception_count",
            "expected_relation_count",
            "predicted_relation_count",
            "matched_relation_count",
            "false_relation_count",
            "expected_contradiction_count",
            "matched_contradiction_count",
            "expected_qualifier_count",
            "connected_qualifier_count",
            "source_claim_count",
            "orphan_source_claim_count",
            "synthesis_claim_count",
            "unsupported_synthesis_claim_count",
            "replay_match_count",
            "resume_reused_units",
            "resume_eligible_units",
            "total_session_wall_time_ms",
            "total_model_tokens",
            "total_projection_bytes",
            "truth_gate_bypass_count",
            "query_path_write_count",
            "direct_canon_write_count",
            "untrusted_instruction_execution_count",
        ):
            _nonnegative_int(getattr(self, name), name)
        if (
            self.synthetic_case_count
            + self.real_case_count
            + self.human_labelled_case_count
            != self.total_case_count
        ):
            raise ReaderEvaluationError(
                "corpus case counts must sum to total_case_count"
            )
        for name in (
            "section_latency_p50_ms",
            "section_latency_p95_ms",
            "rebuild_time_p95_ms",
        ):
            value = getattr(self, name)
            if value is not None:
                _nonnegative_int(value, name)
        if (
            isinstance(self.max_query_path_latency_delta_ms, bool)
            or not isinstance(self.max_query_path_latency_delta_ms, int)
        ):
            raise ReaderEvaluationError(
                "max_query_path_latency_delta_ms must be an integer"
            )
        expected = stable_reader_core_id(
            "reader-evaluation-metrics",
            self.identity_payload(include_id=False),
        )
        if self.metrics_id:
            if self.metrics_id != expected:
                raise ReaderEvaluationError(
                    "metrics_id does not match metric content"
                )
        else:
            object.__setattr__(self, "metrics_id", expected)

    @property
    def claim_fidelity(self) -> float | None:
        return _ratio(self.matched_claim_count, self.expected_claim_count)

    @property
    def source_span_precision(self) -> float | None:
        return _ratio(
            self.correct_source_span_count,
            self.predicted_source_span_count,
        )

    @property
    def source_span_recall(self) -> float | None:
        return _ratio(
            self.correct_source_span_count,
            self.expected_source_span_count,
        )

    @property
    def critical_exception_recall(self) -> float | None:
        return _ratio(
            self.matched_exception_count,
            self.expected_exception_count,
        )

    @property
    def relation_recall(self) -> float | None:
        return _ratio(self.matched_relation_count, self.expected_relation_count)

    @property
    def false_relation_rate(self) -> float | None:
        return _ratio(self.false_relation_count, self.predicted_relation_count)

    @property
    def contradiction_recall(self) -> float | None:
        return _ratio(
            self.matched_contradiction_count,
            self.expected_contradiction_count,
        )

    @property
    def orphan_claim_rate(self) -> float | None:
        return _ratio(self.orphan_source_claim_count, self.source_claim_count)

    @property
    def qualifier_connectivity(self) -> float | None:
        return _ratio(
            self.connected_qualifier_count,
            self.expected_qualifier_count,
        )

    @property
    def unsupported_synthesis_rate(self) -> float | None:
        return _ratio(
            self.unsupported_synthesis_claim_count,
            self.synthesis_claim_count,
        )

    @property
    def replay_match_rate(self) -> float | None:
        return _ratio(self.replay_match_count, self.total_case_count)

    @property
    def resume_reuse_ratio(self) -> float | None:
        return _ratio(self.resume_reused_units, self.resume_eligible_units)

    @property
    def model_tokens_per_case(self) -> float | None:
        return _ratio(self.total_model_tokens, self.total_case_count)

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload = {
            name: getattr(self, name)
            for name in self.__dataclass_fields__
            if name != "metrics_id"
        }
        if include_id:
            payload["metrics_id"] = self.metrics_id
        return payload


@dataclass(frozen=True, slots=True)
class EvaluationSuiteReport:
    evaluator_version: str
    environment: EvaluationEnvironment
    case_results: tuple[ReaderEvaluationCaseResult, ...]
    metrics: ReaderEvaluationMetrics
    warnings: tuple[str, ...] = ()
    schema_version: str = READER_EVALUATION_SCHEMA_VERSION
    report_id: str = ""

    def __post_init__(self) -> None:
        _require_text(self.evaluator_version, "evaluator_version")
        if self.schema_version != READER_EVALUATION_SCHEMA_VERSION:
            raise ReaderEvaluationError("unsupported evaluation report schema")
        if not isinstance(self.environment, EvaluationEnvironment):
            raise ReaderEvaluationError(
                "environment must be an EvaluationEnvironment"
            )
        cases = tuple(self.case_results)
        if not cases or any(
            not isinstance(case, ReaderEvaluationCaseResult) for case in cases
        ):
            raise ReaderEvaluationError(
                "case_results require at least one ReaderEvaluationCaseResult"
            )
        ordered = tuple(sorted(cases, key=lambda item: item.manifest.case_id))
        if cases != ordered:
            raise ReaderEvaluationError("case_results must use canonical case order")
        if len({case.manifest.case_id for case in cases}) != len(cases):
            raise ReaderEvaluationError("case result IDs must be unique")
        if not isinstance(self.metrics, ReaderEvaluationMetrics):
            raise ReaderEvaluationError(
                "metrics must be ReaderEvaluationMetrics"
            )
        expected_metrics = _aggregate_metrics(cases)
        if self.metrics != expected_metrics:
            raise ReaderEvaluationError(
                "metrics must exactly match case result aggregation"
            )
        warnings = _unique_text_tuple(self.warnings, "warning")
        object.__setattr__(self, "case_results", cases)
        object.__setattr__(self, "warnings", warnings)
        expected = stable_reader_core_id(
            "reader-evaluation-suite-report",
            self.identity_payload(include_id=False),
        )
        if self.report_id:
            if self.report_id != expected:
                raise ReaderEvaluationError(
                    "report_id does not match evaluation report content"
                )
        else:
            object.__setattr__(self, "report_id", expected)

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema_version": self.schema_version,
            "evaluator_version": self.evaluator_version,
            "environment_id": self.environment.environment_id,
            "case_result_ids": [case.case_result_id for case in self.case_results],
            "metrics_id": self.metrics.metrics_id,
            "warnings": list(self.warnings),
        }
        if include_id:
            payload["report_id"] = self.report_id
        return payload


class ReaderCoreEvaluationAggregator:
    """Aggregate pre-measured labelled case results into a reproducible report."""

    evaluator_version = "1.0.0"

    def build_report(
        self,
        environment: EvaluationEnvironment,
        case_results: Iterable[ReaderEvaluationCaseResult],
    ) -> EvaluationSuiteReport:
        if not isinstance(environment, EvaluationEnvironment):
            raise ReaderEvaluationError(
                "environment must be an EvaluationEnvironment"
            )
        cases = tuple(sorted(case_results, key=lambda item: item.manifest.case_id))
        if not cases:
            raise ReaderEvaluationError("case_results must not be empty")
        metrics = _aggregate_metrics(cases)
        warnings: list[str] = []
        if metrics.real_case_count == 0:
            warnings.append("real_corpus_not_evaluated")
        if metrics.human_labelled_case_count == 0:
            warnings.append("human_labelled_corpus_not_evaluated")
        if metrics.resume_eligible_units == 0:
            warnings.append("resume_reuse_not_measured")
        return EvaluationSuiteReport(
            evaluator_version=self.evaluator_version,
            environment=environment,
            case_results=cases,
            metrics=metrics,
            warnings=tuple(warnings),
        )


@dataclass(frozen=True, slots=True)
class ReaderPromotionThresholds:
    min_total_cases: int
    min_synthetic_cases: int
    min_real_cases: int
    min_human_labelled_cases: int
    min_claim_fidelity: float
    min_source_span_precision: float
    min_source_span_recall: float
    min_critical_exception_recall: float
    min_relation_recall: float
    max_false_relation_rate: float
    min_contradiction_recall: float
    max_orphan_claim_rate: float
    min_qualifier_connectivity: float
    max_unsupported_synthesis_rate: float
    min_replay_match_rate: float
    min_resume_reuse_ratio: float
    max_query_path_latency_delta_ms: int
    max_section_latency_p95_ms: int | None = None
    max_model_tokens_per_case: float | None = None
    thresholds_id: str = ""

    def __post_init__(self) -> None:
        for name in (
            "min_total_cases",
            "min_synthetic_cases",
            "min_real_cases",
            "min_human_labelled_cases",
        ):
            _nonnegative_int(getattr(self, name), name)
        for name in (
            "min_claim_fidelity",
            "min_source_span_precision",
            "min_source_span_recall",
            "min_critical_exception_recall",
            "min_relation_recall",
            "max_false_relation_rate",
            "min_contradiction_recall",
            "max_orphan_claim_rate",
            "min_qualifier_connectivity",
            "max_unsupported_synthesis_rate",
            "min_replay_match_rate",
            "min_resume_reuse_ratio",
        ):
            _probability(getattr(self, name), name)
        _nonnegative_int(
            self.max_query_path_latency_delta_ms,
            "max_query_path_latency_delta_ms",
        )
        if self.max_section_latency_p95_ms is not None:
            _nonnegative_int(
                self.max_section_latency_p95_ms,
                "max_section_latency_p95_ms",
            )
        if self.max_model_tokens_per_case is not None:
            value = self.max_model_tokens_per_case
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(float(value))
                or float(value) < 0
            ):
                raise ReaderEvaluationError(
                    "max_model_tokens_per_case must be finite and >= 0"
                )
            object.__setattr__(self, "max_model_tokens_per_case", float(value))
        expected = stable_reader_core_id(
            "reader-promotion-thresholds",
            self.identity_payload(include_id=False),
        )
        if self.thresholds_id:
            if self.thresholds_id != expected:
                raise ReaderEvaluationError(
                    "thresholds_id does not match threshold content"
                )
        else:
            object.__setattr__(self, "thresholds_id", expected)

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload = {
            name: getattr(self, name)
            for name in self.__dataclass_fields__
            if name != "thresholds_id"
        }
        if include_id:
            payload["thresholds_id"] = self.thresholds_id
        return payload


@dataclass(frozen=True, slots=True)
class ReaderPromotionReview:
    report_id: str
    thresholds_id: str
    decision: PromotionDecision
    failed_gate_codes: tuple[str, ...]
    insufficient_evidence_codes: tuple[str, ...]
    operator_go_required: bool = True
    live_integration_authorized: bool = False
    review_id: str = ""

    def __post_init__(self) -> None:
        _require_text(self.report_id, "report_id")
        _require_text(self.thresholds_id, "thresholds_id")
        if not isinstance(self.decision, PromotionDecision):
            raise ReaderEvaluationError(
                "decision must be a PromotionDecision"
            )
        failures = _unique_sorted_text(self.failed_gate_codes, "failed_gate_code")
        insufficient = _unique_sorted_text(
            self.insufficient_evidence_codes,
            "insufficient_evidence_code",
        )
        if not isinstance(self.operator_go_required, bool):
            raise ReaderEvaluationError("operator_go_required must be a boolean")
        if not self.operator_go_required:
            raise ReaderEvaluationError("operator GO must always remain required")
        if not isinstance(self.live_integration_authorized, bool):
            raise ReaderEvaluationError(
                "live_integration_authorized must be a boolean"
            )
        if self.live_integration_authorized:
            raise ReaderEvaluationError(
                "promotion review cannot authorize live integration"
            )
        if self.decision is PromotionDecision.ELIGIBLE_FOR_OPERATOR_REVIEW:
            if failures or insufficient:
                raise ReaderEvaluationError(
                    "eligible review cannot contain failed or insufficient gates"
                )
        elif self.decision is PromotionDecision.NO_GO:
            if not failures:
                raise ReaderEvaluationError("NO_GO requires failed gates")
        elif not insufficient:
            raise ReaderEvaluationError(
                "INSUFFICIENT_EVIDENCE requires evidence codes"
            )
        object.__setattr__(self, "failed_gate_codes", failures)
        object.__setattr__(self, "insufficient_evidence_codes", insufficient)
        expected = stable_reader_core_id(
            "reader-promotion-review",
            self.identity_payload(include_id=False),
        )
        if self.review_id:
            if self.review_id != expected:
                raise ReaderEvaluationError(
                    "review_id does not match promotion review content"
                )
        else:
            object.__setattr__(self, "review_id", expected)

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "report_id": self.report_id,
            "thresholds_id": self.thresholds_id,
            "decision": self.decision.value,
            "failed_gate_codes": list(self.failed_gate_codes),
            "insufficient_evidence_codes": list(
                self.insufficient_evidence_codes
            ),
            "operator_go_required": self.operator_go_required,
            "live_integration_authorized": self.live_integration_authorized,
        }
        if include_id:
            payload["review_id"] = self.review_id
        return payload


class ReaderCorePromotionReviewer:
    """Evaluate explicit thresholds without authorizing promotion."""

    def review(
        self,
        report: EvaluationSuiteReport,
        thresholds: ReaderPromotionThresholds,
    ) -> ReaderPromotionReview:
        if not isinstance(report, EvaluationSuiteReport):
            raise ReaderEvaluationError("report must be EvaluationSuiteReport")
        if not isinstance(thresholds, ReaderPromotionThresholds):
            raise ReaderEvaluationError(
                "thresholds must be ReaderPromotionThresholds"
            )
        metrics = report.metrics
        hard_failures = self._hard_safety_failures(metrics)
        if hard_failures:
            return ReaderPromotionReview(
                report_id=report.report_id,
                thresholds_id=thresholds.thresholds_id,
                decision=PromotionDecision.NO_GO,
                failed_gate_codes=tuple(sorted(hard_failures)),
                insufficient_evidence_codes=(),
            )
        insufficient = self._insufficient_evidence(metrics, thresholds)
        if insufficient:
            return ReaderPromotionReview(
                report_id=report.report_id,
                thresholds_id=thresholds.thresholds_id,
                decision=PromotionDecision.INSUFFICIENT_EVIDENCE,
                failed_gate_codes=(),
                insufficient_evidence_codes=tuple(sorted(insufficient)),
            )
        failures = self._threshold_failures(metrics, thresholds)
        decision = (
            PromotionDecision.NO_GO
            if failures
            else PromotionDecision.ELIGIBLE_FOR_OPERATOR_REVIEW
        )
        return ReaderPromotionReview(
            report_id=report.report_id,
            thresholds_id=thresholds.thresholds_id,
            decision=decision,
            failed_gate_codes=tuple(sorted(failures)),
            insufficient_evidence_codes=(),
        )

    @staticmethod
    def _hard_safety_failures(metrics: ReaderEvaluationMetrics) -> set[str]:
        failures: set[str] = set()
        if metrics.truth_gate_bypass_count != 0:
            failures.add("truth_gate_bypass_count_nonzero")
        if metrics.query_path_write_count != 0:
            failures.add("query_path_write_count_nonzero")
        if metrics.direct_canon_write_count != 0:
            failures.add("direct_canon_write_count_nonzero")
        if metrics.untrusted_instruction_execution_count != 0:
            failures.add("untrusted_instruction_execution_count_nonzero")
        return failures

    @staticmethod
    def _insufficient_evidence(
        metrics: ReaderEvaluationMetrics,
        thresholds: ReaderPromotionThresholds,
    ) -> set[str]:
        codes: set[str] = set()
        count_checks = (
            (
                metrics.total_case_count,
                thresholds.min_total_cases,
                "total_case_count_below_minimum",
            ),
            (
                metrics.synthetic_case_count,
                thresholds.min_synthetic_cases,
                "synthetic_case_count_below_minimum",
            ),
            (
                metrics.real_case_count,
                thresholds.min_real_cases,
                "real_case_count_below_minimum",
            ),
            (
                metrics.human_labelled_case_count,
                thresholds.min_human_labelled_cases,
                "human_labelled_case_count_below_minimum",
            ),
        )
        for actual, minimum, code in count_checks:
            if actual < minimum:
                codes.add(code)
        ratio_checks = (
            (metrics.claim_fidelity, "claim_fidelity_not_measured"),
            (metrics.source_span_precision, "source_span_precision_not_measured"),
            (metrics.source_span_recall, "source_span_recall_not_measured"),
            (
                metrics.critical_exception_recall,
                "critical_exception_recall_not_measured",
            ),
            (metrics.relation_recall, "relation_recall_not_measured"),
            (metrics.false_relation_rate, "false_relation_rate_not_measured"),
            (
                metrics.contradiction_recall,
                "contradiction_recall_not_measured",
            ),
            (metrics.orphan_claim_rate, "orphan_claim_rate_not_measured"),
            (
                metrics.qualifier_connectivity,
                "qualifier_connectivity_not_measured",
            ),
            (
                metrics.unsupported_synthesis_rate,
                "unsupported_synthesis_rate_not_measured",
            ),
            (metrics.replay_match_rate, "replay_match_rate_not_measured"),
            (metrics.resume_reuse_ratio, "resume_reuse_ratio_not_measured"),
        )
        for value, code in ratio_checks:
            if value is None:
                codes.add(code)
        if (
            thresholds.max_section_latency_p95_ms is not None
            and metrics.section_latency_p95_ms is None
        ):
            codes.add("section_latency_p95_not_measured")
        if (
            thresholds.max_model_tokens_per_case is not None
            and metrics.model_tokens_per_case is None
        ):
            codes.add("model_tokens_per_case_not_measured")
        return codes

    @staticmethod
    def _threshold_failures(
        metrics: ReaderEvaluationMetrics,
        thresholds: ReaderPromotionThresholds,
    ) -> set[str]:
        failures: set[str] = set()
        minimum_checks = (
            (
                metrics.claim_fidelity,
                thresholds.min_claim_fidelity,
                "claim_fidelity_below_threshold",
            ),
            (
                metrics.source_span_precision,
                thresholds.min_source_span_precision,
                "source_span_precision_below_threshold",
            ),
            (
                metrics.source_span_recall,
                thresholds.min_source_span_recall,
                "source_span_recall_below_threshold",
            ),
            (
                metrics.critical_exception_recall,
                thresholds.min_critical_exception_recall,
                "critical_exception_recall_below_threshold",
            ),
            (
                metrics.relation_recall,
                thresholds.min_relation_recall,
                "relation_recall_below_threshold",
            ),
            (
                metrics.contradiction_recall,
                thresholds.min_contradiction_recall,
                "contradiction_recall_below_threshold",
            ),
            (
                metrics.qualifier_connectivity,
                thresholds.min_qualifier_connectivity,
                "qualifier_connectivity_below_threshold",
            ),
            (
                metrics.replay_match_rate,
                thresholds.min_replay_match_rate,
                "replay_match_rate_below_threshold",
            ),
            (
                metrics.resume_reuse_ratio,
                thresholds.min_resume_reuse_ratio,
                "resume_reuse_ratio_below_threshold",
            ),
        )
        maximum_checks = (
            (
                metrics.false_relation_rate,
                thresholds.max_false_relation_rate,
                "false_relation_rate_above_threshold",
            ),
            (
                metrics.orphan_claim_rate,
                thresholds.max_orphan_claim_rate,
                "orphan_claim_rate_above_threshold",
            ),
            (
                metrics.unsupported_synthesis_rate,
                thresholds.max_unsupported_synthesis_rate,
                "unsupported_synthesis_rate_above_threshold",
            ),
        )
        for value, minimum, code in minimum_checks:
            if value is not None and value < minimum:
                failures.add(code)
        for value, maximum, code in maximum_checks:
            if value is not None and value > maximum:
                failures.add(code)
        if (
            metrics.max_query_path_latency_delta_ms
            > thresholds.max_query_path_latency_delta_ms
        ):
            failures.add("query_path_latency_delta_above_threshold")
        if (
            thresholds.max_section_latency_p95_ms is not None
            and metrics.section_latency_p95_ms is not None
            and metrics.section_latency_p95_ms
            > thresholds.max_section_latency_p95_ms
        ):
            failures.add("section_latency_p95_above_threshold")
        if (
            thresholds.max_model_tokens_per_case is not None
            and metrics.model_tokens_per_case is not None
            and metrics.model_tokens_per_case
            > thresholds.max_model_tokens_per_case
        ):
            failures.add("model_tokens_per_case_above_threshold")
        return failures


def _aggregate_metrics(
    cases: tuple[ReaderEvaluationCaseResult, ...],
) -> ReaderEvaluationMetrics:
    latencies = tuple(
        latency
        for case in cases
        for latency in case.section_latencies_ms
    )
    rebuild_times = tuple(case.rebuild_time_ms for case in cases)
    corpus_counts = {
        kind: sum(case.manifest.corpus_kind is kind for case in cases)
        for kind in EvaluationCorpusKind
    }
    return ReaderEvaluationMetrics(
        total_case_count=len(cases),
        synthetic_case_count=corpus_counts[EvaluationCorpusKind.SYNTHETIC],
        real_case_count=corpus_counts[EvaluationCorpusKind.REAL],
        human_labelled_case_count=corpus_counts[
            EvaluationCorpusKind.HUMAN_LABELLED
        ],
        expected_claim_count=sum(
            case.manifest.expected_claim_count for case in cases
        ),
        predicted_claim_count=sum(case.predicted_claim_count for case in cases),
        matched_claim_count=sum(case.matched_claim_count for case in cases),
        expected_source_span_count=sum(
            case.manifest.expected_source_span_count for case in cases
        ),
        predicted_source_span_count=sum(
            case.predicted_source_span_count for case in cases
        ),
        correct_source_span_count=sum(
            case.correct_source_span_count for case in cases
        ),
        expected_exception_count=sum(
            case.manifest.expected_exception_count for case in cases
        ),
        matched_exception_count=sum(
            case.matched_exception_count for case in cases
        ),
        expected_relation_count=sum(
            case.manifest.expected_relation_count for case in cases
        ),
        predicted_relation_count=sum(
            case.predicted_relation_count for case in cases
        ),
        matched_relation_count=sum(case.matched_relation_count for case in cases),
        false_relation_count=sum(case.false_relation_count for case in cases),
        expected_contradiction_count=sum(
            case.manifest.expected_contradiction_count for case in cases
        ),
        matched_contradiction_count=sum(
            case.matched_contradiction_count for case in cases
        ),
        expected_qualifier_count=sum(
            case.manifest.expected_qualifier_count for case in cases
        ),
        connected_qualifier_count=sum(
            case.connected_qualifier_count for case in cases
        ),
        source_claim_count=sum(case.source_claim_count for case in cases),
        orphan_source_claim_count=sum(
            case.orphan_source_claim_count for case in cases
        ),
        synthesis_claim_count=sum(case.synthesis_claim_count for case in cases),
        unsupported_synthesis_claim_count=sum(
            case.unsupported_synthesis_claim_count for case in cases
        ),
        replay_match_count=sum(case.replay.matched for case in cases),
        resume_reused_units=sum(case.resume_reused_units for case in cases),
        resume_eligible_units=sum(case.resume_eligible_units for case in cases),
        section_latency_p50_ms=_nearest_rank_percentile(latencies, 0.50),
        section_latency_p95_ms=_nearest_rank_percentile(latencies, 0.95),
        total_session_wall_time_ms=sum(
            case.session_wall_time_ms for case in cases
        ),
        total_model_tokens=sum(case.model_tokens for case in cases),
        total_projection_bytes=sum(case.projection_bytes for case in cases),
        rebuild_time_p95_ms=_nearest_rank_percentile(rebuild_times, 0.95),
        max_query_path_latency_delta_ms=max(
            (case.query_path_latency_delta_ms for case in cases),
            default=0,
        ),
        truth_gate_bypass_count=sum(
            case.truth_gate_bypass_count for case in cases
        ),
        query_path_write_count=sum(case.query_path_write_count for case in cases),
        direct_canon_write_count=sum(
            case.direct_canon_write_count for case in cases
        ),
        untrusted_instruction_execution_count=sum(
            case.untrusted_instruction_execution_count for case in cases
        ),
    )


def _nearest_rank_percentile(
    values: Iterable[int],
    percentile: float,
) -> int | None:
    ordered = tuple(sorted(values))
    if not ordered:
        return None
    rank = max(1, math.ceil(percentile * len(ordered)))
    return ordered[rank - 1]


def _ratio(numerator: int, denominator: int) -> float | None:
    return None if denominator == 0 else numerator / denominator


def _probability(value: float, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ReaderEvaluationError(f"{field_name} must be a number in [0, 1]")
    result = float(value)
    if not math.isfinite(result) or not 0.0 <= result <= 1.0:
        raise ReaderEvaluationError(f"{field_name} must be finite and in [0, 1]")
    return result


def _nonnegative_int(value: int, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ReaderEvaluationError(f"{field_name} must be an integer >= 0")
    return value


def _require_text(value: str | None, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReaderEvaluationError(f"{field_name} must be a non-empty string")
    return value


def _text_tuple(values: Iterable[str], field_name: str) -> tuple[str, ...]:
    result = tuple(values)
    for value in result:
        _require_text(value, field_name)
    return result


def _unique_text_tuple(
    values: Iterable[str],
    field_name: str,
) -> tuple[str, ...]:
    result = _text_tuple(values, field_name)
    if len(set(result)) != len(result):
        raise ReaderEvaluationError(f"{field_name} values must be unique")
    return result


def _unique_sorted_text(
    values: Iterable[str],
    field_name: str,
) -> tuple[str, ...]:
    result = _unique_text_tuple(values, field_name)
    ordered = tuple(sorted(result))
    if result != ordered:
        raise ReaderEvaluationError(f"{field_name} values must be sorted")
    return result


__all__ = [
    "READER_EVALUATION_MANIFEST_SCHEMA_VERSION",
    "READER_EVALUATION_SCHEMA_VERSION",
    "EvaluationCorpusKind",
    "EvaluationCorpusManifest",
    "EvaluationEnvironment",
    "EvaluationSuiteReport",
    "PromotionDecision",
    "ReaderCoreEvaluationAggregator",
    "ReaderCorePromotionReviewer",
    "ReaderEvaluationCaseManifest",
    "ReaderEvaluationCaseResult",
    "ReaderEvaluationError",
    "ReaderEvaluationMetrics",
    "ReaderPromotionReview",
    "ReaderPromotionThresholds",
    "ReaderReplayComparator",
    "ReplayComparison",
]
