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
    # Streaming resource bounds (round 2, P1-02). Only used while enabled.
    stream_max_bytes: int = 262_144
    stream_deadline_seconds: float = 180.0
    stream_keepalive_seconds: float = 10.0

    @classmethod
    def from_app(cls) -> SourceXGateConfig:
        cfg = get_config().app
        return cls(
            enabled=bool(getattr(cfg, "enable_source_x_gate", False)),
            stream_max_bytes=_env_int("SOURCE_X_GATE_STREAM_MAX_BYTES", 262_144, 1),
            stream_deadline_seconds=_env_float("SOURCE_X_GATE_STREAM_DEADLINE_S", 180.0, 0.01),
            stream_keepalive_seconds=_env_float("SOURCE_X_GATE_STREAM_KEEPALIVE_S", 10.0, 0.01),
        )


def _env_int(name: str, default: int, minimum: int) -> int:
    try:
        return max(minimum, int(os.environ.get(name, "") or default))
    except ValueError:
        return default


def _env_float(name: str, default: float, minimum: float) -> float:
    try:
        return max(minimum, float(os.environ.get(name, "") or default))
    except ValueError:
        return default


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


# ── Soft L1 contradiction checks (PR #537 secfix, Manus audit 2026-11-24) ────
# _REFUSAL_RE finds a refusal *substring*; it does not say whether the refusal
# is itself negated ("Неверно, что 21,8 не используются") or contradicted by
# an assertion of use in the same text ("…; напротив, они включены").
# These are surface patterns, not semantic understanding. On any doubt the
# sentence is not treated as an explicit refusal, so Soft L1 does not apply
# and the strict L1 block stays.

# The claim of a refusal is denied ("it is not true that …").
_NEGATED_CLAIM_RE = re.compile(
    r"(?:\bневерно\b|\bнеправд\w*|\bложно\b|\bне\s+правда\b|\bне\s+верно\b"
    r"|\bне\s+соответству\w*\s+действительност\w*"
    r"|\bnot\s+true\b|\buntrue\b|\bis\s+false\b|\bis\s+wrong\b|\bincorrect\b"
    r"|\bisn't\s+(?:true|correct|the\s+case)\b|\bnot\s+the\s+case\b"
    r"|\bнельзя\s+(?:сказать|утверждать)\b|\bnever\s+said\b|\bcontrary\s+to\b)",
    re.IGNORECASE,
)
# Explicit contrast that reverses what came before.
_CONTRAST_RE = re.compile(
    r"\b(?:напротив|наоборот|тем\s+не\s+менее|on\s+the\s+contrary|nevertheless"
    r"|nonetheless|instead)\b",
    re.IGNORECASE,
)
# The refusal is someone else's statement, hedged, conditional or a question.
_REPORTED_RE = re.compile(
    r"\b(?:заявил\w*|заявля\w*|сказал\w*|говорит|говорят|утвержда(?:ет|ют|л|ла|ли)"
    r"|по\s+словам|якобы|claims?|claimed|said|says|allegedly|reportedly)\b",
    re.IGNORECASE,
)
_HEDGE_RE = re.compile(
    r"\b(?:возможно|вероятно|видимо|кажется|может\s+быть|perhaps|maybe|probably|possibly)\b",
    re.IGNORECASE,
)
_CONDITIONAL_RE = re.compile(r"\b(?:если|if|unless|whether)\b", re.IGNORECASE)
_QUESTION_RE = re.compile(r"\?\s*$|\bли\b", re.IGNORECASE)
# Verbs that assert use / inclusion / a value. Un-negated, outside a clause
# about the official figures, they contradict a refusal.
_USE_VERB_RE = re.compile(
    r"\b(?:использ\w*|включ\w*|опира\w*|оперир\w*|публику\w*|опубликов\w*"
    r"|цитиру\w*|процитир\w*|приво\w*|привед\w*|учт\w*|учитыва\w*"
    r"|составля\w*|составил\w*|равн\w*|достиг\w*"
    r"|us(?:e|es|ed|ing)|includ(?:e|es|ed|ing)|rel(?:y|ies|ied|ying)|cit(?:e|es|ed|ing)"
    r"|publish(?:es|ed|ing)?|count(?:s|ed)?|amount(?:s|ed)?|equal(?:s|ed)?|reached|totals?)\b",
    re.IGNORECASE,
)
# Refusal forms that are themselves negatable ("не исключены", "not excluded").
_EXCLUSION_REFUSAL_RE = re.compile(
    r"\b(?:исключ\w*|запре\w*|опущ\w*|опуска\w*|отклон\w*|exclud\w*|omit\w*"
    r"|forbid\w*|prohibit\w*|withheld)",
    re.IGNORECASE,
)
_ANAPHORA_RE = re.compile(
    r"\b(?:они|их|им|ими|она|её|ее|ей|ней|неё|нее|ним|них|оно|эт(?:а|у|ой|и|их)\s+(?:цифр|данн|показател|значени)\w*"
    r"|these\s+(?:figures|numbers|data|values)|this\s+(?:figure|number|value)|them|they|those|it)\b",
    re.IGNORECASE,
)
_OFFICIAL_CLAUSE_RE = re.compile(r"официальн|утверждённ\w*\s+данн|\bofficial\b", re.IGNORECASE)
_NEGATOR_TOKENS = frozenset({"не", "ни", "нет", "нельзя", "без", "not", "never", "no", "cannot", "without"})
_NEGATING_STEMS = ("запре", "отказ", "исключ", "exclud", "refus", "declin", "avoid", "prohibit", "forbid", "omit")
_FILLER_TOKENS = frozenset({"вовсе", "были", "был", "была", "было", "будут", "никак", "were", "was", "been", "is", "are", "be"})
# Clause boundaries; a comma between digits (21,8) is not one.
_CLAUSE_SPLIT_RE = re.compile(
    r"(?<!\d),|,(?!\d)|[;:—–]|\s(?:а|но|однако|зато|but|however|while|whereas|yet)\s",
    re.IGNORECASE,
)


