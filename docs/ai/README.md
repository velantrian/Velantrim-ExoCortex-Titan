# 🤖 AI Agent Context Pack

This directory is the **first orientation layer** for AI coding agents, auditors,
reviewers, and future maintainers working on Velantrim Titan.

It exists to reduce blind repository-wide scanning. It is a map, not a substitute for
inspecting current code, tests, workflows, configuration, and runtime evidence.

> **Documentation is orientation, not proof.** For every material claim, verify the
> current implementation, locate its callers, inspect tests and CI, and distinguish
> proposed, implemented, tested, wired, enabled, and observed behavior.

## Required reading order

Read only the minimum context needed, in this order:

1. [`../../README.md`](../../README.md) — product purpose and public maturity claim.
2. [`../../SYSTEM_OVERVIEW.md`](../../SYSTEM_OVERVIEW.md) — high-level architecture.
3. [`../../AGENTS.md`](../../AGENTS.md) — mandatory rules for agents changing code.
4. [`DOCUMENTATION_SYNC_PROTOCOL.md`](DOCUMENTATION_SYNC_PROTOCOL.md) — mandatory
   GitHub and Notion synchronization contract.
5. [`CURRENT_STATE.md`](CURRENT_STATE.md) — verified snapshot of what is in `main`
   and what remains only in open PRs or research documents.
6. [`../state/project_state.json`](../state/project_state.json) — machine-readable
   SHA roles, Continuity readiness, governance state and KB preservation boundary.
7. [`AUDIT_AND_FUTURE_WORK.md`](AUDIT_AND_FUTURE_WORK.md) — durable audit queue,
   evidence anchors, revalidation triggers, authorization boundaries and safe continuation
   procedure. **Ledger order is audit order, not implementation authorization.**
8. [`COMPONENT_MAP.md`](COMPONENT_MAP.md) — component owners, key files, tests, and
   authority boundaries.
9. [`KNOWN_RISKS.md`](KNOWN_RISKS.md) — unresolved engineering and governance risks.
10. [`AUDIT_PLAYBOOK.md`](AUDIT_PLAYBOOK.md) — how to audit without exhausting context.
11. [`WORK_LOG.md`](WORK_LOG.md) — recent significant work, decisions, and hand-offs.
12. [`NOTION_HANDOFF.md`](NOTION_HANDOFF.md) — structured synchronization queue when
    the current actor cannot access Notion.

Then open only the component-specific code, tests, ADRs, PRs, and workflow logs needed
for the current task.

## Source-of-truth order

When sources disagree, use this order for implementation/runtime claims:

1. executable code at the exact commit under review;
2. tests and current CI results;
3. runtime configuration and observed health/metrics;
4. current-state documentation and accepted ADRs;
5. PR descriptions and work-log entries;
6. historical audits, journals, and archived documents.

For semantic project-state questions, follow the repository-local declared owner. In the
current architecture, `docs/state/project_state.json` is the machine-readable project-state
surface; accepted ADRs or explicit contracts may own narrower semantic decisions. Re-query
GitHub before treating any recorded SHA or lifecycle status as current.

`COLLAB_JOURNAL.md`, old audits, and `docs/archive/` are valuable history, but they are
not automatically current truth.

## SHA role rule

Do not call the latest implementation-bearing merge the current repository head when a
later documentation-only commit exists. Use the explicit fields from
`docs/state/project_state.json`:

```text
repository_head_sha_at_verification
implementation_baseline_sha
documentation_checkpoint_sha
```

The first field is an exact observed checkpoint, not an evergreen claim. Re-query
GitHub before treating it as the current head.

## GitHub must work without Notion

Direct Notion access is useful but cannot be assumed. The repository must contain the
complete public technical and audit continuity required to:

- establish current state at an exact SHA;
- inspect authority and safety boundaries;
- reproduce material findings;
- locate known risks and required next actions;
- continue implementation or review.

