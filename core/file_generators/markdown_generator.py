"""
📋 Markdown Generator v1.0 — Plain Markdown
=============================================
Без зависимостей. Чистый Python.

Используется когда нужен Markdown для GitHub, документации, конвертации.
"""

import logging
import time

from .base import (
    Block,
    CalloutBlock,
    CodeBlock,
    DividerBlock,
    FactBlock,
    FileGenerator,
    GenerationResult,
    GenerationSpec,
    HeadingBlock,
    ImageBlock,
    ListBlock,
    ParagraphBlock,
    QuoteBlock,
    TableBlock,
)

logger = logging.getLogger("velantrim.generators.markdown")


class MarkdownGenerator(FileGenerator):
    format_name = "markdown"

    def supported_extensions(self) -> list[str]:
        return [".md", ".markdown"]

    def generate(
        self,
        spec: GenerationSpec,
        output_path: str,
    ) -> GenerationResult:
        result = GenerationResult(output_path=output_path, format="markdown")
        start = time.time()
        self._ensure_output_dir(output_path)

        try:
            content = self._render(spec)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)
            result.method = "native"
            result.block_count = len(spec.blocks)
            result.file_size_bytes = self._file_size(output_path)
            result.metadata = self._build_provenance(output_path)
        except Exception as exc:
            logger.error(f"Markdown generation error: {exc}")
            result.error = str(exc)

        result.generation_time_ms = (time.time() - start) * 1000
        return result

    def _render(self, spec: GenerationSpec) -> str:
        # YAML frontmatter с метаданными
        lines: list[str] = []
        lines.append("---")
        lines.append(f"title: {spec.metadata.title}")
        lines.append(f"author: {spec.metadata.author}")
        if spec.metadata.subject:
            lines.append(f"subject: {spec.metadata.subject}")
        if spec.metadata.keywords:
            lines.append(f"keywords: [{', '.join(spec.metadata.keywords)}]")
        if spec.metadata.created:
            lines.append(f"date: {spec.metadata.created}")
        lines.append(f"theme: {spec.theme}")
        lines.append("---")
        lines.append("")
        lines.append(f"# {spec.metadata.title}")
        lines.append("")

        for block in spec.blocks:
            rendered = self._render_block(block)
            if rendered:
                lines.append(rendered)
                lines.append("")

        return "\n".join(lines)

    def _render_block(self, block: Block) -> str:
        if isinstance(block, HeadingBlock):
            return f"{'#' * min(block.level, 6)} {block.text}"

        if isinstance(block, ParagraphBlock):
            if block.style == "bold":
                return f"**{block.text}**"
            if block.style == "italic":
                return f"*{block.text}*"
            if block.style == "callout":
                return f"> {block.text}"
            return block.text

        if isinstance(block, ListBlock):
            return "\n".join(
                f"{i+1}. {item}" if block.ordered else f"- {item}"
                for i, item in enumerate(block.items)
            )

        if isinstance(block, TableBlock):
            return self._render_table(block)

        if isinstance(block, CodeBlock):
            caption = f"\n*{block.caption}*" if block.caption else ""
            return f"```{block.language}\n{block.code}\n```{caption}"

        if isinstance(block, ImageBlock):
            alt = block.caption or "image"
            return f"![{alt}]({block.path})"

        if isinstance(block, CalloutBlock):
            emoji = {"info": "ℹ️", "success": "✅", "warning": "⚠️", "danger": "🚨"}.get(
                block.callout_type, "ℹ️"
            )
            title = f"**{emoji} {block.title}**\n> " if block.title else f"**{emoji}**\n> "
            return f"> {title}{block.text}"

        if isinstance(block, QuoteBlock):
            author = f"\n> — *{block.author}*" if block.author else ""
            return f"> {block.text}{author}"

        if isinstance(block, DividerBlock):
            return "---"

        if isinstance(block, FactBlock):
            conf_label = self._confidence_to_label(block.confidence)
            return (
                f"### 🔱 {block.claim}\n"
                f"- **ID:** `{block.fact_id}`\n"
                f"- **Состояние:** {block.epistemic_state}\n"
                f"- **Уверенность:** {block.confidence:.3f} {conf_label}\n"
                f"- **Источник:** {block.source}"
            )

        return ""

    @staticmethod
    def _render_table(block: TableBlock) -> str:
        if not block.headers and not block.rows:
            return ""
        lines: list[str] = []
        if block.headers:
            lines.append("| " + " | ".join(str(h) for h in block.headers) + " |")
            lines.append("| " + " | ".join(["---"] * len(block.headers)) + " |")
        for row in block.rows:
            lines.append("| " + " | ".join(
                str(c) if c is not None else "" for c in row
            ) + " |")
        if block.caption:
            lines.append("")
            lines.append(f"*{block.caption}*")
        return "\n".join(lines)
