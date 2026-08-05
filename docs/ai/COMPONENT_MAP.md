# 🗺️ Component and Authority Map

Use the smallest relevant inspection surface and verify exact SHAs, callers and tests.

## Authority rules

Continuity, retrieval, selective-memory extraction, advisory and projections do not acquire Canon authority. Origin/inference is not truth, attestation or action permission. One decision type has one owner.

## Canon and projection delivery

Start with `core/memory.py`, PromotionGateway, TruthGate, WriteGate, PolicyKernel, `core/projection_dispatcher.py` and migrations 020–022. Main risks: mutation ownership is not proven unified and projection delivery has no accepted runtime lifecycle or backlog observability.

## Selective memory — ARM-03

`MAIN + TESTED + DEFAULT OFF / NOT WIRED`. Proposal-only. Start with `core/selective_memory_candidates.py`, focused tests, workflow, benchmark, replay and ADR.

## Continuity R1 — immutable contracts

| Item | Value |
|---|---|
| Status | `MAIN + TESTED / CONTRACTS ONLY` |
| Files | `core/continuity/contracts.py`, public exports |
| Tests | contract, golden and R1 regression suites |
| ADR | `ADR-2026-08-05-continuity-r1-foundation.md` |

## Continuity R2 — shadow ledger, bridge and threads

| Item | Value |
|---|---|
| Status | `MAIN + TESTED / SHADOW READ-SIDE / NOT WIRED` |
| Merge | `320d5ae9f89780efc553ffbfc3a17c1ebc83b47e` |
| Event port | `core/continuity/event_port.py` |
| Conversation bridge | `core/continuity/conversation_bridge.py` |
| Thread projection | `core/continuity/thread_weaver.py` |
| Tests | event-port, bridge, thread-weaver and R2 regression suites |
| Hand-off | `docs/ai/CONTINUITY_R2_HANDOFF.md` |

## Continuity R3 — projections and WorkingMemory adapters

| Item | Value |
|---|---|
| Status | draft PR #203 / pre-merge |
| Context projection | `core/continuity/context_pack.py` |
| Context adapter | `core/continuity/working_memory_adapter.py` |
| State reconciliation | `core/continuity/state_reconciler.py` |
| Goal/open-loop projections | `core/continuity/goal_open_loop.py` |
| Projection adapter | `core/continuity/projection_working_memory_adapter.py` |
| Ownership ADR | `docs/adr/ADR-CONT-SYN-01-contract-reconciliation.md` |
| Hand-off | `docs/ai/CONTINUITY_R3_HANDOFF.md` |

Audit questions:

1. Can model inference displace a user statement? It must not do so silently.
2. Do conflicting user statements remain contested and reviewable?
3. Is a goal excluded without typed attestation?
4. Are open loops accepted only from typed signals rather than raw-text inference?
5. Does every adapted claim retain `truth_confidence=None`?
6. Is policy coverage exact and fail-closed?
7. Does the existing `WorkingMemoryGate` remain the only disposition owner?
8. Does the existing `ContextPack` remain the only final prompt pack?
9. Are storage, Canon, compute, advisory, answer, tool, action and runtime APIs absent?
10. Are producer-side trust, privacy, consent and retention explicitly still unresolved?

## Continuity later layers

| Layer | Intended content | Status |
|---|---|---|
| R4 | continuity-aware compute signals and differential compatibility proof | not implemented |
| R5 | replay evaluation, Advisory shadow and disabled complete runner | not implemented |

Historical #131–#147 remain source material, not an accepted merge path.

## Compute and orientation

Owner: `ComputeController`. New enum members or decision fields require exhaustive downstream mapping and differential legacy tests.

## Identity

`core/identity_layer.py` remains `LEGACY/UNWIRED`; do not activate it.

## API/deployment/supply chain

Start with `server.py`, `api/`, egress, Docker/compose, `pyproject.toml`, locks and workflows. Main risks are composition breadth, shared-key authorization, profile ambiguity, verification scope and reproducibility.
