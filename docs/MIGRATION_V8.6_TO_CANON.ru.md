# 🗺️ План миграции V8.6 → Канон (Движок Истины + Ring Zero)

> **Дата:** 2026-05-31 · **Канон:** [TRUTH_AND_RINGZERO_CANON.ru.md](TRUTH_AND_RINGZERO_CANON.ru.md) ([EN](TRUTH_AND_RINGZERO_CANON.en.md))
> **Источник gap-анализа:** глубокий аудит 2026-05-31 (находки C1/C2/H1–H3, M1–M5) + [AUDIT_V8_6.ru.md](AUDIT_V8_6.ru.md)
>
> Этот документ раскладывает требования соответствия **C1–C12** из §7 канона в конкретные
> задачи по файлам с приоритетами, оценкой трудоёмкости и зависимостями.

## 🧭 Две дороги (не взаимоисключающие)

- **🅱️ Адаптер (уже сделано ✅).** `core/core3_adapter.py` + `velantrim/verify.py` в Core-3 — субпроцесс-мост Dual Core Router. Даёт строгую проверку high-risk запросов **без** инвазивного рефакторинга. Покрыт `tests/test_core3_adapter.py`. Это «исполняемый канон» как первый шаг.
- **🅰️ Порт контрактов (этот план).** Внести единую `truth_policy`, структурный `EvidenceRef`, вердикт `allow/gap_notice/reject` и гейт Ring Zero **внутрь** V8.6. Лечит первопричины, найденные аудитом.

## 🚦 Легенда приоритетов

| Приоритет | Смысл |
|-----------|-------|
| **P0** 🔴 | Баги целостности/безопасности — чинить первым (из критичных находок аудита) |
| **P1** 🟠 | Ядро канона — эпистемика истины (C1–C4, C12) |
| **P2** 🟡 | Конституционный слой и закалка (Ring Zero, boot, audit) |

Трудоёмкость: **S** ≤ полдня · **M** 1–3 дня · **L** > 3 дней.

---

## 📋 Задачи по файлам

### P0 🔴 — Прерэквизиты целостности (баги, не канон-фичи)

| # | C | Файл(ы) | Что сделать | Труд | Аудит |
|---|---|---------|-------------|:----:|-------|
| T0.1 | C6 | `core/memory.py` `store_facts_batch` (~1069–1073) | Перенести все `_l0_put` **после** успешного `with self._db()` (commit). Сейчас L0 пишется до SQL → split-brain при откате батча | S | C2 (crit) |
| T0.2 | C7 | `core/memory.py` `_l0_put/_l0_get` (~205–216), `relations.py` (~449) | Завести `threading.Lock`/`RLock` вокруг всех мутаций и итераций L0; снапшот `list(...)` перед итерацией | M | C1 (crit) |
| T0.3 | C7 | `core/pipeline.py` `_get_causal_graph` (~203–243) | Убрать общий `sqlite3.Connection` между потоками: либо per-op соединение, либо лок вокруг graph-операций | M | M1 |
| T0.4 | C8 | `core/causal_graph.py` `add_relation` (~336), `set_status` | Чинить инверсию метаданных inverse-ребра; гарантировать `pair_id` + каскад статуса на пару | S | M2 |
| T0.5 | — | `core/memory.py` `transition_esm`/`update_state` (~750–822) | Свести L1-UPDATE и refresh метаданных в **одну** транзакцию (иначе краш-окно → checksum-lock факта) | M | H3 |

> ⚠️ Параллельно (вне C-листа, но P0 по безопасности): закрыть auth на `api/llm_routes.py` и убрать выдачу ключа из `/console/bootstrap` (см. аудит security). Это не блокирует канон, но должно идти в том же спринте.

### P1 🟠 — Ядро канона: единая эпистемика истины

