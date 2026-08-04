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
Erasure/dependency handling for these rows was added and tested in issue #183 (see
`ADR-2026-08-03-projection-outbox-erasure-dependency.md`) — `projection_outbox` now
shares `SQLiteGraphStore`'s same-DB dependent registry, so any row a future caller
writes is already covered by the existing atomic same-DB deletion and residual proof.
No Canon caller is wired by that increment either. Multi-user activation remains
blocked until an executable SubjectScope contract exists; this foundation does not
invent one.

`scope_ref` itself was syntactically defined (regex only) but had no executable
semantics until issue #189 (see
`ADR-2026-08-04-local-projection-scope-reference.md`): `ProjectionIntent` v1 now
accepts exactly one exported constant, `LOCAL_PROJECTION_SCOPE_REF = "local:primary"`
— a local routing namespace only, explicitly not an authorization boundary, tenant, or
SubjectScope. This closes the `BLOCKER_SCOPE_CONTRACT` that characterization for the
first Canon caller increment had identified.

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
existing migration suite passed before the self-removing workflow published the clean
foundation change-set.

The first full repository run exposed one unrelated stale Reader Adapter assertion that
hard-coded `019_suggested_edges.sql` as the permanent last migration. That test did not
represent its intended invariant: the Reader Adapter must remain schema-free even when
other subsystems add migrations. It now checks that no Reader-specific migration exists,
without freezing the repository-wide migration head. The corrected Reader regression,
outbox tests and migration suite passed together. All diagnostic and patch workflows and
evidence files were removed before final validation.

## Runtime status

After this increment the subsystem may be only:

```text
DESIGNED
IMPLEMENTED_IN_BRANCH
MERGED_IN_MAIN
```

It is not `RUNTIME_WIRED`, `FEATURE_ENABLED`, `RUNTIME_OBSERVED` or a delivery guarantee.
No existing Canon path writes an outbox row.

## Merge gate

Only standard CI and Docker attached to one maintainer-authored pinned final head count
as merge evidence. Architecture freeze, repository hygiene, Ruff, blocking mypy, the
full repository pytest suite and Docker hardening must be green, with zero unresolved
review threads. Focused or bot-authored runs do not replace this gate.

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

~~Before wiring, add outbox erasure/dependency behavior.~~ Done — issue #183,
`ADR-2026-08-03-projection-outbox-erasure-dependency.md`.

~~Define a usable scope_ref contract.~~ Done — issue #189,
`ADR-2026-08-04-local-projection-scope-reference.md`.

Remaining: select and characterize one single-fact canonical mutation family
(characterization already identified `SQLiteGraphStore.validate_and_promote()` as the
candidate, with its Canon CAS UPDATE, VersionStore snapshot, and AuditChain event
already sharing one `sqlite3.Connection`/transaction), append the intent in that same
transaction using the now-defined `LOCAL_PROJECTION_SCOPE_REF`, source
`canonical_version` from `facts.fact_version` (migration 009 — itself schema-optional,
needs its own fail-closed gating parallel to `projection_outbox`'s), and prove both
directions of rollback. Dispatcher work remains later still.
