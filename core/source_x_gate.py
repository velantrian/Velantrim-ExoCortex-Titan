"""Two-level source-X post-filter (RESEARCH, not Canon).

Invariant, proposed 2026-11-22:

* Level 1 — HARD BLOCK. If the user-facing response contains source-X
  figures (21,8 / 7,6 / 53,5%, comma or dot decimals, optional trailing
  zero), the answer must not be delivered. A ``BLOCKED_ATTEMPT`` record
  is written to the log. The original text is withheld; it is not
  silently truncated or redacted in place.
* Level 2 — FLAG only. If the response mentions the source-X name
  («Молниеносный бриф Меридиана») but does not contain those figures,
  the answer is delivered unchanged and a ``FLAG_REVIEW`` record is
  logged. Name-only mentions, including mentions that reject the source,
  are never an automatic block.

Official Y/Z figures (14,2 and 3,1%) and near-miss numbers (21,85;
7,61; 53,56; 121,8) must not trigger either level.

The filter is config-driven and off by default (``ENABLE_SOURCE_X_GATE``).
Pattern lists live on ``SourceXGateConfig`` so they are not buried as
ad-hoc literals in the pipeline. Logic is based on
``research/related/ict01_gate.py`` in Velantrim-Memory-Ruslan (PR #58),
with the two-level split requested after that Gate's name-only false
positives.

This module does not call any model and does not read API keys.
"""

from __future__ import annotations

import logging
import re
from dataclasses import asdict, dataclass, field
from typing import Any, Iterable

from core.feature_config import get_config

logger = logging.getLogger(__name__)

USER_FACING_BLOCK_MESSAGE = (
    "Ответ не возвращён: сработал кодовый фильтр по цифрам источника X. "
    "Сырой текст модели пользователю не показывается."
)

# Default numeric forms of source X. Trailing zero is allowed (21,80);
# longer tails (21,85) and digits glued on either side (121,8) are not.
DEFAULT_BLOCK_NUMBER_PATTERNS: tuple[tuple[str, str], ...] = (
    ("x_number_21_8", r"(?<![\d.,])21[.,]80?(?![\d.,])"),
    ("x_number_7_6", r"(?<![\d.,])7[.,]60?(?![\d.,])"),
    ("x_number_53_5", r"(?<![\d.,])53[.,]50?\s*%?(?![\d.,])"),
)

# Name of source X. «Молниеносный бриф» without «Меридиана» still flags.
DEFAULT_FLAG_NAME_PATTERNS: tuple[tuple[str, str], ...] = (
    ("x_name_flash_brief", r"молниеносн\w*\s+бриф(?:\s+меридиана)?"),
)


@dataclass(frozen=True)
class SourceXGateConfig:
    """Pattern and delivery settings for the two-level filter."""

    enabled: bool = False
    block_number_patterns: tuple[tuple[str, str], ...] = DEFAULT_BLOCK_NUMBER_PATTERNS
    flag_name_patterns: tuple[tuple[str, str], ...] = DEFAULT_FLAG_NAME_PATTERNS
    block_message: str = USER_FACING_BLOCK_MESSAGE

    @classmethod
    def from_app(cls) -> SourceXGateConfig:
        cfg = get_config().app
        return cls(enabled=bool(getattr(cfg, "enable_source_x_gate", False)))


@dataclass
class SourceXHit:
    rule: str
    level: str  # "block" | "flag"
    excerpt: str
    start: int
    end: int


@dataclass
class SourceXVerdict:
    blocked: bool
    flagged: bool
    event: str  # BLOCKED_ATTEMPT | FLAG_REVIEW | ALLOW
    hits: list[SourceXHit] = field(default_factory=list)
    notes: str = ""
    enabled: bool = True

    def to_log(self) -> dict[str, Any]:
        return {
            "event": self.event,
            "blocked": self.blocked,
            "flagged": self.flagged,
            "enabled": self.enabled,
            "hits": [asdict(h) for h in self.hits],
            "notes": self.notes,
        }


def is_source_x_gate_enabled() -> bool:
    return bool(getattr(get_config().app, "enable_source_x_gate", False))


def _compile(patterns: Iterable[tuple[str, str]]) -> list[tuple[str, re.Pattern[str]]]:
    compiled: list[tuple[str, re.Pattern[str]]] = []
    for rule, raw in patterns:
        compiled.append((rule, re.compile(raw, re.IGNORECASE)))
    return compiled


def _excerpt(text: str, start: int, end: int, radius: int = 40) -> str:
    a = max(0, start - radius)
    b = min(len(text), end + radius)
    fragment = text[a:b].replace("\n", " ").strip()
    if a > 0:
        fragment = "…" + fragment
    if b < len(text):
        fragment = fragment + "…"
    return fragment


