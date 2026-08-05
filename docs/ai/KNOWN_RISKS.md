# ⚠️ Known Risks and Required Proof

**Snapshot:** 2026-08-05  
**Current `main`:** `06529700d70854504b88629eeecf737bdc6b81d5`

Code presence does not close a risk. Closure requires focused/full validation, wiring and
operational evidence.

## P0

- Projection dispatcher is implemented/tested but not runtime-wired or observed.
- Production compose contracts remain materially inconsistent.
- Static-analysis and coverage scope do not uniformly cover all runtime surfaces.
- Store-wide WAL/contention/crash/restart/disk-full testing is incomplete.
- Dependency/build reproducibility and wheel/container parity remain incomplete.

## P1 — Continuity

### R2 is a shadow/read-side substrate, not durable continuity

The R2 recovery branch adds a process-local ledger, read-only notebook bridge and
conservative deterministic thread projection.

Residual risks:

- `LocalShadowLedger` is process-local and lost on restart;
- it is not a Native Kernel implementation or production event store;
- no trusted event producer is wired;
- no purpose/consent/retention/erasure/access-control policy authorizes durable event
  storage;
- exact goal matching can miss real continuations;
- explicit notebook links may be stale or incorrect source data;
- thread links are rebuildable projections, not truth;
- direct callers must impose an operational input bound before any runtime wiring;
- no concurrency/process durability claim follows from an in-process lock;
- legacy notebook rows can contain model-generated or unconfirmed text.

Required before any runtime/durable promotion:

1. explicit event producer and authorization context;
2. bounded queue/batch/cancellation/restart contract;
3. durable adapter RFC with idempotency, retention, erasure and audit;
4. false-link/missed-link evaluation on synthetic or consented data;
5. privacy/security review;
6. no Canon, answer or action authority;
7. operator approval in a separate PR.

### Continuity recovery remains incomplete beyond R2

```text
R3 state + qualified goals/open loops + WorkingMemory adapters
→ R4 compute signals + replay + Advisory shadow
→ R5 disabled complete shadow runner
```

All recovery PRs must be independently green on current `main`. The old #131–#147 chain
is not an accepted merge path. Fixes belong in the lowest owning layer. `DEFER_PATH`
requires exhaustive downstream coverage and legacy behavior requires differential tests.

### R1 schema commitment

R1 canonical bytes/hashes are an interoperability contract. Field changes require a new
schema version and golden vectors.

## Other P1

- ARM-03 remains heuristic proposal-only; candidate precision/privacy evidence is needed
  before ARM-04.
- Identity remains a legacy mutable prototype without accepted consent/scope,
  contestation, audit/version and erasure lifecycle.
- Canon mutation ownership is not proven unified across every family.
- `server.py` remains a composition monolith.
- Shared API key is not per-user/tenant authorization.
- Wheel and container require separate supported-artifact contracts.

## P2

- large generated knowledge assets need a reproducible distribution strategy;
- historical audits need verified-SHA/superseded indexing;
- repository governance settings and discovery metadata need continued hardening.

## Update rule

Use exact states: proposed, implemented, tested, wired, enabled and observed.
