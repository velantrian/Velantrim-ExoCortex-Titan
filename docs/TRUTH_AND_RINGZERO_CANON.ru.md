# 🏛️ КАНОН: Движок Истины + Ring Zero — единый эталон Velantrim

> **Статус:** этолон-спецификация (v1.0, draft-for-implementation) · **Дата:** 2026-05-31
> **Назначение:** единый источник истины, по которому пишется **полноценный код** двухъядерной
> архитектуры Velantrim. Объединяет два изученных эталона в один канон.
>
> **Эталоны-источники:**
> - 🛡️ **Малое ядро / Ring Zero** — `Small Core Complex/small_core/` (+ `manifest/`, `OVERVIEW.md`)
> - 🔬 **Движок истины** — `velantrim_core-3/velantrim_core/velantrim/core/` (P0-1…P0-5, Patch 5, 6.1–6.3)
> - 🔀 **Связь** — `VELANTRIM_Dual_Core_Router/README.ru.md`
> - 🧠 **Большое ядро** — `VELANTRIM_ExoCortex_V8.6/` (этот репозиторий)
>
> ⚠️ **Историческая граница:** этот документ — нормативный эталон, составленный
> 31 мая 2026 года по снимкам эпохи V8.6. Пометки `V8.6:` в части V — неизменяемые
> **исторические данные аудита**, а не текущий статус Titan 9.0. Для текущей реализации
> нужно заново читать live `main`, тесты и CI, `docs/ai/CURRENT_STATE.md` и актуальные
> ownership/inventory-документы. Нельзя превращать старый ❌/⚠️ в текущий backlog без
> повторной проверки exact SHA.

---

## 0. TL;DR — одна формула

```text
Ring Zero      = совесть + BIOS + иммунитет (можно ли доверять ДЕЙСТВИЮ?)
Truth Engine   = эпистемика (можно ли доверять ОТВЕТУ? есть ли evidence?)
Big Core       = память + рост + язык + интерфейсы (варианты)
Dual Core Router = выбор, когда нужен строгий проход через малые ядра
Практические знания = слой данных под Big Core, проходящий те же гейты
```

Оба малых ядра служат одному мета-принципу: **честный интеллект** — система не путает
*знание, гипотезу, желание и ложь* и не выдаёт неизвестность за знание.

---

## 1. Мета-принцип и философские столпы

### 1.1 Мета-принцип
> Сила малого ядра не в количестве знаний, а в том, что оно **защищает условия честного знания**.
> Малое ядро не обязано знать всё. Оно обязано не дать самому умному слою потерять честность.

### 1.2 Три столпа (подтверждены в коде Core-3)
1. **Graph = Truth** — истину держит проверенный граф + политика, а не текст LLM.
2. **LLM = Language** — LLM только *извлекает структуру* и *формулирует*, с обязательным evidence; он не источник истины.
3. **Evidence before Answer** — нет структурного доказательства ⇒ `gap_notice` («честное не знаю»), а не ответ. Trace-only: каждый ответ объясним.

### 1.3 Пять неизменяемых принципов (манифест Ring Zero)
| id | Принцип | Смысл |
|----|---------|-------|
| `graph_truth` | Graph = Truth | Validated-знание живёт в проверенном графе, не только в сгенерированной речи |
| `never_lie` | Never lie to the user | Нет evidence — система говорит «не знаю» |
| `hypothesis_not_fact` | Hypothesis is not fact | Гипотезу нельзя подавать как validated-знание |
| `life_priority` | Life is priority | Безопасность и достоинство человека выше оптимизации |
| `small_core_immutable` | Big Core cannot modify Small Core | Рабочая система может *просить* решение, но не переписывать защищённое ядро |

`can_be_modified_by_big_core: false` — это инвариант манифеста, а не пожелание.

---

## 2. Карта системы

