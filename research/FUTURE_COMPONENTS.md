# 🔬 Research: Future Components for Velantrim ExoCortex

> Источник идей: **HYPERIA V6 «Synapse»** · `HYPERIA_V6_SYNAPSE.md`
> Статус: **не реализованы, исследовательский интерес**
> Правило: **всё что здесь описано — не нужно прямо сейчас. MVP Velantrim покрывает эти задачи существующим кодом. Если объём данных вырастет на порядок — возвращаемся к этому документу.**

---

## 🧮 KDE — Kernel Density Estimation (Entity Layer)

**Что это:**
MAGMA-style статистический метод выделения ГЛАВНЫХ сущностей из потока. Не захламляет граф второстепенными сущностями — только те, что статистически значимы. Работает как фильтр: «эта сущность упоминается достаточно часто и консистентно → сохраняем; эта мелькнула один раз → пропускаем».

**Где применить:**
- Ingestion pipeline — фильтрация шума при массовой загрузке (PDF, архивы чатов)
- Umwelt — отбор объектов для перцепторов (воробью не нужен концепт «термодинамика»)
- Graph Health — автоудаление orphan-сущностей с низкой плотностью

**Когда понадобится:**
При >10 000 фактов. На 500 фактах ручной/ETIR-разбор достаточен. KDE нужен когда ingestion идёт потоком и ручной контроль невозможен.

**Что уже покрывает в V8.7:**
`core/etir.py` — Entity-To-Intent Relations делает 70% этой работы. `core/concept_emergence.py` — Hebbian-рождение концептов отсеивает шум.

---

## 🎯 MemoryRouter — Live-переключение бэкендов без перезапуска

**Что это:**
Агент меняет графовую БД на лету: Neo4j → FalkorDB → KuzuDB → LadybugDB без остановки сервера. Абстракция `MemoryBackend` с горячей заменой реализации.

**Где применить:**
- Production migration — переезд с Kuzu на LadybugDB без downtime
- A/B testing бэкендов — сравнение latency/throughput
- Fallback — если Neo4j упал → автоматически sqlite

**Когда понадобится:**
При production-деплое с несколькими бэкендами. MVP использует один бэкенд (SQLite + LadybugDB) — переключать нечего.

**Что уже покрывает в V8.7:**
`core/storage_facade.py` — фабрика бэкендов с ENV-выбором. `STORAGE_BACKEND=sqlite|ladybug|kuzu|neo4j`. Переключение через рестарт (5 секунд). MemoryRouter даёт горячую замену (0 секунд).

---

## 🔍 Qwen3-Reranker — Cross-encoder Post-MMR

**Что это:**
После MMR (Maximal Marginal Relevance) — модель перечитывает пару (запрос + документ) вместе и даёт финальную оценку релевантности. #1 в MTEB Multilingual benchmark. +8-12% точности retrieval.

**Где применить:**
- HybridRetriever — как финальный rerank после RRF fusion
- Question answering — переранжирование кандидатов перед FactsPack

**Когда понадобится:**
При >5 000 фактов, когда BM25 + Dense + RRF начинают давать шум. На 500 фактах RRF достаточно точен.

**Что уже покрывает в V8.7:**
`core/hybrid_retriever.py` — CrossEncoderReranker уже есть (ms-marco-MiniLM-L-6-v2). Qwen3 — более свежая модель с лучшим качеством на русском. Замена — 1 строка: поменять название модели.

---

## 📑 IndexRAG — Cross-doc Multi-hop без LLM

**Что это:**
Пре-индексация «мостовых» фактов между документами. Факт A из документа 1 и факт B из документа 2 связаны через общую сущность — IndexRAG создаёт bridge-узел заранее, в Slow Path. При query не нужен LLM для multi-hop — мосты уже посчитаны. +4.6 F1 на multi-hop вопросах.

**Где применить:**
- Knowledge ingestion — при загрузке нового документа автоматически ищутся мосты с существующими
- Cross-domain retrieval — поиск связей между разными областями знаний

**Когда понадобится:**
При >50 документов и запросах вида «как открытие X в биологии повлияло на область Y в инженерии?». На 5 документах мосты видны и так.

**Что уже покрывает в V8.7:**
`core/cross_domain.py` — 6 предопределённых мостов между доменами. `core/causal_graph.py` — 15 типов связей, включая `analogous_to`. `core/essence.py` — Gist Synthesizer находит суть без LLM.

---

## 🕸️ AGRAG — Статистический подграф без галлюцинаций

**Что это:**
MCMI (Markov Chain Monte Carlo Inference) — статистический метод построения подграфа. В отличие от LLM-based графов, AGRAG строит ТОЛЬКО статистически значимые связи. Никаких «LLM придумал связь». Только то, что подтверждено данными.

**Где применить:**
- Causal graph — автоматическое нахождение причинных связей из ingestion
- Cross-domain — мосты между доменами на основе статистики, а не правил

**Когда понадобится:**
При >10 000 фактов и желании автоматически строить causal graph из сырых данных. Сейчас causal graph строится вручную или через LLM-экстракцию.

