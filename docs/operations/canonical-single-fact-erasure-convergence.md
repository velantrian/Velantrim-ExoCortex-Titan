# Canonical single-fact erasure convergence

Tracking issue: #279  
Parent truth-foundation issue: #50  
Implementation PR: #280

## Status and purpose

This bounded hardening block removes a legacy duplicate physical-delete owner from
`core.forgetting.ForgettingEngine.forget_one()`.

Before this change, the compatibility API implemented its own raw SQLite deletion
sequence alongside Titan's durable `core.erasure_coordinator.ErasureCoordinator`.
That duplicated destructive mutation semantics and could bypass the durable erasure
job, residual, projection-cleanup, subject-fencing, and completion-tombstone lifecycle.

After this change, the ownership contract is:

```text
ForgettingEngine.forget_one()
        |
        v
legacy compatibility / ForgetVerdict mapping
        |
        v
ErasureCoordinator.erase_fact_durable()
        |
        v
one durable physical single-fact erasure lifecycle
```

`ForgettingEngine.forget_one()` no longer independently executes `DELETE FROM facts`,
drops the delete guard, or inserts its own canonical erasure tombstone.

## Authority boundary

`ErasureCoordinator` remains the existing erasure authority. This convergence does
not introduce a new authority owner, canonical store, scheduler, control plane,
runtime activation, persistence model, Operator GO, runtime authority, or production
authority.

The legacy API remains callable only as a compatibility adapter. Durable completion
state, residual state, job identity, subject fencing, and completion tombstones are
owned by `ErasureCoordinator`.

The legacy `fact_forgotten` provenance event is retained only as post-`COMPLETE`
compatibility side evidence. It is not deletion authority and cannot turn a failed or
partial durable erasure into success.

## Fail-closed result mapping

The compatibility adapter maps durable outcomes conservatively:

| Durable result | Legacy compatibility result |
|---|---|
| `COMPLETE`, erased now | `allowed=true`, `reason=deleted` |
| cached `COMPLETE` | `allowed=true`, `reason=already_deleted`, zero newly affected facts |
| `NOT_FOUND` | `allowed=false`, `reason=fact_not_found` |
| `PARTIAL` | fail closed |
| `FAILED` | fail closed |
| `RESIDUAL_IMMUTABLE_DATA` | fail closed |
| `SUBJECT_CONFLICT` | fail closed |
| unexpected exception/outcome | fail closed |

A terminal attempt is not automatically a successful complete erasure. In particular,
known immutable raw-origin residual data is never translated into a false GDPR
completion claim.

## Tenant/storage isolation

A `ForgettingEngine` constructed with a custom `db_path` must use explicitly bound
tenant embeddings and ngram storage. The compatibility adapter reuses the existing
fail-closed binding helpers before destructive work. It does not silently fall back to
an unrelated process-global derived store.

The adapter creates a store bound to its configured facts database, initializes the
existing schema contract, constructs the existing `ErasureCoordinator` with those
bound dependencies, and closes only the temporary facts-store connection it owns.

## Evidence

The focused regression suite in
`tests/test_forget_one_erasure_convergence.py` covers:

- real temporary-SQLite tenant erasure and global-store isolation;
- durable erasure-job and completion-tombstone evidence;
- repeated/idempotent completed erasure without a second job or tombstone;
- not-found behavior without a durable job;
- Ring Zero denial before tenant backends are opened;
- a structural guard proving the legacy method no longer contains an independent
  `DELETE FROM facts` or delete-trigger bypass;
- explicit fail-closed compatibility mapping for partial, failed, immutable-residual,
  and subject-conflict outcomes.

PR #280's first CI head exposed a test-harness-only stale-module monkeypatch in the
new parameterized mapping test after earlier full-suite fixtures re-imported `core.*`.
Five preceding new integration tests passed. The harness was corrected to patch the
fresh module object resolved at call time, matching the repository's established
full-suite pattern. Production code was not changed by that correction.

Merge requires fresh exact-head success from the repository's protected CI and Docker
workflows plus the `Titan aggregate merge evidence` gate. PR metadata and Notion are
part of that evidence under `Documentation impact: GITHUB_AND_NOTION`.

## Remaining limitations and non-goals

This block closes only the legacy `forget_one()` duplicate physical-delete path. It
does **not** close #50 as a whole.

Still separate:

- PII redaction canonical-write/AuditChain convergence;
- archival claim-rewrite canonicalization;
- causal-relation AuditChain coverage;
- #249 CAS-contention characterization;
- wider runtime activation, ADAO, ARM-04, or production rollout.

Continuity remains exactly `12/12`. Runtime enablement, current Operator GO, runtime
authority, and production authority remain unchanged by this block.
