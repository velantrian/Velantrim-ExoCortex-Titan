# 🧾 AI Engineering Work Log

Re-verify exact SHAs, PR state and workflow conclusions before continuing work.

This file is a compact current hand-off. Older details remain traceable in Git history,
merged PR bodies, issues, ADRs and dated checkpoint documents.

---

## 2026-08-10 — P0 causal Truth-edge convergence in protected review

```text
Parent Truth Foundation:       #50 · OPEN
Tracking issue:                #286 · OPEN
Implementation PR:             #287 · DRAFT / REVIEW-STAGE
Exact audited base main:       3100952f3dacf268f4d9c9b3f5a738f449663de6
Branch:                        p0/causal-relation-canonical-convergence
Documentation impact:          GITHUB_AND_NOTION
Continuity:                    12/12 = 100% · unchanged
Schema:                        v7 · unchanged
Runtime currently enabled:     false · unchanged
Operator GO:                   false · unchanged
Runtime authority:             false · unchanged
Production authority:          false · unchanged
```

### Ownership result

Fresh current-main audit separated the graph surfaces before implementation:

- `CausalGraph` / SQLite `relations`: **canonical causal Truth-edge surface** and the
  real residual #50 mutation gap selected for #286/#287;
- `RelationStore` / `fact_relations`: separate associative strength/LTP/LTD model;
  explicitly not merged into causal Canon;
- optional NetworkX Graph Lab: SELECT-only bounded in-memory analytics;
- optional Neo4j causal persistence: downstream/derived persistence, never remote Canon.

The audit also found that pre-#286 automatic callers could write
`knowledge_status="inferred"` while inheriting `truth_status="validated"` and
`review_state="approved"`. Proposal/inference and accepted truth are now an explicit
review-boundary concern.

### Candidate #287 contract

On the review branch, `CausalGraph` is the candidate one durable mutation owner for
`relations` create/batch/remove/reset. The intended successful mutation unit uses:

- existing WriteGate before durable mutation;
- deterministic relation/status/source/confidence validation;
- existing AuditChain schema prepared before the relation transaction;
- one caller-owned `BEGIN IMMEDIATE` SQLite transaction;
- forward + required inverse rows in one atomic create unit;
- per-physical-row `causal-relation:<relation_id>` AuditChain lifecycle evidence in the
  same transaction;
- rollback of relation rows if audit append fails;
- true duplicate idempotency returning the durable existing relation ID with no false
  audit event;
- automatic/non-manual inference defaulting to `hypothesis/pending` unless a stronger
  accepted status is supplied explicitly.

KB-generated writes/deletes and admin/pipeline resets are being routed through this owner.
The old test-only `create_inverse=False` half-edge escape hatch is rejected for canonical
writes. Snapshot import is treated as local admission input, not remote truth authority.

No relation VersionStore, schema-v8 migration, generalized second write protocol,
background loop or remote Canon is introduced.

### Evidence status

A previous review head proved Docker success but Full CI exposed exactly one blocking
mypy type-contract error in `core/causal_graph.py`; the exact Actions log identified the
problem as `float(object)`. The branch narrowed the confidence type annotation while
preserving fail-closed runtime validation. New exact-head CI/Docker evidence is required
again after all subsequent code/docs commits; earlier runs are not final evidence.

Real-SQLite adversarial coverage on the branch includes:

- forward + inverse + audit atomic commit;
- forced create-audit failure rollback;
- durable-ID duplicate idempotency / no false audit;
- automatic inference pending-by-default and excluded from approved reads;
- explicit accepted-label preservation;
- targeted remove + inverse + audit;
- forced remove-audit rollback;
- remove-miss no-op / no false audit;
- audited full reset;
- structural removal of KB/admin raw relation mutation ownership;
- NetworkX read-only boundary.

### Review boundary

PR #287 remains candidate implementation only until its final exact head has green Full
CI and Docker, review-stage Notion synchronization is written/read back, the PR is marked
ready, `Titan aggregate merge evidence` succeeds, review threads are resolved, and the
protected merge uses that exact expected head. Post-merge Full CI/Docker/aggregate plus a
FINAL Notion read-back are still required before this block reaches 100%.

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