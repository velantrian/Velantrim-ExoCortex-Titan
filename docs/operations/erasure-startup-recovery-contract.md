# Bounded erasure startup recovery — receipt contract

**Status:** contract increment only · no execution or lifespan wiring

## Accounting semantics

`RecoveryDomainReceipt` separates measured outcomes from future work:

- `selected` — items admitted to this bounded run;
- `attempted` — selected items for which the coordinator attempted a claim/run;
- `completed`, `partial`, `failed`, `skipped` — mutually exclusive outcomes whose sum must equal `attempted`;
- `remaining_backlog` — recoverable future work **not already counted as `partial` or `failed`**.

`remaining_backlog` must include every selected-but-unattempted item. A `skipped` item is included in `remaining_backlog` only when it remains resumable, for example because a live lease prevented a claim. A skip caused by a race to a terminal outcome is not backlog.

This separation prevents the aggregate unresolved metric from double-counting the same failed or partial item.

## Derived observation

A measured startup receipt derives its own Reality Lock observation:

- no partial, failed or backlog items → `OBSERVED_ZERO`;
- any partial, failed or backlog item → `OBSERVED_NONZERO`;
- selected-but-unattempted work requires an explicit time-budget stop;
- callers cannot inject a more favorable observation result.

If recovery cannot produce measured domain outcomes because its observer, jobs schema or database fails first, callers must emit `StartupRecoveryFailureReceipt`. It derives `OBSERVER_FAILED`, carries only a typed safe error code and cannot pretend that zero violations were observed.

All recovery error codes are restricted to lower-case `snake_case` identifiers of at most 64 characters. Exception messages, paths, SQL text and payload fragments are invalid receipt data and belong only in protected server logs.

## Persistence honesty

The first increment does not persist receipts. `persisted=True` is valid only with a non-empty `storage_ref`; a non-persisted receipt cannot claim one. Later durable-ledger wiring must set both from the actual committed record rather than configuration intent.

The same persistence rule applies to measured and observer-failure receipts.

## Runtime boundary

This contract does not:

- query an erasure jobs database;
- resume a job or batch;
- modify `server.py` lifespan;
- register a scheduler or background task;
- change erasure/tombstone policy;
- write Canon or affect user-visible output.

## Validation gate

Only CI and Docker runs attached to the final maintainer-authored PR head are accepted. Superseded or `action_required` runs from temporary one-shot patch commits are not merge evidence.
