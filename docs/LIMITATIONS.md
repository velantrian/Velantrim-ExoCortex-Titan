# LIMITATIONS.md — Velantrim V8 Crystal

> Версия: **v8.6.0** (репозиторий; док актуализирован на v8.4.0) · Production readiness ~35%
>
> Это не список стыда — это карта долга. Каждый пункт имеет назначенный Sprint.
>
> **v8.4.0 обновление:** добавлены пункты по NGram split (закрыт), SleepTimeWorker
> startup (закрыт), HybridRetriever per-request (закрыт), CORS/API_KEY defaults
> (закрыты). Счётчик тестов перепроверен на v8.6.0 (2026-05-30): реально
> **610 тест-функций в 46 файлах** (`grep -rc 'def test_' tests/`), а не «256 в 11» —
> прежняя цифра, по-видимому, считала только верхнеуровневые файлы.

---

## Производительность

| # | Ограничение | Детали | Sprint |
|---|-------------|--------|--------|
| ~~P-1~~ | ~~O(N) retrieval~~ | ✅ **Закрыто в v8.3.0**: `NGramIndex` (FTS5 trigram) сужает кандидатов до `limit=50` за O(log N) до BM25. Graceful degradation если FTS5 недоступен. | ✅ Done |
| P-2 | **Мега-блобы** | `idx=8` (56k chars), `idx=12` (120k chars), `idx=60` (81k chars) снижают recall. BM25 деградирует на документах >10k токенов. Для длинных документов рекомендуется BM25L или гибридный reranker. | S2a |
| ~~P-3~~ | ~~Нет индексов L1~~ | ✅ **Закрыто в v8.2.0**: добавлены индексы на `epistemic_state`, `t_ingestion_start`, `t_ingestion_end`, `t_event_valid_start`, `t_event_valid_end`. | ✅ Done |
| P-4 | **Per-op connection** | `_db()` пересоздаёт соединение каждую операцию. Безопаснее для concurrency, но медленнее. Sprint 2c — `aiosqlite` + connection pool. | S2c |

---

## Конкурентность

| # | Ограничение | Детали | Sprint |
|---|-------------|--------|--------|
| C-1 | **Sync only** | Весь `core/` синхронный. Переход на `async/await` + `aiosqlite` — Sprint 2c. До перехода не подключать EventBus и Neo4j — заблокируют event loop. | S2c |
| C-2 | **Split-brain window** | В `transition_esm()` между `UPDATE facts` (L1) и `_l0_put` (L0) есть микро-окно при сбое процесса. После рестарта `get_fact()` читает L1 корректно (D4 обеспечивает порядок L1→L0). Нет runtime-алерта при обнаружении расхождения. | S2c |
| C-3 | **L0 не thread-safe** | `OrderedDict` без блокировок. Безопасно только в single-thread asyncio. При переходе на async добавить `asyncio.Lock` (аналогично патчу L1.5 Velum P0.5). | S2c |

---

## Данные и схема

| # | Ограничение | Детали | Sprint |
|---|-------------|--------|--------|
| D-1 | **DATABASE = dev-mock, не дефолт** | ✅ **Уточнено в v8.6.0:** `retrieve()` читает из реального стора; пустой стор → `[]`. 5 хардкоженных фактов (`_DATABASE_DEV_ONLY`) — fallback только при `VELANTRIM_DEV_MOCK=true` (`core/pipeline.py:605`). Реальный L3-граф (Kuzu/Neo4j) — по-прежнему S2b; `GraphStore ABC` и bi-temporal схема готовы. | ✅/S2b |
| D-2 | **rfc_refs без чанков** | Часть RFC referenced, но не все существуют как чанки в JSONL. Граф знаний частично ненасыщен. | S3 |
| D-3 | **`status: stable` для всех** | Все 63 чанка помечены `stable` включая черновики. Поле не несёт информации. | S3 |
| D-4 | **`layer` у 1 чанка = null** | `idx=0` (заголовочный чанк) не имеет слоя. Намеренно. | — |
| D-5 | **TruthGate = confidence floor** | MVP: пороговая проверка `confidence >= 0.5`. Нет `evidence_count`, нет cross-graph validation, нет mode-aware thresholds. → Рефакторинг в `core/truth_gate.py`. | S2 |
| D-6 | **search() = заглушка** | `SQLiteGraphStore.search()` — `LIKE` по claim. Нет FTS5-индекса, нет семантического поиска. Нарушает контракт `GraphStore ABC` — клиенты могут ожидать семантику. | S2a |

---

## Bi-temporal (частичная реализация)

