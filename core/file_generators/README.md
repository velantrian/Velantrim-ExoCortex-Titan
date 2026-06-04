# 🎨 Velantrim File Generators v1.0

> Создание красивых документов из фактов Velantrim ExoCortex.
> Этап 2 — зеркальный модуль к `core/file_parsers/`.

---

## 🎯 Что умеет

| Формат | Библиотека | Особенности |
|---|---|---|
| 📄 **PDF** | ReportLab | Canvas-based, точный контроль, без системных зависимостей |
| 📝 **DOCX** | python-docx | Word с темами, tracked changes, comments |
| 🎯 **PPTX** | python-pptx | 16:9 widescreen, заметки докладчика, фирменные слайды |
| 📊 **XLSX** | openpyxl | Multi-sheet, conditional formatting, auto-fit |
| 🌐 **HTML** | native Python | Standalone, inline CSS, responsive, print-friendly |
| 📋 **Markdown** | native Python | GitHub-flavored, YAML frontmatter |
| 🔄 **EPUB/LaTeX/RST/...** | pypandoc | 40+ форматов через pandoc |

---

## 🎨 Темы оформления

5 предустановленных тем — выбирай через `theme="..."` в `GenerationSpec`:

| Тема | Назначение | Палитра |
|---|---|---|
| `clean` | Универсальная, минимализм (default) | Blue + slate |
| `scientific` | Академический, статьи | Blue-800 + Times Roman |
| `business` | Строгий, корпоративный | Slate-900 + orange-700 |
| `dark` | Тёмная, презентации | Cyan + violet on dark |
| `velantrim` | Фирменный Velantrim | Cyan-600 + indigo + pink |

---

## 🚀 Использование

### Простой случай — из фактов

```python
from core.file_generators import FileExporter

exporter = FileExporter()

facts = [
    {
        "fact_id": "f1",
        "claim": "Земля имеет форму геоида",
        "confidence": 0.999,
        "epistemic_state": "Validated",
        "source": "NASA",
    },
    # ...
]

# PDF в одну строку
exporter.export_facts(facts, "report.pdf", theme="velantrim")

# То же в DOCX
exporter.export_facts(facts, "report.docx", theme="business")

# И в PowerPoint
exporter.export_facts(facts, "presentation.pptx", theme="dark")
```

### Несколько форматов одним вызовом

```python
results = exporter.export_multi(
    spec,
    output_base="/output/quarterly_report",
    formats=["pdf", "docx", "html", "xlsx", "md"],
)
# → создаст 5 файлов с одинаковым контентом, разные форматы
```

### Полная спецификация документа

```python
from core.file_generators import (
    FileExporter, GenerationSpec, DocumentMetadata,
    HeadingBlock, ParagraphBlock, TableBlock,
    CalloutBlock, FactBlock, DividerBlock,
)

spec = GenerationSpec(
    metadata=DocumentMetadata(
        title="🔱 Анализ памяти Q1 2026",
        author="Velantrim ExoCortex",
        subject="Quarterly memory health report",
        keywords=["memory", "esm", "mhi"],
    ),
    theme="velantrim",
    blocks=[
        HeadingBlock(text="Введение", level=1),
        ParagraphBlock(text="Анализ показал положительную динамику..."),
        
        CalloutBlock(
            callout_type="success",
            title="Главный результат",
            text="MHI вырос с 0.62 до 0.84 за квартал.",
        ),
        
        HeadingBlock(text="Метрики", level=2),
        TableBlock(
            headers=["Метрика", "Q4 2025", "Q1 2026", "Δ"],
            rows=[
                ["MHI", "0.62", "0.84", "+35%"],
                ["Validated facts", "1,240", "3,890", "+213%"],
                ["Avg confidence", "0.71", "0.83", "+17%"],
            ],
            caption="Динамика ключевых метрик",
        ),
        
        DividerBlock(),
        
        HeadingBlock(text="🔬 Анализ фактов", level=2),
        FactBlock(
            fact_id="quarterly_finding_001",
            claim="Drift protection предотвращает 99.3% split-brain ситуаций",
            confidence=0.993,
            epistemic_state="Validated",
            source="audit:Q1_regression_tests",
        ),
    ],
)

result = exporter.export(spec, "report.pdf")
print(f"Создан {result.output_path}, страниц: {result.page_count}")
```

---

## 📦 Контентные блоки

