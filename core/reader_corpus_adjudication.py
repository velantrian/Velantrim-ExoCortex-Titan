"""Verifiable corpus packages and human-label adjudication for PR-RDR-11.

The contracts describe local evaluation documents without embedding their raw
text in labels or receipts. Independent annotator sets are compared explicitly;
every disagreement must be partitioned into an adjudication resolution before a
human-labelled evaluation manifest can be built.

This module grants no model, query, memory, Canon, graph, policy, TruthGate,
Write Gate, tool, or live-integration authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
from pathlib import Path, PurePosixPath
import re
from typing import Iterable, TypeAlias

from core.critical_exceptions import ExceptionCategory
from core.knowledge_capsule import ClaimModality, SourceSpan
from core.reader_core_contracts import RelationKind, stable_reader_core_id
from core.reader_evaluation import (
    EvaluationCorpusKind,
    EvaluationCorpusManifest,
    ReaderEvaluationCaseManifest,
)

CORPUS_PACKAGE_SCHEMA_VERSION = "reader-core.corpus-package.v1"
HUMAN_LABEL_SCHEMA_VERSION = "reader-core.human-labels.v1"
ADJUDICATION_SCHEMA_VERSION = "reader-core.adjudication.v1"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class ReaderCorpusError(ValueError):
    """Raised when corpus, label, or adjudication invariants are invalid."""


class CorpusUsageBasis(str, Enum):
    SYNTHETIC = "synthetic"
    OWNED = "owned"
    PUBLIC_DOMAIN = "public_domain"
    PERMISSIVE_LICENSE = "permissive_license"
    AUTHORIZED_PRIVATE = "authorized_private"


class CorpusPrivacyClass(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    SENSITIVE = "sensitive"


class LabelSetRole(str, Enum):
    ANNOTATOR = "annotator"
    ADJUDICATED = "adjudicated"


class HumanLabelKind(str, Enum):
    CLAIM = "claim"
    EXCEPTION = "exception"
    RELATION = "relation"
    QUALIFIER = "qualifier"


class QualifierKind(str, Enum):
    CONDITION = "condition"
    SCOPE = "scope"
    EXCLUSION = "exclusion"
    APPROVAL = "approval"
    TEMPORAL = "temporal"
    VERSION = "version"
    UNCERTAINTY = "uncertainty"
    OTHER = "other"


@dataclass(frozen=True, slots=True)
class CorpusDocumentDescriptor:
    """Content-addressed local document descriptor without raw document text."""

    document_id: str
    relative_path: str
    source_revision: str
    content_sha256: str
    byte_size: int
    char_count: int
    media_type: str
    usage_basis: CorpusUsageBasis
    rights_reference: str
    privacy_class: CorpusPrivacyClass
    redistribution_allowed: bool
    descriptor_id: str = ""

    def __post_init__(self) -> None:
        for name in (
            "document_id",
            "relative_path",
            "source_revision",
            "content_sha256",
            "media_type",
            "rights_reference",
        ):
            _require_text(getattr(self, name), name)
        normalized_path = _normalize_relative_path(self.relative_path)
        object.__setattr__(self, "relative_path", normalized_path)
        _require_sha256(self.content_sha256, "content_sha256")
        if self.source_revision != self.content_sha256:
            raise ReaderCorpusError(
                "source_revision must equal the exact content SHA-256"
            )
        _nonnegative_int(self.byte_size, "byte_size")
        _nonnegative_int(self.char_count, "char_count")
        if self.byte_size == 0 or self.char_count == 0:
            raise ReaderCorpusError("corpus documents must not be empty")
        if not isinstance(self.usage_basis, CorpusUsageBasis):
            raise ReaderCorpusError("usage_basis must be a CorpusUsageBasis")
        if not isinstance(self.privacy_class, CorpusPrivacyClass):
            raise ReaderCorpusError(
                "privacy_class must be a CorpusPrivacyClass"
            )
        if not isinstance(self.redistribution_allowed, bool):
            raise ReaderCorpusError(
                "redistribution_allowed must be a boolean"
            )
        if (
            self.usage_basis is CorpusUsageBasis.AUTHORIZED_PRIVATE
            and self.redistribution_allowed
        ):
            raise ReaderCorpusError(
                "authorized private documents cannot be marked redistributable"
            )
        if (
            self.privacy_class is CorpusPrivacyClass.SENSITIVE
            and self.redistribution_allowed
        ):
            raise ReaderCorpusError(
                "sensitive documents cannot be marked redistributable"
            )
        expected = stable_reader_core_id(
            "reader-corpus-document-descriptor",
            self.identity_payload(include_id=False),
        )
        if self.descriptor_id:
            if self.descriptor_id != expected:
                raise ReaderCorpusError(
                    "descriptor_id does not match descriptor content"
                )
        else:
            object.__setattr__(self, "descriptor_id", expected)

    @classmethod
    def from_file(
        cls,
        *,
        root: str | Path,
        relative_path: str,
        document_id: str,
        media_type: str,
        usage_basis: CorpusUsageBasis,
        rights_reference: str,
        privacy_class: CorpusPrivacyClass,
        redistribution_allowed: bool,
    ) -> CorpusDocumentDescriptor:
        normalized = _normalize_relative_path(relative_path)
        source = _resolve_corpus_file(root, normalized)
        raw = source.read_bytes()
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ReaderCorpusError(
                f"corpus document must be valid UTF-8: {normalized}"
            ) from exc
        digest = sha256(raw).hexdigest()
        return cls(
            document_id=document_id,
            relative_path=normalized,
            source_revision=digest,
            content_sha256=digest,
            byte_size=len(raw),
            char_count=len(text),
            media_type=media_type,
            usage_basis=usage_basis,
            rights_reference=rights_reference,
            privacy_class=privacy_class,
            redistribution_allowed=redistribution_allowed,
        )

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "document_id": self.document_id,
            "relative_path": self.relative_path,
            "source_revision": self.source_revision,
            "content_sha256": self.content_sha256,
            "byte_size": self.byte_size,
            "char_count": self.char_count,
            "media_type": self.media_type,
            "usage_basis": self.usage_basis.value,
            "rights_reference": self.rights_reference,
            "privacy_class": self.privacy_class.value,
            "redistribution_allowed": self.redistribution_allowed,
        }
        if include_id:
            payload["descriptor_id"] = self.descriptor_id
        return payload

    def verify_file(self, root: str | Path) -> CorpusDocumentVerification:
        source = _resolve_corpus_file(root, self.relative_path)
        raw = source.read_bytes()
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ReaderCorpusError(
                f"corpus document must be valid UTF-8: {self.relative_path}"
            ) from exc
        observed_sha256 = sha256(raw).hexdigest()
        if observed_sha256 != self.content_sha256:
            raise ReaderCorpusError(
                f"document hash mismatch: {self.document_id}"
            )
        if len(raw) != self.byte_size:
            raise ReaderCorpusError(
                f"document byte size mismatch: {self.document_id}"
            )
        if len(text) != self.char_count:
            raise ReaderCorpusError(
                f"document character count mismatch: {self.document_id}"
            )
        return CorpusDocumentVerification.create(
            descriptor_id=self.descriptor_id,
            document_id=self.document_id,
            content_sha256=observed_sha256,
            byte_size=len(raw),
            char_count=len(text),
        )


@dataclass(frozen=True, slots=True)
class CorpusDocumentVerification:
    descriptor_id: str
    document_id: str
    content_sha256: str
    byte_size: int
    char_count: int
    verification_id: str

    def __post_init__(self) -> None:
        _require_text(self.descriptor_id, "descriptor_id")
        _require_text(self.document_id, "document_id")
        _require_sha256(self.content_sha256, "content_sha256")
        _nonnegative_int(self.byte_size, "byte_size")
        _nonnegative_int(self.char_count, "char_count")
        if self.byte_size == 0 or self.char_count == 0:
            raise ReaderCorpusError("verified documents must not be empty")
        expected = stable_reader_core_id(
            "reader-corpus-document-verification",
            {
                "descriptor_id": self.descriptor_id,
                "document_id": self.document_id,
                "content_sha256": self.content_sha256,
                "byte_size": self.byte_size,
                "char_count": self.char_count,
            },
        )
        if self.verification_id != expected:
            raise ReaderCorpusError(
                "verification_id does not match verification content"
            )

    @classmethod
    def create(
        cls,
        *,
        descriptor_id: str,
        document_id: str,
        content_sha256: str,
        byte_size: int,
        char_count: int,
    ) -> CorpusDocumentVerification:
        verification_id = stable_reader_core_id(
            "reader-corpus-document-verification",
            {
                "descriptor_id": descriptor_id,
                "document_id": document_id,
                "content_sha256": content_sha256,
                "byte_size": byte_size,
                "char_count": char_count,
            },
        )
        return cls(
            descriptor_id=descriptor_id,
            document_id=document_id,
            content_sha256=content_sha256,
            byte_size=byte_size,
            char_count=char_count,
            verification_id=verification_id,
        )


@dataclass(frozen=True, slots=True)
class CorpusPackageManifest:
    corpus_name: str
    corpus_version: str
    documents: tuple[CorpusDocumentDescriptor, ...]
    tags: tuple[str, ...] = ()
    schema_version: str = CORPUS_PACKAGE_SCHEMA_VERSION
    package_id: str = ""

    def __post_init__(self) -> None:
        _require_text(self.corpus_name, "corpus_name")
        _require_text(self.corpus_version, "corpus_version")
        if self.schema_version != CORPUS_PACKAGE_SCHEMA_VERSION:
            raise ReaderCorpusError("unsupported corpus package schema")
        documents = tuple(self.documents)
        if not documents or any(
            not isinstance(item, CorpusDocumentDescriptor)
            for item in documents
        ):
            raise ReaderCorpusError(
                "documents require at least one CorpusDocumentDescriptor"
            )
        ordered = tuple(sorted(documents, key=lambda item: item.document_id))
        if len({item.document_id for item in ordered}) != len(ordered):
            raise ReaderCorpusError("document IDs must be unique")
        if len({item.relative_path for item in ordered}) != len(ordered):
            raise ReaderCorpusError("document paths must be unique")
        tags = _unique_sorted_text(self.tags, "tag")
        object.__setattr__(self, "documents", ordered)
        object.__setattr__(self, "tags", tags)
        expected = stable_reader_core_id(
            "reader-corpus-package",
            self.identity_payload(include_id=False),
        )
        if self.package_id:
            if self.package_id != expected:
                raise ReaderCorpusError(
                    "package_id does not match package content"
                )
        else:
            object.__setattr__(self, "package_id", expected)

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema_version": self.schema_version,
            "corpus_name": self.corpus_name,
            "corpus_version": self.corpus_version,
            "descriptor_ids": [item.descriptor_id for item in self.documents],
            "tags": list(self.tags),
        }
        if include_id:
            payload["package_id"] = self.package_id
        return payload

    def verify(self, root: str | Path) -> CorpusPackageVerificationReceipt:
        entries = tuple(document.verify_file(root) for document in self.documents)
        return CorpusPackageVerificationReceipt.create(
            package_id=self.package_id,
            entries=entries,
        )


@dataclass(frozen=True, slots=True)
class CorpusPackageVerificationReceipt:
    package_id: str
    entries: tuple[CorpusDocumentVerification, ...]
    receipt_id: str

    def __post_init__(self) -> None:
        _require_text(self.package_id, "package_id")
        entries = tuple(self.entries)
        if not entries or any(
            not isinstance(item, CorpusDocumentVerification) for item in entries
        ):
            raise ReaderCorpusError(
                "entries require CorpusDocumentVerification values"
            )
        ordered = tuple(sorted(entries, key=lambda item: item.document_id))
        if entries != ordered:
            raise ReaderCorpusError("verification entries must be canonical")
        if len({item.document_id for item in entries}) != len(entries):
            raise ReaderCorpusError("verified document IDs must be unique")
        object.__setattr__(self, "entries", entries)
        expected = stable_reader_core_id(
            "reader-corpus-package-verification",
            {
                "package_id": self.package_id,
                "verification_ids": [item.verification_id for item in entries],
            },
        )
        if self.receipt_id != expected:
            raise ReaderCorpusError(
                "receipt_id does not match package verification content"
            )

    @classmethod
    def create(
        cls,
        *,
        package_id: str,
        entries: Iterable[CorpusDocumentVerification],
    ) -> CorpusPackageVerificationReceipt:
        ordered = tuple(sorted(entries, key=lambda item: item.document_id))
        receipt_id = stable_reader_core_id(
            "reader-corpus-package-verification",
            {
                "package_id": package_id,
                "verification_ids": [item.verification_id for item in ordered],
            },
        )
        return cls(package_id=package_id, entries=ordered, receipt_id=receipt_id)


@dataclass(frozen=True, slots=True)
class HumanClaimLabel:
    label_id: str
    document_id: str
    source_revision: str
    modality: ClaimModality
    source_spans: tuple[SourceSpan, ...]
    qualifier_codes: tuple[str, ...] = ()
    applicability_codes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _validate_label_identity(self.document_id, self.source_revision)
        if not isinstance(self.modality, ClaimModality):
            raise ReaderCorpusError("modality must be a ClaimModality")
        spans = _validated_spans(
            self.source_spans,
            document_id=self.document_id,
            source_revision=self.source_revision,
            field_name="claim source span",
        )
        qualifiers = _unique_sorted_text(self.qualifier_codes, "qualifier_code")
        applicability = _unique_sorted_text(
            self.applicability_codes,
            "applicability_code",
        )
        object.__setattr__(self, "source_spans", spans)
        object.__setattr__(self, "qualifier_codes", qualifiers)
        object.__setattr__(self, "applicability_codes", applicability)
        expected = stable_reader_core_id(
            "reader-human-claim-label",
            self.identity_payload(include_id=False),
        )
        _verify_or_set_label_id(self, expected)

    @property
    def kind(self) -> HumanLabelKind:
        return HumanLabelKind.CLAIM

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "document_id": self.document_id,
            "source_revision": self.source_revision,
            "modality": self.modality.value,
            "source_spans": [span.identity_payload() for span in self.source_spans],
            "qualifier_codes": list(self.qualifier_codes),
            "applicability_codes": list(self.applicability_codes),
        }
        if include_id:
            payload["label_id"] = self.label_id
        return payload

    @classmethod
    def create(
        cls,
        *,
        document_id: str,
        source_revision: str,
        modality: ClaimModality,
        source_spans: Iterable[SourceSpan],
        qualifier_codes: Iterable[str] = (),
        applicability_codes: Iterable[str] = (),
    ) -> HumanClaimLabel:
        spans = tuple(source_spans)
        qualifiers = tuple(sorted(qualifier_codes))
        applicability = tuple(sorted(applicability_codes))
        payload = {
            "document_id": document_id,
            "source_revision": source_revision,
            "modality": modality.value,
            "source_spans": [span.identity_payload() for span in spans],
            "qualifier_codes": list(qualifiers),
            "applicability_codes": list(applicability),
        }
        return cls(
            label_id=stable_reader_core_id("reader-human-claim-label", payload),
            document_id=document_id,
            source_revision=source_revision,
            modality=modality,
            source_spans=spans,
            qualifier_codes=qualifiers,
            applicability_codes=applicability,
        )


@dataclass(frozen=True, slots=True)
class HumanExceptionLabel:
    label_id: str
    document_id: str
    source_revision: str
    category: ExceptionCategory
    trigger_span: SourceSpan
    statement_span: SourceSpan
    target_claim_label_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _validate_label_identity(self.document_id, self.source_revision)
        if not isinstance(self.category, ExceptionCategory):
            raise ReaderCorpusError("category must be an ExceptionCategory")
        _validate_one_span(
            self.trigger_span,
            document_id=self.document_id,
            source_revision=self.source_revision,
            field_name="trigger_span",
        )
        _validate_one_span(
            self.statement_span,
            document_id=self.document_id,
            source_revision=self.source_revision,
            field_name="statement_span",
        )
        if (
            self.trigger_span.start_offset < self.statement_span.start_offset
            or self.trigger_span.end_offset > self.statement_span.end_offset
        ):
            raise ReaderCorpusError(
                "trigger_span must be contained in statement_span"
            )
        targets = _unique_sorted_text(
            self.target_claim_label_ids,
            "target_claim_label_id",
        )
        if not targets:
            raise ReaderCorpusError(
                "human exception labels require at least one target claim"
            )
        object.__setattr__(self, "target_claim_label_ids", targets)
        expected = stable_reader_core_id(
            "reader-human-exception-label",
            self.identity_payload(include_id=False),
        )
        _verify_or_set_label_id(self, expected)

    @property
    def kind(self) -> HumanLabelKind:
        return HumanLabelKind.EXCEPTION

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "document_id": self.document_id,
            "source_revision": self.source_revision,
            "category": self.category.value,
            "trigger_span": self.trigger_span.identity_payload(),
            "statement_span": self.statement_span.identity_payload(),
            "target_claim_label_ids": list(self.target_claim_label_ids),
        }
        if include_id:
            payload["label_id"] = self.label_id
        return payload

    @classmethod
    def create(
        cls,
        *,
        document_id: str,
        source_revision: str,
        category: ExceptionCategory,
        trigger_span: SourceSpan,
        statement_span: SourceSpan,
        target_claim_label_ids: Iterable[str],
    ) -> HumanExceptionLabel:
        targets = tuple(sorted(target_claim_label_ids))
        payload = {
            "document_id": document_id,
            "source_revision": source_revision,
            "category": category.value,
            "trigger_span": trigger_span.identity_payload(),
            "statement_span": statement_span.identity_payload(),
            "target_claim_label_ids": list(targets),
        }
        return cls(
            label_id=stable_reader_core_id("reader-human-exception-label", payload),
            document_id=document_id,
            source_revision=source_revision,
            category=category,
            trigger_span=trigger_span,
            statement_span=statement_span,
            target_claim_label_ids=targets,
        )


@dataclass(frozen=True, slots=True)
class HumanRelationLabel:
    label_id: str
    document_id: str
    source_revision: str
    relation_kind: RelationKind
    source_claim_label_id: str
    target_claim_label_id: str
    evidence_spans: tuple[SourceSpan, ...]

    def __post_init__(self) -> None:
        _validate_label_identity(self.document_id, self.source_revision)
        if not isinstance(self.relation_kind, RelationKind):
            raise ReaderCorpusError("relation_kind must be a RelationKind")
        _require_text(self.source_claim_label_id, "source_claim_label_id")
        _require_text(self.target_claim_label_id, "target_claim_label_id")
        if self.source_claim_label_id == self.target_claim_label_id:
            raise ReaderCorpusError("relation self-loops are forbidden")
        spans = _validated_spans(
            self.evidence_spans,
            document_id=self.document_id,
            source_revision=self.source_revision,
            field_name="relation evidence span",
        )
        object.__setattr__(self, "evidence_spans", spans)
        expected = stable_reader_core_id(
            "reader-human-relation-label",
            self.identity_payload(include_id=False),
        )
        _verify_or_set_label_id(self, expected)

    @property
    def kind(self) -> HumanLabelKind:
        return HumanLabelKind.RELATION

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "document_id": self.document_id,
            "source_revision": self.source_revision,
            "relation_kind": self.relation_kind.value,
            "source_claim_label_id": self.source_claim_label_id,
            "target_claim_label_id": self.target_claim_label_id,
            "evidence_spans": [span.identity_payload() for span in self.evidence_spans],
        }
        if include_id:
            payload["label_id"] = self.label_id
        return payload

    @classmethod
    def create(
        cls,
        *,
        document_id: str,
        source_revision: str,
        relation_kind: RelationKind,
        source_claim_label_id: str,
        target_claim_label_id: str,
        evidence_spans: Iterable[SourceSpan],
    ) -> HumanRelationLabel:
        spans = tuple(evidence_spans)
        payload = {
            "document_id": document_id,
            "source_revision": source_revision,
            "relation_kind": relation_kind.value,
            "source_claim_label_id": source_claim_label_id,
            "target_claim_label_id": target_claim_label_id,
            "evidence_spans": [span.identity_payload() for span in spans],
        }
        return cls(
            label_id=stable_reader_core_id("reader-human-relation-label", payload),
            document_id=document_id,
            source_revision=source_revision,
            relation_kind=relation_kind,
            source_claim_label_id=source_claim_label_id,
            target_claim_label_id=target_claim_label_id,
            evidence_spans=spans,
        )


@dataclass(frozen=True, slots=True)
class HumanQualifierLabel:
    label_id: str
    document_id: str
    source_revision: str
    qualifier_kind: QualifierKind
    target_claim_label_id: str
    source_span: SourceSpan

    def __post_init__(self) -> None:
        _validate_label_identity(self.document_id, self.source_revision)
        if not isinstance(self.qualifier_kind, QualifierKind):
            raise ReaderCorpusError("qualifier_kind must be a QualifierKind")
        _require_text(self.target_claim_label_id, "target_claim_label_id")
        _validate_one_span(
            self.source_span,
            document_id=self.document_id,
            source_revision=self.source_revision,
            field_name="qualifier source span",
        )
        expected = stable_reader_core_id(
            "reader-human-qualifier-label",
            self.identity_payload(include_id=False),
        )
        _verify_or_set_label_id(self, expected)

    @property
    def kind(self) -> HumanLabelKind:
        return HumanLabelKind.QUALIFIER

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "document_id": self.document_id,
            "source_revision": self.source_revision,
            "qualifier_kind": self.qualifier_kind.value,
            "target_claim_label_id": self.target_claim_label_id,
            "source_span": self.source_span.identity_payload(),
        }
        if include_id:
            payload["label_id"] = self.label_id
        return payload

    @classmethod
    def create(
        cls,
        *,
        document_id: str,
        source_revision: str,
        qualifier_kind: QualifierKind,
        target_claim_label_id: str,
        source_span: SourceSpan,
    ) -> HumanQualifierLabel:
        payload = {
            "document_id": document_id,
            "source_revision": source_revision,
            "qualifier_kind": qualifier_kind.value,
            "target_claim_label_id": target_claim_label_id,
            "source_span": source_span.identity_payload(),
        }
        return cls(
            label_id=stable_reader_core_id("reader-human-qualifier-label", payload),
            document_id=document_id,
            source_revision=source_revision,
            qualifier_kind=qualifier_kind,
            target_claim_label_id=target_claim_label_id,
            source_span=source_span,
        )


HumanLabel: TypeAlias = (
    HumanClaimLabel
    | HumanExceptionLabel
    | HumanRelationLabel
    | HumanQualifierLabel
)


@dataclass(frozen=True, slots=True)
class HumanLabelSet:
    document_descriptor_id: str
    document_id: str
    source_revision: str
    annotator_id: str
    guideline_version: str
    label_version: str
    role: LabelSetRole
    claims: tuple[HumanClaimLabel, ...]
    exceptions: tuple[HumanExceptionLabel, ...] = ()
    relations: tuple[HumanRelationLabel, ...] = ()
    qualifiers: tuple[HumanQualifierLabel, ...] = ()
    schema_version: str = HUMAN_LABEL_SCHEMA_VERSION
    label_set_id: str = ""

    def __post_init__(self) -> None:
        for name in (
            "document_descriptor_id",
            "document_id",
            "source_revision",
            "annotator_id",
            "guideline_version",
            "label_version",
        ):
            _require_text(getattr(self, name), name)
        if self.schema_version != HUMAN_LABEL_SCHEMA_VERSION:
            raise ReaderCorpusError("unsupported human-label schema")
        if not isinstance(self.role, LabelSetRole):
            raise ReaderCorpusError("role must be a LabelSetRole")
        claims = _canonical_labels(self.claims, HumanClaimLabel, "claims")
        exceptions = _canonical_labels(
            self.exceptions,
            HumanExceptionLabel,
            "exceptions",
        )
        relations = _canonical_labels(
            self.relations,
            HumanRelationLabel,
            "relations",
        )
        qualifiers = _canonical_labels(
            self.qualifiers,
            HumanQualifierLabel,
            "qualifiers",
        )
        if not claims:
            raise ReaderCorpusError("human label sets require at least one claim")
        all_labels: tuple[HumanLabel, ...] = (
            *claims,
            *exceptions,
            *relations,
            *qualifiers,
        )
        if len({label.label_id for label in all_labels}) != len(all_labels):
            raise ReaderCorpusError("label IDs must be unique across a label set")
        for label in all_labels:
            if (
                label.document_id != self.document_id
                or label.source_revision != self.source_revision
            ):
                raise ReaderCorpusError(
                    "every label must match label-set document and revision"
                )
        claim_ids = {claim.label_id for claim in claims}
        for exception in exceptions:
            if not set(exception.target_claim_label_ids).issubset(claim_ids):
                raise ReaderCorpusError(
                    "exception targets must reference claims in the same label set"
                )
        for relation in relations:
            if (
                relation.source_claim_label_id not in claim_ids
                or relation.target_claim_label_id not in claim_ids
            ):
                raise ReaderCorpusError(
                    "relation endpoints must reference claims in the same label set"
                )
        for qualifier in qualifiers:
            if qualifier.target_claim_label_id not in claim_ids:
                raise ReaderCorpusError(
                    "qualifier target must reference a claim in the same label set"
                )
        object.__setattr__(self, "claims", claims)
        object.__setattr__(self, "exceptions", exceptions)
        object.__setattr__(self, "relations", relations)
        object.__setattr__(self, "qualifiers", qualifiers)
        expected = stable_reader_core_id(
            "reader-human-label-set",
            self.identity_payload(include_id=False),
        )
        if self.label_set_id:
            if self.label_set_id != expected:
                raise ReaderCorpusError(
                    "label_set_id does not match label-set content"
                )
        else:
            object.__setattr__(self, "label_set_id", expected)

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema_version": self.schema_version,
            "document_descriptor_id": self.document_descriptor_id,
            "document_id": self.document_id,
            "source_revision": self.source_revision,
            "annotator_id": self.annotator_id,
            "guideline_version": self.guideline_version,
            "label_version": self.label_version,
            "role": self.role.value,
            "claim_ids": [label.label_id for label in self.claims],
            "exception_ids": [label.label_id for label in self.exceptions],
            "relation_ids": [label.label_id for label in self.relations],
            "qualifier_ids": [label.label_id for label in self.qualifiers],
        }
        if include_id:
            payload["label_set_id"] = self.label_set_id
        return payload

    def labels_by_kind(self, kind: HumanLabelKind) -> tuple[HumanLabel, ...]:
        if kind is HumanLabelKind.CLAIM:
            return self.claims
        if kind is HumanLabelKind.EXCEPTION:
            return self.exceptions
        if kind is HumanLabelKind.RELATION:
            return self.relations
        return self.qualifiers

    def verify_spans(
        self,
        *,
        root: str | Path,
        descriptor: CorpusDocumentDescriptor,
    ) -> HumanLabelSetVerificationReceipt:
        if descriptor.descriptor_id != self.document_descriptor_id:
            raise ReaderCorpusError(
                "descriptor must match label-set document_descriptor_id"
            )
        if (
            descriptor.document_id != self.document_id
            or descriptor.source_revision != self.source_revision
        ):
            raise ReaderCorpusError(
                "descriptor identity must match label-set document and revision"
            )
        descriptor.verify_file(root)
        text = _resolve_corpus_file(root, descriptor.relative_path).read_text(
            encoding="utf-8"
        )
        spans = tuple(_iter_label_spans(self))
        for span in spans:
            if not span.verify(text):
                raise ReaderCorpusError(
                    f"label span failed content verification: {span.span_id}"
                )
        return HumanLabelSetVerificationReceipt.create(
            label_set_id=self.label_set_id,
            descriptor_id=descriptor.descriptor_id,
            verified_span_ids=tuple(sorted(span.span_id for span in spans)),
        )


@dataclass(frozen=True, slots=True)
class HumanLabelSetVerificationReceipt:
    label_set_id: str
    descriptor_id: str
    verified_span_ids: tuple[str, ...]
    receipt_id: str

    def __post_init__(self) -> None:
        _require_text(self.label_set_id, "label_set_id")
        _require_text(self.descriptor_id, "descriptor_id")
        spans = _unique_sorted_text(self.verified_span_ids, "verified_span_id")
        if not spans:
            raise ReaderCorpusError("at least one label span must be verified")
        object.__setattr__(self, "verified_span_ids", spans)
        expected = stable_reader_core_id(
            "reader-human-label-set-verification",
            {
                "label_set_id": self.label_set_id,
                "descriptor_id": self.descriptor_id,
                "verified_span_ids": list(spans),
            },
        )
        if self.receipt_id != expected:
            raise ReaderCorpusError(
                "receipt_id does not match label verification content"
            )

    @classmethod
    def create(
        cls,
        *,
        label_set_id: str,
        descriptor_id: str,
        verified_span_ids: Iterable[str],
    ) -> HumanLabelSetVerificationReceipt:
        spans = tuple(sorted(set(verified_span_ids)))
        receipt_id = stable_reader_core_id(
            "reader-human-label-set-verification",
            {
                "label_set_id": label_set_id,
                "descriptor_id": descriptor_id,
                "verified_span_ids": list(spans),
            },
        )
        return cls(
            label_set_id=label_set_id,
            descriptor_id=descriptor_id,
            verified_span_ids=spans,
            receipt_id=receipt_id,
        )


@dataclass(frozen=True, slots=True)
class AdjudicationResolution:
    kind: HumanLabelKind
    candidate_label_ids: tuple[str, ...]
    resolved_label_ids: tuple[str, ...]
    resolution_code: str
    rationale_code: str
    resolution_id: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.kind, HumanLabelKind):
            raise ReaderCorpusError("kind must be a HumanLabelKind")
        candidates = _unique_sorted_text(
            self.candidate_label_ids,
            "candidate_label_id",
        )
        if not candidates:
            raise ReaderCorpusError(
                "adjudication resolutions require candidate labels"
            )
        resolved = _unique_sorted_text(
            self.resolved_label_ids,
            "resolved_label_id",
        )
        _require_text(self.resolution_code, "resolution_code")
        _require_text(self.rationale_code, "rationale_code")
        object.__setattr__(self, "candidate_label_ids", candidates)
        object.__setattr__(self, "resolved_label_ids", resolved)
        expected = stable_reader_core_id(
            "reader-label-adjudication-resolution",
            self.identity_payload(include_id=False),
        )
        if self.resolution_id:
            if self.resolution_id != expected:
                raise ReaderCorpusError(
                    "resolution_id does not match resolution content"
                )
        else:
            object.__setattr__(self, "resolution_id", expected)

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "kind": self.kind.value,
            "candidate_label_ids": list(self.candidate_label_ids),
            "resolved_label_ids": list(self.resolved_label_ids),
            "resolution_code": self.resolution_code,
            "rationale_code": self.rationale_code,
        }
        if include_id:
            payload["resolution_id"] = self.resolution_id
        return payload


@dataclass(frozen=True, slots=True)
class HumanLabelAdjudication:
    source_label_sets: tuple[HumanLabelSet, ...]
    adjudicator_id: str
    adjudicated_label_set: HumanLabelSet
    resolutions: tuple[AdjudicationResolution, ...]
    schema_version: str = ADJUDICATION_SCHEMA_VERSION
    adjudication_id: str = ""

    def __post_init__(self) -> None:
        if self.schema_version != ADJUDICATION_SCHEMA_VERSION:
            raise ReaderCorpusError("unsupported adjudication schema")
        sources = tuple(self.source_label_sets)
        if len(sources) < 2 or any(
            not isinstance(item, HumanLabelSet) for item in sources
        ):
            raise ReaderCorpusError(
                "adjudication requires at least two HumanLabelSet inputs"
            )
        ordered_sources = tuple(sorted(sources, key=lambda item: item.label_set_id))
        if sources != ordered_sources:
            raise ReaderCorpusError("source label sets must be canonical")
        if any(item.role is not LabelSetRole.ANNOTATOR for item in sources):
            raise ReaderCorpusError(
                "source label sets must have annotator role"
            )
        annotators = {item.annotator_id for item in sources}
        if len(annotators) != len(sources):
            raise ReaderCorpusError(
                "source label sets require distinct annotator IDs"
            )
        _require_text(self.adjudicator_id, "adjudicator_id")
        if self.adjudicator_id in annotators:
            raise ReaderCorpusError(
                "adjudicator must be independent from source annotators"
            )
        if not isinstance(self.adjudicated_label_set, HumanLabelSet):
            raise ReaderCorpusError(
                "adjudicated_label_set must be a HumanLabelSet"
            )
        final = self.adjudicated_label_set
        if final.role is not LabelSetRole.ADJUDICATED:
            raise ReaderCorpusError(
                "adjudicated label set must have adjudicated role"
            )
        if final.annotator_id != self.adjudicator_id:
            raise ReaderCorpusError(
                "adjudicated label-set annotator_id must equal adjudicator_id"
            )
        identity = (
            sources[0].document_descriptor_id,
            sources[0].document_id,
            sources[0].source_revision,
            sources[0].guideline_version,
            sources[0].label_version,
        )
        for item in (*sources[1:], final):
            candidate_identity = (
                item.document_descriptor_id,
                item.document_id,
                item.source_revision,
                item.guideline_version,
                item.label_version,
            )
            if candidate_identity != identity:
                raise ReaderCorpusError(
                    "all label sets must share document and label policy identity"
                )
        resolutions = tuple(self.resolutions)
        if any(
            not isinstance(item, AdjudicationResolution) for item in resolutions
        ):
            raise ReaderCorpusError(
                "resolutions require AdjudicationResolution values"
            )
        ordered_resolutions = tuple(
            sorted(resolutions, key=lambda item: item.resolution_id)
        )
        if resolutions != ordered_resolutions:
            raise ReaderCorpusError("resolutions must use canonical ordering")
        if len({item.resolution_id for item in resolutions}) != len(resolutions):
            raise ReaderCorpusError("resolution IDs must be unique")
        self._validate_disagreement_partition(sources, final, resolutions)
        object.__setattr__(self, "source_label_sets", sources)
        object.__setattr__(self, "resolutions", resolutions)
        expected = stable_reader_core_id(
            "reader-human-label-adjudication",
            self.identity_payload(include_id=False),
        )
        if self.adjudication_id:
            if self.adjudication_id != expected:
                raise ReaderCorpusError(
                    "adjudication_id does not match adjudication content"
                )
        else:
            object.__setattr__(self, "adjudication_id", expected)

    @staticmethod
    def _validate_disagreement_partition(
        sources: tuple[HumanLabelSet, ...],
        final: HumanLabelSet,
        resolutions: tuple[AdjudicationResolution, ...],
    ) -> None:
        candidate_seen: set[str] = set()
        resolved_seen: set[str] = set()
        for kind in HumanLabelKind:
            source_sets = [
                {label.label_id for label in source.labels_by_kind(kind)}
                for source in sources
            ]
            common = set.intersection(*source_sets)
            union = set.union(*source_sets)
            disputed = union - common
            final_ids = {
                label.label_id for label in final.labels_by_kind(kind)
            }
            if not common.issubset(final_ids):
                raise ReaderCorpusError(
                    "labels agreed by all annotators must remain in adjudicated set"
                )
            kind_resolutions = [
                resolution for resolution in resolutions if resolution.kind is kind
            ]
            partition_candidates: set[str] = set()
            partition_resolved: set[str] = set()
            for resolution in kind_resolutions:
                candidate_ids = set(resolution.candidate_label_ids)
                resolved_ids = set(resolution.resolved_label_ids)
                if candidate_ids & candidate_seen:
                    raise ReaderCorpusError(
                        "candidate labels cannot appear in multiple resolutions"
                    )
                if resolved_ids & resolved_seen:
                    raise ReaderCorpusError(
                        "resolved labels cannot appear in multiple resolutions"
                    )
                if not candidate_ids.issubset(disputed):
                    raise ReaderCorpusError(
                        "resolution candidates must be disputed labels of the same kind"
                    )
                if not resolved_ids.issubset(final_ids - common):
                    raise ReaderCorpusError(
                        "resolution outputs must be non-common final labels of the same kind"
                    )
                candidate_seen.update(candidate_ids)
                resolved_seen.update(resolved_ids)
                partition_candidates.update(candidate_ids)
                partition_resolved.update(resolved_ids)
            if partition_candidates != disputed:
                raise ReaderCorpusError(
                    "every disputed label must be resolved exactly once"
                )
            if partition_resolved != final_ids - common:
                raise ReaderCorpusError(
                    "every non-common final label must come from one resolution"
                )

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema_version": self.schema_version,
            "source_label_set_ids": [
                item.label_set_id for item in self.source_label_sets
            ],
            "adjudicator_id": self.adjudicator_id,
            "adjudicated_label_set_id": self.adjudicated_label_set.label_set_id,
            "resolution_ids": [item.resolution_id for item in self.resolutions],
        }
        if include_id:
            payload["adjudication_id"] = self.adjudication_id
        return payload


class HumanLabelEvaluationManifestBuilder:
    """Build the RDR-09 manifest only from fully adjudicated label sets."""

    def build(
        self,
        package: CorpusPackageManifest,
        adjudications: Iterable[HumanLabelAdjudication],
    ) -> EvaluationCorpusManifest:
        if not isinstance(package, CorpusPackageManifest):
            raise ReaderCorpusError("package must be a CorpusPackageManifest")
        items = tuple(adjudications)
        if any(not isinstance(item, HumanLabelAdjudication) for item in items):
            raise ReaderCorpusError(
                "adjudications require HumanLabelAdjudication values"
            )
        by_descriptor = {
            item.adjudicated_label_set.document_descriptor_id: item
            for item in items
        }
        if len(by_descriptor) != len(items):
            raise ReaderCorpusError(
                "only one adjudication is allowed per document descriptor"
            )
        expected_ids = {item.descriptor_id for item in package.documents}
        if set(by_descriptor) != expected_ids:
            raise ReaderCorpusError(
                "adjudications must exactly cover corpus package documents"
            )
        cases: list[ReaderEvaluationCaseManifest] = []
        for descriptor in package.documents:
            label_set = by_descriptor[descriptor.descriptor_id].adjudicated_label_set
            expected_source_span_count = sum(
                len(claim.source_spans) for claim in label_set.claims
            )
            contradiction_count = sum(
                relation.relation_kind is RelationKind.CONTRADICTS
                for relation in label_set.relations
            )
            tags = tuple(
                sorted(
                    {
                        *package.tags,
                        descriptor.usage_basis.value,
                        descriptor.privacy_class.value,
                        "human-adjudicated",
                    }
                )
            )
            cases.append(
                ReaderEvaluationCaseManifest(
                    case_id=descriptor.document_id,
                    corpus_kind=EvaluationCorpusKind.HUMAN_LABELLED,
                    label_version=label_set.label_version,
                    expected_claim_count=len(label_set.claims),
                    expected_source_span_count=expected_source_span_count,
                    expected_exception_count=len(label_set.exceptions),
                    expected_relation_count=len(label_set.relations),
                    expected_contradiction_count=contradiction_count,
                    expected_qualifier_count=len(label_set.qualifiers),
                    tags=tags,
                )
            )
        return EvaluationCorpusManifest(
            corpus_name=package.corpus_name,
            corpus_version=package.corpus_version,
            cases=tuple(cases),
        )


def _resolve_corpus_file(root: str | Path, relative_path: str) -> Path:
    normalized = _normalize_relative_path(relative_path)
    root_path = Path(root).resolve(strict=True)
    if not root_path.is_dir():
        raise ReaderCorpusError("corpus root must be a directory")
    candidate = root_path
    for part in PurePosixPath(normalized).parts:
        candidate = candidate / part
        if candidate.is_symlink():
            raise ReaderCorpusError("corpus paths must not traverse symlinks")
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(root_path)
    except (OSError, ValueError) as exc:
        raise ReaderCorpusError(
            f"corpus path escapes root or does not exist: {normalized}"
        ) from exc
    if not resolved.is_file():
        raise ReaderCorpusError(f"corpus path is not a regular file: {normalized}")
    return resolved


def _normalize_relative_path(value: str) -> str:
    _require_text(value, "relative_path")
    if "\\" in value:
        raise ReaderCorpusError("relative_path must use POSIX separators")
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts:
        raise ReaderCorpusError("relative_path must be a relative POSIX path")
    if any(part in {"", ".", ".."} for part in path.parts):
        raise ReaderCorpusError("relative_path contains unsafe components")
    normalized = path.as_posix()
    if normalized != value:
        raise ReaderCorpusError("relative_path must already be normalized")
    return normalized


def _validate_label_identity(document_id: str, source_revision: str) -> None:
    _require_text(document_id, "document_id")
    _require_sha256(source_revision, "source_revision")


def _validate_one_span(
    span: SourceSpan,
    *,
    document_id: str,
    source_revision: str,
    field_name: str,
) -> None:
    if not isinstance(span, SourceSpan):
        raise ReaderCorpusError(f"{field_name} must be a SourceSpan")
    if span.document_id != document_id:
        raise ReaderCorpusError(f"{field_name} document_id mismatch")
    if span.source_revision != source_revision:
        raise ReaderCorpusError(f"{field_name} source_revision mismatch")


def _validated_spans(
    values: Iterable[SourceSpan],
    *,
    document_id: str,
    source_revision: str,
    field_name: str,
) -> tuple[SourceSpan, ...]:
    spans = tuple(values)
    if not spans:
        raise ReaderCorpusError(f"{field_name} values must not be empty")
    for span in spans:
        _validate_one_span(
            span,
            document_id=document_id,
            source_revision=source_revision,
            field_name=field_name,
        )
    if len({span.span_id for span in spans}) != len(spans):
        raise ReaderCorpusError(f"{field_name} IDs must be unique")
    ordered = tuple(
        sorted(spans, key=lambda span: (span.start_offset, span.end_offset, span.span_id))
    )
    if spans != ordered:
        raise ReaderCorpusError(f"{field_name} values must be canonical")
    return spans


def _verify_or_set_label_id(label: object, expected: str) -> None:
    actual = getattr(label, "label_id")
    if actual:
        if actual != expected:
            raise ReaderCorpusError("label_id does not match label content")
    else:
        object.__setattr__(label, "label_id", expected)


def _canonical_labels(
    values: Iterable[HumanLabel],
    expected_type: type[HumanLabel],
    field_name: str,
) -> tuple[HumanLabel, ...]:
    labels = tuple(values)
    if any(not isinstance(item, expected_type) for item in labels):
        raise ReaderCorpusError(f"{field_name} contain invalid label types")
    ordered = tuple(sorted(labels, key=lambda item: item.label_id))
    if labels != ordered:
        raise ReaderCorpusError(f"{field_name} must use canonical ordering")
    if len({item.label_id for item in labels}) != len(labels):
        raise ReaderCorpusError(f"{field_name} label IDs must be unique")
    return labels


def _iter_label_spans(label_set: HumanLabelSet) -> Iterable[SourceSpan]:
    for claim in label_set.claims:
        yield from claim.source_spans
    for exception in label_set.exceptions:
        yield exception.trigger_span
        yield exception.statement_span
    for relation in label_set.relations:
        yield from relation.evidence_spans
    for qualifier in label_set.qualifiers:
        yield qualifier.source_span


def _require_text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReaderCorpusError(f"{field_name} must be a non-empty string")
    return value


def _require_sha256(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
        raise ReaderCorpusError(
            f"{field_name} must be lowercase SHA-256 hex"
        )
    return value


def _nonnegative_int(value: int, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ReaderCorpusError(f"{field_name} must be an integer >= 0")
    return value


def _unique_sorted_text(
    values: Iterable[str],
    field_name: str,
) -> tuple[str, ...]:
    result = tuple(values)
    for value in result:
        _require_text(value, field_name)
    if len(set(result)) != len(result):
        raise ReaderCorpusError(f"{field_name} values must be unique")
    ordered = tuple(sorted(result))
    if result != ordered:
        raise ReaderCorpusError(f"{field_name} values must be sorted")
    return result


__all__ = [
    "ADJUDICATION_SCHEMA_VERSION",
    "CORPUS_PACKAGE_SCHEMA_VERSION",
    "HUMAN_LABEL_SCHEMA_VERSION",
    "AdjudicationResolution",
    "CorpusDocumentDescriptor",
    "CorpusDocumentVerification",
    "CorpusPackageManifest",
    "CorpusPackageVerificationReceipt",
    "CorpusPrivacyClass",
    "CorpusUsageBasis",
    "HumanClaimLabel",
    "HumanExceptionLabel",
    "HumanLabel",
    "HumanLabelAdjudication",
    "HumanLabelEvaluationManifestBuilder",
    "HumanLabelKind",
    "HumanLabelSet",
    "HumanLabelSetVerificationReceipt",
    "HumanQualifierLabel",
    "HumanRelationLabel",
    "LabelSetRole",
    "QualifierKind",
    "ReaderCorpusError",
]
