# 📍 Current System State

**Verified:** 2026-08-05  
**Current `main`:** `320d5ae9f89780efc553ffbfc3a17c1ebc83b47e`  
**Continuity R3 review surface:** draft PR #203

Verify material claims against exact SHAs, tests, workflows, wiring, configuration and runtime evidence. `MAIN`, `TESTED`, `WIRED`, `ENABLED`, `OBSERVED`, `OPEN PR`, `RESEARCH` and `LEGACY/UNWIRED` are separate states.

## Canon and projection delivery

PromotionGateway and shared promotion primitives are in `main`, but every canonical mutation family is not yet proven to use one typed owner. Projection outbox, version-monotonic FTS apply, checkpoints and bounded dispatch are implemented and tested. The dispatcher still lacks an accepted runtime lifecycle, cadence, backlog SLO and reconciliation loop.

## Selective memory — ARM-03

Merged as `bea535d8fd5f7d59d3f1cee02d060bd026ac05cb`.

**Status:** `MAIN + TESTED + DEFAULT OFF / NOT WIRED / NO ADMISSION`.

It remains proposal-only with no persistence, Canon, gate, answer or action authority.

## Continuity — R1

Merged as `06529700d70854504b88629eeecf737bdc6b81d5`.

**Status:** `MAIN + TESTED / CONTRACTS ONLY / NOT WIRED`.

R1 provides immutable deterministic events, assertions and relations, canonical serialization, golden vectors and authority regression tests.

## Continuity — R2

Merged as `320d5ae9f89780efc553ffbfc3a17c1ebc83b47e`.

**Status:** `MAIN + TESTED / SHADOW READ-SIDE / NOT WIRED`.

R2 provides a disposable process-local neutral ledger, a read-only conversation bridge and conservative deterministic thread projection. It preserves persisted notebook timestamps and related-chat references. It is not a durable event store, not enabled and not user-facing.

## Continuity — R3

Draft PR #203 recovers the historical #138–#143 projection layer on current `main`.

**Status:** `OPEN PR / PRE-MERGE / NOT WIRED / NO USER-FACING AUTHORITY`.

R3 adds:

- deterministic continuity context projection and receipts;
- exact-source adapters into `KnowledgeCapsule`;
- current-state reconciliation where model inference cannot silently replace user statements;
- contested conflict preservation;
- read-only GoalStack snapshots;
- explicit typed goal attestations;
- typed open-loop signals and resolutions;
- policy-neutral state/goal/open-loop candidates for the existing `WorkingMemoryGate` and `ContextPack`.

R3 adds no durable storage, raw-text producer, Canon/ESM/TruthGate mutation, compute routing, advisory, answer, tool, action or runtime wiring.

## Remaining Continuity recovery

```text
R3 projections + WorkingMemory adapters
→ R4 continuity-aware ComputeController signals with differential legacy proof
→ R5 replay evaluation + Advisory shadow + disabled complete runner
```

Still required before any live use:

- trusted event/assertion/attestation/open-loop producers;
- explicit policy owner for attention, recall, eligibility, privacy and conflict inputs;
- consent, retention, erasure and access-control design;
- exhaustive `DEFER_PATH` consumer coverage in R4;
- replay/evaluation and operator approval before any advisory or user-facing path.

## Runtime and deployment

- API and egress policy are fail-closed under documented production settings;
- Docker is non-root and checked;
- `server.py` remains a broad composition module;
- production compose profiles remain inconsistent;
- authentication remains shared API-key rather than per-user/tenant authorization.

## Identity

`core/identity_layer.py` remains `LEGACY/UNWIRED`; do not activate it.
