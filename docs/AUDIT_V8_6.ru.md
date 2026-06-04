# Полный аудит VELANTRIM V8.6 Complex

> **Дата:** 23 мая 2026 (ревизия после спринтов 1–3 и V10 MVP)  
> **Репозиторий:** `VELANTRIM_ExoCortex_V8.6` (папка переименована)  
> **Продукт:** VELANTRIM V8.6 Complex · `server.py` v8.6.0  
> **Связанный fork:** `../Graphiti_fractal-main` (Graphiti/Neo4j, не канон; в каноне — адаптер)

---

## 1. Резюме для руководства

| Критерий | Оценка | Доказательство |
|----------|--------|----------------|
| Ядро памяти L0–L1 + pipeline | 🟢 **Production-ready (dev)** | Полный pytest: **596 passed** (после fix checksum+drift); спринты 1–3: **49/49** |
| ExoCortex L1.5–L5.5 (код) | 🟡 **Beta, выкл. по умолчанию** | `exocortex-dev.env` включает Velum/Etir/L45/… |
| L6 Welfare MVP | 🟡 **MVP, выкл. по умолчанию** | `welfare_monitor`, `volition_gate`, Innenwelt API |
| Innenwelt / ModeRouter / Umwelt | 🟡 **MVP** | `goal_stack`, `core/router/`, `umwelt_store`, PolyWelt (6 агентов) |
| CognitiveFact v9.x + Runtime V10 | 🟡 **MVP** | `cognitive_store`, `cognitive_runtime`, `/cognitive/*`, `/runtime/status` |
| CrossDomain V3 | 🟡 **MVP** | `cross_domain.py`, smart/LLM routing, `analogous_to` в CausalGraph |
| Horizons (research) | 🟢 **Документировано** | 14 карточек + API `/horizons` |
| Graphiti / Neo4j в V8.6 | 🟡 **Адаптер (опц.)** | `graphiti_adapter`, `POST /causal/reload-from-graph`; без live Neo4j — no-op/stub |
| CI / упаковка | 🟢 | `pip install -e .` (P1-3), CI matrix |

**Вердикт:** V8.6 остаётся **каноническим репозиторием**; поверх ядра добавлены **спринты 1–3** (консолидация, Innenwelt, Telegram, CognitiveFact, Umwelt) и **V10 MVP** (runtime, cross-domain). Big-bang замены `memory.py` на `CognitiveFactStore` **нет** — параллельный путь ingest/query. Research-слои (L2.5 staging, NLI Truth Gate, MHI Phase 2) **без полного runtime**.

---

## 2. Объём и метод аудита

Проверено:

- Структура `core/` (**~83** Python-модуля верхнего уровня + `core/router/`), `api/exocortex_api.py`, `app/telegram_ingest.py`, `server.py`
- Документация: `docs/HORIZONS.md`, `docs/ROADMAP_FROM_SYSTEM.ru.md`, `docs/horizons/`
- Тесты: `pytest tests/` — **626 collected**; новые модули (cognitive, cross-domain, innenwelt, umwelt, telegram, sprint1): **49 passed** (~2.5 мин, `--no-cov`)
- Live runtime: uvicorn `:8755`, `GET /health`, `/layers/status`, `/horizons`, `/runtime/status` (при флагах)
- Перенос / адаптер Graphiti: `core/graphiti_adapter.py`, `core/causal_persistence.py`

Не входило в аудит: нагрузочное тестирование, pen-test, production Neo4j, полный coverage ≥80%.

---

## 3. Архитектура (фактическая)

```
Пользователь / Telegram / агент
        │ HTTP (X-Api-Key) · webhook /telegram/*
        ▼
server.py (FastAPI 8.6)
        │
        ├── POST /query ──────────► pipeline (+ cross_domain plan/retrieve, опц.)
        ├── POST /facts, /ingest/text, /cognitive/facts
        │         ├── memory.py (канон L1) + get_raw_text_for_fact (L0)
        │         └── cognitive_store.save_fact_dict (опц., v9.x)
        ├── ModeRouter /goals /gaps /innenwelt /umwelt/* (опц.)
        ├── cognitive_runtime (fact_* → EventBus → NGram incremental)
        └── L6/L4.5/ExoCortex · /runtime/status · /cross-domain/* (опц.)
                │
                ▼
SQLite + NGram FTS + CausalGraph (+ analogous_to cross_domain)
                │
                ├── consolidation_engine · fact_integrity (спринт 1)
                └── storage_facade (sqlite | memory | kuzu | …)
                        └── graphiti_adapter → import_snapshots (опц.)
```

