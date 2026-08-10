# ADR-2026-08-10: Bounded, content-free observation evidence

- Status: Proposed for the bounded implementation tracked by a new Continuity
  12/12 issue
- Date: 2026-08-10
- Repository baseline: `main@9e43f379fc469f471fdc5dced5d280add0d27bf6`
- Scope: bounded observation *mechanism* only
- Target state: mechanism implemented, tested and internally wired; no
  committed activation manifest, no Operator GO, no currently enabled
  deployment, no production observation claim

## Context

Continuity 11/12 added a controlled-enablement boundary: one explicit
deployment-owned decision, bound to exact configuration/owner/tenant/scope
identity, gates the existing internal append/replay surface. That boundary is
deliberately silent about whether an activation, once applied, actually
behaved as declared. `docs/ai/CURRENT_STATE.md` and
`docs/ai/COMPONENT_MAP.md` name the remaining capability explicitly:

> The sole remaining Continuity capability is live monitored/observed
> evidence under separate authority. Continuity 12/12 has not started.

A canary that merely enables and later disables proves nothing on its own:
enablement itself is lazy (lease expiry is only rechecked when a gated
operation runs), and nothing today records that a bounded activation window
actually preserved its own invariants. Without a bounded observation
mechanism, "observed" would either stay permanently unprovable or would have
to be asserted without evidence — both unacceptable.

This ADR adds that mechanism. It deliberately does **not** claim that
Continuity 12/12 is complete: producing real observed evidence requires an
actual operator-authorized bounded activation in a real deployment, which
this repository checkpoint does not supply. See the companion tracking issue
for the explicit `BLOCKED_ON_OPERATOR_GO` status of that separate fact.

## Decision

Add one internal module:

`core/continuity/bounded_observation.py`

It wraps the existing `ContinuityControlledEnablementController`; it does not
replace, re-implement, or duplicate its authority. The existing FastAPI
lifespan composes and opens the observer immediately after the enablement
controller starts, and closes it before the enablement controller shuts down.

### What it reads

`ContinuityBoundedObservationController.observe(...)` reads only:

- the enablement controller's existing public `diagnostic()` snapshot
  (state, applied-decision identifiers, pinned configuration/owner/storage
  identity);
- one new read-only method added to the enablement controller,
  `lease_valid_at(evaluated_at)`, which reports whether the *currently
  applied* decision's lease is valid at a given moment without mutating
  controller state and without invoking a business operation.

It never calls `persist_accepted_admission` or `replay`, never constructs a
second `ContinuityRuntimeCompositionOwner` or `ContinuityArtifactStore`, and
never issues, revokes, or evaluates an activation decision.

### What it records

Each `observe()` call evaluates a fixed, closed checklist of seven structural
invariants (`configuration_binding_stable`, `storage_location_unchanged`,
`single_lifecycle_owner`, `decision_binding_consistent`,
`lease_valid_when_enabled`, `runtime_authority_absent`,
`side_effect_authority_absent`) and appends one immutable,
content-addressed `ContinuityBoundedObservationEvidence` row to a dedicated
table — `continuity_bounded_observation_records` — inside the *same*
tenant-bound SQLite file already selected by runtime composition. No second
database, storage path, service, singleton, or DI framework is introduced.

Every row carries two fixed markers, `no_new_authority_granted` and
`evidence_is_not_permission`, which construction requires to be exactly
`True`. They are not configurable claims: a caller cannot construct evidence
that asserts it granted something.

Three of the seven invariants (`configuration_binding_stable`,
`storage_location_unchanged`, `single_lifecycle_owner`) are also asserted
before evidence is even built — `observe()` raises
`ContinuityObservationConfigurationError` immediately on a substitution
rather than silently recording a failed boolean, matching the fail-closed
posture the rest of this lineage uses for identity binding. They remain in
the recorded checklist for audit completeness. The remaining four invariants
(most importantly `lease_valid_when_enabled`) can legitimately be `False` in
recorded evidence — that is the interesting case this mechanism exists to
catch, e.g. an activation whose lease expired without any gated operation
ever re-checking it.

