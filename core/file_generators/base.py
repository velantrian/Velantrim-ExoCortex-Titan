"""
🎨 Velantrim File Generators v1.0 — Base
==========================================
Зеркальный модуль для core/file_parsers/, но в обратном направлении:
    Facts → GenerationSpec → File (PDF/DOCX/PPTX/XLSX/HTML/MD)

Философия: «Любой факт → красиво оформленный документ»

Архитектура параллельна парсеру:
    FileParser → ParseResult → fact_dict
    FileGenerator ← GenerationResult ← GenerationSpec

Принципы оформления (вдохновлено Claude skills):
- Минимализм по умолчанию, но возможность пышного брендинга
- Семантические темы (clean/scientific/business/dark)
- Все размеры в семантических единицах (xs/sm/md/lg/xl)
- Профессиональные цветовые палитры из дизайн-систем
- Адаптивная типографика (relative line-height, modular scale)
"""

import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("velantrim.generators.base")


# ═══════════════════════════════════════════════════════════════════════════════
# 🎨 ТЕМЫ ОФОРМЛЕНИЯ — единый источник для всех генераторов
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Theme:
    """Семантическая тема оформления документа."""
    name: str
    # Цвета (hex без #)
    primary: str          # Основной акцент
    secondary: str        # Вторичный
    accent: str           # Выделение
    text: str             # Основной текст
    text_muted: str       # Приглушённый
    background: str       # Фон
    surface: str          # Поверхность карточек
    border: str           # Границы
    success: str
    warning: str
    danger: str
    # Типографика
    font_heading: str     # Заголовки
    font_body: str        # Основной текст
    font_mono: str        # Моноширинный
    # FIX v8.5.2 (Claude audit): варианты body-/heading-шрифтов для ReportLab.
    # До этого THEME_SCIENTIFIC передавал font_body_bold/font_body_italic/
    # font_body_bold_italic — но Theme их не принимал → TypeError при инстанцировании.
    # Дополнительно font_heading_bold нужен для табличных заголовков: для
    # Times-Roman нет варианта "Times-Roman-Bold", только "Times-Bold".
    # Дефолт None — генератор подставляет fallback (обычно font_X + "-Bold/-Oblique").
    font_body_bold: str | None = None
    font_body_italic: str | None = None
    font_body_bold_italic: str | None = None
    font_heading_bold: str | None = None
    # Размеры (в pt для документов)
    size_xs: int = 8
    size_sm: int = 10
    size_md: int = 11
    size_lg: int = 14
    size_xl: int = 18
    size_2xl: int = 24
    size_3xl: int = 32
    size_4xl: int = 48
    # Отступы (в pt для PDF, в EMU для DOCX/PPTX)
    spacing_xs: float = 4
    spacing_sm: float = 8
    spacing_md: float = 16
    spacing_lg: float = 24
    spacing_xl: float = 32


# Предустановленные темы — выбраны из проверенных дизайн-систем 2026

THEME_CLEAN = Theme(
    name="clean",
    primary="2563EB",          # blue-600 (Tailwind)
    secondary="64748B",         # slate-500
    accent="0EA5E9",            # sky-500
    text="0F172A",              # slate-900
    text_muted="64748B",
    background="FFFFFF",
    surface="F8FAFC",           # slate-50
    border="E2E8F0",            # slate-200
    success="16A34A",           # green-600
    warning="EA580C",           # orange-600
    danger="DC2626",            # red-600
    font_heading="Helvetica",
    font_body="Helvetica",
    font_mono="Courier",
)

