"""Read-only selective-memory candidate extraction (PR-ARM-03, issue #92).

This module proposes structured candidates for offline/shadow evaluation only.
It has no dependency on Canon, WorkingMemoryGate, Write Gate, embeddings, an
LLM, or the network, and it exposes no write-capable callback.  Candidate
admission belongs to PR-ARM-04.
"""

from __future__ import annotations

import hashlib
import os
import re
import unicodedata
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Iterable

EXTRACTOR_VERSION = "arm03-rule-1"
POLICY_VERSION = "arm03-policy-1"


class CandidateType(str, Enum):
    PREFERENCE = "preference"
    PERSONAL_FACT = "personal_fact"
    RELATIONSHIP = "relationship"
    GOAL = "goal"
    COMMITMENT = "commitment"
    CONSTRAINT = "constraint"
    PROJECT_CONTEXT = "project_context"
    PROCEDURE_HINT = "procedure_hint"
    TEMPORAL_EVENT = "temporal_event"
    OTHER = "other"


class TemporalScope(str, Enum):
    TIMELESS = "timeless"
    CURRENT = "current"
    TEMPORARY = "temporary"
    HISTORICAL = "historical"
    FUTURE_INTENT = "future_intent"
    UNKNOWN = "unknown"


class SensitivityFlag(str, Enum):
    PERSONAL = "personal"
    CONTACT = "contact"
    LOCATION = "location"
    FINANCIAL = "financial"
    MEDICAL = "medical"
    LEGAL = "legal"
    CREDENTIAL = "credential"
    SECURITY = "security"
    MINOR_RELATED = "minor_related"
    HIGH_RISK = "high_risk"


class RejectionReason(str, Enum):
    NO_EXACT_SPAN = "no_exact_span"
    TOO_SHORT = "too_short"
    TOO_LONG = "too_long"
    LOW_STRUCTURAL_CONFIDENCE = "low_structural_confidence"
    DUPLICATE_WITHIN_INPUT = "duplicate_within_input"
    SENSITIVE_BLOCKED = "sensitive_blocked"
    CREDENTIAL_DETECTED = "credential_detected"
    UNSUPPORTED_TYPE = "unsupported_type"
    BUDGET_EXCEEDED = "budget_exceeded"
    MALFORMED_TEMPORAL_SCOPE = "malformed_temporal_scope"
    POLICY_DENIED = "policy_denied"


class SupersessionHint(str, Enum):
    POSSIBLE_DUPLICATE_OF = "possible_duplicate_of"
    POSSIBLE_UPDATE_OF = "possible_update_of"
    POSSIBLE_SUPERSEDES = "possible_supersedes"
    POSSIBLE_CONFLICT_WITH = "possible_conflict_with"


@dataclass(frozen=True, slots=True)
class SourceSpan:
    start_char: int
    end_char: int
    text: str
    source_ref: str


@dataclass(frozen=True, slots=True)
class MemoryCandidate:
    candidate_id: str
    candidate_type: CandidateType
    normalized_text: str
    source_span: SourceSpan
    temporal_scope: TemporalScope
    sensitivity: tuple[SensitivityFlag, ...]
    confidence: float
    dedup_key: str
    supersession_hint: SupersessionHint | None
    policy_version: str
    extractor_version: str


@dataclass(frozen=True, slots=True)
class RejectedCandidate:
    reason: RejectionReason
    source_span: SourceSpan | None
    detail_code: str


@dataclass(frozen=True, slots=True)
class CandidateExtractionTrace:
    input_id: str
    extractor_version: str
    policy_version: str
    candidate_count: int
    rejected_count: int
    candidate_types: tuple[tuple[str, int], ...]
    sensitivity_counts: tuple[tuple[str, int], ...]
    truncated: bool
    elapsed_ms: float
    canon_write_count: int = 0
    memory_write_count: int = 0
    write_gate_call_count: int = 0
    truth_gate_bypass_count: int = 0


@dataclass(frozen=True, slots=True)
class CandidateExtractionResult:
    candidates: tuple[MemoryCandidate, ...]
    rejected: tuple[RejectedCandidate, ...]
    warnings: tuple[str, ...]
    truncated: bool
    extractor_version: str
    policy_version: str
    trace: CandidateExtractionTrace


