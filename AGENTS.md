# 🤖 Velantrim Titan repository guidance

This file is the mandatory entry point for AI coding agents and automated reviewers.
It applies to the entire repository unless a more local `AGENTS.md` narrows the rules.

## 0. Fast path for project status

If the task is about **overall project status, maturity, progress, remaining work,
roadmap, next steps, or continuation/handoff**, read this first:

1. [`docs/project_status/FOR_AI.json`](docs/project_status/FOR_AI.json)
2. Live GitHub state for any PR, SHA, check, or branch that can change the answer.
3. Only the task-specific files required for verification or continuation.

Do **not** read [`docs/project_status/FOR_HUMAN.md`](docs/project_status/FOR_HUMAN.md)
for an AI status task unless the user explicitly asks for the human-facing narrative or
the wording of that document is itself under review.

This is a context-budget rule, not an authority rule. `FOR_AI.json` is orientation only:
it is not Canon, runtime evidence, merge authority, production authorization, or an
evergreen remote-state claim.

For status-only tasks, this fast path supersedes the general reading order below until
additional context is actually required.

## 1. Read before auditing or changing code

For code changes, audits, or architecture work that need broader context, read in this order:

1. [`docs/ai/README.md`](docs/ai/README.md) — AI context-pack manifest and task routes.
2. [`SYSTEM_OVERVIEW.md`](SYSTEM_OVERVIEW.md) — high-level system architecture.
3. [`README.md`](README.md) — public purpose and maturity claim, only when public/product framing matters.
4. [`docs/ai/DOCUMENTATION_SYNC_PROTOCOL.md`](docs/ai/DOCUMENTATION_SYNC_PROTOCOL.md)
   — GitHub and Notion definition of done.
5. [`docs/ai/CURRENT_STATE.md`](docs/ai/CURRENT_STATE.md) — verified `main`, open-PR,
   research and legacy status.
6. Relevant section of
   [`docs/ai/COMPONENT_MAP.md`](docs/ai/COMPONENT_MAP.md).
7. Relevant risks in [`docs/ai/KNOWN_RISKS.md`](docs/ai/KNOWN_RISKS.md).
8. Recent relevant entries in [`docs/ai/WORK_LOG.md`](docs/ai/WORK_LOG.md).
9. [`docs/ai/AUDIT_PLAYBOOK.md`](docs/ai/AUDIT_PLAYBOOK.md) for audit work.
10. [`docs/ai/NOTION_HANDOFF.md`](docs/ai/NOTION_HANDOFF.md) when a required Notion
    synchronization cannot be completed directly.

Then inspect only the affected code, callers, tests, ADRs, PRs and workflows. Do not
load every historical audit or the entire repository unless the evidence requires it.

> Treat documentation as an orientation map, not as proof. Verify material claims at
> the exact commit or PR head under review.

## 2. Source-of-truth order

When sources disagree:

1. executable code at the exact SHA;
2. tests and current CI results;
3. runtime configuration and observed health/metrics;
4. accepted current-state documentation and ADRs;
5. PR descriptions and work-log entries;
6. historical journals, audits and archived documents.

Never treat an open PR or research document as behavior already present in `main`.

## 3. Required status language

For every significant component, distinguish:

- **proposed** — design or research exists but is not merged implementation;
- **implemented** — code exists;
- **tested** — focused tests exist and their result is known;
- **wired** — a production/runtime caller exists;
- **enabled** — the selected profile activates it;
- **observed** — a running instance produced evidence.

Do not replace these with an unqualified statement that a feature “works”.

## 4. Verification

For Python changes, run the narrowest relevant checks first, then the repository gates
that cover the changed surface.

Baseline commands:

```bash
ruff check core/ --output-format=github
mypy core/ --show-error-codes
python -m pytest tests/ -v --tb=short --timeout=300 -x
```

Also run component-specific workflows/tests for changed contracts. Treat branding,
repository-hygiene, architecture-freeze, CI, and Docker workflow failures as blocking.

Do not claim coverage enforcement unless CI actually invokes a blocking coverage
command. Do not claim static-analysis coverage for paths not included in the command.

## 5. Review rules

### Canonical memory boundary

- Flag any query, retrieval, ranking, answering, continuity, advisory, projection, or
  background read path that mutates Canon, epistemic state, relations, activation
  history, or canonical policy state.
- The safe read-side result is evidence or a typed proposal. Durable mutation requires
  an explicit canonical write service and its required transaction/receipt contract.
- Do not create a second owner for promotion, compute routing, policy, or another
  established architectural decision.

### Policy and evidence integrity

- Flag fail-open behavior when policy, TruthGate, provenance, visibility, scope,
  capability, or evidence dependencies are unavailable.
- External or model-derived `WORLD_FACT` records require attributable provenance and
  evidence, remain unvalidated until an explicit transition, and must never be promoted
  by ordinary recall or repetition.
