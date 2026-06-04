# 📝 DOCX Generation Skill

Best practices для создания **профессиональных Word документов** через `core.file_generators.DOCXGenerator`.

---

## 🎯 Когда DOCX, а не PDF

| Сценарий | DOCX | PDF |
|---|---|---|
| Документ для редактирования получателем | ✅ | ❌ |
| Совместная работа над текстом | ✅ | ❌ |
| Архив / финальная версия | ❌ | ✅ |
| Печать / подпись | ❌ | ✅ |
| Контракт с track changes | ✅ | ❌ |
| Шаблон для пользователей | ✅ | ❌ |

**Правило**: DOCX — это работа, PDF — это финал.

---

## ✅ DO

### Минимальный профессиональный пример

```python
from core.file_generators import (
    FileExporter, GenerationSpec, DocumentMetadata,
    HeadingBlock, ParagraphBlock, TableBlock, CalloutBlock,
)

spec = GenerationSpec(
    metadata=DocumentMetadata(
        title="Анализ Q1 2026",
        author="Velantrim Analytics",
        subject="Quarterly memory analysis",
    ),
    theme="business",   # для деловых писем "business" лучше "velantrim"
    blocks=[
        ParagraphBlock(
            text="Этот документ — рабочий черновик. "
                 "Можно править, добавлять комментарии, треки.",
            style="callout",
        ),
        HeadingBlock(text="1. Введение", level=1),
        # ...
    ],
)
FileExporter().export(spec, "draft.docx")
```

### Нумерация разделов в заголовках

В Word нет автонумерации через `level=`. Если нужны "1.", "1.1", "1.1.1" — пиши прямо в тексте:

```python
HeadingBlock(text="1. Введение", level=1)
HeadingBlock(text="1.1 Предпосылки", level=2)
HeadingBlock(text="1.1.1 История вопроса", level=3)
```

### Использование стиля "callout" для рабочих заметок

```python
# Курсив + приглушённый цвет = идеально для "TODO" и заметок автора
ParagraphBlock(
    text="TODO: проверить эти цифры до финальной версии.",
    style="callout",
)
```

### Single-cell таблицы для кода

DOCX генератор оборачивает CodeBlock в single-cell table с серым фоном и моноширинным шрифтом. Это даёт визуальное выделение и сохраняет форматирование.

```python
CodeBlock(
    code="def hello():\n    print('Velantrim')",
    language="python",
    caption="Пример вызова API",
)
```

---

## ❌ DON'T

### Не используй DOCX как PDF

DOCX рендерится по-разному в разных версиях Word/LibreOffice. Если нужен **идентичный вид** у всех получателей — генерируй PDF.

### Не вставляй изображения большого размера

Word плохо ресайзит большие изображения. Подгоняй размер ДО вставки:

```python
# ❌ Плохо: вставка 4K изображения
ImageBlock(path="huge_4k.png", width=None)

# ✅ Хорошо: явный размер в пикселях
ImageBlock(path="huge_4k.png", width=600)
```

### Не пиши длинные параграфы (>5 предложений)

Word устаёт от длинных параграфов. Разбивай.

---

## 🎯 Шаблоны

### Sprint retrospective

```python
def sprint_retro_docx(sprint_data, theme: str = "business"):
    return GenerationSpec(
        metadata=DocumentMetadata(
            title=f"Sprint {sprint_data['name']} Retrospective",
            author=sprint_data["team"],
        ),
        theme=theme,
        blocks=[
            CalloutBlock(
                callout_type="info",
                title="Цели спринта",
                text=sprint_data["goals"],
            ),
            HeadingBlock(text="📈 Что получилось", level=1),
            *[ParagraphBlock(text=f"✅ {w}") for w in sprint_data["wins"]],
            HeadingBlock(text="📉 Что пошло не так", level=1),
            *[ParagraphBlock(text=f"⚠️ {l}") for l in sprint_data["losses"]],
            HeadingBlock(text="🎯 Action items", level=1),
            TableBlock(
                headers=["Action", "Owner", "Due"],
                rows=sprint_data["actions"],
            ),
        ],
    )
```

### Аудит-документ для редактирования

```python
def editable_audit_docx(findings: list):
    """DOCX с местами для комментариев — для review другими."""
    blocks = [
        ParagraphBlock(
            text="ИНСТРУКЦИЯ: добавьте свои комментарии "
                 "через Review → New Comment.",
            style="callout",
        ),
    ]
    for f in findings:
        blocks.extend([
            HeadingBlock(text=f"Finding: {f['title']}", level=2),
            ParagraphBlock(text=f["description"]),
            CalloutBlock(
                callout_type="warning",
                title="Severity",
                text=f["severity"],
            ),
            ParagraphBlock(text="Ваш комментарий: _______________",
                          style="italic"),
        ])
    return GenerationSpec(blocks=blocks, theme="business",
                        metadata=DocumentMetadata(title="Audit Review"))
```

---

## 🔧 Технические нюансы

### Стили Word

Генератор использует built-in стили: `Heading 1-9`, `Normal`, `List Bullet`, `List Number`, `Light Grid Accent 1` для таблиц. Эти стили доступны в любом Word.

### Цвета

Цвета в DOCX через `RGBColor`. Генератор автоматически конвертирует hex темы. Если открываешь в LibreOffice — цвета могут немного отличаться (rendering difference).

### Поддержка emoji

Word 2016+ поддерживает emoji. Если открываете в старых версиях — увидите квадратики.

### Tracked changes

Сейчас генератор НЕ создаёт документы с готовыми tracked changes. Если нужно — пользователь включает их сам через `Review → Track Changes` после открытия.