```text
            ┌─────────────────────────────────────────────┐
            │            🛡️ RING ZERO (малое ядро)         │  ← границы (инварианты)
            │  manifest · invariants I0–I8 · PolicyEngine  │
            │  boot · checkpoint/rollback · quarantine     │
            └───────────────┬─────────────────────────────┘
                            │ ActionContract → PolicyDecision
                            ▼
            ┌─────────────────────────────────────────────┐
            │           🧠 BIG CORE (ExoCortex)            │  ← варианты (рост)
            │  память · профили · LLM · интерфейсы · слои  │
            └───────────────┬─────────────────────────────┘
                            │ query + facts + relations
                            ▼  (через 🔀 Dual Core Router, для строгих запросов)
            ┌─────────────────────────────────────────────┐
            │        🔬 TRUTH ENGINE (Core-3)              │  ← строгий орган истины
            │  truth_policy · EvidenceRef · TruthGate      │
            │  causal_graph · TraceRecord(verdict)         │
            └─────────────────────────────────────────────┘

      📚 Практические знания (world_skills_core) — данные под Big Core, проверяются теми же гейтами.
```

**Инварианты** — то, что заморожено (Ring Zero, манифест, контракты).
**Варианты** — то, что растёт (память, профили, слои, знания Big Core).
Малое ядро задаёт границы, **внутри** которых большое ядро может расти безопасно.

---

# 🛡️ ЧАСТЬ I — Ring Zero (малое ядро): конституция и иммунитет

Ring Zero отвечает не на вопрос «что думать?», а на вопрос «**можно ли доверять этому действию?**».

## 3.1 ActionContract — формат запроса от Big Core к Ring Zero

Big Core **не** спрашивает строкой «можно add_fact?». Он шлёт структурный контракт.

| Поле | Тип | Обяз. | Назначение |
|------|-----|:----:|------------|
| `actor` | str | ✅ | кто инициирует (`big_core`, `llm`, `agent`, `user`, …) |
| `action` | str | ✅ | `add_fact` / `write_memory` / `promote_fact` / `transition_state` / `delete_fact` / `modify_policy` / `rewrite_core` / … |
| `target` | str | ✅ | объект действия (`memory`, `small_core`, `ring_zero`, `values_core`, `immutable_core`, …) |
| `claim` | str? | — | утверждение, если есть |
| `from_state` | str? | — | исходное эпистемическое состояние |
| `to_state` | str? | — | целевое состояние |
| `confidence` | float? | — | ∈ [0.0, 1.0] |
| `evidence_refs` | tuple[str] | — | ссылки на доказательства (см. §4.2 — должны быть структурными) |
| `risk` | str | — | `low` \| `medium` \| `high` \| `critical` (по умолч. `low`) |
| `reason` | str? | — | человекочитаемое обоснование |
| `metadata` | dict | — | произвольное |
| `created_at` | str (UTC ISO) | — | штамп времени (timezone-aware) |

**`structural_errors()`** (валидация формы, → инвариант I0): требует непустые `actor/action/target`,
`risk ∈ ALLOWED_RISKS`, `confidence` числовой и ∈ [0,1].

## 3.2 Инварианты I0–I8 (формальные правила, нарушать нельзя)

`check_invariants(contract) -> list[InvariantFinding{code, severity, message}]`.
Severity ∈ {`block`, `caution`, `quarantine`}.

| Код | Условие | Severity | Смысл |
|-----|---------|:--------:|-------|
| **I0** | `structural_errors()` непусты | `block` | контракт сломан по форме |
| **I1** | `actor ∈ {big_core, llm, agent}` И `target ∈ PROTECTED_TARGETS` | `block` | Big Core не может целиться в Small Core / Ring Zero |
| **I2** | `action ∈ MUTATION_ACTIONS` И `target ∈ PROTECTED_TARGETS` | `block` | защищённые цели неизменяемы через обычные контракты |
| **I3** | `to_state ∈ VALIDATED_STATES` И нет `evidence_refs` | `block` | Validated/ImmutableCore требует evidence |
| **I4** | `to_state ∈ VALIDATED_STATES` И `confidence < 0.85` | `block` | Validated/ImmutableCore требует confidence ≥ 0.85 |
| **I5** | `action ∈ WRITE_ACTIONS` И `confidence < 0.5` | `caution` | низкоуверенную запись понизить до Observed/Hypothesis |
| **I6** | текст содержит `DANGEROUS_WORDS` (lie/deceive/fake/harm/kill/break_truth) | `quarantine` | защитный маркер опасности |
| **I7** | `risk == "critical"` | `quarantine` | критический риск → карантин + ручная проверка |
| **I8** | `risk == "high"` | `caution` | высокий риск → осторожный режим |

