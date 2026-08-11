# 🧾 AI Engineering Work Log

Re-verify exact SHAs, PR state and workflow conclusions before continuing work.

This file is a compact current hand-off. Older details remain traceable in Git history,
merged PR bodies, issues, ADRs and dated checkpoint documents.

---

## 2026-08-11 — P0 raw provenance canonical convergence in protected review

```text
Parent Truth Foundation:       #50 · OPEN
Tracking issue:                #288 · OPEN
Implementation PR:             #289 · DRAFT / REVIEW-STAGE
Exact audited base main:       615201ec1073dafb047028e88ce94463f4ef9b77
Branch:                        p0/raw-provenance-canonical-convergence
Documentation impact:          GITHUB_AND_NOTION
Continuity:                    12/12 = 100% · unchanged
Schema:                        v7 · unchanged
Runtime currently enabled:     false · unchanged
Operator GO:                   false · unchanged
Runtime authority:             false · unchanged
Production authority:          false · unchanged
```

Fresh post-#287 inventory found one meaningful residual #50 family: raw provenance
binding. `SQLiteGraphStore.link_raw_to_fact()` changes canonical `facts.derived_from`
without VersionStore/AuditChain evidence, and legacy `RawMemoryStore.link_fact()` owns a
second direct SQL path. #289 is the bounded candidate: keep the existing SQLiteGraphStore
owner, make first binding guarded and evidence-atomic, reject conflicting second sources,
and reduce the legacy surface to a compatibility adapter.

No schema v8, Continuity expansion, runtime activation, new TruthGate or production
authority is part of this block. #249 remains separate. Parent #50 closes only if a fresh
post-merge current-main inventory proves `REAL_GAP = 0`.

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

`CausalGraph` / `relations` is current-main bounded causal mutation ownership.
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

`MemoryArchival` is now eligibility/filesystem/reporting coordination only. Canonical
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

`CanonicalPiiRedactor` is current-main implementation truth for PII claim redaction. The
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
readiness. Truth Foundation #50 remains OPEN while #286/#287 is review-stage and until a
fresh post-merge residual inventory proves no other meaningful canonical mutation gap
remains. Issue #249 stays separate.