| # | C | Файл(ы) | Что сделать | Труд | Зависит |
|---|---|---------|-------------|:----:|---------|
| T1.1 | C1 | **новый** `core/truth_policy.py` | Портировать из Core-3: `fact_admissible(fact, conf_threshold) → (ok, reason)` + `fact_evidence_ref`. Единый закон допустимости | S | — |
| T1.2 | C1 | `core/truth_gate.py`, `core/pipeline.py` (`truth_gate()` ~789–885, `build_facts_pack` ~648–705), `core/facts_pack.py`, `core/promotion_policy.py` | Все гейты (запись и чтение) опираются на `truth_policy`. Убрать MVP confidence-floor и расходящиеся пороги FactsPack (0.55) vs TruthGate (0.7) | L | T1.1 |
| T1.3 | C2 | `core/evidence.py`, `core/truth_gate.py` `_count_evidence` (~237–248) | Подключить структурный `EvidenceRef` (source_id + chunk/span/quote). `_count_evidence` не должен возвращать 1 по умолчанию; plain-строка невалидна | M | T1.1 |
| T1.4 | C3 | `core/trace.py`, `server.py` `/query` (~2002–2022), `/chat`, `_build_system_prompt` (~290–314) | Read-путь выдаёт явный `allow/gap_notice/reject`; high-conf без evidence ⇒ gap_notice; **не** звать LLM при 0 фактов (или строгий honest-режим) | L | T1.2 |
| T1.5 | C4 | `core/trace.py`, `core/pipeline.py` `_extract_conflicts` (~264–319) | Validated `contradicts`/`known_false` между фактами пакета ⇒ **reject** на этапе ответа, а не только аннотация | M | T1.4 |
| T1.6 | C12 | **новый** `core/thresholds.py` (или в `feature_config`) | Свести лестницу порогов `0.5 ≤ 0.75 ≤ 0.85` в одно место как явные константы; убрать дубли в `truth_gate._MODE_CONFIG`, pipeline, facts_pack, promotion_policy | S | T1.2 |

### P1/P2 🟠🟡 — Дисциплина графа

| # | C | Файл(ы) | Что сделать | Труд |
|---|---|---------|-------------|:----:|
| T2.1 | C5 | `core/causal_bridge.py` (~51–73), `core/cross_domain.py` (~397–402) | Inferred-связи писать `review_state='pending'/truth_status='hypothesis'`, не `approved`. Промоушен только через TruthGate | M |
| T2.2 | C5 | `core/causal_graph.py` `review_pending`-аналог | Добавить процедуру ревью pending→validated (evidence + conf + нет contradiction), как в Core-3 | M |

### P2 🟡 — Конституционный слой (Ring Zero)

| # | C | Файл(ы) | Что сделать | Труд |
|---|---|---------|-------------|:----:|
| T3.1 | C9 | **новый** `core/ring_zero/` (порт `Small Core Complex/small_core/`) | Внести `ActionContract`, `invariants` (I0–I8), `PolicyEngine`, `SafetyMode`. Довести draft до рабочего (persistent checkpoint) | L |
| T3.2 | C9 | `core/memory.py` write-пути, `server.py` mutating-эндпоинты | Вызывать `PolicyEngine.decide(contract)` **перед** записью; заменить выключенный `graph_ring_zero` (0% cov) реальным гейтом, **включённым** по умолчанию | L |
| T3.3 | C10 | `server.py` `lifespan` (~317–438) | `BootProtocol.verify(repo_root, hashes)` на старте; рассинхрон целостности → RECOVERY/refuse | M |
| T3.4 | C11 | `core/audit_chain.py` (расширить) | Append-only журнал на **каждое** решение Ring Zero и **каждый** вердикт Truth Engine (контракт + решение) | M |

---

## 🪜 Порядок выполнения (фазы)

```text
Фаза 0 (P0, спринт 1):  T0.1 → T0.2 → T0.3 → T0.4 → T0.5   (+ security: llm_routes/bootstrap)
                         ── чиним целостность и потокобезопасность ДО фич канона

Фаза 1 (P1, спринт 2):  T1.1 → T1.6 → T1.2 → T1.3 → T1.4 → T1.5
                         ── единая truth_policy + evidence + вердикт + reject-на-противоречии

Фаза 2 (P1/P2, спринт 3): T2.1 → T2.2
                         ── дисциплина инференса (pending→review)

Фаза 3 (P2, спринт 4):  T3.1 → T3.2 → T3.3 → T3.4
                         ── Ring Zero как реальный гейт + boot + audit
```

## ✅ Definition of Done (для каждой фазы)
- Все правки покрыты тестами (целевое: модули C1–C12 ≥ 80% по факту).
- Прогон полного pytest зелёный; новые инвариант-тесты на split-brain (T0.1/0.2), gap_notice (T1.4), reject-on-contradiction (T1.5).
- Каждая задача закрывает соответствующий ❌/⚠️ в §7 канона (обновить статус C# в каноне на ✅).
- Поведение по умолчанию: сильные гейты **включены** (не за выключенным флагом).

## 🔗 Связь с адаптером
Пока идёт Фаза 0–1, адаптер 🅱️ (`core/core3_adapter.py`) уже даёт строгую проверку для high-risk
запросов. После Фазы 1 его можно использовать как **независимый кросс-чек** (двойная проверка:
встроенная политика V8.6 + внешний Core-3), что повышает доверие к ответам в медицине/праве/науке.
