# 🔐 Continuity Source Admission — Current Hand-off

**Verified:** 2026-08-07  
**Current implementation `main`:** `42aa79338c57e9b9a67c3e3c08dd948b60c5541f`  
**Status:** `INTERNAL · UNWIRED · NOT ENABLED · NOT OBSERVED · NO RUNTIME AUTHORITY`  
**Documentation impact:** `GITHUB_AND_NOTION`  
**Notion records:** Titan Hub; Continuity Source Admission — Architecture

This is the current continuation map. Earlier hand-offs and research progress counters are provenance only and do not override `CURRENT_STATE.md`, `KNOWN_RISKS.md` or this checkpoint.

## Mandatory reading order

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
| OpenLoop result → Draft adapter | #240 | `42aa79338c57e9b9a67c3e3c08dd948b60c5541f` | tested/internal/unwired |

## OpenLoop adapter validation

```text
Exact tested head:             9623d60f262d00ab4551f5342f7ef1792723e594
Full Titan CI + coverage:      31168858623 PASS
Continuity contracts:          31168858622 PASS
Docker hardening:              31168858691 PASS
Aggregate merge evidence:      31200451054 PASS
Unresolved review threads:     0
Merge SHA:                     42aa79338c57e9b9a67c3e3c08dd948b60c5541f
Post-merge full CI + coverage: 31200627655 PASS
Post-merge Continuity:         31200627704 PASS
Post-merge Docker:             31200627678 PASS
Post-merge aggregate:          31200627647 PASS
```

Codex was unavailable for substantive review because its usage limit was reached; this is not approval evidence.

## Implemented primary contracts

1. `ContinuityPrincipalContext`;
2. `ContinuityAuthorizationContext`;
3. `ContinuitySourceBindingReceipt`;
4. `ContinuitySourceEnvelope`;
5. `ContinuityObservationDraft`;
6. `ContinuityObservationAdmissionReceipt`;
7. `AuthorizedContinuityObservationBatch`.

These are immutable evidence contracts. The receipt/batch constructors validate structure and provenance links but do not resolve whether caller-supplied evaluator/rule/current decision evidence is trusted.

## Current source status

### State

```text
StateReconciliationResult
→ canonical identity and complete subject validation
→ SourceBindingReceipt + AuthorizationContext evidence
→ SourceEnvelope
→ bounded ObservationDraft proposals
→ STOP
```

Implemented/tested/internal/unwired.

### Goal v2

```text
GoalProjectionResult v2
→ projection/result and decision identity validation
→ exact complete subject and evidence binding
→ SourceEnvelope
→ active + attested + included Goal
→ EVIDENCE_COVERAGE_ITEM Draft
→ STOP
```

Implemented/tested/internal/unwired. Completed, cancelled and excluded goals derive no positive Draft.

### OpenLoop v2

```text
OpenLoopProjectionResult v2
→ projection/result identity recomputation
→ canonical status/reason/time validation
→ exact complete subject binding
→ complete projection/signal/resolution reference evidence
→ SourceEnvelope
→ OPEN or OVERDUE
→ EVIDENCE_COVERAGE_ITEM Draft
→ STOP
```

Implemented/tested/internal/unwired.

Safety boundary:

- `RESOLVED` and `NOT_YET_OPEN` derive no positive Draft;
- summary, kind, due date, related goal and loop key cannot create reminders, schedules, actions, current-state requests, importance, sensitivity, answers, tools, delivery or compute authority;
- signal/resolution payloads are not embedded in the result, so their IDs are required as binding evidence rather than falsely recomputed;
- receipt issuance cannot precede the bound source snapshot;
- result-level `as_of` remains owned by the result contract, not each projection.

## Source eligibility matrix

| Source | Subject prerequisite | Draft adapter | Runtime state |
|---|---|---|---|
| State | complete typed subject set | ✅ | internal/unwired |
| Goal v2 | complete content-addressed subject set | ✅ | internal/unwired |
| OpenLoop v2 | complete content-addressed subject set | ✅ | internal/unwired |

Every adapter enforces:

```text
subjects(source result) == subjects(binding receipt)
subjects(source result) ⊆ subjects(authorization context)
```

Never use `goal_ref`, `related_goal_ref`, `loop_key`, free text or a deployment API key as ownership evidence.

## Non-authority boundary

No accepted change authorizes:

- current authentication or authorization inference;
- consent/lawful-basis decisions;
- restriction or erasure override;
- trusting caller-supplied evaluator/rule identity;
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
→ resolved/allowlisted admission decision
→ immutable receipt and bounded batch
→ current policy/authorization/privacy re-check
→ approved facade
→ explicit wiring
→ explicit enablement
→ observed runtime evidence
```

These remain separate stages.

## Remaining blockers

- deterministic admission evaluator and allowlisted evaluator/rule registry;
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
OpenLoop adapter                 1/1 = 100%
Admission evaluator runtime      0/1 =   0%
Admission-aware facade           0/1 =   0%
Privacy/erasure integration      0/1 =   0%
Runtime wiring                   0/1 =   0%
Runtime enabled                  0/1 =   0%
Live useful-behavior evidence    0/1 =   0%

Continuity live readiness        5/12 = 41.7%
```

Subject-binding rows are completed prerequisites and are not separately counted in the 12-capability readiness denominator.

## Next safe slice

After this canonical documentation checkpoint merges, implement **deterministic admission evaluator and allowlisted rule registry only**.

Required shape:

```text
ContinuitySourceEnvelope
+ complete ContinuityObservationDraft set
+ resolved evaluator definition
+ resolved rule definition
+ explicit current decision evidence
→ fail-closed per-Draft allow/deny partition
→ ContinuityObservationAdmissionReceipt
→ optional AuthorizedContinuityObservationBatch construction
→ STOP
```

Required rules:

- evaluator and rule identifiers must resolve to immutable, content-addressed allowlisted definitions;
- caller-supplied strings alone are untrusted;
- evaluation time is explicit, timezone-aware and within authorization validity;
- current decision evidence must explicitly cover principal, tenant, complete subjects, purpose, policy, restriction and erasure domains;
- missing, stale, withdrawn, mismatched, unknown or non-allowlisted evidence rejects deterministically;
- every Draft is admitted or rejected with a stable reason code and nonempty evidence;
- no silent partial omission;
- batch construction, when used, includes only admitted Drafts and complete receipts;
- no network, DB, environment, wall-clock or mutable-global reads in the pure evaluator.

The PR must not:

- invoke the signal producer;
- persist or replay admission artifacts;
- export a live public facade;
- wire `/query`, startup, workers or schedulers;
- add a feature flag or activation ADR;
- write Canon, ESM, TruthGate or GoalStack;
- create answers, reminders, delivery, tools, actions or compute authority.

## Definition of done for the next slice

- exact base/head SHA;
- bounded implementation + adversarial tests;
- immutable allowlisted evaluator/rule definitions;
- deterministic complete partition with stable reason codes;
- explicit current-decision evidence and staleness checks;
- malformed, missing, cross-tenant, cross-subject and stale inputs fail closed;
- no hidden I/O, persistence or runtime authority;
- Ruff, blocking mypy, Continuity, full pytest, coverage, Docker and aggregate status PASS;
- unresolved review threads `0`;
- GitHub and Notion synchronized;
- explicit `IMPLEMENTED/TESTED/WIRED/ENABLED/OBSERVED` state.
