"""
🔄 Universal Generator v1.0 — pypandoc wrapper
================================================
Конвертация между форматами через pandoc.

Поддерживает 40+ форматов: Markdown ↔ DOCX ↔ HTML ↔ PDF ↔ EPUB ↔ LaTeX ↔ ...

Стратегия:
1. Сначала рендерим GenerationSpec как Markdown через MarkdownGenerator
2. Затем конвертируем pandoc'ом в нужный формат

Это даёт нам:
- EPUB (электронные книги)
- LaTeX (для научных статей)
- RST (Sphinx документация)
- Org-mode (Emacs)
- Mediawiki / Dokuwiki
- Многое другое

Требует:
- pip install pypandoc
- Установленный pandoc в системе:
  - Ubuntu: sudo apt install pandoc
  - macOS: brew install pandoc
  - Windows: choco install pandoc
"""

import logging
import os
import tempfile
import time

from .base import (
    FileGenerator,
    GenerationResult,
    GenerationSpec,
)
from .markdown_generator import MarkdownGenerator

logger = logging.getLogger("velantrim.generators.universal")


def _check_available(module_name: str) -> bool:
    import importlib.util
    return importlib.util.find_spec(module_name) is not None


PYPANDOC_AVAILABLE = _check_available("pypandoc")


# Маппинг расширений → pandoc output format
PANDOC_FORMATS = {
    ".md": "markdown",
    ".markdown": "markdown",
    ".html": "html5",
    ".htm": "html5",
    ".docx": "docx",
    ".odt": "odt",
    ".rtf": "rtf",
    ".epub": "epub",
    ".pdf": "pdf",
    ".latex": "latex",
    ".tex": "latex",
    ".rst": "rst",
    ".org": "org",
    ".mediawiki": "mediawiki",
    ".dokuwiki": "dokuwiki",
    ".asciidoc": "asciidoc",
    ".adoc": "asciidoc",
    ".typ": "typst",
    ".txt": "plain",
}


class UniversalGenerator(FileGenerator):
    """
    Универсальный генератор через pandoc.

    Использует MarkdownGenerator как intermediate, потом конвертирует
    pandoc'ом в любой поддерживаемый формат.
    """

    format_name = "universal"

    def supported_extensions(self) -> list[str]:
        return list(PANDOC_FORMATS.keys())

    def generate(
        self,
        spec: GenerationSpec,
        output_path: str,
    ) -> GenerationResult:
        result = GenerationResult(output_path=output_path, format="universal")
        start = time.time()
        self._ensure_output_dir(output_path)

        if not PYPANDOC_AVAILABLE:
            result.error = (
                "pypandoc не установлен. pip install pypandoc + установи pandoc"
            )
            return result

        # Определяем target format по расширению
        ext = os.path.splitext(output_path)[1].lower()
        target_format = PANDOC_FORMATS.get(ext)
        if not target_format:
            result.error = f"Pandoc не поддерживает формат: {ext}"
            return result

        try:
            # Шаг 1: рендерим в Markdown (intermediate)
            md_generator = MarkdownGenerator()
            with tempfile.NamedTemporaryFile(
                suffix=".md", delete=False, mode="w", encoding="utf-8",
            ) as tmp:
                tmp_path = tmp.name

            md_result = md_generator.generate(spec, tmp_path)
            if md_result.error:
                result.error = f"Markdown intermediate failed: {md_result.error}"
                return result

            # Шаг 2: конвертируем pandoc'ом
            import pypandoc
            extra_args = self._get_extra_args(target_format, spec)
            pypandoc.convert_file(
                tmp_path,
                target_format,
                outputfile=output_path,
                extra_args=extra_args,
            )

            # Очистка временного файла
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

            result.method = f"pandoc → {target_format}"
            result.block_count = len(spec.blocks)
            result.file_size_bytes = self._file_size(output_path)
            result.metadata = self._build_provenance(output_path)

        except Exception as exc:
            logger.error(f"Universal generation error: {exc}")
            result.error = str(exc)

        result.generation_time_ms = (time.time() - start) * 1000
        return result

    @staticmethod
    def _get_extra_args(target_format: str, spec: GenerationSpec) -> list[str]:
        """Дополнительные аргументы pandoc под формат."""
        args = ["--standalone"]

        if target_format == "pdf":
            # Для PDF нужен LaTeX engine
            args += ["--pdf-engine=xelatex"]
            # Поддержка кириллицы
            args += ["-V", "mainfont=DejaVu Serif"]
            args += ["-V", "monofont=DejaVu Sans Mono"]

        if target_format == "epub":
            # Метаданные EPUB
            args += [
                "--metadata", f"title={spec.metadata.title}",
                "--metadata", f"author={spec.metadata.author}",
                "--metadata", f"lang={spec.metadata.language}",
            ]
            if spec.metadata.subject:
                args += ["--metadata", f"subject={spec.metadata.subject}"]

        if target_format == "html5":
            args += ["--self-contained"]  # inline CSS

        if target_format == "latex":
            args += ["-V", "documentclass=article"]
            args += ["-V", "geometry:margin=2cm"]

        # Общие
        if spec.metadata.title:
            args += ["--metadata", f"title={spec.metadata.title}"]

        return args
