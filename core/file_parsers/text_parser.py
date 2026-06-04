"""
📝 Text/Markdown/JSON Parser v2.0
==================================
Поддерживает: TXT, MD, JSON, JSONL, YAML, RTF, code files

CHANGELOG v2.0:
- 🆕 yaml.safe_load (раньше был unsafe load — security)
- 🆕 Frontmatter detection для Markdown (YAML/TOML metadata)
- 🆕 JSONL row counting
- 🆕 Code files detection (.py, .js, .ts, etc) с syntax-aware extraction
- 🆕 Кодировка auto-detection через chardet
"""

import json
import logging
import os
import time

from .base import FileParser, ParseResult

logger = logging.getLogger("velantrim.parsers.text")


def _check_available(module_name: str) -> bool:
    import importlib.util
    return importlib.util.find_spec(module_name) is not None


YAML_AVAILABLE    = _check_available("yaml")
CHARDET_AVAILABLE = _check_available("chardet")


# Расширения, которые трактуем как код (для будущего AST-парсера)
CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs",
    ".cpp", ".c", ".h", ".hpp", ".cs", ".java", ".kt", ".swift",
    ".rb", ".php", ".sh", ".bash", ".ps1", ".lua",
    ".html", ".css", ".scss", ".sass", ".vue", ".svelte",
    ".toml", ".ini", ".cfg", ".conf",
    ".sql", ".graphql", ".proto",
}


class TextParser(FileParser):
    file_type = "text"

    def supported_formats(self) -> list:
        return list({
            ".txt", ".md", ".markdown", ".rst",
            ".json", ".jsonl", ".ndjson",
            ".yaml", ".yml", ".toml",
            ".rtf",
        } | CODE_EXTENSIONS)

    def parse(self, file_path: str) -> ParseResult:
        early = self._check_file(file_path)
        if early is not None:
            return early

        result = ParseResult(file_path=file_path, file_type="text")
        result.file_size_bytes = self._get_file_size(file_path)
        start = time.time()
        ext = os.path.splitext(file_path)[1].lower()

        try:
            # v2.0: автоопределение кодировки
            raw_content = self._read_with_encoding(file_path, result)

            if ext in (".json",):
                text, structured = self._parse_json(raw_content)
                result.extraction_method = "native JSON"
            elif ext in (".jsonl", ".ndjson"):
                text, structured = self._parse_jsonl(raw_content)
                result.extraction_method = "JSONL"
            elif ext in (".yaml", ".yml") and YAML_AVAILABLE:
                text, structured = self._parse_yaml(raw_content)
                result.extraction_method = "YAML safe_load"
            elif ext in (".md", ".markdown"):
                text, structured = self._parse_markdown(raw_content)
                result.extraction_method = "Markdown + frontmatter"
            elif ext in CODE_EXTENSIONS:
                text, structured = self._parse_code(raw_content, ext)
                result.extraction_method = f"code:{ext[1:]}"
            else:
                text = raw_content
                structured = {"format": "plain_text"}
                result.extraction_method = "plain text"

            result.extracted_text = text
            result.structured_data = structured
            result.word_count = len(text.split()) if text else 0
            result.provenance = self._build_provenance(
                file_path, result.extraction_method
            )

            if text.strip():
                result = self._enrich_with_essence(result)

        except Exception as exc:
            logger.error(f"TextParser error: {exc}")
            result.error = str(exc)

        result.parse_time_ms = (time.time() - start) * 1000
        return result

    # ─── Helpers ──────────────────────────────────────────────────────────────

    def _read_with_encoding(self, file_path: str, result: ParseResult) -> str:
        """Читает файл с автоопределением кодировки через chardet (если есть)."""
        if CHARDET_AVAILABLE:
            try:
                import chardet
                with open(file_path, "rb") as f:
                    raw_bytes = f.read()
                detected = chardet.detect(raw_bytes)
                encoding = detected.get("encoding") or "utf-8"
                confidence = detected.get("confidence", 0)
                if confidence < 0.7:
                    result.warnings.append(
                        f"low_encoding_confidence: {encoding} @ {confidence:.0%}"
                    )
                return raw_bytes.decode(encoding, errors="replace")
            except Exception:
                pass

        # Fallback — UTF-8 с replace
        with open(file_path, encoding="utf-8", errors="replace") as f:
            return f.read()

    def _parse_json(self, raw: str) -> tuple[str, dict]:
        data = json.loads(raw)
        return json.dumps(data, ensure_ascii=False, indent=2), {
            "format": "json",
            "data": data,
            "structure_type": type(data).__name__,
        }

    def _parse_jsonl(self, raw: str) -> tuple[str, dict]:
        """JSONL = JSON Lines, по одному объекту на строку."""
        lines = []
        for i, line in enumerate(raw.splitlines()):
            line = line.strip()
            if not line:
                continue
            try:
                lines.append(json.loads(line))
            except json.JSONDecodeError as exc:
                logger.warning(f"JSONL line {i}: {exc}")
        text = "\n".join(json.dumps(l, ensure_ascii=False) for l in lines[:10])
        return text, {
            "format": "jsonl",
            "row_count": len(lines),
            "sample": lines[:5],
        }

    def _parse_yaml(self, raw: str) -> tuple[str, dict]:
        """v2.0: safe_load вместо load — защита от arbitrary code execution."""
        import yaml
        try:
            data = yaml.safe_load(raw)
        except yaml.YAMLError as exc:
            raise ValueError(f"YAML parse error: {exc}")
        return raw, {"format": "yaml", "data": data}

    def _parse_markdown(self, raw: str) -> tuple[str, dict]:
        """
        Markdown с frontmatter detection.
        Поддерживает YAML (---) и TOML (+++) frontmatter.
        """
        frontmatter = None
        body = raw
        if raw.startswith("---\n"):
            end = raw.find("\n---\n", 4)
            if end > 0:
                fm_raw = raw[4:end]
                body = raw[end + 5:]
                if YAML_AVAILABLE:
                    try:
                        import yaml
                        frontmatter = yaml.safe_load(fm_raw)
                    except Exception:
                        frontmatter = {"raw": fm_raw}
                else:
                    frontmatter = {"raw": fm_raw}
        elif raw.startswith("+++\n"):
            end = raw.find("\n+++\n", 4)
            if end > 0:
                frontmatter = {"raw": raw[4:end], "format": "toml"}
                body = raw[end + 5:]

        # Headers extraction (h1, h2, h3)
        headers: list[dict] = []
        for i, line in enumerate(body.splitlines()):
            if line.startswith("#"):
                level = len(line) - len(line.lstrip("#"))
                if 1 <= level <= 6:
                    headers.append({"level": level, "text": line.lstrip("#").strip(), "line": i})

        return body, {
            "format": "markdown",
            "frontmatter": frontmatter,
            "headers": headers,
            "header_count": len(headers),
        }

    def _parse_code(self, raw: str, ext: str) -> tuple[str, dict]:
        """
        Парсинг кода. Пока только метрики, AST — Sprint 2c.

        TODO: для .py использовать ast.parse() и извлекать определения функций/классов.
        """
        lines = raw.splitlines()
        return raw, {
            "format": "code",
            "language": ext.lstrip("."),
            "line_count": len(lines),
            "non_empty_lines": sum(1 for l in lines if l.strip()),
            "comment_lines": sum(
                1 for l in lines
                if l.strip().startswith(("#", "//", "/*", "*"))
            ),
        }
