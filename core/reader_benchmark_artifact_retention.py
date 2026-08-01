"""Signed local backing-artifact retention for Reader Core PR-RDR-24.

The module binds every artifact ID in verified RDR-23 signed evidence to one
local regular file, records deterministic SHA-256/size metadata, signs the
retention manifest, and can re-verify the backing bytes later. It does not embed
artifact bytes, upload data, execute Reader Core, or grant promotion authority.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import Enum
import hashlib
import hmac
import json
import os
from pathlib import Path, PurePosixPath
import stat
from typing import Any, cast

from core.reader_benchmark_evidence_verification import (
    ReaderBenchmarkEvidenceVerificationReceipt,
)
from core.reader_benchmark_runner import canonical_json_bytes, write_canonical_json
from core.reader_core_contracts import stable_reader_core_id
from core.reader_evaluation import PromotionDecision

READER_ARTIFACT_RETENTION_SOURCE_SPEC_SCHEMA_VERSION = (
    "reader-core.artifact-retention-source-spec.v1"
)
READER_ARTIFACT_RETENTION_MANIFEST_SCHEMA_VERSION = (
    "reader-core.artifact-retention-manifest.v1"
)
READER_ARTIFACT_RETENTION_SIGNATURE_SCHEMA_VERSION = (
    "reader-core.artifact-retention-signature.v1"
)
READER_ARTIFACT_RETENTION_VERIFICATION_SCHEMA_VERSION = (
    "reader-core.artifact-retention-verification.v1"
)
READER_ARTIFACT_RETENTION_SIGNATURE_ALGORITHM = "hmac-sha256"
DEFAULT_MAX_ARTIFACT_BYTES = 512 * 1024 * 1024
DEFAULT_MAX_TOTAL_BYTES = 4 * 1024 * 1024 * 1024


class ReaderArtifactRetentionError(ValueError):
    """Raised when backing-artifact retention is malformed or unverifiable."""


class ArtifactRetentionClass(str, Enum):
    BENCHMARK_OUTPUT = "benchmark_output"
    PIPELINE_TRACE = "pipeline_trace"
    MEASUREMENT = "measurement"
    REPLAY = "replay"
    OTHER = "other"


@dataclass(frozen=True, slots=True)
class ReaderArtifactRetentionSourceEntry:
    artifact_id: str
    relative_path: str
    media_type: str
    retention_class: ArtifactRetentionClass
    entry_id: str = ""

    def __post_init__(self) -> None:
        _text(self.artifact_id, "artifact_id")
        normalized_path = _relative_path(self.relative_path)
        _text(self.media_type, "media_type")
        if not isinstance(self.retention_class, ArtifactRetentionClass):
            raise ReaderArtifactRetentionError(
                "retention_class must be an ArtifactRetentionClass"
            )
        object.__setattr__(self, "relative_path", normalized_path)
        expected = stable_reader_core_id(
            "reader-artifact-retention-source-entry",
            self.identity_payload(include_id=False),
        )
        if self.entry_id:
            if self.entry_id != expected:
                raise ReaderArtifactRetentionError(
                    "entry_id does not match source entry content"
                )
        else:
            object.__setattr__(self, "entry_id", expected)

    def source_payload(self) -> dict[str, object]:
        return {
            "artifact_id": self.artifact_id,
            "relative_path": self.relative_path,
            "media_type": self.media_type,
            "retention_class": self.retention_class.value,
        }

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload = self.source_payload()
        if include_id:
            payload["entry_id"] = self.entry_id
        return payload


@dataclass(frozen=True, slots=True)
class ReaderArtifactRetentionSourceSpec:
    evidence_id: str
    evidence_verification_id: str
    artifacts: tuple[ReaderArtifactRetentionSourceEntry, ...]
    schema_version: str = READER_ARTIFACT_RETENTION_SOURCE_SPEC_SCHEMA_VERSION
    spec_id: str = ""

    def __post_init__(self) -> None:
        _text(self.evidence_id, "evidence_id")
        _text(self.evidence_verification_id, "evidence_verification_id")
        if self.schema_version != READER_ARTIFACT_RETENTION_SOURCE_SPEC_SCHEMA_VERSION:
            raise ReaderArtifactRetentionError(
                "unsupported artifact retention source-spec schema"
            )
        entries = tuple(self.artifacts)
        if not entries or any(
            not isinstance(item, ReaderArtifactRetentionSourceEntry)
            for item in entries
        ):
            raise ReaderArtifactRetentionError(
                "artifacts require ReaderArtifactRetentionSourceEntry values"
            )
        ordered = tuple(sorted(entries, key=lambda item: item.artifact_id))
        if len({item.artifact_id for item in ordered}) != len(ordered):
            raise ReaderArtifactRetentionError(
                "source artifact IDs must be unique"
            )
        if len({item.relative_path for item in ordered}) != len(ordered):
            raise ReaderArtifactRetentionError(
                "source artifact relative paths must be unique"
            )
        object.__setattr__(self, "artifacts", ordered)
        expected = stable_reader_core_id(
            "reader-artifact-retention-source-spec",
            self.identity_payload(include_id=False),
        )
        if self.spec_id:
            if self.spec_id != expected:
                raise ReaderArtifactRetentionError(
                    "spec_id does not match source spec content"
                )
        else:
            object.__setattr__(self, "spec_id", expected)

    def source_payload(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "evidence_id": self.evidence_id,
            "evidence_verification_id": self.evidence_verification_id,
            "artifacts": [item.source_payload() for item in self.artifacts],
        }

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema_version": self.schema_version,
            "evidence_id": self.evidence_id,
            "evidence_verification_id": self.evidence_verification_id,
            "entry_ids": [item.entry_id for item in self.artifacts],
        }
        if include_id:
            payload["spec_id"] = self.spec_id
        return payload


@dataclass(frozen=True, slots=True)
class ReaderVerifiedEvidenceArtifactIndex:
    evidence_id: str
    evidence_verification_id: str
    benchmark_bundle_id: str
    benchmark_signature_id: str
    evidence_file_sha256: str
    artifact_ids: tuple[str, ...]
    decision: PromotionDecision
    operator_go_required: bool
    live_integration_authorized: bool
    index_id: str = ""

    def __post_init__(self) -> None:
        for name in (
            "evidence_id",
            "evidence_verification_id",
            "benchmark_bundle_id",
            "benchmark_signature_id",
        ):
            _text(getattr(self, name), name)
        _sha256(self.evidence_file_sha256, "evidence_file_sha256")
        artifact_ids = _unique_sorted_text(self.artifact_ids, "artifact_id")
        if not artifact_ids:
            raise ReaderArtifactRetentionError(
                "verified evidence must reference at least one artifact ID"
            )
        if not isinstance(self.decision, PromotionDecision):
            raise ReaderArtifactRetentionError(
                "decision must be a PromotionDecision"
            )
        _authority_boundary(
            self.operator_go_required,
            self.live_integration_authorized,
        )
        object.__setattr__(self, "artifact_ids", artifact_ids)
        expected = stable_reader_core_id(
            "reader-verified-evidence-artifact-index",
            self.identity_payload(include_id=False),
        )
        if self.index_id:
            if self.index_id != expected:
                raise ReaderArtifactRetentionError(
                    "index_id does not match verified artifact index"
                )
        else:
            object.__setattr__(self, "index_id", expected)

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "evidence_id": self.evidence_id,
            "evidence_verification_id": self.evidence_verification_id,
            "benchmark_bundle_id": self.benchmark_bundle_id,
            "benchmark_signature_id": self.benchmark_signature_id,
            "evidence_file_sha256": self.evidence_file_sha256,
            "artifact_ids": list(self.artifact_ids),
            "decision": self.decision.value,
            "operator_go_required": self.operator_go_required,
            "live_integration_authorized": self.live_integration_authorized,
        }
        if include_id:
            payload["index_id"] = self.index_id
        return payload


@dataclass(frozen=True, slots=True)
class ReaderRetainedBenchmarkArtifact:
    artifact_id: str
    relative_path: str
    media_type: str
    retention_class: ArtifactRetentionClass
    content_sha256: str
    byte_size: int
    record_id: str = ""

    def __post_init__(self) -> None:
        _text(self.artifact_id, "artifact_id")
        normalized_path = _relative_path(self.relative_path)
        _text(self.media_type, "media_type")
        if not isinstance(self.retention_class, ArtifactRetentionClass):
            raise ReaderArtifactRetentionError(
                "retention_class must be an ArtifactRetentionClass"
            )
        _sha256(self.content_sha256, "content_sha256")
        _nonnegative_int(self.byte_size, "byte_size")
        object.__setattr__(self, "relative_path", normalized_path)
        expected = stable_reader_core_id(
            "reader-retained-benchmark-artifact",
            self.identity_payload(include_id=False),
        )
        if self.record_id:
            if self.record_id != expected:
                raise ReaderArtifactRetentionError(
                    "record_id does not match retained artifact content"
                )
        else:
            object.__setattr__(self, "record_id", expected)

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "artifact_id": self.artifact_id,
            "relative_path": self.relative_path,
            "media_type": self.media_type,
            "retention_class": self.retention_class.value,
            "content_sha256": self.content_sha256,
            "byte_size": self.byte_size,
        }
        if include_id:
            payload["record_id"] = self.record_id
        return payload


@dataclass(frozen=True, slots=True)
class ReaderBenchmarkArtifactRetentionManifest:
    evidence_id: str
    evidence_verification_id: str
    benchmark_bundle_id: str
    benchmark_signature_id: str
    evidence_file_sha256: str
    source_spec_id: str
    artifact_index_id: str
    artifacts: tuple[ReaderRetainedBenchmarkArtifact, ...]
    total_byte_size: int
    decision: PromotionDecision
    operator_go_required: bool
    live_integration_authorized: bool
    schema_version: str = READER_ARTIFACT_RETENTION_MANIFEST_SCHEMA_VERSION
    manifest_id: str = ""

    def __post_init__(self) -> None:
        for name in (
            "evidence_id",
            "evidence_verification_id",
            "benchmark_bundle_id",
            "benchmark_signature_id",
            "source_spec_id",
            "artifact_index_id",
        ):
            _text(getattr(self, name), name)
        _sha256(self.evidence_file_sha256, "evidence_file_sha256")
        if self.schema_version != READER_ARTIFACT_RETENTION_MANIFEST_SCHEMA_VERSION:
            raise ReaderArtifactRetentionError(
                "unsupported artifact retention manifest schema"
            )
        records = tuple(self.artifacts)
        if not records or any(
            not isinstance(item, ReaderRetainedBenchmarkArtifact)
            for item in records
        ):
            raise ReaderArtifactRetentionError(
                "artifacts require ReaderRetainedBenchmarkArtifact values"
            )
        ordered = tuple(sorted(records, key=lambda item: item.artifact_id))
        if records != ordered:
            raise ReaderArtifactRetentionError(
                "retained artifacts must use canonical artifact-ID order"
            )
        if len({item.artifact_id for item in records}) != len(records):
            raise ReaderArtifactRetentionError(
                "retained artifact IDs must be unique"
            )
        if len({item.relative_path for item in records}) != len(records):
            raise ReaderArtifactRetentionError(
                "retained artifact relative paths must be unique"
            )
        _nonnegative_int(self.total_byte_size, "total_byte_size")
        if self.total_byte_size != sum(item.byte_size for item in records):
            raise ReaderArtifactRetentionError(
                "total_byte_size must equal retained artifact sizes"
            )
        if not isinstance(self.decision, PromotionDecision):
            raise ReaderArtifactRetentionError(
                "decision must be a PromotionDecision"
            )
        _authority_boundary(
            self.operator_go_required,
            self.live_integration_authorized,
        )
        object.__setattr__(self, "artifacts", records)
        expected = stable_reader_core_id(
            "reader-benchmark-artifact-retention-manifest",
            self.identity_payload(include_id=False),
        )
        if self.manifest_id:
            if self.manifest_id != expected:
                raise ReaderArtifactRetentionError(
                    "manifest_id does not match retention manifest content"
                )
        else:
            object.__setattr__(self, "manifest_id", expected)

    @property
    def artifact_ids(self) -> tuple[str, ...]:
        return tuple(item.artifact_id for item in self.artifacts)

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema_version": self.schema_version,
            "evidence_id": self.evidence_id,
            "evidence_verification_id": self.evidence_verification_id,
            "benchmark_bundle_id": self.benchmark_bundle_id,
            "benchmark_signature_id": self.benchmark_signature_id,
            "evidence_file_sha256": self.evidence_file_sha256,
            "source_spec_id": self.source_spec_id,
            "artifact_index_id": self.artifact_index_id,
            "record_ids": [item.record_id for item in self.artifacts],
            "total_byte_size": self.total_byte_size,
            "decision": self.decision.value,
            "operator_go_required": self.operator_go_required,
            "live_integration_authorized": self.live_integration_authorized,
        }
        if include_id:
            payload["manifest_id"] = self.manifest_id
        return payload


@dataclass(frozen=True, slots=True)
class ReaderArtifactRetentionSignature:
    manifest_id: str
    key_id: str
    manifest_sha256: str
    signature_hex: str
    algorithm: str = READER_ARTIFACT_RETENTION_SIGNATURE_ALGORITHM
    schema_version: str = READER_ARTIFACT_RETENTION_SIGNATURE_SCHEMA_VERSION
    signature_id: str = ""

    def __post_init__(self) -> None:
        _text(self.manifest_id, "manifest_id")
        _text(self.key_id, "key_id")
        if self.algorithm != READER_ARTIFACT_RETENTION_SIGNATURE_ALGORITHM:
            raise ReaderArtifactRetentionError(
                "unsupported artifact retention signature algorithm"
            )
        if self.schema_version != READER_ARTIFACT_RETENTION_SIGNATURE_SCHEMA_VERSION:
            raise ReaderArtifactRetentionError(
                "unsupported artifact retention signature schema"
            )
        _sha256(self.manifest_sha256, "manifest_sha256")
        _sha256(self.signature_hex, "signature_hex")
        expected = stable_reader_core_id(
            "reader-artifact-retention-signature",
            self.identity_payload(include_id=False),
        )
        if self.signature_id:
            if self.signature_id != expected:
                raise ReaderArtifactRetentionError(
                    "signature_id does not match retention signature content"
                )
        else:
            object.__setattr__(self, "signature_id", expected)

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "manifest_id": self.manifest_id,
            "key_id": self.key_id,
            "manifest_sha256": self.manifest_sha256,
            "signature_hex": self.signature_hex,
            "algorithm": self.algorithm,
            "schema_version": self.schema_version,
        }
        if include_id:
            payload["signature_id"] = self.signature_id
        return payload


@dataclass(frozen=True, slots=True)
class ReaderArtifactRetentionVerificationReceipt:
    manifest_id: str
    retention_signature_id: str
    evidence_id: str
    evidence_verification_id: str
    verified_record_ids: tuple[str, ...]
    verified_artifact_count: int
    verified_total_byte_size: int
    decision: PromotionDecision
    operator_go_required: bool
    live_integration_authorized: bool
    schema_version: str = READER_ARTIFACT_RETENTION_VERIFICATION_SCHEMA_VERSION
    verification_id: str = ""

    def __post_init__(self) -> None:
        for name in (
            "manifest_id",
            "retention_signature_id",
            "evidence_id",
            "evidence_verification_id",
        ):
            _text(getattr(self, name), name)
        records = _unique_sorted_text(
            self.verified_record_ids,
            "verified_record_id",
        )
        _nonnegative_int(
            self.verified_artifact_count,
            "verified_artifact_count",
        )
        _nonnegative_int(
            self.verified_total_byte_size,
            "verified_total_byte_size",
        )
        if self.verified_artifact_count != len(records):
            raise ReaderArtifactRetentionError(
                "verified_artifact_count must equal verified record count"
            )
        if not isinstance(self.decision, PromotionDecision):
            raise ReaderArtifactRetentionError(
                "decision must be a PromotionDecision"
            )
        _authority_boundary(
            self.operator_go_required,
            self.live_integration_authorized,
        )
        if self.schema_version != READER_ARTIFACT_RETENTION_VERIFICATION_SCHEMA_VERSION:
            raise ReaderArtifactRetentionError(
                "unsupported artifact retention verification schema"
            )
        object.__setattr__(self, "verified_record_ids", records)
        expected = stable_reader_core_id(
            "reader-artifact-retention-verification",
            self.identity_payload(include_id=False),
        )
        if self.verification_id:
            if self.verification_id != expected:
                raise ReaderArtifactRetentionError(
                    "verification_id does not match retention verification"
                )
        else:
            object.__setattr__(self, "verification_id", expected)

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema_version": self.schema_version,
            "manifest_id": self.manifest_id,
            "retention_signature_id": self.retention_signature_id,
            "evidence_id": self.evidence_id,
            "evidence_verification_id": self.evidence_verification_id,
            "verified_record_ids": list(self.verified_record_ids),
            "verified_artifact_count": self.verified_artifact_count,
            "verified_total_byte_size": self.verified_total_byte_size,
            "decision": self.decision.value,
            "operator_go_required": self.operator_go_required,
            "live_integration_authorized": self.live_integration_authorized,
        }
        if include_id:
            payload["verification_id"] = self.verification_id
        return payload


class ReaderBenchmarkArtifactRetentionBuilder:
    """Bind every verified evidence artifact ID to one bounded local file."""

    def build(
        self,
        *,
        root: str | Path,
        artifact_index: ReaderVerifiedEvidenceArtifactIndex,
        source_spec: ReaderArtifactRetentionSourceSpec,
        max_artifact_bytes: int = DEFAULT_MAX_ARTIFACT_BYTES,
        max_total_bytes: int = DEFAULT_MAX_TOTAL_BYTES,
    ) -> ReaderBenchmarkArtifactRetentionManifest:
        if not isinstance(artifact_index, ReaderVerifiedEvidenceArtifactIndex):
            raise ReaderArtifactRetentionError(
                "artifact_index must be a ReaderVerifiedEvidenceArtifactIndex"
            )
        if not isinstance(source_spec, ReaderArtifactRetentionSourceSpec):
            raise ReaderArtifactRetentionError(
                "source_spec must be a ReaderArtifactRetentionSourceSpec"
            )
        _positive_int(max_artifact_bytes, "max_artifact_bytes")
        _positive_int(max_total_bytes, "max_total_bytes")
        if source_spec.evidence_id != artifact_index.evidence_id:
            raise ReaderArtifactRetentionError(
                "source spec belongs to a different evidence artifact"
            )
        if (
            source_spec.evidence_verification_id
            != artifact_index.evidence_verification_id
        ):
            raise ReaderArtifactRetentionError(
                "source spec belongs to a different evidence verification"
            )
        expected_ids = set(artifact_index.artifact_ids)
        supplied_ids = {item.artifact_id for item in source_spec.artifacts}
        if supplied_ids != expected_ids:
            missing = sorted(expected_ids - supplied_ids)
            extra = sorted(supplied_ids - expected_ids)
            raise ReaderArtifactRetentionError(
                "source spec must exactly cover evidence artifact IDs; "
                f"missing={missing}, extra={extra}"
            )
        root_path = Path(root)
        if root_path.is_symlink():
            raise ReaderArtifactRetentionError("artifact root must not be a symlink")
        root_path = root_path.resolve()
        if not root_path.is_dir():
            raise ReaderArtifactRetentionError(
                "artifact root must be an existing directory"
            )
        records: list[ReaderRetainedBenchmarkArtifact] = []
        total = 0
        for entry in source_spec.artifacts:
            path = _secure_artifact_path(root_path, entry.relative_path)
            digest, byte_size = _hash_regular_file(
                path,
                max_artifact_bytes=max_artifact_bytes,
            )
            total += byte_size
            if total > max_total_bytes:
                raise ReaderArtifactRetentionError(
                    "retained artifact total exceeds max_total_bytes"
                )
            records.append(
                ReaderRetainedBenchmarkArtifact(
                    artifact_id=entry.artifact_id,
                    relative_path=entry.relative_path,
                    media_type=entry.media_type,
                    retention_class=entry.retention_class,
                    content_sha256=digest,
                    byte_size=byte_size,
                )
            )
        return ReaderBenchmarkArtifactRetentionManifest(
            evidence_id=artifact_index.evidence_id,
            evidence_verification_id=artifact_index.evidence_verification_id,
            benchmark_bundle_id=artifact_index.benchmark_bundle_id,
            benchmark_signature_id=artifact_index.benchmark_signature_id,
            evidence_file_sha256=artifact_index.evidence_file_sha256,
            source_spec_id=source_spec.spec_id,
            artifact_index_id=artifact_index.index_id,
            artifacts=tuple(records),
            total_byte_size=total,
            decision=artifact_index.decision,
            operator_go_required=artifact_index.operator_go_required,
            live_integration_authorized=(
                artifact_index.live_integration_authorized
            ),
        )


class ReaderArtifactRetentionSigner:
    @staticmethod
    def sign(
        manifest: ReaderBenchmarkArtifactRetentionManifest,
        *,
        key_id: str,
        secret: bytes,
    ) -> ReaderArtifactRetentionSignature:
        if not isinstance(manifest, ReaderBenchmarkArtifactRetentionManifest):
            raise ReaderArtifactRetentionError(
                "manifest must be a ReaderBenchmarkArtifactRetentionManifest"
            )
        _text(key_id, "key_id")
        _secret(secret)
        manifest_bytes = canonical_json_bytes(manifest)
        return ReaderArtifactRetentionSignature(
            manifest_id=manifest.manifest_id,
            key_id=key_id,
            manifest_sha256=hashlib.sha256(manifest_bytes).hexdigest(),
            signature_hex=hmac.new(
                secret,
                manifest_bytes,
                hashlib.sha256,
            ).hexdigest(),
        )

    @staticmethod
    def verify(
        manifest: ReaderBenchmarkArtifactRetentionManifest,
        signature: ReaderArtifactRetentionSignature,
        *,
        secret: bytes,
    ) -> bool:
        if not isinstance(manifest, ReaderBenchmarkArtifactRetentionManifest):
            raise ReaderArtifactRetentionError(
                "manifest must be a ReaderBenchmarkArtifactRetentionManifest"
            )
        if not isinstance(signature, ReaderArtifactRetentionSignature):
            raise ReaderArtifactRetentionError(
                "signature must be a ReaderArtifactRetentionSignature"
            )
        _secret(secret)
        if signature.manifest_id != manifest.manifest_id:
            return False
        manifest_bytes = canonical_json_bytes(manifest)
        digest = hashlib.sha256(manifest_bytes).hexdigest()
        if not hmac.compare_digest(signature.manifest_sha256, digest):
            return False
        expected = hmac.new(secret, manifest_bytes, hashlib.sha256).hexdigest()
        return hmac.compare_digest(signature.signature_hex, expected)


class ReaderBenchmarkArtifactRetentionVerifier:
    """Authenticate a retention manifest and re-hash every backing file."""

    def verify(
        self,
        *,
        root: str | Path,
        manifest: ReaderBenchmarkArtifactRetentionManifest,
        signature: ReaderArtifactRetentionSignature,
        secret: bytes,
        max_artifact_bytes: int = DEFAULT_MAX_ARTIFACT_BYTES,
        max_total_bytes: int = DEFAULT_MAX_TOTAL_BYTES,
    ) -> ReaderArtifactRetentionVerificationReceipt:
        if not ReaderArtifactRetentionSigner.verify(
            manifest,
            signature,
            secret=secret,
        ):
            raise ReaderArtifactRetentionError(
                "artifact retention signature verification failed"
            )
        _positive_int(max_artifact_bytes, "max_artifact_bytes")
        _positive_int(max_total_bytes, "max_total_bytes")
        if manifest.total_byte_size > max_total_bytes:
            raise ReaderArtifactRetentionError(
                "manifest total exceeds max_total_bytes"
            )
        root_path = Path(root)
        if root_path.is_symlink():
            raise ReaderArtifactRetentionError("artifact root must not be a symlink")
        root_path = root_path.resolve()
        if not root_path.is_dir():
            raise ReaderArtifactRetentionError(
                "artifact root must be an existing directory"
            )
        verified_total = 0
        for record in manifest.artifacts:
            path = _secure_artifact_path(root_path, record.relative_path)
            digest, byte_size = _hash_regular_file(
                path,
                max_artifact_bytes=max_artifact_bytes,
            )
            if byte_size != record.byte_size:
                raise ReaderArtifactRetentionError(
                    f"artifact size mismatch: {record.artifact_id}"
                )
            if not hmac.compare_digest(digest, record.content_sha256):
                raise ReaderArtifactRetentionError(
                    f"artifact digest mismatch: {record.artifact_id}"
                )
            verified_total += byte_size
        if verified_total != manifest.total_byte_size:
            raise ReaderArtifactRetentionError(
                "verified total does not match retention manifest"
            )
        return ReaderArtifactRetentionVerificationReceipt(
            manifest_id=manifest.manifest_id,
            retention_signature_id=signature.signature_id,
            evidence_id=manifest.evidence_id,
            evidence_verification_id=manifest.evidence_verification_id,
            verified_record_ids=tuple(
                item.record_id for item in manifest.artifacts
            ),
            verified_artifact_count=len(manifest.artifacts),
            verified_total_byte_size=verified_total,
            decision=manifest.decision,
            operator_go_required=manifest.operator_go_required,
            live_integration_authorized=(
                manifest.live_integration_authorized
            ),
        )


def extract_verified_evidence_artifact_index(
    *,
    evidence_path: str | Path,
    verification: ReaderBenchmarkEvidenceVerificationReceipt,
) -> ReaderVerifiedEvidenceArtifactIndex:
    if not isinstance(verification, ReaderBenchmarkEvidenceVerificationReceipt):
        raise ReaderArtifactRetentionError(
            "verification must be a ReaderBenchmarkEvidenceVerificationReceipt"
        )
    payload, raw = _load_canonical_object(evidence_path, "signed benchmark evidence")
    digest = hashlib.sha256(raw).hexdigest()
    if not hmac.compare_digest(digest, verification.evidence_file_sha256):
        raise ReaderArtifactRetentionError(
            "evidence file changed after benchmark evidence verification"
        )
    _keys(
        payload,
        required={
            "preparation_id",
            "execution_state",
            "benchmark_bundle",
            "bundle_signature",
            "receipt_ids",
            "failed_attempt_receipt_ids",
            "artifact_ids",
            "schema_version",
            "evidence_id",
        },
        field_name="signed benchmark evidence",
    )
    evidence_id = _text(payload["evidence_id"], "evidence_id")
    bundle = _mapping(payload["benchmark_bundle"], "benchmark_bundle")
    signature = _mapping(payload["bundle_signature"], "bundle_signature")
    review = _mapping(bundle.get("review"), "review")
    bundle_id = _text(bundle.get("bundle_id"), "bundle_id")
    signature_id = _text(signature.get("signature_id"), "signature_id")
    decision = _enum(
        PromotionDecision,
        review.get("decision"),
        "decision",
    )
    operator_go_required = _bool(
        review.get("operator_go_required"),
        "operator_go_required",
    )
    live_authorized = _bool(
        review.get("live_integration_authorized"),
        "live_integration_authorized",
    )
    if evidence_id != verification.evidence_id:
        raise ReaderArtifactRetentionError(
            "evidence ID does not match benchmark verification receipt"
        )
    if bundle_id != verification.benchmark_bundle_id:
        raise ReaderArtifactRetentionError(
            "bundle ID does not match benchmark verification receipt"
        )
    if signature_id != verification.signature_id:
        raise ReaderArtifactRetentionError(
            "signature ID does not match benchmark verification receipt"
        )
    if decision is not verification.decision:
        raise ReaderArtifactRetentionError(
            "review decision does not match benchmark verification receipt"
        )
    if operator_go_required != verification.operator_go_required:
        raise ReaderArtifactRetentionError(
            "Operator GO boundary does not match benchmark verification receipt"
        )
    if live_authorized != verification.live_integration_authorized:
        raise ReaderArtifactRetentionError(
            "live-authorization boundary does not match verification receipt"
        )
    return ReaderVerifiedEvidenceArtifactIndex(
        evidence_id=evidence_id,
        evidence_verification_id=verification.verification_id,
        benchmark_bundle_id=bundle_id,
        benchmark_signature_id=signature_id,
        evidence_file_sha256=digest,
        artifact_ids=_text_array(payload["artifact_ids"], "artifact_id"),
        decision=decision,
        operator_go_required=operator_go_required,
        live_integration_authorized=live_authorized,
    )


def load_artifact_retention_source_spec(
    path: str | Path,
) -> ReaderArtifactRetentionSourceSpec:
    payload, raw = _load_canonical_object(path, "artifact retention source spec")
    _keys(
        payload,
        required={
            "schema_version",
            "evidence_id",
            "evidence_verification_id",
            "artifacts",
        },
        field_name="artifact retention source spec",
    )
    entries_raw = _list(payload["artifacts"], "artifacts")
    spec = ReaderArtifactRetentionSourceSpec(
        schema_version=_text(payload["schema_version"], "schema_version"),
        evidence_id=_text(payload["evidence_id"], "evidence_id"),
        evidence_verification_id=_text(
            payload["evidence_verification_id"],
            "evidence_verification_id",
        ),
        artifacts=tuple(
            _parse_source_entry(item, index=index)
            for index, item in enumerate(entries_raw)
        ),
    )
    if raw != canonical_json_bytes(spec.source_payload()) + b"\n":
        raise ReaderArtifactRetentionError(
            "artifact retention source spec must use canonical ordering"
        )
    return spec


def write_artifact_retention_source_spec(
    path: str | Path,
    spec: ReaderArtifactRetentionSourceSpec,
) -> None:
    if not isinstance(spec, ReaderArtifactRetentionSourceSpec):
        raise ReaderArtifactRetentionError(
            "spec must be a ReaderArtifactRetentionSourceSpec"
        )
    write_canonical_json(path, spec.source_payload())


def load_artifact_retention_manifest(
    path: str | Path,
) -> ReaderBenchmarkArtifactRetentionManifest:
    payload, raw = _load_canonical_object(path, "artifact retention manifest")
    _keys(
        payload,
        required={
            "evidence_id",
            "evidence_verification_id",
            "benchmark_bundle_id",
            "benchmark_signature_id",
            "evidence_file_sha256",
            "source_spec_id",
            "artifact_index_id",
            "artifacts",
            "total_byte_size",
            "decision",
            "operator_go_required",
            "live_integration_authorized",
            "schema_version",
            "manifest_id",
        },
        field_name="artifact retention manifest",
    )
    records_raw = _list(payload["artifacts"], "artifacts")
    manifest = ReaderBenchmarkArtifactRetentionManifest(
        evidence_id=_text(payload["evidence_id"], "evidence_id"),
        evidence_verification_id=_text(
            payload["evidence_verification_id"],
            "evidence_verification_id",
        ),
        benchmark_bundle_id=_text(
            payload["benchmark_bundle_id"],
            "benchmark_bundle_id",
        ),
        benchmark_signature_id=_text(
            payload["benchmark_signature_id"],
            "benchmark_signature_id",
        ),
        evidence_file_sha256=_text(
            payload["evidence_file_sha256"],
            "evidence_file_sha256",
        ),
        source_spec_id=_text(payload["source_spec_id"], "source_spec_id"),
        artifact_index_id=_text(
            payload["artifact_index_id"],
            "artifact_index_id",
        ),
        artifacts=tuple(
            _parse_retained_artifact(item, index=index)
            for index, item in enumerate(records_raw)
        ),
        total_byte_size=_int(payload["total_byte_size"], "total_byte_size"),
        decision=_enum(PromotionDecision, payload["decision"], "decision"),
        operator_go_required=_bool(
            payload["operator_go_required"],
            "operator_go_required",
        ),
        live_integration_authorized=_bool(
            payload["live_integration_authorized"],
            "live_integration_authorized",
        ),
        schema_version=_text(payload["schema_version"], "schema_version"),
        manifest_id=_text(payload["manifest_id"], "manifest_id"),
    )
    if raw != canonical_json_bytes(manifest) + b"\n":
        raise ReaderArtifactRetentionError(
            "artifact retention manifest is not canonical"
        )
    return manifest


def load_artifact_retention_signature(
    path: str | Path,
) -> ReaderArtifactRetentionSignature:
    payload, raw = _load_canonical_object(path, "artifact retention signature")
    _keys(
        payload,
        required={
            "manifest_id",
            "key_id",
            "manifest_sha256",
            "signature_hex",
            "algorithm",
            "schema_version",
            "signature_id",
        },
        field_name="artifact retention signature",
    )
    signature = ReaderArtifactRetentionSignature(
        manifest_id=_text(payload["manifest_id"], "manifest_id"),
        key_id=_text(payload["key_id"], "key_id"),
        manifest_sha256=_text(
            payload["manifest_sha256"],
            "manifest_sha256",
        ),
        signature_hex=_text(payload["signature_hex"], "signature_hex"),
        algorithm=_text(payload["algorithm"], "algorithm"),
        schema_version=_text(payload["schema_version"], "schema_version"),
        signature_id=_text(payload["signature_id"], "signature_id"),
    )
    if raw != canonical_json_bytes(signature) + b"\n":
        raise ReaderArtifactRetentionError(
            "artifact retention signature is not canonical"
        )
    return signature


def _parse_source_entry(
    value: object,
    *,
    index: int,
) -> ReaderArtifactRetentionSourceEntry:
    payload = _mapping(value, f"artifacts[{index}]")
    _keys(
        payload,
        required={
            "artifact_id",
            "relative_path",
            "media_type",
            "retention_class",
        },
        field_name=f"artifacts[{index}]",
    )
    return ReaderArtifactRetentionSourceEntry(
        artifact_id=_text(payload["artifact_id"], "artifact_id"),
        relative_path=_text(payload["relative_path"], "relative_path"),
        media_type=_text(payload["media_type"], "media_type"),
        retention_class=_enum(
            ArtifactRetentionClass,
            payload["retention_class"],
            "retention_class",
        ),
    )


def _parse_retained_artifact(
    value: object,
    *,
    index: int,
) -> ReaderRetainedBenchmarkArtifact:
    payload = _mapping(value, f"artifacts[{index}]")
    _keys(
        payload,
        required={
            "artifact_id",
            "relative_path",
            "media_type",
            "retention_class",
            "content_sha256",
            "byte_size",
            "record_id",
        },
        field_name=f"artifacts[{index}]",
    )
    return ReaderRetainedBenchmarkArtifact(
        artifact_id=_text(payload["artifact_id"], "artifact_id"),
        relative_path=_text(payload["relative_path"], "relative_path"),
        media_type=_text(payload["media_type"], "media_type"),
        retention_class=_enum(
            ArtifactRetentionClass,
            payload["retention_class"],
            "retention_class",
        ),
        content_sha256=_text(payload["content_sha256"], "content_sha256"),
        byte_size=_int(payload["byte_size"], "byte_size"),
        record_id=_text(payload["record_id"], "record_id"),
    )


def _secure_artifact_path(root: Path, relative_path: str) -> Path:
    relative = PurePosixPath(_relative_path(relative_path))
    candidate = root.joinpath(*relative.parts)
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ReaderArtifactRetentionError(
                f"artifact path must not contain symlinks: {relative_path}"
            )
    try:
        resolved = candidate.resolve(strict=True)
    except OSError as exc:
        raise ReaderArtifactRetentionError(
            f"artifact file is missing or inaccessible: {relative_path}"
        ) from exc
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ReaderArtifactRetentionError(
            f"artifact path escapes root: {relative_path}"
        ) from exc
    return resolved


def _hash_regular_file(
    path: Path,
    *,
    max_artifact_bytes: int,
) -> tuple[str, int]:
    flags = os.O_RDONLY
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise ReaderArtifactRetentionError(
            f"cannot open artifact file safely: {path.name}"
        ) from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise ReaderArtifactRetentionError(
                f"artifact path is not a regular file: {path.name}"
            )
        if before.st_size > max_artifact_bytes:
            raise ReaderArtifactRetentionError(
                f"artifact exceeds max_artifact_bytes: {path.name}"
            )
        digest = hashlib.sha256()
        byte_size = 0
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            byte_size += len(chunk)
            if byte_size > max_artifact_bytes:
                raise ReaderArtifactRetentionError(
                    f"artifact exceeds max_artifact_bytes: {path.name}"
                )
            digest.update(chunk)
        after = os.fstat(descriptor)
        identity_before = (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
        )
        identity_after = (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
        )
        if identity_before != identity_after or byte_size != after.st_size:
            raise ReaderArtifactRetentionError(
                f"artifact changed while hashing: {path.name}"
            )
        return digest.hexdigest(), byte_size
    finally:
        os.close(descriptor)


def _load_canonical_object(
    path: str | Path,
    field_name: str,
) -> tuple[dict[str, object], bytes]:
    source = Path(path)
    try:
        raw = source.read_bytes()
        value: Any = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_pairs,
            parse_constant=_reject_json_constant,
        )
    except ReaderArtifactRetentionError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ReaderArtifactRetentionError(
            f"cannot load {field_name} from {source}: {exc}"
        ) from exc
    payload = dict(_mapping(value, field_name))
    if raw != canonical_json_bytes(payload) + b"\n":
        raise ReaderArtifactRetentionError(
            f"{field_name} must use canonical JSON encoding"
        )
    return payload, raw


def _reject_duplicate_pairs(
    pairs: list[tuple[str, object]],
) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ReaderArtifactRetentionError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> object:
    raise ReaderArtifactRetentionError(
        f"non-finite JSON number is not allowed: {value}"
    )


def _relative_path(value: object) -> str:
    text = _text(value, "relative_path")
    if "\\" in text:
        raise ReaderArtifactRetentionError(
            "relative_path must use forward slashes"
        )
    path = PurePosixPath(text)
    if path.is_absolute() or not path.parts:
        raise ReaderArtifactRetentionError(
            "relative_path must be a non-empty relative POSIX path"
        )
    if any(part in {"", ".", ".."} for part in path.parts):
        raise ReaderArtifactRetentionError(
            "relative_path must not contain empty, dot, or parent segments"
        )
    normalized = path.as_posix()
    if normalized != text:
        raise ReaderArtifactRetentionError(
            "relative_path must already be normalized"
        )
    return normalized


def _keys(
    payload: Mapping[str, object],
    *,
    required: set[str],
    field_name: str,
) -> None:
    actual = set(payload)
    missing = sorted(required - actual)
    unknown = sorted(actual - required)
    if missing or unknown:
        raise ReaderArtifactRetentionError(
            f"{field_name} keys mismatch; missing={missing}, unknown={unknown}"
        )


def _mapping(value: object, field_name: str) -> Mapping[str, object]:
    if not isinstance(value, dict) or any(
        not isinstance(key, str) for key in value
    ):
        raise ReaderArtifactRetentionError(
            f"{field_name} must be a JSON object with string keys"
        )
    return cast(Mapping[str, object], value)


def _list(value: object, field_name: str) -> list[object]:
    if not isinstance(value, list):
        raise ReaderArtifactRetentionError(
            f"{field_name} must be a JSON array"
        )
    return cast(list[object], value)


def _text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReaderArtifactRetentionError(
            f"{field_name} must be non-empty text"
        )
    return value


def _int(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ReaderArtifactRetentionError(
            f"{field_name} must be an integer"
        )
    return value


def _nonnegative_int(value: object, field_name: str) -> int:
    number = _int(value, field_name)
    if number < 0:
        raise ReaderArtifactRetentionError(
            f"{field_name} must be nonnegative"
        )
    return number


def _positive_int(value: object, field_name: str) -> int:
    number = _int(value, field_name)
    if number <= 0:
        raise ReaderArtifactRetentionError(
            f"{field_name} must be positive"
        )
    return number


def _bool(value: object, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise ReaderArtifactRetentionError(
            f"{field_name} must be a boolean"
        )
    return value


def _enum(enum_type: type[Any], value: object, field_name: str) -> Any:
    text = _text(value, field_name)
    try:
        return enum_type(text)
    except ValueError as exc:
        raise ReaderArtifactRetentionError(
            f"unsupported {field_name}: {text}"
        ) from exc


def _text_array(value: object, field_name: str) -> tuple[str, ...]:
    return tuple(_text(item, field_name) for item in _list(value, field_name))


def _unique_sorted_text(
    values: Iterable[str],
    field_name: str,
) -> tuple[str, ...]:
    items = tuple(values)
    for item in items:
        _text(item, field_name)
    if len(set(items)) != len(items):
        raise ReaderArtifactRetentionError(
            f"{field_name} values must be unique"
        )
    ordered = tuple(sorted(items))
    if items != ordered:
        raise ReaderArtifactRetentionError(
            f"{field_name} values must use canonical ordering"
        )
    return items


def _sha256(value: object, field_name: str) -> str:
    text = _text(value, field_name)
    if len(text) != 64 or text.lower() != text:
        raise ReaderArtifactRetentionError(
            f"{field_name} must be lowercase SHA-256 hex"
        )
    try:
        int(text, 16)
    except ValueError as exc:
        raise ReaderArtifactRetentionError(
            f"{field_name} must be lowercase SHA-256 hex"
        ) from exc
    return text


def _secret(secret: object) -> bytes:
    if not isinstance(secret, bytes) or len(secret) < 32:
        raise ReaderArtifactRetentionError(
            "HMAC secret must be bytes and at least 32 bytes long"
        )
    return secret


def _authority_boundary(
    operator_go_required: object,
    live_integration_authorized: object,
) -> None:
    if operator_go_required is not True:
        raise ReaderArtifactRetentionError(
            "artifact retention must preserve Operator GO requirement"
        )
    if live_integration_authorized is not False:
        raise ReaderArtifactRetentionError(
            "artifact retention cannot authorize live integration"
        )


__all__ = [
    "DEFAULT_MAX_ARTIFACT_BYTES",
    "DEFAULT_MAX_TOTAL_BYTES",
    "READER_ARTIFACT_RETENTION_MANIFEST_SCHEMA_VERSION",
    "READER_ARTIFACT_RETENTION_SIGNATURE_ALGORITHM",
    "READER_ARTIFACT_RETENTION_SIGNATURE_SCHEMA_VERSION",
    "READER_ARTIFACT_RETENTION_SOURCE_SPEC_SCHEMA_VERSION",
    "READER_ARTIFACT_RETENTION_VERIFICATION_SCHEMA_VERSION",
    "ArtifactRetentionClass",
    "ReaderArtifactRetentionError",
    "ReaderArtifactRetentionSignature",
    "ReaderArtifactRetentionSigner",
    "ReaderArtifactRetentionSourceEntry",
    "ReaderArtifactRetentionSourceSpec",
    "ReaderArtifactRetentionVerificationReceipt",
    "ReaderBenchmarkArtifactRetentionBuilder",
    "ReaderBenchmarkArtifactRetentionManifest",
    "ReaderBenchmarkArtifactRetentionVerifier",
    "ReaderRetainedBenchmarkArtifact",
    "ReaderVerifiedEvidenceArtifactIndex",
    "extract_verified_evidence_artifact_index",
    "load_artifact_retention_manifest",
    "load_artifact_retention_signature",
    "load_artifact_retention_source_spec",
    "write_artifact_retention_source_spec",
]