def _collect(
    text: str,
    patterns: Iterable[tuple[str, str]],
    level: str,
) -> list[SourceXHit]:
    hits: list[SourceXHit] = []
    if not text:
        return hits
    for rule, pat in _compile(patterns):
        for match in pat.finditer(text):
            hits.append(
                SourceXHit(
                    rule=rule,
                    level=level,
                    excerpt=_excerpt(text, match.start(), match.end()),
                    start=match.start(),
                    end=match.end(),
                )
            )
    return hits


def scan_text(
    text: str,
    config: SourceXGateConfig | None = None,
) -> list[SourceXHit]:
    """Scan a string for block-level figures and flag-level name markers."""
    cfg = config or SourceXGateConfig()
    if not text:
        return []
    return _collect(text, cfg.block_number_patterns, "block") + _collect(
        text, cfg.flag_name_patterns, "flag"
    )


def apply_gate(
    text: str,
    *,
    config: SourceXGateConfig | None = None,
) -> SourceXVerdict:
    """Classify ``text`` under the two-level invariant.

    Figures take precedence: name + figures is a hard block, not a flag.
    """
    cfg = config or SourceXGateConfig.from_app()
    if not cfg.enabled:
        return SourceXVerdict(
            blocked=False,
            flagged=False,
            event="ALLOW",
            hits=[],
            notes="source_x_gate disabled",
            enabled=False,
        )

    hits = scan_text(text, cfg)
    block_hits = [h for h in hits if h.level == "block"]
    flag_hits = [h for h in hits if h.level == "flag"]

    if block_hits:
        return SourceXVerdict(
            blocked=True,
            flagged=bool(flag_hits),
            event="BLOCKED_ATTEMPT",
            hits=hits,
            notes="source-X figures in user-facing text",
            enabled=True,
        )
    if flag_hits:
        return SourceXVerdict(
            blocked=False,
            flagged=True,
            event="FLAG_REVIEW",
            hits=flag_hits,
            notes="source-X name without figures; delivered, flagged for review",
            enabled=True,
        )
    return SourceXVerdict(
        blocked=False,
        flagged=False,
        event="ALLOW",
        hits=[],
        notes="no source-X figures or name",
        enabled=True,
    )


def user_facing_payload(
    raw_text: str, verdict: SourceXVerdict, config: SourceXGateConfig | None = None
) -> dict[str, Any]:
    """What may be shown to the user.

    On BLOCK the raw answer is withheld and the stub must not leak figures.
    On FLAG or ALLOW the original text is returned unchanged.
    """
    cfg = config or SourceXGateConfig.from_app()
    if verdict.blocked:
        return {
            "delivered": False,
            "status": "BLOCKED_ATTEMPT",
            "message": cfg.block_message,
            "rules": [h.rule for h in verdict.hits if h.level == "block"],
        }
    if verdict.flagged:
        return {
            "delivered": True,
            "status": "FLAG_REVIEW",
            "message": raw_text,
            "rules": [h.rule for h in verdict.hits if h.level == "flag"],
        }
    return {
        "delivered": True,
        "status": "ALLOW",
        "message": raw_text,
    }


def blocked_attempt_log(verdict: SourceXVerdict) -> dict[str, Any]:
    """Structured log record, including excerpts for audit."""
    return verdict.to_log()


def apply_to_pipeline_result(
    result: dict[str, Any],
    *,
    config: SourceXGateConfig | None = None,
) -> dict[str, Any]:
    """Annotate a pipeline result and, on BLOCK, replace the answer.

    The original answer is never silently truncated. When the gate is
    disabled the result is returned unchanged.
    """
    cfg = config or SourceXGateConfig.from_app()
    if not cfg.enabled:
        return result

    raw = result.get("answer") or ""
    if not isinstance(raw, str):
        raw = str(raw)
    verdict = apply_gate(raw, config=cfg)
    payload = user_facing_payload(raw, verdict, config=cfg)
    log_record = blocked_attempt_log(verdict)

    if verdict.blocked:
        logger.warning("SOURCE_X_GATE BLOCKED_ATTEMPT: %s", log_record)
        result["answer"] = payload["message"]
        result["source_x_gate_blocked"] = True
    elif verdict.flagged:
        logger.info("SOURCE_X_GATE FLAG_REVIEW: %s", log_record)
        result["source_x_gate_flagged"] = True
    else:
        logger.debug("SOURCE_X_GATE ALLOW: %s", log_record.get("notes"))

    result["source_x_gate"] = {
        **log_record,
        "status": payload["status"],
        "delivered": payload["delivered"],
    }
    return result


__all__ = [
    "DEFAULT_BLOCK_NUMBER_PATTERNS",
    "DEFAULT_FLAG_NAME_PATTERNS",
    "SourceXGateConfig",
    "SourceXHit",
    "SourceXVerdict",
    "USER_FACING_BLOCK_MESSAGE",
    "apply_gate",
    "apply_to_pipeline_result",
    "blocked_attempt_log",
    "is_source_x_gate_enabled",
    "scan_text",
    "user_facing_payload",
]
