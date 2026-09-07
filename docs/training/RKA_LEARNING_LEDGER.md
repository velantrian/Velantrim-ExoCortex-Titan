# Retrieval & Knowledge Augmentation — Learning Ledger

**Status:** TRAINING PROGRESSION STATE ONLY · NOT CANON · NOT IDENTITY/BELIEF STORE · NOT PROJECT RUNTIME STATE · NOT PRODUCTION AUTHORITY

**State verified in this training workflow:** 2026-09-07

## Progress semantics

`SESSION_PRESENTED != SESSION_COMPLETED`.

A session is `COMPLETED` only when all of the following are true:

1. explanation done;
2. concept check answered;
3. concept check reviewed;
4. bounded applied exercise completed;
5. applied exercise reviewed;
6. weak/strong points updated;
7. safe next topic identified.

Do not advance automatically from `IN_PROGRESS`, `NOT_ANSWERED`, or `NOT_REVIEWED`. If the learner explicitly asks to move on, preserve the skipped work as `SKIPPED_BY_USER` / `SKIPPED_BY_USER_FOR_NOW`; do not silently rewrite it as completed.

Confirmed `COMPLETED` state must not regress without an explicit reason.

## Current ledger

### RKA-001

- `session_id`: RKA-001
- `module`: retrieval_foundations
- `topic`: corpus_boundary
- `status`: SKIPPED_BY_USER
- `explanation`: COMPLETED
- `concept_check_status`: SKIPPED_BY_USER_FOR_NOW
- `concept_check_result`: NOT_REVIEWED
- `exercise_status`: SKIPPED_BY_USER_FOR_NOW
- `exercise_result`: NOT_REVIEWED
- `assessment`: NOT_AVAILABLE
- `weak_points`: UNKNOWN
- `strong_points`: UNKNOWN
- `next_topic`: segmentation

RKA-001 may be revisited later for a short control check. Its skipped status must not be represented as mastery.

### RKA-002

- `session_id`: RKA-002
- `module`: retrieval_foundations
- `topic`: segmentation
- `status`: IN_PROGRESS
- `explanation`: PRESENTED
- `concept_check_status`: AWAITING_ANSWER
- `concept_check_result`: null
- `exercise_status`: NOT_COMPLETED
- `exercise_result`: null
- `weak_points`: UNKNOWN
- `strong_points`: UNKNOWN
- `next_topic`: indexing

`indexing` remains locked while RKA-002 is `IN_PROGRESS`, unless the learner explicitly asks to skip it; in that case RKA-002 must be marked `SKIPPED_BY_USER`, not `COMPLETED`.

## Program order

1. corpus boundary;
2. segmentation;
3. indexing;
4. lexical / vector / hybrid retrieval;
5. recall and ranking metrics;
6. RAG: query transformation, reranking, context assembly, grounding, evaluation;
7. structured memory;
8. cognitive memory;
9. provenance and evidence chains;
10. contradiction detection / classification / resolution, revision, reopening;
11. agentic RAG;
12. authorization and governance.

## Training-fixture discipline

Artificial Velantrim examples must be labelled one of:

- `[HYPOTHETICAL EXAMPLE]`;
- `[TRAINING FIXTURE]`;
- `[SIMULATED STATE]`.

A real project-state claim requires an explicit live check of the owning source and must distinguish roles such as `VERIFIED_CURRENT`, `VERIFIED_HISTORICAL`, `PROPOSED`, `OPEN_PR`, `DRAFT`, `MERGED`, `AUTHORIZED`, and `NOT_AUTHORIZED` as applicable.

## Retrieval / authority invariants

```text
retrieval != evidence
memory != truth
graph != Canon
claim != evidence
confidence != evidence
implementation != tests
tests != integration evidence
integration evidence != authorization
CI green != semantic correctness
CI green != production authorization
readable source != authoritative source
historical source != current state
open PR != merged state
merged state != production authorization
AVAILABLE_SOURCE != CORPUS_MEMBER != RELEVANT_RESULT != EVIDENCE != CURRENT_TRUTH != AUTHORIZATION
```

For segmentation, preserve a critical qualifier with its claim whenever splitting them could invert or overstate meaning. Typical atomic semantic envelopes include:

- claim + scope;
- claim + negation;
- result + limitation;
- current state + authorization state;
- implementation + production boundary;
- historical defect + fixed/superseded status.

This file records learning progression only. It does not authorize any product, architecture, runtime, Canon, TruthGate, policy, memory, or deployment change.
