# 🗺️ Velantrim — Карта-реконсиляция архитектуры (single source of truth)

> **Дата:** 2026-05-31 · **Автор:** Velantrim × Claude
> **Зачем:** дизайн Velantrim разошёлся на **4 параллельные линии** в разных документах и чатах,
> которые НЕ согласованы по именам компонентов, нумерации слоёв и даже канонической формуле.
> Этот документ сводит их в одну непротиворечивую карту и фиксирует **канонический словарь**.
> Источники проанализированы 2026-05-31: переписка `Что надо-.txt`, handoff `OPENCLAW_…`,
> стратег-доки «От фрактала к кристаллу» / «…к когнитивной модели», и **код V8.6** (истина).
>
> **✅ РЕШЕНИЯ АВТОРА (2026-05-31):**
> 1. Систему и существующие компоненты **НЕ переименовывать** — канон = имена V8.6 as-is; новое только добавляем.
> 2. Линия 🟠 **OpenClaw — ИСКЛЮЧЕНА** (чужой проект, не обогащаем). В карте оставлена лишь как «не наше».

---

## 1. Четыре линии дизайна (что где живёт)

| Линия | Где | Суть | Статус |
|---|---|---|---|
| 🟢 **CODE V8.6** | `VELANTRIM_ExoCortex_V8.6/core/*` | Реально работающий код: ESM, Truth Gate, Velum, Concept Emergence, Causal Graph, Essence, promotion, FSRS | **ИСТИНА** (что есть) |
| 🔵 **Correspondence** | `Documents/Что надо-.txt` | RFC-0080/0081: Exocortex Mirror / Working Notebook (L1.75), MentalBlock, Decay/Reactivation/Observer | **дизайн, кода нет** |
| 🟣 **Strategy** | `Documents/…/От_фрактала_к_кристаллу*.md`, `…когнитивной_модели*.md` | «Crystal Memory» + когнитивная типизация (episodic/semantic/procedural), онтология, GNN | **дизайн/исследование** |
| 🟠 **OpenClaw handoff** | `Documents/…/OPENCLAW_MEMORY_ARCHITECTURE…md` | `memory-fabric` (file-first) + Graphiti bridge для рантайма OpenClaw (контекст Wildberries) | **родственный ДРУГОЙ проект** |

**Вывод №1:** ChatGPT ссылался на «RFC-0080 Essence Layer», «Section 10 Observer», «MentalBlock» как на данность — но **они есть только в линии 🔵 (переписка)**. В коде и формальных доках их нет.

---

## 2. ⚠️ Коллизия №1 — нумерация слоёв (самое опасное)

Одни и те же «L1/L2/L3» означают **разное** в каждой линии:

| Слой | 🟢 CODE V8.6 | 🟠 OpenClaw | 🟣 Strategy | 🔵 Correspondence |
|---|---|---|---|---|
| **L0** | Raw Memory | raw events (files) | episodic | сырой ввод |
| **L1** | ESM-факты (SQLite) | episodes | episodic | рабочий контекст |
| **L1.5** | Velum / Salience | — | — | Velum / context hint |
| **L1.75** | — | — | — | **Exocortex Mirror / Working Notebook** |
| **L2** | Concept Emergence | lessons/patterns | semantic | средне-срочные гипотезы |
| **L3** | Causal/graph (Kuzu/Neo4j) | stable principles | semantic | Graph Truth Store |
| **L3.8** | — | — | **Procedural Memory** (вариант) | — |
| **L4 / L4.5** | Causal, Reasoning / Focus·Audit·Volition | — | Procedural (вариант) | Reasoning |
| **L5 / L5.5** | — / Predictive Fusion | — | — | Observer |
| **L6 / L7** | Welfare (L6) | — | Procedural band | Modes / Mission |

> 🔧 **Решение:** канон — **слои из CODE V8.6** (это истина). «Episodes/Lessons/Principles» из OpenClaw —
> это L1→L2→L3 *операционной* памяти, маппятся, но НЕ переопределяют коды V8.6. Процедурная память:
> три адреса-кандидата (L3.8 / L4.5 / L6–7) — **не решено**; рекомендую новый явный `L4.5 Procedural`
> (рядом с Reasoning), не плодить L3.8.

---

## 3. ⚠️ Коллизия №2 — каноническая формула

| Линия | Формула |
|---|---|
| 🟢 CODE V8.6 (README) | `Graph = Truth · LLM = Language · Memory = Physiology · Volition = Agency` |
| 🔵 Correspondence | `Graph = Truth · LLM = Voice · Memory = Physiology · Volition = Agency` |
| 🟣 Strategy | `Graph = Truth · Memory = Physiology · Cognition = Meta-Layer · Integration = Strategy` |

> 🔧 **Решение (рекомендую канон):**
> **`Graph = Truth · LLM = Voice · Memory = Physiology · Cognition = Meta-Layer · Volition = Agency`**
> — объединяет всё без потерь: истина в графе, LLM только язык, память как физиология,
> когниция (понимание сути/интента) — мета-слой, воля — агентность.

---

## 4. ⚠️ Коллизия №3 — имена компонентов

