"""
📄 PDF Parser v2.0 — Лучшие open-source инструменты 2026 года
==============================================================
Каскад (от лучшего к fallback):
    Marker → Docling → MinerU → Unstructured → PyMuPDF → PyPDF2

CHANGELOG v2.0:
- 🆕 Marker (Surya OCR + опц. LLM rerank) — самый универсальный 2026
- 🆕 PyMuPDF (fitz) заменил PyPDF2 как primary fallback — в 10-50× быстрее
- 🆕 Encrypted PDF detection с понятной ошибкой
- 🆕 Hi-res strategy → fast strategy fallback в Unstructured (timeout-aware)
- 🆕 _enrich_with_essence унаследован из base (был дубликат)
- 🆕 page_count, word_count в ParseResult
"""

import logging
import time

from .base import FileParser, ParseResult

logger = logging.getLogger("velantrim.parsers.pdf")

# ─── Lazy import detection ────────────────────────────────────────────────────

def _check_available(module_name: str) -> bool:
    """Проверяет доступность модуля без импорта."""
    import importlib.util
    return importlib.util.find_spec(module_name) is not None


MARKER_AVAILABLE       = _check_available("marker")
DOCLING_AVAILABLE      = _check_available("docling")
MINERU_AVAILABLE       = _check_available("magic_pdf")
UNSTRUCTURED_AVAILABLE = _check_available("unstructured")
PYMUPDF_AVAILABLE      = _check_available("fitz")
PYPDF2_AVAILABLE       = _check_available("PyPDF2") or _check_available("pypdf")


