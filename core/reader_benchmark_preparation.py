"""Prepare benchmark manifests from verified human evidence for PR-RDR-19.

The bridge converts only fully ready RDR-18 evidence into RDR-14 local benchmark
cases, RDR-09 evaluation manifests, and an RDR-13 batch plan/checkpoint. It does
not execute Reader Core, select a provider, schedule work, or authorize promotion.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from core.reader_benchmark_batch import (
    ReaderBenchmarkBatchCheckpoint,
    ReaderBenchmarkBatchPlan,
    ReaderBenchmarkBatchPlanner,
)
from core.reader_benchmark_executor import ReaderLocalBenchmarkCase
from core.reader_core_contracts import RelationKind, stable_reader_core_id
from core.reader_evaluation import (
    EvaluationCorpusKind,
    EvaluationCorpusManifest,
    ReaderEvaluationCaseManifest,
)
from core.reader_evidence_import import (
    ReaderAdjudicationSubmission,
    ReaderEvidenceImportBundle,
)
from core.reader_evidence_pack import ReaderEvidencePack

READER_BENCHMARK_PREPARATION_SCHEMA_VERSION = (
    "reader-core.benchmark-preparation.v1"
)


class ReaderBenchmarkPreparationError(ValueError):
    """Raised when evidence cannot safely become benchmark input."""


@dataclass(frozen=True, slots=True)
class ReaderPreparedBenchmarkCase:
    evidence_case_id: str
    benchmark_case: ReaderLocalBenchmarkCase
    evaluation_manifest: ReaderEvaluationCaseManifest
    prepared_case_id: str = ""

    def __post_init__(self) -> None:
        _require_text(self.evidence_case_id, "evidence_case_id")
        if not isinstance(self.benchmark_case, ReaderLocalBenchmarkCase):
            raise ReaderBenchmarkPreparationError(
                "benchmark_case must be a ReaderLocalBenchmarkCase"
            )
        if not isinstance(
            self.evaluation_manifest,
            ReaderEvaluationCaseManifest,
        ):
            raise ReaderBenchmarkPreparationError(
                "evaluation_manifest must be a ReaderEvaluationCaseManifest"
            )
        if self.benchmark_case.case_id != self.evaluation_manifest.case_id:
            raise ReaderBenchmarkPreparationError(
                "benchmark case and evaluation manifest case IDs must match"
            )
        expected = stable_reader_core_id(
            "reader-prepared-benchmark-case",
            self.identity_payload(include_id=False),
        )
        if self.prepared_case_id:
            if self.prepared_case_id != expected:
                raise ReaderBenchmarkPreparationError(
                    "prepared_case_id does not match prepared case content"
                )
        else:
            object.__setattr__(self, "prepared_case_id", expected)

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "evidence_case_id": self.evidence_case_id,
            "benchmark_case_spec_id": self.benchmark_case.case_spec_id,
            "evaluation_manifest_id": self.evaluation_manifest.manifest_id,
        }
        if include_id:
            payload["prepared_case_id"] = self.prepared_case_id
        return payload


@dataclass(frozen=True, slots=True)
class ReaderBenchmarkPreparationBundle:
    evidence_pack_id: str
    evidence_import_bundle_id: str
    evaluation_manifest: EvaluationCorpusManifest
    prepared_cases: tuple[ReaderPreparedBenchmarkCase, ...]
    batch_plan: ReaderBenchmarkBatchPlan
    initial_checkpoint: ReaderBenchmarkBatchCheckpoint
    schema_version: str = READER_BENCHMARK_PREPARATION_SCHEMA_VERSION
    preparation_id: str = ""

    def __post_init__(self) -> None:
        _require_text(self.evidence_pack_id, "evidence_pack_id")
        _require_text(
            self.evidence_import_bundle_id,
            "evidence_import_bundle_id",
        )
        if self.schema_version != READER_BENCHMARK_PREPARATION_SCHEMA_VERSION:
            raise ReaderBenchmarkPreparationError(
                "unsupported benchmark preparation schema"
            )
        if not isinstance(self.evaluation_manifest, EvaluationCorpusManifest):
            raise ReaderBenchmarkPreparationError(
                "evaluation_manifest must be an EvaluationCorpusManifest"
            )
        cases = tuple(self.prepared_cases)
        if not cases or any(
            not isinstance(item, ReaderPreparedBenchmarkCase) for item in cases
        ):
            raise ReaderBenchmarkPreparationError(
                "prepared_cases require ReaderPreparedBenchmarkCase values"
            )
        ordered = tuple(
            sorted(cases, key=lambda item: item.benchmark_case.case_id)
        )
        if cases != ordered:
            raise ReaderBenchmarkPreparationError(
                "prepared_cases must use canonical benchmark case ordering"
            )
        if len({item.evidence_case_id for item in cases}) != len(cases):
            raise ReaderBenchmarkPreparationError(
                "evidence case IDs must be unique"
            )
        benchmark_case_ids = tuple(
            item.benchmark_case.case_id for item in cases
        )
        if len(set(benchmark_case_ids)) != len(benchmark_case_ids):
            raise ReaderBenchmarkPreparationError(
                "benchmark case IDs must be unique"
            )
        manifest_case_ids = tuple(
            item.case_id for item in self.evaluation_manifest.cases
        )
        if benchmark_case_ids != manifest_case_ids:
            raise ReaderBenchmarkPreparationError(
                "prepared cases must exactly match evaluation manifest cases"
            )
        if not isinstance(self.batch_plan, ReaderBenchmarkBatchPlan):
            raise ReaderBenchmarkPreparationError(
                "batch_plan must be a ReaderBenchmarkBatchPlan"
            )
        if self.batch_plan.corpus_id != self.evaluation_manifest.corpus_id:
            raise ReaderBenchmarkPreparationError(
                "batch plan corpus must match evaluation manifest"
            )
        if self.batch_plan.case_ids != benchmark_case_ids:
            raise ReaderBenchmarkPreparationError(
                "batch plan must exactly cover prepared benchmark cases"
            )
        if not isinstance(
            self.initial_checkpoint,
            ReaderBenchmarkBatchCheckpoint,
        ):
            raise ReaderBenchmarkPreparationError(
                "initial_checkpoint must be a ReaderBenchmarkBatchCheckpoint"
            )
        if self.initial_checkpoint.plan != self.batch_plan:
            raise ReaderBenchmarkPreparationError(
                "initial checkpoint must use the prepared batch plan"
            )
        if self.initial_checkpoint.receipts:
            raise ReaderBenchmarkPreparationError(
                "initial checkpoint must not contain receipts"
            )
        object.__setattr__(self, "prepared_cases", cases)
        expected = stable_reader_core_id(
            "reader-benchmark-preparation-bundle",
            self.identity_payload(include_id=False),
        )
        if self.preparation_id:
            if self.preparation_id != expected:
                raise ReaderBenchmarkPreparationError(
                    "preparation_id does not match preparation content"
                )
        else:
            object.__setattr__(self, "preparation_id", expected)

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema_version": self.schema_version,
            "evidence_pack_id": self.evidence_pack_id,
            "evidence_import_bundle_id": self.evidence_import_bundle_id,
            "evaluation_corpus_id": self.evaluation_manifest.corpus_id,
            "prepared_case_ids": [
                item.prepared_case_id for item in self.prepared_cases
            ],
            "batch_plan_id": self.batch_plan.plan_id,
            "initial_checkpoint_id": self.initial_checkpoint.checkpoint_id,
        }
        if include_id:
            payload["preparation_id"] = self.preparation_id
        return payload

    @property
    def local_cases(self) -> tuple[ReaderLocalBenchmarkCase, ...]:
        return tuple(item.benchmark_case for item in self.prepared_cases)


class ReaderBenchmarkPreparationBuilder:
    """Convert complete human evidence into non-executed benchmark inputs."""

    def prepare(
        self,
        *,
        pack: ReaderEvidencePack,
        imported: ReaderEvidenceImportBundle,
        environment_id: str,
        thresholds_id: str,
        max_attempts_per_case: int = 1,
        extra_tags: Iterable[str] = (),
    ) -> ReaderBenchmarkPreparationBundle:
        if not isinstance(pack, ReaderEvidencePack):
            raise ReaderBenchmarkPreparationError(
                "pack must be a ReaderEvidencePack"
            )
        if not isinstance(imported, ReaderEvidenceImportBundle):
            raise ReaderBenchmarkPreparationError(
                "imported must be a ReaderEvidenceImportBundle"
            )
        _require_text(environment_id, "environment_id")
        _require_text(thresholds_id, "thresholds_id")
        if imported.evidence_pack_id != pack.pack_id:
            raise ReaderBenchmarkPreparationError(
                "import bundle belongs to a different evidence pack"
            )
        if imported.readiness.plan_id != pack.plan.plan_id:
            raise ReaderBenchmarkPreparationError(
                "readiness belongs to a different evidence plan"
            )
        if not imported.readiness.is_ready_for_benchmark:
            raise ReaderBenchmarkPreparationError(
                "all evidence cases must be ready for benchmark"
            )
        assignments_by_case = {
            item.case_id: item for item in pack.plan.assignments
        }
        adjudications_by_case = {
            item.case_id: item for item in imported.adjudication_submissions
        }
        if set(adjudications_by_case) != set(assignments_by_case):
            raise ReaderBenchmarkPreparationError(
                "adjudications must exactly cover evidence assignments"
            )
        descriptors_by_id = {
            item.descriptor_id: item for item in pack.package.documents
        }
        common_tags = _unique_sorted_text(
            (*pack.package.tags, *tuple(extra_tags), "human-adjudicated"),
            "tag",
        )
        prepared: list[ReaderPreparedBenchmarkCase] = []
        for evidence_case_id in sorted(assignments_by_case):
            assignment = assignments_by_case[evidence_case_id]
            adjudication = adjudications_by_case[evidence_case_id]
            descriptor = descriptors_by_id.get(assignment.descriptor_id)
            if descriptor is None:
                raise ReaderBenchmarkPreparationError(
                    "assignment references a missing corpus descriptor"
                )
            gold = adjudication.adjudicated_label_set
            if (
                gold.document_descriptor_id != descriptor.descriptor_id
                or gold.document_id != descriptor.document_id
                or gold.source_revision != descriptor.source_revision
            ):
                raise ReaderBenchmarkPreparationError(
                    "adjudicated gold does not match corpus descriptor"
                )
            benchmark_case_id = gold.document_id
            local_case = ReaderLocalBenchmarkCase(
                case_id=benchmark_case_id,
                descriptor=descriptor,
                gold=gold,
            )
            case_manifest = ReaderEvaluationCaseManifest(
                case_id=benchmark_case_id,
                corpus_kind=EvaluationCorpusKind.HUMAN_LABELLED,
                label_version=gold.label_version,
                expected_claim_count=len(gold.claims),
                expected_source_span_count=sum(
                    len(item.source_spans) for item in gold.claims
                ),
                expected_exception_count=len(gold.exceptions),
                expected_relation_count=len(gold.relations),
                expected_contradiction_count=sum(
                    item.relation_kind is RelationKind.CONTRADICTS
                    for item in gold.relations
                ),
                expected_qualifier_count=len(gold.qualifiers),
                tags=common_tags,
            )
            prepared.append(
                ReaderPreparedBenchmarkCase(
                    evidence_case_id=evidence_case_id,
                    benchmark_case=local_case,
                    evaluation_manifest=case_manifest,
                )
            )
        prepared_cases = tuple(
            sorted(prepared, key=lambda item: item.benchmark_case.case_id)
        )
        evaluation_manifest = EvaluationCorpusManifest(
            corpus_name=pack.package.corpus_name,
            corpus_version=pack.package.corpus_version,
            cases=tuple(item.evaluation_manifest for item in prepared_cases),
        )
        batch_plan = ReaderBenchmarkBatchPlanner.create_plan(
            corpus_id=evaluation_manifest.corpus_id,
            environment_id=environment_id,
            threshold_policy_id=thresholds_id,
            case_ids=tuple(
                item.benchmark_case.case_id for item in prepared_cases
            ),
            max_attempts_per_case=max_attempts_per_case,
        )
        checkpoint = ReaderBenchmarkBatchPlanner.empty_checkpoint(batch_plan)
        return ReaderBenchmarkPreparationBundle(
            evidence_pack_id=pack.pack_id,
            evidence_import_bundle_id=imported.bundle_id,
            evaluation_manifest=evaluation_manifest,
            prepared_cases=prepared_cases,
            batch_plan=batch_plan,
            initial_checkpoint=checkpoint,
        )


def _require_text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReaderBenchmarkPreparationError(
            f"{field_name} must be non-empty text"
        )
    return value


def _unique_sorted_text(
    values: Iterable[str],
    field_name: str,
) -> tuple[str, ...]:
    items = tuple(values)
    for item in items:
        _require_text(item, field_name)
    if len(set(items)) != len(items):
        raise ReaderBenchmarkPreparationError(
            f"{field_name} values must be unique"
        )
    return tuple(sorted(items))
