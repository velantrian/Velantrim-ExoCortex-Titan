"""Local-only registry and provenance validator for typed evidence references.

The module is deliberately not wired into TruthGate, SQLite storage, ingestion,
network I/O or Canon mutation. Validation runs against one immutable registry
snapshot and emits a content-minimized deterministic receipt.

This prototype does not classify evidence as independent. Snapshot identity
binds a receipt to local metadata; it is not authentication, target-domain
authorization, or evidence of claim truth.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from types import MappingProxyType
from typing import Literal, Mapping, Protocol, Sequence

from core.evidence_reference import (
    EVIDENCE_REFERENCE_POLICY_VERSION,
    EvidenceReference,
)

EVIDENCE_VALIDATION_POLICY_VERSION = "evidence-validation-v1"
EVIDENCE_REGISTRY_SNAPSHOT_SCHEMA_VERSION = 1

ValidationStatus = Literal[
    "accepted",
    "conflicting_reference_id",
    "duplicate_reference_id",
    "fragment_digest_mismatch",
    "invalid_span",
    "lineage_mismatch",
    "revoked_source",
    "source_digest_mismatch",
    "unknown_fragment",
    "unknown_source",
]

_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_DIGEST_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
_SPAN_PATTERN = re.compile(r"^chars:(\d+)-(\d+)$")


def _require_identifier(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not _IDENTIFIER_PATTERN.fullmatch(value):
        raise ValueError(
            f"{field_name} must be a safe 1-128 character technical identifier"
        )
    return value


def _require_digest(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not _DIGEST_PATTERN.fullmatch(value):
        raise ValueError(f"{field_name} must be a lower-case sha256:<64 hex> digest")
    return value


def _require_span(value: object, field_name: str = "span") -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must use the chars:<start>-<end> form")
    match = _SPAN_PATTERN.fullmatch(value)
    if match is None:
        raise ValueError(f"{field_name} must use the chars:<start>-<end> form")
    start, end = (int(part) for part in match.groups())
    if end <= start:
        raise ValueError(f"{field_name} end must be greater than start")
    return value


@dataclass(frozen=True, slots=True)
class EvidenceFragmentRecord:
    """One immutable local fragment record; raw fragment text is not retained."""

    fragment_id: str
    fragment_digest: str
    allowed_spans: frozenset[str]

    def __post_init__(self) -> None:
        _require_identifier(self.fragment_id, "fragment_id")
        _require_digest(self.fragment_digest, "fragment_digest")
        try:
            allowed_spans = frozenset(self.allowed_spans)
        except TypeError as exc:
            raise ValueError("allowed_spans must be an iterable of spans") from exc
        if not allowed_spans:
            raise ValueError("allowed_spans must contain at least one span")
        for span in allowed_spans:
            _require_span(span, "allowed_span")
        object.__setattr__(self, "allowed_spans", allowed_spans)


@dataclass(frozen=True, slots=True)
class EvidenceSourceRecord:
    """Immutable local source metadata used for provenance resolution."""

    source_id: str
    source_digest: str
    lineage_id: str
    status: Literal["active", "revoked"]
    fragments: Mapping[str, EvidenceFragmentRecord]

    def __post_init__(self) -> None:
        _require_identifier(self.source_id, "source_id")
        _require_digest(self.source_digest, "source_digest")
        _require_identifier(self.lineage_id, "lineage_id")
        if self.status not in {"active", "revoked"}:
            raise ValueError("status must be active or revoked")
        if not isinstance(self.fragments, Mapping) or not self.fragments:
            raise ValueError("fragments must contain at least one fragment")

        fragments_snapshot: dict[str, EvidenceFragmentRecord] = {}
        for fragment_key, fragment in self.fragments.items():
            _require_identifier(fragment_key, "fragment mapping key")
            if not isinstance(fragment, EvidenceFragmentRecord):
                raise ValueError(
                    "fragments values must be EvidenceFragmentRecord instances"
                )
            if fragment_key != fragment.fragment_id:
                raise ValueError(
                    "fragment mapping key must equal fragment.fragment_id"
                )
            fragments_snapshot[fragment_key] = fragment
        object.__setattr__(
            self,
            "fragments",
            MappingProxyType(fragments_snapshot),
        )


@dataclass(frozen=True, slots=True)
class EvidenceRegistrySnapshot:
    """One immutable, content-addressed registry view for a validation run."""

    records: Mapping[str, EvidenceSourceRecord]

    def __post_init__(self) -> None:
        if not isinstance(self.records, Mapping):
            raise ValueError("records must be a mapping")

        records_snapshot: dict[str, EvidenceSourceRecord] = {}
        for source_key, record in self.records.items():
            _require_identifier(source_key, "source mapping key")
            if not isinstance(record, EvidenceSourceRecord):
                raise ValueError(
                    "records values must be EvidenceSourceRecord instances"
                )
            if source_key != record.source_id:
                raise ValueError("source mapping key must equal record.source_id")
            records_snapshot[source_key] = record
        object.__setattr__(
            self,
            "records",
            MappingProxyType(records_snapshot),
        )

    def resolve(self, source_id: str) -> EvidenceSourceRecord | None:
        return self.records.get(source_id)

    def to_mapping(self) -> dict[str, object]:
        sources: dict[str, object] = {}
        for source_id, record in sorted(self.records.items()):
            fragments: dict[str, object] = {}
            for fragment_id, fragment in sorted(record.fragments.items()):
                fragments[fragment_id] = {
                    "allowed_spans": sorted(fragment.allowed_spans),
                    "fragment_digest": fragment.fragment_digest,
                    "fragment_id": fragment.fragment_id,
                }
            sources[source_id] = {
                "fragments": fragments,
                "lineage_id": record.lineage_id,
                "source_digest": record.source_digest,
                "source_id": record.source_id,
                "status": record.status,
            }
        return {
            "schema_version": EVIDENCE_REGISTRY_SNAPSHOT_SCHEMA_VERSION,
            "sources": sources,
        }

    @property
    def snapshot_digest(self) -> str:
        canonical = json.dumps(
            self.to_mapping(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return "sha256:" + hashlib.sha256(canonical).hexdigest()


class EvidenceRegistry(Protocol):
    """Registry able to supply one immutable snapshot per validation run."""

    def snapshot(self) -> EvidenceRegistrySnapshot: ...


class InMemoryEvidenceRegistry:
    """Mutable builder whose validator-facing surface is an immutable snapshot."""

    def __init__(self, records: Sequence[EvidenceSourceRecord] = ()) -> None:
        self._records: dict[str, EvidenceSourceRecord] = {}
        for record in records:
            self.register(record)

    def register(self, record: EvidenceSourceRecord) -> None:
        """Register one source; conflicting replacement is rejected."""
        if not isinstance(record, EvidenceSourceRecord):
            raise ValueError("record must be an EvidenceSourceRecord")
        previous = self._records.get(record.source_id)
        if previous is not None and previous != record:
            raise ValueError("source_id already registered with different metadata")
        self._records[record.source_id] = record

    def resolve(self, source_id: str) -> EvidenceSourceRecord | None:
        """Return the builder's current record; validators use snapshot()."""
        return self._records.get(source_id)

    def snapshot(self) -> EvidenceRegistrySnapshot:
        """Capture a defensive immutable copy of the current registry mapping."""
        return EvidenceRegistrySnapshot(self._records)

    @property
    def snapshot_digest(self) -> str:
        """Return the digest of a fresh snapshot for inspection compatibility."""
        return self.snapshot().snapshot_digest