**Что уже покрывает в V8.7:**
`core/causal_graph.py` — 15 типов связей с knowledge_status. `core/concept_emergence.py` — Hebbian-статистика co-occurrence. `core/graph_lab.py` — NetworkX-анализ графа (centrality, communities, cycles). AGRAG — следующий шаг: автоматическое построение графа из сырых данных без LLM.

---

## 🔄 CRAG — Corrective RAG (оценка качества retrieval)

**Что это:**
После retrieval — классификатор оценивает каждый результат: correct / incorrect / ambiguous. Если incorrect → fallback к web-поиску или другому источнику. Если ambiguous → дополнительный retrieval с уточнённым запросом.

**Где применить:**
- Fast Path — после HybridRetriever, перед FactsPack. Отсев нерелевантного.
- Observer — метрика качества retrieval (сколько correct/incorrect/ambiguous)

**Когда понадобится:**
При >1 000 фактов, когда retrieval начинает возвращать шум. На 500 фактах BM25 + Dense + RRF возвращает релевантное в 95% случаев.

**Что уже покрывает в V8.7:**
`core/truth_gate.py` — фильтрует факты по confidence и contradictions. `core/output_faithfulness.py` — проверяет ответ LLM против фактов. `core/observer.py` — мониторит drift и противоречия. CRAG — более тонкий фильтр на уровне retrieval, а не truth.

---

## 🔐 ReRAG — Multi-user Access Control

**Что это:**
Каждый пользователь видит ТОЛЬКО свою память. Deny by default. Фильтр по `owner_user_id` на уровне retrieval и записи. Изоляция между пользователями — даже в одной БД.

**Где применить:**
- Multi-user режим — несколько пользователей в одной инсталляции Velantrim
- API — эндпоинты с авторизацией по user_id

**Когда понадобится:**
Когда Velantrim станет multi-user сервисом. MVP — personal mode (один пользователь). ReRAG не нужен пока нет второго пользователя.

**Что уже покрывает в V8.7:**
API key авторизация (`VELANTRIM_API_KEY`). `core/goal_stack.py` — цели привязаны к `user_id`. `core/working_notebook.py` — блокнот привязан к пользователю. ReRAG — системный уровень изоляции (нельзя случайно показать чужие факты).

---

## 📊 Когда возвращаться к этому документу

| Триггер | Какие компоненты становятся нужны |
|---------|----------------------------------|
| >10 000 фактов | KDE, IndexRAG, CRAG |
| >50 документов | IndexRAG, AGRAG |
| Multi-user режим | ReRAG |
| Production с несколькими бэкендами | MemoryRouter |
| Retrieval accuracy <90% | Qwen3-Reranker |
| Автоматическое построение графа из сырых данных | AGRAG |
| Нужен multi-branch reasoning с верификацией шагов | BranchManager, StepVerifier |
| Нужна полная сессионная история решений | L15 Observer / Diary |
| Нужна консолидация диалогов в финальную суть | Conversation Consolidation (chat_id binding) |
| Ingestion документов >10 страниц | Semantic Chunking + Overlapping |

---

## 🧭 Branch Manager — Multi-branch Reasoning

**Что это:** вместо выбора ОДНОЙ стратегии (Thompson Sampling) — запуск 2-3 параллельных веток рассуждения. Каждая ветка использует разный retrieval, разный mode (engineer/scientist/critic/planner/teacher), разную стратегию. Результаты сравниваются. Выбирается лучший.

```
Query → Mode Selector (engineer/scientist/critic/planner/teacher)
      → Branch Manager запускает 2-3 параллельные ветки
            → Ветка 1: retrieval + causal_chain + PRECISION mode
            → Ветка 2: retrieval + graph_expansion + CREATIVE mode
            → Ветка 3: retrieval + procedural + PRACTICAL mode
      → Step Verifier проверяет логику каждого шага
      → Synthesizer сравнивает ветки, выбирает лучший ответ
      → Writeback: запоминает какая ветка сработала для какого типа запроса
```

**Где применить:**
- Для сложных запросов, где одна стратегия может дать неполный ответ
- Когда Thompson Sampling даёт низкую уверенность — запустить multi-branch
- Для противоречивых тем — увидеть картину с разных сторон

**Когда понадобится:**
При запросах требующих multi-perspective анализа. На простых запросах Thompson Sampling достаточно.

**Что уже покрывает в V8.7:**
Thompson Sampling выбирает одну лучшую стратегию. ModeRouter даёт 3 режима тона. Но нет параллельного анализа с разных углов и сравнения веток.

---

## 🧪 Step Verifier — проверка логики шагов

**Что это:** проверяет каждый шаг reasoning ДО продолжения. Не проверяет факты (это TruthGate) — проверяет ЛОГИКУ: «корректен ли переход от шага 2 к шагу 3?», «не нарушена ли причинная цепочка?», «есть ли логическая ошибка в рассуждении?»

```
Reasoning Trace:
    Step 1: Retrieve факты → ✅ факты есть
    Step 2: Связать причинной цепочкой → ⚠️ Step Verifier: связь слабая
    Step 3: Сгенерировать ответ → ❌ Step Verifier: нельзя — шаг 2 не пройден
```

**Отличие от TruthGate:**
- TruthGate проверяет: «правда ли факт?» (эпистемический контроль)
- Step Verifier проверяет: «правильно ли построено рассуждение?» (логический контроль)

