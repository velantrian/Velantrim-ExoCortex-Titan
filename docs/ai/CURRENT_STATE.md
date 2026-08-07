# 📍 Current System State

**Verified:** 2026-08-07  
**Actual GitHub `main`:** `f0c17de05df6c762c69974775e3c95d9e613cf47`  
**Latest Continuity slice:** PR #236 — bounded Goal source adapter  
**Latest reliability fix:** PR #238 — recovery reports only claimed batches  
**Governance implementation:** PR #235 — aggregate merge evidence + CODEOWNERS  
**Reality boundary:** `INTERNAL · UNWIRED · NOT ENABLED · NOT OBSERVED · NO RUNTIME AUTHORITY`

Material claims require exact SHAs, tests, workflows, wiring, configuration and observed runtime evidence.

```text
PROPOSED ≠ IMPLEMENTED
IMPLEMENTED ≠ TESTED
TESTED ≠ WIRED
WIRED ≠ ENABLED
ENABLED ≠ OBSERVED

Proposal ≠ Evidence
Evidence ≠ Admission
Integrity ≠ Authorization
Authorized batch ≠ Runtime permission
Continuity ≠ Truth or action authority
```

## Current queue

```text
Source-admission architecture:           1/1 = 100%
Primary neutral contracts:               7/7 = 100%
State Draft adapter:                     1/1 = 100%
Goal source adapter:                     1/1 = 100%
OpenLoop source adapter:                 0/1 =   0%
Admission evaluator runtime:             0/1 =   0%
Admission-aware facade:                  0/1 =   0%
Privacy/restriction/erasure integration: 0/1 =   0%
Runtime wiring:                          0/1 =   0%
Runtime enabled:                         0/1 =   0%
Live useful-behavior evidence:           0/1 =   0%
```

Continuity live readiness:

```text
Completed: 4/12 = 33.3%
Remaining: 8/12 = 66.7%
```

Goal and OpenLoop subject binding are complete prerequisites. The Goal adapter completes one explicit live-readiness category but still grants no admission or runtime authority.

## Accepted lineage

| Capability | PR / merge | State |
|---|---|---|
| Source-admission architecture | #223 → `fa7a15726ff14c6fe5c8611b58db7229fa4b6c2b` | accepted architecture |
| Principal / authorization / binding evidence | #225 → `f5725d54b5230f5fbfd6f0550eb08c80ce579237` | tested, internal, unwired |
| Source envelope / observation draft | #226 → `695f22b7ff7cf6f3af4b4a8d326534a601c09178` | tested, internal, unwired |
| Admission receipt / authorized batch | #227 → `4adde7997ec0b2a3d1957224c72131d8c4d35ff2` | tested, internal, unwired |
| State result → Draft adapter | #229 → `0f1a10ab4f92dd7f15a69e55cc98339e7eeb36b1` | tested, internal, unwired |
| Goal subject binding v2 | #230 → `81836b4f715470c50a4c6c7768a2cde7478568c8` | tested prerequisite |
| OpenLoop subject binding v2 | #232 → `659c30e0e8023c48fdf68be8583401fc042a1ab8` | tested prerequisite |
| Aggregate merge evidence | #235 → `d2edd3882b109e572ff1c94fed1754f486c9b980` | active and observed; ruleset not enabled |
| Goal result → Draft adapter | #236 → `2f9eadd2c16a77835fb58c0d1e481abfc57d8a2d` | tested, internal, unwired |
| Recovery ownership hotfix | #238 → `f0c17de05df6c762c69974775e3c95d9e613cf47` | exact-head and post-merge tested |

## Goal adapter evidence

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

## Goal source adapter

PR #236 implements:

```text
GoalProjectionResult v2
→ recompute projection/result identities
→ validate included and excluded decisions
→ validate exact complete subject binding
→ validate result/projection/snapshot/attestation/decision evidence
→ create ContinuitySourceEnvelope
→ derive bounded ObservationDraft proposals
→ STOP
```

Only an active, explicitly attested and included Goal projection may derive:

```text
EVIDENCE_COVERAGE_ITEM = True
```

