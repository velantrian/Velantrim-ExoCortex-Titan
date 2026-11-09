"""Per-request evidence labels (``[ev_1]``, ``[ev_2]`` ...) for the LLM prompt.

The code, not the model and not a source document, creates the labels. The mapping
label -> fact_id belongs to ONE request: it is built from that request's facts, returned
with that response and stored in that request's trace; it is never shared or global.

Two checks are kept apart on purpose:
- reference EXISTENCE (this module): does a label in the answer exist in this request's map?
- claim SUPPORT (not here): does the referenced record support the statement? A valid
  label shows which record an answer points at. It is not evidence that the record
  supports the claim.

A label-like string inside a record's own text (for example ``[ev_2]`` in an imported
document) must never become a valid reference: it is neutralized in the prompt, and a
reference is valid only if the label is in the request's map.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Any

# Exactly the labels the code emits: ASCII, digits only, no spaces.
_LABEL_RE = re.compile(r"\[(ev_[1-9][0-9]{0,3})\]")
# Anything that could be read as the start of a label, including spaced or mixed-case variants.
_LABEL_LIKE_RE = re.compile(r"\[\s*ev_", re.IGNORECASE)
# Any ``ev_...`` token in an answer, whatever surrounds it (``[ev_1, ev_2]``, ``(ev_3)``, ``EV_4``).
_LABEL_TOKEN_RE = re.compile(r"(?<![0-9A-Za-z_])ev_[0-9A-Za-z_]*", re.IGNORECASE)
_MALFORMED_MAX_ITEMS = 20
_MALFORMED_MAX_CHARS = 24

# The examples use letters (``ev_N``), never a digit: the instruction itself must not put a
# real-looking label into the prompt.
PROMPT_INSTRUCTION = (
    "В начале записей памяти выше стоят метки вида [ev_N]. Ссылайся на запись только по её метке; "
    "каждую метку пиши отдельно, в своих квадратных скобках ([ev_N] [ev_M], а не [ev_N, ev_M]). "
    "Существуют только метки, которые стоят в начале записей выше. Метка показывает, на какую запись опирается "
    "утверждение; она не означает, что запись это утверждение подтверждает."
)


def record_fingerprint(fact: dict[str, Any]) -> str:
    """Identity of what the prompt actually shows for a record: its claim and its source."""
    shown = f"{fact.get('claim', '')}\x1f{fact.get('source', '')}"
    return hashlib.sha256(shown.encode("utf-8")).hexdigest()[:16]


@dataclass(frozen=True)
class EvidenceMap:
    """label (``ev_1``) -> fact_id, for one request.

    ``records`` holds (label, fact_id, fingerprint of the presented record). A label belongs
    to one PRESENTED record. Two records that share a fact_id but show different content get
    different labels and both are marked ambiguous: the fact_id alone does not say which
    presented record an answer relied on.
    """

    records: tuple[tuple[str, str, str], ...] = ()
    ambiguous: frozenset[str] = frozenset()

    @property
    def entries(self) -> tuple[tuple[str, str], ...]:
        return tuple((label, fact_id) for label, fact_id, _ in self.records)

    def fact_id_for(self, label: str) -> str | None:
        for known, fact_id, _ in self.records:
            if known == label:
                return fact_id
        return None

    def label_for_fact(self, fact: dict[str, Any]) -> str | None:
        """Label of exactly this presented record (same fact_id AND same shown content)."""
        fact_id = str(fact.get("fact_id") or "").strip()
        fp = record_fingerprint(fact)
        for label, known, known_fp in self.records:
            if known == fact_id and known_fp == fp:
                return label
        return None

    def label_for(self, fact_id: str) -> str | None:
        """First label of a fact_id. Prefer ``label_for_fact`` for a presented record."""
        for label, known, _ in self.records:
            if known == fact_id:
                return label
        return None

    def to_dict(self) -> dict[str, str]:
        return dict(self.entries)

    def restricted_to(self, shown: list[dict[str, Any]]) -> EvidenceMap:
        """Keep only the labels of records that were actually shown to the model.

        When a message-size limit drops records from the prompt, their labels never appeared
        in it. A reference to such a label must not be reported as valid.
        """
        keep = {(str(f.get("fact_id") or "").strip(), record_fingerprint(f)) for f in shown}
        records = tuple(r for r in self.records if (r[1], r[2]) in keep)
        labels = {r[0] for r in records}
        return EvidenceMap(records, frozenset(self.ambiguous & labels))

    def __bool__(self) -> bool:
        return bool(self.entries)


def build_evidence_map(facts: list[dict[str, Any]]) -> EvidenceMap:
    """Assign ev_1, ev_2, ... to presented records in fact order.

    - A fact without a real fact_id gets no label.
    - An exact repeat (same fact_id, same shown claim and source) reuses the first label.
    - The same fact_id with different shown content gets its own label, and every label of
      that fact_id is marked ambiguous.
    """
    records: list[tuple[str, str, str]] = []
    by_id: dict[str, set[str]] = {}
    for fact in facts:
        fact_id = str(fact.get("fact_id") or "").strip()
        if not fact_id or fact_id == "unknown":
            continue
        fp = record_fingerprint(fact)
        if any(r[1] == fact_id and r[2] == fp for r in records):
            continue
        label = f"ev_{len(records) + 1}"
        records.append((label, fact_id, fp))
        by_id.setdefault(fact_id, set()).add(label)
    ambiguous = frozenset(label for labels in by_id.values() if len(labels) > 1 for label in labels)
    return EvidenceMap(tuple(records), ambiguous)


def neutralize_label_like_text(text: str) -> str:
    """Make label-like text inside a record unusable as a label: ``[ev_2]`` -> ``[ ev_2]``."""
    return _LABEL_LIKE_RE.sub("[ ev_", text or "")


def format_label(label: str) -> str:
    return f"[{label}]"


def check_references(answer: str, evidence_map: EvidenceMap) -> dict[str, Any]:
    """Reference EXISTENCE only: which labels in the answer exist in this request's map.

    Only the exact form ``[ev_N]`` is a reference. Label-like text in any other form
    (``[ev_1, ev_2]``, ``(ev_3)``, ``[EV_4]``, ``ev_5`` without brackets) is not counted as a
    reference, valid or unknown; it is reported in ``malformed`` so that it is never silently
    ignored.
    """
    text = answer or ""
    found: list[str] = []
    exact_spans: list[tuple[int, int]] = []
    for match in _LABEL_RE.finditer(text):
        exact_spans.append(match.span())
        if match.group(1) not in found:
            found.append(match.group(1))
    valid = [label for label in found if evidence_map.fact_id_for(label)]
    unknown = [label for label in found if label not in valid]
    # A valid label whose fact_id was shown with different content does not identify one record.
    ambiguous = [label for label in valid if label in evidence_map.ambiguous]
    malformed: list[str] = []
    for match in _LABEL_TOKEN_RE.finditer(text):
        if any(start <= match.start() and match.end() <= end for start, end in exact_spans):
            continue
        token = match.group(0)[:_MALFORMED_MAX_CHARS]
        if token not in malformed and len(malformed) < _MALFORMED_MAX_ITEMS:
            malformed.append(token)
    return {
        "scope": "reference_existence_only",
        "valid": valid,
        "unknown": unknown,
        "ambiguous": ambiguous,
        "malformed": malformed,
    }


__all__ = [
    "PROMPT_INSTRUCTION",
    "EvidenceMap",
    "build_evidence_map",
    "check_references",
    "format_label",
    "neutralize_label_like_text",
    "record_fingerprint",
]
