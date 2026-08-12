# 🗺️ Component and Authority Map

**Continuity:** `12/12 = 100%`  
**Machine state:** schema v7  
**Runtime:** `CURRENTLY DISABLED · CURRENT OPERATOR GO ABSENT · HISTORICAL OBSERVED=true · NO RUNTIME AUTHORITY · NO PRODUCTION AUTHORITY`

This map separates executable ownership from proposals and projections. Re-verify the
live `main` SHA before using a review branch as implementation truth.

## 1. Continuity ownership

| Capability | Primary surface | Authority boundary |
|---|---|---|
| Source adapters | state/goal/open-loop adapters | deterministic proposals only |
| Admission evaluator/facade | admission evaluator + facade | bounded admission decision; no external owner substitution |
| Current-decision resolver | six-owner evidence composition | no accepted live deployment adapters selected |
| Durable lifecycle | admission artifact lifecycle | internal SQLite artifact persistence/replay only |
| Runtime composition | `runtime_composition.py` | wired internally |
| Controlled enablement | `controlled_enablement.py` | finite exact decision gate; current runtime disabled |
| Bounded observation | `bounded_observation.py` | read-only/content-free evidence; historical canary only |
| Composition root | FastAPI lifespan | startup/shutdown + composition; no public write endpoint added by Continuity |

### Current authority facts

```text
Continuity                         12/12 = 100%
runtime currently enabled          false
current Operator GO                false
operator authorization present     false
observed                           true (historical one rolled-back canary)
runtime authority                  false
production authority               false
user-visible runtime activation    false
```

Evidence, configuration, manifest hashes, persisted decisions and the historical canary
are never permission tokens.

## 2. Canonical memory / Truth Foundation ownership

| Mutation family | Accepted/current owner | Status |
|---|---|---|
| create/update canonical fact | existing `SQLiteGraphStore` canonical methods | CONVERGED |
| ESM transition/invalidation/restriction | existing `SQLiteGraphStore` mutation methods | CONVERGED |
| single-fact physical erasure | `ErasureCoordinator.erase_fact_durable()` | CONVERGED; `ForgettingEngine.forget_one()` is legacy adapter |
| PII claim redaction | `CanonicalPiiRedactor` over existing `SQLiteGraphStore` | CONVERGED on merged #283; privacy-sanitized history exception |
| async fact mutations | `AsyncSQLiteStore` → exact synchronous canonical owner | LEGACY_ADAPTER / CONVERGED; native async SQL disabled |
| archival claim rewrite | `CanonicalArchivalRewriter` over existing `SQLiteGraphStore` | CONVERGED on merged #285 · merge checkpoint `3100952f3dacf268f4d9c9b3f5a738f449663de6` |
| causal relation create/delete/reset | `CausalGraph` / `relations` | CONVERGED on merged #287 · checkpoint `615201ec1073dafb047028e88ce94463f4ef9b77` |
| post-create raw provenance binding | `SQLiteGraphStore.link_raw_to_fact()` | CONVERGED on merged #289 · current main `902b2b6335b05f9a6f956e75151a8e801f23ba1d` |
| initial raw provenance on fact creation | existing `SQLiteGraphStore` fact-create parent transactions | CONVERGED on merged #291 · current main `7a47f5dbb786fe267093857bf370fd03703207ac` |
| smart-KB fact create/classify/validate | existing `store_facts_batch()` + canonical ESM owner; builder orchestration only | REVIEW-STAGE on #292/#293 · NOT MAIN |
| associative relation/LTP | `RelationStore` / `fact_relations` | SEPARATE NON-CAUSAL MODEL · not merged into causal Canon |
| optional Neo4j causal persistence | `causal_persistence.py` | derived persistence; NOT canonical authority |
| optional NetworkX Graph Lab | `graph_lab.py` | read-only/in-memory projection; NOT canonical authority |

## 3. PII redaction contract

`CanonicalPiiRedactor` is a narrow mutation-family owner, not a second Canon service.
Successful changed claims use durable-snapshot CAS, preserve state/confidence, refresh
integrity, advance fact version once, sanitize affected VersionStore claim history,
append content-free AuditChain evidence, refresh FTS and append an active projection
refresh intent in one SQLite transaction. L0 is invalidated only after commit.

