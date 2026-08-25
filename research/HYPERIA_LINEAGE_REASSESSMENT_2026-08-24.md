# 🔬 Hyperia / Titan v7.5 / v8 lineage reassessment — 2026-08-24

**Status:** `TRIAGED RESEARCH + ONE BOUNDED ENGINEERING SLICE`  
**Runtime authority:** none added  
**Canon / ESM write authority:** none added  
**Baseline reviewed:** `main@389e1201f95ed9c21c4423eb893061cf80379357`  

## 0. Why this exists

Historical `HYPERIA_V6_SYNAPSE`, `Velantrim v7.5 Titan` and `Velantrim v8 Crystal`
documents are lineage snapshots of the architecture that later became Titan.  Most of
their useful components already exist in current Titan or were deliberately superseded.
This note preserves only the residual ideas that still have a bounded Titan-native use.

Historical wording such as `Graph = Truth` or direct Neo4j restore is **not** current
Titan authority.  Current ownership, evidence and admission boundaries win.

## 1. Classification summary

| ID | Slice | Lane | Current action |
|---|---|---|---|
| `ENG-GH-01` | topology health diagnostics | `ENGINEERING_NOW` | implemented read-only extension; no auto-repair |
| `RT-TOPOLOGY-01` | fan-out prevention + retrieval homeostasis | `R1 CONTRACT` | research only |
| `RT-RANKING-01` | typed candidate features + inverted HyDE + ephemeral ReasonGraph | `R0 QUESTION` | offline benchmark first |
| `RT-LIFECYCLE-01` | task-state-aware consolidation | `R0 QUESTION` | research only |
| `RT-RESTORE-01` | bounded archive restore contract | `R0 QUESTION · CROSS-PROJECT` | Crystal admission owner required |
| `RT-GOALS-01` | hierarchical Goal Stack | `R0 QUESTION · PARKED` | no runtime change yet |
| `RT-REFTRACE-01` | reference decision traces | `R1 CONTRACT` | eval-only design |
| `RT-RESOURCE-01` | multi-component resource budget | `R2 OFFLINE PROTOTYPE` | deterministic prototype only |

## 2. `ENG-GH-01` — bounded topology health diagnostics

- **Origin:** Hyperia graph-health ideas + current-code audit.
- **Verified gap:** `CausalGraph.integrity_report()` already covers orphan facts and
  dangling edges, but does not report hub degree, outgoing fan-out or disconnected
  non-trivial regions.
- **Implementation:** `core/graph_health.py` composes the existing report with deterministic
  topology observations.
- **Boundary:** read-only; does not change the existing integrity score, relation weights,
  truth status, evidence, Canon, admission or repair state.
- **Important semantic limit:** small structural islands are **not** labelled as proven
  retrieval dead zones.  Topology is an observation, not evidence.
- **Next gate:** exact-head CI + independent bounded review before merge.

## 3. `RT-TOPOLOGY-01` — topology prevention and retrieval homeostasis

1. **ID/title:** `RT-TOPOLOGY-01 — Topology prevention and retrieval homeostasis`.
2. **Origin:** historical Hyperia Homeostatic Balancer + fan-out/meta-node proposal.
3. **Problem/opportunity:** long-lived graphs may accumulate hubs, over-exposed domains or
   structurally weak regions even when integrity is valid.
4. **Current evidence:** diagnostic gap verified; no current benchmark proves that automatic
   weight normalization or fan-out rejection improves Titan.
5. **Why research:** prevention changes retrieval behavior and derived weights; thresholds are
   not yet calibrated.
6. **Affected owners:** causal graph, retrieval composition, derived projections.
7. **Authority risks:** topology utility must never become truth/evidence/Canon confidence.
8. **Privacy/erasure:** any derived balancing cache must remain rebuildable and erasure-aware.
9. **Cheapest experiment:** fixed graph fixtures + read-only simulated reweighting; compare
   recall/diversity/hub exposure without persisting changes.
10. **Return trigger:** reproducible topology benchmark shows hub/fan-out concentration or
    domain starvation harms retrieval quality/latency.
11. **Promotion evidence:** baseline vs candidate metrics, no truth-status changes, deterministic
    replay and rollback.
