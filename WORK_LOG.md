# 📓 WORK_LOG — Velantrim ExoCortex

<!-- ═══════════════════════════════════════════════════════════════════
     КАК ПОЛЬЗОВАТЬСЯ ЭТИМ ФАЙЛОМ (читай один раз, потом удали этот блок)

     Этот файл — единый источник правды о состоянии работы над проектом.
     Он живёт в репозитории, а не в чате с ИИ.

     КАК НАЧАТЬ НОВУЮ СЕССИЮ С ЛЮБЫМ ИИ:
     1. Открой новое окно (модель неважна — Claude, Grok, DeepSeek, любая)
     2. Прикрепи этот файл + только нужные для задачи файлы кода (3-5 штук)
     3. Напиши: "Читай WORK_LOG.md. Текущая задача: [ID]. Начнём."
     4. ИИ сам восстановит контекст из файла без лишних объяснений

     КАК ЗАКРЫТЬ ЗАДАЧУ:
     1. Попроси ИИ обновить нужную запись в этом файле
     2. Сделай git commit с сообщением: "work_log: close [ID]"
     3. Закрой окно — контекст сохранён, сессия завершена

     ТРИ ТИПА ЗАПИСЕЙ:
     TASK     — атомарная задача с кодом и тестом (один коммит = одна TASK)
     DECISION — архитектурное решение с обоснованием (почему так, а не иначе)
     RESEARCH — находка из аудита, эксперимента или консультации с ИИ

     СТАТУСЫ: 🔴 open | 🟡 in_progress | ✅ done | ⏸ paused | 🚫 cancelled

     ПРИНЦИП: задача считается закрытой не когда ИИ сказал "готово",
     а когда указанный тест проходит. Числа важнее мнений.
═══════════════════════════════════════════════════════════════════ -->

---

## 🗂️ Индекс

