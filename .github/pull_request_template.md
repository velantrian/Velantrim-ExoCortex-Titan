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
- Notion synchronization: `NOT_REQUIRED` / `PLANNED` / `DONE` / `BLOCKED`
- Notion record (safe title, internal reference, or public URL):
- Decision / ADR reference:
- Historical note: what changed from the original plan, if anything?

For `GITHUB_AND_NOTION`, the PR must remain draft until the Notion record contains the
motivation, intended function, decision, alternatives, evidence, exact reality status,
limitations, and PR link. After merge, add the final merge SHA to Notion.

### AI context files

For architecture, runtime wiring, deployment posture, or known-risk changes:

- [ ] `docs/ai/CURRENT_STATE.md` updated or not applicable with reason.
- [ ] `docs/ai/KNOWN_RISKS.md` updated or not applicable with reason.
- [ ] `docs/ai/COMPONENT_MAP.md` updated or not applicable with reason.
- [ ] `docs/ai/WORK_LOG.md` entry added or not applicable with reason.
- [ ] ADR added/updated for a durable architectural decision or not applicable with reason.

## Remaining limitations

List what this PR deliberately does **not** solve.
