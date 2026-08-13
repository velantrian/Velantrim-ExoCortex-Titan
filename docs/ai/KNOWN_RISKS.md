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

## P1 — Causal ownership merged with three unresolved failure-path findings

Issue #286 / merged PR #287 converged SQLite `relations` mutation on `CausalGraph` at
checkpoint `615201ec1073dafb047028e88ce94463f4ef9b77`. Relation create/batch/remove/reset
uses the bounded canonical owner with same-transaction lifecycle AuditChain evidence.
Automatic/non-manual input defaults to hypothesis/pending, derived snapshots cannot
self-promote authority labels, and Neo4j/Graphiti reload cannot destructively replace
local Canon. `RelationStore` / `fact_relations` remains a separate associative model.

Post-merge Codex review then found three logical defects that green CI did not cover:
snapshot admission could hide WriteGate/AuditChain failure as zero imported rows, an
audited reset failure could retain a singleton backed by a closed connection, and
ambiguous legacy NULL-source duplicates could delete the wrong inverse companions. The
current bounded follow-up candidate propagates admission failures, detaches reset state
before closing, binds inverse deletion by identity, and fails closed when old rows cannot
be paired unambiguously. Until that follow-up is protected-merged and the three #287
threads are evidence-resolved, the earlier "converged" label is incomplete.

Other residuals remain bounded: explicit future accepted-label callers still need their
own authorized admission surface, and full graph reset cost grows with graph size. Neither
risk justifies a raw-SQL bypass or remote truth authority.

## Reduced risk — Post-create raw provenance binding converged

Issue #288 is CLOSED_COMPLETED and PR #289 is protected-merged on current main
`902b2b6335b05f9a6f956e75151a8e801f23ba1d`. For an already-existing unbound fact,
`SQLiteGraphStore.link_raw_to_fact()` owns first-binding CAS semantics with VersionStore
pre-image, `l0_fact_provenance` and AuditChain evidence in one SQLite transaction.
Same-source retries are idempotent, conflicting second sources fail closed, and legacy
`RawMemoryStore.link_fact()` no longer owns an independent canonical UPDATE.

The separate initial-create residual was subsequently converged by merged #290/#291 on
current main `7a47f5dbb786fe267093857bf370fd03703207ac`.

## Reduced risk — Initial fact-create raw provenance converged

Issue #290 is CLOSED_COMPLETED and PR #291 is protected-merged on current main
`7a47f5dbb786fe267093857bf370fd03703207ac`. NEW `raw_*` single/batch facts and
replacement-fact creation close L0 provenance evidence inside their owning creation
transaction; non-raw lineage remains unchanged, generic upsert cannot rebind an existing
durable pointer, and failure rolls back. Pre/post-merge Full CI, Docker and aggregate
evidence passed. This is current-main truth, not review-stage evidence.

## Reduced risk — Smart-KB fact-build authority converged

Fresh post-#291 inventory found that `scripts/build_kb_graph.py` could directly insert
canonical facts and use raw SQL to classify/validate them. Because `serve_smart_kb.ps1`
can install the resulting database as ordinary `VELANTRIM_DB_PATH`, that was a real Truth
Foundation authority gap. Protected merge #293 converged it on current main `c80c8d47588de3d2607c7e1b10aa1677eb84383f`.

Issue #292 is CLOSED_COMPLETED and PR #293 is protected-merged. The accepted path
removes raw fact DML from builder orchestration, admits curated facts through existing
`store_facts_batch()` policy/VersionStore/AuditChain semantics, uses canonical ESM
promotion, treats `--fast-fresh` only as an empty-DB precondition, and fails incomplete
builds. Existing `CausalGraph` ownership is unchanged. Final pre-merge head `48817c5b0067d085135d4e8f144a620a34265597`
passed Full CI `31580684106`, Docker `31580683989`, and ready aggregate `31594821320`;
post-merge main passed Full CI `31594960307`, Docker `31594960229`, and aggregate
`31594960289`. A fresh current-main residual inventory found `REAL_GAP=0`, so parent #50
is CLOSED_COMPLETED. This does not imply production readiness or runtime authority.

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

## P1 — ModelFreeCore was merged before substantive review

Issue #295 / PR #296 is merged on `main@e8adfeaeabc13ab429f5f309ee1c4d6b56d27d96`.
Final-head and post-merge Full CI, Docker and aggregate evidence passed, but no substantive
independent review occurred before merge.

A post-merge audit found that the claimed lexical-only boundary still inherited an
opt-in cognitive reranker; graph collection called the DDL-capable singleton initializer
and swallowed read failures; the renderer called `UNVERIFIED` user reports confirmed
data; and `L2Query` accepted malformed bool/non-string inputs. The current bounded
follow-up candidate closes those paths fail-closed and adds adversarial tests. Until that
follow-up is protected-merged, #296's green CI must not be represented as proof of those
logical guarantees.

Even after hardening, Phase 1 does not prove runtime routing, default-route replacement,
CapabilityRegistry, embedding/vector architecture, ADAO, LLM execution, network/provider
access or production readiness. Optional graph absence remains non-blocking; a graph that
is present but unreadable must not produce a falsely complete answer.

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
