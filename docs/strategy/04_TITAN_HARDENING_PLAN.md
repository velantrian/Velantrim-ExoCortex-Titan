# 4. 🛠️ План закалки Titan → Product-Ready

**Дата:** 2026-06-06 · [← назад к индексу](README.md)

## 🎯 Цель

Перевести Titan из 🟡 «рабочий движок + research (~6.5/10 по [`KERNEL_STATE.md`](../KERNEL_STATE.md))» в 🟢 «деплоябельный продукт» — **переносом дисциплины из Crystal**, не переписыванием.

> 💎 **Двойная выгода:** шаги с бейджем 💎 одновременно создают открытый Crystal-deliverable (см. [док 3](03_GRANT_DELIVERABLES_NLNET.md)). То есть грант может оплачивать ровно ту работу, что делает Titan product-ready.

Порядок — по принципу «честность → приватность/право → проверяемость → наблюдаемость → доступ». Не строить следующий слой, пока не закреплён предыдущий (твой же принцип из `Velantrim_Project_Map.md`).

---

## Phase 0 — Единый источник версии 🟢 (быстро)
- **Что:** убрать разнобой версий (V8.6 / V8.7 / V9 / V10 в заголовках; пересечения даже с Crystal). Версия — только в `pyproject.toml`, в рантайме через `importlib.metadata.version`.
- **Почему:** читатель/ревьюер/инвестор не понимает, что он запускает. Дешёвый, но важный сигнал зрелости (Crystal `FUTURE.md` §2.1).
- **Приёмка:** один источник версии; заголовочные `vX.Y.Z` удалены.
- **Объём:** XS.

## Phase 1 — GDPR-набор 🔴→🟢 💎 (главный разрыв)
- **Что:** портировать из Crystal `erasure.py` / `compliance.py` / `crypto.py` / `pii.py` и подключить к `core/memory.py` + `core/pipeline.py`. Связать уже объявленные admin-инструменты `forget_fact` / `forget_all` (`core/tool_registry.py` — сейчас заглушки) с реальной erasure + tombstone.
- **Почему:** сейчас в Titan GDPR **нет вообще** (только `audit_chain`). Без этого нет ни продукта для реальных пользователей, ни европейского измерения.
- **Приёмка:** erase across L0/L1/L3 + content-free tombstone; restriction исключает из recall; PII-redaction на ingest; encryption-at-rest опционально.
- **Объём:** M. 💎 = грант **D2**.

## Phase 2 — Replayable provenance receipts 🟡→🟢 💎
- **Что:** перенести концепт Crystal `provenance.py` (receipt = SHA-256/HMAC, `verify` по канону) поверх уже существующих `provenance_chain.py` / `evidence_pack.py`.
- **Почему:** закрывает `KERNEL_STATE.md` #9 («trace есть в коде, но не сохраняется долговременно; нет traceability запрос→факт»).
- **Приёмка:** любой ответ можно перепроверить позже; детектит erased/restricted/modified/contradicted.
- **Объём:** S–M. 💎 = грант **D1**.

## Phase 3 — Test-gate + contract + concurrency 🔴→🟢
- **Что:** (а) CI с `--cov-fail-under` как в Crystal; (б) **contract-тест «TruthGate всегда вызывается до записи»** (`KERNEL_STATE.md` #2); (в) **stress-тест 100+ конкурентных INSERT/UPDATE** + явный SQLite WAL (`KERNEL_STATE.md` #3).
- **Почему:** сейчас contract 3/10, конкурентность 4/10. Это разница между «работает у меня» и «продукт».
- **Приёмка:** CI красный при падении покрытия; bypass TruthGate ловится тестом; конкурентная запись без потерь/гонок.
- **Объём:** M.

## Phase 4 — Observability + `velantrim integrity` 🔴→🟢 💎
- **Что:** метрики latency/размера/конфликтов (`KERNEL_STATE.md` #8) + единый агрегат целостности поверх `fact_integrity.py` / `semantic_dedup.py` / `find_contradictions`.
- **Почему:** наблюдаемость = эксплуатируемость; для гранта = auditability.
- **Приёмка:** отчёт находит засеянные дефекты (orphan/dangling/dup/L1↔L3 mismatch/missing evidence_ref); базовые метрики экспонируются.
- **Объём:** S–M. 💎 = грант **D4**.

## Phase 5 — MCP gateway-транспорт 🟡→🟢 💎
- **Что:** реализовать транспорт (StreamableHTTP + SSE) поверх `tool_registry.py`; заменить заглушки `lambda: None` реальными обработчиками; mutation → trace; запись только после TruthGate.
- **Почему:** контракт ролей готов, не хватает «провода». Открывает многоролевой доступ агентов.
- **Приёмка:** см. [`05_RFC_MCP_GATEWAY.md`](05_RFC_MCP_GATEWAY.md) (reader не видит write-tools; деструктив → admin+audit).
- **Объём:** M. 💎 = грант **D3**.

## Phase 6 — Lean «core profile» упаковка 🟡→🟢
- **Что:** профиль сборки со stdlib-defaults (как Crystal): тяжёлые зависимости (fastapi/kuzu/sbert) — опциональные extras; быстрый путь установки для оценки.
- **Почему:** низкий порог входа для ревьюеров/пользователей; «frugal».
- **Приёмка:** `pip install` базового профиля без тяжёлых нативных зависимостей; e2e-демо проходит.
- **Объём:** S–M.

---

## 🗓️ Рекомендованный порядок и зачем именно такой

```
Phase 0 (версия)        ── XS, сразу, чистит сигнал зрелости
   ↓
Phase 1 (GDPR) 💎        ── закрывает крупнейший разрыв + грант D2
   ↓
Phase 2 (receipts) 💎    ── доверие + грант D1 (опирается на GDPR-состояния)
   ↓
Phase 3 (тесты)          ── превращает «работает» в «продукт»
   ↓
Phase 4 (observability) 💎 + Phase 5 (MCP) 💎  ── параллелятся; гранты D4, D3
   ↓
Phase 6 (упаковка)       ── финальный лоск для оценки
```

| Phase | Product-ready? | Грант? | Объём |
|---|---|---|---|
| 0 версия | 🟢 сигнал | — | XS |
| 1 GDPR | 🟢 крупный | 💎 D2 | M |
| 2 receipts | 🟢 | 💎 D1 | S–M |
| 3 тесты | 🟢 ключ | — | M |
| 4 observability | 🟢 | 💎 D4 | S–M |
| 5 MCP | 🟢 | 💎 D3 | M |
| 6 упаковка | 🟢 | — | S–M |

> 🧭 Итог: после Phase 0–3 Titan уже «деплоябелен честно»; Phase 4–6 добавляют наблюдаемость, доступ и лоск. Четыре из семи фаз (💎) одновременно являются открытыми грантовыми deliverables — это и есть мост Crystal ⇄ Titan в действии.
