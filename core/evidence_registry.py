"""Local-only prototype registry and validator for typed evidence references.

The module is deliberately not wired into TruthGate, SQLite storage, ingestion,
network I/O or Canon mutation. It validates the contract from
:mod:`core.evidence_reference` against an explicitly supplied in-memory registry
and emits content-minimized, deterministic receipts for future observe-mode work.
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

EffectiveIndependenceClass = Literal["independent", "derived"]

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
    """One locally registered fragment; no raw fragment text is retained here."""

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
    """Trusted local source metadata used for offline reference resolution."""

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
                raise ValueError("fragments values must be EvidenceFragmentRecord instances")
            if fragment_key != fragment.fragment_id:
                raise ValueError("fragment mapping key must equal fragment.fragment_id")
            fragments_snapshot[fragment_key] = fragment
        object.__setattr__(self, "fragments", MappingProxyType(fragments_snapshot))


class EvidenceRegistry(Protocol):
    """Read-only local source lookup used by the prototype validator."""

    def resolve(self, source_id: str) -> EvidenceSourceRecord | None: ...

    @property
    def snapshot_digest(self) -> str: ...


class InMemoryEvidenceRegistry:
    """Minimal local registry for deterministic unit tests and offline prototypes."""

    def __init__(self, records: Sequence[EvidenceSourceRecord] = ()) -> None:
        self._records: dict[str, EvidenceSourceRecord] = {}
        for record in records:
            self.register(record)

    def register(self, record: EvidenceSourceRecord) -> None:
        """Register exactly one source record; conflicting replacement is rejected."""
        if not isinstance(record, EvidenceSourceRecord):
            raise ValueError("record must be an EvidenceSourceRecord")
        previous = self._records.get(record.source_id)
        if previous is not None and previous != record:
            raise ValueError("source_id already registered with different metadata")
        self._records[record.source_id] = record

    def resolve(self, source_id: str) -> EvidenceSourceRecord | None:
        return self._records.get(source_id)

    @property
    def snapshot_digest(self) -> str:
        snapshot = {
            "sources": {
                source_id: {
                    "fragments": {
                        fragment_id: {
                            "allowed_spans": sorted(fragment.allowed_spans),
                            "fragment_digest": fragment.fragment_digest,
                            "fragment_id": fragment.fragment_id,
                        }
                        for fragment_id, fragment in sorted(record.fragments.items())
                    },
                    "lineage_id": record.lineage_id,
                    "source_digest": record.source_digest,
                    "source_id": record.source_id,
                    "status": record.status,
                }
                for source_id, record in sorted(self._records.items())
            }
        }
        canonical = json.dumps(
            snapshot,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return "sha256:" + hashlib.sha256(canonical).hexdigest()


@dataclass(frozen=True, slots=True)
class EvidenceValidationOutcome:
    """Content-minimized decision for one typed reference."""

    reference_id: str
    reference_digest: str
    status: ValidationStatus
    effective_independence_class: EffectiveIndependenceClass | None


@dataclass(frozen=True, slots=True)
class EvidenceValidationReceipt:
    """Deterministic validation result; it is not a promotion or write receipt."""

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
                    "effective_independence_class": (
                        outcome.effective_independence_class
                    ),
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
        outcomes: list[EvidenceValidationOutcome] = []
        validated_reference_count = 0
        unique_reference_count = 0

        ordered_references = sorted(
            references,
            key=lambda reference: (reference.reference_id, reference.reference_digest),
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
                        effective_independence_class=None,
                    )
                )
                continue

            if reference.reference_id in seen_reference_ids:
                outcomes.append(
                    EvidenceValidationOutcome(
                        reference_id=reference.reference_id,
                        reference_digest=reference.reference_digest,
                        status="duplicate_reference_id",
                        effective_independence_class=None,
                    )
                )
                continue

            seen_reference_ids.add(reference.reference_id)
            unique_reference_count += 1
            status, source = self._validate_reference(reference)
            if status == "accepted":
                assert source is not None
                validated_reference_count += 1

            outcomes.append(
                EvidenceValidationOutcome(
                    reference_id=reference.reference_id,
                    reference_digest=reference.reference_digest,
                    status=status,
                    effective_independence_class=None,
                )
            )

        outcomes.sort(key=lambda outcome: (outcome.reference_id, outcome.reference_digest))
        return EvidenceValidationReceipt(
            fact_ref=self._fact_ref(fact_id),
            policy_version=EVIDENCE_VALIDATION_POLICY_VERSION,
            reference_policy_version=EVIDENCE_REFERENCE_POLICY_VERSION,
            registry_snapshot_digest=self._registry.snapshot_digest,
            raw_reference_count=len(references),
            unique_reference_count=unique_reference_count,
            validated_reference_count=validated_reference_count,
            distinct_independent_lineage_count=0,
            outcomes=tuple(outcomes),
        )

    def _validate_reference(
        self, reference: EvidenceReference
    ) -> tuple[ValidationStatus, EvidenceSourceRecord | None]:
        source = self._registry.resolve(reference.source_id)
        if source is None:
            return "unknown_source", None
        if source.status == "revoked":
            return "revoked_source", None
        if source.source_digest != reference.source_digest:
            return "source_digest_mismatch", None
        if source.lineage_id != reference.lineage_id:
            return "lineage_mismatch", None
        fragment = source.fragments.get(reference.fragment_id)
        if fragment is None:
            return "unknown_fragment", None
        if fragment.fragment_digest != reference.fragment_digest:
            return "fragment_digest_mismatch", None
        if reference.span not in fragment.allowed_spans:
            return "invalid_span", None
        return "accepted", source

    @staticmethod
    def _fact_ref(fact_id: str) -> str:
        digest = hashlib.sha256(fact_id.encode("utf-8")).hexdigest()
        return f"fact_{digest[:24]}"


__all__ = [
    "EVIDENCE_VALIDATION_POLICY_VERSION",
    "EffectiveIndependenceClass",
    "EvidenceFragmentRecord",
    "EvidenceReferenceValidator",
    "EvidenceRegistry",
    "EvidenceSourceRecord",
    "EvidenceValidationOutcome",
    "EvidenceValidationReceipt",
    "InMemoryEvidenceRegistry",
]
