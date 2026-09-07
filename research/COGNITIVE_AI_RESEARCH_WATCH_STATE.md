# Cognitive AI Research Watch State

**Status:** RESEARCH PROCESS STATE ONLY · DOCS ONLY · NO RUNTIME / CANON / TRUTHGATE / POLICY / PRODUCTION AUTHORITY

## Purpose

Keep cognitive-AI monitoring delta-oriented and evidence-aware without turning external research into adoption, implementation, or authorization.

## Current watch boundary

- `last_checked_at`: 2026-09-07
- `topics_checked`:
  - GraphRAG / graph retrieval
  - temporal memory
  - long-lived agents
  - Emotional RAG / affective cognition
  - sparse / neuro-inspired architectures
  - cognitive architectures
  - agent memory
  - retrieval efficiency
- `papers_seen`: maintained in review outputs / intake notes; do not infer adoption from presence here
- `papers_promoted_for_review`: only items with a concrete Titan/Velantrim question and bounded evaluation path
- `papers_rejected`: retain only when useful to avoid repeated review
- `reason_for_rejection`: insufficient evidence, duplicate mechanism, no bounded owner, no measurable gap, or authority-risking framing

## Delta rule

Future research watches should prioritize work published or materially updated after `last_checked_at`.

Older work may re-enter review only when there is a meaningful delta such as:

- peer-review acceptance;
- public code or benchmark release;
- independent replication;
- correction / retraction;
- negative result;
- material revision;
- new comparative evaluation.

Repeated discovery without a material delta is not a new finding.

## Evidence-strength classification

Each significant external item should be classified as one of:

- `PEER_REVIEWED_RESULT`
- `PREPRINT_WITH_REPRODUCIBLE_EVIDENCE`
- `AUTHOR_REPORTED_RESULT`
- `INDEPENDENT_REPLICATION`
- `NEGATIVE_RESULT`
- `CONCEPTUAL_PROPOSAL`

The classification describes evidence maturity, not truth or authority.

## Research-to-adoption ladder

```text
PAPER_FOUND
-> PAPER_VERIFIED
-> RESULT_CLASSIFIED
-> LIMITATIONS_RECORDED
-> VELANTRIM_RELEVANCE_IDENTIFIED
-> OWNER_PROJECT_IDENTIFIED
-> HYPOTHESIS_CREATED
-> BOUNDED_EXPERIMENT
-> LOCAL_EVIDENCE
-> INDEPENDENT_REVIEW
-> EXPLICIT_ADOPTION_DECISION
-> IMPLEMENTATION
-> TESTS
-> INTEGRATION_EVIDENCE
-> AUTHORIZATION
```

Skipping directly from a paper or benchmark to implementation, Canon, production, or authority is out of bounds.

## Required report shape

For a significant work, record at minimum:

- title / date / publication status;
- what is new;
- benchmark/models/datasets/baselines when available;
- what is actually shown;
- separate author claims;
- what is not shown;
- limitations;
- Velantrim relevance;
- potential owning project;
- authority impact: `NONE` unless separately and explicitly authorized;
- safe next step: observe / reproduce / benchmark / bounded experiment / no action.

## Non-conflation

```text
research result != adopted mechanism
adopted mechanism != implemented mechanism
implemented mechanism != tested mechanism
tested mechanism != integrated mechanism
integrated mechanism != authorized mechanism
benchmark success != universal validity
paper result != independent replication
retrieval improvement != evidence authority
graph retrieval != system of record
affective relevance != belief / identity / truth / authority
```

This file is a research-process marker only. It changes no runtime, project state, Canon, policy, product priority, or production authorization.
