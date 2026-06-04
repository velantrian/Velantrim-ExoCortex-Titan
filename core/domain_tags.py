"""
Domain tags (v4) — science | engineering | perception | personal | system | general.

MVP: поле metadata.domain без миграции схемы SQLite.
"""

from __future__ import annotations

import re
from typing import Any

ALLOWED_DOMAINS = frozenset(
    {
        "general",
        "science",
        "engineering",
        "perception",
        "personal",
        "system",
    }
)

_DOMAIN_ALIASES = {
    "sci": "science",
    "scientific": "science",
    "eng": "engineering",
    "tech": "engineering",
    "technology": "engineering",
    "umwelt": "perception",
    "user": "personal",
}


def normalize_domain(raw: Any) -> str:
    """Привести домен к каноническому имени."""
    if raw is None:
        return "general"
    s = str(raw).strip().lower()
    if not s:
        return "general"
    if s in ALLOWED_DOMAINS:
        return s
    if s in _DOMAIN_ALIASES:
        return _DOMAIN_ALIASES[s]
    return "general"


def infer_domain(
    *,
    claim: str = "",
    source: str = "",
    metadata: dict[str, Any] | None = None,
) -> str:
    """Эвристика домена по тексту и metadata (MVP)."""
    meta = metadata or {}
    if meta.get("layer") == 99 or meta.get("domain") == "perception":
        return "perception"
    if meta.get("channel") == "telegram":
        return "personal"
    blob = f"{claim} {source}".lower()
    if re.search(r"инженер|конструк|kuzu|граф|api|neo4j", blob, re.I):
        return "engineering"
    if re.search(r"учён|наук|фотосин|экосистем|биолог|эксперимент", blob, re.I):
        return "science"
    if re.search(r"velantrim|exocortex|pipeline|esm|truth", blob, re.I):
        return "system"
    if re.search(r"telegram|user|личн|цель", blob, re.I):
        return "personal"
    return "general"


def apply_domain_to_metadata(
    metadata: dict[str, Any] | None,
    *,
    claim: str = "",
    source: str = "",
    explicit_domain: str | None = None,
    infer: bool = True,
) -> dict[str, Any]:
    """Записать metadata.domain и content_domain (совместимость с Velum)."""
    meta = dict(metadata or {})
    if explicit_domain is not None:
        dom = normalize_domain(explicit_domain)
    elif meta.get("domain"):
        dom = normalize_domain(meta["domain"])
    elif infer:
        dom = infer_domain(claim=claim, source=source, metadata=meta)
    else:
        dom = "general"
    meta["domain"] = dom
    meta["content_domain"] = dom
    return meta


def fact_domain(fact: dict[str, Any]) -> str:
    meta = fact.get("metadata") or {}
    if isinstance(meta, str):
        import json

        try:
            meta = json.loads(meta)
        except json.JSONDecodeError:
            meta = {}
    return normalize_domain(meta.get("domain") or meta.get("content_domain"))


def filter_facts_by_domain(
    facts: list[dict[str, Any]],
    domain: str | None,
) -> list[dict[str, Any]]:
    if not domain:
        return facts
    want = normalize_domain(domain)
    if want == "general":
        return facts
    return [f for f in facts if fact_domain(f) == want]


def is_domain_tags_enabled() -> bool:
    from core.feature_config import get_config

    return get_config().app.enable_domain_tags


__all__ = [
    "ALLOWED_DOMAINS",
    "apply_domain_to_metadata",
    "fact_domain",
    "filter_facts_by_domain",
    "infer_domain",
    "is_domain_tags_enabled",
    "normalize_domain",
]
