# 📊 XLSX Generation Skill

Best practices для создания **Excel таблиц** через `core.file_generators.XLSXGenerator`.

---

## 🎯 Когда XLSX

| Сценарий | Подходит? |
|---|---|
| Данные для дальнейшего анализа в Excel | ✅ Идеально |
| Финансовые модели с формулами | ✅ |
| Multi-sheet workbook с разными датасетами | ✅ |
| Conditional formatting (цветовая разметка) | ✅ |
| Текстовый отчёт | ❌ → DOCX/PDF |
| Презентация | ❌ → PPTX |

---

## ✅ DO

### Каждая таблица — отдельный лист

```python
spec = GenerationSpec(
    metadata=DocumentMetadata(title="Q1 Data"),
    theme="business",
    blocks=[
        HeadingBlock(text="Memory Metrics", level=1),  # ← имя листа
        TableBlock(headers=[...], rows=[...]),

        HeadingBlock(text="Top Validated Facts", level=1),  # ← новый лист
        TableBlock(headers=[...], rows=[...]),

        HeadingBlock(text="TruthGate Verdicts", level=1),
        TableBlock(headers=[...], rows=[...]),
    ],
)
```

XLSXGenerator автоматически:
- Создаёт лист **📊 Summary** первым (метаданные + статистика)
- Создаёт лист **🔱 Facts** для FactBlock'ов с conditional formatting на confidence
- Создаёт лист **📝 Notes** для всех ParagraphBlock
- Каждый TableBlock → отдельный лист, имя из `caption` или предыдущего HeadingBlock

### Conditional formatting для confidence

В листе Facts автоматически:
- Confidence ≥ 0.9 → 🟢 зелёная заливка
- 0.5 ≤ confidence < 0.9 → 🟡 жёлтая
- < 0.5 → 🔴 красная

Это работает ТОЛЬКО для FactBlock — поэтому используй их вместо TableBlock когда данные — это факты из ESM.

### Headers с темой

Заголовки автоматически получают:
- Фон по `theme.primary`
- Цвет текста по `theme.background`
- Жирный, центрированный
- Заморожены через `freeze_panes = "A2"`

Не нужно стилизовать руками.

---

## ❌ DON'T

### Не пиши длинный текст в ячейку

Excel не предназначен для длинных параграфов. Если ячейка >100 символов — выноси в отдельный лист Notes или используй DOCX.

### Не делай таблицы >20 колонок без причины

Excel это позволяет, но читать будет невозможно. Лучше разбей на несколько листов.

### Не используй HeadingBlock для оформления внутри таблицы

HeadingBlock = название следующего листа. Если хочешь подзаголовок ВНУТРИ таблицы — это row с emoji "🔷 ..." в первой колонке.

---

## 🎯 Шаблоны

### Шаблон: Validated facts → анализ в Excel

```python
def facts_for_analysis(facts: list):
    """Готовый workbook для анализа фактов в Excel."""
    return GenerationSpec(
        metadata=DocumentMetadata(
            title="Velantrim Facts Dataset",
            author="Velantrim ExoCortex",
            subject=f"{len(facts)} facts for analysis",
        ),
        theme="business",
        blocks=[
            HeadingBlock(text="📊 All Facts", level=1),
            # FactBlock даёт conditional formatting на confidence автоматом
            *[FactBlock(
                fact_id=f["fact_id"],
                claim=f["claim"],
                confidence=f["confidence"],
                epistemic_state=f["epistemic_state"],
                source=f["source"],
            ) for f in facts],
        ],
    )
```

Результат: workbook с 3 листами — Summary (метрики), 🔱 Facts (главное с цветовой кодировкой), Notes (пусто или с описаниями).

### Шаблон: финансовый отчёт

```python
def financial_report(periods, metrics):
    return GenerationSpec(
        metadata=DocumentMetadata(title="Q1 2026 Financials"),
        theme="business",
        blocks=[
            HeadingBlock(text="Revenue", level=1),
            TableBlock(
                headers=["Channel"] + periods,
                rows=metrics["revenue"],
                caption="Доходы по каналам",
            ),
            HeadingBlock(text="Expenses", level=1),
            TableBlock(
                headers=["Category"] + periods,
                rows=metrics["expenses"],
                caption="Расходы",
            ),
            HeadingBlock(text="Profit", level=1),
            TableBlock(
                headers=["Метрика"] + periods,
                rows=metrics["profit"],
                caption="Прибыль",
            ),
        ],
    )
```

---

## 🔧 Технические нюансы

### Имена листов

Excel ограничивает имена листов:
- Максимум 31 символ (генератор обрезает автоматически)
- Запрещены: `/ \ * ? [ ] :` (генератор заменяет на `_`)
- Должны быть уникальны (генератор добавляет суффикс `(1)`, `(2)` при коллизии)

### Auto-fit ширины колонок

Генератор пытается подобрать ширину = max длины контента + 4 знака, но не больше 60. Если нужна точная ширина — расширь `_render_table_sheet`.

### Формулы

Сейчас генератор НЕ умеет вставлять Excel-формулы (`=SUM(A1:A10)`). Все значения вставляются как литералы. Если нужны формулы — это Sprint 2c расширение.

### Числа vs строки

Если в `rows` передаёшь числа (`int`, `float`) — Excel поймёт их как числа и можно делать математику. Если строки `"42"` — как текст, формулы не сработают.

```python
# ✅ Хорошо
TableBlock(rows=[["Q1", 1240, 3.42]])

# ❌ Плохо
TableBlock(rows=[["Q1", "1240", "3.42"]])
```

### Conditional formatting и стили

Сейчас CF применяется только к колонке Confidence на листе 🔱 Facts. Если нужно больше CF (на TableBlock, кастомные правила) — это Sprint 2c.
