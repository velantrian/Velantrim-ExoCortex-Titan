# 🔬 PR #243 — Research Intake and Future-Idea Normalization

**Status:** `DRAFT · DOCS-ONLY · GITHUB_AND_NOTION`  
**Base:** `main@a9b269903cd29448714aa985295b67cdb5fe64cf`  
**Pull request:** #243  
**Runtime authority:** none  
**Canon / ESM / TruthGate authority:** none

## Intent

Preserve useful future ideas discovered during audits and architecture conversations
without confusing them with accepted implementation work or allowing them to disappear
in chat history.

## Decision

Use one explicit intake boundary:

```text
verified current defect or accepted missing proof
→ active engineering risk / issue / bounded PR

unproven future architecture or capability
→ research intake card
→ research registry
→ measurable return trigger
```

Research Mode remains visible and traceable but has no runtime, write, answer, compute,
reminder, tool, action or policy authority.

## GitHub changes

- add `research/IDEA_INTAKE_PROTOCOL.md`;
- update `research/README.md` with the classification route;
- update `research/FUTURE_COMPONENTS.md` with triaged candidate tracks and explicit
  return triggers.

## Current engineering items deliberately excluded from Research Mode

- issue #234 branch-ruleset enforcement;
- deterministic Continuity admission evaluator and rule registry;
- admission-aware facade and current authorization/privacy/erasure checks;
- query-path read-only proof and Canon-writer unification;
- projection lifecycle and operational metrics;
- durable operational observability, security review and documentation synchronization.

These already have accepted owners and concrete completion criteria.

## Initial preserved research candidates

- server storage profile evolution;
- ANN/vector projection profiles;
- multi-node / HA deployment;
- policy-driven retrieval coordination;
- operator Assurance Console;
- user-visible Continuity/reminder/action proposals;
- Native Kernel-aligned substrate profiles;
- meta-causal/invariant world model;
- evidence-bound persona and identity candidates.

Each candidate remains `R0` or parked until its documented return trigger is satisfied.

## Documentation synchronization

```text
Documentation impact:   GITHUB_AND_NOTION
Notion access:           AVAILABLE
Notion synchronization: SYNCED
Notion record:           Titan Research Intake & Future Ideas Registry
Notion page ID:          3b5ac84d-0547-815a-8a62-d13568323e99
```

The Notion child page under the Titan Hub mirrors classification lanes, candidate IDs,
current-engineering exclusions, promotion path, return triggers and non-authority
boundaries. Final CI and merge SHA remain post-review/post-merge evidence.

## Explicit non-scope

- no production code, tests, dependencies, migrations or workflows;
- no Continuity evaluator, facade, persistence or runtime wiring;
- no query, startup, worker or scheduler change;
- no PostgreSQL, vector database, ANN or distributed implementation;
- no identity, reminder, delivery, tool or action activation;
- no change to `5/12 = 41.7%` Continuity readiness;
- no claim that any preserved candidate is accepted architecture.

## Review criteria

1. Current engineering debt is not hidden in Research Mode.
2. Every future candidate has an explicit return trigger.
3. Candidate names remain Titan-native and external systems remain prior art.
4. Research stages do not imply implementation, wiring, enablement or observation.
5. Notion mirrors the same decision-bearing facts without becoming runtime proof.