Множества (канонические):
```text
PROTECTED_TARGETS = {small_core, ring_zero, values_core, immutable_core}
WRITE_ACTIONS     = {add_fact, write_memory, promote_fact, transition_state}
MUTATION_ACTIONS  = WRITE_ACTIONS ∪ {delete_fact, modify_policy, rewrite_core}
VALIDATED_STATES  = {validated, immutablecore, immutable_core}
DANGEROUS_WORDS   = {lie, deceive, fake, harm, kill, break_truth}
```

## 3.3 PolicyEngine — единая точка решения

`decide(contract) -> PolicyDecision{allowed, mode, reason, findings, required_state}`.
Приоритет severity (от строгого к мягкому):

```text
1. quarantine ∈ severities → escalate(QUARANTINE); allowed=False
2. block      ∈ severities → allowed=False ("blocked by Small Core invariant")
3. caution    ∈ severities → escalate(CAUTIOUS); allowed=True, required_state="Observed"
4. иначе если НЕ write_allowed (режим QUARANTINE/RECOVERY) → allowed=False
5. иначе → allowed=True ("allowed")
```

🔒 Каждое решение пишется в **AuditLog** (`policy_decision` + контракт + решение). Журнал append-only (JSONL).

## 3.4 Режимы безопасности (SystemSafetyState)

| Режим | Порядок | write_allowed | validated_write | Что можно |
|-------|:------:|:------------:|:---------------:|-----------|
| `NORMAL` | 0 | ✅ | ✅ | читать, писать, учиться, отвечать, повышать до Validated |
| `CAUTIOUS` | 1 | ✅ | ❌ | читать; писать **только** Observed/Hypothesis |
| `QUARANTINE` | 2 | ❌ | ❌ | только чтение и диагностика |
| `RECOVERY` | 3 | ❌ | ❌ | откат к checkpoint, восстановление |

- `escalate(mode, reason)` — **монотонно вверх** (только повышает строгость).
- `clear_to_cautious()` / `clear_to_normal()` — понижение **только вручную** (после review).
- `write_allowed = mode ∈ {NORMAL, CAUTIOUS}` · `validated_write_allowed = mode == NORMAL`.

## 3.5 Boot / Checkpoint / Integrity / Audit (обязательные гейты)

`required_gates = [boot_check, action_contract, policy_gate, truth_boundary, checkpoint, rollback, quarantine]`.

- **BootProtocol.verify(root, required_paths, expected_hashes)** → `BootReport{allowed, reasons, checked_root}`:
  проверяет существование корня Big Core, наличие обязательных путей и **совпадение хэшей** (`hash_tree` + `compare_hashes`). Аудируется.
- **Integrity** — хэши файлов/версии Big Core; рассинхрон → reasons в BootReport (запуск запрещён).
- **CheckpointStore** — сохранение/откат состояния (целевое: persistent на диск; черновик — in-memory).
- **Rollback** — найти лучший безопасный checkpoint и восстановить (триггер RECOVERY).

## 3.6 Контракт Ring Zero (in/out)
```json
// IN  (ActionContract)
{ "actor":"big_core","action":"promote_fact","target":"memory",
  "claim":"ДНК хранит генетическую информацию","from_state":"Supported",
  "to_state":"Validated","confidence":0.94,
  "evidence_refs":[{"source_id":"bio_textbook_01","quote":"…"}],"risk":"low" }
// OUT (PolicyDecision)
{ "allowed":true,"mode":"normal","reason":"allowed","findings":[],"required_state":null }
```

---

# 🔬 ЧАСТЬ II — Движок истины (Core-3): эпистемика

## 4.1 Единая Truth Policy — ОДИН закон (P0-4)

Единственный закон допустимости факта, на который опираются **И** запись (TruthGate), **И** чтение (TraceRecord):

```text
admissible(fact) ⇔  confidence ≥ conf_threshold
                AND  валидный EvidenceRef (source → source_id)
                AND  не known_false и не contradicted (проверяется по графу)
```

`fact_admissible(fact, conf_threshold) -> (ok: bool, reason: str)`, причины: `low_confidence` | `no_evidence` | `ok`.
🚫 **Запрещено** иметь несколько расходящихся политик для записи и чтения.

## 4.2 EvidenceRef — контракт доказательства

```text
EvidenceRef{ source_id?, chunk_id?, span?:[int,int], quote? }
is_valid() ⇔ source_id присутствует И есть хотя бы один локатор (chunk_id | span | quote)
```
- Хранится в БД как JSON-строка. `from_raw()` принимает dict | JSON-строку | plain-строку | None.
- **Plain-строка намеренно невалидна** (нет `source_id`) — старый формат не проходит контракт и требует обновления.
- `missing_fields()` объясняет, чего не хватает (для held-причин).