### Deterministic session result

`summarize_observation_session(evidences)` reduces an ordered set of evidence
rows to one pure, content-free result: whether every invariant passed, and —
specifically — whether the session's evidence shows a transition into
`ENABLED` followed later by a transition back to `DISABLED` under one
unchanged configuration identity (`rollback_verified`). This is the
"deterministic observation result" a bounded canary needs to produce; it is
computed entirely from already-persisted rows and has no further effect.

### State separation preserved

```text
implemented
≠ tested
≠ wired
≠ enablement mechanism implemented
≠ runtime currently enabled
≠ operator authorization present
≠ observation mechanism implemented   <- this ADR
≠ observed                            <- requires a real deployment + Operator GO
≠ runtime authority
≠ production-authoritative
```

This module can be exercised end-to-end in tests with a synthetic operator
decision (exactly as `controlled_enablement.py`'s own tests do). That proves
the mechanism works. It does not and cannot, by itself, make `observed=true`
a project fact — that requires an actual operator-authorized bounded
activation against a real deployment, which is outside this repository
checkpoint's authority to supply or simulate.

## Authority matrix

| Concern | Owner after this ADR | Explicitly not granted |
|---|---|---|
| Runtime composition | existing `ContinuityRuntimeCompositionOwner` | observation authority |
| Controlled enablement | existing `ContinuityControlledEnablementController` | observation authority |
| Lease validity read | new read-only `lease_valid_at()` | state mutation, gating |
| Observation evidence | new dedicated table, same SQLite file | permission token semantics |
| Observation session result | pure reduction over persisted rows | Operator GO, production authority |
| Operator GO project fact | absent; explicit future operational evidence | inferred from this ADR |
| Production observation | Continuity 12/12 real-evidence checkpoint | this ADR |

## Fail-closed policy

Reject or refuse observation for:

- an observer bound to a mismatched configuration/enablement-controller pair
  at construction;
- `observe()` before `open()`;
- `observe()` while the underlying runtime is `NEW` (never started) or
  `STOPPED` (shut down);
- a substituted configuration, storage location, or lifecycle owner detected
  at observation time;
- a non-positive, stale, or conflicting observation sequence;
- malformed, digest-mismatched, or schema-incompatible persisted evidence;
- an incomplete or unknown invariant checklist;
- a `no_new_authority_granted` or `evidence_is_not_permission` value other
  than exactly `True`.

No permissive fallback or automatic authority escalation exists.

## Explicit non-scope

This ADR does not add or authorize:

- Continuity 12/12 completion, a committed live activation manifest, or
  Operator GO as a project fact;
- public rollout, user activation, or any `/query` behavior change;
- producer invocation, event creation, or Canon/ESM/TruthGate/GoalStack
  writes;
- reminders, notifications, tools, actions, delivery, or a
  worker/scheduler/background loop;
- external telemetry, alerting, SLO/SLA, or a new control-plane service;
- a second runtime, store, path, singleton, or DI framework;
- issue #249, dependency upgrades, Phase II, ADAO, or unrelated refactoring;
- a production-readiness or independent-review claim.

## Required evidence before acceptance

1. focused and adversarial tests for configuration binding, lifecycle
   gating, monotonic sequencing/idempotency, concurrency, restart/rollback,
   and absent authority escalation;
2. structural proof of one runtime/storage path, unchanged `/query`, and
   absent forbidden side-effect imports or calls;
3. Ruff, blocking mypy, and focused tests on the exact head;
4. full pytest and the repository's blocking coverage ratchet;
5. Continuity, full Titan CI, Docker, and exact aggregate merge evidence as
   required;
6. submitted reviews, Codex comments, and unresolved threads checked on the
   exact head;
7. protected merge using the verified head SHA and post-merge CI/aggregate
   evidence.

This mechanism being merged and green does **not** by itself justify
recording Continuity as `12/12`. That requires separate, factual evidence
that a real bounded activation was operator-authorized, observed, and rolled
back — see the tracking issue's exit criteria.
