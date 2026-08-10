# ADR — PII redaction privacy-history exception

**Date:** 2026-08-10  
**Status:** Accepted — protected merge PR #283  
**Issue:** #282 · CLOSED_COMPLETED · parent #50 OPEN  
**Exact tested head:** `f4e41ca419e650a3a798dada77db82c02213b219`  
**Merge/main:** `493b1b6b6204cc9a7f5de82709717a1b625e2234`

## Context

Titan's Issue #50 canonical mutation contract normally requires a mutation to commit its
canonical row change together with a `VersionStore` pre-image and tamper-evident
`AuditChain` event. That is the correct default for recoverable history.

PII claim redaction is a special case. `VersionStore` stores historical plaintext
`claim`. Preserving the ordinary exact pre-image would re-persist the email, phone,
personal name or other detected token the operation is intended to remove. The version
store would itself become a residual PII store.

The pre-existing `ForgettingEngine.redact_pii_fact()` and `redact_pii_batch()` also owned
direct SQLite `UPDATE facts SET claim=...` paths. They bumped `fact_version` but did not
bind the claim mutation to same-transaction VersionStore/AuditChain evidence.

## Decision

`core.pii_redaction.CanonicalPiiRedactor`, backed by the existing `SQLiteGraphStore`
connection/transaction primitives, is the narrow owner of PII claim redaction.
`ForgettingEngine` is a compatibility adapter and no longer owns a direct claim UPDATE.

For this mutation family, privacy takes precedence over exact plaintext historical
recovery:

1. current `facts.claim` is replaced with the deterministic redacted claim;
2. `epistemic_state` and `confidence` are preserved exactly;
3. claim-derived integrity metadata is recomputed;
4. `fact_version` advances once when active;
5. the write is CAS-guarded on durable source claim + `updated_at`;
6. retained `fact_versions.claim` values for that fact are sanitized in the same
   transaction and their integrity metadata/checksum recomputed;
7. the VersionStore boundary row is itself sanitized before insertion;
8. a content-free `AuditChain` `FACT_UPDATED` event is appended in the same transaction;
9. claim-bearing FTS is refreshed synchronously when present;
10. when migration 020 is active, a content-free projection refresh intent is appended
    in the same transaction;
11. CAS/evidence/outbox failure rolls the entire transaction back;
12. L0 is invalidated only after commit.

Batch redaction preflights a bounded set and applies it in one `BEGIN IMMEDIATE`
transaction; one stale candidate rolls back the whole batch.

## Why this is not a second Canon architecture

`CanonicalPiiRedactor` does not introduce another database, general write protocol,
TruthGate, policy kernel, scheduler, runtime or control plane. It cannot promote ESM
state, erase facts physically, mutate relations, archive memory or activate runtime.

## Privacy / history trade-off

Exact plaintext time-travel recovery is intentionally impossible for the redacted claim
surface after redaction. Structural historical evidence remains — version timing, state,
confidence, source, caused-by metadata, checksums and a content-free AuditChain event —
but not the removed plaintext token on this claim surface.

This ADR does not authorize rewriting the append-only AuditChain. New redaction events are
content-free; historical unrelated/legacy audit events are not claimed sanitized.

## Residual boundary / non-claims

`REDACT_PII` remains claim-surface redaction. It is not proof of complete GDPR Article 17
erasure from immutable/raw origin storage, arbitrary metadata fields, every graph/vector
or external backend, backups or external systems. Full physical erasure remains owned by
`ErasureCoordinator` / durable batch erasure and their residual checks.

No schema migration, Continuity change, runtime enablement, Operator GO, runtime authority
or production authority follows from this decision.

## Alternatives rejected

- **Ordinary exact VersionStore pre-image:** rejected because it preserves removed PII.
- **Skip VersionStore/AuditChain:** rejected because it recreates the #50 evidence gap.
- **Physical erase and recreate:** rejected because it changes semantics and duplicates
  erasure authority.
- **Second privacy database/ledger:** rejected because existing SQLite transaction,
  VersionStore, AuditChain and outbox are sufficient.

## Verified evidence

The merged implementation proved state/confidence preservation, exact +1 version,
historical claim sanitization with VersionStore integrity, content-free AuditChain,
FTS/outbox consistency, true no-op behavior, forced VersionStore/AuditChain rollback,
stale-snapshot failure and batch atomicity.

Exact-head CI `31392230442`, Docker `31392230462` and aggregate `31392977479` succeeded;
post-merge CI `31393127943`, Docker `31393127973` and aggregate `31393128123` succeeded.
Final Notion synchronization/read-back was confirmed.