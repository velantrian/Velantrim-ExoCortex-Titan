# 📍 Current System State

**Verified:** 2026-08-05  
**Current `main`:** `a19d16656676ad5c98c92d4776e9709edbfb920c`  
**Continuity R4 review surface:** draft PR #204

Verify material claims against exact SHAs, tests, workflows, wiring, configuration and runtime evidence. `MAIN`, `TESTED`, `WIRED`, `ENABLED`, `OBSERVED`, `OPEN PR`, `RESEARCH` and `LEGACY/UNWIRED` are separate states.

## Canon and projection delivery

PromotionGateway and shared promotion primitives are in `main`, but every canonical mutation family is not yet proven to use one typed owner. Projection outbox, version-monotonic FTS apply, checkpoints and bounded dispatch are implemented and tested. The dispatcher still lacks an accepted runtime lifecycle, cadence, backlog SLO and reconciliation loop.

## Selective memory — ARM-03

Merged as `bea535d8fd5f7d59d3f1cee02d060bd026ac05cb`.

**Status:** `MAIN + TESTED + DEFAULT OFF / NOT WIRED / NO ADMISSION`.

## Continuity R1 — immutable foundation

Merged as `06529700d70854504b88629eeecf737bdc6b81d5`.

**Status:** `MAIN + TESTED / CONTRACTS ONLY / NOT WIRED`.

## Continuity R2 — shadow read-side

Merged as `320d5ae9f89780efc553ffbfc3a17c1ebc83b47e`.

**Status:** `MAIN + TESTED / PROCESS-LOCAL READ-SIDE / NOT WIRED`.

R2 provides the neutral in-memory ledger, read-only conversation bridge and conservative deterministic thread projection.

## Continuity R3 — projections and WorkingMemory adapters

Merged as `a19d16656676ad5c98c92d4776e9709edbfb920c`.

**Status:** `MAIN + TESTED / REBUILDABLE PROJECTIONS / NOT WIRED`.

R3 provides:

- deterministic continuity context and receipts;
- exact-source adapters into `KnowledgeCapsule`;
- current-state reconciliation with user-over-inference protection;
- contested conflict visibility;
- read-only GoalStack snapshots;
- typed goal attestations and open-loop signals/resolutions;
- policy-neutral candidates for the existing `WorkingMemoryGate` and final `ContextPack`.

R3 adds no producer admission, durable storage, Canon/ESM/TruthGate mutation, compute/advisory/answer/action authority or runtime wiring. Its Synaptic ownership ADR remains `PROPOSED`; merge does not authorize activation.

## Continuity R4 — compatible compute assessment

Draft PR #204 adds a separate shadow assessment around the unchanged legacy compute decision.

**Status:** `OPEN PR / FOCUSED TESTED / SHADOW ONLY / NOT WIRED`.

R4 preserves:

- the five existing `ComputePath` values;
- the seven-field `ComputeDecision` constructor and old serialization;
- the exact `decide_compute_path()` signature and legacy decision matrix;
- exhaustive `RapidOrientation` path mapping.

The new explicit `assess_compute_with_continuity()` API can raise important contradiction, missing/stale required state or sensitive low-evidence input to VERIFY, or cap a degraded DEEP route to NORMAL. It adds no `DEFER_PATH`, runtime caller or user-visible behavior.

## Remaining Continuity recovery

```text
R4 compatible compute assessment
→ R5 replay evaluation + Advisory shadow + disabled complete runner
```

Still required before live use:

- trusted event/assertion/attestation/open-loop/compute-signal producers;
- one policy owner for attention, recall, eligibility, privacy and conflict inputs;
- consent, retention, erasure and access-control design;
- operational evaluation and operator approval;
- separate ADR before any new compute route such as DEFER.

## Runtime and deployment

- API and egress policy are fail-closed under documented production settings;
- Docker is non-root and checked;
- `server.py` remains a broad composition module;
- production compose profiles remain inconsistent;
- authentication remains shared API-key rather than per-user/tenant authorization.

## Identity

`core/identity_layer.py` remains `LEGACY/UNWIRED`; do not activate it.
