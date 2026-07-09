# 1. 🟢🟡🔵 Product-Ready vs Research — честная карта

**Дата:** 2026-06-06 · [← назад к индексу](README.md)

Этот документ даёт **честную разметку зрелости** по обоим проектам. Он нужен для двух вещей:
1. **Презентация фондам/инвесторам** — показать product-ready ядро + честный research-фронтир.
2. **Внутренняя дисциплина** — не путать «работает в тесте» с «готово к продакшену».

> 🧠 **Почему это важно именно тебе:** для NLnet/инвестора заявка без явного product-ready ядра выглядит как «исследование без продукта». А «всё готово» без research-honesty выглядит как хайп и проваливает независимую валидацию. Правильная позиция — **середина: твёрдое ядро + честный фронтир**. Это и есть то, что ты просил «зашить».

Легенда: 🟢 PRODUCT-READY · 🟡 WORKING/RESEARCH (норма для стартапа) · 🔵 DESIGNED · 🔴 GAP. Полная легенда — в [README](README.md).

---

## 💎 Crystal — карта зрелости

Crystal специально собран как **презентабельное ядро**. Большинство — реально product-ready.

| Возможность | Статус | Обоснование (по аудиту) |
|---|---|---|
| Memory L0/L1 + ESM (8 состояний) | 🟢 PRODUCT-READY | `core/memory.py`, покрыто тестами |
| TruthGate (adaptive, type-aware) | 🟢 PRODUCT-READY | единственный вход в канон; subjective ≠ world-fact |
| L3 граф (swappable: sqlite/mock/ladybug/neo4j) | 🟢 PRODUCT-READY | dependency-free sqlite-бэкенд переживает рестарт |
| Provenance receipts (replayable, tamper-evident) | 🟢 PRODUCT-READY | `core/provenance.py`: SHA-256+HMAC, перепроверка по канону |
| GDPR-набор (erasure/restrict/RoPA/crypto/PII/audit) | 🟢 PRODUCT-READY | Art. 5/17/18/30/32, content-free tombstone |
| Retrieval: vector cosine + graph-walk + episodic | 🟡 WORKING | работает; беднее, чем Titan Hybrid (нет BM25+Dense+RRF) |
| Contradiction classifier (детерминированный) | 🟢 PRODUCT-READY | negation/antonym/numeric, high-precision |
| Consolidation / decay (SleepCycle, FSRS-style) | 🟡 WORKING | один механизм; полноценный FSRS — в FUTURE §3.5 |
| CLI (15 команд) + упаковка `pip install .` | 🟢 PRODUCT-READY | stdlib-only runtime, console-script |
| Тесты / качество | 🟢 PRODUCT-READY | **384 теста, 99% покрытие, CI cov-fail-under=95** |
| Bio-прототипы (fractal/immune/neurogenesis) | 🔵 DESIGNED | `prototypes/*` — демки с `print()`, не подключены |
| Epigenetic adaptation | 🟡 WORKING | единственный bio-модуль, подключён в adaptive TruthGate |
| Высшая когниция (concept/analogy/volition/neurocore) | 🔵 DESIGNED | RFC0066/65/67/68 — «designed, not coded» |
| Capability-based доступ / MCP gateway | 🔴 GAP | нет (есть в Titan как `tool_registry.py`) |
| Файловый ввод/вывод | 🔴 GAP | нет парсеров/генераторов |

**Итог Crystal:** ✅ ядро памяти + провенанс + GDPR + упаковка = **product-ready**. Высшая когниция и bio — честно помечены как research/designed.

---

## 🧠 Titan — карта зрелости

Titan — это **частично рабочая система + research-движок**. Гораздо мощнее по возможностям, но не закалён и без GDPR.

### 🟢/🟡 Что реально работает

