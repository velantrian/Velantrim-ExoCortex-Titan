# Дорожная карта: `Documents\system` → VELANTRIM V8.6 → V10

> **Источник:** `C:\Users\VELAN\Documents\system\` (4 docx: эксперимент, v2, полная, v4)  
> **База кода:** `VELANTRIM_ExoCortex_V8.6` (V8.6 Complex)  
> **Дата:** 22.05.2026

Легенда **эмоций** (ценность / риск):

| | |
|---|---|
| 🚀 | Высокий эффект — брать в приоритет |
| 🟢 | Уже есть — включить или использовать |
| 🟡 | Частично — доработка |
| ⚠️ | Сложно / долго / политики |
| 💤 | Horizons / V10+ |

---

## Спринт 0 — «сегодня» (0–2 дня, без нового кода)

Цель: выжать максимум из **уже реализованного** (Kuzu подключён).

| # | Действие | Файлы / API | Эффект | |
|---|----------|-------------|--------|---|
| 0.1 | Перезапуск с `config/exocortex-kuzu.env` | `scripts/start_kuzu_server.ps1` | L3 = Kuzu, MHI `graph_coverage=1` | 🟢 |
| 0.2 | Загрузить 20–50 фактов + 10 query | `POST /facts`, `POST /query` | ↑ `validated_ratio`, MHI → 0.6+ | 🚀 |
| 0.3 | Включить dev-профиль ExoCortex | `config/exocortex-dev.env` | Velum, Etir, L45, L6 в `/layers/status` | 🟢 🚀 |
| 0.4 | Проверить `exocortex_sections` в query | `ENABLE_VELUM=1`, `VELUM_HINT_MIN_WEIGHT=0.05` | Контекст L1.5 в ответе | 🟡 🚀 |

**Критерий готовности:** `/health` → MHI ≥ 0.60, `GraphStore: KuzuGraphStore` в логе.

---

## Спринт 1 — одна неделя ✅ (22.05.2026)

Цель: закрыть **боль из docx v2**, не ломая V8.6.

| # | Тема | Реализация | Статус |
|---|------|------------|--------|
| 1.1 | **ConsolidationEngine** | `core/consolidation_engine.py`, SleepTimeWorker, `POST /memory/consolidate` | ✅ |
| 1.2 | **checksum** | `core/fact_integrity.py` → metadata в `store_fact` | ✅ |
| 1.3 | **episode_hash dedup** | `POST /facts`, `ENABLE_EPISODE_DEDUP` | ✅ |
| 1.4 | **L4.5** | `ENABLE_L45=1` в `exocortex-dev.env` | ✅ |
| 1.5 | Документация | `ROADMAP_FROM_SYSTEM.ru.md`, аудит | ✅ |

**Тесты:** `pytest tests/test_sprint1_integrity.py -q --no-cov`

**API:** `POST /memory/consolidate` · дедуп: повторный `POST /facts` с тем же текстом → `deduplicated: true`

---

## Спринт 2 — один месяц

Цель: **мотивация и режимы ответа** (v2 + v4 из docx).

| # | Тема из `system` | Что сделать | Новые модули (предложение) | Результат | |
|---|------------------|-------------|----------------------------|-----------|---|
| 2.1 | **Goal Stack** | CRUD целей пользователя; привязка к query | `core/goal_stack.py` | Память «знает цель» | ✅ |
| 2.2 | **Gap Detector** (v4) | Сравнение Goal Stack с фактами памяти | `core/gap_detector.py` | Проактивные подсказки «чего не хватает» | ✅ |
| 2.3 | **ModeRouter** + 3 линзы | PERSONAL / VELANTRIM / UMWELT (упрощённый MVP) | `core/router/` | Один API — разный тон/политика ответа | ✅ |
| 2.4 | **API gaps & goals** | `GET /goals`, `GET /gaps`, `POST /goals` | `server.py`, OpenAPI | Видимость в UI/агенте | ✅ |
| 2.5 | **Graphiti ingest** (опц.) | `graphiti_adapter`, `POST /causal/reload-from-graph`, `import_snapshots` | `core/graphiti_adapter.py`, `causal_persistence.py` | Enterprise L3 | 🟡 |
| 2.6 | **Telegram → L0** | L0 raw + L1 fact; webhook + polling | `app/telegram_ingest.py`, `app/telegram_bot.py` | Вход как в эксперименте | ✅ |

**Зависимости:** 2.2 требует Kuzu 🟢; 2.3 можно без полного Umwelt (6 агентов → фаза 3).

**Критерий:** агент получает `gaps[]` в ответе query; router переключает `mode` в JSON.

---

## Спринт 3 — квартал (подготовка V10)

Цель: мост **dict/SQLite → CognitiveFact** без big-bang.

| # | Тема | Что сделать | Ссылка | |
|---|------|-------------|--------|---|
| 3.1 | **CognitiveFact dataclass** | v9.1: класс + маппер dict↔store | `core/cognitive_fact.py`, `GET /facts/{id}/cognitive` | ✅ |
| 3.2 | **CognitiveFactStore** | v9.2–9.3: save/get/list/transition | `core/cognitive_store.py`, `/cognitive/facts` | ✅ |
| 3.3 | **Relations в факте** | v9.7: `relations[]` preview + CausalGraph | `load_relations_for_fact`, `GET /facts/{id}/relations` | ✅ |
| 3.4 | **Umwelt MVP** | engineer, scientist, sparrow; seed + layer 99 | `umwelt_store`, `umwelt_mvp_seed.json`, API `/umwelt/*` | ✅ |
| 3.5 | **Innenwelt MVP** | Goals + welfare on + somatic tags в metadata | `goal_stack`, `gap_detector`, `interoception`, API | ✅ |
| 3.6 | **Domain tags** (v4) | `metadata.domain` + filter в retrieval/query | `core/domain_tags.py` | ✅ |

---

## Горизонт V10+ (из `system` + `VISION_V10_DRAFT`)

| # | Идея | Статус в V8.6 | Когда | |
|---|------|---------------|-------|---|
| V1 | **Unified Cognitive Runtime** (один EventBus, один store) | `cognitive_runtime`, `GET /runtime/status`, fact_*→retriever | V10 MVP | 🟡 |
| V2 | **Полный Umwelt** (6 агентов, affordances) | `poly_welt_registry`, seed 10 perceptions, `GET /umwelt/agents` | V10+ | 🟡 |
| V3 | **CrossDomainLayer** + DomainOrchestrator | smart route, LLM plan, CausalGraph `analogous_to` | `cross_domain.py` | 🟡 |
| V4 | **MHI Phase 2** (topology/ML) | Phase 1 в `/health` | Horizons E2 | 💤 |
| V5 | **NLI Truth Gate** | `NotImplementedError` | Horizons R2 | 💤 |
| V6 | **velantrim_graph.py** как в эксперименте | Портировано в `storage_facade` | Закрыто Kuzu | 🟢 |

---

## Матрица приоритетов (только 🚀 из аудита `system`)

| Приоритет | Элемент | Спринт | Усилие | Импакт на продукт |
|-----------|---------|--------|--------|-------------------|
| P0 | Kuzu + факты + MHI HEALTHY | 0 | S | Стабильная демо-память |
| P1 | ConsolidationEngine + checksum | 1 | M | Доверие к памяти, аудит |
| P2 | Goal Stack + Gap Detector | 2 | M | «Умный» агент, отличие от RAG |
| P3 | ModeRouter (3 линзы) | 2 | M–L | UX персонализация |
| P4 | CognitiveFact v9.x | 3 | L | Техдолг, скорость фич |
| P5 | Umwelt / Domains v4 | 3–V10 | XL | Research-уровень |

---

## Что **не** переносить в ближайшие спринты

| Элемент | Почему | Эмоция |
|---------|--------|--------|
| Полный Neo4j без необходимости | Kuzu уже закрывает L3 локально | 🟢 |
| 6 агентов Umwelt сразу | Сложность политик и тестов | ⚠️ |
| CrossDomain science↔engineering | Нужны domain tags + orchestrator | 💤 |
| Переписать всё на Graphiti fork | Два канона — путаница; только адаптер | ⚠️ |

---

## Связанные документы

| Документ | Роль |
|----------|------|
| [AUDIT_V8_6.ru.md](AUDIT_V8_6.ru.md) | Текущее состояние кода |
| [VISION_V10_DRAFT.md](VISION_V10_DRAFT.md) | Куда идём (CognitiveFact) |
| [KUZU_SETUP.ru.md](KUZU_SETUP.ru.md) | L3 Kuzu |
| [HORIZONS.md](HORIZONS.md) | Research / experimental |
| `C:\Users\VELAN\Documents\system\*.docx` | Исходные спеки v2/v4 |

---

*При выполнении спринта обновляйте статус в `CHANGELOG.md` и чеклист в [AUDIT_V8_6.ru.md](AUDIT_V8_6.ru.md) §14.*
