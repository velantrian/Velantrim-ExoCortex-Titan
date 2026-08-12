"""
📚 core/world_skills_ingest.py — ingest базы знаний World Skills Core (вариант 3)
================================================================================

Превращает курируемые батч-таблицы `docs/knowledge/world_skills_core/ru/*BATCH*.ru.md`
в факты + типизированные causal-рёбра, чтобы живой пайплайн (Essence-цепочки, семантическая
корроборация, обучение) работал на НАСТОЯЩИХ знаниях, а не на демо.

Read-only к markdown (зона Codex не пишется). Пишет в ПЕРЕДАННЫЙ store (по умолчанию НЕ в
основной velantrim.db — указывай отдельный knowledge-store). Курируемые знания приходят
сразу `Validated` (схема KNOWLEDGE_0). No-DELETE. Без LLM.

Формат таблицы батча: | ID | Тип | Суть | Условия/границы | Связи |
"""
from __future__ import annotations

import glob
import logging
import os
import re
from collections.abc import Sequence
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_KNOWLEDGE_DIR = "docs/knowledge/world_skills_core/ru"
FACT_ID_RE = re.compile(r"^[a-z0-9_]+(?:\.[a-z0-9_]+)+$")

# Не-факт документы (карты/охват/протокол) — у них нет таблицы `| ID | … | Суть | …`.
# Всё остальное в каталоге — таблицы фактов, включая seed-паки 01–09 (P0/P1: формальная
# логика/математика, природа, инженерия, человек+общество), которые раньше терялись из-за
# фильтра `*BATCH*` и уносили самые структурированные научные единицы (formal_notation/limits).
_NON_FACT_FILES = frozenset({
    "00_WORLD_SKILLS_CORE_MAP.ru.md",
    "00_CURATED_CAUSAL_RELATIONS.ru.md",
    "10_PRACTICAL_FULL_SCOPE_MAP.ru.md",
    "11_AGRO_TEXTILE_INDUSTRY_ECONOMY_SCOPE.ru.md",
    "12_50K_COLLECTION_PROTOCOL.ru.md",
    "99_SOURCE_RULES_AND_COLLECTION_PLAN.ru.md",
})


def split_markdown_table_row(line: str) -> list[str]:
    """Split a markdown row without treating code-span or escaped pipes as columns."""
    row = line.strip()
    if not row.startswith("|"):
        return []
    cells: list[str] = []
    current: list[str] = []
    in_code = False
    escaped = False
    for char in row[1:]:
        if escaped:
            current.append(char)
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == "`":
            in_code = not in_code
            current.append(char)
        elif char == "|" and not in_code:
            cells.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    if current:
        cells.append("".join(current).strip())
    return cells


