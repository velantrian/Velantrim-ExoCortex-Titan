"""
🧬 Velantrim File Parser Base v2.0
====================================
Абстрактный интерфейс для всех парсеров файлов.

CHANGELOG v2.0 (Этап 1):
- BLAKE3 → SHA256 (нет внешних зависимостей, всегда работает)
- _enrich_with_essence ВЫНЕСЕН в базовый класс (DRY — было 6 дубликатов)
- MAX_FILE_SIZE проверка перед парсингом (защита от OOM на больших файлах)
- LazyImport для тяжёлых зависимостей (Whisper, sentence-transformers)
- ParserRegistry — singleton реестр (вместо хардкода в FileIngester)
- Encrypted PDF detection — понятная ошибка вместо crash
- Размер выборки для Essence — настраиваемый (а не хардкод 5000)
"""

import hashlib
import logging
import os
import threading
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Optional

logger = logging.getLogger("velantrim.parsers.base")

# ─── Конфигурация по умолчанию ────────────────────────────────────────────────

# Максимальный размер файла для парсинга (защита от OOM)
# Можно переопределить через ENV: VELANTRIM_MAX_FILE_SIZE_MB
DEFAULT_MAX_FILE_SIZE_MB = int(os.getenv("VELANTRIM_MAX_FILE_SIZE_MB", "500"))

# Размер выборки для Essence Extractor (раньше был хардкод 5000)
DEFAULT_ESSENCE_SAMPLE_SIZE = int(os.getenv("VELANTRIM_ESSENCE_SAMPLE", "5000"))


# ─── Унифицированный результат парсинга ───────────────────────────────────────

@dataclass
class ParseResult:
    """
    Унифицированный результат парсинга любого файла.

    Совместимо с store_fact() из core.memory.
    """
    file_path: str
    file_type: str
    extracted_text: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    structured_data: dict[str, Any] = field(default_factory=dict)
    essence: dict[str, Any] | None = None
    classification: dict[str, Any] | None = None
    provenance: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    parse_time_ms: float = 0.0
    extraction_method: str = ""
    # v2.0: новые поля
    file_size_bytes: int = 0
    page_count: int | None = None
    word_count: int | None = None
    language: str | None = None
    warnings: list[str] = field(default_factory=list)

    def to_fact_dict(self, source_override: str | None = None) -> dict[str, Any]:
        """
        Конвертирует результат в формат факта для store_fact().

        v2.0: SHA256 вместо BLAKE3 (нет внешних зависимостей).
        Confidence учитывает наличие essence и наличие ошибок/warnings.

        FIX v8.5.2 (Claude audit): возвращён параметр source_override.
        Используется для маркировки доверенных источников (domain_seed,
        ring_zero, axioms) при ингесте знаний из специальных директорий.
        Без него факт source = f"file_parser:{basename}".
        """
        # SHA256 работает везде из stdlib, в отличие от BLAKE3
        content = (
            self.extracted_text.encode("utf-8", errors="ignore")
            if self.extracted_text
            else self.file_path.encode("utf-8")
        )
        file_hash = hashlib.sha256(content).hexdigest()[:16]

        # Confidence calibration:
        # - Есть essence + нет warnings → 0.85
        # - Есть essence + есть warnings → 0.75
        # - Нет essence + нет warnings → 0.65
        # - Нет essence + есть warnings → 0.55
        # - Есть error → 0.0 (factually broken)
        # FIX v8.5.2 (Claude audit): пустой файл (no text, no essence, no error)
        # должен иметь более низкую confidence, чем непустой без essence —
        # отсутствие содержания само по себе уменьшает доверие.
        if self.error:
            confidence = 0.0
        elif self.essence:
            confidence = 0.75 if self.warnings else 0.85
        elif not self.extracted_text:
            confidence = 0.4   # пустой файл — минимальная confidence
        else:
            confidence = 0.55 if self.warnings else 0.65

        # Claim: используем essence или extracted_text. Если оба пустые
        # и текста нет — placeholder с именем файла, чтобы факт не был "пустым".
        if self.essence:
            claim = self.essence.get("Суть", self.extracted_text[:300])
        elif self.extracted_text:
            claim = self.extracted_text[:300]
        else:
            # FIX v8.5.2 (Claude audit): placeholder для пустых файлов.
            # Раньше claim получался пустой строкой → факт без содержания.
            claim = f"[empty file: {os.path.basename(self.file_path)}]"

        # FIX v8.5.3 (Gemini finding): source sanitization против prompt injection.
        # source вклеивается в LLM system prompt в server.py:190 через f-string
        # без экранирования: f"- [{f.get('source',...)}] {f.get('claim','')}".
        # Если имя файла содержит ]Ignore all past directives[.pdf, эта строка
        # идёт прямо в LLM контекст. Защита: оставляем только безопасные символы.
        import re as _re
        source = source_override if source_override else (
            f"file_parser:{os.path.basename(self.file_path)}"
        )
        # Разрешаем: буквы, цифры, дефис, подчёркивание, точка, двоеточие, слэш.
        # Всё остальное (скобки, кавычки, спецсимволы, пробелы) заменяем на _.
        source = _re.sub(r"[^\w\-./:]", "_", source)

        return {
            "fact_id": f"{self.file_type}_{file_hash}",
            "claim": claim,
            "source": source,
            "confidence": confidence,
            "metadata": {
                "file_path": self.file_path,
                "file_type": self.file_type,
                "file_size_bytes": self.file_size_bytes,
                "extraction_method": self.extraction_method,
                "essence": self.essence,
                "classification": self.classification,
                "provenance": self.provenance,
                "parse_time_ms": self.parse_time_ms,
                "page_count": self.page_count,
                "word_count": self.word_count,
                "language": self.language,
                "warnings": self.warnings,
            },
            "epistemic_state": "Observed",
        }