**Где применить:**
- После каждого шага reasoning перед переходом к следующему
- Для сложных запросов где важна правильность цепочки (медицина, право, наука)

**Когда понадобится:**
Когда система начинает давать логически противоречивые ответы. Сейчас TruthGate и OutputFaithfulness ловят это постфактум.

**Что уже покрывает в V8.7:**
ResponseAudit проверяет ответ после генерации. GCR-фильтр проверяет supported/unsupported. Но нет логической верификации промежуточных шагов рассуждения.

---

## 📖 L15 Observer / Diary — сессионный дневник

**Что это:** пассивный наблюдатель сессий. Фиксирует:
- **open_loops** — незавершённые темы, вопросы без ответа
- **decisions** — принятые решения и их контекст
- **keywords** — ключевые темы сессии
- **resume_summary** — краткая выжимка сессии для следующего запуска

```
Сессия #47 (2 июня 2026, 14:00-15:30)
    open_loops: ["нужно проверить Kuzu→LadybugDB миграцию"]
    decisions: ["выбрали DuckDB для аналитики", "отложили Graphiti до 100K фактов"]
    keywords: ["архитектура", "хранение", "миграция", "DuckDB"]
    resume_summary: "Обсуждали storage-архитектуру. Решили добавить DuckDB. Остался открытым вопрос миграции Kuzu."
```

**Отличие от sleep_time_worker:**
- sleep_time_worker: консолидирует ПАМЯТЬ (продвигает факты, чистит мусор)
- L15 Observer: консолидирует ИСТОРИЮ СЕССИЙ (дневник, контекст для восстановления)

**Где применить:**
- При старте новой сессии — загрузить resume_summary вместо всей истории
- Для долгих проектов — видеть прогресс: что решено, что открыто

**Когда понадобится:**
Когда количество сессий превышает 50 и восстановление контекста требует много токенов.

**Что уже покрывает в V8.7:**
CoreMemoryBlocks хранит профиль. ConversationBuffer хранит диалог. Но нет структурированного дневника сессий с open_loops/decisions/resume.

---

## ⚖️ Adaptive Truth Thresholds — контекстно-адаптивные пороги TruthGate

**Что это:** вместо фиксированных CognitiveModes — пороги TruthGate меняются динамически в зависимости от контекста диалога и реакции пользователя.

```
Зелёная зона (доверие):
    тема созидания (экология, здоровье, строительство)
    + пользователь подтверждает полезность ответа
    → confidence порог снижается с 0.7 до 0.5
    → Hypothesized факты допускаются
    → Guardian переходит в режим «соавтора»

Красная зона (верификация):
    тема новая, сомнительная, противоречит канону
    → confidence порог повышается до 0.9
    → требуется 5+ evidence
    → Guardian задаёт уточняющие вопросы (Зачем? Откуда?)
    → все unsupported claims → [HYPOTHESIS]
```

**Отличие от CognitiveModes:**
- CognitiveModes: фиксированные режимы (PRECISION/BALANCED/EXPLORATION/CREATIVE). Пользователь выбирает явно
- Adaptive Thresholds: пороги меняются АВТОМАТИЧЕСКИ по контексту. Тема → порог. Реакция пользователя → коррекция

**Где применить:**
- TruthGate.evaluate() — вместо фиксированного `min_confidence` читать динамический порог
- pipeline enrichment — перед TruthGate определить «зону» темы по domain/cross_domain
- L4 самообучение — если пользователь подтвердил полезность, снизить порог для этой темы

**Когда понадобится:**
Когда один CognitiveMode не покрывает разнообразие тем. Для созидательных тем (экология, искусство) — мягкий порог. Для научных (медицина, право) — жёсткий.

**Что уже покрывает в V8.7:**
`promotion_policy.py` — правила промоута. CognitiveModes — 4 фиксированных режима. `truth_policy.py` — modal guard. Но нет динамической адаптации порога по контексту темы и реакции пользователя.

---

## 🕰️ L14 Chronotope — временная проверка решений

**Что это:** проверяет НЕ «правильное ли решение», а «своевременно ли». Ортогонально TruthGate — тот проверяет истинность, Chronotope проверяет время.

```
L4 хочет принять стратегическое решение
    → L14 Chronotope проверяет:
        - время суток? (3:00 ночи → DEFER: иди спать, решение утром)
        - фаза проекта? (данные ещё не собраны → WAIT: рано)
        - конфликт с календарём? (уже запланировано → CONFLICT)
        - сезонность? (зимний проект обсуждается летом → NOTE: не сезон)
```

**Влияние на систему:**
- ⭕ Может DEFER reasoning (отложить до утра / до сбора данных)
- ❌ НЕ пишет в память (эфемерный контекст)
- 🌀 Косвенно влияет на ответы через тайминг

**Где применить:**
- Pipeline — перед L4 Reasoning: `if chronotope.defer_reasoning() → return defer_message`
- SleepTimeWorker — в 3:00 ночи послать сигнал Chronotope о начале нового цикла
- Проектные слои L7-L9 — синхронизация с долгосрочными планами

**Когда понадобится:**
Когда система начинает принимать решения без учёта времени и контекста. Для долгосрочных проектов где важен тайминг.

