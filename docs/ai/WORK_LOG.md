# 🧾 AI Engineering Work Log

Re-verify exact SHAs, PR state and workflow conclusions before continuing work.

This file is a compact current hand-off. Older details remain traceable in Git history,
merged PR bodies, issues, ADRs and dated checkpoint documents.

---

## 2026-08-12 — P0 smart-KB convergence + Truth Foundation #50 completed

```text
Parent Truth Foundation:       #50 · CLOSED_COMPLETED · fresh residual REAL_GAP=0
Tracking issue:                #292 · CLOSED_COMPLETED
Implementation PR:             #293 · MERGED
Final pre-merge head:          48817c5b0067d085135d4e8f144a620a34265597
Protected squash merge/main:   c80c8d47588de3d2607c7e1b10aa1677eb84383f
Merge parent:                  7a47f5dbb786fe267093857bf370fd03703207ac
Focused identical-tree gate:   31578562991 · SUCCESS
Pre-merge Full CI:             31580684106 · SUCCESS
Pre-merge Docker:              31580683989 · SUCCESS
Ready aggregate:               31594821320 · SUCCESS
Post-merge Full CI:            31594960307 · SUCCESS
Post-merge Docker:             31594960229 · SUCCESS
Post-merge aggregate:          31594960289 · SUCCESS
Merge signature:               VERIFIED / valid
Submitted reviews:             0
Codex code review:             NOT RUN — USAGE LIMIT
Unresolved review threads:     0
Continuity:                    12/12 = 100% · unchanged
Schema:                        v7 · unchanged
Runtime currently enabled:     false · unchanged
Operator GO:                   false · unchanged
Runtime authority:             false · unchanged
Production authority:          false · unchanged
```

Current-main smart-KB fact build no longer owns raw canonical fact DML. Curated fact
admission delegates to `store_facts_batch()`, validation to canonical ESM promotion,
`--fast-fresh` is only an empty-DB precondition, incomplete builds fail closed, and
causal edges remain on `CausalGraph`.

Fresh residual inventory on `c80c8d47588de3d2607c7e1b10aa1677eb84383f` rechecked fact create/update, raw provenance, ESM
transitions, supersede, redaction, archival rewrite, durable erasure/dependent deletion,
causal relations, async adapters, smart-KB build, cache-maintenance, projections/indexes,
entity/living-context/notes/audit side stores, migration-only paths and scratch ingestion.
No new meaningful canonical mutation owner remained: `REAL_GAP=0`. Emergency coverage
issue #28 is CLOSED. Open #53 is downstream architecture that depends on #50 and is not
a residual #50 mutation gap or an authorization granted by this closure.

---

## Historical pre-merge evidence — P0 smart-KB fact-build authority

```text
Parent Truth Foundation:       #50 · OPEN / reopened
Tracking issue:                #292 · OPEN
Implementation PR:             #293 · DRAFT / REVIEW-STAGE
Authoritative base main:       7a47f5dbb786fe267093857bf370fd03703207ac
Branch:                        p0/smart-kb-fact-build-authority
Clean implementation head:     a61d0f64a0d0df49f9c2153e3500f2b0cdd12a5d
Focused identical-tree gate:   31578562991 · SUCCESS
Exact-head Full CI:            31579598960 · SUCCESS
Exact-head Docker:             31579598954 · SUCCESS
Draft aggregate:               31579598885 · SUCCESS · not final merge gate
Documentation impact:          GITHUB_AND_NOTION · REVIEW sync pending final candidate
Continuity:                    12/12 = 100% · unchanged
Schema:                        v7 · unchanged
Runtime currently enabled:     false · unchanged
Operator GO:                   false · unchanged
Runtime authority:             false · unchanged
Production authority:          false · unchanged
```

Fresh post-#291 inventory found direct smart-KB fact DML in `build_kb_graph.py`. The
resulting database can be launched as normal `VELANTRIM_DB_PATH`, so parent #50 remains
OPEN. The candidate removes builder-owned fact INSERT/UPDATE authority, declares curated
WSC classification before canonical batch admission, uses VersionStore/AuditChain-aware
batch reclassification and canonical ESM promotion, preserves `CausalGraph` ownership,
and makes `--fast-fresh` an empty-DB precondition rather than an authority bypass.
Incomplete ingest/validation fails the build.

The clean PR commit has exactly one parent (`main@7a47f5db...`) and six intended files;
staging helper history is not ancestral to PR #293. AI truth-doc reconciliation follows
the green code head and therefore changes the final PR head; Full CI + Docker must run
again on that final docs head before Notion REVIEW evidence or readiness/merge.

---

## 2026-08-12 — P0 initial fact-create raw provenance convergence completed

```text
Parent Truth Foundation:       #50 · OPEN / reopened after fresh residual
Tracking issue:                #290 · CLOSED_COMPLETED
Implementation PR:             #291 · MERGED
Final pre-merge head:          701e382cbd5fc08fc0d8475569bdeef7bc5fc673
Protected squash merge/main:   7a47f5dbb786fe267093857bf370fd03703207ac
Merge parent:                  902b2b6335b05f9a6f956e75151a8e801f23ba1d
Pre-merge Full CI:             31574822654 · SUCCESS
Pre-merge Docker:              31574822650 · SUCCESS
Ready aggregate:               31575538209 · SUCCESS
Post-merge Full CI:            31575663761 · SUCCESS
Post-merge Docker:             31575663848 · SUCCESS
Post-merge aggregate:          31575663733 · SUCCESS
Submitted reviews:             0
Codex code review:             NOT RUN — USAGE LIMIT
Unresolved review threads:     0
Documentation impact:          GITHUB_AND_NOTION · FINAL read-back confirmed
```

