"""
📂 Velantrim File Parsers v2.0 — Универсальный модуль для работы с файлами
============================================================================

Поддерживаемые форматы (60+ расширений в 11 категориях):

📄 Документы:       PDF, DOCX, PPTX, ODP, RTF
📚 Книги:           EPUB, MOBI, AZW, AZW3, FB2
📝 Текст:           TXT, MD, RST, JSON, JSONL, YAML, TOML
💻 Код:             PY, JS, TS, GO, RS, CPP, JAVA, HTML, CSS, SQL, ...
📊 Таблицы:         CSV, TSV, XLSX, XLS, ODS
📧 Email:           EML, MSG, MBOX
🌐 Web:             HTML, HTM, XHTML, MHTML, XML
🖼️ Изображения:    JPG, PNG, GIF, WebP, BMP, TIFF, HEIC
🎤 Аудио:           MP3, WAV, FLAC, OGG, M4A, AAC, OPUS, AIFF
🎬 Видео:           MP4, MOV, AVI, MKV, WEBM, M4V, TS, MTS
📦 Архивы:          ZIP, TAR, GZ, BZ2, 7Z, RAR (рекурсивно)

CHANGELOG v2.0 (Этап 1 audit):
- Marker (Surya OCR) для PDF — лучший универсальный 2026
- PyMuPDF заменил PyPDF2 (10-50× быстрее)
- faster-whisper для аудио — 4× быстрее openai-whisper
- Lazy singleton модели (Whisper больше не грузится 100 раз для 100 файлов)
- ParserRegistry для регистрации (раньше хардкод в FileIngester)
- 4 НОВЫХ парсера: EPUB, Email, HTML, Archive (с recursive extraction)
- PPTX парсер для презентаций
- _enrich_with_essence вынесен в base (был дубликат в 6 парсерах)
- SHA256 вместо BLAKE3 (без внешних зависимостей)
- MAX_FILE_SIZE защита от OOM
- Parallel processing для ingest_directory()

Использование:
    from core.file_parsers import FileIngester

    ingester = FileIngester()
    result = ingester.ingest("document.pdf")
    fact = ingester.to_fact(result)

    # Параллельная обработка
    results = ingester.ingest_directory("/docs", workers=4, recursive=True)
"""

from .base import (
    FileParser,
    ParseResult,
    ParserRegistry,
    _ModelSingleton,
)
from .file_ingester import FileIngester

# Парсеры (опциональный импорт — для прямого использования)
__all__ = [
    "FileParser",
    "ParseResult",
    "ParserRegistry",
    "FileIngester",
    "_ModelSingleton",
]

__version__ = "2.0.0"
