"""
🌐 HTML Parser v2.0 — Web-страницы (НОВЫЙ)
============================================
Поддерживает: HTML, HTM, XHTML, MHTML, XML

Каскад: trafilatura → readability → BeautifulSoup → regex (fallback)
"""

import logging
import time

from .base import FileParser, ParseResult

logger = logging.getLogger("velantrim.parsers.html")


def _check_available(module_name: str) -> bool:
    import importlib.util
    return importlib.util.find_spec(module_name) is not None


TRAFILATURA_AVAILABLE = _check_available("trafilatura")
READABILITY_AVAILABLE = _check_available("readability")
BS4_AVAILABLE         = _check_available("bs4")


class HTMLParser(FileParser):
    file_type = "html"

    def supported_formats(self) -> list:
        return [".html", ".htm", ".xhtml", ".mhtml", ".xml"]

    def parse(self, file_path: str) -> ParseResult:
        early = self._check_file(file_path)
        if early is not None:
            return early

        result = ParseResult(file_path=file_path, file_type="html")
        result.file_size_bytes = self._get_file_size(file_path)
        start = time.time()

        try:
            with open(file_path, encoding="utf-8", errors="replace") as f:
                raw = f.read()

            # Метод 1: trafilatura — лучший для извлечения main content из веб-страниц
            if TRAFILATURA_AVAILABLE:
                text, structured = self._parse_trafilatura(raw)
                result.extraction_method = "trafilatura"
            # Метод 2: readability — алгоритм Mozilla
            elif READABILITY_AVAILABLE:
                text, structured = self._parse_readability(raw)
                result.extraction_method = "readability"
            # Метод 3: BeautifulSoup — полный парсинг с custom фильтрацией
            elif BS4_AVAILABLE:
                text, structured = self._parse_bs4(raw)
                result.extraction_method = "BeautifulSoup"
            # Метод 4: regex fallback
            else:
                text, structured = self._parse_regex(raw)
                result.extraction_method = "regex (no BS4)"

            result.extracted_text = text
            result.structured_data = structured
            result.word_count = len(text.split()) if text else 0
            result.provenance = self._build_provenance(file_path, result.extraction_method)

            if text.strip():
                result = self._enrich_with_essence(result)

        except Exception as exc:
            logger.error(f"HTMLParser error: {exc}")
            result.error = str(exc)

        result.parse_time_ms = (time.time() - start) * 1000
        return result

    # ─── Backends ─────────────────────────────────────────────────────────────

    def _parse_trafilatura(self, raw: str) -> tuple[str, dict]:
        import trafilatura
        text = trafilatura.extract(raw) or ""
        metadata = trafilatura.extract_metadata(raw)
        meta_dict = metadata.as_dict() if metadata else {}
        return text, {
            "format": "html",
            "metadata": meta_dict,
            "extraction": "main_content",
        }

    def _parse_readability(self, raw: str) -> tuple[str, dict]:
        from readability import Document
        doc = Document(raw)
        title = doc.title()
        content_html = doc.summary()
        # HTML → text
        if BS4_AVAILABLE:
            from bs4 import BeautifulSoup
            text = BeautifulSoup(content_html, "html.parser").get_text("\n", strip=True)
        else:
            import re
            text = re.sub(r"<[^>]+>", " ", content_html)
            text = re.sub(r"\s+", " ", text).strip()
        return text, {"title": title, "format": "html"}

    def _parse_bs4(self, raw: str) -> tuple[str, dict]:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(raw, "html.parser")

        # Удаляем script, style, nav, footer, header
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        title_tag = soup.find("title")
        title = title_tag.get_text().strip() if title_tag else ""

        # Headers structure
        headers = [
            {"level": int(h.name[1]), "text": h.get_text().strip()}
            for h in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
        ]

        # Links
        links = [
            {"text": a.get_text().strip(), "href": a.get("href", "")}
            for a in soup.find_all("a")
            if a.get("href")
        ][:50]

        text = soup.get_text("\n", strip=True)
        return text, {
            "title": title,
            "headers": headers,
            "links": links,
            "header_count": len(headers),
            "link_count": len(soup.find_all("a")),
        }

    def _parse_regex(self, raw: str) -> tuple[str, dict]:
        """Минимальный fallback без зависимостей."""
        import re
        # FIX v8.5.3 (Gemini finding): ReDoS hardening.
        # Паттерн <script[^>]*>.*?</script> с re.DOTALL на больших входных
        # данных без закрывающего тега делает O(N) перебор — не экспоненциальный
        # ReDoS, но достаточно медленный чтобы задушить поток при adversarial input.
        # Простейший fix: обрезать raw до разумного лимита перед regex-обработкой.
        # 512KB достаточно для любой реальной веб-страницы, сайты >500KB редки.
        MAX_REGEX_INPUT = 512 * 1024  # 512 KB
        if len(raw) > MAX_REGEX_INPUT:
            raw = raw[:MAX_REGEX_INPUT]
        # Удаляем script и style блоки
        clean = re.sub(r"<script[^>]*>.*?</script>", "", raw, flags=re.DOTALL | re.IGNORECASE)
        clean = re.sub(r"<style[^>]*>.*?</style>", "", clean, flags=re.DOTALL | re.IGNORECASE)
        # Удаляем теги
        text = re.sub(r"<[^>]+>", " ", clean)
        # Нормализуем пробелы
        text = re.sub(r"\s+", " ", text).strip()
        # Title
        title_match = re.search(r"<title[^>]*>(.*?)</title>", raw, re.IGNORECASE | re.DOTALL)
        title = title_match.group(1).strip() if title_match else ""
        return text, {"title": title, "format": "html", "method": "regex_fallback"}