12. **Decision history:** 2026-08-24 — keep prevention/homeostasis out of runtime; implement only
    diagnostics now.

## 4. `RT-RANKING-01` — typed ranking features, inverted HyDE and ephemeral ReasonGraph

1. **ID/title:** `RT-RANKING-01 — Bounded retrieval ranking experiments`.
2. **Origin:** historical 11-dimensional CandidateScore, offline query-key generation and
   reasoning DAG ideas.
3. **Problem/opportunity:** current retrieval may benefit from explicit decomposed features
   instead of one opaque score on difficult Reader/multi-hop workloads.
4. **Current evidence:** existing adaptive-retrieval architecture already owns routing and
   rebuildable projections; no fixed benchmark yet proves these additions improve it.
5. **Why research:** feature weights, HyDE value and ReasonGraph cost are unproven.
6. **Affected owners:** retrieval composition, Reader, evaluation replay.
7. **Authority risks:** ranking features and temporary reasoning structure are never evidence,
   truth, policy or Canon.
8. **Privacy/erasure:** derived keys/graphs must be rebuildable and deletable with source data.
9. **Cheapest experiment:** offline fixed corpus comparing baseline vs typed features, then
   optional inverted-HyDE keys and ephemeral DAG separately.
10. **Return trigger:** Reader/multi-hop benchmark misses a declared recall/latency/coverage goal.
11. **Promotion evidence:** measured gain, bounded compute, deterministic replay, lexical fallback,
    no query-path writes.
12. **Decision history:** 2026-08-24 — do not copy the historical 11 weights literally and do not
    create a second retriever.

## 5. `RT-LIFECYCLE-01` — task-state-aware consolidation

1. **ID/title:** `RT-LIFECYCLE-01 — Task-state-informed consolidation scheduling`.
2. **Origin:** historical task lifecycle + consolidation coupling.
3. **Problem/opportunity:** active work should remain easy to revisit while resolved/archived work
   may be eligible for stronger background consolidation.
4. **Current evidence:** no current workload proves a required scheduling change.
5. **Why research:** task state is contextual, not epistemic, and must not become a write gate.
6. **Affected owners:** consolidation scheduling, Working Desk / continuity research.
7. **Authority risks:** `task_state != truth_state`; closing a task cannot validate evidence.
8. **Privacy/erasure:** retention cannot be extended merely because a task is active.
9. **Cheapest experiment:** replay a task corpus and vary scheduling priority only.
10. **Return trigger:** measured reread/consolidation cost or context loss on long-running tasks.
11. **Promotion evidence:** lower cost or better resume quality with identical admitted memory set.
12. **Decision history:** 2026-08-24 — research only.

## 6. `RT-RESTORE-01` — bounded archive restore contract

1. **ID/title:** `RT-RESTORE-01 — Evidence-preserving archive restore request`.
2. **Origin:** historical `MemoryRestoreProtocol`.
3. **Problem/opportunity:** archival needs a controlled reverse path when an operator/user requests
   restoration.
4. **Current evidence:** historical implementation restored directly into Neo4j and is not valid
   for current authority boundaries.
5. **Why research:** ownership crosses Titan orchestration and Crystal evidence/admission semantics.
6. **Affected owners:** Titan orchestration, Crystal admission/provenance, archive storage.
7. **Authority risks:** restored data must not become Validated/Canon merely because it existed before.
8. **Privacy/erasure:** an erased/revoked item must not be resurrected from archive.
9. **Cheapest experiment:** fixture-only `RestoreRequest -> integrity/provenance checks -> candidate`
   with no writes.
10. **Return trigger:** an accepted archive/recovery workload requires user-visible restoration.
11. **Promotion evidence:** cross-project owner decision, erasure/revocation proof, source hash and
    lineage validation, explicit admission result and audit receipt.
12. **Decision history:** 2026-08-24 — Titan may request/orchestrate; Crystal remains the trusted
    memory/admission owner.  No direct graph merge.

## 7. `RT-GOALS-01` — hierarchical Goal Stack

1. **ID/title:** `RT-GOALS-01 — Hierarchical goal relationships`.
2. **Origin:** historical SOAR-style `parent_id` proposal.
3. **Problem/opportunity:** current `core/goal_stack.py` is flat; subgoal relationships may improve
   complex planning and resume.
