"""
🛡️ TruthGate Audit Report
============================
Готовый шаблон отчёта об аудите TruthGate.

Использование:
    from core.velantrim_reports import generate_truthgate_audit
    from core.truth_gate import TruthGate, CognitiveMode

    # Прогон фактов через TruthGate
    gate = TruthGate(store)
    verdicts = [gate.evaluate(f, mode=CognitiveMode.BALANCED) for f in facts]

    spec = generate_truthgate_audit(verdicts)
    FileExporter().export(spec, "audit.pdf")
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
    ParagraphBlock,
    TableBlock,
)


def generate_truthgate_audit(
    verdicts: list[Any],
    theme: str = "scientific",
    show_passed: bool = True,
    show_rejected: bool = True,
    show_details: bool = True,
) -> GenerationSpec:
    """
    Сгенерировать GenerationSpec для аудита TruthGate.

    Args:
        verdicts: список TruthGateVerdict из core.truth_gate
        theme: имя темы (scientific — лучший вариант для аудита)
        show_passed: показать прошедшие факты
        show_rejected: показать отклонённые факты
        show_details: показать FactBlock для каждого отклонённого

    Returns:
        GenerationSpec
    """
    total = len(verdicts)
    passed = sum(1 for v in verdicts if getattr(v, "passed", False))
    rejected = total - passed

    pass_rate = (passed / total * 100) if total > 0 else 0

    # Hero summary
    if pass_rate >= 80:
        summary_type, summary_emoji = "success", "✅"
    elif pass_rate >= 50:
        summary_type, summary_emoji = "warning", "⚠️"
    else:
        summary_type, summary_emoji = "danger", "🚨"

    blocks: list = [
        CalloutBlock(
            callout_type=summary_type,
            title=f"{summary_emoji} Сводка аудита",
            text=(
                f"Проверено фактов: {total}. "
                f"Прошли TruthGate: {passed} ({pass_rate:.1f}%). "
                f"Отклонены: {rejected} ({100 - pass_rate:.1f}%)."
            ),
        ),
        DividerBlock(),
    ]

    # Распределение по причинам отклонения
    if rejected > 0:
        reasons: dict = {}
        for v in verdicts:
            if not getattr(v, "passed", False):
                reason = getattr(v, "reason", "unknown")
                reasons[reason] = reasons.get(reason, 0) + 1

        blocks.append(HeadingBlock(text="❌ Причины отклонения", level=1))
        blocks.append(TableBlock(
            headers=["Причина", "Количество", "%"],
            rows=[
                [reason, str(count), f"{count / rejected * 100:.1f}%"]
                for reason, count in sorted(
                    reasons.items(), key=lambda x: -x[1]
                )
            ],
            caption=f"Из {rejected} отклонённых фактов",
        ))

    # Распределение по режимам
    modes_used: dict = {}
    for v in verdicts:
        mode_obj = getattr(v, "mode", None)
        mode_name = (
            mode_obj.value if mode_obj is not None and hasattr(mode_obj, "value")
            else str(mode_obj or "unknown")
        )
        modes_used[mode_name] = modes_used.get(mode_name, 0) + 1

    if modes_used:
        blocks.append(HeadingBlock(text="🧠 Использованные режимы", level=2))
        blocks.append(TableBlock(
            headers=["Cognitive Mode", "Количество", "%"],
            rows=[
                [mode, str(count), f"{count / total * 100:.1f}%"]
                for mode, count in sorted(modes_used.items(), key=lambda x: -x[1])
            ],
        ))

    # Список вердиктов в виде таблицы
    blocks.append(DividerBlock())
    blocks.append(HeadingBlock(text="📋 Все вердикты", level=1))
    verdict_rows = []
    for v in verdicts:
        fact_id = getattr(v, "fact_id", "—")
        mode_obj = getattr(v, "mode", None)
        mode_str = (
            mode_obj.value if mode_obj is not None and hasattr(mode_obj, "value")
            else str(mode_obj or "—")
        )
        passed_v = getattr(v, "passed", False)
        verdict_str = "✅ Passed" if passed_v else "❌ Rejected"
        reason = getattr(v, "reason", "—") if not passed_v else "passed"
        verdict_rows.append([fact_id, mode_str, verdict_str, reason])

    blocks.append(TableBlock(
        headers=["Fact ID", "Mode", "Verdict", "Reason"],
        rows=verdict_rows,
        caption="Полный список TruthGate вердиктов",
    ))

    # Детали по отклонённым (FactBlock'и)
    if show_rejected and show_details and rejected > 0:
        blocks.append(DividerBlock())
        blocks.append(HeadingBlock(text="🔴 Отклонённые факты — подробности", level=1))
        blocks.append(ParagraphBlock(
            text="Эти факты НЕ прошли TruthGate и требуют ручной проверки "
                 "или дополнительных evidence.",
            style="callout",
        ))
        for v in verdicts:
            if not getattr(v, "passed", False):
                fact_data = getattr(v, "fact", None) or {}
                blocks.append(FactBlock(
                    fact_id=fact_data.get("fact_id", getattr(v, "fact_id", "—")),
                    claim=fact_data.get("claim", "—"),
                    confidence=fact_data.get("confidence", 0.0),
                    epistemic_state="Rejected",   # специальный псевдо-state
                    source=fact_data.get("source", "—"),
                ))
                # Reason ниже
                blocks.append(ParagraphBlock(
                    text=f"📌 Причина: {getattr(v, 'reason', '—')}. "
                         f"{getattr(v, 'justification', '')}",
                    style="callout",
                ))

    return GenerationSpec(
        metadata=DocumentMetadata(
            title=f"🛡️ TruthGate Audit Report — {datetime.now(UTC).strftime('%Y-%m-%d')}",
            author="Velantrim TruthGate",
            subject=f"Audit of {total} facts ({pass_rate:.1f}% passed)",
            keywords=["truthgate", "audit", "verification"],
            created=datetime.now(UTC).isoformat(),
        ),
        theme=theme,
        blocks=blocks,
    )
