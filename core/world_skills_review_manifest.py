"""Local-only resolver for owner-reviewed World Skills source manifests.

This adapter is deliberately not wired into HTTP routes, MemoryOpsStore,
fact metadata, ingestion, TruthGate, Canon, or promotion. A reference digest
match resolves only a location/integrity pointer; source review provenance and
claim-support review are separate manifest attestations. None is authority to
admit, validate, promote, or mutate a fact.
Reviewer IDs and approval references are recorded attestations, not
cryptographic identity verification or digital signatures.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath
from types import MappingProxyType
from typing import Literal, Mapping

from core.evidence_reference import EvidenceReference
from core.evidence_registry import (
    EvidenceFragmentRecord,
    EvidenceReferenceValidator,
    EvidenceRegistrySnapshot,
    EvidenceSourceRecord,
    EvidenceValidationReceipt,
    InMemoryEvidenceRegistry,
)

WORLD_SKILLS_REVIEW_MANIFEST_SCHEMA_VERSION = 1
WORLD_SKILLS_CANONICAL_TEXT_POLICY_VERSION = "world-skills-canonical-text-v1"
OWNER_REVIEW_MANIFEST_RELATIVE_PATH = Path(
    "docs/evidence/world_skills_pr1_owner_review_manifest.v1.json"
)
CANDIDATE_SOURCE_PATH = "docs/knowledge/world_skills_core/ru/01_P0_FORMAL_LOGIC_MATH.ru.md"

_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_SPAN_RE = re.compile(r"^chars:(0|[1-9][0-9]*)-(0|[1-9][0-9]*)$")
_TIMESTAMP_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$")
_MAX_SPAN_DIGITS = 18
_ALLOWED_SOURCE_PATHS = frozenset({CANDIDATE_SOURCE_PATH})


class WorldSkillsManifestError(ValueError):
    """Raised when the local review manifest or its pinned text is invalid."""


def _canonical_json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise WorldSkillsManifestError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def canonical_text_v1(raw_bytes: bytes) -> str:
    """Decode strict UTF-8; normalize line endings and Unicode NFC only.

    All other bytes/text (including leading/trailing spaces and final newlines)
    are preserved. Spans address Python Unicode code points in this exact text,
    with a half-open [start, end) range.
    """
    if not isinstance(raw_bytes, bytes):
        raise WorldSkillsManifestError("source bytes must be bytes")
    try:
        text = raw_bytes.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise WorldSkillsManifestError("source must be strict UTF-8") from exc
    if text.startswith("\ufeff"):
        raise WorldSkillsManifestError("UTF-8 BOM is not permitted by canonical-text-v1")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return unicodedata.normalize("NFC", text)


def _digest(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _require_digest(value: object, field: str) -> str:
    if not isinstance(value, str) or _DIGEST_RE.fullmatch(value) is None:
        raise WorldSkillsManifestError(f"{field} must be sha256:<64 lower-case hex>")
    return value


def _require_identifier(value: object, field: str) -> str:
    if not isinstance(value, str) or _IDENTIFIER_RE.fullmatch(value) is None:
        raise WorldSkillsManifestError(f"{field} must be a safe technical identifier")
    return value


def _require_exact_keys(value: object, expected: set[str], field: str) -> dict[str, object]:
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise WorldSkillsManifestError(f"{field} must be a JSON object")
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        unexpected = sorted(actual - expected)
        raise WorldSkillsManifestError(
            f"{field} fields mismatch: missing={missing}; unexpected={unexpected}"
        )
    return value


def _parse_span(value: object, canonical_text: str | None) -> str:
    if not isinstance(value, str) or _SPAN_RE.fullmatch(value) is None:
        raise WorldSkillsManifestError("span must use canonical ASCII chars:<start>-<end> form")
    start_text, end_text = value.removeprefix("chars:").split("-", maxsplit=1)
    if len(start_text) > _MAX_SPAN_DIGITS or len(end_text) > _MAX_SPAN_DIGITS:
        raise WorldSkillsManifestError("span decimal components exceed 18 digits")
    start, end = int(start_text), int(end_text)
    if end <= start or (canonical_text is not None and end > len(canonical_text)):
        raise WorldSkillsManifestError(
            "span must be non-empty and within available canonical text"
        )
    return value


def _parse_review(value: object, field: str) -> Mapping[str, str]:
    review = _require_exact_keys(
        value,
        {"status", "reviewer_id", "reviewed_at", "approval_ref"},
        field,
    )
    if review["status"] != "attested_unverified":
        raise WorldSkillsManifestError(
            f"{field}.status must be attested_unverified; owner identity is not authenticated"
        )
    reviewer_id = _require_identifier(review["reviewer_id"], f"{field}.reviewer_id")
    approval_ref = _require_identifier(review["approval_ref"], f"{field}.approval_ref")
    reviewed_at = review["reviewed_at"]
    if not isinstance(reviewed_at, str) or _TIMESTAMP_RE.fullmatch(reviewed_at) is None:
        raise WorldSkillsManifestError(f"{field}.reviewed_at must use UTC second precision")
    try:
        datetime.strptime(reviewed_at, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise WorldSkillsManifestError(f"{field}.reviewed_at is not a valid UTC timestamp") from exc
    return MappingProxyType(
        {
            "status": "attested_unverified",
            "reviewer_id": reviewer_id,
            "reviewed_at": reviewed_at,
            "approval_ref": approval_ref,
        }
    )


def _safe_repo_file(repo_root: Path, relative_path: str) -> Path:
    if relative_path not in _ALLOWED_SOURCE_PATHS:
        raise WorldSkillsManifestError("source path is not in the bounded candidate allowlist")
    pure = PurePosixPath(relative_path)
    if pure.is_absolute() or ".." in pure.parts or "\\" in relative_path:
        raise WorldSkillsManifestError("source path must be a safe repository-relative POSIX path")
    root = repo_root.resolve(strict=True)
    path = root
    for part in pure.parts:
        path = path / part
        if path.is_symlink():
            raise WorldSkillsManifestError("symlinked source paths are not permitted")
    try:
        resolved = path.resolve(strict=True)
    except FileNotFoundError as exc:
        raise WorldSkillsManifestError("manifest source file does not exist") from exc
    if not resolved.is_relative_to(root) or not resolved.is_file():
        raise WorldSkillsManifestError(
            "manifest source must be a regular file inside the repository"
        )
    return resolved


@dataclass(frozen=True, slots=True)
class WorldSkillsEvidenceResult:
    """Three independent local observations; none grants evidence/admission authority."""

    reference_state: Literal["REFERENCE_RESOLVED", "REFERENCE_UNRESOLVED"]
    source_provenance_state: Literal[
        "SOURCE_PROVENANCE_ATTESTED_UNVERIFIED",
        "SOURCE_PROVENANCE_NOT_ATTESTED",
    ]
    claim_support_state: Literal[
        "CLAIM_SUPPORT_ATTESTED_UNVERIFIED",
        "CLAIM_SUPPORT_NOT_ESTABLISHED",
    ]
    validation_status: str
    source_status: Literal["active", "revoked"] | None
    validation_receipt_digest: str


class _FixedSnapshotRegistry:
    """Validator adapter exposing only one immutable manifest-derived snapshot."""

    def __init__(self, snapshot: EvidenceRegistrySnapshot) -> None:
        self._snapshot = snapshot

    def snapshot(self) -> EvidenceRegistrySnapshot:
        return self._snapshot


class WorldSkillsEvidenceResolver:
    """Read-only resolver over the fixed local manifest and one immutable snapshot."""

    def __init__(
        self,
        *,
        snapshot: EvidenceRegistrySnapshot,
        source_reviews: Mapping[str, Mapping[str, str]],
        claim_support_reviews: Mapping[tuple[str, str, str, str], tuple[str, Mapping[str, str]]],
    ) -> None:
        self._snapshot = snapshot
        self._source_reviews = MappingProxyType(dict(source_reviews))
        self._claim_support_reviews = MappingProxyType(dict(claim_support_reviews))
        self._validator = EvidenceReferenceValidator(_FixedSnapshotRegistry(snapshot))

    @classmethod
    def load(cls, repo_root: str | Path) -> WorldSkillsEvidenceResolver:
        """Load only the fixed checked-in manifest; there is no request/store input."""
        root = Path(repo_root).resolve(strict=True)
        manifest_path = root / OWNER_REVIEW_MANIFEST_RELATIVE_PATH
        if manifest_path.is_symlink() or not manifest_path.is_file():
            raise WorldSkillsManifestError("fixed owner-review manifest is missing or symlinked")
        try:
            document = json.loads(
                manifest_path.read_text(encoding="utf-8"),
                object_pairs_hook=_canonical_json_object,
            )
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise WorldSkillsManifestError(
                "fixed owner-review manifest is unreadable JSON"
            ) from exc
        return cls._from_document(root, document)

    @classmethod
    def _from_document(cls, repo_root: Path, document: object) -> WorldSkillsEvidenceResolver:
        top = _require_exact_keys(
            document,
            {
                "schema_version",
                "canonical_text_policy_version",
                "candidates",
                "sources",
                "claim_support_reviews",
            },
            "manifest",
        )
        if (
            not isinstance(top["schema_version"], int)
            or isinstance(top["schema_version"], bool)
            or top["schema_version"] != WORLD_SKILLS_REVIEW_MANIFEST_SCHEMA_VERSION
        ):
            raise WorldSkillsManifestError("unsupported owner-review manifest schema_version")
        if top["canonical_text_policy_version"] != WORLD_SKILLS_CANONICAL_TEXT_POLICY_VERSION:
            raise WorldSkillsManifestError("unsupported canonical-text policy version")
        candidates = top["candidates"]
        sources = top["sources"]
        claim_reviews = top["claim_support_reviews"]
        if (
            not isinstance(candidates, list)
            or not isinstance(sources, list)
            or not isinstance(claim_reviews, list)
        ):
            raise WorldSkillsManifestError(
                "candidates, sources, and claim_support_reviews must be arrays"
            )

        candidate_ids: set[str] = set()
        candidate_paths: set[str] = set()
        for index, candidate_value in enumerate(candidates):
            candidate = _require_exact_keys(
                candidate_value,
                {"source_id", "relative_path", "source_digest", "canonical_text_digest", "status"},
                f"candidates[{index}]",
            )
            source_id = _require_identifier(
                candidate["source_id"], f"candidates[{index}].source_id"
            )
            relative_path = candidate["relative_path"]
            if not isinstance(relative_path, str) or relative_path not in _ALLOWED_SOURCE_PATHS:
                raise WorldSkillsManifestError("candidate path is outside the bounded allowlist")
            expected_source_digest = _require_digest(
                candidate["source_digest"], f"candidates[{index}].source_digest"
            )
            expected_canonical_digest = _require_digest(
                candidate["canonical_text_digest"],
                f"candidates[{index}].canonical_text_digest",
            )
            if candidate["status"] != "pending_owner_review":
                raise WorldSkillsManifestError("candidate entries must remain pending_owner_review")
            candidate_file = _safe_repo_file(repo_root, relative_path)
            candidate_bytes = candidate_file.read_bytes()
            if _digest(candidate_bytes) != expected_source_digest:
                raise WorldSkillsManifestError("pending candidate raw-byte digest mismatch")
            candidate_text = canonical_text_v1(candidate_bytes)
            if _digest(candidate_text.encode("utf-8")) != expected_canonical_digest:
                raise WorldSkillsManifestError("pending candidate canonical-text digest mismatch")
            if source_id in candidate_ids or relative_path in candidate_paths:
                raise WorldSkillsManifestError("duplicate candidate source or path")
            candidate_ids.add(source_id)
            candidate_paths.add(relative_path)

        records: list[EvidenceSourceRecord] = []
        source_reviews: dict[str, Mapping[str, str]] = {}
        source_ids: set[str] = set()
        source_paths: set[str] = set()
        for index, source_value in enumerate(sources):
            source = _require_exact_keys(
                source_value,
                {
                    "source_id",
                    "relative_path",
                    "lineage_id",
                    "status",
                    "source_digest",
                    "canonical_text_digest",
                    "source_review",
                    "fragments",
                },
                f"sources[{index}]",
            )
            source_id = _require_identifier(source["source_id"], f"sources[{index}].source_id")
            lineage_id = _require_identifier(source["lineage_id"], f"sources[{index}].lineage_id")
            relative_path = source["relative_path"]
            if not isinstance(relative_path, str):
                raise WorldSkillsManifestError("relative_path must be a string")
            if not isinstance(source["status"], str) or source["status"] not in {
                "active",
                "revoked",
            }:
                raise WorldSkillsManifestError("source status must be active or revoked")
            if source_id in source_ids or relative_path in source_paths:
                raise WorldSkillsManifestError("duplicate source id or relative path")
            if source_id in candidate_ids or relative_path in candidate_paths:
                raise WorldSkillsManifestError("a candidate cannot also be an active source")
            source_ids.add(source_id)
            source_paths.add(relative_path)
            source_digest = _require_digest(
                source["source_digest"], f"sources[{index}].source_digest"
            )
            canonical_digest = _require_digest(
                source["canonical_text_digest"], f"sources[{index}].canonical_text_digest"
            )
            source_review = _parse_review(
                source["source_review"], f"sources[{index}].source_review"
            )

            if source["status"] == "active":
                source_file = _safe_repo_file(repo_root, relative_path)
                raw_bytes = source_file.read_bytes()
                if _digest(raw_bytes) != source_digest:
                    raise WorldSkillsManifestError("active source raw-byte digest mismatch")
                canonical_text = canonical_text_v1(raw_bytes)
                canonical_bytes = canonical_text.encode("utf-8")
                if _digest(canonical_bytes) != canonical_digest:
                    raise WorldSkillsManifestError("active source canonical-text digest mismatch")
            else:
                # A revoked source is a metadata-only tombstone: retain its pinned
                # identifiers/digests, but do not require or read the old source file.
                if relative_path not in _ALLOWED_SOURCE_PATHS:
                    raise WorldSkillsManifestError(
                        "source path is not in the bounded candidate allowlist"
                    )
                canonical_text = ""

            fragment_values = source["fragments"]
            if not isinstance(fragment_values, list) or not fragment_values:
                raise WorldSkillsManifestError("active source records require at least one fragment")
            fragments: dict[str, EvidenceFragmentRecord] = {}
            for fragment_index, fragment_value in enumerate(fragment_values):
                fragment = _require_exact_keys(
                    fragment_value,
                    {"fragment_id", "span", "fragment_digest"},
                    f"sources[{index}].fragments[{fragment_index}]",
                )
                fragment_id = _require_identifier(fragment["fragment_id"], "fragment_id")
                fragment_digest = _require_digest(fragment["fragment_digest"], "fragment_digest")
                if fragment_id in fragments:
                    raise WorldSkillsManifestError("duplicate fragment_id")
                if source["status"] == "active":
                    span = _parse_span(fragment["span"], canonical_text)
                    start_text, end_text = span.removeprefix("chars:").split("-", maxsplit=1)
                    fragment_bytes = canonical_text[int(start_text) : int(end_text)].encode("utf-8")
                    if _digest(fragment_bytes) != fragment_digest:
                        raise WorldSkillsManifestError(
                            "fragment digest does not match exact canonical-text span"
                        )
                else:
                    # The original text is unavailable for tombstones, so validate
                    # canonical span syntax and ordering but cannot recheck its bound.
                    span = _parse_span(fragment["span"], None)
                    _require_digest(fragment_digest, "fragment_digest")
                fragments[fragment_id] = EvidenceFragmentRecord(
                    fragment_id=fragment_id,
                    fragment_digest=fragment_digest,
                    allowed_spans=frozenset({span}),
                )
            records.append(
                EvidenceSourceRecord(
                    source_id=source_id,
                    source_digest=source_digest,
                    lineage_id=lineage_id,
                    status=source["status"],
                    fragments=fragments,
                )
            )
            source_reviews[source_id] = source_review

        overlap_paths = source_paths & candidate_paths
        if overlap_paths:
            raise WorldSkillsManifestError(
                "active source path is still listed as a pending candidate"
            )

        claim_support_reviews: dict[tuple[str, str, str, str], tuple[str, Mapping[str, str]]] = {}
        for index, review_value in enumerate(claim_reviews):
            review = _require_exact_keys(
                review_value,
                {
                    "fact_id",
                    "claim_digest",
                    "reference_id",
                    "reference_digest",
                    "assessment",
                    "review",
                },
                f"claim_support_reviews[{index}]",
            )
            fact_id = _require_identifier(review["fact_id"], "claim fact_id")
            claim_digest = _require_digest(review["claim_digest"], "claim_digest")
            reference_id = _require_identifier(review["reference_id"], "claim reference_id")
            reference_digest = _require_digest(review["reference_digest"], "claim reference_digest")
            assessment = review["assessment"]
            if not isinstance(assessment, str) or assessment not in {
                "supports",
                "does_not_support",
                "unclear",
            }:
                raise WorldSkillsManifestError("claim assessment is unsupported")
            claim_review_provenance = _parse_review(
                review["review"], f"claim_support_reviews[{index}].review"
            )
            key = (fact_id, claim_digest, reference_id, reference_digest)
            if key in claim_support_reviews:
                raise WorldSkillsManifestError("duplicate claim-support review key")
            claim_support_reviews[key] = (assessment, claim_review_provenance)

        registry = InMemoryEvidenceRegistry(records)
        return cls(
            snapshot=registry.snapshot(),
            source_reviews=source_reviews,
            claim_support_reviews=claim_support_reviews,
        )

    def resolve(
        self,
        reference: EvidenceReference,
        *,
        fact_id: str,
        claim_text: str,
    ) -> WorldSkillsEvidenceResult:
        """Evaluate three independent local states without any write/admission action."""
        if not isinstance(claim_text, str):
            raise WorldSkillsManifestError("claim_text must be a string")
        receipt: EvidenceValidationReceipt = self._validator.validate(
            fact_id=fact_id,
            references=[reference],
        )
        outcome = receipt.outcomes[0]
        source = self._snapshot.resolve(reference.source_id)
        reference_resolved = outcome.status == "accepted"
        review = self._source_reviews.get(reference.source_id)
        source_provenance_attested = (
            review is not None and review.get("status") == "attested_unverified"
        )
        claim_support_attested = False
        if (
            reference_resolved
            and source_provenance_attested
            and source is not None
            and source.status == "active"
        ):
            claim_digest = _digest(canonical_text_v1(claim_text.encode("utf-8")).encode("utf-8"))
            review_key = (
                fact_id,
                claim_digest,
                reference.reference_id,
                reference.reference_digest,
            )
            claim_review = self._claim_support_reviews.get(review_key)
            claim_support_attested = claim_review is not None and claim_review[0] == "supports"
        return WorldSkillsEvidenceResult(
            reference_state=(
                "REFERENCE_RESOLVED" if reference_resolved else "REFERENCE_UNRESOLVED"
            ),
            source_provenance_state=(
                "SOURCE_PROVENANCE_ATTESTED_UNVERIFIED"
                if source_provenance_attested
                else "SOURCE_PROVENANCE_NOT_ATTESTED"
            ),
            claim_support_state=(
                "CLAIM_SUPPORT_ATTESTED_UNVERIFIED"
                if claim_support_attested
                else "CLAIM_SUPPORT_NOT_ESTABLISHED"
            ),
            validation_status=outcome.status,
            source_status=source.status if source is not None else None,
            validation_receipt_digest=receipt.receipt_digest,
        )


__all__ = [
    "CANDIDATE_SOURCE_PATH",
    "OWNER_REVIEW_MANIFEST_RELATIVE_PATH",
    "WORLD_SKILLS_CANONICAL_TEXT_POLICY_VERSION",
    "WORLD_SKILLS_REVIEW_MANIFEST_SCHEMA_VERSION",
    "WorldSkillsEvidenceResolver",
    "WorldSkillsEvidenceResult",
    "WorldSkillsManifestError",
    "canonical_text_v1",
]
