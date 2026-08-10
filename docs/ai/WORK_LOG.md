# 🧾 AI Engineering Work Log

Re-verify exact SHAs, PR state and workflow conclusions before continuing work.

This file is a compact current hand-off. Older details remain traceable in Git history,
merged PR bodies, issues, ADRs and dated checkpoint documents.

---

## 2026-08-10 — P0 archival canonical claim convergence in protected review

```text
Parent Truth Foundation:       #50 · OPEN
Tracking issue:                #284 · OPEN during review
Implementation PR:             #285 · DRAFT / REVIEW-STAGE
Exact audited base main:       493b1b6b6204cc9a7f5de82709717a1b625e2234
Documentation impact:          GITHUB_AND_NOTION
Continuity:                    12/12 = 100% · unchanged
Schema:                        v7 · unchanged
Runtime currently enabled:     false · unchanged
Operator GO:                   false · unchanged
Runtime authority:             false · unchanged
Production authority:          false · unchanged
```

### Residual inventory

Focused #50 audit on the exact base classified:

- single-fact erasure: converged through `ErasureCoordinator`; legacy `forget_one()` is
  an adapter;
- PII claim redaction: converged on `CanonicalPiiRedactor` in merged PR #283;
- async fact mutations: converged as `AsyncSQLiteStore` adapters over exact synchronous
  canonical methods; the independent native-SQL path remains disabled;
- archival claim rewrite: **REAL_GAP** selected for #284/#285;
- causal relation create/delete: **REAL_GAP**, deliberately left as a separate future
  #50 bounded block;
- #249: separate contention characterization, untouched.

### Archival candidate contract

PR #285 removes direct `UPDATE facts` ownership from `MemoryArchival`. The coordinator
continues bounded eligibility, payload preparation, restore and reporting, while a narrow
`CanonicalArchivalRewriter` reuses the existing `SQLiteGraphStore` transaction owner.

One archive payload batch binds durable-snapshot CAS, exact VersionStore pre-image,
content-free AuditChain evidence, `archived_facts` marker, integrity refresh, exact
fact-version bump, FTS refresh, active migration-020 projection intent and post-commit
L0 invalidation. Any SQLite/evidence failure rolls the whole DB batch back.

Filesystem and SQLite are not falsely described as one ACID transaction. The payload is
created uniquely, flushed and fsynced before Canon may reference it. If the DB/evidence
transaction then fails, the new payload is removed best-effort; an OS-level cleanup
failure can leave only a non-canonical orphan file, never canonical success.

Real temporary-SQLite tests cover happy path, no-op/repeat, missing payload, stale CAS,
VersionStore/AuditChain rollback, FTS/outbox consistency, batch rollback and structural
removal of legacy raw-SQL ownership.

### Review boundary

This section is review evidence while PR #285 is unmerged. Treat exact branch code as
candidate implementation only. Before ready-for-review, final head must be frozen,
Full CI and Docker must succeed, GitHub docs must be complete, and the existing Notion
page must receive a `REVIEW EVIDENCE / NOT MAIN` block with read-back confirmation.
Protected merge additionally requires `Titan aggregate merge evidence`, zero unresolved
review threads and an unchanged expected head/base relationship.

---

## 2026-08-10 — PII claim-redaction convergence completed

```text
Parent Truth Foundation:       #50 · OPEN
Tracking issue:                #282 · CLOSED_COMPLETED
Implementation PR:             #283 · MERGED
Exact tested head:             f4e41ca419e650a3a798dada77db82c02213b219
Protected squash merge/main:   493b1b6b6204cc9a7f5de82709717a1b625e2234
Exact-head Full CI:            31392230442 · SUCCESS
Exact-head Docker:             31392230462 · SUCCESS
Exact-head aggregate:          31392977479 · SUCCESS
Post-merge Full CI:            31393127943 · SUCCESS
Post-merge Docker:             31393127973 · SUCCESS
Post-merge aggregate:          31393128123 · SUCCESS
Submitted reviews:             0
Codex:                         NOT RUN — USAGE LIMIT
Unresolved review threads:     0
Independent review:            NOT CLAIMED
Documentation impact:          GITHUB_AND_NOTION · FINAL read-back confirmed
```

`CanonicalPiiRedactor` is now current-main implementation truth for PII claim redaction.
The privacy-history exception sanitizes affected `fact_versions.claim` values instead of
re-persisting removed plaintext PII. This does not claim complete Article 17 erasure from
all possible storage surfaces; durable physical erasure remains a separate coordinator
contract.

---

## 2026-08-10 — Continuity 12/12 bounded observation completed

```text
Tracking issue:                #275 · CLOSED_COMPLETED
Canary baseline:               39ba28dbf6bce4da1e18d6726ae4f4f79dc5f24e
Mechanism PR:                  #276 · merge 456b762b1e752a2f5fb22762869336be9fed42a4
Historical observed evidence:  true · one operator-authorized rolled-back canary
Runtime currently enabled:     false
Current Operator GO:           false · one-time canary grant exhausted
Runtime authority:             false
Production authority:          false
Continuity:                    12/12 = 100%
Schema:                        v7
```

No standing authorization, public rollout, scheduler/autonomous loop or production
readiness follows from the completed canary.

---

## Governance boundary

```text
Ruleset:                      main-governance · id 20601712 · active
Mode:                         SOLO · required approvals 0
Bypass actors:                0
Required check:               Titan aggregate merge evidence
Strict status policy:         true
Conversation resolution:      required
```

## Stable continuation boundary

Continuity is complete at `12/12 = 100%`; do not invent 13/12 or infer production
readiness. Truth Foundation #50 remains OPEN until remaining real canonical mutation
gaps, notably causal relation mutation, are separately converged and verified. Issue
#249 remains separate.