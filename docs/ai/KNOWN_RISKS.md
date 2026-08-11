# ⚠️ Known Risks and Required Proof

**Snapshot:** 2026-08-11
**Continuity:** `12/12 = 100%` — complete  
**Runtime:** `CURRENTLY DISABLED · CURRENT OPERATOR GO ABSENT · HISTORICAL OBSERVED=true · NO RUNTIME AUTHORITY · NO PRODUCTION AUTHORITY`  
**Governance:** active `main-governance` · solo mode · approvals `0` · required check `Titan aggregate merge evidence`

A green CI run, manifest, config, historical canary, archive payload, audit record or
Notion update is evidence only. None of them grants current permission, runtime authority
or production authority.

## P0 — No current Operator GO or deployed activation

The completed bounded canary used a single-use human authorization that is exhausted.
Current runtime state remains disabled and current Operator GO remains false. Any future
real activation requires a separately scoped current decision and explicit Operator GO.

## P0 — Concrete live current-decision owner adapters remain unselected

The six Continuity current-decision ports still lack accepted live deployment adapters
for principal, authorization, consent/lawful basis, restriction, erasure and
PolicySnapshot. Continuity 12/12 does not replace those owners.

## P1 — Continuity 12/12 is not production readiness

The internal mechanism chain and one rolled-back canary do not prove production traffic,
SLOs, disaster recovery, public multi-user rollout, independent security review or
production-scale failure recovery.

## P1 — Solo governance has no independent approval gate

The active repository ruleset requires zero approvals in solo mode, while requiring PR
flow, thread resolution and the aggregate status check. Independent review is therefore
not implied by mergeability. Codex usage-limit failures must be recorded as `NOT RUN —
USAGE LIMIT`, never as approval.

## P1 — Uncharacterized CAS-contention failure

Issue #249 remains OPEN and separate. The known `BrokenBarrierError` evidence is currently
consistent with runner/scheduling-sensitive test orchestration; a production CAS defect
has not been proven. Do not weaken one-winner/one-intent assertions without evidence.

## P1 — PII claim redaction is bounded, not universal physical erasure

Issue #282 / merged PR #283 converged PII **claim** redaction on
`CanonicalPiiRedactor`. Affected VersionStore claim history is intentionally sanitized so
the removed plaintext is not re-persisted. This is current-main implementation truth at
`493b1b6b6204cc9a7f5de82709717a1b625e2234`.

It does not prove removal from arbitrary metadata, immutable/raw origins, every external
backend, backups or unrelated historical logs. Full durable physical erasure remains a
separate ErasureCoordinator contract; no certified GDPR claim follows.

## P1 — Archival filesystem/SQLite boundary remains bounded

Issue #284 / merged PR #285 converged archival canonical claim rewrite on the existing
`SQLiteGraphStore` evidence primitives. It is current-main truth at
`3100952f3dacf268f4d9c9b3f5a738f449663de6`.

The payload is created/fsynced before Canon may point at it; canonical claim, VersionStore,
AuditChain, archive marker, FTS and active outbox intent are one SQLite transaction. A
filesystem file cannot join that SQLite ACID transaction without another transactional
system. If the SQLite transaction fails after payload creation, cleanup remains
best-effort. An OS cleanup failure can leave a **non-canonical orphan payload**; that
residue is never canonical archival success.

## Reduced risk — Causal Truth-edge mutation ownership converged

Issue #286 / merged PR #287 converged SQLite `relations` mutation on `CausalGraph` at
current main `615201ec1073dafb047028e88ce94463f4ef9b77`. Relation create/batch/remove/reset
now uses the bounded canonical owner with same-transaction lifecycle AuditChain evidence.
Automatic/non-manual input defaults to hypothesis/pending, derived snapshots cannot
self-promote authority labels, and Neo4j/Graphiti reload cannot destructively replace
local Canon. `RelationStore` / `fact_relations` remains a separate associative model.

Residual risks remain bounded: explicit future accepted-label callers still need their own
authorized admission surface, and full graph reset cost grows with graph size. Neither
risk justifies a raw-SQL bypass or remote truth authority.

## P0 — Raw provenance canonical evidence remains review-stage

Fresh residual audit of parent #50 after #287 found one meaningful mutation family:
`facts.derived_from`. Current main still allows `SQLiteGraphStore.link_raw_to_fact()` to
change the field without VersionStore/AuditChain evidence, and legacy
`RawMemoryStore.link_fact()` owns a second direct UPDATE path.

Issue #288 / draft PR #289 is the bounded convergence candidate. Review-head semantics
must preserve first-binding-only ownership, same-source idempotency, different-source
fail-closed behavior, same-transaction VersionStore + provenance + AuditChain evidence,
and legacy delegation to the existing canonical owner. These guarantees are **not main
truth** until protected merge and post-merge verification.

## P1 — Full causal reset can generate proportional audit volume

An explicit destructive causal reset enumerates physical relation IDs and appends a
structured `relation_removed` event for each removed row in the same transaction. This
maximizes audit fidelity but means transaction work grows with graph size. It is an
explicit admin/KB operation, not a background loop.

Production-scale reset latency/size is not proven by #287 and must not be represented as
such. This risk does not justify bypassing the canonical owner or dropping audit evidence.

## Reduced risk — async canonical mutation bypass

`AsyncSQLiteStore` is an async execution adapter over exact synchronous canonical methods
using `asyncio.to_thread`. The former native aiosqlite write implementation remains
explicitly disabled. Existing equivalence and cancellation tests prove the adapter does
not own an independent SQL mutation path.

## Operational residuals

Still not proved:

- multi-process write contention under production load;
- large-graph full-reset latency/audit volume under production load;
- disk-full/filesystem-permission behavior at production scale;
- live backup/restore and disaster-recovery orchestration;
- external audit service/SLO/alerting coverage;
- independent security review or penetration test;
- complete production evidence for Reader Core (#120).

## Risk update rule

Keep these states separate:

```text
IMPLEMENTED
TESTED
WIRED
RUNTIME CURRENTLY ENABLED
OPERATOR AUTHORIZATION PRESENT
OPERATOR GO
OBSERVED                 <- durable historical evidence
RUNTIME AUTHORITY
PRODUCTION AUTHORITY
PRODUCTION-READY
```

Never infer a later state from an earlier one. In particular, historical observation and
12/12 Continuity never imply current permission or production authority.