@dataclass(frozen=True, slots=True)
class CandidateExtractionPolicy:
    max_candidates_per_input: int = 12
    max_candidate_chars: int = 500
    max_total_candidate_chars: int = 2_000
    max_source_spans: int = 64
    min_candidate_chars: int = 4
    block_credentials: bool = True
    redact_sensitive_payloads: bool = True
    extractor_version: str = EXTRACTOR_VERSION
    policy_version: str = POLICY_VERSION

    def __post_init__(self) -> None:
        numeric = (
            self.max_candidates_per_input,
            self.max_candidate_chars,
            self.max_total_candidate_chars,
            self.max_source_spans,
            self.min_candidate_chars,
        )
        if any(value < 1 for value in numeric):
            raise ValueError("candidate extraction limits must be positive")
        if self.min_candidate_chars > self.max_candidate_chars:
            raise ValueError("min_candidate_chars must not exceed max_candidate_chars")


_SENTENCE_RE = re.compile(r"[^.!?\n]+(?:[.!?]+|$)", re.UNICODE)
_WS_RE = re.compile(r"\s+", re.UNICODE)

_CREDENTIAL_RE = re.compile(
    r"(?ix)(?:"
    r"(?:api[_ -]?key|token|password|passwd|secret)\s*[:=]\s*[A-Za-z0-9_\-./+=]{6,}"
    r"|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"
    r"|gh[pousr]_[A-Za-z0-9]{20,}"
    r")"
)
_CONTACT_RE = re.compile(r"(?i)(?:\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b|\+?\d[\d ()-]{7,}\d)")
_FINANCIAL_RE = re.compile(r"(?i)\b(?:iban|swift|credit card|bank account|карта|сч[её]т)\b")
_MEDICAL_RE = re.compile(
    r"(?i)\b(?:diagnos(?:is|ed)|medication|prescription|cancer|diabetes|"
    r"диагноз|лекарств|рецепт|рак|диабет)\b"
)
_LEGAL_RE = re.compile(r"(?i)\b(?:lawsuit|attorney|court order|суд|адвокат|иск)\b")
_LOCATION_RE = re.compile(r"(?i)\b(?:home address|street address|адрес проживания|живу по адресу)\b")
_MINOR_RE = re.compile(r"(?i)\b(?:my child|my son|my daughter|minor|мой ребёнок|мой ребенок|сыну|дочери)\b")
_HIGH_RISK_RE = re.compile(r"(?i)\b(?:suicid|self[- ]harm|kill myself|самоубий|самоповрежд)\b")

_TYPE_PATTERNS: tuple[tuple[CandidateType, re.Pattern[str]], ...] = (
    (
        CandidateType.PREFERENCE,
        re.compile(
            r"(?i)\b(?:i prefer|i like|i love|my preference|я предпочитаю|мне нравится|я люблю)\b"
        ),
    ),
    (
        CandidateType.GOAL,
        re.compile(r"(?i)\b(?:my goal|i want to|i plan to|моя цель|я хочу|хочу|планирую)\b"),
    ),
    (
        CandidateType.COMMITMENT,
        re.compile(r"(?i)\b(?:i promise|i will|обещаю|я сделаю|сделаю к|обязуюсь)\b"),
    ),
    (
        CandidateType.CONSTRAINT,
        re.compile(r"(?i)\b(?:must not|must|cannot|can't|constraint|нельзя|не могу|обязательно|ограничение)\b"),
    ),
    (
        CandidateType.RELATIONSHIP,
        re.compile(
            r"(?i)\b(?:my wife|my husband|my brother|my sister|my partner|"
            r"моя жена|мой муж|мой брат|моя сестра|мой партн[её]р)\b"
        ),
    ),
    (
        CandidateType.PROJECT_CONTEXT,
        re.compile(r"(?i)\b(?:project|repository|repo|codebase|проект|репозиторий|кодовая база)\b"),
    ),
    (
        CandidateType.PROCEDURE_HINT,
        re.compile(r"(?i)\b(?:workflow|procedure|steps?|runbook|процедура|шаги|регламент)\b"),
    ),
    (
        CandidateType.PERSONAL_FACT,
        re.compile(r"(?i)\b(?:i am|i live|i work|my name is|я живу|я работаю|меня зовут|мне \d+)\b"),
    ),
)