def parse_batch_markdown(text: str) -> list[dict[str, Any]]:
    """Распарсить markdown-таблицу батча → список фактов (чистая, тестируемая функция).

    HEADER-AWARE: колонка «Суть» (claim) определяется по строке заголовка — форматы
    различаются: старый `| ID | Тип | Суть | Условия | Связи |` (Суть = col 2) и новый
    `| ID | KnowledgeUnit | Тип | Суть | Практический смысл |` (Суть = col 3). Без этого
    новые батчи парсились с claim = «Тип» (баг). Домен берётся из namespace-префикса ID
    (до первой точки) → включает домен-блокировку семантического дедупа (D4).
    """
    facts: list[dict[str, Any]] = []
    seen: set = set()
    claim_idx: int = 2          # fallback к старому формату, если заголовок не найден
    type_idx: int = 1
    unit_idx: int | None = None
    conditions_idx: int | None = 3
    links_idx: int | None = 4
    practical_idx: int | None = None
    causes_idx: int | None = None
    enables_idx: int | None = None
    requires_idx: int | None = None
    prevents_idx: int | None = None
    depends_idx: int | None = None
    evidence_idx: int | None = None
    rel_conf_idx: int | None = None
    header_width: int | None = None
    for line in text.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = split_markdown_table_row(line)
        if len(cells) < 3:
            continue
        low = [c.lower().strip("` ").strip() for c in cells]
        # строка-заголовок → запоминаем индексы колонок
        claim_header_idx = next(
            (i for i, cell in enumerate(low) if "суть" in cell),
            None,
        )
        if "id" in low and claim_header_idx is not None:
            header_width = len(cells)
            claim_idx = claim_header_idx
            type_idx = low.index("тип") if "тип" in low else 1
            unit_idx = low.index("knowledgeunit") if "knowledgeunit" in low else None
            conditions_idx = next(
                (i for i, cell in enumerate(low) if "услов" in cell or "границ" in cell),
                None,
            )
            links_idx = next(
                (i for i, cell in enumerate(low) if cell in {"связи", "links"}),
                None,
            )
            practical_idx = next(
                (i for i, cell in enumerate(low) if "практическ" in cell),
                None,
            )
            causes_idx = next((i for i, cell in enumerate(low) if cell == "causes"), None)
            enables_idx = next((i for i, cell in enumerate(low) if cell == "enables"), None)
            requires_idx = next((i for i, cell in enumerate(low) if cell == "requires"), None)
            prevents_idx = next((i for i, cell in enumerate(low) if cell == "prevents"), None)
            depends_idx = next(
                (i for i, cell in enumerate(low) if cell in {"dependson", "depends_on", "depends on"}),
                None,
            )
            evidence_idx = next((i for i, cell in enumerate(low) if cell == "evidence"), None)
            rel_conf_idx = next(
                (i for i, cell in enumerate(low) if cell in {"relationconfidence", "relation_confidence"}),
                None,
            )
            continue
        # строка-разделитель таблицы (---|---)
        if all(set(c) <= set("-: ") for c in cells if c):
            continue
        fid = cells[0].strip("` ").strip()
        if not fid or fid.lower() == "id" or set(fid) <= set("-: "):
            continue
        if not FACT_ID_RE.fullmatch(fid):
            logger.warning("Skipping malformed World Skills fact ID: %s", fid)
            continue
        ci = claim_idx if claim_idx < len(cells) else (2 if len(cells) > 2 else len(cells) - 1)
        overflow = header_width is not None and len(cells) > header_width
        # A raw `|` inside legacy prose is malformed Markdown. Preserve every token in
        # the claim rather than silently shifting conditions/practical text into columns.
        claim = " | ".join(cells[ci:]).strip() if overflow else cells[ci].strip()
        if len(claim) < 8 or fid in seen:
            continue
        seen.add(fid)
        ftype = cells[type_idx].strip() if type_idx < len(cells) else ""
        domain = fid.split(".")[0] if "." in fid else fid

        def _cell(idx: int | None) -> str:
            return cells[idx].strip() if idx is not None and idx < len(cells) else ""

        facts.append({
            "fact_id": fid,
            "knowledge_unit": _cell(unit_idx),
            "type": ftype,
            "claim": claim,
            "conditions": "" if overflow else _cell(conditions_idx),
            "links": "" if overflow else _cell(links_idx),
            "practical": "" if overflow else _cell(practical_idx),
            "causes": "" if overflow else _cell(causes_idx),
            "enables": "" if overflow else _cell(enables_idx),
            "requires": "" if overflow else _cell(requires_idx),
            "prevents": "" if overflow else _cell(prevents_idx),
            "depends_on": "" if overflow else _cell(depends_idx),
            "evidence": "" if overflow else _cell(evidence_idx),
            "relation_confidence": "" if overflow else _cell(rel_conf_idx),
            "source": f"wsc:{ftype or 'unknown'}",   # контракт source неизменён
            "confidence": 0.85,
            "metadata": {
                "domain": domain,
                "type": ftype,
                "table_overflow_repaired": overflow,
            },
        })
    return facts


def parse_batch_file(path: str) -> list[dict[str, Any]]:
    with open(path, encoding="utf-8") as fh:
        facts = parse_batch_markdown(fh.read())
    filename = os.path.basename(path)
    upper_name = filename.upper()
    practical_domain = any(
        marker in upper_name
        for marker in ("_OPS", "_OPERATIONS", "_PRACTICAL", "_MAINTENANCE", "_REPAIR")
    )
    for fact in facts:
        metadata = fact.setdefault("metadata", {})
        metadata["knowledge_file"] = filename
        metadata["practical_domain"] = practical_domain
    return facts


