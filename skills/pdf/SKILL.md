# 📄 PDF Generation Skill

Best practices для создания **красивых, профессиональных PDF** документов через `core.file_generators.PDFGenerator`.

Этот skill — карта решений «когда что использовать» для Velantrim. Когда нужно создать PDF, прочти это первым.

---

## 🎯 Когда использовать PDF

| Сценарий | Подходит? |
|---|---|
| Финальный отчёт для архива (read-only) | ✅ Идеально |
| Документ для печати / подписи | ✅ Идеально |
| Отправка stakeholders | ✅ Идеально |
| Контент для редактирования | ❌ → DOCX |
| Динамические данные | ❌ → HTML |
| Длинная книга (>100 стр.) | ⚠️ → EPUB через `universal_generator` |
| Презентация | ❌ → PPTX |
| Таблицы с формулами | ❌ → XLSX |

---

## 🎨 Выбор темы

```python
from core.file_generators import FileExporter, GenerationSpec, DocumentMetadata

# Правило выбора:
# - Внутренний отчёт о здоровье памяти → "velantrim"
# - Документ для научной публикации → "scientific"
# - Корпоративный отчёт инвесторам → "business"
# - Архивный аудит → "clean"
# - Презентация в тёмном зале → "dark"

spec = GenerationSpec(
    metadata=DocumentMetadata(title="..."),
    theme="velantrim",  # ← выбери одну из 5
    blocks=[...],
)
```

---

## ✅ DO — что делать

### Структурированный отчёт с разделами

```python
from core.file_generators import (
    GenerationSpec, DocumentMetadata,
    HeadingBlock, ParagraphBlock, TableBlock,
    CalloutBlock, DividerBlock, FactBlock,
)

spec = GenerationSpec(
    metadata=DocumentMetadata(
        title="Quarterly Memory Report",
        author="Velantrim ExoCortex",
        subject="Q1 2026 health audit",
        keywords=["mhi", "memory", "audit"],
        description="Анализ здоровья памяти за квартал",
    ),
    theme="velantrim",
    blocks=[
        # 1. Краткое резюме сверху — главный результат
        CalloutBlock(
            callout_type="success",
            title="Главный результат",
            text="MHI вырос с 0.62 до 0.84 за квартал.",
        ),
        DividerBlock(),

        # 2. Содержание через H1/H2/H3 (для TOC и навигации)
        HeadingBlock(text="Введение", level=1),
        ParagraphBlock(text="..."),

        HeadingBlock(text="Метрики", level=2),
        TableBlock(
            headers=["Метрика", "Q4 2025", "Q1 2026", "Δ"],
            rows=[...],
            caption="Динамика ключевых метрик",
        ),
    ],
)
```

### Использование FactBlock для фактов из памяти

```python
# 🔱 Velantrim-специфично: для каждого факта из ESM используй FactBlock,
# а не плоский ParagraphBlock. Тогда автоматически рендерится:
# - claim как заголовок
# - метаданные снизу (id, confidence, state, source)
# - цвет рамки слева по epistemic_state (зелёный=Validated, ...)

FactBlock(
    fact_id="f_quantum_001",
    claim="Квантовая запутанность не передаёт информацию быстрее света",
    confidence=0.98,
    epistemic_state="Validated",
    source="physics:Aspect_2022",
)
```

### Иерархия заголовков

```python
HeadingBlock(text="Глава 1", level=1)        # h1 — крупный, в цвете темы
HeadingBlock(text="1.1 Раздел", level=2)     # h2 — секции
HeadingBlock(text="1.1.1 Подраздел", level=3) # h3 — детали
# level=4-6 редко нужно, h3 обычно достаточно
```

### Таблицы со смыслом

```python
TableBlock(
    headers=["Метрика", "Значение", "Тренд"],
    rows=[
        ["MHI", "0.84", "↑ +35%"],
        ["Validated facts", "3,890", "↑ +213%"],
    ],
    caption="Ключевые метрики Q1 2026",   # ← caption обязателен для таблиц с данными
)
```

### Callouts по семантике

