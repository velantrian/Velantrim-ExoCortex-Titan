# 🔩 Velantrim — Kernel State (Реальное состояние ядра)

**Версия:** 1.0
**Дата:** 20 мая 2026
**Назначение:** честная фиксация того, что в ядре системы укреплено, а что — нет.

---

## 🎯 Зачем этот документ

Когда внешние AI-аудиторы (Gemini, ChatGPT, Perplexity, DeepSeek и др.) предлагают
«Kernel Hardening Sprint» — важно понимать **что уже сделано** а что **реально
требует работы**. Этот документ — честная инвентаризация без преувеличений.

---

## ✅ Что УЖЕ укреплено (TASK-01..TASK-15 + TASK-16/17)

### Запись в память
| Аспект | Состояние | Где реализовано |
|--------|-----------|-----------------|
| Единая точка входа `store_fact()` | ✅ Done | `core/memory.py:212` |
| No-op guard при повторной записи | ✅ Done (TASK-05) | `core/memory.py:_is_noop()` |
| Validated ESM transition контролируется | ✅ Done | `core/memory.py:transition_esm()` |
| Batch-запись через одну транзакцию | ✅ Done | `core/memory.py:store_facts_batch()` |
| L0 Raw Memory immutable storage | ✅ Done (TASK-09) | `core/memory.py:store_raw_text()` |
| `derived_from` provenance link | ✅ Done (TASK-09) | `link_raw_to_fact()` |
| Triggers против изменения raw | ✅ Done | `migrations/010_raw_memory.sql` |

### Retrieval
| Аспект | Состояние | Где реализовано |
|--------|-----------|-----------------|
| `get_fact_ids()` без полной загрузки | ✅ Done (TASK-06) | `core/memory.py:946` |
| `get_facts_by_ids()` top-K fetch | ✅ Done (TASK-06) | `core/memory.py:950` |
| HybridRetriever singleton | ✅ Done | `core/pipeline.py:_get_hybrid_retriever()` |
| `mark_retriever_dirty` только при new INSERT | ✅ Done (TASK-04) | `pipeline.py + memory.py` |
| BM25 fallback с term overlap проверкой | ✅ Done | `core/pipeline.py:_retrieve_from_store()` |

### TruthGate / ESM
| Аспект | Состояние | Где реализовано |
|--------|-----------|-----------------|
| ESM матрица переходов | ✅ Done | `core/memory.py:ESM_TRANSITIONS` |
| Validated → Validated идемпотентность | ✅ Done | `transition_esm()` |
| ImmutableCore не выходит | ✅ Done | ESM матрица |
| TruthGate с 4 режимами CognitiveMode | ✅ Done | `core/truth_gate.py` |
| Pipeline вызывает truth_gate перед записью | ✅ Done | `core/pipeline.py:run()` шаг 5 |

### CausalGraph
| Аспект | Состояние | Где реализовано |
|--------|-----------|-----------------|
| 15 forward + 15 backward типов связей | ✅ Done | `core/causal_graph.py` |
| `find_contradictions` с cycle protection | ✅ Done (TASK-10) | `causal_graph.py:_visited_facts` |
| `causal_chain` с deque O(1) | ✅ Done (TASK-11) | `causal_graph.py` |
| Подключён в pipeline как шаг 7 | ✅ Done (TASK-08) | `pipeline.py:_extract_causal_hints` |
| Contradiction-First шаг 7.5 | ✅ Done (TASK-16) | `pipeline.py:_extract_conflicts` |
| Singleton с db_path tracking | ✅ Done | `pipeline.py:_get_causal_graph()` |

### Тестирование
| Аспект | Состояние |
|--------|-----------|
| Регрессионные тесты для P0 багов | ✅ 502 passed |
| Tests изолированы через monkeypatch | ✅ Done |
| `isolated_db` autouse фикстура | ✅ Done |
| Цикл protection тесты | ✅ Done (TASK-10, TASK-16) |

---

## ⚠️ Что ЧАСТИЧНО укреплено

### Контракты ядра
| Аспект | Состояние | Что нужно |
|--------|-----------|-----------|
| Документированный contract "TruthGate → store_fact" | 🟡 В коде, но не в тесте | Contract test |
| Документированный contract "L0 immutable" | 🟡 Через trigger SQL, не в Python | Test + assertion |
| Концепция Memory Tiers (L0/L1/L2/Pending/L3) | 🟡 Формализован contract | Runtime-подключение recursive router |
| RetrievalPath / compression / Guardian contracts | 🟡 Формализованы | Интеграция в `/query` и консолидацию |