def _clauses(sentence: str) -> list[str]:
    return [c for c in _CLAUSE_SPLIT_RE.split(sentence) if c and c.strip()]


def _tokens(text: str) -> list[str]:
    return re.findall(r"[\w']+", text.lower())


# Phrases that contain a negator word but do not negate ("тем не менее").
_NON_NEGATING_PHRASES_RE = re.compile(
    r"\b(?:тем\s+не\s+менее|не\s+менее|не\s+только|not\s+only)\b", re.IGNORECASE
)


def _negated_before(prefix: str, *, window: int = 3) -> bool:
    toks = _tokens(_NON_NEGATING_PHRASES_RE.sub(" ", prefix))
    for t in toks[-window:]:
        if t in _NEGATOR_TOKENS or t.endswith("n't") or t.startswith(_NEGATING_STEMS):
            return True
    return False


def _negated_directly(prefix: str) -> bool:
    toks = [t for t in _tokens(prefix) if t not in _FILLER_TOKENS]
    return bool(toks) and (toks[-1] in _NEGATOR_TOKENS or toks[-1].endswith("n't"))


# "Source X cites 7.6 …" / "в документе (источник X) приводятся цифры …":
# a citing verb whose subject is the refused source reports what the source
# says; it is not the speaker using the figures.
_ATTRIBUTION_VERB_RE = re.compile(
    r"^(?:приво\w*|привед\w*|указ\w*|называ\w*|содерж\w*|сообща\w*"
    r"|cit(?:e|es|ed|ing)|states?|stated|reports?|reported|lists?|listed|mentions?|mentioned|gives)$",
    re.IGNORECASE,
)
_SOURCE_WORD_RE = re.compile(
    r"\b(?:источник\w*|бриф\w*|документ\w*|source|brief|document)\b", re.IGNORECASE
)


def _affirmed_use(text: str) -> bool:
    """True when a clause asserts use / a value without negation and without
    being about the official figures or attributed to the refused source."""
    for clause in _clauses(text):
        if _OFFICIAL_CLAUSE_RE.search(clause):
            continue
        for m in _USE_VERB_RE.finditer(clause):
            before = clause[: m.start()]
            if _negated_before(before):
                continue
            if _ATTRIBUTION_VERB_RE.match(m.group(0)) and _SOURCE_WORD_RE.search(before):
                continue
            return True
    return False