**Принципы (инварианты):** Graph = Truth · ESM-переходы через Truth Gate · L0 immutable.

---

## 4. Карта слоёв runtime

Источник истины API: `GET /layers/status` · документ: [LAYERS_AND_HORIZONS.ru.md](LAYERS_AND_HORIZONS.ru.md)

| Слой | Статус по умолчанию | ENV / примечание |
|------|---------------------|------------------|
| L0 Raw Memory | 🟢 on | — |
| L1 ESM + Truth Gate + pipeline | 🟢 on | `ENABLE_TRUTH_GATE` |
| L1.5 Velum, Salience | 🟡 off | `ENABLE_VELUM`, `ENABLE_SALIENCE` |
| L2 Concept Emergence | 🟡 off | `ENABLE_CONCEPT_EMERGENCE` |
| **L2.5 Staging** | 🔬 **research** | нет кода · [horizons/L2_5_STAGING.md](horizons/L2_5_STAGING.md) |
| L3 SQLite graph | 🟢 on | `STORAGE_BACKEND` |
| L3.5a Etir | 🟡 off | `ENABLE_ETIR` |
| L3.5b Immutable Core | 🟡 off | `ENABLE_IMMUTABLE_CORE` |
| L4 Causal | 🟢 on* | `ENABLE_CAUSAL_GRAPH` |
| L4 Reasoning Bank | 🟡 off | `ENABLE_REASONING_BANK` |
| L4.5 Audit / Focus / Volition | 🟡 off | `ENABLE_L45` |
| L5.5 Predictive Fusion | 🟡 off | `ENABLE_PREDICTIVE_FUSION` |
| Decay Orchestrator | 🟡 off | `ENABLE_DECAY_ORCHESTRATOR` |
| L6 Welfare MVP | 🟡 off | `ENABLE_L6_WELFARE` |
| EventBus | 🟡 off | `ENABLE_EVENT_BUS` |
| SleepTimeWorker | 🟢 on* | `SLEEP_WORKER_ENABLED` |
| **Consolidation + episode dedup** | 🟡 off | `POST /memory/consolidate`, `ENABLE_EPISODE_DEDUP` |
| **Innenwelt (goals/gaps)** | 🟡 off | `ENABLE_INNENWELT` |
| **ModeRouter** | 🟡 off | `ENABLE_MODE_ROUTER` — PERSONAL / VELANTRIM / UMWELT |
| **Umwelt store + PolyWelt** | 🟡 off | `ENABLE_UMWELT_STORE`, 6 перцепторов в registry |
| **CognitiveFact + store** | 🟡 off | `ENABLE_COGNITIVE_FACT`, `ENABLE_COGNITIVE_STORE` |
| **Cognitive Runtime V10** | 🟡 off | `ENABLE_COGNITIVE_RUNTIME` |
| **CrossDomain V3** | 🟡 off | `ENABLE_CROSS_DOMAIN`, `ENABLE_CROSS_DOMAIN_CAUSAL` |
| **Telegram ingest** | 🟡 off | `ENABLE_TELEGRAM_INGEST` |
| **Domain tags** | 🟡 off | `ENABLE_DOMAIN_TAGS` |

\* Отключение возможно через ENV. Dev-профиль: [config/exocortex-dev.env](../config/exocortex-dev.env).

---

## 5. Спринты 1–3 и V10 (реализовано в коде)

| Блок | Модули / API | Статус |
|------|----------------|--------|
| Спринт 1: консолидация, целостность | `consolidation_engine`, `fact_integrity`, `/memory/consolidate` | ✅ MVP |
| Спринт 2: Innenwelt, router, Telegram, Graphiti | `goal_stack`, `gap_detector`, `router/`, `telegram_ingest`, `graphiti_adapter` | ✅ MVP |
| Спринт 3: CognitiveFact, relations, Umwelt | `cognitive_fact`, `cognitive_store`, `/facts/{id}/relations`, `umwelt_store` | ✅ MVP |
| V10: Unified Runtime | `cognitive_runtime`, `GET /runtime/status` | 🟡 MVP |
| V10: PolyWelt 6 агентов | `poly_welt_registry`, `GET /umwelt/agents` | 🟡 registry + seed |
| V10: CrossDomain | `cross_domain.py`, `POST /query` → `cross_domain` | 🟡 MVP |

