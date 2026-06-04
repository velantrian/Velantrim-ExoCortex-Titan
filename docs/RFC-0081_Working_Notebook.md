# RFC-0081 — Exocortex Mirror / Working Notebook (Fast-Path понимание пользователя)

> **Статус:** P0 РЕАЛИЗОВАН (`core/working_notebook.py`) · **Слой:** L1.75 (между L1-контекстом и L2-концептами)
> **Дата:** 2026-05-31 · **Линия:** очищено из переписки `Что надо-.txt` (дедуп + калибровка чисел)
> **Связь:** RFC-0080 (Cognition Layer) · RFC-0082 (Sleep Consolidation, Slow Path) · код: `core/working_notebook.py`
>
> ⚙️ **Все числовые пороги ниже — НАСТРАИВАЕМЫЕ ДЕФОЛТЫ, требуют калибровки на данных.**
> (Урок: порог дедупа из переписки 0.92 оказался завышен → откалиброван до 0.78. Числа здесь — стартовые.)

---

## 1. Purpose
Дать системе **оперативную модель текущего мышления пользователя** — маленькими блоками сути
(цель, ограничения, приоритеты, материалы, открытые вопросы) — которая строится молча в реальном
времени **до retrieval и ответа**. Система перестаёт реагировать на последние слова и начинает
вести диалог в рамках истинной ментальной модели пользователя («думай, как я»).

## 2. Non-Goals
- ❌ НЕ источник истины (мысли ≠ факты мира).
- ❌ НЕ пишет в L3 Graph (только через Truth Gate, как и всё остальное).
- ❌ НЕ заменяет LLM/генерацию — только управляет вниманием и формирует директиву.
- ❌ НЕ требует LLM в P0 (детерминированная эвристика; семантика — P1).

## 3. Data Contracts
Реализовано в `core/working_notebook.py`.

**MentalBlock:** `id`, `type` (`goal`/`constraint`/`priority`/`material`/`open_question`/`topic`/`detail`),
`text`, `base_priority`, `current_score`, `state` (ACTIVE/WARM/COLD/DORMANT), `missed_turns`,
`last_touched_turn`, `access_count`, `protected`, **`truth_status="USER_STATED"`**.

**NotebookState (на сессию):** `session_id`, `turn`, `core_goal`, `blocks[]`.

## 4. Invariants
| # | Инвариант |
|---|---|
| I-1 | **`USER_STATED ≠ FACT`** — каждый блок помечен `truth_status=USER_STATED`; не смешивается с verified-графом. |
| I-2 | **Read-Only L3** — блокнот только читает из L3 (через Retrieval), писать в долгую память не может. |
| I-3 | **Decay affects attention, not truth** — затухание убирает из фокуса, не меняет истину и не удаляет. |
| I-4 | **Mandatory compression** — в LLM идёт `NotebookState` + найденные факты, а не сырой диалог (экономия токенов). |
| I-5 | **User correction > mention_boost** — явное отрицание пользователя сильнее автоматического воскрешения. |

## 5. Pipeline Integration
```
User Message → 📓 Working Notebook (update blocks, decay, reactivation) → directive()
            → GoalFrame/Retrieval (учитывает core_goal + constraints) → Facts Pack → Truth Gate → LLM → Answer
```
Блокнот стоит ПЕРЕД retrieval; его `directive()` сжимает «о чём думает пользователь» в короткую инструкцию.
*(Wiring в `/query` — следующий шаг интеграции, см. Roadmap.)*

## 6. Decay Policy (Section 8) — ⚙️ настраиваемые дефолты
`Score = base_priority × exp(−λ × missed_turns)`. λ по типу (медленнее тухнут ограничения/цели):

| Тип | λ (дефолт) | base_priority |
|---|---|---|
| 🛡️ protected | 0.00 | — |
| ⚖️ constraint | 0.03 | 0.90 |
| 🔥 priority | 0.05 | 0.85 |
| 🎯 goal | 0.06 | 0.92 |
| ❓ open_question | 0.10 | 0.70 |
| 🧱 material/topic | 0.12 | 0.72 / 0.60 |
| 🧩 detail | 0.20 | 0.50 |

**Состояния:** ACTIVE ≥ 0.70 · WARM 0.40–0.69 · COLD 0.15–0.39 · DORMANT < 0.15.
DORMANT = убран из активного промпта, **не удалён** (хранится, воскрешаем).

## 7. Reactivation / Mention Boost (Section 9) — ⚙️ дефолты
Повторное касание темы возвращает блок в фокус. P0: совпадение по id ИЛИ лексическому overlap (Jaccard ≥ 0.5).
**P1:** семантическая реактивация (alias/concept match по эмбеддингам), 3 уровня совпадения (exact/alias/concept),
`concept_match` не поднимает выше WARM без подтверждения; поле `blocked_by_user_correction` (I-5).

## 8. Observer Drift Check (Section 10) — P1
Контрольный слой над Decay+Reactivation: ловит `false_reactivation`, `stale_constraint`, `topic_switch`,
`core_goal_drift`, `overboosting`, `contradiction_detected`, `truth_scope_leak`. Действия: LOG / WARNING /
downgrade / require_confirmation / GUARDIAN_BLOCK. **Не реализовано в P0.**

## 9. MVP / P0 — что РЕАЛИЗОВАНО
`core/working_notebook.py` (флаг `ENABLE_WORKING_NOTEBOOK`, без LLM, no-L3-write):
- ✅ эвристическая экстракция блоков из сообщения; ✅ turn-based decay (Section 6);
- ✅ реактивация по id/лексике (Section 7 P0); ✅ состояния; ✅ `core_goal`; ✅ `directive()`.
- ✅ `tests/test_working_notebook.py` (8 тестов).

## 10. Risks
- **State drift** — резкая смена темы; смягчается decay + (P1) Observer.
- **Галлюцинация намерений** — грубая эвристика может выдумать блок; смягчается (P1) Observer + семантика.
- **Качество экстракции** — P0 эвристика груба; P1 = лёгкая модель/LLM-экстрактор.

## 11. Roadmap
| Этап | Что | Статус |
|---|---|---|
| P0 | Схема + decay + reactivation(lex) + directive | ✅ реализовано |
| P1 | Семантическая экстракция + concept-match реактивация | 🔜 |
| P1 | **Wiring в `/query`** (директива перед retrieval) | 🔜 (вариант 2) |
| P1 | Observer Drift Check (Section 10) | 📋 |
| P2 | Калибровка λ/порогов на реальных диалогах (бенчмарк) | 📋 |
