# 📓 COLLAB JOURNAL — Velantrim × Claude

> **Назначение:** живая «записная книжка» совместной работы. Claude обновляет её
> **после каждого прогона / завершённого шага**: что сделано, почему, что дальше.
> Это внешняя память (страховка от потери контекста) и след для гранта.
>
> **Правило:** новые записи — сверху раздела «Хронология». Факты — проверяемые
> (команда/файл/коммит). Никаких неподтверждённых цифр.

---

## 🎯 Цель проекта (как сформулировал автор, 2026-05-30)

Настоящий **экзокортекс** — фрактальная память L0–L7 по образу человеческой, но умнее:
- **Понимание сути** (Essence): сжать сложное в короткий человеческий вывод, связать
  разные концепции, понять «о чём на самом деле речь».
- **Observer** (наблюдатель потоков информации) — куда течёт информация и что с ней делать.
- **Граф знаний**: суть науки — инвариантная / вариантная / **практическая** (~25%,
  где строят мосты, микропроцессоры, химию), + педагогический слой, **без «учебного шума»** —
  только узлы и рёбра инвариантов; машина считает через связи, человеку объясняет коротко.
- **Умное забывание** (FSRS), автономность, параллельность без перегрузки.
- **Малое ядро** как failover, если основной экзокортекс даёт сбой.

Принцип работы: **хребет — вглубь, прежде чем конечности — вширь.** Каждый слой
доводится до «реально работает + доказано тестом», только потом следующий.

---

## 📊 Базовая линия (ground truth, проверено 2026-05-30)

**Окружение для тестов:** изолированный `.venv` (Python **3.12.13** через `uv`).
Команда: `.venv/Scripts/python.exe -m pytest -o addopts="" -q --no-cov`
(полный прогон с покрытием: убрать `--no-cov`, добавить `--cov=core --cov-report=term-missing`).
Системный Python — 3.14.5 (`py`), но для воспроизводимости держим 3.12.

**Полный прогон (16.5 мин):**
- `682 собрано → 652 passed · 0 FAILED · 17 skipped · 13 xfailed` ✅ реально зелёный
- **coverage core/ = 56.21%** (НЕ заявленные «~87%»); порог проекта `fail_under=80` не достигнут
- Ядро покрыто хорошо: `storage` 100%, `truth_gate` 92%, `fractal_memory` 92%,
  `trace`/`ngram` 91%, `causal_graph` 87%, `memory` 85%, `pipeline` 72%
- Периферия тянет вниз: `epistemic_pipeline`/`types`/`text_utils`/`tts`/`velum_persistence` ~0%,
  `concept_emergence` 27%, `salience` ~39%
- **Вывод:** 56% = измеренные «35% готовности» из LIMITATIONS.md. Сердце живо и крепко.

---

## 🗺️ План (приоритет: ❶ Essence)

- [~] **❶ Essence Layer P0** — детерминированный фундамент «сути». ← В РАБОТЕ
  - [x] `core/essence.py` — gist + роли + цепочка + короткий ответ + WhyTrace (за флагом `ENABLE_ESSENCE`, без LLM, не трогает stable `/query`).
  - [x] `tests/test_essence.py` — 21 тест, все зелёные.
  - [ ] Подключить causal_graph как источник `relations` (реальные причинные связи).
  - [ ] Опционально: LLM-композер поверх P0 (креативный синтез) — отдельный флаг + тесты.
  - [ ] Wiring в `/query` за флагом + интеграционный тест (только после RFC, канон).
- [ ] **❷ Граф знаний науки** — наполнение `docs/knowledge/world_skills_core/` (зона Codex).
- [ ] **❸ Dual-core надёжность** — `Small Core Complex` + `Dual_Core_Router` + failover.
- [ ] Гигиена: удалить карантин (−162 МБ), починить split-brain L1→L0, распилить `server.py`.

---

## 🤝 Координация (важно — параллельная работа)

- **git-страховка стоит** (репозиторий инициализирован 2026-05-30). Все правки обратимы.
- **Codex работает в `docs/knowledge/world_skills_core/`** (README, MAP, BATCH_001/002) —
  это его территория, Claude туда не пишет и не коммитит за него.
- Claude держится core-кода + корневых доков + тестов. При конфликте — git спасёт.

---

## 🕓 Хронология (новое сверху)

### 2026-05-31 — 📚 Вариант 3: ingest реальной базы знаний (world_skills_ingest)
- `core/world_skills_ingest.py` — реальный переиспользуемый ingest: `parse_batch_markdown`/`parse_knowledge_dir`,
  `ingest_facts` (курируемые → Validated, no-DELETE), `ingest_world_skills` (+ типизированные рёбра linker).
  `tests/test_world_skills_ingest.py`: **4 passed** (парсер + ingest в store; поймал баг в собственном тесте — починен).
- Демо на РЕАЛЬНОМ BATCH_001 (80 фактов): загружено 80, 26 рёбер; **Essence-цепочка на настоящих знаниях**:
  «Пшеница даёт зерно —enables→ Помол превращает зерно в муку —precedes→ Просеивание». ✅ Цель варианта 3 достигнута.
