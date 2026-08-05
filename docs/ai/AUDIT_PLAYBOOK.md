# 🔍 AI Audit Playbook

This playbook defines a context-efficient audit method for Velantrim Titan. The goal is
not to read every file. The goal is to obtain enough verified evidence to make a
reliable conclusion without losing the architecture in a large context window.

## 1. Establish the exact object under review

Record before reading deeply:

- repository and default branch;
- exact base commit SHA;
- PR number and exact head SHA, if applicable;
- whether the PR is stacked and what its base branch is;
- changed files;
- current check conclusions;
- whether the question concerns `main`, an open PR, research, or a running instance.

Never mix facts from an open branch into the state of `main`.

## 2. Read the orientation layer

Read in order:

1. root `README.md`;
2. `SYSTEM_OVERVIEW.md`;
3. root `AGENTS.md`;
4. `docs/ai/CURRENT_STATE.md`;
5. relevant section of `docs/ai/COMPONENT_MAP.md`;
6. relevant risks and recent work-log entries.

Stop reading general documentation when the affected component and authority boundary
are clear.

## 3. Define the audit claim

Convert broad requests into testable questions. Examples:

- “Is this production-ready?” becomes separate questions about authentication,
  concurrency, persistence, failure recovery, deployment contract, observability, and
  supply-chain reproducibility.
- “Does this preserve legacy behavior?” becomes a differential input/output contract.
- “Is this end-to-end?” requires a real producer, runtime caller, lifecycle owner,
  consumer, and observed result—not only typed fixtures.
- “Is this safe?” requires a threat model and failure-path evidence, not only happy-path
  tests.

## 4. Trace authority before implementation detail

For every changed component, identify:

```text
input producer
→ contract
→ decision owner
→ mutation or output authority
→ durable state
→ downstream consumers
→ operator visibility
```

Flag:

- a second owner for an existing decision;
- inferred data being treated as user attestation;
- read paths that mutate Canon;
- projection or advisory code gaining answer/write/action authority;
- policy failures that degrade to permissive behavior;
- broad exceptions that convert failure into success or empty output.

## 5. Inspect the real diff and downstream consumers

Do not rely on a PR summary alone.

For changed enums, protocols, dataclasses, schemas, public return objects, environment
flags, migrations, and route responses:

1. inspect the exact diff;
2. search every consumer and serializer;
3. inspect exhaustive maps and `match`/`if` branches;
4. inspect tests for old and new behavior;
5. inspect any UI/API schema that mirrors the contract.

Example pattern:

```text
new enum member
→ search all mappings
→ require exhaustive mapping test
→ verify safe unknown-value failure
```

## 6. Separate five maturity questions

For each feature, report independently:

| Question | Evidence |
|---|---|
| Implemented? | file/function exists at exact SHA |
| Tested? | focused tests and their result |
| Wired? | production/runtime caller exists |
| Enabled? | selected profile/config activates it |
| Observed? | runtime health, metrics, logs, or trace evidence |

Never collapse these into “works”.

## 7. Verify tests and CI honestly

Check:

- what paths trigger the workflow;
- which Python versions run;
- exact lint/type-check scope;
- whether coverage is executed and enforced;
- whether tests were skipped after an earlier failing step;
- whether the check ran on the PR head or a synthetic merge commit;
- whether dependency resolution is locked and reproducible;
- whether stacked child PRs contain fixes missing from their parents.

A green child PR does not make a red parent independently mergeable.

## 8. Audit failure and recovery paths

At minimum consider:

- process crash before and after commit;
- timeout and cancellation;
- duplicate delivery and replay;
- stale lease or stale CAS snapshot;
- concurrent writers;
- database busy/locked, disk full, corruption, and missing migration state;
- provider/network denial;
- restart with accumulated backlog;
- erasure while derived state or work items remain;
- configuration drift between documented profiles.

For background workers, verify lifecycle owner, bounded work, backoff, shutdown,
operator metrics, and reconciliation.

## 9. Review stacked PRs in checkpoints

For a large dependency stack:

- review architecture contracts before implementation;
- require each parent PR to be independently green;
- place review gates where authority first changes;
- do not approve only the top aggregate diff;
- rebase upward after fixes are moved to the lowest owning PR;
- compare the final aggregate against `main` after the stack is clean.

## 10. Produce an evidence table

Use a compact format:

| Finding | Evidence | Impact | Confidence | Required action |
|---|---|---|---|---|

Mark assumptions and distinguish:

- confirmed defect;
- latent integration defect;
- missing evidence;
- design trade-off;
- documentation drift;
- future recommendation.

## 11. Update the context pack

After significant work:

- update `CURRENT_STATE.md` only for verified status changes;
- update `KNOWN_RISKS.md` with narrowed or closed proof;
- add a concise `WORK_LOG.md` entry with commit/PR references;
- update `COMPONENT_MAP.md` if ownership or first-read paths changed;
- add or amend an ADR for durable architecture decisions.

## Audit completion criteria

An audit is complete enough for a decision when it states:

- exact scope and SHA;
- what is proven and what is not;
- authority and runtime wiring;
- tests/checks actually observed;
- highest-impact defects and missing evidence;
- a prioritized, minimal next-action sequence;
- documentation freshness caveats.
