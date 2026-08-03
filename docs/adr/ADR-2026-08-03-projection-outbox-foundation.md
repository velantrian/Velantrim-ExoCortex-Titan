# ADR — Transaction-owned projection-outbox foundation

**Status:** accepted for foundation only  
**Date:** 2026-08-03  
**Issue:** #179  
**Dependencies:** promotion ownership #166–#173; SQLite proofs #174–#177

## Context

Titan's implemented canonical write paths already require their Canon mutation,
VersionStore pre-image and AuditChain event to share one SQLite transaction. Rebuildable
FTS, graph and vector projections must never become authoritative, but the repository has
no runtime ProjectionOutbox and therefore no durable same-transaction delivery intent.

Introducing a dispatcher, retry policy and Canon caller wiring in one change would mix
three different authorities. The first increment must establish only the durable append
primitive and prove its transaction semantics.

## Decision

Add an immutable `projection_outbox` intent table and a typed append primitive:

```text
caller-owned SQLite transaction
├── Canon mutation (future caller increment)
├── VersionStore / AuditChain (existing caller contract)
└── append_projection_intent_in_transaction(...)
    └── immutable technical routing intent
```

The append primitive:

- requires an already-active caller-owned `sqlite3.Connection` transaction;
- never opens its own connection;
- never commits or rolls back;
- never retries;
- never dispatches or mutates a projection;
- uses a deterministic semantic `outbox_id` for exact idempotency;
- fails closed if an existing row with that id has different semantics.

## Content minimization

The durable v1 intent contains only:

- outbox id;
- aggregate type and technical aggregate id;
- explicit scope reference supplied by the future caller;
- projection kind;
- refresh/remove operation;
- canonical version;
- policy version;
- creation timestamp.

It contains no claim, justification, evidence body, evidence references, prompt, model
output or arbitrary payload JSON.

A direct aggregate identifier remains inside the same protected Canon SQLite database.
No Canon caller may be wired until erasure/dependency handling for these rows is added
and tested. Multi-user activation remains blocked until an executable SubjectScope
contract exists; this foundation does not invent one.

## Delivery-state separation

The foundation table is immutable intent, not a work-queue state machine. Dispatcher
claim/lease, attempts, acknowledgement, dead-letter policy and retry timing will be
introduced separately after crash semantics are specified. This avoids freezing an
untested retry model into migration 020.

## Atomicity proof

Foundation tests show:

1. append without an active transaction fails closed;
2. append leaves the caller transaction open;
3. another connection cannot observe the row before commit;
4. Canon probe mutation and intent both disappear on caller rollback;
5. an outbox semantic collision propagates an exception so the caller can roll back its
   Canon mutation;
6. an exact duplicate is one idempotent row, not a second intent;
7. migration 020 is registered, idempotent and integrity-safe.

The exact migration-runner patch, focused Ruff, focused mypy, outbox atomicity tests and
existing migration suite passed before the self-removing workflow published the final
six-file change-set. Bot-authored follow-up workflows were `action_required` with zero
jobs, so they are not accepted as evidence; standard CI and Docker must run again on a
maintainer-authored pinned head.

## Runtime status

After this increment the subsystem may be only:

```text
DESIGNED
IMPLEMENTED_IN_BRANCH
MERGED_IN_MAIN
```

It is not `RUNTIME_WIRED`, `FEATURE_ENABLED`, `RUNTIME_OBSERVED` or a delivery guarantee.
No existing Canon path writes an outbox row.

## Non-goals

- no Canon caller migration;
- no dispatcher, worker, scheduler, lease or retry;
- no network or remote transport;
- no exactly-once claim;
- no projection authority;
- no compound supersede integration;
- no Continuity activation;
- no database replacement.

## Next increment

Select and characterize one single-fact canonical mutation family. Before wiring, add
outbox erasure/dependency behavior. Then append the intent in the same existing
transaction and prove both directions of rollback. Dispatcher work remains later.
