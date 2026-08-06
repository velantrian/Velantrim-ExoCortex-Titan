# 🔐 Continuity Source Admission — Current Hand-off

**Verified:** 2026-08-06  
**Current `main`:** `81836b4f715470c50a4c6c7768a2cde7478568c8`  
**Status:** `INTERNAL · UNWIRED · NOT ENABLED · NO RUNTIME AUTHORITY`  
**Documentation impact:** `GITHUB_AND_NOTION`  
**Notion records:** Titan Hub; Continuity Source Admission — Architecture

This hand-off is the current continuation map for the Continuity source-admission workstream. Historical R1–R5 hand-offs remain useful for provenance, but they do not override `CURRENT_STATE.md`, accepted architecture or this later checkpoint.

## 1. Read before continuing

Read in this order:

1. `AGENTS.md`;
2. `docs/ai/README.md`;
3. `docs/ai/DOCUMENTATION_SYNC_PROTOCOL.md`;
4. `docs/ai/CURRENT_STATE.md`;
5. `docs/ai/KNOWN_RISKS.md`;
6. `docs/ai/COMPONENT_MAP.md`;
7. recent entries in `docs/ai/WORK_LOG.md`;
8. `docs/research/CONTINUITY_SOURCE_ADMISSION_ARCHITECTURE.md`;
9. this hand-off;
10. `docs/ai/AUDIT_PLAYBOOK.md` before final review.

Then inspect only the code and tests relevant to the next slice.

## 2. Accepted lineage

| Capability | PR | Merge SHA | Current state |
|---|---:|---|---|
| Source-admission architecture | #223 | `fa7a15726ff14c6fe5c8611b58db7229fa4b6c2b` | accepted docs-only architecture |
| Principal / authorization / source-binding evidence | #225 | `f5725d54b5230f5fbfd6f0550eb08c80ce579237` | implemented, tested, internal, unwired |
| Source envelope / observation draft | #226 | `695f22b7ff7cf6f3af4b4a8d326534a601c09178` | implemented, tested, internal, unwired |
| Admission receipt / authorized batch | #227 | `4adde7997ec0b2a3d1957224c72131d8c4d35ff2` | implemented, tested, internal, unwired |
| Post-contract documentation checkpoint | #228 | `ce0fad49ee5e3431751b8cb5dfdfcc405e98cbaf` | docs-only |
| State reconciliation → Draft adapter | #229 | `0f1a10ab4f92dd7f15a69e55cc98339e7eeb36b1` | implemented, tested, internal, unwired |
| Goal subject-binding schema v2 | #230 | `81836b4f715470c50a4c6c7768a2cde7478568c8` | implemented, tested, internal, unwired |

## 3. Exact validation evidence

### PR #229 — State Draft adapter

```text
Exact tested head:      aecea098ab5e3fba0539a044a77ababe32067b79
Continuity contracts:   31093141984 PASS
Full Titan CI:          31093142993 PASS
Docker hardening:       31093142155 PASS
```

An earlier coverage-instrumented run exposed an unrelated intermittent erasure-recovery concurrency race. The exact unchanged head passed on retry. Preserve the first failure as risk evidence; do not describe the result as an unconditional first-attempt pass.

### PR #230 — Goal subject binding

```text
Exact tested head:      995b1a846b8f3d35c07f103430a6f6b1db007cca
Continuity contracts:   31106174878 PASS
Full Titan CI:          31106175347 PASS
Docker hardening:       31106174460 PASS
Unresolved threads:     0
```

The exact-head review confirmed subject propagation, cross-subject rejection, schema v2 regression coverage and absence of runtime wiring or authority.

## 4. Implemented primary contracts

The primary neutral source-admission family is complete:

1. `ContinuityPrincipalContext`;
2. `ContinuityAuthorizationContext`;
3. `ContinuitySourceBindingReceipt`;
4. `ContinuitySourceEnvelope`;
5. `ContinuityObservationDraft`;
6. `ContinuityObservationAdmissionReceipt`;
7. `AuthorizedContinuityObservationBatch`.

Helper evidence contracts include:

- `ContinuityDraftRejection`;
- `ContinuityDraftObservationLink`;
- `ContinuityAdmissionDisposition`.

These are internal contracts. They are not exported through `core.continuity.__init__` and do not grant runtime permission.

## 5. State Draft adapter result

PR #229 added an explicit adapter from `StateReconciliationResult` to proposal evidence.

```text
StateReconciliationResult
→ recompute result and projection identities
→ enumerate complete source subject set
→ validate exact SourceBindingReceipt subject set
→ validate source digest, policy, as_of and evidence
→ create ContinuitySourceEnvelope
→ derive bounded ObservationDraft proposals
→ STOP
```

Allowed derivations are limited to:

- `context_degraded`;
- `active_contradiction`;
- `context_freshness`.

The adapter rejects the complete source result when subject binding is incomplete or inconsistent. It does not silently filter a multi-subject result.

The adapter does not:

- authenticate a principal;
- decide authorization;
- evaluate consent, restrictions or erasure;
- create an admission receipt or authorized batch;
- invoke the signal producer;
- persist, wire, enable or expose runtime behavior.

## 6. Goal subject-binding result

PR #230 corrected the Goal projection contract by advancing it to `continuity.goal_projection.v2`.

```text
GoalRecordSnapshot.user_id
→ GoalAttestation.user_id
→ GoalProjection.user_id
→ GoalProjectionDecision.user_id
→ GoalProjectionResult.subject_ids
→ content-addressed result identity
```