## 4.3 TruthGate — промоушен pending → validated

`TruthGate(store, graph, promote_threshold=0.75)`:
- `submit_inferred(inferred)` — сохраняет inferred-связь как **PENDING**, evidence сериализуется.
- `review_pending()` → `{promoted, rejected, held}`. Для каждой pending forward-связи:
  1. `is_known_false(frm,to,rtype)` (validated deny-ребро) → **refuted** (rejected: known_false)
  2. validated/approved `contradicts` affirm-ребро → **refuted** (rejected: contradicts)
  3. `EvidenceRef.from_raw(...).is_valid()` ложно → **held** (`no_evidence:<поля>`)
  4. пустой `source` → **held** (no_source)
  5. `confidence ≥ promote_threshold` → **validated** (каскад на inverse через pair_id) · иначе **held** (low_confidence)

## 4.4 TraceRecord — вердикт ответа (P0-4/P0-5)

`build_facts_pack` пускает в пакет **только** факты, прошедшие §4.1 (остальные → `rejected` с причиной, `evidence_ref` заполняется).
`build_trace` выносит вердикт:

| Условие | decision | truth_status | Смысл |
|---------|:--------:|:------------:|-------|
| есть validated `contradicts`/`known_false` между фактами пакета | **`reject`** | contradicted | ответ отклонён |
| ни один факт не прошёл policy (в т.ч. high-conf без source) | **`gap_notice`** | insufficient | честное «не знаю» |
| иначе | **`allow`** | validated | N фактов с evidence + путь из K рёбер |

`TraceRecord{ query, intent, facts_pack_id, evidence_ids, path[PathStep], truth_status, decision, note }`.
`path` строится только по `validated/approved`, не-inverse рёбрам между допущенными фактами (объяснимость).

## 4.5 Каузальный граф — правила

- **Только FORWARD-типы** добавляются; inverse создаётся авто. `FORWARD_TYPES = {causes, prevents, requires, enables, implies, contradicts, generalizes, specializes, precedes, follows, composes, analogous_to, becomes}`.
- **Идемпотентность (P0-3):** дубль `(from,to,type,source)` → возвращается **существующий** id (без фантомов, без молчаливого OR IGNORE).
- **Атомарность:** forward + inverse пишутся в **одной транзакции** с общим `pair_id`.
- **Каскад статуса (P0-2):** `set_status(rid)` меняет статус на **всю пару** через `pair_id`.
- **Negative knowledge:** `polarity='deny'` = «A НЕ rtype B». `is_known_false` блокирует только по validated/approved deny.
- **Bi-temporal:** `valid_from/valid_to`, запросы `as_of` (Pearl L2 do-оператор в `propagate_change`).
- БД-инвариант: `CHECK(from≠to)`, `CHECK(polarity IN ('affirm','deny'))`, `UNIQUE(from,to,type,source)`.

## 4.6 Store — инварианты целостности

- **Один источник истины — БД.** ❌ **Никакого L0-кэша**, рассинхронизируемого с L1 ⇒ split-brain невозможен *по конструкции*.
- **Потокобезопасность:** весь доступ к БД — через locked API (`query/execute/transaction`) под **единым реентрантным `RLock`**. Никто вне store не трогает `.conn` напрямую.
- **UPSERT, не `INSERT OR REPLACE`:** REPLACE = DELETE+INSERT → `ON DELETE CASCADE` сносит связи. UPSERT обновляет строку на месте, сохраняя `fact_id`, связи и `created_at`.
- `transaction()` — атомарный блок: commit разом или rollback.

## 4.7 Дисциплина инференса → всегда PENDING

Любой авто-вывод (affordance→causal, ingest-инференс) пишется как `truth_status='hypothesis'/review_state='pending'`,
концепт резолвится в `fact_id` (не голая строка), только валидные FORWARD-типы.
🚫 **Запрещено** писать inferred-связь сразу как `approved/validated`.

## 4.8 Retrieval — HybridRetriever
`score = α·lexical + γ·graph_proximity + δ·recency` (нормализованные [0..1]; по умолч. α=0.5, γ=0.35, δ=0.15, decay=0.7, depth=3).
Граф **участвует в ранжировании** (рекурсивный CTE, вес растекается по `causes/enables/requires/...`). Честное имя — «graph proximity», не «PageRank». Флаги `use_graph/use_recency` для ablation в eval.

