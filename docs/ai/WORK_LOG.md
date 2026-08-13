# 🧾 AI Engineering Work Log

Re-verify exact SHAs, PR state and workflow conclusions before continuing work.
Older detail remains traceable in Git history, merged PRs, issues, ADRs and dated checkpoints.

---

## 2026-08-13 — Phase 2A capability registry · DRAFT / FINAL REVIEW CANDIDATE

```text
main:                         51058f2d5662edfdb91b037a46dce9297c441a1b
main signature:               VERIFIED / valid
#50:                          CLOSED_COMPLETED · final REAL_GAP=0
#53:                          OPEN
#299:                         OPEN · ADMITTED_FOR_BOUNDED_IMPLEMENTATION
#300:                         OPEN · DRAFT · NOT MERGED
#300 base:                    main@51058f2d5662edfdb91b037a46dce9297c441a1b
pre-WORK_LOG candidate head:  50ed8c68110feae34d2a914ab503562315016f4f
Codex exact-head review:      NOT RUN — USAGE LIMIT
Continuity:                   12/12
schema:                       v7
runtime enabled:              false
Operator GO:                  false
runtime authority:            false
production authority:         false
```

The #297/#298 foundation closure is complete. Phase 2A was admitted separately through
#299; admission is not runtime authorization.

Fresh owner audit confirmed that `core/policy_kernel.py` already owns effective policy,
network/remote-data limits, local-only Canon policy and capability leases.
`core/provider_catalog.py` remains the console-facing LLM model catalogue. Existing
QueryRouter/pipeline, compute-profile, TRACE/Audit, Canon/ESM, TruthGate/WriteGate and
remote-egress ownership remain unchanged.

Draft PR #300 adds an **unwired metadata contract** only:

- stable provider/capability descriptors;
- capability-specific declared `data_mode` forwarded to PolicyKernel;
- explicit provider health: UNKNOWN / HEALTHY / DEGRADED / UNAVAILABLE;
- deterministic selection/no-selection with separate health and policy reason codes;
- trace-ready explanation metadata without TRACE persistence;
- remote metadata cannot hide required network access;
- malformed typed metadata fails closed;
- policy exceptions and mixed policy snapshots fail closed.

### Authority-bypass self-review finding and fix

Self-review found that the early candidate accepted an arbitrary `CapabilityLeaser` in the
registry constructor for testability. That would have left a future production extension
point where a caller could supply an allow-all substitute instead of the real PolicyKernel.
This was treated as a blocking authority defect and removed before Ready.

The final candidate contract now has:

```text
CapabilityRegistry()
    → mandatory get_policy_kernel()
    → no policy/leaser constructor injection
```

Tests replace the module-level lookup with `unittest.mock.patch` only inside the test
process. This is not a production extension point. The same self-review also moved
`data_mode` to capability scope, preserves health reason independently of policy reason,
validates booleans/enums, and keeps policy-snapshot TOCTOU fail-closed.

The relevant ADR, operations contract, `COMPONENT_MAP.md`, AI README route and
`PHASE2A_CAPABILITY_REGISTRY.md` are aligned to this owner model.

### Review evidence

A Codex review was requested on ancestor head
`009e5fbc11b03fd4033c939ae04ff0a8835e797b`, but Codex returned
`NOT RUN — USAGE LIMIT`. This is neither approval nor a finding. No independent formal
approval is claimed or required by the active solo ruleset.

The candidate changed after that request because the local authority-bypass audit found
and fixed the constructor injection surface. Therefore the Codex request is ancestor
metadata only, not final-head review evidence.

The branch head immediately before this WORK_LOG update is
`50ed8c68110feae34d2a914ab503562315016f4f`; this documentation commit itself advances the
branch. Fresh Full CI and Docker on the new exact head are mandatory. Green ancestor runs
must not be reused as final proof.

### Notion synchronization

The existing `Velantrim Titan 9.0` page contains a Phase 2A REVIEW-STAGE block. No new
Notion page was created. After the new exact head completes CI/Docker, refresh that same
block with exact evidence and the constructor-injection fix, then read it back before
Ready.

---

## 2026-08-13 — #297 / #298 foundation closure · FINAL

```text
#297 hardening merge:            c96b734b94f30e1d96e8bcb992dec429bda5c8fd
#297 review threads:             13/13 RESOLVED
#297 READY aggregate:            #914 · 31725868065 · SUCCESS
#297 post-merge Full CI:         #1085 · 31725945373 · SUCCESS
#297 post-merge Docker:          #705 · 31725945362 · SUCCESS
#298 truth reconciliation merge: 51058f2d5662edfdb91b037a46dce9297c441a1b
#298 exact-head Full CI:         #1086 · 31729146690 · SUCCESS
#298 READY aggregate:            #920 · 31729778909 · SUCCESS
#298 post-merge Full CI:         #1087 · 31729908579 · SUCCESS
#298 post-merge aggregate:       #921 · 31729908264 · SUCCESS
```

The active solo ruleset requires zero approving reviews, review-thread resolution and the
`Titan aggregate merge evidence` status check. Independent review must not be invented.

---

## Next safe order

```text
fresh exact-head Full CI + Docker
→ verify PR head unchanged and review threads = 0
→ refresh same-page Notion review evidence + read-back
→ mark Ready
→ require fresh READY aggregate on unchanged head
→ protected squash merge
→ post-merge main/signature/CI/Docker/aggregate verification
→ FINAL GitHub + same-page Notion reconciliation
→ close #299 only after all acceptance evidence is satisfied
```

Never infer schema v8, Continuity 13/12, runtime enablement, Operator GO, runtime authority
or production authority from Phase 2A.
