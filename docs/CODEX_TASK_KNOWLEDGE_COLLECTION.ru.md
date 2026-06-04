# 🤖 ТЗ для ChatGPT Codex — сбор базы знаний World Skills Core (→ 50K)

> **Дата:** 2026-05-31 · **Владелец задачи:** ChatGPT Codex · **Репозиторий (канон, под git):**
> `C:\Users\VELAN\Documents\Research Velantrim\VELANTRIM_ExoCortex_V8.6`
>
> Эта задача — **только наполнение базы знаний** (markdown-батчи фактов). Архитектуру/код
> ведёт другой агент. Цель: довести `world_skills_core` с ~6 700 до **50 000** KnowledgeUnit,
> сохраняя нулевой дубль и качество. Работай маленькими шагами, проверяя инструментом.

## 0. Что ты делаешь и чего НЕ делаешь
- ✅ **Делаешь:** пишешь новые batch-файлы фактов в `docs/knowledge/world_skills_core/ru/`,
  обновляешь `WORLD_SKILLS_CORE_STATE.ru.json`, запускаешь верификатор, коммитишь.
- ❌ **НЕ трогаешь:** `core/`, `server.py`, `api/`, `config/`, тесты — это зона другого агента.
- ❌ **НЕ включаешь** никакие ENABLE_*-флаги, не запускаешь сервер, не пишешь в `data/*.db`.
- ❌ **НЕ выдумываешь** источники/статистику; никакого вредного контента (см. `forbidden` в STATE).

## 1. Рабочий цикл (повторяй для каждого набора батчей)
```
1. Прочитай docs/knowledge/world_skills_core/WORLD_SKILLS_CORE_STATE.ru.json
   → current_checkpoint (сколько, последний батч), known_gaps_next_priority, covered_macro_areas.
2. Выбери 3–5 тем из known_gaps (или из нового слоя, см. §5). НЕ повторяй covered.
3. Напиши batch-файлы (формат §2), нумерация продолжается: NN_BATCH_XXX_TOPIC.ru.md.
4. Запусти верификатор:
       .venv\Scripts\python.exe scripts/verify_world_skills.py --update-state
   Должно быть: 0 duplicate IDs, 0 malformed. Линтер покажет duplicate/generic claims.
5. Обнови в STATE: last_batch_number, last_batch_file, перенеси закрытые темы из
   known_gaps_next_priority в covered_macro_areas. Когда слой исчерпан — задай новый (§5).
6. Закоммить (§6). В конце сообщи: всего units, дублей, осталось до 50K, последний batch.
```

## 2. Формат batch-файла (СТРОГО)
Имя: `NN_BATCH_XXX_TOPIC.ru.md` (NN — порядковый префикс файла, XXX — номер батча).
Заголовок + markdown-таблица из **5 колонок**:
```
# BATCH_XXX — <English Topic Title>
# world_skills_core · source: world_skills_core:batch_XXX:<topic_slug>
# KnowledgeUnits: <N>

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| domain.sub.term | Короткое имя | invariant\|variant | <самодостаточный факт> | <зачем/применение> |
```
- **40–50 строк** на батч, тематически цельных.
- `Тип`: `invariant` (неизменная истина/принцип) или `variant` (прикладное/контекстное).

## 3. Правила ID
- Формат `domain.subdomain.term` (или `domain.term`), **lowercase ASCII**, без пробелов.
- **Уникальность глобальная** — verify падает (exit 1) при дубле ID.
- Новый домен = новый namespace-префикс (снижает риск коллизий и включает домен-блокировку дедупа).

## 4. 🔑 Правило самодостаточного claim (КРИТИЧНО — см. docs/INGEST_SCHEMA_50K.ru.md §8)
**`Суть` (claim) должен содержать факт ЦЕЛИКОМ.** Различающая информация — В САМОМ claim,
а не только в колонке `KnowledgeUnit`/`Практический смысл` (движок хранит и ищет именно claim).
```
ПЛОХО:    | geo.fr.cap | Франция — Париж | invariant | столица, евро (EUR) | … |
          | geo.it.cap | Италия — Рим     | invariant | столица, евро (EUR) | … |   ← claim'ы идентичны!
ХОРОШО:   | geo.fr.cap | Франция — Париж | invariant | Столица Франции — Париж; валюта евро (EUR) | … |
```
Верификатор флажит **duplicate claims** (одна нормализованная «Суть» у ≥2 ID) и **short claims**
(<12 симв.). Перед коммитом эти числа должны быть низкими; запускай для строгой проверки:
```
.venv\Scripts\python.exe scripts/verify_world_skills.py --strict-claims   # exit 1 при claim-проблемах
```

## 5. Слои (как расширять охват)
Идём от ширины к глубине. Уже закрыто: breadth (060-079) → научная глубина (080-095) →
прикладная (096-107) → reasoning/reference (108-122). **Задай слой 5** и далее, например:
- право-детали (договоры по типам, трудовое/семейное/уголовное практически);
- инженерные расчёты (сопромат, электротехника-задачи, теплотехника);
- медицина по системам (симптом→дифдиагноз→референс, без назначений/доз);
- языки конкретно (грамматика популярных языков, фразы, письменности);
- регионы/история по периодам и странам; искусство по эпохам; экономика отраслей.
Правило: каждая новая тема даёт **новый практический аспект**, а не пересказ покрытого.

## 6. Коммиты
- Работай на ветке (не в `master`): `git checkout -b codex/knowledge-batches-<date>`.
- Один коммит на набор батчей. Сообщение: что за темы, сколько units, результат verify.
- В конце сообщения: `Co-Authored-By: ChatGPT Codex <noreply@openai.com>`.
- Не делай force-push, не трогай чужие файлы.

## 7. Definition of Done (для каждого набора)
- [ ] verify: **0 duplicate IDs**, 0 malformed.
- [ ] duplicate/generic claims не выросли значимо (новые claim самодостаточны).
- [ ] STATE обновлён (счётчик, last_batch, covered/gaps), JSON валиден.
- [ ] Коммит на ветке с понятным сообщением.
- [ ] В чате: всего units / дублей / осталось до 50K / последний batch.

## 8. Запрещено (`batch_generation_contract.forbidden` в STATE)
- unsafe step-by-step harmful instructions; medical dosing advice; weapon construction;
  illegal evasion; **fabricated sources or fake statistics**; duplicate IDs.

---
*Источник правды по прогрессу — `WORLD_SKILLS_CORE_STATE.ru.json`. Если контекст потерян —
прочитай его `continuation_instruction` и продолжай. Канон по истине/архитектуре (не трогать):
`docs/TRUTH_AND_RINGZERO_CANON.ru.md`, `docs/DEDUP_AND_SCALE_1M.ru.md`, `docs/INGEST_SCHEMA_50K.ru.md`.*
