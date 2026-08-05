# 🔗 Notion synchronization hand-off queue

This file preserves a complete, public transfer package when an AI agent or contributor
can work in GitHub but cannot access the Titan Notion workspace.

A missing Notion connector is **not** a reason to abandon an audit, implementation, or
review. GitHub must remain sufficient to understand the technical state, verify evidence,
and continue the work.

## Access and synchronization states

| State | Meaning | Required action |
|---|---|---|
| `NOTION_AVAILABLE` | The current actor can read and update the intended Notion record | Synchronize GitHub and Notion in the same work cycle |
| `HANDOFF_REQUIRED` | The current actor cannot access Notion | Complete the GitHub record and add a structured item below |
| `SYNCED` | A connected human or AI verified the GitHub evidence and updated Notion | Record the safe Notion title/reference and final evidence |
| `NOT_REQUIRED` | The change is correctly classified as GitHub-only | State the reason in the PR |
| `BLOCKED_PRIVACY_OR_PERMISSION` | A real privacy, permission, or unresolved-target problem prevents safe synchronization | Keep the PR draft and escalate the exact blocker |

`HANDOFF_REQUIRED` is the normal connectorless state. Do not use
`BLOCKED_PRIVACY_OR_PERMISSION` merely because a connector is absent.

## GitHub completeness invariant

The following may never exist only in Notion:

- implemented behavior or a changed technical contract;
- a material audit or review finding;
- a known engineering, privacy, security, or authority risk;
- exact PR, commit, test, CI, benchmark, or runtime evidence required for review;
- an architectural decision that changes implementation direction;
- a required engineering next action or unresolved blocker.

GitHub and Notion do not need sentence-for-sentence duplication. GitHub carries the
complete public technical and audit package. Notion carries deeper rationale, rejected
alternatives, roadmap, cross-project context, and historical evolution. Both must retain
the same decision-bearing facts, exact status, evidence, limitations, and next actions.

## Connectorless actor procedure

1. Continue the audit or implementation from GitHub.
2. Update the affected technical documents and the relevant files under `docs/ai/`.
3. Record exact base/head SHA, PR or issue, tests, CI, limitations, and next actions.
4. Add a hand-off item below for work classified `GITHUB_AND_NOTION`.
5. Set the PR fields to:
   - `Notion access: UNAVAILABLE`;
   - `Notion synchronization: HANDOFF_REQUIRED`;
   - `GitHub hand-off path: docs/ai/NOTION_HANDOFF.md#<item-anchor>`.
6. Never claim that Notion was updated.
7. Keep an implementation or architectural PR draft until a connected actor verifies
   the evidence and records `SYNCED`.

Documentation-only work may be reviewed according to repository policy, but its Notion
status must still remain explicit and truthful.

## Connected actor procedure

1. Verify the hand-off against the current PR, exact SHA, repository state, tests, and CI.
2. Create or update the intended Notion record.
3. Preserve the problem, decision, alternatives, boundaries, evidence, limitations, and
   next actions.
4. Add a safe Notion title or internal reference to the PR and this item.
5. Change the item status to `SYNCED`.
6. After merge, add the final merge SHA, final CI evidence, deviations from the original
   plan, and remaining work.

## Privacy boundary

Titan is public. Do not copy private workspace notes, personal information, secrets,
private datasets, inaccessible URLs, or private cross-project material into this file.
Use a safe page title or internal reference when the Notion URL must remain private.

## Hand-off item template

Copy this section for each pending synchronization and place new items above older ones.

```markdown
## YYYY-MM-DD — Short title

- **Status:** `HANDOFF_REQUIRED` / `SYNCED` / `BLOCKED_PRIVACY_OR_PERMISSION`
- **Documentation impact:** `GITHUB_AND_NOTION`
- **Repository / PR / issue:**
- **Base SHA:**
- **Head SHA:**
- **Intended Notion record:** safe title or internal reference
- **Notion access for originating actor:** `UNAVAILABLE`

### Problem / opportunity

### Material findings

### Decision and rationale

### Rejected or deferred alternatives

### Authority, safety, privacy, and Canon boundaries

### GitHub files updated

### Evidence

### Known limitations

### Next actions

### Synchronization result

- Connected actor:
- Notion record:
- Status: `SYNCED`
- Final PR / merge SHA / CI:
```

## Queue

No pending hand-off items at the time this protocol was introduced. Future
connectorless actors must add items here rather than leaving material context only in a
chat transcript or private scratchpad.
