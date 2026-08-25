# 🔬 Research: Future Components for Velantrim ExoCortex

**Status:** `RESEARCH INDEX`  
**Runtime authority:** none  
**Canon write authority:** none  
**Updated:** 2026-08-24

This file is the current entry point for future and external architecture research. Historical feature catalogues are preserved separately and must not be read as current runtime claims.

All new ideas from audits, conversations, external AI analysis or operator feedback must first pass [`IDEA_INTAKE_PROTOCOL.md`](IDEA_INTAKE_PROTOCOL.md). The intake protocol separates current engineering obligations from speculative or future research so neither is lost or misclassified.

## Active research tracks

| Priority | Track | Status | Contract |
|---|---|---|---|
| P0 | Evaluation replay, fork and structural diff | `R1 — contract` | [`EVALUATION_REPLAY_PROTOCOL.md`](EVALUATION_REPLAY_PROTOCOL.md) |
| P1 | Temporal evidence and claim validity | `R0/R1 — research` | [`EXTERNAL_ARCHITECTURE_PATTERNS.md`](EXTERNAL_ARCHITECTURE_PATTERNS.md#p1--temporal-evidence-and-claim-validity) |
| P2 | Unified decision and run receipts | `R0/R1 — research` | [`EXTERNAL_ARCHITECTURE_PATTERNS.md`](EXTERNAL_ARCHITECTURE_PATTERNS.md#p2--unified-decision-and-run-receipts) |
| P3 | Capability-based extension registry | `R0/R1 — research` | [`EXTERNAL_ARCHITECTURE_PATTERNS.md`](EXTERNAL_ARCHITECTURE_PATTERNS.md#p3--capability-based-extension-registry) |
| P4 | Evaluated procedural skills | `R0/R1 — research` | [`EXTERNAL_ARCHITECTURE_PATTERNS.md`](EXTERNAL_ARCHITECTURE_PATTERNS.md#p4--evaluated-procedural-skills) |

## Triaged candidate tracks — 2026-08-07

These items are preserved as future research. They are not active implementation commitments.

| ID | Candidate | State | Return trigger |
|---|---|---|---|
| `RT-STORAGE-01` | transactional server Canon profile, strict Mode Lock and same-backend outbox | `R0 · PARKED` | measured SQLite SLO failure, multi-node/HA requirement or accepted remote multi-user workload |
| `RT-RETRIEVAL-01` | ANN/vector projection profiles such as FAISS, HNSW or pgvector | `R0 · PARKED` | versioned corpus benchmark proves current latency, memory or recall target is missed |
| `RT-DISTRIBUTED-01` | multi-node, replication, fencing, failover and reconciliation profile | `R0 · PARKED` | accepted deployment requires multiple live writers or a formal HA SLO |
| `RT-ROUTING-01` | policy-driven retrieval coordination without a second PolicyKernel/ComputeController | `R0 · PARKED` | measured routing inconsistency, duplicated authority or benchmarked cost/latency loss |
| `RT-ASSURANCE-01` | operator assurance console for lineage, receipts, replay, lag and erasure state | `R0` | durable read models and replay artifacts exist and operators require one coherent surface |
| `RT-CONTINUITY-01` | user-visible continuity, reminders and bounded action proposals | `R0 · BLOCKED` | evaluator, current privacy/authorization, facade, retention, shadow evaluation and Operator GO exist |
| `RT-SUBSTRATE-01` | Native Kernel-aligned storage/compute substrate profiles | `R0` | concrete cross-project integration slice with accepted ownership and compatibility tests |
| `RT-WORLDMODEL-01` | meta-causal model of causes, motives, invariants, contradictions and unknowns | `R0` | fixed evidence corpus and comparison target against current causal retrieval |
| `RT-IDENTITY-01` | contestable evidence-bound persona and identity candidates | `R0 · PARKED` | accepted identity admission, consent, correction, supersession, retraction and erasure protocol |

Detailed boundaries, cheapest experiments and forbidden shortcuts are defined in [`IDEA_INTAKE_PROTOCOL.md`](IDEA_INTAKE_PROTOCOL.md#6-initial-candidate-set-from-the-2026-08-07-audit).

## Triaged candidate tracks — 2026-08-24 lineage reassessment

The historical Hyperia / Titan v7.5 / v8 specifications were re-read against current
`main`. Most components are already implemented, superseded or deliberately rejected.
Only the residual bounded slices below remain. Full research cards and decision history
are in [`HYPERIA_LINEAGE_REASSESSMENT_2026-08-24.md`](HYPERIA_LINEAGE_REASSESSMENT_2026-08-24.md).

| ID | Candidate | State | Return trigger |
|---|---|---|---|
| `RT-TOPOLOGY-01` | fan-out prevention and retrieval homeostasis without truth-weight coupling | `R1 · RESEARCH` | topology benchmark proves hub/fan-out concentration or domain starvation harms retrieval |
| `RT-RANKING-01` | typed ranking features, inverted HyDE keys and ephemeral ReasonGraph | `R0 · RESEARCH` | Reader/multi-hop benchmark misses declared recall, coverage or latency goal |
| `RT-LIFECYCLE-01` | task-state-informed consolidation scheduling | `R0 · RESEARCH` | long-running task replay shows measurable resume/context-loss or consolidation-cost defect |
| `RT-RESTORE-01` | evidence-preserving archive restore request with Crystal admission ownership | `R0 · CROSS-PROJECT` | accepted archive/recovery workload requires restoration and cross-project owner contract exists |
| `RT-GOALS-01` | hierarchical Goal Stack relationships | `R0 · PARKED` | concrete nested-goal workload cannot be represented cleanly by current flat goal model |
| `RT-REFTRACE-01` | reference decision trace fixtures for replay/regression | `R1 · EVAL-ONLY` | current evaluation fixtures cannot express a required regression case |
| `RT-RESOURCE-01` | deterministic multi-component RAM/CPU profile budget | `R2 · OFFLINE PROTOTYPE` | supported local runtime profiles require an OOM/contention preflight |

A separate bounded engineering slice, `ENG-GH-01`, adds read-only topology diagnostics
(hubs, fan-out and disconnected non-trivial components) without changing the existing
`CausalGraph.integrity_report()` score or adding auto-repair. It is current engineering,
not a research commitment.

## Current engineering work that is not research

Do not move these items into the future registry:

- issue #234 administrator branch-ruleset enforcement;
- deterministic Continuity admission evaluator and allowlisted rule registry;
- admission-aware facade and anti-bypass guards;
- current authorization, consent, restriction, erasure and policy resolution;
- query-path read-only proof and Canon-writer unification;
- projection lifecycle, reconciliation and operational metrics;
- durable operational observability, backup/recovery and incident evidence;
- security review and documentation synchronization.

They already have accepted owners, evidence and required completion criteria.

## Existing Titan-native programs

- [`RAPID_CALIBRATED_ORIENTATION.md`](RAPID_CALIBRATED_ORIENTATION.md) — read-only orientation and route proposals;
- [`D16_EXECUTIVE_CONTROL_CONTRACT.md`](D16_EXECUTIVE_CONTROL_CONTRACT.md) — proposal vocabulary, no active controller authority;
- [`FAILURE_LIFECYCLE_RELIABILITY_CONTRACT.md`](FAILURE_LIFECYCLE_RELIABILITY_CONTRACT.md) — failure, lifecycle and reliability boundaries;
- [`WORKING_DESK_RESEARCH_MODE.md`](WORKING_DESK_RESEARCH_MODE.md) — bounded task-aware research composition;
- [`../docs/research/ADAPTIVE_RETRIEVAL_MEMORY_ARCHITECTURE.md`](../docs/research/ADAPTIVE_RETRIEVAL_MEMORY_ARCHITECTURE.md) — adaptive routing, selective memory and rebuildable projections;
- [`HYPERIA_LINEAGE_REASSESSMENT_2026-08-24.md`](HYPERIA_LINEAGE_REASSESSMENT_2026-08-24.md) — residual lineage ideas after current-code deduplication and authority review.

## Promotion rule

```text
captured idea
→ triage against current architecture
→ Titan-native contract
→ licence/threat/privacy review
→ offline prototype
→ deterministic replay evaluation
→ shadow receipts
→ explicit architecture decision
→ bounded engineering PR
→ separate activation decision when authority changes
```

No item in this index is runtime merely because it is documented.

## Return triggers

Return to a research item only when at least one trigger exists:

- a measured limitation in the current baseline;
- a reproducible benchmark case;
- a concrete workload that existing components cannot satisfy;
- an approved security, policy or compliance requirement;
- an operator-labelled evaluation dataset;
- closure of an explicitly recorded engineering prerequisite.

Feature count, novelty and external popularity are not sufficient triggers.

## Legacy catalogue

The previous long-form catalogue is preserved at [`archive/FUTURE_COMPONENTS_LEGACY_2026-07-30.md`](archive/FUTURE_COMPONENTS_LEGACY_2026-07-30.md). It contains historical V8.x ideas and estimates; those entries are prior research notes, not current status claims.

## Core rule

```text
Ideas are preserved.
Current engineering remains explicit.
Research has no hidden authority.
Old ideas remain traceable.
Only measured improvements advance.
```
