# 📍 Current System State

**Verified:** 2026-08-05  
**Current `main`:** `529d8b6b182b1a548d27558173f0aca473bcc400`  
**Continuity R5A review surface:** draft PR #205

Verify claims against exact SHAs, tests, workflows, wiring and runtime evidence. `MAIN`, `TESTED`, `WIRED`, `ENABLED`, `OBSERVED`, `OPEN PR`, `RESEARCH` and `LEGACY/UNWIRED` are separate states.

## Canon and projection delivery

Projection outbox, version-monotonic FTS apply, checkpoints and bounded dispatch are implemented and tested. The dispatcher remains unwired and lacks accepted lifecycle, cadence, backlog SLO and operational reconciliation.

## Selective memory ARM-03

Merged as `bea535d8fd5f7d59d3f1cee02d060bd026ac05cb`.

**Status:** `MAIN + TESTED + DEFAULT OFF / NOT WIRED / NO ADMISSION`.

## Continuity R1

Merged as `06529700d70854504b88629eeecf737bdc6b81d5`.

**Status:** `MAIN + TESTED / IMMUTABLE CONTRACTS / NOT WIRED`.

## Continuity R2

Merged as `320d5ae9f89780efc553ffbfc3a17c1ebc83b47e`.

**Status:** `MAIN + TESTED / PROCESS-LOCAL READ-SIDE / NOT WIRED`.

## Continuity R3

Merged as `a19d16656676ad5c98c92d4776e9709edbfb920c`.

**Status:** `MAIN + TESTED / REBUILDABLE PROJECTIONS / NOT WIRED`.

It provides continuity context, current-state reconciliation, attested goals, typed open loops and policy-neutral adapters into the existing WorkingMemoryGate/ContextPack path. No producer admission, durable storage, Canon, compute, advisory, answer or action authority.

## Continuity R4

Merged as `529d8b6b182b1a548d27558173f0aca473bcc400`.

**Status:** `MAIN + TESTED / SHADOW COMPUTE ASSESSMENT / NOT WIRED`.

R4 preserves the legacy five-path compute API and exposes a separate explicit assessment that may preserve, raise to VERIFY, or cap degraded DEEP to NORMAL. No `DEFER_PATH` or runtime caller exists.

## Continuity R5A

Draft PR #205 adds deterministic replay evidence and a low-risk Advisory Shadow v2.

**Status:** `OPEN PR / FOCUSED TESTED / SHADOW ONLY / NOT WIRED`.

Replay zero-tolerance gates cover privacy leakage, inference-as-fact, missing provenance, budget overflow, query-time Canon writes, replay divergence and silent overwrite.

Advisory candidates require passed replay, private audience, explicit typed relevance signal, exact actionable projection, explicit permission, source-linked basis refs and `shadow_only=True`. Candidate text is inspectable shadow data only and cannot be delivered.

`AdvisoryAction.DEFER` is a shadow disposition, not a compute path.

## Remaining Continuity recovery

```text
R5A replay gates + Advisory Shadow
→ R5B complete disabled orchestration runner
```

Before any live use:

- trusted producers and one policy owner;
- consent, retention, erasure, tenant isolation and access control;
- replay corpus and calibration evidence;
- runtime feature flag, monitoring and rollback;
- anti-spam, localization, scheduling and cancellation;
- explicit operator approval and a separate activation ADR.

## Runtime and deployment

- API and egress policy are fail-closed under documented production settings;
- Docker is non-root and checked;
- `server.py` remains a broad composition module;
- production compose profiles remain inconsistent;
- authentication remains shared API-key rather than per-user/tenant authorization.

## Identity

`core/identity_layer.py` remains `LEGACY/UNWIRED`; do not activate it.