THEME_SCIENTIFIC = Theme(
    name="scientific",
    primary="1E40AF",          # blue-800, академический
    secondary="475569",
    accent="0F766E",            # teal-700
    text="030712",
    text_muted="4B5563",
    background="FFFFFF",
    surface="F9FAFB",
    border="D1D5DB",
    success="166534",
    warning="C2410C",
    danger="991B1B",
    font_heading="Times-Roman",
    font_body="Times-Roman",
    # FIX v8.5.1: явные имена шрифтов для ReportLab
    # "Times-Roman-Bold" не существует — только "Times-Bold"
    font_body_bold="Times-Bold",
    font_body_italic="Times-Italic",
    font_body_bold_italic="Times-BoldItalic",
    # FIX v8.5.2 (Claude audit): heading тоже Times-Bold, не Times-Roman-Bold
    font_heading_bold="Times-Bold",
    font_mono="Courier",
)

THEME_BUSINESS = Theme(
    name="business",
    primary="0F172A",          # slate-900 (строгий)
    secondary="334155",
    accent="C2410C",            # orange-700 — единственный акцент
    text="0F172A",
    text_muted="475569",
    background="FFFFFF",
    surface="F1F5F9",
    border="CBD5E1",
    success="15803D",
    warning="A16207",
    danger="B91C1C",
    font_heading="Helvetica",
    font_body="Helvetica",
    font_mono="Courier",
)

THEME_DARK = Theme(
    name="dark",
    primary="60A5FA",          # blue-400
    secondary="94A3B8",
    accent="A78BFA",            # violet-400
    text="F1F5F9",
    text_muted="94A3B8",
    background="0F172A",
    surface="1E293B",
    border="334155",
    success="4ADE80",
    warning="FB923C",
    danger="F87171",
    font_heading="Helvetica",
    font_body="Helvetica",
    font_mono="Courier",
)

THEME_VELANTRIM = Theme(
    name="velantrim",
    primary="0891B2",          # cyan-600 (фирменный Velantrim)
    secondary="6366F1",         # indigo-500
    accent="EC4899",            # pink-500
    text="0F172A",
    text_muted="64748B",
    background="FFFFFF",
    surface="ECFEFF",           # cyan-50
    border="A5F3FC",            # cyan-200
    success="059669",
    warning="D97706",
    danger="DC2626",
    font_heading="Helvetica",
    font_body="Helvetica",
    font_mono="Courier",
)


THEMES: dict[str, Theme] = {
    "clean": THEME_CLEAN,
    "scientific": THEME_SCIENTIFIC,
    "business": THEME_BUSINESS,
    "dark": THEME_DARK,
    "velantrim": THEME_VELANTRIM,
}


def get_theme(name: str = "clean") -> Theme:
    """Получить тему по имени. Default = clean."""
    return THEMES.get(name, THEME_CLEAN)


# ═══════════════════════════════════════════════════════════════════════════════
# 📦 КОНТЕНТНЫЕ БЛОКИ — Document Object Model
# ═══════════════════════════════════════════════════════════════════════════════
# Промежуточное представление документа, независимое от формата.
# Так PDF, DOCX, PPTX, HTML генераторы получают одни и те же блоки
# и оформляют их по-разному.

@dataclass
class Block:
    """Базовый контентный блок."""
    block_type: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class HeadingBlock(Block):
    """Заголовок (h1-h6 эквивалент)."""
    text: str = ""
    level: int = 1
    block_type: str = "heading"


@dataclass
class ParagraphBlock(Block):
    """Параграф текста."""
    text: str = ""
    style: str = "normal"   # normal | bold | italic | callout | quote
    block_type: str = "paragraph"


@dataclass
class ListBlock(Block):
    """Список (упорядоченный/неупорядоченный)."""
    items: list[str] = field(default_factory=list)
    ordered: bool = False
    block_type: str = "list"


@dataclass
class TableBlock(Block):
    """Таблица."""
    headers: list[str] = field(default_factory=list)
    rows: list[list[Any]] = field(default_factory=list)
    caption: str | None = None
    block_type: str = "table"


@dataclass
class CodeBlock(Block):
    """Блок кода."""
    code: str = ""
    language: str = "python"
    caption: str | None = None
    block_type: str = "code"


@dataclass
class ImageBlock(Block):
    """Изображение."""
    path: str = ""             # путь к файлу или URL
    caption: str | None = None
    width: int | None = None
    height: int | None = None
    block_type: str = "image"


