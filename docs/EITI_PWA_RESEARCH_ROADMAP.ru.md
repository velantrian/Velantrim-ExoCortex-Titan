# 🧪 EITI PWA Research Roadmap для Velantrim

**Источник:** тезисы Claude по `VELANTRIM EITI PWA v14.0 target`  
**Статус:** roadmap для Research/PWA, не stable runtime  
**Открыть:** `/console/research-app` — активная Research App, `/console/research-roadmap` — карта T1–T12.  
**Правило:** всё делать поверх существующего кода, без изменения stable `/query` и stable DB.

---

## Главный вывод

Тезисы полезны для Velantrim, но правильное место — **Research PWA / Browser Console**:

```text
Stable V8.6 = Python/FastAPI/SQLite trusted core
Research PWA = browser sandbox: SQLite WASM, Fractal Router, TRACE UI, L3 Viewer
```

Это даёт безопасный способ тестировать память как инструмент AI-агента, не
записывая экспериментальные факты в `data/velantrim.db`.

---

## Карта T1–T12

| ID | Тема | Использование для Velantrim | Куда класть | Эмоция |
|----|------|-----------------------------|-------------|--------|
| T1 | Fractal Memory L0→L3 | схема слоёв, parent, compression, Guardian flag | Research DB / PWA schema | 🌌✅ |
| T2 | ESM 8-state machine | сверить с текущей ESM-матрицей, UI badges | shared contract + Research UI | ⚖️✅ |
| T3 | Hash-chain audit | audit trail для browser memory | PWA first, позже API parity | 🔐✅ |
| T4 | Truth Gate + Pending | ручное подтверждение фактов до L3 | Research API + Pending UI | 🛡️✅ |
| T5 | FSRS + Hebbian | decay/strength для experimental recall | Research memory analytics | 🧠🟡 |
| T6 | Fractal Router | recursive retrieval и `retrieval_path` | `/research/query` | 🧭✅ |
| T7 | TextRank compression | L2 summaries без LLM | PWA ingestion + consolidation | 🗜️✅ |
| T8 | Guardian faithfulness | browser-side минимальная проверка ответа | Research response guard | 🛡️🟢 |
| T9 | Enforced TRACE | строгий поток “нет TRACE → нет ответа” | только Research | 🧾🟡 |
| T10 | TRACE UI | раскрываемая панель под ответом | Browser console | 🔍✅ |
| T11 | Немецкий язык | безопасное i18n-расширение | console UI | 🇩🇪✅ |
| T12 | L3 Viewer | управление canonical/pending memory | Research Console | 🧠✅ |

---

## Очерёдность реализации

### Этап 1 — безопасные PWA-утилиты

| Задача | Почему первая |
|--------|---------------|
| T3 Hash-chain audit | Web Crypto, нет зависимостей, даёт доверие к локальной памяти |
| T7 TextRank | чистый JS, полезен для L2 summaries и больших файлов |
| T11 German i18n | не трогает память и retrieval |

### Этап 2 — ядро Research Memory

| Задача | Условие |
|--------|---------|
| T1 Fractal schema | только research DB / SQLite WASM, не stable DB |
| T2 ESM matrix | единый contract с Python ESM |
| T4 Truth Gate + Pending | запрет прямой записи в L3 |

### Этап 3 — retrieval/cognitive layer

| Задача | Условие |
|--------|---------|
| T5 FSRS + Hebbian | после `stability`, `last_accessed`, edge `strength` |
| T6 Fractal Router | после `fractal_level`, `memory_layer`, ESM |
| T8 Guardian | после facts/TRACE flow |
| T9 Enforced TRACE | только в `/research/query`, не в stable `/query` |

### Этап 4 — UI

| Задача | Что даёт |
|--------|----------|
| T10 TRACE UI | видимость причин, фактов, блокировок |
| T12 L3 Viewer | ручное управление Pending/Validated/Contradicted/Deprecated |

---

## Обязательные правки к тезисам перед кодом

| Место | Риск | Исправление |
|------|------|-------------|
| T3 hash-chain | `new Date()` вызывается дважды, verify может не совпасть | создать `const at = new Date().toISOString()` один раз |
| T2 ESM | `Retracted` есть, но нет входящих переходов | добавить явные переходы в `Retracted` или убрать из UI |
| T6 levels | `evidence → principle` спорное направление | сделать direction configurable |
| T9 strict TRACE | может заблокировать нормальный stable ответ | включать только Research |
| T1 ALTER facts | риск испортить stable DB | применять только к `velantrim_research.db` / WASM DB |

---

## Stable contract

Запрещено:

- менять stable `/query` ради эксперимента;
- писать Research факты в `data/velantrim.db`;
- продвигать L2 в L3 без Truth Gate;
- удалять `ImmutableCore`;
- дублировать Python core логикой JS без contract-тестов.

Разрешено:

- делать PWA-реализацию как sandbox;
- сохранять Research trace/audit отдельно;
- сравнивать stable и research ответы на одинаковых запросах;
- переносить в stable только после тестов и ревью.

---

## Итог

Тезисы Claude стоит принять как **Research PWA roadmap**:

> Velantrim Research PWA = SQLite WASM memory + Fractal L0→L3 + ESM + Hash-chain audit + Truth Gate/Pending + FSRS/TextRank + Recursive Retrieval + Guardian + TRACE UI + L3 Viewer.

Stable V8.6 остаётся trusted core. Research PWA становится лабораторией, где
можно безопасно проверять новые механизмы памяти.
