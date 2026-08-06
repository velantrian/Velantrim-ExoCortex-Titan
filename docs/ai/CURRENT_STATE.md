# 📍 Current System State

**Verified:** 2026-08-06  
**Current `main` / verified production-code head:** `81836b4f715470c50a4c6c7768a2cde7478568c8`  
**Documentation checkpoint scope:** PR #229 State Draft adapter + PR #230 Goal subject binding  
**Reality boundary:** `INTERNAL · UNWIRED · NOT ENABLED · NO RUNTIME AUTHORITY`

Material claims must be verified against exact SHAs, tests, workflows, wiring, configuration and runtime evidence.

```text
PROPOSED ≠ IMPLEMENTED
IMPLEMENTED ≠ TESTED
TESTED ≠ WIRED
WIRED ≠ ENABLED
ENABLED ≠ OBSERVED

Proposal ≠ Evidence
Evidence ≠ Approval
Approval ≠ Activation
Integrity ≠ Authorization
Receipt provenance ≠ Current permission
Authorized batch ≠ Runtime permission
Continuity ≠ Truth
Continuity ≠ Compute authority
Shadow output ≠ User-visible output
```

## Queue status

```text
Source-admission architecture:          1/1 = 100%
Primary neutral contracts:              7/7 = 100%
State Draft adapter:                    1/1 = 100%
Goal subject-binding correction:        1/1 = 100%
OpenLoop subject-binding correction:    0/1 =   0%
Goal source adapter:                    0/1 =   0%
OpenLoop source adapter:                0/1 =   0%
Admission evaluator runtime:            0/1 =   0%
Admission-aware facade:                 0/1 =   0%
Privacy/restriction/erasure integration:0/1 =   0%
Runtime wiring:                         0/1 =   0%
Runtime enabled:                        0/1 =   0%
Live observed evidence:                 0/1 =   0%
```

The documentation checkpoint and the two merged implementation slices do not increase live readiness.

## Accepted source-admission lineage

| Capability | Accepted change | State |
|---|---|---|
| Architecture and owner map | #223 → `fa7a15726ff14c6fe5c8611b58db7229fa4b6c2b` | main, docs-only |
| Principal / authorization / source-binding evidence | #225 → `f5725d54b5230f5fbfd6f0550eb08c80ce579237` | main, tested, internal, unwired |
| Source envelope / observation draft | #226 → `695f22b7ff7cf6f3af4b4a8d326534a601c09178` | main, tested, internal, unwired |
| Admission receipt / authorized batch | #227 → `4adde7997ec0b2a3d1957224c72131d8c4d35ff2` | main, tested, internal, unwired |
| Canonical post-contract docs checkpoint | #228 → `ce0fad49ee5e3431751b8cb5dfdfcc405e98cbaf` | main, docs-only |
| State reconciliation → Draft adapter | #229 → `0f1a10ab4f92dd7f15a69e55cc98339e7eeb36b1` | main, tested, internal, unwired |
| Goal subject-binding schema correction | #230 → `81836b4f715470c50a4c6c7768a2cde7478568c8` | main, tested, internal, unwired |

## Exact-head validation

| PR | Exact tested head | Continuity contracts | Full Titan CI | Docker hardening |
|---:|---|---:|---:|---:|
| #229 | `aecea098ab5e3fba0539a044a77ababe32067b79` | `31093141984` ✅ | `31093142993` ✅ | `31093142155` ✅ |
| #230 | `995b1a846b8f3d35c07f103430a6f6b1db007cca` | `31106174878` ✅ | `31106175347` ✅ | `31106174460` ✅ |

Both final heads passed repository guards, Ruff, blocking mypy, focused Continuity tests, full pytest, the blocking `core ≥74%` coverage ratchet and Docker runtime/secret checks. PR #229 had an earlier unrelated erasure-recovery concurrency failure during a coverage run; the unchanged exact head passed on retry. This remains a known flaky/concurrency risk rather than an unconditional first-attempt pass.

## Seven implemented primary contracts

1. `ContinuityPrincipalContext`
2. `ContinuityAuthorizationContext`
3. `ContinuitySourceBindingReceipt`
4. `ContinuitySourceEnvelope`
5. `ContinuityObservationDraft`
6. `ContinuityObservationAdmissionReceipt`
7. `AuthorizedContinuityObservationBatch`

