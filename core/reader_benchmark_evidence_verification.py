"""Offline verification of Reader Core benchmark evidence for PR-RDR-23.

The verifier consumes the three canonical RDR-22 outputs: benchmark bundle,
detached signature, and signed evidence. It reconstructs the typed execution
state, manifest, thresholds, benchmark input, report, review, bundle, and signed
evidence, requires byte-for-byte canonical equality, and verifies the detached
HMAC. It performs no model execution and grants no promotion authority.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, cast

from core.reader_benchmark_finalization import (
    READER_BENCHMARK_FINALIZATION_SCHEMA_VERSION,
    ReaderBenchmarkFinalizationError,
    ReaderSignedBenchmarkEvidence,
)
from core.reader_benchmark_portability import (
    ReaderBenchmarkFinalizationEnvelope,
    ReaderBenchmarkPortabilityError,
    _parse_manifest,
    _parse_state,
)
from core.reader_benchmark_runner import (
    READER_BENCHMARK_SIGNATURE_ALGORITHM,
    READER_BENCHMARK_SIGNATURE_SCHEMA_VERSION,
    ReaderBenchmarkError,
    ReaderBenchmarkRunner,
    ReaderBenchmarkSignature,
    ReaderBenchmarkSigner,
    canonical_json_bytes,
)
from core.reader_core_contracts import stable_reader_core_id
from core.reader_evaluation import (
    PromotionDecision,
    ReaderEvaluationError,
    ReaderPromotionThresholds,
)
from core.reader_prepared_batch_runner import ReaderPreparedBatchRunnerError

READER_BENCHMARK_EVIDENCE_VERIFICATION_SCHEMA_VERSION = (
    "reader-core.benchmark-evidence-verification.v1"
)


class ReaderBenchmarkEvidenceVerificationError(ValueError):
    """Raised when a benchmark evidence artifact set fails offline verification."""


@dataclass(frozen=True, slots=True)
class ReaderBenchmarkEvidenceVerificationReceipt:
    envelope_id: str
    evidence_id: str
    benchmark_bundle_id: str
    signature_id: str
    key_id: str
    bundle_file_sha256: str
    signature_file_sha256: str
    evidence_file_sha256: str
    decision: PromotionDecision
    operator_go_required: bool
    live_integration_authorized: bool
    schema_version: str = READER_BENCHMARK_EVIDENCE_VERIFICATION_SCHEMA_VERSION
    verification_id: str = ""

    def __post_init__(self) -> None:
        for name in (
            "envelope_id",
            "evidence_id",
            "benchmark_bundle_id",
            "signature_id",
            "key_id",
        ):
            _text(getattr(self, name), name)
        for name in (
            "bundle_file_sha256",
            "signature_file_sha256",
            "evidence_file_sha256",
        ):
            _sha256(getattr(self, name), name)
        if not isinstance(self.decision, PromotionDecision):
            raise ReaderBenchmarkEvidenceVerificationError(
                "decision must be a PromotionDecision"
            )
        if self.schema_version != READER_BENCHMARK_EVIDENCE_VERIFICATION_SCHEMA_VERSION:
            raise ReaderBenchmarkEvidenceVerificationError(
                "unsupported evidence verification schema"
            )
        if self.operator_go_required is not True:
            raise ReaderBenchmarkEvidenceVerificationError(
                "verified evidence must preserve Operator GO requirement"
            )
        if self.live_integration_authorized is not False:
            raise ReaderBenchmarkEvidenceVerificationError(
                "verified evidence cannot authorize live integration"
            )
        expected = stable_reader_core_id(
            "reader-benchmark-evidence-verification",
            self.identity_payload(include_id=False),
        )
        if self.verification_id:
            if self.verification_id != expected:
                raise ReaderBenchmarkEvidenceVerificationError(
                    "verification_id does not match verification receipt"
                )
        else:
            object.__setattr__(self, "verification_id", expected)

    def identity_payload(self, *, include_id: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema_version": self.schema_version,
            "envelope_id": self.envelope_id,
            "evidence_id": self.evidence_id,
            "benchmark_bundle_id": self.benchmark_bundle_id,
            "signature_id": self.signature_id,
            "key_id": self.key_id,
            "bundle_file_sha256": self.bundle_file_sha256,
            "signature_file_sha256": self.signature_file_sha256,
            "evidence_file_sha256": self.evidence_file_sha256,
            "decision": self.decision.value,
            "operator_go_required": self.operator_go_required,
            "live_integration_authorized": self.live_integration_authorized,
        }
        if include_id:
            payload["verification_id"] = self.verification_id
        return payload


class ReaderBenchmarkEvidenceVerifier:
    """Reconstruct and authenticate one canonical benchmark evidence artifact set."""

    def verify_files(
        self,
        *,
        bundle_path: str | Path,
        signature_path: str | Path,
        evidence_path: str | Path,
        secret: bytes,
    ) -> ReaderBenchmarkEvidenceVerificationReceipt:
        try:
            bundle_payload, bundle_bytes = _load_canonical_object(
                bundle_path,
                "benchmark bundle",
            )
            signature_payload, signature_bytes = _load_canonical_object(
                signature_path,
                "benchmark signature",
            )
            evidence_payload, evidence_bytes = _load_canonical_object(
                evidence_path,
                "signed benchmark evidence",
            )
            _keys(
                evidence_payload,
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
            if evidence_payload["benchmark_bundle"] != bundle_payload:
                raise ReaderBenchmarkEvidenceVerificationError(
                    "evidence benchmark_bundle does not match bundle file"
                )
            if evidence_payload["bundle_signature"] != signature_payload:
                raise ReaderBenchmarkEvidenceVerificationError(
                    "evidence bundle_signature does not match signature file"
                )

            state = _parse_state(
                _mapping(
                    evidence_payload["execution_state"],
                    "execution_state",
                )
            )
            manifest = _parse_manifest(
                _mapping(bundle_payload.get("manifest"), "manifest")
            )
            preparation_id = _text(
                evidence_payload["preparation_id"],
                "preparation_id",
            )
            envelope = ReaderBenchmarkFinalizationEnvelope(
                preparation_id=preparation_id,
                evaluation_manifest=manifest,
                batch_plan=state.checkpoint.plan,
                execution_state=state,
            )
            thresholds = _parse_thresholds(
                _mapping(bundle_payload.get("thresholds"), "thresholds")
            )
            benchmark_input = state.to_benchmark_input()
            regenerated_bundle = ReaderBenchmarkRunner().run(
                manifest,
                benchmark_input,
                thresholds,
            )
            if bundle_bytes != canonical_json_bytes(regenerated_bundle) + b"\n":
                raise ReaderBenchmarkEvidenceVerificationError(
                    "benchmark bundle does not match deterministic reconstruction"
                )

            signature = _parse_signature(signature_payload)
            if not ReaderBenchmarkSigner.verify(
                regenerated_bundle,
                signature,
                secret=secret,
            ):
                raise ReaderBenchmarkEvidenceVerificationError(
                    "benchmark bundle signature verification failed"
                )

            evidence = ReaderSignedBenchmarkEvidence(
                preparation_id=preparation_id,
                execution_state=state,
                benchmark_bundle=regenerated_bundle,
                bundle_signature=signature,
                receipt_ids=_text_array(
                    evidence_payload["receipt_ids"],
                    "receipt_id",
                ),
                failed_attempt_receipt_ids=_text_array(
                    evidence_payload["failed_attempt_receipt_ids"],
                    "failed_attempt_receipt_id",
                ),
                artifact_ids=_text_array(
                    evidence_payload["artifact_ids"],
                    "artifact_id",
                ),
                schema_version=_text(
                    evidence_payload["schema_version"],
                    "schema_version",
                ),
                evidence_id=_text(
                    evidence_payload["evidence_id"],
                    "evidence_id",
                ),
            )
            if evidence.schema_version != READER_BENCHMARK_FINALIZATION_SCHEMA_VERSION:
                raise ReaderBenchmarkEvidenceVerificationError(
                    "unsupported signed evidence schema"
                )
            if evidence_bytes != canonical_json_bytes(evidence) + b"\n":
                raise ReaderBenchmarkEvidenceVerificationError(
                    "signed evidence does not match deterministic reconstruction"
                )
            if signature_bytes != canonical_json_bytes(signature) + b"\n":
                raise ReaderBenchmarkEvidenceVerificationError(
                    "signature file does not match typed signature reconstruction"
                )
        except ReaderBenchmarkEvidenceVerificationError:
            raise
        except (
            ReaderBenchmarkError,
            ReaderBenchmarkFinalizationError,
            ReaderBenchmarkPortabilityError,
            ReaderPreparedBatchRunnerError,
            ReaderEvaluationError,
            OSError,
            UnicodeError,
            json.JSONDecodeError,
            ValueError,
        ) as exc:
            raise ReaderBenchmarkEvidenceVerificationError(str(exc)) from exc

        return ReaderBenchmarkEvidenceVerificationReceipt(
            envelope_id=envelope.envelope_id,
            evidence_id=evidence.evidence_id,
            benchmark_bundle_id=regenerated_bundle.bundle_id,
            signature_id=signature.signature_id,
            key_id=signature.key_id,
            bundle_file_sha256=hashlib.sha256(bundle_bytes).hexdigest(),
            signature_file_sha256=hashlib.sha256(signature_bytes).hexdigest(),
            evidence_file_sha256=hashlib.sha256(evidence_bytes).hexdigest(),
            decision=evidence.decision,
            operator_go_required=evidence.operator_go_required,
            live_integration_authorized=evidence.live_integration_authorized,
        )


def _parse_signature(
    payload: Mapping[str, object],
) -> ReaderBenchmarkSignature:
    _keys(
        payload,
        required={
            "bundle_id",
            "key_id",
            "bundle_sha256",
            "signature_hex",
            "algorithm",
            "schema_version",
            "signature_id",
        },
        field_name="benchmark signature",
    )
    algorithm = _text(payload["algorithm"], "algorithm")
    schema_version = _text(payload["schema_version"], "schema_version")
    if algorithm != READER_BENCHMARK_SIGNATURE_ALGORITHM:
        raise ReaderBenchmarkEvidenceVerificationError(
            "unsupported benchmark signature algorithm"
        )
    if schema_version != READER_BENCHMARK_SIGNATURE_SCHEMA_VERSION:
        raise ReaderBenchmarkEvidenceVerificationError(
            "unsupported benchmark signature schema"
        )
    return ReaderBenchmarkSignature(
        bundle_id=_text(payload["bundle_id"], "bundle_id"),
        key_id=_text(payload["key_id"], "key_id"),
        bundle_sha256=_text(payload["bundle_sha256"], "bundle_sha256"),
        signature_hex=_text(payload["signature_hex"], "signature_hex"),
        algorithm=algorithm,
        schema_version=schema_version,
        signature_id=_text(payload["signature_id"], "signature_id"),
    )


def _parse_thresholds(
    payload: Mapping[str, object],
) -> ReaderPromotionThresholds:
    required = {
        "min_total_cases",
        "min_synthetic_cases",
        "min_real_cases",
        "min_human_labelled_cases",
        "min_claim_fidelity",
        "min_source_span_precision",
        "min_source_span_recall",
        "min_critical_exception_recall",
        "min_relation_recall",
        "max_false_relation_rate",
        "min_contradiction_recall",
        "max_orphan_claim_rate",
        "min_qualifier_connectivity",
        "max_unsupported_synthesis_rate",
        "min_replay_match_rate",
        "min_resume_reuse_ratio",
        "max_query_path_latency_delta_ms",
        "max_section_latency_p95_ms",
        "max_model_tokens_per_case",
        "thresholds_id",
    }
    _keys(payload, required=required, field_name="promotion thresholds")
    return ReaderPromotionThresholds(
        min_total_cases=_int(payload["min_total_cases"], "min_total_cases"),
        min_synthetic_cases=_int(
            payload["min_synthetic_cases"],
            "min_synthetic_cases",
        ),
        min_real_cases=_int(payload["min_real_cases"], "min_real_cases"),
        min_human_labelled_cases=_int(
            payload["min_human_labelled_cases"],
            "min_human_labelled_cases",
        ),
        min_claim_fidelity=_number(
            payload["min_claim_fidelity"],
            "min_claim_fidelity",
        ),
        min_source_span_precision=_number(
            payload["min_source_span_precision"],
            "min_source_span_precision",
        ),
        min_source_span_recall=_number(
            payload["min_source_span_recall"],
            "min_source_span_recall",
        ),
        min_critical_exception_recall=_number(
            payload["min_critical_exception_recall"],
            "min_critical_exception_recall",
        ),
        min_relation_recall=_number(
            payload["min_relation_recall"],
            "min_relation_recall",
        ),
        max_false_relation_rate=_number(
            payload["max_false_relation_rate"],
            "max_false_relation_rate",
        ),
        min_contradiction_recall=_number(
            payload["min_contradiction_recall"],
            "min_contradiction_recall",
        ),
        max_orphan_claim_rate=_number(
            payload["max_orphan_claim_rate"],
            "max_orphan_claim_rate",
        ),
        min_qualifier_connectivity=_number(
            payload["min_qualifier_connectivity"],
            "min_qualifier_connectivity",
        ),
        max_unsupported_synthesis_rate=_number(
            payload["max_unsupported_synthesis_rate"],
            "max_unsupported_synthesis_rate",
        ),
        min_replay_match_rate=_number(
            payload["min_replay_match_rate"],
            "min_replay_match_rate",
        ),
        min_resume_reuse_ratio=_number(
            payload["min_resume_reuse_ratio"],
            "min_resume_reuse_ratio",
        ),
        max_query_path_latency_delta_ms=_int(
            payload["max_query_path_latency_delta_ms"],
            "max_query_path_latency_delta_ms",
        ),
        max_section_latency_p95_ms=_optional_int(
            payload["max_section_latency_p95_ms"],
            "max_section_latency_p95_ms",
        ),
        max_model_tokens_per_case=_optional_number(
            payload["max_model_tokens_per_case"],
            "max_model_tokens_per_case",
        ),
        thresholds_id=_text(payload["thresholds_id"], "thresholds_id"),
    )


def _load_canonical_object(
    path: str | Path,
    field_name: str,
) -> tuple[dict[str, object], bytes]:
    source = Path(path)
    raw = source.read_bytes()
    value: Any = json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=_reject_duplicate_pairs,
        parse_constant=_reject_json_constant,
    )
    payload = dict(_mapping(value, field_name))
    if raw != canonical_json_bytes(payload) + b"\n":
        raise ReaderBenchmarkEvidenceVerificationError(
            f"{field_name} must use canonical JSON encoding"
        )
    return payload, raw


def _reject_duplicate_pairs(
    pairs: list[tuple[str, object]],
) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ReaderBenchmarkEvidenceVerificationError(
                f"duplicate JSON key: {key}"
            )
        result[key] = value
    return result


def _reject_json_constant(value: str) -> object:
    raise ReaderBenchmarkEvidenceVerificationError(
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
        raise ReaderBenchmarkEvidenceVerificationError(
            f"{field_name} keys mismatch; missing={missing}, unknown={unknown}"
        )


def _mapping(value: object, field_name: str) -> Mapping[str, object]:
    if not isinstance(value, dict) or any(
        not isinstance(key, str) for key in value
    ):
        raise ReaderBenchmarkEvidenceVerificationError(
            f"{field_name} must be a JSON object with string keys"
        )
    return cast(Mapping[str, object], value)


def _list(value: object, field_name: str) -> list[object]:
    if not isinstance(value, list):
        raise ReaderBenchmarkEvidenceVerificationError(
            f"{field_name} must be a JSON array"
        )
    return cast(list[object], value)


def _text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReaderBenchmarkEvidenceVerificationError(
            f"{field_name} must be non-empty text"
        )
    return value


def _int(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ReaderBenchmarkEvidenceVerificationError(
            f"{field_name} must be an integer"
        )
    return value


def _number(value: object, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ReaderBenchmarkEvidenceVerificationError(
            f"{field_name} must be a number"
        )
    return float(value)


def _optional_int(value: object, field_name: str) -> int | None:
    if value is None:
        return None
    return _int(value, field_name)


def _optional_number(value: object, field_name: str) -> float | None:
    if value is None:
        return None
    return _number(value, field_name)


def _text_array(value: object, field_name: str) -> tuple[str, ...]:
    return tuple(_text(item, field_name) for item in _list(value, field_name))


def _sha256(value: object, field_name: str) -> str:
    text = _text(value, field_name)
    if len(text) != 64 or text.lower() != text:
        raise ReaderBenchmarkEvidenceVerificationError(
            f"{field_name} must be lowercase SHA-256 hex"
        )
    try:
        int(text, 16)
    except ValueError as exc:
        raise ReaderBenchmarkEvidenceVerificationError(
            f"{field_name} must be lowercase SHA-256 hex"
        ) from exc
    return text


__all__ = [
    "READER_BENCHMARK_EVIDENCE_VERIFICATION_SCHEMA_VERSION",
    "ReaderBenchmarkEvidenceVerificationError",
    "ReaderBenchmarkEvidenceVerificationReceipt",
    "ReaderBenchmarkEvidenceVerifier",
]
