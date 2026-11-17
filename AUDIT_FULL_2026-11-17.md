# Аудит репозитория Velantrim Exo-Cortex-Titan

- **Дата:** 2026-11-17
- **Объект:** `main` @ `485c4b0` (merge PR #515). PR #523 (`fe992ae`) и PR #524 (`4750c89`) проверены отдельно как ветки, не слиты.
- **Режим:** только чтение. Ничего не закоммичено, не запушено, в `main` не влито, PR не комментировался. Этот файл лежит в рабочей копии как неотслеживаемый.
- **Размер кода:** 831 `.py`-файл, ~262 тыс. строк, 356 модулей в `core/`, 383 файла в `tests/`.

## 0. Как проводился аудит и что не проверено

| Метод | Что сделано |
|---|---|
| Статанализ | bandit (137 тыс. LOC), vulture, ruff (F, B, S, BLE, ARG, C901, PLW), radon (цикломатическая сложность), pip-audit по `uv.lock` со всеми extras (~120 пакетов) |
| Поиск секретов | regex по форматам токенов (OpenAI, GitHub, AWS, Slack, Telegram, PEM) по всему дереву и по именам файлов |
| Ручной разбор | четыре независимых прохода: ядро памяти/истины; сетевая поверхность (server, api, app, MCP, парсеры файлов); инфраструктура (Docker, CI, зависимости, лицензии, миграции, static); мёртвый код, дубли, дрейф документации, покрытие тестами |
| Проверка утверждений ChatGPT | прочитан код обеих PR-веток, пара утверждений воспроизведена |

**Ограничения (важно для оценки достоверности):**

- Тесты репозитория **не запускались** (4969 тестов автора #523 и 71 тест #524 мной не воспроизведены).
- `fastapi` и `sentence-transformers` в контейнере не установлены. HTTP-слой проверялся чтением кода, плотные ретриверы не запускались.
- Часть находок ядра памяти (помечены **POC**) исполнитель воспроизвёл скриптами на временных SQLite-БД. Я лично перечитал по коду ключевые места (в отчёте отмечено «перечитано»), но сами POC не перезапускал.
- Находки без пометки POC подтверждены только чтением кода.

**Сводка по критичности:** P0 (критично) — **0**. Остальное по областям — в разделах ниже.

---

## 1. Проверка отчёта ChatGPT (PR #523, #524)

Все утверждения ChatGPT, которые я проверял, подтвердились по коду. Ниже — статус и уточнения.

| # | Утверждение ChatGPT | Статус | Доказательство |
|---|---|---|---|
| C1 | #523: смешанный batch сохраняется частично, ошибка классификатора отклоняет только свой факт | **Подтверждено** | `pr523:core/memory.py` ~4268–4275: `ValueError(classification_error)`, ~4420: `except Exception` → `stats["errors"] += 1` и `continue`; допущенные записи идут в общую транзакцию. Тесты (`test_admission_classification_fail_closed.py`, `test_audit_evidence_integrity.py`) подают в batch **один** элемент или только валидные, смешанного сценария нет |
| C2 | #523: `supersede()` обходит `resolve_admission_types()` | **Подтверждено** | `pr523:core/truth_maintenance.py` ~204–228: `except Exception: _ct = normalize_claim_type(...)`; ветка с явным `claim_type` не классифицирует `origin_type`; затем вызывается `admit_fact`, но не `resolve_admission_types`. Дополнительно в этой ветке мёртвый тернар с одинаковыми ветками |
| C3 | MCP `store_fact` отдаёт `inserted:false` как успех | **Подтверждено** | `core/tool_handlers.py:171-179` (одинаково на `main`) |
| C4 | Telegram ingest игнорирует результат записи, отвечает `ok: true` | **Подтверждено** | `app/telegram_ingest.py:109-118` и `:73-90`; webhook отвечает «✅ Память: …» (`server.py:~3977`) |
| C5 | `reinforce()` не проверяет результат `store_fact`, пишет `fact_reinforced` | **Подтверждено и усилено** | см. P1-A5: `reinforce()` для не-`Observed` факта вообще падает с `ValueError` в `store_fact`, а провенанс-запись обёрнута в `except Exception: pass` |
| C6 | #524: `1e999` проходит парсер как `inf`, `JSONResponse` падает с `ValueError` (HTTP 500) | **Воспроизведено** | `json.loads('{"id":1e999}', parse_constant=…)` → `inf`; `JSONResponse(...)` → `ValueError: Out of range float values are not JSON compliant`. В `pr524:api/mcp_gateway.py` нет `parse_float`/`isfinite`; тестов на `1e999` нет |
| C7 | #524: гонка идемпотентности между сессиями | **Подтверждено статически** | Блокировка побочных эффектов привязана к `session:<sid>` (`mcp_transport.py` ~324–335), ключ кэша — `(caller, tool, key)` (~473–504). Последовательность «get → `tool.fn()` → put» без резервирования in-flight записи. Разные сессии одного вызывающего с одним ключом оба получают MISS |
| C8 | #524: исходная находка A05 (CORS и `Idempotency-Key`) не закрыта | **Не проверял** | `server.py` в #524 не менялся (в diff его нет) |
| C9 | Совместимость двух PR: общие файлы `CURRENT_STATE.md`, `KNOWN_RISKS.md`, `WORK_LOG.md` | **Подтверждено** | оба PR меняют `docs/ai/{CURRENT_STATE,KNOWN_RISKS,WORK_LOG}.md`; код (`core/*.py`, `api/*.py`) не пересекается. Файлы PR: #523 — 12, #524 — 8 |

**Дополнения к выводам ChatGPT (не были в его отчёте):**

1. **#524 кэширует и ошибочные результаты.** В `_execute_tools_call` вызов `self._idempotency.put(...)` выполняется после всех веток `except`, значит `isError:true` тоже попадает в кэш. Повтор с тем же `Idempotency-Key` после временного сбоя вернёт старую ошибку и не выполнит операцию (P2).
2. **Вынос в `run_in_threadpool` в #524 делает блокировку осмысленной.** На `main` обработчик синхронный внутри `async def`, и `threading.RLock` ничего не сериализует. После #524 гонка из C7 становится достижимой — вывод ChatGPT верный.
3. **Ограничение `1e999` шире, чем `id`.** Любое число в `params`, которое потом попадёт в ответ, даст ту же проблему. Достаточно проверять `math.isfinite` на всех float после разбора или передать `parse_float`.
4. **На `main` исправлений #523 вообще нет** (`resolve_admission_types` не встречается в `core/`). Значит, все перечисленные выше проблемы классификации присутствуют на `main` целиком, а не только в обходных путях.

**Минимум для #523:** закрыть `supersede()` через общий `resolve_admission_types()`; явно выбрать контракт batch (атомарный all-or-nothing или честный partial-result с перечислением id) и покрыть его тестом со смешанным batch; перевести MCP/Telegram/`reinforce` на `store_fact_result` и обработку статуса.
**Минимум для #524:** проверка конечности чисел + HTTP-тест на `±1e999`; сериализация «проверка кэша → выполнение → публикация» по ключу идемпотентности (а не глобальный lock); не кэшировать `isError`.

---

## 2. Находки: ядро памяти и истины

Файлы: `core/memory.py`, `truth_maintenance.py`, `truth_gate.py`, `write_gate.py`, `pipeline.py`, `causal_graph.py`, `erasure_coordinator.py`, `hybrid_retriever.py`, `audit_chain.py`.

**SQL-инъекции не найдено.** Все 56+ срабатываний bandit B608 — f-строки только с константами (списки плейсхолдеров, фиксированные имена таблиц/колонок), значения пользователя всегда параметризованы. Это ложные срабатывания.

### P1

| ID | Где | Проблема | Предложение |
|---|---|---|---|
| **M-1** | `core/memory.py:1675-1677`, `:4267-4269`, `:1804-1815`, `:4371` | `store_fact` и `store_facts_batch` не проверяют Ring Zero (I6): `VALUES_CORE`/`RING_ZERO` можно создать сразу `Validated`, а upsert с другим claim переводит существующий в `Contradicted`. `transition_esm`, `validate_and_promote`, `supersede` такие id отклоняют (`:3104`, `:3852`), а upsert-пути нет. **POC.** Достижимо через `POST /facts` (`fact_id` задаётся клиентом) и MCP `store_fact`. Перечитано: `IMMUTABLE_FACT_IDS` проверяется на 1066/3104/3852, а на путях записи — только условие «сидера» (1675/4267) | Общая предпроверка `fact_id in IMMUTABLE_FACT_IDS` для обоих путей; тест на upsert Ring Zero с другим claim |
| **M-2** | `core/memory.py:1805`, ON CONFLICT `:1994-2005`, batch `:4503` | Upsert поверх `Validated`/`Supported` молча перезаписывает confidence, source, `claim_type`, `origin_type` и весь `metadata` (включая `evidence_refs`), контрольная сумма пересчитывается, так что порча не видна. **POC:** факт с confidence 0.95 и 2 evidence после upsert стал 0.01, `source="unknown"`, без evidence, остался `Validated` | Для строк в `Supported/Validated/ImmutableCore` отклонять или автоматически понижать при смене этих полей; повторный прогон гейта |
| **M-3** | `core/pipeline.py:243`, `core/causal_graph.py:192,200-207,488-512` | Синглтон `CausalGraph` держит одно SQLite-соединение с `check_same_thread=True` и без блокировки. **POC:** `add_relation` из другого потока даёт `ProgrammingError`. Сервер работает через `asyncio.to_thread`, так что поведение зависит от того, каким потоком создан синглтон. Ошибки глотаются: `truth_maintenance.contradict` (`:408-409`, `pass`) возвращает `False` без ребра, `pipeline._extract_conflicts` (`:383`) молча теряет «contradiction-first» конфликты, `close()` при смене БД (`:237`, `:342`) подавлен и соединение течёт. Фабрика `_get_causal_graph` — незащищённый check-then-create | Соединение на поток либо `check_same_thread=False` + `RLock` внутри `CausalGraph`; блокировка на фабрике |
| **M-4** | `core/memory.py:1376`, upsert `:1994-2000`, batch `:4503,4531` | Флаг `restricted` (GDPR Art. 18) хранится в `metadata`, а upsert заменяет колонку целиком. **POC:** после `set_restricted(True)` повторная запись того же `fact_id` (одиночная и batch) возвращает факт в выдачу | Переносить защитные ключи метаданных из существующей строки или вынести в отдельную колонку; тест |

### P2

| ID | Где | Проблема | Предложение |
|---|---|---|---|
| M-5 | `core/truth_maintenance.py:71`, `:481`, `:83` | `reinforce()` и `confidence_decay()` передают в `store_fact` факт с `Supported/Validated`, а `store_fact` бросает `ValueError: новые факты создаются только в 'Observed'` (`memory.py:1679`). `confidence_decay` работает только на таких фактах, то есть никогда не срабатывает; `reinforce` работает только для `Observed`. Вызовов и тестов нет («FIX #10» не прогонялся). **POC** | Отдельный CAS-метод обновления confidence; тесты |
| M-6 | `core/truth_maintenance.py:393-394, 408-409, 418-419` | `contradict()` глотает `transition_esm`, запись ребра и реестр противоречий (`debug`/`pass`) и всё равно возвращает `changed=True`. Незакрытый пункт прежнего аудита (#23/M8) | Узкие `except`, лог `WARNING`, структурный результат |
| M-7 | `core/memory.py:1724`, `:4328`, `truth_maintenance.py:241` vs `truth_gate.py:245` | WriteGate проверяет `bool(evidence_refs)`, TruthGate — список различных непустых строк; гейты расходятся. **POC:** `evidence_refs=[""]` и `"zzz"` пропустили LLM-`WORLD_FACT` | Единый валидатор evidence |
| M-8 | `core/memory.py:1722` vs `:1739-1745`, batch `:4309-4331` | `admit_fact` выполняется до вывода `origin_type`: `WORLD_FACT` с `source="gpt-4"` без явного origin проходит как `LLM_OUTPUT`, а с явным — отклоняется. В batch второго прохода нет, поэтому origin остаётся `UNKNOWN`. **POC** | Выводить origin до гейта общим хелпером |
| M-9 | `core/memory.py:3965`, `server.py:3120` | `invalidate_edge` закрывает окна валидности, но состояние не меняет; ни один путь чтения (`get_facts_by_ids`, `FactsPackBuilder`) не фильтрует по `t_ingestion_end`/`t_event_valid_end`. «Инвалидированный» `Validated` факт попадает в ответы. CAS-промах возвращается как 404 | Фильтр окон в выдаче; 409 на CAS-промах |
| M-10 | `core/memory.py:4484-4598` (нет `upsert_fts_row`), одиночный путь `:2089` | `store_facts_batch` не обновляет FTS-индекс. **POC:** факт из batch не находится `search()`, ошибка тихая (fallback на LIKE только по исключению) | Вызывать `upsert_fts_row` внутри batch-транзакции |
| M-11 | `core/pipeline.py:137-161` | `_get_hybrid_retriever` возвращает глобал `_HYBRID_RETRIEVER` после снятия контроля, а не локально собранный: параллельный запрос с другим корпусом может подменить его. `_HYBRID_DIRTY=False` ставится после сборки (теряется `mark_retriever_dirty()` во время сборки). Ключ кэша — набор id кандидатов, поэтому корпус BM25 пересобирается почти на каждый запрос (аудит #18 исправлен частично) | Возвращать локальную ссылку; lock или счётчик поколения; ключ по версии хранилища |
| M-12 | `core/memory.py:154-166`, `core/forgetting.py:742-750`, `core/contradiction_registry.py:178-205` | Erasure завершается, а производные персональные данные остаются: `provenance_chains` не входит в `_SAME_DB_DEPENDENT_TABLES`, туда пишется `user_id` субъекта (append-only, никогда не чистится); реестр противоречий хранит `claim_a/claim_b`; `DenseRetriever._VECTOR_CACHE` держит эмбеддинги; `l0_raw_memory` хранит полный текст (задокументировано как `RESIDUAL_IMMUTABLE_DATA`, смягчения нет) | Добавить таблицу и реестр в purge и проверку остатков; не писать `user_id` в провенанс; план редактирования сырого текста |
| M-13 | `core/memory.py:2112-2123` и вызовы | Устаревший bool-API `store_fact()` возвращает `False` и для отказа гейта, и для NOOP, и для UPDATE. Вызывающие, ошибочно трактующие результат: `tool_handlers.py:153,174`, `umwelt_store.py:317` (`created += 1` всегда), `app/telegram_ingest.py:109`, `reconsolidation.py:208`, `world_skills_ingest.py:547`, `truth_maintenance.py:71,481`. `store_facts_batch` возвращает только счётчики | Перейти на `store_fact_result`; batch должен возвращать результат по каждому id |
| M-14 | `core/pipeline.py:1368, 1377, 1283, 901` | `response_guardian` и `output_faithfulness` обёрнуты в `except Exception: logger.debug(...)`: при сбое ответ уходит без защиты. `run()` вызывает `build_facts_pack(require_policy=False)`; при ошибке `FactsPackBuilder` откат на сырые факты включая `Contradicted/Collapsed/Deprecated` | Fail-closed или пометка ответа; `WARNING` |
| M-15 | `core/audit_chain.py:60`, `verify_chain`/`list_chain_ids` | Цепочки аудита пишутся, но `verify_chain` в проде никто не вызывает (только тесты); проверка ограничена `MAX_VERIFY_ROWS` | Периодическая/стартовая верификация и health-сигнал |
| M-16 | `core/truth_gate.py:231-245`, `core/memory.py:3839-3856` | TruthGate слабее заявленного: evidence — любые различные строки из метаданных вызывающего (**POC:** PRECISION проходит с `["a","b","c","d","e"]`), confidence самоопределяемый; стадия противоречий по умолчанию `"none"`, поэтому `Validated` достижим при наличии `Contradicted` соседей, а вердикт печатает «contradictions=0». Неизвестный `mode` (например `"PRECISON"`) тихо становится `BALANCED` (**POC**) | Исключение на неизвестный режим; правдивое обоснование; графовая проверка противоречий |
| M-17 | `core/app.py:144` | `app.store` — отдельный `SQLiteGraphStore` на той же БД со своим L0-кэшем (128 записей, без TTL и инвалидации между экземплярами) и своим `_db_lock`. **POC:** после перевода факта в `Contradicted` одним хранилищем другое отдаёт старое состояние | Использовать общий `_GLOBAL_STORE` или durable-проверку версии при чтении |

### P3

| ID | Где | Проблема | Предложение |
|---|---|---|---|
| M-18 | `core/memory.py:1695-1805`, `:2735-2760` | Чтение `existing` и drift-логика вне транзакции, затем безусловный upsert; `update_state` пересобирает весь `metadata` из L0 под CAS только по `epistemic_state` — параллельное изменение метаданных теряется | Условие по версии в UPDATE |
| M-19 | `core/memory.py:2421`, `:2944`, `server.py:2901` | `store_raw_text` и `refresh_fact_integrity_metadata` без `ensure_writes_allowed()`; сырой текст пишется до `store_fact_result`, поэтому отказ (503) оставляет сирот в L0 | Гейт SAFE_MODE; порядок записи |
| M-20 | `core/causal_graph.py:776-805`, `:949-966` | `causal_chain` перебирает все простые пути до `max_depth` без лимитов (экспоненциально на плотных графах; `max_depth` из MCP не ограничен); `find_contradictions` рекурсивен по `implies` без глубины | Лимиты результатов и узлов; итерация |
| M-21 | `memory.py:1696-1745`, `:4279-4313`, `truth_maintenance.py:204-228` | Блок классификации claim/origin скопирован трижды с расхождением поведения. Радон: `_store_fact_outcome` F(55) 473 строки, `store_facts_batch` F(50) 392 строки, `_db` E(35), `pipeline.run` F(42), `build_facts_pack` E(36) | Общий admission-резолвер; декомпозиция |
| M-22 | `core/memory.py:445-835` | `_db()` — RLock-контекст, закрывающий соединение в `finally`: вложенный `with self._db()` в одном потоке молча коммитит внешнюю транзакцию (в `invalidate_edge` `:4055-4059` на это уже наткнулись). Текущих вложенных использований не найдено. Тихие `except` вокруг DDL-backfill (`:764`), закрытия (`:785`, `:815`), прогрева `VersionStore`, FTS-fallback `search()` (`:4131`) | Защита от вложения; логирование на `WARNING` |
| M-23 | `core/hybrid_retriever.py:632, 631, 396-413, 370, 220, 330-342, 643, 704` | `retrieve_5stage` оставляет `final_score=0.0`, поиск `rrf_score` O(n²); нормализация min-max в RRF мёртвая; у `DenseRetriever.retrieve` нет порога схожести (не запускалось); класс-флаг `_AVAILABLE` отключает dense для всех экземпляров после одного сбоя | Исправить; тесты |
| M-24 | `core/pipeline.py:476`, `:607-619`, `:662,708,775` | `_NGRAM_INDEX = NGramIndex()` игнорирует `set_global_ngram` (совпадает только при `VELANTRIM_NGRAM_DB`); fallback ограничен 1000 последних фактов; строки выдачи захардкожены `Observed` | Единая регистрация индекса |
| M-25 | `core/erasure_coordinator.py:213-214, 1331-1341` | `erasure_log.claim_hash` — несоленый SHA-256 claim, хранится вечно: низкоэнтропийные claim подбираются по словарю | HMAC с ключом развёртывания или отказ от хеша |

**Исправлено относительно прежних аудитов (подтверждено исполнителем):** #2 (матрица ESM), #3 (синхронизация состояния в batch), #14 (supersede с TruthGate, I68, атомарный CAS), #19 (CAS в `update_state`), #8/#22 (`import_snapshots`), H3 (восстановление erasure при старте, `server.py:531`).
**Не исправлено:** #23/M8 (M-6), #18 частично (M-11), пункт Low про `causal_chain` (M-20).

---

## 3. Находки: сетевая поверхность

Файлы: `server.py`, `api/`, `app/`, `core/mcp_transport.py`, `core/tool_handlers.py`, `core/tool_registry.py`, `server_patch/export_endpoints.py`, `core/file_parsers/`, `core/sandbox/`.

**Не найдено:** инъекций команд/SQL, pickle/yaml/eval, SSRF; незащищённых state-changing маршрутов. `core/sandbox/` — только план, процессы не запускает. Guard-ы traversal/zip-bomb для zip/tar/rar устроены корректно (7z отключён).

### P1

| ID | Где | Проблема | Предложение |
|---|---|---|---|
| **N-1** | `app/telegram_bot.py:50,76,71` | `r.raise_for_status()` даёт `httpx.HTTPStatusError`, в тексте которого полный URL `https://api.telegram.org/bot<TOKEN>/getUpdates`; `logger.warning("poll error: %s", exc)` пишет токен бота в лог при любом 401/409/5xx каждые 3 с. Кроме того, `❌ Ошибка ingest: {exc}` отправляется пользователю в Telegram. Перечитано | Логировать тип исключения и статус; редактировать токен; не эхо-ить `exc` |
| **N-2** | `server.py:3205-3257` (`ingest_text`), `scripts/ingest_file.py` | Сбой возвращается как HTTP 200 `{"stored":0,"errors":[str(exc)]}` (`WritesBlockedError` в SAFE_MODE), тогда как `POST /facts` отдаёт 503/422. `stored_ids = batch[:real_stored]` предполагает, что успешны первые N фактов, при отклонении в середине список неверный. `ingest_file.py` смотрит только статус HTTP. Перечитано | 4xx/5xx или 207 при ошибках; результат по каждому факту; не класть `str(exc)` в тело |
| **N-3** | `server.py:2846-2873` (`POST /cognitive/facts`) | Маршрут объявлен `201`, использует bool-`save()`, при отказе гейта/бюджета возвращает 201 с несохранённым кандидатом (`cf.to_dict()`); `ValueError` из `create_observed` не мапится в 400. Это тот же дефект, что PR-C1 исправил в `POST /facts`. Перечитано | `save_result()` + маппинг `WriteStatus` в HTTP-коды |
| **N-4** | `core/tool_handlers.py:128-176` | MCP `store_fact` и `propose_hypothesis` используют bool-API; `propose_hypothesis` делает `transition_esm` для несозданного факта и сообщает `epistemic_state:"Observed"` для несуществующего `hyp.*` | `store_fact_result`, `isError` при отказе, код причины |
| **N-5** | `app/telegram_ingest.py:73-90, 109-118`, `server.py:~3977` | Результат записи игнорируется в обоих путях; webhook отвечает «✅ Память» для несуществующего факта | `store_fact_result`, ошибка при не-accepted |
| **N-6** | `api/mcp_gateway.py:92-105,170,184` (на `main`) | `async def mcp_post` вызывает синхронный `tool.fn` прямо в event loop (SQLite, retrieval, граф, erasure-саги): один медленный вызов замораживает всё приложение, включая `/health`. Блокировки `RLock` при этом бесполезны | `asyncio.to_thread`. **Закрывается PR #524**, но см. гонку C7 |

### P2

| ID | Где | Проблема | Предложение |
|---|---|---|---|
| N-7 | `server.py:712, 3953`, `api/web_console.py:79` | `hmac.compare_digest(str, str)` бросает `TypeError` на не-ASCII (заголовки декодируются как latin-1): `X-Api-Key: é` даёт 500 вместо 401; не-ASCII настроенный ключ ломает все авторизованные вызовы | Сравнивать `.encode("utf-8")` |
| N-8 | `server.py:1360-1365, 3180-3187` | `IngestRequest.text` без `max_length`, нет лимита тела; цикл чанкинга пересчитывает `len(" ".join(...))` на каждом слове (O(n·chunk)) прямо в async-обработчике | Лимит, счётчик длины, вне event loop |
| N-9 | `server.py:1297-1303, 995-1006`, `api/llm_routes.py:62` | Неограниченные поля: `FactCreate.claim/source/fact_id/metadata`, `ChatRequest.chat_history/block_memory`, `SttTranscribeBody.audio_base64`, `ExportFactsRequest.facts`, `XaiExplainBody.fact_ids`, `EtirActivateBody.seeds` | `max_length`/`max_items`, глобальный лимит тела (в #524 есть только для `/mcp`) |
| N-10 | `core/mcp_transport.py:504-523` | Ошибочные результаты тоже кэшируются по `Idempotency-Key` (повтор после сбоя отдаёт старую ошибку). **Сохраняется в #524** | Кэшировать только `isError == False` |
| N-11 | `core/mcp_transport.py:208-216, 249-292`, `api/mcp_gateway.py:231` | Сессии MCP без TTL/лимита; блокировки по client-chosen `Mcp-Session-Id` не удаляются; `DELETE /mcp` позволяет любому держателю ключа удалить любую сессию. **В основном закрывается #524** (TTL/LRU), привязка сессии к учётным данным — нет | Привязка к fingerprint |
| N-12 | `api/mcp_gateway.py:83-87,175-181`, `mcp_transport.py:333,385` | `UnicodeDecodeError` не ловится (500), batch без лимитов, не-dict `params` — 500 вместо -32602. **Частично закрывается #524** (лимиты размера/batch/глубины) | Валидация типов |
| N-13 | `core/tool_handlers.py:200-224`, `core/tool_registry.py:432-452`, `server.py:3408-3436` | `validate_fact(by=)`, `contradict_fact(by=)`, `forget_fact(actor=, subject_user_id=)` принимают актора из клиентского JSON и пишут его в аудит/erasure — подделка аудита. `forget_all` корректно использует `needs_principal`; edge approve/reject (`by=body.by`) — нет | `needs_principal=True`, убрать `by/actor` из схемы |
| N-14 | `core/tool_handlers.py:171-179`, `core/memory.py:~1696-1730` | MCP `store_fact` и `POST /facts` передают произвольный dict: WriteGate решает по клиентским `evidence_refs`, `claim_type`, `origin_type`; `memory_type`, `derived_from` проходят напрямую | Белый список полей |
| N-15 | `server.py:2574-2575, 1715, 1983, 2186` | `/query` возвращает 200 с `"[LLM error: {exc}]"`, `/chat` кладёт `str(exc)` в ответ (в тексте провайдеров бывают фрагменты ключей); локальные `HTTPException(detail=str(exc))`. Прежний M9 исправлен частично | Фиксированное сообщение + correlation id |
| N-16 | `api/server_middleware.py:309,326`, `core/rate_limit.py:23,43` | Rate limit выключен по умолчанию; ключ — `request.client.host` (за прокси один бакет), `_buckets` без эвикции, проверка до авторизации, 429 без CORS/security-заголовков. Остаётся с прежнего аудита | `--proxy-headers`, TTL, отдельный лимит на неудачную авторизацию |
| N-17 | `server.py:3925-3979`, `app/telegram_ingest.py:56-58` | Webhook-секрет подтверждает источник, но нет allowlist чатов/пользователей: любой, нашедший бота, пишет факты с confidence 0.75 (то же в polling-боте). `fact_id = tg_{chat}_{message_id}` с check-then-act: redelivery и `edited_message` дают дубли | `TELEGRAM_ALLOWED_CHAT_IDS`, дедуп по `update_id` с уникальным ограничением |
| N-18 | `server.py:4527-4530, 3222-3226, 3607-3665`, `api/exocortex_api.py`, `server_patch/export_endpoints.py:171,201,239,294` | Синхронные операции в `async def`: `_ngram.rebuild/index`, `/etir/activate`, `/focus`, `/audit/recent`, `/immutable/snapshots`, `/layers/status`, все `/export/*` (генерация PDF/DOCX) | `asyncio.to_thread` |
| N-19 | `server.py:2710-2722, 2815-2834, 4450-4470` | `GET /facts`, `/cognitive/facts` грузят всю таблицу и режут в Python; `limit/offset` не валидируются (отрицательный `offset` режет с конца); health-проба консоли вызывает `/facts` | LIMIT/OFFSET в SQL, `Query(ge=, le=)` |
| N-20 | `api/web_console.py:366-371`, `api/llm_routes.py:182-192`, `server.py:1541, 3295-3335` | Неавторизованные маршруты раскрывают развёртывание: `/debug/console` (абсолютные пути, режим auth, `allow_open`), `/debug/llm-catalog`, `/layers/status`, `/compute-profile`, `/setup/llm` | `require_api_key` или отключить в проде |

### P3

| ID | Где | Проблема |
|---|---|---|
| N-21 | `core/file_parsers/archive_parser.py:105-133,205,241`, `file_ingester.py:183,211-215,283-305`, `video_parser.py:152-190` | Глубина архива хранится изменением общего `registry._initialized["archive"]` вне `try/finally`: при `workers>1` потоки видят чужую глубину, защита `MAX_DEPTH` может быть обойдена; `_stats` без блокировки; `getmembers()` читает все заголовки до `MAX_FILES`; лимит 1 ГБ на архив суммируется по вложенности; `ingest_directory` следует symlink; ffmpeg без `-protocol_whitelist`/`-nostdin` (hardening) |
| N-22 | `server_patch/export_endpoints.py:72,85,114-123,136-152,278,312` | `require_api_key=None` по умолчанию (fail-open); клиентский `format` попадает в суффикс временного файла; утечка temp-файла при исключении экспортёра; текст `ImportError` в `detail` |
| N-23 | `docker-compose.dev.yml:24`, `server.py:51-92` | Публичный ключ по умолчанию; нет минимальной длины/силы `VELANTRIM_API_KEY` |
| N-24 | `server.py:3680-3740, 4028-4048` | `/graph/analyze`, `/graph/path`, `/goals`: неограниченные `top_k`, `max_nodes`, `cutoff`, `limit`; `all_simple_paths(cutoff=N)` экспоненциален |
| N-25 | `api/mcp_gateway.py:128,200,217,227`, `server.py` (53 из 90 обработчиков), `core/tool_registry.py:271-420` | Нет docstring у всех 4 MCP-обработчиков и 53/90 маршрутов; большинство MCP-инструментов без `params`, поэтому `tools/list` отдаёт пустую `inputSchema` и нет валидации (`search_facts k`, `causal_chain max_depth`, `get_facts_for_entity limit` не ограничены); `reset_graph(confirm="false")` истинно |
| N-26 | `api/server_middleware.py`, `web_console.py:186`, `server.py:2592` | Нет `Content-Security-Policy` (75 `innerHTML` в консоли); HSTS по `request.client.host`; `/console/auth/check\|verify` — оракулы ключа без троттлинга, `verify` возвращает текст исключения; `/memory/stats` отдаёт `db_path`; `except Exception: pass` на `server.py:2592` |

---

## 4. Находки: инфраструктура, зависимости, лицензии

**Положительное:** образ Docker пинован по digest, запуск не от root (uid 10001), установка с `--require-hashes`, `docker-compose.prod.yml` усилен (read-only, `cap_drop: ALL`, `no-new-privileges`, loopback, обязательный ключ), все сторонние GitHub Actions закреплены по SHA, `pull_request_target` не выполняет код PR, в CI есть `uv audit`, покрытие ≥74%, SBOM, CodeQL, Dependabot, CODEOWNERS.
**pip-audit по `uv.lock`: известных уязвимостей нет.** **Секретов не найдено** (только плейсхолдеры и тестовые фикстуры `ghp_abcdefghijklmnopqrstuvwxyz123456` в `tests/` и `benchmarks/`).

### P2

| ID | Где | Проблема | Предложение |
|---|---|---|---|
| I-1 | `scripts/apply_migrations.py:214-282` (`dry_run_on_copy`), `:418-426` | `--dry-run-copy` падает на обычной БД (`duplicate column name: claim_type`): в реальном прогоне миграция 011 пропускает уже существующие колонки (`version == 11`), в dry-run такой ветки нет. Воспроизведено исполнителем на временной БД: dry-run `False`, реальный apply успешен — ложный отрицательный результат предпроверки | Общая функция «вычистить применённый DDL»; тест на БД, созданной `SQLiteGraphStore` |
| I-2 | `scripts/apply_migrations.py:285, 488` | Миграции не атомарны: `executescript` без транзакции (только `014` содержит свой `BEGIN/COMMIT`); сбой посередине оставляет частичную схему без повышения `user_version`, повтор падает на уже применённых `ALTER` (у `009` нет логики вычистки); строчное сопоставление DDL ломается при переформатировании; down-миграций нет | `BEGIN IMMEDIATE` + `user_version` в одной транзакции; guard-ы существования колонок из Python |
| I-3 | `docker-compose.dev.yml:22,24`, `docker-compose.yml:29` | Публикация `8000:8000` на всех интерфейсах, ключ по умолчанию `dev-key-change-me` — доступ по публично известному ключу из LAN/облака. Перечитано | `127.0.0.1:8000:8000`, ключ обязателен (`:?`) |
| I-4 | `scripts/bootstrap_titan.py:106, 139-155` | `.env` с новым `VELANTRIM_API_KEY` создаётся с правами по умолчанию (обычно 0644; `configure_provider.py:82` делает `0o600` правильно); зависимости ставятся `pip install -e .[server,parsers]` в обход `uv.lock` | `0o600`; установка по lock-файлу |

### P3

| ID | Где | Проблема | Предложение |
|---|---|---|---|
| I-5 | `.github/workflows/stage9-browser-acceptance.yml:31,35`, `stage10-bounded-pilot.yml:31` | Установка без lock-файла (`pip install -e`, `playwright>=1.48,<2`), вне `sync-python-deps` | Использовать composite action |
| I-6 | `.github/workflows/ci.yml:49`, `docker.yml` | Линт только `core/` (`api/`, `utils/`, `server.py`, `app/`, `localmind/`, `scripts/` не покрыты, mypy тоже только `core/`); bandit не запускается; образ не сканируется (Trivy/Grype) | Расширить цели, добавить `bandit -ll`, скан образа |
| I-7 | `ci.yml`, `docker.yml` | Нет блока `permissions:` (остальные workflow его имеют). Перечитано для `ci.yml` | `permissions: contents: read` |
| I-8 | `.github/workflows/pages.yml:17-18` | `contents: write` на весь workflow; запись нужна только шагу деплоя | Сузить область |
| I-9 | `pyproject.toml:99` и др. | `ruff>=0.4,<0.5` (0.4.10, 2024 г.) — не получает новых правил; нижние границы далеко от протестированных: `fastapi>=0.110` (lock 0.162.0), `redis>=4.6.0` (8.1.0), `graphiti-core>=0.3.0` (0.31.2), `openai-whisper>=20231117` (20250625). Перечитано для ruff | Поднять границы; CI-job с `uv sync --resolution lowest-direct` |
| I-10 | `scripts/fill_domain_quality.py:98`, `fill_sparse_auto.py:428` | bandit B324 (MD5) — ложное срабатывание (суффикс id дубликата) | `usedforsecurity=False` |
| I-11 | `scripts/prod_volume_backup_restore.py:194-204` | Защиты членов архива (абсолютные пути, `..`, ссылки, спец-типы) корректны, но: резервный Python-путь использует `filter="data"` только при Python ≥3.12 (фильтры есть в 3.11.4+, а образ на 3.11.15 запускается без фильтра — перечитано); основной путь `tar xzf` без `--no-same-owner/--no-same-permissions` (от root восстанавливаются setuid/setgid); нет лимита распакованного размера | `hasattr(tarfile, "data_filter")`, флаги tar, лимит размера |
| I-12 | B310: `prod_volume_backup_restore.py:746`, `stage9_browser_acceptance.py:26,42`, `titan_v1_bounded_pilot.py:45`, `bootstrap_titan.py:184`, `check_pr_merge_evidence.py:247` | В основном loopback/фиксированный `api.github.com`; `prod_volume_backup_restore.py:746`, `ingest_file.py`, `titan_tools.py` принимают пользовательский base URL — допустима любая схема, ключ уйдёт на любой хост | Проверка `scheme in {"http","https"}` |
| I-13 | `scripts/_gen_batches_870_891.py` (3475 строк), `_gen_batches_867_871.py`, `_fill_sparse_batches_pt1.py`, `fill_sparse_direct.py`, `fix_kb_issues.py`, `strip_misplaced_municipal.py`, `fix_ledger_corruption.py`, `cleanup_unknown_ops.py`, `i18n_bulk*.js`, `fix_mic.js`, `_inject_de.*` и др. | Одноразовые генераторы без ссылок, правят корпус знаний на месте (валидация — `assert`). `_gen_batches_869_878.py` уже закарантинен тестом | Перенести в `docs/history/generators/*.txt` или удалить |
| I-14 | `scripts/rename_folder_to_V8.6.ps1:4,8` | Захардкожен `C:\Users\VELAN\Documents\velantrim` (имя локального пользователя); скрипт устарел | Удалить |
| I-15 | `config/exocortex-dev.env` (копируется `Dockerfile:150`), `scripts/start_kuzu_server.ps1:15` | В образе лежит `VELANTRIM_ALLOW_OPEN=true` и `dev-change-me` (активно только при `VELANTRIM_PROFILE=developer`). Перечитано | Не копировать dev-профиль в образ; без ключей по умолчанию |
| I-16 | `Dockerfile:80` | Инструменты сборки не пинованы (`pip --upgrade`, `build`, `setuptools>=83` в изолированной среде без хешей), тогда как рантайм ставится с `--require-hashes`: сборка колеса негерметична | Пины + constraints с хешами |
| I-17 | `static/console/index.html:4850, 6054-6061, 6876-6877, 8453`, `i18n-snippet.js:572`, `research-app.js:180-182` | Неэкранированные значения в `innerHTML` (`t("profile.server", {title, emoji})`, `it.emoji`, `p.title/p.id`, `e.message`, `data-id="${f.id}"`). Основной рендер чата/памяти экранируется корректно; значения приходят от собственного сервера/localStorage, поэтому эксплуатация маловероятна | `escapeHtml` на все подстановки; `textContent` |
| I-18 | `static/console/index.html:6810-6812, 6963` | Ключи LLM-провайдеров и ключ Titan хранятся в `localStorage` открытым текстом; CSP нет нигде — любой XSS (см. I-17) читает все ключи | CSP после рефакторинга inline-скриптов; описать компромисс |
| I-19 | `scripts/apply_migrations.py:35-51` | Список миграций захардкожен: новый `.sql`, не добавленный в `MIGRATIONS`, молча не применяется | Тест соответствия каталога списку |
| I-20 | `pyproject.toml:11` | Устаревшая форма `license = { file = "LICENSE" }` (PEP 639), нет SPDX и классификатора; в README нет строки о лицензии. `LICENSE` — MIT, согласован с `pyproject`. Прямые зависимости, которые исполнитель опознал, пермиссивные, но lock **не сканировался** на лицензии. **Непроверенные** риски: проприетарные NVIDIA CUDA-колёса (`torch`) в extras `embeddings/retrieval/audio`; `pymorphy3-dicts-ru` (данные OpenCorpora, предположительно CC BY-SA) входит в `server` и Docker-образ | `license = "MIT"`; строка в README; `pip-licenses` в CI; проверить условия `pymorphy3-dicts-ru` |
| I-21 | `uv.lock:548,1705` (`posthog==7.17.0` через `graphiti-core`) | `SECURITY.md` §1 заявляет «без телеметрии», а `graphiti-core` (extra `async-backend`) по имеющимся сведениям шлёт анонимную телеметрию, если не задано `GRAPHITI_TELEMETRY_ENABLED=false`; ни в compose, ни в `.env.example` переменной нет. Не проверено запуском | Задать переменную или пометить в документации |

---

## 5. Находки: мёртвый код, дубли, дрейф контрактов, документация, тесты

### Ключевые числа

| Метрика | Значение |
|---|---|
| Модулей в `core/` | 356 |
| Модулей-сирот (нет импортёров вне тестов, нет ссылок из `server.py`/`api`/`app`/`scripts`/`pyproject`/CI) | **59** (из них без тестов — 16; явно помечены «unwired/shadow/deprecated» — 18) |
| Модулей, недостижимых из любой продуктивной точки входа | 79 |
| Модулей без импортирующего их теста | 93 (около 66 вовсе не упоминаются в `tests/`, в основном подпакеты) |
| vulture (функции/классы, `core/`) | 85 (40 — нулевые ссылки, 20 — только тесты, 25 — ложные) |
| Публичных символов без docstring | **1773 из 3407 (52%)**; модулей без docstring 18/356 |
| Дубли помощников | `_canonical_json` ×19, `_digest` ×14, `_now` ×14, `_check_available` ×16, `_require_text` ×27, `_positive_int` ×11, `_unique_sorted_text` ×15 |
| Замороженных dataclass / из них с `__post_init__` | 401 / 272 |
| Локальных классов ошибок `*Error` | 102 (ни один не наследует `VelantrimError`) |
| `sqlite3.connect(` в `core/` | 112 (16 модулей без timeout/busy_timeout) |
| ruff ARG001/ARG002 | 323 / 221 по всему репозиторию (в `core/` — 45) |
| ruff C901 (сложность) | 194; radon ранг E/F — десятки функций (худшие: `StateReconciler._reconcile_group` F(57), `_store_fact_outcome` F(55), `AuthorizedContinuityObservationBatch.create` F(55), `parse_batch_markdown` F(53), `store_facts_batch` F(50)) |
| Блоки `except Exception: pass/continue` (ruff S110/S112) | 66 / 7; blind-except (BLE001) — 310 |

### Находки

| ID | Серьёзность | Где | Проблема | Предложение |
|---|---|---|---|---|
| D-1 | P2 | `core/compliance.py:33-63` | Весь модуль GDPR Art. 18/30 недостижим из продакшена (импортирует только `tests/test_compliance.py`). Читающая сторона есть (`memory.py` скрывает `metadata.restricted`), а писать флаг, кроме этого модуля, нечем; `VELANTRIM_L3_BACKEND` не документирована. Перечитано: `restrict_processing` вне тестов не вызывается | Зарегистрировать как admin-инструменты/эндпоинты или пометить «не подключено» в `docs/LIMITATIONS.md` |
| D-2 | P2 | `migrations/012_crystal_memory.sql:61-71`, `core/memory.py:~158-170`, `core/entity_resolver.py:364` | Erasure не чистит таблицу `entities` (`canonical_name`, `aliases_json`, `description`; типы включают `person`): имя сущности удалённого факта сохраняется. `delete_mentions_for_fact` вызовов не имеет. Перечитано: `entities` в `erasure_coordinator.py` не встречается. Тест проверяет только `fact_mentions` | Удалять/обезличивать сущность при стирании последнего упоминания в той же атомарной очистке; тест |
| D-3 | P2 | `core/entity_resolver.py` (419 строк), `tool_handlers.py:182` | Нет тестов; `link_entity` глотает любые исключения и возвращает `""` — сбой записи выглядит успехом | Возвращать ошибку; тесты сбоя, конкурентности, немигрированной БД |
| D-4 | P2 | `core/graph_lab_bridge.py:134-135,189`, `core/multilingual_router.py:109`, `core/causal_graph.py:865,918`, `core/velantrim_reports/mhi_report.py:38`, `truthgate_report.py:36`, `core/file_parsers/file_ingester.py:298`, `core/file_generators/*` (`theme`), `interoception.py:165`, `meaning_parser.py:93` и др. | Публичные функции принимают аргументы и молча игнорируют их. Перечитано: `get_bridge_concepts(domain_a, domain_b)` игнорирует оба, `propagate_change(fact_id, change)` игнорирует `change`. `find_analogies(cross_domain)` выставлен как аргумент MCP-инструмента (`tool_handlers.py:164-168`), поэтому клиентская настройка ни на что не влияет | Удалить параметры или реализовать; `TypeError/NotImplementedError` там, где на них могут опираться |
| D-5 | P2 | `Velantrim_Project_Map.md:70`, `docs/horizons/E2_MHI_PHASE2.md:3`, `E6_SHADOW_STATE.md:46`, `docs/strategy/01_PRODUCT_READY_VS_RESEARCH.md:24`, `docs/WORK_SUMMARY.md:17`, `docs/DATABASE_RELEASE.ru.md:104` | Документы описывают `GET /reports/mhi` как действующий (маршрута нет), «PRODUCT-READY» модуль `core/provenance.py` (файл — `provenance_chain.py`), несуществующие `utils/rfc_parser.py` и `scripts/sync_l3_ladybug.py` | Исправить пути/маршруты или пометить как план |
| D-6 | P3 | `core/tool_registry.py:212-217` | `register()` перезаписывает `_tools[name]`, но дописывает `_by_capability` без удаления прежней записи: `x` как reader, затем admin оставляет в `for_capability("reader")` admin-инструмент; двойная регистрация дублирует список. **Воспроизведено исполнителем.** Перечитано. Не эксплуатируется сейчас (`mcp_transport.py:366-396` перепроверяет `has_tool`), но латентный риск авторизации | Запретить дубли или перестраивать индекс; тест |
| D-7 | P3 | 59 модулей-сирот | Крупные: `velum_persistence.py` (380), `text_utils.py` (408, совпадает по имени с живым `utils/text_utils.py`), `types.py` (280), `trusted_retrieval.py`, `curiosity_engine.py`, `meaning_parser.py`, `multi_index_retriever.py`, `evidence_pack.py`, `reasoning_bank.py`, `negative_reinforcement.py`, `working_memory.py`, `query_expander.py`, `fact_decayer.py`, `adaptive_truth.py`, `conversation_buffer.py`, `backends/kuzu_graph.py`; с тестами, но без продакшн-вызовов: `fractal_memory.py` (582), `forgetting.py` (776), `projection_dispatcher.py` (706), `relations.py` (597) и др. `errors.py`: иерархия `VelantrimError` используется только тестом, `MemoryError` затеняет встроенное; `erasure.py` — устаревший shim без вызовов | Удалить или перенести в `experimental/`; CI-проверка маркера «unwired» |
| D-8 | P3 | 19 копий `_canonical_json` (9 различных тел) | 13 копий с `allow_nan=False`, 6 без: `rapid_orientation.py:124`, `reader_core_contracts.py:95`, `context_pack.py:101`, `knowledge_capsule.py:464`, `continuity/thread_weaver.py:88`, `continuity/conversation_bridge.py:94` — молча хешируют NaN/Infinity, тогда как `continuity/contracts.py:133` отклоняет; дайджесты для одного класса данных различаются. Также `_digest`/`_stable_digest` (~18), `_canonical_datetime` ×4, `_sha256(value, field)` ×5, `_utc` ×3, `_check_available` ×16 (`file_parsers`/`file_generators`), `_now` ×14 | Один `core/_canon.py` и `file_parsers/_compat.py` |
| D-9 | P3 | `core/sandbox/contracts.py:60`, `core/critical_exceptions.py:613`, `core/code_structural_memory/contracts.py:23` и др. | Повторяющиеся валидаторы frozen-dataclass (`_require_text` ×27, `_positive_int` ×11, `_unique_sorted_text` ×15 и т. д.) различаются только классом исключения | Общий модуль валидаторов с параметризацией |
| D-10 | P3 | `core/provenance_chain.py:131-190`, `core/audit_chain.py:676-700, 1421-1432`, `core/memory.py:3014` | Три разных стиля retry: `provenance_chain` повторяет только на «database is locked», `audit_chain` — на любой `OperationalError` с паузами 10–50 мс (прячет ошибки схемы за 5 попытками); 112 прямых `sqlite3.connect`, 16 модулей без `busy_timeout` (`ngram_index.py` — 8 вызовов, участвует в erasure, `umwelt_store.py` — 6, `sleep_time_worker.py` — 6, `goal_stack.py` — 5) | Единые `connect()` и `retry_on_locked()` |
| D-11 | P3 | `core/file_parsers/archive_parser.py:200-266`, `tests/test_smoke.py:230-286` | Traversal и `max_files_reached` для zip/tar не проверяются тестами (RAR — да); `test_rar_uses_the_same_traversal_check_as_zip` — инспекция исходника; 18 утверждений на `inspect.getsource` в 10 тестовых файлах (например, `test_smoke.py:273-286` проверяет наличие строки «threading.Lock» вместо конкурентности) | Реальные тесты на traversal, symlink, переполнение числа файлов; блокировка `_stats` |
| D-12 | P3 | `core/graph_ring_zero.py:49`, `core/tool_registry.py:516`, `tool_handlers.py:305`, `core/mcp_transport.py` | `graph_ring_zero` без тестов; успешный путь `reset_graph(confirm=True)` не тестируется; нет тестов на hardlink-член архива, повреждённый/усечённый архив, горячий backup при параллельной записи; конкурентность `mcp_transport` — один файл. Erasure (48 файлов тестов), audit chain (14) и auth/clamp MCP покрыты хорошо | Добавить тесты |
| D-13 | P3 | 20 переменных окружения: `GRAPHITI_NEO4J_URI/USER/PASSWORD` (`graphiti_adapter.py:44-46`), `TRUTH_GATE_MODE`, `KNOWLEDGE_GROUP_ID` (`feature_config.py:194,210`), `VELANTRIM_ARCHIVE_AGE`, `VELANTRIM_CORE3_*`, `VELANTRIM_{CSV_ESSENCE,DISABLE_GENERATORS,DISABLE_PARSERS,ESSENCE_SAMPLE,OCR_OSD,PDF_STRATEGY,VIDEO_OCR,WHISPER_COMPUTE_TYPE,L3_BACKEND}` | Читаются в коде, но нигде не описаны (ни в документации, ни в `.env.example`, ни в compose); обратный дрейф: `VELANTRIM_AUDIT_CHAIN_C4` задокументирован как флаг отката, но код его не читает | Описать/удалить |
| D-14 | P3 | `.github/workflows/docker.yml:170`, `pyproject.toml:20`, `velantrim_reports/*`, `docs/INVARIANTS.md:97`, `docs/LIMITATIONS.md:86`, `docs/Velantrim_V9_Final_Audited.md:696-702` | Устаревшие комментарии/документы: «`living_context.py` импортирует `affordance_linker.py`» неверно; `TruthGateVerdict` в `core.truth_gate` не существует; `TruthGate._find_contradictions_nli()`, `emergency_invalidate_trusted()`, маршруты `/memory/audit/*` отсутствуют | Исправить |
| D-15 | P3 | `core/runtime_flags.py` (15/18), `tool_handlers.py` (13/18), `events.py` (10/10), `continuity/advisory_shadow.py` (13/13), `continuity/contracts.py` (13/14), `reader_operator_decision.py` (21/24), `reader_shadow_burn_in.py` (21/25) и др. | Нет docstring у публичного API (52% по репозиторию) | Начать с MCP-обработчиков и контрактов |

Топ-уровневые README, `CANONICAL.md`, `SYSTEM_OVERVIEW*.md` расхождений с кодом не показали; дрейф сосредоточен в старых спецификациях, стратегических документах и журналах работ. Из 634 выборочных ссылок на пути не нашлось 8, из 79 ссылок `file.py::symbol` — 2 (обе — примеры).

---

## 6. Приоритетный план

1. **До слияния #523/#524 (то, что уже нашёл ChatGPT и что подтверждено):** `supersede()` через `resolve_admission_types` (C2); контракт batch и смешанный тест (C1); сквозной контракт «отказ → не `ok:true`» для MCP (N-4), Telegram (N-5), `/cognitive/facts` (N-3), `/ingest` (N-2); `±1e999` (C6); идемпотентность между сессиями и не кэшировать ошибки (C7, N-10).
2. **Инварианты памяти (новые, не в отчёте ChatGPT):** M-1 (Ring Zero через upsert), M-2 (порча `Validated` upsert-ом), M-4 (потеря `restricted`), M-3 (CausalGraph в потоках), M-5 (`reinforce`/`confidence_decay` не работают), M-10 (batch не в FTS).
3. **Секреты и утечки:** N-1 (токен Telegram в логах), N-15 (`str(exc)` в ответах), I-3/I-15 (dev-ключ и открытый порт).
4. **Приватность/GDPR:** M-12, D-2, D-1.
5. **Остальное:** лимиты входа (N-8, N-9, N-19, N-24), CI-гигиена (I-5…I-9), удаление/карантин сирот и одноразовых скриптов (D-7, I-13), единый модуль канонического JSON (D-8), документация публичного API.

## 7. Чего в отчёте нет

- Результатов прогона набора тестов и покрытия.
- Динамической проверки HTTP-слоя (нет `fastapi` в контейнере) и плотных ретриверов.
- Лицензионного сканирования `uv.lock` (только наблюдения I-20).
- Повторного запуска POC исполнителей: они подтверждены чтением кода, но не перезапускались мной.
