# RFC-0080 — Cognition Layer (понимание сути · интент · почему)

> **Статус:** частично РЕАЛИЗОВАН · **Слой:** Meta-Layer (формула: `Cognition = Meta-Layer`)
> **Дата:** 2026-05-31 · **Линия:** очищено из переписки (ранее называлось «Essence Layer» / WhyEngine /
> SituationModel / EssenceRecord — переименовано в **Cognition Layer**, чтобы не путать с `core/essence.py`).
> **Связь:** RFC-0081 (Working Notebook — модель мышления ПОЛЬЗОВАТЕЛЯ) · RFC-0082 (Slow Path).

---

## 1. Purpose
Cognition Layer — это **мета-слой понимания** поверх памяти-истины. Он отвечает на вопросы
«что здесь главное?», «почему?», «что пользователь на самом деле имеет в виду?» и превращает
набор проверенных фактов в **короткий человеческий вывод** со смысловой цепочкой и провенансом.

Различие (важно, чтобы не путать имена):
- **RFC-0080 Cognition Layer** = понимание ЗНАНИЯ (суть фактов, причинность, интент запроса).
- **RFC-0081 Working Notebook** = модель мышления ПОЛЬЗОВАТЕЛЯ в сессии (цель/ограничения).
- Оба — «тёплые» слои НАД холодным графом-истиной; ни один не пишет в L3 напрямую.

## 2. Non-Goals
- ❌ НЕ источник истины (Graph = Truth; Cognition только осмысляет проверенное).
- ❌ НЕ скрывает неопределённость ради красивого вывода.
- ❌ НЕ «личность»/эмоции — только ясность мышления.

## 3. Компоненты и их статус в V8.6
| Компонент (канон) | Роль | Реализация в V8.6 | Статус |
|---|---|---|---|
| **EssenceComposer** | суть + смысловая цепочка + короткий ответ + WhyTrace | `core/essence.py` (`compose_essence`) | ✅ реализован |
| **UnderstandingLayer** | причинность + living context + ответ «для ребёнка/инженера» | `core/understanding_layer.py` | ✅ есть |
| **IntentDetector** (WhyEngine) | «что пользователь имеет в виду» | `core/dialogue_essence.py::_detect_intent` | 🟡 частично |
| **SituationModel** | текущая ситуация/контекст рассуждения | пересекается с Working Notebook (RFC-0081) | 🟡 future |
| **EssenceRecord** | сохранённая «суть» с провенансом | `Essence.to_dict()` (gist/chain/why) | ✅ покрыто |
| **KnowledgeLinker** | связи фактов → causal-рёбра для цепочки | `core/knowledge_linker.py` | ✅ реализован |

## 4. Invariants
1. **Graph = Truth** — Cognition осмысляет, но истину хранит граф; вывод только из Validated/Supported.
2. **Сохранять uncertainty** — Essence помечает предварительность (Supported / низкая confidence).
3. **Хранить WhyTrace** — каждый вывод объясним (почему выбрана эта суть, какие факты/связи).
4. **Не писать в L3 без Truth Gate** — Cognition не повышает факты в обход верификации.

## 5. Каноническая формула (место Cognition)
```
Graph = Truth · LLM = Voice · Memory = Physiology · Cognition = Meta-Layer · Volition = Agency
```
Cognition = «способность классифицировать знания и понимать интент» (мета-слой над памятью).

## 6. Pipeline
```
Validated факты + causal-рёбра (KnowledgeLinker) → EssenceComposer → {суть, цепочка, WhyTrace, uncertainty}
   ↑ интент запроса (IntentDetector) направляет, что именно осмыслять
```
Реализовано: `generate_answer` (за флагом `ENABLE_ESSENCE`) уже отдаёт «Суть + Цепочка + WhyTrace».

## 7. Roadmap
| Этап | Что | Статус |
|---|---|---|
| P0 | EssenceComposer (gist/chain/WhyTrace) + KnowledgeLinker | ✅ реализовано |
| P1 | IntentDetector усилить (маршрутизация по типу вопроса: definition/causal/affordance/predict) | 🔜 |
| P1 | LLM-композер поверх P0 (креативный синтез далёких концепций) | 📋 |
| P2 | SituationModel как явный объект (связать с Working Notebook RFC-0081) | 📋 |

> **Итог:** Cognition Layer — это «что главное + почему + интент». В V8.6 его ядро (EssenceComposer +
> KnowledgeLinker) уже работает за флагом; остальное (богатый интент, LLM-синтез) — дорожная карта.
