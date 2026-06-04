# 🎯 PPTX Generation Skill

Best practices для создания **профессиональных презентаций** через `core.file_generators.PPTXGenerator`.

---

## 🎯 Когда PPTX

| Сценарий | Подходит? |
|---|---|
| Доклад на встрече / конференции | ✅ |
| Demo для инвесторов | ✅ |
| Sprint review | ✅ |
| Обучающие материалы | ✅ |
| Long-form контент (>20 слайдов) | ⚠️ Используй PDF/DOCX |
| Чтение в одиночку | ❌ → PDF |

---

## 📐 Правила хорошей презентации

### Правило 1: один слайд = одна мысль

```python
# ❌ Плохо: 8 буллетов на слайде
HeadingBlock(text="Quarterly Review", level=1)
ParagraphBlock(text="Метрика 1: ...")
ParagraphBlock(text="Метрика 2: ...")
# ... ещё 6 ...

# ✅ Хорошо: разбить на несколько слайдов через HeadingBlock(level=1)
HeadingBlock(text="Q1 Metrics: MHI", level=1)
ParagraphBlock(text="MHI вырос с 0.62 до 0.84")

HeadingBlock(text="Q1 Metrics: Validated Facts", level=1)
ParagraphBlock(text="Validated facts: 1240 → 3890 (+213%)")
```

### Правило 2: 6×6 для bullet points

Максимум **6 буллетов** на слайде, **6 слов** в каждом. Если больше — разбивай на слайды или используй два колонки (TODO).

### Правило 3: один FactBlock = один слайд

```python
# Velantrim-pattern: ключевой факт занимает весь слайд
FactBlock(
    fact_id="finding_001",
    claim="Drift protection предотвращает 99.3% split-brain ситуаций",
    confidence=0.993,
    epistemic_state="Validated",
    source="audit:Q1_regression",
)
# → отдельный слайд с claim как огромный заголовок,
#   метаданные внизу, цветная боковая полоса по state.
```

### Правило 4: таблица — отдельный слайд

```python
TableBlock(
    headers=["Метрика", "Q4 2025", "Q1 2026"],
    rows=[...],
    caption="Ключевые метрики",  # ← станет title слайда
)
```

### Правило 5: один шрифт, два размера

Темы устанавливают `font_heading` и `font_body`. Не смешивай больше двух семейств шрифтов.

---

## 🎨 Выбор темы

| Тема | Когда |
|---|---|
| `velantrim` 🔱 | Внутренние demo, sprint reviews |
| `business` | Инвесторы, board meetings |
| `scientific` | Академические доклады |
| `dark` | Тёмные залы конференций, evening events |
| `clean` | Универсально, training, workshops |

---

## ✅ Полный шаблон pitch deck

```python
def pitch_deck_template(product_data):
    """Стандартный pitch deck по Y Combinator."""
    return GenerationSpec(
        metadata=DocumentMetadata(
            title=product_data["name"],
            author=product_data["team"],
            subject="Investor pitch",
        ),
        theme="business",
        blocks=[
            # Слайд 1: Title
            HeadingBlock(text=product_data["name"], level=1),
            ParagraphBlock(text=product_data["tagline"]),

            # Слайд 2: Problem
            HeadingBlock(text="❌ Problem", level=1),
            ParagraphBlock(text=product_data["problem"]),

            # Слайд 3: Solution
            HeadingBlock(text="✅ Solution", level=1),
            ParagraphBlock(text=product_data["solution"]),

            # Слайд 4: How it works
            HeadingBlock(text="🛠️ How it works", level=1),
            ListBlock(items=product_data["features"]),

            # Слайд 5: Traction (таблица → отдельный слайд)
            HeadingBlock(text="📈 Traction", level=1),
            TableBlock(
                headers=["Метрика", "Q3", "Q4", "Q1 (now)"],
                rows=product_data["traction"],
                caption="Quarterly growth",
            ),

            # Слайд 6: Team
            HeadingBlock(text="👥 Team", level=1),
            ListBlock(items=product_data["team_members"]),

            # Слайд 7: Ask
            HeadingBlock(text="🎯 Ask", level=1),
            CalloutBlock(
                callout_type="info",
                title=f"💰 ${product_data['ask']}",
                text=product_data["ask_description"],
            ),
        ],
    )
```

---

## ✅ Sprint Review template

```python
def sprint_review_pptx(sprint):
    return GenerationSpec(
        metadata=DocumentMetadata(
            title=f"Sprint {sprint['number']} Review",
            author=sprint["team"],
        ),
        theme="velantrim",
        blocks=[
            # Title slide создаётся автоматически из metadata.title

            # Goal recap
            HeadingBlock(text="🎯 Цель спринта", level=1),
            ParagraphBlock(text=sprint["goal"]),

            # Что доставили (по одному факту на слайд)
            HeadingBlock(text="✅ Доставили", level=1),
            *[FactBlock(
                fact_id=f"sprint_{sprint['number']}_delivery_{i}",
                claim=delivery["title"],
                confidence=1.0,
                epistemic_state="Validated",
                source=delivery["pr_link"],
            ) for i, delivery in enumerate(sprint["delivered"])],

            # Метрики
            HeadingBlock(text="📊 Метрики", level=1),
            TableBlock(
                headers=["Метрика", "Цель", "Факт", "Δ"],
                rows=sprint["metrics"],
            ),

            # Что не успели
            HeadingBlock(text="⏰ Перенесли", level=1),
            ListBlock(items=sprint["carryover"]),

            # Next sprint
            HeadingBlock(text="🚀 Следующий спринт", level=1),
            ListBlock(items=sprint["next_goals"]),
        ],
    )
```

---

## 🔧 Технические нюансы

### Widescreen 16:9

Размер слайдов жёстко 13.333 × 7.5 дюймов (16:9 widescreen). Если нужен 4:3 — нужно расширить генератор.

### Speaker notes

Для `FactBlock` заметки докладчика заполняются автоматически (id, confidence, state, source). Для других блоков заметок нет — нужно расширение.

### Изображения

ImageBlock работает, но качество зависит от исходника. Используй минимум 1920×1080 для widescreen.

### Анимации

Анимации НЕ генерируются программно — это анти-паттерн. Если хочешь анимации, добавь их вручную в PowerPoint после генерации.

### Custom layouts

Сейчас используется только Blank layout (slide_layouts[6]). Title bar рисуется через `add_shape`. Если нужен Title+Content или Two-Column — нужно расширение.

---

## ❌ DON'T

- Не помещай >100 слов на один слайд
- Не делай 12 буллетов — лучше 3 слайда по 4
- Не используй >2 шрифтов
- Не клади изображения <800px ширины — будут пиксельные на проекторе
- Не пиши целые параграфы в слайды — это для речи

---

## 📚 Дополнительно

- PDF аналог: `core/file_generators/skills/pdf/SKILL.md`
- API: `core/file_generators/README.md`