## 4.9 Living Context — 8 измерений
`LivingContext`: **WHERE** (locations) · **WHO** (agents) · **HOW** (affordances) · **WHAT** (products) · **FEEL** (qualities) · **ROLE** (systemic_roles) · **TIME** (temporal) · **DEEP** (deep_knowledge).
Аффордансы **agent-relative** (Гибсон): дерево «гнездиться» для птицы, «срубить» для человека. Lossless `to_dict/from_dict`, провенанс на каждый аффорданс.

## 4.10 LLM = Язык — экстрактор с обязательным evidence
LLM **извлекает структуру** (relations + 8-мерный контекст), промпт **заставляет** вернуть `evidence_ref{source_id,chunk_id,span,quote}`.
`confidence = доля прогонов self-consistency, согласных по (from,to,type)`; evidence — первый валидный (провенанс не усредняется). Все извлечённые связи рождаются `pending`. Нет LLM → детерминированный regex-fallback.

## 4.11 FSRS — созревание через использование
`plasticity_factor ∈ [0.3..1.0]` от `retrieval_count`, **не** от wall-clock. Агента выключили на 14 дней → факты не «созрели». Исключение: `INVARIANT/PRINCIPLE` зреют медленно по времени (редко запрашиваются).

---

# 🔀 ЧАСТЬ III — Объединение: единый шлюз

## 5.1 Единый словарь решений

Два малых ядра и роутер должны говорить на **одном языке вердиктов**:

| Ring Zero (PolicyDecision) | Truth Engine (TraceRecord) | Dual Core Router | Единый вердикт |
|----------------------------|----------------------------|------------------|----------------|
| `allowed=True, mode=normal` | `decision=allow` | `allow` | **ALLOW** — отвечать с опорой на факты |
| `caution` / `required_state=Observed` | `decision=gap_notice` | `gap_notice` | **GAP_NOTICE** — «недостаточно данных» |
| `block` / `quarantine` | `decision=reject` | `reject` | **REJECT** — не выдавать утверждение |

> Ring Zero — **грубый конституционный** гейт (можно ли это *действие*).
> Truth Engine — **тонкий эпистемический** гейт (есть ли *evidence* под *ответ*).
> Это один закон на двух уровнях: I3/I4 (evidence+conf для Validated) ≡ truth_policy (evidence+conf для admissible).

## 5.2 Единый словарь эпистемических состояний

Канонический набор (надмножество ESM V8.6 ∪ Core-3 ∪ Ring Zero):
```text
Observed → Hypothesized/Supported → Validated → ImmutableCore
                     ↘ Contradicted / Collapsed / Deprecated
relations.truth_status: pending → validated | refuted   (+ review_state: pending/approved)
relations.polarity:     affirm | deny (negative knowledge)
```
Новые факты **рождаются `Observed`**. Повышение до `Validated` — только через TruthGate (evidence+conf≥0.75) И при `validated_write_allowed` (режим NORMAL). До `ImmutableCore`/конституции — conf ≥ 0.85 (I4).

## 5.3 Сквозной поток запроса (reference)

```text
boot:    BootProtocol.verify(big_core_root, hashes) → иначе RECOVERY
write:   Big Core → ActionContract → PolicyEngine.decide
             ├─ REJECT (block/quarantine) → StopRule / Quarantine / Rollback
             ├─ GAP/CAUTION → записать только Observed/Hypothesis
             └─ ALLOW → store_fact → (inferred → TruthGate.submit_inferred = pending)
review:  TruthGate.review_pending → promoted/refuted/held
read:    Big Core → (Router: high-risk?) → build_trace(query)
             ├─ reject     → честный отказ (+ blocked_reason)
             ├─ gap_notice → «недостаточно данных» (LLM не «досочиняет»)
             └─ allow      → LLM формулирует ОТВЕТ строго из FactsPack (+ TraceRecord)
audit:   каждое решение Ring Zero и каждый вердикт Truth Engine → append-only журнал
```

## 5.4 Единая лестница порогов (reconcile)

Три порога — это **не противоречие, а три ступени** одной лестницы. Реализация обязана держать их в **одном месте** как явные константы:

