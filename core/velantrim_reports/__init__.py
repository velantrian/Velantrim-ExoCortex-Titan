"""
📑 Velantrim Reports v1.0 — Готовые шаблоны отчётов
====================================================

Модуль готовых шаблонов для типичных задач Velantrim:
- MHI dashboard
- TruthGate audit
- Knowledge Base export
- Sprint Review

Все функции возвращают GenerationSpec — готовый к экспорту через FileExporter.

Использование:
    from core.velantrim_reports import (
        generate_mhi_report,
        generate_truthgate_audit,
        generate_knowledge_base,
        generate_sprint_review,
    )
    from core.file_generators import FileExporter

    # MHI отчёт
    spec = generate_mhi_report(mhi_report)
    FileExporter().export(spec, "mhi.pdf")

    # TruthGate аудит
    spec = generate_truthgate_audit(verdicts)
    FileExporter().export_multi(spec, "audit", formats=["pdf", "html", "docx"])

    # Knowledge Base
    spec = generate_knowledge_base(validated_facts)
    FileExporter().export(spec, "kb.epub")

    # Sprint Review
    spec = generate_sprint_review(sprint_data, format_hint="pptx")
    FileExporter().export(spec, "sprint_review.pptx")
"""

from .knowledge_base import generate_knowledge_base
from .mhi_report import generate_mhi_report
from .sprint_review import generate_sprint_review
from .truthgate_report import generate_truthgate_audit

__all__ = [
    "generate_mhi_report",
    "generate_truthgate_audit",
    "generate_knowledge_base",
    "generate_sprint_review",
]

__version__ = "1.0.0"