def refusal_assessment(sentence: str) -> str:
    """Classify one sentence: ``refusal`` | ``negated_refusal`` | ``ambiguous`` | ``none``.

    Pattern heuristic only. Anything other than ``refusal`` keeps strict L1.
    """
    if not sentence or not sentence.strip():
        return "none"
    if not _REFUSAL_RE.search(sentence):
        return "none"
    if _NEGATED_CLAIM_RE.search(sentence):
        return "negated_refusal"
    for clause in _clauses(sentence):
        for m in _EXCLUSION_REFUSAL_RE.finditer(clause):
            if _negated_directly(clause[: m.start()]):
                return "negated_refusal"
    if (
        _CONTRAST_RE.search(sentence)
        or _REPORTED_RE.search(sentence)
        or _HEDGE_RE.search(sentence)
        or _CONDITIONAL_RE.search(sentence)
        or _QUESTION_RE.search(sentence)
        or _affirmed_use(sentence)
    ):
        return "ambiguous"
    return "refusal"


def text_contradicts_refusal(text: str, refusal_sentences: Iterable[str]) -> bool:
    """A sentence elsewhere in the text denies the refusal or asserts use of
    the refused figures ("Напротив, они включены в отчёт.")."""
    skip = {s.strip() for s in refusal_sentences}
    for _a, _b, sent in sentences_with_spans(text):
        if sent.strip() in skip:
            continue
        if _NEGATED_CLAIM_RE.search(sent) and _REFUSAL_RE.search(sent):
            return True
        if (_CONTRAST_RE.search(sent) or _ANAPHORA_RE.search(sent)) and _affirmed_use(sent):
            return True
    return False


def is_explicit_refusal_sentence(sentence: str) -> bool:
    return refusal_assessment(sentence) == "refusal"


