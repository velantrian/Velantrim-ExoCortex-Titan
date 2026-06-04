# 🏛️ Velantrim ExoCortex — Четыре оси архитектуры

> V8.7 Titan / ChatGPT-аудит · 3 июня 2026

---

## 📐 ЧЕТЫРЕ ОРТОГОНАЛЬНЫЕ ОСИ ПАМЯТИ

Каждый факт в Velantrim существует в четырёхмерном пространстве. Оси независимы — изменение координаты на одной оси не меняет остальные.

```
                    EPISTEMIC AXIS (насколько истинно)
                              ↑
                              │
    IDENTITY AXIS ←───────────●───────────→ PROCESSING AXIS
    (насколько это Я)          │           (как обработано)
                              │
                              ↓
                    PROVENANCE AXIS (откуда и как)
```

---

## 🔬 Ось 1 — Эпистемическая (насколько истинно)

**Вопрос:** можно ли этому верить?

| Поле | Значения | Где |
|------|---------|-----|
| `claim_type` | WORLD_FACT · USER_STATED · OPINION · EMOTION · UNKNOWN | `cognitive_fact.py` |
| `source_status` | USER_REPORTED · LLM_OUTPUT · IMPORT · MANUAL · VERIFIED | `cognitive_fact.py` |
| `confidence` | 0.0 – 1.0 | `memory.py` |
| `epistemic_state` | Observed → Hypothesized → Supported → Validated → ImmutableCore | `esm.py` |
| `truth_scope` | personal_identity · world_fact · shared_knowledge · cultural_belief | `cognitive_fact.py` |

**Контроль:** `truth_gate.py` + `truth_policy.py` + `write_gate.py` + GCR-фильтр

---

## 🏗️ Ось 2 — Обработки (как глубоко обработано)

**Вопрос:** на какой стадии обработки находится этот факт?

| Слой | Стадия | Где |
|------|--------|-----|
| L0 | Raw — сырой ввод, иммутабельный | `raw_memory.py` |
| L1 | Episodic — привязан к сессии | `memory.py` (STM) |
| L1.5 | Velum — co-occurrence преграф | `velum.py` |
| L2 | Clustered — среднесрочные темы | `fractal_memory.py` |
| L3 | Graph — долгосрочный граф истины | `memory.py` (LTM) + LadybugDB |
| L3.5 | Immutable Core — снапшоты | `immutable_core_scheduler.py` |
| L4 | Reasoning — паттерны рассуждения | `reasoning_bank.py` + `causal_graph.py` |
| L5 | Anticipatory — предсказание | `sae_prediction.py` + `lsm_prediction.py` |
| L5.5 | Predictive Fusion — арбитр | `predictive_fusion.py` |
| L6 | Values — ценности и благополучие | `welfare_monitor.py` + `volition_gate.py` |

---

## 🧬 Ось 3 — Идентичности (насколько это Я)

**Вопрос:** это факт о мире или факт обо мне?

| Слой | Категория | Где |
|------|-----------|-----|
| F1 | Identity Kernel — ценности, принципы | `identity_layer.py` VALUES |
| F2 | Life Context — работа, семья, интересы | `identity_layer.py` WORLDVIEW |
| F3 | Raw Archive — полная история | `identity_layer.py` BIOGRAPHY |
| F4 | Autobiographical Narrative — кто я | `identity_layer.py` COMPASS |
| — | CoreMemoryBlocks — оперативный профиль | `sleep_time_worker.py` |
| — | WorkingNotebook — текущая модель мышления | `working_notebook.py` |
| — | GoalFrame — активные цели | `goal_frame.py` + `goal_stack.py` |

**self_axis:** 1.0 = это Я, 0.0 = чистый факт о мире.

**truth_scope:** personal_identity (истинно как самоописание), world_fact (объективно).

---

## 🔗 Ось 4 — Провенанса (откуда и как менялось)

**Вопрос:** какой путь прошёл этот факт от стимула до ответа?

| Звено | Что | Где |
|-------|-----|-----|
| 1. Стимул | input_event_id → stimulus_type | `stimulus_map.py` |
| 2. Извлечение | claim_type + source_status | `cognitive_fact.py` |
| 3. Проверка | TruthGate verdict | `truth_gate.py` |
| 4. Запись | WriteGate → store | `write_gate.py` + `memory.py` |
| 5. Цепочка | append-only hash-chain | `provenance_chain.py` |
| 6. Снапшот | SHA-256 delta snapshots | `immutable_core_scheduler.py` |
| 7. Ответ | response_id → stimulus_map | `stimulus_map.py` |
| 8. Аудит | audit_chain + observer | `audit_chain.py` + `observer.py` |

**Трассируемость:** stimulus → factor → TruthGate → response. В обе стороны.

---

## 🧭 КАК ЧИТАТЬ ЭТУ КАРТУ

Любой модуль Velantrim можно позиционировать в этой системе координат:

```
cognitive_runtime.py  → Ось 2: L3–L4  | Ось 4: звено 4
identity_layer.py     → Ось 3: F1–F4  | Ось 1: personal_identity
stimulus_map.py       → Ось 4: звенья 1+7
truth_gate.py         → Ось 1: контроль | Ось 4: звено 3
velum.py              → Ось 2: L1.5    | Ось 4: не пишет в граф (read-only)
```

---

> **Формула Velantrim v8.7:**
> Memory stores significance. SQLite preserves evidence. TruthGate protects truth.
> Provenance preserves origin. Identity Axis preserves self. Graph maps relations.
> Reasoning builds chains. LLM only speaks. GCR guards the boundary.
