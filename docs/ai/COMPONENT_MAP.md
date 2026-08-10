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
| archival claim rewrite | `CanonicalArchivalRewriter` over existing `SQLiteGraphStore` | REVIEW-STAGE on #285 until protected merge |
| causal relation create/delete | current `CausalGraph` direct relation-table mutation | REAL_GAP · separate future #50 block |
| optional Neo4j causal persistence | `causal_persistence.py` | derived persistence; NOT canonical authority |

## 3. PII redaction contract

`CanonicalPiiRedactor` is a narrow mutation-family owner, not a second Canon service.
Successful changed claims use durable-snapshot CAS, preserve state/confidence, refresh
integrity, advance fact version once, sanitize affected VersionStore claim history,
append content-free AuditChain evidence, refresh FTS and append an active projection
refresh intent in one SQLite transaction. L0 is invalidated only after commit.

Exact plaintext time-travel recovery for the redacted claim surface is intentionally
sacrificed so the privacy operation does not re-store the removed PII. Full physical
erasure remains a separate durable-erasure contract.

## 4. Archival convergence contract — issue #284 / PR #285

The legacy path previously did:

```text
MemoryArchival
→ archive JSON
→ raw INSERT archived_facts
→ raw UPDATE facts.claim + manual version bump
→ commit
```

The candidate ownership is:

```text
MemoryArchival
  eligibility + bounded payload preparation + restore/reporting
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
  + content-free AuditChain FACT_UPDATED
  + synchronous FTS refresh when present
  + active migration-020 projection refresh intent
        |
        v
COMMIT → L0 invalidation
```

`MemoryArchival` no longer owns direct `UPDATE facts` in the candidate branch.

### Filesystem boundary

Archive payload creation is a precondition, not a second Canon transaction:

```text
exclusive create → flush → fsync → validate payload exists
→ BEGIN IMMEDIATE SQLite canonical mutation
```

If SQLite/evidence fails, Canon and all same-DB evidence roll back. The coordinator
removes the just-created payload best-effort. An unremovable orphan file remains
non-canonical residue and cannot be interpreted as successful archival.

This adds no scheduler/background loop. Archival occurs only when an existing caller
explicitly invokes the coordinator.

## 5. Causal residual boundary

`CausalGraph.add_relation()` currently inserts forward/inverse rows and commits directly;
`remove_relation()` directly deletes and commits. Ingest-side causal bridge code may call
`add_relation()` for inferred relations. These writes are therefore a separate meaningful
#50 mutation family requiring a later bounded architecture/evidence convergence.

Do not solve causal mutation inside #285. Do not promote optional Neo4j persistence into
Canon while solving it.

## 6. Projection authority

FTS, graph/vector indexes, caches, summaries, Neo4j copies and projection-outbox workers
are derived/rebuildable surfaces. Projection state never wins over Canon and cannot grant
write or answer authority by itself.

## 7. Anti-bypass guarantees preserved

- no second canonical store or general write protocol is introduced by #285;
- runtime configuration cannot grant Operator GO;
- historical canary evidence cannot silently re-enable runtime;
- async callers cannot select the removed native-SQL write path;
- PII redaction cannot retain ordinary plaintext VersionStore history for the redacted
  claim surface;
- archival Canon cannot point to a payload that failed its preparation precondition;
- failed archival CAS/version/audit/outbox operations commit no false canonical or audit
  success;
- causal remains explicitly unresolved rather than being falsely marked converged;
- no producer/action/reminder/notification/tool/scheduler authority is added.

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
separate canonical-memory hardening workstream and remains OPEN while real mutation gaps
remain. Current review work does not authorize Phase II, 13/12, ADAO, ARM-04, wider
runtime activation, production rollout or a standing Operator GO.