| # | Ограничение | Детали | Sprint |
|---|-------------|--------|--------|
| BT-1 | **SQLite, не Neo4j** | Bi-temporal поля реализованы в SQLite как TEXT (ISO 8601 UTC). Работает корректно только если все timestamp строго UTC без суффикса timezone. Нет enforcement timezone при `store_fact()`. Neo4j имеет нативный `datetime` тип. | S2c |
| BT-2 | **BlackboardBus не реализован** | I97 зафиксирован в `GraphStore ABC` контракте, но `BlackboardBus` как отдельный компонент не написан. Прямые вызовы `store_fact()` — MVP допустимо. | S2c |
| BT-3 | **Нет Cold Storage GC** | I96 запрещает DELETE. Факты в `Collapsed` с `t_ingestion_end > 6 месяцев` будут бесконечно накапливаться в L1. Нужен GC → архив (DuckDB/S3). | S3 |
| BT-4 | **Миграция bi-temporal L1 → L3 не спроектирована** | Стратегия переноса 4 полей `t_*` из SQLite TEXT в Neo4j `datetime` не описана. Риск потери `t_ingestion_*` при консолидации. | S2c |

---

## A6–A10 (Sprint A патчи)

| Патч | Статус | Что не так |
|------|--------|------------|
| A6 EventBus | 📄 documented, not wired | TOCTOU deque · **`aioredis` deprecated → использовать `redis.asyncio` из `redis>=4.2.0`** (aioredis не работает на Python 3.11+) |
| A7 LockManager | 📄 documented, not wired | `_global_lock_order` не используется · **`min_idle` → `max_connections`** (устаревший параметр API) |
| A8 CircuitBreaker | 📄 documented, not wired | — |
| A9 RateLimiter | 📄 documented, not wired | — |
| A10 HealthCheck | 📄 documented, not wired | — |

> ⚠️ **ВАЖНО для A6**: никогда не использовать `import aioredis` — библиотека заброшена и вызывает `TypeError: duplicate base class TimeoutError` на Python 3.11+. Правильный импорт: `from redis.asyncio import Redis`.

Подключение всех патчей — **Sprint 2c**.

---

## TRUSTED_SOURCES (I98)

| # | Ограничение | Детали | Sprint |
|---|-------------|--------|--------|
| TS-1 | **Нет стратегии конфликтов между доверенными источниками** | Если два `domain_seed` источника дают взаимоисключающие факты — системы разрешения нет. | S2 |
| TS-2 | **TrustedSources "замораживают" ошибочные факты** | Если `ring_zero` или `domain_seed` источник ошибся, факт нельзя ни Contradict, ни изменить claim через обычный путь. Нужен `emergency_invalidate_trusted()` с 2-approval flow. | S2 |

---

## Покрытие инвариантов спеки

| Аспект | Цифры |
|--------|-------|
| Инвариантов в JSONL-спеке | ~94 нумерованных + 17 RFC/sub |
| Документировано в `INVARIANTS.md` | I1, I2, I6, I50, I50-b, I68, I96, I97, **I98, I99, I100–I103** + D1–D7, PL1–PL4, S1–S3 |
| **Не задокументировано** | **~76 нумерованных** (критичные: I28, I38, I49) |

→ Sprint 3 цель: автогенерация описаний из JSONL.

---

## SLO (честные цифры)

| Метрика | До v8.4.0 | После v8.4.0 | Цель S2 |
|---------|-----------|--------------|---------|
| Production readiness | ~28% | ~35% | ~55% |
| Latency (5 фактов mock) | < 50ms | < 50ms | < 50ms |
| Latency (HybridRetriever singleton) | N/A (per-req init) | ~50-200ms warm | < 2s |
| Latency (HybridRetriever cold start) | ~1-2s каждый раз | ~1-2s один раз | ~500ms |
| Test coverage (`core/*`) | 81% | 86% | > 90% |
| Тесты | 191 (заявлено) / 160 (реально) | **256 (реально)** + new regression | расширение по мере роста |
| Critical P0 bugs | 0 ✅ | 0 ✅ | 0 |
| Critical integration bugs | 7 (server, sleep, NGram, CORS, etc) | **0 ✅** (все закрыты в v8.4.0) | 0 |
| Bi-temporal: 4 поля на факт | ✅ SQLite | ✅ SQLite | ✅ Neo4j Sprint 2c |
| TruthGate contradiction-stage | naive default (false positives!) | **disabled default** (opt-in only) | NLI via ATLAS-OS Sprint 2c |
| SleepTimeWorker реальный запуск | ❌ TypeError тихо | ✅ запускается | ✅ + реальный LLM |
| HybridRetriever singleton | ❌ per-request init | ✅ singleton + dirty flag | ✅ + Redis cache |
