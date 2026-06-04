# Velantrim V8 Crystal — Work Summary

**Version**: **v8.3.0** · Audit-fixed + Bi-temporal + TRUSTED_SOURCES + NGramIndex + SleepTimeWorker + FileIngester · May 2026
**Status**: ✅ MVP, P0/P1 баги закрыты, bi-temporal реализован · ❌ NOT production-ready (~28%)

---

## 🎯 Что сделано

### Phase 1: Metadata hardening (Sprint 1, апрель 2026)

- ✅ Cyrillic chunk_ids: 39 → 0 (транслитерация)
- ✅ Layer field: 55 null → 1 null (только заголовочный)
- ✅ Depends_on: 54 пустых → 27 (RFC dependencies inferred)
- ✅ RFC duplicates: подтверждены как намеренная организация (multi-section)
- ✅ Migration tool `velantrim_migrate_v3_1.py` (rollback, checksums, dry-run) → перенесён в `scripts/`
- ✅ `utils/rfc_parser.py` — shared RFC парсер с поддержкой диапазонов

### Phase 2: Code hardening (Sprint 1 + Audit)

**P0 баги исправлены:**
- `store_fact` UPSERT больше не сбрасывает `epistemic_state`
- Добавлена колонка `history` с миграцией для старых БД
- Per-op SQLite connection (вернули из ZIP-версии)
- `get_all_facts` прогревает L0

**P1 баги исправлены:**
- `tokenize` обрабатывает em-dash, en-dash, дефис, пунктуацию
- `confidence` = source confidence (стабильная), `retrieval_score` отдельно
- `promote_trace` валидирует ESM-матрицу + идемпотентность
- Guardian проверяет fact_id coverage

**Audit fixes:**
- `pipeline.run()` идемпотентен на persistent DB
- I50: `store_fact` запрещает обход через initial state
- I50-b: `transition_esm` блокирует `ImmutableCore` для не-Ring-Zero
- `confidence` валидируется в `[0, 1]`
- `get_fact` возвращает `deepcopy`
- `promote_trace` идемпотентен
- Параметр `by` в `transition_esm`

### Phase 3: Documentation

- 🆕 `INVARIANTS.md` — таблица инвариантов
- 🆕 `LIMITATIONS.md` — карта долга
- 🆕 `SPRINT_A_NOTES.md` — замечания по A6-A10
- 🆕 `SYSTEM_OVERVIEW.md` — как система работает с диаграммами
- ✏️ `README.md` — честный статус
- ✏️ `ROADMAP.md` — честная карта спринтов

### Phase 4: Bi-temporal + Storage ABC (v8.2.0, май 2026)

- ✅ **I96 реализован**: 4 bi-temporal поля в SQLite схеме
  - `t_event_valid_start`, `t_event_valid_end`, `t_ingestion_start`, `t_ingestion_end`
  - Автомиграция через `ALTER TABLE` для существующих БД
  - Индексы на bi-temporal полях (закрыт P-3)
- ✅ **`get_fact_at()`** — time-travel запрос
- ✅ **`invalidate_edge()`** — инвалидация без DELETE
- ✅ **`search()`** — заглушка поиска (Sprint 2 → FTS5/Graphiti) — помечена `NotImplementedError`-предупреждением
- ✅ **`make_store()`** — фабрика для тестовой изоляции
- ✅ **`storage.py` v8.1.0**: bi-temporal методы добавлены в ABC
- ✅ **`trace.py` v8.0.4**: параметр `by` в `promote_trace()`, `promoted_by` в trace
- ✅ **Drift protection тест** (TASK-02)
- ✅ **Исправлена тестовая изоляция** через `make_store()`
- ✅ **Тесты bi-temporal**: get_fact_at, invalidate_edge, Collapsed→t_ingestion_end, time-window

### Phase 5: Sprint 1++ — TRUSTED_SOURCES + NGramIndex + EmbeddingRegistry + SleepTimeWorker + FileIngester (v8.3.0, май 2026)

- ✅ **I98 реализован (TRUSTED_SOURCES whitelist)**
  - `ring_zero`, `domain_seed`, `system_axiom` защищены от `Contradicted` и drift
  - `TrustedSourceError` — отдельное исключение
  - Тесты: 5 тестов `test_trusted_source_*`

- ✅ **NGramIndex v1.0.0 (I99) — закрыт P-1** 🆕
  - SQLite FTS5 trigram tokenizer
  - O(log N) сужение кандидатов до `limit=50` перед BM25
  - Graceful degradation если FTS5 недоступен → pipeline fallback
  - Инвариант I99: не хранит ESM-состояние (Graph = Truth сохраняется)
  - Тесты: 14 тестов `test_ngram.py`

