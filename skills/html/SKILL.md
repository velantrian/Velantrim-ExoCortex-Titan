# 🌐 HTML Generation Skill

Best practices для **standalone HTML отчётов** через `core.file_generators.HTMLGenerator`.

---

## 🎯 Когда HTML

| Сценарий | Подходит? |
|---|---|
| Отчёт для просмотра в браузере | ✅ |
| Email-friendly документ | ✅ |
| Web dashboard | ✅ |
| Конвертация в PDF позже | ✅ (через print) |
| Embedded в Notion / Confluence | ✅ |
| Печать на принтере | ✅ (print CSS включён) |
| Интерактивные данные | ⚠️ Нет JS — статика |

---

## 🎨 Особенности HTML генератора

### Standalone — всё inline

Генератор создаёт **один файл** без зависимостей:
- CSS встроен через `<style>` тег
- Нет CDN, нет внешних ресурсов
- Открывается на любом устройстве offline

```python
exporter.export(spec, "report.html")
# → один .html файл, можно отправить email-вложением
```

### CSS custom properties для тем

Темы реализованы через `:root { --color-primary: ...; }`. Если хочешь кастомизировать после генерации — открой файл и поменяй переменные.

### Responsive

`max-width: 800px` + `viewport meta` → отлично читается на мобильных.

### Print-friendly

Включён `@media print` блок с:
- Скрытием navigation
- Page-break-inside для таблиц
- Конвертацией в B&W при необходимости

Это значит, что **HTML можно открыть в браузере и распечатать в PDF** — получится не хуже чем через ReportLab.

---

## ✅ DO

### Использование разных типов callout

```python
CalloutBlock(callout_type="info",    title="💡 Заметка", text="...")
CalloutBlock(callout_type="success", title="✅ Готово",   text="...")
CalloutBlock(callout_type="warning", title="⚠️ Внимание", text="...")
CalloutBlock(callout_type="danger",  title="🚨 Критично", text="...")
```

В HTML каждый callout получает свой цвет рамки слева. Это даёт визуальную семантику без слов.

### Markdown vs HTML

Если документ для GitHub / Markdown-окружения → используй `MarkdownGenerator`.
Если для веба, рассылок, дашбордов → HTML.

### Эмодзи и UTF-8

Полная поддержка эмодзи. Используй щедро — это улучшает читаемость.

---

## ❌ DON'T

### Не вставляй JavaScript

Генератор сознательно не генерирует JS. Если нужна интерактивность — это не отчёт, а web app. Используй другие инструменты.

### Не используй внешние ресурсы

```python
# ❌ Плохо — зависимость от интернета
ImageBlock(path="https://cdn.example.com/img.png")

# ✅ Хорошо — локальный файл (или base64)
ImageBlock(path="/path/to/local.png")
```

### Не вставляй изображения >2MB inline

HTML файл становится огромным. Лучше — относительные пути к локальным файлам в той же папке.

---

## 🎯 Шаблоны

### Email-friendly отчёт

```python
def email_report(facts, theme="clean"):
    """HTML который хорошо смотрится в почтовых клиентах."""
    return GenerationSpec(
        metadata=DocumentMetadata(
            title="Daily Velantrim Report",
            description="Automated daily summary",
        ),
        theme=theme,
        blocks=[
            CalloutBlock(
                callout_type="info",
                title=f"📊 Сводка за день",
                text=f"Обработано {len(facts)} фактов",
            ),
            *[FactBlock(**f) for f in facts[:10]],  # top-10
        ],
    )
```

### Web dashboard

```python
def web_dashboard(mhi, top_facts, recent_audits):
    return GenerationSpec(
        metadata=DocumentMetadata(title="Velantrim Dashboard"),
        theme="velantrim",
        blocks=[
            # Hero metric
            CalloutBlock(
                callout_type="success" if mhi.score > 0.6 else "warning",
                title=f"MHI: {mhi.score:.3f}",
                text=mhi.status.value,
            ),

            # Top facts grid
            HeadingBlock(text="🏆 Top Validated Facts", level=2),
            *[FactBlock(**f) for f in top_facts],

            # Recent audits table
            HeadingBlock(text="🛡️ Recent TruthGate Audits", level=2),
            TableBlock(
                headers=["Time", "Fact", "Verdict"],
                rows=recent_audits,
            ),
        ],
    )
```

### Print-to-PDF workflow

```python
# 1. Генерируем HTML
exporter.export(spec, "report.html")

# 2. Пользователь открывает в Chrome → Cmd+P → Save as PDF
# Результат: качественный PDF с правильной типографикой и без хвостов
```

Это альтернатива прямой генерации PDF когда нужен CSS-level контроль.

---

## 🔧 Технические нюансы

### Размер файла

Типичный HTML с темой и 50 блоками — около 30-50 KB. Это меньше большинства PDF аналогов.

### Encoding

`<meta charset="UTF-8">` всегда. Кириллица, эмодзи, китайский — всё работает.

### Без JS — намеренно

Это упрощает деплой и безопасность. Если очень нужна интерактивность — генерируй HTML как basis, потом добавь JS через post-processing.

### CSS overrides

После генерации можешь открыть `.html` и:
- Поменять `--color-primary` в `:root` → перекраска всего документа
- Поменять `--font-body` → новый шрифт
- Добавить свой `<style>` блок после генератора

Это удобно для кастомизации без правки Python.