| Блок | Назначение | PDF | DOCX | PPTX | XLSX | HTML | MD |
|---|---|---|---|---|---|---|---|
| `HeadingBlock` | Заголовки h1-h6 | ✅ | ✅ | ✅ slide title | ✅ sheet name | ✅ | ✅ |
| `ParagraphBlock` | Параграф (normal/bold/italic/callout) | ✅ | ✅ | ✅ bullet | ✅ Notes sheet | ✅ | ✅ |
| `ListBlock` | Список (ordered/unordered) | ✅ | ✅ | ✅ bullets | — | ✅ | ✅ |
| `TableBlock` | Таблица с caption | ✅ | ✅ | ✅ slide | ✅ separate sheet | ✅ | ✅ |
| `CodeBlock` | Код с подсветкой | ✅ | ✅ | — | — | ✅ | ✅ |
| `ImageBlock` | Изображение с caption | ✅ | ✅ | ✅ slide | — | ✅ | ✅ |
| `CalloutBlock` | info/success/warning/danger | ✅ | ✅ | ✅ bullet | — | ✅ | ✅ |
| `QuoteBlock` | Цитата с автором | ✅ | ✅ | ✅ bullet | — | ✅ | ✅ |
| `DividerBlock` | Горизонтальная линия | ✅ | ✅ | — | — | ✅ | ✅ |
| `FactBlock` 🔱 | Velantrim-факт со всей метой | ✅ | ✅ | ✅ slide | ✅ Facts sheet | ✅ | ✅ |

---

## 🏗️ Архитектура

```
core/file_generators/
├── __init__.py              ← публичное API + версия
├── base.py                  ← FileGenerator ABC, блоки, темы, registry
├── file_exporter.py         ← главный оркестратор (зеркало FileIngester)
│
├── pdf_generator.py         ← ReportLab с темами
├── docx_generator.py        ← python-docx
├── pptx_generator.py        ← python-pptx, widescreen 16:9
├── xlsx_generator.py        ← openpyxl, multi-sheet, conditional formatting
├── html_generator.py        ← native HTML5, standalone, inline CSS
├── markdown_generator.py    ← native, GitHub-flavored
└── universal_generator.py   ← pypandoc для EPUB/LaTeX/RST/etc

requirements_generators.txt  ← опц. зависимости
README.md
```

---

## 🔧 Установка

```bash
# Минимум (Markdown и HTML работают без зависимостей)
# Markdown + HTML — work out of the box

# Полный стек
pip install -r requirements_generators.txt

# Для PDF через pandoc нужен LaTeX:
sudo apt install texlive-xetex                 # Ubuntu
brew install --cask basictex                    # macOS
```

---

## ⚙️ Конфигурация через ENV

| Переменная | Описание |
|---|---|
| `VELANTRIM_DISABLE_GENERATORS` | Список через запятую: `pdf,docx` отключит эти генераторы |

---

## 📐 Параллельная архитектура с парсером

Парсер и генератор — зеркальные модули с одинаковым API:

```python
# Парсинг: file → fact
parser = FileIngester()
result = parser.ingest("input.pdf")
fact = result.to_fact_dict()

# Генерация: fact → file (обратная операция)
exporter = FileExporter()
spec = GenerationSpec.from_facts([fact], theme="velantrim")
exporter.export(spec, "output.pdf")

# Round-trip возможен: parse → store → export
```

---

## 🎯 Use cases в Velantrim

### 1. Memory health dashboard
```python
from core.mhi import MHICalculator
from core.file_generators import FileExporter, GenerationSpec, ...

mhi = MHICalculator(store).calculate()
spec = GenerationSpec(
    metadata=DocumentMetadata(title=f"MHI Report: {mhi.status.value}"),
    blocks=[
        HeadingBlock(text="Memory Health Index", level=1),
        CalloutBlock(
            callout_type="success" if mhi.score > 0.6 else "warning",
            title=f"MHI = {mhi.score:.3f}",
            text=mhi.recommendations[0],
        ),
        TableBlock(headers=["Метрика", "Значение"], rows=[...]),
    ],
)
exporter.export(spec, f"reports/mhi_{date.today()}.pdf")
```

### 2. Validated facts → книга знаний
```python
from core.memory import get_all_facts
validated = get_all_facts(epistemic_state="Validated")
exporter.export_facts(
    validated,
    "knowledge_base.epub",        # через pandoc → EPUB
    title="Velantrim Knowledge Base",
    theme="scientific",
)
```

### 3. TruthGate audit report
```python
from core.truth_gate import TruthGate
verdicts = [...]
spec = GenerationSpec(blocks=[
    HeadingBlock(text="TruthGate Audit", level=1),
    TableBlock(
        headers=["Fact ID", "Mode", "Passed", "Reason"],
        rows=[[v.fact_id, v.mode.value, v.passed, v.reason] for v in verdicts],
    ),
])
exporter.export(spec, "truthgate_audit.xlsx")
```

### 4. Sprint retrospective
```python
exporter.export_multi(
    sprint_spec,
    output_base="reports/sprint_2a_retro",
    formats=["pdf", "docx", "pptx", "html"],
)
# → 4 формата одного контента: для архива, для редактирования,
#   для презентации stakeholders, для web
```
