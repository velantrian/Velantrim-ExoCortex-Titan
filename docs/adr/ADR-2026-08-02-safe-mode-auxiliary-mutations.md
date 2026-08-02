# ADR: Freeze auxiliary user-state mutations in SAFE_MODE

- **Status:** Accepted for implementation
- **Date:** 2026-08-02
- **Decision owner:** repository maintainer/operator
- **Scope:** local mutable user/projection stores outside canonical facts

## Context

Canonical fact writes already consult `PolicyKernel` through `core.write_gate`. Several local stores mutate user or operational state directly through SQLite:

- goals;
- console notes;
- source registry;
- fact inbox;
- inbox promotion side effects;
- reasoning traces.

In SAFE_MODE these paths could continue mutating state even while Canon was read-only. `MemoryOpsStore.promote_inbox_item()` was especially important because it could append immutable raw L0 text before the canonical store returned a SAFE_MODE rejection.

## Decision

Introduce `core.mutation_gate.ensure_user_mutations_allowed(scope)`.

The gate:

1. validates a safe technical scope identifier;
2. captures the current immutable `PolicySnapshot`;
3. permits mutation only when `snapshot.writes_allowed` is true;
4. raises a typed `UserMutationBlockedError` on SAFE_MODE or policy dependency failure.

Apply it before all user-state work in:

- `GoalStack.create` and `GoalStack.update_status`;
- `ConsoleNotesStore.create_note`, `update_note`, `delete_note`;
- `MemoryOpsStore.register_source`, `enqueue_fact`, `set_inbox_status`, `promote_inbox_item`, `save_trace`.

## Explicit exceptions

Do not apply this gate to safety/compliance mechanisms that may be required during SAFE_MODE:

- erasure jobs, batches, tombstones and recovery evidence;
- migrations and technical schema initialization;
- health/readiness evidence;
- append-only incident or audit ledgers.

Those paths retain their own least-authority, content-minimization and durability contracts.

## Consequences

### Positive

- SAFE_MODE becomes a system-wide freeze for mutable user and projection state, not only Canon;
- policy dependency failure remains fail-closed;
- inbox promotion cannot create raw L0 or partial projection state before a blocked canonical write;
- reads and recovery/audit operations remain available for incident response.

### Trade-offs

- note, goal, inbox and trace endpoints may return a typed mutation-blocked error during incidents;
- technical table initialization may still write DDL while SAFE_MODE is active;
- future mutable stores must be inventoried and explicitly classified.

## Rejected alternatives

- **Gate every SQLite write:** rejected because it would disable erasure, audit and health evidence needed during incidents.
- **Reuse only `ensure_writes_allowed()`:** rejected because its naming and contract are canonical-specific and would obscure the auxiliary/safety distinction.
- **Block only API routes:** rejected because internal workers and direct Python callers could bypass route-level checks.
