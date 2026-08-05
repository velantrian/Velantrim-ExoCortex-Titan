# 🗺️ Component and Authority Map

Use the smallest relevant inspection surface and verify exact SHAs, callers and tests.

## Authority rules

Continuity, retrieval, selective-memory extraction, advisory and projections do not acquire Canon authority. Origin/inference is not truth, attestation, compute permission or action authority. One decision type has one owner.

## Canon and projection delivery

Start with `core/memory.py`, PromotionGateway, TruthGate, WriteGate, PolicyKernel, `core/projection_dispatcher.py` and migrations 020–022. Main risks: mutation ownership is not proven unified and projection delivery has no accepted runtime lifecycle or backlog observability.

## Selective memory — ARM-03

`MAIN + TESTED + DEFAULT OFF / NOT WIRED`. Proposal-only. Start with `core/selective_memory_candidates.py`, focused tests, workflow, benchmark, replay and ADR.

## Continuity R1 — immutable contracts

| Item | Value |
|---|---|
| Status | `MAIN + TESTED / CONTRACTS ONLY` |
| Files | `core/continuity/contracts.py`, public exports |
| Merge | `06529700d70854504b88629eeecf737bdc6b81d5` |

## Continuity R2 — shadow ledger, bridge and threads

| Item | Value |
|---|---|
| Status | `MAIN + TESTED / SHADOW READ-SIDE / NOT WIRED` |
| Merge | `320d5ae9f89780efc553ffbfc3a17c1ebc83b47e` |
| Event port | `core/continuity/event_port.py` |
| Conversation bridge | `core/continuity/conversation_bridge.py` |
| Thread projection | `core/continuity/thread_weaver.py` |

## Continuity R3 — projections and WorkingMemory adapters

| Item | Value |
|---|---|
| Status | `MAIN + TESTED / PROJECTIONS / NOT WIRED` |
| Merge | `a19d16656676ad5c98c92d4776e9709edbfb920c` |
| Context projection | `core/continuity/context_pack.py` |
| Context adapter | `core/continuity/working_memory_adapter.py` |
| State reconciliation | `core/continuity/state_reconciler.py` |
| Goal/open-loop projections | `core/continuity/goal_open_loop.py` |
| Projection adapter | `core/continuity/projection_working_memory_adapter.py` |
| Ownership ADR | `docs/adr/ADR-CONT-SYN-01-contract-reconciliation.md` (`PROPOSED`) |

## Continuity R4 — compatible compute assessment

| Item | Value |
|---|---|
| Status | draft PR #204 / shadow only / not wired |
| Legacy owner | `decide_compute_path()` in `core/compute_controller.py` |
| New input | `ContinuityComputeSignals` |
| New output | `ContinuityComputeAssessment` |
| New API | `assess_compute_with_continuity()` |
| ADR | `ADR-2026-08-05-continuity-r4-compatible-compute-assessment.md` |
| Hand-off | `docs/ai/CONTINUITY_R4_HANDOFF.md` |

R4 audit questions:

1. Is the legacy `decide_compute_path()` signature unchanged?
2. Are exactly five `ComputePath` enum values retained?
3. Is direct positional `ComputeDecision` construction still valid?
4. Is the old seven-key `to_dict()` payload unchanged?
5. Does the legacy decision matrix remain identical?
6. Does `RapidOrientation` remain exhaustive over every path?
7. Are continuity inputs typed and fail-closed?
8. Can continuity only preserve, raise to VERIFY or cap degraded DEEP?
9. Is VERIFY never downgraded?
10. Are retrieval, persistence, Canon, answer, action and runtime APIs absent?
11. Is `shadow_only=False` rejected?
12. Is there no live caller or feature activation?

## Continuity R5 — later recovery

Replay evaluation, Advisory shadow and disabled complete runner remain unimplemented on current main. Historical #145–#147 are source material, not accepted merge targets.

## Compute and orientation

Legacy compute owner: `ComputeController`. New enum members require exhaustive downstream mapping. `RapidOrientation` currently exhaustively maps the five accepted paths; this is why R4 does not add DEFER.

## Identity

`core/identity_layer.py` remains `LEGACY/UNWIRED`; do not activate it.

## API/deployment/supply chain

Start with `server.py`, `api/`, egress, Docker/compose, `pyproject.toml`, locks and workflows. Main risks are composition breadth, shared-key authorization, profile ambiguity, verification scope and reproducibility.
