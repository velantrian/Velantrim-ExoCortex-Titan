# ⚠️ Known Risks and Required Proof

**Snapshot:** 2026-08-05  
**Current `main`:** `320d5ae9f89780efc553ffbfc3a17c1ebc83b47e`

Code presence does not close a risk. Closure requires focused/full validation, wiring and operational evidence.

## P0

- Projection dispatcher is implemented/tested but not runtime-wired or observed.
- Production compose contracts remain materially inconsistent.
- Static-analysis and coverage scope do not uniformly cover all runtime surfaces.
- Store-wide WAL/contention/crash/restart/disk-full testing is incomplete.
- Dependency/build reproducibility and wheel/container parity remain incomplete.

## P1 — Continuity

### R2 is a shadow/read-side substrate, not durable continuity

R2 is merged and tested but remains process-local, disposable and unwired. No trusted producer, durable adapter, retention/erasure/access-control contract or operational input bound exists. Exact goal matching can miss real continuations; explicit notebook links may be stale; thread links are rebuildable projections, not truth.

### R3 adds projections, not trusted admission or policy authority

Draft PR #203 adds context, current-state, goal and open-loop projections plus adapters to the existing WorkingMemory path.

Residual risks:

- assertions, attestations and open-loop signals are trusted typed inputs; their producer and authorization contract is not part of R3;
- caller-supplied attention, recall, eligibility, restriction, erasure, protection and conflict fields have no accepted single policy owner yet;
- GoalStack snapshots can contain legacy or previously inferred content; explicit attestation is required but attestation issuance is not designed here;
- current-state reconciliation is deterministic policy, not external truth;
- selected state projections can still be wrong if their immutable source assertions are wrong;
- contested projections require review and must not become answer/action authority;
- virtual continuity documents are derived projections, not original source documents;
- projection adapters preserve provenance only as supplied by the source records;
- no durable retention, consent, erasure or tenant boundary is authorized;
- no runtime caller, feature flag, startup hook or user-visible integration is included.

Required before runtime or durable use:

1. trusted producer contracts for assertions, attestations and open-loop signals;
2. explicit policy owner for all Gate input fields;
3. purpose/consent/retention/erasure/access-control review;
4. adversarial tests for forged source refs, stale attestations and cross-user leakage;
5. evaluation of contested-state behavior and false current-state selection;
6. no Canon, answer or action authority;
7. separate operator approval.

### Remaining recovery

```text
R4 continuity-aware ComputeController signals
→ R5 replay evaluation + Advisory shadow + disabled runner
```

R4 must include differential legacy behavior proof and exhaustive downstream coverage for any new compute path such as `DEFER_PATH`. Old #131–#147 remain historical source material, not an accepted merge route.

### R1 schema commitment

R1 canonical bytes/hashes are an interoperability contract. Field changes require a new schema version and golden vectors.

## Other P1

- ARM-03 remains heuristic proposal-only; candidate precision/privacy evidence is needed before ARM-04.
- Identity remains a legacy mutable prototype without accepted consent/scope, contestation, audit/version and erasure lifecycle.
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