Дорожная карта: [ROADMAP_FROM_SYSTEM.ru.md](ROADMAP_FROM_SYSTEM.ru.md). Не сделано: big-bang замена store, политики 6 агентов, NLI Truth Gate, MHI Phase 2.

---

## 6. Horizons (исследования)

| Категория | Кол-во в API | Документация |
|-----------|--------------|--------------|
| research | 7 | L2.5, L6 full, R2–R5, KDE |
| experimental | 7 | E1, E2, E3–E7 |
| vision (V1+) | — | только V9 §, без отдельных `.md` |

Индекс: [horizons/README.md](horizons/README.md) · `GET /horizons`

**Легенда:** 🔬 research = спека есть, production-кода нет · 🧪 experimental = Phase 0 / partial.

---

## 7. HTTP API (инвентарь)

### Система и память (ядро)

| Метод | Путь | Auth |
|-------|------|------|
| GET | `/`, `/health` | health — опц. |
| POST | `/query` (+ `cross_domain` при `ENABLE_CROSS_DOMAIN`) | ✅ |
| GET/POST | `/facts`, `/facts/{id}`, transition, invalidate, time-travel | ✅ |
| GET | `/facts/{id}/cognitive`, `/facts/{id}/relations` | `ENABLE_COGNITIVE_*` / relations |
| GET/POST | `/cognitive/facts` | `ENABLE_COGNITIVE_STORE` |
| POST | `/ingest/text` | ✅ |
| GET | `/memory/stats`, `/memory/rebuild-index`, POST `/memory/consolidate` | ✅ |
| POST | `/causal/reload-from-graph` | Graphiti adapter (опц.) |
| GET | `/agent/notebook`, `/agent/suggest`, POST `/agent/episode` | ✅ |

### ExoCortex / Layers / Horizons

| Метод | Путь | Требует флаг |
|-------|------|--------------|
| GET | `/layers/status` | — |
| GET | `/horizons` | — |
| POST | `/etir/activate` | `ENABLE_ETIR` |
| GET | `/focus` | `ENABLE_L45` / `ENABLE_FOCUS_ENGINE` |
| GET | `/audit/recent` | `ENABLE_RESPONSE_AUDIT` / `ENABLE_L45` |
| GET/POST | `/immutable/snapshots` | `ENABLE_IMMUTABLE_CORE` |
| GET | `/welfare` | `ENABLE_L6_WELFARE` |
| POST | `/memory/volition` | `ENABLE_MEMORY_VOLITION` / L6 |
| GET | `/eventbus/metrics` | `ENABLE_EVENT_BUS` |
| GET | `/runtime/status` | `ENABLE_COGNITIVE_RUNTIME` |
| GET/POST | `/cross-domain/bridges`, `/plan`, `/link-causal` | `ENABLE_CROSS_DOMAIN` |
| GET/POST | `/goals`, `/gaps`, `/innenwelt` | `ENABLE_INNENWELT` |
| GET/POST | `/router/modes`, `/router/route` | `ENABLE_MODE_ROUTER` |
| GET/POST | `/umwelt/*`, `/umwelt/agents`, `/umwelt/seed` | `ENABLE_UMWELT_STORE` |
| POST | `/telegram/ingest`, `/telegram/webhook`, GET `/telegram/status` | `ENABLE_TELEGRAM_INGEST` |

Export-эндпоинты: `server_patch/export_endpoints.py` (с auth).

OpenAPI: `/docs` при запущенном uvicorn.

---

## 8. Интеграция ExoCortex (после переноса из Graphiti)

| Компонент | Файл | Подключение |
|-----------|------|-------------|
| ENV-конфиг | `core/feature_config.py` | Единый `get_config().app.*` |
| Ingest observe | `core/exocortex_hooks.py` | `server.py` facts + ingest background |
| Query enrich | `exocortex_hooks.enrich_query_context` | `pipeline.py` шаг 9 → `exocortex_sections` |
| Event handlers | `core/event_bridge.py` | L6 + L45 при lifespan |
| HTTP helpers | `api/exocortex_api.py` | layers, etir, focus, audit, immutable |
| Каталог Horizons | `core/horizons_catalog.py` | `/horizons`, `/layers/status` |
| Порт-скрипт | `scripts/port_exocortex_from_fractal.py` | Повторный перенос из fork |