4. **Current evidence:** structural absence verified, but no workload currently proves hierarchy is
   necessary.
5. **Why research:** schema/API semantics (cycles, deletion, status inheritance) need a contract.
6. **Affected owners:** Innenwelt goal surface and continuity helpers.
7. **Authority risks:** goal hierarchy is user/task state, not truth or action authority.
8. **Privacy/erasure:** child goals inherit no hidden retention or consent by default.
9. **Cheapest experiment:** fixture-only tree with cycle rejection and no server API changes.
10. **Return trigger:** concrete nested-goal workload that cannot be represented cleanly today.
11. **Promotion evidence:** migration plan, cycle/ownership tests, backward compatibility and no
    action-authority implication.
12. **Decision history:** 2026-08-24 — park; do not add SOAR as a new subsystem.

## 8. `RT-REFTRACE-01` — reference decision traces

1. **ID/title:** `RT-REFTRACE-01 — Reference decision trace fixtures`.
2. **Origin:** historical TraceExample concept, reclassified as evaluation data.
3. **Problem/opportunity:** regression tests benefit from stable examples of candidate selection,
   exclusion, evidence and expected verdicts.
4. **Current evidence:** Titan already has evaluation replay and Reader benchmark fixtures.
5. **Why research:** the smallest useful schema should reuse those owners rather than create a new
   memory type.
6. **Affected owners:** evaluation replay, Reader evaluation, TruthPolicy tests.
7. **Authority risks:** a stored trace is an expected test result, never truth/evidence itself.
8. **Privacy/erasure:** fixtures should be synthetic or explicitly approved.
9. **Cheapest experiment:** one synthetic fixture:
   `query -> candidates -> selected evidence -> exclusions -> expected verdict`.
10. **Return trigger:** a regression cannot be expressed cleanly with current evaluation fixtures.
11. **Promotion evidence:** schema reuse, deterministic replay and zero runtime callers.
12. **Decision history:** 2026-08-24 — eval-only; no `TraceExample` memory node.

## 9. `RT-RESOURCE-01` — multi-component resource budget

1. **ID/title:** `RT-RESOURCE-01 — Deterministic local resource profile budget`.
2. **Origin:** historical multi-component RAM-pressure invariant.
3. **Problem/opportunity:** current `core/memory_budget.py` protects fact-count growth, not total
   local profile RAM/CPU composition.
4. **Current evidence:** code inspection confirms the existing budget is fact-count based.
5. **Why research:** real reservations and operator downshift policy are not calibrated.
6. **Affected owners:** operator/startup profile, ComputeController boundary; not memory truth.
7. **Authority risks:** the prototype may advise `fit/pressure/downshift/refuse` but does not activate,
   disable or route anything.
8. **Privacy/erasure:** none beyond normal telemetry if later measured live; prototype has no probing.
9. **Cheapest experiment:** deterministic supplied-capacity evaluator.
10. **Return trigger:** accepted local runtime profiles need a preflight that prevents OOM/contention.
11. **Promotion evidence:** measured reservations on supported profiles, conservative reserve policy,
    operator-visible reasoning and explicit wiring decision.
12. **Decision history:** 2026-08-24 — `R2 OFFLINE PROTOTYPE` added at
    `research/prototypes/resource_budget.py`; no runtime import/wiring.

## 10. Explicitly not reopened

The reassessment does **not** reopen or duplicate:

- DAAD, FSRS, Velum, salience, ETIR, ReasoningBank, predictive fusion, LSM,
  EmbeddingRegistry, CognitiveModes, Guardian, CircuitBreaker or existing MemoryBudget;
- a standalone SOAR engine;
- a second Graph Health subsystem;
- CQRS Shadow State as a new proposal (already a Titan Horizon);
- direct Neo4j-as-truth architecture;
- Domain Seed direct-to-Canon writes;
- Multi-User Authority as a truth resolver;
- Laplace confidence without a measured current confidence defect.

## 11. Promotion invariant

```text
historical idea
→ current-owner check
→ measured trigger
→ offline deterministic experiment
→ replay/shadow evidence
→ explicit bounded engineering decision

historical specification != current backlog
retrieval topology != evidence
restored data != revalidated data
resource fit != runtime authorization
```
