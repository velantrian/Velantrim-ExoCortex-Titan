# Canonical PII redaction — ownership and residual boundary

**Tracking:** issue #282 · CLOSED_COMPLETED · parent #50 OPEN  
**Implementation PR:** #283 · MERGED  
**Exact tested head:** `f4e41ca419e650a3a798dada77db82c02213b219`  
**Protected squash merge:** `493b1b6b6204cc9a7f5de82709717a1b625e2234`  
**Architecture decision:** `docs/adr/ADR-2026-08-10-pii-redaction-privacy-history-exception.md`

## Current ownership

```text
legacy callers
    |
    v
ForgettingEngine.redact_pii_fact()/redact_pii_batch()
    |
    v
CanonicalPiiRedactor
    |
    v
existing SQLiteGraphStore transaction
    +-- CAS-guarded facts.claim mutation
    +-- refreshed integrity metadata
    +-- fact_version bump
    +-- privacy-sanitized VersionStore history/boundary
    +-- content-free AuditChain event
    +-- synchronous FTS refresh when present
    `-- content-free projection outbox refresh when migration 020 is active
```

`CanonicalPiiRedactor` is the current-main single owner for the PII **claim-redaction
mutation family**. It is not a general Canon service and does not own ESM promotion,
physical erasure, archival, causal relations, scheduling, runtime activation or policy
escalation.

## Privacy-history rule

Ordinary Titan lifecycle mutations preserve their exact pre-image in `fact_versions`.
PII redaction is intentionally different: exact plaintext recovery of the removed PII
would make the version store itself a residual PII store.

For a successful redaction, affected historical `fact_versions.claim` values are
sanitized in the same transaction and their integrity metadata/checksum is recomputed.
The redaction boundary VersionStore row is also stored with the sanitized claim. A
content-free AuditChain event records that the canonical fact changed without persisting
the removed claim in the new event.

This is a narrow privacy exception, not a general permission to rewrite history.

## Atomicity / failure semantics

A successful changed claim commits as one SQLite transaction. A stale source snapshot,
VersionStore failure, AuditChain failure, activated projection-outbox failure or other
SQLite failure aborts the whole operation. No-PII is a true no-op and emits no false
version/audit/outbox evidence. Batch redaction is bounded and all-or-nothing for the
selected candidates.

## Explicit non-claims

This mechanism redacts PII from the canonical fact's **claim surface**. It does not prove
physical erasure from arbitrary metadata, immutable raw origins, every graph/vector or
external backend, backups, third-party systems or legacy logs. Full data-subject erasure
remains the durable erasure coordinators' contract.

No GDPR certification, production readiness, current runtime enablement, current
Operator GO, runtime authority or production authority follows from this mechanism.

## Verified evidence

- exact-head Full CI `31392230442` — SUCCESS;
- exact-head Docker `31392230462` — SUCCESS;
- exact-head aggregate `31392977479` — SUCCESS;
- post-merge Full CI `31393127943` — SUCCESS;
- post-merge Docker `31393127973` — SUCCESS;
- post-merge aggregate `31393128123` — SUCCESS;
- submitted reviews `0`; unresolved review threads `0`;
- Codex `NOT RUN — USAGE LIMIT`; independent review not claimed;
- final Notion synchronization/read-back confirmed.

Parent #50 remains open for residual mutation families.