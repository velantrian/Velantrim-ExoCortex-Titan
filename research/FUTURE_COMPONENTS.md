# 🔬 Research: Future Components for Velantrim ExoCortex

**Status:** `RESEARCH INDEX`  
**Runtime authority:** none  
**Canon write authority:** none  
**Updated:** 2026-07-30

This file is the current entry point for future and external architecture research. Historical feature catalogues are preserved separately and must not be read as current runtime claims.

## Active research tracks

| Priority | Track | Status | Contract |
|---|---|---|---|
| P0 | Evaluation replay, fork and structural diff | `R1 — contract` | [`EVALUATION_REPLAY_PROTOCOL.md`](EVALUATION_REPLAY_PROTOCOL.md) |
| P1 | Temporal evidence and claim validity | `R0/R1 — research` | [`EXTERNAL_ARCHITECTURE_PATTERNS.md`](EXTERNAL_ARCHITECTURE_PATTERNS.md#p1--temporal-evidence-and-claim-validity) |
| P2 | Unified decision and run receipts | `R0/R1 — research` | [`EXTERNAL_ARCHITECTURE_PATTERNS.md`](EXTERNAL_ARCHITECTURE_PATTERNS.md#p2--unified-decision-and-run-receipts) |
| P3 | Capability-based extension registry | `R0/R1 — research` | [`EXTERNAL_ARCHITECTURE_PATTERNS.md`](EXTERNAL_ARCHITECTURE_PATTERNS.md#p3--capability-based-extension-registry) |
| P4 | Evaluated procedural skills | `R0/R1 — research` | [`EXTERNAL_ARCHITECTURE_PATTERNS.md`](EXTERNAL_ARCHITECTURE_PATTERNS.md#p4--evaluated-procedural-skills) |

## Existing Titan-native programs

- [`RAPID_CALIBRATED_ORIENTATION.md`](RAPID_CALIBRATED_ORIENTATION.md) — read-only orientation and route proposals;
- [`D16_EXECUTIVE_CONTROL_CONTRACT.md`](D16_EXECUTIVE_CONTROL_CONTRACT.md) — proposal vocabulary, no active controller authority;
- [`FAILURE_LIFECYCLE_RELIABILITY_CONTRACT.md`](FAILURE_LIFECYCLE_RELIABILITY_CONTRACT.md) — failure disposition, memory lifecycle and reliability;
- [`WORKING_DESK_RESEARCH_MODE.md`](WORKING_DESK_RESEARCH_MODE.md) — bounded task-aware research composition;
- [`../docs/research/ADAPTIVE_RETRIEVAL_MEMORY_ARCHITECTURE.md`](../docs/research/ADAPTIVE_RETRIEVAL_MEMORY_ARCHITECTURE.md) — adaptive routing, selective memory and rebuildable projections;
- [`EXTERNAL_MODEL_COGNITIVE_PROPOSALS.md`](EXTERNAL_MODEL_COGNITIVE_PROPOSALS.md) — `Q0`-tier candidate ideas from external AI assistants, fact-checked and filtered before recording; none promoted to the `P` track yet.

## Promotion rule

```text
research note
→ Titan-native contract
→ licence/threat review
→ offline prototype
→ deterministic replay evaluation
→ shadow receipts
→ explicit Operator GO
→ bounded implementation PR
```

No item in this index is runtime merely because it is documented.

## Return triggers

Return to a research item only when at least one trigger exists:

- a measured limitation in the current baseline;
- a reproducible benchmark case;
- a concrete workload that existing components cannot satisfy;
- an approved security, policy or compliance requirement;
- an operator-labelled evaluation dataset.

Feature count, novelty and external popularity are not sufficient triggers.

## Legacy catalogue

The previous long-form catalogue is preserved at [`archive/FUTURE_COMPONENTS_LEGACY_2026-07-30.md`](archive/FUTURE_COMPONENTS_LEGACY_2026-07-30.md). It contains historical V8.x ideas and estimates; those entries are prior research notes, not current status claims.

## Core rule

```text
Research is visible.
Authority stays explicit.
Old ideas remain traceable.
Only measured improvements advance.
```
