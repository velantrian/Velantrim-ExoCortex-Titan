#!/usr/bin/env python3
"""
🎨 Velantrim File Exporter v1.0 — Главный оркестратор
=======================================================
Единая точка для генерации файлов из GenerationSpec.

Зеркальный API парсера:
    FileIngester.ingest(path)       → ParseResult
    FileExporter.export(spec, path) → GenerationResult

Использование:
    exporter = FileExporter()

    # Из готовой спецификации
    spec = GenerationSpec(...)
    result = exporter.export(spec, "/output/report.pdf")

    # Из списка фактов (удобный shortcut)
    facts = [{"fact_id": "f1", "claim": "Земля круглая", "confidence": 0.99,
              "epistemic_state": "Validated", "source": "physics"}]
    exporter.export_facts(facts, "/output/report.pdf",
                          title="Отчёт", theme="velantrim")

    # Несколько форматов сразу
    exporter.export_multi(spec, "/output/report",
                          formats=["pdf", "docx", "html"])
"""

import logging
import os
from pathlib import Path
from typing import Any

from .base import (
    GenerationResult,
    GenerationSpec,
    GeneratorRegistry,
)

logger = logging.getLogger("velantrim.file_exporter")


def _register_default_generators(registry: GeneratorRegistry) -> None:
    """
    Регистрирует все встроенные генераторы.
    Можно отключать через ENV: VELANTRIM_DISABLE_GENERATORS=pdf,docx
    """
    disabled = set(
        g.strip().lower()
        for g in os.getenv("VELANTRIM_DISABLE_GENERATORS", "").split(",")
        if g.strip()
    )

    if "pdf" not in disabled:
        from .pdf_generator import PDFGenerator
        registry.register("pdf", PDFGenerator, [".pdf"])

    if "docx" not in disabled:
        from .docx_generator import DOCXGenerator
        registry.register("docx", DOCXGenerator, [".docx"])

    if "pptx" not in disabled:
        from .pptx_generator import PPTXGenerator
        registry.register("pptx", PPTXGenerator, [".pptx"])

    if "xlsx" not in disabled:
        from .xlsx_generator import XLSXGenerator
        registry.register("xlsx", XLSXGenerator, [".xlsx"])

    if "html" not in disabled:
        from .html_generator import HTMLGenerator
        registry.register("html", HTMLGenerator, [".html", ".htm"])

    if "markdown" not in disabled:
        from .markdown_generator import MarkdownGenerator
        registry.register("markdown", MarkdownGenerator, [".md", ".markdown"])

    # Universal через pandoc — для редких форматов (.epub, .latex, .rst, .org)
    if "universal" not in disabled:
        from .universal_generator import UniversalGenerator
        registry.register("universal", UniversalGenerator, [
            ".epub", ".latex", ".tex", ".rst", ".org",
            ".mediawiki", ".dokuwiki", ".asciidoc", ".adoc",
            ".odt", ".rtf", ".typ",
        ])