**Что уже покрывает в V8.7:**
Ничего. Все решения принимаются когда угодно. TruthGate проверяет истинность. MetaSupervisor проверяет здоровье. Нет временной проверки решений.

---

## ❓ L16 Dialogue Orientation — пред-фильтр запросов

**Что это:** фильтрует запросы ДО reasoning — экономит токены на бессмысленных запросах. Не проверяет качество ответа (ResponseGuardian) — проверяет СТОИТ ЛИ отвечать.

```
Запрос пользователя → L16 Dialogue Orientation:
    - BLOCK: спам, оскорбления, боты → «я не отвечаю на это»
    - ASK_IDENTITY: неизвестный пользователь → «представься пожалуйста»
    - ASK_CLARIFY: бессвязный текст → «я не понял вопрос, уточни»
    - FLAG: скрытая манипуляция → пометить для Observer
    - ALLOW: нормальный запрос → пропустить в L4
```

**Отличие от ResponseGuardian:**
- ResponseGuardian: проверяет ОТВЕТ после LLM (токены уже потрачены)
- L16: проверяет ЗАПРОС до reasoning (токены НЕ потрачены)

**Влияние на систему:**
- ⭕ Блокирует reasoning ДО прояснения
- ⭕ Временная память (TTL=6 месяцев) для неизвестных контактов
- ❌ НЕ принимает решений о содержании ответа

**Где применить:**
- Fast Path — самый первый шаг, до pipeline
- API middleware — проверка на уровне HTTP до передачи в обработчик

**Когда понадобится:**
При публичном API или большом количестве запросов от неизвестных источников. Экономия токенов на спаме и мусоре.

**Что уже покрывает в V8.7:**
`rate_limit.py` — ограничение частоты запросов. `response_guardian.py` — проверка ответа. `security/middleware` — базовые проверки. Но нет семантического пред-фильтра (спам vs нормальный запрос vs требуется уточнение).

---

## 🎯 Embedding-based Routing — замена 29 if/elif на product-key lookup

**Что это:** вместо 29 паттернов `if "почему" in query → WHY` — embedding запроса сравнивается с центроидами формул по косинусному расстоянию. O(1) поиск вместо O(n) перебора.

**Источник:** HMA Internal Router / PEER product-key routing (Meta, 2024). PDF: «продукт-ключи доказывают что memory retrieval и expert routing — одна математическая операция».

**Где применить:**
- `question_formula.py` — заменить rule-based классификатор на embedding-based
- `ModeRouter` — расширить 3 режима до динамической маршрутизации

**Когда понадобится:**
Когда 29 формул перестают покрывать разнообразие запросов (>100 различных паттернов). Embedding-based routing не требует пополнения списка if/elif.

**Что уже покрывает в V8.7:**
`question_formula.py` — 29 rule-based формул. Работает хорошо на 29 типах. Не масштабируется на 100+.

---

## 📐 Learnable Retrieval Weights — адаптивные α/β/γ для HybridRetriever

**Что это:** вместо фиксированных весов BM25 + Dense + RRF — адаптивные веса, которые обновляются через Prediction Error. На DEFINE-запросах BM25 получает больший вес. На WHY — causal graph. На HOW — procedural.

```
HMA_Attn = α·BM25 + β·Dense + γ·Causal
α, β, γ ∈ [0,1], α+β+γ = 1

Обновление:
    если ответ пользователя = «не релевантно» → штраф тому компоненту, который дал этот результат
    если ответ = «отлично» → усиление веса компонента
```

**Источник:** HMA Hybrid Attention формула. PDF: «α, β, γ — learnable веса. Router loss: CrossEntropy(predicted, true) + KL-дивергенция для баланса.»

**Где применить:**
- `hybrid_retriever.py` — добавить адаптивные веса с обновлением через feedback
- `reasoning_bank.py` — использовать Thompson Sampling для выбора комбинации весов

**Когда понадобится:**
Когда фиксированные веса RRF перестают давать хорошие результаты на разных типах запросов.

**Что уже покрывает в V8.7:**
RRF fusion с фиксированным k=60. `retrieve_5stage()` — фиксированная последовательность этапов. Нет обратной связи для адаптации весов.

---

## 📦 Three-tier Session Persistence — персистентность между сессиями

**Что это:** три уровня сохранения состояния сессии с разной степенью сжатия.

```
Tier 1: Structured Slots → SQLite (CoreMemoryBlocks)     ← быстрое восстановление
Tier 2: SSM State → Infini-Attention компрессия          ← сжатое состояние WM
Tier 3: KV-cache → LMCache/Mooncake + MLA (15× сжатие)   ← точное состояние
```

**Адаптация для V8.7:**
У нас уже есть Tier 1 (`CoreMemoryBlocks` → SQLite) и Tier 3 (ImmutableCore снапшоты). Не хватает Tier 2 — сохранения SSM-состояния (LSM state) между сессиями. Сейчас LSM-состояние теряется при перезапуске.

**Источник:** HMA session persistence. PDF: «Infini-Attention: фиксированная матрица key_dim×value_dim достигает 114× сжатия vs полный KV cache.»

