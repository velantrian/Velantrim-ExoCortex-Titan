# 🔄 Code ↔ Documentation ↔ Notion Sync Protocol

This protocol makes documentation synchronization part of the definition of done for
Velantrim Titan. A material change is not complete when only the code has changed.
The implementation record, technical documentation, decision history, and remaining
limitations must describe the same reality.

## 1. Roles of each surface

| Surface | Role | Authority |
|---|---|---|
| GitHub `main` code and tests | Executable implementation truth | Highest for implemented behavior |
| GitHub current-state docs and ADRs | Technical contract, boundaries, risks, ownership | Must match verified `main` |
| Pull request | Change scope, evidence, review discussion, limitations | Proposal until merged |
| `docs/ai/WORK_LOG.md` | Concise engineering hand-off and chronology | Current operational history |
| Notion project hub | Deep rationale, intended function, rejected alternatives, roadmap, cross-project context | Strategy and decision history; never runtime proof |

Notion may explain **why** a capability was proposed or changed. It must not claim that
the capability is implemented, wired, enabled, or observed unless GitHub evidence at an
exact SHA supports that statement.

## 2. Documentation impact classes

Every PR must select one class:

### `NONE`

Use only for changes with no material effect on behavior, contracts, architecture,
operations, risks, user instructions, or project intent. Examples: typo-only edits or a
test refactor with no changed coverage claim. The PR must state why no documentation
change is needed.

### `GITHUB_ONLY`

Use when the technical record must change but no deeper project decision or roadmap
context is introduced. Typical examples: a focused bug fix, clarified failure mode,
updated command, corrected status, or narrowed known risk.

### `GITHUB_AND_NOTION`

Required when a change affects any of the following:

- architecture, ownership, authority, safety, privacy, or trust boundaries;
- a new technology, module, function, capability, or integration direction;
- runtime wiring, activation posture, deployment model, or operational workflow;
- a durable design decision with meaningful alternatives or trade-offs;
- product meaning, roadmap, grant/investor positioning, or cross-project boundaries;
- a previously documented plan that was implemented, rejected, replaced, or deferred.

## 3. Mandatory workflow for AI agents and contributors

### Before editing

1. Read `AGENTS.md`, the relevant AI context files, accepted ADRs, and affected code.
2. Read the related Notion decision or project page when access is available and the
   task is `GITHUB_AND_NOTION`.
3. Establish the exact base SHA and distinguish current `main` from open-PR or research
   claims.

### During implementation

1. Record material decisions, assumptions, alternatives, and rejected paths.
2. Keep status language exact: `implemented`, `tested`, `wired`, `enabled`, and
   `observed` are separate claims.
3. Do not postpone documentation until context has been lost.

### Before opening or updating the PR

1. Update the relevant GitHub documentation:
   - `CURRENT_STATE.md` for verified state changes;
   - `KNOWN_RISKS.md` for opened, narrowed, or closed risks;
   - `COMPONENT_MAP.md` for ownership and first-read path changes;
   - `WORK_LOG.md` for significant work and hand-off;
   - an ADR for durable architectural decisions.
2. Complete the `Documentation synchronization` block in the PR template.
3. For `GITHUB_AND_NOTION`, create or update the Notion record and include its title or
   URL when safe to expose in the repository.
4. If Notion is unavailable, mark the sync as `BLOCKED`, keep the PR as draft, and do
   not claim the task is fully complete.

### After merge

For `GITHUB_AND_NOTION`, update the Notion record with:

- final PR number and merge commit SHA;
- final status and verification evidence;
- what changed from the original plan;
- remaining limitations and follow-up work.

## 4. Required Notion change record

A substantial Notion entry should contain:

1. **Problem / opportunity** — what motivated the work.
2. **Intended function** — what the technology or module is meant to provide.
3. **Decision** — what was selected and why.
4. **Alternatives** — what was considered, rejected, or deferred.
5. **Implementation summary** — affected components and public contracts.
6. **Authority and safety boundary** — what the change is not allowed to do.
7. **Evidence** — tests, CI, measurements, PR, issue, and exact SHA.
8. **Reality status** — proposed / implemented / tested / wired / enabled / observed.
9. **Known limitations** — unresolved risks and deliberate exclusions.
10. **Next actions** — follow-up issues or decision points.

## 5. Public-repository privacy rule

Titan is public. Do not copy private Notion content, personal notes, secrets, or private
workspace URLs into public GitHub files or PRs. The PR may use an internal page title or
stable internal identifier instead of a URL. GitHub must still contain enough technical
information for an external reviewer to understand and verify the change.

## 6. Completion rule

```text
code changed
  + focused tests and CI evidence
  + GitHub technical docs synchronized
  + Notion rationale/history synchronized when required
  + final links, SHA, limitations, and status recorded
= change complete
```

A checked box without corresponding content is not synchronization. A Notion plan is
not implementation evidence. A merged implementation with stale documentation is not a
finished change.