@dataclass(frozen=True, slots=True)
class EvidenceValidationOutcome:
    """Content-minimized provenance-validation result for one typed reference."""

    reference_id: str
    reference_digest: str
    status: ValidationStatus


@dataclass(frozen=True, slots=True)
class EvidenceValidationReceipt:
    """Deterministic result; not a promotion, truth, or authority receipt."""

    fact_ref: str
    policy_version: str
    reference_policy_version: str
    registry_snapshot_digest: str
    raw_reference_count: int
    unique_reference_count: int
    validated_reference_count: int
    distinct_independent_lineage_count: int
    outcomes: tuple[EvidenceValidationOutcome, ...]

    def __post_init__(self) -> None:
        _require_digest(self.registry_snapshot_digest, "registry_snapshot_digest")
        counts = (
            self.raw_reference_count,
            self.unique_reference_count,
            self.validated_reference_count,
            self.distinct_independent_lineage_count,
        )
        if any(
            not isinstance(value, int) or isinstance(value, bool) or value < 0
            for value in counts
        ):
            raise ValueError("receipt counts must be non-negative integers")
        if not (
            self.distinct_independent_lineage_count
            <= self.validated_reference_count
            <= self.unique_reference_count
            <= self.raw_reference_count
        ):
            raise ValueError("receipt counts violate validation ordering")
        if self.distinct_independent_lineage_count != 0:
            raise ValueError(
                "prototype receipt cannot assert independent lineages without "
                "an authorized independence policy"
            )

    def to_mapping(self) -> dict[str, object]:
        return {
            "distinct_independent_lineage_count": (
                self.distinct_independent_lineage_count
            ),
            "fact_ref": self.fact_ref,
            "outcomes": [
                {
                    "reference_digest": outcome.reference_digest,
                    "reference_id": outcome.reference_id,
                    "status": outcome.status,
                }
                for outcome in self.outcomes
            ],
            "policy_version": self.policy_version,
            "raw_reference_count": self.raw_reference_count,
            "reference_policy_version": self.reference_policy_version,
            "registry_snapshot_digest": self.registry_snapshot_digest,
            "unique_reference_count": self.unique_reference_count,
            "validated_reference_count": self.validated_reference_count,
        }

    @property
    def receipt_digest(self) -> str:
        canonical = json.dumps(
            self.to_mapping(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return "sha256:" + hashlib.sha256(canonical).hexdigest()


class EvidenceReferenceValidator:
    """Validate typed references against one immutable local registry snapshot."""

    def __init__(self, registry: EvidenceRegistry) -> None:
        self._registry = registry

    def validate(
        self,
        *,
        fact_id: str,
        references: Sequence[EvidenceReference],
    ) -> EvidenceValidationReceipt:
        """Return a deterministic receipt without mutating a fact or registry."""
        if not isinstance(fact_id, str) or not fact_id:
            raise ValueError("fact_id must be a non-empty string")

        snapshot = self._registry.snapshot()
        if not isinstance(snapshot, EvidenceRegistrySnapshot):
            raise ValueError(
                "registry.snapshot() must return EvidenceRegistrySnapshot"
            )

        seen_reference_ids: set[str] = set()
        outcomes: list[EvidenceValidationOutcome] = []
        validated_reference_count = 0
        unique_reference_count = 0

        ordered_references = sorted(
            references,
            key=lambda reference: (
                reference.reference_id,
                reference.reference_digest,
            ),
        )
        reference_digests_by_id: dict[str, set[str]] = {}
        for reference in ordered_references:
            reference_digests_by_id.setdefault(reference.reference_id, set()).add(
                reference.reference_digest
            )
        conflicting_reference_ids = {
            reference_id
            for reference_id, reference_digests in reference_digests_by_id.items()
            if len(reference_digests) > 1
        }

        for reference in ordered_references:
            if reference.reference_id in conflicting_reference_ids:
                if reference.reference_id not in seen_reference_ids:
                    seen_reference_ids.add(reference.reference_id)
                    unique_reference_count += 1
                outcomes.append(
                    EvidenceValidationOutcome(
                        reference_id=reference.reference_id,
                        reference_digest=reference.reference_digest,
                        status="conflicting_reference_id",
                    )
                )
                continue

            if reference.reference_id in seen_reference_ids:
                outcomes.append(
                    EvidenceValidationOutcome(
                        reference_id=reference.reference_id,
                        reference_digest=reference.reference_digest,
                        status="duplicate_reference_id",
                    )
                )
                continue

            seen_reference_ids.add(reference.reference_id)
            unique_reference_count += 1
            status = self._validate_reference(snapshot, reference)
            if status == "accepted":
                validated_reference_count += 1

            outcomes.append(
                EvidenceValidationOutcome(
                    reference_id=reference.reference_id,
                    reference_digest=reference.reference_digest,
                    status=status,
                )
            )

        outcomes.sort(
            key=lambda outcome: (
                outcome.reference_id,
                outcome.reference_digest,
            )
        )
        return EvidenceValidationReceipt(
            fact_ref=self._fact_ref(fact_id),
            policy_version=EVIDENCE_VALIDATION_POLICY_VERSION,
            reference_policy_version=EVIDENCE_REFERENCE_POLICY_VERSION,
            registry_snapshot_digest=snapshot.snapshot_digest,
            raw_reference_count=len(references),
            unique_reference_count=unique_reference_count,
            validated_reference_count=validated_reference_count,
            distinct_independent_lineage_count=0,
            outcomes=tuple(outcomes),
        )

    @staticmethod
    def _validate_reference(
        snapshot: EvidenceRegistrySnapshot,
        reference: EvidenceReference,
    ) -> ValidationStatus:
        source = snapshot.resolve(reference.source_id)
        if source is None:
            return "unknown_source"
        if source.status == "revoked":
            return "revoked_source"
        if source.source_digest != reference.source_digest:
            return "source_digest_mismatch"
        if source.lineage_id != reference.lineage_id:
            return "lineage_mismatch"
        fragment = source.fragments.get(reference.fragment_id)
        if fragment is None:
            return "unknown_fragment"
        if fragment.fragment_digest != reference.fragment_digest:
            return "fragment_digest_mismatch"
        if reference.span not in fragment.allowed_spans:
            return "invalid_span"
        return "accepted"

    @staticmethod
    def _fact_ref(fact_id: str) -> str:
        digest = hashlib.sha256(fact_id.encode("utf-8")).hexdigest()
        return f"fact_{digest[:24]}"


__all__ = [
    "EVIDENCE_REGISTRY_SNAPSHOT_SCHEMA_VERSION",
    "EVIDENCE_VALIDATION_POLICY_VERSION",
    "EvidenceFragmentRecord",
    "EvidenceReferenceValidator",
    "EvidenceRegistry",
    "EvidenceRegistrySnapshot",
    "EvidenceSourceRecord",
    "EvidenceValidationOutcome",
    "EvidenceValidationReceipt",
    "InMemoryEvidenceRegistry",
]