Completed, cancelled and excluded goals derive no positive Draft. Title, description, priority and keywords cannot create importance, sensitivity, reminders, answers, tools, actions or compute authority.

The adapter is not publicly exported and is not called by `/query`, startup, workers, schedulers or the signal producer.

## Recovery ownership hotfix

Post-merge coverage for PR #236 exposed a real reporting race:

```text
two recovery workers select one batch
→ one wins the CAS and completes
→ loser fails the claim after terminal completion
→ old code returns the winner's cached report to the loser
→ both callers appear to have processed the batch
```

The erasure side effect itself remained single-execution. PR #238 makes crash-recovery calls with `wait_if_running=False` return `None` after every lost claim. Live/idempotent callers still receive cached terminal reports or wait for an active owner.

```text
Triggering run:                31164988400
Triggering result:             coverage FAILURE
Observed suite at failure:     1 failed, 3665 passed, 17 skipped,
                               21 deselected, 1 xfailed
Exact hotfix head:             6cc5899afe98f53a1ee0e7fff665948b0c5a3d92
Hotfix full CI + coverage:     31166079813 PASS
Hotfix Docker:                 31166079825 PASS
Hotfix aggregate evidence:     PASS
Hotfix merge:                  f0c17de05df6c762c69974775e3c95d9e613cf47
Post-merge full CI + coverage: 31166699745 PASS
Post-merge Docker:             31166697770 PASS
```

The race test remains enabled under coverage. No exclusion or blind rerun was used.

## Source status

| Source | Subject prerequisite | Draft adapter | Runtime state |
|---|---|---|---|
| `StateReconciliationResult` | complete typed subject set | ✅ implemented/tested | internal, unwired |
| `GoalProjectionResult` v2 | complete content-addressed `subject_ids` | ✅ implemented/tested | internal, unwired |
| `OpenLoopProjectionResult` v2 | complete content-addressed `subject_ids` | ❌ absent | blocked from admission path |

Every adapter must enforce:

```text
subjects(source result) == subjects(binding receipt)
subjects(source result) ⊆ subjects(current authorization)
```

`goal_ref`, `related_goal_ref`, `loop_key` and deployment API keys are not ownership evidence.

## Governance state

PR #235 added the active workflow `Aggregate merge evidence`, exact status context `Titan aggregate merge evidence`, CODEOWNERS, fail-closed workflow aggregation, stale-base checks and documentation synchronization checks.

PR #236 and PR #238 supplied live proof:

```text
Draft → aggregate pending
Ready + every applicable exact-head workflow PASS → aggregate success
```

`main` remains unprotected. Until repository rules require the aggregate context, approval, resolved conversations, up-to-date branches and CODEOWNERS review, governance is implemented but not technically enforced. Issue #234 owns the administrator-only remainder.

## Explicit limitations

Not implemented:

- OpenLoop source adapter;
- admission evaluator and trusted evaluator/rule registry;
- current principal/tenant/subject authorization resolution;
- current consent/lawful-basis, restriction, erasure and policy checks;
- admission-aware facade and anti-bypass guards;
- durable admission retention, persistence, replay and cleanup;
- package export;
- `/query`, startup, worker or scheduler wiring;
- feature flag, SLO, alert, rollback or activation ADR;
- Canon/ESM/TruthGate/GoalStack write authority;
- answer, reminder, delivery, tool, action or compute-route authority;
- live useful-behavior evidence.

A valid receipt proves represented evidence integrity, not current permission.

## Next safe slice

After this documentation checkpoint, implement **OpenLoop source adapter only**:

```text
OpenLoopProjectionResult v2
→ recompute/validate projection and result identities
→ validate complete subject binding and source evidence
→ create SourceEnvelope
→ derive conservative bounded Draft proposals
→ STOP
```

Required final state:

```text
IMPLEMENTED · TESTED · INTERNAL · UNWIRED
NO ADMISSION DECISION
NO AUTHORIZED BATCH
NO PRODUCER INVOCATION
NO PERSISTENCE
NO RUNTIME OR USER-VISIBLE AUTHORITY
```

Admission evaluation, privacy/erasure integration, facade, persistence, runtime wiring and activation remain later independent stages.