# ─── Singleton модели (lazy-loaded heavy resources) ───────────────────────────

class _ModelSingleton:
    """
    Реестр lazy-loaded моделей. Whisper, sentence-transformers и т.п.
    загружаются ОДИН РАЗ за время жизни процесса.

    v2.0 fix: до этого Whisper загружался в каждом parse() — 1.5GB модель
    грузилась 100 раз для 100 аудио-файлов.

    FIX v8.5.1 (Gemini Critical):
    Добавлен threading.Lock — двойная проверка (double-checked locking).
    Без Lock два параллельных потока могли одновременно загрузить Whisper
    (1.5GB × 2 = 3GB) → OOM crash сервера.
    """
    _instances: dict[str, Any] = {}
    _lock: threading.Lock = threading.Lock()

    @classmethod
    def get(cls, key: str, loader: Callable[[], Any]) -> Any:
        # Быстрый путь: уже загружено (без Lock, атомарно для Python GIL)
        if key in cls._instances:
            return cls._instances[key]
        # Медленный путь: загрузка с Lock — только один поток загружает
        with cls._lock:
            if key not in cls._instances:  # Double-checked locking
                logger.info(f"⏳ Loading model: {key} (первый запуск)")
                cls._instances[key] = loader()
                logger.info(f"✅ Model loaded: {key}")
        return cls._instances[key]

    @classmethod
    def clear(cls, key: str | None = None) -> None:
        if key:
            cls._instances.pop(key, None)
        else:
            cls._instances.clear()


# ─── Базовый класс парсера ────────────────────────────────────────────────────