```python
CalloutBlock(callout_type="info",    title="ℹ️ Заметка", text="...")
CalloutBlock(callout_type="success", title="✅ Успех",  text="...")
CalloutBlock(callout_type="warning", title="⚠️ Внимание", text="...")
CalloutBlock(callout_type="danger",  title="🚨 Критично",  text="...")
```

---

## ❌ DON'T — чего избегать

### Не повторяй заголовок документа в первом H1

```python
# ❌ ПЛОХО — дублирование с title в metadata
spec = GenerationSpec(
    metadata=DocumentMetadata(title="Отчёт Q1"),
    blocks=[
        HeadingBlock(text="Отчёт Q1", level=1),  # ← дублирует title
        ...
    ]
)

# ✅ ХОРОШО — title уже в header документа
spec = GenerationSpec(
    metadata=DocumentMetadata(title="Отчёт Q1"),
    blocks=[
        HeadingBlock(text="Введение", level=1),  # ← сразу контент
        ...
    ]
)
```

### Не злоупотребляй жирным/курсивом

```python
# ❌ Каждое второе слово болдом — читать невозможно
ParagraphBlock(text="**Это** очень **важный** **факт** о **квантовой** **физике**", style="bold")

# ✅ Болдом — ключевое утверждение раз в параграф
ParagraphBlock(text="Это важный факт о квантовой физике."),
ParagraphBlock(text="Главное здесь — нелокальность.", style="bold"),
```

### Не делай таблицу шире 6 колонок

PDF A4 портрет вмещает максимум 6 колонок читаемо. Если больше — либо landscape, либо разбей на несколько таблиц, либо вынеси в XLSX.

### Не используй `level=6` без нужды

```python
# ❌ Никто не различит h5 и h6 на бумаге
HeadingBlock(text="Подподподраздел", level=6)

# ✅ Используй callout или bold parahgraph для дальнейшей детализации
```

### Не вставляй огромные code blocks

PDF плохо для кода >50 строк. Лучше — ссылка на GitHub/Gist в `ParagraphBlock`, или экспорт отдельным `.py` файлом.

---

## 📐 Профессиональные шаблоны

### 🔬 Шаблон 1: Аудит-отчёт TruthGate

```python
def truthgate_audit_report(verdicts: list, theme: str = "scientific"):
    blocks = [
        # Executive summary
        CalloutBlock(
            callout_type="info",
            title="Сводка аудита",
            text=f"Проверено {len(verdicts)} фактов. "
                 f"Прошли: {sum(1 for v in verdicts if v.passed)}. "
                 f"Отклонены: {sum(1 for v in verdicts if not v.passed)}.",
        ),
        DividerBlock(),
        HeadingBlock(text="Детальная таблица", level=2),
        TableBlock(
            headers=["Fact ID", "Mode", "Verdict", "Reason"],
            rows=[
                [v.fact_id, v.mode.value,
                 "✅ Passed" if v.passed else "❌ Rejected",
                 v.reason]
                for v in verdicts
            ],
            caption="TruthGate verdicts",
        ),
        DividerBlock(),
        HeadingBlock(text="Отклонённые факты", level=2),
    ]
    for v in verdicts:
        if not v.passed:
            blocks.append(FactBlock(
                fact_id=v.fact_id,
                claim=v.fact_claim,
                confidence=v.confidence,
                epistemic_state="Hypothesized",
                source=v.source,
            ))
    return GenerationSpec(
        metadata=DocumentMetadata(title="🛡️ TruthGate Audit"),
        theme=theme,
        blocks=blocks,
    )
```

### 📊 Шаблон 2: MHI Dashboard

