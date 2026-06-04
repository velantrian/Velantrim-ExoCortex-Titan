# RFC-0082 — Sleep Consolidation Loop (Slow Path Cognitive Consolidation)

> **Статус:** Draft / P0-ready · **Дата:** 2026-05-31 · **Автор:** Velantrim × Claude
> **Связь:** дополняет **RFC-0081** (Fast Path: Decay → Reactivation → Observer → RetrievalDirective).
> RFC-0081 = «как система думает СЕЙЧАС» (session/fast path).
> RFC-0082 = «как система становится умнее НОЧЬЮ» (consolidation/slow path).
> **Канон:** Graph = Truth · LLM = Voice · Memory = Physiology · забывание = снижение доступности, не уничтожение истины.

---

## 1. Purpose

Дать Velantrim **единый ночной цикл консолидации**, который в простое (Slow Path) приводит память
в порядок — так же, как мозг во сне консолидирует опыт. Цель — закрыть главный диагноз аудита
(«ширина опережает глубину»): **не добавлять новые органы, а соединить уже существующие** в один ритм.

Цикл превращает разрозненные факты в **организованное, само-подтверждающееся, непротиворечивое**
знание и реализует обещание задумки: *«чем дольше система живёт и чем больше с ней общаются —
тем лучше она себя организует и понимает»*.

```text
promotion → semantic dedup/merge → corroboration → contradiction resolution
          → salience/FSRS decay → concept re-clustering → consolidation_report
```

Уже готово на момент RFC (переиспользуем, не пишем заново):
- `core/promotion_policy.py` — градуированный промоушен по доказательствам (Step 2 mechanism).
- `core/knowledge_linker.py` — типизированные causal-рёбра (для re-clustering / связей).
- `core/consolidation_engine.py::run_consolidation` — точка входа + диспетчер по флагу.
- `core/sleep_time_worker.py` — хост Slow Path (`_run_sleep_cycle` уже зовёт `run_consolidation`).
- FSRS-модули: `core/salience.py`, `core/salience_fsrs.py`, `core/vintage_decay.py`.
- `core/concept_emergence.py` — Hebbian-кластеризация (Step 5).
- `core/truth_gate.py`, `core/memory.py` (ESM, `transition_esm`, `invalidate_edge`, no-DELETE).

---

## 2. Non-goals

- ❌ НЕ новые линзы, режимы, философские слои, агенты или новые названия памяти.
- ❌ НЕ замена Fast Path (RFC-0081): цикл НИКОГДА не работает в `/query`-пути.
- ❌ НЕ LLM-обязательность для P0: P0 детерминирован (embeddings — да, генеративный LLM — нет).
- ❌ НЕ изменение `truth_status`/`confidence` по «популярности» или обратной связи (см. инвариант I-E).
- ❌ НЕ физическое удаление фактов или рёбер (см. инвариант I-A).
- ❌ НЕ полный семантический NLI противоречий в P0 (это P1, тиер с LLM).

---

## 3. Input

Цикл работает над **снимком стора** (P0 — без отдельного event-log; событийный вход — P1).

```json
{
  "store": "GraphStore",                     // источник фактов (get_all_facts)
  "causal_graph": "CausalGraph",             // рёбра (relations)
  "embedder": "SentenceTransformer|null",    // all-MiniLM / multilingual; null → dedup пропускается
  "config": {
    "dedup_threshold": 0.92,
    "decay_idle_days": 90,
    "max_batch": 2000,
    "dry_run": false
  }
}
```

Состояния-кандидаты на обработку: `Observed`, `Hypothesized`, `Supported`, `Validated`.
**Исключены всегда:** `ImmutableCore`, Ring Zero (`VALUES_CORE`, `RING_ZERO`), `Collapsed` (терминал).

---

## 4. Step 1 — Semantic Dedup / Merge

**Зачем:** два факта об одном и том же в разных словах не должны жить как независимые.
Слияние → один канонический факт с **множеством источников** → топливо для корроборации (Step 2).

**Как (P0, детерминированно):**
1. Эмбеддинги claim всех фактов (`sentence-transformers`, уже установлен).
2. Кластеризация по косинусной близости ≥ `dedup_threshold` (порог консервативный, 0.92).
3. В кластере выбрать **канонический** факт: приоритет по (ESM-состояние ↑, confidence ↑, возраст ↑).
4. Источники остальных **объединяются** в `sources[]` канонического (множество, не перезапись).
5. Дубликаты → `Deprecated` через `transition_esm`, с ребром `merged_into → canonical` (НЕ удаляются).

```json
{
  "merge": {
    "canonical_id": "agro.crop.wheat.grain_use",
    "absorbed_ids": ["kb.wheat.grain_alt"],
    "sources_after": ["physics", "agro_handbook", "user_2026"],
    "similarity": 0.94
  }
}
```

