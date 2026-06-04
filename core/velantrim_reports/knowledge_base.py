"""
📖 Knowledge Base Export
==========================
Экспорт всех Validated/ImmutableCore фактов в формате книги знаний.

Использование:
    from core.velantrim_reports import generate_knowledge_base
    from core.memory import get_all_facts
    from core.file_generators import FileExporter

    validated = get_all_facts(epistemic_state="Validated")
    spec = generate_knowledge_base(validated)

    # В разных форматах:
    FileExporter().export(spec, "kb.epub")     # → книга для e-reader'а
    FileExporter().export(spec, "kb.pdf")      # → PDF
    FileExporter().export(spec, "kb.docx")     # → редактируемый Word
    FileExporter().export(spec, "kb.html")     # → веб-версия
"""

from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

from core.file_generators import (
    CalloutBlock,
    DividerBlock,
    DocumentMetadata,
    FactBlock,
    GenerationSpec,
    HeadingBlock,
    ParagraphBlock,
    QuoteBlock,
    TableBlock,
)


def generate_knowledge_base(
    facts: list[dict[str, Any]],
    theme: str = "scientific",
    group_by: str = "source",
    title: str = "Velantrim Knowledge Base",
    include_index: bool = True,
) -> GenerationSpec:
    """
    Сгенерировать книгу знаний из фактов.

    Args:
        facts: список фактов (dict с fact_id, claim, confidence, source, epistemic_state)
        theme: тема оформления (scientific — для академического вида)
        group_by: "source" | "epistemic_state" | "confidence_band" | "none"
        title: название книги
        include_index: добавить вступительный индекс (статистику)

    Returns:
        GenerationSpec
    """
    n = len(facts)

    # ─── Введение ───
    blocks: list = [
        QuoteBlock(
            text="Память без верификации — это просто хранение. "
                 "Верификация без памяти — это просто проверка. "
                 "Velantrim объединяет одно с другим.",
            author="Velantrim ExoCortex",
        ),
        DividerBlock(),
        ParagraphBlock(
            text=f"Эта база содержит {n} верифицированных фактов из памяти "
                 f"Velantrim ExoCortex. Каждый факт прошёл TruthGate и имеет "
                 f"явный жизненный цикл (ESM), источник, уверенность и provenance.",
        ),
    ]

    if include_index:
        # Статистика
        states: dict[str, int] = defaultdict(int)
        sources: dict[str, int] = defaultdict(int)
        confidences: list[float] = []

        for f in facts:
            states[f.get("epistemic_state", "Observed")] += 1
            sources[f.get("source", "unknown")] += 1
            confidences.append(f.get("confidence", 0.0))

        avg_conf = sum(confidences) / len(confidences) if confidences else 0

        blocks.extend([
            CalloutBlock(
                callout_type="info",
                title="📊 Сводка",
                text=(
                    f"Всего фактов: {n}. "
                    f"Средняя уверенность: {avg_conf:.3f}. "
                    f"Источников: {len(sources)}. "
                    f"Состояний: {len(states)}."
                ),
            ),
            HeadingBlock(text="Распределение по состояниям", level=2),
            TableBlock(
                headers=["Epistemic State", "Количество", "%"],
                rows=[
                    [state, str(count), f"{count / n * 100:.1f}%"]
                    for state, count in sorted(states.items(), key=lambda x: -x[1])
                ],
            ),
            DividerBlock(),
        ])

    # ─── Группировка ───
    if group_by == "source":
        groups: dict[str, list] = defaultdict(list)
        for f in facts:
            groups[f.get("source", "unknown")].append(f)
        group_emoji = "📂"
    elif group_by == "epistemic_state":
        groups = defaultdict(list)
        for f in facts:
            groups[f.get("epistemic_state", "Observed")].append(f)
        group_emoji = "🔵"
    elif group_by == "confidence_band":
        groups = defaultdict(list)
        for f in facts:
            c = f.get("confidence", 0)
            if c >= 0.9:
                band = "🟢 Высокая (≥0.9)"
            elif c >= 0.7:
                band = "🟡 Средняя (0.7–0.9)"
            elif c >= 0.5:
                band = "🟠 Низкая (0.5–0.7)"
            else:
                band = "🔴 Очень низкая (<0.5)"
            groups[band].append(f)
        group_emoji = "📊"
    else:
        groups = {"Все факты": facts}
        group_emoji = "📚"

    # ─── Рендеринг по группам ───
    for group_name, group_facts in sorted(groups.items()):
        blocks.append(HeadingBlock(
            text=f"{group_emoji} {group_name} ({len(group_facts)})",
            level=1,
        ))
        for fact in sorted(group_facts, key=lambda f: -f.get("confidence", 0)):
            blocks.append(FactBlock(
                fact_id=fact.get("fact_id", ""),
                claim=fact.get("claim", ""),
                confidence=fact.get("confidence", 0.0),
                epistemic_state=fact.get("epistemic_state", "Observed"),
                source=fact.get("source", ""),
            ))

    # ─── Footer ───
    blocks.append(DividerBlock())
    blocks.append(ParagraphBlock(
        text=f"Сгенерировано {datetime.now(UTC).strftime('%d.%m.%Y %H:%M')} UTC "
             "автоматически из памяти Velantrim ExoCortex.",
        style="callout",
    ))

    return GenerationSpec(
        metadata=DocumentMetadata(
            title=title,
            author="Velantrim ExoCortex",
            subject=f"Knowledge base of {n} verified facts",
            keywords=["knowledge", "facts", "verified", "esm"],
            description=f"Compendium of {n} validated facts",
            created=datetime.now(UTC).isoformat(),
        ),
        theme=theme,
        blocks=blocks,
    )
