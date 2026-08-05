## Summary

Describe what changed and why.

## Scope

- Base commit / parent PR:
- Components changed:
- Authority or runtime boundary changed: yes / no

## Evidence

- [ ] I inspected the real callers and downstream consumers.
- [ ] I ran the narrow focused tests for this component.
- [ ] I ran the relevant lint/type-check workflow.
- [ ] I recorded exact results, including skipped or failing steps.
- [ ] I distinguished implemented, tested, wired, enabled, and observed behavior.

## Safety and architecture

- [ ] No new Canon, policy, compute-routing, identity, projection, or action authority was introduced accidentally.
- [ ] Failure paths are fail-closed where required.
- [ ] New enum/schema/status members have exhaustive consumer coverage.
- [ ] Background work is bounded, cancellable, observable, and restart-safe.
- [ ] This PR is independently green; fixes are not deferred to a child stacked PR.

## Documentation synchronization

Follow [`docs/ai/DOCUMENTATION_SYNC_PROTOCOL.md`](../docs/ai/DOCUMENTATION_SYNC_PROTOCOL.md).
Do not remove this block; it is the hand-off contract for humans and AI agents.

- Documentation impact: `NONE` / `GITHUB_ONLY` / `GITHUB_AND_NOTION`
- GitHub documentation updated (paths, or `NOT_REQUIRED` with reason):
- GitHub contains the complete technical/audit context without Notion: `YES` / `NO`
- Notion access: `AVAILABLE` / `UNAVAILABLE` / `NOT_REQUIRED`
- Notion synchronization: `NOT_REQUIRED` / `PLANNED` / `HANDOFF_REQUIRED` / `SYNCED` / `BLOCKED_PRIVACY_OR_PERMISSION`
- GitHub hand-off path: `docs/ai/NOTION_HANDOFF.md#...` / `NOT_REQUIRED`
- Notion record (safe title, internal reference, or public URL):
- Decision / ADR reference:
- Historical note: what changed from the original plan, if anything?

For `GITHUB_AND_NOTION` work:

- an actor with Notion access updates both systems in the same work cycle;
- an actor without Notion access completes the GitHub record and creates a structured
  `HANDOFF_REQUIRED` item in `docs/ai/NOTION_HANDOFF.md`;
- no actor may claim `SYNCED` without verifying the intended Notion record;
- `BLOCKED_PRIVACY_OR_PERMISSION` is reserved for a real privacy, permission, or
  unresolved-target problem, not for the mere absence of a connector;
- implementation and architectural PRs remain draft until the required synchronization
  is verified.

After merge, add the final merge SHA, CI evidence, limitations, and deviations from the
original plan to the Notion record or active hand-off item.

### AI context files

For architecture, runtime wiring, deployment posture, or known-risk changes:

- [ ] `docs/ai/CURRENT_STATE.md` updated or not applicable with reason.
- [ ] `docs/ai/KNOWN_RISKS.md` updated or not applicable with reason.
- [ ] `docs/ai/COMPONENT_MAP.md` updated or not applicable with reason.
- [ ] `docs/ai/WORK_LOG.md` entry added or not applicable with reason.
- [ ] ADR added/updated for a durable architectural decision or not applicable with reason.
- [ ] Connectorless hand-off added/closed or not applicable with reason.

## Remaining limitations

List what this PR deliberately does **not** solve.
