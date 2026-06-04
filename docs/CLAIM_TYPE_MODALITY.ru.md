# 🏷️ Эпистемическая гигиена памяти — claim_type / origin_type (v8.7)

> **Статус:** реализовано в `master` (2026-06-02), модальность в pipeline — за флагом
> **Зачем:** чтобы система помнила **чувства, мнения и опыт**, но не превращала их в
> **ложные факты о мире**. «память ≠ знание · чувство ≠ факт · важность ≠ истинность».
> **Происхождение:** синтез внешних аудитов (ChatGPT/DeepSeek/Qwen/Gemini), отфильтрованный
> по реальному коду. Большинство «спек» уже было в каноне; здесь — что реально добавлено.

---

## 🧭 Три ортогональные оси факта (не смешивать)

| Ось | Поле | Вопрос | Где |
|-----|------|--------|-----|
| Верификация | `epistemic_state` (ESM) | насколько проверено? | `memory.py` (не трогалось) |
| **Модальность** | **`claim_type`** | что это за утверждение? | `validators.py`, колонка `facts` |
| **Происхождение** | **`origin_type`** | откуда пришло? | `validators.py`, колонка `facts` |
| Надёжность | `confidence` | насколько достоверно? | существующее |
| Важность | `salience` (не `significance_score`) | насколько важно для retrieval? | `salience.py` (переиспользуется) |

`claim_type` ≠ `epistemic_state`: факт может быть `Validated` **и** `EMOTION` одновременно.

---

## 📋 Значения

**`claim_type`** (`core/validators.py::ClaimType`): `WORLD_FACT`, `USER_EXPERIENCE`, `EMOTION`,
`INTERPRETATION`, `OPINION`, `GOAL`, `PREFERENCE`, `SYSTEM_NOTE`, `UNKNOWN`.
- `SUBJECTIVE_TYPES` = {EMOTION, OPINION, INTERPRETATION, PREFERENCE} — не могут стать `ImmutableCore`.
- `SELF_VALIDATING` = субъективные + {GOAL, USER_EXPERIENCE, SYSTEM_NOTE, UNKNOWN}.

**`origin_type`** (`OriginType`): `USER_REPORTED`, `SYSTEM_OBSERVED`, `DERIVED`, `EXTERNAL`,
`LLM_OUTPUT`, `SYSTEM_GENERATED`, `UNKNOWN`. (Переименовано из спек-`source_status`, чтобы не
конфликтовать со state `Observed` в ESM.)

---

## 🤖 Классификатор `core/claim_classifier.py`

Детерминированный, **ru-first**, без LLM (P0). Маркеры: «я чувствую» → EMOTION, «я думаю/мне
кажется» → OPINION/INTERPRETATION, «я хочу/моя цель» → GOAL, «я помню» → USER_EXPERIENCE,
«согласно источнику…» → WORLD_FACT+EXTERNAL. Явный `claim_type` в `store_fact` **побеждает**
классификатор. Неуверенность → `UNKNOWN`.

---

## ⚖️ Type-aware TruthGate (`core/truth_policy.py`)

- **`modality_guard(fact, target_state)`** — БЛОКИРУЕТ недопустимое: субъективное → `ImmutableCore`;
  `WORLD_FACT`+`LLM_OUTPUT` без evidence → `Validated/ImmutableCore`; **`UNKNOWN` без evidence →
  `Validated/ImmutableCore`** (неклассифицированное не трактуется как факт мира).
- **`recommend_target_state(fact)`** — РЕКОМЕНДУЕТ потолок промоушна (матрица `claim_type×origin_type`):
  WORLD_FACT+EXTERNAL+evidence→Validated; WORLD_FACT+USER_REPORTED→Hypothesized;
  WORLD_FACT+LLM_OUTPUT→Observed; субъективное+человек→Validated; субъективное+LLM→Hypothesized.
- ADVISORY: промоушн всё равно через `transition_esm()` (матрица ESM) + `modality_guard`.

---

## ⚙️ Подключение к pipeline (за флагом `ENABLE_TRUTH_POLICY`, по умолчанию **OFF**)

`pipeline.run` **шаг 6**:
- **OFF (дефолт):** легаси — все факты → `Validated`, `truth_status=VERIFIED`. Поведение прежнее.
- **ON:** промоушн по `recommend_target_state` (rank-guard — **только вперёд, без демоушна**);
  `truth_status=VERIFIED` **только** для `Validated AND claim_type==WORLD_FACT`. EMOTION/OPINION
  валидны как модальность, но `UNVERIFIED`. Ответ получает честные метки («Вы сообщали о чувстве…»).

**Важный инвариант (всегда вкл):** `build_facts_pack` при ре-сторе на ретриве **сохраняет уже
присвоенную модальность** — классификатор не переклассифицирует `EMOTION→WORLD_FACT` по тексту.

---

## ✅ Что НЕ сделано (осознанно)

- `significance_score` как поле — **дубль** существующего `salience` (оси важность/надёжность уже разделены).
- Write-path TruthGate (`/facts`, `/ingest`), `core3_adapter` (мёртвый код), `synchronous=FULL` на
  всех стораджах — отдельные крупные решения, только через diff-plan.
- L2-таблица, episodic graph, Kuzu-замена SQLite — преждевременно (см. `POLYGLOT_EPISTEMIC_INVARIANTS.ru.md`).

---

## 🧪 Тесты
`tests/test_claim_type.py` (24), `tests/test_pipeline.py::test_pipeline_step6_modality_*` (2).
Полный сьют: 945 passed / 0 failed.

> **Канон:** *TruthGate не решает, существует ли чувство — он решает, можно ли трактовать его как
> факт о мире. Чувство валидно как чувство. Только источник + след + отсутствие противоречий →
> WORLD_FACT.*
