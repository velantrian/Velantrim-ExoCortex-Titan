"""
📊 MHI Dashboard Report
========================
Готовый шаблон отчёта о здоровье памяти Velantrim.

Использование:
    from core.velantrim_reports import generate_mhi_report
    from core.memory import _GLOBAL_STORE
    from core.mhi import MHICalculator
    from core.file_generators import FileExporter

    mhi = MHICalculator(_GLOBAL_STORE).calculate()
    spec = generate_mhi_report(mhi, theme="velantrim")

    FileExporter().export(spec, "reports/mhi_dashboard.pdf")
    # или сразу в несколько форматов:
    FileExporter().export_multi(spec, "reports/mhi_dashboard",
                                formats=["pdf", "html", "docx"])
"""

from datetime import UTC, datetime
from typing import Any

from core.file_generators import (
    CalloutBlock,
    DividerBlock,
    DocumentMetadata,
    GenerationSpec,
    HeadingBlock,
    ParagraphBlock,
    TableBlock,
)


def generate_mhi_report(
    mhi_report: Any,
    theme: str = "velantrim",
    include_history: bool = False,
) -> GenerationSpec:
    """
    Сгенерировать GenerationSpec для MHI dashboard.

    Args:
        mhi_report: объект MHIReport из core.mhi.MHICalculator.calculate()
        theme: имя темы оформления
        include_history: добавить ли историю MHI (если доступна)

    Returns:
        GenerationSpec готовый для FileExporter.export()
    """
    # Статус → эмодзи и тип callout
    status_str = (
        mhi_report.status.value if hasattr(mhi_report.status, "value")
        else str(mhi_report.status)
    )
    status_config = {
        "HEALTHY":   ("🟢", "success"),
        "DEGRADED":  ("🟡", "warning"),
        "SAFE_MODE": ("🔴", "danger"),
    }
    emoji, callout_type = status_config.get(status_str, ("⚪", "info"))

    blocks: list = [
        # Hero callout — главный показатель
        CalloutBlock(
            callout_type=callout_type,
            title=f"{emoji} {status_str}",
            text=f"MHI = {mhi_report.score:.3f}",
        ),
        DividerBlock(),

        # Компоненты MHI
        HeadingBlock(text="📐 Компоненты MHI", level=1),
        ParagraphBlock(
            text="MHI = 0.30 × validated + 0.25 × freshness + "
                 "0.25 × precision + 0.20 × graph",
            style="callout",
        ),
        TableBlock(
            headers=["Компонент", "Значение", "Вес", "Вклад"],
            rows=[
                [
                    "Validated Ratio",
                    f"{getattr(mhi_report, 'validated_ratio', 0):.3f}",
                    "30%",
                    f"{getattr(mhi_report, 'validated_ratio', 0) * 0.30:.3f}",
                ],
                [
                    "Freshness",
                    f"{getattr(mhi_report, 'freshness', 0):.3f}",
                    "25%",
                    f"{getattr(mhi_report, 'freshness', 0) * 0.25:.3f}",
                ],
                [
                    "Retrieval Precision",
                    f"{getattr(mhi_report, 'retrieval_precision', 0):.3f}",
                    "25%",
                    f"{getattr(mhi_report, 'retrieval_precision', 0) * 0.25:.3f}",
                ],
                [
                    "Graph Coverage",
                    f"{getattr(mhi_report, 'graph_coverage', 0):.3f}",
                    "20%",
                    f"{getattr(mhi_report, 'graph_coverage', 0) * 0.20:.3f}",
                ],
            ],
            caption="Разбивка вклада каждого компонента в итоговый MHI",
        ),
    ]

    # Пороги
    blocks.extend([
        HeadingBlock(text="🎯 Пороги SLO", level=2),
        TableBlock(
            headers=["Зона", "Порог", "Действие"],
            rows=[
                ["🟢 HEALTHY",  "≥ 0.60", "Норма — никаких действий"],
                ["🟡 DEGRADED легкий",  "0.50 – 0.60", "Мониторинг, плавная коррекция"],
                ["🟡 DEGRADED тяжёлый", "0.30 – 0.50", "Ускорить ConsolidationEngine"],
                ["🔴 SAFE_MODE", "< 0.30", "Немедленный GC + alert ops"],
            ],
            caption="Из INVARIANTS.md MHI-2 (v8.4.0)",
        ),
    ])

    # Рекомендации
    recs = getattr(mhi_report, "recommendations", []) or []
    if recs:
        blocks.append(DividerBlock())
        blocks.append(HeadingBlock(text="💡 Рекомендации", level=1))
        for rec in recs:
            blocks.append(ParagraphBlock(text=f"• {rec}"))

    # Дополнительная статистика
    extras = []
    for attr_name, label in [
        ("total_facts", "Всего фактов в памяти"),
        ("validated_count", "Validated фактов"),
        ("avg_age_days", "Средний возраст фактов (дни)"),
        ("active_contradictions", "Активных противоречий"),
    ]:
        val = getattr(mhi_report, attr_name, None)
        if val is not None:
            extras.append([label, str(val)])

    if extras:
        blocks.append(DividerBlock())
        blocks.append(HeadingBlock(text="📊 Дополнительная статистика", level=1))
        blocks.append(TableBlock(
            headers=["Метрика", "Значение"],
            rows=extras,
        ))

    return GenerationSpec(
        metadata=DocumentMetadata(
            title=f"📊 Memory Health Index — {datetime.now(UTC).strftime('%Y-%m-%d')}",
            author="Velantrim ExoCortex",
            subject=f"MHI = {mhi_report.score:.3f} ({status_str})",
            keywords=["mhi", "memory", "health", "audit"],
            created=datetime.now(UTC).isoformat(),
            description="Автоматический отчёт о здоровье памяти Velantrim",
        ),
        theme=theme,
        blocks=blocks,
    )
