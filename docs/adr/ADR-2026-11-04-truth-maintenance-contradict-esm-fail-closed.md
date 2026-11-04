# ADR-2026-11-04 — TruthMaintenance.contradict ESM False is non-mutation

- **Status:** accepted
- **Date:** 2026-11-04
- **Owner:** repository maintainer (Velantrim Titan)

## Context

`core/truth_maintenance.py::contradict()` already called
`transition_esm(..., "Contradicted")` for each side of a contradiction pair.
`transition_esm` returns `False` for a missing fact or a failed CAS write and
raises for an illegal ESM transition. The pre-fix loop treated only exceptions
as skips and set `changed = True` after every non-raising call, including
`False`. That allowed CONTRADICTS causal edges and contradiction-registry rows
without a durable ESM mutation.

The architecture-freeze guard flags any added runtime line containing
`transition_esm(` as an authority marker. This ADR records that the PR rewrites
the existing call for fail-closed success semantics and does **not** introduce a
second ESM mutation owner.

## Decision

Keep `TruthMaintenance.contradict` as the sole manual contradiction orchestrator
on this path. Count a side as mutated only when
`transition_esm(fid, "Contradicted", by="truth_maintenance.contradict")`
returns `True`. Mint CONTRADICTS edges and contradiction-registry records only
when at least one durable transition succeeded. Do not add a parallel
Canon/ESM writer, TruthGate bypass, or feature flag.

## Authority boundary

- Canon/ESM writes: unchanged owner — `core.memory.transition_esm` /
  `SQLiteGraphStore.transition_esm` only; `contradict()` remains a caller.
- Background execution: none added.
- Network/provider access: none.
- External actions: none.
- User-visible influence: none beyond correcting false-positive success reports.

## Data, scope and privacy

No new persistence schema, subject scope, or retention class. Existing fact
rows, causal-graph edges, and contradiction-registry entries remain the only
surfaces; false edges are prevented going forward, not backfilled.

## Failure semantics

Fail closed on non-mutation:

- both facts missing → `False` (existing early return);
- missing partner and/or illegal ESM transition → `False`, no edge, no registry
  row when zero sides commit;
- at least one `True` ESM commit → `True`, best-effort edge/registry as before.

Exceptions from illegal transitions remain skipped per side. Secondary
edge/registry writes stay best-effort after a successful facts mutation (same
limitation class as supersede post-commit artifacts).

## Observability and receipts

ESM history `by` is set to `truth_maintenance.contradict` for successful
transitions. No new Operator GO, runtime enablement, or production receipt.

## Rollback

Revert the PR. Pre-fix behavior returns; no migration required.

## Validation

- `tests/test_truth_maintenance_contradict_fail_closed.py`
- Hosted CI on the PR head, including architecture-freeze with this ADR present

**PRODUCTION NOT AUTHORIZED. OPERATOR GO NOT ESTABLISHED.**