def classify_l1_hits(text: str, l1_hits: list[SourceXHit]) -> dict[str, Any]:
    official = has_official_figures(text)
    per_hit: list[dict[str, Any]] = []
    all_refusal = True if l1_hits else False
    for h in l1_hits:
        sent = sentence_for_offset(text, h.start, h.end)
        kind = refusal_assessment(sent)
        refusal = kind == "refusal"
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
                "refusal_kind": kind,
                "label_only": bool(_LABEL_ONLY_RE.search(sent)),
            }
        )
    contradicted = bool(all_refusal) and text_contradicts_refusal(
        text, [x["sentence"] for x in per_hit]
    )
    if contradicted:
        all_refusal = False
    qualifies = bool(l1_hits) and official["both"] and all_refusal
    return {
        "official": official,
        "all_l1_in_refusal_sentences": all_refusal,
        "qualifies_for_flag_l1_refusal": qualifies,
        "refusal_contradicted_elsewhere": contradicted,
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
    """In-memory decision record, including excerpts. NEVER log this.

    Use :func:`safe_log_record` for anything written to logs.
    """
    return verdict.to_log()


def safe_log_record(verdict: SourceXVerdict, *, surface: str | None = None) -> dict[str, Any]:
    """Log-safe decision record (round 2, P0-01).

    Contains only the event, booleans, and per hit the rule id, level and
    character positions. No excerpt, sentence, source text, hash of the
    text, or exception message.
    """
    soft = verdict.soft_classification or {}
    official = soft.get("official") or {}
    record: dict[str, Any] = {
        "event": verdict.event,
        "blocked": verdict.blocked,
        "flagged": verdict.flagged,
        "hits": [
            {"rule": h.rule, "level": h.level, "start": h.start, "end": h.end}
            for h in verdict.hits
        ],
        "official_14_2": bool(official.get("has_14_2")),
        "official_3_1_pct": bool(official.get("has_3_1_pct")),
        "all_l1_in_refusal_sentences": bool(soft.get("all_l1_in_refusal_sentences")),
    }
    if surface is not None:
        record["surface"] = surface
    return record


def safe_notes_log(notes_review: dict[str, Any]) -> dict[str, Any]:
    """Log-safe view of :func:`review_notes` output (no excerpts)."""
    return {
        "event": notes_review.get("event"),
        "level": notes_review.get("level"),
        "hits": [
            {
                "rule": h.get("rule"),
                "level": h.get("level"),
                "start": h.get("start"),
                "end": h.get("end"),
            }
            for h in notes_review.get("hits") or []
        ],
    }


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
        # Type only: no message, no traceback (messages may quote the text).
        logger.error("SOURCE_X_GATE GATE_ERROR surface=pipeline: %s", type(exc).__name__)
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
    safe = safe_log_record(verdict, surface="pipeline")

    if verdict.blocked:
        logger.warning("SOURCE_X_GATE BLOCKED_ATTEMPT: %s", safe)
        result["answer"] = payload["message"]
        result["source_x_gate_blocked"] = True
    elif verdict.event == "FLAG_L1_REFUSAL":
        logger.info("SOURCE_X_GATE FLAG_L1_REFUSAL: %s", safe)
        result["source_x_gate_flagged"] = True
        result["source_x_gate_flag_l1_refusal"] = True
    elif verdict.flagged:
        logger.info("SOURCE_X_GATE FLAG_REVIEW: %s", safe)
        result["source_x_gate_flagged"] = True
    else:
        logger.debug("SOURCE_X_GATE ALLOW: %s", safe)

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
            logger.info("SOURCE_X_GATE FLAG_REVIEW_NOTES: %s", safe_notes_log(notes_review))
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
    # DISABLED | NO_ANSWER | ALLOW | FLAG_REVIEW | FLAG_L1_REFUSAL | BLOCKED_ATTEMPT | GATE_ERROR
    status: str
    surface: str
    blocked: bool = False
    flagged: bool = False
    rules: tuple[str, ...] = ()
    reason: str = ""
    origin: str = "final_check"  # final_check | pipeline

    @property
    def enabled(self) -> bool:
        return self.status != "DISABLED"

    def public(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "surface": self.surface,
            "blocked": self.blocked,
            "flagged": self.flagged,
            "delivered": (not self.blocked) and self.status != "NO_ANSWER",
            "rules": list(self.rules),
            "reason": self.reason,
            "origin": self.origin,
        }


# Severity for merging verdicts: a later re-check may never weaken an
# earlier decision (round 2, P1-01).
_STATUS_RANK = {
    "DISABLED": -1,
    "NO_ANSWER": 0,
    "ALLOW": 1,
    "FLAG_REVIEW": 2,
    "FLAG_L1_REFUSAL": 3,
    "BLOCKED_ATTEMPT": 4,
    GATE_ERROR_EVENT: 5,
}


def merge_with_prior_verdict(
    recheck: FinalGateOutcome,
    prior: dict[str, Any] | None,
) -> FinalGateOutcome:
    """Keep the stricter of an earlier (pipeline) verdict and the re-check.

    ``prior`` is the pipeline's ``result["source_x_gate"]`` record. If the
    pipeline already withheld the answer, the re-check of the stub (which
    is clean and would say ALLOW) must not erase that decision.
    """
    if not recheck.enabled or not isinstance(prior, dict):
        return recheck
    prior_status = str(prior.get("status") or prior.get("event") or "")
    if _STATUS_RANK.get(prior_status, -1) <= _STATUS_RANK.get(recheck.status, -1):
        return recheck
    prior_blocked = bool(prior.get("blocked")) or prior_status in ("BLOCKED_ATTEMPT", GATE_ERROR_EVENT)
    rules = tuple(
        sorted(
            {str(h.get("rule")) for h in prior.get("hits") or [] if h.get("level") == "block"}
        )
    )
    return FinalGateOutcome(
        text=recheck.text,
        status=prior_status,
        surface=recheck.surface,
        blocked=prior_blocked,
        flagged=bool(prior.get("flagged")) or prior_status.startswith("FLAG"),
        rules=rules,
        reason=str(prior.get("reason") or "withheld_by_pipeline_gate"),
        origin="pipeline",
    )


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
            return FinalGateOutcome(
                text=None, status="NO_ANSWER", surface=surface, reason="no_answer_produced"
            )
        raw = text if isinstance(text, str) else str(text)
        verdict = apply_gate(raw, config=cfg)
        payload = user_facing_payload(raw, verdict, config=cfg)
        record = safe_log_record(verdict, surface=surface)
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
            reason="source_x_figures" if verdict.blocked else "",
        )
    except Exception as exc:  # noqa: BLE001 - fail closed when the flag is on
        # Type only: no message, no traceback (messages may quote the text).
        logger.error("SOURCE_X_GATE GATE_ERROR surface=%s: %s", surface, type(exc).__name__)
        return FinalGateOutcome(
            text=cfg.error_message,
            status=GATE_ERROR_EVENT,
            surface=surface,
            blocked=True,
            reason=f"gate_exception:{type(exc).__name__}",
        )


