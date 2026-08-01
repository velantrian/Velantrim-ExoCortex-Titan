"""Strict local import of returned human evidence for Reader Core PR-RDR-18.

The importer binds returned annotation and adjudication JSON to an existing
RDR-17 evidence pack, verifies every label span against local source bytes, and
produces an RDR-16 readiness report. It does not generate labels, execute Reader
Core, upload data, or authorize benchmark promotion or live integration.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path
from typing import Any, TypeVar, cast

from core.critical_exceptions import ExceptionCategory
from core.knowledge_capsule import ClaimModality, SourceSpan
from core.reader_core_contracts import RelationKind, stable_reader_core_id
from core.reader_corpus_adjudication import (
    ADJUDICATION_SCHEMA_VERSION,
    AdjudicationResolution,
    CorpusDocumentDescriptor,
    HumanClaimLabel,
    HumanExceptionLabel,
    HumanLabelAdjudication,
    HumanLabelKind,
    HumanLabelSet,
    HumanLabelSetVerificationReceipt,
    HumanQualifierLabel,
    HumanRelationLabel,
    LabelSetRole,
    QualifierKind,
    ReaderCorpusError,
)
from core.reader_evidence_intake import (
    ReaderAnnotationPacket,
    ReaderEvidenceReadinessEvaluator,
    ReaderEvidenceReadinessReport,
)
from core.reader_evidence_pack import ReaderEvidencePack

READER_ANNOTATION_SUBMISSION_SCHEMA_VERSION = (
    "reader-core.annotation-submission.v1"
)
READER_ADJUDICATION_SUBMISSION_SCHEMA_VERSION = (
    "reader-core.adjudication-submission.v1"
)
READER_EVIDENCE_IMPORT_BUNDLE_SCHEMA_VERSION = (
    "reader-core.evidence-import-bundle.v1"
)

E = TypeVar("E", bound=Enum)
T = TypeVar("T")


class ReaderEvidenceImportError(ValueError):
    """Raised when returned evidence is malformed, stale, or foreign."""


@dataclass(frozen=True, slots=True)
class ReaderAnnotationSubmission:
    packet_id: str
    label_set: HumanLabelSet
    schema_version: str = READER_ANNOTATION_SUBMISSION_SCHEMA_VERSION
    submission_id: str = ""

    def __post_init__(self) -> None:
        _require_text(self.packet_id, "packet_id")
        if self.schema_version != READER_ANNOTATION_SUBMISSION_SCHEMA_VERSION:
            raise ReaderEvidenceImportError(
                "unsupported annotation submission schema"
            )
        if not isinstance(self.label_set, HumanLabelSet):
            raise ReaderEvidenceImportError(
                "label_set must be a HumanLabelSet"
            )
        if self.label_set.role is not LabelSetRole.ANNOTATOR:
            raise ReaderEvidenceImportError(
                "annotation submission label_set must have annotator role"
            )
        expected = stable_reader_core_id(
            "reader-annotation-submission",
            self.identity_payload(include_id=False),
        )
        if self.submission_id:
            if self.submission_id != expected:
                raise ReaderEvidenceImportError(
                    "submission_id does not match annotation submission content"
                )
        else:
            object.__setattr__(self, "submission_id", expected)

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema_version": self.schema_version,
            "packet_id": self.packet_id,
            "label_set_id": self.label_set.label_set_id,
        }
        if include_id:
            payload["submission_id"] = self.submission_id
        return payload


@dataclass(frozen=True, slots=True)
class ReaderAdjudicationSubmission:
    case_id: str
    adjudicator_id: str
    source_label_set_ids: tuple[str, ...]
    adjudicated_label_set: HumanLabelSet
    resolutions: tuple[AdjudicationResolution, ...]
    schema_version: str = READER_ADJUDICATION_SUBMISSION_SCHEMA_VERSION
    adjudication_id: str = ""
    submission_id: str = ""

    def __post_init__(self) -> None:
        _require_text(self.case_id, "case_id")
        _require_text(self.adjudicator_id, "adjudicator_id")
        if self.schema_version != READER_ADJUDICATION_SUBMISSION_SCHEMA_VERSION:
            raise ReaderEvidenceImportError(
                "unsupported adjudication submission schema"
            )
        source_ids = _unique_sorted_text(
            self.source_label_set_ids,
            "source_label_set_id",
        )
        if len(source_ids) < 2:
            raise ReaderEvidenceImportError(
                "adjudication submission requires at least two source label sets"
            )
        if not isinstance(self.adjudicated_label_set, HumanLabelSet):
            raise ReaderEvidenceImportError(
                "adjudicated_label_set must be a HumanLabelSet"
            )
        if self.adjudicated_label_set.role is not LabelSetRole.ADJUDICATED:
            raise ReaderEvidenceImportError(
                "adjudicated label set must have adjudicated role"
            )
        if self.adjudicated_label_set.annotator_id != self.adjudicator_id:
            raise ReaderEvidenceImportError(
                "adjudicated label-set annotator_id must equal adjudicator_id"
            )
        resolutions = tuple(self.resolutions)
        if any(
            not isinstance(item, AdjudicationResolution) for item in resolutions
        ):
            raise ReaderEvidenceImportError(
                "resolutions require AdjudicationResolution values"
            )
        resolutions = tuple(
            sorted(resolutions, key=lambda item: item.resolution_id)
        )
        if len({item.resolution_id for item in resolutions}) != len(resolutions):
            raise ReaderEvidenceImportError("resolution IDs must be unique")
        object.__setattr__(self, "source_label_set_ids", source_ids)
        object.__setattr__(self, "resolutions", resolutions)
        expected = stable_reader_core_id(
            "reader-adjudication-submission",
            self.identity_payload(include_ids=False),
        )
        if self.submission_id:
            if self.submission_id != expected:
                raise ReaderEvidenceImportError(
                    "submission_id does not match adjudication submission content"
                )
        else:
            object.__setattr__(self, "submission_id", expected)

    def identity_payload(self, *, include_ids: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema_version": self.schema_version,
            "case_id": self.case_id,
            "adjudicator_id": self.adjudicator_id,
            "source_label_set_ids": list(self.source_label_set_ids),
            "adjudicated_label_set_id": (
                self.adjudicated_label_set.label_set_id
            ),
            "resolution_ids": [item.resolution_id for item in self.resolutions],
        }
        if include_ids:
            payload["adjudication_id"] = self.adjudication_id
            payload["submission_id"] = self.submission_id
        elif self.adjudication_id:
            payload["adjudication_id"] = self.adjudication_id
        return payload


@dataclass(frozen=True, slots=True)
class ReaderEvidenceImportBundle:
    evidence_pack_id: str
    annotation_submissions: tuple[ReaderAnnotationSubmission, ...]
    adjudication_submissions: tuple[ReaderAdjudicationSubmission, ...]
    label_verifications: tuple[HumanLabelSetVerificationReceipt, ...]
    readiness: ReaderEvidenceReadinessReport
    schema_version: str = READER_EVIDENCE_IMPORT_BUNDLE_SCHEMA_VERSION
    bundle_id: str = ""

    def __post_init__(self) -> None:
        _require_text(self.evidence_pack_id, "evidence_pack_id")
        if self.schema_version != READER_EVIDENCE_IMPORT_BUNDLE_SCHEMA_VERSION:
            raise ReaderEvidenceImportError(
                "unsupported evidence import bundle schema"
            )
        annotations = _canonical_typed(
            self.annotation_submissions,
            ReaderAnnotationSubmission,
            key=lambda item: item.submission_id,
            field_name="annotation_submissions",
            allow_empty=True,
        )
        adjudications = _canonical_typed(
            self.adjudication_submissions,
            ReaderAdjudicationSubmission,
            key=lambda item: item.submission_id,
            field_name="adjudication_submissions",
            allow_empty=True,
        )
        verifications = _canonical_typed(
            self.label_verifications,
            HumanLabelSetVerificationReceipt,
            key=lambda item: item.receipt_id,
            field_name="label_verifications",
            allow_empty=True,
        )
        if not isinstance(self.readiness, ReaderEvidenceReadinessReport):
            raise ReaderEvidenceImportError(
                "readiness must be a ReaderEvidenceReadinessReport"
            )
        if len({item.packet_id for item in annotations}) != len(annotations):
            raise ReaderEvidenceImportError(
                "annotation packet submissions must be unique"
            )
        if len({item.case_id for item in adjudications}) != len(adjudications):
            raise ReaderEvidenceImportError(
                "adjudication case submissions must be unique"
            )
        object.__setattr__(self, "annotation_submissions", annotations)
        object.__setattr__(self, "adjudication_submissions", adjudications)
        object.__setattr__(self, "label_verifications", verifications)
        expected = stable_reader_core_id(
            "reader-evidence-import-bundle",
            self.identity_payload(include_id=False),
        )
        if self.bundle_id:
            if self.bundle_id != expected:
                raise ReaderEvidenceImportError(
                    "bundle_id does not match evidence import bundle content"
                )
        else:
            object.__setattr__(self, "bundle_id", expected)

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema_version": self.schema_version,
            "evidence_pack_id": self.evidence_pack_id,
            "annotation_submission_ids": [
                item.submission_id for item in self.annotation_submissions
            ],
            "adjudication_submission_ids": [
                item.submission_id for item in self.adjudication_submissions
            ],
            "label_verification_receipt_ids": [
                item.receipt_id for item in self.label_verifications
            ],
            "readiness_report_id": self.readiness.report_id,
        }
        if include_id:
            payload["bundle_id"] = self.bundle_id
        return payload


class ReaderEvidenceImporter:
    """Import a local return directory and evaluate evidence readiness."""

    def import_directory(
        self,
        *,
        root: str | Path,
        pack: ReaderEvidencePack,
        submission_directory: str | Path,
    ) -> ReaderEvidenceImportBundle:
        if not isinstance(pack, ReaderEvidencePack):
            raise ReaderEvidenceImportError(
                "pack must be a ReaderEvidencePack"
            )
        root_path = Path(root).resolve()
        if not root_path.is_dir():
            raise ReaderEvidenceImportError(
                "root must be an existing directory"
            )
        submission_path = Path(submission_directory)
        if not submission_path.is_dir():
            raise ReaderEvidenceImportError(
                "submission_directory must be an existing directory"
            )
        files = tuple(sorted(submission_path.iterdir(), key=lambda item: item.name))
        for item in files:
            if not item.is_file() or item.suffix.lower() != ".json":
                raise ReaderEvidenceImportError(
                    "submission_directory may contain only JSON files"
                )

        annotation_payloads: list[tuple[Path, Mapping[str, object]]] = []
        adjudication_payloads: list[tuple[Path, Mapping[str, object]]] = []
        for path in files:
            payload = _load_json_object(path, "evidence submission")
            schema = _require_text(payload.get("schema_version"), "schema_version")
            if schema == READER_ANNOTATION_SUBMISSION_SCHEMA_VERSION:
                annotation_payloads.append((path, payload))
            elif schema == READER_ADJUDICATION_SUBMISSION_SCHEMA_VERSION:
                adjudication_payloads.append((path, payload))
            else:
                raise ReaderEvidenceImportError(
                    f"unsupported evidence submission schema in {path.name}"
                )

        packets_by_id = {item.packet_id: item for item in pack.annotation_packets}
        descriptors_by_id = {
            item.descriptor_id: item for item in pack.package.documents
        }
        annotations: list[ReaderAnnotationSubmission] = []
        annotation_by_label_set_id: dict[str, ReaderAnnotationSubmission] = {}
        seen_packet_ids: set[str] = set()
        for path, payload in annotation_payloads:
            annotation_submission = _parse_annotation_submission(payload)
            if annotation_submission.packet_id in seen_packet_ids:
                raise ReaderEvidenceImportError(
                    "duplicate annotation submission for packet"
                )
            packet = packets_by_id.get(annotation_submission.packet_id)
            if packet is None:
                raise ReaderEvidenceImportError(
                    f"annotation submission references foreign packet: {path.name}"
                )
            _validate_annotation_packet(
                packet,
                annotation_submission.label_set,
            )
            label_set_id = annotation_submission.label_set.label_set_id
            if label_set_id in annotation_by_label_set_id:
                raise ReaderEvidenceImportError(
                    "duplicate annotation label_set_id"
                )
            seen_packet_ids.add(annotation_submission.packet_id)
            annotations.append(annotation_submission)
            annotation_by_label_set_id[label_set_id] = annotation_submission

        adjudications: list[ReaderAdjudicationSubmission] = []
        typed_adjudications: list[HumanLabelAdjudication] = []
        final_label_sets: list[HumanLabelSet] = []
        seen_case_ids: set[str] = set()
        assignments_by_case = {
            item.case_id: item for item in pack.plan.assignments
        }
        for path, payload in adjudication_payloads:
            adjudication_submission = _parse_adjudication_submission(payload)
            if adjudication_submission.case_id in seen_case_ids:
                raise ReaderEvidenceImportError(
                    "duplicate adjudication submission for case"
                )
            assignment = assignments_by_case.get(adjudication_submission.case_id)
            if assignment is None:
                raise ReaderEvidenceImportError(
                    f"adjudication submission references foreign case: {path.name}"
                )
            if (
                adjudication_submission.adjudicator_id
                != assignment.adjudicator_id
            ):
                raise ReaderEvidenceImportError(
                    "adjudication submission uses wrong adjudicator"
                )
            source_submissions: list[ReaderAnnotationSubmission] = []
            for source_id in adjudication_submission.source_label_set_ids:
                source_submission = annotation_by_label_set_id.get(source_id)
                if source_submission is None:
                    raise ReaderEvidenceImportError(
                        "adjudication source label set has not been imported"
                    )
                source_submissions.append(source_submission)
            source_sets = tuple(
                sorted(
                    (item.label_set for item in source_submissions),
                    key=lambda item: item.label_set_id,
                )
            )
            if {item.annotator_id for item in source_sets} != set(
                assignment.annotator_ids
            ):
                raise ReaderEvidenceImportError(
                    "adjudication sources must exactly match assigned annotators"
                )
            final_set = adjudication_submission.adjudicated_label_set
            if (
                final_set.document_descriptor_id != assignment.descriptor_id
                or final_set.document_id != assignment.document_id
                or final_set.source_revision != assignment.source_revision
                or final_set.guideline_version
                != pack.guideline.guideline_version
            ):
                raise ReaderEvidenceImportError(
                    "adjudicated label set does not match evidence assignment"
                )
            typed_adjudication = HumanLabelAdjudication(
                source_label_sets=source_sets,
                adjudicator_id=adjudication_submission.adjudicator_id,
                adjudicated_label_set=final_set,
                resolutions=adjudication_submission.resolutions,
                schema_version=ADJUDICATION_SCHEMA_VERSION,
                adjudication_id=adjudication_submission.adjudication_id,
            )
            if adjudication_submission.adjudication_id:
                if (
                    typed_adjudication.adjudication_id
                    != adjudication_submission.adjudication_id
                ):
                    raise ReaderEvidenceImportError(
                        "adjudication_id does not match reconstructed adjudication"
                    )
            else:
                adjudication_submission = ReaderAdjudicationSubmission(
                    case_id=adjudication_submission.case_id,
                    adjudicator_id=adjudication_submission.adjudicator_id,
                    source_label_set_ids=(
                        adjudication_submission.source_label_set_ids
                    ),
                    adjudicated_label_set=(
                        adjudication_submission.adjudicated_label_set
                    ),
                    resolutions=adjudication_submission.resolutions,
                    adjudication_id=typed_adjudication.adjudication_id,
                )
            seen_case_ids.add(adjudication_submission.case_id)
            adjudications.append(adjudication_submission)
            typed_adjudications.append(typed_adjudication)
            final_label_sets.append(final_set)

        verification_receipts: list[HumanLabelSetVerificationReceipt] = []
        label_sets_to_verify = [
            item.label_set for item in annotations
        ] + final_label_sets
        seen_label_set_ids: set[str] = set()
        for label_set in label_sets_to_verify:
            if label_set.label_set_id in seen_label_set_ids:
                continue
            descriptor = descriptors_by_id.get(label_set.document_descriptor_id)
            if descriptor is None:
                raise ReaderEvidenceImportError(
                    "label set references a foreign corpus descriptor"
                )
            verification_receipts.append(
                _verify_label_set(
                    root=root_path,
                    descriptor=descriptor,
                    label_set=label_set,
                )
            )
            seen_label_set_ids.add(label_set.label_set_id)

        readiness = ReaderEvidenceReadinessEvaluator().evaluate(
            plan=pack.plan,
            package=pack.package,
            package_verification=pack.package_verification,
            annotation_sets=tuple(item.label_set for item in annotations),
            adjudications=tuple(typed_adjudications),
            label_verifications=tuple(verification_receipts),
        )
        return ReaderEvidenceImportBundle(
            evidence_pack_id=pack.pack_id,
            annotation_submissions=tuple(annotations),
            adjudication_submissions=tuple(adjudications),
            label_verifications=tuple(verification_receipts),
            readiness=readiness,
        )


def _verify_label_set(
    *,
    root: Path,
    descriptor: CorpusDocumentDescriptor,
    label_set: HumanLabelSet,
) -> HumanLabelSetVerificationReceipt:
    try:
        return label_set.verify_spans(root=root, descriptor=descriptor)
    except ReaderCorpusError as exc:
        raise ReaderEvidenceImportError(
            f"label-set span verification failed: {label_set.label_set_id}: {exc}"
        ) from exc


def _validate_annotation_packet(
    packet: ReaderAnnotationPacket,
    label_set: HumanLabelSet,
) -> None:
    if (
        label_set.document_descriptor_id != packet.descriptor_id
        or label_set.document_id != packet.document_id
        or label_set.source_revision != packet.source_revision
        or label_set.annotator_id != packet.annotator_id
    ):
        raise ReaderEvidenceImportError(
            "annotation label set does not match assigned packet"
        )


def _parse_annotation_submission(
    payload: Mapping[str, object],
) -> ReaderAnnotationSubmission:
    _require_exact_keys(
        payload,
        required={"schema_version", "packet_id", "label_set"},
        optional={"submission_id"},
        field_name="annotation submission",
    )
    return ReaderAnnotationSubmission(
        schema_version=_require_text(
            payload["schema_version"],
            "schema_version",
        ),
        packet_id=_require_text(payload["packet_id"], "packet_id"),
        label_set=_parse_label_set(
            _require_mapping(payload["label_set"], "label_set")
        ),
        submission_id=_optional_text(
            payload.get("submission_id"),
            "submission_id",
        )
        or "",
    )


def _parse_adjudication_submission(
    payload: Mapping[str, object],
) -> ReaderAdjudicationSubmission:
    _require_exact_keys(
        payload,
        required={
            "schema_version",
            "case_id",
            "adjudicator_id",
            "source_label_set_ids",
            "adjudicated_label_set",
            "resolutions",
        },
        optional={"adjudication_id", "submission_id"},
        field_name="adjudication submission",
    )
    resolutions_raw = _require_list(payload["resolutions"], "resolutions")
    return ReaderAdjudicationSubmission(
        schema_version=_require_text(
            payload["schema_version"],
            "schema_version",
        ),
        case_id=_require_text(payload["case_id"], "case_id"),
        adjudicator_id=_require_text(
            payload["adjudicator_id"],
            "adjudicator_id",
        ),
        source_label_set_ids=_text_sequence(
            payload["source_label_set_ids"],
            "source_label_set_id",
        ),
        adjudicated_label_set=_parse_label_set(
            _require_mapping(
                payload["adjudicated_label_set"],
                "adjudicated_label_set",
            )
        ),
        resolutions=tuple(
            _parse_resolution(item, index=index)
            for index, item in enumerate(resolutions_raw)
        ),
        adjudication_id=_optional_text(
            payload.get("adjudication_id"),
            "adjudication_id",
        )
        or "",
        submission_id=_optional_text(
            payload.get("submission_id"),
            "submission_id",
        )
        or "",
    )


def _parse_label_set(payload: Mapping[str, object]) -> HumanLabelSet:
    _require_exact_keys(
        payload,
        required={
            "schema_version",
            "document_descriptor_id",
            "document_id",
            "source_revision",
            "annotator_id",
            "guideline_version",
            "label_version",
            "role",
            "claims",
            "exceptions",
            "relations",
            "qualifiers",
            "label_set_id",
        },
        optional=set(),
        field_name="human label set",
    )
    claims_raw = _require_list(payload["claims"], "claims")
    exceptions_raw = _require_list(payload["exceptions"], "exceptions")
    relations_raw = _require_list(payload["relations"], "relations")
    qualifiers_raw = _require_list(payload["qualifiers"], "qualifiers")
    return HumanLabelSet(
        schema_version=_require_text(
            payload["schema_version"],
            "schema_version",
        ),
        document_descriptor_id=_require_text(
            payload["document_descriptor_id"],
            "document_descriptor_id",
        ),
        document_id=_require_text(payload["document_id"], "document_id"),
        source_revision=_require_text(
            payload["source_revision"],
            "source_revision",
        ),
        annotator_id=_require_text(payload["annotator_id"], "annotator_id"),
        guideline_version=_require_text(
            payload["guideline_version"],
            "guideline_version",
        ),
        label_version=_require_text(
            payload["label_version"],
            "label_version",
        ),
        role=_enum_value(LabelSetRole, payload["role"], "role"),
        claims=tuple(
            _parse_claim(item, index=index)
            for index, item in enumerate(claims_raw)
        ),
        exceptions=tuple(
            _parse_exception(item, index=index)
            for index, item in enumerate(exceptions_raw)
        ),
        relations=tuple(
            _parse_relation(item, index=index)
            for index, item in enumerate(relations_raw)
        ),
        qualifiers=tuple(
            _parse_qualifier(item, index=index)
            for index, item in enumerate(qualifiers_raw)
        ),
        label_set_id=_require_text(
            payload["label_set_id"],
            "label_set_id",
        ),
    )


def _parse_claim(value: object, *, index: int) -> HumanClaimLabel:
    field_name = f"claims[{index}]"
    payload = _require_mapping(value, field_name)
    _require_exact_keys(
        payload,
        required={
            "label_id",
            "document_id",
            "source_revision",
            "modality",
            "source_spans",
            "qualifier_codes",
            "applicability_codes",
        },
        optional=set(),
        field_name=field_name,
    )
    spans_raw = _require_list(payload["source_spans"], "source_spans")
    return HumanClaimLabel(
        label_id=_require_text(payload["label_id"], "label_id"),
        document_id=_require_text(payload["document_id"], "document_id"),
        source_revision=_require_text(
            payload["source_revision"],
            "source_revision",
        ),
        modality=_enum_value(
            ClaimModality,
            payload["modality"],
            "modality",
        ),
        source_spans=tuple(
            _parse_span(item, field_name=f"source_spans[{span_index}]")
            for span_index, item in enumerate(spans_raw)
        ),
        qualifier_codes=_text_sequence(
            payload["qualifier_codes"],
            "qualifier_code",
        ),
        applicability_codes=_text_sequence(
            payload["applicability_codes"],
            "applicability_code",
        ),
    )


def _parse_exception(value: object, *, index: int) -> HumanExceptionLabel:
    field_name = f"exceptions[{index}]"
    payload = _require_mapping(value, field_name)
    _require_exact_keys(
        payload,
        required={
            "label_id",
            "document_id",
            "source_revision",
            "category",
            "trigger_span",
            "statement_span",
            "target_claim_label_ids",
        },
        optional=set(),
        field_name=field_name,
    )
    return HumanExceptionLabel(
        label_id=_require_text(payload["label_id"], "label_id"),
        document_id=_require_text(payload["document_id"], "document_id"),
        source_revision=_require_text(
            payload["source_revision"],
            "source_revision",
        ),
        category=_enum_value(
            ExceptionCategory,
            payload["category"],
            "category",
        ),
        trigger_span=_parse_span(
            payload["trigger_span"],
            field_name="trigger_span",
        ),
        statement_span=_parse_span(
            payload["statement_span"],
            field_name="statement_span",
        ),
        target_claim_label_ids=_text_sequence(
            payload["target_claim_label_ids"],
            "target_claim_label_id",
        ),
    )


def _parse_relation(value: object, *, index: int) -> HumanRelationLabel:
    field_name = f"relations[{index}]"
    payload = _require_mapping(value, field_name)
    _require_exact_keys(
        payload,
        required={
            "label_id",
            "document_id",
            "source_revision",
            "relation_kind",
            "source_claim_label_id",
            "target_claim_label_id",
            "evidence_spans",
        },
        optional=set(),
        field_name=field_name,
    )
    spans_raw = _require_list(payload["evidence_spans"], "evidence_spans")
    return HumanRelationLabel(
        label_id=_require_text(payload["label_id"], "label_id"),
        document_id=_require_text(payload["document_id"], "document_id"),
        source_revision=_require_text(
            payload["source_revision"],
            "source_revision",
        ),
        relation_kind=_enum_value(
            RelationKind,
            payload["relation_kind"],
            "relation_kind",
        ),
        source_claim_label_id=_require_text(
            payload["source_claim_label_id"],
            "source_claim_label_id",
        ),
        target_claim_label_id=_require_text(
            payload["target_claim_label_id"],
            "target_claim_label_id",
        ),
        evidence_spans=tuple(
            _parse_span(item, field_name=f"evidence_spans[{span_index}]")
            for span_index, item in enumerate(spans_raw)
        ),
    )


def _parse_qualifier(value: object, *, index: int) -> HumanQualifierLabel:
    field_name = f"qualifiers[{index}]"
    payload = _require_mapping(value, field_name)
    _require_exact_keys(
        payload,
        required={
            "label_id",
            "document_id",
            "source_revision",
            "qualifier_kind",
            "target_claim_label_id",
            "source_span",
        },
        optional=set(),
        field_name=field_name,
    )
    return HumanQualifierLabel(
        label_id=_require_text(payload["label_id"], "label_id"),
        document_id=_require_text(payload["document_id"], "document_id"),
        source_revision=_require_text(
            payload["source_revision"],
            "source_revision",
        ),
        qualifier_kind=_enum_value(
            QualifierKind,
            payload["qualifier_kind"],
            "qualifier_kind",
        ),
        target_claim_label_id=_require_text(
            payload["target_claim_label_id"],
            "target_claim_label_id",
        ),
        source_span=_parse_span(
            payload["source_span"],
            field_name="source_span",
        ),
    )


def _parse_span(value: object, *, field_name: str) -> SourceSpan:
    payload = _require_mapping(value, field_name)
    _require_exact_keys(
        payload,
        required={
            "span_id",
            "document_id",
            "start_offset",
            "end_offset",
            "content_hash",
            "source_revision",
        },
        optional=set(),
        field_name=field_name,
    )
    return SourceSpan(
        span_id=_require_text(payload["span_id"], "span_id"),
        document_id=_require_text(payload["document_id"], "document_id"),
        start_offset=_require_int(payload["start_offset"], "start_offset"),
        end_offset=_require_int(payload["end_offset"], "end_offset"),
        content_hash=_require_text(payload["content_hash"], "content_hash"),
        source_revision=_require_text(
            payload["source_revision"],
            "source_revision",
        ),
    )


def _parse_resolution(value: object, *, index: int) -> AdjudicationResolution:
    field_name = f"resolutions[{index}]"
    payload = _require_mapping(value, field_name)
    _require_exact_keys(
        payload,
        required={
            "kind",
            "candidate_label_ids",
            "resolved_label_ids",
            "resolution_code",
            "rationale_code",
            "resolution_id",
        },
        optional=set(),
        field_name=field_name,
    )
    return AdjudicationResolution(
        kind=_enum_value(HumanLabelKind, payload["kind"], "kind"),
        candidate_label_ids=_text_sequence(
            payload["candidate_label_ids"],
            "candidate_label_id",
        ),
        resolved_label_ids=_text_sequence(
            payload["resolved_label_ids"],
            "resolved_label_id",
        ),
        resolution_code=_require_text(
            payload["resolution_code"],
            "resolution_code",
        ),
        rationale_code=_require_text(
            payload["rationale_code"],
            "rationale_code",
        ),
        resolution_id=_require_text(
            payload["resolution_id"],
            "resolution_id",
        ),
    )


def _load_json_object(path: Path, field_name: str) -> Mapping[str, object]:
    try:
        value: Any = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ReaderEvidenceImportError(
            f"failed to load {field_name} from {path.name}: {exc}"
        ) from exc
    return _require_mapping(value, field_name)


def _require_mapping(value: object, field_name: str) -> Mapping[str, object]:
    if not isinstance(value, dict) or any(
        not isinstance(key, str) for key in value
    ):
        raise ReaderEvidenceImportError(
            f"{field_name} must be a JSON object with string keys"
        )
    return cast(Mapping[str, object], value)


def _require_list(value: object, field_name: str) -> list[object]:
    if not isinstance(value, list):
        raise ReaderEvidenceImportError(f"{field_name} must be a JSON array")
    return cast(list[object], value)


def _require_exact_keys(
    payload: Mapping[str, object],
    *,
    required: set[str],
    optional: set[str],
    field_name: str,
) -> None:
    keys = set(payload)
    missing = sorted(required - keys)
    unknown = sorted(keys - required - optional)
    if missing:
        raise ReaderEvidenceImportError(
            f"{field_name} is missing keys: {', '.join(missing)}"
        )
    if unknown:
        raise ReaderEvidenceImportError(
            f"{field_name} has unknown keys: {', '.join(unknown)}"
        )


def _enum_value(
    enum_type: type[E],
    value: object,
    field_name: str,
) -> E:
    text = _require_text(value, field_name)
    try:
        return enum_type(text)
    except ValueError as exc:
        allowed = ", ".join(str(item.value) for item in enum_type)
        raise ReaderEvidenceImportError(
            f"{field_name} must be one of: {allowed}"
        ) from exc


def _require_text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReaderEvidenceImportError(
            f"{field_name} must be non-empty text"
        )
    return value


def _optional_text(value: object, field_name: str) -> str | None:
    if value is None:
        return None
    return _require_text(value, field_name)


def _require_int(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ReaderEvidenceImportError(f"{field_name} must be an integer")
    return value


def _text_sequence(value: object, field_name: str) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise ReaderEvidenceImportError(f"{field_name} values must be an array")
    return tuple(_require_text(item, field_name) for item in value)


def _unique_sorted_text(
    values: Iterable[str],
    field_name: str,
) -> tuple[str, ...]:
    items = tuple(values)
    for item in items:
        _require_text(item, field_name)
    if len(set(items)) != len(items):
        raise ReaderEvidenceImportError(
            f"{field_name} values must be unique"
        )
    return tuple(sorted(items))


def _canonical_typed(
    values: Iterable[T],
    expected_type: type[T],
    *,
    key: Callable[[T], str],
    field_name: str,
    allow_empty: bool,
) -> tuple[T, ...]:
    items = tuple(values)
    if not allow_empty and not items:
        raise ReaderEvidenceImportError(f"{field_name} must not be empty")
    if any(not isinstance(item, expected_type) for item in items):
        raise ReaderEvidenceImportError(
            f"{field_name} contain invalid values"
        )
    ordered = tuple(sorted(items, key=key))
    if len({key(item) for item in ordered}) != len(ordered):
        raise ReaderEvidenceImportError(f"{field_name} IDs must be unique")
    return ordered