Перенесённые модули (примеры): `velum`, `etir`, `immutable_core`, `concept_emergence`, `l45_bridge`, `predictive_fusion`, `decay_orchestrator`, `storage_facade`, backends.

---

## 9. Тестирование

| Набор | Результат |
|-------|-----------|
| Полный `tests/` (23.05.2026, `--no-cov`, ~13 мин) | **596 passed**, 17 skipped, 13 xfailed (до fix: 593+3 fail — checksum после `transition_esm`) |
| Спринты 1–3 + V10 (целевой прогон) | **49 passed** (~2.5 мин) |
| ExoCortex + Horizons | 47+ passed (import, flags, e2e, causal_bridge) |
| L6 welfare | 4 passed |
| Smoke | 35+ passed |

**Исправлено (23.05):** `content_checksum` обновляется в `update_state` после ESM-перехода; `assert_claim_update_allowed` не блокирует TASK-02 drift при смене `claim`.

Запуск:

```powershell
.\scripts\run_tests.ps1
# или
.\.venv\Scripts\python.exe -m pytest tests/ --no-cov -q
```

CI: `.github/workflows/ci.yml` (matrix: default + exocortex flags).

**Примечание:** `pyproject.toml` задаёт `--cov=core` и `fail_under=80` — для локального полного прогона рекомендуется `--no-cov`.

---

## 10. Runtime-проверка (пример)

```
Uvicorn http://127.0.0.1:8755
Application startup complete
Migrations: 008, 009, 010
GET /health → healthy
GET /layers/status → product VELANTRIM V8.6 Complex
GET /horizons → research=7, experimental=7
GET /runtime/status → enabled, ngram_subscriber (при exocortex-dev.env)
GET /umwelt/agents → 6 agents (engineer, scientist, …)
POST /query → cross_domain.routing (при ENABLE_CROSS_DOMAIN=1)
```

При пустой БД: NGram rebuild 0 validated — ожидаемо.

---

## 11. Безопасность

| Тема | Статус | Рекомендация |
|------|--------|--------------|
| API key | Реализован `X-Api-Key` | Production: обязательный ключ |
| Open mode | `VELANTRIM_ALLOW_OPEN=true` | Только dev |
| CORS | Пустой список по умолчанию | Явно задать origins в prod |
| Секреты в git | Не обнаружены | `.env` в gitignore |
| SQL injection | SafeFTSQuery, параметризованный SQLite | Поддерживать |
| Welfare / volition | Блок при RED (L6) | Включать L6 в prod осознанно |

---

## 12. Найденные проблемы

### P0 — блокеры production (нет)

Критических падений при старте и полном pytest нет.

### P1 — исправлено (22.05.2026)

| ID | Было | Исправление |
|----|------|-------------|
| P1-1 | Нет `causal_persistence` | `core/causal_persistence.py` (Neo4j no-op без graphiti) |
| P1-2 | `asyncio.run` в pipeline | `core/async_utils.run_coroutine_sync` |
| P1-3 | `pip install -e .` | `LICENSE` + `[tool.setuptools.packages.find]` |
| P1-4 | Дубли `is_l6_welfare_enabled` | Канон: `core/runtime_flags.py` |

### P2 — техдолг (актуально)

- Глобальные синглтоны `_GLOBAL_STORE`, NGram, `CognitiveFactStore` — TODO DI
- Truth Gate NLI — `NotImplementedError` (Horizon V5)
- Live Neo4j ingest — только через fork; в каноне — **адаптер** + reload snapshots без обязательного кластера
- Два пути записи фактов (`memory` vs `cognitive_store`) — нужна стратегия конвергенции (без big-bang)
- EventBus: частичная унификация v9.4 (`event_bridge` + runtime subscribers)
- Параллельный DDL `derived_from` при concurrent pipeline (смягчено в тестах)
- ~~3 теста drift/checksum~~ — исправлено: refresh checksum в `update_state`

### P3 — косметика

- Vision V1+ без отдельных карточек в `docs/horizons/`
- Graphiti fork — только redirect в `docs/HORIZONS.md`

