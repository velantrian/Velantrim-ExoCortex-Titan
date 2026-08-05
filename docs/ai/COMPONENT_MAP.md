# 🗺️ Component and Authority Map

Use the smallest relevant inspection surface and verify exact SHAs, callers and tests.

## Authority rules

Continuity, retrieval, selective-memory extraction, advisory and projections do not
acquire Canon authority. Origin/inference is not truth, attestation or action permission.
One decision type has one owner.

## Canon and promotion

Start with `core/memory.py`, PromotionGateway, TruthGate, WriteGate and PolicyKernel.
Main risk: every mutation family is not proven to use one typed owner.

## Projection delivery

Start with `core/projection_dispatcher.py`, projection helpers and migrations 020–022.
Main risk: no accepted runtime lifecycle or backlog observability.

## Selective memory — ARM-03

`MAIN + TESTED + DEFAULT OFF / NOT WIRED`. Proposal-only. Start with
`core/selective_memory_candidates.py`, focused tests, workflow, benchmark, replay and ADR.

## Continuity R1 — immutable contracts

| Item | Value |
|---|---|
| Status | `MAIN + TESTED / CONTRACTS ONLY` |
| Files | `core/continuity/contracts.py`, public exports |
| Tests | contract, golden and R1 regression suites |
| ADR | `ADR-2026-08-05-continuity-r1-foundation.md` |

Audit canonicalization, content IDs, provenance and separation of origin from truth and
projection state.

## Continuity R2 — shadow ledger, bridge and threads

| Item | Value |
|---|---|
| Status | recovery branch / draft review |
| Event port | `core/continuity/event_port.py` |
| Conversation bridge | `core/continuity/conversation_bridge.py` |
| Thread projection | `core/continuity/thread_weaver.py` |
| Legacy source fidelity | `core/conversation_consolidation.py` read methods |
| Tests | event-port, bridge, thread-weaver and R2 regression suites |
| ADR | `ADR-2026-08-05-continuity-r2-shadow-bridge-threads.md` |
| Hand-off | `docs/ai/CONTINUITY_R2_HANDOFF.md` |

Audit questions:

1. Is the ledger process-local, append-only and without destructive/durable/Canon APIs?
2. Are idempotent replay and same-key/different-event conflicts distinguished?
3. Does integrity verification recompute canonical hashes?
4. Does ConversationBridge call only read methods?
5. Are `created_at` and `related_chats` preserved from persisted rows?
6. Are episodes deterministic, immutable and non-epistemic?
7. Do explicit refs and exact goal text remain the only v1 link triggers?
8. Can topic/time equality create a false link? It must not.
9. Are missing explicit targets retained as unresolved typed references?
10. Are DB migrations, runtime wiring, model calls, Canon/gates and actions absent?

## Continuity later layers

| Layer | Intended content | Status |
|---|---|---|
| R3 | state, qualified goals/open loops, WorkingMemory adapters | not implemented |
| R4 | compute signals, replay and Advisory shadow | not implemented |
| R5 | disabled complete shadow runner | not implemented |

Historical #131–#147 remain source material, not an accepted merge path.

## Compute and orientation

Owner: `ComputeController`. Start with compute controller, Rapid Orientation and goal
frame. New enum members require exhaustive downstream mapping and differential legacy
tests.

## Identity

`core/identity_layer.py` remains `LEGACY/UNWIRED`; do not activate it.

## API/deployment/supply chain

Start with `server.py`, `api/`, egress, Docker/compose, `pyproject.toml`, locks and
workflows. Main risks are composition breadth, shared-key authorization, profile
ambiguity, verification scope and reproducibility.