_FUTURE_RE = re.compile(r"(?i)\b(?:tomorrow|next week|next month|will|plan to|завтра|на следующей неделе|буду|планирую)\b")
_TEMPORARY_RE = re.compile(r"(?i)\b(?:for now|temporarily|this week|today only|пока|временно|на этой неделе|только сегодня)\b")
_HISTORICAL_RE = re.compile(r"(?i)\b(?:used to|previously|last year|раньше|ранее|в прошлом году)\b")
_CURRENT_RE = re.compile(r"(?i)\b(?:currently|now|today|сейчас|сегодня|в настоящее время)\b")
_DATE_RE = re.compile(r"\b(?:\d{4}-\d{2}-\d{2}|\d{1,2}[./-]\d{1,2}[./-]\d{2,4})\b")
_NEGATION_RE = re.compile(r"(?i)\b(?:not|never|don't|do not|не|никогда)\b")


def _env_flag(name: str, default: str = "0") -> bool:
    return (os.getenv(name, default) or "").strip().lower() in {"1", "true", "yes", "on"}


def is_selective_memory_candidate_shadow_enabled() -> bool:
    """Feature flag for diagnostic/shadow invocation. Default is OFF."""
    return _env_flag("ENABLE_SELECTIVE_MEMORY_CANDIDATE_SHADOW")


def normalize_candidate_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text)
    return _WS_RE.sub(" ", normalized).strip()


def validate_source_span(source_text: str, span: SourceSpan) -> bool:
    if span.start_char < 0 or span.end_char < span.start_char:
        return False
    if span.end_char > len(source_text):
        return False
    return source_text[span.start_char : span.end_char] == span.text


def _digest(parts: Iterable[str]) -> str:
    payload = "\0".join(parts).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _iter_spans(source_text: str, source_ref: str, limit: int) -> Iterable[SourceSpan]:
    count = 0
    for match in _SENTENCE_RE.finditer(source_text):
        if count >= limit:
            return
        raw = match.group(0)
        left = len(raw) - len(raw.lstrip())
        right = len(raw.rstrip())
        if right <= left:
            continue
        start = match.start() + left
        end = match.start() + right
        span = SourceSpan(start, end, source_text[start:end], source_ref)
        if validate_source_span(source_text, span):
            count += 1
            yield span


def _candidate_type(text: str) -> CandidateType:
    for candidate_type, pattern in _TYPE_PATTERNS:
        if pattern.search(text):
            return candidate_type
    if _DATE_RE.search(text) or _FUTURE_RE.search(text) or _HISTORICAL_RE.search(text):
        return CandidateType.TEMPORAL_EVENT
    return CandidateType.OTHER


def _temporal_scope(text: str, candidate_type: CandidateType) -> TemporalScope:
    if _FUTURE_RE.search(text) or candidate_type in {CandidateType.GOAL, CandidateType.COMMITMENT}:
        return TemporalScope.FUTURE_INTENT
    if _TEMPORARY_RE.search(text):
        return TemporalScope.TEMPORARY
    if _HISTORICAL_RE.search(text):
        return TemporalScope.HISTORICAL
    if _CURRENT_RE.search(text):
        return TemporalScope.CURRENT
    if candidate_type in {CandidateType.PREFERENCE, CandidateType.RELATIONSHIP, CandidateType.PERSONAL_FACT}:
        return TemporalScope.TIMELESS
    return TemporalScope.UNKNOWN


def _sensitivity(text: str) -> tuple[SensitivityFlag, ...]:
    flags: set[SensitivityFlag] = set()
    if _CREDENTIAL_RE.search(text):
        flags.update({SensitivityFlag.CREDENTIAL, SensitivityFlag.SECURITY, SensitivityFlag.HIGH_RISK})
    if _CONTACT_RE.search(text):
        flags.update({SensitivityFlag.CONTACT, SensitivityFlag.PERSONAL})
    if _FINANCIAL_RE.search(text):
        flags.update({SensitivityFlag.FINANCIAL, SensitivityFlag.HIGH_RISK})
    if _MEDICAL_RE.search(text):
        flags.update({SensitivityFlag.MEDICAL, SensitivityFlag.HIGH_RISK})
    if _LEGAL_RE.search(text):
        flags.update({SensitivityFlag.LEGAL, SensitivityFlag.HIGH_RISK})
    if _LOCATION_RE.search(text):
        flags.update({SensitivityFlag.LOCATION, SensitivityFlag.PERSONAL})
    if _MINOR_RE.search(text):
        flags.update({SensitivityFlag.MINOR_RELATED, SensitivityFlag.PERSONAL, SensitivityFlag.HIGH_RISK})
    if _HIGH_RISK_RE.search(text):
        flags.add(SensitivityFlag.HIGH_RISK)
    return tuple(sorted(flags, key=lambda item: item.value))