Current main closes initial `raw_*` provenance for single/batch creation and replacement
fact creation without reinterpreting non-raw fact lineage. A fresh post-merge inventory
then found the separate smart-KB build authority residual #292; #50 was explicitly
reopened. That residual does not invalidate #290/#291.

---

## 2026-08-11 — P0 raw provenance post-create convergence completed

```text
Parent Truth Foundation:       #50 · OPEN / reopened after fresh residual
Tracking issue:                #288 · CLOSED_COMPLETED
Implementation PR:             #289 · MERGED
Exact tested head:             784038006edf76a145bae405b6a3822de88535a5
Protected squash merge/main:   902b2b6335b05f9a6f956e75151a8e801f23ba1d
Merge parent:                  615201ec1073dafb047028e88ce94463f4ef9b77
Exact-head Full CI:            31547334551 · SUCCESS
Exact-head Docker:             31547334516 · SUCCESS
Final ready aggregate:         31547915888 · SUCCESS
Post-merge Full CI:            31547943296 · SUCCESS
Post-merge Docker:             31547943295 · SUCCESS
Post-merge aggregate:          31547943289 · SUCCESS
Submitted reviews:             0
Codex code review:             NOT RUN — USAGE LIMIT
Unresolved review threads:     0
Documentation impact:          GITHUB_AND_NOTION · FINAL read-back confirmed
```

`SQLiteGraphStore.link_raw_to_fact()` is current-main canonical ownership for first raw
provenance binding on an already-existing unbound fact. First binding is guarded and
atomic with VersionStore pre-image, `l0_fact_provenance` and AuditChain evidence;
same-source retry is idempotent, conflicting second source fails closed, and legacy
`RawMemoryStore.link_fact()` no longer owns an independent canonical UPDATE.

The merge briefly auto-closed parent #50, but a fresh current-main residual inventory
immediately found the separate initial-create bypass tracked as #290. #50 was explicitly
reopened; that correction is intentional authority state, not a rollback of #289.

---

## 2026-08-11 — Causal Truth-edge convergence completed

```text
Parent Truth Foundation:       #50 · OPEN
Tracking issue:                #286 · CLOSED_COMPLETED
Implementation PR:             #287 · MERGED
Exact tested head:             0ce3ce41e2873040167443171a2f4ca332c63647
Protected squash merge/main:   615201ec1073dafb047028e88ce94463f4ef9b77
Exact-head Full CI:            31481226935 · SUCCESS
Exact-head Docker:             31481226883 · SUCCESS
Ready aggregate:               31482185643 · attempt 2 · SUCCESS
Post-merge Full CI:            31482420553 · SUCCESS
Post-merge Docker:             31482420582 · SUCCESS
Post-merge aggregate:          31482420624 · SUCCESS
Submitted reviews:             0
Unresolved review threads:     0
Documentation impact:          GITHUB_AND_NOTION · FINAL read-back confirmed
```

`CausalGraph` / `relations` is bounded causal mutation ownership.
`RelationStore` / `fact_relations` remains separate, NetworkX remains read-only, and
Neo4j/Graphiti remain derived. Automatic inference is pending-by-default and derived
reload is non-destructive. This merge granted no runtime or production authority.

---

## 2026-08-10 — Archival canonical claim convergence completed

```text
Parent Truth Foundation:       #50 · OPEN
Tracking issue:                #284 · CLOSED_COMPLETED
Implementation PR:             #285 · MERGED
Exact tested head:             8cd409e3a3a927e23e4bf7c581d9086cb2393829
Protected squash merge/main:   3100952f3dacf268f4d9c9b3f5a738f449663de6
Exact-head Full CI:            31405276475 · SUCCESS
Exact-head Docker:             31405282608 · SUCCESS
Exact-head aggregate:          31406163119 · SUCCESS
Post-merge Full CI:            31406541015 · SUCCESS
Post-merge Docker:             31406540630 · SUCCESS
Post-merge aggregate:          31406540411 · SUCCESS
Submitted reviews:             0
Codex:                         NOT RUN — USAGE LIMIT
Unresolved review threads:     0
Independent review:            NOT CLAIMED
Documentation impact:          GITHUB_AND_NOTION · FINAL read-back confirmed
```

`MemoryArchival` is eligibility/filesystem/reporting coordination only. Canonical
archival claim rewrite is owned by the narrow `CanonicalArchivalRewriter` over existing
`SQLiteGraphStore` transaction/evidence primitives. The filesystem/SQLite boundary is
honest: payload first, Canon second; cleanup failure can leave only non-canonical orphan
residue, never canonical success.

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

`CanonicalPiiRedactor` is implementation truth for PII claim redaction. The
privacy-history exception sanitizes affected `fact_versions.claim` values instead of
re-persisting removed plaintext PII. This does not claim complete Article 17 erasure from
all possible storage surfaces; durable physical erasure remains separate.

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
readiness. Truth Foundation #50 is CLOSED_COMPLETED on current main `c80c8d47588de3d2607c7e1b10aa1677eb84383f` after merged
#293, green post-merge evidence and a fresh residual inventory with `REAL_GAP=0`. Merged
#288/#289, #290/#291 and #292/#293 are current-main Truth Foundation history. Issue #249
stays separate. Open #53 is downstream architecture, not an automatic next implementation
authorization. No schema v8, Phase II, ADAO, ARM-04, runtime activation, standing Operator
GO, runtime authority or production authority follows from this closure.