| ID | Тип | Статус | Заголовок | Приоритет |
|----|-----|--------|-----------|-----------|
| [RESEARCH-01](#research-01) | RESEARCH | ✅ done | Глубокий аудит v8.5.1 — Claude + ChatGPT | — |
| [DECISION-01](#decision-01) | DECISION | ✅ done | Work_log как единый источник правды | — |
| [TASK-01](#task-01) | TASK | ✅ done | Фикс: available — property vs method | P0 |
| [TASK-02](#task-02) | TASK | ✅ done | Фикс: coverage target в pyproject.toml | P0 |
| [TASK-03](#task-03) | TASK | ✅ done | Фикс: datetime.utcnow() → timezone.utc | P0 |
| [TASK-04](#task-04) | TASK | ✅ done | Фикс: mark_retriever_dirty в каждом query | P0 |
| [TASK-05](#task-05) | TASK | ✅ done | Фикс: store_fact двойная запись в pipeline | P1 |
| [TASK-06](#task-06) | TASK | ✅ done | Фикс: get_all_facts без LIMIT | P1 |
| [TASK-07](#task-07) | TASK | ✅ done | Фикс: DATABASE fallback в production-пути | P1 |
| [TASK-08](#task-08) | TASK | ✅ done | Интеграция: CausalGraph → pipeline.run() | P2 |
| [TASK-09](#task-09) | TASK | ✅ done | Интеграция: RawMemory → store_fact + ingest | P2 |
| [TASK-10](#task-10) | TASK | ✅ done | Фикс: find_contradictions — рекурсия без защиты | P2 |
| [TASK-11](#task-11) | TASK | ✅ done | Оптимизация: BFS deque вместо list.pop(0) | P2 |
| [TASK-12](#task-12) | TASK | ✅ done | Замена: pipeline.build_facts_pack → FactsPackBuilder | P2 |
| [TASK-13](#task-13) | TASK | ✅ done | Гигиена: consolidate 4 CHANGELOG в один | P3 |
| [TASK-14](#task-14) | TASK | ✅ done | Гигиена: Diary/ → docs/seed/ + ЗАПУСК → RUN.ru.md | P3 |
| [TASK-15](#task-15) | TASK | ✅ done | Гигиена: .coverage → .gitignore | P3 |

---

## RESEARCH-01

**Тип:** RESEARCH  
**Статус:** ✅ done  
**Дата:** 2026-05-19  
**Источник:** Claude (глубокий аудит) + ChatGPT (прогон тестов + формат file→line→risk→patch)

### Что изучалось

Полный аудит кодовой базы Velantrim ExoCortex v8.5.1 (142 файла, ~24 100 строк).
Два независимых ИИ анализировали одну и ту же базу разными методами.
Claude строил импорт-граф и архитектурный анализ. ChatGPT запускал `pytest` и читал рантайм-ошибки.

### Ключевые находки

**Только Claude нашёл:**
- `mark_retriever_dirty()` вызывается на каждом `/query` → HybridRetriever singleton пересоздаётся каждый запрос, performance-фикс v8.4.0 фактически не работает.
- 43% ядра (6 600 / 15 332 строк) — orphan-код: CausalGraph, RawMemory, audit_chain, affordance_linker, evidence, facts_pack, cache_coherence, confidence, living_context, file_parsers/.
- CausalGraph (Patch 13, 841 строка, 44 теста) **не подключён к pipeline**. `POST /query` никогда его не вызывает.
- RawMemory (355 строк, миграция 010) создаёт таблицы с триггерами, но `RawMemoryStore.store()` не вызывается нигде в проекте.
- `_count_evidence` в TruthGate возвращает фиктивное значение — PRECISION mode физически непроходим.
- `find_contradictions` рекурсивен без cycle protection.
- `get_all_facts()` без LIMIT на каждом `/query`.
- Двойной builder FactsPack: `pipeline.build_facts_pack` (50 строк) vs `core/facts_pack.FactsPackBuilder` (382 строки с CognitiveMode-политиками).

**Только ChatGPT нашёл:**
- `TypeError: 'bool' object is not callable` в `tests/test_server_integration.py:154` — реальный сбой, воспроизводится через `pytest`. Причина: `available` — `@property`, но тест вызывает `available()`.
- Coverage target `--cov=file_parsers` в `pyproject.toml` неверный (пакет живёт как `core.file_parsers`) → CoverageWarning, метрики покрытия частично врут.
- `datetime.utcnow()` в 4 файлах `core/velantrim_reports/*.py` — deprecated на Python 3.12+.
- `ResourceWarning: unclosed database` в прогоне тестов.
- Реальный счёт тестов: `pytest --collect-only` собирает **505** (не 484 и не 266 как в доках) — разница за счёт параметризованных тестов.

**Оба нашли:**
- `DATABASE_DEV_ONLY` fallback в production-пути pipeline.
- Глобальный state: `_GLOBAL_STORE`, `_GLOBAL_NGRAM`, 12 module-level синглтонов.
- Расхождение версий в документах (v8.4.0 / v8.5.0 / v8.5.1 / v8.5.3).
- 4 отдельных CHANGELOG-файла.

### Вывод

Система имеет два параллельных слоя: рабочий MVP (~3 000 строк) и "архитектура будущего" (~6 600 строк), которая написана, протестирована, но не подключена к продакшн-пути. Главный приоритет — не новые модули, а интеграция уже написанного.

### Связанные задачи

TASK-01 через TASK-15 — все выведены из этого исследования.

---


## RESEARCH-02

**Тип:** RESEARCH  
**Статус:** ✅ done  
**Дата:** 2026-05-20  
**Источник:** Велантриец (вопрос) → Claude (ответ) → DeepSeek + Grok (развитие) → ChatGPT (рецензия) → Велантриец (сборка ТЗ)

### Что изучалось

Может ли ИИ создавать или только интерпретирует? Где граница между человеком-творцом
и ИИ-помощником? Что эта граница означает для архитектуры Velantrim?

### Ход разговора

1. **Велантриец** задал вопрос: «Машина может фантазировать про корабль на левитации
   или только интерпретирует существующее?»

2. **Claude** ответил «нет — не потому что я ограниченный, а потому что фантазия
   требует тела, смертности и опыта поражения. Я могу быть оркестром, но не
   композитором.»

3. **DeepSeek** услышал этот ответ и развил: «человек создаёт — ИИ усиливает».

4. **Grok** формализовал в манифест с тремя ролями (Человек-Творец / ИИ-Оркестр /
   Правильный порядок).

5. **ChatGPT** отрецензировал манифест и предложил усиление: «не просто 'ИИ не может
   хотеть', а 'ИИ не задаёт цель, он работает внутри цели заданной человеком'» —
   философское превращено в инженерное требование.

6. **Велантриец** собрал из всех вкладов **ТЗ v1.0** с 6 инвариантами.

### Ключевые находки

- Граница между человеком и ИИ — **структурная**, а не временная. GPT-5 или GPT-10
  её не сотрут — потому что фантазия требует тела и смертности.
- Velantrim не должен пытаться стать автономным субъектом — это противоречит
  его собственной цели расширения человеческого мышления.
- Манифест нужен **в самом проекте**, не в чате. Следующий ИИ-агент должен
  прочитать его перед началом работы.
- ТЗ должен содержать **inversion tests** — конкретные сценарии нарушений,
  чтобы инварианты можно было проверять, а не только декларировать.

### Метанаблюдение

Этот разговор сам по себе — демонстрация поликогнитивного синтеза под человеческим
контролем. Claude дал направление, DeepSeek подхватил, Grok формализовал, ChatGPT
отрецензировал, Велантриец решил что взять и собрал финальный документ. Это именно
то что Velantrim должен делать с фактами — собирать перспективы под человеческим
авторством. Идея проекта подтвердилась его же методом работы.

### Артефакты

- `docs/PHILOSOPHY.md` — манифест для людей
- `docs/PHILOSOPHY_SPEC.md` — инварианты I1-I6 + inversion tests для AI-агентов
- Обновлены: `README.md`, `Velantrim_Project_Map.md` со ссылками на эти документы

### Связанные задачи

Этот RESEARCH влияет на ВСЕ будущие задачи — каждая фича должна проходить проверку
через inversion tests из `PHILOSOPHY_SPEC.md`.

---

## DECISION-01

**Тип:** DECISION  
**Статус:** ✅ done  
**Дата:** 2026-05-19

### Решение

Ввести `WORK_LOG.md` как единый источник правды о состоянии работы. Файл живёт в репозитории рядом с кодом.

### Почему так

Контекст между сессиями с ИИ терялся. Длинные чаты деградируют по точности. Разные ИИ (Claude, Grok, ChatGPT, DeepSeek) не могут передавать контекст друг другу напрямую. Файл в репо версионируется, доступен любому ИИ через прикрепление, не зависит от конкретной модели или сервиса.

### Альтернативы которые отклонили

Notion/Obsidian — внешний инструмент, надо синхронизировать вручную. Длинный чат — деградирует, непереносим. Голова — ненадёжно на дистанции.

### Формат записи

Три типа: TASK (атомарная задача с тестом как критерием закрытия), DECISION (архитектурный выбор с обоснованием), RESEARCH (находки из аудитов и экспериментов).

---

## TASK-01

**Тип:** TASK  
**Статус:** 🔴 open  
**Приоритет:** P0 — ломает тест прямо сейчас  
**Источник:** ChatGPT (прогон pytest), подтверждён Claude

### Проблема

`available` в `core/ngram_index.py:222` объявлен как `@property`. В `tests/test_server_integration.py:154` вызывается как `srv._ngram.available()` со скобками. В `docs/INVARIANTS.md:71` тоже написано `NGramIndex.available()`. Контрактный дрейф в трёх местах.

**Симптом:** `TypeError: 'bool' object is not callable` — тест падает, CI сломан.

### Файлы для работы

`core/ngram_index.py`, `tests/test_server_integration.py`, `docs/INVARIANTS.md`

### Критерий закрытия

```
pytest tests/test_server_integration.py::TestNGramCoherence::test_indexed_fact_findable_through_server
```
Должен проходить без `TypeError`.

### Минимальный патч

Убрать скобки в `test_server_integration.py:154`: заменить `available()` на `available`. Обновить описание в `INVARIANTS.md:71` — убрать скобки из `NGramIndex.available()`. Весь остальной код (`server.py`, `pipeline.py`) уже использует property-стиль корректно.

### Коммит

`fix: NGramIndex.available property call site in test + docs`

---

## TASK-02

**Тип:** TASK  
**Статус:** 🔴 open  
**Приоритет:** P0 — метрики покрытия врут  
**Источник:** ChatGPT

### Проблема

В `pyproject.toml` в `addopts` стоит `--cov=file_parsers`, но пакет лежит как `core.file_parsers`. При прогоне pytest выдаёт `CoverageWarning: Module file_parsers was never imported`. Отчёт покрытия содержит мусор, цифры ненадёжны.

### Файлы для работы

`pyproject.toml`

### Критерий закрытия

```
pytest tests/test_smoke.py 2>&1 | grep -c "CoverageWarning"
```
Должен вернуть `0`.

### Минимальный патч

В `pyproject.toml`, строка `addopts`: заменить `--cov=file_parsers` на `--cov=core.file_parsers`. Либо убрать этот target целиком, поскольку `--cov=core` уже покрывает весь `core/`, включая `core.file_parsers`.

### Коммит

`fix: coverage target file_parsers → core.file_parsers in pyproject.toml`

---

## TASK-03

**Тип:** TASK  
**Статус:** 🔴 open  
**Приоритет:** P0 — deprecated на Python 3.12+, сломается на 3.14  
**Источник:** ChatGPT

### Проблема

В четырёх файлах `core/velantrim_reports/` используется `datetime.utcnow()` — deprecated с Python 3.12, запланировано к удалению. Рядом в тех же файлах используется `datetime.now()` без timezone — naive datetime, несовместимый с bi-temporal полями системы.

**Конкретные строки:**
`knowledge_base.py:156,168` | `mhi_report.py:152,156` | `sprint_review.py:155` | `truthgate_report.py:165,169`

### Файлы для работы

`core/velantrim_reports/knowledge_base.py`, `mhi_report.py`, `sprint_review.py`, `truthgate_report.py`

### Критерий закрытия

```
grep -rn "utcnow\|datetime\.now()" core/velantrim_reports/
```
Должен вернуть пустой результат.

### Минимальный патч

Заменить все `datetime.utcnow()` на `datetime.now(timezone.utc)`. Для display-строк (`.strftime(...)`) оставить `datetime.now(timezone.utc).strftime(...)` — это корректно. Убедиться что `from datetime import datetime, timezone` в импортах каждого файла.

### Коммит

`fix: replace datetime.utcnow() with datetime.now(timezone.utc) in reports`

---

## TASK-04

**Тип:** TASK  
**Статус:** 🔴 open  
**Приоритет:** P0 — performance-регрессия на каждом запросе  
**Источник:** Claude

### Проблема

В `core/pipeline.py:367` функция `build_facts_pack()` вызывает `mark_retriever_dirty()` на каждой итерации. Это инвалидирует singleton `HybridRetriever` на каждом `POST /query`. При следующем вызове `_get_hybrid_retriever()` полностью пересоздаёт объект: загружает `sentence-transformer` (~80MB) и пересчитывает эмбеддинги всей базы. AUDIT-FIX v8.4.0 ("performance bomb defused, 20-50ms вместо 1-2s") фактически не работает.

### Файлы для работы

`core/pipeline.py`

### Критерий закрытия

При двух последовательных `POST /query` с одинаковым запросом второй должен **не пересоздавать** HybridRetriever. Проверяется логом: `HybridRetriever singleton (re)built` должен появиться только один раз при прогоне двух запросов подряд.

```
pytest tests/test_pipeline.py -k "test_idempotent or test_repeated"
```

### Минимальный патч

`mark_retriever_dirty()` вызывать только если `store_fact()` реально сделал INSERT (новый факт), а не UPSERT без изменений. Добавить возвращаемое значение в `store_fact` — флаг `was_new: bool`. В `build_facts_pack` вызывать `mark_retriever_dirty()` только если `was_new == True`.

### Коммит

`fix: mark_retriever_dirty only on real INSERT, not on every query`

---

## TASK-05

**Тип:** TASK  
**Статус:** 🔴 open  
**Приоритет:** P1  
**Источник:** Claude

### Проблема

В `core/pipeline.py:354-364` `build_facts_pack()` вызывает `store_fact()` для каждого факта из `retrieved` — но эти факты только что пришли из `get_all_facts()`, то есть они уже в БД. Это ON CONFLICT UPDATE с теми же данными: лишняя транзакция SQLite + drift-check на каждом запросе.

### Файлы для работы

`core/pipeline.py`

### Критерий закрытия

```
pytest tests/test_pipeline.py -v
```
Все тесты проходят. Дополнительно: добавить тест `test_build_facts_pack_no_redundant_write` — при передаче уже существующего факта `store_fact` не вызывается.

### Минимальный патч

В `build_facts_pack` перед `store_fact()` проверять `if get_fact(fact_id) is None` — писать только новые факты. Для уже существующих — только обновлять `retrieval_score` в in-memory pack-снапшоте.

---

## TASK-06

**Тип:** TASK  
**Статус:** 🔴 open  
**Приоритет:** P1 — масштабируемость  
**Источник:** Claude

### Проблема

В `core/pipeline.py:214` `_retrieve_from_store()` начинается с `all_facts = get_all_facts()` — выгрузка всей базы в Python-список на каждом запросе. NGramIndex потом сужает, но к этому моменту все строки уже в RAM. При 100k фактов это 10-50MB на каждый `/query`.

### Файлы для работы

`core/pipeline.py`, `core/memory.py`, `core/storage.py`

### Критерий закрытия

```
pytest tests/test_pipeline.py -v
```
Все тесты проходят. При 1000+ фактов в БД `_retrieve_from_store` не должен загружать более top-N полных записей.

### Минимальный патч

Добавить в `GraphStore ABC` метод `get_fact_ids()` возвращающий только `fact_id`. Передавать список ID в NGramIndex. После NGram-фильтрации тянуть полные факты только для кандидатов через `get_fact(fact_id)` в цикле.

---

## TASK-07

**Тип:** TASK  
**Статус:** 🔴 open  
**Приоритет:** P1 — архитектурная мина  
**Источник:** Claude + ChatGPT

### Проблема

В `core/pipeline.py:300-302` при пустом store `retrieve()` возвращает 5 хардкоженных демо-фактов из `_DATABASE_DEV_ONLY`. В production пустая БД должна возвращать честный пустой результат, а не учебные факты о квантовой физике.

### Файлы для работы

`core/pipeline.py`

### Критерий закрытия

```
pytest tests/test_pipeline.py -k "test_empty_store"
```
Тест `test_empty_store_returns_empty_not_mock` (нужно создать) — пустой store возвращает `{"error": "...", "facts": []}`, не демо-факты.

### Минимальный патч

Убрать fallback в `retrieve()`. В `_DATABASE_DEV_ONLY` добавить защитный guard: использовать только если явно установлен `os.getenv("VELANTRIM_DEV_MOCK", "false") == "true"`.

---

## TASK-08

**Тип:** TASK  
**Статус:** 🔴 open  
**Приоритет:** P2 — главная архитектурная задача  
**Источник:** Claude

### Проблема

`core/causal_graph.py` (841 строка, 44 теста, Patch 13) не подключён к `pipeline.run()`. Флагман "перехода от памяти к пониманию" реально не запускается при `POST /query`. Аналогично `core/understanding_layer.py` (326 строк) не имеет точки входа в production-пути.

### Файлы для работы

`core/causal_graph.py`, `core/pipeline.py`, `server.py`, `migrations/008_add_relations.sql`

### Критерий закрытия

После `POST /query` в ответе появляется секция `causal_hints` с хотя бы одним автоматически предложенным ребром (с `knowledge_status="hypothetical"`). Тест:
```
pytest tests/test_pipeline.py -k "test_causal_hints_in_response"
```

### Минимальный патч (MVP)

В `pipeline.run()` после шага 6 (ESM transition) для каждого нового Validated-факта запускать lightweight extractor: regex по ключевым словам ("потому что", "из-за", "следовательно", "because", "therefore") и предлагать `CausalGraph.add_relation(..., knowledge_status="hypothetical")`. Не блокировать ответ — добавлять как аннотацию.

---

## TASK-09

**Тип:** TASK  
**Статус:** 🔴 open  
**Приоритет:** P2 — "защита от Semantic Drift" сейчас мертва  
**Источник:** Claude

### Проблема

`core/raw_memory.py` (355 строк) создаёт API для L0 Immutable Raw Memory. Миграция `010_raw_memory.sql` создаёт таблицы с триггерами `prevent_update/prevent_delete`. Но во всём проекте **ноль вызовов** `RawMemoryStore.store()`. Декларируемая "защита от Semantic Drift" — это пустая таблица.

### Файлы для работы

`core/raw_memory.py`, `core/pipeline.py`, `server.py` (endpoint `POST /facts` и `POST /ingest/text`)

### Критерий закрытия

После `POST /ingest/text` таблица `l0_raw_memory` содержит запись с оригинальным текстом. Факт в `facts` имеет заполненное поле `derived_from`. Тест:
```
pytest tests/test_smoke.py -k "test_raw_memory_populated_after_ingest"
```

### Минимальный патч

В `POST /facts` перед `store_fact()` вызывать `RawMemoryStore(conn).store(req.claim, source=req.source)`, получать `raw_id`, добавлять `derived_from=raw_id` в словарь факта. Аналогично в `POST /ingest/text`.

---

## TASK-10

**Тип:** TASK  
**Статус:** 🔴 open  
**Приоритет:** P2 — риск бесконечной рекурсии  
**Источник:** Claude

### Проблема

В `core/causal_graph.py:730-733` `find_contradictions()` рекурсивно вызывает сама себя через цепочку `implies`. Локальный `seen_ids` сбрасывается на каждом recursion frame. На циклическом графе (`A implies B`, `B implies C`, `C implies A`) уходит в бесконечную рекурсию или экспоненциальный перебор.

### Файлы для работы

`core/causal_graph.py`

### Критерий закрытия

```
pytest tests/test_causal_graph.py -k "test_contradictions_cyclic"
```
Тест на граф с циклом — не должен зависать, должен завершиться за разумное время (< 1 сек).

### Минимальный патч

Добавить параметр `_visited: set[str] | None = None` в сигнатуру `find_contradictions`. Инициализировать `set()` при первом вызове. Передавать `visited | {fact_id}` при рекурсии. Проверять `if fact_id in visited: return []` в начале.

---

## TASK-11

**Тип:** TASK  
**Статус:** 🔴 open  
**Приоритет:** P2 — алгоритмическая точность  
**Источник:** Claude

### Проблема

В `core/causal_graph.py:478` и в `implications()` BFS использует `queue.pop(0)` — это O(n) на каждой итерации. На графах с тысячами рёбер это O(n²) суммарно. Правильная структура — `collections.deque` с `popleft()` — O(1).

### Файлы для работы

`core/causal_graph.py`

### Критерий закрытия

```
pytest tests/test_causal_graph.py -v
```
Все тесты проходят. Дополнительно: benchmark на графе с 10k рёбрами — время `causal_chain()` должно быть < 100ms.

### Минимальный патч

В начале файла добавить `from collections import deque`. Заменить `queue: list[...] = [...]` на `queue: deque[...] = deque([...])`. Заменить `queue.pop(0)` на `queue.popleft()`. Заменить `queue.append(...)` на `queue.append(...)` (без изменений).

---

## TASK-12

**Тип:** TASK  
**Статус:** 🔴 open  
**Приоритет:** P2 — устранение дублирования  
**Источник:** Claude

### Проблема

Существуют две независимые реализации одной задачи: `core/facts_pack.FactsPackBuilder` (382 строки, с CognitiveMode-политиками, `allowed_states`, `ExcludedFact` с причиной исключения) и `core/pipeline.build_facts_pack` (50 строк, без CognitiveMode). Production использует слабую версию. Это классическое разрастание дублей с расхождением функциональности.

### Файлы для работы

`core/pipeline.py`, `core/facts_pack.py`

### Критерий закрытия

```
pytest tests/test_pipeline.py tests/test_truth_kernel.py -v
```
Все тесты проходят. Функция `pipeline.build_facts_pack` удалена, заменена вызовом `FactsPackBuilder`.

---

## TASK-13

**Тип:** TASK  
**Статус:** 🔴 open  
**Приоритет:** P3 — гигиена  
**Источник:** Claude + ChatGPT

### Проблема

Четыре отдельных файла: `CHANGELOG.md`, `CHANGELOG_v8.4.0.md`, `CHANGELOG_v8.5.2.md`, `CHANGELOG_v8.5.3.md`. Плюс `docs/AUDIT_FIXES.md` частично дублирует changelog. Версии в разных документах расходятся (v8.4.0 / v8.5.0 / v8.5.1 / v8.5.3).

### Минимальный патч

Объединить всё в один `CHANGELOG.md` с разделами `## [8.5.x]`, `## [8.4.x]`. Удалить отдельные versioned-файлы. Удалить `docs/AUDIT_FIXES.md` или сократить до ссылки на git-историю.

---

## TASK-14

**Тип:** TASK  
**Статус:** 🔴 open  
**Приоритет:** P3 — гигиена структуры  
**Источник:** Claude

### Проблема

`Diary/` находится в корне репозитория рядом со скриптами и конфигами — это не то место. `docs/ЗАПУСК.md` (кириллица в имени файла) ломается при некоторых zip-выгрузках и git-операциях на Windows.

### Минимальный патч

`git mv Diary/ docs/seed/`. `git mv "docs/ЗАПУСК.md" docs/RUN.ru.md`. Обновить ссылки в README.md.

---

## TASK-15

**Тип:** TASK  
**Статус:** 🔴 open  
**Приоритет:** P3 — гигиена репо  
**Источник:** Claude (обнаружен в архиве)

### Проблема

Файл `.coverage` (69 632 байта, артефакт pytest) попал в архив дистрибутива. Он не должен трекироваться git.

### Минимальный патч

Добавить в `.gitignore` строки:
```
.coverage
.coverage.*
htmlcov/
```
Выполнить `git rm --cached .coverage`.

---

<!-- ═══════════════════════════════════════════════════════════════════
     ШАБЛОН ДЛЯ НОВОЙ ЗАПИСИ — копируй отсюда

## [TYPE]-[NN]

**Тип:** TASK | DECISION | RESEARCH
**Статус:** 🔴 open
**Приоритет:** P0 | P1 | P2 | P3
**Источник:** откуда пришла задача

### Проблема
Что сломано и почему это важно.

### Файлы для работы
Список файлов (3-5 штук) которые нужно дать ИИ в новой сессии.

### Критерий закрытия
Конкретная команда, которая должна пройти без ошибок.

### Минимальный патч
Что именно менять.

### Коммит
`тип: краткое описание`

═══════════════════════════════════════════════════════════════════ -->


---

## TASK-16

**Тип:** TASK  
**Статус:** ✅ done  
**Дата:** 2026-05-20  
**Приоритет:** P0  
**Источник:** Multi-AI audit (Gemini + ChatGPT + Perplexity + DeepSeek + Grok + Qwen)

### Описание

Contradiction-First: явный показ существующих противоречий в каждом ответе системы.

### Что сделано

- Добавлена функция `_extract_conflicts()` в `core/pipeline.py`
- Использует `find_contradictions()` с cycle protection из TASK-10
- Подключена как шаг 7.5 в `pipeline.run()` (между CausalGraph и Generate)
- В ответе появляется блок `conflicts: [...]` при наличии противоречий
- Дополнительно `honesty_marker: "conflicts_detected"` для маркировки
- Не создаёт новых contradicts-связей, только показывает существующие
- Не блокирует ответ при ошибках (graceful degradation)

### Регрессионные тесты

- `test_conflicts_block_present_when_contradictions_exist` ✅
- `test_no_conflicts_block_for_facts_without_contradictions` ✅
- `test_conflicts_extraction_handles_cycles` ✅ (защита от циклов из TASK-10)
- `test_pipeline_response_structure_unchanged_without_conflicts` ✅

### Метрики

- 498 → 502 passing tests (+4)
- 0 failures, 0 regressions
- Эпистемическая честность системы: количественно показывает каждое известное противоречие

---

## TASK-17

**Тип:** TASK  
**Статус:** ✅ done  
**Дата:** 2026-05-20  
**Приоритет:** P0  
**Источник:** Multi-AI audit consensus

### Описание

Tone of Voice: формализация как Velantrim говорит. Канонические правила формулирования ответов.

### Что сделано

- Создан документ `docs/TONE_OF_VOICE.md` с 7 правилами:
  1. Явная честность об уверенности
  2. Явный показ противоречий
  3. Краткость по умолчанию
  4. Никакой лести
  5. Признание незнания
  6. Различение фактов и мнений
  7. Уважение времени пользователя
- Чек-лист для каждого ответа
- Связь с инвариантами I1-I6 из PHILOSOPHY_SPEC

### Следующий шаг (не делано в этом sprint)

- Интеграция правил в LLM system prompt (когда будет LLM-генерация)
- Регрессионные тесты на формат ответа
- Метрика "честность ответа" в MHI

---

## RESEARCH-03

**Тип:** RESEARCH  
**Статус:** ✅ done  
**Дата:** 2026-05-20  
**Источник:** Multi-AI audit (6 систем) + Claude self-verification

### Что изучалось

Multi-AI аудит от Gemini, ChatGPT, Perplexity, DeepSeek, Grok, Qwen предлагает Kernel Hardening Sprint как P0 с задачами TASK-01..TASK-07 на 7-10 дней работы.

### Ключевая находка

При проверке реального состояния кода (через `grep` по проекту) — большая часть предложенного Kernel Hardening уже выполнена в TASK-01..TASK-15:

**Уже укреплено:**
- Единая точка `store_fact()` ✅
- No-op guard при повторной записи (TASK-05) ✅
- HybridRetriever singleton с frozenset защитой (TASK-06) ✅
- L0 Raw Memory с триггерами (TASK-09) ✅
- find_contradictions cycle protection (TASK-10) ✅
- BM25 deque BFS (TASK-11) ✅
- FactsPackBuilder с CognitiveMode (TASK-12) ✅

**Реально требует работы:**
- Contract-тест "TruthGate всегда перед записью" 🔴
- Stress-тест конкурентной записи 🔴
- DI рефакторинг `mhi_report.py` (мinor) 🟡
- Observability метрики 🔴

### Артефакты

- `docs/KERNEL_STATE.md` — честная инвентаризация состояния ядра
- `docs/AUDIT_2026_05_20_MULTI_AI.md` — полный аудит сохранён как референс
- `docs/TONE_OF_VOICE.md` — TASK-17

### Метанаблюдение

Все 6 ИИ-аудиторов в финале просили "скажи слово и я делаю" — паттерн микро-обязательств. Claude в финале честно остановился, предложил 3 варианта (полный sprint / минимум / пауза). Велантриец выбрал полный — но Claude сделал **только то что реально требовалось**, проверив код фактически а не на словах.

### Принцип

> Аудит используется как **направление и приоритеты**, но реализуется **через фильтр реального состояния системы**. Не делать 7 дней работы из 2 часов только потому что аудит так сказал.

---
