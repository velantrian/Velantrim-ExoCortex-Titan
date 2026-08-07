# 🔐 Continuity Source Admission — Current Hand-off

**Verified:** 2026-08-07  
**Current implementation `main`:** `659c30e0e8023c48fdf68be8583401fc042a1ab8`  
**Status:** `INTERNAL · UNWIRED · NOT ENABLED · NOT OBSERVED · NO RUNTIME AUTHORITY`  
**Documentation impact:** `GITHUB_AND_NOTION`  
**Notion records:** Titan Hub; Continuity Source Admission — Architecture

This is the current continuation map for source-admission work. Historical R1–R5 and earlier source-admission hand-offs remain provenance only; they do not override `CURRENT_STATE.md` or this checkpoint.

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

Then inspect only code/tests relevant to the next bounded slice.

## Accepted lineage

| Capability | PR | Merge SHA | State |
|---|---:|---|---|
| Source-admission architecture | #223 | `fa7a15726ff14c6fe5c8611b58db7229fa4b6c2b` | accepted docs-only architecture |
| Principal / authorization / binding evidence | #225 | `f5725d54b5230f5fbfd6f0550eb08c80ce579237` | implemented/tested/internal/unwired |
| Source envelope / observation draft | #226 | `695f22b7ff7cf6f3af4b4a8d326534a601c09178` | implemented/tested/internal/unwired |
| Admission receipt / authorized batch | #227 | `4adde7997ec0b2a3d1957224c72131d8c4d35ff2` | implemented/tested/internal/unwired |
| State reconciliation → Draft adapter | #229 | `0f1a10ab4f92dd7f15a69e55cc98339e7eeb36b1` | implemented/tested/internal/unwired |
| Goal subject binding v2 | #230 | `81836b4f715470c50a4c6c7768a2cde7478568c8` | implemented/tested/internal/unwired |
| OpenLoop subject binding v2 | #232 | `659c30e0e8023c48fdf68be8583401fc042a1ab8` | implemented/tested/internal/unwired |

## PR #232 validation

```text
Exact tested head:      909789ee99e169f83aa5fab927ed6312e20cf471
Full Titan CI:          31154197511 PASS
Continuity contracts:   31154197538 PASS
Docker hardening:       31154197912 PASS
Unresolved threads:     0
Merge SHA:              659c30e0e8023c48fdf68be8583401fc042a1ab8
```

The earlier cancelled Continuity job on `81e07a8ea59f486da9f5cf147ecc2932044fa024` executed no test steps because a hosted runner did not acquire it. The final exact-head run above is the accepted evidence.

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
→ complete subject-set validation
→ source binding validation
→ SourceEnvelope
→ bounded ObservationDraft proposals
→ STOP
```

The adapter is implemented/tested/internal/unwired. It performs no authentication, admission, persistence, producer invocation or runtime effect.

### Goal

Goal schema `continuity.goal_projection.v2` binds `user_id` through attestation, projection, decision and complete sorted result subject set. Cross-subject attestations fail closed. Goal source adapter remains absent.

### OpenLoop

OpenLoop schema `continuity.open_loop_projection.v2` binds `user_id` through signal, resolution, projection and complete sorted result subject set. Cross-subject resolutions fail closed.

A direct regression test proves:

```text
same OpenLoop semantics + different user_id
→ different signal_id
→ different resolution_id
→ different projection_id
→ different result_id
```

OpenLoop source adapter remains absent.

## Source eligibility matrix

| Source | Subject prerequisite | Adapter |
|---|---|---|
| State | complete typed subject set | ✅ implemented, internal, unwired |
| Goal v2 | explicit complete content-addressed subject set | ❌ absent |
| OpenLoop v2 | explicit complete content-addressed subject set | ❌ absent |

Every future adapter must enforce:

```text
subjects(source result) == subjects(binding receipt)
subjects(source result) ⊆ subjects(current authorization)
```

Do not use `goal_ref`, `related_goal_ref`, `loop_key` or a deployment API key as subject ownership.

## Non-authority boundary

No accepted change authorizes:

- current authentication or authorization inference;
- consent/lawful-basis decisions;
- restriction or erasure override;
- admission decisions;
- persistence or replay lifecycle;
- Canon/ESM/TruthGate writes;
- `/query`, startup, worker or scheduler wiring;
- public export or feature activation;
- answer, reminder, delivery, tool, action or compute-route authority;
- treating receipts or authorized batches as permanent runtime permission.

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

## Remaining blockers

- Goal source adapter;
- OpenLoop source adapter;
- admission evaluator and evaluator/rule allowlist;
- current principal, tenant and subject authorization resolution;
- consent/lawful-basis verification;
- current restriction and erasure checks;
- current policy compatibility;
- durable retention, persistence, replay and cleanup lifecycle;
- admission-aware facade;
- anti-bypass guards;
- runtime wiring;
- feature flag, operator workflow, SLO, alert and rollback;
- activation ADR;
- live observed evidence.

## Honest readiness

```text
Primary neutral contracts        7/7 = 100%
State adapter                    1/1 = 100%
Goal subject binding             1/1 = 100%
OpenLoop subject binding         1/1 = 100%
Goal adapter                     0/1 =   0%
OpenLoop adapter                 0/1 =   0%
Admission evaluator runtime      0/1 =   0%
Admission-aware facade           0/1 =   0%
Privacy/erasure integration      0/1 =   0%
Runtime wiring                   0/1 =   0%
Runtime enabled                  0/1 =   0%
Live observed evidence           0/1 =   0%

Continuity live readiness        3/12 = 25%
```

## Next safe slice

Implement **Goal source adapter only** in a separate PR.

Required end state:

```text
GoalProjectionResult v2
→ recompute/validate immutable identities
→ validate complete subject binding
→ create SourceEnvelope
→ derive bounded Draft proposals
→ STOP
```

It must not:

- make an admission decision;
- create an authorized batch;
- invoke the signal producer;
- persist or export runtime state;
- wire `/query`, startup, workers or schedulers;
- add a feature flag;
- write Canon/TruthGate/GoalStack;
- create answers, reminders, tools or actions.

OpenLoop adapter remains a later separate PR. Evaluator, privacy/erasure integration, facade, durable lifecycle, runtime wiring and activation remain later independent phases.

## Definition of done for the next slice

- exact base/head SHA;
- bounded diff and explicit goal;
- complete subject-set validation;
- canonical identity recomputation;
- conservative bounded Draft mapping;
- fail-closed malformed, stale and mismatched inputs;
- focused adversarial tests;
- Ruff, blocking mypy, Continuity contracts, full pytest, coverage and Docker as applicable;
- unresolved review threads `0`;
- GitHub and Notion synchronized in the same work cycle;
- explicit non-scope;
- exact status separation: `IMPLEMENTED`, `TESTED`, `WIRED`, `ENABLED`, `OBSERVED`.
