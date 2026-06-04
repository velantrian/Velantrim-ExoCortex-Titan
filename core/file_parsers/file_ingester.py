#!/usr/bin/env python3
"""
🎯 Velantrim File Ingester v2.0 — Главный оркестратор
=======================================================
Единая точка входа для парсинга любых файлов.

CHANGELOG v2.0:
- 🆕 Через ParserRegistry (lazy init вместо хардкода)
- 🆕 Parallel processing для ingest_directory() через ThreadPoolExecutor
- 🆕 Архивы автоматически обрабатываются рекурсивно (через ArchiveParser inner)
- 🆕 Progress callback для длинных операций
- 🆕 Stats содержат метрики времени и размера
- 🆕 Можно отключать конкретные парсеры через ENV
"""

import logging
import os
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from .base import ParseResult, ParserRegistry

logger = logging.getLogger("velantrim.file_ingester")


def _register_default_parsers(registry: ParserRegistry) -> None:
    """
    Регистрирует все встроенные парсеры.
    Можно отключать конкретные через ENV: VELANTRIM_DISABLE_PARSERS=video,audio
    """
    disabled = set(
        p.strip().lower()
        for p in os.getenv("VELANTRIM_DISABLE_PARSERS", "").split(",")
        if p.strip()
    )

    # Lazy imports — не грузим тяжёлые зависимости пока не нужны
    if "pdf" not in disabled:
        from .pdf_parser import PDFParser
        registry.register("pdf", PDFParser, [".pdf"])

    if "docx" not in disabled:
        from .docx_parser import DOCXParser
        registry.register("docx", DOCXParser, [".docx", ".docm"])

    if "pptx" not in disabled:
        from .pptx_parser import PPTXParser
        registry.register("pptx", PPTXParser, [".pptx", ".pptm", ".odp"])

    if "text" not in disabled:
        from .text_parser import CODE_EXTENSIONS, TextParser
        text_exts = list({
            ".txt", ".md", ".markdown", ".rst",
            ".json", ".jsonl", ".ndjson",
            ".yaml", ".yml", ".toml",
            ".rtf",
        } | CODE_EXTENSIONS)
        registry.register("text", TextParser, text_exts)

    if "csv" not in disabled:
        from .csv_parser import CSVParser
        registry.register("csv", CSVParser, [".csv", ".tsv", ".xlsx", ".xls", ".ods"])

    if "image" not in disabled:
        from .image_parser import ImageParser
        registry.register("image", ImageParser, [
            ".jpg", ".jpeg", ".png", ".gif", ".webp",
            ".bmp", ".tiff", ".tif", ".heic", ".heif",
        ])

    if "audio" not in disabled:
        from .audio_parser import AudioParser
        registry.register("audio", AudioParser, [
            ".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac", ".wma", ".opus", ".aiff",
        ])

    if "video" not in disabled:
        from .video_parser import VideoParser
        registry.register("video", VideoParser, [
            ".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v", ".ts", ".mts",
        ])

    if "epub" not in disabled:
        from .epub_parser import EPUBParser
        registry.register("epub", EPUBParser, [".epub", ".mobi", ".azw", ".azw3", ".fb2"])

    if "email" not in disabled:
        from .email_parser import EmailParser
        registry.register("email", EmailParser, [".eml", ".msg", ".mbox"])

    if "html" not in disabled:
        from .html_parser import HTMLParser
        registry.register("html", HTMLParser, [".html", ".htm", ".xhtml", ".mhtml", ".xml"])

    if "archive" not in disabled:
        from .archive_parser import ArchiveParser
        registry.register("archive", ArchiveParser, [
            ".zip", ".tar", ".gz", ".tgz", ".tar.gz", ".bz2", ".tbz2", ".7z", ".rar",
        ])