- Model inference is not user attestation. Inferred goals, preferences, identity, or
  commitments must remain typed candidates until the required confirmation/admission
  policy is satisfied.

### Atomic writes and rebuildable projections

- Flag changes that can commit a Canon mutation without its required `VersionStore`
  pre-image, `AuditChain` event, CAS protection, or active outbox intent where the
  outbox-backed protocol applies.
- FTS, graph, vector, continuity, context, and advisory state are rebuildable or derived
  views. They must not override canonical restriction, deletion, archive, visibility,
  scope, or epistemic state.
- Projection application needs projection-specific policy, lease, version, scope and
  resource checks. Do not reuse Canon admission as a second decision over an already
  committed fact.

### Compute and public contracts

- When adding an enum member, schema field, dataclass property, status, route or event
  type, search all consumers, exhaustive maps, serializers, UI/API schemas and tests.
- Add exhaustive set-equality tests for static mappings where practical.
- For compatibility claims, use differential tests against the previous implementation
  with equivalent inputs; do not rely on one representative test.

### Background work

Any worker, scheduler or startup task must have:

- a single lifecycle owner;
- bounded batch and runtime;
- cancellation and clean shutdown;
- backoff/jitter under contention;
- idempotency or explicit at-least-once semantics;
- retry/park/dead-letter behavior;
- backlog, age, failure and version-lag observability;
- restart and reconciliation tests.

Do not fully drain an unbounded backlog synchronously before the service becomes
healthy.

### Identity and personal data

- Treat `core/identity_layer.py` as legacy/unwired until an accepted replacement
  protocol exists.
- Do not add new production callers or writes to it.
- Identity assertions require source modality, consent/scope, sensitivity,
  contestation, supersession, retraction and erasure semantics.
- Keep policy/mechanism evolution governance separate from individual identity-content
  admission.

## 6. Stacked PR rules

For stacked changes:

- record the dependency order;
- require every parent PR to be independently green;
- move fixes to the lowest PR that owns the defect;
- review checkpoints where authority or a live consumer first changes;
- rebase children after parent fixes;
- inspect the final aggregate diff against `main` before merge.

A green child PR does not repair a red parent.

## 7. Documentation and Notion synchronization obligation

Any PR that materially changes architecture, runtime wiring, authority boundaries,
deployment posture, project direction, or a known risk must update the relevant public
GitHub documentation:

- `docs/ai/CURRENT_STATE.md` for verified status changes;
- `docs/ai/KNOWN_RISKS.md` for opened, narrowed or closed risks;
- `docs/ai/COMPONENT_MAP.md` for ownership or first-read path changes;
- `docs/ai/WORK_LOG.md` for significant work and hand-off;
- an ADR/RFC for durable architectural decisions;
- any affected security, deployment, status, user, or research documents.

Every PR must follow
[`docs/ai/DOCUMENTATION_SYNC_PROTOCOL.md`](docs/ai/DOCUMENTATION_SYNC_PROTOCOL.md)
and classify its documentation impact as `NONE`, `GITHUB_ONLY`, or
`GITHUB_AND_NOTION`.

### GitHub completeness invariant

GitHub must contain enough public technical and audit context for an AI or human reviewer
to understand, verify, and continue the work without Notion access. Implemented behavior,
material findings, known risks, exact evidence, architectural decisions, blockers, and
required next actions must never exist only in Notion.

### When Notion is available

For `GITHUB_AND_NOTION`, update the corresponding Notion decision/history record in the
same work cycle. Include motivation, intended function, decision, alternatives, evidence,
exact reality status, limitations, PR, and final merge SHA.

### When Notion is unavailable

Do not abandon the task and do not claim that Notion was updated. Complete the GitHub
record, add a structured item to
[`docs/ai/NOTION_HANDOFF.md`](docs/ai/NOTION_HANDOFF.md), and set:

- `Notion access: UNAVAILABLE`;
- `Notion synchronization: HANDOFF_REQUIRED`;
- the exact GitHub hand-off path.

A connected human or AI must verify the GitHub evidence, update Notion, and mark the item
`SYNCED`. `BLOCKED_PRIVACY_OR_PERMISSION` is reserved for a real privacy, permission, or
unresolved-target problem, not merely the absence of a connector.

Do not expose private Notion content or private workspace URLs in this public repository.
A safe page title or internal reference may be used in the public PR.

Do not copy stale test counts or unverified PR claims into current-state documentation.
Use exact dates, SHAs, PR/issue numbers, evidence, and remaining limitations.

## 8. Change discipline

Before writing:

1. establish exact base/head SHA and task scope;
2. inspect current callers and tests;
3. choose the lowest-risk owning component;
4. preserve default-off/shadow-only boundaries unless activation is explicitly in scope;
5. make the smallest coherent change;
6. validate it;
7. update GitHub documentation and Notion or create a structured hand-off;
8. open a draft PR with evidence and remaining risks.

Do not silently merge unrelated cleanup, broad refactors, feature activation, or policy
changes into a focused fix.