Helper evidence contracts:

- `ContinuityDraftRejection`;
- `ContinuityDraftObservationLink`;
- `ContinuityAdmissionDisposition`.

These modules remain internal and are not exported through `core.continuity.__init__`.

## State Draft adapter — implemented and tested

PR #229 adds `core/continuity/state_source_adapter.py`.

System result:

```text
Before:
StateReconciliationResult was only conditionally eligible in architecture.
No accepted deterministic source adapter produced Continuity Draft evidence.

After:
One explicit invocation can validate a complete immutable State result,
its canonical identities, complete subject set and source-binding receipt,
then produce a ContinuitySourceEnvelope and conservative ObservationDrafts.
```

Implemented guarantees:

- complete subject set is enumerated before semantic derivation;
- binding subjects must exactly equal all projection subjects;
- no silent partial filtering of unauthorized projections;
- result and projection content-addressed identities are recomputed;
- result, digest, policy version, `as_of` and evidence consistency are validated;
- derivations are limited to bounded `context_degraded`, `active_contradiction` and `context_freshness` Drafts;
- output remains deterministic, proposal-only and `no_runtime_authority=True`;
- no admission decision, authorized batch, producer call, persistence or runtime side effect is created.

## Goal subject binding — implemented and tested

PR #230 changes the Goal projection schema to `continuity.goal_projection.v2`.

System result:

```text
Before:
GoalRecordSnapshot contained user_id, but GoalProjectionResult lost it.
A Goal result could not prove subject ownership from its immutable identity.

After:
user_id is explicit and content-addressed through attestation, projection,
decision and the complete sorted result subject set.
Cross-subject attestations fail closed.
```

Implemented guarantees:

- `GoalAttestation.user_id` is mandatory and enters attestation identity;
- `GoalProjection.user_id` and `GoalProjectionDecision.user_id` are explicit;
- `GoalProjectionResult.subject_ids` is complete, sorted and enters result identity;
- snapshot and attestation subject mismatch is rejected;
- multi-subject results remain explicit rather than silently filtered;
- advisory, shadow-runner and WorkingMemory fixtures were migrated to the required contract.

This corrects the subject-identity prerequisite only. No Goal source adapter exists.

## Source eligibility

| Source | Current subject binding | Current disposition |
|---|---|---|
| `StateReconciliationResult` | every projection has typed `SubjectRef`; complete-set checks implemented | Draft adapter implemented/tested; internal and unwired |
| `GoalProjectionResult` v2 | explicit content-addressed `user_id` and complete `subject_ids` | subject prerequisite complete; future Goal adapter still absent |
| `OpenLoopProjectionResult` v1 | no tenant/user/subject identity | blocked until explicit immutable subject binding exists |

Required State invariant:

```text
subjects(source result) == subjects(source binding receipt)
subjects(source result) ⊆ subjects(authorization)
```

Required Goal invariant for a future adapter:

```text
subjects(goal result) == subjects(source binding receipt)
subjects(goal result) ⊆ subjects(authorization)
```

`goal_ref` and `related_goal_ref` are relations, not subject-ownership evidence.

## Explicit limitations

The contracts and adapters make evidence immutable and tamper-evident. They do **not** prove that referenced evidence is authentic, approved, current or unrevoked.

Not implemented:

- authentication-receipt verification;
- evaluator/rule registry or allowlist;
- current tenant/subject authorization lookup;
- consent or lawful-basis verification;
- current restriction registry;
- current erasure-domain check;
- current `PolicySnapshot` compatibility evaluation;
- source freshness policy evaluation outside bounded adapter rules;
- Goal source adapter;
- OpenLoop subject binding or source adapter;
- admission evaluator runtime;
- admission-aware facade;
- persistence or replay store for admission artifacts;
- public package export;
- `/query`, startup, worker or scheduler wiring;
- feature flag, enablement, SLO, alert or rollback operation;
- answer, reminder, tool, action, Canon, TruthGate, GoalStack or compute-route authority.

A structurally valid receipt is evidence, not current authorization. A future gate must resolve and allowlist evaluator/rule identities and re-check current policy, authorization, restriction and erasure state.

