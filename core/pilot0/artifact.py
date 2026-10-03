"""Canonical, allowlisted and hash-frozen Pilot-0 Reader output artifacts.

This module serializes an already-produced ``SemanticReader`` result. It never
calls ``extract`` and never writes the source text or arbitrary runtime metadata.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import math
import re
from types import MappingProxyType
from typing import Any, Mapping

from core.knowledge_capsule import (
    CapsuleClaim,
    ClaimModality,
    KnowledgeCapsule,
    SourceSpan,
)
from core.deepseek_config import validate_deepseek_thinking_mode
from core.pilot0.config import Pilot0ReaderConfig
from core.pilot0.pdf_input import PARSER_NAME, PINNED_PARSER_VERSION
from core.semantic_reader import (
    RawSource,
    ReaderBudget,
    ReaderMode,
    ReaderResult,
    ReaderStatus,
    SemanticReader,
)

ARTIFACT_SCHEMA = "pilot0.frozen-reader.v1"
_ENVELOPE_KEYS = frozenset({"format", "payload_sha256", "payload"})
_SECRET_TEXT_PATTERNS = (
    re.compile(r"(?i)\b(?:sk|rk|ghp|gho|ghu|ghs|github_pat|xox[baprs])[-_][A-Za-z0-9_-]{12,}\b"),
    re.compile(r"(?i)\bAIza[0-9A-Za-z_-]{30,}\b"),
    re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/-]{12,}=?"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"(?i)\b(?:api[_ -]?key|access[_ -]?token|secret)\s*[:=]\s*[^\s,;]{8,}"),
)


class Pilot0ArtifactError(ValueError):
    """Reader output is not safe or complete enough to freeze."""


@dataclass(frozen=True, slots=True)
class FrozenReaderArtifact:
    """Exact canonical JSON bytes plus digests for payload and complete file."""

    json_bytes: bytes
    payload_sha256: str
    sha256: str


def canonical_json_bytes(value: Any) -> bytes:
    """Stable UTF-8 JSON encoding used for both payload and envelope hashing."""

    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise Pilot0ArtifactError("Artifact contains non-canonical JSON data") from exc


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise Pilot0ArtifactError("Duplicate JSON key in frozen Reader artifact")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise Pilot0ArtifactError(f"Non-finite JSON number is not allowed: {value}")


def _scan_for_secret_shaped_text(value: Any) -> None:
    if isinstance(value, str):
        if any(pattern.search(value) for pattern in _SECRET_TEXT_PATTERNS):
            raise Pilot0ArtifactError("Secret-shaped content refused by artifact allowlist")
        return
    if isinstance(value, dict):
        for key, child in value.items():
            if not isinstance(key, str):
                raise Pilot0ArtifactError("Artifact keys must be strings")
            if re.search(
                r"(?i)(api[_-]?key|secret|password|source[_-]?map|sealed[_-]?key|prior[_-]?answers?)",
                key,
            ):
                raise Pilot0ArtifactError("Forbidden field name in Reader artifact")
            _scan_for_secret_shaped_text(child)
        return
    if isinstance(value, (list, tuple)):
        for child in value:
            _scan_for_secret_shaped_text(child)
        return
    if value is None or isinstance(value, (bool, int, float)):
        if isinstance(value, float) and not math.isfinite(value):
            raise Pilot0ArtifactError("Non-finite number in Reader artifact")
        return
    raise Pilot0ArtifactError("Unsupported value type in Reader artifact")


def _span_payload(span: SourceSpan) -> dict[str, Any]:
    return {
        "span_id": span.span_id,
        "document_id": span.document_id,
        "source_revision": span.source_revision,
        "start_offset": span.start_offset,
        "end_offset": span.end_offset,
        "content_sha256": span.content_hash,
    }


def _claim_payload(claim: CapsuleClaim) -> dict[str, Any]:
    return {
        "claim_id": claim.claim_id,
        "text": claim.text,
        "modality": claim.modality.value,
        "extraction_confidence": claim.extraction_confidence,
        "truth_confidence": claim.truth_confidence,
        "qualifiers": list(claim.qualifiers),
        "uncertainties": list(claim.uncertainties),
        "applicability_conditions": list(claim.applicability_conditions),
        "temporal_scope": claim.temporal_scope,
        "source_spans": [_span_payload(span) for span in claim.source_spans],
    }


def _validate_payload(payload: Any) -> dict[str, Any]:
    """Enforce this exact schema; unknown fields never pass through to evaluation."""

    if not isinstance(payload, dict):
        raise Pilot0ArtifactError("Frozen Reader payload must be a JSON object")
    expected_top = {
        "schema",
        "reader",
        "source",
        "config",
        "claims",
        "cards",
        "relations",
        "coverage",
        "synthesis",
        "warnings",
        "execution",
    }
    if set(payload) != expected_top or payload.get("schema") != ARTIFACT_SCHEMA:
        raise Pilot0ArtifactError("Frozen Reader payload has an unsupported schema")

    expected = {
        "reader": {"id", "version", "capsule_id", "capsule_schema", "prompt_version"},
        "source": {"document_id", "revision", "parser"},
        "config": {"mode", "budget", "reader"},
        "budget": {"max_source_chars", "max_claims", "max_essence_chars"},
        "reader_config": {"provider", "model_selection", "deepseek_thinking"},
        "parser": {"name", "version"},
        "claim": {
            "claim_id",
            "text",
            "modality",
            "extraction_confidence",
            "truth_confidence",
            "qualifiers",
            "uncertainties",
            "applicability_conditions",
            "temporal_scope",
            "source_spans",
        },
        "span": {
            "span_id",
            "document_id",
            "source_revision",
            "start_offset",
            "end_offset",
            "content_sha256",
        },
        "coverage": {
            "capsule_coverage_score",
            "compression_ratio",
            "reader_core_axes",
            "card_count",
            "relation_count",
        },
        "synthesis": {"essence", "entities", "omitted_questions"},
        "warning": {"code", "safe_message"},
        "execution": {
            "artifact_builder",
            "reader_result_status",
            "source_character_count",
            "claim_count",
            "warning_count",
            "local_network_calls",
            "credential_fields_included",
            "raw_source_field_included",
            "full_provenance_map_included",
        },
    }
    for name in ("reader", "source", "config", "coverage", "synthesis", "execution"):
        value = payload.get(name)
        if not isinstance(value, dict) or set(value) != expected[name]:
            raise Pilot0ArtifactError(f"Frozen Reader {name} object has unknown or missing fields")
    if not isinstance(payload["source"]["parser"], dict) or set(payload["source"]["parser"]) != expected["parser"]:
        raise Pilot0ArtifactError("Frozen Reader parser identity is not allowlisted")
    if not isinstance(payload["config"].get("budget"), dict) or set(payload["config"]["budget"]) != expected["budget"]:
        raise Pilot0ArtifactError("Frozen Reader budget is not allowlisted")
    if not isinstance(payload["config"].get("reader"), dict) or set(payload["config"]["reader"]) != expected["reader_config"]:
        raise Pilot0ArtifactError("Frozen Reader configuration is not allowlisted")

    if not isinstance(payload["claims"], list) or not payload["claims"]:
        raise Pilot0ArtifactError("Frozen Reader artifact must contain at least one claim")
    for claim in payload["claims"]:
        if not isinstance(claim, dict) or set(claim) != expected["claim"]:
            raise Pilot0ArtifactError("Frozen claim has unknown or missing fields")
        if not isinstance(claim["source_spans"], list) or not claim["source_spans"]:
            raise Pilot0ArtifactError("Every frozen claim requires source spans")
        for span in claim["source_spans"]:
            if not isinstance(span, dict) or set(span) != expected["span"]:
                raise Pilot0ArtifactError("Frozen source span has unknown or missing fields")
    if payload["cards"] != [] or payload["relations"] != []:
        raise Pilot0ArtifactError("This SemanticReader contract does not emit cards or relations")
    if payload["coverage"]["reader_core_axes"] != []:
        raise Pilot0ArtifactError("ReaderCore coverage axes are not emitted by SemanticReader")
    if payload["coverage"]["card_count"] != 0 or payload["coverage"]["relation_count"] != 0:
        raise Pilot0ArtifactError("Coverage counts must match the empty cards/relations")
    if not isinstance(payload["warnings"], list):
        raise Pilot0ArtifactError("Frozen Reader warnings must be a list")
    for warning in payload["warnings"]:
        if not isinstance(warning, dict) or set(warning) != expected["warning"]:
            raise Pilot0ArtifactError("Frozen Reader warning has unknown or missing fields")
    if payload["source"]["parser"] != {
        "name": PARSER_NAME,
        "version": PINNED_PARSER_VERSION,
    }:
        raise Pilot0ArtifactError("Frozen Reader parser identity differs from the Pilot-0 pin")
    reader_config = payload["config"]["reader"]
    if reader_config.get("provider") != "deepseek" or reader_config.get("model_selection") != "OWNER_SELECTED":
        raise Pilot0ArtifactError("Pilot-0 provider/model selection is outside the authorized config")
    try:
        validate_deepseek_thinking_mode(reader_config.get("deepseek_thinking"))
    except ValueError as exc:
        raise Pilot0ArtifactError("Pilot-0 thinking configuration is not allowlisted") from exc

    reader = payload["reader"]
    for field in ("id", "version", "capsule_id", "capsule_schema"):
        if not isinstance(reader[field], str) or not reader[field].strip():
            raise Pilot0ArtifactError(f"Frozen Reader {field} must be a non-empty string")
    if reader["prompt_version"] is not None and not isinstance(reader["prompt_version"], str):
        raise Pilot0ArtifactError("Frozen Reader prompt_version must be a string or null")

    source = payload["source"]
    if not isinstance(source["document_id"], str) or not source["document_id"].strip():
        raise Pilot0ArtifactError("Frozen source document_id must be non-empty")
    if not isinstance(source["revision"], str) or not re.fullmatch(
        r"sha256:[0-9a-f]{64}", source["revision"]
    ):
        raise Pilot0ArtifactError("Frozen source revision must be a SHA-256 identity")

    config = payload["config"]
    if config["mode"] not in {mode.value for mode in ReaderMode}:
        raise Pilot0ArtifactError("Frozen Reader mode is not supported")
    budget = config["budget"]
    for field in ("max_source_chars", "max_claims", "max_essence_chars"):
        if isinstance(budget[field], bool) or not isinstance(budget[field], int) or budget[field] <= 0:
            raise Pilot0ArtifactError("Frozen Reader budget values must be positive integers")
    if len(payload["claims"]) > budget["max_claims"]:
        raise Pilot0ArtifactError("Frozen claim count exceeds the recorded Reader budget")

    for claim in payload["claims"]:
        for field in ("claim_id", "text"):
            if not isinstance(claim[field], str) or not claim[field].strip():
                raise Pilot0ArtifactError(f"Frozen claim {field} must be non-empty")
        if claim["modality"] not in {modality.value for modality in ClaimModality}:
            raise Pilot0ArtifactError("Frozen claim modality is not supported")
        for field in ("extraction_confidence", "truth_confidence"):
            value = claim[field]
            if field == "truth_confidence" and value is None:
                continue
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 1:
                raise Pilot0ArtifactError("Frozen claim confidence must be finite and in [0, 1]")
        for field in ("qualifiers", "uncertainties", "applicability_conditions"):
            if not isinstance(claim[field], list) or any(
                not isinstance(item, str) or not item.strip() for item in claim[field]
            ):
                raise Pilot0ArtifactError(f"Frozen claim {field} must contain non-empty strings")
        if claim["temporal_scope"] is not None and not isinstance(claim["temporal_scope"], str):
            raise Pilot0ArtifactError("Frozen claim temporal_scope must be a string or null")
        for span in claim["source_spans"]:
            if (
                not isinstance(span["span_id"], str)
                or not span["span_id"].strip()
                or span["document_id"] != source["document_id"]
                or span["source_revision"] != source["revision"]
                or isinstance(span["start_offset"], bool)
                or not isinstance(span["start_offset"], int)
                or isinstance(span["end_offset"], bool)
                or not isinstance(span["end_offset"], int)
                or span["start_offset"] < 0
                or span["end_offset"] <= span["start_offset"]
                or span["end_offset"] - span["start_offset"] != len(claim["text"])
                or not isinstance(span["content_sha256"], str)
                or not re.fullmatch(r"[0-9a-f]{64}", span["content_sha256"])
            ):
                raise Pilot0ArtifactError("Frozen source span does not match its source identity")

    coverage = payload["coverage"]
    score = coverage["capsule_coverage_score"]
    ratio = coverage["compression_ratio"]
    if isinstance(score, bool) or not isinstance(score, (int, float)) or not math.isfinite(score) or not 0 <= score <= 1:
        raise Pilot0ArtifactError("Frozen coverage score must be finite and in [0, 1]")
    if isinstance(ratio, bool) or not isinstance(ratio, (int, float)) or not math.isfinite(ratio) or ratio <= 0:
        raise Pilot0ArtifactError("Frozen compression ratio must be finite and positive")

    synthesis = payload["synthesis"]
    if not isinstance(synthesis["essence"], str) or not synthesis["essence"].strip():
        raise Pilot0ArtifactError("Frozen synthesis essence must be non-empty")
    if len(synthesis["essence"]) > budget["max_essence_chars"]:
        raise Pilot0ArtifactError("Frozen synthesis exceeds the recorded Reader budget")
    for field in ("entities", "omitted_questions"):
        if not isinstance(synthesis[field], list) or any(
            not isinstance(item, str) or not item.strip() for item in synthesis[field]
        ):
            raise Pilot0ArtifactError(f"Frozen synthesis {field} must contain non-empty strings")
    for warning in payload["warnings"]:
        if any(not isinstance(warning[field], str) or not warning[field].strip() for field in ("code", "safe_message")):
            raise Pilot0ArtifactError("Frozen warning code/message must be non-empty strings")

    execution = payload["execution"]
    if execution["artifact_builder"] != "pilot0-canonicalizer-v1":
        raise Pilot0ArtifactError("Frozen artifact builder identity is unsupported")
    if execution["reader_result_status"] not in {ReaderStatus.SUCCESS.value, ReaderStatus.PARTIAL.value}:
        raise Pilot0ArtifactError("Frozen Reader status must be success or partial")
    for field in ("source_character_count", "claim_count", "warning_count", "local_network_calls"):
        value = execution[field]
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise Pilot0ArtifactError("Frozen execution counts must be non-negative integers")
    if (
        execution["source_character_count"] > budget["max_source_chars"]
        or execution["source_character_count"] <= 0
        or execution["claim_count"] != len(payload["claims"])
        or execution["warning_count"] != len(payload["warnings"])
        or execution["local_network_calls"] != 0
        or execution["credential_fields_included"] is not False
        or execution["raw_source_field_included"] is not False
        or execution["full_provenance_map_included"] is not False
    ):
        raise Pilot0ArtifactError("Frozen execution metadata violates the offline allowlist")
    if execution["reader_result_status"] == ReaderStatus.PARTIAL.value:
        if not payload["warnings"]:
            raise Pilot0ArtifactError("Partial frozen Reader results require warnings")
    elif payload["warnings"]:
        raise Pilot0ArtifactError("Successful frozen Reader results must not include warnings")
    if any(
        span["end_offset"] > execution["source_character_count"]
        for claim in payload["claims"]
        for span in claim["source_spans"]
    ):
        raise Pilot0ArtifactError("Frozen source span exceeds the recorded source length")
    _scan_for_secret_shaped_text(payload)
    return payload


def freeze_reader_output(
    reader: SemanticReader,
    source: RawSource,
    *,
    mode: ReaderMode,
    budget: ReaderBudget,
    result: ReaderResult,
    reader_config: Pilot0ReaderConfig | None = None,
    parser_name: str = PARSER_NAME,
    parser_version: str = PINNED_PARSER_VERSION,
) -> FrozenReaderArtifact:
    """Canonicalize a supplied Reader result without calling the Reader."""

    if not isinstance(reader, SemanticReader):
        raise Pilot0ArtifactError("reader must implement the existing SemanticReader protocol")
    if not isinstance(source, RawSource) or not isinstance(result, ReaderResult):
        raise Pilot0ArtifactError("source/result must use the existing SemanticReader contracts")
    if not isinstance(mode, ReaderMode) or not isinstance(budget, ReaderBudget):
        raise Pilot0ArtifactError("mode and budget must use the existing Reader contracts")
    if not result.accepted or result.capsule is None:
        raise Pilot0ArtifactError("Only successful or partial Reader outputs can be frozen")
    if not source.source_revision:
        raise Pilot0ArtifactError("A source revision is required for a frozen artifact")
    if len(source.text) > budget.max_source_chars:
        raise Pilot0ArtifactError("Source text exceeds the declared Reader budget")
    if parser_name != PARSER_NAME or parser_version != PINNED_PARSER_VERSION:
        raise Pilot0ArtifactError("Only the pinned local pypdf parser is allowed")

    capsule: KnowledgeCapsule = result.capsule
    reader_id = reader.reader_id
    reader_version = reader.reader_version
    if (capsule.source_document_id, capsule.reader_id, capsule.reader_version) != (
        source.document_id,
        reader_id,
        reader_version,
    ):
        raise Pilot0ArtifactError("Reader result identity does not match its source/Reader")
    if not capsule.prompt_version or capsule.prompt_version.strip() == "":
        prompt_version = None
    else:
        prompt_version = capsule.prompt_version

    for claim in capsule.claims:
        if not any(
            source.text[span.start_offset : span.end_offset] == claim.text
            and span.verify(source.text)
            and span.document_id == source.document_id
            and span.source_revision == source.source_revision
            for span in claim.source_spans
            if span.end_offset <= len(source.text)
        ):
            raise Pilot0ArtifactError("Claim is not exactly linked to the declared source revision")

    warnings = [
        {"code": warning.code, "safe_message": warning.safe_message}
        for warning in result.warnings
    ]
    config = reader_config or Pilot0ReaderConfig()
    payload: dict[str, Any] = {
        "schema": ARTIFACT_SCHEMA,
        "reader": {
            "id": reader_id,
            "version": reader_version,
            "capsule_id": capsule.capsule_id,
            "capsule_schema": capsule.schema_version,
            "prompt_version": prompt_version,
        },
        "source": {
            "document_id": source.document_id,
            "revision": source.source_revision,
            "parser": {"name": parser_name, "version": parser_version},
        },
        "config": {
            "mode": mode.value,
            "budget": {
                "max_source_chars": budget.max_source_chars,
                "max_claims": budget.max_claims,
                "max_essence_chars": budget.max_essence_chars,
            },
            "reader": config.to_safe_dict(),
        },
        "claims": [_claim_payload(claim) for claim in capsule.claims],
        "cards": [],
        "relations": [],
        "coverage": {
            "capsule_coverage_score": capsule.coverage_score,
            "compression_ratio": capsule.compression_ratio,
            "reader_core_axes": [],
            "card_count": 0,
            "relation_count": 0,
        },
        "synthesis": {
            "essence": capsule.essence,
            "entities": list(capsule.entities),
            "omitted_questions": list(capsule.omitted_questions),
        },
        "warnings": warnings,
        "execution": {
            "artifact_builder": "pilot0-canonicalizer-v1",
            "reader_result_status": result.status.value,
            "source_character_count": len(source.text),
            "claim_count": len(capsule.claims),
            "warning_count": len(warnings),
            "local_network_calls": 0,
            "credential_fields_included": False,
            "raw_source_field_included": False,
            "full_provenance_map_included": False,
        },
    }
    payload = _validate_payload(payload)
    payload_bytes = canonical_json_bytes(payload)
    payload_digest = sha256(payload_bytes).hexdigest()
    envelope = {
        "format": ARTIFACT_SCHEMA,
        "payload_sha256": payload_digest,
        "payload": payload,
    }
    frozen_bytes = canonical_json_bytes(envelope)
    return FrozenReaderArtifact(
        json_bytes=frozen_bytes,
        payload_sha256=payload_digest,
        sha256=sha256(frozen_bytes).hexdigest(),
    )


def parse_frozen_reader_json(
    frozen_reader_json: bytes,
    *,
    expected_sha256: str | None = None,
) -> Mapping[str, Any]:
    """Verify exact canonical frozen JSON and return a recursively read-only payload."""

    if not isinstance(frozen_reader_json, bytes):
        raise Pilot0ArtifactError("Evaluator accepts frozen Reader JSON bytes only")
    if expected_sha256 is not None and sha256(frozen_reader_json).hexdigest() != expected_sha256:
        raise Pilot0ArtifactError("Exact frozen Reader byte hash does not match")
    try:
        envelope = json.loads(
            frozen_reader_json.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_json_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Pilot0ArtifactError("Frozen Reader input is not valid UTF-8 JSON") from exc
    if not isinstance(envelope, dict) or set(envelope) != _ENVELOPE_KEYS:
        raise Pilot0ArtifactError("Evaluator accepts only the frozen Reader JSON envelope")
    if envelope.get("format") != ARTIFACT_SCHEMA:
        raise Pilot0ArtifactError("Frozen Reader JSON format is not supported")
    payload = _validate_payload(envelope.get("payload"))
    payload_bytes = canonical_json_bytes(payload)
    if sha256(payload_bytes).hexdigest() != envelope.get("payload_sha256"):
        raise Pilot0ArtifactError("Frozen Reader payload hash verification failed")
    if canonical_json_bytes(envelope) != frozen_reader_json:
        raise Pilot0ArtifactError("Frozen Reader JSON bytes are not in canonical frozen form")
    return _deep_freeze(payload)


def _deep_freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _deep_freeze(child) for key, child in value.items()})
    if isinstance(value, list):
        return tuple(_deep_freeze(child) for child in value)
    return value


__all__ = [
    "ARTIFACT_SCHEMA",
    "FrozenReaderArtifact",
    "Pilot0ArtifactError",
    "canonical_json_bytes",
    "freeze_reader_output",
    "parse_frozen_reader_json",
]
