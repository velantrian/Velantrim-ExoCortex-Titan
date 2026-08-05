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

Do not add vague statements such as “everything works”. Distinguish implementation,
tests, runtime wiring, enablement, and observation.

---

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
- PR #146 is textually mergeable but `mergeable_state: unstable`.
- The failing `Continuity contracts` run stops at mypy with an optional assignment error
  in `core/continuity/advisory_shadow.py`; continuity tests are skipped after that fail.
- PR #147 contains a behavior-neutral typing fix that should be moved to #146.
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

1. make PR #146 independently green and move its typing fix down from #147;
2. close the `DEFER_PATH` consumer gap and add exhaustive enum tests in #144;
3. add differential legacy-compatibility tests for #144;
4. rebase and independently review the Continuity stack;
5. close projection runtime delivery in staged operational PRs;
6. quarantine and redesign Identity rather than patching the legacy store;
7. continue CI, deployment, concurrency and supply-chain hardening.