class FileIngester:
    """
    Универсальный загрузчик файлов в Velantrim.

    v2.0: ParserRegistry, parallel processing, archive recursion, progress callbacks.

    Использование:
        ingester = FileIngester()
        result = ingester.ingest("document.pdf")
        fact = ingester.to_fact(result)

        # Параллельная обработка директории
        results = ingester.ingest_directory("/docs", workers=4)

        # С progress callback
        def on_progress(done, total, current_file):
            print(f"[{done}/{total}] {current_file}")
        results = ingester.ingest_directory("/docs", progress=on_progress)
    """

    def __init__(self, enable_archive_recursion: bool = True) -> None:
        self.registry = ParserRegistry()
        _register_default_parsers(self.registry)

        # Архивы обрабатываются рекурсивно через тот же FileIngester (self)
        if enable_archive_recursion:
            try:
                from .archive_parser import ArchiveParser
                # Создаём ArchiveParser-инстанс с ссылкой на self
                archive_parser = ArchiveParser(inner_ingester=self, _depth=0)
                # Заменяем в registry на инстанс с inner
                self.registry._initialized["archive"] = archive_parser
            except Exception as exc:
                logger.debug(f"Archive recursion setup failed: {exc}")

        self._stats: dict[str, Any] = {
            "processed": 0,
            "errors": 0,
            "by_type": {},
            "total_bytes": 0,
            "total_time_ms": 0.0,
        }

    def ingest(self, file_path: str) -> ParseResult:
        """Парсит один файл."""
        if not os.path.exists(file_path):
            return ParseResult(
                file_path=file_path,
                file_type="unknown",
                error=f"Файл не найден: {file_path}",
            )

        # Получаем расширение, для .tar.gz нужна особая обработка
        path = Path(file_path)
        ext = path.suffix.lower()
        # tar.gz и tar.bz2 — двойные расширения
        if path.suffixes and len(path.suffixes) >= 2:
            double_ext = "".join(path.suffixes[-2:]).lower()
            if double_ext in (".tar.gz", ".tar.bz2"):
                ext = double_ext

        parser = self.registry.get_parser_for(ext)
        if parser is None:
            # Fallback: попробуем как text
            parser = self.registry.get_parser_for(".txt")
            if parser is None:
                return ParseResult(
                    file_path=file_path,
                    file_type=ext,
                    error=f"Нет парсера для типа: {ext}",
                )

        logger.info(f"📂 Ingesting: {file_path} → {parser.__class__.__name__}")

        try:
            result = parser.parse(file_path)
            self._update_stats(result, parser_name=parser.__class__.__name__)
            return result
        except Exception as exc:
            self._stats["errors"] += 1
            logger.error(f"Ingestion failed for {file_path}: {exc}")
            return ParseResult(
                file_path=file_path,
                file_type=parser.file_type,
                error=str(exc),
            )

    def ingest_directory(
        self,
        directory: str,
        recursive: bool = False,
        workers: int = 1,
        progress: Callable[[int, int, str], None] | None = None,
    ) -> list[ParseResult]:
        """
        Парсит все поддерживаемые файлы в директории.

        Args:
            directory: путь к папке
            recursive: рекурсивный обход подпапок
            workers: количество параллельных потоков (1 = sequential)
            progress: callback(done, total, current_file) для прогресса

        Returns:
            Список ParseResult для каждого обработанного файла.
        """
        path = Path(directory)
        if not path.is_dir():
            return []

        # Собираем все файлы
        files: list[Path] = []
        supported = set(self.registry.supported_extensions())
        iterator = path.rglob("*") if recursive else path.glob("*")
        for f in iterator:
            if f.is_file() and f.suffix.lower() in supported:
                files.append(f)

        total = len(files)
        logger.info(f"📁 Found {total} supported files in {directory}")

        if total == 0:
            return []

        results: list[ParseResult] = []

        if workers <= 1:
            # Sequential
            for i, fpath in enumerate(files):
                r = self.ingest(str(fpath))
                results.append(r)
                if progress:
                    progress(i + 1, total, str(fpath))
        else:
            # Parallel через ThreadPoolExecutor
            # FIX v8.5.3 (Gemini finding): batch-обработка вместо submit-bomb.
            # Раньше {executor.submit(self.ingest, str(f)): f for f in files}
            # сразу создавал N Future-объектов в RAM при N=500K файлах OOM-crash.
            # Сейчас обрабатываем чанками по chunk_size: в RAM одновременно
            # максимум 2*workers Future-ов, остальные ждут своей очереди.
            # Прогресс репортится по мере завершения каждого chunk'а.
            chunk_size = max(workers * 2, 50)  # окно небольшое, чтобы не съесть RAM
            with ThreadPoolExecutor(max_workers=workers) as executor:
                done = 0
                for i in range(0, len(files), chunk_size):
                    batch = files[i:i + chunk_size]
                    future_to_path = {
                        executor.submit(self.ingest, str(f)): f for f in batch
                    }
                    for future in as_completed(future_to_path):
                        fpath = future_to_path[future]
                        try:
                            r = future.result()
                            results.append(r)
                        except Exception as exc:
                            results.append(ParseResult(
                                file_path=str(fpath),
                                file_type="unknown",
                                error=str(exc),
                            ))
                        done += 1
                        if progress:
                            progress(done, total, str(fpath))

        logger.info(f"✅ Ingestion complete: {len(results)} files")
        return results

    def to_fact(self, result: ParseResult, source_override: str | None = None) -> dict[str, Any]:
        """
        Конвертирует ParseResult в формат факта для store_fact().

        FIX v8.5.2 (Claude audit): source_override прокидывается в ParseResult.to_fact_dict
        для маркировки доверенных источников (domain_seed, ring_zero и т.д.).
        """
        return result.to_fact_dict(source_override=source_override)

    def to_facts(
        self,
        results: list[ParseResult],
        source_override: str | None = None,
    ) -> list[dict[str, Any]]:
        """Batch-конвертация с опциональным source_override на весь batch."""
        return [r.to_fact_dict(source_override=source_override) for r in results]

    def get_stats(self) -> dict[str, Any]:
        """Текущая статистика парсинга."""
        return dict(self._stats)

    def get_supported_formats(self) -> dict[str, list[str]]:
        """Карта `тип → расширения` всех зарегистрированных парсеров."""
        return self.registry.parsers_by_type()

    # ─── Internal ─────────────────────────────────────────────────────────────

    def _update_stats(self, result: ParseResult, parser_name: str) -> None:
        self._stats["processed"] += 1
        self._stats["total_bytes"] += result.file_size_bytes
        self._stats["total_time_ms"] += result.parse_time_ms
        ptype = result.file_type
        self._stats["by_type"][ptype] = self._stats["by_type"].get(ptype, 0) + 1
        if result.error:
            self._stats["errors"] += 1