```python
def mhi_dashboard(mhi_report, theme: str = "velantrim"):
    status_emoji = {"HEALTHY": "🟢", "DEGRADED": "🟡", "SAFE_MODE": "🔴"}
    callout_type = {"HEALTHY": "success", "DEGRADED": "warning", "SAFE_MODE": "danger"}

    return GenerationSpec(
        metadata=DocumentMetadata(
            title=f"📊 Memory Health Index",
            subject=f"MHI = {mhi_report.score:.3f} ({mhi_report.status.value})",
        ),
        theme=theme,
        blocks=[
            CalloutBlock(
                callout_type=callout_type[mhi_report.status.value],
                title=f"{status_emoji[mhi_report.status.value]} {mhi_report.status.value}",
                text=f"MHI = {mhi_report.score:.3f}",
            ),
            HeadingBlock(text="Компоненты MHI", level=2),
            TableBlock(
                headers=["Компонент", "Значение", "Вклад"],
                rows=[
                    ["Validated Ratio", f"{mhi_report.validated_ratio:.3f}", "30%"],
                    ["Freshness",       f"{mhi_report.freshness:.3f}",       "25%"],
                    ["Precision",       f"{mhi_report.retrieval_precision:.3f}", "25%"],
                    ["Graph Coverage",  f"{mhi_report.graph_coverage:.3f}",  "20%"],
                ],
            ),
            HeadingBlock(text="Рекомендации", level=2),
            *[ParagraphBlock(text=f"• {rec}") for rec in mhi_report.recommendations],
        ],
    )
```

### 📖 Шаблон 3: Validated Knowledge Base

```python
def validated_knowledge_book(facts: list, theme: str = "scientific"):
    blocks = [
        HeadingBlock(text="🔱 Velantrim Knowledge Base", level=1),
        ParagraphBlock(
            text=f"Эта база содержит {len(facts)} верифицированных фактов "
                 f"из памяти Velantrim ExoCortex.",
            style="callout",
        ),
        DividerBlock(),
    ]
    # Группируем по source
    by_source = {}
    for f in facts:
        by_source.setdefault(f["source"], []).append(f)
    for source, source_facts in sorted(by_source.items()):
        blocks.append(HeadingBlock(text=f"📂 {source}", level=2))
        for fact in source_facts:
            blocks.append(FactBlock(
                fact_id=fact["fact_id"],
                claim=fact["claim"],
                confidence=fact["confidence"],
                epistemic_state=fact["epistemic_state"],
                source=fact["source"],
            ))
    return GenerationSpec(
        metadata=DocumentMetadata(
            title="🔱 Velantrim Knowledge Base",
            subject=f"{len(facts)} validated facts",
        ),
        theme=theme,
        blocks=blocks,
    )
```

---

## 🔧 Технические нюансы

### Размер шрифта vs тема

Темы устанавливают семантические размеры (`size_xs`/`sm`/`md`/`lg`/`xl`/`2xl`/`3xl`/`4xl`). Не задавай размеры напрямую — используй темы.

### Кириллица

ReportLab поддерживает кириллицу из коробки через встроенные шрифты Helvetica и Times. Если нужны кастомные шрифты — регистрируй через `pdfmetrics.registerFont()` ДО создания спецификации.

### Большие документы (>50 страниц)

- Используй `DividerBlock` между логическими секциями для visual rhythm
- TableBlock автоматически повторяет header на каждой странице (`repeatRows=1`)
- Изображения ресайзятся через `block.width` (в pixels)

### Footer и pagination

Footer пишется автоматически: `Velantrim ExoCortex • {author} • Стр. {page}`. Если нужен кастомный — нужно расширять `PDFGenerator._render_reportlab`.

---

## 🎯 Чек-лист перед генерацией

- [ ] Заголовок описывает содержимое (не "Отчёт", а "Memory Health Q1 2026")
- [ ] Author заполнен
- [ ] Тема соответствует аудитории
- [ ] Executive summary в начале (CalloutBlock)
- [ ] Иерархия заголовков 1-3 уровня
- [ ] Таблицы имеют caption
- [ ] Изображения имеют caption
- [ ] FactBlock для фактов из ESM (не ParagraphBlock!)
- [ ] DividerBlock между крупными разделами
- [ ] Нет h6, нет 8-колоночных таблиц, нет 100-строчных code blocks

---

## 📚 Дополнительно

- HTML аналог: `core/file_generators/SKILL_html.md`
- DOCX аналог: `core/file_generators/SKILL_docx.md`
- PPTX аналог: `core/file_generators/SKILL_pptx.md`
- Полный API: `core/file_generators/README.md`
