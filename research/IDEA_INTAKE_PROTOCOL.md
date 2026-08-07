# 🔬 Titan Research Intake Protocol

**Status:** `RESEARCH GOVERNANCE CONTRACT`  
**Runtime authority:** none  
**Canon / ESM write authority:** none  
**Initial baseline:** `main@a9b269903cd29448714aa985295b67cdb5fe64cf`  
**Updated:** 2026-08-07

This protocol prevents useful ideas from disappearing in chat, audit notes or temporary
AI context while also preventing speculative ideas from being presented as accepted
implementation work.

It is the entry boundary for ideas discovered during:

- repository audits and code review;
- architecture discussions;
- comparisons with external systems or other AI analyses;
- operator feedback and observed runtime limitations;
- cross-project discussions with Native Kernel, Crystal or Mentaury;
- future-looking product and cognitive-system design.

A research record preserves an idea. It does **not** approve it, prioritize it for the
current engineering queue or grant runtime authority.

## 1. First classification: where does the item belong?

| Lane | Use when | Canonical destination |
|---|---|---|
| `ENGINEERING_NOW` | a verified defect, accepted missing capability, governance gap or required production proof already follows from current architecture | `docs/ai/KNOWN_RISKS.md`, current hand-off, issue or bounded implementation PR |
| `RESEARCH_CANDIDATE` | the idea may be useful, but the design, owner, value, threat boundary or evidence trigger is not yet accepted | this protocol and `FUTURE_COMPONENTS.md` |
| `PARKED` | the idea is coherent but no measured trigger justifies spending implementation capacity | research registry with a return trigger |
| `REJECTED` | the idea conflicts with Titan invariants, duplicates an accepted owner or creates unacceptable authority/risk | research registry with the rejection reason |
| `SUPERSEDED` | a later Titan-native contract or implementation replaces the original idea | research history with the replacement reference |

### Items that are not Research Mode

The following are current engineering or hardening work and must not be hidden in a
future-ideas list:

- administrator enforcement of issue #234 (`main` ruleset / branch protection);
- deterministic Continuity admission evaluator and allowlisted rule registry;
- admission-aware facade and anti-bypass guards;
- current authorization, consent/lawful-basis, restriction, erasure and policy checks;
- query-path read-only enforcement and Canon-writer ownership unification;
- projection dispatcher lifecycle, reconciliation and operational metrics;
- durable operational observability, backup/recovery and incident evidence;
- security review, deployment hardening and documentation synchronization.

These items have current evidence, accepted boundaries and concrete completion criteria.
They belong in the active engineering plan even when implementation is staged.

## 2. Research maturity states

```text
INBOX
→ TRIAGED
→ R0 QUESTION
→ R1 CONTRACT
→ R2 OFFLINE PROTOTYPE
→ R3 SHADOW EVALUATION
→ PROMOTED TO ENGINEERING
```

An item may also become `PARKED`, `REJECTED` or `SUPERSEDED` from any stage.

| State | Meaning |
|---|---|
| `INBOX` | idea captured, not yet classified |
| `TRIAGED` | duplicate/owner/current-work check completed |
| `R0 QUESTION` | problem and hypotheses recorded; no accepted architecture |
| `R1 CONTRACT` | Titan-native interfaces, invariants and non-authority boundary defined |
| `R2 OFFLINE PROTOTYPE` | isolated deterministic prototype; no production caller |
| `R3 SHADOW EVALUATION` | bounded evaluation receipts and metrics; no user-visible authority |
| `PROMOTED TO ENGINEERING` | explicit decision moves one bounded slice into the active roadmap |
| `PARKED` | preserved with a return trigger, no active implementation |
| `REJECTED` | explicit reason records why the path should not proceed |
| `SUPERSEDED` | replaced by a newer accepted contract or implementation |

## 3. Mandatory research-card fields

Every candidate must record:

1. **ID and title** — stable Titan-native name, not an external product name.
2. **Origin** — audit, user idea, external prior art, benchmark or incident.
3. **Problem / opportunity** — what current limitation or future capability is involved.
4. **Current evidence** — exact SHA, metric, workload or `NONE`.
5. **Why this is research** — what is not yet known or accepted.
6. **Affected owners** — Canon, PolicyKernel, retrieval, Continuity, identity, storage,
   action, operator or cross-project boundary.
7. **Authority risks** — possible write, answer, compute, reminder, tool or action power.
8. **Privacy / erasure risks** — subject scope, retention, consent and deletion impact.
9. **Cheapest useful experiment** — offline and bounded by default.
10. **Return trigger** — measurable condition that justifies reopening the item.
11. **Promotion evidence** — criteria required before an engineering PR.
12. **Status and decision history** — including rejection or supersession reason.

An idea without a return trigger is a note, not an active research track.

## 4. Research admission checks

Before adding a new track, check:

```text
Does an accepted component already own this decision?
Is the item already current engineering work?
Is there a measured limitation or concrete future workload?
Can the first experiment remain offline and deterministic?
Can failure remain fail-closed?
Does the idea preserve Canon, policy and erasure authority?
Is there an explicit stop condition?
```

Do not create a new router, gate, memory owner, graph owner, policy root, identity path or
storage authority only because an external project uses one.

## 5. Promotion path