---

## 13. Сравнение с Graphiti_fractal-main

| Аспект | V8.6 (канон) | Graphiti fork |
|--------|--------------|---------------|
| Сервер | `server.py` | `app.py` |
| L6 MVP + Innenwelt | ✅ | redirect / legacy |
| Horizons docs | ✅ полный набор | redirect |
| Neo4j ingest | 🟡 адаптер `graphiti_adapter` | ✅ native |
| CognitiveFact / CrossDomain | ✅ MVP | в основном в V9-спеках |
| SleepTimeWorker | ✅ | ❌ |
| Etir/L4.5 Beta | код, off по умолчанию | был primary |

См. [RELATED_PROJECTS.ru.md](RELATED_PROJECTS.ru.md).

---

## 14. Рекомендации (дорожная карта)

### Немедленно (dev)

1. Скопировать [config/exocortex-dev.env](../config/exocortex-dev.env) → `.env`
2. Задать `VELANTRIM_API_KEY`, убрать `VELANTRIM_ALLOW_OPEN` вне dev
3. Сценарий: fact → `GET /facts/{id}/cognitive` → `POST /query` (поле `cross_domain` при флаге)
4. `GET /runtime/status` при `ENABLE_COGNITIVE_RUNTIME=1`

### Выполнено (май 2026) — не дублировать

- ~~P1: `causal_persistence`, async enrich, `pyproject`/`LICENSE`, L6 flags~~
- ~~Спринт 1: consolidation, fact_integrity~~
- ~~Спринт 2–3: Innenwelt, router, Telegram, CognitiveFact store, Umwelt MVP~~
- ~~V10 MVP: runtime, cross-domain, PolyWelt registry~~

### Следующий спринт

1. Периодический полный `pytest tests/ --no-cov` в CI (~13 мин)
2. Политики 6 Umwelt-агентов (не только registry/seed)
3. Конвергенция `memory` ↔ `CognitiveFactStore` (единый write-path)
4. Опционально: `ENABLE_CROSS_DOMAIN_LLM_ROUTING=1` + smoke

### Средний срок (Horizons)

1. L2.5 Staging prototype (RFC0014)
2. Live Neo4j cluster + production Graphiti sync
3. Полный L6 RFC0069 (IntrospectionProbe)
4. NLI Truth Gate (V5), MHI Phase 2 (V4)

---

## 15. Чеклист «готовность к демо ExoCortex + V10 MVP»

- [ ] `.env` из `exocortex-dev.env`
- [ ] `GET /layers/status` — нужные слои `enabled: true`
- [ ] `POST /facts` → `GET /facts/{id}/cognitive` (при `ENABLE_COGNITIVE_FACT`)
- [ ] `POST /query` — `exocortex_sections` и/или `cross_domain`
- [ ] `GET /runtime/status` — subscribers, dirty retriever
- [ ] `GET /umwelt/agents` — 6 перцепторов
- [ ] `ENABLE_L6_WELFARE=1` → `GET /welfare`, volition 409 при RED
- [ ] `pytest tests/test_exocortex_e2e.py tests/test_cognitive_runtime.py -v`

---

## 16. Связанные документы

| Документ | Назначение |
|----------|------------|
| [HORIZONS.md](HORIZONS.md) | Индекс Horizons |
| [LAYERS_AND_HORIZONS.ru.md](LAYERS_AND_HORIZONS.ru.md) | Таблица слоёв |
| [horizons/README.md](horizons/README.md) | Карточки |
| [Velantrim_V9_Final_Audited.md](Velantrim_V9_Final_Audited.md) | Спека V9 |
| [RELATED_PROJECTS.ru.md](RELATED_PROJECTS.ru.md) | Границы репозиториев |
| [ROADMAP_FROM_SYSTEM.ru.md](ROADMAP_FROM_SYSTEM.ru.md) | Спринты: system docx → V8.6 → V10 |
| [../CHANGELOG.md](../CHANGELOG.md) | История 8.6.0 |
| [../README.md](../README.md) | Быстрый старт |

---

*Аудит: ExoCortex/Horizons (22.05) + спринты 1–3 и V10 MVP (23.05). При изменениях архитектуры обновляйте этот файл, `CHANGELOG.md` и `GET /layers/status`.*