| Ступень | Порог conf | Дополнительно | Источник |
|---------|:----------:|---------------|----------|
| **Допуск в ответ** (admissible/read) | ≥ **0.5** | + валидный evidence | `truth_policy.DEFAULT_CONF_THRESHOLD` |
| **Промоушен в Validated** (граф) | ≥ **0.75** | + evidence + нет contradiction/known_false | `TruthGate.promote_threshold` |
| **Конституционный Validated/Immutable** | ≥ **0.85** | + evidence_refs (I3) | Ring Zero `I4` |

Инвариант: `0.5 ≤ 0.75 ≤ 0.85`. Низкоуверенная запись (<0.5) → `caution`/Observed (I5).

## 5.5 Dual Core Router — контракт моста
```json
// IN
{ "query":"…", "facts":[{ "fact_id","claim","confidence","source" }],
  "relations":[{ "from_fact_id","to_fact_id","relation_type","confidence","source" }],
  "mode":"strict" }
// OUT
{ "decision":"allow|gap_notice|reject", "truth_status":"validated|insufficient|contradicted",
  "evidence_ids":["…"], "trace_note":"…", "blocked_reason":null }
```
Правила интеграции (из Dual Core Router): адаптер **не** тащит малое ядро внутрь Big Core; subprocess-вариант первым (изоляция); малое ядро **не** пишет в основную БезопаснуюБД Big Core без отдельного разрешения; роутер включается **не на все** запросы, а на строгие/high-risk (медицина, право, наука, grant).

---

# 🧭 ЧАСТЬ IV — Инварианты vs Варианты vs Практические знания

| Слой | Природа | Где | Можно менять? |
|------|---------|-----|:-------------:|
| Манифест + инварианты I0–I8 | **инвариант** | Ring Zero | ❌ только через явный конституционный процесс, не Big Core |
| Контракты (ActionContract, EvidenceRef, TraceRecord, FORWARD_TYPES) | **инвариант** | оба малых ядра | ❌ ломать нельзя (версионирование — да) |
| Truth Policy, пороги-лестница | **квази-инвариант** | Truth Engine | ⚠️ только согласованно, в одном месте |
| Память, профили, линзы, слои L0–L6 | **вариант** | Big Core | ✅ растёт свободно внутри границ |
| Практические знания (`world_skills_core`) | **данные** | Big Core | ✅ наполняется; проходит те же гейты (evidence/TruthGate) |

Практические знания — это **факты с источником**, а не исключение из правил: каждый батч `world_skills_core`
при попадании в граф обязан нести `source` и пройти Truth Policy; недоказанные — остаются Observed/pending.

---

# ✅ ЧАСТЬ V — Нормативный чек-лист + исторический снимок V8.6

> Требования C1–C12 ниже нормативные. Скобочные пометки `V8.6:` возле C1–C9 —
> **исторические находки от 2026-05-31**. Они не утверждают текущий результат Titan 9.0.
> Текущее соответствие нужно подтверждать live-кодом, тестами, CI и актуальными
> inventory-документами на exact SHA.

Полноценная реализация двухъядерной системы **обязана** удовлетворять:

- **C1.** Единая `truth_policy`, используемая И записью, И чтением. *(V8.6: ❌ 4+ расходящихся гейта)*
- **C2.** Структурный `EvidenceRef` (source_id + локатор) подключён к промоушену; plain-строка невалидна. *(V8.6: ❌ `EvidenceItem` есть, но не подключён; `_count_evidence` возвращает 1)*
- **C3.** Read-путь выдаёт `allow|gap_notice|reject`; high-conf без evidence ⇒ `gap_notice`; не отвечает при 0 фактов. *(V8.6: ❌ отвечает по голому confidence)*
- **C4.** Противоречие/known_false между фактами ответа ⇒ `reject` на этапе ответа, а не только оффлайн. *(V8.6: ❌ только аннотирует)*
- **C5.** Инференс пишется `pending`, промоушен только через TruthGate. *(V8.6: ⚠️ `causal_bridge` пишет inferred как approved)*
- **C6.** Один источник истины (без рассинхрон-кэша) ИЛИ кэш под локом с записью L1→L0. *(V8.6: ❌ split-brain C1/C2/H3)*
- **C7.** Весь доступ к БД потокобезопасен (RLock/единое соединение или per-op с локом). *(V8.6: ❌ незалоченный L0, общий conn графа M1)*
- **C8.** Граф: идемпотентный `add_relation`, атомарные forward+inverse с `pair_id`, каскад `set_status`. *(V8.6: ⚠️ баг метаданных inverse M2)*
- **C9.** Ring Zero как реальный гейт перед записью Big Core (PolicyEngine.decide), а не выключенный `graph_ring_zero`. *(V8.6: ❌ `ENABLE_IMMUTABLE_CORE` off, 0% покрытие)*
- **C10.** Boot-проверка целостности Big Core (хэши) перед запуском; рассинхрон → RECOVERY.
- **C11.** Append-only audit на каждое решение Ring Zero и каждый вердикт Truth Engine.
- **C12.** Пороги-лестница `0.5 ≤ 0.75 ≤ 0.85` в одном месте как явные константы.

