# ADR-2026-08-10: Continuity 12/12 — bounded observation canary

- Status: Accepted
- Date: 2026-08-10
- Repository baseline: `main@39ba28dbf6bce4da1e18d6726ae4f4f79dc5f24e`
- Scope: one operator-authorized bounded canary execution, plus the
  machine-readable schema/validator changes required to record it honestly
- Tracking: #275

## Context

`core/continuity/controlled_enablement.py` (PR #273) and
`core/continuity/bounded_observation.py` (PR #276) had both been implemented,
tested and wired, but exercised only against synthetic operator decisions
inside pytest. The remaining Continuity capability — real observed evidence
— explicitly could not be produced by an AI agent on its own initiative; it
required a human operator to supply the missing authorization.

The project's own repository owner supplied that authorization directly, in
chat, scoped to this exact repository, this exact `main` SHA, tracking issue
#275, and one minimal bounded lifecycle
(`VALIDATE → ENABLE → OBSERVE → DISABLE → verify rejection → SHUTDOWN →
RESTART → verify no silent re-enable`), with an explicit list of what is not
authorized (production rollout, public enablement, `/query` change, any
Canon/ESM/TruthGate/GoalStack write, any external action, a second runtime
or storage path, or treating the grant as standing authority). This ADR
records what was executed and what the resulting evidence does and does not
establish.

## Decision

### Canary execution

A standalone script (not a pytest fixture) called the exact production
composition functions used by `api/server_middleware.py`'s FastAPI lifespan
— `compose_controlled_continuity_runtime_from_environment`,
`ContinuityBoundedObservationController`/`compose_bounded_observation`, and
`summarize_observation_session` — with an explicit `environ` mapping passed
directly to those functions (never `os.environ`, so the host process
environment was never mutated), a dedicated canary storage root, and a
dedicated canary tenant reference (`tenant:continuity-canary-2026-08-10`,
never a real production tenant).

Sequence executed, each step producing real, persisted evidence in a real
SQLite file (no test-only shortcuts, real wall-clock timestamps):

1. **VALIDATE** — compose the runtime configuration and enablement
   controller with no activation manifest; `startup()`; confirm `DISABLED`.
2. **bounded OBSERVE** (baseline) — record disabled-state evidence.
3. **controlled ENABLE** — apply one real, bounded, human-operator-attributed
   `ContinuityActivationDecision` (10-minute lease); confirm `ENABLED`.
4. **bounded OBSERVE** (enabled) — record evidence: lease valid, all seven
   invariants pass.
5. **explicit DISABLE** — apply a higher-sequence disable decision; confirm
   `DISABLED`.
6. **bounded OBSERVE** (post-disable) + `summarize_observation_session` over
   all three observations — `rollback_verified=true`.
7. **verify post-disable rejection** — a real call to
   `persist_accepted_admission` raises `ContinuityActivationStateError`
   before any graph is inspected, proving the gate rejects while disabled.
8. **clean SHUTDOWN** — controller state `STOPPED`.
9. **RESTART** — fresh controller/observer objects against the same storage,
   no activation manifest supplied; `startup()` returns `DISABLED` despite
   the persisted `ENABLED` row from step 3 — no silent re-enable.
10. **final fail-closed** — second shutdown; runtime left `STOPPED`/disabled.

Full structured evidence (decision IDs, observation IDs, invariant results,
session summary) was written to a local evidence file and is summarized by
identifier in `docs/ai/WORK_LOG.md` and the Notion synchronization; the raw
SQLite file is canary-local scratch state, not committed to this repository.

### What this proves and what it does not

**Proved:** a real, human-operator-authorized bounded activation of the
existing mechanism behaves exactly as designed — enable, observe, disable,
rejected access, clean shutdown, and a restart that does not silently
resurrect the prior activation. `rollback_verified=true` is a real,
reproducible fact about this one canary, not a test assertion.

**Not proved and not claimed:** production readiness, production authority,
any standing Operator GO, any change to `/query` or user-visible behavior,
any Canon/ESM/TruthGate/GoalStack write, or any authorization for future
activation. The operator's authorization was explicitly single-use and is
exhausted; a new activation requires a new, separately scoped Operator GO.

### Validator correction: `observed` is historical, `enabled` is current

`scripts/check_project_state.py`'s shared `common()` validator previously
rejected `observed=true` whenever `enabled=false`:

```python
if observed and not enabled:
    raise ProjectStateError("Continuity cannot be observed while enabled=false")
```

This was never exercised before this canary (every prior schema forced
`observed=false` via `continuity_flags()`'s literal defaults), but it is
wrong for the fact this canary actually produced: real observation evidence
now exists **and** the runtime is correctly back in its fail-closed,
disabled state. `observed` records durable historical evidence (like
`implemented`/`tested`/`wired`); `enabled` records current runtime state —
exactly the distinction `docs/ai/AGENTS.md` §3 already requires. Conflating
them would make it structurally impossible to ever record a real bounded
canary's intended outcome.

The check is corrected to the invariant that was actually intended —
observation requires the mechanism to have been wired, not to be currently
enabled:

```python
if observed and not wired:
    raise ProjectStateError("Continuity cannot be observed while wired=false")
```

`continuity_flags()` is refactored from a purely-additive tuple to a
dict-with-overrides so a schema can legitimately override a named default
(schema v7 sets `observed=True`) without duplicate, order-sensitive checks.

### Schema v7

`docs/state/project_state.json` advances to schema v7: `completed_capabilities
= 12`, `total_capabilities = 12`, `readiness_percent = 100.0`,
`observation_mechanism_implemented = true`, `observed = true`, while
`enabled`, `operator_authorization_present`, `operator_go`,
`runtime_authority`, `user_visible_behavior_changed` and
`side_effects_enabled` all remain `false` — the current facts, unchanged by
the now-concluded canary. A new `continuity_bounded_observation_canary`
record carries the canary's own exact identity and proof flags
(`operator_authorized_canary`, `rollback_verified`,
`no_silent_reenable_verified`, `post_disable_rejection_verified`, all
`true`), pinned to `main@39ba28dbf6bce4da1e18d6726ae4f4f79dc5f24e`. Schemas
v1-v6 are preserved unchanged and their historical fixtures/tests are
unaffected by the `common()` correction (they never exercised the removed
branch).

## Authority matrix

| Concern | Owner after this ADR | Explicitly not granted |
|---|---|---|
| Activation decision issuance | existing controlled-enablement controller | standing/future authorization |
| Observation evidence | existing bounded-observation controller | permission, current runtime authority |
| Canary authorization | one human operator, one bounded scope, exhausted | repeatable/standing Operator GO |
| `observed` project fact | durable historical record of this canary | current runtime state |
| `enabled` / `operator_go` project facts | current runtime state | inferred from historical `observed` |
| Production authority | absent | this ADR |

## Explicit non-scope

No production rollout, no public enablement, no permanent runtime
enablement, no `/query` or user-visible-behavior change, no
Canon/ESM/TruthGate/GoalStack write, no reminder/notification/action/tool
call, no autonomous loop or scheduler activation, no second runtime or
storage path, no new control plane, no expanded canary scope, no standing
Operator GO, and no claim that this Operator GO carries forward to any
future SHA or any future implementation change. Per the operator's own
terms, any future implementation change to this code exhausts this
authorization and requires a new bounded PR, new exact-head CI, a new
protected merge, and a fresh, separately scoped Operator GO.