```text
captured idea
→ triage against current architecture
→ Titan-native research contract
→ licence / security / privacy / threat review
→ offline prototype
→ deterministic replay evaluation
→ shadow receipts and measured comparison
→ explicit architecture decision
→ bounded engineering PR
→ separate activation decision when authority changes
```

Promotion requires evidence that the current baseline cannot satisfy the target workload
or that the proposed approach produces a measured improvement without weakening safety,
privacy, determinism, local-first operation or replaceability.

## 6. Initial candidate set from the 2026-08-07 audit

These candidates are preserved without becoming current implementation commitments.

### `RT-STORAGE-01` — Server storage profile evolution

- **Status:** `R0 QUESTION · PARKED`.
- **Idea:** PostgreSQL or another transactional server profile behind a backend-neutral
  Canon contract, strict deployment Mode Lock and same-backend transactional outbox.
- **Why research:** SQLite is the accepted local profile and no measured Titan workload
  currently proves that a second Canon backend is required.
- **Return trigger:** sustained write contention, multi-node/HA requirement, remote
  multi-user deployment or a reproducible workload that violates the SQLite SLO.
- **Forbidden shortcut:** splitting Canon, audit and outbox across independent databases
  without an accepted transaction protocol.

### `RT-RETRIEVAL-01` — ANN / vector projection profiles

- **Status:** `R0 QUESTION · PARKED`.
- **Idea:** evaluate FAISS, HNSW, pgvector or service-based ANN as rebuildable projection
  profiles, never as truth owners.
- **Return trigger:** versioned corpus benchmark shows the existing lexical/dense path
  misses latency, memory or recall targets at a defined scale.
- **Promotion evidence:** cold/warm latency, recall, rebuild time, memory, model-version
  isolation, erasure propagation and lexical fallback.

### `RT-DISTRIBUTED-01` — Multi-node and high-availability deployment

- **Status:** `R0 QUESTION · PARKED`.
- **Idea:** leader/fencing, replication, migration, failover and reconciliation profile.
- **Return trigger:** an accepted deployment requires multiple live writers or an HA SLO.
- **Boundary:** no distributed complexity in the local-first default path.

### `RT-ROUTING-01` — Policy-driven retrieval coordination

- **Status:** `R0 QUESTION · PARKED`.
- **Idea:** reduce duplicated/orphaned routing decisions through one observable proposal
  contract without creating a second PolicyKernel or ComputeController.
- **Return trigger:** measured inconsistent routing, duplicated authority or benchmarked
  cost/latency loss in the current composition.

### `RT-ASSURANCE-01` — Operator Assurance Console

- **Status:** `R0 QUESTION`.
- **Idea:** one operator surface combining memory lineage, admission receipts, replay
  divergence, projection lag, erasure state and current authority boundaries.
- **Why research:** the UI must follow accepted durable read models; it must not invent a
  second Canon, admission gate or policy owner.
- **Return trigger:** durable read models and replay artifacts exist and operators need a
  coherent incident/review surface.

### `RT-CONTINUITY-01` — User-visible Continuity, reminders and action proposals

- **Status:** `R0 QUESTION · BLOCKED BY ENGINEERING PREREQUISITES`.
- **Idea:** bounded context continuity may eventually produce user-visible suggestions,
  reminders or action proposals.
- **Prerequisites:** evaluator, current authorization/privacy checks, facade, retention,
  replay, shadow evaluation, SLO, rollback and explicit Operator GO.
- **Boundary:** research cannot grant reminder, delivery, tool or action authority.

### `RT-SUBSTRATE-01` — Kernel-neutral substrate profiles

- **Status:** `R0 QUESTION`.
- **Idea:** align Titan persistence and compute profiles with Native Kernel contracts
  without making SQLite, PostgreSQL, embeddings, LLMs, CPU/GPU or a specific graph engine
  part of the Architecture Canon.
- **Return trigger:** a concrete cross-project integration slice with accepted ownership
  and compatibility tests.

### `RT-WORLDMODEL-01` — Meta-causal and invariant world model

- **Status:** `R0 QUESTION`.
- **Idea:** represent causes, motives, contradictions, invariants, uncertainty and
  unexplained relations beyond a single conventional logic formalism.
- **Cheapest experiment:** offline typed graph over a fixed evidence corpus with explicit
  provenance and comparison against current causal retrieval.
- **Boundary:** hypotheses remain proposals; similarity or graph connectivity is not
  truth, policy or action authority.

### `RT-IDENTITY-01` — Evidence-bound persona and identity candidates

- **Status:** `R0 QUESTION · PARKED`.
- **Idea:** model stable preferences, values, autobiographical evidence and persona
  continuity as contestable candidates rather than inferred identity facts.
- **Boundary:** model inference is not user attestation; no production caller may use the
  legacy identity layer as authority.
- **Return trigger:** an accepted identity admission, consent, correction, supersession,
  retraction and erasure protocol.

## 7. Review cadence

Review the registry only when:

- a return trigger becomes true;
- a current engineering dependency closes;
- a benchmark or incident supplies new evidence;
- a duplicate or superseding implementation is discovered;
- the operator explicitly reprioritizes research capacity.

Do not repeatedly reopen parked ideas merely because they are interesting.

## 8. Core invariant

```text
Ideas are preserved.
Current engineering remains explicit.
Research has no hidden authority.
Only evidence promotes a bounded slice.
```
