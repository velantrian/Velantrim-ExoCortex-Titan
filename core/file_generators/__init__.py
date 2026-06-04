"""
🎨 Velantrim File Generators v1.0 — Создание красивых документов
==================================================================

Зеркальный модуль для core/file_parsers/, но в обратном направлении:
    facts → GenerationSpec → красиво оформленный файл

Поддерживаемые форматы:
    📄 PDF       — ReportLab (отчёты, документы)
    📝 DOCX      — python-docx (Word документы)
    🎯 PPTX      — python-pptx (PowerPoint презентации)
    📊 XLSX      — openpyxl (Excel таблицы с conditional formatting)
    🌐 HTML      — native (standalone HTML5 с inline CSS)
    📋 Markdown  — native (GitHub-flavored)
    🔄 EPUB/LaTeX/RST/etc — pandoc (40+ форматов)

Темы оформления:
    clean      — Светлая, минимализм (default)
    scientific — Академический Times-Roman, синий
    business   — Строгий чёрно-оранжевый
    dark       — Тёмная для презентаций
    velantrim  — Фирменная cyan + indigo

Использование:
    from core.file_generators import FileExporter, GenerationSpec, HeadingBlock

    exporter = FileExporter()

    # Из готовой спецификации
    spec = GenerationSpec(
        metadata=DocumentMetadata(title="Отчёт"),
        theme="velantrim",
        blocks=[
            HeadingBlock(text="Анализ", level=1),
            ParagraphBlock(text="Введение..."),
        ]
    )
    result = exporter.export(spec, "report.pdf")

    # Shortcut для фактов
    facts = [{"fact_id": "f1", "claim": "...", "confidence": 0.9,
              "epistemic_state": "Validated", "source": "..."}]
    exporter.export_facts(facts, "facts.docx", theme="velantrim")

    # Несколько форматов сразу
    exporter.export_multi(spec, "/output/report", ["pdf", "docx", "html"])
"""

from .base import (
    THEMES,
    # Блоки
    Block,
    CalloutBlock,
    CodeBlock,
    DividerBlock,
    DocumentMetadata,
    FactBlock,
    FileGenerator,
    GenerationResult,
    GenerationSpec,
    GeneratorRegistry,
    HeadingBlock,
    ImageBlock,
    ListBlock,
    ParagraphBlock,
    QuoteBlock,
    TableBlock,
    Theme,
    get_theme,
)
from .file_exporter import FileExporter

__all__ = [
    "FileExporter",
    "GenerationSpec",
    "GenerationResult",
    "GeneratorRegistry",
    "DocumentMetadata",
    "Theme",
    "THEMES",
    "get_theme",
    "FileGenerator",
    "Block",
    "HeadingBlock",
    "ParagraphBlock",
    "ListBlock",
    "TableBlock",
    "CodeBlock",
    "ImageBlock",
    "CalloutBlock",
    "QuoteBlock",
    "DividerBlock",
    "FactBlock",
]

__version__ = "1.0.0"
