# ⚠️ Known Risks and Required Proof

**Snapshot:** 2026-08-05  
**Current `main`:** `529d8b6b182b1a548d27558173f0aca473bcc400`

Code presence does not close a risk. Closure requires focused/full validation, wiring and operational evidence.

## P0

- Projection dispatcher is implemented/tested but not runtime-wired or observed.
- Production compose contracts remain materially inconsistent.
- Static-analysis and coverage scope do not uniformly cover all runtime surfaces.
- Store-wide WAL/contention/crash/restart/disk-full testing is incomplete.
- Dependency/build reproducibility and wheel/container parity remain incomplete.

## P1 — Continuity R1–R4

R1 contracts, R2 read-side, R3 projections and R4 compute assessment are in main and tested. They remain unwired and non-user-facing.

Residual risks include missing trusted producers, policy ownership, durable adapter, consent, tenant isolation, retention, erasure, access control, calibration and operational evidence.

## P1 — R5A replay evaluation

Draft PR #205 adds deterministic snapshots and zero-tolerance gates.

Residual risks:

- privacy/query-write/silent-overwrite counters not derivable from pure artifacts are caller supplied;
- a dishonest or incomplete observer can under-report external effects;
- snapshot equality proves deterministic artifacts, not semantic correctness;
- the replay corpus, scenario coverage and hidden holdouts are not supplied by R5A;
- compute assessment provenance is represented by the final decision hash, not the whole R4 assessment object;
- reports are process objects only and are not durably retained;
- no operational baseline, SLO or alert exists.

Required before runtime evaluation:

1. trusted observation producer;
2. versioned replay corpus and holdouts;
3. durable evidence/retention policy;
4. calibration and false-pass analysis;
5. operator review of hard-gate coverage.

## P1 — R5A Advisory Shadow

Residual risks:

- relevance signals are caller supplied and can be forged or overproduced;
- private audience is asserted by the caller, not authenticated here;
- projection source refs can be stale or cross-tenant if upstream policy fails;
- proposed Russian text has no localization contract;
- no anti-spam, frequency cap, scheduling, cancellation, delivery or consent runtime;
- no user-visible feedback loop or effectiveness metric;
- reminder-shaped candidates are proposals only, but careless future wiring could bypass that boundary;
- Advisory `DEFER` could be confused with compute defer unless documentation remains explicit;
- candidate/receipt objects are not persisted or erased by a durable lifecycle;
- high/critical sensitivity is recorded but not a complete domain policy.

Required before live advisory:

1. trusted signal and audience owner;
2. tenant/subject authorization;
3. explicit opt-in and purpose binding;
4. anti-spam, scheduling, cancellation and localization;
5. durable receipt/erasure policy;
6. shadow metrics and operator approval;
7. separate activation ADR and rollback plan.

## R5B remains unimplemented

Historical #147 is stale and depends on historical R4/R5 APIs. A complete runner must be rebuilt on the accepted current APIs, disabled by default and independently reviewed.

## Other P1

- ARM-03 remains heuristic proposal-only.
- Identity remains a legacy mutable prototype without accepted lifecycle.
- Canon mutation ownership is not proven unified across every family.
- `server.py` remains a composition monolith.
- Shared API key is not per-user/tenant authorization.

## Update rule

Use exact states: proposed, implemented, tested, wired, enabled and observed.