@dataclass
class CalloutBlock(Block):
    """Выделенный блок (info/warning/success/danger)."""
    text: str = ""
    callout_type: str = "info"    # info | warning | success | danger
    title: str | None = None
    block_type: str = "callout"


@dataclass
class QuoteBlock(Block):
    """Цитата."""
    text: str = ""
    author: str | None = None
    block_type: str = "quote"


@dataclass
class DividerBlock(Block):
    """Горизонтальная линия."""
    block_type: str = "divider"


@dataclass
class FactBlock(Block):
    """
    Velantrim-специфичный блок — оформление факта со всеми метаданными.
    Используется когда нужно красиво показать факт из памяти.
    """
    fact_id: str = ""
    claim: str = ""
    confidence: float = 0.0
    source: str = ""
    epistemic_state: str = "Observed"
    block_type: str = "fact"


# ═══════════════════════════════════════════════════════════════════════════════
# 📋 СПЕЦИФИКАЦИЯ ДОКУМЕНТА
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class DocumentMetadata:
    """Метаданные документа."""
    title: str = "Untitled"
    author: str = "Velantrim ExoCortex"
    subject: str = ""
    keywords: list[str] = field(default_factory=list)
    description: str = ""
    created: str | None = None       # ISO timestamp
    language: str = "ru"


@dataclass
class GenerationSpec:
    """
    Спецификация документа для генерации.
    Передаётся в любой генератор — он отрисует её в своём формате.

    Использование:
        spec = GenerationSpec(
            metadata=DocumentMetadata(title="Отчёт"),
            theme="velantrim",
            blocks=[
                HeadingBlock(text="Анализ", level=1),
                ParagraphBlock(text="Введение..."),
                TableBlock(headers=["Метрика", "Значение"], rows=[...]),
            ]
        )
        generator.generate(spec, "/output/report.pdf")
    """
    metadata: DocumentMetadata = field(default_factory=DocumentMetadata)
    theme: str = "clean"                # имя темы из THEMES
    blocks: list[Block] = field(default_factory=list)
    options: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_facts(
        cls,
        facts: list[dict[str, Any]],
        title: str = "Velantrim Facts Report",
        theme: str = "velantrim",
        include_metadata: bool = True,
    ) -> "GenerationSpec":
        """
        Удобный конструктор: список фактов → готовая спецификация.
        Каждый факт превращается в FactBlock с раскрытыми метаданными.
        """
        meta = DocumentMetadata(
            title=title,
            subject=f"Velantrim ExoCortex report ({len(facts)} facts)",
            created=datetime.now(UTC).isoformat(),
        )
        blocks: list[Block] = [
            HeadingBlock(text=title, level=1),
            ParagraphBlock(
                text=f"Отчёт содержит {len(facts)} фактов из памяти Velantrim. "
                     f"Сгенерирован {datetime.now().strftime('%d.%m.%Y %H:%M')}.",
                style="callout",
            ),
            DividerBlock(),
        ]
        for fact in facts:
            blocks.append(FactBlock(
                fact_id=fact.get("fact_id", ""),
                claim=fact.get("claim", ""),
                confidence=fact.get("confidence", 0.0),
                source=fact.get("source", ""),
                epistemic_state=fact.get("epistemic_state", "Observed"),
            ))
        if include_metadata:
            blocks.append(DividerBlock())
            blocks.append(HeadingBlock(text="📊 Сводка", level=2))
            blocks.append(_summary_table_from_facts(facts))
        return cls(metadata=meta, theme=theme, blocks=blocks)


