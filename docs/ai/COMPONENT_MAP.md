# 🗺️ Component and Authority Map

Use the smallest relevant inspection surface and verify exact SHAs, callers and tests.

## Continuity lineage

| Layer | Status | Primary surface |
|---|---|---|
| R1 | main/tested/unwired | `core/continuity/contracts.py` |
| R2 | main/tested/unwired | `event_port.py`, `conversation_bridge.py`, `thread_weaver.py` |
| R3 | main/tested/unwired | `context_pack.py`, `state_reconciler.py`, `goal_open_loop.py`, WorkingMemory adapters |
| R4 | main/tested/unwired | `ContinuityComputeSignals`, `ContinuityComputeAssessment`, `assess_compute_with_continuity()` |
| R5A | draft #205 / shadow only | `evaluation.py`, `advisory_shadow.py` |
| R5B | not implemented | complete disabled orchestration runner |

## R5A replay evaluation

Start with:

- `core/continuity/evaluation.py`;
- `tests/test_continuity_evaluation.py`;
- `docs/adr/ADR-2026-08-05-continuity-r5a-replay-advisory-shadow.md`.

Audit questions:

1. Are snapshot identities deterministic?
2. Does replay divergence fail the report?
3. Are all hard gates zero-tolerance?
4. Can R4 final assessment decisions be hashed without execution?
5. Are externally observed effects explicit counters rather than inferred successes?
6. Are persistence, mutation and apply APIs absent?

## R5A Advisory Shadow

Start with:

- `core/continuity/advisory_shadow.py`;
- `tests/test_continuity_advisory_shadow.py`;
- `docs/ai/CONTINUITY_R5A_HANDOFF.md`.

Audit questions:

1. Does a failed replay report always produce text-free `DEFER`?
2. Does non-private audience always silence personal continuity?
3. Is every candidate triggered by an explicit typed signal?
4. Does the signal resolve to exactly one supplied projection ID?
5. Are inactive goals/resolved loops/non-blockers excluded?
6. Are reminder/confirmation permissions enforced?
7. Are basis refs mandatory for reminder-shaped candidates?
8. Is deterministic priority independent of input order?
9. Can a non-actionable higher signal be skipped safely?
10. Is `shadow_only=False` rejected?
11. Are delivery, answers, tools, actions and persistence absent?
12. Is Advisory `DEFER` kept separate from compute routing?

## Canon and projection delivery

Start with `core/memory.py`, PromotionGateway, TruthGate, WriteGate, PolicyKernel, `core/projection_dispatcher.py` and migrations 020–022. Dispatcher runtime lifecycle remains unresolved.

## Identity

`core/identity_layer.py` remains `LEGACY/UNWIRED`; do not activate it.

## API/deployment/supply chain

Start with `server.py`, `api/`, egress, Docker/compose, `pyproject.toml`, locks and workflows. Main risks remain composition breadth, shared-key authorization, profile ambiguity and reproducibility.
