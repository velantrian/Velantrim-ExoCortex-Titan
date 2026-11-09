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

import re
from dataclasses import dataclass
from typing import Any

# Exactly the labels the code emits: ASCII, digits only, no spaces.
_LABEL_RE = re.compile(r"\[(ev_[1-9][0-9]{0,3})\]")
# Anything that could be read as the start of a label, including spaced or mixed-case variants.
_LABEL_LIKE_RE = re.compile(r"\[\s*ev_", re.IGNORECASE)

PROMPT_INSTRUCTION = (
    "Каждая запись памяти имеет метку вида [ev_N]. Ссылайся на запись только по такой метке. "
    "Существуют только метки из списка ниже. Метка показывает, на какую запись опирается "
    "утверждение; она не означает, что запись это утверждение подтверждает."
)


@dataclass(frozen=True)
class EvidenceMap:
    """label (``ev_1``) -> fact_id, for one request."""

    entries: tuple[tuple[str, str], ...] = ()

    def fact_id_for(self, label: str) -> str | None:
        for known, fact_id in self.entries:
            if known == label:
                return fact_id
        return None

    def label_for(self, fact_id: str) -> str | None:
        for label, known in self.entries:
            if known == fact_id:
                return label
        return None

    def to_dict(self) -> dict[str, str]:
        return dict(self.entries)

    def __bool__(self) -> bool:
        return bool(self.entries)


def build_evidence_map(facts: list[dict[str, Any]]) -> EvidenceMap:
    """Assign ev_1, ev_2, ... in fact order. A fact without a real fact_id gets no label,
    and a repeated fact_id keeps its first label."""
    entries: list[tuple[str, str]] = []
    seen: set[str] = set()
    for fact in facts:
        fact_id = str(fact.get("fact_id") or "").strip()
        if not fact_id or fact_id == "unknown" or fact_id in seen:
            continue
        seen.add(fact_id)
        entries.append((f"ev_{len(entries) + 1}", fact_id))
    return EvidenceMap(tuple(entries))


def neutralize_label_like_text(text: str) -> str:
    """Make label-like text inside a record unusable as a label: ``[ev_2]`` -> ``[ ev_2]``."""
    return _LABEL_LIKE_RE.sub("[ ev_", text or "")


def format_label(label: str) -> str:
    return f"[{label}]"


def check_references(answer: str, evidence_map: EvidenceMap) -> dict[str, Any]:
    """Reference EXISTENCE only: which labels in the answer exist in this request's map."""
    found: list[str] = []
    for label in _LABEL_RE.findall(answer or ""):
        if label not in found:
            found.append(label)
    valid = [label for label in found if evidence_map.fact_id_for(label)]
    unknown = [label for label in found if label not in valid]
    return {"scope": "reference_existence_only", "valid": valid, "unknown": unknown}


__all__ = [
    "PROMPT_INSTRUCTION",
    "EvidenceMap",
    "build_evidence_map",
    "check_references",
    "format_label",
    "neutralize_label_like_text",
]
