"""Answer composition for offline LocalMind replies."""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any

from core.console_memory import category_emoji, category_label, classify_fact
from localmind.intent_router import intent_for


def _lang(lang: str | None, text: str) -> str:
    if (lang or "").lower().startswith("en"):
        return "en"
    if re.search(r"[а-яё]", text or "", re.I):
        return "ru"
    return "en" if re.search(r"\b(what|who|how|tell|about|projects|notes)\b", text or "", re.I) else "ru"


def _fact_claim(fact: dict[str, Any]) -> str:
    return str(fact.get("claim") or fact.get("text") or "").strip()


def _fact_category(fact: dict[str, Any]) -> str:
    meta = fact.get("metadata") or {}
    if not isinstance(meta, dict):
        meta = {}
    claim = _fact_claim(fact)
    return str(meta.get("memory_category") or meta.get("category") or classify_fact(claim) or "general")


def _dedupe_facts(facts: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for fact in facts:
        claim = _fact_claim(fact)
        if not claim:
            continue
        key = re.sub(r"\W+", " ", claim.lower(), flags=re.U).strip()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(fact)
    return out


def _filter_facts(intent: str, facts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    facts = _dedupe_facts(facts)
    if intent == "projects":
        return [
            f for f in facts
            if _fact_category(f) in {"project", "work"}
            or re.search(r"(проект|project|repo|репозитор|kuzu|neo4j)", _fact_claim(f), re.I)
        ]
    if intent == "about_user":
        preferred = [
            f for f in facts
            if _fact_category(f) in {"personal", "family", "work", "project", "preference", "health", "contact", "date"}
        ]
        return preferred or facts
    return facts


def _format_facts(facts: list[dict[str, Any]], lang: str, detailed: bool) -> str:
    if not facts:
        return "I do not have matching saved facts yet." if lang == "en" else "Пока нет подходящих сохранённых фактов."
    lines: list[str] = []
    for fact in facts[:20 if detailed else 8]:
        claim = _fact_claim(fact)
        cat = _fact_category(fact)
        state = fact.get("epistemic_state") or "Observed"
        conf = fact.get("confidence")
        prefix = f"{category_emoji(cat)} {category_label(cat, lang)}"
        if detailed:
            fid = fact.get("fact_id") or fact.get("id") or "?"
            conf_text = f", conf={float(conf):.0%}" if isinstance(conf, (int, float)) else ""
            lines.append(f"• {prefix}: {claim} [{fid}, {state}{conf_text}]")
        else:
            lines.append(f"• {prefix}: {claim}")
    return "\n".join(lines)


def build_offline_reply(
    message: str,
    facts: list[dict[str, Any]],
    notes: list[dict[str, Any]] | None = None,
    lang: str | None = "ru",
) -> str | None:
    intent = intent_for(message)
    if intent == "none":
        return None
    actual_lang = _lang(lang, message)
    detailed = bool(re.search(r"(подроб|деталь|detail|detailed|everything|всё|все)", message or "", re.I))
    notes = notes or []

    if intent == "greeting":
        return (
            "Hi. I am here, working locally with the saved memory. You can ask what I know about you, projects, notes, or how I am built."
            if actual_lang == "en"
            else "Привет. Я на месте и могу работать локально с сохранённой памятью. Можешь спросить, что я знаю о тебе, о проектах, заметках или как я устроен."
        )
    if intent == "status":
        return (
            f"I am running locally. I can read saved facts ({len(_dedupe_facts(facts))}) and notes ({len(notes)}) without internet."
            if actual_lang == "en"
            else f"Работаю локально. Без интернета могу читать сохранённые факты ({len(_dedupe_facts(facts))}) и заметки ({len(notes)})."
        )
    if intent == "system":
        return (
            "I am the Velantrim console: FastAPI server, SQLite memory, retrieval pipeline, TruthGate/ESM states, optional LLM connectors, and LocalMind for offline answers."
            if actual_lang == "en"
            else "Я консоль Velantrim: FastAPI-сервер, SQLite-память, retrieval-пайплайн, состояния TruthGate/ESM, опциональные LLM-провайдеры и LocalMind для offline-ответов."
        )
    if intent == "notes":
        if not notes:
            return "No saved notes yet." if actual_lang == "en" else "Заметок пока нет."
        head = "Saved notes:" if actual_lang == "en" else "Сохранённые заметки:"
        body = "\n".join(
            f"• {n.get('note_id')}: {n.get('title') or 'Note'} — {n.get('content', '')[:240]}"
            for n in notes[:12]
        )
        return head + "\n" + body

    selected = _filter_facts(intent, facts)
    if intent == "projects":
        head = "Saved project/work information:" if actual_lang == "en" else "Сохранённая информация о проектах/работе:"
    elif intent == "inventory":
        head = "Saved information I can see locally:" if actual_lang == "en" else "Информация, которую я вижу локально:"
    else:
        head = "What I know about you from saved memory:" if actual_lang == "en" else "Что я знаю о тебе из сохранённой памяти:"
    return head + "\n" + _format_facts(selected, actual_lang, detailed)