> Исторический gap-анализ: см. глубокий аудит 2026-05-31 (находки C1/C2/H1–H3,
> M1–M2, security) и `docs/AUDIT_V8_6.ru.md`. Каждый `V8.6:` ❌/⚠️ выше фиксирует
> только тот исторический снимок; его нельзя цитировать как текущий дефект Titan 9.0
> или активный backlog без повторной верификации.

---

## Приложение A — Канонические константы
```text
# Ring Zero
PROTECTED_TARGETS = {small_core, ring_zero, values_core, immutable_core}
VALIDATED_STATES  = {validated, immutablecore, immutable_core}
ALLOWED_RISKS     = {low, medium, high, critical}
I4_VALIDATED_MIN_CONF = 0.85 ; I5_WRITE_CAUTION_BELOW = 0.5
MODE_ORDER: NORMAL<CAUTIOUS<QUARANTINE<RECOVERY ; write_allowed = {NORMAL,CAUTIOUS}

# Truth Engine
DEFAULT_CONF_THRESHOLD = 0.5     # admissible / read
PROMOTE_THRESHOLD      = 0.75    # pending → validated
FORWARD_TYPES (13) ; PROX_TYPES = {causes,enables,requires,prevents,composes,becomes}
retrieval: alpha=0.5 gamma=0.35 delta=0.15 decay=0.7 max_depth=3
FSRS: plasticity ∈ [0.3..1.0] ; PRIMING_WINDOW_DAYS=14
```

## Приложение B — Глоссарий
- **Ring Zero / Small Core** — защищённое неизменяемое ядро (конституция + BIOS + иммунитет).
- **Truth Engine / Core-3** — строгий орган истины (evidence + граф + вердикт).
- **Big Core / ExoCortex** — рабочая система (память, язык, интерфейсы).
- **ActionContract** — структурный запрос Big Core → Ring Zero.
- **EvidenceRef** — структурный объект доказательства (source_id + локатор).
- **TraceRecord** — объяснимый вердикт ответа (allow/gap_notice/reject + путь).
- **gap_notice** — честное «не знаю» при отсутствии evidence.
- **known_false** — validated deny-ребро (negative knowledge).
- **split-brain** — рассинхрон кэша L0 и хранилища L1 (запрещён каноном, C6).

## Приложение C — Файлы-эталоны (откуда взят канон)
```text
Small Core Complex/manifest/small_core_manifest.draft.json   # манифест (5 принципов)
Small Core Complex/small_core/invariants.py                  # I0–I8
Small Core Complex/small_core/action_contract.py             # ActionContract
Small Core Complex/small_core/policy_engine.py               # PolicyEngine.decide
Small Core Complex/small_core/quarantine.py                  # SafetyMode / SystemSafetyState
Small Core Complex/small_core/boot_protocol.py               # BootProtocol.verify
velantrim_core-3/.../core/truth_policy.py                    # единый закон
velantrim_core-3/.../core/truth_gate.py                      # промоушен
velantrim_core-3/.../core/evidence.py                        # EvidenceRef
velantrim_core-3/.../core/trace.py                           # TraceRecord / вердикт
velantrim_core-3/.../core/causal_graph.py                    # граф истины
velantrim_core-3/.../core/store.py                           # инварианты целостности
VELANTRIM_Dual_Core_Router/README.ru.md                      # контракт адаптера
```

---

*Канон v1.0 — единый эталон. Изменения — только согласованным версионированием; нарушать инварианты §1.3 и контракты §3–§4 запрещено. Этот документ — то, по чему пишется код.*
