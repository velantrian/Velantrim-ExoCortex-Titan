"""
📄 PDF Generator v1.0 — ReportLab + WeasyPrint
================================================
Генерация красивых PDF документов из GenerationSpec.

Стратегия:
- Primary: ReportLab (canvas + flowables) — точный контроль, без зависимостей от системы
- Alternative: WeasyPrint (HTML→PDF) — для сложных layout с CSS

ReportLab выбран как primary потому что:
- Работает без системных зависимостей (WeasyPrint требует Pango/Cairo)
- Точный контроль над каждым элементом
- Профессиональные шаблоны для отчётов
- Лидер по поддержке таблиц и графиков

Особенности:
- Семантические темы (clean/scientific/business/dark/velantrim)
- Header/footer с pagination
- TOC автоматический (через анкоры)
- Callout-блоки с цветовой кодировкой
- Поддержка кириллицы через встроенные шрифты
"""

import logging
import time

from .base import (
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
    get_theme,
)

logger = logging.getLogger("velantrim.generators.pdf")


def _check_available(module_name: str) -> bool:
    import importlib.util
    return importlib.util.find_spec(module_name) is not None


REPORTLAB_AVAILABLE = _check_available("reportlab")
WEASYPRINT_AVAILABLE = _check_available("weasyprint")