STREAM_BUFFER_LIMIT_REASON = "stream_buffer_limit"
STREAM_DEADLINE_REASON = "stream_deadline"


class SourceXStreamBuffer:
    """Hold streamed model text until the gate has a verdict on all of it.

    Flag off: :meth:`feed` returns each chunk unchanged (streaming as
    before). Flag on: :meth:`feed` keeps the chunk and returns ``None`` so
    nothing reaches the client; :meth:`finalize` gates the whole text and
    returns the only text that may be released. Figures split across chunks
    (``"2" + "1,8"``) are therefore seen whole.

    Bounded (round 2, P1-02): at most ``config.stream_max_bytes`` UTF-8
    bytes are held. Past the limit the buffer drops what it holds, sets
    :attr:`overflowed`, and :meth:`finalize` fails closed with
    ``GATE_ERROR`` / ``stream_buffer_limit`` — no partial text is released.
    """

    def __init__(self, *, surface: str, config: SourceXGateConfig | None = None) -> None:
        self.surface = surface
        self.config = resolve_gate_config(config)
        self.enabled = bool(self.config.enabled)
        self.max_bytes = int(self.config.stream_max_bytes)
        self._parts: list[str] = []
        self._bytes = 0
        self.overflowed = False
        self.deadline_exceeded = False

    def feed(self, chunk: str | None) -> str | None:
        if not self.enabled:
            return chunk
        if self.overflowed or not chunk:
            return None
        text = chunk if isinstance(chunk, str) else str(chunk)
        self._bytes += len(text.encode("utf-8"))
        if self._bytes > self.max_bytes:
            self._overflow()
            return None
        self._parts.append(text)
        return None

    def _overflow(self) -> None:
        self.overflowed = True
        self._parts.clear()
        logger.error(
            "SOURCE_X_GATE GATE_ERROR surface=%s: %s",
            self.surface,
            STREAM_BUFFER_LIMIT_REASON,
        )

    def mark_deadline_exceeded(self) -> None:
        self.deadline_exceeded = True
        self._parts.clear()
        logger.error(
            "SOURCE_X_GATE GATE_ERROR surface=%s: %s", self.surface, STREAM_DEADLINE_REASON
        )

    @property
    def held_bytes(self) -> int:
        return 0 if self.overflowed else self._bytes

    @property
    def held_text(self) -> str:
        return "".join(self._parts)

    def _fail(self, reason: str) -> FinalGateOutcome:
        return FinalGateOutcome(
            text=self.config.error_message,
            status=GATE_ERROR_EVENT,
            surface=self.surface,
            blocked=True,
            reason=reason,
        )

    def finalize(self, full_text: str | None = None) -> FinalGateOutcome:
        """Gate ``full_text`` (provider's final reply) or the held chunks.

        When both exist and differ, both are gated and the stricter result
        wins, so a provider that reports a different final reply cannot
        smuggle held chunks past the check. Overflow, an exceeded deadline,
        or a final reply above the byte limit fail closed.
        """
        if self.enabled:
            if self.overflowed:
                return self._fail(STREAM_BUFFER_LIMIT_REASON)
            if self.deadline_exceeded:
                return self._fail(STREAM_DEADLINE_REASON)
            if full_text is not None and len(full_text.encode("utf-8")) > self.max_bytes:
                self._overflow()
                return self._fail(STREAM_BUFFER_LIMIT_REASON)
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


# ── Outbound boundary (round 2, P0-02) ───────────────────────────────────────

WITHHELD_PLACEHOLDER = "[withheld: source-X gate]"

PathPattern = tuple[str, ...]


