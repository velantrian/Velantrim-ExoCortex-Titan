# ADR — Archival canonical claim-rewrite convergence

**Date:** 2026-08-10  
**Status:** Proposed on PR #285 until protected merge  
**Issue:** #284 · parent #50  
**Audited base:** `main@493b1b6b6204cc9a7f5de82709717a1b625e2234`

## Context

`core.memory_archival.MemoryArchival` historically mixed four responsibilities: archival
eligibility, filesystem payload creation, `archived_facts` bookkeeping, and a direct
canonical `facts.claim` UPDATE. The direct UPDATE manually bumped `fact_version` but did
not participate in the Truth Foundation mutation contract: no durable-snapshot CAS,
VersionStore pre-image, AuditChain event, integrity refresh, FTS refresh, projection
outbox intent, or post-commit cache invalidation.

This is a real residual Issue #50 bypass. It is separate from the causal-relation gap and
from #249 CAS contention characterization.

## Decision

Introduce one narrow mutation-family owner,
`core.archival_mutation.CanonicalArchivalRewriter`, over the existing
`SQLiteGraphStore` connection and transaction primitives.

`MemoryArchival` remains the coordinator for:

- selecting sufficiently old non-`ImmutableCore` facts;
- preparing the archive JSON payload;
- bounded batches (maximum 100 facts per payload);
- restore/read reporting and statistics;
- best-effort removal of a newly-created orphan payload after DB/evidence failure.

It no longer executes a direct `UPDATE facts`.

For each selected batch, the canonical SQLite transaction binds:

1. the durable source snapshot selected before payload creation;
2. a CAS on `fact_id + claim + updated_at`;
3. the claim rewrite to `[ARCHIVED: archive://…]`;
4. claim-derived integrity metadata refresh;
5. exactly one `fact_version` bump when the active schema contains the column;
6. exact pre-change VersionStore evidence;
7. an `archived_facts` marker;
8. a content-free/tamper-evident `AuditChain` `FACT_UPDATED` event;
9. synchronous FTS refresh when FTS exists;
10. a content-free projection refresh intent when migration 020 is active;
11. L0 invalidation only after commit.

Any stale CAS, version failure, audit failure, activated outbox failure, duplicate archive
marker, or SQLite failure rolls the whole SQLite transaction back. No false audit or
projection evidence is committed for a failed batch.

## Filesystem / SQLite boundary

A filesystem file and SQLite cannot participate in one literal ACID transaction without
adding a second transactional system or distributed transaction protocol, which this
bounded change explicitly rejects.

The fail-closed ordering is therefore:

```text
write unique archive payload with exclusive create
→ flush + fsync payload
→ validate payload exists
→ BEGIN IMMEDIATE canonical SQLite transaction
→ CAS + version + marker + audit + projections
→ COMMIT
→ invalidate L0
```

Canon is never allowed to point at a payload that was not successfully prepared first.
If the SQLite/evidence transaction then fails, the coordinator removes that newly-created
payload best-effort. If operating-system cleanup itself fails, the leftover file is an
**orphan non-canonical payload**, not a successful archive and not canonical truth. This
bounded residue must be observable in logs and may be cleaned operationally later; it
does not justify committing a false canonical archive claim.

## Why this is not a second Canon architecture

`CanonicalArchivalRewriter` owns only the archival claim-rewrite mutation family. It
introduces no new database, general write API, TruthGate, scheduler, runtime, singleton,
control plane, remote provider, or standing authority. It reuses existing
`SQLiteGraphStore`, VersionStore, AuditChain, FTS and projection-outbox contracts.

Archive files preserve payload history but do not become Canon. Neo4j/vector/FTS surfaces
remain derived projections.

## Authority boundary

This decision does not grant:

- ESM promotion authority;
- runtime activation;
- Operator GO;
- runtime authority;
- production authority;
- automatic/background archival scheduling;
- wider rollout.

Continuity remains `12/12`; project-state schema remains `v7`; runtime remains disabled.

## Alternatives rejected

### A. Keep raw SQL and merely add an AuditChain call

Rejected. It would still duplicate canonical version/CAS/integrity/projection semantics
and could drift again.

### B. Move archive files into a second transactional database

Rejected. It creates another durable authority/store and a reconciliation problem larger
than the bounded gap.

### C. Commit Canon first and write the archive payload afterward

Rejected. A crash or filesystem failure could leave a canonical claim pointing to a
payload that never existed.

### D. Make causal-relation hardening part of this PR

Rejected. Causal mutation is a separate real #50 gap with different ownership and must be
reviewed independently.

## Validation requirements

Before merge, exact-head evidence must show real temporary-SQLite tests for:

- happy path with preserved state/confidence and exact +1 version;
- dry-run and already-archived no-op with no false evidence;
- missing payload rejection before mutation;
- stale snapshot/CAS miss;
- forced VersionStore failure rollback;
- forced AuditChain failure rollback;
- `archived_facts`, FTS and projection-outbox transaction consistency;
- one stale member rolling back the rest of its archive batch;
- payload cleanup after a failed DB/evidence transaction;
- structural proof that the legacy coordinator no longer owns `UPDATE facts`.

Full CI, Docker and protected aggregate merge evidence are required on the final head.

## Residual scope

Parent #50 remains OPEN. Causal relation create/delete mutation hardening remains a
separate residual gap. Issue #249 remains separate. No production-readiness claim follows
from this convergence.