class FileExporter:
    """
    Главный оркестратор экспорта файлов.

    Зеркало FileIngester для парсера.
    """

    def __init__(self) -> None:
        self.registry = GeneratorRegistry()
        _register_default_generators(self.registry)
        self._stats: dict[str, Any] = {
            "generated": 0,
            "errors": 0,
            "by_format": {},
            "total_bytes": 0,
            "total_time_ms": 0.0,
        }

    # ─── Главные методы ───────────────────────────────────────────────────────

    def export(
        self,
        spec: GenerationSpec,
        output_path: str,
    ) -> GenerationResult:
        """
        Генерирует файл из спецификации. Формат определяется по расширению.

        Args:
            spec: спецификация документа
            output_path: путь к выходному файлу (расширение определяет формат)

        Returns:
            GenerationResult с информацией о результате
        """
        ext = Path(output_path).suffix.lower()
        generator = self.registry.get_generator_for(ext)
        if generator is None:
            return GenerationResult(
                output_path=output_path,
                format="unknown",
                error=f"Нет генератора для типа: {ext}. "
                      f"Доступны: {self.registry.supported_extensions()}",
            )

        logger.info(
            f"🎨 Generating: {output_path} → {generator.__class__.__name__}"
        )
        try:
            result = generator.generate(spec, output_path)
            self._update_stats(result)
            return result
        except Exception as exc:
            logger.error(f"Generation failed: {exc}")
            self._stats["errors"] += 1
            return GenerationResult(
                output_path=output_path,
                format=generator.format_name,
                error=str(exc),
            )

    def export_facts(
        self,
        facts: list[dict[str, Any]],
        output_path: str,
        title: str = "Velantrim Facts Report",
        theme: str = "velantrim",
        author: str = "Velantrim ExoCortex",
        include_metadata: bool = True,
    ) -> GenerationResult:
        """
        Удобный shortcut: список фактов → готовый документ.

        Использование:
            from core.memory import get_all_facts
            facts = get_all_facts(epistemic_state="Validated")
            exporter.export_facts(facts, "validated_facts.pdf")
        """
        spec = GenerationSpec.from_facts(
            facts=facts,
            title=title,
            theme=theme,
            include_metadata=include_metadata,
        )
        spec.metadata.author = author
        return self.export(spec, output_path)

    def export_multi(
        self,
        spec: GenerationSpec,
        output_base: str,
        formats: list[str],
    ) -> dict[str, GenerationResult]:
        """
        Генерирует один документ в нескольких форматах сразу.

        Args:
            spec: единая спецификация
            output_base: базовый путь без расширения, например "/out/report"
            formats: ["pdf", "docx", "html"] — список расширений

        Returns:
            {format: GenerationResult}

        Пример:
            results = exporter.export_multi(
                spec, "/out/report",
                formats=["pdf", "docx", "html", "md"]
            )
            # → /out/report.pdf, /out/report.docx, /out/report.html, /out/report.md
        """
        results: dict[str, GenerationResult] = {}
        for fmt in formats:
            ext = fmt if fmt.startswith(".") else f".{fmt}"
            output_path = f"{output_base}{ext}"
            results[fmt] = self.export(spec, output_path)
        return results

    # ─── Информация о возможностях ────────────────────────────────────────────

    def get_supported_formats(self) -> list[str]:
        """Все поддерживаемые расширения."""
        return self.registry.supported_extensions()

    def get_stats(self) -> dict[str, Any]:
        """Статистика генератора."""
        return dict(self._stats)

    # ─── Internal ─────────────────────────────────────────────────────────────

    def _update_stats(self, result: GenerationResult) -> None:
        self._stats["generated"] += 1
        self._stats["total_bytes"] += result.file_size_bytes
        self._stats["total_time_ms"] += result.generation_time_ms
        fmt = result.format
        self._stats["by_format"][fmt] = self._stats["by_format"].get(fmt, 0) + 1
        if result.error:
            self._stats["errors"] += 1


# ─── CLI для теста ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    exporter = FileExporter()
    print("🦋 Velantrim File Exporter v1.0 — поддерживаемые форматы:")
    for ext in exporter.get_supported_formats():
        print(f"  {ext}")
    print()

    # Демо: генерируем sample report
    if len(sys.argv) > 1:
        output_path = sys.argv[1]
        sample_facts = [
            {
                "fact_id": "f1",
                "claim": "Земля имеет форму геоида (приближённо сферы)",
                "confidence": 0.999,
                "source": "physics:NASA",
                "epistemic_state": "Validated",
            },
            {
                "fact_id": "f2",
                "claim": "Скорость света в вакууме — 299 792 458 м/с",
                "confidence": 1.0,
                "source": "physics:CODATA",
                "epistemic_state": "ImmutableCore",
            },
            {
                "fact_id": "f3",
                "claim": "AI достигнет AGI в ближайшие 10 лет",
                "confidence": 0.42,
                "source": "speculation:user",
                "epistemic_state": "Hypothesized",
            },
        ]
        result = exporter.export_facts(
            sample_facts,
            output_path,
            title="🔱 Демо отчёта Velantrim ExoCortex",
            theme="velantrim",
        )
        if result.error:
            print(f"❌ Ошибка: {result.error}")
        else:
            print(f"✅ Создан: {result.output_path}")
            print(f"   Формат: {result.format}")
            print(f"   Метод:  {result.method}")
            print(f"   Размер: {result.file_size_bytes / 1024:.1f} KB")
            print(f"   Время:  {result.generation_time_ms:.0f}ms")
            if result.page_count:
                print(f"   Страниц: {result.page_count}")
    else:
        print("Использование: python file_exporter.py <output.pdf|docx|pptx|xlsx|html|md>")
