"""
Эссенция диалога для веб-консоли: узлы, связи, тема, намерение.

Не полная онтология «знаний человечества» — компактный граф из сообщения,
блока памяти браузера и фактов RAG. Для мониторинга в реальном времени (SSE).
"""

from __future__ import annotations

import re
import time
from typing import Any

from core.console_memory import extract_memory_candidates

# Типы узлов и связей (машинный слой — без педагогики в промпт)
NODE_KINDS = frozenset(
    {"user", "person", "place", "age", "topic", "fact", "memory", "system"}
)
REL_TYPES = {
    "about": ("о теме", "about"),
    "named": ("зовут", "named"),
    "lives_in": ("живёт в", "lives in"),
    "age_is": ("возраст", "age"),
    "wants": ("хочет", "wants"),
    "corrects": ("уточняет", "corrects"),
    "relates": ("связано с", "relates to"),
    "in_block": ("в блоке памяти", "in memory block"),
    "retrieved": ("из памяти RAG", "retrieved"),
    "saved": ("сохранено", "saved"),
    "suggested": ("кандидат", "suggested"),
}

_CORRECTION = re.compile(
    r"(исправ|уточн|на самом деле|не\s+\d+\s*,?\s*а\s+|wrong|actually|"
    r"correction|опечатк|ошибк)",
    re.I,
)
_QUESTION = re.compile(r"\?|^(как|что|почему|зачем|где|когда|who|what|why|how)\b", re.I)
_WANT = re.compile(
    r"(хочу|нужно|хотел бы|would like|i want|мне бы|желательно|"
    r"сделайте|сделай|please)",
    re.I,
)
_REMEMBER = re.compile(r"запомни|remember|сохрани в память", re.I)

_NAME = re.compile(
    r"(?:меня зовут|моё имя|мое имя|my name is|зовут)\s+([A-Za-zА-Яа-яЁё\-]{2,40})",
    re.I,
)
_AGE = re.compile(r"(?:мне|i am|i'm)\s+(\d{1,3})\s*(?:лет|years? old)", re.I)
_CITY = re.compile(
    r"(?:живу в|я из|i live in|i'm from|from)\s+([A-Za-zА-Яа-яЁё\-\s]{2,50}?)"
    r"(?:[,.!?]|$)",
    re.I,
)

_TOPIC_KEYWORDS: list[tuple[str, str]] = [
    (r"памят|memory|факт|fact", "Память и факты"),
    (r"консол|console|интерфейс|ui\b", "Веб-консоль"),
    (r"velantrim|экзокортекс|exocortex", "Velantrim"),
    (r"llm|deepseek|gemini|gpt|модел", "LLM и модели"),
    (r"связ|граф|эссенц|essence", "Связи и эссенция"),
    (r"проект|project|стартап", "Проект"),
    (r"работ|work|компани|company", "Работа"),
    (r"семь|родн|family|мама|папа", "Семья"),
    (r"здоров|health|аллерг", "Здоровье"),
    (r"обучен|курс|exam|учеб", "Обучение"),
]


def _nid(prefix: str, key: str) -> str:
    safe = re.sub(r"[^\w\-]", "_", (key or "")[:48].lower())
    return f"{prefix}_{safe}" if safe else f"{prefix}_{int(time.time() * 1000) % 100000}"


def _detect_intent(message: str) -> tuple[str, str]:
    """intent_id, label_ru."""
    raw = (message or "").strip()
    if _CORRECTION.search(raw):
        return "correct", "Уточнение / исправление"
    if _REMEMBER.search(raw):
        return "remember", "Просьба запомнить"
    if _QUESTION.search(raw):
        return "question", "Вопрос"
    if _WANT.search(raw):
        return "wish", "Пожелание / запрос"
    return "inform", "Сообщение / факт"


def _detect_topic(message: str, lang: str) -> str:
    low = (message or "").lower()
    for pat, label in _TOPIC_KEYWORDS:
        if re.search(pat, low, re.I):
            return label
    words = [w for w in re.findall(r"[а-яёa-z]{4,}", low, re.I) if len(w) >= 4]
    if words:
        head = " ".join(words[:3])
        return head[:60] + ("…" if len(head) > 60 else "")
    return "Общий диалог" if lang != "en" else "General dialogue"


