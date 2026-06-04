# 🧠 BICA Alignment Layer — карта когнитивных функций Velantrim

**Статус:** P2 / Research + Grant Mode — карта и чеклист, **не код и не runtime-модуль**
**Runtime:** не активируется; ничего не исполняет, не пишет в память, не меняет `/query`
**Правило:** этот документ только **классифицирует и проверяет** существующие модули.
Любое изменение поведения — отдельный RFC + тесты + feature flag.

---

## Зачем это

BICA (Biologically Inspired Cognitive Architectures) — рамка для описания систем
через **когнитивные функции** (внимание, рабочая память, причинность, консолидация…),
а не через «базы данных + LLM».

Назначение слоя в Velantrim — **двойное и узкое**:
1. 🧾 **Grant Mode** — позиционировать проект как
   *local, provenance-first, graph-grounded, biologically-inspired cognitive architecture*,
   а не «чат-бот с памятью».
2. 🧪 **Eval / Architecture** — чеклист, по которому видно **архитектурные дыры**:
   если когнитивной функции нет ни в одном модуле — это сигнал, а не повод срочно строить.

> ⚠️ **Чем BICA здесь НЕ является.** Не «мозг поверх всего», не замена Graph=Truth,
> не автономный агент, не оправдание для новых модулей, не заявка на AGI.
> Velantrim сознательно **не** берёт из BICA антропоморфный балласт: `self`,
> эмоции-как-карта-амигдалы, social abilities, embodiment. Цель — **эпистемический
> инструмент проверяемого знания**, а не копия человеческого разума.

---

## 🗺️ BICA-карта: функция → существующий модуль Velantrim

Все модули в колонке справа уже есть в коде (проверено). BICA лишь даёт им единый язык.

| Когнитивная функция | Модуль(и) Velantrim |
|---|---|
| 👁️ Perception (вход) | file_parsers, ingest, console / chat |
| 🧭 Attention (внимание) | `working_notebook` / Exocortex Mirror, Retrieval Directive |
| 🎯 Motivation / Goal | `goal_frame`, `goal_stack`, `gap_detector` |
| 🧠 Working Memory | `working_notebook`, session state |
| 📚 Semantic Memory | `causal_graph` + Kuzu/Ladybug graph, `memory` (L3) |
| 🗂️ Episodic Memory | ESM (`esm`), bi-temporal факты, `memory_ops` reasoning_traces |
| 🧬 Procedural Memory | `reasoning_bank`, action/strategy templates |
| 🔥 Salience / важность | `salience`, `velum`/`velum_bridge`, `interoception`, `actr_activation` |
| 🕸️ Causal Reasoning | `causal_graph` (15 типов), `understanding_layer`, `graph_lab` (NetworkX) |
| 🔮 Prediction | `predict_intervention` / `counterfactual` (Pearl L2), `predictive_fusion` |
| 🧩 Gist / Essence | `essence` (`compose_essence`), `living_context` |
| ⚖️ Evaluation / Truth | `truth_gate`, `truth_policy`, `observer`, `mhi`, eval-линейка |
| 🛡️ Ethics / Safety | `graph_ring_zero` / Guardian, `audit_chain`, `volition_gate` |
| 🌙 Consolidation | `consolidation_engine`, `sleep_time_worker`, `fsrs`/`decay_orchestrator` |
| 🗣️ Speech (рендер) | `llm_router`, `llm_stream` (LLM = голос, не источник истины) |

**Вывод карты:** Velantrim **уже** покрывает почти все BICA-функции — просто без ярлыка.
Это аргумент для гранта и подтверждение зрелости архитектуры.

---

## 🧪 BICA-eval — 6 вопросов (чеклист зрелости)

Не автотесты — **ревизионный чеклист**. Для каждого: где реализовано + как проверить.
Можно со временем превратить в тесты поверх существующей eval-линейки
(`tests/test_eval_golden.py`).

| # | Вопрос | Где в Velantrim | Как проверить сейчас |
|---|---|---|---|
| **BICA-01** | Система удерживает **цель**? | `goal_frame` → `attention_router` (goal_fit) | вход меняет приоритет retrieval |
| **BICA-02** | Не смешивает **факт и мнение/гипотезу**? | ESM-статусы, `truth_policy`, `observer` `truth_scope_leak` | golden Contradicted-факты → `reject`/флаг |
| **BICA-03** | Строит **модель ситуации / суть**? | `essence.compose_essence`, `living_context` | `/query` возвращает essence-блок |
| **BICA-04** | Может объяснить **причинную цепочку**? | `causal_graph` WhyTrace, `graph_lab` paths | explain/why по fact_id даёт цепочку |
| **BICA-05** | Отправляет **гипотезу в Pending**, а не сразу в FACT? | ESM (`Observed→…`), `memory_ops` inbox, TruthGate | LLM-вывод не становится FACT напрямую |
| **BICA-06** | **Консолидирует** опыт после сессии? | `consolidation_engine`, `sleep_time_worker` | sleep-цикл: дедуп + продвижение |

> Зелёный по всем шести = архитектура когнитивно полна. Красный = точная дыра,
> а не расплывчатое «надо улучшить».

---

## 🧭 Статус и границы

- **P2 / опционально.** Не входит в MVP-core, не на горячем пути.
- **Документ, не подсистема.** Не добавляет зависимостей и не меняет поведение.
- **Инвариант канона (из аудитов):** *facts are not executable instructions* —
  данные (claim/evidence) и команды (policy/Ring Zero) разделены; LLM говорит, но не правит.
- **Возможные инкременты позже** (каждый — отдельный RFC + флаг + тесты):
  path-finding в эпизодическом пространстве (расширение `graph_lab`),
  schema-evolution поверх `concept_emergence`/`concept_promote`.
