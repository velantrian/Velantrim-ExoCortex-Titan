# PR-C4 Design Report — полное AuditChain coverage Truth Kernel

> **Статус:** design-only. Код по этому документу **не** писать до явного authorization.  
> **База:** PR-C2 (#44, merged) + PR-C3 (lifecycle wiring; hardening в Draft).  
> **Архитектура (зафиксирована, не менять):** C1 same-transaction + S2 per-fact `chain_id` via `audit_subject_id` · `memory_events.fact_id = NULL` · hash v2 · без free-text claim/prompt · structured `actor_code` / `reason_code` · ProvenanceChain / VersionStore не трогать без крайней нужды.

---

## 1. Полная карта write-path (после C2+C3)

### 1.1 Уже покрыто AuditChain (choke points)

| Choke point | Функция | Event types |
|---|---|---|
| ESM / terminal | `memory.update_state` | `esm_transition`, `fact_deprecated`, `fact_collapsed`, `fact_contradicted` |
| Validated CAS | `memory._promote_to_validated_cas` | `esm_transition` |
| create / update | `memory._store_fact_outcome` | `fact_created`, `fact_updated`, `fact_contradicted` |
| batch upsert | `memory.store_facts_batch` | то же |
| bi-temporal end | `memory.invalidate_edge` | `fact_invalidated` |
| supersede | `memory.supersede_fact_cas` | `fact_created` (new) + `fact_deprecated` (old) |

Косвенно через них: `transition_esm`, `promote_esm_to`, `validate_and_promote`, HTTP/MCP wrappers, `truth_maintenance.supersede`, consolidation / contradiction callers.

### 1.2 Не покрыто (значимые пути)

| Write Path | Что меняет | Сейчас журналируется? | Нужно AuditChain? | Почему | event_type (proposal) | Same-txn? | Double-log риск |
|---|---|---|---|---|---|---|---|
| `memory.erase_fact_dependents_atomic` | DELETE facts + dependents | нет | **да P0** | физическое уничтожение | `fact_erased` | да | низкий |
| `memory.write_tombstone` | `erasure_log` | нет | **да P0** | Art.30 ≠ hash-chain | `erasure_tombstone` | да | низкий |
| `forgetting.forget_one` | legacy DELETE | нет | **да P0** | bypass coordinator | через erase choke | да | **средний** dual-path |
| `forgetting.redact_pii_*` | UPDATE claim | нет | **да P0** | content mutation | `fact_claim_redacted` | да | низкий |
| `memory_archival` archive | claim → `[ARCHIVED:…]` | нет | **да P0** | claim rewrite | `fact_archived` | да | низкий |
| `async_store._aiosqlite_store_*` | UPSERT в обход store | нет | **да P0** | полный bypass | делегировать в sync | — | критический |
| `scripts/build_kb_graph` raw INSERT / bulk ESM | facts | нет | **да P0** | ломает I50 | через public APIs | — | — |
| `causal_graph.add/remove_relation` | `relations` | нет | **да P0** | Truth edges | `relation_created` / `relation_removed` | да | низкий |
| `memory.set_restricted` | GDPR Art.18 flag | нет | **да P1** | меняет recall | `fact_restricted` / `unrestricted` | да | низкий |
| `memory.link_raw_to_fact` / `raw_memory.link_to_fact` | `derived_from` | нет | **да P1** | provenance на facts | `fact_derived_linked` | да | средний (два пути) |
| `memory.refresh_fact_integrity_metadata` | metadata CAS | нет | **да P1** | durable metadata | `fact_metadata_refreshed` | да | низкий |
| `AuditChain.log_truth_gate_verdict` | helper есть, не wired | нет | **да P1** | verdict без мутации | `truth_gate_verdict` | отдельная txn OK | средний с promote |
| `kb_graph_build` bulk edges / wipe | relations | нет | **да P1** | mass ingest | `relation_*` / `relations_wiped` | да | низкий |
| embeddings / ngram / FTS | indexes | нет | отложить P2 | derived | — | — | — |
| `RelationStore` (`fact_relations`) | associative LTP | нет | отложить P2 | не ESM Truth | — | — | — |
| VersionStore / ProvenanceChain | свои ledger’ы | свои | отложить | не дублировать | — | — | dual-ledger |

---

## 2. Архитектура полного audit coverage

**Правило choke point (C4):**  
`caller never logs; only the function that owns the SQL WRITE logs`, same SQLite transaction, через `AuditChain.log_in_transaction`.

```
facts lifecycle     → уже: _store_fact_outcome / store_facts_batch / update_state /
                           _promote_to_validated_cas / invalidate_edge / supersede_fact_cas
facts erase         → ТОЛЬКО erase_fact_dependents_atomic (+ write_tombstone рядом)
facts claim/meta    → set_restricted / redact_* / archival / refresh_* / link_raw_to_fact
relations (Truth)   → ТОЛЬКО CausalGraph.add_relation / remove_relation
                      (kb_graph_build вызывает тот же internal helper)
bypass paths        → deprecate async_store direct SQL; scripts → public APIs
```

Не вводить event sourcing, hash v3, free-text claim в payload.

---

## 3. Предлагаемые event types

**Уже есть:** `fact_created`, `fact_updated`, `esm_transition`, `fact_deprecated`, `fact_collapsed`, `fact_contradicted`, `fact_invalidated`, `truth_gate_verdict`, `observer_verdict`, `immutable_attempt_blocked`, …

**Новые (proposal only):**

| event_type | Назначение |
|---|---|
| `fact_erased` | physical DELETE |
| `erasure_tombstone` | Art.30 tombstone |
| `fact_claim_redacted` | PII redaction |
| `fact_archived` | archival rewrite |
| `fact_restricted` / `fact_unrestricted` | Art.18 |
| `fact_metadata_refreshed` | integrity metadata |
| `fact_derived_linked` | derived_from |
| `relation_created` / `relation_removed` | causal edges |
| `relations_wiped` | mass DELETE |
| `fact_taxonomy_updated` | claim_type/origin (опц.) |

**Унификация:** не переиспользовать `fact_updated` для metadata-only / claim-redact — отдельные типы. Legacy shortcuts `log_fact_created` / `log_esm_transition` с `claim_preview` **не** расширять в production paths.

---

## 4. Предлагаемый payload (не реализовывать)

Каркас C2/C3: `actor`=code, `reason`=code, `from_state`/`to_state` когда есть, **без claim/prompt**.

| event | payload |
|---|---|
| `fact_erased` | `{tables_deleted: {name: n}}` |
| `erasure_tombstone` | `{job_id?, claim_hash_prefix?, reason_code}` |
| `fact_claim_redacted` | `{claim_len_before, claim_len_after, pii_tag_count}` |
| `fact_archived` | `{archive_file_id?}` |
| `fact_restricted` | `{restricted: true}` |
| `fact_metadata_refreshed` | `{fields: [...]}` |
| `fact_derived_linked` | `{derivation_type}` |
| `relation_*` | `{relation_id, from_fact_id, to_fact_id, relation_type}` |
| `truth_gate_verdict` | `{passed, mode}` |

Опционально для forensic (C4+): `operation_id`, `request_id`, `source_module`, `correlation_id` — только коды/UUID, не free-text. **Не** добавлять `confidence` как обязательное (уже вынесено из hash v2 envelope для transitions).

Новые reason_codes (allowlist): `erasure_durable`, `pii_redaction`, `archival`, `gdpr_restriction`, `integrity_refresh`, `derived_link`, `causal_write`, `kb_bulk`.

---

## 5. Time Travel

**AuditChain alone недостаточен** для полного восстановления объекта.

Есть: порядок lifecycle event_type + from/to_state + actor/reason + hash integrity.  
Нет: claim, metadata, bi-temporal values (кроме факта invalidate), snapshots, relation graph.

Для object-level time travel нужны: **AuditChain** (event ledger) + **VersionStore** (pre-images) + live `facts`/`relations`. Это feature, не баг C1+S2.

---

## 6. Совместимость

| Система | Политика C4 |
|---|---|
| VersionStore | оставить отдельным ledger; same-txn с ним не требовать |
| ProvenanceChain | не дублировать те же события; AuditChain = SoT lifecycle |
| Erasure | один choke в `erase_fact_dependents_atomic`; coordinator не логирует повторно |
| Causal | per-relation chain **или** endpoint fact-chains — зафиксировать в implementation TZ |
| Snapshot / Export / Replay | не смешивать; AuditChain = audit, не snapshot store |

---

## 7. Риски

1. Double-log erase (coordinator + store) / forget_one + erase  
2. Double-log relations (CausalGraph + caller)  
3. `truth_gate_verdict` + `esm_transition` на promote — два события OK, если явно разделены  
4. Legacy `log_fact_created` с claim_preview — запретить на wired paths  
5. `async_store` / `build_kb_graph` bypass — coverage никогда не полное, пока живы  
6. Backfill исторических erase/relations — невосстановим; не делать silent backfill

---

## 8. RED test plan (implementation PR-C4)

1. Erasure atomicity: success → 1 `fact_erased` (+ tombstone); forced audit fail → row остаётся  
2. Erase miss / Ring Zero → 0 events, no phantom chain  
3. Redact → 1 `fact_claim_redacted`; payload без текста; fail → claim не меняется  
4. `set_restricted` / unrestrict  
5. `link_raw_to_fact` success / missing / second no-op  
6. Relations add/remove + rollback; wipe → `relations_wiped`  
7. No double-log через coordinator  
8. Bypass guard: async_store делегирует или fails closed  
9. Chain identity: erase/redact на том же `fact-transition:{audit_subject_id}`  
10. C1+S2 invariants: `fact_id` NULL, allowlists, verify_chain, no claim in payload  
11. `build_kb_graph`: bulk ESM UPDATE запрещён / must use transition

---

## 9. Migration impact

- Новые event_type — строки, **без** DDL enum  
- Actor/reason allowlist — additive only  
- Новая migration обычно **не нужна**  
- Backfill истории — out of scope  

---

## 10. Rollback strategy

- Feature-flag `VELANTRIM_AUDIT_CHAIN_C4=0` вокруг новых call sites  
- C2/C3 paths не трогать  
- Rollback = revert PR; append-only chains остаются валидными  
- Legacy `forget_one` → перевести на `erase_fact_dependents_atomic` или удалить  
- `async_store` → redirect на sync store через executor  

---

## 11. Рекомендуемый порядок реализации (после authorization)

`P0 erase+tombstone → P0 claim rewrite (redact/archival) → P0 close bypasses → P0 causal relations → P1 restricted/derived/metadata/truth_gate → P2 indexes`

---

## 12. Прогресс (на момент этого отчёта)

| Пакет | Статус |
|---|---|
| PR-C1 (write/version consistency) | ✅ 100% |
| PR-C2 (ESM transition ledger) | ✅ 100% merged |
| PR-C3 (lifecycle paths wiring) | 🟡 ~95% Draft (hardening + tests) |
| PR-C4 (этот design → implementation) | 🔵 0% code / **100% design** |
| Общий audit Truth Kernel | ~75% done / ~25% left (P0/P1 выше) |