**Безопасность:** канонический никогда не теряет провенанс; дубликат сохраняется как `Deprecated`
с обратной ссылкой (reversible, no-DELETE). Ring Zero / ImmutableCore не сливаются.

---

## 5. Step 2 — Corroboration Update

**Зачем:** независимые подтверждения = рост доверия. Прямо усиливает Truth Gate.

**Как:** для каждого (канонического) факта `corroboration = |distinct sources|` (после Step 1).
Подаём в `promotion_policy.Evidence.corroboration` и прогоняем `recommend_transition`:

```text
дедуп → evidence_count++ → corroboration↑ → основания для Supported / Validated
```

Переиспользуем готовый `core/promotion_policy.py` (правила: `support_corroboration=2`,
`validate_corroboration=3`, выдержка во времени, доверенные источники I98). Переходы — только
через матрицу ESM. `confidence` НЕ накручивается напрямую — растёт право на повышение состояния.

```json
{ "corroboration": { "fact_id": "...", "sources": 3, "recommended": "Supported→Validated" } }
```

---

## 6. Step 3 — Contradiction Resolution

**Зачем:** без разрешения противоречий знание гниёт (тащит оба конфликтующих блока).

**P0-scope (детерминированный, без LLM):**
- **Явная супрессия (supersession):** новый факт о том же субъекте + сигнал коррекции/новизны
  (temporal recency, маркеры «на самом деле / уже не / отказался») → старый `→ Contradicted`
  (FROZEN/SUPERSEDED), новый `ACTIVE`, ребро `superseded_by` / `contradicts` в CausalGraph.
- **Кластерные конфликты:** в семантическом кластере (Step 1) факты с противоположной полярностью
  (negation-маркеры) помечаются `requires_review=true` — не авто-резолвятся в P0.

**P1 (тиер с LLM/NLI):** полноценное семантическое обнаружение противоречий из текста.

```json
{
  "contradiction": {
    "subject": "user.material_choice",
    "superseded_id": "blk_wood_2026_05",   "new_state": "Contradicted",
    "active_id":     "blk_brick_2026_06",
    "edge": "superseded_by",
    "auto_resolved": true
  }
}
```

**Связь с RFC-0081:** супрессия пользовательских предпочтений = вход для **Section 10 Observer**
и **MentalBlock Schema v2** (старый блок → SUPERSEDED, новый → ACTIVE).

---

## 7. Step 4 — Salience / FSRS Decay (умное забывание)

**Зачем:** неиспользуемое знание должно «тускнеть» — но не уничтожаться.

**Как:** на каждый факт — FSRS-расписание (`salience_fsrs.py`) от времени последнего доступа.
- idle > `decay_idle_days` и низкая salience → `Deprecated` → cold-archive (вне горячего ретрива).
- забывание = **снижение retrievability/salience**, НЕ DELETE и НЕ смена `truth_status`.
- **Исключения:** Ring Zero, `ImmutableCore`, недавно-валидированные — не распадаются.

```json
{ "decay": { "fact_id": "...", "idle_days": 142, "salience": 0.08, "action": "Deprecated→archive" } }
```

---

## 8. Step 5 — Concept Re-clustering

**Зачем:** организовать факты в концепты/иерархию — «хорошо организуется».

**Как:** `concept_emergence.py` (Hebbian co-occurrence) + эмбеддинги Step 1 → (пере)формировать
ProtoConcepts, обновлять членство фактов в концептах, строить связи через `knowledge_linker`
(`enables/precedes/causes`). Продвижение ProtoConcept → концепт — через существующий `concept_promote`.

```json
{ "cluster": { "concept_id": "concept.grain_processing", "members": 9, "new": 2, "updated": 7 } }
```

---

## 9. Output — consolidation_report

```json
{
  "consolidation_report": {
    "run_id": "sleep_20260601_0300",
    "started_at": "2026-06-01T03:00:00Z",
    "facts_examined": 1842,
    "merged_facts": 37,
    "corroboration_updates": 91,
    "promoted": { "Observed->Supported": 44, "Supported->Validated": 12 },
    "contradictions_found": 6,
    "contradictions_auto_resolved": 4,
    "facts_deprecated": 14,
    "clusters_updated": 22,
    "errors": 0,
    "dry_run": false,
    "requires_review": true,
    "review_items": ["contradiction:user.material_choice", "merge:low_conf_cluster_7"]
  }
}
```

Возвращается из `run_consolidation` (совместимо: объект с `.to_dict()`), логируется
`SleepTimeWorker`, доступен через `GET /memory/consolidate/last` (P1) и `POST /memory/consolidate`.

---

## 10. Safety invariants

