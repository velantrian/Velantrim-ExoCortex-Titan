"""
OutputFaithfulnessChecker F6.5 — пост-проверка ответа (Titan HYPERIA-6).

Extractive mode: TF-IDF overlap, 0 токенов. Только Slow Path / аудит.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any

from core.feature_config import get_config

logger = logging.getLogger(__name__)

_TOKEN_RE = re.compile(r"\b\w{3,}\b", re.UNICODE)


@dataclass
class FaithfulnessResult:
    score: float
    grounded_claims: int
    total_claims: int
    unsupported: list[str] = field(default_factory=list)
    mode: str = "extractive"

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": round(self.score, 4),
            "grounded_claims": self.grounded_claims,
            "total_claims": self.total_claims,
            "unsupported": self.unsupported[:5],
            "mode": self.mode,
        }


def is_output_faithfulness_enabled() -> bool:
    return get_config().app.enable_output_faithfulness


def _tokenize(text: str) -> set[str]:
    return set(_TOKEN_RE.findall((text or "").lower()))


def _fact_text(fact: dict[str, Any]) -> str:
    return (fact.get("claim") or fact.get("content") or fact.get("text") or "").strip()


class OutputFaithfulnessChecker:
    """Проверка соответствия ответа source_facts (extractive по умолчанию)."""

    def check(
        self,
        response: str,
        source_facts: list[dict[str, Any]],
        *,
        overlap_threshold: float = 0.3,
    ) -> FaithfulnessResult:
        if not source_facts:
            return FaithfulnessResult(
                score=0.5,
                grounded_claims=0,
                total_claims=0,
                unsupported=[],
                mode="no_sources",
            )
        return self._extractive_check(response, source_facts, overlap_threshold)

    def _extractive_check(
        self,
        response: str,
        source_facts: list[dict[str, Any]],
        overlap_threshold: float,
    ) -> FaithfulnessResult:
        claims = [c.strip() for c in response.split(". ") if c.strip()]
        grounded = 0
        unsupported: list[str] = []

        for claim in claims:
            claim_tokens = _tokenize(claim)
            if not claim_tokens:
                continue
            matched = False
            for fact in source_facts:
                fact_tokens = _tokenize(_fact_text(fact))
                if not fact_tokens:
                    continue
                overlap = len(claim_tokens & fact_tokens) / max(1, len(claim_tokens))
                if overlap > overlap_threshold:
                    matched = True
                    break
            if matched:
                grounded += 1
            else:
                unsupported.append(claim[:100])

        total = max(1, len([c for c in claims if c.strip()]))
        score = grounded / total
        return FaithfulnessResult(
            score=score,
            grounded_claims=grounded,
            total_claims=total,
            unsupported=unsupported,
            mode="extractive",
        )


_checker: OutputFaithfulnessChecker | None = None


def get_faithfulness_checker() -> OutputFaithfulnessChecker:
    global _checker
    if _checker is None:
        _checker = OutputFaithfulnessChecker()
    return _checker


def check_response_faithfulness(
    response: str,
    source_facts: list[dict[str, Any]],
) -> FaithfulnessResult | None:
    if not is_output_faithfulness_enabled():
        return None
    return get_faithfulness_checker().check(response, source_facts)


__all__ = [
    "FaithfulnessResult",
    "OutputFaithfulnessChecker",
    "check_response_faithfulness",
    "get_faithfulness_checker",
    "is_output_faithfulness_enabled",
]


# ─── V8.7 Titan: GCR Programmable Filter ────────────────────────────────────

import re as _re
from dataclasses import dataclass as _dataclass, field as _field
from typing import List as _List, Dict as _Dict, Any as _Any

@_dataclass
class GCRResult:
    """Результат Graph-Constrained Response фильтра."""
    claim: str
    verdict: str                      # grounded | hypothesis | unsupported
    overlap_score: float
    matched_fact_ids: _List[str] = _field(default_factory=list)
    reason: str = ""


def apply_gcr_filter(
    response: str,
    source_facts: _List[_Dict[_Any, _Any]],
    *,
    hypothesis_threshold: float = 0.20,
    grounded_threshold: float = 0.45,
) -> str:
    """Программируемый GCR-фильтр: маркирует unsupported claims."""
    if not response or not response.strip():
        return response
    if not source_facts:
        return f"[HYPOTHESIS: нет верифицированных фактов] {response}"
    claims = [c.strip() for c in response.split(". ") if c.strip()]
    filtered = []
    tok_re = _re.compile(r"\b\w{3,}\b", _re.UNICODE)
    for claim in claims:
        ct = set(tok_re.findall(claim.lower()))
        if not ct:
            filtered.append(claim)
            continue
        best = 0.0
        for fact in source_facts:
            ft = set(tok_re.findall((fact.get("claim") or fact.get("content") or "").lower()))
            if not ft:
                continue
            o = len(ct & ft) / max(1, len(ct))
            if o > best:
                best = o
        if best >= grounded_threshold:
            filtered.append(claim)
        elif best >= hypothesis_threshold:
            filtered.append(f"[HYPOTHESIS: overlap={best:.2f}] {claim}")
        else:
            filtered.append(f"[UNSUPPORTED: нет в графе] {claim}")
    result = ". ".join(filtered)
    if not result.endswith("."):
        result += "."
    return result


def gcr_annotate_response(
    response: str,
    source_facts: _List[_Dict[_Any, _Any]],
) -> _Dict[_Any, _Any]:
    """Полный GCR-анализ ответа."""
    if not response or not source_facts:
        return {"filtered_response": response or "", "total_claims": 0, "grounded_count": 0}
    claims = [c.strip() for c in response.split(". ") if c.strip()]
    tok_re = _re.compile(r"\b\w{3,}\b", _re.UNICODE)
    grounded = 0
    hypo = 0
    for claim in claims:
        ct = set(tok_re.findall(claim.lower()))
        if not ct:
            grounded += 1
            continue
        best = 0.0
        for fact in source_facts:
            ft = set(tok_re.findall((fact.get("claim") or "").lower()))
            if not ft:
                continue
            o = len(ct & ft) / max(1, len(ct))
            if o > best:
                best = o
        if best >= 0.45:
            grounded += 1
        elif best >= 0.20:
            hypo += 1
    filtered = apply_gcr_filter(response, source_facts)
    return {
        "filtered_response": filtered,
        "total_claims": len(claims),
        "grounded_count": grounded,
        "hypothesis_count": hypo,
        "unsupported_count": len(claims) - grounded - hypo,
        "faithfulness_score": round(grounded / max(1, len(claims)), 3),
    }
