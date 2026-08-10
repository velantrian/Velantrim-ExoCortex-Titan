# ADR — PII redaction privacy-history exception

**Date:** 2026-08-10  
**Status:** Proposed on PR #283 until protected merge  
**Issue:** #282 · parent #50  
**Base:** `main@d62d51636f96749950fd60cac316e41f46a461a5`

## Context

Titan's Issue #50 canonical mutation contract normally requires a mutation to commit its
canonical row change together with a `VersionStore` pre-image and a tamper-evident
`AuditChain` event. That is the correct default for recoverable history.

PII claim redaction is a special case. `VersionStore` stores the historical plaintext
`claim`. If redaction preserved the ordinary exact pre-image, an operation intended to
remove `alice@example.com`, a phone number, a personal name, or another detected token
would re-persist that same token in `fact_versions`. The audit/version surface would
become a residual PII store.

The pre-existing `ForgettingEngine.redact_pii_fact()` and `redact_pii_batch()` also
owned direct SQLite `UPDATE facts SET claim=...` paths. They bumped `fact_version` but
did not bind the claim mutation to same-transaction VersionStore/AuditChain evidence.

## Decision

Introduce one narrow mutation-family service,
`core.pii_redaction.CanonicalPiiRedactor`, backed by the existing
`SQLiteGraphStore` connection/transaction primitives. It owns **only PII claim
redaction**. `ForgettingEngine` becomes a compatibility adapter and no longer owns a
direct claim UPDATE.

For this mutation family, privacy takes precedence over exact plaintext historical
recovery:

1. the current `facts.claim` is replaced with the deterministic redacted claim;
2. `epistemic_state` and `confidence` are preserved exactly (I-F3);
3. claim-derived integrity metadata is recomputed;
4. `fact_version` advances once when the Truth Kernel version column is active;
5. the write is CAS-guarded on the durable source claim + `updated_at` snapshot;
6. already-retained `fact_versions.claim` values for that fact are sanitized inside the
   same transaction, with their integrity metadata/checksum recomputed;
7. the VersionStore boundary row created for redaction is itself sanitized before it is
   inserted — the plaintext pre-redaction claim is not re-persisted;
8. a content-free `AuditChain` `FACT_UPDATED` event is appended in the same transaction;
9. claim-bearing FTS is refreshed in that same transaction when available;
10. when migration 020 is active, a content-free projection refresh intent is appended
    in the same transaction;
11. any CAS/evidence/outbox failure rolls the entire canonical redaction transaction
    back;
12. L0 is invalidated only after commit.

Batch redaction snapshots a bounded selected set, preflights evidence schema, then
applies every candidate in one `BEGIN IMMEDIATE` transaction. A stale candidate aborts
and rolls back the whole batch.

## Why this is not a second Canon architecture

`CanonicalPiiRedactor` does not introduce another database, general write protocol,
TruthGate, policy kernel, scheduler, runtime, or control plane. It is a narrowly typed
privacy mutation service over the existing `SQLiteGraphStore` transaction owner. It
cannot promote ESM state, erase facts physically, mutate relations, archive memory, or
activate runtime behavior.

## Privacy / history trade-off

The decision deliberately makes exact plaintext time-travel recovery impossible for
the redacted claim surface after redaction. That is intentional. A privacy redaction
that leaves recoverable plaintext PII in ordinary version history does not satisfy its
own stated purpose.

The system retains structural historical evidence — version timing, state, confidence,
source, caused-by metadata, checksums and a content-free AuditChain mutation event — but
not the removed plaintext token on this claim surface.

This ADR does **not** authorize rewriting the append-only AuditChain. New redaction
events are content-free. Historical audit events from unrelated/legacy paths are not
claimed sanitized by this change.

## Residual boundary / non-claims

`REDACT_PII` remains claim-surface redaction. It is **not** proof of complete GDPR
Article 17 erasure from:

- immutable/raw origin storage;
- arbitrary metadata fields outside the claim-redaction contract;
- graph/vector or external backends that do not have an active fact-addressable privacy
  removal contract;
- backups or external systems;
- historic third-party payloads/logs outside this transaction.

Full physical erasure remains owned by `ErasureCoordinator` / durable batch erasure and
their residual checks. This ADR does not create a certified GDPR compliance claim.

## Alternatives rejected

### A. Ordinary exact VersionStore pre-image

Rejected: it preserves the original PII in `fact_versions` and makes redaction
self-defeating.

### B. Skip VersionStore and AuditChain entirely

Rejected: this recreates the current #50 evidence gap and allows a meaningful Canon
mutation without structured tamper-evident evidence.

### C. Physical erase and recreate the fact

Rejected: changes the semantics of `REDACT_PII`, risks identity/relation breakage, and
duplicates the durable erasure authority.

### D. Add a second privacy database or redaction ledger

Rejected: creates another durable authority/store and unnecessary reconciliation
burden. Existing SQLite transaction, VersionStore structure, AuditChain and outbox are
sufficient for this bounded contract.

## Validation requirements

Before merge, exact-head evidence must prove:

- single and batch redaction preserve state/confidence;
- fact version advances exactly once per changed current fact;
- current integrity metadata validates after redaction;
- no original PII remains in the affected `fact_versions.claim` rows;
- `VersionStore.verify_versions_integrity()` remains green after sanitization;
- new AuditChain evidence is content-free;
- FTS reflects the redacted claim;
- active outbox receives only content-free refresh intent;
- no-PII is a true no-op;
- forced VersionStore/AuditChain failure rolls back Canon/history/FTS/outbox;
- stale snapshot fails closed;
- one stale member rolls back a batch's other redactions;
- full repository CI/gates pass on the final PR head.

## Authority and runtime boundary

No schema migration, Continuity change, ADAO/ARM-04 work, runtime enablement, Operator
GO, runtime authority or production authority is introduced by this decision.
