# 🗺️ Velantrim Titan 9.0 — живая карта системы

> **Назначение:** экскурсия по архитектуре для пользователя, инженера, оператора,
> аудитора и AI-агента.
>
> **Версия продукта:** <!-- SYNC:VERSION -->v9.0.0<!-- /SYNC:VERSION -->
> **Проверенная база:** `main@70bc34fecdcf0bae15bc2264445e31b87b79bf08` на 2026-09-08.
> Это датированный checkpoint проверки, а не вечное утверждение о latest remote head.
>
> **Роль документа:** навигация и объяснение. При конфликте приоритет имеют код на
> exact SHA, тесты/CI, выбранная конфигурация и наблюдаемое runtime evidence.

[🇬🇧 English](SYSTEM_OVERVIEW.en.md) ·
[🏠 README](README.md) ·
[🇷🇺 README на русском](README.ru.md) ·
[📊 статус проекта](docs/PROJECT_STATUS.md) ·
[🔍 карта для аудитора](docs/REVIEWER_README.md) ·
[🏛️ канон истины](docs/TRUTH_AND_RINGZERO_CANON.ru.md)

---

## 🧭 Выберите маршрут

| Цель | Маршрут | Глубина |
|---|---|---:|
| 👋 понять идею | [объяснение за 30 секунд](#plain) | L0 |
| 🗺️ увидеть систему | [карта компонентов](#map) | L1 |
| 🔄 понять query/write flows | [два главных потока](#flows) | L2 |
| 🧑‍💻 проверить контракты | [инженерные границы](#engineer) | L3 |
| 🧾 проверить claims | [evidence/status rules](#evidence) | L1–L3 |
| 🧪 проверить жизнеспособность | [Architecture Assurance](#assurance) | L2–L3 |
| 🤖 объяснить Titan другому | [протокол самообъяснения](#self-explain) | адаптивно |

---

<a id="plain"></a>

## 👋 L0 — Titan за 30 секунд

Velantrim Titan — это **local-first проверяемая долговременная память/runtime для
AI-агентов**. Он разделяет вещи, которые обычный чат часто смешивает:

```text
источник → память → retrieval → policy → ответ
```

Удобная аналогия:

```text
библиотекарь  находит записи
лаборант      сохраняет источник и неопределённость
пограничник   ограничивает доверенные изменения состояния
аудитор       фиксирует наблюдаемые системой этапы
переводчик    превращает допущенный контекст в человеческий язык
```

Titan — не оракул. Он усиливает traceability и разделение полномочий, но не делает
любой текст истинным.

Инженерная формула:

```text
Memory stores state.
Retrieval proposes context.
Policy limits authority.
TruthGate evaluates admission where that contract applies.
TRACE records observable path artifacts.
LLM renders language.
```

Критические инварианты:

```text
retrieval ≠ evidence
admission ≠ verification
confidence ≠ evidence
model output ≠ Canon
TRACE membership ≠ semantic use ≠ answer support
CI green ≠ runtime/production authorization
```

---

<a id="evidence"></a>

## 🧾 Как читать статусы

| Метка | Значение |
|---|---|
| 🟢 **default path** | относится к базовому пути |
| ✅ **main / tested** | код и релевантные тесты находятся в `main` |
| 🟡 **available / gated** | реализация есть; использование зависит от профиля/ENV/dependency |
| 🚧 **open PR** | ещё не является частью `main` |
| 🔬 **research / proposed** | исследование/дизайн; runtime authority нет |
| ⚠️ **known limitation** | ограниченный claim, gap или debt |
| 📡 **runtime observed** | есть evidence от конкретного запущенного экземпляра |

Не сжимать это в одно слово:

```text
implemented ≠ tested ≠ wired ≠ enabled ≠ observed
```

Порядок source of truth для implementation-вопросов:

1. executable code на exact SHA;
2. тесты и текущие CI results;
3. выбранная runtime configuration и наблюдаемая telemetry;
4. current-state docs и принятые ADR;
5. PR/work-log history;
6. historical audits/archive.

Для live activation проверяйте config плюс `/health`, `/layers/status`, `/titan/status`.

---

<a id="map"></a>

## 🗺️ L1 — карта компонентов

```text
┌──────────────────── ЧЕЛОВЕК / АГЕНТ / ФАЙЛ ────────────────────┐
└──────────────────────────────┬──────────────────────────────────┘
                               ▼
                    API · auth · policy · egress
                               │
                ┌──────────────┴──────────────┐
                ▼                             ▼
           READ PATH                      WRITE PATH
        query / retrieval              source / candidate
                │                             │
                ▼                             ▼
      admitted context + TRACE          ESM + evidence
                │                             │
                ▼                             ▼
        Guardian / policy              TruthGate / CAS
                │                             │
                └──────────────┬──────────────┘
                               ▼
                     provenance · audit
                               │
                 ┌─────────────┴─────────────┐
                 ▼                           ▼
          derived projections          replaceable LLM
```

| Область | Роль | Основные поверхности |
|---|---|---|
| API | network boundary, auth, routes | `server.py`, `api/` |
| Orchestration | read-side flow | `core/pipeline.py`, `core/app.py` |
| Memory | fact + ESM + temporal state | `core/memory.py` |
| Retrieval | lexical baseline, optional dense/graph signals, narrowing | `core/hybrid_retriever.py`, `core/ngram_index.py` |
| Trust/write | policy, write admission, standard promotion | `core/truth_gate.py`, `core/write_gate.py`, `core/promotion_gateway.py`, `core/policy_kernel.py` |
| Provenance/audit | source lineage и аудируемые эффекты | `core/provenance_chain.py`, `core/audit_chain.py` |
| Remote egress | fail-closed remote capability boundary | `core/remote_egress.py` |
| Synaptic | source-linked document reading/shadow evaluation | `core/semantic_reader.py`, `core/knowledge_capsule.py` |
| Research | proposed/feature-gated композиции | `research/`, shadow paths, feature flags |

Derived indexes/graphs ускоряют retrieval и анализ. Они не становятся скрытым вторым
Canon только потому, что быстрее или семантически богаче.

---

<a id="flows"></a>

## 🔄 L2 — два главных потока

### 🔎 Поток A: query / answer

```text
query
  → API boundary
  → QueryPipeline
  → candidate narrowing / hybrid retrieval
       lexical baseline
       optional dense / graph signals when available
  → FactsPackBuilder / Guardian / truth policy
  → structured TRACE / result
  → optional LLM rendering
```

**Текущая implementation boundary:** `core/pipeline.py::run()` read-only относительно
canonical fact storage, ESM promotion и causal-relation mutation. Старое утверждение, что
legacy `POST /query` выполняет promotion, историческое и больше не соответствует коду.

Текущий server answer path всё ещё использует legacy query answer authority. Synaptic
shadow evaluation отделён и не получает answer authority только потому, что wired как
shadow processing.

### ✍️ Поток B: допущенная мутация

```text
source / candidate
  → provenance / metadata
  → legal ESM transition + применимые write checks
  → reviewed mutation owner
  → CAS / transactional evidence where required
  → local Canon / durable state
  → projections / audit updates
```

Стандартные `Validated` promotion callers сходятся на `PromotionGateway` и каноническом
`SQLiteGraphStore.validate_and_promote()`. Это **не** означает один глобальный owner всех
мутаций: обычные non-Validated transitions, invalidation, relation lifecycle, erasure,
archival/redaction и compound supersession сохраняют собственные явные контракты.

---

## 🔍 Что сейчас означает «hybrid retrieval»

`HybridRetriever` поддерживает lexical/BM25-style retrieval, dense embeddings, optional
graph signals и ranking fusion. Реальное использование зависит от dependencies/config.

```text
hybrid capability существует
  ≠ все зависимости установлены
  ≠ каждый signal запускается на каждом query
  ≠ ranking score является truth/evidence authority
```

Базовый Python package не имеет обязательных third-party dependencies. Dense retrieval и
часть enhanced paths требуют optional extras и деградируют к более узкому retrieval,
если компоненты недоступны.

---

## 📄 Synaptic Exo-Cortex

Текущий bounded status на проверенной базе:

```text
Raw evidence
  → ✅ SemanticReader
  → ✅ KnowledgeCapsule + exact SourceSpan
  → ✅ LLM Reader Adapter
       main/tested; нет server /query answer-path caller;
       standalone CLI использует scripts/read_document.py
  → ✅ Working Memory Gate
       main/tested; только shadow-chain
  → ✅ ContextPack
       main/tested; только shadow-chain
  → ✅ shadow evaluation
       main/tested; feature-gated; qualifying POST /query responses only;
       без answer authority
  → active answer authority
       НЕ передан Synaptic; LEGACY_QUERY остаётся authoritative
```

Shadow processing не пишет Canon/ESM и не становится active answer authority без
отдельного решения. `KnowledgeCapsule` остаётся proposal/evidence structure, а не Canon.

---

## 🔌 MCP transport

`core/tool_registry.py` и `core/mcp_transport.py` содержат bounded capability-based
JSON-RPC transport, включая capability ceilings и ограниченную process-local idempotency.

Reality status:

```text
implemented: yes (bounded)
module tests/evidence: present
server-wired by default: no
enabled только из-за наличия файла: no
runtime authority: no
production authorization: no
```

Фраза «registry есть, transport/server нет» уже устарела. Но и «transport есть, значит
MCP deployed» — тоже неверно.

---

<a id="engineer"></a>

## 🧑‍💻 L3 — инженерные границы

### 1. Read и write — разные полномочия

```text
READ
  возвращает facts / context / evidence / proposals
  не должен тихо мутировать Canon

WRITE
  использует явный owning service
  проверяет требуемые policy / ESM / provenance contracts
  записывает требуемый durable/audit effect
```

### 2. Canon и projections — разные уровни authority

```text
canonical state
  > rebuildable indexes / vectors / graph views / caches
  > model/provider output
```

Сбой projection должен вести к rebuild/degradation, а не к скрытому изменению truth.

### 3. LLM — заменяемый исполнитель

LLM может извлекать, сжимать с qualifiers, ранжировать, суммировать и формулировать.
Сам по себе он не может дать Canon admission, обойти PolicyKernel/TruthGate/write
boundary или превратить self-report модели в runtime evidence.

### 4. TRACE — accountability, не proof внутренней когниции

Titan может наблюдать retrieval/selection, serialization, provider packing, structured
trace artifacts и answer output. Bounded evidence-use tests явно разделяют:

```text
R = retrieved / selected
S = serialized
T = transmitted after provider packing
U = demonstrably used by model          НЕ устанавливается только R/S/T
A = demonstrably supports final answer  НЕ устанавливается только R/S/T
```

Не переименовывать R/S/T в U/A без отдельного attribution evidence.

### 5. Remote providers остаются за policy boundary

Remote server calls проходят через `core/remote_egress.py` и PolicyKernel. Metadata-only
`data_mode="none"` разрешён только закрытому capability set; user prompts, memory и audio
не могут тихо обходить remote-data policy.

---

<a id="self-explain"></a>

## 🎓 Протокол самообъяснения

Документация Titan должна объяснять одну и ту же реальность на разной глубине, не меняя
truth status:

```text
«Какая глубина нужна?»
  → plain
  → operator
  → engineer
  → reviewer
```

Правила:

1. Начинать мелко; углубляться по запросу.
2. Сохранять статус `proposed/implemented/tested/wired/enabled/observed`.
3. Давать evidence pointers для material claims.
4. Говорить `UNKNOWN`, когда current state не установлен.
5. Не выдавать architecture explanation за скрытый chain-of-thought.
6. Не считать несколько model opinions по общему контексту независимым evidence.

---

<a id="assurance"></a>

## 🧪 Architecture Assurance

Architecture Assurance — инженерный цикл, а не новый authority-owning cognitive organ:

```text
model
  → bounded implementation
  → deterministic load / fault injection
  → metrics + retained evidence
  → correction
```

Внутри runtime нужны invariants, fail-closed policy, limits, CAS/idempotency и audit hooks.
Снаружи — load/spike/soak, fault injection, recovery drills, property tests, replay и
capacity characterization.

Полезная queueing-интуиция:

\[
\rho = \frac{\lambda E[S]}{c}
\]

Но средняя utilization не является production guarantee. Нужно измерять tail latency,
service-time variance, storage amplification, common-cause failures и recovery. Текущая
SQLite concurrency evidence — bounded characterization, а не доказательство unlimited
multiprocess или network-filesystem safety.

---

## 🚫 Что Atlas не утверждает

- нулевые hallucinations;
- абсолютную истинность sources;
- certified GDPR/compliance;
- независимый security audit, которого не было;
- drop-in production-ready multi-user SaaS;
- consciousness / subjective experience;
- что каждый `core/` module enabled;
- что research/open PR уже runtime;
- что green CI = Operator GO / production authorization;
- что TRACE доказывает internal model use или answer support.

Production-hardening риски: [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md).
Bounded V1 productization может быть `DONE`, пока production-hardening work остаётся —
это разные scopes.

---

## 🔄 Как поддерживать Atlas актуальным

При architecture-facing изменении review должен ответить:

```text
1. Что изменилось для пользователя?
2. Какой контракт изменился для инженера?
3. Какой status теперь верен?
4. Где code/test/CI/runtime evidence?
5. Что происходит при failure?
```

Не использовать недатированный «current SHA» как вечную truth. Фиксируйте датированный
audited checkpoint и re-query GitHub, когда live state действительно важен.
