"""Immutable, local-only evidence-reference contract.

This v1 module is intentionally contract-only. It does not perform network I/O,
mutate Canon, resolve sources, or change TruthGate admission. Resolution and
validation are owned by :mod:`core.evidence_registry`.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping

EVIDENCE_REFERENCE_SCHEMA_VERSION = 1
EVIDENCE_REFERENCE_POLICY_VERSION = "evidence-reference-v1"

_REFERENCE_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_DIGEST_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
# v1 accepts exactly one ASCII representation per numeric span component.
_SPAN_PATTERN = re.compile(r"^chars:(0|[1-9][0-9]*)-(0|[1-9][0-9]*)$")
# Keep int conversion bounded and deterministic. This is a representation limit,
# not an evidence-policy, retrieval, admission, or runtime behavior change.
_MAX_SPAN_COMPONENT_DIGITS = 18
# UTC second precision is deliberately strict in v1.  It rejects equivalent
# aliases such as +00:00, fractional .000Z, lower-case t/z and Unicode digits.
_TIMESTAMP_PATTERN = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$")
_REQUIRED_FIELDS = frozenset(
    {
        "schema_version",
        "reference_id",
        "source_id",
        "source_digest",
        "fragment_id",
        "fragment_digest",
        "span",
        "lineage_id",
        "captured_at",
    }
)


class EvidenceReferenceError(ValueError):
    """Raised when an evidence-reference payload violates the v1 contract."""


def _require_identifier(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not _REFERENCE_ID_PATTERN.fullmatch(value):
        raise EvidenceReferenceError(
            f"{field_name} must be a safe 1-128 character technical identifier"
        )
    return value


def _require_digest(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not _DIGEST_PATTERN.fullmatch(value):
        raise EvidenceReferenceError(
            f"{field_name} must be a lower-case sha256:<64 hex> digest"
        )
    return value


def _require_span(value: object) -> str:
    if not isinstance(value, str) or _SPAN_PATTERN.fullmatch(value) is None:
        raise EvidenceReferenceError(
            "span must use canonical ASCII chars:<start>-<end> form"
        )
    start_text, end_text = value.removeprefix("chars:").split("-", maxsplit=1)
    if (
        len(start_text) > _MAX_SPAN_COMPONENT_DIGITS
        or len(end_text) > _MAX_SPAN_COMPONENT_DIGITS
    ):
        raise EvidenceReferenceError(
            "span decimal components must contain at most "
            f"{_MAX_SPAN_COMPONENT_DIGITS} ASCII digits"
        )
    start, end = int(start_text), int(end_text)
    if end <= start:
        raise EvidenceReferenceError("span end must be greater than span start")
    return value


def _require_timestamp(value: object) -> str:
    if not isinstance(value, str) or _TIMESTAMP_PATTERN.fullmatch(value) is None:
        raise EvidenceReferenceError(
            "captured_at must use canonical RFC3339 UTC second precision "
            "YYYY-MM-DDTHH:MM:SSZ"
        )
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise EvidenceReferenceError(
            "captured_at must use canonical RFC3339 UTC second precision "
            "YYYY-MM-DDTHH:MM:SSZ"
        ) from exc
    return value


@dataclass(frozen=True, slots=True)
class EvidenceReference:
    """One integrity-pinned reference to a local evidence fragment.

    The reference contains only technical identifiers, digests, a local fragment
    selector and lineage metadata. It deliberately excludes raw source content,
    quotes, URLs, credentials and provider payloads.
    """

    schema_version: int
    reference_id: str
    source_id: str
    source_digest: str
    fragment_id: str
    fragment_digest: str
    span: str
    lineage_id: str
    captured_at: str

    def __post_init__(self) -> None:
        if (
            not isinstance(self.schema_version, int)
            or isinstance(self.schema_version, bool)
            or self.schema_version != EVIDENCE_REFERENCE_SCHEMA_VERSION
        ):
            raise EvidenceReferenceError(
                f"schema_version must equal {EVIDENCE_REFERENCE_SCHEMA_VERSION}"
            )
        _require_identifier(self.reference_id, "reference_id")
        _require_identifier(self.source_id, "source_id")
        _require_digest(self.source_digest, "source_digest")
        _require_identifier(self.fragment_id, "fragment_id")
        _require_digest(self.fragment_digest, "fragment_digest")
        _require_span(self.span)
        _require_identifier(self.lineage_id, "lineage_id")
        _require_timestamp(self.captured_at)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> EvidenceReference:
        """Parse an exact v1 mapping and reject missing or unknown fields."""
        if not isinstance(payload, Mapping):
            raise EvidenceReferenceError("evidence reference payload must be a mapping")
        try:
            payload_snapshot = dict(payload)
        except (KeyError, TypeError, ValueError, RuntimeError) as exc:
            raise EvidenceReferenceError(
                "evidence reference payload could not be read consistently"
            ) from exc
        payload_keys = tuple(payload_snapshot.keys())
        if any(not isinstance(key, str) for key in payload_keys):
            raise EvidenceReferenceError("evidence reference field names must be strings")
        keys = frozenset(payload_keys)
        missing = _REQUIRED_FIELDS - keys
        unexpected = keys - _REQUIRED_FIELDS
        if missing or unexpected:
            details: list[str] = []
            if missing:
                details.append("missing=" + ",".join(sorted(missing)))
            if unexpected:
                details.append("unexpected=" + ",".join(sorted(unexpected)))
            raise EvidenceReferenceError("invalid evidence reference fields: " + "; ".join(details))
        return cls(
            schema_version=payload_snapshot["schema_version"],
            reference_id=payload_snapshot["reference_id"],
            source_id=payload_snapshot["source_id"],
            source_digest=payload_snapshot["source_digest"],
            fragment_id=payload_snapshot["fragment_id"],
            fragment_digest=payload_snapshot["fragment_digest"],
            span=payload_snapshot["span"],
            lineage_id=payload_snapshot["lineage_id"],
            captured_at=payload_snapshot["captured_at"],
        )

    def to_mapping(self) -> dict[str, object]:
        """Return the canonical serializable v1 mapping."""
        return {
            "captured_at": self.captured_at,
            "fragment_digest": self.fragment_digest,
            "fragment_id": self.fragment_id,
            "lineage_id": self.lineage_id,
            "reference_id": self.reference_id,
            "schema_version": self.schema_version,
            "source_digest": self.source_digest,
            "source_id": self.source_id,
            "span": self.span,
        }

    def canonical_json_bytes(self) -> bytes:
        """Encode the reference deterministically for identity and receipt binding."""
        return json.dumps(
            self.to_mapping(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

    @property
    def reference_digest(self) -> str:
        """Return a content-minimized stable identifier for this exact reference."""
        return "sha256:" + hashlib.sha256(self.canonical_json_bytes()).hexdigest()


__all__ = [
    "EVIDENCE_REFERENCE_POLICY_VERSION",
    "EVIDENCE_REFERENCE_SCHEMA_VERSION",
    "EvidenceReference",
    "EvidenceReferenceError",
]
