# 🔄 Code ↔ Documentation ↔ Notion Sync Protocol

This protocol makes documentation synchronization part of the definition of done for
Velantrim Titan. A material change is not complete when only code has changed. The
implementation record, technical documentation, decision history, evidence, limitations,
and next actions must describe one coherent reality.

## 1. Roles of each surface

| Surface | Role | Authority |
|---|---|---|
| GitHub `main` code and tests | Executable implementation truth | Highest for implemented behavior |
| GitHub current-state docs and ADRs | Public technical contract, boundaries, risks, ownership | Must match verified `main` |
| Pull request | Change scope, evidence, review discussion, limitations | Proposal until merged |
| `docs/ai/WORK_LOG.md` | Concise engineering hand-off and chronology | Current operational history |
| `docs/ai/NOTION_HANDOFF.md` | Connectorless transfer queue | Public synchronization evidence, not runtime proof |
| Notion project hub | Deep rationale, intended function, rejected alternatives, roadmap and cross-project history | Strategy and decision history; never runtime proof |

Notion may explain **why** a capability was proposed or changed. It must not claim that
the capability is implemented, tested, wired, enabled, or observed unless GitHub
evidence at an exact SHA supports that statement.

## 2. GitHub completeness invariant

An AI agent without Notion access must still be able to understand the current project,
perform an audit, implement a change, verify evidence, and hand work to the next actor
from GitHub alone.

The following may never exist only in Notion:

- implemented behavior or a changed technical contract;
- a material audit or review finding;
- a known engineering, privacy, security, or authority risk;
- exact PR, SHA, test, CI, benchmark, or runtime evidence required for review;
- a durable architectural decision that changes implementation direction;
- an unresolved blocker or required engineering next action.

GitHub and Notion do not need sentence-for-sentence duplication. GitHub carries the
complete public technical and audit package. Notion carries deeper rationale, rejected
alternatives, roadmap, cross-project context, and historical evolution. Both preserve
the same decision-bearing facts, reality status, evidence, limitations, and next actions.

## 3. Documentation impact classes

Every PR must select one class.

**Narrow exception (trusted Dependabot only):** The aggregate merge-evidence gate may infer `NONE` for a trusted Dependabot PR when:
- Actor identity is `dependabot[bot]` with type `Bot` (GitHub API, not PR body text)
- All changed files are in the strict dependency-only allowlist: `uv.lock`, `requirements.txt`, `requirements-<fragment>.txt` (no `/`), `requirements/<filename>.txt` (exactly one level deep)
- No documentation-sensitive paths are present (workflows, actions, `pyproject.toml`, `.github/dependabot.yml`, governance docs)
- Human authors, unknown bots, spoofed identity text, and Dependabot PRs with mixed/sensitive paths remain fail-closed and must provide explicit metadata

Human-authored PRs and non-allowlisted Dependabot PRs continue to require explicit classification.

### `NONE`

Use only when behavior, contracts, architecture, operations, risks, user instructions,
and project intent are unchanged. The PR must state why no documentation update is
needed.

### `GITHUB_ONLY`

Use when the public technical record must change but no deeper project decision or
roadmap context is introduced. Examples include a focused bug fix, corrected command,
clarified failure mode, or narrowed known risk.

### `GITHUB_AND_NOTION`

Required when a change affects any of the following:

- architecture, ownership, authority, safety, privacy, or trust boundaries;
- a new technology, module, function, capability, or integration direction;
- runtime wiring, activation posture, deployment model, or operational workflow;
- a durable design decision with meaningful alternatives or trade-offs;
- product meaning, roadmap, grant/investor positioning, or cross-project boundaries;
- a previously documented plan that was implemented, rejected, replaced, or deferred;
- a material audit that changes engineering priorities or accepted risk.

## 4. Notion access states

