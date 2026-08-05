# 🧾 AI Engineering Work Log

This is the concise hand-off log for architecture-significant work. New entries go at
the top. It is not a replacement for Git history, PR discussion, ADRs, or current code.

For older collaboration history, see [`../../COLLAB_JOURNAL.md`](../../COLLAB_JOURNAL.md).
Treat old journal claims as historical until re-verified.

## Entry template

```markdown
## YYYY-MM-DD — Short title

**Scope:** PR/issue/commit/component

### Verified before change
- exact facts and SHAs

### Changed
- files and behavior

### Validation
- commands/checks and exact outcomes

### Decisions
- accepted boundaries and rejected alternatives

### Remaining
- prioritized follow-up
```

Do not add vague statements such as “everything works”. Distinguish proposed,
implemented, tested, wired, enabled, and observed behavior.

---

## 2026-08-05 — Connectorless GitHub → Notion hand-off contract

**Scope:** PR #199; documentation/governance only; branch
`agent/documentation-sync-contract`

### Verified before change

- PR #199 was based on the current `main` checkpoint
  `bb87ea4f00a68581c2365e63f833a366e810289b` and did not require a rebase.
- The first synchronization draft treated missing Notion access as generic `BLOCKED`.
- Not every AI agent or reviewer can use a Notion connector, so that rule could stop a
  valid GitHub audit or leave material findings only in chat.

### Changed

- added `docs/ai/NOTION_HANDOFF.md` as the structured connectorless transfer queue;
- established the GitHub completeness invariant: implemented contracts, material
  findings, risks, evidence, decisions, blockers, and next actions may not exist only in
  Notion;
- defined `NOTION_AVAILABLE`, `HANDOFF_REQUIRED`, `SYNCED`, `NOT_REQUIRED`, and
  `BLOCKED_PRIVACY_OR_PERMISSION`;
- updated `AGENTS.md`, the AI context index, synchronization protocol, and PR template;
- required explicit Notion access, synchronization status, and GitHub hand-off path.

### Validation

- documentation/governance-only diff;
- no runtime, Canon, policy, compute, projection, identity, deployment, dependency, or
  test-baseline change;
- full repository CI is required before merge.

### Decisions

- absence of a connector is `HANDOFF_REQUIRED`, not a generic blocker;
- a connectorless actor completes the GitHub analysis and public technical record;
- a connected actor verifies evidence, updates Notion, and marks the item `SYNCED`;
- `BLOCKED_PRIVACY_OR_PERMISSION` is reserved for a real privacy, permission, or
  unresolved-target problem;
- GitHub and Notion synchronize decision-bearing facts without duplicating every
  paragraph.

### Remaining

- run full Titan CI on the final head;
- synchronize the updated connectorless decision into the Titan Notion protocol record;
- merge PR #199 only after green checks and final Notion evidence;
- consider a separately reviewed CI parser for PR synchronization fields.

## 2026-08-05 — Code, GitHub documentation, and Notion synchronization contract

**Scope:** documentation/governance only; branch `agent/documentation-sync-contract`

### Verified before change

- `AGENTS.md` already required AI agents to update current-state, risk, component-map,
  work-log, and ADR documentation for material changes.
- The PR template already contained an AI-context checklist.
- The Titan Notion hub already recorded substantial GitHub changes, but the repository
  did not define one explicit impact taxonomy or a mandatory deep-rationale record.

### Changed

- added `DOCUMENTATION_SYNC_PROTOCOL.md` as the common definition of done;
- defined `NONE`, `GITHUB_ONLY`, and `GITHUB_AND_NOTION` impact classes;
- required Notion records for new technologies, modules, durable decisions, roadmap,
  cross-project, authority, deployment, and product-meaning changes;
- required exact PR/SHA, status, evidence, limitations, alternatives, and post-merge
  reconciliation;
- expanded `AGENTS.md`, the AI context index, and the PR template so coding agents must
  perform or explicitly hand off the synchronization rather than silently omit it.

### Validation

- documentation-only consistency review;
- no runtime code, Canon path, policy path, dependency, deployment, or test baseline
  changed.

### Decisions