| # | Инвариант | Обеспечение |
|---|-----------|-------------|
| **I-A** | Нет физического DELETE | только `transition_esm` + `invalidate_edge` (set `t_*_end`); дубликаты → `Deprecated` |
| **I-B** | Все ESM-переходы через матрицу | вызовы только `store.transition_esm(...)` |
| **I-C** | Truth Gate не обходится | повышение только через `promotion_policy`/`truth_gate`, не прямой UPDATE |
| **I-D** | Ring Zero / ImmutableCore неприкосновенны | исключены из dedup/decay/supersession |
| **I-E** | Обратная связь/польза → salience, НЕ truth | feedback меняет retrievability, никогда `truth_status`/`confidence` |
| **I-F** | Идемпотентность | повторный прогон на неизменном сторе → 0 изменений |
| **I-G** | Bounded & Slow-Path-only | `max_batch`, async/idle; НИКОГДА в `/query` (инвариант I28 dual-process) |
| **I-H** | Провенанс на каждое изменение | `by="sleep_consolidation"`, `caused_by`, run_id в истории |
| **I-I** | dry_run | при `dry_run=true` отчёт считается, но переходы НЕ применяются |

---

## 11. P0 implementation

**Объём P0 (по приоритету ChatGPT-аудита):**
- **P0.1 Semantic Dedup → Corroboration** — `core/semantic_dedup.py` (новый): кластеризация по
  эмбеддингам + слияние источников → подаёт corroboration в готовый `promotion_policy`.
- **P0.2 Contradiction Resolver** — `core/contradiction_resolver.py` (новый): только явная
  супрессия (temporal + маркеры), ребро `superseded_by`, остальное → `requires_review`.
- **P0.3 Sleep Consolidation Loop** — оркестратор `core/sleep_consolidation.py`, который связывает
  шаги и возвращает `consolidation_report`. Подключается в `run_consolidation` **за новым флагом
  `ENABLE_SLEEP_CONSOLIDATION`** (по умолчанию ВЫКЛ); компонуется с `ENABLE_GRADUATED_PROMOTION`.

**Дисциплина (как в текущей сессии):** аддитивно, за флагом, не трогая stable `/query`; каждый
шаг — с тестами; всё в git; по умолчанию поведение системы не меняется.

**P1 (после P0):** Step 4 decay-wiring, Step 5 re-clustering, affordance-обогащение,
`document → facts`, событийный вход (memory_events), `GET /memory/consolidate/last`.

**P2:** Gaps/Curiosity loop, Response-feedback loop (строго по I-E).

```text
P0.1 dedup→corroboration   ┐
P0.2 contradiction resolver├─► P0.3 sleep loop (flag) ─► consolidation_report
(reuse promotion_policy)   ┘
```

---

## 12. Tests (P0)

**`tests/test_semantic_dedup.py`**
- два почти-дубликата (ru+en, sim≥0.92) → 1 канонический + объединённые источники;
- дубликат → `Deprecated` с ребром `merged_into` (no-DELETE: оба факта существуют);
- разные по смыслу факты (sim<0.92) → НЕ сливаются;
- `embedder=None` → шаг безопасно пропускается (graceful).

**`tests/test_contradiction_resolver.py`**
- новый факт о том же субъекте + маркер коррекции → старый `Contradicted`, ребро `superseded_by`;
- старый факт НЕ удалён (виден, с провенансом);
- неоднозначный кластерный конфликт → `requires_review=true`, авто-резолва нет.

**`tests/test_sleep_consolidation.py`**
- флаг ВЫКЛ → `run_consolidation` = прежний наивный путь (бит-в-бит);
- флаг ВКЛ → отчёт-схема валидна, шаги отработали;
- **идемпотентность** (I-F): второй прогон → `merged=0, promoted={}, deprecated=0`;
- **I-D**: Ring Zero/ImmutableCore не тронуты;
- **I-E**: симуляция feedback меняет salience, но `truth_status` неизменен;
- **I-I**: `dry_run=true` → отчёт ненулевой, состояния НЕ изменились.

---

## Приложение A — связь Fast Path (RFC-0081) ↔ Slow Path (RFC-0082)

```text
RFC-0081  Fast Path (сейчас, session):
   Decay → Reactivation → Observer → RetrievalDirective → ответ

RFC-0082  Slow Path (ночью, consolidation):
   Promotion → Dedup → Corroboration → ContradictionResolution → Forgetting → Re-clustering

Контракт между ними:
   Slow Path пишет, что стало известно/слилось/устарело;
   Fast Path читает уже организованную, подтверждённую, непротиворечивую память.
   Section 10 Observer ↔ Step 3 (супрессия MentalBlock).
   Section 11 RetrievalDirective ↔ Step 5 (концепты как цели ретрива: type=affordance_lookup и др.).
```