- ⚠️ **НАХОДКА (P1, производительность):** per-fact ingest ~**1.76с/факт** (80 фактов = 141с) → 1700 ≈ 50 мин
  (полный ingest «завис» именно поэтому, пришлось капнуть до 80). Причина — per-fact накладные
  (`_snapshot_before_change` / NGram / memory_budget). Фикс: bulk через `store_facts_batch` + отложенная
  переиндексация. Профилировать отдельно.
- ✅ **ОЧЕРЕДЬ АВТОРА ЗАКРЫТА:** причесать RFC · вариант 1 · вариант 2 · вариант 3.

### 2026-05-31 — 🔌 Вариант 2: Working Notebook подключён в pipeline (run_with_notebook)
- `core/working_notebook.py`: реестр сессий + `get_notebook` / `notebook_directive_for` / `reset_notebooks`.
- `core/pipeline.py`: обёртка `run_with_notebook(query, session_id)` — АДДИТИВНО, `run()` не тронут;
  при `ENABLE_WORKING_NOTEBOOK`+session_id кладёт `notebook_directive` («думай, как я») + `notebook` РЯДОМ с ответом.
- `tests/test_notebook_wiring.py`: **4 passed** (директива при флаге; выкл по умолчанию; без сессии; persist across turns).
- LLM-слой (server) может подставить директиву в системный промпт перед ответом. В L3 не пишет.

### 2026-05-31 — ⚙️ Вариант 1: органы в рантайме (профиль) + многоязычная модель
- `config/profiles/cognitive.env` — опт-ин профиль: включает все P0-органы + `SEMANTIC_DEDUP_MODEL`=multilingual.
  Основной `.env` НЕ тронут (опт-ин через профиль).
- Многоязычная модель доказана: ru↔en «вода кипит»↔«boiling point» = **0.84** (было 0.22 на MiniLM) → сливаются.
- Интегрированный прогон (`run_consolidation`→sleep-loop, все флаги вкл): `corroboration_mode=semantic`;
  ru+en промоутнуты в Supported (семантическая корроборация); противоречие дерево «подходит/не подходит» → `a` Contradicted.
  Working Notebook выдал директиву. **Полный стек работает вместе.**
- ⚠️ **НАХОДКА (P1):** семантический дедуп считает противоположно-полярные факты («X»/«не X») как ВЗАИМНУЮ
  корроборацию (они в одном смысловом кластере) → завышает её (b «не подходит» промоутнулся за компанию).
  Фикс: исключать opposite-polarity из corroboration (переиспользовать polarity из `contradiction_resolver`). Отдельно.

### 2026-05-31 — 🏁 Полный прогон после split-brain/security — 760 passed, 0 FAILED
- **760 passed, 0 FAILED, 17 skipped, 13 xfailed** (1242с / 20.7 мин). Coverage `core/` = **58%**.
- Подтверждено: правки `memory.py` (split-brain L0→L1) + `server.py` (security) + ВСЕ сессионные модули
  интегрированы ЧИСТО — ноль падений на всём проекте. `EXIT_CODE=1` = только порог покрытия 80%, не падения.
- 🏁 Весь проект зелёный как единое целое **после самой рискованной правки сессии** (ядро памяти).

### 2026-05-31 — 🩹 Split-brain L0→L1 фикс + батч-ingest (из backlog, «и то, и другое»)
- **SPLIT-BRAIN (audit C-2):** в `memory.store_fact` переставил `_l0_put` ПОСЛЕ записи L1 (durable).
  Раньше L0-кэш писался ДО INSERT → при сбое L1 факт оставался в L0 без L1. Теперь порядок L1→L0
  (соответствует инварианту D4). **ESM/regression: 47 passed** — фикс безопасен.
  `tests/test_split_brain.py` (durability: свежий стор читает факт из L1): **2 passed**.
- **БАТЧ-INGEST:** `world_skills_ingest.ingest_facts` теперь через `store_facts_batch` (одна транзакция).
  Замер 80 фактов: store-фаза **141с → 1.5с (~90×)**; 1700 фактов ≈ 30с (было ~50 мин).
  НО `validate=True` всё ещё ~135с — узкое место **не store, а `transition_esm`** (per-op connection, P-4).
  Вывод: для bulk → `validate=False` (Observed) + промоушен через consolidation; быстрый batch-transition = P2.

### 2026-05-31 — 🔐 Рекомендации автора: безопасность + канон + «другое» (+ оценка DeepSeek)
- 🔴 **#1 БЕЗОПАСНОСТЬ закрыта** (висела с первого аудита): `server.py` — constant-time ключ
  (`hmac.compare_digest`), **fail-closed** `/telegram/webhook` (без секрета → 403), скрытый Swagger
  (`ENABLE_API_DOCS`). `.env` (gitignored): сильный ключ + `ALLOW_OPEN=false` (было `dev-change-me`+`true`).
  `.env.example` уже был безопасен. `test_telegram_ingest`: обновлён + тест fail-closed (7 passed).
