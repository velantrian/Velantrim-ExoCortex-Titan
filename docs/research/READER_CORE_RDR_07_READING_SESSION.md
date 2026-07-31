# PR-RDR-07 — ReadingSession

**Boundary:** `SHADOW_FOUNDATION / IMMUTABLE_SNAPSHOTS / NO_PERSISTENCE_WIRING / NO_RUNTIME_AUTHORITY`

## Purpose

`ReadingSession` makes long-document work resumable and observable without
turning Reader Core into a scheduler, database owner, truth authority, or Canon
writer.

```text
logical session_id
    ↓
immutable snapshot_id #0
    ↓ receipt
immutable snapshot_id #1
    ↓ receipt
immutable snapshot_id #2
```

A session mutation never changes an existing snapshot in place. Every accepted
transition creates a new frozen snapshot and appends a self-verifying receipt.

## Added contracts

- `ReadingSession` — immutable progress snapshot;
- `ReadingSessionReceipt` — append-only session-local transition chain;
- `ReadingSessionCheckpoint` — exact snapshot restoration envelope;
- `ReadingSessionBudget` / `ReadingSessionUsage` — cumulative measured resource
  accounting;
- `SessionLease` — worker fencing token with monotonically increasing
  generation;
- `SessionUnitArtifact` — exact mapping from a completed reading unit to a
  current or reused `SectionCard` reference;
- `RevisionReusePlan` — fail-closed revision invalidation and exact-text reuse
  proposal;
- `ReadingSessionManager` — pure deterministic transition engine.

## State semantics

```text
CREATED → READING → PAUSED → READING
                 ↘ DEGRADED ↗
READING/DEGRADED → COMPLETED
active states     → FAILED | CANCELLED | STALE
STALE + reuse plan → CREATED on the new revision generation
```

Completion requires:

1. no pending reading units;
2. a recorded `CoverageMap` reference;
3. an unexpired matching worker lease.

Unresolved questions do not falsely block completion; they remain explicit
session data for global synthesis.

## Two distinct lease concepts

`SessionLease` is a local worker-ownership fence:

```text
runner_id + generation + expires_at_ms
```

It prevents a stale worker from mutating a snapshot after another worker has
claimed the session. It grants no tool, network, model, policy, memory, or write
capability.

`capability_lease_ref` is only an opaque reference to an independently issued
policy capability. PR-RDR-07 does not create, renew, interpret, or authorize
that capability.

## Resource accounting

The session independently records:

- processed reading units;
- source characters;
- model tokens;
- wall time;
- emitted receipts.

A transition that would exceed any hard budget fails before a new snapshot is
created. Resource usage is not confidence, correctness, understanding, or
truth.

## Pause, resume, and crash recovery

A checkpoint contains an exact `ReadingSession` snapshot and a content-derived
`checkpoint_id`. Restoring the checkpoint returns the same immutable snapshot;
a caller must claim a fresh lease generation before resuming paused or stale
work.

PR-RDR-07 defines the durable data contract but deliberately adds no database,
filesystem, background worker, queue, or runtime integration. A later storage
adapter can persist the checkpoint without redefining transition semantics.

## Revision-aware reuse

Reuse is allowed only when all of the following hold:

1. old and new units belong to the same document;
2. source revisions differ;
3. the unit text, source hash, and character count match exactly;
4. the fingerprint occurs exactly once among completed old units and exactly
   once in the new plan.

Repeated identical passages are ambiguous and therefore not reused. Changed or
ambiguous units become explicitly pending.

A reused artifact is stored as:

```text
kind = REUSED_CARD
artifact_source_revision = old revision
unit_id = new revision unit
```

This preserves the fact that the cache reference came from an older revision.
It does not silently relabel old provenance as new provenance.

## Invariants

- pending and completed units exactly partition the current reading plan;
- completed units have exactly one ordered artifact reference;
- current cards match the current source revision;
- receipt sequence starts at zero and forms an unbroken previous-ID chain;
- the last receipt state equals the snapshot state;
- resource receipt accounting equals the receipt count;
- stale lease generations cannot mutate a newer claim;
- forged lease, receipt, checkpoint, reuse-plan, and snapshot IDs fail closed;
- original sources and previous snapshots are never modified;
- no Canon write, memory admission, graph authority, TruthGate bypass, Write
  Gate call, model call, network call, tool call, or `/query` wiring.

## Deferred

- SQLite or filesystem persistence adapter;
- distributed clock and lease renewal service;
- queue worker implementation;
- capability broker integration;
- automatic card provenance rebasing;
- global synthesis creation;
- live-path promotion and operator controls.