**Где применить:**
- `lsm_prediction.py` — добавить `save_state()` / `load_state()`
- `sleep_time_worker.py` — checkpoint LSM перед выключением

**Когда понадобится:**
Когда важно сохранять «ритм» пользователя между сессиями без перезапуска.

**Что уже покрывает в V8.7:**
`CoreMemoryBlocks` сохраняет профиль. `ImmutableCoreScheduler` сохраняет снапшоты графа. Но LSM-состояние (ритм сессий) теряется при перезапуске.

---

## 📝 Conversation Consolidation — двухфазный блокнот диалога

**Что это:** связка `chat_id` между WorkingNotebook (реал-тайм) и GistSynthesizer (пост-фактум). После завершения диалога — автоматическая консолидация в финальную суть.

**Источник:** Rosebud AI Journal (апрель 2026). Grok: «во время чата — временный блокнот → после чата — финальная суть с анализом логики разговора».

```
Фаза 1 (реал-тайм):
    WorkingNotebook каждые 4-5 сообщений извлекает key_insights
    Сохраняет во временный блокнот с chat_id

Фаза 2 (после завершения):
    GistSynthesizer читает временный блокнот
    Анализирует логику: от чего начали → какие вопросы → к чему пришли
    Создаёт финальную запись с:
        - main_topic, user_goal, key_insights, conclusion
        - related_chats (ссылки на похожие диалоги)
        - chat_id для трассировки
```

**Где применить:**
- `working_notebook.py` — добавить `chat_id` + двухуровневую структуру (короткий + полный блокнот)
- `essence/gist.py` — авто-вызов при завершении сессии для финальной консолидации
- SleepTimeWorker — периодическая консолидация блокнотов в долгосрочную память

**Когда понадобится:**
При 10+ диалогах когда пользователь хочет спросить «что мы обсуждали по RAG» и получить структурированный ответ, а не кучу разрозненных фактов.

**Что уже покрывает в V8.7:**
`working_notebook.py` — live mirror диалога. `essence/gist.py` — Gist Synthesizer. `CoreMemoryBlocks` — постоянный контекст. Но нет явной связки через `chat_id` и нет двухфазной консолидации (реал-тайм → финальная суть).

---

## ✂️ Semantic Chunking — умное нарезание документов

**Что это:** при ingestion резать документы не по фиксированному размеру (512 токенов), а по смыслу. Когда тема меняется — новый chunk. Соседние чанки перекрываются на 20-30%.

**Источник:** Rosebud AI Journal (апрель 2026). «Переход с фиксированных chunks на semantic + overlapping даёт заметный прирост качества почти без лишней сложности.»

```
Фиксированные чанки:     [======512 токенов======][======512======]
Semantic чанки:          [====тема A====][==тема B==][======тема C======]
                         [<- 30% overlap ->]
```

**Где применить:**
- `file_parsers/file_ingester.py` — добавить semantic chunking перед extraction
- `meaning_parser.py` — улучшить качество gist для каждого чанка

**Когда понадобится:**
При ingestion документов >10 страниц. Фиксированные чанки теряют смысл на границах тем.

**Что уже покрывает в V8.7:**
`file_parsers/` — 12+ парсеров с базовым chunking. Но без semantic boundary detection.

---

## 🗂️ Neural Blackboard Pattern — единый канал записи в L3 (I97)

**Что это:** все модули пишут в L3 ТОЛЬКО через BlackboardBus — абстрактный канал с сигналами. Прямой Cypher CREATE/SET запрещён. Модули становятся readers/writers через адаптеры.

**Источник:** V9 Final §2.2. van der Velde & de Kamps, *Neural blackboard architectures*, 2006.

```
Velum → BlackboardAdapter → BlackboardBus → L3 Repository → Neo4j
Etir  → BlackboardAdapter ↗
Observer → BlackboardAdapter ↗
```

**Где применить:**
- Рефакторинг 6 модулей (Velum, Etir, Observer, ReasoningBank, FSRSWorker, ConceptEmergence)
- Замена прямых write-вызовов на сигналы BlackboardBus

**Когда понадобится:**
Когда количество модулей с прямым доступом к L3 превышает 10. Blackboard снижает coupling.

**Что уже покрывает в V8.7:**
`write_gate.py` — единственная точка входа для новых фактов. Но модули всё ещё вызывают `store_fact()` напрямую, а не через сигналы. Blackboard — следующий уровень абстракции.

---

## 🔀 DecayOrchestrator — унификация decay-стратегий

**Что это:** единый оркестратор для FSRS + ACT-R + Hebbian (Velum) + DAAD + Salience. Решает проблему интерференции — когда несколько decay-механизмов конфликтуют на одном факте.

**Источник:** V9 Final §2.3. Priority chain: ESM → DAAD → FSRS → Vintage → Salience.

```
DecayOrchestrator.apply(fact):
    1. ESM проверка (ImmutableCore → skip decay)
    2. DAAD: λ_eff = Σ(dᵢ × λᵢ) по доменам
    3. FSRS: R = (1 + 19/81 × t/S)^(-0.5)
    4. Vintage: дата публикации → decay_factor
    5. Salience: emotional_salience > 0.85 → Ring Zero protection
    6. Результат: unified_attention_weight
```

