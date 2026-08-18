"""Local-only prototype registry and validator for typed evidence references.

The module is deliberately not wired into TruthGate, SQLite storage, ingestion,
network I/O or Canon mutation. It validates the contract from
:mod:`core.evidence_reference` against an explicitly supplied in-memory registry
and emits content-minimized, deterministic receipts for future observe-mode work.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Literal, Mapping, Protocol, Sequence

from core.evidence_reference import (
    EVIDENCE_REFERENCE_POLICY_VERSION,
    EvidenceReference,
)

EVIDENCE_VALIDATION_POLICY_VERSION = "evidence-validation-v1"

ValidationStatus = Literal[
    "accepted",
    "derived_not_counted",
    "duplicate_reference_id",
    "fragment_digest_mismatch",
    "invalid_span",
    "lineage_mismatch",
    "revoked_source",
    "same_lineage_not_counted",
    "source_digest_mismatch",
    "unknown_fragment",
    "unknown_source",
]


@dataclass(frozen=True, slots=True)
class EvidenceFragmentRecord:
    """One locally registered fragment; no raw fragment text is retained here."""

    fragment_id: str
    fragment_digest: str
    allowed_spans: frozenset[str]

    def __post_init__(self) -> None:
        if not self.fragment_id:
            raise ValueError("fragment_id must be non-empty")
        if not self.fragment_digest.startswith("sha256:"):
            raise ValueError("fragment_digest must be a sha256 digest")
        if not self.allowed_spans:
            raise ValueError("allowed_spans must contain at least one span")


@dataclass(frozen=True, slots=True)
class EvidenceSourceRecord:
    """Hash-pinned local source metadata used for offline reference resolution."""

    source_id: str
    source_digest: str
    lineage_id: str
    status: Literal["active", "revoked"]
    fragments: Mapping[str, EvidenceFragmentRecord]

    def __post_init__(self) -> None:
        if not self.source_id:
            raise ValueError("source_id must be non-empty")
        if not self.source_digest.startswith("sha256:"):
            raise ValueError("source_digest must be a sha256 digest")
        if not self.lineage_id:
            raise ValueError("lineage_id must be non-empty")
        if self.status not in {"active", "revoked"}:
            raise ValueError("status must be active or revoked")
        if not self.fragments:
            raise ValueError("fragments must contain at least one fragment")


class EvidenceRegistry(Protocol):
    """Read-only local source lookup used by the prototype validator."""

    def resolve(self, source_id: str) -> EvidenceSourceRecord | None: ...


class InMemoryEvidenceRegistry:
    """Minimal local registry for deterministic unit tests and offline prototypes."""

    def __init__(self, records: Sequence[EvidenceSourceRecord] = ()) -> None:
        self._records: dict[str, EvidenceSourceRecord] = {}
        for record in records:
            self.register(record)

    def register(self, record: EvidenceSourceRecord) -> None:
        """Register exactly one source record; conflicting replacement is rejected."""
        previous = self._records.get(record.source_id)
        if previous is not None and previous != record:
            raise ValueError("source_id already registered with different metadata")
        self._records[record.source_id] = record

    def resolve(self, source_id: str) -> EvidenceSourceRecord | None:
        return self._records.get(source_id)


@dataclass(frozen=True, slots=True)
class EvidenceValidationOutcome:
    """Content-minimized decision for one typed reference."""

    reference_id: str
    reference_digest: str
    status: ValidationStatus


@dataclass(frozen=True, slots=True)
class EvidenceValidationReceipt:
    """Deterministic validation result; it is not a promotion or write receipt."""

    fact_ref: str
    policy_version: str
    reference_policy_version: str
    raw_reference_count: int
    unique_reference_count: int
    validated_reference_count: int
    distinct_independent_lineage_count: int
    outcomes: tuple[EvidenceValidationOutcome, ...]

    def __post_init__(self) -> None:
        counts = (
            self.raw_reference_count,
            self.unique_reference_count,
            self.validated_reference_count,
            self.distinct_independent_lineage_count,
        )
        if any(not isinstance(value, int) or value < 0 for value in counts):
            raise ValueError("receipt counts must be non-negative integers")
        if not (
            self.distinct_independent_lineage_count
            <= self.validated_reference_count
            <= self.unique_reference_count
            <= self.raw_reference_count
        ):
            raise ValueError("receipt counts violate validation ordering")

    def to_mapping(self) -> dict[str, object]:
        return {
            "distinct_independent_lineage_count": self.distinct_independent_lineage_count,
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
    """Validate typed references against a supplied local-only registry snapshot."""

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
        seen_reference_ids: set[str] = set()
        counted_lineages: set[str] = set()
        outcomes: list[EvidenceValidationOutcome] = []
        validated_reference_count = 0
        unique_reference_count = 0

        for reference in references:
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
            status = self._validate_reference(reference)
            if status == "accepted":
                validated_reference_count += 1
                if reference.lineage_id in counted_lineages:
                    status = "same_lineage_not_counted"
                elif reference.independence_class != "independent":
                    status = (
                        "derived_not_counted"
                        if reference.independence_class == "derived"
                        else "same_lineage_not_counted"
                    )
                else:
                    counted_lineages.add(reference.lineage_id)

            outcomes.append(
                EvidenceValidationOutcome(
                    reference_id=reference.reference_id,
                    reference_digest=reference.reference_digest,
                    status=status,
                )
            )

        outcomes.sort(key=lambda outcome: (outcome.reference_id, outcome.reference_digest))
        return EvidenceValidationReceipt(
            fact_ref=self._fact_ref(fact_id),
            policy_version=EVIDENCE_VALIDATION_POLICY_VERSION,
            reference_policy_version=EVIDENCE_REFERENCE_POLICY_VERSION,
            raw_reference_count=len(references),
            unique_reference_count=unique_reference_count,
            validated_reference_count=validated_reference_count,
            distinct_independent_lineage_count=len(counted_lineages),
            outcomes=tuple(outcomes),
        )

    def _validate_reference(self, reference: EvidenceReference) -> ValidationStatus:
        source = self._registry.resolve(reference.source_id)
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
    "EVIDENCE_VALIDATION_POLICY_VERSION",
    "EvidenceFragmentRecord",
    "EvidenceReferenceValidator",
    "EvidenceRegistry",
    "EvidenceSourceRecord",
    "EvidenceValidationOutcome",
    "EvidenceValidationReceipt",
    "InMemoryEvidenceRegistry",
]
