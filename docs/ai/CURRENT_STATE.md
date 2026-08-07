# 📍 Current System State

**Verified:** 2026-08-07  
**Actual GitHub `main`:** `2f9eadd2c16a77835fb58c0d1e481abfc57d8a2d`  
**Latest implementation:** PR #236 — bounded Goal source adapter  
**Latest governance implementation:** PR #235 — aggregate merge evidence + CODEOWNERS  
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
Live observed evidence:                  0/1 =   0%
```

Continuity live readiness:

```text
Completed: 4/12 = 33.3%
Remaining: 8/12 = 66.7%
```

Subject-binding prerequisites are complete for Goal and OpenLoop, but prerequisites are not counted as live categories. The Goal adapter increases readiness because it completes one of the 12 explicit categories; it still grants no admission or runtime authority.

## Accepted lineage

| Capability | PR / merge | State |
|---|---|---|
| Source-admission architecture | #223 → `fa7a15726ff14c6fe5c8611b58db7229fa4b6c2b` | accepted docs-only architecture |
| Principal / authorization / binding evidence | #225 → `f5725d54b5230f5fbfd6f0550eb08c80ce579237` | tested, internal, unwired |
| Source envelope / observation draft | #226 → `695f22b7ff7cf6f3af4b4a8d326534a601c09178` | tested, internal, unwired |
| Admission receipt / authorized batch | #227 → `4adde7997ec0b2a3d1957224c72131d8c4d35ff2` | tested, internal, unwired |
| State result → Draft adapter | #229 → `0f1a10ab4f92dd7f15a69e55cc98339e7eeb36b1` | tested, internal, unwired |
| Goal subject binding v2 | #230 → `81836b4f715470c50a4c6c7768a2cde7478568c8` | tested prerequisite |
| OpenLoop subject binding v2 | #232 → `659c30e0e8023c48fdf68be8583401fc042a1ab8` | tested prerequisite |
| Aggregate merge evidence | #235 → `d2edd3882b109e572ff1c94fed1754f486c9b980` | implemented and live-observed for PR evidence; not required by ruleset yet |
| Goal result → Draft adapter | #236 → `2f9eadd2c16a77835fb58c0d1e481abfc57d8a2d` | tested, internal, unwired |

## PR #236 evidence

```text
Exact tested head:             be5b50315c1995d5eb946f3eae7ead58be2f3d8e
Full Titan CI + coverage:      31164336300 PASS
Continuity contracts:          31164336323 PASS
Docker hardening:              31164336269 PASS
Aggregate merge evidence:      31164890308 PASS
Unresolved review threads:     0
Merge SHA:                     2f9eadd2c16a77835fb58c0d1e481abfc57d8a2d
Post-merge Continuity:         31164986649 PASS
Post-merge full CI / Docker:   running at this checkpoint
```

First failures are retained as evidence rather than hidden:

- `31163837999`: unused test import, caught by Ruff;
- `31163955972`: optional-variable shadowing, caught by blocking mypy;
- both were fixed before final exact-head validation;
- the temporary diagnostic workflow was removed before merge.

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

Only an active, explicitly attested, included Goal projection may derive:

```text
EVIDENCE_COVERAGE_ITEM = True
```

Completed, cancelled and excluded goals derive no positive Draft. Goal title, description, priority and keywords cannot create important-claim, sensitivity, current-state, reminder, answer, tool, action or compute authority.

The adapter is not exported publicly and is not called by `/query`, startup, workers, schedulers or the signal producer.

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

PR #235 added:

- active workflow `Aggregate merge evidence`;
- exact status context `Titan aggregate merge evidence`;
- always-required primary CI plus path-aware Continuity, Docker and ARM-03 requirements;
- fail-closed missing, cancelled, timed-out, skipped, neutral and stale evidence;
- documentation-impact and Notion synchronization validation;
- CODEOWNERS for authority-sensitive surfaces.

PR #236 supplied the first live proof:

```text
Draft → aggregate pending
Ready + exact-head CI/Continuity/Docker PASS → aggregate success
```

However, `main` remains unprotected. Until repository rules require this context, approvals, resolved conversations and up-to-date branches, governance is implemented but not technically enforced. Issue #234 owns the administrator-only remainder.

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

Implement **OpenLoop source adapter only** in a separate PR:

```text
OpenLoopProjectionResult v2
→ recompute/validate immutable identities
→ validate complete subject binding and evidence
→ create SourceEnvelope
→ derive bounded Draft proposals
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
