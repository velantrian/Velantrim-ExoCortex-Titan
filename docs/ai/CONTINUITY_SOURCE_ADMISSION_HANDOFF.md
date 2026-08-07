# 🔐 Continuity Source Admission — Current Hand-off

**Verified:** 2026-08-07  
**Current implementation `main`:** `f0c17de05df6c762c69974775e3c95d9e613cf47`  
**Status:** `INTERNAL · UNWIRED · NOT ENABLED · NOT OBSERVED · NO RUNTIME AUTHORITY`  
**Documentation impact:** `GITHUB_AND_NOTION`  
**Notion records:** Titan Hub; Continuity Source Admission — Architecture

This is the continuation map for source-admission work. Earlier hand-offs are provenance only and do not override `CURRENT_STATE.md` or this checkpoint.

## Read before continuing

1. `AGENTS.md`;
2. `docs/ai/README.md`;
3. `docs/ai/DOCUMENTATION_SYNC_PROTOCOL.md`;
4. `docs/ai/CURRENT_STATE.md`;
5. `docs/ai/KNOWN_RISKS.md`;
6. `docs/ai/COMPONENT_MAP.md`;
7. recent `docs/ai/WORK_LOG.md` entries;
8. `docs/research/CONTINUITY_SOURCE_ADMISSION_ARCHITECTURE.md`;
9. this hand-off;
10. `docs/ai/AUDIT_PLAYBOOK.md` before final review.

Inspect only code/tests relevant to the next bounded slice.

## Accepted lineage

| Capability | PR | Merge SHA | State |
|---|---:|---|---|
| Source-admission architecture | #223 | `fa7a15726ff14c6fe5c8611b58db7229fa4b6c2b` | accepted architecture |
| Principal / authorization / binding evidence | #225 | `f5725d54b5230f5fbfd6f0550eb08c80ce579237` | tested/internal/unwired |
| Source envelope / observation draft | #226 | `695f22b7ff7cf6f3af4b4a8d326534a601c09178` | tested/internal/unwired |
| Admission receipt / authorized batch | #227 | `4adde7997ec0b2a3d1957224c72131d8c4d35ff2` | tested/internal/unwired |
| State result → Draft adapter | #229 | `0f1a10ab4f92dd7f15a69e55cc98339e7eeb36b1` | tested/internal/unwired |
| Goal subject binding v2 | #230 | `81836b4f715470c50a4c6c7768a2cde7478568c8` | tested prerequisite |
| OpenLoop subject binding v2 | #232 | `659c30e0e8023c48fdf68be8583401fc042a1ab8` | tested prerequisite |
| Aggregate merge evidence | #235 | `d2edd3882b109e572ff1c94fed1754f486c9b980` | active/observed; ruleset not enabled |
| Goal result → Draft adapter | #236 | `2f9eadd2c16a77835fb58c0d1e481abfc57d8a2d` | tested/internal/unwired |
| Recovery ownership hotfix | #238 | `f0c17de05df6c762c69974775e3c95d9e613cf47` | exact-head and post-merge tested |

## Goal adapter validation

```text
Exact tested head:             be5b50315c1995d5eb946f3eae7ead58be2f3d8e
Full Titan CI + coverage:      31164336300 PASS
Continuity contracts:          31164336323 PASS
Docker hardening:              31164336269 PASS
Aggregate merge evidence:      31164890308 PASS
Unresolved review threads:     0
Merge SHA:                     2f9eadd2c16a77835fb58c0d1e481abfc57d8a2d
Post-merge Continuity:         31164986649 PASS
Post-merge Docker:             31164989870 PASS
Post-merge ordinary pytest:    PASS in 31164988400
Post-merge coverage:           FAILURE in 31164988400 → fixed by PR #238
```

## Recovery hotfix validation

```text
Triggering coverage run:       31164988400 FAILURE
Triggering assertion:          recovery workers both reported the batch
Exact hotfix head:             6cc5899afe98f53a1ee0e7fff665948b0c5a3d92
Full Titan CI + coverage:      31166079813 PASS
Docker hardening:              31166079825 PASS
Aggregate merge evidence:      PASS
Unresolved review threads:     0
Merge SHA:                     f0c17de05df6c762c69974775e3c95d9e613cf47
Post-merge full CI + coverage: 31166699745 PASS
Post-merge Docker:             31166697770 PASS
```

The hotfix does not alter erasure selection, CAS fencing, lease ownership or deletion. It corrects result ownership:

```text
recovery worker loses claim → return None
live/idempotent caller sees terminal batch → return cached report
live caller sees active owner → wait for completion
```

The existing real two-worker test remains enabled under coverage, and a deterministic lost-claim regression was added. No exclusion or blind rerun was used.

## Implemented primary contracts

1. `ContinuityPrincipalContext`;
2. `ContinuityAuthorizationContext`;
3. `ContinuitySourceBindingReceipt`;
4. `ContinuitySourceEnvelope`;
5. `ContinuityObservationDraft`;
6. `ContinuityObservationAdmissionReceipt`;
7. `AuthorizedContinuityObservationBatch`.

These are evidence contracts, not runtime permission.

