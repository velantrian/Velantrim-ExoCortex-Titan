"""
🌐 HTML Generator v1.0 — Красивые HTML отчёты
================================================
Семантический HTML5 с inline-CSS под выбранную тему.

Особенности:
- Standalone HTML — открывается в любом браузере, всё inline (нет CDN)
- Responsive layout (max-width 800px, mobile-friendly)
- Темы через CSS custom properties (--color-primary и т.д.)
- Print-friendly стили (для конвертации в PDF через браузер)
- Эмодзи и UTF-8
- Без JavaScript — максимальная совместимость
"""

import html
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
    get_theme,
)

logger = logging.getLogger("velantrim.generators.html")


class HTMLGenerator(FileGenerator):
    """HTML генератор. Без зависимостей — чистый Python."""

    format_name = "html"

    def supported_extensions(self) -> list[str]:
        return [".html", ".htm"]

    def generate(
        self,
        spec: GenerationSpec,
        output_path: str,
    ) -> GenerationResult:
        result = GenerationResult(output_path=output_path, format="html")
        start = time.time()
        self._ensure_output_dir(output_path)
        theme = get_theme(spec.theme)

        try:
            html_content = self._render(spec, theme)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            result.method = "native HTML5"
            result.block_count = len(spec.blocks)
            result.file_size_bytes = self._file_size(output_path)
            result.metadata = self._build_provenance(output_path)
        except Exception as exc:
            logger.error(f"HTML generation error: {exc}")
            result.error = str(exc)

        result.generation_time_ms = (time.time() - start) * 1000
        return result

    # ─── Render ───────────────────────────────────────────────────────────────

    def _render(self, spec: GenerationSpec, theme) -> str:
        body_blocks = []
        for block in spec.blocks:
            body_blocks.append(self._render_block(block, theme))

        body_html = "\n".join(body_blocks)
        css = self._generate_css(theme)
        title = html.escape(spec.metadata.title)
        author = html.escape(spec.metadata.author)
        description = html.escape(spec.metadata.description)
        lang = spec.metadata.language or "ru"

        return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="author" content="{author}">
<meta name="description" content="{description}">
<title>{title}</title>
<style>
{css}
</style>
</head>
<body>
<main class="container">
<header class="document-header">
<h1 class="document-title">{title}</h1>
<p class="document-meta">{author}</p>
</header>
<article class="document-body">
{body_html}
</article>
<footer class="document-footer">
<p>Сгенерировано Velantrim ExoCortex • {author}</p>
</footer>
</main>
</body>
</html>
"""

    def _generate_css(self, theme) -> str:
        """CSS с темой через custom properties."""
        return f"""
:root {{
  --color-primary: #{theme.primary};
  --color-secondary: #{theme.secondary};
  --color-accent: #{theme.accent};
  --color-text: #{theme.text};
  --color-text-muted: #{theme.text_muted};
  --color-bg: #{theme.background};
  --color-surface: #{theme.surface};
  --color-border: #{theme.border};
  --color-success: #{theme.success};
  --color-warning: #{theme.warning};
  --color-danger: #{theme.danger};
  --font-heading: "{theme.font_heading}", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  --font-body: "{theme.font_body}", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  --font-mono: "{theme.font_mono}", ui-monospace, "SF Mono", Menlo, monospace;
}}