def _summary_table_from_facts(facts: list[dict]) -> TableBlock:
    """Внутренний helper: сводная статистика по фактам."""
    # Подсчёт по epistemic_state
    states: dict[str, int] = {}
    confidences: list[float] = []
    for f in facts:
        s = f.get("epistemic_state", "Observed")
        states[s] = states.get(s, 0) + 1
        confidences.append(f.get("confidence", 0.0))

    rows = []
    rows.append(["Всего фактов", str(len(facts))])
    rows.append(["Средняя уверенность", f"{sum(confidences) / len(confidences):.3f}" if confidences else "—"])
    for state, count in sorted(states.items(), key=lambda x: -x[1]):
        rows.append([f"  {state}", str(count)])

    return TableBlock(
        headers=["Метрика", "Значение"],
        rows=rows,
        caption="Сводная статистика по фактам",
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 📤 РЕЗУЛЬТАТ ГЕНЕРАЦИИ
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class GenerationResult:
    """Результат генерации — зеркало ParseResult."""
    output_path: str
    format: str
    file_size_bytes: int = 0
    page_count: int | None = None
    block_count: int = 0
    generation_time_ms: float = 0.0
    method: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    error: str | None = None

    @property
    def success(self) -> bool:
        return self.error is None and os.path.exists(self.output_path)


# ═══════════════════════════════════════════════════════════════════════════════
# 🏗️ БАЗОВЫЙ КЛАСС ГЕНЕРАТОРА
# ═══════════════════════════════════════════════════════════════════════════════

class FileGenerator(ABC):
    """
    Базовый класс для всех генераторов.
    Каждый генератор знает свой формат и умеет отрисовать GenerationSpec.
    """
    format_name: str = "unknown"

    @abstractmethod
    def generate(
        self,
        spec: GenerationSpec,
        output_path: str,
    ) -> GenerationResult:
        """Генерирует файл из спецификации."""

    @abstractmethod
    def supported_extensions(self) -> list[str]:
        """Расширения которые умеет создавать."""

    # ─── Общие хелперы ────────────────────────────────────────────────────────

    def _ensure_output_dir(self, output_path: str) -> None:
        """Создаёт директорию для output если её нет."""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    def _build_provenance(self, output_path: str) -> dict[str, Any]:
        """W3C PROV-O metadata."""
        return {
            "prov:wasGeneratedBy": f"Velantrim {self.__class__.__name__}",
            "prov:generatedAtTime": datetime.now(UTC).isoformat(),
            "velantrim:generator": self.__class__.__name__,
            "velantrim:format": self.format_name,
            "velantrim:output_path": output_path,
        }

    def _file_size(self, path: str) -> int:
        return os.path.getsize(path) if os.path.exists(path) else 0

    @staticmethod
    def _confidence_to_label(conf: float) -> str:
        """Преобразует confidence в текстовую метку для отображения."""
        if conf >= 0.9:
            return "🟢 высокая"
        if conf >= 0.7:
            return "🟡 средняя"
        if conf >= 0.5:
            return "🟠 низкая"
        return "🔴 очень низкая"


# ═══════════════════════════════════════════════════════════════════════════════
# 🗂️ РЕЕСТР ГЕНЕРАТОРОВ
# ═══════════════════════════════════════════════════════════════════════════════

class GeneratorRegistry:
    """
    Singleton реестр генераторов — зеркало ParserRegistry.
    """
    _instance: Optional["GeneratorRegistry"] = None
    _generators: dict[str, type] = {}
    _extension_map: dict[str, str] = {}
    _initialized: dict[str, FileGenerator] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def register(
        self,
        format_name: str,
        generator_class: type,
        extensions: list[str],
    ) -> None:
        self._generators[format_name] = generator_class
        for ext in extensions:
            ext = ext.lower()
            if not ext.startswith("."):
                ext = "." + ext
            self._extension_map[ext] = format_name

    def get_generator_for(self, extension: str) -> FileGenerator | None:
        ext = extension.lower()
        if not ext.startswith("."):
            ext = "." + ext
        format_name = self._extension_map.get(ext)
        if not format_name:
            return None
        if format_name not in self._initialized:
            self._initialized[format_name] = self._generators[format_name]()
        return self._initialized[format_name]

    def supported_extensions(self) -> list[str]:
        return sorted(self._extension_map.keys())
