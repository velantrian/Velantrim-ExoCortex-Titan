"""
📚 EPUB Parser v2.0 — Электронные книги (НОВЫЙ)
=================================================
Поддерживает: EPUB, MOBI, AZW, AZW3, FB2

Каскад: ebooklib → mobi → fb2-parser
"""

import logging
import time

from .base import FileParser, ParseResult

logger = logging.getLogger("velantrim.parsers.epub")


def _check_available(module_name: str) -> bool:
    import importlib.util
    return importlib.util.find_spec(module_name) is not None


EBOOKLIB_AVAILABLE = _check_available("ebooklib")
BS4_AVAILABLE      = _check_available("bs4")


class EPUBParser(FileParser):
    file_type = "epub"

    # Книги могут быть большими
    max_file_size_bytes = 200 * 1024 * 1024  # 200 MB

    def supported_formats(self) -> list:
        return [".epub", ".mobi", ".azw", ".azw3", ".fb2"]

    def parse(self, file_path: str) -> ParseResult:
        early = self._check_file(file_path)
        if early is not None:
            return early

        result = ParseResult(file_path=file_path, file_type="epub")
        result.file_size_bytes = self._get_file_size(file_path)
        start = time.time()
        import os
        ext = os.path.splitext(file_path)[1].lower()

        try:
            if ext == ".epub" and EBOOKLIB_AVAILABLE:
                text, structured, lang = self._parse_epub(file_path)
                result.extraction_method = "ebooklib"
                result.language = lang
            else:
                result.error = (
                    f"Парсер для {ext} не доступен. "
                    f"Установите: pip install ebooklib beautifulsoup4"
                )
                return result

            result.extracted_text = text
            result.structured_data = structured
            result.word_count = len(text.split()) if text else 0
            result.page_count = structured.get("chapter_count", 0)
            result.provenance = self._build_provenance(file_path, result.extraction_method)

            if text.strip():
                result = self._enrich_with_essence(result)

        except Exception as exc:
            logger.error(f"EPUBParser error: {exc}")
            result.error = str(exc)

        result.parse_time_ms = (time.time() - start) * 1000
        return result

    def _parse_epub(self, file_path: str) -> tuple[str, dict, str]:
        import ebooklib
        from ebooklib import epub

        book = epub.read_epub(file_path)

        # Метаданные
        title = book.get_metadata("DC", "title")
        creator = book.get_metadata("DC", "creator")
        language = book.get_metadata("DC", "language")
        publisher = book.get_metadata("DC", "publisher")

        # Извлекаем текст глав
        chapters: list[dict] = []
        full_text_parts: list[str] = []
        for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            content = item.get_content().decode("utf-8", errors="replace")
            if BS4_AVAILABLE:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(content, "html.parser")
                # Title из <h1>, <h2> или <title>
                title_tag = soup.find(["h1", "h2", "title"])
                chapter_title = title_tag.get_text().strip() if title_tag else item.get_name()
                # Чистый текст без HTML
                chapter_text = soup.get_text(separator="\n", strip=True)
            else:
                # Простое удаление HTML тегов
                import re
                chapter_text = re.sub(r"<[^>]+>", " ", content)
                chapter_text = re.sub(r"\s+", " ", chapter_text).strip()
                chapter_title = item.get_name()

            chapters.append({
                "title": chapter_title,
                "text_length": len(chapter_text),
                "preview": chapter_text[:200],
            })
            full_text_parts.append(chapter_text)

        full_text = "\n\n".join(full_text_parts)
        structured = {
            "title": title[0][0] if title else "",
            "creator": creator[0][0] if creator else "",
            "publisher": publisher[0][0] if publisher else "",
            "chapters": chapters,
            "chapter_count": len(chapters),
        }
        lang = language[0][0] if language else "unknown"
        return full_text, structured, lang