* {{ box-sizing: border-box; }}
html {{ scroll-behavior: smooth; }}
body {{
  margin: 0;
  padding: 0;
  font-family: var(--font-body);
  font-size: {theme.size_md}px;
  line-height: 1.6;
  color: var(--color-text);
  background: var(--color-bg);
}}
.container {{
  max-width: 800px;
  margin: 0 auto;
  padding: 32px 24px;
}}
.document-header {{
  text-align: center;
  padding-bottom: 24px;
  margin-bottom: 32px;
  border-bottom: 2px solid var(--color-primary);
}}
.document-title {{
  font-family: var(--font-heading);
  font-size: {theme.size_4xl}px;
  font-weight: 700;
  color: var(--color-primary);
  margin: 0 0 8px;
  line-height: 1.2;
}}
.document-meta {{
  color: var(--color-text-muted);
  margin: 0;
  font-size: {theme.size_md}px;
}}
.document-body h1, .document-body h2, .document-body h3, .document-body h4 {{
  font-family: var(--font-heading);
  color: var(--color-primary);
  line-height: 1.3;
  margin-top: 32px;
  margin-bottom: 12px;
}}
.document-body h1 {{ font-size: {theme.size_3xl}px; border-bottom: 1px solid var(--color-border); padding-bottom: 8px; }}
.document-body h2 {{ font-size: {theme.size_2xl}px; }}
.document-body h3 {{ font-size: {theme.size_xl}px; color: var(--color-secondary); }}
.document-body h4 {{ font-size: {theme.size_lg}px; color: var(--color-secondary); }}
.document-body p {{ margin: 0 0 16px; }}
.document-body p.callout-text {{ color: var(--color-text-muted); font-style: italic; }}
.document-body ul, .document-body ol {{ margin: 0 0 16px; padding-left: 32px; }}
.document-body li {{ margin-bottom: 6px; }}
.document-body table {{
  width: 100%;
  border-collapse: collapse;
  margin: 16px 0;
  font-size: {theme.size_sm}px;
  background: var(--color-bg);
  border-radius: 6px;
  overflow: hidden;
}}
.document-body thead {{ background: var(--color-primary); }}
.document-body th {{
  padding: 12px;
  text-align: left;
  color: var(--color-bg);
  font-weight: 600;
  font-family: var(--font-heading);
}}
.document-body td {{
  padding: 10px 12px;
  border-top: 1px solid var(--color-border);
}}
.document-body tbody tr:nth-child(even) {{ background: var(--color-surface); }}
.document-body figcaption {{
  font-size: {theme.size_xs}px;
  color: var(--color-text-muted);
  font-style: italic;
  text-align: center;
  margin-top: 6px;
}}
.document-body pre {{
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-left: 3px solid var(--color-accent);
  border-radius: 6px;
  padding: 16px;
  overflow-x: auto;
  font-family: var(--font-mono);
  font-size: {theme.size_sm}px;
  line-height: 1.5;
  margin: 16px 0;
}}
.document-body blockquote {{
  border-left: 3px solid var(--color-accent);
  padding: 8px 16px;
  margin: 16px 0;
  color: var(--color-text-muted);
  font-style: italic;
  background: var(--color-surface);
}}
.document-body blockquote cite {{
  display: block;
  margin-top: 8px;
  font-size: {theme.size_sm}px;
  color: var(--color-text-muted);
  font-style: normal;
}}
.document-body hr {{
  border: none;
  height: 1px;
  background: var(--color-border);
  margin: 32px 0;
}}
.callout {{
  border-radius: 6px;
  padding: 16px;
  margin: 16px 0;
  background: var(--color-surface);
  border-left: 3px solid var(--color-primary);
}}
.callout-info {{ border-left-color: var(--color-primary); }}
.callout-success {{ border-left-color: var(--color-success); }}
.callout-warning {{ border-left-color: var(--color-warning); }}
.callout-danger {{ border-left-color: var(--color-danger); }}
.callout-title {{
  font-weight: 600;
  margin-bottom: 6px;
}}
.callout-info .callout-title {{ color: var(--color-primary); }}
.callout-success .callout-title {{ color: var(--color-success); }}
.callout-warning .callout-title {{ color: var(--color-warning); }}
.callout-danger .callout-title {{ color: var(--color-danger); }}
.fact-card {{
  border-radius: 6px;
  padding: 16px;
  margin: 12px 0;
  background: var(--color-surface);
  border-left: 4px solid var(--color-primary);
}}
.fact-card-validated {{ border-left-color: var(--color-success); }}
.fact-card-hypothesized {{ border-left-color: var(--color-warning); }}
.fact-card-contradicted, .fact-card-collapsed {{ border-left-color: var(--color-danger); }}
.fact-claim {{
  font-weight: 600;
  font-size: {theme.size_md}px;
  margin: 0 0 8px;
}}
.fact-meta {{
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  font-size: {theme.size_xs}px;
  color: var(--color-text-muted);
}}
.fact-meta-item {{ display: inline-flex; align-items: center; gap: 4px; }}
.fact-meta-item code {{
  font-family: var(--font-mono);
  background: var(--color-bg);
  padding: 1px 6px;
  border-radius: 3px;
  border: 1px solid var(--color-border);
}}
.confidence-high {{ color: var(--color-success); font-weight: 600; }}
.confidence-mid {{ color: var(--color-warning); font-weight: 600; }}
.confidence-low {{ color: var(--color-danger); font-weight: 600; }}
.document-body img {{ max-width: 100%; height: auto; display: block; margin: 16px auto; border-radius: 6px; }}
.document-footer {{
  margin-top: 48px;
  padding-top: 16px;
  border-top: 1px solid var(--color-border);
  text-align: center;
  color: var(--color-text-muted);
  font-size: {theme.size_xs}px;
}}
@media print {{
  body {{ font-size: 11pt; background: white; }}
  .container {{ max-width: 100%; padding: 0; }}
  .document-header {{ page-break-after: avoid; }}
  h1, h2, h3 {{ page-break-after: avoid; }}
  table, blockquote, .callout, .fact-card {{ page-break-inside: avoid; }}
}}
"""

    # ─── Block renderers ──────────────────────────────────────────────────────

    def _render_block(self, block: Block, theme) -> str:
        if isinstance(block, HeadingBlock):
            level = min(max(block.level, 1), 6)
            return f"<h{level}>{html.escape(block.text)}</h{level}>"

        if isinstance(block, ParagraphBlock):
            text = html.escape(block.text)
            if block.style == "bold":
                return f"<p><strong>{text}</strong></p>"
            if block.style == "italic":
                return f"<p><em>{text}</em></p>"
            if block.style == "callout":
                return f'<p class="callout-text">{text}</p>'
            return f"<p>{text}</p>"

        if isinstance(block, ListBlock):
            tag = "ol" if block.ordered else "ul"
            items = "\n".join(
                f"  <li>{html.escape(item)}</li>" for item in block.items
            )
            return f"<{tag}>\n{items}\n</{tag}>"

        if isinstance(block, TableBlock):
            return self._render_table(block)

        if isinstance(block, CodeBlock):
            code = html.escape(block.code)
            caption = (
                f'<figcaption>{html.escape(block.caption)}</figcaption>'
                if block.caption else ""
            )
            return f'<figure><pre><code class="language-{block.language}">{code}</code></pre>{caption}</figure>'

        if isinstance(block, ImageBlock):
            alt = html.escape(block.caption or "Image")
            caption = (
                f'<figcaption>{html.escape(block.caption)}</figcaption>'
                if block.caption else ""
            )
            return f'<figure><img src="{html.escape(block.path)}" alt="{alt}">{caption}</figure>'

        if isinstance(block, CalloutBlock):
            type_class = f"callout-{block.callout_type}"
            emoji_map = {"info": "ℹ️", "success": "✅", "warning": "⚠️", "danger": "🚨"}
            emoji = emoji_map.get(block.callout_type, "ℹ️")
            title_html = (
                f'<div class="callout-title">{emoji} {html.escape(block.title)}</div>'
                if block.title else
                f'<div class="callout-title">{emoji}</div>'
            )
            text = html.escape(block.text)
            return f'<div class="callout {type_class}">{title_html}<div>{text}</div></div>'

        if isinstance(block, QuoteBlock):
            text = html.escape(block.text)
            cite = (
                f'<cite>— {html.escape(block.author)}</cite>'
                if block.author else ""
            )
            return f"<blockquote><p>{text}</p>{cite}</blockquote>"

        if isinstance(block, DividerBlock):
            return "<hr>"

        if isinstance(block, FactBlock):
            return self._render_fact(block)

        return f"<!-- unknown block type: {block.block_type} -->"

    def _render_table(self, block: TableBlock) -> str:
        headers = "".join(
            f"<th>{html.escape(str(h))}</th>" for h in block.headers
        )
        rows_html = []
        for row in block.rows:
            cells = "".join(
                f"<td>{html.escape(str(c) if c is not None else '')}</td>"
                for c in row
            )
            rows_html.append(f"<tr>{cells}</tr>")
        rows = "\n".join(rows_html)
        caption = (
            f'<caption>{html.escape(block.caption)}</caption>'
            if block.caption else ""
        )
        return (
            f"<table>{caption}\n"
            f"<thead><tr>{headers}</tr></thead>\n"
            f"<tbody>\n{rows}\n</tbody>\n"
            f"</table>"
        )

    def _render_fact(self, block: FactBlock) -> str:
        state_class_map = {
            "Validated": "validated",
            "Supported": "validated",
            "ImmutableCore": "validated",
            "Hypothesized": "hypothesized",
            "Contradicted": "contradicted",
            "Collapsed": "collapsed",
            "Deprecated": "collapsed",
        }
        state_class = state_class_map.get(block.epistemic_state, "info")

        # Confidence label
        if block.confidence >= 0.7:
            conf_class = "confidence-high"
        elif block.confidence >= 0.5:
            conf_class = "confidence-mid"
        else:
            conf_class = "confidence-low"

        return f'''<div class="fact-card fact-card-{state_class}">
<div class="fact-claim">{html.escape(block.claim)}</div>
<div class="fact-meta">
  <span class="fact-meta-item">📌 ID: <code>{html.escape(block.fact_id)}</code></span>
  <span class="fact-meta-item">🔵 {html.escape(block.epistemic_state)}</span>
  <span class="fact-meta-item">📊 <span class="{conf_class}">{block.confidence:.3f}</span></span>
  <span class="fact-meta-item">📂 {html.escape(block.source)}</span>
</div>
</div>'''
