# ⚠️ Known Risks and Required Proof

**Snapshot:** 2026-08-10  
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

## P1 — Archival filesystem/SQLite boundary

Issue #284 / PR #285 converges the archival canonical claim rewrite on existing
`SQLiteGraphStore` evidence primitives. The candidate contract creates, flushes and
fsyncs the unique archive payload before a SQLite transaction may point Canon at it.
CAS/version/audit/marker/FTS/outbox failures roll the SQLite batch back.

A filesystem file cannot participate in the same SQLite ACID transaction without adding
another transactional system. If the DB/evidence transaction fails after payload
creation, cleanup is best-effort. An OS-level cleanup failure may therefore leave a
**non-canonical orphan archive payload**. That residue must never be represented as a
successful canonical archive. This risk is bounded and documented, not hidden.

Until PR #285 is protected-merged and post-merge verified, the archival section is
review-stage evidence, not `main` truth.

## P1 — Causal relation mutation remains a separate Truth Foundation gap

Current `CausalGraph.add_relation()` / `remove_relation()` own direct relation-table
mutation and commit semantics without the same canonical AuditChain/version-policy
contract required by #50. Ingest-side heuristic code can call `add_relation()` directly.
This is intentionally **not** repaired in PR #285; it remains the next separate residual
mutation family to audit/converge after archival finalization.

Optional Neo4j causal persistence is downstream/derived persistence and must not become a
second Canon owner while this is addressed.

## Reduced risk — async canonical mutation bypass

`AsyncSQLiteStore` is an async execution adapter over exact synchronous canonical methods
using `asyncio.to_thread`. The former native aiosqlite write implementation remains
explicitly disabled. Existing equivalence and cancellation tests prove the adapter does
not own an independent SQL mutation path.

## Operational residuals

Still not proved:

- multi-process write contention under production load;
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