| State | Meaning | Required action |
|---|---|---|
| `NOTION_AVAILABLE` | The current actor can access the intended Notion record | Update GitHub and Notion in the same work cycle |
| `HANDOFF_REQUIRED` | The current actor lacks Notion access | Complete GitHub and add a structured item to `NOTION_HANDOFF.md` |
| `SYNCED` | A connected actor verified GitHub evidence and updated Notion | Record the safe Notion reference and final evidence |
| `NOT_REQUIRED` | The change is correctly GitHub-only | State the reason in the PR |
| `BLOCKED_PRIVACY_OR_PERMISSION` | A real privacy, permission, or unresolved-target problem exists | Keep the PR draft and escalate the exact blocker |

A missing connector alone is not `BLOCKED_PRIVACY_OR_PERMISSION`.

## 5. Mandatory workflow

### Before editing

1. Read `AGENTS.md`, the AI context pack, accepted ADRs, and affected code.
2. Establish the exact base SHA and distinguish `main`, open PR, research, and legacy
   claims.
3. Read the related Notion record when the task is `GITHUB_AND_NOTION` and access is
   available.
4. When Notion is unavailable, continue from GitHub and plan a hand-off rather than
   abandoning the task.

### During analysis or implementation

1. Record material findings, decisions, assumptions, alternatives, and rejected paths.
2. Keep status language exact: `proposed`, `implemented`, `tested`, `wired`, `enabled`,
   and `observed` are separate claims.
3. Update public GitHub technical documents in the same branch when their contract or
   status changes.
4. Do not leave important conclusions only in chat, private scratchpads, or Notion.

### Before review

1. Update the relevant GitHub surfaces:
   - `CURRENT_STATE.md` for verified status changes;
   - `KNOWN_RISKS.md` for opened, narrowed, proven, or closed risks;
   - `COMPONENT_MAP.md` for ownership and first-read path changes;
   - `WORK_LOG.md` for significant work and hand-off;
   - an ADR/RFC for durable decisions;
   - other affected security, deployment, status, user, or research documents.
2. Complete the PR `Documentation synchronization` block.
3. Confirm that GitHub contains the complete public technical and audit context without
   requiring Notion.
4. For `GITHUB_AND_NOTION`:
   - with access: update the intended Notion record and mark `SYNCED` only after
     verification;
   - without access: add a structured `HANDOFF_REQUIRED` item to
     `docs/ai/NOTION_HANDOFF.md` and link it from the PR.
5. Keep implementation and architectural PRs draft until required synchronization is
   verified.

### After merge

For `GITHUB_AND_NOTION`, add or transfer:

- final PR number and merge SHA;
- final CI, tests, benchmark, and runtime evidence;
- what changed from the original plan;
- remaining limitations and follow-up work;
- the final synchronization status.

## 6. Required deep Notion record

A substantial Notion entry should contain:

1. **Problem / opportunity**
2. **Intended function**
3. **Decision and rationale**
4. **Alternatives rejected or deferred**
5. **Implementation or audit summary**
6. **Authority, safety, privacy, and Canon boundaries**
7. **Evidence: tests, CI, measurements, PR, issue, exact SHA**
8. **Reality status: proposed / implemented / tested / wired / enabled / observed**
9. **Known limitations**
10. **Difference from the initial plan**
11. **Next actions**

## 7. Connectorless hand-off

Use [`NOTION_HANDOFF.md`](NOTION_HANDOFF.md) when the originating actor cannot access
Notion. Each item must include the problem, findings, decision, alternatives, boundaries,
GitHub files, exact evidence, limitations, next actions, and intended Notion target.

The connected actor must verify the evidence rather than copying the hand-off blindly.
Only that actor may change the synchronization state from `HANDOFF_REQUIRED` to `SYNCED`.

## 8. Public/private boundary

Titan is public. Never copy private workspace notes, personal information, secrets,
private datasets, inaccessible URLs, or private cross-project content into GitHub. Use a
safe page title or internal reference where necessary. Privacy does not justify omitting
the public technical contract, evidence, limitations, or next actions.

## 9. Completion rule

```text
code or architecture changed
  + focused tests and CI evidence
  + complete public GitHub technical/audit record
  + direct Notion synchronization or structured connectorless hand-off
  + final links, SHA, limitations, and status recorded
= change complete
```

A checked box without corresponding content is not synchronization. A Notion plan is
not implementation evidence. A merged implementation with stale public documentation is
not a finished change.
