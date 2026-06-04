"""
Целостность фактов: checksum (anti-reconsolidation) и episode_hash (dedup).

Спринт 1 — из спеки CognitiveFact (`Documents/system`).
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

_PROTECTED_STATES = frozenset({"Validated", "Supported", "ImmutableCore"})

_WS_RE = re.compile(r"\s+")
_PUNCT_RE = re.compile(r"[^\w\s\u0400-\u04ff@-]", re.UNICODE)
_LEADING_FILLER_RE = re.compile(r"^(?:что|that)\s+", re.I)


def compute_content_checksum(
    claim: str,
    source: str,
    confidence: float,
    epistemic_state: str,
) -> str:
    """SHA256 от канонического содержимого факта (первые 32 hex)."""
    conf = round(float(confidence), 6)
    payload = "|".join(
        [
            _WS_RE.sub(" ", (claim or "").strip()),
            (source or "unknown").strip(),
            f"{conf:.6f}",
            (epistemic_state or "Observed").strip(),
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


def normalize_claim_for_dedup(claim: str) -> str:
    """Канонический текст факта для сравнения (без источника и регистра)."""
    s = _WS_RE.sub(" ", (claim or "").strip().lower())
    s = _LEADING_FILLER_RE.sub("", s)
    s = _PUNCT_RE.sub("", s)
    return _WS_RE.sub(" ", s).strip()


def compute_claim_dedup_key(claim: str) -> str:
    """Ключ дедупликации только по содержанию claim (любой source)."""
    norm = normalize_claim_for_dedup(claim)
    if not norm:
        return ""
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()[:16]


def compute_episode_hash(claim: str, source: str) -> str:
    """Хеш эпизода для pattern separation (дедуп ingest)."""
    norm = normalize_claim_for_dedup(claim) or _WS_RE.sub(" ", (claim or "").strip().lower())
    src = (source or "unknown").strip().lower()
    return hashlib.sha256(f"{src}|{norm}".encode()).hexdigest()[:16]


def attach_integrity_metadata(
    metadata: dict[str, Any] | None,
    *,
    claim: str,
    source: str,
    confidence: float,
    epistemic_state: str,
) -> dict[str, Any]:
    """Добавить checksum и episode_hash в metadata."""
    meta = dict(metadata or {})
    meta["content_checksum"] = compute_content_checksum(
        claim, source, confidence, epistemic_state
    )
    meta["episode_hash"] = compute_episode_hash(claim, source)
    meta["claim_dedup_key"] = compute_claim_dedup_key(claim)
    return meta


def verify_stored_checksum(fact: dict[str, Any]) -> bool:
    """Проверить, что metadata.content_checksum совпадает с полями факта."""
    meta = fact.get("metadata") or {}
    if isinstance(meta, str):
        try:
            meta = json.loads(meta)
        except json.JSONDecodeError:
            return False
    expected = meta.get("content_checksum")
    if not expected:
        return True
    actual = compute_content_checksum(
        fact.get("claim", ""),
        fact.get("source", "unknown"),
        float(fact.get("confidence", 0.5)),
        fact.get("epistemic_state", "Observed"),
    )
    return expected == actual


def assert_claim_update_allowed(existing: dict[str, Any], new_claim: str) -> None:
    """
    Для Validated/Supported: запрет тихой смены claim без transition_esm.
    Дополняет TASK-02 drift protection в memory.store_fact.
    """
    state = existing.get("epistemic_state", "Observed")
    if state not in _PROTECTED_STATES:
        return
    old_claim = (existing.get("claim") or "").strip()
    new_claim_s = (new_claim or "").strip()
    if old_claim != new_claim_s:
        # TASK-02: смену claim у Validated/Supported обрабатывает drift protection в store_fact
        return
    if not verify_stored_checksum(existing):
        raise ValueError(
            f"fact_integrity: checksum не совпадает у '{existing.get('fact_id')}' "
            "— возможная реконсолидация"
        )


__all__ = [
    "assert_claim_update_allowed",
    "attach_integrity_metadata",
    "compute_claim_dedup_key",
    "compute_content_checksum",
    "compute_episode_hash",
    "normalize_claim_for_dedup",
    "verify_stored_checksum",
]