## Current source status

### State

```text
StateReconciliationResult
→ canonical identity checks
→ complete subject-set and binding validation
→ SourceEnvelope
→ bounded ObservationDraft proposals
→ STOP
```

Implemented/tested/internal/unwired. No authentication, admission, persistence, producer invocation or runtime effect.

### Goal

```text
GoalProjectionResult v2
→ projection/result identity recomputation
→ complete included/excluded decision validation
→ exact result/binding subject equality
→ complete result/projection/snapshot/attestation/decision evidence
→ SourceEnvelope
→ active attested Goal → EVIDENCE_COVERAGE_ITEM Draft
→ STOP
```

Implemented/tested/internal/unwired.

Safety boundary:

- completed, cancelled and excluded Goals emit no positive Draft;
- title, description, priority and keywords cannot create importance, sensitivity, reminders, answers, tools or actions;
- adapter creates no admission receipt or authorized batch;
- adapter invokes no producer and persists nothing.

### OpenLoop

Schema `continuity.open_loop_projection.v2` has complete content-addressed subject identity and cross-subject resolution rejection. Source adapter remains absent.

The current result contains projection IDs plus signal/resolution references, but not the full original signal/resolution payloads. The next adapter can recompute projection/result identities and require all signal/resolution IDs as binding evidence; it must not claim to recompute unavailable source payload identities unless the contract is separately expanded.

## Source eligibility matrix

| Source | Subject prerequisite | Draft adapter |
|---|---|---|
| State | complete typed subject set | ✅ internal/unwired |
| Goal v2 | complete content-addressed subject set | ✅ internal/unwired |
| OpenLoop v2 | complete content-addressed subject set | ❌ absent |

Every adapter must enforce:

```text
subjects(source result) == subjects(binding receipt)
subjects(source result) ⊆ subjects(current authorization)
```

Never use `goal_ref`, `related_goal_ref`, `loop_key` or a deployment API key as ownership evidence.

## Non-authority boundary

No accepted change authorizes:

- current authentication or authorization inference;
- consent/lawful-basis decisions;
- restriction or erasure override;
- admission decisions or authorized batches;
- producer invocation;
- persistence or replay lifecycle;
- Canon/ESM/TruthGate/GoalStack writes;
- `/query`, startup, worker or scheduler wiring;
- feature activation;
- answers, reminders, delivery, tools, actions or compute routes;
- treating receipts, Drafts or batches as permanent runtime permission.

```text
Projection
→ Draft proposal
→ Admission evidence
→ Current policy/authorization/privacy decision
→ Approved facade
→ Explicit wiring
→ Explicit enablement
→ Observed runtime evidence
```

These remain separate stages.

## Remaining blockers

- OpenLoop source adapter;
- admission evaluator and allowlisted evaluator/rule registry;
- current principal/tenant/subject authorization resolution;
- current consent/lawful-basis verification;
- current restriction, erasure and policy checks;
- durable admission retention, persistence, replay and cleanup;
- admission-aware facade and anti-bypass guards;
- runtime wiring;
- feature flag, operator workflow, SLO, alert and rollback;
- activation ADR;
- live useful-behavior evidence;
- administrator activation of branch ruleset / required aggregate status.

## Honest readiness

```text
Primary neutral contracts        7/7 = 100%
State adapter                    1/1 = 100%
Goal adapter                     1/1 = 100%
OpenLoop adapter                 0/1 =   0%
Admission evaluator runtime      0/1 =   0%
Admission-aware facade           0/1 =   0%
Privacy/erasure integration      0/1 =   0%
Runtime wiring                   0/1 =   0%
Runtime enabled                  0/1 =   0%
Live useful-behavior evidence    0/1 =   0%

Continuity live readiness        4/12 = 33.3%
```

## Next safe slice

After canonical documentation merge, implement **OpenLoop source adapter only**.

Required boundary:

```text
OpenLoopProjectionResult v2
→ recompute projection/result identities
→ validate canonical status/reason relationships
→ validate complete subject binding and signal/resolution evidence
→ create SourceEnvelope
→ derive conservative bounded Draft proposals
→ STOP
```

The safest initial mapping is evidence-only. `OPEN`, `OVERDUE`, `RESOLVED`, due dates, summaries and kinds must not automatically become reminders, actions, current-state requests, sensitivity or delivery authority.

The PR must not:

- make admission decisions or create authorized batches;
- invoke the signal producer;
- persist or export runtime state;
- wire `/query`, startup, workers or schedulers;
- add a feature flag;
- write Canon/TruthGate/GoalStack;
- create answers, reminders, tools or actions.

## Definition of done for the next slice

- exact base/head SHA;
- bounded implementation + adversarial tests;
- canonical projection/result identity recomputation;
- complete subject/evidence validation;
- conservative mapping with no hidden authority;
- malformed, stale and mismatched inputs fail closed;
- Ruff, blocking mypy, Continuity, full pytest, coverage, Docker and aggregate status PASS;
- unresolved review threads `0`;
- GitHub and Notion synchronized;
- explicit `IMPLEMENTED/TESTED/WIRED/ENABLED/OBSERVED` state.