# ─── CLI для теста ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    ingester = FileIngester()

    print("🦋 Velantrim File Ingester v2.0 — поддерживаемые форматы:\n")
    for category, exts in ingester.get_supported_formats().items():
        print(f"  {category:12s}: {', '.join(exts)}")
    print()

    if len(sys.argv) > 1:
        for file_path in sys.argv[1:]:
            print(f"📂 Обрабатываю: {file_path}\n")
            result = ingester.ingest(file_path)

            if result.error:
                print(f"❌ Ошибка: {result.error}")
            else:
                print(f"✅ Тип:    {result.file_type}")
                print(f"   Метод:  {result.extraction_method}")
                print(f"   Время:  {result.parse_time_ms:.0f}ms")
                print(f"   Размер: {result.file_size_bytes / 1024:.1f} KB")
                if result.page_count:
                    print(f"   Страниц: {result.page_count}")
                if result.word_count:
                    print(f"   Слов:   {result.word_count}")
                if result.language:
                    print(f"   Язык:   {result.language}")
                if result.warnings:
                    print(f"   ⚠ Warnings: {', '.join(result.warnings)}")
                print(f"   Текст:  {result.extracted_text[:200]}...")

                fact = ingester.to_fact(result)
                print("\n📦 Готовый факт для Velantrim:")
                print(f"   fact_id:    {fact['fact_id']}")
                print(f"   confidence: {fact['confidence']}")
                print(f"   claim:      {fact['claim'][:100]}...")
            print()

        print("\n📊 Статистика:")
        for k, v in ingester.get_stats().items():
            print(f"   {k}: {v}")
    else:
        print("Использование: python file_ingester.py <файл1> [файл2 ...]")