- ✅ **EmbeddingRegistry v1.0.0** 🆕
  - Защита от `numpy.dot` dim-mismatch
  - 17 поддерживаемых моделей
  - Тесты: 15 тестов `test_embedding_registry.py`

- ✅ **SleepTimeWorker + CoreMemoryBlocks v1.0.0 (I100-I103)** 🆕
  - `CoreMemoryBlocks` — три постоянных слота (user_profile / agent_persona / current_goals)
  - `SleepTimeWorker` с активным idle-циклом `think()` каждые 5+ минут
  - `suggest_next_step()` — предлагает следующий шаг из RNE документов
  - `get_notebook()` — полный снапшот блокнота
  - ⚠️ LLM mock → Sprint 2c: заменить на реальный `LLMClientABC`
  - `make_sleep_time_worker()` — фабрика для тестовой изоляции
  - Тесты: 30+ тестов `test_sleep_time_worker.py`

- ✅ **RFC0063 Knowledge Ingestion Pipeline v1.1.0 (FileIngester)** 🆕
  - `FileParser` ABC + `ParseResult` с W3C PROV provenance
  - 20+ форматов: PDF, DOCX, TXT/MD/JSON/YAML, CSV, JPG/PNG, MP3/WAV, MP4
  - Каскадные парсеры: Docling→MinerU→Unstructured→PyPDF2 (PDF)
  - Blake3 → sha256 fallback с `logger.warning()` при недоступности blake3
  - NGramIndex: `ngram_index_fact()` после каждого `store_fact()` (I99)
  - TRUSTED_SOURCES: `source_override="domain_seed"` + auto-detect из имени пути (I98)
  - SleepTimeWorker уведомление после batch `ingest_directory()`
  - `KnowledgeIngesterV5` — интеграция ESM + NGramIndex + TRUSTED_SOURCES + SleepTimeWorker
  - Тесты: 25+ тестов `test_knowledge_ingester.py`

---

## 📊 Метрики

### Тесты

| Файл | Тестов | Coverage |
|------|--------|----------|
| `test_esm.py` | 44 | core/memory.py: ~90% |
| `test_pipeline.py` | 19 | core/pipeline.py: 76% |
| `test_regression_p0.py` | 8 | (регрессия P0 + bi-temporal) |
| `test_migration.py` | 13 | velantrim_migrate_v3_1.py |
| `test_sprint_a_wiring.py` | sentinel | AST check |
| `test_ngram.py` | 14 | core/ngram_index.py 🆕 |
| `test_embedding_registry.py` | 15 | core/embedding_registry.py 🆕 |
| `test_sleep_time_worker.py` | 30+ | core/sleep_time_worker.py 🆕 |
| `test_knowledge_ingester.py` | 25+ | file_parsers/ 🆕 |
| **Итого** | **160+** | **core/* 81%** |

### Инварианты

- Документировано в `INVARIANTS.md`: 22 (I1, I2, I6, I50, I50-b, I68, I96, I97, **I98, I99, I100–I103** + D1–D7, PL1–PL4, S1–S3)
- В JSONL-спеке: ~94 нумерованных + 17 RFC/sub
- Не задокументировано: ~72 (Sprint 3+ — автогенерация из JSONL)

### Метаданные спеки

| Метрика | До | После |
|---------|----|-------|
| Cyrillic chunk_ids | 39 | 0 |
| Null layers | 55 | 1 (header) |
| Empty depends_on | 54 | 27 |
| SQLite индексы | 1 | 4 (+ bi-temporal) |

### Production readiness

| Компонент | v8.2.0 | v8.3.0 |
|-----------|--------|--------|
| ESM + Ring Zero | ✅ | ✅ |
| Bi-temporal I96 | ✅ | ✅ |
| TRUSTED_SOURCES I98 | ❌ | ✅ 🆕 |
| NGramIndex I99 | ❌ | ✅ 🆕 |
| EmbeddingRegistry | ❌ | ✅ 🆕 |
| SleepTimeWorker | ❌ | ✅ (mock LLM) 🆕 |
| FileIngester 20+ форматов | ❌ | ✅ 🆕 |
| L3 Neo4j / Graphiti | ❌ | ❌ Sprint 2c |
| async/await | ❌ | ❌ Sprint 2c |
| Реальный LLM | ❌ | ❌ Sprint 2c |
| **Production readiness** | **~22%** | **~28%** |