- GitHub `main` code and tests remain implementation truth.
- GitHub docs remain the compact public technical contract.
- Notion stores deeper rationale, intended function, rejected alternatives, project
  history, and cross-project context.
- Private Notion content and workspace URLs must not be copied into public GitHub.

### Remaining

- CI enforcement of machine-readable PR fields may be added separately after workflow
  policy is reviewed against fork and permission behavior.

## 2026-08-05 — AI context navigation and audit hand-off

**Baseline:** `main` at `024454e5ee17a52f6de321e6917bf29eb5cc88ca`  
**Documentation branch:** `agent/ai-context-navigation`

### Purpose

Create a compact, mandatory reading route so AI agents can understand Titan's
architecture, current status, recent work, and unresolved risks before scanning the
repository or changing code.

### Added or updated

- expanded root `AGENTS.md` into the mandatory coding-agent contract;
- added `docs/ai/README.md` as the AI start page and reading order;
- added `docs/ai/CURRENT_STATE.md` to separate `main`, open PRs, research and legacy
  code;
- added `docs/ai/COMPONENT_MAP.md` for authority owners, first files and first tests;
- added `docs/ai/AUDIT_PLAYBOOK.md` for context-efficient evidence-driven audits;
- added `docs/ai/KNOWN_RISKS.md` as an actionable risk/proof register;
- added this concise work log;
- linked the AI context pack from the public README;
- added a PR checklist requiring relevant AI context updates for architectural changes.

### Verified findings captured

#### Continuity stack

- PRs #131–#147 remain a draft stacked series outside `main`.
- No formal independent review was recorded in the inspected PRs.
- PR #146 is textually mergeable but its independent historical validation was not
  sufficient for direct stack merge.
- PR #147 contains a behavior-neutral typing fix that belongs in #146.
- PR #144 changes more than an optional argument: it adds `DEFER_PATH`, strict input
  validation, immutable/slotted result contracts, tuple reasons, policy version and
  defer/rebuild fields.
- On the stack branch, `core/rapid_orientation.py::_cost_for_path()` omits
  `DEFER_PATH`; current call sites do not pass continuity signals, so the defect is
  latent until the natural wiring step.
- The stack has typed fixtures and a complete shadow runner, but no accepted live
  producer from conversation text to trusted goal/open-loop attestations.

#### Projection delivery

- transactional outbox, checkpoints, version-monotonic FTS apply and bounded dispatcher
  are in `main`;
- dispatcher is not called by startup, scheduler or a background lifecycle;
- the agreed implementation order is metrics → manual bounded dispatch → gated worker →
  reconciliation;
- projection synchronization should use its own apply gate rather than reusing Canon
  admission as a second epistemic decision.

#### Identity

- `core/identity_layer.py` is a legacy/unwired mutable store, not a production identity
  protocol;
- RFC-0084 can govern changes to an identity mechanism, but individual identity
  assertions require separate admission, reconciliation, contestation, retraction and
  erasure semantics.

#### Repository hardening

- two production-oriented compose profiles conflict;
- coverage is configured but not blocked in the main CI command;
- static analysis does not cover all runtime surfaces;
- dependency/build reproducibility remains incomplete;
- concurrency evidence is narrow rather than systemic;
- packaging differs between wheel and Docker runtime;
- server composition and shared-key authorization remain production limitations.

### Decisions

- AI documentation is an orientation map, never unverified truth.
- Current state and historical work are separate documents.
- The compact `docs/ai/` pack is read before component code; wider repository scans are
  evidence-driven.
- Significant architectural PRs must update the relevant current-state, risk, component
  and work-log entries.
- Existing `COLLAB_JOURNAL.md` remains historical; it is not duplicated or silently
  promoted to current truth.

### Remaining engineering order

1. rebuild the Continuity stack on current `main` rather than merging stale stacked
   branches directly;
2. move the Advisory typing fix to the layer that owns it;
3. close the `DEFER_PATH` consumer gap and add exhaustive enum tests;
4. add differential legacy-compatibility tests;
5. close projection runtime delivery in staged operational PRs;
6. quarantine and redesign Identity rather than patching the legacy store;
7. continue CI, deployment, concurrency and supply-chain hardening.
