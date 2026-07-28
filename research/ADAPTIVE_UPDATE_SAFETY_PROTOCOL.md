# 🧪 Adaptive Update Safety Protocol — Research Registry

**Status:** RFC candidate · shadow-only · no runtime wiring  
**Normative document:** `docs/RFC-0084_ADAPTIVE_UPDATE_SAFETY_PROTOCOL.md`  
**Source inspiration:** https://habr.com/ru/articles/1063406/

## Purpose

Preserve a reusable safety pattern for future adaptive Titan changes:

```text
candidate update
→ rehearsal corpus
→ new-capability evaluation
→ regression budget
→ stability window
→ explicit approval
→ versioned apply
→ immutable receipt
→ rollback
```

## Where it may apply

- `LearningPatch` evaluation;
- adaptive retrieval-policy proposals;
- skill promotion;
- lexical and intent-routing changes;
- ExperienceReplay proposals;
- future local model adaptation;
- derived projection changes.

## Current boundary

- no automatic learning;
- no direct Canon writes;
- no TruthGate or Guardian bypass;
- no direct Velum mutation;
- no runtime defaults changed;
- no Crystal runtime or grant-scope change;
- `PASS`, `STABLE` and `SHADOW_VALID` are not apply permission.

## Return triggers

Revisit this research item when at least one of the following becomes executable:

- LearningPatch receives a persistence or apply path;
- retrieval policies may change automatically;
- ExperienceReplay proposals may affect a projection;
- a skill can be promoted from observations;
- local model weights or adapters can be updated;
- an Operator-approved adaptive apply service is planned.

## Required next artifact

The first implementation PR, if approved, should add only typed shadow evaluator
contracts, deterministic validation and immutable receipts. It must not add an
`apply()` method or wire stable `/query`.
