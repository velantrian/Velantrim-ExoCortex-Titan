"""Signed Reader Core operator decisions for PR-RDR-25.

The module records a human/operator disposition over already verified
benchmark and retained-artifact evidence. An approval can authorize isolated
shadow evaluation only. Live integration, query-path wiring, Canon writes,
memory writes, and tool authority remain forbidden by construction.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import hmac
import json
from pathlib import Path
from typing import Any, cast

from core.reader_benchmark_artifact_retention import (
    READER_ARTIFACT_RETENTION_VERIFICATION_SCHEMA_VERSION,
    ReaderArtifactRetentionVerificationReceipt,
    ReaderBenchmarkArtifactRetentionManifest,
)
from core.reader_benchmark_evidence_verification import (
    READER_BENCHMARK_EVIDENCE_VERIFICATION_SCHEMA_VERSION,
    ReaderBenchmarkEvidenceVerificationReceipt,
)
from core.reader_benchmark_runner import canonical_json_bytes, write_canonical_json
from core.reader_core_contracts import stable_reader_core_id
from core.reader_evaluation import PromotionDecision

READER_OPERATOR_DECISION_SOURCE_SCHEMA_VERSION = (
    "reader-core.operator-decision-source.v1"
)
READER_OPERATOR_DECISION_SCHEMA_VERSION = "reader-core.operator-decision.v1"
READER_OPERATOR_DECISION_SIGNATURE_SCHEMA_VERSION = (
    "reader-core.operator-decision-signature.v1"
)
READER_OPERATOR_REVOCATION_SOURCE_SCHEMA_VERSION = (
    "reader-core.operator-revocation-source.v1"
)
READER_OPERATOR_REVOCATION_SCHEMA_VERSION = (
    "reader-core.operator-decision-revocation.v1"
)
READER_OPERATOR_REVOCATION_SIGNATURE_SCHEMA_VERSION = (
    "reader-core.operator-revocation-signature.v1"
)
READER_OPERATOR_DECISION_STATUS_SCHEMA_VERSION = (
    "reader-core.operator-decision-status.v1"
)
READER_OPERATOR_SIGNATURE_ALGORITHM = "hmac-sha256"


class ReaderOperatorDecisionError(ValueError):
    """Raised when operator-decision evidence is malformed or inconsistent."""


class OperatorDecisionDisposition(str, Enum):
    APPROVE_SHADOW_ONLY = "approve_shadow_only"
    DEFER = "defer"
    NO_GO = "no_go"


class OperatorDecisionStatus(str, Enum):
    ACTIVE_SHADOW_APPROVAL = "active_shadow_approval"
    NOT_YET_VALID = "not_yet_valid"
    EXPIRED = "expired"
    REVOKED = "revoked"
    NON_APPROVING = "non_approving"


@dataclass(frozen=True, slots=True)
class ReaderOperatorDecisionSource:
    operator_id: str
    disposition: OperatorDecisionDisposition
    decided_at_utc: str
    valid_from_utc: str
    valid_until_utc: str
    rationale_codes: tuple[str, ...]
    condition_codes: tuple[str, ...]
    schema_version: str = READER_OPERATOR_DECISION_SOURCE_SCHEMA_VERSION
    source_id: str = ""

    def __post_init__(self) -> None:
        _text(self.operator_id, "operator_id")
        if not isinstance(self.disposition, OperatorDecisionDisposition):
            raise ReaderOperatorDecisionError(
                "disposition must be an OperatorDecisionDisposition"
            )
        decided = _utc(self.decided_at_utc, "decided_at_utc")
        valid_from = _utc(self.valid_from_utc, "valid_from_utc")
        valid_until = _utc(self.valid_until_utc, "valid_until_utc")
        if decided > valid_from:
            raise ReaderOperatorDecisionError(
                "decided_at_utc must not be after valid_from_utc"
            )
        if valid_from >= valid_until:
            raise ReaderOperatorDecisionError(
                "valid_until_utc must be after valid_from_utc"
            )
        rationale = _unique_sorted_text(self.rationale_codes, "rationale_code")
        conditions = _unique_sorted_text(self.condition_codes, "condition_code")
        if self.disposition is OperatorDecisionDisposition.APPROVE_SHADOW_ONLY:
            if not conditions:
                raise ReaderOperatorDecisionError(
                    "shadow approval requires explicit condition codes"
                )
        elif not rationale:
            raise ReaderOperatorDecisionError(
                "defer and no-go decisions require rationale codes"
            )
        object.__setattr__(self, "rationale_codes", rationale)
        object.__setattr__(self, "condition_codes", conditions)
        if (
            self.schema_version
            != READER_OPERATOR_DECISION_SOURCE_SCHEMA_VERSION
        ):
            raise ReaderOperatorDecisionError(
                "unsupported operator decision source schema"
            )
        expected = stable_reader_core_id(
            "reader-operator-decision-source",
            self.identity_payload(include_id=False),
        )
        if self.source_id:
            if self.source_id != expected:
                raise ReaderOperatorDecisionError(
                    "source_id does not match decision source content"
                )
        else:
            object.__setattr__(self, "source_id", expected)

    def source_payload(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "operator_id": self.operator_id,
            "disposition": self.disposition.value,
            "decided_at_utc": self.decided_at_utc,
            "valid_from_utc": self.valid_from_utc,
            "valid_until_utc": self.valid_until_utc,
            "rationale_codes": list(self.rationale_codes),
            "condition_codes": list(self.condition_codes),
        }

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload = self.source_payload()
        if include_id:
            payload["source_id"] = self.source_id
        return payload


@dataclass(frozen=True, slots=True)
class ReaderOperatorDecisionRecord:
    source: ReaderOperatorDecisionSource
    evidence_id: str
    benchmark_verification_id: str
    retention_manifest_id: str
    retention_verification_id: str
    benchmark_bundle_id: str
    benchmark_signature_id: str
    review_decision: PromotionDecision
    shadow_evaluation_authorized: bool
    live_integration_authorized: bool = False
    query_path_wiring_authorized: bool = False
    canon_write_authorized: bool = False
    memory_write_authorized: bool = False
    schema_version: str = READER_OPERATOR_DECISION_SCHEMA_VERSION
    decision_id: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.source, ReaderOperatorDecisionSource):
            raise ReaderOperatorDecisionError(
                "source must be a ReaderOperatorDecisionSource"
            )
        for name in (
            "evidence_id",
            "benchmark_verification_id",
            "retention_manifest_id",
            "retention_verification_id",
            "benchmark_bundle_id",
            "benchmark_signature_id",
        ):
            _text(getattr(self, name), name)
        if not isinstance(self.review_decision, PromotionDecision):
            raise ReaderOperatorDecisionError(
                "review_decision must be a PromotionDecision"
            )
        expected_shadow = (
            self.source.disposition
            is OperatorDecisionDisposition.APPROVE_SHADOW_ONLY
        )
        if self.shadow_evaluation_authorized is not expected_shadow:
            raise ReaderOperatorDecisionError(
                "shadow authorization must exactly match decision disposition"
            )
        if expected_shadow and (
            self.review_decision
            is not PromotionDecision.ELIGIBLE_FOR_OPERATOR_REVIEW
        ):
            raise ReaderOperatorDecisionError(
                "shadow approval requires eligible_for_operator_review"
            )
        _forbidden_authority(
            live=self.live_integration_authorized,
            query=self.query_path_wiring_authorized,
            canon=self.canon_write_authorized,
            memory=self.memory_write_authorized,
        )
        if self.schema_version != READER_OPERATOR_DECISION_SCHEMA_VERSION:
            raise ReaderOperatorDecisionError(
                "unsupported operator decision schema"
            )
        expected = stable_reader_core_id(
            "reader-operator-decision-record",
            self.identity_payload(include_id=False),
        )
        if self.decision_id:
            if self.decision_id != expected:
                raise ReaderOperatorDecisionError(
                    "decision_id does not match operator decision content"
                )
        else:
            object.__setattr__(self, "decision_id", expected)

    @property
    def operator_id(self) -> str:
        return self.source.operator_id

    @property
    def disposition(self) -> OperatorDecisionDisposition:
        return self.source.disposition

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema_version": self.schema_version,
            "source_id": self.source.source_id,
            "source": self.source,
            "evidence_id": self.evidence_id,
            "benchmark_verification_id": self.benchmark_verification_id,
            "retention_manifest_id": self.retention_manifest_id,
            "retention_verification_id": self.retention_verification_id,
            "benchmark_bundle_id": self.benchmark_bundle_id,
            "benchmark_signature_id": self.benchmark_signature_id,
            "review_decision": self.review_decision.value,
            "shadow_evaluation_authorized": (
                self.shadow_evaluation_authorized
            ),
            "live_integration_authorized": self.live_integration_authorized,
            "query_path_wiring_authorized": (
                self.query_path_wiring_authorized
            ),
            "canon_write_authorized": self.canon_write_authorized,
            "memory_write_authorized": self.memory_write_authorized,
        }
        if include_id:
            payload["decision_id"] = self.decision_id
        return payload


@dataclass(frozen=True, slots=True)
class ReaderOperatorDecisionSignature:
    decision_id: str
    key_id: str
    decision_sha256: str
    signature_hex: str
    algorithm: str = READER_OPERATOR_SIGNATURE_ALGORITHM
    schema_version: str = READER_OPERATOR_DECISION_SIGNATURE_SCHEMA_VERSION
    signature_id: str = ""

    def __post_init__(self) -> None:
        _text(self.decision_id, "decision_id")
        _text(self.key_id, "key_id")
        _sha256(self.decision_sha256, "decision_sha256")
        _sha256(self.signature_hex, "signature_hex")
        if self.algorithm != READER_OPERATOR_SIGNATURE_ALGORITHM:
            raise ReaderOperatorDecisionError(
                "unsupported operator decision signature algorithm"
            )
        if (
            self.schema_version
            != READER_OPERATOR_DECISION_SIGNATURE_SCHEMA_VERSION
        ):
            raise ReaderOperatorDecisionError(
                "unsupported operator decision signature schema"
            )
        expected = stable_reader_core_id(
            "reader-operator-decision-signature",
            self.identity_payload(include_id=False),
        )
        if self.signature_id:
            if self.signature_id != expected:
                raise ReaderOperatorDecisionError(
                    "signature_id does not match operator signature content"
                )
        else:
            object.__setattr__(self, "signature_id", expected)

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "decision_id": self.decision_id,
            "key_id": self.key_id,
            "decision_sha256": self.decision_sha256,
            "signature_hex": self.signature_hex,
            "algorithm": self.algorithm,
            "schema_version": self.schema_version,
        }
        if include_id:
            payload["signature_id"] = self.signature_id
        return payload


@dataclass(frozen=True, slots=True)
class ReaderOperatorRevocationSource:
    operator_id: str
    revoked_at_utc: str
    rationale_codes: tuple[str, ...]
    schema_version: str = READER_OPERATOR_REVOCATION_SOURCE_SCHEMA_VERSION
    source_id: str = ""

    def __post_init__(self) -> None:
        _text(self.operator_id, "operator_id")
        _utc(self.revoked_at_utc, "revoked_at_utc")
        rationale = _unique_sorted_text(self.rationale_codes, "rationale_code")
        if not rationale:
            raise ReaderOperatorDecisionError(
                "revocation requires rationale codes"
            )
        object.__setattr__(self, "rationale_codes", rationale)
        if (
            self.schema_version
            != READER_OPERATOR_REVOCATION_SOURCE_SCHEMA_VERSION
        ):
            raise ReaderOperatorDecisionError(
                "unsupported operator revocation source schema"
            )
        expected = stable_reader_core_id(
            "reader-operator-revocation-source",
            self.identity_payload(include_id=False),
        )
        if self.source_id:
            if self.source_id != expected:
                raise ReaderOperatorDecisionError(
                    "source_id does not match revocation source content"
                )
        else:
            object.__setattr__(self, "source_id", expected)

    def source_payload(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "operator_id": self.operator_id,
            "revoked_at_utc": self.revoked_at_utc,
            "rationale_codes": list(self.rationale_codes),
        }

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload = self.source_payload()
        if include_id:
            payload["source_id"] = self.source_id
        return payload


@dataclass(frozen=True, slots=True)
class ReaderOperatorDecisionRevocation:
    decision_id: str
    decision_signature_id: str
    source: ReaderOperatorRevocationSource
    schema_version: str = READER_OPERATOR_REVOCATION_SCHEMA_VERSION
    revocation_id: str = ""

    def __post_init__(self) -> None:
        _text(self.decision_id, "decision_id")
        _text(self.decision_signature_id, "decision_signature_id")
        if not isinstance(self.source, ReaderOperatorRevocationSource):
            raise ReaderOperatorDecisionError(
                "source must be a ReaderOperatorRevocationSource"
            )
        if self.schema_version != READER_OPERATOR_REVOCATION_SCHEMA_VERSION:
            raise ReaderOperatorDecisionError(
                "unsupported operator revocation schema"
            )
        expected = stable_reader_core_id(
            "reader-operator-decision-revocation",
            self.identity_payload(include_id=False),
        )
        if self.revocation_id:
            if self.revocation_id != expected:
                raise ReaderOperatorDecisionError(
                    "revocation_id does not match revocation content"
                )
        else:
            object.__setattr__(self, "revocation_id", expected)

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema_version": self.schema_version,
            "decision_id": self.decision_id,
            "decision_signature_id": self.decision_signature_id,
            "source_id": self.source.source_id,
            "source": self.source,
        }
        if include_id:
            payload["revocation_id"] = self.revocation_id
        return payload


@dataclass(frozen=True, slots=True)
class ReaderOperatorRevocationSignature:
    revocation_id: str
    key_id: str
    revocation_sha256: str
    signature_hex: str
    algorithm: str = READER_OPERATOR_SIGNATURE_ALGORITHM
    schema_version: str = READER_OPERATOR_REVOCATION_SIGNATURE_SCHEMA_VERSION
    signature_id: str = ""

    def __post_init__(self) -> None:
        _text(self.revocation_id, "revocation_id")
        _text(self.key_id, "key_id")
        _sha256(self.revocation_sha256, "revocation_sha256")
        _sha256(self.signature_hex, "signature_hex")
        if self.algorithm != READER_OPERATOR_SIGNATURE_ALGORITHM:
            raise ReaderOperatorDecisionError(
                "unsupported operator revocation signature algorithm"
            )
        if (
            self.schema_version
            != READER_OPERATOR_REVOCATION_SIGNATURE_SCHEMA_VERSION
        ):
            raise ReaderOperatorDecisionError(
                "unsupported operator revocation signature schema"
            )
        expected = stable_reader_core_id(
            "reader-operator-revocation-signature",
            self.identity_payload(include_id=False),
        )
        if self.signature_id:
            if self.signature_id != expected:
                raise ReaderOperatorDecisionError(
                    "signature_id does not match revocation signature content"
                )
        else:
            object.__setattr__(self, "signature_id", expected)

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "revocation_id": self.revocation_id,
            "key_id": self.key_id,
            "revocation_sha256": self.revocation_sha256,
            "signature_hex": self.signature_hex,
            "algorithm": self.algorithm,
            "schema_version": self.schema_version,
        }
        if include_id:
            payload["signature_id"] = self.signature_id
        return payload


@dataclass(frozen=True, slots=True)
class ReaderOperatorDecisionStatusReceipt:
    decision_id: str
    decision_signature_id: str
    as_of_utc: str
    status: OperatorDecisionStatus
    revocation_id: str | None
    revocation_signature_id: str | None
    shadow_evaluation_authorized: bool
    live_integration_authorized: bool = False
    query_path_wiring_authorized: bool = False
    canon_write_authorized: bool = False
    memory_write_authorized: bool = False
    schema_version: str = READER_OPERATOR_DECISION_STATUS_SCHEMA_VERSION
    status_id: str = ""

    def __post_init__(self) -> None:
        _text(self.decision_id, "decision_id")
        _text(self.decision_signature_id, "decision_signature_id")
        _utc(self.as_of_utc, "as_of_utc")
        if not isinstance(self.status, OperatorDecisionStatus):
            raise ReaderOperatorDecisionError(
                "status must be an OperatorDecisionStatus"
            )
        if (self.revocation_id is None) != (
            self.revocation_signature_id is None
        ):
            raise ReaderOperatorDecisionError(
                "revocation IDs must be both present or both absent"
            )
        if self.revocation_id is not None:
            _text(self.revocation_id, "revocation_id")
            _text(self.revocation_signature_id, "revocation_signature_id")
        expected_shadow = (
            self.status is OperatorDecisionStatus.ACTIVE_SHADOW_APPROVAL
        )
        if self.shadow_evaluation_authorized is not expected_shadow:
            raise ReaderOperatorDecisionError(
                "shadow authorization must exactly match active status"
            )
        _forbidden_authority(
            live=self.live_integration_authorized,
            query=self.query_path_wiring_authorized,
            canon=self.canon_write_authorized,
            memory=self.memory_write_authorized,
        )
        if (
            self.schema_version
            != READER_OPERATOR_DECISION_STATUS_SCHEMA_VERSION
        ):
            raise ReaderOperatorDecisionError(
                "unsupported operator decision status schema"
            )
        expected = stable_reader_core_id(
            "reader-operator-decision-status",
            self.identity_payload(include_id=False),
        )
        if self.status_id:
            if self.status_id != expected:
                raise ReaderOperatorDecisionError(
                    "status_id does not match decision status content"
                )
        else:
            object.__setattr__(self, "status_id", expected)

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema_version": self.schema_version,
            "decision_id": self.decision_id,
            "decision_signature_id": self.decision_signature_id,
            "as_of_utc": self.as_of_utc,
            "status": self.status.value,
            "revocation_id": self.revocation_id,
            "revocation_signature_id": self.revocation_signature_id,
            "shadow_evaluation_authorized": (
                self.shadow_evaluation_authorized
            ),
            "live_integration_authorized": self.live_integration_authorized,
            "query_path_wiring_authorized": (
                self.query_path_wiring_authorized
            ),
            "canon_write_authorized": self.canon_write_authorized,
            "memory_write_authorized": self.memory_write_authorized,
        }
        if include_id:
            payload["status_id"] = self.status_id
        return payload


class ReaderOperatorDecisionBuilder:
    """Bind an operator disposition to verified benchmark and retention evidence."""

    def build(
        self,
        *,
        benchmark_verification: ReaderBenchmarkEvidenceVerificationReceipt,
        retention_manifest: ReaderBenchmarkArtifactRetentionManifest,
        retention_verification: ReaderArtifactRetentionVerificationReceipt,
        source: ReaderOperatorDecisionSource,
    ) -> ReaderOperatorDecisionRecord:
        if not isinstance(
            benchmark_verification,
            ReaderBenchmarkEvidenceVerificationReceipt,
        ):
            raise ReaderOperatorDecisionError(
                "benchmark_verification must be a verification receipt"
            )
        if not isinstance(
            retention_manifest,
            ReaderBenchmarkArtifactRetentionManifest,
        ):
            raise ReaderOperatorDecisionError(
                "retention_manifest must be a retention manifest"
            )
        if not isinstance(
            retention_verification,
            ReaderArtifactRetentionVerificationReceipt,
        ):
            raise ReaderOperatorDecisionError(
                "retention_verification must be a retention verification receipt"
            )
        if not isinstance(source, ReaderOperatorDecisionSource):
            raise ReaderOperatorDecisionError(
                "source must be a ReaderOperatorDecisionSource"
            )
        _validate_evidence_chain(
            benchmark=benchmark_verification,
            manifest=retention_manifest,
            retention=retention_verification,
        )
        if (
            source.disposition
            is OperatorDecisionDisposition.APPROVE_SHADOW_ONLY
            and benchmark_verification.decision
            is not PromotionDecision.ELIGIBLE_FOR_OPERATOR_REVIEW
        ):
            raise ReaderOperatorDecisionError(
                "shadow approval requires eligible benchmark evidence"
            )
        return ReaderOperatorDecisionRecord(
            source=source,
            evidence_id=benchmark_verification.evidence_id,
            benchmark_verification_id=(
                benchmark_verification.verification_id
            ),
            retention_manifest_id=retention_manifest.manifest_id,
            retention_verification_id=(
                retention_verification.verification_id
            ),
            benchmark_bundle_id=benchmark_verification.benchmark_bundle_id,
            benchmark_signature_id=benchmark_verification.signature_id,
            review_decision=benchmark_verification.decision,
            shadow_evaluation_authorized=(
                source.disposition
                is OperatorDecisionDisposition.APPROVE_SHADOW_ONLY
            ),
        )


class ReaderOperatorDecisionSigner:
    @staticmethod
    def sign(
        decision: ReaderOperatorDecisionRecord,
        *,
        key_id: str,
        secret: bytes,
    ) -> ReaderOperatorDecisionSignature:
        if not isinstance(decision, ReaderOperatorDecisionRecord):
            raise ReaderOperatorDecisionError(
                "decision must be a ReaderOperatorDecisionRecord"
            )
        _text(key_id, "key_id")
        _secret(secret)
        payload = canonical_json_bytes(decision)
        return ReaderOperatorDecisionSignature(
            decision_id=decision.decision_id,
            key_id=key_id,
            decision_sha256=hashlib.sha256(payload).hexdigest(),
            signature_hex=hmac.new(secret, payload, hashlib.sha256).hexdigest(),
        )

    @staticmethod
    def verify(
        decision: ReaderOperatorDecisionRecord,
        signature: ReaderOperatorDecisionSignature,
        *,
        secret: bytes,
    ) -> bool:
        if not isinstance(decision, ReaderOperatorDecisionRecord):
            raise ReaderOperatorDecisionError(
                "decision must be a ReaderOperatorDecisionRecord"
            )
        if not isinstance(signature, ReaderOperatorDecisionSignature):
            raise ReaderOperatorDecisionError(
                "signature must be a ReaderOperatorDecisionSignature"
            )
        _secret(secret)
        if signature.decision_id != decision.decision_id:
            return False
        payload = canonical_json_bytes(decision)
        digest = hashlib.sha256(payload).hexdigest()
        if not hmac.compare_digest(signature.decision_sha256, digest):
            return False
        expected = hmac.new(secret, payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(signature.signature_hex, expected)


class ReaderOperatorRevocationSigner:
    @staticmethod
    def create(
        *,
        decision: ReaderOperatorDecisionRecord,
        decision_signature: ReaderOperatorDecisionSignature,
        source: ReaderOperatorRevocationSource,
    ) -> ReaderOperatorDecisionRevocation:
        if not isinstance(decision, ReaderOperatorDecisionRecord):
            raise ReaderOperatorDecisionError(
                "decision must be a ReaderOperatorDecisionRecord"
            )
        if not isinstance(decision_signature, ReaderOperatorDecisionSignature):
            raise ReaderOperatorDecisionError(
                "decision_signature must be a decision signature"
            )
        if not isinstance(source, ReaderOperatorRevocationSource):
            raise ReaderOperatorDecisionError(
                "source must be a ReaderOperatorRevocationSource"
            )
        if decision_signature.decision_id != decision.decision_id:
            raise ReaderOperatorDecisionError(
                "decision signature belongs to a different decision"
            )
        revoked = _utc(source.revoked_at_utc, "revoked_at_utc")
        decided = _utc(decision.source.decided_at_utc, "decided_at_utc")
        if revoked < decided:
            raise ReaderOperatorDecisionError(
                "revocation cannot predate the operator decision"
            )
        return ReaderOperatorDecisionRevocation(
            decision_id=decision.decision_id,
            decision_signature_id=decision_signature.signature_id,
            source=source,
        )

    @staticmethod
    def sign(
        revocation: ReaderOperatorDecisionRevocation,
        *,
        key_id: str,
        secret: bytes,
    ) -> ReaderOperatorRevocationSignature:
        if not isinstance(revocation, ReaderOperatorDecisionRevocation):
            raise ReaderOperatorDecisionError(
                "revocation must be a ReaderOperatorDecisionRevocation"
            )
        _text(key_id, "key_id")
        _secret(secret)
        payload = canonical_json_bytes(revocation)
        return ReaderOperatorRevocationSignature(
            revocation_id=revocation.revocation_id,
            key_id=key_id,
            revocation_sha256=hashlib.sha256(payload).hexdigest(),
            signature_hex=hmac.new(secret, payload, hashlib.sha256).hexdigest(),
        )

    @staticmethod
    def verify(
        revocation: ReaderOperatorDecisionRevocation,
        signature: ReaderOperatorRevocationSignature,
        *,
        secret: bytes,
    ) -> bool:
        if not isinstance(revocation, ReaderOperatorDecisionRevocation):
            raise ReaderOperatorDecisionError(
                "revocation must be a ReaderOperatorDecisionRevocation"
            )
        if not isinstance(signature, ReaderOperatorRevocationSignature):
            raise ReaderOperatorDecisionError(
                "signature must be a ReaderOperatorRevocationSignature"
            )
        _secret(secret)
        if signature.revocation_id != revocation.revocation_id:
            return False
        payload = canonical_json_bytes(revocation)
        digest = hashlib.sha256(payload).hexdigest()
        if not hmac.compare_digest(signature.revocation_sha256, digest):
            return False
        expected = hmac.new(secret, payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(signature.signature_hex, expected)


class ReaderOperatorDecisionEvaluator:
    """Evaluate one signed decision at an explicit UTC instant."""

    def evaluate(
        self,
        *,
        decision: ReaderOperatorDecisionRecord,
        decision_signature: ReaderOperatorDecisionSignature,
        secret: bytes,
        as_of_utc: str,
        revocation: ReaderOperatorDecisionRevocation | None = None,
        revocation_signature: ReaderOperatorRevocationSignature | None = None,
    ) -> ReaderOperatorDecisionStatusReceipt:
        if not ReaderOperatorDecisionSigner.verify(
            decision,
            decision_signature,
            secret=secret,
        ):
            raise ReaderOperatorDecisionError(
                "operator decision signature verification failed"
            )
        if (revocation is None) != (revocation_signature is None):
            raise ReaderOperatorDecisionError(
                "revocation and signature must be both present or both absent"
            )
        as_of = _utc(as_of_utc, "as_of_utc")
        status: OperatorDecisionStatus
        revocation_id: str | None = None
        revocation_signature_id: str | None = None
        if revocation is not None and revocation_signature is not None:
            if revocation.decision_id != decision.decision_id:
                raise ReaderOperatorDecisionError(
                    "revocation belongs to a different decision"
                )
            if (
                revocation.decision_signature_id
                != decision_signature.signature_id
            ):
                raise ReaderOperatorDecisionError(
                    "revocation references a different decision signature"
                )
            if not ReaderOperatorRevocationSigner.verify(
                revocation,
                revocation_signature,
                secret=secret,
            ):
                raise ReaderOperatorDecisionError(
                    "operator revocation signature verification failed"
                )
            revocation_id = revocation.revocation_id
            revocation_signature_id = revocation_signature.signature_id
            revoked_at = _utc(
                revocation.source.revoked_at_utc,
                "revoked_at_utc",
            )
            if revoked_at <= as_of:
                status = OperatorDecisionStatus.REVOKED
            else:
                status = self._unrevoked_status(decision, as_of)
        else:
            status = self._unrevoked_status(decision, as_of)
        return ReaderOperatorDecisionStatusReceipt(
            decision_id=decision.decision_id,
            decision_signature_id=decision_signature.signature_id,
            as_of_utc=as_of_utc,
            status=status,
            revocation_id=revocation_id,
            revocation_signature_id=revocation_signature_id,
            shadow_evaluation_authorized=(
                status is OperatorDecisionStatus.ACTIVE_SHADOW_APPROVAL
            ),
        )

    @staticmethod
    def _unrevoked_status(
        decision: ReaderOperatorDecisionRecord,
        as_of: datetime,
    ) -> OperatorDecisionStatus:
        valid_from = _utc(decision.source.valid_from_utc, "valid_from_utc")
        valid_until = _utc(decision.source.valid_until_utc, "valid_until_utc")
        if as_of < valid_from:
            return OperatorDecisionStatus.NOT_YET_VALID
        if as_of >= valid_until:
            return OperatorDecisionStatus.EXPIRED
        if (
            decision.disposition
            is OperatorDecisionDisposition.APPROVE_SHADOW_ONLY
        ):
            return OperatorDecisionStatus.ACTIVE_SHADOW_APPROVAL
        return OperatorDecisionStatus.NON_APPROVING


def load_operator_decision_source(
    path: str | Path,
) -> ReaderOperatorDecisionSource:
    payload, raw = _load_object(path, "operator decision source")
    _keys(
        payload,
        required={
            "schema_version",
            "operator_id",
            "disposition",
            "decided_at_utc",
            "valid_from_utc",
            "valid_until_utc",
            "rationale_codes",
            "condition_codes",
        },
        field_name="operator decision source",
    )
    source = ReaderOperatorDecisionSource(
        schema_version=_text(payload["schema_version"], "schema_version"),
        operator_id=_text(payload["operator_id"], "operator_id"),
        disposition=_enum(
            OperatorDecisionDisposition,
            payload["disposition"],
            "disposition",
        ),
        decided_at_utc=_text(payload["decided_at_utc"], "decided_at_utc"),
        valid_from_utc=_text(payload["valid_from_utc"], "valid_from_utc"),
        valid_until_utc=_text(payload["valid_until_utc"], "valid_until_utc"),
        rationale_codes=_text_array(
            payload["rationale_codes"],
            "rationale_code",
        ),
        condition_codes=_text_array(
            payload["condition_codes"],
            "condition_code",
        ),
    )
    if raw != canonical_json_bytes(source.source_payload()) + b"\n":
        raise ReaderOperatorDecisionError(
            "operator decision source must use canonical ordering"
        )
    return source


def write_operator_decision_source(
    path: str | Path,
    source: ReaderOperatorDecisionSource,
) -> None:
    if not isinstance(source, ReaderOperatorDecisionSource):
        raise ReaderOperatorDecisionError(
            "source must be a ReaderOperatorDecisionSource"
        )
    write_canonical_json(path, source.source_payload())


def load_operator_revocation_source(
    path: str | Path,
) -> ReaderOperatorRevocationSource:
    payload, raw = _load_object(path, "operator revocation source")
    _keys(
        payload,
        required={
            "schema_version",
            "operator_id",
            "revoked_at_utc",
            "rationale_codes",
        },
        field_name="operator revocation source",
    )
    source = ReaderOperatorRevocationSource(
        schema_version=_text(payload["schema_version"], "schema_version"),
        operator_id=_text(payload["operator_id"], "operator_id"),
        revoked_at_utc=_text(payload["revoked_at_utc"], "revoked_at_utc"),
        rationale_codes=_text_array(
            payload["rationale_codes"],
            "rationale_code",
        ),
    )
    if raw != canonical_json_bytes(source.source_payload()) + b"\n":
        raise ReaderOperatorDecisionError(
            "operator revocation source must use canonical ordering"
        )
    return source


def write_operator_revocation_source(
    path: str | Path,
    source: ReaderOperatorRevocationSource,
) -> None:
    if not isinstance(source, ReaderOperatorRevocationSource):
        raise ReaderOperatorDecisionError(
            "source must be a ReaderOperatorRevocationSource"
        )
    write_canonical_json(path, source.source_payload())


def load_benchmark_verification_receipt(
    path: str | Path,
) -> ReaderBenchmarkEvidenceVerificationReceipt:
    payload, raw = _load_object(path, "benchmark verification receipt")
    _keys(
        payload,
        required={
            "envelope_id",
            "evidence_id",
            "benchmark_bundle_id",
            "signature_id",
            "key_id",
            "bundle_file_sha256",
            "signature_file_sha256",
            "evidence_file_sha256",
            "decision",
            "operator_go_required",
            "live_integration_authorized",
            "schema_version",
            "verification_id",
        },
        field_name="benchmark verification receipt",
    )
    receipt = ReaderBenchmarkEvidenceVerificationReceipt(
        envelope_id=_text(payload["envelope_id"], "envelope_id"),
        evidence_id=_text(payload["evidence_id"], "evidence_id"),
        benchmark_bundle_id=_text(
            payload["benchmark_bundle_id"],
            "benchmark_bundle_id",
        ),
        signature_id=_text(payload["signature_id"], "signature_id"),
        key_id=_text(payload["key_id"], "key_id"),
        bundle_file_sha256=_text(
            payload["bundle_file_sha256"],
            "bundle_file_sha256",
        ),
        signature_file_sha256=_text(
            payload["signature_file_sha256"],
            "signature_file_sha256",
        ),
        evidence_file_sha256=_text(
            payload["evidence_file_sha256"],
            "evidence_file_sha256",
        ),
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
        verification_id=_text(payload["verification_id"], "verification_id"),
    )
    if (
        receipt.schema_version
        != READER_BENCHMARK_EVIDENCE_VERIFICATION_SCHEMA_VERSION
    ):
        raise ReaderOperatorDecisionError(
            "unsupported benchmark verification schema"
        )
    if raw != canonical_json_bytes(receipt) + b"\n":
        raise ReaderOperatorDecisionError(
            "benchmark verification receipt is not canonical"
        )
    return receipt


def load_retention_verification_receipt(
    path: str | Path,
) -> ReaderArtifactRetentionVerificationReceipt:
    payload, raw = _load_object(path, "retention verification receipt")
    _keys(
        payload,
        required={
            "manifest_id",
            "retention_signature_id",
            "evidence_id",
            "evidence_verification_id",
            "verified_record_ids",
            "verified_artifact_count",
            "verified_total_byte_size",
            "decision",
            "operator_go_required",
            "live_integration_authorized",
            "schema_version",
            "verification_id",
        },
        field_name="retention verification receipt",
    )
    receipt = ReaderArtifactRetentionVerificationReceipt(
        manifest_id=_text(payload["manifest_id"], "manifest_id"),
        retention_signature_id=_text(
            payload["retention_signature_id"],
            "retention_signature_id",
        ),
        evidence_id=_text(payload["evidence_id"], "evidence_id"),
        evidence_verification_id=_text(
            payload["evidence_verification_id"],
            "evidence_verification_id",
        ),
        verified_record_ids=_text_array(
            payload["verified_record_ids"],
            "verified_record_id",
        ),
        verified_artifact_count=_int(
            payload["verified_artifact_count"],
            "verified_artifact_count",
        ),
        verified_total_byte_size=_int(
            payload["verified_total_byte_size"],
            "verified_total_byte_size",
        ),
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
        verification_id=_text(payload["verification_id"], "verification_id"),
    )
    if (
        receipt.schema_version
        != READER_ARTIFACT_RETENTION_VERIFICATION_SCHEMA_VERSION
    ):
        raise ReaderOperatorDecisionError(
            "unsupported retention verification schema"
        )
    if raw != canonical_json_bytes(receipt) + b"\n":
        raise ReaderOperatorDecisionError(
            "retention verification receipt is not canonical"
        )
    return receipt


def load_operator_decision(
    path: str | Path,
) -> ReaderOperatorDecisionRecord:
    payload, raw = _load_object(path, "operator decision")
    _keys(
        payload,
        required={
            "source",
            "evidence_id",
            "benchmark_verification_id",
            "retention_manifest_id",
            "retention_verification_id",
            "benchmark_bundle_id",
            "benchmark_signature_id",
            "review_decision",
            "shadow_evaluation_authorized",
            "live_integration_authorized",
            "query_path_wiring_authorized",
            "canon_write_authorized",
            "memory_write_authorized",
            "schema_version",
            "decision_id",
        },
        field_name="operator decision",
    )
    source = _parse_decision_source_object(
        _mapping(payload["source"], "source"),
        require_id=True,
    )
    decision = ReaderOperatorDecisionRecord(
        source=source,
        evidence_id=_text(payload["evidence_id"], "evidence_id"),
        benchmark_verification_id=_text(
            payload["benchmark_verification_id"],
            "benchmark_verification_id",
        ),
        retention_manifest_id=_text(
            payload["retention_manifest_id"],
            "retention_manifest_id",
        ),
        retention_verification_id=_text(
            payload["retention_verification_id"],
            "retention_verification_id",
        ),
        benchmark_bundle_id=_text(
            payload["benchmark_bundle_id"],
            "benchmark_bundle_id",
        ),
        benchmark_signature_id=_text(
            payload["benchmark_signature_id"],
            "benchmark_signature_id",
        ),
        review_decision=_enum(
            PromotionDecision,
            payload["review_decision"],
            "review_decision",
        ),
        shadow_evaluation_authorized=_bool(
            payload["shadow_evaluation_authorized"],
            "shadow_evaluation_authorized",
        ),
        live_integration_authorized=_bool(
            payload["live_integration_authorized"],
            "live_integration_authorized",
        ),
        query_path_wiring_authorized=_bool(
            payload["query_path_wiring_authorized"],
            "query_path_wiring_authorized",
        ),
        canon_write_authorized=_bool(
            payload["canon_write_authorized"],
            "canon_write_authorized",
        ),
        memory_write_authorized=_bool(
            payload["memory_write_authorized"],
            "memory_write_authorized",
        ),
        schema_version=_text(payload["schema_version"], "schema_version"),
        decision_id=_text(payload["decision_id"], "decision_id"),
    )
    if raw != canonical_json_bytes(decision) + b"\n":
        raise ReaderOperatorDecisionError("operator decision is not canonical")
    return decision


def load_operator_decision_signature(
    path: str | Path,
) -> ReaderOperatorDecisionSignature:
    payload, raw = _load_object(path, "operator decision signature")
    signature = _parse_decision_signature(payload)
    if raw != canonical_json_bytes(signature) + b"\n":
        raise ReaderOperatorDecisionError(
            "operator decision signature is not canonical"
        )
    return signature


def load_operator_revocation(
    path: str | Path,
) -> ReaderOperatorDecisionRevocation:
    payload, raw = _load_object(path, "operator revocation")
    _keys(
        payload,
        required={
            "decision_id",
            "decision_signature_id",
            "source",
            "schema_version",
            "revocation_id",
        },
        field_name="operator revocation",
    )
    revocation = ReaderOperatorDecisionRevocation(
        decision_id=_text(payload["decision_id"], "decision_id"),
        decision_signature_id=_text(
            payload["decision_signature_id"],
            "decision_signature_id",
        ),
        source=_parse_revocation_source_object(
            _mapping(payload["source"], "source"),
            require_id=True,
        ),
        schema_version=_text(payload["schema_version"], "schema_version"),
        revocation_id=_text(payload["revocation_id"], "revocation_id"),
    )
    if raw != canonical_json_bytes(revocation) + b"\n":
        raise ReaderOperatorDecisionError("operator revocation is not canonical")
    return revocation


def load_operator_revocation_signature(
    path: str | Path,
) -> ReaderOperatorRevocationSignature:
    payload, raw = _load_object(path, "operator revocation signature")
    signature = _parse_revocation_signature(payload)
    if raw != canonical_json_bytes(signature) + b"\n":
        raise ReaderOperatorDecisionError(
            "operator revocation signature is not canonical"
        )
    return signature


def _parse_decision_source_object(
    payload: Mapping[str, object],
    *,
    require_id: bool,
) -> ReaderOperatorDecisionSource:
    required = {
        "schema_version",
        "operator_id",
        "disposition",
        "decided_at_utc",
        "valid_from_utc",
        "valid_until_utc",
        "rationale_codes",
        "condition_codes",
    }
    if require_id:
        required.add("source_id")
    _keys(payload, required=required, field_name="decision source")
    return ReaderOperatorDecisionSource(
        schema_version=_text(payload["schema_version"], "schema_version"),
        operator_id=_text(payload["operator_id"], "operator_id"),
        disposition=_enum(
            OperatorDecisionDisposition,
            payload["disposition"],
            "disposition",
        ),
        decided_at_utc=_text(payload["decided_at_utc"], "decided_at_utc"),
        valid_from_utc=_text(payload["valid_from_utc"], "valid_from_utc"),
        valid_until_utc=_text(payload["valid_until_utc"], "valid_until_utc"),
        rationale_codes=_text_array(
            payload["rationale_codes"],
            "rationale_code",
        ),
        condition_codes=_text_array(
            payload["condition_codes"],
            "condition_code",
        ),
        source_id=(
            _text(payload["source_id"], "source_id") if require_id else ""
        ),
    )


def _parse_revocation_source_object(
    payload: Mapping[str, object],
    *,
    require_id: bool,
) -> ReaderOperatorRevocationSource:
    required = {
        "schema_version",
        "operator_id",
        "revoked_at_utc",
        "rationale_codes",
    }
    if require_id:
        required.add("source_id")
    _keys(payload, required=required, field_name="revocation source")
    return ReaderOperatorRevocationSource(
        schema_version=_text(payload["schema_version"], "schema_version"),
        operator_id=_text(payload["operator_id"], "operator_id"),
        revoked_at_utc=_text(payload["revoked_at_utc"], "revoked_at_utc"),
        rationale_codes=_text_array(
            payload["rationale_codes"],
            "rationale_code",
        ),
        source_id=(
            _text(payload["source_id"], "source_id") if require_id else ""
        ),
    )


def _parse_decision_signature(
    payload: Mapping[str, object],
) -> ReaderOperatorDecisionSignature:
    _keys(
        payload,
        required={
            "decision_id",
            "key_id",
            "decision_sha256",
            "signature_hex",
            "algorithm",
            "schema_version",
            "signature_id",
        },
        field_name="operator decision signature",
    )
    return ReaderOperatorDecisionSignature(
        decision_id=_text(payload["decision_id"], "decision_id"),
        key_id=_text(payload["key_id"], "key_id"),
        decision_sha256=_text(
            payload["decision_sha256"],
            "decision_sha256",
        ),
        signature_hex=_text(payload["signature_hex"], "signature_hex"),
        algorithm=_text(payload["algorithm"], "algorithm"),
        schema_version=_text(payload["schema_version"], "schema_version"),
        signature_id=_text(payload["signature_id"], "signature_id"),
    )


def _parse_revocation_signature(
    payload: Mapping[str, object],
) -> ReaderOperatorRevocationSignature:
    _keys(
        payload,
        required={
            "revocation_id",
            "key_id",
            "revocation_sha256",
            "signature_hex",
            "algorithm",
            "schema_version",
            "signature_id",
        },
        field_name="operator revocation signature",
    )
    return ReaderOperatorRevocationSignature(
        revocation_id=_text(payload["revocation_id"], "revocation_id"),
        key_id=_text(payload["key_id"], "key_id"),
        revocation_sha256=_text(
            payload["revocation_sha256"],
            "revocation_sha256",
        ),
        signature_hex=_text(payload["signature_hex"], "signature_hex"),
        algorithm=_text(payload["algorithm"], "algorithm"),
        schema_version=_text(payload["schema_version"], "schema_version"),
        signature_id=_text(payload["signature_id"], "signature_id"),
    )


def _validate_evidence_chain(
    *,
    benchmark: ReaderBenchmarkEvidenceVerificationReceipt,
    manifest: ReaderBenchmarkArtifactRetentionManifest,
    retention: ReaderArtifactRetentionVerificationReceipt,
) -> None:
    if manifest.evidence_id != benchmark.evidence_id:
        raise ReaderOperatorDecisionError(
            "retention manifest belongs to a different evidence artifact"
        )
    if manifest.evidence_verification_id != benchmark.verification_id:
        raise ReaderOperatorDecisionError(
            "retention manifest belongs to a different benchmark verification"
        )
    if manifest.benchmark_bundle_id != benchmark.benchmark_bundle_id:
        raise ReaderOperatorDecisionError(
            "retention manifest belongs to a different benchmark bundle"
        )
    if manifest.benchmark_signature_id != benchmark.signature_id:
        raise ReaderOperatorDecisionError(
            "retention manifest belongs to a different benchmark signature"
        )
    if manifest.decision is not benchmark.decision:
        raise ReaderOperatorDecisionError(
            "retention manifest review decision does not match benchmark"
        )
    if retention.manifest_id != manifest.manifest_id:
        raise ReaderOperatorDecisionError(
            "retention verification belongs to a different manifest"
        )
    if retention.evidence_id != benchmark.evidence_id:
        raise ReaderOperatorDecisionError(
            "retention verification belongs to a different evidence artifact"
        )
    if retention.evidence_verification_id != benchmark.verification_id:
        raise ReaderOperatorDecisionError(
            "retention verification belongs to a different benchmark verification"
        )
    if retention.decision is not benchmark.decision:
        raise ReaderOperatorDecisionError(
            "retention verification review decision does not match benchmark"
        )
    if retention.verified_artifact_count != len(manifest.artifacts):
        raise ReaderOperatorDecisionError(
            "retention verification artifact count does not match manifest"
        )
    if retention.verified_total_byte_size != manifest.total_byte_size:
        raise ReaderOperatorDecisionError(
            "retention verification byte total does not match manifest"
        )
    if set(retention.verified_record_ids) != {
        item.record_id for item in manifest.artifacts
    }:
        raise ReaderOperatorDecisionError(
            "retention verification records do not match manifest"
        )
    for required, live in (
        (benchmark.operator_go_required, benchmark.live_integration_authorized),
        (manifest.operator_go_required, manifest.live_integration_authorized),
        (retention.operator_go_required, retention.live_integration_authorized),
    ):
        if required is not True or live is not False:
            raise ReaderOperatorDecisionError(
                "evidence chain violates authority boundary"
            )


def _load_object(
    path: str | Path,
    field_name: str,
) -> tuple[dict[str, object], bytes]:
    source = Path(path)
    try:
        raw = source.read_bytes()
        value: Any = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_pairs,
            parse_constant=_reject_constant,
        )
    except ReaderOperatorDecisionError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ReaderOperatorDecisionError(
            f"cannot load {field_name} from {source}: {exc}"
        ) from exc
    payload = dict(_mapping(value, field_name))
    if raw != canonical_json_bytes(payload) + b"\n":
        raise ReaderOperatorDecisionError(
            f"{field_name} must use canonical JSON encoding"
        )
    return payload, raw


def _reject_duplicate_pairs(
    pairs: list[tuple[str, object]],
) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ReaderOperatorDecisionError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> object:
    raise ReaderOperatorDecisionError(
        f"non-finite JSON number is not allowed: {value}"
    )


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
        raise ReaderOperatorDecisionError(
            f"{field_name} keys mismatch; missing={missing}, unknown={unknown}"
        )


def _mapping(value: object, field_name: str) -> Mapping[str, object]:
    if not isinstance(value, dict) or any(
        not isinstance(key, str) for key in value
    ):
        raise ReaderOperatorDecisionError(
            f"{field_name} must be a JSON object with string keys"
        )
    return cast(Mapping[str, object], value)


def _list(value: object, field_name: str) -> list[object]:
    if not isinstance(value, list):
        raise ReaderOperatorDecisionError(
            f"{field_name} must be a JSON array"
        )
    return cast(list[object], value)


def _text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReaderOperatorDecisionError(
            f"{field_name} must be non-empty text"
        )
    return value


def _bool(value: object, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise ReaderOperatorDecisionError(
            f"{field_name} must be a boolean"
        )
    return value


def _int(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ReaderOperatorDecisionError(
            f"{field_name} must be an integer"
        )
    return value


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
        raise ReaderOperatorDecisionError(
            f"{field_name} values must be unique"
        )
    ordered = tuple(sorted(items))
    if items != ordered:
        raise ReaderOperatorDecisionError(
            f"{field_name} values must use canonical ordering"
        )
    return items


def _enum(enum_type: type[Any], value: object, field_name: str) -> Any:
    text = _text(value, field_name)
    try:
        return enum_type(text)
    except ValueError as exc:
        raise ReaderOperatorDecisionError(
            f"unsupported {field_name}: {text}"
        ) from exc


def _utc(value: object, field_name: str) -> datetime:
    text = _text(value, field_name)
    try:
        parsed = datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc
        )
    except ValueError as exc:
        raise ReaderOperatorDecisionError(
            f"{field_name} must use canonical UTC format "
            "YYYY-MM-DDTHH:MM:SSZ"
        ) from exc
    return parsed


def _sha256(value: object, field_name: str) -> str:
    text = _text(value, field_name)
    if len(text) != 64 or text.lower() != text:
        raise ReaderOperatorDecisionError(
            f"{field_name} must be lowercase SHA-256 hex"
        )
    try:
        int(text, 16)
    except ValueError as exc:
        raise ReaderOperatorDecisionError(
            f"{field_name} must be lowercase SHA-256 hex"
        ) from exc
    return text


def _secret(value: object) -> bytes:
    if not isinstance(value, bytes) or len(value) < 32:
        raise ReaderOperatorDecisionError(
            "HMAC secret must be bytes and at least 32 bytes long"
        )
    return value


def _forbidden_authority(
    *,
    live: object,
    query: object,
    canon: object,
    memory: object,
) -> None:
    for value, name in (
        (live, "live_integration_authorized"),
        (query, "query_path_wiring_authorized"),
        (canon, "canon_write_authorized"),
        (memory, "memory_write_authorized"),
    ):
        if value is not False:
            raise ReaderOperatorDecisionError(f"{name} must remain false")


__all__ = [
    "READER_OPERATOR_DECISION_SCHEMA_VERSION",
    "READER_OPERATOR_DECISION_SIGNATURE_SCHEMA_VERSION",
    "READER_OPERATOR_DECISION_SOURCE_SCHEMA_VERSION",
    "READER_OPERATOR_DECISION_STATUS_SCHEMA_VERSION",
    "READER_OPERATOR_REVOCATION_SCHEMA_VERSION",
    "READER_OPERATOR_REVOCATION_SIGNATURE_SCHEMA_VERSION",
    "READER_OPERATOR_REVOCATION_SOURCE_SCHEMA_VERSION",
    "READER_OPERATOR_SIGNATURE_ALGORITHM",
    "OperatorDecisionDisposition",
    "OperatorDecisionStatus",
    "ReaderOperatorDecisionBuilder",
    "ReaderOperatorDecisionError",
    "ReaderOperatorDecisionEvaluator",
    "ReaderOperatorDecisionRecord",
    "ReaderOperatorDecisionSignature",
    "ReaderOperatorDecisionSigner",
    "ReaderOperatorDecisionSource",
    "ReaderOperatorDecisionStatusReceipt",
    "ReaderOperatorDecisionRevocation",
    "ReaderOperatorRevocationSignature",
    "ReaderOperatorRevocationSigner",
    "ReaderOperatorRevocationSource",
    "load_benchmark_verification_receipt",
    "load_operator_decision",
    "load_operator_decision_signature",
    "load_operator_decision_source",
    "load_operator_revocation",
    "load_operator_revocation_signature",
    "load_operator_revocation_source",
    "load_retention_verification_receipt",
    "write_operator_decision_source",
    "write_operator_revocation_source",
]
