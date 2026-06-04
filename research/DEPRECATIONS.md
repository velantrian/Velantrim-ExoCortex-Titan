# 📋 Velantrim V8.7 Titan — Журнал устаревших технологий

> Принцип из Гиперии Encyclopedia: **ничего не удаляется — только помечается и заменяется.**
> Это позволяет понять эволюцию системы и причины каждого решения.

---

## ⚠️ ЧТО БЫЛО ЗАМЕНЕНО (ПРОВЕРЕНО ПО КОДУ V8.7)

| # | Устаревший компонент | Статус | Чем заменён в V8.7 | Где в коде |
|---|---------------------|--------|---------------------|------------|
| 1 | `UCB1` (выбор стратегий) | ✅ **ЗАМЕНЁН** | `Thompson Sampling` (Beta-распределение) — +8% cumulative reward | `core/reasoning_bank.py:59` — `thompson_sample()` |
| 2 | `boto3` (sync S3) | ✅ **ЗАМЕНЁН** | `memory_archival.py` — локальный JSON-архив. S3/MinIO — опциональный backend | `core/memory_archival.py` |
| 3 | `asyncio.Queue()` без лимита | ✅ **ЗАМЕНЁН** | `asyncio.Queue(maxsize=10_000)` — защита от OOM | `core/event_bus.py:26` — `MAX_QUEUE_SIZE = 10_000` |
| 4 | `datetime.now()` (наивный) | ✅ **ЗАМЕНЁН** | `datetime.now(timezone.utc)` — везде в коде | `core/memory.py`, все модули |
| 5 | `OpenAI text-embedding-3` | ✅ **ЗАМЕНЁН** | `sentence-transformers` (all-MiniLM-L6-v2) + опционально `deepvk/USER-bge-m3` (RU) | `core/hybrid_retriever.py` |
| 6 | `GPT-4` / `GPT-4o-mini` | ✅ **ЗАМЕНЁН** | `GPT-5.5` / `Claude Sonnet 4.6` / `Claude Opus 4.8` / `DeepSeek V4` / `Qwen 3.7` | `core/provider_catalog.py` |
| 7 | `Llama 3` | ✅ **ЗАМЕНЁН** | `Llama 4 Maverick` (17B×128E MoE, апрель 2025) — Scout deprecated | `core/provider_catalog.py` |
| 8 | `Qwen3` / `Qwen3.5` / `Qwen3.6` (все) | ✅ **ЗАМЕНЁН** | `Qwen3.7-Max` (21 мая 2026) + `Qwen3.7-Plus` (1 июня 2026) | `core/provider_catalog.py` |
| 9 | `DeepSeek V3` / `R1` / `V3.2` (все) | ✅ **ЗАМЕНЁН** | `DeepSeek V4 Pro` (1.6T) + `DeepSeek V4 Flash` (284B) — апрель 2026 | `core/provider_catalog.py` |
| 10 | `Claude 3.x` / `Claude Sonnet 4` (все) | ✅ **ЗАМЕНЁН** | `Claude Sonnet 4.6` (17 фев 2026) + `Claude Opus 4.8` (28 мая 2026) — 1M контекст | `core/provider_catalog.py` |
| 11 | `GPT-5.4` (все снапшоты) | ✅ **УДАЛЁН** | `GPT-5.5` — единственная актуальная | `core/provider_catalog.py` |
| 12 | `Redis Streams` (EventBus) | ✅ **ЗАМЕНЁН** | `asyncio.Queue` + SQLite fallback | `core/event_bus.py` |
| 13 | `Kafka` | ✅ **УБРАН** | `asyncio.EventBus` — для одного агента избыточен | — |
| 14 | `Ebbinghaus decay` | ✅ **ЗАМЕНЁН** | `FSRS power-law`: R = (1 + 19/81 × t/S)^(-0.5) | `core/fsrs.py` |

---

## 🟡 ЧТО ВСЁ ЕЩЁ АКТУАЛЬНО И РАБОТАЕТ

| # | Компонент | Статус | Где используется |
|---|----------|--------|-----------------|
| 1 | `SQLite` (WAL) | ✅ **Основа** | `core/memory.py` — всё хранилище фактов |
| 2 | `LadybugDB/Kuzu` (граф) | ✅ **Активно** | `core/backends/ladybug_graph.py` — Graph=Truth |
| 3 | `Neo4j` | 🟡 **Опционально** | `core/graphiti_adapter.py` — визуальный аудит / гранты / демо |
| 4 | `BM25 + Dense + RRF` | ✅ **Активно** | `core/hybrid_retriever.py` |
| 5 | `FTS5 trigram (NGramIndex)` | ✅ **Активно** | `core/ngram_index.py` |
| 6 | `sentence-transformers` | ✅ **Активно** | `core/hybrid_retriever.py` — Dense retrieval |
| 7 | `pymorphy3` | ✅ **Активно** | `core/lemmatizer_ru.py` — русская лемматизация |
| 8 | `aiosqlite` | ✅ **Опционально** | `core/async_store.py` — async DB (флаг `VELANTRIM_ASYNC_DB=1`) |
| 9 | `Prometheus` | ✅ **Опционально** | `core/metrics.py` — `/metrics` эндпоинт |
| 10 | `Gemini 3.5 Flash` | ✅ **Активно** | `core/provider_catalog.py` — Google Gemini (19 мая 2026, 1M контекст) |
| 11 | `Gemini 3.5 Pro` | 🟡 **Июнь 2026** | Внутреннее тестирование Google. GA ожидается в июне 2026 |

---

## 🟣 Neo4j — ОПЦИОНАЛЬНЫЙ БЭКЕНД

Neo4j **НЕ удалён** из архитектуры. Он остаётся опциональным для трёх сценариев:

| Сценарий | Зачем | Как включить |
|----------|-------|-------------|
| 🧬 **Визуальный аудит** | Neo4j Bloom — интерактивная визуализация графа. Видно связи, противоречия, кластеры | `STORAGE_BACKEND=neo4j` |
| 🎓 **Гранты / демо** | Красивая графовая визуализация для презентаций и статей | `NEO4J_URI=bolt://...` |
| 🔬 **Эксперименты** | Тестирование Cypher-запросов на реальном графе без LadybugDB | `GRAPHITI_NEO4J_URI=...` |

**По умолчанию:** `STORAGE_BACKEND=sqlite` (факты) + `STORAGE_BACKEND=ladybug` (граф). Neo4j — внешний сервер, включается только когда нужен.

**Файлы:** `core/graphiti_adapter.py` · `core/storage_facade.py` · `core/backends/`

---

## 🔮 ЧТО МОЖЕТ УСТАРЕТЬ В БУДУЩЕМ

| # | Компонент | Риск | Альтернатива |
|---|----------|------|-------------|
| 1 | `all-MiniLM-L6-v2` (эмбеддинги) | Слабая поддержка русского | `deepvk/USER-bge-m3` — лучшая RU-модель |
| 2 | `cross-encoder/ms-marco-MiniLM` (reranker) | EN-only | `Qwen3-Reranker` — #1 MTEB Multilingual |
| 3 | `KuzuDB` (legacy API) | Kuzu переименован в LadybugDB | `LadybugDB` — активный MIT-форк с совместимым API |
| 4 | `sync sqlite3` (в FastAPI) | Блокирует event loop | `aiosqlite` — уже есть за флагом, ждёт включения по умолчанию |

---

> 📅 **Последнее обновление:** 3 июня 2026 · V8.7 Titan
> 🔱 **Правило:** ничего не удаляется без записи в этот журнал. Каждая замена документируется с причиной.