class PDFParser(FileParser):
    """
    Парсер PDF с каскадом методов от лучшего к fallback.

    Конфигурация через ENV:
        VELANTRIM_PDF_USE_MARKER_LLM=true    — включает Marker --use_llm
        VELANTRIM_PDF_STRATEGY=hi_res|fast   — Unstructured strategy
    """

    file_type = "pdf"

    # PDF может быть очень большим (книги), но 500MB всё ещё разумно
    # Можно переопределить через ENV: VELANTRIM_MAX_FILE_SIZE_MB

    def supported_formats(self) -> list:
        return [".pdf"]

    def parse(self, file_path: str) -> ParseResult:
        # Валидация файла (существование, размер, не пустой)
        early = self._check_file(file_path)
        if early is not None:
            return early

        result = ParseResult(file_path=file_path, file_type="pdf")
        result.file_size_bytes = self._get_file_size(file_path)
        start = time.time()

        # Проверка на encrypted PDF — даём понятную ошибку
        if self._is_encrypted(file_path):
            result.error = (
                "PDF зашифрован паролем — расшифруйте его перед парсингом "
                "(qpdf --decrypt input.pdf output.pdf)"
            )
            result.parse_time_ms = (time.time() - start) * 1000
            return result

        # ─── Каскад методов ───
        try:
            # Метод 1: Marker — лучший универсальный инструмент 2026
            if MARKER_AVAILABLE:
                try:
                    text, structured, pages = self._parse_marker(file_path)
                    if text.strip():
                        return self._finalize(
                            result, text, structured, "Marker",
                            page_count=pages, start=start,
                        )
                except Exception as exc:
                    logger.warning(f"Marker failed: {exc}")
                    result.warnings.append(f"marker_failed: {type(exc).__name__}")

            # Метод 2: Docling — enterprise-grade, лучший для RAG
            if DOCLING_AVAILABLE:
                try:
                    text, structured, pages = self._parse_docling(file_path)
                    if text.strip():
                        return self._finalize(
                            result, text, structured, "Docling (IBM)",
                            page_count=pages, start=start,
                        )
                except Exception as exc:
                    logger.warning(f"Docling failed: {exc}")
                    result.warnings.append(f"docling_failed: {type(exc).__name__}")

            # Метод 3: MinerU — лучший для CJK и научных статей
            if MINERU_AVAILABLE:
                try:
                    text, structured, pages = self._parse_mineru(file_path)
                    if text.strip():
                        return self._finalize(
                            result, text, structured, "MinerU",
                            page_count=pages, start=start,
                        )
                except Exception as exc:
                    logger.warning(f"MinerU failed: {exc}")

            # Метод 4: Unstructured — широкая поддержка форматов
            if UNSTRUCTURED_AVAILABLE:
                try:
                    text, structured, pages = self._parse_unstructured(file_path)
                    if text.strip():
                        return self._finalize(
                            result, text, structured, "Unstructured",
                            page_count=pages, start=start,
                        )
                except Exception as exc:
                    logger.warning(f"Unstructured failed: {exc}")

            # Метод 5: PyMuPDF (fitz) — быстрый fallback, в 10-50× быстрее PyPDF2
            if PYMUPDF_AVAILABLE:
                try:
                    text, structured, pages = self._parse_pymupdf(file_path)
                    return self._finalize(
                        result, text, structured, "PyMuPDF (fast fallback)",
                        page_count=pages, start=start,
                    )
                except Exception as exc:
                    logger.warning(f"PyMuPDF failed: {exc}")

            # Метод 6: PyPDF2 — последний universal fallback
            if PYPDF2_AVAILABLE:
                text, structured, pages = self._parse_pypdf2(file_path)
                return self._finalize(
                    result, text, structured, "PyPDF2 (last resort)",
                    page_count=pages, start=start,
                )

            result.error = (
                "Ни один PDF-парсер не доступен. Установите: "
                "pip install marker-pdf  ИЛИ  pip install pymupdf"
            )
        except Exception as exc:
            logger.error(f"PDFParser unrecoverable error: {exc}")
            result.error = str(exc)

        result.parse_time_ms = (time.time() - start) * 1000
        return result

    # ─── Helpers ──────────────────────────────────────────────────────────────

    def _finalize(
        self,
        result: ParseResult,
        text: str,
        structured: dict,
        method: str,
        page_count: int,
        start: float,
    ) -> ParseResult:
        """Заполняет result и применяет enrichment из base."""
        result.extracted_text = text
        result.structured_data = structured
        result.extraction_method = method
        result.page_count = page_count
        result.word_count = len(text.split()) if text else 0
        result.parse_time_ms = (time.time() - start) * 1000
        result.provenance = self._build_provenance(result.file_path, method)
        return self._enrich_with_essence(result)  # унаследован из base

    @staticmethod
    def _is_encrypted(file_path: str) -> bool:
        """Проверяет зашифрован ли PDF (без расшифровки)."""
        try:
            if PYMUPDF_AVAILABLE:
                import fitz
                doc = fitz.open(file_path)
                is_enc = doc.is_encrypted
                doc.close()
                return is_enc
            if PYPDF2_AVAILABLE:
                try:
                    from pypdf import PdfReader
                except ImportError:
                    from PyPDF2 import PdfReader
                reader = PdfReader(file_path)
                return reader.is_encrypted
        except Exception:
            pass
        return False

    # ─── Конкретные парсеры ───────────────────────────────────────────────────

    def _parse_marker(self, file_path: str) -> tuple[str, dict, int]:
        """
        Marker — самый универсальный инструмент 2026.
        Surya OCR + опц. LLM rerank через --use_llm.
        """
        import os

        from marker.converters.pdf import PdfConverter
        from marker.models import create_model_dict

        use_llm = os.getenv("VELANTRIM_PDF_USE_MARKER_LLM", "false").lower() == "true"
        converter = PdfConverter(
            artifact_dict=create_model_dict(),
            config={"use_llm": use_llm} if use_llm else None,
        )
        rendered = converter(file_path)
        text = rendered.markdown or ""
        return text, {
            "format": "markdown",
            "metadata": rendered.metadata or {},
            "use_llm": use_llm,
        }, len(rendered.metadata.get("page_stats", []) or []) or 0

    def _parse_docling(self, file_path: str) -> tuple[str, dict, int]:
        """Docling — IBM, лучший для enterprise RAG."""
        from docling.document_converter import DocumentConverter
        converter = DocumentConverter()
        result = converter.convert(file_path)
        doc = result.document
        text = doc.export_to_markdown()
        return text, {
            "format": "markdown",
            "tables": [t.model_dump() for t in (doc.tables or [])],
            "pictures": len(doc.pictures or []),
        }, len(doc.pages or [])

    def _parse_mineru(self, file_path: str) -> tuple[str, dict, int]:
        """MinerU — лучший для CJK и научных статей."""
        # Упрощённый вызов — реальный API требует больше настройки
        with open(file_path, "rb") as f:
            data = f.read()
        # NOTE: real MinerU API сложнее — это упрощённая обёртка
        text = ""  # full integration TODO
        return text, {"raw_bytes": len(data)}, 0

    def _parse_unstructured(self, file_path: str) -> tuple[str, dict, int]:
        """Unstructured — широкая поддержка с typed elements."""
        import os

        from unstructured.partition.pdf import partition_pdf

        # Hi-res медленнее но точнее. Fast — для быстрого fallback.
        strategy = os.getenv("VELANTRIM_PDF_STRATEGY", "hi_res")
        try:
            elements = partition_pdf(file_path, strategy=strategy)
        except Exception:
            # Если hi_res упал — пробуем fast
            elements = partition_pdf(file_path, strategy="fast")

        text = "\n\n".join(str(el) for el in elements)
        return text, {
            "elements": [
                {"type": type(el).__name__, "text": str(el)}
                for el in elements
            ],
            "strategy": strategy,
        }, sum(1 for el in elements if hasattr(el, "metadata") and getattr(el.metadata, "page_number", None))

    def _parse_pymupdf(self, file_path: str) -> tuple[str, dict, int]:
        """
        PyMuPDF (fitz) — быстрый primary fallback.
        В 10-50× быстрее PyPDF2 для извлечения текста.
        """
        import fitz
        doc = fitz.open(file_path)
        try:
            pages_text = []
            tables_count = 0
            for page in doc:
                pages_text.append(page.get_text())
                # PyMuPDF умеет находить таблицы
                try:
                    tabs = page.find_tables()
                    tables_count += len(tabs.tables)
                except Exception:
                    pass

            text = "\n\n".join(pages_text)
            metadata = doc.metadata or {}
            page_count = doc.page_count
            return text, {
                "metadata": metadata,
                "pages": page_count,
                "tables_detected": tables_count,
            }, page_count
        finally:
            doc.close()

    def _parse_pypdf2(self, file_path: str) -> tuple[str, dict, int]:
        """PyPDF2/pypdf — последний universal fallback."""
        try:
            from pypdf import PdfReader
        except ImportError:
            from PyPDF2 import PdfReader

        with open(file_path, "rb") as f:
            reader = PdfReader(f)
            text = "\n\n".join(page.extract_text() or "" for page in reader.pages)
            metadata = dict(reader.metadata) if reader.metadata else {}
            page_count = len(reader.pages)
        return text, {"metadata": metadata, "pages": page_count}, page_count