| Возможность | Статус | Код (LOC подтверждён) |
|---|---|---|
| Memory + ESM + bi-temporal + L0-immutable | 🟢 PRODUCT-READY | `memory.py` 1510, `memory_ops.py` 746 |
| HTTP API (FastAPI) + web-console | 🟢 PRODUCT-READY | `server.py`, `api/` |
| Hybrid retrieval (BM25+Dense+RRF) + ngram FTS5 | 🟡 WORKING | `hybrid_retriever.py` 606, singleton |
| Causal graph (15 типов, chain/contradictions) | 🟡 WORKING | `causal_graph.py` 1222 |
| **Умное забывание** (decay/reconsolidation/vintage) | 🟡 WORKING | `forgetting.py` 605, `decay_orchestrator`, `reconsolidation` 232, `fsrs`, `fact_decayer` |
| TruthGate + 4 CognitiveModes | 🟡 WORKING | `truth_gate.py` + `facts_pack.py` |
| Файлы: 12 парсеров + 6 генераторов | 🟡 WORKING | `file_parsers/`, `file_generators/` |
| База знаний (invariant/variant/practical + world_skills) | 🟡 WORKING | `docs/knowledge/KNOWLEDGE_1..6`, `world_skills_ingest.py` |
| Capability-based tool registry | 🟡 WORKING (контракт) | `tool_registry.py` — ⚠️ реализации = заглушки `lambda: None` |
| LLM-оркестрация (router/stream/multilingual/tts) | 🟡 WORKING | `llm_router.py` 530, `llm_stream.py` 474 |
| Provenance / evidence / audit | 🟡 WORKING | `provenance_chain.py` 372, `evidence_pack.py` 225, `audit_chain.py` 430 |

### 🟡 Research-зрелость (работает как PoC, не закалено)

| Слой | Код |
|---|---|
| Noetic / meta-cognition | `noetic_core.py` 222, `meta_cognition.py` 144 |
| Essence / Velum | `velum.py` 839, `essence.py` 365, `essence_facade/` |
| Perspectives / poly-welt / umwelt | `perspectives.py` 377, `poly_welt_registry.py`, `umwelt_registry.py` |
| Concept emergence / naming / promote | `concept_emergence.py` 471 |
| Goals / curiosity / volition | `goal_frame.py` 163, `curiosity_engine.py` 272, `volition_gate.py` ⚠️ 33 (MVP) |
| Identity / welfare / interoception (L6) | `identity_layer.py` 329, `welfare_monitor.py` 198, `interoception.py` 183 |

### 🔴 Дыры (мешают product-ready)

| Дыра | Источник |
|---|---|
| **Нет GDPR вообще** (нет erasure/compliance/crypto/pii) | grep подтвердил: только `audit_chain` |
| Contract-тесты слабые (3/10) | `docs/KERNEL_STATE.md` |
| Конкурентность не проверена (4/10) | `docs/KERNEL_STATE.md` (нет stress-теста) |
| Observability слабая (3/10), trace не персистится | `docs/KERNEL_STATE.md` #8, #9 |
| Версионный разнобой (V8.6/8.7/V9/V10) | пересекается даже с Crystal-заголовками |
| MCP gateway-транспорт | реестр есть, сервера нет |
| `velantrim integrity` (единый отчёт целостности) | кубики есть (`fact_integrity`, `semantic_dedup`), агрегата нет |

**Итог Titan:** 🟡 мощный рабочий движок на research-зрелости (~6.5/10 по собственному `KERNEL_STATE.md`). Чтобы стать 🟢 product-ready — нужен [план закалки](04_TITAN_HARDENING_PLAN.md).

---

## 🗣️ Как это формулировать фонду (готовый абзац)

> *«Velantrim состоит из product-ready открытого ядра (Crystal: verifiable memory + provenance receipts + полный GDPR-набор, 99% тестового покрытия, упаковано и устанавливается одной командой) и приватного исследовательского движка (Titan), где уже работают прототипы более высоких слоёв — каузальные рассуждения, умное забывание, многоролевой доступ агентов. Часть research-фронтира честно не закрыта — это нормально для системы на стадии стартапа; именно его открытое дозревание мы и предлагаем профинансировать как вклад в commons.»*

Это даёт ревьюеру: твёрдое ядро (вес) + честность (проходит валидацию) + доказанный прототипами roadmap (низкий риск).