**Где применить:**
- `decay_orchestrator.py` — уже есть скелет
- Все модули decay переходят на вызов через оркестратор

**Когда понадобится:**
Сейчас decay-модули работают независимо. При росте графа интерференция станет заметной.

**Что уже покрывает в V8.7:**
`decay_orchestrator.py` — скелет есть. `daad.py` — domain-aware. `fsrs.py` — power-law. `salience.py` — значимость. Но нет координации между ними.

---

## 📋 Formal Component Registry — реестр компонентов в YAML

**Что это:** вместо markdown-документов — `component_registry.yaml` с 37 компонентами, каждый с baseline_status / verification_layer / v9_target_status / evidence / dependencies.

**Источник:** V9 Final §3. 37 компонентов с трехуровневым статусом (🟢/🟡/🔴) и верификацией (✅/⚠️).

**Где применить:**
- `component_registry.yaml` в корне проекта
- CI проверяет что статус компонента соответствует реальности

**Когда понадобится:**
При 50+ компонентах когда markdown перестаёт быть управляемым.

**Что уже покрывает в V8.7:**
`layers_status.py` — статус слоёв L0–L6. `titan_status.py` — статус портирования. Но нет единого YAML-реестра всех 130+ модулей с верификацией.

---

## 🧬 AGM Belief Revision — формальная ревизия убеждений (Kumiho)

**Что это:** когда факт противоречит канону — создаётся immutable revision node. Старый факт НЕ меняется и НЕ удаляется. Новый факт получает tag-указатель на старый. Система всегда знает что она передумала, когда и почему.

**Источник:** Kumiho (Young Bin Park, март 2026). arXiv:2603.17244. AGM-постулаты (K*2–K*6) формализуют процесс: успешная ревизия, минимальное изменение, сохранение непротиворечивости.

```
Было: «Солнце вращается вокруг Земли» (теория Птолемея)
Стало: «Земля вращается вокруг Солнца» (теория Коперника)

V8.7 сейчас:       старый → Contradicted → Deprecated
AGM revision:      старый → immutable revision node (сохранён навсегда)
                   новый → указывает на старый через :SUPERSEDES_BY
                   audit trail: кто, когда, почему передумал
```

**Где применить:**
- `truth_maintenance.py` — заменить `supersede()` на AGM-совместимую ревизию
- `provenance_chain.py` — каждый revision node получает hash в цепочке

**Когда понадобится:**
При 1000+ фактов где противоречия неизбежны. AGM гарантирует что граф никогда не противоречит сам себе. 97.5% adversarial refusal (Kumiho benchmark).

**Что уже покрывает в V8.7:**
`truth_maintenance.py` — supersede/contradict. `contradiction_registry.py` — CRISPR-спейсеры. Но без формальных AGM-постулатов и immutable revision nodes.

---

## 🎯 Utility-gated Consolidation — фильтр полезности (CraniMem)

**Что это:** перед консолидацией — attentional gate проверяет UTILITY эпизода/факта. Не просто «high confidence → Validated», а «пригодился ли этот факт реально?». Бесполезные high-confidence факты отбрасываются.

**Источник:** CraniMem (март 2026). arXiv:2603.15642. Attentional gating + systems consolidation. Два bounded store (episodic buffer + knowledge graph).

```
ConsolidationEngine сейчас:
    Observed + confidence > 0.75 → Validated (микро-пакетно)

CraniMem-подобно:
    Observed + confidence > 0.75 → attentional gate проверяет UTILITY:
        - usage_count > 0? (использовался в ответах?)
        - user_satisfaction по домену > 0.5? (пользователю пригодилось?)
        - связан с другими Validated фактами? (часть сети знаний?)
        Если ДА → Validated
        Если НЕТ → остаётся Observed (сохраняем но не продвигаем)
```

**Где применить:**
- `consolidation_engine.py` — добавить utility check перед promotion
- `experience_replay.py` — обратная связь: какие факты реально пригодились

**Когда понадобится:**
При 5000+ фактов когда консолидация без фильтра заполняет L3 бесполезными фактами.

**Что уже покрывает в V8.7:**
`consolidation_engine.py` — micro-batch promotion по confidence. `reconsolidation.py` — обновляет usage_count. Но нет фильтра полезности при консолидации.

---

## 🧾 Trajectory-level Provenance — visited-but-uncited tracking

**Что это:** отслеживать ВСЕ узлы графа которые были посещены при reasoning — не только те что попали в финальные citations. Исследования показывают что ответ зависит от посещённых-но-непроцитированных узлов.

**Источник:** arXiv 2605.15109 (май 2026). «Why Neighborhoods Matter: Traversal Context and Provenance in Agentic GraphRAG».

```
Сейчас:
    query → retrieval → 3 факта в ответе → citations = эти 3 факта

Trajectory-level:
    query → retrieval → 8 фактов-кандидатов → ego_net_expand (depth=2) → ещё 25 узлов
    → из них 3 процитированы в ответе
    → НО 5 непроцитированных повлияли на выбор (исключены из-за низкого confidence,
      но их наличие изменило ranking)
    → provenance = все 28 узлов + траектория обхода
```

**Где применить:**
- `stimulus_map.py` — добавить trajectory tracking (не только финальные факты)
- `causal_graph.py` — записывать visited_nodes при обходе