def _extract_entities(message: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    m = _NAME.search(message or "")
    if m:
        out.append({"kind": "person", "label": m.group(1).strip(), "key": m.group(1).strip()})
    m = _AGE.search(message or "")
    if m:
        out.append({"kind": "age", "label": m.group(1), "key": f"age_{m.group(1)}"})
    m = _CITY.search(message or "")
    if m:
        city = " ".join(m.group(1).split())
        out.append({"kind": "place", "label": city, "key": city})
    return out


def build_essence_snapshot(
    message: str,
    *,
    lang: str = "ru",
    phase: str = "read",
    block_memory: list[dict[str, Any]] | None = None,
    retrieved_facts: list[dict[str, Any]] | None = None,
    candidates: list[dict[str, Any]] | None = None,
    memory_saved: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Снимок графа эссенции для UI.

    phase: read | link | commit — стадия обработки (для live-мониторинга).
    """
    en = lang == "en"
    msg = (message or "").strip()
    intent_id, intent_label = _detect_intent(msg)
    topic = _detect_topic(msg, lang)

    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    seen_nodes: set[str] = set()

    def add_node(nid: str, label: str, kind: str, status: str = "active") -> str:
        if nid in seen_nodes:
            return nid
        seen_nodes.add(nid)
        nodes.append(
            {
                "id": nid,
                "label": label[:120],
                "kind": kind if kind in NODE_KINDS else "fact",
                "status": status,
            }
        )
        return nid

    def add_edge(fr: str, to: str, rel: str, label: str | None = None) -> None:
        if fr not in seen_nodes or to not in seen_nodes:
            return
        ru, en_l = REL_TYPES.get(rel, ("связь", "link"))
        edges.append(
            {
                "id": f"e_{fr}_{to}_{rel}",
                "from": fr,
                "to": to,
                "rel": rel,
                "label": label or (en_l if en else ru),
            }
        )

    user_id = add_node("n_user", "Вы" if not en else "You", "user", "active")
    topic_id = add_node(_nid("topic", topic), topic, "topic", "active")
    add_edge(user_id, topic_id, "about")

    for ent in _extract_entities(msg):
        eid = add_node(_nid(ent["kind"], ent["key"]), ent["label"], ent["kind"], "hypothesis")
        rel = "named" if ent["kind"] == "person" else "lives_in" if ent["kind"] == "place" else "age_is"
        add_edge(user_id, eid, rel)

    if intent_id == "correct":
        corr_id = add_node("n_correction", "Исправление" if not en else "Correction", "topic", "active")
        add_edge(user_id, corr_id, "corrects", intent_label)

    # --- link: блок памяти + RAG ---
    if phase in ("link", "commit"):
        for item in (block_memory or [])[:12]:
            claim = (item.get("claim") or "").strip()
            if not claim:
                continue
            fid = add_node(_nid("blk", claim), claim[:80], "memory", "committed")
            add_edge(fid, topic_id, "relates")
            add_edge(user_id, fid, "in_block")

        for fact in (retrieved_facts or [])[:8]:
            claim = (fact.get("claim") or "").strip()
            if not claim:
                continue
            fid = add_node(_nid("rag", claim), claim[:80], "system", "retrieved")
            add_edge(fid, topic_id, "retrieved")
            add_edge(user_id, fid, "retrieved")

    # --- commit: кандидаты и сохранения ---
    if phase == "commit":
        for cand in (candidates or [])[:6]:
            claim = (cand.get("claim") or "").strip()
            if not claim:
                continue
            st = "hypothesis"
            fid = add_node(_nid("cand", claim), claim[:80], "fact", st)
            add_edge(user_id, fid, "suggested")

        for saved in (memory_saved or [])[:6]:
            claim = (saved.get("claim") or "").strip()
            if not claim:
                continue
            store = saved.get("memory_store") or "block"
            kind = "memory" if store == "block" else "system"
            fid = add_node(_nid("saved", claim), claim[:80], kind, "committed")
            add_edge(user_id, fid, "saved")

    # Кандидаты из эвристик, если не переданы
    if phase == "read" and not candidates:
        for cand in extract_memory_candidates(msg)[:4]:
            claim = (cand.get("claim") or "").strip()
            if not claim:
                continue
            fid = add_node(_nid("ext", claim), claim[:80], "fact", "hypothesis")
            add_edge(user_id, fid, "suggested")

    summary_parts = [topic, intent_label]
    if nodes and len(nodes) > 2:
        summary_parts.append(f"{len(nodes)} узл., {len(edges)} связ.")
    summary = " · ".join(summary_parts)

    pedagogy = _pedagogy_line(
        en=en,
        intent_id=intent_id,
        topic=topic,
        n_nodes=len(nodes),
        n_edges=len(edges),
        phase=phase,
    )

    return {
        "phase": phase,
        "updated_at_ms": int(time.time() * 1000),
        "topic": topic,
        "intent": intent_id,
        "intent_label": intent_label,
        "summary": summary,
        "nodes": nodes,
        "edges": edges,
        "pedagogy": pedagogy,
        "test_mode": True,
    }


def _pedagogy_line(
    *,
    en: bool,
    intent_id: str,
    topic: str,
    n_nodes: int,
    n_edges: int,
    phase: str,
) -> str:
    """Короткое объяснение для человека в правой панели."""
    phase_ru = {"read": "чтение сообщения", "link": "связь с памятью", "commit": "фиксация"}
    phase_en = {"read": "reading message", "link": "linking memory", "commit": "commit"}
    ph = phase_en.get(phase, phase) if en else phase_ru.get(phase, phase)
    if en:
        return (
            f"Stage: {ph}. Topic «{topic}». "
            f"Built {n_nodes} nodes and {n_edges} edges from your text and memory (test console)."
        )
    return (
        f"Стадия: {ph}. Тема «{topic}». "
        f"Собрано {n_nodes} узлов и {n_edges} связей из текста и памяти (тестовая консоль)."
    )


__all__ = ["build_essence_snapshot", "NODE_KINDS", "REL_TYPES"]
