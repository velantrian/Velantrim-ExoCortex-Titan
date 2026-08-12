# 🧾 AI Engineering Work Log

Re-verify exact SHAs, PR state and workflow conclusions before continuing work.

This file is a compact current hand-off. Older details remain traceable in Git history,
merged PR bodies, issues, ADRs and dated checkpoint documents.

---

## 2026-08-12 — P0 initial fact-create raw provenance convergence in protected review

```text
Parent Truth Foundation:       #50 · OPEN / reopened
Tracking issue:                #290 · OPEN
Implementation PR:             #291 · DRAFT / REVIEW-STAGE
Authoritative base main:       902b2b6335b05f9a6f956e75151a8e801f23ba1d
Branch:                        p0/initial-raw-provenance-create-convergence
Implementation/test head:      927972c39c167098f2424fe64b99e45744e6e035
Focused provenance tests:      9/9 PASS · diagnostic run 31574307055
Exact-head Full CI:            31574249831 · SUCCESS
Exact-head Docker:             31574249775 · SUCCESS
Submitted reviews:             0 at pre-doc reconciliation
Unresolved review threads:     0 at pre-doc reconciliation
Documentation impact:          GITHUB_AND_NOTION · REVIEW sync pending final candidate
Continuity:                    12/12 = 100% · unchanged
Schema:                        v7 · unchanged
Runtime currently enabled:     false · unchanged
Operator GO:                   false · unchanged
Runtime authority:             false · unchanged
Production authority:          false · unchanged
```

Fresh post-#289 current-main inventory found one separate residual: initial fact creation
could establish a `raw_*` `derived_from` pointer without the first-binding provenance
evidence that #289 added to the explicit post-create linker. Because `derived_from` also
carries GIST → VERBATIM fact lineage, the bounded candidate does not globally strip the
field.

The #291 review candidate verifies a `raw_*` parent and appends
`l0_fact_provenance` inside the same parent FACT_CREATED SQLite transaction for new facts.
Existing durable pointers win over incoming generic upsert data; non-raw lineage remains
unchanged. Batch create and `supersede_fact_cas()` use the same parent-create rule. A new
fact has no predecessor, so no artificial VersionStore pre-image or second FACT_UPDATED
event is created. Missing raw/evidence/audit failure is fail-closed and rolls back the
owning transaction.

The original exact-head CI failure on `599e4fb61a03b00971bfc06f597d7b2eca2ac61a`
was reproduced with an isolated diagnostic workflow: the new regression test held a
collection-time `WriteStatus` Enum object while the full suite exercised import isolation,
so identity compared against a different live module instance even though both rendered
`WriteStatus.CREATED`. The test now resolves `WriteStatus` lazily at assertion time and
keeps strict identity semantics. No production behavior, xfail, skip, coverage threshold
or assertion meaning was weakened.

AI truth-doc reconciliation follows the green implementation head and intentionally
changes the final PR head; Full CI + Docker must therefore run again on the final docs
head before Notion REVIEW evidence or readiness/merge. #249 remains separate. Parent #50
must remain OPEN until protected merge, post-merge verification and a fresh residual
current-main inventory establish whether `REAL_GAP = 0`.

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
readiness. Truth Foundation #50 remains OPEN while #290/#291 is review-stage and until a
fresh post-merge residual inventory proves no other meaningful canonical mutation gap
remains. Merged #288/#289 is current-main post-create provenance truth. Issue #249 stays
separate. No schema v8, Phase II, ADAO, ARM-04, runtime activation, standing Operator GO,
runtime authority or production authority follows from the current review block.