**Когда понадобится:**
При аудите ответов — понять почему система выбрала именно эти 3 факта из 28 кандидатов.

**Что уже покрывает в V8.7:**
`stimulus_map.py` — отслеживает финальные факты в ответе. `causal_graph.py` — traverses граф. Но нет записи полной траектории обхода.

---

## 🔀 Ripple Propagation — автоматическая переоценка downstream-убеждений (Atlas)

**Что это:** когда upstream-факт меняется — ВСЕ downstream-факты, зависящие от него, автоматически переоцениваются. Не «пометить как устаревшее», а полный пересчёт confidence по цепочке зависимостей.

**Источник:** Atlas (Rich Schefren, июнь 2026). Open-source реализация Kumiho + Ripple propagation engine. 49/49 AGM-постулатов верифицированы на Neo4j.

```
Факт A (upstream): «Солнце вращается вокруг Земли» → Deprecated
    → Ripple проверяет все факты, зависящие от A:
        Факт B: «Планеты движутся по эпициклам» (зависит от A)
            → confidence падает с 0.9 до 0.3 (основание исчезло)
            → если confidence < 0.5 → Contradicted
        Факт C: «Гравитация объясняет орбиты» (не зависит от A)
            → не затронут
```

**Отличие от supersede:**
- `supersede()`: заменяет ОДИН факт. Не трогает downstream
- Ripple: проходит по ВСЕМУ графу зависимостей и пересчитывает

**Где применить:**
- `truth_maintenance.py` — добавить Ripple после supersede/contradict
- `causal_graph.py` — traversal по `DEPENDS_ON` рёбрам

**Когда понадобится:**
При 500+ взаимосвязанных фактов. Одно изменение в «корневом» факте может затронуть 50+ downstream.

**Что уже покрывает в V8.7:**
`truth_maintenance.py` — supersede/contradict/reinforce. Но без propagation engine.

---

## 🌐 Mesh Memory Protocol — агенты обмениваются когнитивным состоянием (MMP/SVAF)

**Что это:** протокол прямого обмена когнитивным состоянием между агентами. 7 типизированных семантических полей (CAT7). Per-field evaluation gate (SVAF). CfC-нейросеть с per-neuron временными константами. Без серверов, без центральной координации.

**Источник:** MMP (Mesh Memory Protocol, апрель 2026). arXiv:2604.03955. 8-слойная архитектура.

```
Агент А (инженер): наблюдение → CMB с 7 полями → SVAF gate → принято
Агент Б (учёный):   то же наблюдение → SVAF gate → частично принято (другие α_f)

Поля CAT7: focus, mood, domain, confidence, urgency, novelty, authority
Fast neurons (τ<5s): синхронизация настроения между агентами
Slow neurons (τ>30s): сохранение экспертизы домена
```

**Где применить:**
- `perspectives.py` — роли как MMP-агенты, обменивающиеся CMB
- `branch_manager.py` — синтез через per-field evaluation вместо простого concatenation

**Когда понадобится:**
Multi-agent сценарии. Для single-agent (V8.7 сейчас) — избыточно. Но при 3+ ролях параллельно — улучшает качество синтеза.

**Что уже покрывает в V8.7:**
`perspectives.py` — 9 ролей. `branch_manager.py` — параллельные ветки. Но без per-field evaluation gate.

---

## 📊 Entropy-Triggered Consolidation — консолидация по энтропии (MemArchitect)

**Что это:** консолидация запускается не по таймеру, а когда Entropy Ratio < 0.4 (высокая избыточность информации). Эпизодические воспоминания с fading retrievability (0.3≤R≤0.7) сжимаются в семантические факты. «Забываемый» шум (R<0.3) активно удаляется.

**Источник:** MemArchitect (март 2026). arXiv:2603.18330. Policy-driven memory governance. Adaptive Token Budgeting.

```
Сейчас (V8.7):
    SleepTimeWorker запускает consolidation по таймеру (каждые N минут)

MemArchitect-подобно:
    Мониторинг Entropy Ratio в episodic buffer
    Ratio < 0.4 → избыточность → consolidation cycle
    Ratio > 0.7 → новая информация → сохранить, не консолидировать
    Adaptive Token Budgeting: 30% резерв для reasoning, 10% для recall
```

**Где применить:**
- `consolidation_engine.py` — entropy-based trigger вместо таймера
- `sleep_time_worker.py` — adaptive token budgeting

**Когда понадобится:**
При активном использовании когда таймерная консолидация либо слишком частая, либо слишком редкая.

**Что уже покрывает в V8.7:**
`sleep_time_worker.py` — таймерная консолидация. `consolidation_engine.py` — micro-batch. Но без entropy-triggered механизма.

---

## 🔀 Quality-Gated Retrieval — двухуровневый retrieval с контролем качества (D-Mem)

**Что это:** две системы памяти — быстрая векторная (System 1) + медленная exhaustive (System 2). Quality Gate проверяет retrieved-контекст по трём осям перед ответом. Если контекст некачественный → fallback к полному чтению истории.

**Источник:** D-Mem (март 2026). arXiv:2603.18631. F1=53.5 на LoCoMo.

