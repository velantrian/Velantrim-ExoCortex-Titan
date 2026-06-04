# 🗄️ Полиглотная эпистемическая целостность + принципы безопасной памяти

> **Статус:** канон-инвариант (companion к `docs/INVARIANTS.md`, продолжает нумерацию I-серии)
> **Дата:** 2026-06-01
> **Назначение:** зафиксировать, **какое хранилище имеет право хранить какой уровень истины**,
> и записать защитные принципы памяти (pressure/decay/budget), отфильтрованные из внешних
> аудитов (DeepSeek/ChatGPT/Grok/Qwen) по соответствию реальному коду канона.
>
> ⚠️ Это **спецификация принципов**, а не новый код. Большинство уже соблюдается; документ
> делает их явными — для грантов, ревью и защиты от опасных «оптимизаций» в будущем.

---

## I200 — PolyglotEpistemicIntegrity (полиглотная эпистемическая целостность)

Каждое хранилище несёт **роль по уровню истины**. Источник: формализация Qwen RFC-0082.

| Слой / технология | Роль | Эпистемический статус |
|---|---|---|
| **SQLite (WAL)** | журнал, evidence, audit_chain, pending, snapshots | `SOURCE_OF_PROVENANCE` |
| **Kuzu / LadybugDB** | канонический граф истины (через TruthGate) | `WORLD_FACT` |
| **NetworkX** (`core/graph_lab.py`) | read-only анализ подграфа (centrality/cycles/paths) | `ANALYTICAL_SANDBOX` |
| **DuckDB** (опц., не P0) | OLAP-метрики/дашборды | `SYSTEM_METRICS` |
| **dense/vector** (`hybrid_retriever`) | семантический recall/fallback | `HYPOTHESIS / UNVERIFIED` |
| **Graphiti / temporal** (опц.) | песочница временной памяти | `TEMPORAL_EPISODE` |

**Инвариант I200:** *ни одно хранилище — кроме канонического графа через TruthGate — не имеет
права повышать `truth_status` факта до `FACT`/`Validated`.* Retrieval (lexical/dense/graph-lab)
**достаёт кандидатов**, но не присваивает истину. Анализ (NetworkX/DuckDB) **наблюдает**, но не
пишет факты. Это уже соблюдается в каноне: `truth_policy.decide` + `truth_gate` — единственный путь
к `Validated` (ср. I68 в `INVARIANTS.md`); `graph_lab`/`observer` — строго read-only/passive.

---

## I201 — MemoryPressureNotExecutioner (давление памяти ≠ палач фактов)

При достижении лимитов памяти система входит в **режим давления**, а НЕ авто-удаляет/Collapse факты.
Источник: safety-поправка ChatGPT к «Hard Cap Wall».

Порядок при `memory_budget_fact_warn → _gc → _hard` (пороги уже в `feature_config.py`):
1. предупредить (`warn`);
2. остановить авто-ingest;
3. сжать эпизоды (dedup похожих);
4. demote `UNVERIFIED`/`Hypothesized` в cold/pending;
5. требовать review;
6. **только потом** — optional collapse низкоценного шума, и **никогда** автоматически для
   `Validated`/`ImmutableCore`/Ring-Zero/source-backed/trace-critical узлов.

**Запрещено:** `select_victim()` → авто-`Collapsed` подтверждённого факта только из-за лимита.

---

## I202 — TruthConfidenceNotRetrievability (истинность ≠ приоритет доступа)

`truth_confidence` и `retrieval_priority` — **разные оси**. Источник: ChatGPT.

- Затухание/decay снижает **retrievability** (факт «остывает», уходит из активного фокуса).
- Decay **НЕ** портит `truth_status`/`evidence_confidence` подтверждённого источником факта.

```
FACT + COLD          = истинен, но не в активном фокусе   (норма)
FACT + LOW EVIDENCE  = слабое доказательство              (это другое — не decay)
```

Согласуется с нашим `cognitive_distance` (epistemic-ось отдельно от temporal/usage) и
гетерогенным decay (`fsrs.volatility_stability` трогает стабильность забывания, не истину).

---

## I203 — MultiSignalForgetting (забывание по многим сигналам, не по возрасту)

Кандидат на demote/archive определяется НЕ только возрастом. Источник: ChatGPT.
Учитывать: `source_ref?`, `trace_ref?`, `usage_count`, `graph_degree`, `task_anchor`,
`user_pinned`, `contradiction_status`, `epistemic_state`. Возраст — лишь один фактор.
(Уже частично: `volatility_class` в гетерогенном decay; полный L1-decay — будущий инкремент.)

---

## I204 — LowBudgetFastSafeNotCreative (низкий бюджет → FAST_SAFE)

При нехватке бюджета режим — **FAST_SAFE** (меньше фактов, строже uncertainty, короткий ответ),
а **не** `CREATIVE`. Источник: ChatGPT. Creative включается по **intent** пользователя, не по
дефициту токенов. Согласуется с `budget_planner` (lexical/hybrid/multi-hop по сложности, не по
«креативности»).

---

## I205 — DerivedLinksThroughPending (авто-связи только через Pending)

Автоматически выведенные связи (напр. co-occurrence/«CoincidenceDetector», cross-domain bridges)
пишутся в **Pending Queue**, а не напрямую в канонический граф. Источник: Qwen.
Промоушен в граф — только через review/TruthGate. Защищает граф от замусоривания ложными рёбрами.
(Ср. T2.1 в `MIGRATION_V8.6_TO_CANON.ru.md`: inferred-связи = `pending`, не `approved`.)

---

## Происхождение (provenance этого документа)

Отфильтровано из внешних аудитов **по сверке с кодом канона** (не на веру):
- Те аудиты работали на устаревшей теневой копии (baseline ~596 тестов; канон — 893+), поэтому
  ~12 их «находок» уже реализованы здесь (EventBus, CognitiveDistance, BudgetPlanner, Observer,
  TruthPolicy, graph_lab, Source Authenticity, гетерогенный decay, security headers, rate-limit).
- В этот документ вынесено **только то, что НЕ было в коде и безопасно**: один формализующий
  инвариант (I200, Qwen) и четыре защитных принципа (I201–I204, ChatGPT) + I205 (Qwen).
- Отклонено как преждевременное/опасное: DuckDB/Qdrant/Graphiti-as-core, fractal-dimension-в-MHI,
  авто-collapse фактов, confidence-decay подтверждённого FACT, auto-linking без Pending.

*Velantrim ExoCortex · POLYGLOT_EPISTEMIC_INVARIANTS · 2026-06-01*
*"Хранилище достаёт и наблюдает; истину присваивает только TruthGate."*
