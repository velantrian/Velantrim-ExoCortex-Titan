"""Deterministic, source-linked ContextPack contract for Synaptic Exo-Cortex.

The pack is an immutable prompt payload built from an existing WorkingMemoryPlan.
It does not retrieve, rescore, render an answer, persist, promote, or mutate
knowledge. Token accounting uses a conservative UTF-8 byte upper bound so the
serialized payload never silently exceeds its provider-neutral budget.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json
import math
import re
from typing import Iterable

from core.knowledge_capsule import (
    CapsuleClaim,
    ClaimModality,
    KnowledgeCapsule,
    SourceSpan,
)
from core.working_memory_gate import (
    GateDecision,
    GateDisposition,
    GateReason,
    WorkingMemoryPlan,
)

SCHEMA_VERSION = "synaptic.context-pack.v1"
TOKEN_COUNTER_ID = "utf8-byte-upper-bound-v1"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class ContextPackError(ValueError):
    """Base error for ContextPack contract violations."""


class ContextPackBudgetExceeded(ContextPackError):
    """The mandatory prompt payload cannot fit the configured budget."""

    def __init__(self, *, required_tokens: int, max_tokens: int) -> None:
        self.required_tokens = required_tokens
        self.max_tokens = max_tokens
        super().__init__(
            f"mandatory ContextPack requires {required_tokens} token units; "
            f"budget allows {max_tokens}"
        )


class ContextNoteKind(str, Enum):
    """Structured claim annotation preserved separately from claim text."""

    QUALIFIER = "qualifier"
    UNCERTAINTY = "uncertainty"
    APPLICABILITY_CONDITION = "applicability_condition"
    TEMPORAL_SCOPE = "temporal_scope"


class ContextPackWarningCode(str, Enum):
    """Stable non-fatal ContextPack warning codes."""

    DEFERRED_POINTERS_OMITTED = "deferred_pointers_omitted"


def _non_empty(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContextPackError(f"{name} must be a non-empty string")
    return value


def _positive_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ContextPackError(f"{name} must be a positive integer")
    return value


def _non_negative_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ContextPackError(f"{name} must be a non-negative integer")
    return value


def _probability(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ContextPackError(f"{name} must be a finite number in [0, 1]")
    result = float(value)
    if not math.isfinite(result) or not 0.0 <= result <= 1.0:
        raise ContextPackError(f"{name} must be a finite number in [0, 1]")
    return result


def _strict_bool(value: object, name: str) -> bool:
    if not isinstance(value, bool):
        raise ContextPackError(f"{name} must be a bool")
    return value


def _canonical_json(payload: object) -> str:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _stable_digest(payload: object) -> str:
    return sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def conservative_token_upper_bound(text: str) -> int:
    """Count UTF-8 bytes as deterministic provider-neutral token units.

    Byte-level tokenizers cannot emit more tokens than source bytes. Providers
    with a tighter exact tokenizer may enforce an additional downstream limit;
    this contract deliberately never claims an exact provider token count.
    """

    if not isinstance(text, str):
        raise ContextPackError("text must be a string")
    return len(text.encode("utf-8"))


def _reason_tuple(values: Iterable[GateReason], name: str) -> tuple[GateReason, ...]:
    result = tuple(values)
    if not result or any(not isinstance(value, GateReason) for value in result):
        raise ContextPackError(f"{name} must contain at least one GateReason")
    return result


@dataclass(frozen=True, slots=True)
class ContextPackBudget:
    """Hard budget for the final serialized prompt payload."""

    max_tokens: int = 16_384
    max_deferred_pointers: int = 32

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "max_tokens", _positive_int(self.max_tokens, "max_tokens")
        )
        object.__setattr__(
            self,
            "max_deferred_pointers",
            _non_negative_int(self.max_deferred_pointers, "max_deferred_pointers"),
        )


@dataclass(frozen=True, slots=True)
class ContextEvidence:
    """Exact source provenance copied from a validated SourceSpan."""

    span_id: str
    document_id: str
    start_offset: int
    end_offset: int
    content_hash: str
    source_revision: str | None = None

    def __post_init__(self) -> None:
        _non_empty(self.span_id, "span_id")
        _non_empty(self.document_id, "document_id")
        if self.source_revision is not None:
            _non_empty(self.source_revision, "source_revision")
        if (
            isinstance(self.start_offset, bool)
            or not isinstance(self.start_offset, int)
            or isinstance(self.end_offset, bool)
            or not isinstance(self.end_offset, int)
            or self.start_offset < 0
            or self.end_offset <= self.start_offset
        ):
            raise ContextPackError(
                "evidence must satisfy 0 <= start_offset < end_offset"
            )
        if not isinstance(self.content_hash, str) or not _SHA256_RE.fullmatch(
            self.content_hash
        ):
            raise ContextPackError(
                "content_hash must be a lowercase SHA-256 hex digest"
            )

    @classmethod
    def from_span(cls, span: SourceSpan) -> ContextEvidence:
        if not isinstance(span, SourceSpan):
            raise ContextPackError("span must be a SourceSpan")
        return cls(
            span_id=span.span_id,
            document_id=span.document_id,
            start_offset=span.start_offset,
            end_offset=span.end_offset,
            content_hash=span.content_hash,
            source_revision=span.source_revision,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "span_id": self.span_id,
            "document_id": self.document_id,
            "source_revision": self.source_revision,
            "start_offset": self.start_offset,
            "end_offset": self.end_offset,
            "content_hash": self.content_hash,
        }


@dataclass(frozen=True, slots=True)
class ContextClaim:
    """One complete source-linked claim admitted by the Gate."""

    capsule_id: str
    claim_id: str
    text: str
    modality: ClaimModality
    evidence: tuple[ContextEvidence, ...]
    extraction_confidence: float
    truth_confidence: float | None
    disposition: GateDisposition
    reasons: tuple[GateReason, ...]
    attention_score: float
    protected: bool
    rank: int

    def __post_init__(self) -> None:
        _non_empty(self.capsule_id, "capsule_id")
        _non_empty(self.claim_id, "claim_id")
        _non_empty(self.text, "text")
        if not isinstance(self.modality, ClaimModality):
            raise ContextPackError("modality must be a ClaimModality")
        evidence = tuple(self.evidence)
        if not evidence or any(
            not isinstance(item, ContextEvidence) for item in evidence
        ):
            raise ContextPackError(
                "every ContextClaim must contain at least one ContextEvidence"
            )
        object.__setattr__(
            self,
            "evidence",
            tuple(
                sorted(
                    evidence,
                    key=lambda item: (
                        item.document_id,
                        item.source_revision or "",
                        item.start_offset,
                        item.end_offset,
                        item.span_id,
                    ),
                )
            ),
        )
        object.__setattr__(
            self,
            "extraction_confidence",
            _probability(self.extraction_confidence, "extraction_confidence"),
        )
        if self.truth_confidence is not None:
            object.__setattr__(
                self,
                "truth_confidence",
                _probability(self.truth_confidence, "truth_confidence"),
            )
        if self.disposition not in {
            GateDisposition.ACTIVE,
            GateDisposition.COMPRESS,
        }:
            raise ContextPackError(
                "ContextClaim disposition must be ACTIVE or COMPRESS"
            )
        object.__setattr__(
            self, "reasons", _reason_tuple(self.reasons, "reasons")
        )
        object.__setattr__(
            self,
            "attention_score",
            _probability(self.attention_score, "attention_score"),
        )
        object.__setattr__(
            self, "protected", _strict_bool(self.protected, "protected")
        )
        object.__setattr__(self, "rank", _positive_int(self.rank, "rank"))

    def to_dict(self) -> dict[str, object]:
        return {
            "capsule_id": self.capsule_id,
            "claim_id": self.claim_id,
            "text": self.text,
            "modality": self.modality.value,
            "evidence": [item.to_dict() for item in self.evidence],
            "extraction_confidence": self.extraction_confidence,
            "truth_confidence": self.truth_confidence,
            "disposition": self.disposition.value,
            "reasons": [reason.value for reason in self.reasons],
            "attention_score": self.attention_score,
            "protected": self.protected,
            "rank": self.rank,
        }


@dataclass(frozen=True, slots=True)
class ContextNote:
    """Qualifier, uncertainty, condition, or temporal scope for one packed claim."""

    capsule_id: str
    claim_id: str
    kind: ContextNoteKind
    text: str

    def __post_init__(self) -> None:
        _non_empty(self.capsule_id, "capsule_id")
        _non_empty(self.claim_id, "claim_id")
        if not isinstance(self.kind, ContextNoteKind):
            raise ContextPackError("kind must be a ContextNoteKind")
        _non_empty(self.text, "text")

    def to_dict(self) -> dict[str, str]:
        return {
            "capsule_id": self.capsule_id,
            "claim_id": self.claim_id,
            "kind": self.kind.value,
            "text": self.text,
        }


@dataclass(frozen=True, slots=True)
class ConflictPointer:
    """Non-content pointer for a quarantined capsule."""

    capsule_id: str
    source_document_id: str
    reasons: tuple[GateReason, ...]
    protected: bool

    def __post_init__(self) -> None:
        _non_empty(self.capsule_id, "capsule_id")
        _non_empty(self.source_document_id, "source_document_id")
        object.__setattr__(
            self, "reasons", _reason_tuple(self.reasons, "reasons")
        )
        if GateReason.CONFLICT not in self.reasons:
            raise ContextPackError("ConflictPointer must include the CONFLICT reason")
        object.__setattr__(
            self, "protected", _strict_bool(self.protected, "protected")
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "capsule_id": self.capsule_id,
            "source_document_id": self.source_document_id,
            "reasons": [reason.value for reason in self.reasons],
            "protected": self.protected,
        }


@dataclass(frozen=True, slots=True)
class DeferredPointer:
    """Bounded pointer to an eligible capsule not selected into active context."""

    capsule_id: str
    source_document_id: str
    rank: int
    reasons: tuple[GateReason, ...]
    attention_score: float
    protected: bool

    def __post_init__(self) -> None:
        _non_empty(self.capsule_id, "capsule_id")
        _non_empty(self.source_document_id, "source_document_id")
        object.__setattr__(self, "rank", _positive_int(self.rank, "rank"))
        object.__setattr__(
            self, "reasons", _reason_tuple(self.reasons, "reasons")
        )
        object.__setattr__(
            self,
            "attention_score",
            _probability(self.attention_score, "attention_score"),
        )
        object.__setattr__(
            self, "protected", _strict_bool(self.protected, "protected")
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "capsule_id": self.capsule_id,
            "source_document_id": self.source_document_id,
            "rank": self.rank,
            "reasons": [reason.value for reason in self.reasons],
            "attention_score": self.attention_score,
            "protected": self.protected,
        }


@dataclass(frozen=True, slots=True)
class ContextPackWarning:
    """Structured warning for explicitly omitted optional pack content."""

    code: ContextPackWarningCode
    omitted_count: int

    def __post_init__(self) -> None:
        if not isinstance(self.code, ContextPackWarningCode):
            raise ContextPackError("code must be a ContextPackWarningCode")
        object.__setattr__(
            self, "omitted_count", _positive_int(self.omitted_count, "omitted_count")
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "code": self.code.value,
            "omitted_count": self.omitted_count,
        }


@dataclass(frozen=True, slots=True)
class ContextPack:
    """Immutable, deterministic, budget-checked prompt payload."""

    pack_id: str
    schema_version: str
    token_counter_id: str
    max_tokens: int
    claims: tuple[ContextClaim, ...]
    notes: tuple[ContextNote, ...]
    conflicts: tuple[ConflictPointer, ...]
    deferred: tuple[DeferredPointer, ...]
    warnings: tuple[ContextPackWarning, ...]
    deferred_total: int
    excluded_count: int

    def __post_init__(self) -> None:
        _non_empty(self.pack_id, "pack_id")
        _non_empty(self.schema_version, "schema_version")
        _non_empty(self.token_counter_id, "token_counter_id")
        object.__setattr__(
            self, "max_tokens", _positive_int(self.max_tokens, "max_tokens")
        )
        claims = tuple(self.claims)
        notes = tuple(self.notes)
        conflicts = tuple(self.conflicts)
        deferred = tuple(self.deferred)
        warnings = tuple(self.warnings)
        if any(not isinstance(item, ContextClaim) for item in claims):
            raise ContextPackError("claims must contain only ContextClaim values")
        if any(not isinstance(item, ContextNote) for item in notes):
            raise ContextPackError("notes must contain only ContextNote values")
        if any(not isinstance(item, ConflictPointer) for item in conflicts):
            raise ContextPackError(
                "conflicts must contain only ConflictPointer values"
            )
        if any(not isinstance(item, DeferredPointer) for item in deferred):
            raise ContextPackError(
                "deferred must contain only DeferredPointer values"
            )
        if any(not isinstance(item, ContextPackWarning) for item in warnings):
            raise ContextPackError(
                "warnings must contain only ContextPackWarning values"
            )

        claims = tuple(
            sorted(
                claims,
                key=lambda item: (
                    item.rank,
                    min(evidence.start_offset for evidence in item.evidence),
                    item.capsule_id,
                    item.claim_id,
                ),
            )
        )
        notes = tuple(
            sorted(
                notes,
                key=lambda item: (
                    item.capsule_id,
                    item.claim_id,
                    item.kind.value,
                    item.text,
                ),
            )
        )
        conflicts = tuple(sorted(conflicts, key=lambda item: item.capsule_id))
        deferred = tuple(
            sorted(deferred, key=lambda item: (item.rank, item.capsule_id))
        )
        warnings = tuple(
            sorted(warnings, key=lambda item: (item.code.value, item.omitted_count))
        )
        object.__setattr__(self, "claims", claims)
        object.__setattr__(self, "notes", notes)
        object.__setattr__(self, "conflicts", conflicts)
        object.__setattr__(self, "deferred", deferred)
        object.__setattr__(self, "warnings", warnings)
        object.__setattr__(
            self,
            "deferred_total",
            _non_negative_int(self.deferred_total, "deferred_total"),
        )
        object.__setattr__(
            self,
            "excluded_count",
            _non_negative_int(self.excluded_count, "excluded_count"),
        )

        claim_keys = {(item.capsule_id, item.claim_id) for item in claims}
        if len(claim_keys) != len(claims):
            raise ContextPackError("packed claim identities must be unique")
        if any(
            (note.capsule_id, note.claim_id) not in claim_keys for note in notes
        ):
            raise ContextPackError("every ContextNote must reference a packed claim")
        selected_capsules = {item.capsule_id for item in claims}
        conflict_capsules = {item.capsule_id for item in conflicts}
        deferred_capsules = {item.capsule_id for item in deferred}
        if selected_capsules & conflict_capsules:
            raise ContextPackError(
                "a capsule cannot be both selected and quarantined"
            )
        if selected_capsules & deferred_capsules:
            raise ContextPackError("a capsule cannot be both selected and deferred")
        if conflict_capsules & deferred_capsules:
            raise ContextPackError(
                "a capsule cannot be both quarantined and deferred"
            )
        if self.deferred_total < len(deferred):
            raise ContextPackError(
                "deferred_total cannot be smaller than included deferred pointers"
            )
        omitted_deferred = self.deferred_total - len(deferred)
        deferred_warnings = tuple(
            warning
            for warning in warnings
            if warning.code is ContextPackWarningCode.DEFERRED_POINTERS_OMITTED
        )
        if omitted_deferred == 0 and deferred_warnings:
            raise ContextPackError(
                "deferred omission warning is invalid when no pointer was omitted"
            )
        if omitted_deferred > 0 and (
            len(deferred_warnings) != 1
            or deferred_warnings[0].omitted_count != omitted_deferred
        ):
            raise ContextPackError(
                "deferred pointer omissions require one exact structured warning"
            )

        expected_id = self.compute_content_id(
            schema_version=self.schema_version,
            token_counter_id=self.token_counter_id,
            max_tokens=self.max_tokens,
            claims=claims,
            notes=notes,
            conflicts=conflicts,
            deferred=deferred,
            warnings=warnings,
            deferred_total=self.deferred_total,
            excluded_count=self.excluded_count,
        )
        if self.pack_id != expected_id:
            raise ContextPackError("pack_id does not match ContextPack content")
        if self.token_cost > self.max_tokens:
            raise ContextPackBudgetExceeded(
                required_tokens=self.token_cost, max_tokens=self.max_tokens
            )

    @classmethod
    def create(
        cls,
        *,
        max_tokens: int,
        claims: Iterable[ContextClaim],
        notes: Iterable[ContextNote],
        conflicts: Iterable[ConflictPointer],
        deferred: Iterable[DeferredPointer],
        warnings: Iterable[ContextPackWarning],
        deferred_total: int,
        excluded_count: int,
        schema_version: str = SCHEMA_VERSION,
        token_counter_id: str = TOKEN_COUNTER_ID,
    ) -> ContextPack:
        claims_tuple = tuple(
            sorted(
                tuple(claims),
                key=lambda item: (
                    item.rank,
                    min(evidence.start_offset for evidence in item.evidence),
                    item.capsule_id,
                    item.claim_id,
                ),
            )
        )
        notes_tuple = tuple(
            sorted(
                tuple(notes),
                key=lambda item: (
                    item.capsule_id,
                    item.claim_id,
                    item.kind.value,
                    item.text,
                ),
            )
        )
        conflicts_tuple = tuple(
            sorted(tuple(conflicts), key=lambda item: item.capsule_id)
        )
        deferred_tuple = tuple(
            sorted(
                tuple(deferred),
                key=lambda item: (item.rank, item.capsule_id),
            )
        )
        warnings_tuple = tuple(
            sorted(
                tuple(warnings),
                key=lambda item: (item.code.value, item.omitted_count),
            )
        )
        pack_id = cls.compute_content_id(
            schema_version=schema_version,
            token_counter_id=token_counter_id,
            max_tokens=max_tokens,
            claims=claims_tuple,
            notes=notes_tuple,
            conflicts=conflicts_tuple,
            deferred=deferred_tuple,
            warnings=warnings_tuple,
            deferred_total=deferred_total,
            excluded_count=excluded_count,
        )
        return cls(
            pack_id=pack_id,
            schema_version=schema_version,
            token_counter_id=token_counter_id,
            max_tokens=max_tokens,
            claims=claims_tuple,
            notes=notes_tuple,
            conflicts=conflicts_tuple,
            deferred=deferred_tuple,
            warnings=warnings_tuple,
            deferred_total=deferred_total,
            excluded_count=excluded_count,
        )

    @staticmethod
    def compute_content_id(
        *,
        schema_version: str,
        token_counter_id: str,
        max_tokens: int,
        claims: Iterable[ContextClaim],
        notes: Iterable[ContextNote],
        conflicts: Iterable[ConflictPointer],
        deferred: Iterable[DeferredPointer],
        warnings: Iterable[ContextPackWarning],
        deferred_total: int,
        excluded_count: int,
    ) -> str:
        return _stable_digest(
            {
                "schema_version": schema_version,
                "token_counter_id": token_counter_id,
                "max_tokens": max_tokens,
                "claims": [item.to_dict() for item in claims],
                "notes": [item.to_dict() for item in notes],
                "conflicts": [item.to_dict() for item in conflicts],
                "deferred": [item.to_dict() for item in deferred],
                "warnings": [item.to_dict() for item in warnings],
                "deferred_total": deferred_total,
                "excluded_count": excluded_count,
            }
        )

    @property
    def token_cost(self) -> int:
        return conservative_token_upper_bound(self.to_prompt_json())

    def to_prompt_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "pack_id": self.pack_id,
            "token_counter_id": self.token_counter_id,
            "budget": {"max_tokens": self.max_tokens},
            "claims": [item.to_dict() for item in self.claims],
            "notes": [item.to_dict() for item in self.notes],
            "conflicts": [item.to_dict() for item in self.conflicts],
            "deferred": [item.to_dict() for item in self.deferred],
            "meta": {
                "deferred_total": self.deferred_total,
                "deferred_included": len(self.deferred),
                "excluded_count": self.excluded_count,
            },
            "warnings": [item.to_dict() for item in self.warnings],
        }

    def to_prompt_json(self) -> str:
        return _canonical_json(self.to_prompt_dict())


def _claim_sort_key(claim: CapsuleClaim) -> tuple[int, str]:
    return (
        min(span.start_offset for span in claim.source_spans),
        claim.claim_id,
    )


def _claims_for_exact_essence(capsule: KnowledgeCapsule) -> tuple[CapsuleClaim, ...]:
    """Resolve one unambiguous ordered subset whose complete text equals essence."""

    ordered = tuple(sorted(capsule.claims, key=_claim_sort_key))
    target = capsule.essence
    paths: dict[int, list[tuple[int, ...]]] = {0: [()]}
    for index, claim in enumerate(ordered):
        next_paths = {position: list(values) for position, values in paths.items()}
        for position, values in paths.items():
            fragment = claim.text if position == 0 else " " + claim.text
            if not target.startswith(fragment, position):
                continue
            new_position = position + len(fragment)
            bucket = next_paths.setdefault(new_position, [])
            for value in values:
                candidate = value + (index,)
                if candidate not in bucket:
                    bucket.append(candidate)
                if len(bucket) > 2:
                    del bucket[2:]
        paths = next_paths

    matches = paths.get(len(target), [])
    non_empty = tuple(path for path in matches if path)
    if len(non_empty) != 1:
        if not non_empty:
            raise ContextPackError(
                f"compressed capsule {capsule.capsule_id} essence is not composed "
                "of complete source claims"
            )
        raise ContextPackError(
            f"compressed capsule {capsule.capsule_id} essence provenance is ambiguous"
        )
    return tuple(ordered[index] for index in non_empty[0])


def _evidence_for_claim(claim: CapsuleClaim) -> tuple[ContextEvidence, ...]:
    return tuple(ContextEvidence.from_span(span) for span in claim.source_spans)


def _notes_for_claim(
    capsule: KnowledgeCapsule, claim: CapsuleClaim
) -> tuple[ContextNote, ...]:
    notes: list[ContextNote] = []
    notes.extend(
        ContextNote(
            capsule_id=capsule.capsule_id,
            claim_id=claim.claim_id,
            kind=ContextNoteKind.QUALIFIER,
            text=text,
        )
        for text in claim.qualifiers
    )
    notes.extend(
        ContextNote(
            capsule_id=capsule.capsule_id,
            claim_id=claim.claim_id,
            kind=ContextNoteKind.UNCERTAINTY,
            text=text,
        )
        for text in claim.uncertainties
    )
    notes.extend(
        ContextNote(
            capsule_id=capsule.capsule_id,
            claim_id=claim.claim_id,
            kind=ContextNoteKind.APPLICABILITY_CONDITION,
            text=text,
        )
        for text in claim.applicability_conditions
    )
    if claim.temporal_scope is not None:
        notes.append(
            ContextNote(
                capsule_id=capsule.capsule_id,
                claim_id=claim.claim_id,
                kind=ContextNoteKind.TEMPORAL_SCOPE,
                text=claim.temporal_scope,
            )
        )
    return tuple(notes)


def _packed_claim(
    capsule: KnowledgeCapsule,
    claim: CapsuleClaim,
    decision: GateDecision,
) -> ContextClaim:
    if decision.rank is None:
        raise ContextPackError("selected Gate decision must have a rank")
    return ContextClaim(
        capsule_id=capsule.capsule_id,
        claim_id=claim.claim_id,
        text=claim.text,
        modality=claim.modality,
        evidence=_evidence_for_claim(claim),
        extraction_confidence=claim.extraction_confidence,
        truth_confidence=claim.truth_confidence,
        disposition=decision.disposition,
        reasons=decision.reasons,
        attention_score=decision.attention_score,
        protected=decision.protected,
        rank=decision.rank,
    )


class ContextPackBuilder:
    """Pure builder from a complete Gate plan and its immutable capsules."""

    def build(
        self,
        plan: WorkingMemoryPlan,
        capsules: Iterable[KnowledgeCapsule],
        *,
        budget: ContextPackBudget | None = None,
    ) -> ContextPack:
        if not isinstance(plan, WorkingMemoryPlan):
            raise ContextPackError("plan must be a WorkingMemoryPlan")
        if budget is None:
            resolved_budget = ContextPackBudget()
        elif isinstance(budget, ContextPackBudget):
            resolved_budget = budget
        else:
            raise ContextPackError(
                "budget must be a ContextPackBudget or None"
            )

        materialized = tuple(capsules)
        if any(not isinstance(item, KnowledgeCapsule) for item in materialized):
            raise ContextPackError(
                "capsules must contain only KnowledgeCapsule values"
            )
        by_id: dict[str, KnowledgeCapsule] = {}
        for capsule in materialized:
            if capsule.capsule_id in by_id:
                raise ContextPackError(
                    f"duplicate capsule_id: {capsule.capsule_id}"
                )
            by_id[capsule.capsule_id] = capsule

        decision_ids = {decision.capsule_id for decision in plan.decisions}
        if set(by_id) != decision_ids:
            missing = sorted(decision_ids - set(by_id))
            unexpected = sorted(set(by_id) - decision_ids)
            raise ContextPackError(
                f"plan/capsule mismatch: missing={missing}, unexpected={unexpected}"
            )

        selected_decisions = tuple(
            sorted(
                (
                    decision
                    for decision in plan.decisions
                    if decision.disposition
                    in {GateDisposition.ACTIVE, GateDisposition.COMPRESS}
                ),
                key=lambda decision: (
                    decision.rank if decision.rank is not None else 0,
                    decision.capsule_id,
                ),
            )
        )
        claims: list[ContextClaim] = []
        notes: list[ContextNote] = []
        for decision in selected_decisions:
            capsule = by_id[decision.capsule_id]
            source_claims = (
                tuple(sorted(capsule.claims, key=_claim_sort_key))
                if decision.disposition is GateDisposition.ACTIVE
                else _claims_for_exact_essence(capsule)
            )
            for claim in source_claims:
                claims.append(_packed_claim(capsule, claim, decision))
                notes.extend(_notes_for_claim(capsule, claim))

        conflicts = tuple(
            ConflictPointer(
                capsule_id=decision.capsule_id,
                source_document_id=by_id[decision.capsule_id].source_document_id,
                reasons=decision.reasons,
                protected=decision.protected,
            )
            for decision in plan.quarantined
        )
        deferred_all = tuple(
            DeferredPointer(
                capsule_id=decision.capsule_id,
                source_document_id=by_id[decision.capsule_id].source_document_id,
                rank=decision.rank
                if decision.rank is not None
                else _raise_unranked_deferred(),
                reasons=decision.reasons,
                attention_score=decision.attention_score,
                protected=decision.protected,
            )
            for decision in plan.deferred
        )
        excluded_count = len(plan.excluded)

        mandatory = ContextPack.create(
            max_tokens=resolved_budget.max_tokens,
            claims=claims,
            notes=notes,
            conflicts=conflicts,
            deferred=(),
            warnings=(
                (
                    ContextPackWarning(
                        code=ContextPackWarningCode.DEFERRED_POINTERS_OMITTED,
                        omitted_count=len(deferred_all),
                    ),
                )
                if deferred_all
                else ()
            ),
            deferred_total=len(deferred_all),
            excluded_count=excluded_count,
        )
        if mandatory.token_cost > resolved_budget.max_tokens:
            raise ContextPackBudgetExceeded(
                required_tokens=mandatory.token_cost,
                max_tokens=resolved_budget.max_tokens,
            )

        max_count = min(
            len(deferred_all), resolved_budget.max_deferred_pointers
        )
        best: ContextPack | None = None
        for included_count in range(max_count + 1):
            omitted_count = len(deferred_all) - included_count
            warnings: tuple[ContextPackWarning, ...] = (
                (
                    ContextPackWarning(
                        code=ContextPackWarningCode.DEFERRED_POINTERS_OMITTED,
                        omitted_count=omitted_count,
                    ),
                )
                if omitted_count
                else ()
            )
            try:
                candidate = ContextPack.create(
                    max_tokens=resolved_budget.max_tokens,
                    claims=claims,
                    notes=notes,
                    conflicts=conflicts,
                    deferred=deferred_all[:included_count],
                    warnings=warnings,
                    deferred_total=len(deferred_all),
                    excluded_count=excluded_count,
                )
            except ContextPackBudgetExceeded:
                continue
            best = candidate

        if best is None:
            raise ContextPackBudgetExceeded(
                required_tokens=mandatory.token_cost,
                max_tokens=resolved_budget.max_tokens,
            )
        return best


def _raise_unranked_deferred() -> int:
    raise ContextPackError("DEFER Gate decision must have a rank")


__all__ = [
    "SCHEMA_VERSION",
    "TOKEN_COUNTER_ID",
    "ConflictPointer",
    "ContextClaim",
    "ContextEvidence",
    "ContextNote",
    "ContextNoteKind",
    "ContextPack",
    "ContextPackBudget",
    "ContextPackBudgetExceeded",
    "ContextPackBuilder",
    "ContextPackError",
    "ContextPackWarning",
    "ContextPackWarningCode",
    "DeferredPointer",
    "conservative_token_upper_bound",
]
