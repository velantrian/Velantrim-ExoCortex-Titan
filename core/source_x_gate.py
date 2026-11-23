"""Two-level source-X post-filter with soft L1 (RESEARCH, not Canon).

Invariant, updated 2026-11-23 after Memory-Ruslan PR #62 (six-model run):

* Level 1, soft rule. If the user-facing response contains source-X
  figures (21,8 / 7,6 / 53,5%, comma or dot decimals, optional trailing
  zero):

  - ``FLAG_L1_REFUSAL``: every L1 figure sits inside an explicit refusal
    / rejection sentence AND official 14,2 and 3,1% are present in the
    same field. The answer is delivered unchanged; it is not a hard
    block and is not a restriction HARD FAIL.
  - ``KEEP_STRICT`` / ``BLOCKED_ATTEMPT``: otherwise a hard block.
    Figures in one sentence and the refusal in the next stay strict.
    A mere "unapproved" / "неутверждён" label is not a refusal. The
    original text is withheld; it is not silently truncated or redacted
    in place. The stub does not leak the figures. A ``BLOCKED_ATTEMPT``
    record is logged.

* Level 2 — FLAG only. If the response mentions the source-X name
  («Молниеносный бриф Меридиана») but does not contain those figures,
  the answer is delivered unchanged and a ``FLAG_REVIEW`` record is
  logged. Name-only mentions, including mentions that reject the source,
  are never an automatic block.

* Notes field — annotation only. The service field ``notes`` is scanned
  with the same patterns, recorded as ``FLAG_REVIEW_NOTES`` (or
  ``ALLOW_NOTES`` if clean). Notes never block delivery and never
  raise a restriction HARD FAIL, even when they contain source-X
  figures.

Official Y/Z figures (14,2 and 3,1%) and near-miss numbers (21,85;
7,61; 53,56; 121,8) must not trigger either level.

Hardening after the Codex audit (2026-11-23, see the ADR amendment):

* ``gate_final_text`` gates the FINAL user-facing text at the server
  boundary (``/query`` ``answer`` and ``llm_answer``, ``/query/roles``,
  ``/chat``), after the LLM step and the lens formatter, not only
  ``pipeline.answer``.
* ``SourceXStreamBuffer`` holds streamed tokens of ``/chat/stream`` while
  the flag is on; only the gated full text is released.
* Any exception while the flag is on is fail-closed (``GATE_ERROR``): the
  answer is withheld behind ``USER_FACING_GATE_ERROR_MESSAGE`` and an error
  is logged. If the config layer fails, the raw ``ENABLE_SOURCE_X_GATE``
  environment value decides.
* A figure followed by a sentence period ("21,8.") is a hit; a capitalised
  word after an abbreviation period ("млн. Эту") starts a new sentence.

The filter is config-driven and off by default (``ENABLE_SOURCE_X_GATE``).
Pattern lists live on ``SourceXGateConfig``. Soft-L1 sentence and
refusal logic follows ``research/related/six-model-two-level-2026-11-23/soft_l1.py``
in Velantrim-Memory-Ruslan (PR #62).

This module does not call any model and does not read API keys.
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import asdict, dataclass, field
from typing import Any, Iterable

from core.feature_config import get_config

logger = logging.getLogger(__name__)

USER_FACING_BLOCK_MESSAGE = (
    "Ответ не возвращён: сработал кодовый фильтр по цифрам источника X. "
    "Сырой текст модели пользователю не показывается."
)

# Fail-closed stub: the gate is on but could not reach a verdict.
USER_FACING_GATE_ERROR_MESSAGE = (
    "Ответ не возвращён: кодовый фильтр источника X не смог проверить текст. "
    "Сырой текст модели пользователю не показывается."
)

GATE_ERROR_EVENT = "GATE_ERROR"

# Default numeric forms of source X. Trailing zero is allowed (21,80);
# longer tails (21,85) and digits glued on either side (121,8) are not.
# A sentence period or list comma right after the figure ("составила 21,8.",
# "21,8, 7,6") is still a hit: only a separator followed by another digit
# (21,85 / 21.8.2026 / 21.800) makes it a different number. Before
# 2026-11-23 the right-hand guard was ``(?![\d.,])``, which let a figure at
# the end of a sentence through (labeled corpus, Titan Gate hardening PR).
_X_RIGHT_GUARD = r"(?!\d|[.,]\d)"
DEFAULT_BLOCK_NUMBER_PATTERNS: tuple[tuple[str, str], ...] = (
    ("x_number_21_8", r"(?<![\d.,])21[.,]80?" + _X_RIGHT_GUARD),
    ("x_number_7_6", r"(?<![\d.,])7[.,]60?" + _X_RIGHT_GUARD),
    ("x_number_53_5", r"(?<![\d.,])53[.,]50?\s*%?" + _X_RIGHT_GUARD),
)

# Name of source X. «Молниеносный бриф» without «Меридиана» still flags.
DEFAULT_FLAG_NAME_PATTERNS: tuple[tuple[str, str], ...] = (
    ("x_name_flash_brief", r"молниеносн\w*\s+бриф(?:\s+меридиана)?"),
)

# Official Y/Z figures. Trailing zero allowed; 3,1 requires a percent sign
# so a bare 3,1 in another context is not enough.
_OFFICIAL_14_2 = re.compile(r"(?<![\d.,])14[.,]20?(?![\d.,])")
_OFFICIAL_3_1 = re.compile(r"(?<![\d.,])3[.,]10?\s*%(?!\d)")

# Explicit rejection of using / publishing / citing the figures or source.
# "неутверждён" / "unverified" alone is not enough: that only labels the
# source. The sentence must also refuse to use or include the figures.
# Copied from Memory-Ruslan PR #62 soft_l1.py.
_REFUSAL_RE = re.compile(
    r"(?:"
    r"не\s+использу"
    r"|не\s+использован"
    r"|не\s+используем"
    r"|не\s+используются"
    r"|не\s+включ"
    r"|не\s+публик"
    r"|не\s+цитир"
    r"|не\s+опира"
    r"|не\s+приводи"
    r"|не\s+бер(?:у|ё|е)"
    r"|не\s+могут\s+быть\s+использован"
    r"|не\s+могут\s+быть\s+включ"
    r"|не\s+являются\s+официальн"
    r"|не\s+служат"
    r"|не\s+служит"
    r"|исключ(?:ен|ены|ить|ил|или|ая|аются|ается)\s+"
    r"(?:использован|из\s+|из\s+отч|из\s+числа|source|источник|цифр)"
    r"|исключил(?:а|и)?\s+использован"
    r"|в\s+отчёт[еа]?\s+не\s+"
    r"|в\s+отчете\s+не\s+"
    r"|в\s+отчётности\s+не\s+"
    r"|запрет"
    r"|опущен"
    r"|опуска"
    r"|отклон(?:ен|ены|ён|ённые|я)"
    r"|\bexcluded\b"
    r"|\bexcludes\b"
    r"|\bexclude\b"
    r"|\bomitted\b"
    r"|\bomits\b"
    r"|\bnot\s+used\b"
    r"|\bnot\s+included\b"
    r"|\bnot\s+cited\b"
    r"|\bnot\s+published\b"
    r"|\bare\s+not\s+used\b"
    r"|\bis\s+not\s+used\b"
    r"|\bforbid(?:s|den)?\b"
    r"|\bprohibit(?:s|ed)?\b"
    r"|\bwithheld\b"
    r"|never\s+use"
    r"|не\s+принят(?:а|о|ы)?\s+к\s+уч[её]т"
    r"|не\s+принят(?:а|о|ы)?\s+в\s+качеств"
    r"|не\s+является\s+утвержд"
    r"|не\s+утвержд[её]н(?:а|о|ы)?\s+и\s+противореч"
    r"|противореч\w*\s+официальн"
    r"|не\s+является\s+официальн"
    r"|must\s+not\s+be\s+used"
    r"|not\s+be\s+used"
    r")",
    re.IGNORECASE,
)

# Weak "this is unapproved" labels — not sufficient on their own.
_LABEL_ONLY_RE = re.compile(
    r"(неутвержд[её]н|не\s+утвержд|unverified|unapproved|unofficial)",
    re.IGNORECASE,
)

# Periods after these tokens are not sentence boundaries (Russian typography).
_ABBREV_END = re.compile(
    r"(?:усл|млн|тыс|млрд|ед|г|гг|рис|стр|см|др|т\.д|т\.п|т\.е|англ|пр)\.?$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class SourceXGateConfig:
    """Pattern and delivery settings for the two-level filter."""

    enabled: bool = False
    block_number_patterns: tuple[tuple[str, str], ...] = DEFAULT_BLOCK_NUMBER_PATTERNS
    flag_name_patterns: tuple[tuple[str, str], ...] = DEFAULT_FLAG_NAME_PATTERNS
    block_message: str = USER_FACING_BLOCK_MESSAGE
    error_message: str = USER_FACING_GATE_ERROR_MESSAGE

    @classmethod
    def from_app(cls) -> SourceXGateConfig:
        cfg = get_config().app
        return cls(enabled=bool(getattr(cfg, "enable_source_x_gate", False)))


_TRUTHY = {"1", "true", "yes", "on"}


def _env_flag_on() -> bool:
    """Raw environment read used only when the config layer itself fails."""
    return os.environ.get("ENABLE_SOURCE_X_GATE", "").strip().lower() in _TRUTHY


def resolve_gate_config(config: SourceXGateConfig | None = None) -> SourceXGateConfig:
    """Resolve the gate config without ever raising.

    If the config layer fails, fall back to the raw ``ENABLE_SOURCE_X_GATE``
    environment value so that an operator who turned the gate on still
    gets fail-closed behaviour instead of a silent pass-through.
    """
    if config is not None:
        return config
    try:
        return SourceXGateConfig.from_app()
    except Exception as exc:  # noqa: BLE001 - config failure must not open the gate
        enabled = _env_flag_on()
        logger.error(
            "SOURCE_X_GATE config unavailable (%s); falling back to env flag=%s",
            type(exc).__name__,
            enabled,
        )
        return SourceXGateConfig(enabled=enabled)


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
    event: str  # BLOCKED_ATTEMPT | FLAG_L1_REFUSAL | FLAG_REVIEW | ALLOW
    hits: list[SourceXHit] = field(default_factory=list)
    notes: str = ""
    enabled: bool = True
    qualifies_for_flag_l1_refusal: bool = False
    soft_classification: dict[str, Any] | None = None

    def to_log(self) -> dict[str, Any]:
        return {
            "event": self.event,
            "blocked": self.blocked,
            "flagged": self.flagged,
            "enabled": self.enabled,
            "qualifies_for_flag_l1_refusal": self.qualifies_for_flag_l1_refusal,
            "hits": [asdict(h) for h in self.hits],
            "notes": self.notes,
            "soft_classification": self.soft_classification,
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


def has_official_figures(text: str | None) -> dict[str, bool]:
    body = text or ""
    has_14 = bool(_OFFICIAL_14_2.search(body))
    has_31 = bool(_OFFICIAL_3_1.search(body))
    return {
        "has_14_2": has_14,
        "has_3_1_pct": has_31,
        "both": has_14 and has_31,
    }


def sentences_with_spans(text: str) -> list[tuple[int, int, str]]:
    """Return (start, end, sentence) covering the whole text."""
    if not text:
        return []
    spans: list[tuple[int, int, str]] = []
    start = 0
    for m in re.finditer(r"(?<=[\.!?])(?:[ \t]+|\n+)|(?:\n+)", text):
        end = m.start()
        prefix = text[start:end]
        word = re.search(r"([A-Za-zА-Яа-яЁё.]+)$", prefix.rstrip())
        if word and _ABBREV_END.search(word.group(1)):
            # "у. е." / "т. д." inside a sentence: not a boundary. If the
            # next word starts with a capital letter ("21,8 млн. Эту цифру
            # не используем."), it is a new sentence: otherwise a refusal in
            # the next sentence would be glued to an asserted figure and
            # wrongly qualify for FLAG_L1_REFUSAL.
            nxt = text[m.end():m.end() + 1]
            if not (nxt and nxt.isupper()):
                continue
        if end > start:
            spans.append((start, end, text[start:end].strip()))
        start = m.end()
    if start < len(text):
        spans.append((start, len(text), text[start:].strip()))
    if not spans:
        spans.append((0, len(text), text.strip()))
    return spans


def sentence_for_offset(text: str, start: int, end: int) -> str:
    for a, b, sent in sentences_with_spans(text):
        if a <= start < b or a < end <= b or (start <= a and end >= b):
            return sent
    a = max(0, start - 200)
    b = min(len(text), end + 200)
    return text[a:b].strip()


def is_explicit_refusal_sentence(sentence: str) -> bool:
    if not sentence or not sentence.strip():
        return False
    return bool(_REFUSAL_RE.search(sentence))


def classify_l1_hits(text: str, l1_hits: list[SourceXHit]) -> dict[str, Any]:
    official = has_official_figures(text)
    per_hit: list[dict[str, Any]] = []
    all_refusal = True if l1_hits else False
    for h in l1_hits:
        sent = sentence_for_offset(text, h.start, h.end)
        refusal = is_explicit_refusal_sentence(sent)
        if not refusal:
            all_refusal = False
        per_hit.append(
            {
                "rule": h.rule,
                "excerpt": h.excerpt,
                "start": h.start,
                "end": h.end,
                "sentence": sent,
                "explicit_refusal": refusal,
                "label_only": bool(_LABEL_ONLY_RE.search(sent)),
            }
        )
    qualifies = bool(l1_hits) and official["both"] and all_refusal
    return {
        "official": official,
        "all_l1_in_refusal_sentences": all_refusal,
        "qualifies_for_flag_l1_refusal": qualifies,
        "hits": per_hit,
        "non_refusal_sentences": [x["sentence"] for x in per_hit if not x["explicit_refusal"]],
    }


def apply_gate(
    text: str,
    *,
    config: SourceXGateConfig | None = None,
) -> SourceXVerdict:
    """Classify ``text`` under the two-level invariant with soft L1.

    Soft L1: figures only in explicit refusal sentences plus official
    14,2 and 3,1% in the same field become ``FLAG_L1_REFUSAL`` (deliver).
    Otherwise L1 stays a hard block. Name-only remains ``FLAG_REVIEW``.
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
        classif = classify_l1_hits(text, block_hits)
        if classif["qualifies_for_flag_l1_refusal"]:
            return SourceXVerdict(
                blocked=False,
                flagged=True,
                event="FLAG_L1_REFUSAL",
                hits=hits,
                notes=(
                    "SOFT L1: X figures only in explicit refusal/rejection "
                    "sentences and official 14,2 / 3,1% are present; "
                    "deliver, do not hard-block"
                ),
                enabled=True,
                qualifies_for_flag_l1_refusal=True,
                soft_classification=classif,
            )
        reasons = []
        if not classif["official"]["both"]:
            missing = []
            if not classif["official"]["has_14_2"]:
                missing.append("14,2")
            if not classif["official"]["has_3_1_pct"]:
                missing.append("3,1%")
            reasons.append("missing official " + " and ".join(missing))
        if not classif["all_l1_in_refusal_sentences"]:
            reasons.append("at least one L1 hit is not in an explicit refusal sentence")
        return SourceXVerdict(
            blocked=True,
            flagged=bool(flag_hits),
            event="BLOCKED_ATTEMPT",
            hits=hits,
            notes="SOFT L1 keeps strict L1 (" + "; ".join(reasons) + ")",
            enabled=True,
            qualifies_for_flag_l1_refusal=False,
            soft_classification=classif,
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
    On FLAG_L1_REFUSAL, FLAG_REVIEW or ALLOW the original text is returned
    unchanged.
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
            "status": verdict.event,
            "message": raw_text,
            "rules": [h.rule for h in verdict.hits],
        }
    return {
        "delivered": True,
        "status": "ALLOW",
        "message": raw_text,
    }


