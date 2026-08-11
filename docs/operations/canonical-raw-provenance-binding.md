# Canonical raw provenance binding — operational contract

Tracking: #288  
Parent: #50  
Baseline: `main@615201ec1073dafb047028e88ce94463f4ef9b77`

## Scope

This bounded block converges mutation of `facts.derived_from` onto the existing `SQLiteGraphStore` owner. It does not change the authority of raw text, TruthGate, ESM promotion, runtime enablement or production rollout.

## Required behavior

| Case | Canon | Provenance | VersionStore | AuditChain | Result |
|---|---|---|---|---|---|
| missing raw | unchanged | none | none | none | false |
| missing fact | unchanged | none | none | none | false |
| first valid binding | `NULL -> raw_id` | one row | one pre-image | one `FACT_UPDATED` | true |
| identical retry | unchanged | no duplicate | no duplicate | no duplicate | true |
| different second raw | unchanged | no conflicting row | none | none | false |
| CAS loss, same raw won | winner only | winner only | winner only | winner only | idempotent true after durable read-back |
| CAS loss, different raw won | winner only | winner only | winner only | winner only | false |
| VersionStore failure | rollback | rollback | rollback | none | exception/fail closed |
| AuditChain failure | rollback | rollback | rollback | rollback | exception/fail closed |

## Transaction boundary

For the successful first bind, the guarded `facts` UPDATE, VersionStore pre-image, `l0_fact_provenance` insert and AuditChain append use the same SQLite connection and transaction. Audit schema readiness happens before that transaction. L0 cache invalidation happens only after commit.

## Legacy adapter boundary

`core/raw_memory.py::RawMemoryStore.link_fact()` must contain no direct `UPDATE facts SET derived_from`. File-backed use delegates canonical binding to `SQLiteGraphStore.link_raw_to_fact()`. Its historical `raw_derivation_chain` row is a derived/read-side trace only and may be absent on a virgin runtime database.

## Non-scope

- no schema v8;
- no Continuity 13/12;
- no new write protocol or canonical store;
- no raw-text rewrite/deletion policy;
- no #249 contention characterization;
- no runtime activation, Operator GO, runtime authority or production authority;
- no ADAO / ARM-04 / Phase II.

## Exit gate

Exact-head Full CI and Docker must succeed. Review-stage Notion evidence must be synchronized before ready state. Ready-state `Titan aggregate merge evidence` must succeed before protected exact-head squash merge. Post-merge Full CI, Docker and aggregate must succeed. Then a fresh residual current-main inventory decides whether parent #50 can close.
