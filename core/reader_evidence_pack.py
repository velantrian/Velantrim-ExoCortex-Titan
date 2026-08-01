"""Canonical local evidence-pack construction for Reader Core PR-RDR-17.

The pack builder reads only an explicit local source specification, hashes and
verifies rights-described corpus files plus the annotation guideline, and emits
operator and blind annotation metadata artifacts. It never embeds document text,
executes Reader Core, contacts a provider, or authorizes live integration.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
from typing import Any, TypeVar, cast

from core.reader_core_contracts import stable_reader_core_id
from core.reader_corpus_adjudication import (
    CorpusDocumentDescriptor,
    CorpusPackageManifest,
    CorpusPackageVerificationReceipt,
    CorpusPrivacyClass,
    CorpusUsageBasis,
    HumanLabelKind,
)
from core.reader_evidence_intake import (
    ReaderAnnotationGuidelineSpec,
    ReaderAnnotationPacket,
    ReaderEvidenceProgramPlan,
    ReaderEvidenceProgramPlanner,
    ReaderEvidenceReadinessEvaluator,
    ReaderEvidenceReadinessReport,
)

READER_EVIDENCE_SOURCE_SPEC_SCHEMA_VERSION = "reader-core.evidence-source-spec.v1"
READER_EVIDENCE_PACK_SCHEMA_VERSION = "reader-core.evidence-pack.v1"

T = TypeVar("T")
E = TypeVar("E", bound=Enum)


class ReaderEvidencePackError(ValueError):
    """Raised when an evidence source spec or generated pack is invalid."""


@dataclass(frozen=True, slots=True)
class ReaderEvidenceDocumentSource:
    document_id: str
    relative_path: str
    media_type: str
    usage_basis: CorpusUsageBasis
    rights_reference: str
    privacy_class: CorpusPrivacyClass
    redistribution_allowed: bool
    source_id: str = ""

    def __post_init__(self) -> None:
        for field_name in (
            "document_id",
            "relative_path",
            "media_type",
            "rights_reference",
        ):
            _require_text(getattr(self, field_name), field_name)
        relative_path = _normalize_relative_path(self.relative_path)
        if not isinstance(self.usage_basis, CorpusUsageBasis):
            raise ReaderEvidencePackError(
                "usage_basis must be a CorpusUsageBasis"
            )
        if not isinstance(self.privacy_class, CorpusPrivacyClass):
            raise ReaderEvidencePackError(
                "privacy_class must be a CorpusPrivacyClass"
            )
        if not isinstance(self.redistribution_allowed, bool):
            raise ReaderEvidencePackError(
                "redistribution_allowed must be a boolean"
            )
        if (
            self.usage_basis is CorpusUsageBasis.AUTHORIZED_PRIVATE
            and self.redistribution_allowed
        ):
            raise ReaderEvidencePackError(
                "authorized private documents cannot be redistributable"
            )
        if (
            self.privacy_class is CorpusPrivacyClass.SENSITIVE
            and self.redistribution_allowed
        ):
            raise ReaderEvidencePackError(
                "sensitive documents cannot be redistributable"
            )
        object.__setattr__(self, "relative_path", relative_path)
        expected = stable_reader_core_id(
            "reader-evidence-document-source",
            self.identity_payload(include_id=False),
        )
        if self.source_id:
            if self.source_id != expected:
                raise ReaderEvidencePackError(
                    "source_id does not match document source content"
                )
        else:
            object.__setattr__(self, "source_id", expected)

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "document_id": self.document_id,
            "relative_path": self.relative_path,
            "media_type": self.media_type,
            "usage_basis": self.usage_basis.value,
            "rights_reference": self.rights_reference,
            "privacy_class": self.privacy_class.value,
            "redistribution_allowed": self.redistribution_allowed,
        }
        if include_id:
            payload["source_id"] = self.source_id
        return payload


@dataclass(frozen=True, slots=True)
class ReaderEvidenceGuidelineSource:
    guideline_version: str
    relative_path: str
    required_label_kinds: tuple[HumanLabelKind, ...]
    min_independent_annotators: int = 2
    source_id: str = ""

    def __post_init__(self) -> None:
        _require_text(self.guideline_version, "guideline_version")
        relative_path = _normalize_relative_path(self.relative_path)
        kinds = tuple(self.required_label_kinds)
        if not kinds or any(not isinstance(item, HumanLabelKind) for item in kinds):
            raise ReaderEvidencePackError(
                "required_label_kinds require HumanLabelKind values"
            )
        kinds = tuple(sorted(kinds, key=lambda item: item.value))
        if len(set(kinds)) != len(kinds):
            raise ReaderEvidencePackError(
                "required_label_kinds must be unique"
            )
        if HumanLabelKind.CLAIM not in kinds:
            raise ReaderEvidencePackError(
                "guideline source must require claim review"
            )
        if (
            isinstance(self.min_independent_annotators, bool)
            or not isinstance(self.min_independent_annotators, int)
            or self.min_independent_annotators < 2
        ):
            raise ReaderEvidencePackError(
                "min_independent_annotators must be an integer >= 2"
            )
        object.__setattr__(self, "relative_path", relative_path)
        object.__setattr__(self, "required_label_kinds", kinds)
        expected = stable_reader_core_id(
            "reader-evidence-guideline-source",
            self.identity_payload(include_id=False),
        )
        if self.source_id:
            if self.source_id != expected:
                raise ReaderEvidencePackError(
                    "source_id does not match guideline source content"
                )
        else:
            object.__setattr__(self, "source_id", expected)

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "guideline_version": self.guideline_version,
            "relative_path": self.relative_path,
            "required_label_kinds": [
                item.value for item in self.required_label_kinds
            ],
            "min_independent_annotators": self.min_independent_annotators,
        }
        if include_id:
            payload["source_id"] = self.source_id
        return payload


@dataclass(frozen=True, slots=True)
class ReaderEvidenceAssignmentSource:
    document_id: str
    annotator_ids: tuple[str, ...]
    adjudicator_id: str
    source_id: str = ""

    def __post_init__(self) -> None:
        _require_text(self.document_id, "document_id")
        _require_text(self.adjudicator_id, "adjudicator_id")
        annotators = _unique_sorted_text(self.annotator_ids, "annotator_id")
        if len(annotators) < 2:
            raise ReaderEvidencePackError(
                "assignment sources require at least two annotators"
            )
        if self.adjudicator_id in annotators:
            raise ReaderEvidencePackError(
                "adjudicator must differ from every annotator"
            )
        object.__setattr__(self, "annotator_ids", annotators)
        expected = stable_reader_core_id(
            "reader-evidence-assignment-source",
            self.identity_payload(include_id=False),
        )
        if self.source_id:
            if self.source_id != expected:
                raise ReaderEvidencePackError(
                    "source_id does not match assignment source content"
                )
        else:
            object.__setattr__(self, "source_id", expected)

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "document_id": self.document_id,
            "annotator_ids": list(self.annotator_ids),
            "adjudicator_id": self.adjudicator_id,
        }
        if include_id:
            payload["source_id"] = self.source_id
        return payload


@dataclass(frozen=True, slots=True)
class ReaderEvidenceSourceSpec:
    corpus_name: str
    corpus_version: str
    documents: tuple[ReaderEvidenceDocumentSource, ...]
    guideline: ReaderEvidenceGuidelineSource
    assignments: tuple[ReaderEvidenceAssignmentSource, ...]
    tags: tuple[str, ...] = ()
    schema_version: str = READER_EVIDENCE_SOURCE_SPEC_SCHEMA_VERSION
    spec_id: str = ""

    def __post_init__(self) -> None:
        _require_text(self.corpus_name, "corpus_name")
        _require_text(self.corpus_version, "corpus_version")
        if self.schema_version != READER_EVIDENCE_SOURCE_SPEC_SCHEMA_VERSION:
            raise ReaderEvidencePackError(
                "unsupported evidence source spec schema"
            )
        documents = _canonical_instances(
            self.documents,
            ReaderEvidenceDocumentSource,
            key=lambda item: item.document_id,
            field_name="documents",
        )
        assignments = _canonical_instances(
            self.assignments,
            ReaderEvidenceAssignmentSource,
            key=lambda item: item.document_id,
            field_name="assignments",
        )
        if not isinstance(self.guideline, ReaderEvidenceGuidelineSource):
            raise ReaderEvidencePackError(
                "guideline must be a ReaderEvidenceGuidelineSource"
            )
        document_ids = tuple(item.document_id for item in documents)
        assignment_ids = tuple(item.document_id for item in assignments)
        if document_ids != assignment_ids:
            raise ReaderEvidencePackError(
                "assignments must exactly cover document IDs"
            )
        if len({item.relative_path for item in documents}) != len(documents):
            raise ReaderEvidencePackError("document paths must be unique")
        tags = _unique_sorted_text(self.tags, "tag")
        object.__setattr__(self, "documents", documents)
        object.__setattr__(self, "assignments", assignments)
        object.__setattr__(self, "tags", tags)
        expected = stable_reader_core_id(
            "reader-evidence-source-spec",
            self.identity_payload(include_id=False),
        )
        if self.spec_id:
            if self.spec_id != expected:
                raise ReaderEvidencePackError(
                    "spec_id does not match source spec content"
                )
        else:
            object.__setattr__(self, "spec_id", expected)

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema_version": self.schema_version,
            "corpus_name": self.corpus_name,
            "corpus_version": self.corpus_version,
            "document_source_ids": [item.source_id for item in self.documents],
            "guideline_source_id": self.guideline.source_id,
            "assignment_source_ids": [
                item.source_id for item in self.assignments
            ],
            "tags": list(self.tags),
        }
        if include_id:
            payload["spec_id"] = self.spec_id
        return payload


@dataclass(frozen=True, slots=True)
class ReaderEvidencePack:
    source_spec_id: str
    package: CorpusPackageManifest
    package_verification: CorpusPackageVerificationReceipt
    guideline: ReaderAnnotationGuidelineSpec
    plan: ReaderEvidenceProgramPlan
    annotation_packets: tuple[ReaderAnnotationPacket, ...]
    initial_readiness: ReaderEvidenceReadinessReport
    schema_version: str = READER_EVIDENCE_PACK_SCHEMA_VERSION
    pack_id: str = ""

    def __post_init__(self) -> None:
        _require_text(self.source_spec_id, "source_spec_id")
        if self.schema_version != READER_EVIDENCE_PACK_SCHEMA_VERSION:
            raise ReaderEvidencePackError("unsupported evidence pack schema")
        if not isinstance(self.package, CorpusPackageManifest):
            raise ReaderEvidencePackError(
                "package must be a CorpusPackageManifest"
            )
        if not isinstance(
            self.package_verification,
            CorpusPackageVerificationReceipt,
        ):
            raise ReaderEvidencePackError(
                "package_verification must be a verification receipt"
            )
        if not isinstance(self.guideline, ReaderAnnotationGuidelineSpec):
            raise ReaderEvidencePackError(
                "guideline must be a ReaderAnnotationGuidelineSpec"
            )
        if not isinstance(self.plan, ReaderEvidenceProgramPlan):
            raise ReaderEvidencePackError(
                "plan must be a ReaderEvidenceProgramPlan"
            )
        if not isinstance(self.initial_readiness, ReaderEvidenceReadinessReport):
            raise ReaderEvidencePackError(
                "initial_readiness must be a readiness report"
            )
        raw_packets = tuple(self.annotation_packets)
        if not raw_packets or any(
            not isinstance(item, ReaderAnnotationPacket) for item in raw_packets
        ):
            raise ReaderEvidencePackError(
                "annotation_packets require ReaderAnnotationPacket values"
            )
        packets = tuple(
            sorted(
                raw_packets,
                key=lambda item: (item.case_id, item.annotator_id),
            )
        )
        if len({item.packet_id for item in packets}) != len(packets):
            raise ReaderEvidencePackError("annotation packet IDs must be unique")
        if self.package_verification.package_id != self.package.package_id:
            raise ReaderEvidencePackError(
                "package verification must match package"
            )
        if self.plan.package_id != self.package.package_id:
            raise ReaderEvidencePackError("plan must match package")
        if self.plan.guideline.guideline_id != self.guideline.guideline_id:
            raise ReaderEvidencePackError("plan must match guideline")
        if self.initial_readiness.plan_id != self.plan.plan_id:
            raise ReaderEvidencePackError("readiness must match plan")
        if self.initial_readiness.package_id != self.package.package_id:
            raise ReaderEvidencePackError("readiness must match package")
        if (
            self.initial_readiness.package_verification_receipt_id
            != self.package_verification.receipt_id
        ):
            raise ReaderEvidencePackError(
                "readiness must reference package verification"
            )
        expected_packet_ids = {
            item.packet_id
            for item in ReaderEvidenceProgramPlanner.build_annotation_packets(
                self.plan
            )
        }
        if {item.packet_id for item in packets} != expected_packet_ids:
            raise ReaderEvidencePackError(
                "annotation packets must exactly cover plan assignments"
            )
        object.__setattr__(self, "annotation_packets", packets)
        expected = stable_reader_core_id(
            "reader-evidence-pack",
            self.identity_payload(include_id=False),
        )
        if self.pack_id:
            if self.pack_id != expected:
                raise ReaderEvidencePackError(
                    "pack_id does not match evidence pack content"
                )
        else:
            object.__setattr__(self, "pack_id", expected)

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema_version": self.schema_version,
            "source_spec_id": self.source_spec_id,
            "package_id": self.package.package_id,
            "package_verification_receipt_id": (
                self.package_verification.receipt_id
            ),
            "guideline_id": self.guideline.guideline_id,
            "plan_id": self.plan.plan_id,
            "annotation_packet_ids": [
                item.packet_id for item in self.annotation_packets
            ],
            "initial_readiness_report_id": self.initial_readiness.report_id,
        }
        if include_id:
            payload["pack_id"] = self.pack_id
        return payload


class ReaderEvidencePackBuilder:
    """Build one verified local evidence pack from an explicit source spec."""

    def build(
        self,
        *,
        root: str | Path,
        spec: ReaderEvidenceSourceSpec,
    ) -> ReaderEvidencePack:
        if not isinstance(spec, ReaderEvidenceSourceSpec):
            raise ReaderEvidencePackError(
                "spec must be a ReaderEvidenceSourceSpec"
            )
        root_path = Path(root).resolve()
        if not root_path.is_dir():
            raise ReaderEvidencePackError("root must be an existing directory")
        descriptors = tuple(
            CorpusDocumentDescriptor.from_file(
                root=root_path,
                relative_path=item.relative_path,
                document_id=item.document_id,
                media_type=item.media_type,
                usage_basis=item.usage_basis,
                rights_reference=item.rights_reference,
                privacy_class=item.privacy_class,
                redistribution_allowed=item.redistribution_allowed,
            )
            for item in spec.documents
        )
        package = CorpusPackageManifest(
            corpus_name=spec.corpus_name,
            corpus_version=spec.corpus_version,
            documents=descriptors,
            tags=spec.tags,
        )
        package_verification = package.verify(root_path)
        guideline_path = _resolve_local_file(
            root_path,
            spec.guideline.relative_path,
            field_name="guideline relative_path",
        )
        guideline = ReaderAnnotationGuidelineSpec(
            guideline_version=spec.guideline.guideline_version,
            content_sha256=sha256(guideline_path.read_bytes()).hexdigest(),
            required_label_kinds=spec.guideline.required_label_kinds,
            min_independent_annotators=(
                spec.guideline.min_independent_annotators
            ),
        )
        plan = ReaderEvidenceProgramPlanner.create_plan(
            package=package,
            guideline=guideline,
            annotator_ids_by_document={
                item.document_id: item.annotator_ids
                for item in spec.assignments
            },
            adjudicator_ids_by_document={
                item.document_id: item.adjudicator_id
                for item in spec.assignments
            },
        )
        packets = ReaderEvidenceProgramPlanner.build_annotation_packets(plan)
        readiness = ReaderEvidenceReadinessEvaluator().evaluate(
            plan=plan,
            package=package,
            package_verification=package_verification,
        )
        return ReaderEvidencePack(
            source_spec_id=spec.spec_id,
            package=package,
            package_verification=package_verification,
            guideline=guideline,
            plan=plan,
            annotation_packets=packets,
            initial_readiness=readiness,
        )


def load_evidence_source_spec(path: str | Path) -> ReaderEvidenceSourceSpec:
    payload = _load_json_object(path, "evidence source spec")
    _require_exact_keys(
        payload,
        required={
            "schema_version",
            "corpus_name",
            "corpus_version",
            "documents",
            "guideline",
            "assignments",
        },
        optional={"tags", "spec_id"},
        field_name="evidence source spec",
    )
    documents_raw = _require_list(payload["documents"], "documents")
    assignments_raw = _require_list(payload["assignments"], "assignments")
    guideline_raw = _require_mapping(payload["guideline"], "guideline")
    return ReaderEvidenceSourceSpec(
        schema_version=_require_text(payload["schema_version"], "schema_version"),
        corpus_name=_require_text(payload["corpus_name"], "corpus_name"),
        corpus_version=_require_text(
            payload["corpus_version"],
            "corpus_version",
        ),
        documents=tuple(
            _parse_document_source(item, index=index)
            for index, item in enumerate(documents_raw)
        ),
        guideline=_parse_guideline_source(guideline_raw),
        assignments=tuple(
            _parse_assignment_source(item, index=index)
            for index, item in enumerate(assignments_raw)
        ),
        tags=_text_sequence(payload.get("tags", []), "tag"),
        spec_id=_optional_text(payload.get("spec_id"), "spec_id") or "",
    )


def evidence_pack_payload(pack: ReaderEvidencePack) -> dict[str, object]:
    if not isinstance(pack, ReaderEvidencePack):
        raise ReaderEvidencePackError("pack must be a ReaderEvidencePack")
    payload = _canonical_value(pack)
    if not isinstance(payload, dict):
        raise ReaderEvidencePackError("evidence pack serialization failed")
    return cast(dict[str, object], payload)


def annotation_packet_payload(
    packet: ReaderAnnotationPacket,
) -> dict[str, object]:
    if not isinstance(packet, ReaderAnnotationPacket):
        raise ReaderEvidencePackError(
            "packet must be a ReaderAnnotationPacket"
        )
    payload = _canonical_value(packet)
    if not isinstance(payload, dict):
        raise ReaderEvidencePackError("annotation packet serialization failed")
    return cast(dict[str, object], payload)


def write_canonical_json(path: str | Path, value: object) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(
        _canonical_value(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    output.write_text(serialized + "\n", encoding="utf-8")


def write_annotation_packets(
    directory: str | Path,
    packets: Iterable[ReaderAnnotationPacket],
) -> tuple[Path, ...]:
    raw_packets = tuple(packets)
    if not raw_packets or any(
        not isinstance(item, ReaderAnnotationPacket) for item in raw_packets
    ):
        raise ReaderEvidencePackError(
            "packets require at least one ReaderAnnotationPacket"
        )
    ordered = tuple(
        sorted(
            raw_packets,
            key=lambda item: (item.case_id, item.annotator_id, item.packet_id),
        )
    )
    output_dir = Path(directory)
    if output_dir.exists():
        if not output_dir.is_dir():
            raise ReaderEvidencePackError(
                "packet output path must be a directory"
            )
        if any(output_dir.iterdir()):
            raise ReaderEvidencePackError(
                "packet output directory must be empty"
            )
    else:
        output_dir.mkdir(parents=True, exist_ok=False)
    written: list[Path] = []
    for packet in ordered:
        output = output_dir / f"annotation-packet-{packet.packet_id}.json"
        write_canonical_json(output, packet)
        written.append(output)
    return tuple(written)


def _parse_document_source(
    value: object,
    *,
    index: int,
) -> ReaderEvidenceDocumentSource:
    field_name = f"documents[{index}]"
    payload = _require_mapping(value, field_name)
    _require_exact_keys(
        payload,
        required={
            "document_id",
            "relative_path",
            "media_type",
            "usage_basis",
            "rights_reference",
            "privacy_class",
            "redistribution_allowed",
        },
        optional={"source_id"},
        field_name=field_name,
    )
    return ReaderEvidenceDocumentSource(
        document_id=_require_text(payload["document_id"], "document_id"),
        relative_path=_require_text(payload["relative_path"], "relative_path"),
        media_type=_require_text(payload["media_type"], "media_type"),
        usage_basis=_enum_value(
            CorpusUsageBasis,
            payload["usage_basis"],
            "usage_basis",
        ),
        rights_reference=_require_text(
            payload["rights_reference"],
            "rights_reference",
        ),
        privacy_class=_enum_value(
            CorpusPrivacyClass,
            payload["privacy_class"],
            "privacy_class",
        ),
        redistribution_allowed=_require_bool(
            payload["redistribution_allowed"],
            "redistribution_allowed",
        ),
        source_id=_optional_text(payload.get("source_id"), "source_id") or "",
    )


def _parse_guideline_source(
    payload: Mapping[str, object],
) -> ReaderEvidenceGuidelineSource:
    _require_exact_keys(
        payload,
        required={
            "guideline_version",
            "relative_path",
            "required_label_kinds",
        },
        optional={"min_independent_annotators", "source_id"},
        field_name="guideline",
    )
    kinds_raw = _require_list(
        payload["required_label_kinds"],
        "required_label_kinds",
    )
    return ReaderEvidenceGuidelineSource(
        guideline_version=_require_text(
            payload["guideline_version"],
            "guideline_version",
        ),
        relative_path=_require_text(payload["relative_path"], "relative_path"),
        required_label_kinds=tuple(
            _enum_value(HumanLabelKind, item, "required_label_kind")
            for item in kinds_raw
        ),
        min_independent_annotators=_positive_int(
            payload.get("min_independent_annotators", 2),
            "min_independent_annotators",
            minimum=2,
        ),
        source_id=_optional_text(payload.get("source_id"), "source_id") or "",
    )


def _parse_assignment_source(
    value: object,
    *,
    index: int,
) -> ReaderEvidenceAssignmentSource:
    field_name = f"assignments[{index}]"
    payload = _require_mapping(value, field_name)
    _require_exact_keys(
        payload,
        required={"document_id", "annotator_ids", "adjudicator_id"},
        optional={"source_id"},
        field_name=field_name,
    )
    return ReaderEvidenceAssignmentSource(
        document_id=_require_text(payload["document_id"], "document_id"),
        annotator_ids=_text_sequence(payload["annotator_ids"], "annotator_id"),
        adjudicator_id=_require_text(
            payload["adjudicator_id"],
            "adjudicator_id",
        ),
        source_id=_optional_text(payload.get("source_id"), "source_id") or "",
    )


def _canonical_value(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        dataclass_value = cast(Any, value)
        return {
            field.name: _canonical_value(getattr(dataclass_value, field.name))
            for field in fields(dataclass_value)
        }
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {
            str(key): _canonical_value(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (tuple, list)):
        return [_canonical_value(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise ReaderEvidencePackError(
        f"unsupported canonical JSON value: {type(value).__name__}"
    )


def _load_json_object(path: str | Path, field_name: str) -> dict[str, object]:
    input_path = Path(path)
    try:
        value: Any = json.loads(input_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ReaderEvidencePackError(
            f"failed to load {field_name}: {exc}"
        ) from exc
    return dict(_require_mapping(value, field_name))


def _require_mapping(value: object, field_name: str) -> Mapping[str, object]:
    if not isinstance(value, dict) or any(
        not isinstance(key, str) for key in value
    ):
        raise ReaderEvidencePackError(
            f"{field_name} must be a JSON object with string keys"
        )
    return cast(Mapping[str, object], value)


def _require_list(value: object, field_name: str) -> list[object]:
    if not isinstance(value, list):
        raise ReaderEvidencePackError(f"{field_name} must be a JSON array")
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
        raise ReaderEvidencePackError(
            f"{field_name} is missing keys: {', '.join(missing)}"
        )
    if unknown:
        raise ReaderEvidencePackError(
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
        raise ReaderEvidencePackError(
            f"{field_name} must be one of: {allowed}"
        ) from exc


def _require_text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReaderEvidencePackError(
            f"{field_name} must be non-empty text"
        )
    return value


def _optional_text(value: object, field_name: str) -> str | None:
    if value is None:
        return None
    return _require_text(value, field_name)


def _require_bool(value: object, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise ReaderEvidencePackError(f"{field_name} must be a boolean")
    return value


def _positive_int(value: object, field_name: str, *, minimum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ReaderEvidencePackError(
            f"{field_name} must be an integer >= {minimum}"
        )
    return value


def _text_sequence(value: object, field_name: str) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise ReaderEvidencePackError(f"{field_name} values must be an array")
    return tuple(_require_text(item, field_name) for item in value)


def _unique_sorted_text(
    values: Iterable[str],
    field_name: str,
) -> tuple[str, ...]:
    items = tuple(values)
    for item in items:
        _require_text(item, field_name)
    if len(set(items)) != len(items):
        raise ReaderEvidencePackError(
            f"{field_name} values must be unique"
        )
    return tuple(sorted(items))


def _normalize_relative_path(value: str) -> str:
    _require_text(value, "relative_path")
    if "\\" in value:
        raise ReaderEvidencePackError(
            "relative_path must use POSIX separators"
        )
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or ".." in path.parts:
        raise ReaderEvidencePackError(
            "relative_path must remain inside the local root"
        )
    normalized = path.as_posix()
    if normalized in {".", ""}:
        raise ReaderEvidencePackError("relative_path must reference a file")
    return normalized


def _resolve_local_file(
    root: Path,
    relative_path: str,
    *,
    field_name: str,
) -> Path:
    normalized = _normalize_relative_path(relative_path)
    candidate = (root / normalized).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ReaderEvidencePackError(
            f"{field_name} escapes the local root"
        ) from exc
    if not candidate.is_file():
        raise ReaderEvidencePackError(
            f"{field_name} does not reference an existing file"
        )
    return candidate


def _canonical_instances(
    values: Iterable[T],
    expected_type: type[T],
    *,
    key: Callable[[T], str],
    field_name: str,
) -> tuple[T, ...]:
    items = tuple(values)
    if not items or any(not isinstance(item, expected_type) for item in items):
        raise ReaderEvidencePackError(
            f"{field_name} require at least one {expected_type.__name__}"
        )
    ordered = tuple(sorted(items, key=key))
    keys = tuple(key(item) for item in ordered)
    if len(set(keys)) != len(keys):
        raise ReaderEvidencePackError(f"{field_name} keys must be unique")
    return ordered