| Концепт | Имена в линиях | Канон (рекоменд.) | Статус в коде V8.6 |
|---|---|---|---|
| Проверка истины | `TruthGate` (🟢🟣) / `TruthLayer` (🟣) | **TruthGate** | ✅ `core/truth_gate.py` |
| Машина состояний | `ESM` (🟢🟣) | **ESM** | ✅ `core/memory.py` |
| «Суть для ответа» | мой `core/essence.py` (gist+цепочка) | **Essence (answer)** | ✅ построен мной |
| «Слой понимания» (future) | `Essence Layer`/`WhyEngine`/`SituationModel` (🔵, RFC-0080) | **Cognition Layer** (чтобы не путать с Essence) | ❌ только дизайн |
| Модель мышления юзера | `Exocortex Mirror`/`Working Notebook` (🔵, L1.75) | **Working Notebook** | ❌ только дизайн |
| Затухание | `Decay Policy` (🔵) / FSRS (🟢) / weight-decay (🟣) | **Decay** (attention) + **FSRS** (memory) | 🟡 `salience_fsrs/vintage_decay` (не подключены) |
| Воскрешение | `mention_boost`/`ReactivationEngine` (🔵🟣) | **Reactivation** | ❌ только дизайн |
| Контроль дрейфа | `Observer`(🔵 §10) / `Observer++`(🟣) / response_audit (🟢) | **Observer** | 🟡 `core/response_audit.py` (частично) |
| Эмёрдженс концептов | `concept_emergence`(🟢) / `…Engine`/`…Detector`(🟣) | **ConceptEmergence** (один) | ✅ `core/concept_emergence.py` |
| Линковщик связей | мой `knowledge_linker.py` | **KnowledgeLinker** | ✅ построен мной |
| Консолидация | `ConsolidationEngine`(🟢🟣) + мой sleep loop (RFC-0082) | **ConsolidationEngine / SleepLoop** | ✅ + RFC-0082 |
| Псевдоним системы | `HYPERIA` (🟣) = Velantrim | **Velantrim** | — |

---

## 5. Инварианты — что согласовано (и это ценно)

Несмотря на расхождения, **три инварианта совпадают во всех линиях** — это твёрдое ядро:
1. **`Graph = Truth`** — истина в графе, не в LLM. (все линии)
2. **No-overwrite / append-and-invalidate** — старый факт не стирается, помечается `invalid`; новый создаётся. (🟢 no-DELETE/`invalidate_edge`; 🔵 superseded_by; 🟣 «пометка invalid»)
3. **`USER_STATED ≠ FACT`** — мысль/намерение пользователя ≠ проверенный факт мира. (🔵 явно; 🟢 ESM-состояния; заложено в RFC-0082 I-E)

И добавочный из 🔵, который стоит сделать каноном: **«Decay affects attention, not truth»** (затухание убирает из фокуса, не удаляет истину).

---

## 6. Что РЕАЛЬНО существует vs дизайн (карта статусов)

```
✅ РАБОТАЕТ В КОДЕ (🟢):
   ESM · TruthGate · Velum(L1.5) · ConceptEmergence · CausalGraph(L3) · HybridRetriever
   + Essence(answer) + promotion_policy + knowledge_linker  ← построены в этой сессии
   🟡 написаны, но не подключены: FSRS(salience/vintage), CoherentCache, response_audit(Observer-частично)

📐 ДИЗАЙН, КОДА НЕТ (🔵 correspondence):
   Working Notebook (L1.75) · MentalBlock схема · Decay/Reactivation/Observer policies
   Cognition Layer (бывш. «Essence Layer» RFC-0080: WhyEngine/SituationModel)
   → мой RFC-0082 (Sleep Loop) = Slow-Path-дополнение к этой линии

🔬 ИССЛЕДОВАНИЕ/СТРАТЕГИЯ (🟣):
   Crystal/онтология · equivariant GNN · Procedural Memory · 5-stage retrieval · 11-dim scoring

🟠 ДРУГОЙ ПРОЕКТ (OpenClaw/Wildberries): memory-fabric + Graphiti bridge — НЕ кодовая база V8.6
```

---

## 7. Рекомендуемый канонический словарь (going forward)

Чтобы прекратить размножение имён, фиксируем:

- **Слои** — по CODE V8.6. Новые: `L1.75 Working Notebook`, `L4.5 Procedural` (если делаем).
- **Формула** — `Graph=Truth · LLM=Voice · Memory=Physiology · Cognition=Meta-Layer · Volition=Agency`.
- **Понимание сути:** `Essence` = суть **фактов для ответа** (есть в коде); `Cognition Layer / Working Notebook` = модель **мышления пользователя** (дизайн). Это РАЗНЫЕ вещи — не путать.
- **Forgetting:** `Decay` (внимание, turn-based, Working Notebook) ≠ `FSRS` (память, time-based, L1–L3). Оба «не трогают truth».
- **RFC-нумерация:** перенести в репозиторий как реальные файлы: RFC-0080 (Cognition Layer), RFC-0081 (Working Notebook: Decay/Reactivation/Observer), RFC-0082 (Sleep Consolidation — уже есть). Тогда ссылки перестанут висеть в воздухе.

---

## 8. Что делать дальше (рекомендация)

1. **Утвердить этот канон** (слои + формула + словарь) — твоё решение как автора.
2. **Перенести 🔵-дизайн в репозиторий** как чистые RFC-0080/0081 (без дублей переписки, числа = «настраиваемые дефолты, требуют бенчмарка»).
3. **Решить судьбу 🟠 OpenClaw-линии:** влить идеи (episodes/lessons/principles, graceful graph-fallback) в канон ИЛИ явно отметить как архив/другой проект.
4. Только потом — код новых органов (Working Notebook P0), уже по единому канону.

> 🧭 **Главный смысл карты:** проблема Velantrim не в нехватке идей, а в том, что идеи живут в 4 несогласованных линиях. Этот документ — первый шаг к одному канону. Код V8.6 = истина; остальное маппится на него.