Guarantees:

- subject identity is mandatory, not inferred;
- attestation subject enters immutable identity;
- snapshot/attestation subject mismatch fails closed;
- projection and decision preserve the subject;
- result contains the complete sorted subject set;
- subject set enters the result digest;
- multi-subject results remain explicit;
- direct test fixtures were migrated instead of adding a fake default.

This closes only the Goal source-identity prerequisite. No Goal source adapter exists.

## 7. Current source eligibility

| Source | Subject evidence | Disposition |
|---|---|---|
| `StateReconciliationResult` | each projection has typed `SubjectRef`; complete-set adapter checks exist | Draft adapter implemented/tested; internal and unwired |
| `GoalProjectionResult` v2 | explicit `user_id` and complete content-addressed `subject_ids` | subject prerequisite complete; adapter absent |
| `OpenLoopProjectionResult` v1 | no tenant/user/subject identity | blocked |

Do not use `goal_ref` or `related_goal_ref` as subject-ownership evidence.

## 8. OpenLoop gap

The next safe implementation slice is **OpenLoop subject identity only**.

Current problem:

```text
OpenLoopSignal
OpenLoopProjection
OpenLoopProjectionResult
```

lack explicit immutable tenant/user/subject identity. A future adapter cannot prove authorization scope from those objects.

Required outcome:

```text
subject identity
→ canonical payload
→ content-addressed signal/projection identity
→ decision identity
→ complete result subject set
→ result digest
```

Required rules:

- subject identity is mandatory;
- schema version is advanced explicitly;
- ambiguous or cross-subject input fails closed;
- complete subject set is preserved in the result;
- all direct constructors, canonicalizers and affected fixtures are updated;
- no placeholder subject is introduced for backward compatibility;
- no source adapter is added in the same PR.

## 9. Minimal code-reading scope for OpenLoop

Start with only:

- `core/continuity/goal_open_loop.py`;
- canonicalization and serialization helpers used by OpenLoop in that module;
- source-admission contracts only where needed to verify vocabulary boundaries;
- `tests/test_continuity_goal_open_loop.py`;
- advisory/shadow fixtures constructing `OpenLoopProjection` directly;
- WorkingMemory adapter tests consuming OpenLoop projections.

Expand the search only after a concrete dependency is discovered.

Do not pre-load:

- all of `core/`;
- all tests;
- all historical RFCs;
- every old Continuity hand-off;
- closed PR history.

## 10. Non-authority boundary

No accepted change authorizes:

- Canon or TruthGate writes;
- `/query` behavior changes;
- startup registration, worker or scheduler;
- persistence or public package export;
- answer, reminder, delivery, tool or action execution;
- compute-route ownership;
- automatic identity or consent inference;
- treating the shared API key as end-user identity;
- using receipt provenance as permanent permission;
- using an authorized batch as runtime permission;
- using bare v1 observations as a live trust boundary.

```text
Proposal
→ Evidence
→ Admission decision
→ Approved boundary
→ Explicit wiring
→ Explicit enablement
→ Observed runtime evidence
```

These remain separate stages.

## 11. Remaining blockers

- OpenLoop subject binding;
- Goal source adapter;
- OpenLoop source adapter;
- admission evaluator runtime and evaluator/rule allowlist;
- current principal, tenant and subject authorization resolution;
- consent or lawful-basis verification;
- current restriction and erasure checks;
- current policy compatibility;
- retention, persistence, replay and cleanup lifecycle;
- admission-aware facade;
- anti-bypass guards;
- runtime wiring;
- feature flag, operator workflow, SLO, alert and rollback;
- separate activation ADR;
- live observed evidence.

## 12. Honest readiness

```text
Primary neutral contracts       7/7 = 100%
State adapter                   1/1 = 100%
Goal subject binding            1/1 = 100%
OpenLoop subject binding        0/1 =   0%
Goal adapter                    0/1 =   0%
OpenLoop adapter                0/1 =   0%
Admission evaluator runtime     0/1 =   0%
Admission-aware facade          0/1 =   0%
Privacy/erasure integration     0/1 =   0%
Runtime wiring                  0/1 =   0%
Runtime enabled                 0/1 =   0%
Live observed evidence          0/1 =   0%

Continuity live readiness       3/12 = 25%
```

State adapter and Goal binding are engineering prerequisites. They do not add authentication, current authorization, privacy closure, wiring, enablement or observation.

## 13. Definition of done for the next slice

A future OpenLoop subject-binding PR is complete only when it includes:

- explicit Goal for the system result;
- exact base and head SHA;
- bounded diff;
- schema and identity invariants;
- focused adversarial tests;
- affected fixture migration;
- Ruff and blocking mypy;
- Continuity contract tests;
- full pytest and blocking coverage ratchet;
- Docker hardening;
- exact-head final review and unresolved threads `0`;
- `CURRENT_STATE`, `COMPONENT_MAP`, `KNOWN_RISKS`, `WORK_LOG` and this hand-off updated as required;
- Notion synchronized in the same work cycle;
- explicit non-scope and remaining blockers;
- status stated separately as `IMPLEMENTED`, `TESTED`, `WIRED`, `ENABLED` and `OBSERVED`.

The next slice must finish at:

```text
IMPLEMENTED · TESTED · INTERNAL · UNWIRED · NOT ENABLED · NOT OBSERVED
NO RUNTIME AUTHORITY
```