def _redact(text: str) -> str:
    return _CONTACT_RE.sub("[REDACTED_CONTACT]", _CREDENTIAL_RE.sub("[REDACTED_SECRET]", text))


def _confidence(candidate_type: CandidateType, text: str) -> float:
    if candidate_type is CandidateType.OTHER:
        return 0.35
    score = 0.78
    if _NEGATION_RE.search(text):
        score -= 0.05
    if len(text) < 12:
        score -= 0.10
    return max(0.0, min(1.0, round(score, 3)))


def _empty_result(
    source_text: str,
    source_ref: str,
    policy: CandidateExtractionPolicy,
    *,
    warning: str | None = None,
) -> CandidateExtractionResult:
    input_id = _digest((source_ref, source_text, policy.extractor_version, policy.policy_version))
    warnings = (warning,) if warning else ()
    trace = CandidateExtractionTrace(
        input_id=input_id,
        extractor_version=policy.extractor_version,
        policy_version=policy.policy_version,
        candidate_count=0,
        rejected_count=0,
        candidate_types=(),
        sensitivity_counts=(),
        truncated=False,
        elapsed_ms=0.0,
    )
    return CandidateExtractionResult(
        candidates=(),
        rejected=(),
        warnings=warnings,
        truncated=False,
        extractor_version=policy.extractor_version,
        policy_version=policy.policy_version,
        trace=trace,
    )