Exact plaintext time-travel recovery for the redacted claim surface is intentionally
sacrificed so the privacy operation does not re-store the removed PII. Full physical
erasure remains a separate durable-erasure contract.

## 4. Archival convergence contract — merged #284 / #285

The old path directly owned archive marker + canonical claim mutation. Current main now
uses:

```text
MemoryArchival
  eligibility + durable payload preparation + restore/reporting
        |
        v
CanonicalArchivalRewriter
        |
        v
existing SQLiteGraphStore transaction
  + durable-snapshot CAS
  + claim + integrity metadata + exact version bump
  + exact VersionStore pre-image
  + archived_facts marker
  + tamper-evident AuditChain FACT_UPDATED
  + synchronous FTS refresh when present
  + active migration-020 projection refresh intent
        |
        v
COMMIT → L0 invalidation
```

The protected squash merge is current-main truth at
`3100952f3dacf268f4d9c9b3f5a738f449663de6`. Filesystem payload creation remains a
precondition rather than a falsely claimed cross-system ACID transaction. A cleanup
failure after DB rollback can leave a non-canonical orphan file, never canonical success.

## 5. Causal Truth-edge convergence — merged #286 / #287

Protected merge #287 established `CausalGraph` / SQLite `relations` as the bounded local
causal Truth-edge mutation owner at checkpoint
`615201ec1073dafb047028e88ce94463f4ef9b77`.

`RelationStore` / `fact_relations` remains a separate associative/LTP model. NetworkX
Graph Lab remains SELECT-only analytics. Neo4j / Graphiti remain downstream/derived and
cannot grant local truth or reset authority. Automatic/non-manual causal input is
re-admitted as hypothesis/pending by default, and derived snapshots cannot self-promote
remote `validated/approved` labels into local authority. Derived reload is non-destructive
and cannot erase local Canon when the remote copy is empty, stale, unavailable or
rejected.

Exact final evidence for #287 is preserved in the merged PR, closed #286 and the existing
Notion FINAL block. Continuity remains 12/12 and schema v7; runtime/Operator
GO/runtime-authority/production-authority all remain false.

### Raw provenance linker convergence — merged #288 / #289

Protected squash merge #289 converged the explicit post-create raw provenance mutation
owner on current main `902b2b6335b05f9a6f956e75151a8e801f23ba1d`. `SQLiteGraphStore.link_raw_to_fact()`
now owns first-binding CAS semantics for an already-existing unbound fact, with the
VersionStore pre-image, `l0_fact_provenance` row and AuditChain evidence in the same
SQLite transaction. Same-source retries are idempotent, conflicting second sources fail
closed, and `RawMemoryStore.link_fact()` no longer owns an independent canonical UPDATE.
Issue #288 is CLOSED_COMPLETED.

### Initial-create raw provenance convergence — merged #290 / #291

Protected squash merge #291 converged initial `raw_*` provenance on current main
`7a47f5dbb786fe267093857bf370fd03703207ac`. New single/batch facts and replacement-fact
creation inside `supersede_fact_cas()` verify the L0 raw parent and close matching
`l0_fact_provenance` evidence inside the owning FACT_CREATED transaction. Existing durable
pointers cannot be rebound through generic upsert, while non-raw `derived_from` remains
fact-to-fact lineage. Issue #290 is CLOSED_COMPLETED; post-merge Full CI, Docker and
aggregate evidence all passed.

### Smart-KB fact-build residual — issue #292 / draft PR #293

Fresh post-#291 current-main inventory found that `scripts/build_kb_graph.py` could bypass
canonical fact authority: `--fast-fresh` directly inserted `facts`, and build paths used
raw SQL to classify facts and drive the ESM ladder. The resulting `velantrim_kb.db` can
become the ordinary `VELANTRIM_DB_PATH`, so this is a Canon surface rather than an inert
export.

