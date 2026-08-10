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
| archival claim rewrite | `CanonicalArchivalRewriter` over existing `SQLiteGraphStore` | CONVERGED on merged #285 · current main `3100952f3dacf268f4d9c9b3f5a738f449663de6` |
| causal relation create/delete/reset | candidate `CausalGraph` canonical owner on #286/#287 | REVIEW-STAGE · NOT MAIN until protected merge |
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

## 5. Causal Truth-edge convergence — issue #286 / draft PR #287

Fresh ownership audit separates four graph-shaped surfaces:

```text
SQLite relations
    = causal Truth-edge Canon
    = candidate single mutation owner: CausalGraph

fact_relations / RelationStore
    = associative strength + LTP/LTD model
    = separate semantics, not causal Canon

NetworkX Graph Lab
    = SELECT-only in-memory analytics

Neo4j causal persistence
    = downstream/derived copy
```

On the #287 review branch, `CausalGraph` is the candidate single canonical owner for
`relations` create/batch/remove/reset. Candidate semantics bind WriteGate, deterministic
validation, one caller-owned SQLite transaction and same-transaction per-relation
AuditChain lifecycle evidence. Audit failure rolls the relation mutation back.

Forward + inverse rows are one atomic create unit. Semantic duplicate input returns the
already durable relation ID rather than a generated phantom ID and creates no false audit
event.

### Proposal / truth boundary

Automatic inference is not accepted causal truth. Unless an explicit admission/review
path supplies stronger labels:

```text
knowledge_status != known OR inference_source is non-manual
→ truth_status = hypothesis
→ review_state = pending
```

Approved traversal reads remain approved-only by default. Diagnostics may explicitly
inspect pending rows. HITL approval of an edge suggestion may authorize recording a
hypothesis; it does not by itself validate the causal proposition as truth.

### Candidate bypass removal

On #287, KB batch writes/deletes and admin/pipeline reset surfaces delegate durable
`relations` mutation to `CausalGraph`. `create_inverse=False` is rejected for canonical
writes so a caller cannot create a deliberately unaudited half-edge.

Dependent relation deletion inside the already-durable fact-erasure transaction remains
part of that parent erasure transaction and is not double-logged as an independent
causal mutation merely to satisfy #286.

This section is **review evidence only** until #287 is protected-merged and post-merge
verified. It grants no runtime permission or production authority.

## 6. Projection authority

FTS, graph/vector indexes, caches, summaries, NetworkX analytics, Neo4j copies and
projection-outbox workers are derived/rebuildable surfaces. Projection state never wins
over Canon and cannot grant write or answer authority by itself.

## 7. Anti-bypass guarantees and review boundaries

Current-main guarantees:

- no second canonical store or general write protocol was introduced by #283/#285;
- runtime configuration cannot grant Operator GO;
- historical canary evidence cannot silently re-enable runtime;
- async callers cannot select the removed native-SQL fact write path;
- PII redaction does not retain ordinary plaintext VersionStore history for the redacted claim surface;
- archival Canon cannot point to a payload that failed its preparation precondition;
- failed archival CAS/version/audit/outbox operations commit no false canonical or audit success.

Candidate #287 guarantees, not yet main truth:

- causal `relations` create/delete/reset is converged on one `CausalGraph` mutation owner;
- automatic inference cannot silently default to `validated/approved`;
- KB/admin/pipeline surfaces do not own independent durable causal SQL mutation;
- NetworkX and Neo4j remain non-authoritative;
- `RelationStore/fact_relations` is not falsely merged into causal Canon.

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
separate canonical-memory hardening workstream and remains OPEN while #286/#287 is under
review and until a fresh post-merge residual inventory proves no other meaningful #50
mutation family remains. Current review work does not authorize Phase II, 13/12, ADAO,
ARM-04, wider runtime activation, production rollout or a standing Operator GO.