def extract_memory_candidates(
    source_text: str,
    *,
    source_ref: str,
    policy: CandidateExtractionPolicy | None = None,
    clock: Callable[[], float] | None = None,
) -> CandidateExtractionResult:
    """Extract bounded proposal candidates without writing any state.

    ``clock`` is optional so production diagnostics may measure elapsed time;
    omitting it keeps the result fully deterministic (elapsed_ms == 0.0).
    """
    active_policy = policy or CandidateExtractionPolicy()
    if not isinstance(source_text, str):
        return _empty_result("", source_ref, active_policy, warning="invalid_source_text")
    if not source_text.strip():
        return _empty_result(source_text, source_ref, active_policy)
    if not source_ref.strip():
        return _empty_result(source_text, "<missing>", active_policy, warning="missing_source_ref")

    started = clock() if clock else 0.0
    candidates: list[MemoryCandidate] = []
    rejected: list[RejectedCandidate] = []
    warnings: list[str] = []
    seen_dedup: dict[str, str] = {}
    total_chars = 0
    truncated = False

    for span in _iter_spans(source_text, source_ref, active_policy.max_source_spans):
        normalized = normalize_candidate_text(span.text)
        if len(normalized) < active_policy.min_candidate_chars:
            rejected.append(RejectedCandidate(RejectionReason.TOO_SHORT, span, "min_candidate_chars"))
            continue
        if len(normalized) > active_policy.max_candidate_chars:
            rejected.append(RejectedCandidate(RejectionReason.TOO_LONG, span, "max_candidate_chars"))
            continue

        sensitivity = _sensitivity(normalized)
        if active_policy.block_credentials and SensitivityFlag.CREDENTIAL in sensitivity:
            safe_span = SourceSpan(
                span.start_char,
                span.end_char,
                _redact(span.text) if active_policy.redact_sensitive_payloads else "[REDACTED]",
                span.source_ref,
            )
            rejected.append(
                RejectedCandidate(RejectionReason.CREDENTIAL_DETECTED, safe_span, "credential_policy")
            )
            continue

        candidate_type = _candidate_type(normalized)
        temporal_scope = _temporal_scope(normalized, candidate_type)
        safe_text = _redact(normalized) if active_policy.redact_sensitive_payloads else normalized
        dedup_material = normalize_candidate_text(safe_text).casefold()
        dedup_key = _digest((candidate_type.value, temporal_scope.value, dedup_material))

        if dedup_key in seen_dedup:
            rejected.append(
                RejectedCandidate(
                    RejectionReason.DUPLICATE_WITHIN_INPUT,
                    span,
                    seen_dedup[dedup_key],
                )
            )
            continue

        if len(candidates) >= active_policy.max_candidates_per_input:
            truncated = True
            rejected.append(RejectedCandidate(RejectionReason.BUDGET_EXCEEDED, span, "max_candidates"))
            continue
        if total_chars + len(safe_text) > active_policy.max_total_candidate_chars:
            truncated = True
            rejected.append(RejectedCandidate(RejectionReason.BUDGET_EXCEEDED, span, "max_total_chars"))
            continue

        candidate_id = _digest(
            (
                source_ref,
                str(span.start_char),
                str(span.end_char),
                candidate_type.value,
                temporal_scope.value,
                dedup_key,
                active_policy.extractor_version,
                active_policy.policy_version,
            )
        )
        candidate = MemoryCandidate(
            candidate_id=candidate_id,
            candidate_type=candidate_type,
            normalized_text=safe_text,
            source_span=span,
            temporal_scope=temporal_scope,
            sensitivity=sensitivity,
            confidence=_confidence(candidate_type, normalized),
            dedup_key=dedup_key,
            supersession_hint=None,
            policy_version=active_policy.policy_version,
            extractor_version=active_policy.extractor_version,
        )
        seen_dedup[dedup_key] = candidate_id
        candidates.append(candidate)
        total_chars += len(safe_text)

    if truncated:
        warnings.append("candidate_budget_truncated")

    type_counts: dict[str, int] = {}
    sensitivity_counts: dict[str, int] = {}
    for candidate in candidates:
        type_counts[candidate.candidate_type.value] = type_counts.get(candidate.candidate_type.value, 0) + 1
        for flag in candidate.sensitivity:
            sensitivity_counts[flag.value] = sensitivity_counts.get(flag.value, 0) + 1

    elapsed_ms = 0.0
    if clock:
        elapsed_ms = max(0.0, round((clock() - started) * 1000.0, 3))
    input_id = _digest((source_ref, source_text, active_policy.extractor_version, active_policy.policy_version))
    trace = CandidateExtractionTrace(
        input_id=input_id,
        extractor_version=active_policy.extractor_version,
        policy_version=active_policy.policy_version,
        candidate_count=len(candidates),
        rejected_count=len(rejected),
        candidate_types=tuple(sorted(type_counts.items())),
        sensitivity_counts=tuple(sorted(sensitivity_counts.items())),
        truncated=truncated,
        elapsed_ms=elapsed_ms,
    )
    return CandidateExtractionResult(
        candidates=tuple(candidates),
        rejected=tuple(rejected),
        warnings=tuple(warnings),
        truncated=truncated,
        extractor_version=active_policy.extractor_version,
        policy_version=active_policy.policy_version,
        trace=trace,
    )


def run_shadow_extraction(
    source_text: str,
    *,
    source_ref: str,
    policy: CandidateExtractionPolicy | None = None,
) -> CandidateExtractionResult:
    """Flag-gated diagnostic entrypoint; never changes the live memory path."""
    active_policy = policy or CandidateExtractionPolicy()
    if not is_selective_memory_candidate_shadow_enabled():
        return _empty_result(
            source_text,
            source_ref,
            active_policy,
            warning="selective_memory_candidate_shadow_disabled",
        )
    return extract_memory_candidates(source_text, source_ref=source_ref, policy=active_policy)


__all__ = [
    "CandidateExtractionPolicy",
    "CandidateExtractionResult",
    "CandidateExtractionTrace",
    "CandidateType",
    "MemoryCandidate",
    "RejectedCandidate",
    "RejectionReason",
    "SensitivityFlag",
    "SourceSpan",
    "SupersessionHint",
    "TemporalScope",
    "extract_memory_candidates",
    "is_selective_memory_candidate_shadow_enabled",
    "normalize_candidate_text",
    "run_shadow_extraction",
    "validate_source_span",
]