def parse_knowledge_dir(knowledge_dir: str = DEFAULT_KNOWLEDGE_DIR) -> list[dict[str, Any]]:
    """Распарсить все fact-таблицы каталога (`*.ru.md`, кроме карт/охвата/протокола).

    Раньше фильтр был `*BATCH*` — он молча выбрасывал seed-паки 01–09 (~540 единиц
    самой структурированной науки). Теперь грузим все таблицы, исключая `_NON_FACT_FILES`.
    """
    facts: list[dict[str, Any]] = []
    seen: set = set()
    for path in sorted(glob.glob(os.path.join(knowledge_dir, "*.ru.md"))):
        if os.path.basename(path) in _NON_FACT_FILES:
            continue
        for f in parse_batch_file(path):
            if f["fact_id"] not in seen:
                seen.add(f["fact_id"])
                facts.append(f)
    return facts


def ingest_facts(store: Any, facts: Sequence[dict[str, Any]], validate: bool = True) -> dict[str, int]:
    """
    Загрузить факты в store. Курируемые знания → сразу Validated (через матрицу ESM:
    Observed→Validated легально). No-DELETE.
    """
    rep = {"parsed": len(facts), "ingested": 0, "validated": 0, "errors": 0}
    if not facts:
        return rep

    payload = [{
        "fact_id": f["fact_id"], "claim": f["claim"],
        "source": f["source"], "confidence": f.get("confidence", 0.85),
        "metadata": f.get("metadata", {}),   # domain → блокировка семантического дедупа (D4)
        # Curated World Skills rows are external world claims. Declare this
        # before canonical admission instead of writing UNKNOWN and repairing
        # the classification later with raw SQL.
        "claim_type": "WORLD_FACT",
        "origin_type": "EXTERNAL",
        "memory_type": "semantic",
    } for f in facts]

    # PERF (audit P-4): один коннект на весь батч вместо per-fact store_fact
    # (per-op connection давал ~1.76с/факт). store_facts_batch = одна транзакция.
    try:
        bstats = store.store_facts_batch(payload)
        rep["ingested"] = int(bstats.get("stored", 0)) + int(bstats.get("updated", 0))
        rep["errors"] += int(bstats.get("errors", 0))
    except Exception as exc:  # noqa: BLE001 — fallback на per-fact, если batch недоступен
        logger.debug("store_facts_batch failed (%s) → per-fact", exc)
        for p in payload:
            try:
                if store.store_fact(p):
                    rep["ingested"] += 1
                else:
                    rep["errors"] += 1
            except Exception:  # noqa: BLE001
                rep["errors"] += 1

    if validate:
        for f in facts:
            try:
                if store.promote_to_validated(f["fact_id"], by="world_skills_ingest"):
                    rep["validated"] += 1
            except Exception as exc:  # noqa: BLE001
                logger.debug("validate %s: %s", f.get("fact_id"), exc)
                rep["errors"] += 1
    return rep


def ingest_world_skills(
    store: Any,
    knowledge_dir: str = DEFAULT_KNOWLEDGE_DIR,
    validate: bool = True,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Полный ingest: парсинг каталога → загрузка в store → типизированные рёбра (knowledge_linker).
    Возвращает (report, facts, edges). Рёбра НЕ пишутся в store здесь — отдаются для CausalGraph/Essence.
    """
    facts = parse_knowledge_dir(knowledge_dir)
    rep = ingest_facts(store, facts, validate=validate)
    try:
        from core.knowledge_linker import link_facts
        edges = link_facts(facts)
    except Exception as exc:  # noqa: BLE001
        logger.debug("link_facts: %s", exc)
        edges = []
    rep["edges"] = len(edges)
    return rep, facts, edges


__all__ = [
    "DEFAULT_KNOWLEDGE_DIR",
    "ingest_facts",
    "ingest_world_skills",
    "parse_batch_file",
    "parse_batch_markdown",
    "parse_knowledge_dir",
    "split_markdown_table_row",
]
