# 5. 📜 RFC-MCP-GATEWAY — Capability-based Agent Access

**Статус:** 🔵 DRAFT · **Дата:** 2026-06-06 · [← назад к индексу](README.md)
**Автор-инициатор:** аудит-сессия · **Категория:** доступ к памяти / безопасность / interop

---

## 1. Мотивация

Агентам (Claude / ChatGPT / Cursor / локальные) нужен доступ к памяти Velantrim. Наивный подход — дать одну «write»-функцию и проверять права в рантайме — оставляет дыру: **LLM всё равно видит опасный инструмент и может его вызвать**.

**Идея (источник — [Habr 1044200, Wiki-MCP-Server](https://habr.com/ru/articles/1044200/), апрель 2026):** роли — это не «права», а **разные наборы инструментов**. Если инструмент не зарегистрирован для роли — клиент MCP его не видит, модель физически не может его вызвать.

> ⚠️ **Честная оговорка по источнику:** в статье эффект графа на recall (46.7%→68.3%) измерен на крошечном графе (72 ноды / 215 рёбер) и стек облачный (AlloyDB/Vertex/Gemini, `ai.generate()` в SQL). Берём **архитектурный паттерн доступа**, а не стек и не цифры.

---

## 2. Текущее состояние в Velantrim

| Часть | Статус | Где |
|---|---|---|
| Реестр инструментов по capability | 🟡 контракт готов | Titan `core/tool_registry.py` (5 ролей, capability-chain, MCP-манифест `to_manifest`, флаги `destructive`/`audit`) |
| Реализации инструментов | 🔴 заглушки | `lambda: None` в `register_velantrim_tools` |
| MCP-транспорт (StreamableHTTP/SSE) | 🔴 нет | — |
| Запись только после TruthGate | 🟢 закон | `pipeline.py` / `truth_gate.py` |
| GDPR-инструменты (`forget_fact`/`forget_all`) | 🟡 объявлены, не подключены | `tool_registry.py` (admin) → ждут Phase 1 закалки |

**Вывод:** половина (контракт ролей) сделана; нужно дописать транспорт + реализации и портировать в Crystal (AGPL-3.0) как грантовый deliverable [D3](03_GRANT_DELIVERABLES_NLNET.md).

---

## 3. Дизайн

### 3.1 Роли = наборы инструментов (capability chain)

```
reader      → только чтение (search, get_fact, causal_chain, explain, graph_stats)
researcher  → + предложить гипотезу (propose_hypothesis, find_analogies)
ingester    → + запись в L1/L2 (store_fact, link_entity)   [Observed/Hypothesized]
guardian    → + валидация/переходы (validate_fact, contradict_fact, supersede_fact)
admin       → + деструктив (forget_fact, forget_all, reset_graph)   [GDPR, audit]
```

Каждый уровень включает нижележащие. Инструмент уровня X доступен X и выше; **для ролей ниже — отсутствует в списке** (не «запрещён», а невидим).

### 3.2 Транспорт

```
POST/GET/DELETE /mcp          → StreamableHTTP (MCP 2025-11-25)
GET /mcp/sse + POST /mcp/...   → SSE (legacy 2024-11-05, обратная совместимость)
```
Аутентификация на уровне сессии определяет capability → сервер регистрирует только доступный набор инструментов для этой сессии.

### 3.3 Инварианты безопасности (НЕ нарушать)

```
Graph      = Truth            (источник истины — только граф)
MCP        = Access Layer     (интерфейс, НЕ источник истины)
Capability = Tool Visibility  (нет инструмента в наборе → вызов невозможен)
TruthGate  = Write Gate       (любая запись в канон — только через гейт)
Guardian   = Safety Gate      (деструктив — только admin + подтверждение)
Trace      = Accountability   (каждый mutation оставляет след)
```

### 3.4 LLM как Hypothesis Booster (не источник фактов)

LLM-классификация рёбер/фактов допустима **только** так:
```
LLM_OUTPUT → claim_type=HYPOTHESIS, source_status=LLM_OUTPUT
           → Pending слой → Guardian / TruthGate / human review
           → только потом, может быть, L3
```
❌ Запрещено: `LLM-вывод → сразу FACT/WORLD_FACT`. (Уже закон Velantrim.)

### 3.5 Обогащение edge-registry (опционально, поверх 15 типов)

Идея из статьи: типы рёбер несут не только имя, но и семантику доступа/веса. Поверх `causal_graph.py` (15 типов) добавить реестр политик:
```json
{
  "edge_type": "REQUIRES",
  "direction_rule": "A requires B",
  "weight": 0.9,
  "truth_effect": "prerequisite",
  "allowed_claim_types": ["WORLD_FACT", "METHOD", "MODEL"],
  "source_required": true,
  "review_required": false,
  "reversible": false
}
```

### 3.6 Graph observability tools (для reader)

Экспонировать read-only диагностику (опирается на существующие `fact_integrity.py` / `semantic_dedup.py`):
`graph_stats`, `graph_path A→B`, `graph_neighbors`, `graph_contradictions`, `graph_dedup`, `graph_orphans`, `integrity` (агрегат → грант [D4](03_GRANT_DELIVERABLES_NLNET.md)).

---

## 4. Non-goals (чего НЕ делаем)

- ❌ Не тянем облачный стек (AlloyDB / Vertex / Gemini-in-SQL) — против local-first. У нас SQLite + Kuzu/Ladybug.
- ❌ MCP не становится источником истины — только контролируемый доступ.
- ❌ Basic Auth как единственная защита — для Velantrim нужен capability + audit + signed write + TruthGate.

---

## 5. Критерии приёмки

1. `reader`-сессия **не содержит** write/destructive инструментов в списке (проверка: их нет в манифесте).
2. Деструктивный инструмент требует `admin` **и** пишет в audit/erasure-log.
3. Любая запись проходит TruthGate; bypass невозможен (contract-тест).
4. Оба транспорта (StreamableHTTP + SSE) обслуживают одну сессию.
5. Каждый mutation оставляет trace (accountability).
6. Реализация целиком открыта (AGPL-3.0) и переносима в Crystal.

---

## 6. Грантовая ценность (почему это сильный пункт NLnet)

- **Interop/commons:** MCP — открытый протокол; gateway переиспользуем другими проектами.
- **European dimension / privacy:** ролевое разделение записи + GDPR-инструменты в admin.
- **Verifiable/auditable:** каждый mutation → trace; observability-инструменты.
- **De-risked:** контракт уже работает в Titan (`tool_registry.py`) → «не обещаем, у нас есть прототип».

> 💡 Подавать как deliverable [D3](03_GRANT_DELIVERABLES_NLNET.md). Реализация = Phase 5 [плана закалки](04_TITAN_HARDENING_PLAN.md). Открытая часть → Crystal; продуктовая оркестрация инструментов → остаётся моатом Titan ([IP-граница](02_IP_BOUNDARY_OPEN_VS_MOAT.md)).
