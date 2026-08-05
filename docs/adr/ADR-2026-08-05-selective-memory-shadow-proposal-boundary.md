# ADR — ARM-03 Selective-Memory Shadow Proposal Boundary

- **Status:** Accepted for PR #200 review
- **Date:** 2026-08-05
- **Scope:** `core/selective_memory_candidates.py` and
  `ENABLE_SELECTIVE_MEMORY_CANDIDATE_SHADOW`
- **Decision owner:** human maintainer / repository architecture policy

## Context

Titan needs a bounded way to evaluate which statements from a conversation might be
useful as future memory candidates. The old PR #102 explored a deterministic shadow
extractor but was based on stale `main` and left several safety contracts unresolved.

The primary architectural risk is authority confusion:

```text
candidate extraction
→ mistaken for memory admission
→ mistaken for Canon or truth
→ silent query-path persistence
```

A feature flag and a class named `CandidateExtractionPolicy` are intentionally detected
by the architecture-freeze guard. Their authority must therefore be explicit before the
code may merge.

## Decision

ARM-03 owns only a **bounded proposal-generation policy**.

```text
source text
→ exact bounded spans
→ local candidate classification
→ sensitivity / injection checks
→ redacted immutable proposals
→ offline or shadow evaluation receipt
→ no write
```

`CandidateExtractionPolicy` may decide only:

- input/output budgets;
- minimum and maximum candidate length;
- whether credentials are rejected;
- whether instruction-shaped memory injection is rejected;
- whether sensitive candidate payloads are redacted;
- extractor and policy version identity.

It may not decide:

- whether a statement is true;
- whether a user confirmed it;
- whether it should be retained durably;
- whether it enters Working Memory or Canon;
- whether a conflict is resolved;
- whether an answer, reminder, tool or action is authorized.

## Feature-flag boundary

`ENABLE_SELECTIVE_MEMORY_CANDIDATE_SHADOW` is default off.

Flag off:

```text
run_shadow_extraction
→ returns before candidate extraction
→ no model/network/database work
→ no write
→ legacy behavior unchanged
```

Flag on grants permission only to execute the local proposal extractor through the
explicit diagnostic entrypoint. It grants no persistence, admission, response or action
authority.

ARM-03 is not wired into `/query` and does not add a worker, queue or startup task.

## Evidence and provenance

Each proposal carries exact source offsets and a SHA-256 span hash. Raw exact source text
may remain inside protected in-process evidence for offset verification, but portable
output must use the explicit safe serializer with redaction.

`extraction_confidence` measures structural extraction confidence only. It is not truth
confidence, reliability, salience or admission probability.

`POSSIBLE_UPDATE_OF` is a deterministic within-input hint. It is not a durable
supersession relation and cannot mutate an existing record.

## Security boundary

Bounded English/Russian instruction patterns detect examples of prompt-to-memory
injection, including requests to ignore prior instructions, remember permanently, write
to Canon, disable safety checks or bypass gates. Default disposition is rejection with
security/high-risk markers.

This detection is a conservative heuristic, not a complete semantic security system.
Later model-assisted detection, if proposed, requires a separate ADR and must remain
outside admission authority.

## Alternatives considered

### Direct extraction → Canon

Rejected. It collapses proposal, evidence, admission and truth authority.

### Query-time synchronous admission

Rejected. It adds latency and hidden mutation to a read path.

### LLM-first extraction

Deferred. It adds provider, cost, prompt-injection and reproducibility concerns before a
deterministic baseline is evaluated.

### Store whole conversations as memory

Rejected as the ARM-03 default. It violates selective retention and expands privacy
exposure.

### Remove the feature flag and policy class to satisfy CI

Rejected. The correct response to the architecture guard is an explicit authority
contract, not renaming or hiding the surface.

## Consequences

Positive:

- exact proposal-only authority is reviewable;
- flag-off behavior remains cheap and deterministic;
- privacy-safe portable evidence has an explicit contract;
- future ARM-04 cannot claim implicit approval from ARM-03.

Costs:

- no user-visible memory benefit yet;
- heuristic extraction requires evaluation;
- source evidence and redaction require careful caller discipline;
- admission needs a separate design and operator decision.

## Promotion gates

ARM-04 is prohibited until a separate PR and ADR define:

- trusted subject/context ownership;
- candidate precision and false-retention evaluation;
- privacy, consent, erasure and revocation behavior;
- WorkingMemoryGate disposition;
- explicit Write Gate and audit receipt;
- no query-path implicit write;
- operator approval.

## Rollback

Disable the feature flag or remove the diagnostic caller. Because ARM-03 has no durable
writes, no memory rollback or migration is required.
