# SAFE_MODE mutation boundary

**Status:** auxiliary user/projection hardening · safety ledgers remain writable

## Existing protected Canon boundary

Titan already blocks these canonical operations through `core.write_gate` and `PolicyKernel`:

- fact create/update;
- structured `store_fact_result`;
- ESM transition;
- temporal invalidation;
- batch fact writes.

## Confirmed auxiliary gaps

The following mutable stores write outside the canonical facts API and previously did not consult the active policy snapshot:

| Store | Mutable operations | Classification |
|---|---|---|
| GoalStack | create goal, change status | mutable user state |
| ConsoleNotesStore | create, update, delete note | mutable user state |
| MemoryOps source registry | register/update source | operational projection |
| MemoryOps fact inbox | enqueue, status update | operational projection |
| MemoryOps promotion | raw append, Canon proposal, inbox update | mixed; gate before all work |
| MemoryOps reasoning traces | save trace | mutable operational history |

These operations stop before their first read-modify-write step when `PolicySnapshot.writes_allowed` is false.

## Gate

`core.mutation_gate.ensure_user_mutations_allowed(scope)` captures one verified local policy snapshot and raises `UserMutationBlockedError` when:

- MetaSupervisor is in SAFE_MODE; or
- policy dependencies are unavailable and the snapshot fails closed.

Scopes are safe lower-case dotted identifiers and are retained only as technical reason context.

## Explicit exceptions

The auxiliary gate is deliberately **not** applied to:

- GDPR erasure jobs, batches, tombstones and recovery receipts;
- incident/audit evidence required to diagnose SAFE_MODE;
- health/readiness evidence;
- schema migrations and technical table initialization;
- append-only safety/compliance ledgers.

These mechanisms may be required precisely while user and Canon mutation is frozen. Their own contracts remain responsible for content minimization, append-only behavior, idempotency and bounded execution.

## Promotion ordering

`MemoryOpsStore.promote_inbox_item()` calls the auxiliary gate before:

1. reading/adopting the inbox item;
2. appending immutable raw L0 text;
3. calling canonical `store_fact_result`;
4. updating inbox/provenance state.

This prevents the old partial-write shape where raw L0 could be appended before the canonical write gate rejected SAFE_MODE.

## Runtime result

```text
SAFE_MODE or policy dependency unavailable
→ Goal/Note/Inbox/Source/Trace mutation raises typed error
→ no partial raw/Canon/projection write
→ reads remain available
→ erasure/audit/health ledgers remain operational
```

## Validation boundary

The exact self-removing patch compiled all modified stores and passed:

- 9 canonical SAFE_MODE write tests;
- 7 auxiliary mutation-boundary tests;
- 5 direct Innenwelt/GoalStack tests.

The two server-import API cases are covered by standard full repository CI, whose complete dependency profile includes deployment/server extras. Temporary patch workflow/script files are absent from the final branch.

The final maintainer-authored head was emitted after the TruthPolicy `/query` hardening reached `main`, so standard CI and Docker validate this boundary against the current combined safety baseline.