## Required future admission-aware facade

The existing pure producer remains a shadow/test API. Bare v1 observations cannot form a live trust boundary.

A future facade must accept only a complete `AuthorizedContinuityObservationBatch` and must:

1. resolve every principal, authorization, binding, admission and evaluator reference;
2. verify evaluator/rule allowlists;
3. re-check current authorization expiry or withdrawal;
4. re-check current consent or lawful basis;
5. re-check current restriction and erasure state;
6. validate tenant and complete subject scope;
7. validate current policy compatibility;
8. validate batch, receipt, envelope and object identities;
9. only then invoke the existing pure signal producer;
10. bind aggregate output to the batch and receipt IDs;
11. remain disabled and produce zero user-visible effect until a separate activation ADR and operator approval.

No such facade exists.

## Continuity live readiness

```text
Completed: 3/12 = 25%
Remaining: 9/12 = 75%
```

Completed live-readiness categories remain:

- shadow contracts;
- deterministic replay/tests;
- disabled-by-default authority boundary.

State adapter and Goal schema completion are prerequisite engineering slices; they do not themselves add authentication, admission runtime, privacy closure, wiring, enablement or observed operation.

## Existing Continuity shadow stack

| Layer | Accepted SHA | State |
|---|---|---|
| R1 — immutable contracts | `06529700d70854504b88629eeecf737bdc6b81d5` | main, tested, unwired |
| R2 — process-local read-side and threads | `320d5ae9f89780efc553ffbfc3a17c1ebc83b47e` | main, tested, process-local, unwired |
| R3 — projections and WorkingMemory adapters | `a19d16656676ad5c98c92d4776e9709edbfb920c` | main, tested, rebuildable, unwired |
| R4 — compute assessment | `529d8b6b182b1a548d27558173f0aca473bcc400` | main, tested, shadow-only, unwired |
| R5A — replay gates / Advisory Shadow | `58e29bba26299ce7003b62e73fd3b25e028956de` | main, tested, shadow-only, unwired |
| R5B — disabled runner | `27b91a59f9e9291092b220ac1f53bfeae2daea28` | main, tested, default-off, unwired |
| Typed signal producer | `5f1ce06199ebabd6a23f3656ddd91c5c968170fe` | main, tested, shadow-only, unwired |
| Producer hardening | `e37a5d13332628bcdbd0d9441d7a61d5f8a8d523` | main, tested, shadow-only, unwired |
| Source-admission primary contracts | `4adde7997ec0b2a3d1957224c72131d8c4d35ff2` | main, tested, internal, unwired |
| State Draft adapter | `0f1a10ab4f92dd7f15a69e55cc98339e7eeb36b1` | main, tested, internal, unwired |
| Goal subject binding v2 | `81836b4f715470c50a4c6c7768a2cde7478568c8` | main, tested, internal, unwired |

## Global non-authority statement

No accepted checkpoint authorizes:

- direct Canon write or TruthGate bypass;
- `/query` behavior change;
- startup registration, worker or scheduler;
- policy expansion;
- tool/action execution;
- automatic reminders or advice;
- automatic identity or learning admission;
- treating a shared API key as end-user identity;
- trusting evaluator/rule strings without resolution and allowlisting;
- cross-tenant or unauthorized cross-subject aggregation;
- OpenLoop admission without immutable subject binding;
- bare v1 observations as a live trust boundary;
- treating an admission receipt or authorized batch as runtime permission.

## Next safe implementation slice

The next implementation PR may correct **OpenLoop subject identity only**.

It must:

- make subject identity explicit, immutable and content-addressed in the OpenLoop evidence object;
- propagate subject identity through projection, decision and result identity;
- reject ambiguous or cross-subject inputs fail-closed;
- update the schema version rather than inventing a placeholder default;
- update every direct constructor, serializer/canonicalizer and affected fixture;
- remain internal, explicitly invoked and unwired;
- add no OpenLoop source adapter, admission evaluator, producer invocation, persistence, public export, server/startup/worker/scheduler call, feature flag or user-visible effect.

Goal and OpenLoop source adapters must remain separate later PRs. Runtime wiring remains a still-later architecture and activation decision.
