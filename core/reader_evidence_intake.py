"""Operational evidence intake contracts for Reader Core PR-RDR-16.

This module binds a verified corpus package to blind independent annotation
assignments, adjudication packets, and an explicit benchmark-readiness report.
It does not create human labels, execute Reader Core, authorize promotion, or
write to query, memory, Canon, graph, policy, or tool paths.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import Enum
import re

from core.reader_core_contracts import stable_reader_core_id
from core.reader_corpus_adjudication import (
    CorpusPackageManifest,
    CorpusPackageVerificationReceipt,
    HumanLabelAdjudication,
    HumanLabelKind,
    HumanLabelSet,
    HumanLabelSetVerificationReceipt,
    LabelSetRole,
)

READER_EVIDENCE_INTAKE_SCHEMA_VERSION = "reader-core.evidence-intake.v1"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class ReaderEvidenceIntakeError(ValueError):
    """Raised when evidence-program identities or workflow invariants fail."""


class EvidenceCaseStage(str, Enum):
    AWAITING_PACKAGE_VERIFICATION = "awaiting_package_verification"
    AWAITING_ANNOTATION = "awaiting_annotation"
    AWAITING_ADJUDICATION = "awaiting_adjudication"
    AWAITING_LABEL_VERIFICATION = "awaiting_label_verification"
    READY_FOR_BENCHMARK = "ready_for_benchmark"


@dataclass(frozen=True, slots=True)
class ReaderAnnotationGuidelineSpec:
    guideline_version: str
    content_sha256: str
    required_label_kinds: tuple[HumanLabelKind, ...]
    min_independent_annotators: int = 2
    schema_version: str = READER_EVIDENCE_INTAKE_SCHEMA_VERSION
    guideline_id: str = ""

    def __post_init__(self) -> None:
        _require_text(self.guideline_version, "guideline_version")
        _require_sha256(self.content_sha256, "content_sha256")
        if self.schema_version != READER_EVIDENCE_INTAKE_SCHEMA_VERSION:
            raise ReaderEvidenceIntakeError(
                "unsupported evidence intake schema"
            )
        if (
            isinstance(self.min_independent_annotators, bool)
            or not isinstance(self.min_independent_annotators, int)
            or self.min_independent_annotators < 2
        ):
            raise ReaderEvidenceIntakeError(
                "min_independent_annotators must be an integer >= 2"
            )
        kinds = tuple(self.required_label_kinds)
        if not kinds or any(not isinstance(item, HumanLabelKind) for item in kinds):
            raise ReaderEvidenceIntakeError(
                "required_label_kinds require HumanLabelKind values"
            )
        ordered = tuple(sorted(kinds, key=lambda item: item.value))
        if kinds != ordered:
            raise ReaderEvidenceIntakeError(
                "required_label_kinds must use canonical ordering"
            )
        if len(set(kinds)) != len(kinds):
            raise ReaderEvidenceIntakeError(
                "required_label_kinds must be unique"
            )
        if HumanLabelKind.CLAIM not in kinds:
            raise ReaderEvidenceIntakeError(
                "annotation guidelines must require claim review"
            )
        expected = stable_reader_core_id(
            "reader-annotation-guideline-spec",
            self.identity_payload(include_id=False),
        )
        if self.guideline_id:
            if self.guideline_id != expected:
                raise ReaderEvidenceIntakeError(
                    "guideline_id does not match guideline content"
                )
        else:
            object.__setattr__(self, "guideline_id", expected)

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema_version": self.schema_version,
            "guideline_version": self.guideline_version,
            "content_sha256": self.content_sha256,
            "required_label_kinds": [
                item.value for item in self.required_label_kinds
            ],
            "min_independent_annotators": self.min_independent_annotators,
        }
        if include_id:
            payload["guideline_id"] = self.guideline_id
        return payload


@dataclass(frozen=True, slots=True)
class ReaderEvidenceCaseAssignment:
    case_id: str
    descriptor_id: str
    document_id: str
    source_revision: str
    annotator_ids: tuple[str, ...]
    adjudicator_id: str
    assignment_id: str = ""

    def __post_init__(self) -> None:
        for field_name in (
            "case_id",
            "descriptor_id",
            "document_id",
            "source_revision",
            "adjudicator_id",
        ):
            _require_text(getattr(self, field_name), field_name)
        annotators = _unique_sorted_text(self.annotator_ids, "annotator_id")
        if len(annotators) < 2:
            raise ReaderEvidenceIntakeError(
                "case assignments require at least two annotators"
            )
        if self.adjudicator_id in annotators:
            raise ReaderEvidenceIntakeError(
                "adjudicator must be independent from assigned annotators"
            )
        object.__setattr__(self, "annotator_ids", annotators)
        expected = stable_reader_core_id(
            "reader-evidence-case-assignment",
            self.identity_payload(include_id=False),
        )
        if self.assignment_id:
            if self.assignment_id != expected:
                raise ReaderEvidenceIntakeError(
                    "assignment_id does not match assignment content"
                )
        else:
            object.__setattr__(self, "assignment_id", expected)

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "case_id": self.case_id,
            "descriptor_id": self.descriptor_id,
            "document_id": self.document_id,
            "source_revision": self.source_revision,
            "annotator_ids": list(self.annotator_ids),
            "adjudicator_id": self.adjudicator_id,
        }
        if include_id:
            payload["assignment_id"] = self.assignment_id
        return payload


@dataclass(frozen=True, slots=True)
class ReaderEvidenceProgramPlan:
    package_id: str
    descriptor_ids: tuple[str, ...]
    guideline: ReaderAnnotationGuidelineSpec
    assignments: tuple[ReaderEvidenceCaseAssignment, ...]
    schema_version: str = READER_EVIDENCE_INTAKE_SCHEMA_VERSION
    plan_id: str = ""

    def __post_init__(self) -> None:
        _require_text(self.package_id, "package_id")
        if self.schema_version != READER_EVIDENCE_INTAKE_SCHEMA_VERSION:
            raise ReaderEvidenceIntakeError(
                "unsupported evidence intake schema"
            )
        if not isinstance(self.guideline, ReaderAnnotationGuidelineSpec):
            raise ReaderEvidenceIntakeError(
                "guideline must be a ReaderAnnotationGuidelineSpec"
            )
        descriptor_ids = _unique_sorted_text(
            self.descriptor_ids,
            "descriptor_id",
        )
        assignments = tuple(self.assignments)
        if not assignments or any(
            not isinstance(item, ReaderEvidenceCaseAssignment)
            for item in assignments
        ):
            raise ReaderEvidenceIntakeError(
                "assignments require ReaderEvidenceCaseAssignment values"
            )
        ordered = tuple(sorted(assignments, key=lambda item: item.case_id))
        if assignments != ordered:
            raise ReaderEvidenceIntakeError(
                "assignments must use canonical case ordering"
            )
        if len({item.case_id for item in assignments}) != len(assignments):
            raise ReaderEvidenceIntakeError("case IDs must be unique")
        assignment_descriptor_ids = tuple(
            sorted(item.descriptor_id for item in assignments)
        )
        if assignment_descriptor_ids != descriptor_ids:
            raise ReaderEvidenceIntakeError(
                "assignments must exactly cover descriptor_ids"
            )
        if len({item.document_id for item in assignments}) != len(assignments):
            raise ReaderEvidenceIntakeError("document IDs must be unique")
        for assignment in assignments:
            if (
                len(assignment.annotator_ids)
                < self.guideline.min_independent_annotators
            ):
                raise ReaderEvidenceIntakeError(
                    "assignment does not meet guideline annotator minimum"
                )
        object.__setattr__(self, "descriptor_ids", descriptor_ids)
        object.__setattr__(self, "assignments", assignments)
        expected = stable_reader_core_id(
            "reader-evidence-program-plan",
            self.identity_payload(include_id=False),
        )
        if self.plan_id:
            if self.plan_id != expected:
                raise ReaderEvidenceIntakeError(
                    "plan_id does not match evidence plan content"
                )
        else:
            object.__setattr__(self, "plan_id", expected)

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema_version": self.schema_version,
            "package_id": self.package_id,
            "descriptor_ids": list(self.descriptor_ids),
            "guideline_id": self.guideline.guideline_id,
            "assignment_ids": [item.assignment_id for item in self.assignments],
        }
        if include_id:
            payload["plan_id"] = self.plan_id
        return payload

    def assignment_for_case(self, case_id: str) -> ReaderEvidenceCaseAssignment:
        for assignment in self.assignments:
            if assignment.case_id == case_id:
                return assignment
        raise ReaderEvidenceIntakeError("case_id is not present in evidence plan")


@dataclass(frozen=True, slots=True)
class ReaderAnnotationPacket:
    plan_id: str
    assignment_id: str
    case_id: str
    descriptor_id: str
    document_id: str
    source_revision: str
    annotator_id: str
    guideline_id: str
    packet_id: str = ""

    def __post_init__(self) -> None:
        for field_name in (
            "plan_id",
            "assignment_id",
            "case_id",
            "descriptor_id",
            "document_id",
            "source_revision",
            "annotator_id",
            "guideline_id",
        ):
            _require_text(getattr(self, field_name), field_name)
        expected = stable_reader_core_id(
            "reader-annotation-packet",
            self.identity_payload(include_id=False),
        )
        if self.packet_id:
            if self.packet_id != expected:
                raise ReaderEvidenceIntakeError(
                    "packet_id does not match annotation packet content"
                )
        else:
            object.__setattr__(self, "packet_id", expected)

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "plan_id": self.plan_id,
            "assignment_id": self.assignment_id,
            "case_id": self.case_id,
            "descriptor_id": self.descriptor_id,
            "document_id": self.document_id,
            "source_revision": self.source_revision,
            "annotator_id": self.annotator_id,
            "guideline_id": self.guideline_id,
        }
        if include_id:
            payload["packet_id"] = self.packet_id
        return payload


@dataclass(frozen=True, slots=True)
class ReaderAdjudicationPacket:
    plan_id: str
    assignment_id: str
    case_id: str
    descriptor_id: str
    document_id: str
    source_revision: str
    adjudicator_id: str
    guideline_id: str
    source_label_set_ids: tuple[str, ...]
    packet_id: str = ""

    def __post_init__(self) -> None:
        for field_name in (
            "plan_id",
            "assignment_id",
            "case_id",
            "descriptor_id",
            "document_id",
            "source_revision",
            "adjudicator_id",
            "guideline_id",
        ):
            _require_text(getattr(self, field_name), field_name)
        label_set_ids = _unique_sorted_text(
            self.source_label_set_ids,
            "source_label_set_id",
        )
        if len(label_set_ids) < 2:
            raise ReaderEvidenceIntakeError(
                "adjudication packets require at least two source label sets"
            )
        object.__setattr__(self, "source_label_set_ids", label_set_ids)
        expected = stable_reader_core_id(
            "reader-adjudication-packet",
            self.identity_payload(include_id=False),
        )
        if self.packet_id:
            if self.packet_id != expected:
                raise ReaderEvidenceIntakeError(
                    "packet_id does not match adjudication packet content"
                )
        else:
            object.__setattr__(self, "packet_id", expected)

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "plan_id": self.plan_id,
            "assignment_id": self.assignment_id,
            "case_id": self.case_id,
            "descriptor_id": self.descriptor_id,
            "document_id": self.document_id,
            "source_revision": self.source_revision,
            "adjudicator_id": self.adjudicator_id,
            "guideline_id": self.guideline_id,
            "source_label_set_ids": list(self.source_label_set_ids),
        }
        if include_id:
            payload["packet_id"] = self.packet_id
        return payload


@dataclass(frozen=True, slots=True)
class ReaderEvidenceCaseReadiness:
    assignment_id: str
    case_id: str
    stage: EvidenceCaseStage
    received_annotator_ids: tuple[str, ...]
    missing_annotator_ids: tuple[str, ...]
    annotation_label_set_ids: tuple[str, ...]
    adjudication_id: str | None
    verified_label_set_ids: tuple[str, ...]
    blockers: tuple[str, ...]
    readiness_id: str = ""

    def __post_init__(self) -> None:
        _require_text(self.assignment_id, "assignment_id")
        _require_text(self.case_id, "case_id")
        if not isinstance(self.stage, EvidenceCaseStage):
            raise ReaderEvidenceIntakeError(
                "stage must be an EvidenceCaseStage"
            )
        received = _unique_sorted_text(
            self.received_annotator_ids,
            "received_annotator_id",
        )
        missing = _unique_sorted_text(
            self.missing_annotator_ids,
            "missing_annotator_id",
        )
        if set(received) & set(missing):
            raise ReaderEvidenceIntakeError(
                "received and missing annotators must be disjoint"
            )
        annotations = _unique_sorted_text(
            self.annotation_label_set_ids,
            "annotation_label_set_id",
        )
        verified = _unique_sorted_text(
            self.verified_label_set_ids,
            "verified_label_set_id",
        )
        blockers = _unique_sorted_text(self.blockers, "blocker")
        if self.adjudication_id is not None:
            _require_text(self.adjudication_id, "adjudication_id")
        if self.stage is EvidenceCaseStage.READY_FOR_BENCHMARK:
            if missing or blockers or self.adjudication_id is None:
                raise ReaderEvidenceIntakeError(
                    "ready cases require complete adjudication without blockers"
                )
        object.__setattr__(self, "received_annotator_ids", received)
        object.__setattr__(self, "missing_annotator_ids", missing)
        object.__setattr__(self, "annotation_label_set_ids", annotations)
        object.__setattr__(self, "verified_label_set_ids", verified)
        object.__setattr__(self, "blockers", blockers)
        expected = stable_reader_core_id(
            "reader-evidence-case-readiness",
            self.identity_payload(include_id=False),
        )
        if self.readiness_id:
            if self.readiness_id != expected:
                raise ReaderEvidenceIntakeError(
                    "readiness_id does not match readiness content"
                )
        else:
            object.__setattr__(self, "readiness_id", expected)

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "assignment_id": self.assignment_id,
            "case_id": self.case_id,
            "stage": self.stage.value,
            "received_annotator_ids": list(self.received_annotator_ids),
            "missing_annotator_ids": list(self.missing_annotator_ids),
            "annotation_label_set_ids": list(self.annotation_label_set_ids),
            "adjudication_id": self.adjudication_id,
            "verified_label_set_ids": list(self.verified_label_set_ids),
            "blockers": list(self.blockers),
        }
        if include_id:
            payload["readiness_id"] = self.readiness_id
        return payload


@dataclass(frozen=True, slots=True)
class ReaderEvidenceReadinessReport:
    plan_id: str
    package_id: str
    package_verification_receipt_id: str | None
    cases: tuple[ReaderEvidenceCaseReadiness, ...]
    report_id: str = ""

    def __post_init__(self) -> None:
        _require_text(self.plan_id, "plan_id")
        _require_text(self.package_id, "package_id")
        if self.package_verification_receipt_id is not None:
            _require_text(
                self.package_verification_receipt_id,
                "package_verification_receipt_id",
            )
        cases = tuple(self.cases)
        if not cases or any(
            not isinstance(item, ReaderEvidenceCaseReadiness) for item in cases
        ):
            raise ReaderEvidenceIntakeError(
                "cases require ReaderEvidenceCaseReadiness values"
            )
        ordered = tuple(sorted(cases, key=lambda item: item.case_id))
        if cases != ordered:
            raise ReaderEvidenceIntakeError(
                "readiness cases must use canonical ordering"
            )
        if len({item.case_id for item in cases}) != len(cases):
            raise ReaderEvidenceIntakeError(
                "readiness case IDs must be unique"
            )
        object.__setattr__(self, "cases", cases)
        expected = stable_reader_core_id(
            "reader-evidence-readiness-report",
            self.identity_payload(include_id=False),
        )
        if self.report_id:
            if self.report_id != expected:
                raise ReaderEvidenceIntakeError(
                    "report_id does not match readiness report content"
                )
        else:
            object.__setattr__(self, "report_id", expected)

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "plan_id": self.plan_id,
            "package_id": self.package_id,
            "package_verification_receipt_id": (
                self.package_verification_receipt_id
            ),
            "case_readiness_ids": [item.readiness_id for item in self.cases],
        }
        if include_id:
            payload["report_id"] = self.report_id
        return payload

    @property
    def is_ready_for_benchmark(self) -> bool:
        return all(
            item.stage is EvidenceCaseStage.READY_FOR_BENCHMARK
            for item in self.cases
        )

    @property
    def ready_case_ids(self) -> tuple[str, ...]:
        return tuple(
            item.case_id
            for item in self.cases
            if item.stage is EvidenceCaseStage.READY_FOR_BENCHMARK
        )


class ReaderEvidenceProgramPlanner:
    """Build blind assignments and packets from explicit operator mappings."""

    @staticmethod
    def create_plan(
        *,
        package: CorpusPackageManifest,
        guideline: ReaderAnnotationGuidelineSpec,
        annotator_ids_by_document: Mapping[str, Iterable[str]],
        adjudicator_ids_by_document: Mapping[str, str],
    ) -> ReaderEvidenceProgramPlan:
        if not isinstance(package, CorpusPackageManifest):
            raise ReaderEvidenceIntakeError(
                "package must be a CorpusPackageManifest"
            )
        if not isinstance(guideline, ReaderAnnotationGuidelineSpec):
            raise ReaderEvidenceIntakeError(
                "guideline must be a ReaderAnnotationGuidelineSpec"
            )
        document_ids = {item.document_id for item in package.documents}
        if set(annotator_ids_by_document) != document_ids:
            raise ReaderEvidenceIntakeError(
                "annotator mappings must exactly cover package documents"
            )
        if set(adjudicator_ids_by_document) != document_ids:
            raise ReaderEvidenceIntakeError(
                "adjudicator mappings must exactly cover package documents"
            )
        assignments: list[ReaderEvidenceCaseAssignment] = []
        for descriptor in package.documents:
            case_id = stable_reader_core_id(
                "reader-evidence-case",
                {
                    "package_id": package.package_id,
                    "descriptor_id": descriptor.descriptor_id,
                },
            )
            assignments.append(
                ReaderEvidenceCaseAssignment(
                    case_id=case_id,
                    descriptor_id=descriptor.descriptor_id,
                    document_id=descriptor.document_id,
                    source_revision=descriptor.source_revision,
                    annotator_ids=tuple(
                        annotator_ids_by_document[descriptor.document_id]
                    ),
                    adjudicator_id=adjudicator_ids_by_document[
                        descriptor.document_id
                    ],
                )
            )
        ordered = tuple(sorted(assignments, key=lambda item: item.case_id))
        return ReaderEvidenceProgramPlan(
            package_id=package.package_id,
            descriptor_ids=tuple(
                sorted(item.descriptor_id for item in package.documents)
            ),
            guideline=guideline,
            assignments=ordered,
        )

    @staticmethod
    def build_annotation_packets(
        plan: ReaderEvidenceProgramPlan,
    ) -> tuple[ReaderAnnotationPacket, ...]:
        if not isinstance(plan, ReaderEvidenceProgramPlan):
            raise ReaderEvidenceIntakeError(
                "plan must be a ReaderEvidenceProgramPlan"
            )
        packets = [
            ReaderAnnotationPacket(
                plan_id=plan.plan_id,
                assignment_id=assignment.assignment_id,
                case_id=assignment.case_id,
                descriptor_id=assignment.descriptor_id,
                document_id=assignment.document_id,
                source_revision=assignment.source_revision,
                annotator_id=annotator_id,
                guideline_id=plan.guideline.guideline_id,
            )
            for assignment in plan.assignments
            for annotator_id in assignment.annotator_ids
        ]
        return tuple(
            sorted(
                packets,
                key=lambda item: (item.case_id, item.annotator_id),
            )
        )

    @staticmethod
    def build_adjudication_packet(
        *,
        plan: ReaderEvidenceProgramPlan,
        case_id: str,
        annotation_sets: Iterable[HumanLabelSet],
    ) -> ReaderAdjudicationPacket:
        assignment = plan.assignment_for_case(case_id)
        sources = _validate_annotation_sets(
            assignment=assignment,
            guideline=plan.guideline,
            annotation_sets=annotation_sets,
            require_complete=True,
        )
        return ReaderAdjudicationPacket(
            plan_id=plan.plan_id,
            assignment_id=assignment.assignment_id,
            case_id=assignment.case_id,
            descriptor_id=assignment.descriptor_id,
            document_id=assignment.document_id,
            source_revision=assignment.source_revision,
            adjudicator_id=assignment.adjudicator_id,
            guideline_id=plan.guideline.guideline_id,
            source_label_set_ids=tuple(
                sorted(item.label_set_id for item in sources)
            ),
        )


class ReaderEvidenceReadinessEvaluator:
    """Evaluate evidence completeness without executing or promoting anything."""

    def evaluate(
        self,
        *,
        plan: ReaderEvidenceProgramPlan,
        package: CorpusPackageManifest,
        package_verification: CorpusPackageVerificationReceipt | None = None,
        annotation_sets: Iterable[HumanLabelSet] = (),
        adjudications: Iterable[HumanLabelAdjudication] = (),
        label_verifications: Iterable[HumanLabelSetVerificationReceipt] = (),
    ) -> ReaderEvidenceReadinessReport:
        _validate_plan_package(plan, package)
        package_is_verified = _validate_package_verification(
            package,
            package_verification,
        )
        assignments_by_descriptor = {
            item.descriptor_id: item for item in plan.assignments
        }
        annotations = tuple(annotation_sets)
        if any(not isinstance(item, HumanLabelSet) for item in annotations):
            raise ReaderEvidenceIntakeError(
                "annotation_sets require HumanLabelSet values"
            )
        annotation_by_descriptor: dict[str, dict[str, HumanLabelSet]] = {
            descriptor_id: {} for descriptor_id in plan.descriptor_ids
        }
        for label_set in annotations:
            if label_set.role is not LabelSetRole.ANNOTATOR:
                raise ReaderEvidenceIntakeError(
                    "annotation_sets must have annotator role"
                )
            assignment = assignments_by_descriptor.get(
                label_set.document_descriptor_id
            )
            if assignment is None:
                raise ReaderEvidenceIntakeError(
                    "annotation set belongs to a foreign descriptor"
                )
            _validate_label_set_identity(
                assignment,
                plan.guideline,
                label_set,
            )
            if label_set.annotator_id not in assignment.annotator_ids:
                raise ReaderEvidenceIntakeError(
                    "annotation set belongs to an unassigned annotator"
                )
            previous = annotation_by_descriptor[assignment.descriptor_id].get(
                label_set.annotator_id
            )
            if previous is not None and previous.label_set_id != label_set.label_set_id:
                raise ReaderEvidenceIntakeError(
                    "an annotator may submit only one label set per case"
                )
            annotation_by_descriptor[assignment.descriptor_id][
                label_set.annotator_id
            ] = label_set

        adjudication_by_descriptor: dict[str, HumanLabelAdjudication] = {}
        for adjudication in tuple(adjudications):
            if not isinstance(adjudication, HumanLabelAdjudication):
                raise ReaderEvidenceIntakeError(
                    "adjudications require HumanLabelAdjudication values"
                )
            descriptor_id = (
                adjudication.adjudicated_label_set.document_descriptor_id
            )
            assignment = assignments_by_descriptor.get(descriptor_id)
            if assignment is None:
                raise ReaderEvidenceIntakeError(
                    "adjudication belongs to a foreign descriptor"
                )
            if descriptor_id in adjudication_by_descriptor:
                raise ReaderEvidenceIntakeError(
                    "only one adjudication is allowed per evidence case"
                )
            if adjudication.adjudicator_id != assignment.adjudicator_id:
                raise ReaderEvidenceIntakeError(
                    "adjudication uses the wrong assigned adjudicator"
                )
            source_annotators = {
                item.annotator_id for item in adjudication.source_label_sets
            }
            if source_annotators != set(assignment.annotator_ids):
                raise ReaderEvidenceIntakeError(
                    "adjudication must use exactly the assigned annotators"
                )
            for source in adjudication.source_label_sets:
                _validate_label_set_identity(
                    assignment,
                    plan.guideline,
                    source,
                )
                previous = annotation_by_descriptor[descriptor_id].get(
                    source.annotator_id
                )
                if previous is not None and previous.label_set_id != source.label_set_id:
                    raise ReaderEvidenceIntakeError(
                        "adjudication source conflicts with submitted annotation"
                    )
                annotation_by_descriptor[descriptor_id][
                    source.annotator_id
                ] = source
            _validate_label_set_identity(
                assignment,
                plan.guideline,
                adjudication.adjudicated_label_set,
            )
            adjudication_by_descriptor[descriptor_id] = adjudication

        for assignment in plan.assignments:
            versions = {
                item.label_version
                for item in annotation_by_descriptor[
                    assignment.descriptor_id
                ].values()
            }
            if len(versions) > 1:
                raise ReaderEvidenceIntakeError(
                    "annotation label versions must match within a case"
                )

        known_label_sets: dict[str, HumanLabelSet] = {}
        for per_case in annotation_by_descriptor.values():
            for label_set in per_case.values():
                known_label_sets[label_set.label_set_id] = label_set
        for adjudication in adjudication_by_descriptor.values():
            final = adjudication.adjudicated_label_set
            known_label_sets[final.label_set_id] = final

        verification_by_label_set: dict[
            str,
            HumanLabelSetVerificationReceipt,
        ] = {}
        for receipt in tuple(label_verifications):
            if not isinstance(receipt, HumanLabelSetVerificationReceipt):
                raise ReaderEvidenceIntakeError(
                    "label_verifications require verification receipts"
                )
            verified_label_set = known_label_sets.get(receipt.label_set_id)
            if verified_label_set is None:
                raise ReaderEvidenceIntakeError(
                    "label verification references an unknown label set"
                )
            if (
                receipt.descriptor_id
                != verified_label_set.document_descriptor_id
            ):
                raise ReaderEvidenceIntakeError(
                    "label verification descriptor does not match label set"
                )
            previous_receipt = verification_by_label_set.get(receipt.label_set_id)
            if (
                previous_receipt is not None
                and previous_receipt.receipt_id != receipt.receipt_id
            ):
                raise ReaderEvidenceIntakeError(
                    "label set has conflicting verification receipts"
                )
            verification_by_label_set[receipt.label_set_id] = receipt

        case_readiness: list[ReaderEvidenceCaseReadiness] = []
        for assignment in plan.assignments:
            received_by_annotator = annotation_by_descriptor[
                assignment.descriptor_id
            ]
            received_ids = tuple(sorted(received_by_annotator))
            missing_ids = tuple(
                sorted(set(assignment.annotator_ids) - set(received_ids))
            )
            annotation_ids = tuple(
                sorted(
                    item.label_set_id for item in received_by_annotator.values()
                )
            )
            case_adjudication = adjudication_by_descriptor.get(
                assignment.descriptor_id
            )
            required_verification_ids = set(annotation_ids)
            if case_adjudication is not None:
                required_verification_ids.add(
                    case_adjudication.adjudicated_label_set.label_set_id
                )
            verified_ids = tuple(
                sorted(
                    required_verification_ids
                    & set(verification_by_label_set)
                )
            )
            blockers: list[str] = []
            if not package_is_verified:
                blockers.append("missing_package_verification")
            blockers.extend(
                f"missing_annotation:{annotator_id}"
                for annotator_id in missing_ids
            )
            if not missing_ids and case_adjudication is None:
                blockers.append("missing_adjudication")
            missing_verification_ids = tuple(
                sorted(required_verification_ids - set(verified_ids))
            )
            blockers.extend(
                f"missing_label_verification:{label_set_id}"
                for label_set_id in missing_verification_ids
            )
            if not package_is_verified:
                stage = EvidenceCaseStage.AWAITING_PACKAGE_VERIFICATION
            elif missing_ids:
                stage = EvidenceCaseStage.AWAITING_ANNOTATION
            elif case_adjudication is None:
                stage = EvidenceCaseStage.AWAITING_ADJUDICATION
            elif missing_verification_ids:
                stage = EvidenceCaseStage.AWAITING_LABEL_VERIFICATION
            else:
                stage = EvidenceCaseStage.READY_FOR_BENCHMARK
            case_readiness.append(
                ReaderEvidenceCaseReadiness(
                    assignment_id=assignment.assignment_id,
                    case_id=assignment.case_id,
                    stage=stage,
                    received_annotator_ids=received_ids,
                    missing_annotator_ids=missing_ids,
                    annotation_label_set_ids=annotation_ids,
                    adjudication_id=(
                        None
                        if case_adjudication is None
                        else case_adjudication.adjudication_id
                    ),
                    verified_label_set_ids=verified_ids,
                    blockers=tuple(sorted(blockers)),
                )
            )
        return ReaderEvidenceReadinessReport(
            plan_id=plan.plan_id,
            package_id=package.package_id,
            package_verification_receipt_id=(
                None
                if package_verification is None
                else package_verification.receipt_id
            ),
            cases=tuple(sorted(case_readiness, key=lambda item: item.case_id)),
        )


def _validate_plan_package(
    plan: ReaderEvidenceProgramPlan,
    package: CorpusPackageManifest,
) -> None:
    if not isinstance(plan, ReaderEvidenceProgramPlan):
        raise ReaderEvidenceIntakeError(
            "plan must be a ReaderEvidenceProgramPlan"
        )
    if not isinstance(package, CorpusPackageManifest):
        raise ReaderEvidenceIntakeError(
            "package must be a CorpusPackageManifest"
        )
    if plan.package_id != package.package_id:
        raise ReaderEvidenceIntakeError(
            "plan belongs to a different corpus package"
        )
    descriptors_by_id = {
        item.descriptor_id: item for item in package.documents
    }
    if set(descriptors_by_id) != set(plan.descriptor_ids):
        raise ReaderEvidenceIntakeError(
            "plan must exactly cover package descriptors"
        )
    for assignment in plan.assignments:
        descriptor = descriptors_by_id[assignment.descriptor_id]
        if (
            assignment.document_id != descriptor.document_id
            or assignment.source_revision != descriptor.source_revision
        ):
            raise ReaderEvidenceIntakeError(
                "assignment identity does not match package descriptor"
            )


def _validate_package_verification(
    package: CorpusPackageManifest,
    receipt: CorpusPackageVerificationReceipt | None,
) -> bool:
    if receipt is None:
        return False
    if not isinstance(receipt, CorpusPackageVerificationReceipt):
        raise ReaderEvidenceIntakeError(
            "package_verification must be a verification receipt"
        )
    if receipt.package_id != package.package_id:
        raise ReaderEvidenceIntakeError(
            "package verification belongs to a different package"
        )
    entries_by_descriptor = {item.descriptor_id: item for item in receipt.entries}
    descriptors_by_id = {
        item.descriptor_id: item for item in package.documents
    }
    if set(entries_by_descriptor) != set(descriptors_by_id):
        raise ReaderEvidenceIntakeError(
            "package verification must exactly cover package descriptors"
        )
    for descriptor_id, descriptor in descriptors_by_id.items():
        entry = entries_by_descriptor[descriptor_id]
        if (
            entry.document_id != descriptor.document_id
            or entry.content_sha256 != descriptor.content_sha256
            or entry.byte_size != descriptor.byte_size
            or entry.char_count != descriptor.char_count
        ):
            raise ReaderEvidenceIntakeError(
                "package verification entry does not match descriptor"
            )
    return True


def _validate_annotation_sets(
    *,
    assignment: ReaderEvidenceCaseAssignment,
    guideline: ReaderAnnotationGuidelineSpec,
    annotation_sets: Iterable[HumanLabelSet],
    require_complete: bool,
) -> tuple[HumanLabelSet, ...]:
    items = tuple(annotation_sets)
    if any(not isinstance(item, HumanLabelSet) for item in items):
        raise ReaderEvidenceIntakeError(
            "annotation sets require HumanLabelSet values"
        )
    by_annotator: dict[str, HumanLabelSet] = {}
    for label_set in items:
        if label_set.role is not LabelSetRole.ANNOTATOR:
            raise ReaderEvidenceIntakeError(
                "annotation sets must have annotator role"
            )
        _validate_label_set_identity(assignment, guideline, label_set)
        if label_set.annotator_id not in assignment.annotator_ids:
            raise ReaderEvidenceIntakeError(
                "annotation set belongs to an unassigned annotator"
            )
        if label_set.annotator_id in by_annotator:
            raise ReaderEvidenceIntakeError(
                "annotator label sets must be unique per case"
            )
        by_annotator[label_set.annotator_id] = label_set
    if require_complete and set(by_annotator) != set(assignment.annotator_ids):
        raise ReaderEvidenceIntakeError(
            "adjudication packet requires all assigned annotation sets"
        )
    versions = {item.label_version for item in by_annotator.values()}
    if len(versions) > 1:
        raise ReaderEvidenceIntakeError(
            "annotation label versions must match within a case"
        )
    return tuple(
        sorted(by_annotator.values(), key=lambda item: item.label_set_id)
    )


def _validate_label_set_identity(
    assignment: ReaderEvidenceCaseAssignment,
    guideline: ReaderAnnotationGuidelineSpec,
    label_set: HumanLabelSet,
) -> None:
    if (
        label_set.document_descriptor_id != assignment.descriptor_id
        or label_set.document_id != assignment.document_id
        or label_set.source_revision != assignment.source_revision
    ):
        raise ReaderEvidenceIntakeError(
            "label set identity does not match evidence assignment"
        )
    if label_set.guideline_version != guideline.guideline_version:
        raise ReaderEvidenceIntakeError(
            "label set guideline version does not match evidence plan"
        )


def _require_text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReaderEvidenceIntakeError(
            f"{field_name} must be non-empty text"
        )
    return value


def _require_sha256(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
        raise ReaderEvidenceIntakeError(
            f"{field_name} must be a lowercase SHA-256 digest"
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
        raise ReaderEvidenceIntakeError(
            f"{field_name} values must be unique"
        )
    return tuple(sorted(items))