- 🚨 **#0 КАНОН против расползания:** `CANONICAL.md` — ЭТА папка (git, server.py=3510, 34+ коммита) = канон.
  ≥8 копий в `Documents\velantrim\` БЕЗ git. **DeepSeek аудировал СТАРУЮ `Documents\velantrim\V8.6`**
  (server.py=1998, no-git) → его числа (543 теста, ~1990 строк) — к НЕЙ, не к канону. Рекоменд.: заморозить
  старые в `_archive`, не удалять (возможен уникальный контент). Карантин −162 МБ можно удалить.
- 🧹 **«Другое» (быстрые победы):** `backend_capabilities()` честный (`neo4j:False`, не безусловно True);
  `semantic_dedup` больше НЕ корроборирует «X»/«не X» (split по полярности, +1 тест) — закрыта находка варианта 1.
- 📊 **Оценка DeepSeek:** красивая презентация (Canvas+эмодзи), НО числа устаревшие (доковые «543/596/87%» —
  опровергнуты, реально 748/56-58%) и копия старая. Полезное взять (backlog): нет Dockerfile, нет
  `AGENTS.md`/`.cursor/rules`, Telegram E2E, Kuzu version-pin `>=0.7,<0.12`.
- 📋 **Остаётся в backlog (крупное, честно):** рефактор server.py (3510 стр), split-brain L0→L1,
  CoherentCache wiring, Observer Drift (RFC-0081 §10), LLM-композер Essence, batch-ingest (перф ~1.76с/факт),
  xfail-маскировка knowledge_ingester, полный прогон после правок.

### 2026-05-31 — 📄 RFC-0080/0081 перенесены в репо как чистые файлы (вариант «причесать RFC»)
- `docs/RFC-0081_Working_Notebook.md` — чистая спека (дедуп из переписки): Purpose..Observer,
  числа помечены ⚙️ «настраиваемые дефолты», отмечен реализованный P0 (`core/working_notebook.py`).
- `docs/RFC-0080_Cognition_Layer.md` — мета-слой «суть/интент/почему» (бывш. «Essence Layer», переименован,
  чтобы не путать с `core/essence.py`); маппинг на реальные модули (essence/understanding/dialogue_essence/linker).
- Теперь ссылки RFC-0080/0081/0082 указывают на реальные файлы репо, а не на переписку. Очередь автора: далее варианты 1→2→3.

### 2026-05-31 — 🏁 Полный прогон «для чистоты» — 748 passed, 0 FAILED (ВЕХА)
- **748 passed, 0 FAILED, 17 skipped, 13 xfailed** (1346с / 22 мин, dense активен). Coverage `core/` = **58%**.
- Новые модули покрыты сильно: `working_notebook` **94%**, `contradiction_resolver` **90%**,
  `semantic_dedup` **86%**, `sleep_consolidation` **77%** — все сильно выше среднего.
- Подтверждено: ВСЯ сессионная работа интегрирована ЧИСТО, ничего не сломано
  (`EXIT_CODE=1` = только порог покрытия 80%, не падения тестов).
- 🏁 **ВЕХА: вся «живая память» собрана (P0), за флагами, зелёная как единое целое.**

### 2026-05-31 — 📓 Working Notebook (RFC-0081 P0) + дедуп-модель настраиваемая
- Построен `core/working_notebook.py` (флаг `ENABLE_WORKING_NOTEBOOK`, без LLM, НЕ пишет в L3,
  `truth_status=USER_STATED`): MentalBlock-схема + turn-based decay (λ по типу, Раздел 8) +
  реактивация/mention-boost (Раздел 9) + состояния ACTIVE/WARM/COLD/DORMANT + `directive()` «думай, как я».
  `tests/test_working_notebook.py`: **8 passed**. Демо: «дом, бюджет 9млн, тепло, дерево» → 4 блока + директива;
  отвлёкся 6 сообщений → цель WARM, бюджет держится ACTIVE (constraint тухнет медленнее); повторил → воскресла.
- `semantic_dedup.default_embedder`: модель через env `SEMANTIC_DEDUP_MODEL` (многоязычная для ru↔en).
  Семантик-дедуп УЖЕ течёт в sleep-loop (при `ENABLE_SEMANTIC_DEDUP`+embedder → corroboration_mode=semantic).
- Graphiti (уточнение автору): ImmutableCore НЕ требует Graphiti (есть на SQLite); Graphiti добавляет
  communities (сильнее concept-L2) + fractal profile (L3-синтез) + граф-обход. См. `BACKENDS_AND_GRAPHITI.md`.

### 2026-05-31 — 🌙 Sleep Consolidation Loop (P0.3) — органы связаны в ОДИН ритм
- Построен `core/sleep_consolidation.py` (флаг `ENABLE_SLEEP_CONSOLIDATION`): цикл
  **corroboration → promotion → contradiction → decay**, отчёт `consolidation_report` (.to_dict()).
  Каждый шаг в try/except (сбой органа не валит цикл — Slow Path degraded).
- В `run_graduated_promotion` добавлен `corroboration_override` → цикл подаёт СЕМАНТИЧЕСКУЮ
  корроборацию (если включён ENABLE_SEMANTIC_DEDUP + есть embedder), иначе лексическую.
- Подключён в `run_consolidation` (диспетчер: **sleep > graduated > наивный**). `SleepTimeWorker`
  и `POST /memory/consolidate` получают полный цикл за флагом, прозрачно.
- `tests/test_sleep_consolidation.py`: **6 passed** (+22 promotion целы). Демо: t1 Observed→Supported,
  «дерево подходит»(Validated)→Contradicted (superseded by «не подходит»), отчёт со всеми стадиями.
- Decay над ФАКТАМИ честно `skipped_p0` (DecayOrchestrator targets Velum-синапсы/веса — P1).
- ✅✅✅ **ТРОЙКА P0 RFC-0082 ЗАКРЫТА:** P0.1 дедуп→корроборация · P0.2 противоречия · P0.3 sleep-loop.
  «Мозг во сне» работает: система сама себя приводит в порядок (за флагом).

### 2026-05-31 — ⚖️ Разрешение противоречий (P0.2) — память не «гниёт»
- Построен `core/contradiction_resolver.py` (аддитивно, флаг `ENABLE_CONTRADICTION_RESOLVER`, без LLM):
  субъект = claim без отрицания → «X» и «не X» попадают в одну группу; полярность считается на
  исходном claim; один субъект + противоположная полярность = противоречие; новее вытесняет старое.
  Matrix-safe: `Validated` старый → `Contradicted`; не-Validated → `requires_review` (не форсим); no-DELETE.
- `tests/test_contradiction_resolver.py`: **9 passed**. Демо: «дерево подходит»(Validated) +
  «дерево не подходит» → старое `Contradicted`, новое активно, ребро `superseded_by`.
- ✅ **Тройка P0 из RFC-0082 закрыта:** P0.1 дедуп→корроборация · P0.2 противоречия.
  Осталось P0.3 — sleep-loop (оркестратор, что свяжет promotion+dedup+contradiction+decay в один ритм).

### 2026-05-31 — 🧬 Семантический дедуп → корроборация (P0.1, по приоритету ChatGPT)
- Построен `core/semantic_dedup.py` (аддитивно, флаг `ENABLE_SEMANTIC_DEDUP`, без мутаций стора,
  graceful fallback на лексику): `cluster_by_meaning`, `compute_semantic_corroboration` (drop-in
  семантическая замена лексической `compute_corroboration`), `plan_dedup` (dry-run планы слияния, no-DELETE).
  `embed_fn` инъектируется → тесты детерминированны без загрузки модели.
- `tests/test_semantic_dedup.py`: **9 passed** (фейк-эмбеддер).
- Демо на реальной MiniLM: парафразы «car needs fuel»↔«cars require fuel»=**0.84**, «boiling»↔«water boils»=**0.90**,
  разные темы=**0.18**. Дубли сливаются → корроборация **2** → promotion `Observed→Supported`
  (лексика дала бы 1 → лишь Hypothesized). Связка дедуп→корроборация→обучение доказана.
- **НАХОДКА (voice=reality):** дефолт-порог 0.92 (из переписки) СЛИШКОМ строг для MiniLM → откалибровал
  на **0.78** (измерено; зазор «то же»0.84–0.90 vs «разное»0.18 огромный). ru↔en=0.22 → MiniLM не сольёт
  кросс-язык, нужна многоязычная модель (подтверждает находку First Light).

### 2026-05-31 — Демо «забывания» + фикс реального бага + Graphiti как опция
- Демо `decay_orchestrator` (умное забывание) вскрыло **реальный баг**: `AppSettings` без поля
  `salience_fsrs_protect_threshold` → orchestrator падал `AttributeError` (за флагом, никто не натыкался,
  как и баг пустого корпуса BM25). **Фикс:** добавил поле (default 0.95) в `feature_config.py`.
  `tests/test_decay_orchestrator_smoke.py`: **5 passed** (страж против регресса).
- Демо: обычный факт тускнеет (1.0→0.976/год), `ImmutableCore` + высокий salience **защищены**,
  частое вспоминание (выше stability) тускнеет медленнее. «Умное забывание» **теперь реально работает**.
- Donor Graphiti_fractal: переносить нечего; реально «взять» = мелочь `experience/models.py`
  (схема task-run + context-hash dedup) — опционально, 5 целей не двигает.
- По просьбе автора Graphiti НЕ выкидываем → `docs/BACKENDS_AND_GRAPHITI.md`: память сменная
  (sqlite дефолт / kuzu / graphiti+neo4j опц.); что Graphiti даёт сверх SQLite (communities=L2,
  fractal profile=L3, граф-обход, авто-извлечение связей), цена (сервер+LLM), когда что выбирать.

### 2026-05-31 — Аудит донора Graphiti_fractal-main: переносить НЕЧЕГО (V8.6 — суперсет)
- Сравнил `Documents/velantrim/Graphiti_fractal-main` (донор, 196 py) с V8.6. **Вывод: золота нет.**
  Все ПЕРЕНОСИМЫЕ модули уже в V8.6 (decay_orchestrator/fsrs/daad/vintage — байт-в-байт; salience/
  concept/velum/truth_gate — новее в V8.6). Уникальное в доноре (layers/l2-l3, knowledge/ingest,
  experience/writer, authorship, identity) — Graphiti/Neo4j/LLM-завязано → не для SQLite-дефолта V8.6.
- ⚠️ **КОРРЕКЦИЯ к раннему аудиту:** цели автора БОЛЬШЕ готовы в V8.6, чем казалось:
  • забывание → `core/decay_orchestrator.py` РЕАЛЬНО есть и подключён (flag `enable_decay_orchestrator`,
    цепочка ESM→DAAD→FSRS→Vintage→Salience, 0 LLM, SQLite) — не «unwired», как я писал раньше;
  • affordances → `core/affordance_linker.py` существует; intent → `dialogue_essence._detect_intent`;
    fractal L1→L2→L3 → `fractal_memory.py` (формальный, 19.5KB). Донор этого НЕ имеет вовсе.
- Graphiti_fractal = **предок/архив** V8.6, не новая линия. Вывод: не переносить, а ОЖИВЛЯТЬ V8.6.
- Мелочи-кандидаты (НЕ двигают 5 целей, опционально): `experience/models.py` (схема task-run +
  context-hash dedup), `local_episode_store.py` — проверить против `cognitive_store`/`storage`.

### 2026-05-31 — 🗺️ Карта-реконсиляция: дизайн живёт в 4 НЕсогласованных линиях
- По запросу «свести RFC-0080 + handoff в одну карту» прочитал переписку `Что надо-.txt`, handoff
  `OPENCLAW_…` и стратег-доки «От фрактала…». **Находка:** дизайн Velantrim разошёлся на 4 линии:
  🟢 CODE V8.6 (истина) · 🔵 переписка (RFC-0080/0081 Exocortex Mirror — **кода нет**) ·
  🟣 «Crystal/когнитивная» стратегия · 🟠 OpenClaw/Wildberries (**другой проект**, memory-fabric+Graphiti).
- **RFC-0080 как файла НЕ существует** — Essence Layer/WhyEngine/SituationModel только в переписке.
- Коллизии: нумерация слоёв (L1/L2/L3 значат РАЗНОЕ в каждой линии), каноническая формула (3 версии),
  имена (TruthGate↔TruthLayer, «Essence»×3, Observer×3, ConceptEmergence Engine↔Detector).
- Согласованное ядро (твёрдое): `Graph=Truth` · append-and-invalidate (no-DELETE) · `USER_STATED≠FACT`.
- Написан `docs/ARCHITECTURE_RECONCILIATION_MAP.md` — единый канон: слои по коду, объединённая формула,
  словарь имён, статус-карта (что РАБОТАЕТ / дизайн / другой проект). **Ждёт утверждения автором.**

### 2026-05-31 — 📐 RFC-0082 Sleep Consolidation Loop (по аудиту ChatGPT)
- ChatGPT прорецензировал мой инженерный аудит (9/10) и согласился: «не расширять — соединить
  существующие органы в единый sleep-cycle». Попросил оформить RFC-0082 (JSON-контракты + P0-тесты).
- Написан `docs/RFC-0082_Sleep_Consolidation_Loop.md`: Slow Path, дополняет RFC-0081 (Fast Path).
  Цикл: promotion → semantic dedup → corroboration → contradiction resolution → FSRS decay → re-clustering.
- Опора на РЕАЛЬНЫЕ модули V8.6 (`promotion_policy`/`knowledge_linker`/`consolidation_engine`/FSRS/
  `concept_emergence` уже есть) + 9 safety-инвариантов (no-DELETE, Truth Gate не обходится,
  feedback≠truth_status, идемпотентность, Slow-Path-only, dry_run).
- P0: `semantic_dedup→corroboration` (P0.1) + `contradiction_resolver` (P0.2) + sleep-loop за флагом
  `ENABLE_SLEEP_CONSOLIDATION` (P0.3). P1: decay-wiring, re-clustering, affordances, doc→facts.
- Это ДОКУМЕНТ (спека), не код — реализацию P0 делаем следующим шагом по слову автора.

### 2026-05-31 — 🎯 Линковщик v2: ориентация по типу + типизация рёбер
- **① Ориентация:** рёбра теперь идут low-tier→high-tier (`MATERIAL_SOURCE→PROCESS→FAILURE_MODE`).
  Развороты исправлены — напр. «хлопок —enables→ кардочесание» (было наоборот).
- **② Типизация** (детерминированно, без LLM): процесс→процесс = `precedes`; явный cue
  («вызывает/приводит к/leads to») = `causes`; иначе `enables`.
- На BATCH_001: 34 рёбра (21 `enables` + 13 `precedes`), направление cotton корректно.
  Essence-цепочка стала точнее: «Пшеница —enables→ Помол —precedes→ Просеивание».
- Тесты `test_knowledge_linker.py`: **11 passed** (+3: ориентация, precedes, causes).
- Честно: ПОЛНОЕ извлечение причинности из прозы (новые рёбра из текста claim, многоязычно) —
  следующий тир, нужен LLM/NLP. Здесь — детерминированный no-LLM срез (типы + текстовые cue).
- ⚠️ Допущение: концепт = средние сегменты id → правило рассчитано на 4-сегментные id реальных
  батчей (`domain.cat.concept.qualifier`); очень короткие id теряют лист-концепт (P0-ограничение).

### 2026-05-31 — 🔗 Линковщик «Связи → causal-рёбра» (закрыл находку №1 из First Light)
- Построен `core/knowledge_linker.py` (детерминированный, без LLM, stdlib): правило
  тег↔сегмент-id → направленное ребро `A —enables→ B` (валидный тип CausalGraph,
  `status=inferred`, conf 0.6). Аддитивно, рантайм/БД не трогает.
- Фильтры шума: концепт = СРЕДНИЕ сегменты id (лист-квалификатор отброшен → убрал
  «чечевица→пшеница»); широкие токены (>4 фактов) скипаются как категории.
- Тесты `test_knowledge_linker.py`: **8 passed**.
- **РЕЗУЛЬТАТ на реальном BATCH_001:** 36 рёбер; Essence-цепочка ОЖИЛА на настоящих данных:
  «Пшеница даёт зерно —enables→ Помол превращает зерно в муку —enables→ Просеивание…».
- Честно: структурное линкование приблизительно по НАПРАВЛЕНИЮ (часть рёбер развёрнуты,
  напр. cotton-обработка↔растение); истинная причинность из ТЕКСТА claim + ориентация по
  типу (`MATERIAL_SOURCE→PROCESS`) — следующий тиер. Но цепочки на реальных знаниях теперь возможны.

### 2026-05-31 — 🌅 First Light: смоук-тест Essence на РЕАЛЬНОМ батче (read-only)
Одноразовый тест (temp-стор, `data/velantrim.db` НЕ тронут, контент НЕ дополняли):
50 фактов из BATCH_001 → парсинг markdown-таблицы → загрузка+валидация → семантика + Essence.
**Что работает:**
- ✅ парсер markdown-таблицы → факты; 50/50 загружено и провалидировано;
- ✅ семантика на РЕАЛЬНЫХ русских знаниях: запрос «из чего делают ткань» (без слова «волокно»)
  → нашёл «Сизаль даёт волокно», «Лён даёт волокно» (dense 0.73/0.67). Поиск по смыслу работает;
- ✅ Essence выдал суть на реальных данных.
**Честные находки — что подготовить ДО заливки 5–10К:**
- [цепочки] батч-таблицы дают в «Связи» только теги-темы, НЕ типизированные рёбра факт→факт →
  цепочка пуста (gist-only). Нужен linking-проход `prereq/links → causal-рёбра`.
- [качество поиска] `all-MiniLM-L6-v2` англо-центричен; на русском часть хитов рыхлые
  (марена/паста). Для реального ingest → многоязычная модель (напр. `paraphrase-multilingual-MiniLM`).
- [синтез] Essence P0 берёт ТОП-факт как суть, не синтезирует поверх набора («ткань — из
  растительных волокон: лён, сизаль…»). Это LLM-композер (вершина), future work.
**Вывод:** петля переварила реальный формат; выявлены 3 дешёвые подготовки до масштаба. Контент не трогали.

### 2026-05-31 — Полный прогон «для чистоты» после серии правок pipeline ✅
- **700 passed, 0 FAILED, 17 skipped, 13 xfailed** (1205с / 20 мин, dense активен).
- Прирост +27 тестов с прошлого полного прогона (673→700): петля обучения (22) + Essence-расширение (5).
- Coverage `core/` = **57%**. Новые модули покрыты сильно: `essence.py` **99%**, `promotion_policy.py` **87%**.
- Подтверждено: семантика + петля обучения + Essence+causal-цепочка интегрированы ЧИСТО, ничего не сломано.
- `EXIT_CODE=1` = только порог покрытия 80% (не падения тестов).
- 🏁 Веха: весь сессионный прогресс зелёный как единое целое.

### 2026-05-30 — Causal-связи поданы в Essence: ответ стал ЦЕПОЧКОЙ 🔗🌿
- `generate_answer` (флаг `ENABLE_ESSENCE`) теперь тянет надёжные рёбра из `CausalGraph` через
  новый helper `pipeline._essence_relations_for`: только `known/inferred`, оба конца — в наборе
  фактов ответа; гипотетические (conf 0.35) исключены. Никогда не бросает (граф недоступен → []).
- Результат: ответ из «Суть: <факт>» стал «Суть: <gist> + Цепочка: A —causes→ B —enables→ C».
- Демо вживую: дрова→горение→тепло→дом собралось в цепочку с WhyTrace.
- Тесты: `test_essence.py` **26** (+3: фильтрация helper, <2 фактов, цепочка через generate_answer).
  (Дефолтный путь флаг-выкл не тронут — helper вызывается только внутри essence-ветки.)

### 2026-05-30 — Essence ПОДКЛЮЧЁН к ответу за флагом ENABLE_ESSENCE 🌿
- `generate_answer()`: флаг выкл → прежний `" | ".join` (бит-в-бит); флаг вкл → `compose_essence`
  → ответ «Суть: …» + структура essence (gist/roles/chain/WhyTrace) в результате.
  Канон соблюдён: Truth Gate/БД не тронуты, работаем только с Validated/Supported фактами.
- Проверено: `dialogue_essence.py` — ДРУГОЕ (граф диалога для веб-консоли SSE), не дублируем. ✅
- Тесты: `test_essence.py` 23 (+2 wiring), суммарно с `test_pipeline.py` — **55 passed**. Default join цел.
- ⚠️ Ограничение слоя: без causal-связей essence даёт лишь gist (без цепочки). Цепочка появится
  при подаче рёбер `causal_graph` → следующий шаг. Включить: `ENABLE_ESSENCE=1`.

### 2026-05-30 — Петля обучения ПОДКЛЮЧЕНА за флагом (option «б») 🔌
- `run_consolidation()` теперь диспетчер по `ENABLE_GRADUATED_PROMOTION`:
  • выкл → наивный `ConsolidationEngine` (fallback, прежнее поведение бит-в-бит);
  • вкл  → градуированная петля `promotion_policy`.
  Оба возвращают `.to_dict()` → `SleepTimeWorker` и `POST /memory/consolidate` работают без изменений.
- Тесты: `test_promotion_policy.py` **22** (+2 диспетчер-теста), `test_sprint1_integrity` (наивный путь цел),
  `test_sleep_time_worker` **37** — всё зелёное.
- **Как включить в runtime:** `ENABLE_GRADUATED_PROMOTION=1` в `.env` (+ `CONSOLIDATION_ON_SLEEP=1`
  для авто-цикла в SleepTimeWorker). По умолчанию выкл → ничьё поведение не меняется.

### 2026-05-30 — Петля обучения P0 (градуированный промоушен) 🫀
- Нашёл существующий `core/consolidation_engine.py` — но правило НАИВНОЕ: `Observed→Validated`
  при `confidence>=0.75`. Подтверждено вживую: `random_blog` conf 0.8 → сразу Validated («штамп»).
- Построил `core/promotion_policy.py` (аддитивно, флаг `ENABLE_GRADUATED_PROMOTION`, без LLM):
  лестница `Observed→Hypothesized→Supported→Validated` по СИГНАЛАМ — корроборация (N разных
  источников), доверие источнику (I98), выдержка во времени, противоречия (демоушен в Contradicted).
  Один шаг за прогон → факт «дозревает» за сессии. `tests/test_promotion_policy.py`: **20 passed**.
- Контраст (демо): тот же `random_blog` теперь → `Hypothesized` (честно, не истина); а мысль,
  подтверждённая 3 источниками, climbs `Observed→Supported→Validated` за 2 прогона.
- НЕ тронуты `consolidation_engine.py` и stable `/query`. Wiring — отдельное решение автора.

### 2026-05-30 — Полный прогон тестов «для чистоты» (после семантики + фиксов)
- ✅ **673 passed, 0 FAILED, 17 skipped, 13 xfailed** (1145с / 19 мин, dense активен).
- Coverage `core/` = **56.64%** (15285 stmts). Новый `core/essence.py` — **99%** покрытие.
- Фикс пустого корпуса BM25 подтверждён на ВСЁМ наборе; ничего не сломано.
- ⚠️ Замечено: уже есть `core/dialogue_essence.py` (133 stmts, 83%) — возможен overlap с моим
  `essence.py`; проверить при wiring (не дублировать).

### 2026-05-30 — Включён семантический поиск (+ найден и починен баг)
- Установлены `rank-bm25` (настоящий BM25 Okapi вместо naive TF-IDF) и `sentence-transformers`+`torch`
  (модель `all-MiniLM-L6-v2`). Зависимости уже были объявлены в pyproject extra `retrieval`
  → воспроизводимо: `pip install -e ".[retrieval]"`.
- **Доказано:** запрос «vehicle» (нет общих слов с «car») → dense нашёл «A car needs fuel to run»,
  BM25 в одиночку — пусто. Через весь pipeline: провалидированный факт + «vehicle» → корректный ответ.
  Система теперь ищет по СМЫСЛУ, а не по дословному совпадению.
- **Регрессия найдена и устранена:** активация `rank-bm25` вскрыла `ZeroDivisionError` на пустом
  корпусе (`BM25Okapi([])` → avgdl=0/0). Фикс в `core/hybrid_retriever.py:_build_index`
  (guard на пустой корпус + broad except). `test_hybrid_retriever.py`: **21 passed**.
- **Урок:** graceful degradation скрывал баг — он проявился, только когда зависимость реально установлена.

### 2026-05-30 — Живая диагностика системы памяти (как она работает)
Прогнал ядро памяти вживую (изолированная temp-БД, real `data/velantrim.db` не тронут).
**Подтверждено, что работает как задумано:**
- Ingestion → факт входит в `Observed`, bi-temporal автозаполнен.
- ESM-лестница `Observed→Supported→Validated` только через матрицу, с провенансом (who/from/when).
- Нелегальный переход `Validated→Observed` блокируется; Ring Zero (`VALUES_CORE`) неизменяем;
  no-DELETE (`invalidate_edge` ставит `t_*_end`); time-travel `get_fact_at` работает.
- **ГЛАВНОЕ (Test B):** система отвечает ТОЛЬКО из `Validated`. Observed-факт → пустой ответ
  «Guardian: FactsPack пустой»; после promote→Validated → реальный ответ. Анти-галлюцинация в действии.

**Находки для доработки (evidence-based):**
- [HIGH] Нет авто-промоушена: факты висят в `Observed` навсегда → на холодном сторе система МОЛЧИТ.
  Нужен learning/consolidation loop (корроборация/доверие источнику/время → Supported → Validated).
- [MED] Подсказка «Consider using EXPLORATION mode» вводит в заблуждение — EXPLORATION тоже исключил факт.
- [MED] dev-mock (5 фактов) — тупик: пустой ответ во всех режимах. Ложное впечатление «ничего не работает».
- [MED] Retrieval деградирован: `rank-bm25` и `sentence-transformers` не установлены → naive TF-IDF, без semantic.

### 2026-05-30 — Essence Layer P0 (первый строительный шаг)
- Создан `core/essence.py` (детерминированный, stdlib-only, за флагом `ENABLE_ESSENCE`).
  Соблюдает 5 правил канона: не трогает Truth Gate/`/query`, gist только из
  Validated/Supported, не скрывает uncertainty, хранит WhyTrace, без LLM/«личности».
- Создан `tests/test_essence.py` — 21 тест. Поймал и пофиксил баг дизайна:
  цепочка смысла теперь строится **от корневой причины**, а не от факта-сути
  (соответствие канону «причина → механизм → вывод»). Итог: **21 passed**.
- Модуль аддитивен и изолирован (0 импортов из `core/`) → не влияет на существующие тесты.

### 2026-05-30 — Документация ↔ реальность + verified baseline
- Коммит `e74e7eb`: вписаны ПРОВЕРЕННЫЕ числа прогона (652 passed / 0 failed / 56%)
  вместо оценочных «~87% / все зелёные». Поправка: прежнее сомнение «зелёному не верить»
  было основано на чужих артефактах (проект `v8_5_1`); это дерево реально чистое.
- Коммит `521b792`: синхронизированы устаревшие заявления — число тестов (256→610 функций),
  D-1 («5 фактов» → dev-mock за `VELANTRIM_DEV_MOCK`), версия v8.4.0→v8.6.0 в OVERVIEW/LIMITATIONS.

### 2026-05-30 — git как сеть безопасности
- Коммит `1de0c7e`: `git init` в `VELANTRIM_ExoCortex_V8.6` + усиленный `.gitignore`
  (логи, tmp, `*.exe/*.zip`, `.tools/`, `data/backups/`). 365 файлов, без секретов
  (корневой `.env` с `dev-change-me` + `ALLOW_OPEN` исключён).

### 2026-05-30 — глубокий аудит (6 направлений)
- Безопасность: код чистый (нет eval/exec/pickle/SSRF), но дефолты открыты
  (`ALLOW_OPEN=true`, ключ `dev-change-me`, незащищённый `/telegram/webhook`, открытый Swagger).
- Корректность ядра: инварианты ESM/Ring Zero/no-DELETE соблюдены; split-brain L0↔L1 реален
  и хуже доков (порядок L0→L1); `CoherentCache` написан, но не подключён.
- Качество: `server.py` god-file (3510 строк, 78 роутов); 36% обработчиков молча глотают ошибки.
- Гигиена: нет git (исправлено), 162 МБ карантина к удалению, конфликт версий v8.6 vs v8.17.9.

---

## ⏭️ Следующий шаг (для возобновления)

**Essence-цепочка ✅ готова.** Возможные следующие шаги (выбор автора):
  • ingest курируемых знаний (`docs/knowledge/world_skills_core`) → `prereq/links` становятся
    рёбрами CausalGraph → цепочки на РЕАЛЬНОЙ базе, а не на демо-фактах;
  • семантическая корроборация для петли обучения (эмбеддинги вместо дословного совпадения);
  • LLM-композер поверх P0 (креативный синтез «вершина»);
  • прогнать полный набор тестов для чистоты после серии правок pipeline.

---

**Решение по wiring петли обучения (для автора).** `promotion_policy.py` готов и протестирован,
но НЕ подключён к runtime (флаг `ENABLE_GRADUATED_PROMOTION` выкл, аддитивно). Варианты:
  (a) заменить наивный `ConsolidationEngine` в `SleepTimeWorker`;
  (b) добавить как альтернативу за флагом (безопаснее всего);
  (c) объединить логику.
Улучшения сверху: семантическая корроборация (sentence-transformers уже стоит — считать
«тот же смысл» по эмбеддингам, а не только по нормализованному тексту); заменить `" | ".join`
на Essence; починить подсказку EXPLORATION; ingest курируемых знаний (приходят валидными по KNOWLEDGE_0).
