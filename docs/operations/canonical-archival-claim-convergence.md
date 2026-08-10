# Canonical archival claim convergence

Tracking issue: #284  
Parent Truth Foundation: #50  
Implementation PR: #285

## Purpose

This bounded block removes the archival canonical-claim rewrite from
`MemoryArchival`'s legacy raw-SQL ownership. The coordinator still selects old facts,
prepares/restores archive payloads and reports results, but canonical mutation is owned
by `CanonicalArchivalRewriter` over the existing `SQLiteGraphStore` transaction.

## Before

```text
MemoryArchival
  → write JSON payload
  → INSERT archived_facts
  → raw UPDATE facts.claim + manual fact_version bump
  → commit
```

Missing from that canonical rewrite were durable-snapshot CAS, VersionStore,
AuditChain, integrity refresh, FTS/outbox consistency and post-commit L0 invalidation.

## After

```text
MemoryArchival eligibility/coordinator
  → unique payload write + flush + fsync
  → CanonicalArchivalRewriter
       → existing SQLiteGraphStore transaction
       → CAS facts.claim + updated_at snapshot
       → exact VersionStore pre-image
       → archived_facts marker
       → content-free AuditChain FACT_UPDATED
       → integrity metadata refresh
       → exact +1 fact_version when active
       → synchronous FTS refresh when present
       → migration-020 content-free projection refresh intent when active
  → COMMIT
  → post-commit L0 invalidation
```

## Failure contract

- payload creation failure: no canonical mutation is attempted;
- missing payload precondition: fail before canonical mutation;
- stale CAS: whole SQLite batch rolls back;
- VersionStore/AuditChain/outbox/SQLite failure: whole SQLite batch rolls back;
- no failed batch commits an `archived_facts` marker, audit event or projection intent;
- if payload exists but SQLite transaction fails, the coordinator removes that newly
  created file best-effort;
- an OS-level cleanup failure may leave a non-canonical orphan file, but never converts
  the failed transaction into canonical success.

The batch atomicity unit is one generated archive payload, bounded at 100 selected facts.
A later batch failure does not roll back earlier independently committed payload batches
and does not misreport them as failed.

## Authority boundary

This convergence introduces no new Canon, general write protocol, TruthGate, runtime,
scheduler, control plane, global authority or remote write path. It does not enable
background archival. It does not change Continuity, schema v7, runtime enablement,
Operator GO, runtime authority or production authority.

## Residual Truth Foundation work

This block is archival-only. Causal relation mutation remains a separate #50 gap.
Async fact mutation is already an adapter over synchronous canonical semantics. Issue
#249 remains a separate contention-characterization task.

## Review evidence boundary

Until PR #285 is protected-merged and post-merge CI is verified, this document describes
review-stage implementation, not `main` implementation truth. Review-stage Notion must be
marked `REVIEW EVIDENCE / NOT MAIN` and pinned to the exact final PR head.