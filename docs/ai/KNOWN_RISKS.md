# ⚠️ Known Risks and Required Proof

**Snapshot:** 2026-08-12
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
the removed plaintext is not re-persisted. This is implementation truth at checkpoint
`493b1b6b6204cc9a7f5de82709717a1b625e2234`.

It does not prove removal from arbitrary metadata, immutable/raw origins, every external
backend, backups or unrelated historical logs. Full durable physical erasure remains a
separate ErasureCoordinator contract; no certified GDPR claim follows.

## P1 — Archival filesystem/SQLite boundary remains bounded

Issue #284 / merged PR #285 converged archival canonical claim rewrite on the existing
`SQLiteGraphStore` evidence primitives at checkpoint
`3100952f3dacf268f4d9c9b3f5a738f449663de6`.

The payload is created/fsynced before Canon may point at it; canonical claim, VersionStore,
AuditChain, archive marker, FTS and active outbox intent are one SQLite transaction. A
filesystem file cannot join that SQLite ACID transaction without another transactional
system. If the SQLite transaction fails after payload creation, cleanup remains
best-effort. An OS cleanup failure can leave a **non-canonical orphan payload**; that
residue is never canonical archival success.

## Reduced risk — Causal Truth-edge mutation ownership converged

Issue #286 / merged PR #287 converged SQLite `relations` mutation on `CausalGraph` at
checkpoint `615201ec1073dafb047028e88ce94463f4ef9b77`. Relation create/batch/remove/reset
uses the bounded canonical owner with same-transaction lifecycle AuditChain evidence.
Automatic/non-manual input defaults to hypothesis/pending, derived snapshots cannot
self-promote authority labels, and Neo4j/Graphiti reload cannot destructively replace
local Canon. `RelationStore` / `fact_relations` remains a separate associative model.

Residual risks remain bounded: explicit future accepted-label callers still need their own
authorized admission surface, and full graph reset cost grows with graph size. Neither
risk justifies a raw-SQL bypass or remote truth authority.

## Reduced risk — Post-create raw provenance binding converged

Issue #288 is CLOSED_COMPLETED and PR #289 is protected-merged on current main
`902b2b6335b05f9a6f956e75151a8e801f23ba1d`. For an already-existing unbound fact,
`SQLiteGraphStore.link_raw_to_fact()` owns first-binding CAS semantics with VersionStore
pre-image, `l0_fact_provenance` and AuditChain evidence in one SQLite transaction.
Same-source retries are idempotent, conflicting second sources fail closed, and legacy
`RawMemoryStore.link_fact()` no longer owns an independent canonical UPDATE.

This convergence does **not** imply that every fact-create surface was already covered;
that separate residual is tracked below as #290/#291.

## P0 — Initial fact-create raw provenance remains review-stage

Fresh post-#289 current-main inventory found that a NEW fact can receive `derived_from`
directly during single/batch creation. Because this historical field also carries
fact-to-fact lineage, a global ban or strip would be unsafe: MeaningParser GIST → VERBATIM
lineage is not L0 raw provenance.

Issue #290 / draft PR #291 is the bounded candidate. On the review head, `raw_*` denotes
L0 raw identity: the raw parent must exist and matching `l0_fact_provenance` evidence is
created inside the same owning FACT_CREATED transaction. Generic update paths preserve an
existing durable pointer rather than rebinding it; non-raw lineage remains unchanged.
Batch creation and `supersede_fact_cas()` use the same parent-transaction rule. A new fact
has no predecessor, so the candidate does not fabricate a VersionStore pre-image or a
second FACT_UPDATED event. Missing raw/evidence/audit failure must roll the parent
transaction back.

Focused regression evidence on implementation head
`927972c39c167098f2424fe64b99e45744e6e035` passed 9/9 tests, including direct create,
batch create, non-raw lineage, no-rebind and supersede creation. Exact-head Full CI
`31574249831` and Docker `31574249775` were SUCCESS before this AI truth-doc
reconciliation. These are **review evidence only**; #291 is not main truth until protected
merge and post-merge verification.

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
