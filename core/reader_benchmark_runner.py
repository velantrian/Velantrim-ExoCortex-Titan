"""Executable, local-only Reader Core benchmark runner for PR-RDR-10.

The runner consumes explicit source-controlled manifests, measured observations,
and promotion thresholds. It builds the PR-RDR-09 report and review objects,
serializes a canonical benchmark bundle, and can authenticate that bundle with a
detached HMAC-SHA256 signature.

It does not execute a model, read a live query path, persist memory, write Canon,
authorize promotion, or grant any runtime authority.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
import hashlib
import hmac
import json
import os
from pathlib import Path
from typing import cast

from core.reader_core_contracts import stable_reader_core_id
from core.reader_evaluation import (
    READER_EVALUATION_MANIFEST_SCHEMA_VERSION,
    EvaluationCorpusKind,
    EvaluationCorpusManifest,
    EvaluationEnvironment,
    EvaluationSuiteReport,
    ReaderCoreEvaluationAggregator,
    ReaderCorePromotionReviewer,
    ReaderEvaluationCaseManifest,
    ReaderEvaluationCaseResult,
    ReaderEvaluationError,
    ReaderPromotionReview,
    ReaderPromotionThresholds,
    ReaderReplayComparator,
)

READER_BENCHMARK_INPUT_SCHEMA_VERSION = "reader-core.benchmark-input.v1"
READER_BENCHMARK_THRESHOLDS_SCHEMA_VERSION = "reader-core.promotion-thresholds.v1"
READER_BENCHMARK_BUNDLE_SCHEMA_VERSION = "reader-core.benchmark-bundle.v1"
READER_BENCHMARK_SIGNATURE_SCHEMA_VERSION = "reader-core.benchmark-signature.v1"
READER_BENCHMARK_SIGNATURE_ALGORITHM = "hmac-sha256"


class ReaderBenchmarkError(ValueError):
    """Raised when benchmark inputs, bundles, or signatures are invalid."""


@dataclass(frozen=True, slots=True)
class ReaderBenchmarkObservation:
    """One explicit, pre-measured benchmark observation.

    Artifact IDs preserve order because replay determinism is order-sensitive.
    No field is inferred from a model or a live runtime path by this contract.
    """

    case_id: str
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
    first_artifact_ids: tuple[str, ...]
    second_artifact_ids: tuple[str, ...]
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
    observation_id: str = ""

    def __post_init__(self) -> None:
        _require_text(self.case_id, "case_id")
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
            raise ReaderBenchmarkError(
                "query_path_latency_delta_ms must be an integer"
            )
        first = _text_tuple(self.first_artifact_ids, "first_artifact_id")
        second = _text_tuple(self.second_artifact_ids, "second_artifact_id")
        latencies = tuple(self.section_latencies_ms)
        for latency in latencies:
            _nonnegative_int(latency, "section_latency_ms")
        warnings = _unique_sorted_text(self.warnings, "warning")
        object.__setattr__(self, "first_artifact_ids", first)
        object.__setattr__(self, "second_artifact_ids", second)
        object.__setattr__(self, "section_latencies_ms", latencies)
        object.__setattr__(self, "warnings", warnings)
        expected = stable_reader_core_id(
            "reader-benchmark-observation",
            self.identity_payload(include_id=False),
        )
        if self.observation_id:
            if self.observation_id != expected:
                raise ReaderBenchmarkError(
                    "observation_id does not match observation content"
                )
        else:
            object.__setattr__(self, "observation_id", expected)

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "case_id": self.case_id,
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
            "first_artifact_ids": list(self.first_artifact_ids),
            "second_artifact_ids": list(self.second_artifact_ids),
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
            payload["observation_id"] = self.observation_id
        return payload

    def to_case_result(
        self,
        manifest: ReaderEvaluationCaseManifest,
    ) -> ReaderEvaluationCaseResult:
        if manifest.case_id != self.case_id:
            raise ReaderBenchmarkError(
                "observation case_id must match case manifest"
            )
        replay = ReaderReplayComparator.compare(
            self.case_id,
            self.first_artifact_ids,
            self.second_artifact_ids,
        )
        return ReaderEvaluationCaseResult(
            manifest=manifest,
            predicted_claim_count=self.predicted_claim_count,
            matched_claim_count=self.matched_claim_count,
            predicted_source_span_count=self.predicted_source_span_count,
            correct_source_span_count=self.correct_source_span_count,
            predicted_exception_count=self.predicted_exception_count,
            matched_exception_count=self.matched_exception_count,
            predicted_relation_count=self.predicted_relation_count,
            matched_relation_count=self.matched_relation_count,
            false_relation_count=self.false_relation_count,
            matched_contradiction_count=self.matched_contradiction_count,
            connected_qualifier_count=self.connected_qualifier_count,
            source_claim_count=self.source_claim_count,
            orphan_source_claim_count=self.orphan_source_claim_count,
            synthesis_claim_count=self.synthesis_claim_count,
            unsupported_synthesis_claim_count=(
                self.unsupported_synthesis_claim_count
            ),
            replay=replay,
            section_latencies_ms=self.section_latencies_ms,
            session_wall_time_ms=self.session_wall_time_ms,
            model_tokens=self.model_tokens,
            projection_bytes=self.projection_bytes,
            rebuild_time_ms=self.rebuild_time_ms,
            query_path_latency_delta_ms=self.query_path_latency_delta_ms,
            resume_reused_units=self.resume_reused_units,
            resume_eligible_units=self.resume_eligible_units,
            truth_gate_bypass_count=self.truth_gate_bypass_count,
            query_path_write_count=self.query_path_write_count,
            direct_canon_write_count=self.direct_canon_write_count,
            untrusted_instruction_execution_count=(
                self.untrusted_instruction_execution_count
            ),
            warnings=self.warnings,
        )


@dataclass(frozen=True, slots=True)
class ReaderBenchmarkInput:
    environment: EvaluationEnvironment
    observations: tuple[ReaderBenchmarkObservation, ...]
    schema_version: str = READER_BENCHMARK_INPUT_SCHEMA_VERSION
    benchmark_input_id: str = ""

    def __post_init__(self) -> None:
        if self.schema_version != READER_BENCHMARK_INPUT_SCHEMA_VERSION:
            raise ReaderBenchmarkError("unsupported benchmark input schema")
        if not isinstance(self.environment, EvaluationEnvironment):
            raise ReaderBenchmarkError(
                "environment must be an EvaluationEnvironment"
            )
        observations = tuple(self.observations)
        if not observations or any(
            not isinstance(item, ReaderBenchmarkObservation)
            for item in observations
        ):
            raise ReaderBenchmarkError(
                "observations require at least one ReaderBenchmarkObservation"
            )
        ordered = tuple(sorted(observations, key=lambda item: item.case_id))
        if len({item.case_id for item in ordered}) != len(ordered):
            raise ReaderBenchmarkError("observation case IDs must be unique")
        object.__setattr__(self, "observations", ordered)
        expected = stable_reader_core_id(
            "reader-benchmark-input",
            self.identity_payload(include_id=False),
        )
        if self.benchmark_input_id:
            if self.benchmark_input_id != expected:
                raise ReaderBenchmarkError(
                    "benchmark_input_id does not match input content"
                )
        else:
            object.__setattr__(self, "benchmark_input_id", expected)

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema_version": self.schema_version,
            "environment_id": self.environment.environment_id,
            "observation_ids": [
                item.observation_id for item in self.observations
            ],
        }
        if include_id:
            payload["benchmark_input_id"] = self.benchmark_input_id
        return payload


@dataclass(frozen=True, slots=True)
class ReaderBenchmarkBundle:
    manifest: EvaluationCorpusManifest
    benchmark_input: ReaderBenchmarkInput
    thresholds: ReaderPromotionThresholds
    report: EvaluationSuiteReport
    review: ReaderPromotionReview
    schema_version: str = READER_BENCHMARK_BUNDLE_SCHEMA_VERSION
    input_digest: str = ""
    bundle_id: str = ""

    def __post_init__(self) -> None:
        if self.schema_version != READER_BENCHMARK_BUNDLE_SCHEMA_VERSION:
            raise ReaderBenchmarkError("unsupported benchmark bundle schema")
        if not isinstance(self.manifest, EvaluationCorpusManifest):
            raise ReaderBenchmarkError(
                "manifest must be an EvaluationCorpusManifest"
            )
        if not isinstance(self.benchmark_input, ReaderBenchmarkInput):
            raise ReaderBenchmarkError(
                "benchmark_input must be a ReaderBenchmarkInput"
            )
        if not isinstance(self.thresholds, ReaderPromotionThresholds):
            raise ReaderBenchmarkError(
                "thresholds must be ReaderPromotionThresholds"
            )
        if not isinstance(self.report, EvaluationSuiteReport):
            raise ReaderBenchmarkError("report must be EvaluationSuiteReport")
        if not isinstance(self.review, ReaderPromotionReview):
            raise ReaderBenchmarkError("review must be ReaderPromotionReview")
        manifest_case_ids = tuple(case.case_id for case in self.manifest.cases)
        observation_case_ids = tuple(
            item.case_id for item in self.benchmark_input.observations
        )
        report_case_ids = tuple(
            item.manifest.case_id for item in self.report.case_results
        )
        if observation_case_ids != manifest_case_ids:
            raise ReaderBenchmarkError(
                "observations must exactly cover manifest cases"
            )
        if report_case_ids != manifest_case_ids:
            raise ReaderBenchmarkError(
                "report must exactly cover manifest cases"
            )
        if self.report.environment != self.benchmark_input.environment:
            raise ReaderBenchmarkError(
                "report environment must match benchmark input"
            )
        if self.review.report_id != self.report.report_id:
            raise ReaderBenchmarkError("review must reference report_id")
        if self.review.thresholds_id != self.thresholds.thresholds_id:
            raise ReaderBenchmarkError("review must reference thresholds_id")
        expected_input_digest = stable_reader_core_id(
            "reader-benchmark-complete-input",
            {
                "corpus_id": self.manifest.corpus_id,
                "benchmark_input_id": self.benchmark_input.benchmark_input_id,
                "thresholds_id": self.thresholds.thresholds_id,
            },
        )
        if self.input_digest:
            if self.input_digest != expected_input_digest:
                raise ReaderBenchmarkError(
                    "input_digest does not match benchmark inputs"
                )
        else:
            object.__setattr__(self, "input_digest", expected_input_digest)
        expected_bundle_id = stable_reader_core_id(
            "reader-benchmark-bundle",
            self.identity_payload(include_id=False),
        )
        if self.bundle_id:
            if self.bundle_id != expected_bundle_id:
                raise ReaderBenchmarkError(
                    "bundle_id does not match benchmark bundle content"
                )
        else:
            object.__setattr__(self, "bundle_id", expected_bundle_id)

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema_version": self.schema_version,
            "input_digest": self.input_digest,
            "report_id": self.report.report_id,
            "review_id": self.review.review_id,
        }
        if include_id:
            payload["bundle_id"] = self.bundle_id
        return payload


@dataclass(frozen=True, slots=True)
class ReaderBenchmarkSignature:
    bundle_id: str
    key_id: str
    bundle_sha256: str
    signature_hex: str
    algorithm: str = READER_BENCHMARK_SIGNATURE_ALGORITHM
    schema_version: str = READER_BENCHMARK_SIGNATURE_SCHEMA_VERSION
    signature_id: str = ""

    def __post_init__(self) -> None:
        _require_text(self.bundle_id, "bundle_id")
        _require_text(self.key_id, "key_id")
        if self.algorithm != READER_BENCHMARK_SIGNATURE_ALGORITHM:
            raise ReaderBenchmarkError("unsupported signature algorithm")
        if self.schema_version != READER_BENCHMARK_SIGNATURE_SCHEMA_VERSION:
            raise ReaderBenchmarkError("unsupported signature schema")
        _require_sha256_hex(self.bundle_sha256, "bundle_sha256")
        _require_sha256_hex(self.signature_hex, "signature_hex")
        expected = stable_reader_core_id(
            "reader-benchmark-signature",
            self.identity_payload(include_id=False),
        )
        if self.signature_id:
            if self.signature_id != expected:
                raise ReaderBenchmarkError(
                    "signature_id does not match signature content"
                )
        else:
            object.__setattr__(self, "signature_id", expected)

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema_version": self.schema_version,
            "algorithm": self.algorithm,
            "bundle_id": self.bundle_id,
            "key_id": self.key_id,
            "bundle_sha256": self.bundle_sha256,
            "signature_hex": self.signature_hex,
        }
        if include_id:
            payload["signature_id"] = self.signature_id
        return payload


class ReaderBenchmarkRunner:
    """Build a deterministic report and non-authoritative promotion review."""

    def run(
        self,
        manifest: EvaluationCorpusManifest,
        benchmark_input: ReaderBenchmarkInput,
        thresholds: ReaderPromotionThresholds,
    ) -> ReaderBenchmarkBundle:
        if not isinstance(manifest, EvaluationCorpusManifest):
            raise ReaderBenchmarkError(
                "manifest must be an EvaluationCorpusManifest"
            )
        if not isinstance(benchmark_input, ReaderBenchmarkInput):
            raise ReaderBenchmarkError(
                "benchmark_input must be a ReaderBenchmarkInput"
            )
        if not isinstance(thresholds, ReaderPromotionThresholds):
            raise ReaderBenchmarkError(
                "thresholds must be ReaderPromotionThresholds"
            )
        manifests_by_case = {case.case_id: case for case in manifest.cases}
        observed_case_ids = {
            item.case_id for item in benchmark_input.observations
        }
        if observed_case_ids != set(manifests_by_case):
            missing = sorted(set(manifests_by_case) - observed_case_ids)
            extra = sorted(observed_case_ids - set(manifests_by_case))
            raise ReaderBenchmarkError(
                f"observations must exactly cover manifest cases; "
                f"missing={missing}, extra={extra}"
            )
        try:
            case_results = tuple(
                item.to_case_result(manifests_by_case[item.case_id])
                for item in benchmark_input.observations
            )
            report = ReaderCoreEvaluationAggregator().build_report(
                benchmark_input.environment,
                case_results,
            )
            review = ReaderCorePromotionReviewer().review(report, thresholds)
        except ReaderEvaluationError as exc:
            raise ReaderBenchmarkError(str(exc)) from exc
        return ReaderBenchmarkBundle(
            manifest=manifest,
            benchmark_input=benchmark_input,
            thresholds=thresholds,
            report=report,
            review=review,
        )


class ReaderBenchmarkSigner:
    """Create and verify a detached HMAC-SHA256 bundle authenticator."""

    @staticmethod
    def sign(
        bundle: ReaderBenchmarkBundle,
        *,
        key_id: str,
        secret: bytes,
    ) -> ReaderBenchmarkSignature:
        if not isinstance(bundle, ReaderBenchmarkBundle):
            raise ReaderBenchmarkError("bundle must be ReaderBenchmarkBundle")
        _require_text(key_id, "key_id")
        _require_secret(secret)
        bundle_bytes = canonical_json_bytes(bundle)
        bundle_sha256 = hashlib.sha256(bundle_bytes).hexdigest()
        signature_hex = hmac.new(
            secret,
            bundle_bytes,
            hashlib.sha256,
        ).hexdigest()
        return ReaderBenchmarkSignature(
            bundle_id=bundle.bundle_id,
            key_id=key_id,
            bundle_sha256=bundle_sha256,
            signature_hex=signature_hex,
        )

    @staticmethod
    def verify(
        bundle: ReaderBenchmarkBundle,
        signature: ReaderBenchmarkSignature,
        *,
        secret: bytes,
    ) -> bool:
        if not isinstance(bundle, ReaderBenchmarkBundle):
            raise ReaderBenchmarkError("bundle must be ReaderBenchmarkBundle")
        if not isinstance(signature, ReaderBenchmarkSignature):
            raise ReaderBenchmarkError(
                "signature must be ReaderBenchmarkSignature"
            )
        _require_secret(secret)
        if signature.bundle_id != bundle.bundle_id:
            return False
        bundle_bytes = canonical_json_bytes(bundle)
        digest = hashlib.sha256(bundle_bytes).hexdigest()
        if not hmac.compare_digest(signature.bundle_sha256, digest):
            return False
        expected = hmac.new(secret, bundle_bytes, hashlib.sha256).hexdigest()
        return hmac.compare_digest(signature.signature_hex, expected)


def load_evaluation_manifest(path: str | Path) -> EvaluationCorpusManifest:
    root = _read_json_object(path)
    _check_keys(
        root,
        required={"schema_version", "corpus_name", "corpus_version", "cases"},
    )
    schema_version = _as_text(root["schema_version"], "schema_version")
    if schema_version != READER_EVALUATION_MANIFEST_SCHEMA_VERSION:
        raise ReaderBenchmarkError("unsupported evaluation manifest schema")
    cases_payload = _as_sequence(root["cases"], "cases")
    cases = tuple(_parse_case_manifest(item) for item in cases_payload)
    try:
        return EvaluationCorpusManifest(
            schema_version=schema_version,
            corpus_name=_as_text(root["corpus_name"], "corpus_name"),
            corpus_version=_as_text(root["corpus_version"], "corpus_version"),
            cases=cases,
        )
    except ReaderEvaluationError as exc:
        raise ReaderBenchmarkError(str(exc)) from exc


def load_benchmark_input(path: str | Path) -> ReaderBenchmarkInput:
    root = _read_json_object(path)
    _check_keys(
        root,
        required={"schema_version", "environment", "observations"},
    )
    schema_version = _as_text(root["schema_version"], "schema_version")
    if schema_version != READER_BENCHMARK_INPUT_SCHEMA_VERSION:
        raise ReaderBenchmarkError("unsupported benchmark input schema")
    environment = _parse_environment(root["environment"])
    observations_payload = _as_sequence(root["observations"], "observations")
    observations = tuple(
        _parse_observation(item) for item in observations_payload
    )
    return ReaderBenchmarkInput(
        schema_version=schema_version,
        environment=environment,
        observations=observations,
    )


def load_promotion_thresholds(path: str | Path) -> ReaderPromotionThresholds:
    root = _read_json_object(path)
    required = {
        "schema_version",
        "min_total_cases",
        "min_synthetic_cases",
        "min_real_cases",
        "min_human_labelled_cases",
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
        "max_query_path_latency_delta_ms",
        "max_section_latency_p95_ms",
        "max_model_tokens_per_case",
    }
    _check_keys(root, required=required)
    schema_version = _as_text(root["schema_version"], "schema_version")
    if schema_version != READER_BENCHMARK_THRESHOLDS_SCHEMA_VERSION:
        raise ReaderBenchmarkError("unsupported promotion thresholds schema")
    try:
        return ReaderPromotionThresholds(
            min_total_cases=_as_int(root["min_total_cases"], "min_total_cases"),
            min_synthetic_cases=_as_int(
                root["min_synthetic_cases"],
                "min_synthetic_cases",
            ),
            min_real_cases=_as_int(root["min_real_cases"], "min_real_cases"),
            min_human_labelled_cases=_as_int(
                root["min_human_labelled_cases"],
                "min_human_labelled_cases",
            ),
            min_claim_fidelity=_as_float(
                root["min_claim_fidelity"],
                "min_claim_fidelity",
            ),
            min_source_span_precision=_as_float(
                root["min_source_span_precision"],
                "min_source_span_precision",
            ),
            min_source_span_recall=_as_float(
                root["min_source_span_recall"],
                "min_source_span_recall",
            ),
            min_critical_exception_recall=_as_float(
                root["min_critical_exception_recall"],
                "min_critical_exception_recall",
            ),
            min_relation_recall=_as_float(
                root["min_relation_recall"],
                "min_relation_recall",
            ),
            max_false_relation_rate=_as_float(
                root["max_false_relation_rate"],
                "max_false_relation_rate",
            ),
            min_contradiction_recall=_as_float(
                root["min_contradiction_recall"],
                "min_contradiction_recall",
            ),
            max_orphan_claim_rate=_as_float(
                root["max_orphan_claim_rate"],
                "max_orphan_claim_rate",
            ),
            min_qualifier_connectivity=_as_float(
                root["min_qualifier_connectivity"],
                "min_qualifier_connectivity",
            ),
            max_unsupported_synthesis_rate=_as_float(
                root["max_unsupported_synthesis_rate"],
                "max_unsupported_synthesis_rate",
            ),
            min_replay_match_rate=_as_float(
                root["min_replay_match_rate"],
                "min_replay_match_rate",
            ),
            min_resume_reuse_ratio=_as_float(
                root["min_resume_reuse_ratio"],
                "min_resume_reuse_ratio",
            ),
            max_query_path_latency_delta_ms=_as_int(
                root["max_query_path_latency_delta_ms"],
                "max_query_path_latency_delta_ms",
            ),
            max_section_latency_p95_ms=_as_optional_int(
                root["max_section_latency_p95_ms"],
                "max_section_latency_p95_ms",
            ),
            max_model_tokens_per_case=_as_optional_float(
                root["max_model_tokens_per_case"],
                "max_model_tokens_per_case",
            ),
        )
    except ReaderEvaluationError as exc:
        raise ReaderBenchmarkError(str(exc)) from exc


def canonical_json_bytes(value: object) -> bytes:
    payload = _to_jsonable(value)
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def write_canonical_json(path: str | Path, value: object) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(
        f".{destination.name}.{os.getpid()}.tmp"
    )
    try:
        with temporary.open("wb") as handle:
            handle.write(canonical_json_bytes(value))
            handle.write(b"\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
    finally:
        if temporary.exists():
            temporary.unlink()


def _parse_case_manifest(value: object) -> ReaderEvaluationCaseManifest:
    item = _as_mapping(value, "case")
    required = {
        "case_id",
        "corpus_kind",
        "label_version",
        "expected_claim_count",
        "expected_source_span_count",
        "expected_exception_count",
        "expected_relation_count",
        "expected_contradiction_count",
        "expected_qualifier_count",
        "tags",
    }
    _check_keys(item, required=required)
    tags = tuple(
        _as_text(tag, "tag") for tag in _as_sequence(item["tags"], "tags")
    )
    try:
        return ReaderEvaluationCaseManifest(
            case_id=_as_text(item["case_id"], "case_id"),
            corpus_kind=EvaluationCorpusKind(
                _as_text(item["corpus_kind"], "corpus_kind")
            ),
            label_version=_as_text(item["label_version"], "label_version"),
            expected_claim_count=_as_int(
                item["expected_claim_count"],
                "expected_claim_count",
            ),
            expected_source_span_count=_as_int(
                item["expected_source_span_count"],
                "expected_source_span_count",
            ),
            expected_exception_count=_as_int(
                item["expected_exception_count"],
                "expected_exception_count",
            ),
            expected_relation_count=_as_int(
                item["expected_relation_count"],
                "expected_relation_count",
            ),
            expected_contradiction_count=_as_int(
                item["expected_contradiction_count"],
                "expected_contradiction_count",
            ),
            expected_qualifier_count=_as_int(
                item["expected_qualifier_count"],
                "expected_qualifier_count",
            ),
            tags=tags,
        )
    except (ReaderEvaluationError, ValueError) as exc:
        raise ReaderBenchmarkError(str(exc)) from exc


def _parse_environment(value: object) -> EvaluationEnvironment:
    item = _as_mapping(value, "environment")
    required = {
        "commit_sha",
        "runner_id",
        "python_version",
        "hardware_profile",
        "config_digest",
        "model_id",
        "model_version",
    }
    _check_keys(item, required=required)
    try:
        return EvaluationEnvironment(
            commit_sha=_as_text(item["commit_sha"], "commit_sha"),
            runner_id=_as_text(item["runner_id"], "runner_id"),
            python_version=_as_text(
                item["python_version"],
                "python_version",
            ),
            hardware_profile=_as_text(
                item["hardware_profile"],
                "hardware_profile",
            ),
            config_digest=_as_text(
                item["config_digest"],
                "config_digest",
            ),
            model_id=_as_optional_text(item["model_id"], "model_id"),
            model_version=_as_optional_text(
                item["model_version"],
                "model_version",
            ),
        )
    except ReaderEvaluationError as exc:
        raise ReaderBenchmarkError(str(exc)) from exc


def _parse_observation(value: object) -> ReaderBenchmarkObservation:
    item = _as_mapping(value, "observation")
    required = {
        "case_id",
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
        "first_artifact_ids",
        "second_artifact_ids",
        "section_latencies_ms",
        "session_wall_time_ms",
        "model_tokens",
        "projection_bytes",
        "rebuild_time_ms",
        "query_path_latency_delta_ms",
        "resume_reused_units",
        "resume_eligible_units",
        "truth_gate_bypass_count",
        "query_path_write_count",
        "direct_canon_write_count",
        "untrusted_instruction_execution_count",
        "warnings",
    }
    _check_keys(item, required=required)
    integer_fields = {
        name: _as_int(item[name], name)
        for name in required
        if name.endswith("_count")
        or name.endswith("_ms")
        or name
        in {
            "model_tokens",
            "projection_bytes",
            "resume_reused_units",
            "resume_eligible_units",
        }
    }
    first_artifacts = tuple(
        _as_text(entry, "first_artifact_id")
        for entry in _as_sequence(
            item["first_artifact_ids"],
            "first_artifact_ids",
        )
    )
    second_artifacts = tuple(
        _as_text(entry, "second_artifact_id")
        for entry in _as_sequence(
            item["second_artifact_ids"],
            "second_artifact_ids",
        )
    )
    latencies = tuple(
        _as_int(entry, "section_latency_ms")
        for entry in _as_sequence(
            item["section_latencies_ms"],
            "section_latencies_ms",
        )
    )
    warnings = tuple(
        _as_text(entry, "warning")
        for entry in _as_sequence(item["warnings"], "warnings")
    )
    return ReaderBenchmarkObservation(
        case_id=_as_text(item["case_id"], "case_id"),
        predicted_claim_count=integer_fields["predicted_claim_count"],
        matched_claim_count=integer_fields["matched_claim_count"],
        predicted_source_span_count=integer_fields[
            "predicted_source_span_count"
        ],
        correct_source_span_count=integer_fields[
            "correct_source_span_count"
        ],
        predicted_exception_count=integer_fields[
            "predicted_exception_count"
        ],
        matched_exception_count=integer_fields["matched_exception_count"],
        predicted_relation_count=integer_fields["predicted_relation_count"],
        matched_relation_count=integer_fields["matched_relation_count"],
        false_relation_count=integer_fields["false_relation_count"],
        matched_contradiction_count=integer_fields[
            "matched_contradiction_count"
        ],
        connected_qualifier_count=integer_fields[
            "connected_qualifier_count"
        ],
        source_claim_count=integer_fields["source_claim_count"],
        orphan_source_claim_count=integer_fields["orphan_source_claim_count"],
        synthesis_claim_count=integer_fields["synthesis_claim_count"],
        unsupported_synthesis_claim_count=integer_fields[
            "unsupported_synthesis_claim_count"
        ],
        first_artifact_ids=first_artifacts,
        second_artifact_ids=second_artifacts,
        section_latencies_ms=latencies,
        session_wall_time_ms=integer_fields["session_wall_time_ms"],
        model_tokens=integer_fields["model_tokens"],
        projection_bytes=integer_fields["projection_bytes"],
        rebuild_time_ms=integer_fields["rebuild_time_ms"],
        query_path_latency_delta_ms=integer_fields[
            "query_path_latency_delta_ms"
        ],
        resume_reused_units=integer_fields["resume_reused_units"],
        resume_eligible_units=integer_fields["resume_eligible_units"],
        truth_gate_bypass_count=integer_fields["truth_gate_bypass_count"],
        query_path_write_count=integer_fields["query_path_write_count"],
        direct_canon_write_count=integer_fields["direct_canon_write_count"],
        untrusted_instruction_execution_count=integer_fields[
            "untrusted_instruction_execution_count"
        ],
        warnings=warnings,
    )


def _read_json_object(path: str | Path) -> dict[str, object]:
    source = Path(path)
    try:
        text = source.read_text(encoding="utf-8")
        value = json.loads(text, object_pairs_hook=_reject_duplicate_pairs)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ReaderBenchmarkError(f"cannot read JSON from {source}: {exc}") from exc
    return _as_mapping(value, str(source))


def _reject_duplicate_pairs(
    pairs: list[tuple[str, object]],
) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ReaderBenchmarkError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _check_keys(
    value: Mapping[str, object],
    *,
    required: set[str],
    optional: set[str] | None = None,
) -> None:
    allowed = required | (optional or set())
    actual = set(value)
    missing = sorted(required - actual)
    unknown = sorted(actual - allowed)
    if missing or unknown:
        raise ReaderBenchmarkError(
            f"JSON object keys mismatch; missing={missing}, unknown={unknown}"
        )


def _as_mapping(value: object, field_name: str) -> dict[str, object]:
    if not isinstance(value, Mapping):
        raise ReaderBenchmarkError(f"{field_name} must be a JSON object")
    result: dict[str, object] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise ReaderBenchmarkError(
                f"{field_name} object keys must be strings"
            )
        result[key] = item
    return result


def _as_sequence(value: object, field_name: str) -> Sequence[object]:
    if isinstance(value, (str, bytes, bytearray)) or not isinstance(
        value,
        Sequence,
    ):
        raise ReaderBenchmarkError(f"{field_name} must be a JSON array")
    return cast(Sequence[object], value)


def _as_text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReaderBenchmarkError(f"{field_name} must be a non-empty string")
    return value


def _as_optional_text(value: object, field_name: str) -> str | None:
    if value is None:
        return None
    return _as_text(value, field_name)


def _as_int(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ReaderBenchmarkError(f"{field_name} must be an integer")
    return value


def _as_optional_int(value: object, field_name: str) -> int | None:
    if value is None:
        return None
    return _as_int(value, field_name)


def _as_float(value: object, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ReaderBenchmarkError(f"{field_name} must be a number")
    return float(value)


def _as_optional_float(value: object, field_name: str) -> float | None:
    if value is None:
        return None
    return _as_float(value, field_name)


def _to_jsonable(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _to_jsonable(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, Mapping):
        return {
            str(key): _to_jsonable(item)
            for key, item in value.items()
        }
    if isinstance(value, (tuple, list)):
        return [_to_jsonable(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise ReaderBenchmarkError(
        f"value of type {type(value).__name__} is not JSON serializable"
    )


def _require_text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReaderBenchmarkError(f"{field_name} must be a non-empty string")
    return value


def _nonnegative_int(value: int, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ReaderBenchmarkError(f"{field_name} must be an integer >= 0")
    return value


def _text_tuple(values: Iterable[str], field_name: str) -> tuple[str, ...]:
    result = tuple(values)
    for value in result:
        _require_text(value, field_name)
    return result


def _unique_sorted_text(
    values: Iterable[str],
    field_name: str,
) -> tuple[str, ...]:
    result = _text_tuple(values, field_name)
    if len(set(result)) != len(result):
        raise ReaderBenchmarkError(f"{field_name} values must be unique")
    ordered = tuple(sorted(result))
    if result != ordered:
        raise ReaderBenchmarkError(f"{field_name} values must be sorted")
    return result


def _require_sha256_hex(value: str, field_name: str) -> str:
    if len(value) != 64:
        raise ReaderBenchmarkError(f"{field_name} must be 64 hex characters")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ReaderBenchmarkError(
            f"{field_name} must be lowercase SHA-256 hex"
        ) from exc
    if value != value.lower():
        raise ReaderBenchmarkError(
            f"{field_name} must be lowercase SHA-256 hex"
        )
    return value


def _require_secret(secret: bytes) -> bytes:
    if not isinstance(secret, bytes) or len(secret) < 32:
        raise ReaderBenchmarkError(
            "HMAC secret must be bytes and at least 32 bytes long"
        )
    return secret


__all__ = [
    "READER_BENCHMARK_BUNDLE_SCHEMA_VERSION",
    "READER_BENCHMARK_INPUT_SCHEMA_VERSION",
    "READER_BENCHMARK_SIGNATURE_ALGORITHM",
    "READER_BENCHMARK_SIGNATURE_SCHEMA_VERSION",
    "READER_BENCHMARK_THRESHOLDS_SCHEMA_VERSION",
    "ReaderBenchmarkBundle",
    "ReaderBenchmarkError",
    "ReaderBenchmarkInput",
    "ReaderBenchmarkObservation",
    "ReaderBenchmarkRunner",
    "ReaderBenchmarkSignature",
    "ReaderBenchmarkSigner",
    "canonical_json_bytes",
    "load_benchmark_input",
    "load_evaluation_manifest",
    "load_promotion_thresholds",
    "write_canonical_json",
]
