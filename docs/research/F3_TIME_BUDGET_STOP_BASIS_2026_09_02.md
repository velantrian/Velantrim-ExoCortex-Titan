# F3 time-budget stop-basis probe — 2026-09-02

## Scope

Bounded research probe against the existing `StartupRecoveryReceipt` contract in `core/erasure_startup_recovery.py`.

No production/runtime behavior is added or changed.

## Question

Can the same outward unresolved observation preserve a materially different stop basis when the bounded recovery run stopped because its time budget was exhausted versus when unresolved recovery work simply remains?

## Existing contract under test

For a receipt with unresolved recovery work, `StartupRecoveryReceipt` emits:

- `ObservationState.OBSERVED_NONZERO`
- `observed_value = unresolved_count`
- `reason_code = "time_budget_exhausted"` when `stopped_by_time_budget` is true
- otherwise `reason_code = "recovery_work_remaining"`

## Controlled comparison

The probe fixes the outward state and unresolved count at the same values and varies only `stopped_by_time_budget`.

Expected distinction:

`SAME OBSERVED_NONZERO + SAME unresolved_count != SAME STOP BASIS`

Specifically:

`TIME-BUDGET STOP != ORDINARY REMAINING WORK`

## Ceiling

This probe does **not** establish:

- task-conditioned insufficiency;
- irreducible uncertainty;
- deadline semantics outside this startup-recovery time budget;
- resource exhaustion in general;
- automatic retry/reopen policy;
- scheduler behavior;
- action or runtime authority;
- a universal StopReason/StopReceipt architecture;
- full F3 end-to-end completion.

`DRAFT_STALE != TIME_BUDGET_EXHAUSTED` remains an explicit distinction.

## Disposition

If exact-head CI passes, the bounded conclusion is:

`TIME-BUDGET STOP BASIS PRESERVATION = OBSERVED IN EXISTING TITAN CONTRACT`

while:

`TASK-CONDITIONED STOP = NOT_ESTABLISHED`

`IRREDUCIBLE UNCERTAINTY STOP = NOT_ESTABLISHED`

`FULL F3 = NOT_ESTABLISHED`

No new primitive or owner is justified by this probe alone.