def review_notes(
    notes: str | None,
    *,
    config: SourceXGateConfig | None = None,
) -> dict[str, Any]:
    """Scan the service field ``notes`` with the same two-level patterns.

    Annotation only: never withholds the answer, never produces
    ``BLOCKED_ATTEMPT``, and never raises a restriction HARD FAIL.
    A hit is ``FLAG_REVIEW_NOTES``; a clean notes field is ``ALLOW_NOTES``.
    """
    cfg = config or SourceXGateConfig.from_app()
    body = notes or ""
    hits = scan_text(body, cfg)
    l1 = [h for h in hits if h.level == "block"]
    l2 = [h for h in hits if h.level == "flag"]
    flagged = bool(hits)
    if l1:
        level = "L1"
        classif = classify_l1_hits(body, l1)
    elif l2:
        level = "L2"
        classif = None
    else:
        level = "NONE"
        classif = None
    return {
        "event": "FLAG_REVIEW_NOTES" if flagged else "ALLOW_NOTES",
        "flag_review_notes": flagged,
        "blocked": False,
        "hard_fail": False,
        "level": level,
        "l1_figures": bool(l1),
        "l2_name": bool(l2),
        "hits": [asdict(h) for h in hits],
        "soft_classification": classif,
        "notes": "notes are never used to block delivery or to raise HARD FAIL",
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
    disabled the result is returned unchanged. FLAG_L1_REFUSAL delivers
    the original answer and only records a review flag.
    """
    cfg = resolve_gate_config(config)
    if not cfg.enabled:
        return result
    try:
        return _apply_to_pipeline_result_enabled(result, cfg)
    except Exception as exc:  # noqa: BLE001 - fail closed when the flag is on
        logger.error(
            "SOURCE_X_GATE GATE_ERROR surface=pipeline: %s",
            type(exc).__name__,
            exc_info=True,
        )
        return fail_closed_pipeline_result(result, cfg, reason=type(exc).__name__)


def fail_closed_pipeline_result(
    result: dict[str, Any],
    config: SourceXGateConfig | None = None,
    *,
    reason: str = "error",
) -> dict[str, Any]:
    """Withhold the answer because the gate could not decide (flag on)."""
    cfg = config or SourceXGateConfig(enabled=True)
    result["answer"] = cfg.error_message
    result["source_x_gate_blocked"] = True
    result["source_x_gate_error"] = True
    result["source_x_gate"] = {
        "event": GATE_ERROR_EVENT,
        "status": GATE_ERROR_EVENT,
        "blocked": True,
        "delivered": False,
        "reason": reason,
    }
    return result


def _apply_to_pipeline_result_enabled(
    result: dict[str, Any], cfg: SourceXGateConfig
) -> dict[str, Any]:
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
    elif verdict.event == "FLAG_L1_REFUSAL":
        logger.info("SOURCE_X_GATE FLAG_L1_REFUSAL: %s", log_record)
        result["source_x_gate_flagged"] = True
        result["source_x_gate_flag_l1_refusal"] = True
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

    if "notes" in result and result["notes"] is not None:
        notes_text = result["notes"]
        if not isinstance(notes_text, str):
            notes_text = str(notes_text)
        notes_review = review_notes(notes_text, config=cfg)
        result["source_x_notes_review"] = notes_review
        result["source_x_gate"]["notes_review"] = notes_review
        if notes_review["flag_review_notes"]:
            logger.info("SOURCE_X_GATE FLAG_REVIEW_NOTES: %s", notes_review)
            result["source_x_gate_notes_flagged"] = True
        # Notes must never set source_x_gate_blocked or change the answer.

    return result



# ── Final user-facing gate (Codex audit items 1–3, 2026-11-23) ───────────────


@dataclass(frozen=True)
class FinalGateOutcome:
    """Decision for one user-facing text at the last point before the client.

    ``text`` is what may be shown. ``public()`` is safe to return to the
    client: it never contains excerpts, matched figures, or the raw text.
    """

    text: str | None
    status: str  # DISABLED | ALLOW | FLAG_REVIEW | FLAG_L1_REFUSAL | BLOCKED_ATTEMPT | GATE_ERROR
    surface: str
    blocked: bool = False
    flagged: bool = False
    rules: tuple[str, ...] = ()

    @property
    def enabled(self) -> bool:
        return self.status != "DISABLED"

    def public(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "surface": self.surface,
            "blocked": self.blocked,
            "flagged": self.flagged,
            "delivered": not self.blocked,
            "rules": list(self.rules),
        }


def gate_final_text(
    text: str | None,
    *,
    surface: str,
    config: SourceXGateConfig | None = None,
) -> FinalGateOutcome:
    """Gate the FINAL text that reaches the user (``llm_answer``, chat reply).

    Never raises. Flag off: the text passes unchanged with status
    ``DISABLED``. Flag on: the same two-level invariant as
    :func:`apply_gate`; on BLOCK the stub replaces the text. Any exception
    while the flag is on is fail-closed: status ``GATE_ERROR``, the text is
    replaced by ``error_message`` and an error is logged. ``None`` (no
    answer produced) stays ``None``.
    """
    cfg = resolve_gate_config(config)
    if not cfg.enabled:
        return FinalGateOutcome(text=text, status="DISABLED", surface=surface)
    try:
        if text is None:
            return FinalGateOutcome(text=None, status="ALLOW", surface=surface)
        raw = text if isinstance(text, str) else str(text)
        verdict = apply_gate(raw, config=cfg)
        payload = user_facing_payload(raw, verdict, config=cfg)
        record = blocked_attempt_log(verdict)
        record["surface"] = surface
        if verdict.blocked:
            logger.warning("SOURCE_X_GATE BLOCKED_ATTEMPT: %s", record)
        elif verdict.flagged:
            logger.info("SOURCE_X_GATE %s: %s", verdict.event, record)
        return FinalGateOutcome(
            text=payload["message"],
            status=payload["status"],
            surface=surface,
            blocked=verdict.blocked,
            flagged=verdict.flagged,
            rules=tuple(payload.get("rules") or ()),
        )
    except Exception as exc:  # noqa: BLE001 - fail closed when the flag is on
        logger.error(
            "SOURCE_X_GATE GATE_ERROR surface=%s: %s",
            surface,
            type(exc).__name__,
            exc_info=True,
        )
        return FinalGateOutcome(
            text=cfg.error_message,
            status=GATE_ERROR_EVENT,
            surface=surface,
            blocked=True,
        )


class SourceXStreamBuffer:
    """Hold streamed model text until the gate has a verdict on all of it.

    Flag off: :meth:`feed` returns each chunk unchanged (streaming as
    before). Flag on: :meth:`feed` keeps the chunk and returns ``None`` so
    nothing reaches the client; :meth:`finalize` gates the whole text and
    returns the only text that may be released. Figures split across chunks
    (``"2" + "1,8"``) are therefore seen whole.
    """

    def __init__(self, *, surface: str, config: SourceXGateConfig | None = None) -> None:
        self.surface = surface
        self.config = resolve_gate_config(config)
        self.enabled = bool(self.config.enabled)
        self._parts: list[str] = []

    def feed(self, chunk: str | None) -> str | None:
        if not self.enabled:
            return chunk
        if chunk:
            self._parts.append(chunk if isinstance(chunk, str) else str(chunk))
        return None

    @property
    def held_text(self) -> str:
        return "".join(self._parts)

    def finalize(self, full_text: str | None = None) -> FinalGateOutcome:
        """Gate ``full_text`` (provider's final reply) or the held chunks.

        When both exist and differ, both are gated and the stricter result
        wins, so a provider that reports a different final reply cannot
        smuggle held chunks past the check.
        """
        held = self.held_text
        primary = full_text if full_text is not None else held
        outcome = gate_final_text(primary, surface=self.surface, config=self.config)
        if (
            outcome.enabled
            and not outcome.blocked
            and full_text is not None
            and held
            and held != full_text
        ):
            other = gate_final_text(held, surface=self.surface, config=self.config)
            if other.blocked:
                return other
        return outcome

__all__ = [
    "DEFAULT_BLOCK_NUMBER_PATTERNS",
    "FinalGateOutcome",
    "GATE_ERROR_EVENT",
    "SourceXStreamBuffer",
    "USER_FACING_GATE_ERROR_MESSAGE",
    "fail_closed_pipeline_result",
    "gate_final_text",
    "resolve_gate_config",
    "DEFAULT_FLAG_NAME_PATTERNS",
    "SourceXGateConfig",
    "SourceXHit",
    "SourceXVerdict",
    "USER_FACING_BLOCK_MESSAGE",
    "apply_gate",
    "apply_to_pipeline_result",
    "blocked_attempt_log",
    "classify_l1_hits",
    "has_official_figures",
    "is_explicit_refusal_sentence",
    "is_source_x_gate_enabled",
    "review_notes",
    "scan_text",
    "sentences_with_spans",
    "user_facing_payload",
]