```
Quality Gate (3 оси):
    Relevance       — retrieved-факты релевантны запросу?
    Faithfulness    — retrieved-факты подтверждены источниками?
    Completeness    — retrieved-контекст покрывает запрос полностью?

Если любая ось < порог:
    System 1 (fast) → System 2 (exhaustive) — читаем сырую историю
```

**Где применить:**
- `pipeline.py` — Quality Gate после FactsPack, перед TruthGate
- `hybrid_retriever.py` — двухуровневый retrieval: fast (BM25+Dense) → quality check → exhaustive (full scan)

**Когда понадобится:**
При 500+ фактов когда retrieval иногда возвращает неполный контекст. Quality Gate предотвращает ответы на основе некачественного retrieval.

**Что уже покрывает в V8.7:**
`output_faithfulness.py` — проверяет ответ ПОСЛЕ генерации. `response_guardian.py` — Guardian ПОСЛЕ LLM. Но нет проверки качества retrieved-контекста ДО генерации.

---

## 📐 Hierarchical Attention Routing — динамическая маршрутизация L1→L2→L3 (MKA)

**Что это:** иерархический KV-кэш с тремя уровнями. L1 (local — текущий диалог), L2 (session — сессия), L3 (long-term — вся история). Запрос динамически маршрутизируется: простые вопросы → L1, сложные → L1+L2+L3. До 5× быстрее обучения чем MLA.

**Источник:** MKA (март 2026). arXiv:2603.20586. FastMKA — broadcast routing.

```
Запрос «привет» → Router → L1 (local) → ответ за 2ms
Запрос «что мы обсуждали про архитектуру в прошлый вторник?» → Router → L1+L2+L3 → ответ за 50ms
```

**Где применить:**
- `hybrid_retriever.py` — добавить hierarchical routing: local → session → long-term
- `attention_router.py` — динамическое решение какой уровень retrieval использовать

**Когда понадобится:**
При 20+ диалогах когда каждый запрос сканирует все факты — неэффективно. MKA снижает latency на 80% для простых запросов.

**Что уже покрывает в V8.7:**
`NGramIndex` — pre-filter. `hybrid_retriever.py` — BM25+Dense+RRF. Но без иерархической маршрутизации между уровнями памяти.

---

## 🧠 TMS Downstream Invalidation — авто-инвалидация зависимых фактов (Doyle 1979 + Atlas)

**Что это:** когда premise-факт отозван (Contradicted/Deprecated) — ВСЕ downstream-факты, которые от него зависели, автоматически инвалидируются. Truth Maintenance System (TMS) отслеживает зависимости между убеждениями. Классика AI (Doyle, 1979). Atlas (2026) реализовал на property graph.

**Источник:** Doyle (1979) + Atlas (июнь 2026, open-source). 49/49 AGM-постулатов + Ripple propagation.

```
Факт A → Contradicted
    → TMS проверяет: какие факты зависят от A?
        Факт B: depends_on [A] → автоматически → Contradicted
        Факт C: depends_on [A, D] → confidence снижен на 50%
        Факт D: не зависит от A → без изменений
```

**Отличие от Ripple:** Ripple пересчитывает confidence. TMS делает жёсткую инвалидацию — если основание рухнуло, зависимый факт тоже рушится.

**Где применить:**
- `truth_maintenance.py` — добавить TMS-слой над supersede/contradict
- `causal_graph.py` — dependency tracking с автоматической инвалидацией

**Когда понадобится:**
При первом же противоречии в графе. Без TMS зависимые факты остаются «живыми» хотя их основание рухнуло.

**Что уже покрывает в V8.7:**
`truth_maintenance.py` — supersede/contradict/reinforce. `causal_graph.py` — 15 типов связей с knowledge_status. Но без автоматической downstream-инвалидации.

---

## 🌐 7-Channel Cognitive Retrieval — 7 параллельных каналов поиска (SuperLocalMemory)

**Что это:** вместо 3 каналов (BM25 + Dense + RRF) — 7: semantic, keyword, entity graph, temporal, spreading activation, consolidation replay, Hopfield associative. Zero-LLM Mode A. 70.4% на LoCoMo. 215 source modules.

**Источник:** SuperLocalMemory V3.3 (апрель 2026). arXiv:2604.04514. Fisher-Rao квантованные эмбеддинги.

```
7 каналов:
    1. Semantic       — dense vector (как сейчас)
    2. Keyword        — BM25/FTS5 (как сейчас)
    3. Entity Graph   — traversal по causal_graph
    4. Temporal       — bi-temporal search (I96)
    5. Spreading Activation — Etir-like priming
    6. Consolidation Replay — experience_replay.py результаты
    7. Hopfield Associative — pattern completion из partial match
```

**Где применить:**
- `hybrid_retriever.py` — расширить с 3 до 7 каналов
- `retrieve_5stage()` — добавить temporal + spreading + Hopfield этапы

**Когда понадобится:**
При 5000+ фактов когда 3 канала не дают достаточного recall. 7 каналов поднимают LoCoMo с ~50% до 70%.

**Что уже покрывает в V8.7:**
Каналы 1-3 уже работают (BM25 + Dense + RRF). Канал 4 частично (bi-temporal I96). Каналы 5-7 — нет.
