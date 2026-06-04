"""
🚀 Sprint Review Report
=========================
Готовый шаблон отчёта о спринте.

Использование:
    from core.velantrim_reports import generate_sprint_review

    sprint_data = {
        "number": "2a",
        "name": "Audit fixes",
        "team": "Velantrim Core",
        "goal": "Закрыть 7 критических интеграционных багов из аудита",
        "delivered": [
            {"title": "SleepTimeWorker startup fix", "type": "bug"},
            {"title": "NGram split resolved", "type": "bug"},
        ],
        "metrics": [
            ["Тестов", 256, 266, "+10"],
            ["Coverage", "86%", "87%", "+1%"],
        ],
        "carryover": ["Real LLM in pipeline.generate_answer"],
        "next_goals": ["Sprint 2b: реальный LLM integration"],
    }

    spec = generate_sprint_review(sprint_data)
    FileExporter().export(spec, "sprint_review.pptx")  # для презентации
"""

from datetime import UTC, datetime
from typing import Any

from core.file_generators import (
    CalloutBlock,
    DividerBlock,
    DocumentMetadata,
    FactBlock,
    GenerationSpec,
    HeadingBlock,
    ListBlock,
    TableBlock,
)


def generate_sprint_review(
    sprint: dict[str, Any],
    theme: str = "velantrim",
    format_hint: str = "pptx",
) -> GenerationSpec:
    """
    Сгенерировать GenerationSpec для sprint review.

    Args:
        sprint: dict с ключами number, name, team, goal, delivered,
                metrics, carryover, next_goals
        theme: имя темы
        format_hint: "pptx" для презентации (короче, каждый элемент на слайде)
                     или "docx"/"pdf" для документа (длиннее, плотнее)

    Returns:
        GenerationSpec
    """
    is_presentation = format_hint == "pptx"

    blocks: list = []

    # ─── Цель ───
    blocks.append(HeadingBlock(
        text=f"🎯 Цель Sprint {sprint.get('number', '?')}",
        level=1,
    ))
    blocks.append(CalloutBlock(
        callout_type="info",
        title=sprint.get("name", "Sprint review"),
        text=sprint.get("goal", "—"),
    ))

    # ─── Что доставили ───
    delivered = sprint.get("delivered", [])
    if delivered:
        blocks.append(HeadingBlock(text=f"✅ Доставили ({len(delivered)})", level=1))
        if is_presentation:
            # Для презентации — каждый item как FactBlock (отдельный слайд)
            for item in delivered:
                if isinstance(item, dict):
                    blocks.append(FactBlock(
                        fact_id=f"sprint_{sprint.get('number')}_delivery_{delivered.index(item)}",
                        claim=item.get("title", str(item)),
                        confidence=1.0,
                        epistemic_state="Validated",
                        source=item.get("type", "delivery"),
                    ))
                else:
                    blocks.append(FactBlock(
                        fact_id=f"sprint_{sprint.get('number')}_delivery_{delivered.index(item)}",
                        claim=str(item),
                        confidence=1.0,
                        epistemic_state="Validated",
                        source="sprint_delivery",
                    ))
        else:
            # Для документа — компактный список
            blocks.append(ListBlock(
                items=[
                    (item.get("title", str(item)) if isinstance(item, dict) else str(item))
                    for item in delivered
                ],
            ))

    # ─── Метрики ───
    metrics = sprint.get("metrics", [])
    if metrics:
        blocks.append(HeadingBlock(text="📊 Метрики", level=1))
        blocks.append(TableBlock(
            headers=["Метрика", "Было", "Стало", "Δ"],
            rows=metrics,
            caption="Изменения за спринт",
        ))

    # ─── Что не успели ───
    carryover = sprint.get("carryover", [])
    if carryover:
        blocks.append(HeadingBlock(text="⏰ Перенесли", level=1))
        blocks.append(CalloutBlock(
            callout_type="warning",
            title="Carryover в следующий спринт",
            text=f"{len(carryover)} элементов",
        ))
        blocks.append(ListBlock(items=carryover))

    # ─── Lessons learned ───
    lessons = sprint.get("lessons", [])
    if lessons:
        blocks.append(HeadingBlock(text="💡 Уроки", level=1))
        for lesson in lessons:
            blocks.append(CalloutBlock(
                callout_type="info",
                title="Lesson learned",
                text=lesson,
            ))

    # ─── Следующий спринт ───
    next_goals = sprint.get("next_goals", [])
    if next_goals:
        blocks.append(DividerBlock())
        blocks.append(HeadingBlock(text="🚀 Следующий спринт", level=1))
        blocks.append(CalloutBlock(
            callout_type="success",
            title=f"Sprint {sprint.get('next_number', '?')}",
            text=sprint.get("next_name", "Следующая итерация"),
        ))
        blocks.append(ListBlock(items=next_goals))

    return GenerationSpec(
        metadata=DocumentMetadata(
            title=f"🚀 Sprint {sprint.get('number', '?')} Review: {sprint.get('name', '')}",
            author=sprint.get("team", "Velantrim Core"),
            subject="Sprint review and retrospective",
            keywords=["sprint", "review", "agile"],
            created=datetime.now(UTC).isoformat(),
        ),
        theme=theme,
        blocks=blocks,
    )