class PDFGenerator(FileGenerator):
    """Генератор PDF через ReportLab с темами."""

    format_name = "pdf"

    def supported_extensions(self) -> list[str]:
        return [".pdf"]

    def generate(
        self,
        spec: GenerationSpec,
        output_path: str,
    ) -> GenerationResult:
        result = GenerationResult(output_path=output_path, format="pdf")
        start = time.time()

        if not REPORTLAB_AVAILABLE:
            result.error = (
                "ReportLab не установлен. pip install reportlab"
            )
            return result

        self._ensure_output_dir(output_path)
        theme = get_theme(spec.theme)

        try:
            page_count = self._render_reportlab(spec, output_path, theme)
            result.method = "ReportLab"
            result.page_count = page_count
            result.block_count = len(spec.blocks)
            result.file_size_bytes = self._file_size(output_path)
            result.metadata = self._build_provenance(output_path)
        except Exception as exc:
            logger.error(f"PDF generation error: {exc}")
            result.error = str(exc)

        result.generation_time_ms = (time.time() - start) * 1000
        return result

    # ─── ReportLab implementation ─────────────────────────────────────────────

    def _render_reportlab(
        self,
        spec: GenerationSpec,
        output_path: str,
        theme,
    ) -> int:
        """Основной метод рендеринга через ReportLab."""
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_JUSTIFY
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import cm
        from reportlab.platypus import (
            HRFlowable,
            Paragraph,
            SimpleDocTemplate,
            Spacer,
        )

        # Конвертируем hex цвета в colors.HexColor
        c_primary = colors.HexColor(f"#{theme.primary}")
        c_secondary = colors.HexColor(f"#{theme.secondary}")
        c_accent = colors.HexColor(f"#{theme.accent}")
        c_text = colors.HexColor(f"#{theme.text}")
        c_muted = colors.HexColor(f"#{theme.text_muted}")
        c_bg = colors.HexColor(f"#{theme.background}")
        c_surface = colors.HexColor(f"#{theme.surface}")
        c_border = colors.HexColor(f"#{theme.border}")
        c_success = colors.HexColor(f"#{theme.success}")
        c_warning = colors.HexColor(f"#{theme.warning}")
        c_danger = colors.HexColor(f"#{theme.danger}")

        # ─── Стили параграфов под тему ───
        ss = getSampleStyleSheet()

        h1 = ParagraphStyle(
            "h1", parent=ss["Heading1"],
            fontName=theme.font_heading,
            fontSize=theme.size_3xl, textColor=c_primary,
            spaceAfter=theme.spacing_md, spaceBefore=theme.spacing_lg,
            leading=theme.size_3xl * 1.2,
        )
        h2 = ParagraphStyle(
            "h2", parent=ss["Heading2"],
            fontName=theme.font_heading,
            fontSize=theme.size_2xl, textColor=c_primary,
            spaceAfter=theme.spacing_sm, spaceBefore=theme.spacing_md,
            leading=theme.size_2xl * 1.2,
        )
        h3 = ParagraphStyle(
            "h3", parent=ss["Heading3"],
            fontName=theme.font_heading,
            fontSize=theme.size_xl, textColor=c_secondary,
            spaceAfter=theme.spacing_sm, spaceBefore=theme.spacing_sm,
            leading=theme.size_xl * 1.3,
        )
        body = ParagraphStyle(
            "body", parent=ss["BodyText"],
            fontName=theme.font_body,
            fontSize=theme.size_md, textColor=c_text,
            alignment=TA_JUSTIFY,
            spaceAfter=theme.spacing_sm,
            leading=theme.size_md * 1.5,
        )
        # FIX v8.5.2 (Claude audit): используем font_body_bold/italic если заданы
        # явно в Theme (как в THEME_SCIENTIFIC: "Times-Bold" вместо
        # несуществующего "Times-Roman-Bold"). Fallback на f"{font_body}-Bold"
        # сохраняет старое поведение для тем без явных вариантов (Helvetica и т.д.).
        _body_bold_font = theme.font_body_bold or f"{theme.font_body}-Bold"
        _body_italic_font = theme.font_body_italic or f"{theme.font_body}-Oblique"
        body_bold = ParagraphStyle(
            "body_bold", parent=body, fontName=_body_bold_font,
        )
        body_italic = ParagraphStyle(
            "body_italic", parent=body, fontName=_body_italic_font,
        )
        muted = ParagraphStyle(
            "muted", parent=body,
            fontSize=theme.size_sm, textColor=c_muted,
        )
        code_style = ParagraphStyle(
            "code", parent=body,
            fontName=theme.font_mono,
            fontSize=theme.size_sm,
            textColor=c_text,
            backColor=c_surface,
            borderColor=c_border, borderWidth=0.5, borderPadding=8,
            leading=theme.size_sm * 1.4,
        )
        quote_style = ParagraphStyle(
            "quote", parent=body,
            fontName=_body_italic_font,
            leftIndent=20, rightIndent=20,
            textColor=c_muted,
            borderColor=c_accent, borderPadding=8,
        )

        # ─── Header/Footer ───
        def _header_footer(canvas, doc) -> None:
            canvas.saveState()
            # Header
            canvas.setFont(theme.font_body, theme.size_xs)
            canvas.setFillColor(c_muted)
            canvas.drawString(
                2 * cm, A4[1] - 1.2 * cm,
                spec.metadata.title,
            )
            # Линия под header
            canvas.setStrokeColor(c_border)
            canvas.setLineWidth(0.5)
            canvas.line(2 * cm, A4[1] - 1.4 * cm, A4[0] - 2 * cm, A4[1] - 1.4 * cm)
            # Footer
            footer_text = (
                f"Velantrim ExoCortex • {spec.metadata.author} • "
                f"Стр. {doc.page}"
            )
            canvas.drawCentredString(A4[0] / 2, 1.2 * cm, footer_text)
            canvas.restoreState()

        # ─── Документ ───
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            leftMargin=2 * cm, rightMargin=2 * cm,
            topMargin=2 * cm, bottomMargin=2 * cm,
            title=spec.metadata.title,
            author=spec.metadata.author,
            subject=spec.metadata.subject,
            keywords=", ".join(spec.metadata.keywords) if spec.metadata.keywords else "",
        )

        story: list = []

        # ─── Render каждого блока ───
        for block in spec.blocks:
            if isinstance(block, HeadingBlock):
                style = h1 if block.level == 1 else (h2 if block.level == 2 else h3)
                story.append(Paragraph(self._escape(block.text), style))

            elif isinstance(block, ParagraphBlock):
                style = body
                if block.style == "bold":
                    style = body_bold
                elif block.style == "italic":
                    style = body_italic
                elif block.style == "callout":
                    style = muted
                story.append(Paragraph(self._escape(block.text), style))

            elif isinstance(block, ListBlock):
                self._render_list(story, block, body, theme)

            elif isinstance(block, TableBlock):
                self._render_table(
                    story, block, body, muted,
                    c_primary, c_surface, c_border, c_bg,
                    theme,
                )

            elif isinstance(block, CodeBlock):
                story.append(Paragraph(
                    self._escape(block.code).replace("\n", "<br/>"),
                    code_style,
                ))
                if block.caption:
                    story.append(Paragraph(self._escape(block.caption), muted))

            elif isinstance(block, ImageBlock):
                self._render_image(story, block, muted)

            elif isinstance(block, CalloutBlock):
                self._render_callout(
                    story, block, body, theme,
                    c_success, c_warning, c_danger, c_primary, c_surface,
                )

            elif isinstance(block, QuoteBlock):
                quote_text = self._escape(block.text)
                if block.author:
                    quote_text += f"<br/>— <i>{self._escape(block.author)}</i>"
                story.append(Paragraph(quote_text, quote_style))

            elif isinstance(block, DividerBlock):
                story.append(Spacer(1, theme.spacing_sm))
                story.append(HRFlowable(
                    width="100%", thickness=0.5, color=c_border,
                ))
                story.append(Spacer(1, theme.spacing_sm))

            elif isinstance(block, FactBlock):
                self._render_fact(
                    story, block, body, muted, theme,
                    c_primary, c_surface, c_border,
                    c_success, c_warning, c_danger,
                )

        # Build
        doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)

        # Подсчёт страниц
        try:
            from pypdf import PdfReader
            reader = PdfReader(output_path)
            return len(reader.pages)
        except Exception:
            return 0

    # ─── Helpers для отдельных блоков ─────────────────────────────────────────

    @staticmethod
    def _escape(text: str) -> str:
        """Экранирование для ReportLab Paragraph (XML-like)."""
        if not text:
            return ""
        return (
            text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
        )

    def _render_list(self, story, block: ListBlock, body_style, theme) -> None:
        from reportlab.platypus import Paragraph
        for i, item in enumerate(block.items):
            marker = f"{i+1}." if block.ordered else "•"
            text = f"{marker}&nbsp;&nbsp;{self._escape(item)}"
            story.append(Paragraph(text, body_style))

    def _render_table(
        self, story, block: TableBlock, body_style, muted_style,
        c_primary, c_surface, c_border, c_bg, theme,
    ) -> None:
        from reportlab.lib import colors
        from reportlab.platypus import Paragraph, Table, TableStyle

        # Заголовки + строки
        data = [block.headers] + [
            [str(cell) if cell is not None else "" for cell in row]
            for row in block.rows
        ]
        table = Table(data, repeatRows=1)
        # FIX v8.5.2 (Claude audit): font_heading_bold для таблиц
        _heading_bold_font = theme.font_heading_bold or f"{theme.font_heading}-Bold"
        table.setStyle(TableStyle([
            # Header
            ("BACKGROUND", (0, 0), (-1, 0), c_primary),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor(f"#{theme.background}")),
            ("FONTNAME", (0, 0), (-1, 0), _heading_bold_font),
            ("FONTSIZE", (0, 0), (-1, 0), theme.size_md),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("TOPPADDING", (0, 0), (-1, 0), 8),
            # Body
            ("FONTNAME", (0, 1), (-1, -1), theme.font_body),
            ("FONTSIZE", (0, 1), (-1, -1), theme.size_sm),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [c_bg, c_surface]),
            ("GRID", (0, 0), (-1, -1), 0.5, c_border),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(table)
        if block.caption:
            story.append(Paragraph(self._escape(block.caption), muted_style))

    def _render_image(self, story, block: ImageBlock, muted_style) -> None:
        import os

        from reportlab.lib.units import cm
        from reportlab.platypus import Image, Paragraph

        if not os.path.exists(block.path):
            story.append(Paragraph(
                f"[Изображение не найдено: {block.path}]",
                muted_style,
            ))
            return

        try:
            width = (block.width / 28.35) if block.width else 15 * cm
            img = Image(block.path, width=width, height=None)
            img.hAlign = "CENTER"
            story.append(img)
            if block.caption:
                story.append(Paragraph(self._escape(block.caption), muted_style))
        except Exception as exc:
            story.append(Paragraph(
                f"[Ошибка изображения: {exc}]", muted_style,
            ))

    def _render_callout(
        self, story, block: CalloutBlock, body_style, theme,
        c_success, c_warning, c_danger, c_primary, c_surface,
    ) -> None:
        from reportlab.platypus import Paragraph, Table, TableStyle

        # Цвет и эмодзи по типу
        type_config = {
            "info": ("ℹ️", c_primary),
            "success": ("✅", c_success),
            "warning": ("⚠️", c_warning),
            "danger": ("🚨", c_danger),
        }
        emoji, accent_color = type_config.get(block.callout_type, type_config["info"])

        content = f"<b>{emoji} {self._escape(block.title or block.callout_type.title())}</b><br/>{self._escape(block.text)}"
        table = Table([[Paragraph(content, body_style)]], colWidths=[None])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), c_surface),
            ("LINEBEFORE", (0, 0), (0, -1), 3, accent_color),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(table)

    def _render_fact(
        self, story, block: FactBlock, body_style, muted_style, theme,
        c_primary, c_surface, c_border,
        c_success, c_warning, c_danger,
    ) -> None:
        """Velantrim-специфичный рендеринг факта."""
        from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

        # Цвет рамки по epistemic_state
        state_colors = {
            "Validated": c_success,
            "Supported": c_success,
            "Hypothesized": c_warning,
            "Observed": c_primary,
            "Contradicted": c_danger,
            "Collapsed": c_danger,
            "Deprecated": c_danger,
            "ImmutableCore": c_success,
        }
        state_color = state_colors.get(block.epistemic_state, c_primary)
        conf_label = self._confidence_to_label(block.confidence)

        content = (
            f"<b>{self._escape(block.claim)}</b><br/>"
            f"<font size='{theme.size_xs}' color='#{theme.text_muted}'>"
            f"ID: <font face='{theme.font_mono}'>{block.fact_id}</font> &nbsp;|&nbsp; "
            f"Состояние: <b>{block.epistemic_state}</b> &nbsp;|&nbsp; "
            f"Уверенность: {block.confidence:.3f} {conf_label} &nbsp;|&nbsp; "
            f"Источник: {self._escape(block.source)}"
            f"</font>"
        )
        table = Table([[Paragraph(content, body_style)]], colWidths=[None])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), c_surface),
            ("LINEBEFORE", (0, 0), (0, -1), 3, state_color),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(table)
        story.append(Spacer(1, theme.spacing_xs))
