# 🔱 VELANTRIM Titan — Глубокий аудит (2026-08-17)

> **Проверенный HEAD:** `588ffe61c711f6e63ac42cc304d95642a0671b08` (main, парent `6c744334199999935782d4f74db1b438f37b19f4`).
> Все ссылки `file:line` ниже проверены против **именно этого** коммита.
>
> **Метод:** multi-agent повторный аудит. 5 параллельных research-агентов (read-only, ни один файл кода
> не менялся ни одним из них — `git status` оставался чистым на протяжении всей работы):
> (1) реверификация всех пяти High-находок (H1–H5) `AUDIT_DEEP_2026-07-28.md` против текущего HEAD;
> (2) реверификация всех 15 Medium-находок (M1–M15) + выборочных Low того же отчёта;
> (3) свежий аудит подсистем, смердженных **после** 07-28 (Phase 2A Capability Registry, Phase 3A Embedding
> Space Identity, CSM Stage C сканер, multilingual retrieval patch, storage-bootstrap serialization fix
> #347/PR #349, CAS-характеризация #249/PR #346) — включая написанные и реально прогнанные независимые
> concurrency-стресс-пробы (~7200 конкурентных попыток суммарно, отдельно от штатных тестов репозитория);
> (4) свежий security-срез (auth, SSRF/injection, новые роуты, eval/exec/pickle, секреты, CORS, DoS) —
> независимый от находок обоих предыдущих аудитов;
> (5) реальный прогон `ruff`/`mypy`/`pytest` **на закреплённом `uv.lock`-тулчейне** (не на произвольно
> установленных версиях) + свежий silent-except sweep по последним 15 коммитам, трогавшим `core/`.
>
> **Это НЕ отчёт «применил фиксы».** Диагностика only. Единственный источник истины о состоянии кода —
> сам код на указанном коммите; находки ниже — diagnosis, не implementation truth.
>
> **Важное совпадение по времени.** PR #349 (закрывающий issue #347) был смерджен **сегодня же**,
> `2026-08-17T08:28:19Z`, за несколько часов до этого аудита. Issue #347 намеренно остаётся `open` на
> GitHub — согласно явному чек-листу самого PR #349, ручное закрытие идёт последним шагом **после**
> «GitHub current-truth reconciliation». Часть III и обновления `docs/ai/KNOWN_RISKS.md`/`WORK_LOG.md` в
> этом же коммите — и есть эта реконсиляция, включая независимую post-merge верификацию самого фикса.

---

## 📌 Резюме одной строкой

```
Пред. аудит (07-28):  Critical 0 · High 5 (H1-H5) · Medium 15 (M1-M15) · Low 15
Статус находок 07-28: FIXED — 6 (H1,H4,H5,M2,M7,M10) · CLOSED-BY-REDESIGN — 1 (H2)
                      PARTIAL — 2 (H3,M12) · NOT FIXED — 10 (M1,M3,M4,M6,M8,M9,M11,M13,M14,M15)
Новый аудит (08-17):  Critical 0 · High 0 · Reduced-risk/contained 2 (H3,M12)
                      Medium 13 (10 carried + 3 new) · Low 7 подтверждено-открытых (3 carried + 4 new)
                      + 1 new Low найдена-и-закрыта-этим-же-аудитом (docs-sync #347)
                      + ~12 Low из 07-28 НЕ реверифицированы в этом цикле (не путать с «фиксед»)
CI на 588ffe6:        закреплённый тулчейн (uv.lock): ruff 0 ошибок · mypy 0 ошибок (330 файлов) ·
                      pytest 4301 passed / 17 skipped / 1 xfailed / 0 failed (228s) — все зелёные не
                      декларативно, а реальным прогоном
GitHub-эвиденс #347:  PR #349 MERGED 2026-08-17T08:28:19Z · exact head d1d025a9 · Full CI #1317/
                      32007770456 SUCCESS · CodeQL #155 SUCCESS · Docker #868 SUCCESS ·
                      CAS-характеризация #14/32007770435 SUCCESS (4/4 hosted jobs, py3.11+py3.12)
```

---

## Часть I — Статус находок аудита 2026-07-28

Легенда: ✅ FIXED · 🔁 CLOSED-BY-REDESIGN (баг исчез не «починкой», а осознанным изменением архитектуры) ·
🟡 PARTIAL · ❌ NOT FIXED.

### 🟠 HIGH

| # | Находка | Статус | Комментарий |
|---|---|---|---|
| H1 | MetaSupervisor: budget-сигнал пришпилен к 0.0 (`get_budget_planner` не существует) | ✅ FIXED | `core/meta_supervisor.py:301-309` теперь импортирует реальные экспорты (`evaluate_budget`, `is_memory_budget_enabled`); `except` теперь `logger.warning` вместо silent-`pass`. Заодно исправлены ещё два смежных бага: эскалация DEGRADED→SAFE_MODE теперь проверяется раньше recovery (было — вечная осцилляция HEALTHY↔DEGRADED), и `budget` включён в условие recovery (:351,366,380,391). Регрессия закреплена `tests/test_meta_supervisor_budget_signal.py`. |
| H2 | ExperienceReplay: Velum reinforcement/decay — трёхслойный мёртвый путь (wrong import → несуществующие методы → async/sync) | 🔁 CLOSED-BY-REDESIGN | Мёртвый путь исчез (PR #66), но пост-мерж ревью нашло, что «оживший» вызов нарушает AGENTS.md §Canonical memory boundary тремя новыми способами (cross-loop доступ к Velum-синглтону, запись `fact_id` в keyspace имён сущностей, игнорирование `ENABLE_VELUM=0`). Corrective PR перевёл движок в намеренный analysis-only: `core/experience_replay.py:75-106` теперь всегда честно репортит `velum_edges_boosted/decayed: 0` + `velum_apply_status`/`velum_apply_reason`. Реинфорсмент по этому пути по-прежнему не применяется — теперь по архитектурному решению, а не по багу. |
| H3 | GDPR erasure: crash-recovery (`resume_incomplete_jobs`/`resume_incomplete_batches`) нигде не подключены к продакшену | 🟡 PARTIAL | Именно эти функции **всё ещё** не имеют вызывающих вне тестов (`core/erasure_coordinator.py:2050-2051`, `core/erasure_batch_coordinator.py:1550-1551`). НО: новый, отдельный, **ограниченный по бюджету** механизм подключён в `server.py:318-331` (FastAPI `lifespan`, один раз на процесс, `execute_and_record_startup_recovery()`) → `core/erasure_bounded_recovery.py`/`core/erasure_bounded_batch_recovery.py`, использующий те же низкоуровневые примитивы напрямую (не сами эти функции). `docs/operations/erasure-bounded-single-recovery.md` явно говорит, что это не заменяет `resume_incomplete_jobs()` для исчерпывающего дренажа. Практический риск «зависшая сага пропущена навсегда» для типичного бэклога закрыт; для бэклога сверх бюджета (по умолчанию 25 jobs/5 batches/5000ms) — по-прежнему нужен ручной вызов. |
| H4 | RAR-парсер: size-guard считает заявленный (untrusted) размер, обходимо | ✅ FIXED | `core/file_parsers/archive_parser.py:291-355`: заголовочный `info.file_size` теперь только «дешёвый early-reject», реальное ограничение — потоковое, через тот же `_stream_copy_capped()`, что и zip/tar (:348-351). Заодно выровнен path-traversal-чек на ту же `abspath`-схему, что и `_extract_zip`. |
| H5 | Gemini model-id интерполируется в URL без валидации; существующий валидатор мёртв | ✅ FIXED | Новый `assert_safe_gemini_model_id()` (`core/gemini_models.py:397-426`, regex `^gemini-[a-z0-9][a-z0-9.-]*$`) вызывается прямо в `_gemini_generate_url` (`core/llm_router.py:378`) перед сборкой URL. Отдельно `model_allowed_for_provider` теперь реально вызывается через новый `assert_model_allowed()` (`llm_router.py:501-517`) из `chat_complete()` (:537) и `test_connection()` (:781) — включая deepseek-ветку, которая раньше могла это обойти. `tests/test_egress_review_fixes.py:167` AST-тестом закрепляет, что валидатор имеет реального продового вызывающего. |

### 🟡 MEDIUM

| # | Находка | Статус | Комментарий |
|---|---|---|---|
| M1 | SAFE_MODE не блокирует запись в `console_notes`/`goal_stack`/`memory_ops`/`umwelt_store` | ❌ NOT FIXED | Ни один из четырёх файлов и ни один из их роутов в `server.py` не зовёт `write_gate.ensure_writes_allowed()` — подтверждено grep, без единого совпадения. Новая деталь: даже единственный частично-гейтнутый путь (`/memory/inbox/{id}/promote` → `memory_ops.py:438` → `store_fact_result`, корректно отклоняющий в SAFE_MODE) всё равно исполняет ungated `store_raw_text()` и `UPDATE fact_inbox` (:448-452,471-475) **независимо от отказа** — т.е. БД продолжает расти в SAFE_MODE даже на этом пути. |
| M2 | `ForgettingEngine.forget_one()` — мёртвый код с оригинальным GDPR-багом | ✅ FIXED | Мигрирован на `ErasureCoordinator.erase_fact_durable()` (`core/forgetting.py:266-367`) коммитом `9cda006` (2026-08-10, «Converge legacy single-fact erasure on durable coordinator», #280) — уже после базового коммита прошлого аудита. |
| M3 | `store_fact`/`store_facts_batch` UPSERT без CAS-guard (в отличие от `update_state`) | ❌ NOT FIXED | `core/memory.py:1977-2020` и `:4447-4503` — оба `ON CONFLICT(fact_id) DO UPDATE` без `WHERE`. Контраст подтверждён: `update_state()` (:2802-2820) и ещё 10+ мест в файле используют `WHERE fact_id=? AND epistemic_state=?`. |
| M4 | `ProvenanceChain._compute_hash` без `hash_version` — legacy-записи провалят `verify()` | ❌ NOT FIXED | `core/provenance_chain.py:41-54,245-309` — колонки `hash_version` по-прежнему нет (в отличие от `audit_chain.py`, где есть v1/v2 dual-dispatch через `migrations/017_audit_chain_hash_v2.sql`). `.verify()` по-прежнему не имеет вызывающих вне докстринга. |
| M6 | EdgeSuggester: гонка дублей suggested-edges → неотловленный `IntegrityError` | ❌ NOT FIXED | `migrations/019_suggested_edges.sql:6-26` — по-прежнему нет UNIQUE на `(from,to,type)`. `approve()` (`core/edge_suggester.py:317-382`) по-прежнему без try/except вокруг `add_relation()`; роут `server.py:3017-3039` ловит только `KeyError`/`ValueError` → до сих пор 500 клиенту при гонке. |
| M7 | `CausalGraph.import_snapshots` — bare except, нет счётчика failed | ✅ FIXED | Переписан коммитом `615201e` (2026-08-11, #287): малформед-строки теперь `raise ValueError` немедленно; вставка идёт через `add_relations_batch()` (`core/causal_graph.py:490-530`) одной транзакцией с `except Exception: rollback(); raise`. Семантика поменялась с «best-effort частичный импорт» на «atomic all-or-nothing» — стоит иметь в виду тем, кто полагался на старое поведение. |
| M8 | `truth_maintenance.contradict()` тихо глотает вторичные записи, `changed=True` всё равно | ❌ NOT FIXED | `core/truth_maintenance.py:393-415` — байт-в-байт как в прошлом аудите, те же номера строк. |
| M9 | `server.py` отдаёт `str(exc)` клиенту | ❌ NOT FIXED | Глобальный handler `server.py:4198-4204` (номера строк съехали из-за промежуточных коммитов, код тот же) + 25 локальных `HTTPException(detail=str(exc))`. Существующий санитайзер в `api/server_middleware.py:269-304` покрывает только `/system/epigenetic` (отдельный фикс #52) и не относится к общему случаю. |
| M10 | BranchManager: LLM/essence-фоллбек всегда мёртв (неверные kwargs/сигнатуры) | ✅ FIXED | Коммит `019f581` (2026-08-15, #334): `core/branch_manager.py:98-124,260-305` — LLM теперь используется только когда вызывающий передаёт реальный `llm_config`; `compose_essence(facts, relations=None)` вызывается с правильной сигнатурой и dataclass-доступом. Confidence=0.3 шаблон теперь настоящий last-resort, а не единственный достижимый путь. |
| M11 | GraphLab `analyze_graph` — параметр `db_path` не существует в реальной сигнатуре | ❌ NOT FIXED | `core/graph_lab_bridge.py:113-129` всё ещё зовёт `gl_analyze(db_path=...)` против `core/graph_lab.py:319-325` (`conn=`, без `db_path`) — файл не трогали с момента прошлого аудита (одна историческая правка во всей git-истории файла). |
| M12 | Несколько построенных, но не подключённых safety/decay-модулей | 🟡 PARTIAL | `core/compute_controller.py` теперь имеет реального вызывающего — `core/rapid_orientation.py` → `api/server_middleware.py:147-159` за флагом `ENABLE_RCO_SHADOW`, но это read-only shadow-диагностика, которая **никогда не мутирует состояние и не гейтит ничего живого** (по собственному докстрингу модуля). `memory_archival.py`, `fact_decayer.py`, `adaptive_truth.py`, `negative_reinforcement.py` — по-прежнему 0 ссылок где-либо вне тестов. |
| M13 | `modality_guard` bare list-truthiness | ❌ NOT FIXED | `core/truth_policy.py:177,191` — те же номера строк, без изменений. |
| M14 | `NAMESPACE_BRIDGE_CONFIDENCE` регрессировала до 0.30 | ❌ NOT FIXED | `core/knowledge_linker.py:487` — значение то же, всё ещё ниже traversal-порога 0.5. |
| M15 | HybridRetriever пересобирается на каждый branch/запрос | ❌ NOT FIXED | `core/branch_manager.py:227-258` — всё ещё создаёт свежий `HybridRetriever(facts)`, никогда не трогая dirty-tracked синглтон-кэш `core/pipeline.py:130-161`. Подтверждено: diff коммита `019f581` (M10) вообще не касался тела `_retrieve_with_hints`. |

### 🟢 LOW — реверифицированы в этом цикле (только эти три; остальные ~12 из 07-28 см. примечание ниже)

| Находка | Статус | Комментарий |
|---|---|---|
| Нет Content-Security-Policy заголовка | ❌ NOT FIXED | `api/server_middleware.py:281-312` — X-Frame-Options/X-Content-Type-Options/HSTS/Referrer-Policy есть, CSP по-прежнему нет. |
| PII-редакция (`pii.py`) / at-rest-шифрование (`crypto.py`) opt-in-выключены | ❌ NOT FIXED (by design) | `core/pii.py:14,38-40`, `core/crypto.py:11-13,55-63` — оба по-прежнему требуют явного `VELANTRIM_REDACT_PII`/`VELANTRIM_ENCRYPTION_KEY`. Осознанный дизайн, не регрессия. |
| Rate limiter без XFF-awareness | ❌ NOT FIXED | `api/server_middleware.py:326` — по-прежнему чистый `request.client.host`. |

> **Про остальные ~12 Low-находок 07-28** (дубль `_ESM_RANK`, orphaned-модули, `storage_info.cache_clear()`,
> unused reverse-edge weight, `_next_seq` sentinel, отсутствие append-only триггеров на `provenance_chains`,
> и т.д.) — **не входили в scope этого цикла реверификации** (низкий приоритет относительно security/
> concurrency/new-subsystem сканирования в отведённом бюджете агентов). Это explicitly "не проверено", а
> не "фиксед" — не путать одно с другим.

---

## Часть II — Новые находки (после 07-28)

### 🟡 MEDIUM (новое)

**N1. `POST /ingest/text` — неограниченное поле `text`, нет лимита размера запроса.**
`server.py:1104-1109` (`IngestRequest.text: str = Field(..., min_length=1)` — в отличие от других request-body в этом же файле, `max_length` нет), обработчик `server.py:2769-2827`, сток — `core/memory.py:4169-4230` (`store_facts_batch`, один неограниченный цикл, без потолка на размер батча). Нигде в `api/server_middleware.py`/Dockerfile/compose нет глобального лимита размера тела запроса.
**Сценарий:** аутентифицированный клиент (держатель единственного общего `VELANTRIM_API_KEY`) шлёт `text` на десятки МБ с `chunk_size=50` (минимально разрешённый) → построение списка чанков и батча без потолка на их число → один неограниченный `store_facts_batch()`-вызов → скачок памяти/CPU, долгая единичная блокирующая транзакция, необратимый рост БД за один запрос.

**N2. `GET /facts` — `limit`/`offset` применяются уже после материализации всей таблицы.**
`server.py:2319-2336` режет `facts[offset:offset+limit]` уже **после** вызова `get_all_facts()`. `core/memory.py:2371-2417`: все четыре ветки `SELECT * FROM facts ...` — без SQL `LIMIT`, `.fetchall()` всей таблицы, затем `json.loads()` дважды + запись в L0-кэш + `copy.deepcopy()` **на каждую строку**, независимо от запрошенного `limit`.
**Сценарий:** контраст — `/health` (`server.py:2056-2058`) уже был исправлен на `COUNT...GROUP BY` именно для этой цели (паттерн известен команде), но не применён здесь. Обычный `GET /facts?limit=100` при большой таблице фактов — full table scan + full deep-copy каждой строки. Комбинируется с N1: один запрос раздувает таблицу, каждый последующий `/facts`-вызов **любого** клиента дорожает.

**N3. `VersionStore._ensure_schema()` — тот же класс гонки, что #347, в соседнем компоненте той же bootstrap-последовательности.**
`core/version_store.py:200-206` гейтит свой 5-стейтментный `VERSIONS_SCHEMA` (`executescript`, `core/version_store.py:67-97`) только процесс-локальным `threading.Lock()`/`set()` (`_SCHEMA_INIT_LOCK`/`_SCHEMA_READY`, :60-61) — **не** транзакцией `BEGIN IMMEDIATE`, в отличие от только что исправленного (см. Часть III) соседнего пути. `VersionStore(self.db_path)` конструируется прямо в той же bootstrap-последовательности (`core/memory.py:790`), а также достижим из `core/archival_mutation.py:83` и `core/pii_redaction.py:125`.
**Оценка риска:** структурно реальный пробел (нет транзакционной обёртки, нет cross-process защиты), но вероятно низкой вероятности — целевой скрипт маленький и чисто `IF NOT EXISTS` (нет `ALTER TABLE`, нет read-modify-write, в отличие от бага #347). Стресс-тест (40× 8 отдельных `multiprocessing`-процессов + 450× 8-30 потоков с `threading.Barrier`, ~7200 попыток суммарно) **не воспроизвёл сбой ни разу**. Репортится как честный структурный пробел для консистентности, не как подтверждённый живой инцидент.

### 🟢 LOW (новое)

**N4. `core/multilingual_router.py` — несинхронизированное глобальное состояние в patch/unpatch.**
`_installed_retrieve`/`_original_retrieve` (module-level globals, :191-192) читаются-проверяются-пишутся без блокировки в `patch_pipeline_retrieval()`/`unpatch_pipeline_retrieval()` (:201-269). Теоретическая гонка при двух конкурентных вызовах может нарушить собственную документированную гарантию модуля («exactly one wrapper, never stack layers»). Стресс-тест (800 попыток × 8 потоков) гонку не воспроизвёл — единственный продовый вызывающий (`server.py:421-428`) вызывает функцию ровно один раз, последовательно, на старте. Не достижимо в проде сегодня.

**N5. Документационный разрыв: #347 закрыт кодом, но `docs/ai/KNOWN_RISKS.md`/`WORK_LOG.md` ещё говорили «open».** — **закрыто этим же аудитом**, см. Часть III и списки изменений ниже. PR #349 (фикс #347) смерджен `2026-08-17T08:28:19Z`, за несколько часов до этого аудита; сам PR явно требует «GitHub current-truth reconciliation» как отдельный шаг после мержа — этот аудит его и выполняет.

**N6. `server_patch/export_endpoints.py` — несанитизированное поле `format` доходит до `tempfile`-suffix, необработанное исключение утекает путь.**
`_format_to_ext()`/`_save_and_return()` (:99-163) не валидируют `format` перед использованием как `suffix=`. Проверено эмпирически (изолированный scratch-скрипт, не против самого приложения): значение с `/` даёт `FileNotFoundError` (случайный префикс имени от `tempfile` делает traversal-сегмент нерезолвящимся) — **не** arbitrary-write/traversal. Но `POST /export/facts` не оборачивает вызов в try/except → исключение всплывает в глобальный handler (`server.py:4198-4204`), который всё ещё делает `str(exc)` → раскрывает клиенту абсолютный путь внутреннего temp-каталога сервера.

**N7. MCP tool-call ошибки возвращают сырой текст исключения.**
`core/mcp_transport.py:239-247`: `except Exception as exc: ... {"content":[{"type":"text","text":str(exc)}],"isError":True}`. Тот же класс, что M9, но в подсистеме, которую ни один из двух прошлых аудитов не проверял. Требует валидный API-ключ и минимум "reader" MCP-capability.

**N8. `requirements-dev.txt` устарел относительно `pyproject.toml`/`uv.lock`.**
Пинит `pytest>=8.0,<9`/`pytest-asyncio>=0.23,<1`, тогда как `pyproject.toml`'s `dev`-extra и закреплённый `uv.lock` требуют `pytest>=9.0.3,<10`/`pytest-asyncio>=1.4.0,<2`. Буквальная установка по этому файлу поставит несовместимый pytest. Процессный, не security-риск.

---

## Часть III — Аудит новых подсистем (смерджены после 07-28)

Все шесть проверены независимым чтением кода (не только доков) + прогоном штатных тестов подсистемы +,
для двух наиболее concurrency-чувствительных, написанными и прогнанными отдельными стресс-пробами.

### Phase 2A Capability Registry (`core/capability_registry.py`) — 🟢 solid, claims подтверждены

Никакой constructor-injection: `__init__` (:187-188) жёстко зовёт `get_policy_kernel()` — единственный,
процесс-широкий синглтон. Unknown/unavailable health помечается `eligible=False` (:277-301) **до**
обращения к PolicyKernel. Preference не может обойти denial — фильтруется списком `eligible` (:362-366)
прежде, чем `preference` вообще участвует в tie-break (:376-390). Политик-исключение на одном кандидате
валит весь `resolve()` в `policy_evaluation_incomplete`, а не частичный успех (:310-346). Unwired
подтверждён: единственное упоминание вне `core/capability_registry.py`/тестов — докстринг в
`core/model_free_core.py:15`, явно говорящий «не вызывается». `tests/test_capability_registry.py` 8/8,
ruff/mypy чисты. Одно низкоприоритетное наблюдение: `PolicyKernel.lease_capability()` спецкейсит
литеральный id `"canonical_write"` (`core/policy_kernel.py:339`) — если когда-то реестр подключат и
кто-то зарегистрирует capability под этим именем, аренда молча переключится на canonical-write правила.
Недостижимо сегодня (реестр не подключён, такой регистрации нет).

### Phase 3A Embedding Space Identity — 🟢 solid, claims подтверждены

Diff коммита `4932727` касается только `embedding_registry.py`/`hybrid_retriever.py` — второго реестра/
стора не создано. Dimension fail-close реален: `DenseRetriever.retrieve()` (`core/hybrid_retriever.py:
349-373`) валидирует **весь** батч кандидатов через `validate_pair_dimensions()` до скоринга; несовпадение
даёт `DimMismatchError` → `return []` → откат на BM25-only, без частичного/неверного скора. Legacy-строки
без полной identity классифицируются `STALE_MODEL`, никогда `FRESH` (`embedding_projection.py:174-266`) —
не авто-усыновляются. `resolve_or_fallback`/`EmbeddingProjectionStore` не имеют вызывающих вне
`benchmarks/`/тестов; `pipeline.py` их не трогает. `tests/test_phase3a_embedding_space.py` 17/17,
ruff/mypy чисты. Новых дефектов нет.

### CSM Stage C сканер (`core/code_structural_memory/`) — 🟢 самая аккуратная из шести

Unwired подтверждён — 0 вызывающих вне пакета/тестов (`server.py`, `api/`, `scripts/`, workflows, Docker,
pyproject — ничего). Symlink-race hardening корректен по букве: каждый компонент пути открывается через
`os.open(..., dir_fd=parent_fd, O_DIRECTORY|O_NOFOLLOW)` (`scanner.py:871-915`), `fstat()`/`os.read()`
работают на **том же** уже открытом fd — классический фикс TOCTOU symlink-подмены. Конкурентность:
lease acquire/assert/release и оба finalize-пути — `BEGIN IMMEDIATE` + WHERE-CAS с проверкой `rowcount==1`,
`except Exception: rollback(); raise` везде, без единого broad swallow в commit-пути. Reuse-safety:
`_snapshot_semantics_match()` (:1529-1645) полностью пере-верифицирует header+nodes+edges перед разрешением
на переиспользование снапшота. Байт-бюджет: `total_bytes` считается безусловно (:1143), даже для
впоследствии отклонённого файла — совпадает с заявкой ADR. 72/72 теста по всем 7 CSM-файлам, ruff/mypy
чисты. Новых дефектов нет.

### Multilingual retrieval patch lifecycle (`core/multilingual_router.py`, PR #341) — 🟡 функционально верно, 1 Low (см. N4)

Идемпотентность, точное восстановление оригинала, отсутствие затирания внешней замены и очистка stale-
bookkeeping — подтверждены чтением `patch_pipeline_retrieval()`/`unpatch_pipeline_retrieval()` (:201-269)
и всеми 4/4 тестами. Единственный продовый вызывающий — `server.py:421-428`, один последовательный `await`
на старте. См. N4 выше про несинхронизированные глобалы (Low, не воспроизведено, не достижимо сегодня).

### Storage bootstrap serialization fix — issue #347 / PR #349 — ✅ подтверждён исправленным

**GitHub-факты (проверены напрямую через API, не по докам):** PR #349 `MERGED` `2026-08-17T08:28:19Z`,
exact head `d1d025a952d623293f7ff2d868596fdfd37e119e`, база `main@6c744334...` (= коммит #350, родитель
HEAD). Exact-head evidence: Full CI `#1317`/`32007770456` SUCCESS · CodeQL `#155`/`32007770414` SUCCESS ·
Docker `#868`/`32007770410` SUCCESS · Dependency vulnerability audit SUCCESS · Coverage ratchet (core≥74%)
SUCCESS · CAS contention characterization `#14`/`32007770435` SUCCESS на всех 4 hosted matrix job
(py3.11×2 shards, py3.12×2 shards).

**Код (проверен независимо от PR-описания):** весь lazy DDL/bootstrap (~40 statements) обёрнут в
`conn.execute("BEGIN IMMEDIATE")` (`core/memory.py:489-491`) … `conn.commit()` (:767). На исключении —
явный `rollback()` (сам защищён — сбой rollback только логируется), `close()`, `self._sqlite_conn = None`,
безусловный re-`raise` (:769-779) — без silent swallow. `BEGIN IMMEDIATE` берёт RESERVED lock на уровне
файловой блокировки ОС — сериализует не только потоки одного процесса, но и **отдельные ОС-процессы** на
одном файле (ADR прямо отвергает Python-level global lock именно по этой причине). Структурного риска
дедлока нет — единственный mutex-ресурс, ограниченный `self._busy_timeout_ms`; таймаут всплывает как
`OperationalError` через тот же rollback/raise путь, а не виснет.

**Независимая post-merge проверка (эта же работа, часть сегодняшнего аудита):** написана и прогнана
отдельная стресс-проба — 40 попыток × 8 подлинно раздельных `multiprocessing`-процессов — воспроизвести
исходный `sqlite3.OperationalError: database schema has changed` на пофикшенном коде. **0 сбоев.** Это
и есть тот самый шаг «post-merge main verification», который сам PR #349 перечисляет как обязательный
перед закрытием issue #347.

**Найден один смежный, не покрытый этим PR остаточный риск** — см. находку N3 выше
(`VersionStore._ensure_schema()`, тот же класс гонки, вероятность ниже, не воспроизведена).

**Вывод для issue #347:** код-фикс подтверждён независимо (GitHub CI evidence + собственная
стресс-проверка этого аудита). `docs/ai/KNOWN_RISKS.md`/`docs/ai/WORK_LOG.md` обновлены этим же коммитом,
чтобы отразить это (см. список изменений ниже). Согласно собственному чек-листу PR #349, **ручное закрытие
issue #347 на GitHub — намеренно отдельный, human-in-the-loop шаг**, не автоматизируется этим аудитом.

### CAS contention characterization — issue #249 / PR #346 — ✅ классификация обоснована, не отмывание

Diff `fa09bc1` касается только `tests/test_promotion_projection_outbox_caller.py` (добавляет
последовательный `ensure_schema()` для всех stores **до** установки CAS-race gate) + новый workflow;
`_promote_to_validated_cas()` не тронут. Сам `_promote_to_validated_cas()` (`core/memory.py:3163` и далее)
— корректный однострочный CAS: `UPDATE facts ... WHERE fact_id=? AND epistemic_state=? AND updated_at=?`,
`committed = cur.rowcount==1`, всё в одной транзакции с VersionStore-снапшотом и AuditChain-событием — без
read-then-write TOCTOU-окна. Более старый узкий unit-тест (`tests/test_sqlite_promotion_cas_contention.py`,
существовал до этого PR, гоняет 2 писателя против уже забутстрапленной БД) независимо доказывает
one-winner/one-loser CAS. Прогнан отдельно — 1/1 pass, плюс переработанный `[25]`-тест — 3/3 pass.
Формулировки в `docs/ai/KNOWN_RISKS.md` («не доказательство неограниченной конкурентности SQLite или
production-scale multiprocess safety») откалиброваны корректно, без overclaim.

---

## Часть IV — Реальное здоровье CI/тулчейна

Прогнано напрямую, не переписано из документации.

```
ruff check core/:    0 ошибок — но ТОЛЬКО на закреплённом uv.lock-тулчейне (ruff 0.4.10, точное
                     совпадение с requirements-dev.txt/pyproject.toml/uv.lock). Амбиентный глобальный
                     ruff 0.15.8 в песочнице даёт 148 ложных `UP045` (правило, которого не существует
                     в 0.4.10; предупреждение самого ruff про удалённый `UP038` — тот же симптом
                     версийного рассинхрона). Это артефакт тулчейна, не дефект кода.
mypy core/:          0 ошибок, "Success: no issues found in 330 source files" — на закреплённом mypy
                     1.20.2 (точное совпадение с uv.lock). Амбиентный изолированный mypy 1.19.1 даёт 1
                     ложную ошибку (нет стаба types-PyYAML в его собственном venv, не в проекте).
pytest tests/:       4301 passed, 17 skipped, 1 xfailed, 0 failed за 228.19s. Все 17 skip — легитимны и
                     дали бы тот же результат в реальном CI (нет живого uvicorn, нет соседнего репо
                     velantrim_core-3, нет reportlab/python-pptx — ни один не в pyproject extras).
CI workflow match:   да, дословно — `.github/workflows/ci.yml` job `lint-and-test` гоняет identical три
                     команды на Python 3.11 через `uv sync --frozen`. Отдельная job `coverage` энфорсит
                     `--fail-under=74` на core/-scope (две concurrency-стресс-теста явно исключены из
                     coverage-рана — конфликт между coverage trace hooks и per-thread trace hooks теста,
                     сами тесты при этом гоняются в lint-and-test).
new silent-except:   0 новых. Внутри последних 15 коммитов, трогавших core/, найдено ОБРАТНОЕ — 3
                     ранее существовавших silent-swallow паттерна были исправлены: bootstrap-handler в
                     memory.py (588ffe6), NGram-handlers в index_coordinator.py (0498312), fallback-
                     handlers в branch_manager.py (019f581).
```

---

## Что сделано хорошо

- **Культура ре-аудита продолжает работать на практике, а не на бумаге.** Из 20 находок H1-H5/M1-M15
  прошлого аудита 6 полностью исправлены (в т.ч. три — попутно, коммитами, не заявленными как «фикс
  аудита»: M2/M7/M10 через #280/#287/#334), 1 закрыта осознанным архитектурным решением (H2), 2 частично
  (H3/M12) и только 10 не тронуты. Ни один статус не регрессировал.
- **PR #349 (issue #347) — образцовый пример bounded fix.** Диагностика → минимальная транзакционная
  сериализация → явный отказ от retry/timeout-inflation/WAL-смены → полная hosted-evidence-цепочка →
  честное «issue остаётся open до ручной реконсиляции». Независимая стресс-проверка этого аудита (~40×8
  процессов) не нашла ни одного контрпримера.
- **CI реально зелёный, не только продекларирован.** 4301 passed / 0 failed / 0 ruff / 0 mypy на
  закреплённом тулчейне — при том, что это тот же тулчейн, что реально гоняет `.github/workflows/ci.yml`
  (проверено построчным сравнением workflow-файла с локальным прогоном).
- **Три из шести подсистем, смердженных с прошлого аудита (Phase 2A, Phase 3A, CSM Stage C), не дали
  вообще ни одной новой находки** при целевом поиске second-owner-мутаций, auth-bypass, TOCTOU-гонок и
  rename-drift — том самом наборе классов дефектов, что каждый предыдущий аудит этого репозитория
  реально находил. Их «UNWIRED/NOT ENABLED» заявления подтверждены прямым grep, а не переписаны с доков.
- **Security-срез не нашёл ни одной новой Critical/High.** Несколько мест, выглядевших подозрительно при
  поверхностном чтении (`/system/epigenetic` без видимого auth-декоратора, MCP capability header, LLM-
  provider-bypass), при проверке оказались уже корректно закрыты в другом слое (middleware, PolicyKernel-
  дефолты) — подтверждено динамическим прогоном существующих тестов, а не только чтением кода.

---

## Рекомендованный порядок (диагностика — решение о фиксах за автором)

1. **M1** — самое системно значимое из нефикшенного: SAFE_MODE — это заявленный инвариант экстренной
   остановки записи (`meta_supervisor.py:16`), а не блокирует реально 4 модуля + одну ungated под-запись
   даже на частично гейтнутом пути. Распространить `write_gate.ensure_writes_allowed()` на
   `console_notes`/`goal_stack`/`memory_ops`/`umwelt_store`, и на `store_raw_text()`/`fact_inbox`-апдейт
   внутри promote-пути.
2. **N1/N2** — граничат друг с другом (одна раздувает таблицу, вторая делает каждый последующий запрос к
   ней дороже): добавить `max_length` на `IngestRequest.text` + потолок на итоговый размер батча; добавить
   реальный SQL `LIMIT`/`OFFSET` в `get_all_facts()`, по образцу уже существующего `/health`-фикса.
3. **H3** — если политика требует гарантии «ни одна erasure-сага не зависает дольше X», нужно либо поднять
   бюджет ограниченного startup-recovery, либо подключить периодический (не только startup) вызов
   исчерпывающего `resume_incomplete_jobs()`/`resume_incomplete_batches()`.
4. **M9/N6/N7** — один и тот же класс (утечка `str(exc)`) в трёх местах (`server.py` глобальный handler,
   `export_endpoints.py`, `core/mcp_transport.py`): стоит одного сквозного фикса, а не трёх точечных.
5. **N3** — привести `VersionStore._ensure_schema()` к тому же `BEGIN IMMEDIATE`-паттерну, что и #347, для
   консистентности, даже если вероятность реального попадания низкая.
6. **M3/M4/M6/M8/M11/M13/M14/M15** — без изменений с прошлого аудита; ни один не concurrency/security-
   критичен настолько, чтобы обгонять пункты 1-5, но остаются реальным техническим долгом.