def _path_matches(path: tuple[str, ...], pattern: PathPattern, *, prefix: bool) -> bool:
    if prefix:
        if len(path) < len(pattern):
            return False
    elif len(path) != len(pattern):
        return False
    return all(p == "*" or p == q for p, q in zip(pattern, path, strict=False))


def sanitize_outbound(
    payload: Any,
    *,
    surface: str,
    exempt: Iterable[PathPattern] = (),
    already_gated: Iterable[PathPattern] = (),
    config: SourceXGateConfig | None = None,
) -> tuple[Any, list[str]]:
    """Scan every string leaf of a serialisable payload for Level-1 figures.

    Used on the whole HTTP response body and on every SSE event while the
    flag is on. A string leaf with a Level-1 figure is replaced by
    :data:`WITHHELD_PLACEHOLDER` (strict rule: no soft refusal path here).

    * ``already_gated``: exact paths whose text was already decided by
      :func:`gate_final_text` (soft L1 may legitimately deliver a refusal);
      they are not re-scanned.
    * ``exempt``: path prefixes that the evidence-access policy currently
      returns unchanged (``facts``, ``memory_*``, ``dialogue_essence``,
      essence snapshots, the user's own query). They are NOT modified here;
      see the PROPOSED ADR for the data-flow map. Hits inside them are only
      counted in the returned list as ``exempt:<path>``.

    Returns ``(payload, findings)``; findings hold paths only, never text.
    Never raises: on internal error every non-exempt, non-gated string leaf
    is withheld (fail closed).
    """
    cfg = resolve_gate_config(config)
    if not cfg.enabled:
        return payload, []
    exempt_l = [tuple(p) for p in exempt]
    gated_l = [tuple(p) for p in already_gated]
    findings: list[str] = []
    patterns = _compile(cfg.block_number_patterns)

    def has_l1(text: str) -> bool:
        return any(p.search(text) for _, p in patterns)

    def walk(node: Any, path: tuple[str, ...], fail_all: bool) -> Any:
        if any(_path_matches(path, g, prefix=False) for g in gated_l):
            return node
        is_exempt = any(_path_matches(path, e, prefix=True) for e in exempt_l)
        if isinstance(node, str):
            if is_exempt:
                if not fail_all and has_l1(node):
                    findings.append("exempt:" + "/".join(path))
                return node
            if fail_all or has_l1(node):
                findings.append("/".join(path))
                return WITHHELD_PLACEHOLDER
            return node
        if isinstance(node, dict):
            return {k: walk(v, path + (str(k),), fail_all) for k, v in node.items()}
        if isinstance(node, list):
            return [walk(v, path + (str(i),), fail_all) for i, v in enumerate(node)]
        if isinstance(node, tuple):
            return tuple(walk(v, path + (str(i),), fail_all) for i, v in enumerate(node))
        return node

    try:
        out = walk(payload, (), False)
    except Exception as exc:  # noqa: BLE001 - fail closed
        logger.error("SOURCE_X_GATE GATE_ERROR surface=%s: %s", surface, type(exc).__name__)
        findings = []
        try:
            out = walk(payload, (), True)
        except Exception:  # noqa: BLE001
            return {}, ["*"]
    blocked = [f for f in findings if not f.startswith("exempt:")]
    if blocked:
        logger.warning(
            "SOURCE_X_GATE OUTBOUND_WITHHELD surface=%s paths=%s", surface, blocked
        )
    return out, findings


__all__ = [
    "DEFAULT_BLOCK_NUMBER_PATTERNS",
    "FinalGateOutcome",
    "GATE_ERROR_EVENT",
    "STREAM_BUFFER_LIMIT_REASON",
    "STREAM_DEADLINE_REASON",
    "SourceXStreamBuffer",
    "USER_FACING_GATE_ERROR_MESSAGE",
    "WITHHELD_PLACEHOLDER",
    "fail_closed_pipeline_result",
    "gate_final_text",
    "merge_with_prior_verdict",
    "resolve_gate_config",
    "safe_log_record",
    "safe_notes_log",
    "sanitize_outbound",
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
    "refusal_assessment",
    "text_contradicts_refusal",
    "is_source_x_gate_enabled",
    "review_notes",
    "scan_text",
    "sentences_with_spans",
    "user_facing_payload",
]