No implemented contract, material audit finding, known risk, exact evidence,
architectural decision, blocker, or required next action may exist only in Notion.

### Actor with Notion access

```text
analyze or implement in GitHub
→ update public technical and AI context documents
→ update deeper Notion rationale/history
→ verify evidence and mark SYNCED
```

### Actor without Notion access

```text
analyze or implement from GitHub
→ complete the public technical and AI context record
→ add HANDOFF_REQUIRED to NOTION_HANDOFF.md
→ connected actor verifies evidence and updates Notion
→ mark SYNCED
```

A missing connector is `HANDOFF_REQUIRED`, not a generic blocker.

## Task-specific routes

| Task | Read next |
|---|---|
| Canon, ESM, promotion, truth | `COMPONENT_MAP.md#canon-and-promotion` plus Truth/Promotion ADRs |
| Projection outbox or FTS | `COMPONENT_MAP.md#projection-delivery` and `KNOWN_RISKS.md#risk-p0-01` |
| Continuity PR stack | `CURRENT_STATE.md` plus current PR diffs/checks |
| Capability/provider registry or Phase 2A #299/#300 | `PHASE2A_CAPABILITY_REGISTRY.md`, the Phase 2A ADR, then exact PR evidence |
| Embedding-space identity or Phase 3A #327/#328 | `PHASE3A_EMBEDDING_SPACE_IDENTITY.md`, the Phase 3A ADR, then exact PR evidence |
| Code Structural Memory Stage C / PR #335 | `CSM_STAGE_C_SCANNER.md`, `../adr/ADR-2026-08-15-csm-stage-c-explicit-scanner.md`, then exact PR evidence |
| Knowledge-base graph or release asset | `../knowledge/KB_GRAPH_GOVERNANCE.md`, `scripts/validate_kb_graph.py`, `scripts/audit_kb_graph.py` |
| Identity or personalization | `CURRENT_STATE.md#identity-layer` and the identity risk entry |
| API/security/deployment | `SECURITY.md`, compose files, Dockerfile, server lifespan, current checks |
| General audit / future work | `AUDIT_AND_FUTURE_WORK.md` → `AUDIT_PLAYBOOK.md`, then only the relevant evidence owner |
| New module, technology, or durable decision | `DOCUMENTATION_SYNC_PROTOCOL.md`, affected ADRs, and the related Notion record or connectorless hand-off |
| No Notion connector | `NOTION_HANDOFF.md` and the connectorless procedure in the sync protocol |

## Context-budget rule

Do not load the entire repository or every historical audit by default. Prefer:

```text
orientation pack
→ current-state + future-work ledger
→ affected component map
→ current diff / callers
→ focused tests and CI
→ wider search only when evidence demands it
```

The goal is not to fit the whole repository into one prompt. The goal is to preserve
architecture, provenance, and unresolved work while spending context on the files that can
actually change the conclusion.

## Update obligation

Any PR that materially changes architecture, runtime wiring, authority boundaries,
production posture, project direction, or a known risk must update the relevant files in
this directory.

At minimum:

- update `CURRENT_STATE.md` when status changes;
- reconcile `AUDIT_AND_FUTURE_WORK.md` when a future-work state, evidence anchor,
  authorization boundary, or revalidation trigger changes;
- update `KNOWN_RISKS.md` when a risk is opened, narrowed, proven, or closed;
- add a concise entry to `WORK_LOG.md` for significant work;
- update `COMPONENT_MAP.md` when ownership or key paths change;
- add or amend an ADR for a durable architectural decision;
- update `docs/state/project_state.json` only when its governed SHA/readiness/governance
  semantics actually change; do not advance schema merely because a new module exists;
- classify the PR as `NONE`, `GITHUB_ONLY`, or `GITHUB_AND_NOTION`;
- update Notion directly or add a structured `HANDOFF_REQUIRED` item when required.

Do not record unverified claims, test counts copied from old runs, or aspirational
features as current runtime behavior.