PR #293 is review-stage only. Its candidate removes raw fact DML from the builder,
declares curated World Skills rows as `WORLD_FACT / EXTERNAL` before admission, delegates
create/update to existing `store_facts_batch()` evidence semantics, and delegates
validation to `promote_to_validated()` / canonical ESM transitions. Batch classification
changes become VersionStore/AuditChain-evidenced changes with coherent L0/L1 state.
`--fast-fresh` becomes only an empty-database precondition, and incomplete ingest or
validation fails the build. Causal edges remain owned by the already-converged
`CausalGraph`. These guarantees are NOT main truth until protected merge and post-merge
verification.

## 6. Projection authority

FTS, graph/vector indexes, caches, summaries, NetworkX analytics, Neo4j copies and
projection-outbox workers are derived/rebuildable surfaces. Projection state never wins
over Canon and cannot grant write or answer authority by itself.

## 7. Anti-bypass guarantees and review boundaries

Current-main guarantees include:

- no second canonical store or general write protocol was introduced by #283/#285/#289;
- runtime configuration cannot grant Operator GO;
- historical canary evidence cannot silently re-enable runtime;
- async callers cannot select the removed native-SQL fact write path;
- PII redaction does not retain ordinary plaintext VersionStore history for the redacted claim surface;
- archival Canon cannot point to a payload that failed its preparation precondition;
- failed archival CAS/version/audit/outbox operations commit no false canonical or audit success;
- causal `relations` create/delete/reset is converged on one `CausalGraph` mutation owner;
- automatic causal inference cannot silently default to `validated/approved`;
- NetworkX and Neo4j/Graphiti remain non-authoritative and derived reload is non-destructive;
- post-create raw provenance binding cannot mutate `facts.derived_from` without the #289 canonical evidence contract;
- conflicting second-source post-create provenance fails closed and the legacy raw-memory adapter owns no independent canonical SQL mutation.

Current-main #291 guarantee:

- NEW `raw_*` facts cannot establish Canon without matching same-parent-transaction L0 provenance evidence;
- missing raw/evidence/audit failure rolls back the owning creation transaction;
- generic upsert cannot rebind existing durable raw provenance;
- non-raw fact lineage remains unchanged.

Candidate #293 review boundary:

- smart-KB builder must own no direct `INSERT INTO facts` or `UPDATE facts SET` mutation path;
- curated WSC fact admission must use the existing canonical batch owner and evidence semantics;
- ESM validation must use canonical transition ownership rather than raw SQL;
- `--fast-fresh` may require empty storage but cannot grant a bootstrap authority bypass;
- incomplete/evidence-failed build must not report an accepted active smart-KB Canon;
- causal-edge ownership must remain on `CausalGraph`.

No producer/action/reminder/notification/tool/scheduler authority is added.

## 8. Historical Continuity checkpoints

| Block | Merge/checkpoint | Meaning |
|---|---|---|
| current-decision resolver | `dc30817f2c4abb1afcaab2f127e679d5f9b884d7` | schema v3 · 8/12 |
| durable lifecycle | `064845579c520e7464678cd0c41d9b650368dfa8` | schema v4 · 9/12 |
| runtime composition | `802e833fa251a8831add8a6b802a5ebb57533549` | schema v5 · 10/12 |
| controlled enablement | `66318e6883590cb29a4565157e0a3a25b3716d81` | schema v6 · 11/12 |
| observation mechanism | `456b762b1e752a2f5fb22762869336be9fed42a4` | mechanism present; still 11/12 at merge |
| bounded canary | `39ba28dbf6bce4da1e18d6726ae4f4f79dc5f24e` | schema v7 · 12/12 · rolled back to disabled |

## 9. Current continuation boundary

Continuity has no remaining capability: `12/12` is complete. Truth Foundation #50 is a
separate canonical-memory hardening workstream and remains OPEN while #292/#293 is
review-stage and until a fresh post-merge current-main inventory proves no other
meaningful #50 mutation family remains. Merged #290/#291 is current-main initial raw
provenance truth and is not a pending gate. Current review work does not authorize Phase
II, 13/12, ADAO, ARM-04, wider runtime activation, production rollout or a standing
Operator GO.
