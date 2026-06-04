# ⚖️ KNOWLEDGE_5_LOGIC — Логика и правила вывода (v3.0)

**Цель:** 200-500 правил и принципов.
**ESM:** → `ImmutableCore` для классических законов, `Validated` для производных.
**Confidence:** 0.95-1.0.
**Время сбора:** 30-80 часов.

---

## 🎯 Что собирать

Только **формальные правила**. Не объяснения, не примеры из реальной жизни — сами правила.

```
До (с педагогикой):
   "Modus Ponens — основа всех математических доказательств..."
   + 3 предложения объяснения
   + 5 примеров
   + 3 типичные ошибки
   = 200 слов

После (только суть):
   "Если (A → B) и A истинны, то B истинно: (A→B) ∧ A ⊢ B"
   = 15 слов
```

---

## 📚 Темы

### Классическая логика (~50)
- 3 закона мышления (тождества, противоречия, исключённого третьего)
- 6 базовых операторов (∧, ∨, →, ↔, ¬, ⊕)
- Законы Де Моргана
- Правила вывода: modus ponens, modus tollens, hypothetical/disjunctive syllogism, conjunction, simplification
- Силлогизмы Аристотеля (24 модуса)

### Логика предикатов (~30)
- Квантификаторы ∀, ∃
- Правила работы с квантификаторами
- Аксиомы FOL

### Индуктивное и абдуктивное рассуждение (~20)
- Виды индукции
- Абдукция (вывод к наилучшему объяснению)
- Проблема индукции

### Байесовское и каузальное (~30)
- Теорема Байеса
- Prior/Likelihood/Posterior
- Иерархия Pearl (ассоциация → интервенция → контрфактуал)
- Условия каузальности

### Логические ошибки (~50)
- Формальные: утверждение консеквента, отрицание антецедента
- Неформальные: ad hominem, соломенное чучело, ложная дилемма, post hoc, скользкий склон
- Когнитивные искажения: confirmation bias, anchoring, availability, survivorship

### Эпистемология (~20)
- A priori / A posteriori
- Tacit knowledge
- Регресс обоснования
- Гёттиеровские случаи

### Парадоксы (~10)
- Лжеца, Рассела, Зенона, кучи

---

## 📦 Формат v3.0

```json
{
  "id": "rule.modus_ponens",
  "domain": "logic.propositional",
  "type": "inference_rule",
  "statement": "Если истинна импликация A→B и истинно A, то истинно B.",
  "formal_notation": "(A → B) ∧ A ⊢ B",
  "conditions": "Классическая пропозициональная логика.",
  "limits": [
    "В многозначных логиках требуется модификация",
    "В нечёткой логике работает по-другому"
  ],
  "prereq": ["concept.implication", "concept.truth_value"],
  "derives_from": [],
  "confidence": 1.0,
  "tags": ["modus_ponens", "inference", "deduction"],

  "category": "inference_rule",
  "is_axiomatic": true,
  "related_logic": ["rule.modus_tollens", "rule.hypothetical_syllogism"]
}
```

**Особые поля для LOGIC:**
- `category` — `inference_rule` / `law_of_thought` / `fallacy` / `bias` / `paradox` / `principle`
- `is_axiomatic` — true для аксиом
- `related_logic` — связи с другими логическими понятиями

---

## 🤖 Инструкция для ИИ-сборщика

1. Возьми раздел (формальная логика, индукция, ошибки...).
2. Каждое правило — отдельная запись.
3. **ОБЯЗАТЕЛЬНО:**
   - `formal_notation` где возможно
   - `category` точно
   - `is_axiomatic` true/false
4. **Statement — 1 предложение.**
5. **НЕ ДОБАВЛЯЙ:** примеры из жизни, объяснения, common_confusions.

**Объём:** 25-30 на файл. Файлов ~10-20.

---

## ✅ Чек-лист

```
☑ id в формате rule.* / fallacy.* / bias.* / paradox.*?
☑ category правильно (inference_rule/fallacy/bias/...)?
☑ is_axiomatic заполнено?
☑ formal_notation есть (если применимо)?
☑ statement — 1 предложение?
☑ confidence ≥ 0.95?
☑ НЕТ примеров из реальной жизни в statement?
```

---

## 🔗 Связь с архитектурой Velantrim

```
Логический принцип            →  Где в коде
───────────────────────       ──────────────────
Закон противоречия            →  find_contradictions() (TASK-16)
Modus Ponens                  →  CausalGraph.causal_chain()
Темпоральная логика           →  bi-temporal model
Каузальная иерархия           →  CausalGraph 15 типов связей
Байесовское обновление        →  confidence update
Falsifiability                →  ESM Validated → Contradicted
Когнитивные искажения         →  inversion_tests
```

---

## 🎯 Источники

```
📘 Классика
   • Аристотель "Органон"
   • Mendelson "Introduction to Mathematical Logic"
   • Hurley "A Concise Introduction to Logic"

📕 Эпистемология
   • Stanford Encyclopedia of Philosophy
   • Pearl "The Book of Why" (каузальность)

📓 Когнитивные искажения
   • Kahneman "Thinking, Fast and Slow"
   • Tversky & Kahneman original papers
```