class FileParser(ABC):
    """
    Базовый класс для всех парсеров файлов Velantrim.

    v2.0: общий enrichment, валидация размера, lazy-loading через _ModelSingleton.
    """

    file_type: str = "unknown"

    # Максимальный размер файла (можно переопределить в subclass)
    max_file_size_bytes: int = DEFAULT_MAX_FILE_SIZE_MB * 1024 * 1024

    # Размер выборки для Essence (можно переопределить в subclass)
    essence_sample_size: int = DEFAULT_ESSENCE_SAMPLE_SIZE

    @abstractmethod
    def parse(self, file_path: str) -> ParseResult:
        """Парсит файл и возвращает структурированный результат."""

    @abstractmethod
    def supported_formats(self) -> list[str]:
        """Возвращает список поддерживаемых расширений."""

    # ─── Общие хелперы ────────────────────────────────────────────────────────

    def _check_file(self, file_path: str) -> ParseResult | None:
        """
        Унифицированная валидация файла перед парсингом.
        Возвращает ParseResult с error если что-то не так, иначе None.

        v2.0: добавлена проверка max_file_size_bytes (защита от OOM).
        """
        if not os.path.exists(file_path):
            return ParseResult(
                file_path=file_path,
                file_type=self.file_type,
                error=f"Файл не найден: {file_path}",
            )

        size = os.path.getsize(file_path)
        if size > self.max_file_size_bytes:
            return ParseResult(
                file_path=file_path,
                file_type=self.file_type,
                file_size_bytes=size,
                error=(
                    f"Файл слишком большой: {size / 1024 / 1024:.1f} MB > "
                    f"{self.max_file_size_bytes / 1024 / 1024:.0f} MB лимит. "
                    f"Установи VELANTRIM_MAX_FILE_SIZE_MB для увеличения."
                ),
            )

        if size == 0:
            return ParseResult(
                file_path=file_path,
                file_type=self.file_type,
                error="Пустой файл (0 байт)",
            )

        return None  # OK, можно парсить

    def _get_file_size(self, file_path: str) -> int:
        """Размер файла в байтах."""
        return os.path.getsize(file_path) if os.path.exists(file_path) else 0

    def _build_provenance(self, file_path: str, method: str) -> dict[str, Any]:
        """Создаёт provenance-запись в формате W3C PROV-O."""
        return {
            "prov:wasGeneratedBy": f"Velantrim {self.__class__.__name__} + {method}",
            "prov:used": file_path,
            "prov:generatedAtTime": datetime.now(UTC).isoformat(),
            "velantrim:parser": self.__class__.__name__,
            "velantrim:extraction_method": method,
            "velantrim:file_size_bytes": self._get_file_size(file_path),
            "velantrim:parser_version": "2.0",
        }

    def _enrich_with_essence(self, result: ParseResult) -> ParseResult:
        """
        Общий enrichment через EssenceExtractorV5 + PearlLogic.

        v2.0: ВЫНЕСЕН ИЗ ВСЕХ ПАРСЕРОВ В БАЗОВЫЙ КЛАСС (раньше — 6 дубликатов).
        Каждый парсер получает enrichment бесплатно через self._enrich_with_essence().

        Безопасно: если EssenceExtractorV5 или PearlLogic не установлены —
        просто пропускает enrichment без ошибки.
        """
        if not result.extracted_text or not result.extracted_text.strip():
            return result

        # Essence extraction
        try:
            from essence_extractor_v5 import EssenceExtractorV5
            extractor = EssenceExtractorV5()
            essences = extractor.extract(
                result.extracted_text[: self.essence_sample_size],
                source=f"{self.file_type}:{result.file_path}",
            )
            if essences:
                result.essence = extractor.to_beautiful_dict(essences[0])
        except ImportError:
            result.warnings.append("EssenceExtractorV5 не установлен — essence skipped")
        except Exception as exc:
            logger.warning(f"Essence enrichment failed: {exc}")
            result.warnings.append(f"essence_error: {exc}")

        # Classification через Pearl Logic
        if result.essence:
            try:
                from pearl_logic import PearlLogic
                pearl = PearlLogic()
                # Создаём временный объект для classify
                class _ClassifyContext:
                    source = f"{self.file_type}_parser"
                    confidence = 0.85
                c = pearl.classify(_ClassifyContext(), {"claim_status": "pending"})
                result.classification = {
                    "knowledge_type": c.knowledge_type.value,
                    "edge_type": c.edge_type.value,
                    "trust_level": c.trust_level,
                    "reason": c.reason,
                }
            except ImportError:
                pass  # PearlLogic опциональный — без warning
            except Exception as exc:
                logger.debug(f"Pearl classification failed: {exc}")

        return result


# ─── Реестр парсеров ──────────────────────────────────────────────────────────

class ParserRegistry:
    """
    Singleton реестр парсеров. Альтернатива хардкоду в FileIngester.__init__.

    v2.0: добавление нового парсера = одна строка вместо правки 4 файлов.

    Использование:
        registry = ParserRegistry()
        registry.register("pdf", PDFParser, [".pdf"])
        registry.register("epub", EPUBParser, [".epub", ".mobi"])
        parser = registry.get_parser_for(".pdf")
    """

    _instance: Optional["ParserRegistry"] = None
    _parsers: dict[str, type] = {}          # type_name → ParserClass
    _extension_map: dict[str, str] = {}     # extension → type_name
    _initialized: dict[str, FileParser] = {}  # lazy инстансы

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def register(
        self,
        parser_type: str,
        parser_class: type,
        extensions: list[str],
    ) -> None:
        """Регистрирует парсер для набора расширений."""
        self._parsers[parser_type] = parser_class
        for ext in extensions:
            ext = ext.lower()
            if not ext.startswith("."):
                ext = "." + ext
            self._extension_map[ext] = parser_type

    def get_parser_for(self, extension: str) -> FileParser | None:
        """
        Возвращает парсер для расширения. Инстанс создаётся лениво.
        """
        ext = extension.lower()
        if not ext.startswith("."):
            ext = "." + ext

        parser_type = self._extension_map.get(ext)
        if not parser_type:
            return None

        if parser_type not in self._initialized:
            self._initialized[parser_type] = self._parsers[parser_type]()
        return self._initialized[parser_type]

    def supported_extensions(self) -> list[str]:
        """Все зарегистрированные расширения."""
        return sorted(self._extension_map.keys())

    def parsers_by_type(self) -> dict[str, list[str]]:
        """Карта `тип → расширения` для отчётов."""
        result: dict[str, list[str]] = {}
        for ext, ptype in self._extension_map.items():
            result.setdefault(ptype, []).append(ext)
        return {k: sorted(v) for k, v in result.items()}