### Конкурентность
| Аспект | Состояние | Что нужно |
|--------|-----------|-----------|
| asyncio paths в server.py | 🟡 Через `asyncio.to_thread` | Stress-test |
| SQLite WAL mode | 🟡 Подразумевается, не проверено | Явная настройка |
| Race condition защита | 🔴 Не тестировалось | Стресс-тест 100+ конкурентных записей |

### Идентичность системы
| Аспект | Состояние |
|--------|-----------|
| Tone of Voice документ | ✅ Done (TASK-17) `docs/TONE_OF_VOICE.md` |
| Tone в LLM system prompt | 🔴 Пока нет (LLM генерация не интегрирована) |
| Inversion tests в PHILOSOPHY_SPEC | ✅ Done |

---

## 🔴 Что НЕ укреплено (честно)

### Архитектурные дыры
1. **`mhi_report.py` импортирует `_GLOBAL_STORE` напрямую** — minor coupling.
   Не критично т.к. только для чтения, но это нарушение принципа DI.

2. **Нет contract test "TruthGate всегда вызывается до записи".**
   Сейчас это **дисциплина кода**, не **проверяемый инвариант**.
   Возможно при рефакторинге появится bypass — никто не заметит.

3. **Нет stress-теста конкурентной записи.**
   Pipeline работает корректно в тестах с одним потоком.
   Под нагрузкой 100+ одновременных POST /facts — неизвестно.

4. **`_HYBRID_RETRIEVER` singleton глобальный.**
   Сделана защита через `_HYBRID_FACT_IDS: frozenset` для детекции смены,
   но это эвристика, не строгий контракт.

5. **CausalGraph singleton через global переменную.**
   `_CAUSAL_GRAPH` + `_CAUSAL_GRAPH_DB_PATH` — работает для tests + production,
   но это не "чистая" архитектура.

### Knowledge model
6. **Нет `knowledge_type` (INVARIANT/VARIANT/PRACTICAL).**
   Все факты равны по природе. Идея есть в обсуждениях, не в коде.

7. **Memory Tiers имеют contract, но не полный runtime-router.**
   `core/fractal_memory.py` фиксирует L0 → L1 → L2 → Pending → TruthGate → L3,
   `RetrievalPath`, compression rules и Guardian layers, но
   `retrieval_mode="recursive"` ещё не подключён к `/query`.

### Observability
8. **Нет метрик** по latency pipeline, размеру памяти, конфликтам.
   Только MHI как агрегат.

9. **Нет traceability** какой запрос привёл к какому факту.
   `trace` есть в коде, но не сохраняется долговременно.

---

## 📊 Реальная оценка зрелости ядра

```
Если шкала 0-10:
   Запись:           8/10  ✅ хорошо
   Retrieval:        7/10  ✅ хорошо
   TruthGate:        7/10  ✅ хорошо
   CausalGraph:      8/10  ✅ хорошо (после TASK-16)
   Контракт-тесты:   3/10  🔴 слабо
   Конкурентность:   4/10  🔴 не проверено
   Observability:    3/10  🔴 слабо
   Knowledge model:  5/10  🟡 базовая, нужна доработка

   ОБЩАЯ ЗРЕЛОСТЬ:  ~6.5/10
```

**Это нормально для проекта в активной разработке.**
**Не "сломано" — но и не "production-ready" по строгим стандартам.**

---

## 🛤️ Что делать дальше (приоритеты)

### Сейчас (после TASK-16/17):
- ☑ Contradiction-First подключён к pipeline
- ☑ Tone of Voice зафиксирован документально
- ☑ 502 теста passing

### Следующая итерация (после паузы и обдумывания):
- 🔧 Contract test: "TruthGate вызывается перед каждым store_fact в production-пути"
- 🔧 Stress test: 100+ конкурентных INSERT/UPDATE
- 🔧 DI рефакторинг `mhi_report.py` (убрать прямой импорт _GLOBAL_STORE)

### Через 2-3 итерации:
- 📚 Knowledge types (INVARIANT/VARIANT/PRACTICAL)
- 🗂️ Fractal Memory Router: optional recursive retrieval + `memory_route` в TRACE
- 📊 Observability metrics

### V10 vision (отложено):
- 🌐 Multi-domain retrieval
- 🧬 Synaptic decay
- 🌙 NeuroSleep phases

---

## 🤝 Контракт с будущими аудиторами

Если внешний AI-аудитор предлагает «срочно делать Kernel Hardening Sprint» —
этот документ показывает что **большая часть hardening уже сделана** в
TASK-01..TASK-17. Что **реально требует работы** — задокументировано в разделе
«Что НЕ укреплено».

**Не делать всё что предлагает аудит автоматически.** Проверять — что уже есть.

---

> 🌿 *Этот документ — честный self-report. Он намеренно показывает дыры наряду
> с достижениями. Это лучше чем красивая отчётность "всё готово".*
