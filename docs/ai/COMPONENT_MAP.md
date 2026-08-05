# 🗺️ Component and Authority Map

Use exact SHAs, callers and tests. Presence is not wiring.

## Continuity recovery lineage

| Layer | State | Primary files |
|---|---|---|
| R1 | main/tested/unwired | `contracts.py` |
| R2 | main/tested/unwired | `event_port.py`, `conversation_bridge.py`, `thread_weaver.py` |
| R3 | main/tested/unwired | `context_pack.py`, `state_reconciler.py`, `goal_open_loop.py`, adapters |
| R4 | main/tested/unwired | `core/compute_controller.py` compatible assessment API |
| R5A | main/tested/unwired | `evaluation.py`, `advisory_shadow.py` |
| R5B | draft #206 | `shadow_runner.py` |

## R5B complete shadow runner

Start with:

- `core/continuity/shadow_runner.py`;
- `tests/test_continuity_shadow_runner.py`;
- `docs/adr/ADR-2026-08-05-continuity-r5b-disabled-shadow-runner.md`;
- `docs/ai/CONTINUITY_R5B_HANDOFF.md`.

Audit questions:

1. Does default execution return before any component call?
2. Does `enabled=True` remain local object evaluation rather than runtime activation?
3. Are all inputs already typed?
4. Does Advisory intent resolve exactly one projection or fail closed?
5. Are caller policy values copied rather than re-inferred?
6. Does the runner use the existing WorkingMemoryGate and ContextPackBuilder?
7. Does it call R4 `assess_compute_with_continuity()` rather than changing legacy compute routing?
8. Is only the final R4 decision snapshotted, never executed?
9. Do baseline and reversed-order replay produce the same snapshot?
10. Do R5A hard-gate failures prevent reminder-shaped output?
11. Are shared audiences silenced?
12. Do all receipts include `NO_RUNTIME_AUTHORITY`?
13. Are server, startup, worker, scheduler, persistence, network, answer, delivery, tool and action interfaces absent?

## Authority ownership

- truth/Canon: existing canonical memory/TruthGate paths;
- WorkingMemory disposition: existing `WorkingMemoryGate`;
- final prompt context: existing `ContextPackBuilder`;
- compute routing: legacy `decide_compute_path()`; R4 assessment is separate shadow evidence;
- Advisory selection: R5A shadow gate only;
- runtime activation: no owner is accepted yet.

## Other review surfaces

Projection delivery remains unwired. Identity remains legacy/unwired. API/deployment review starts with `server.py`, API auth, egress, Docker/compose and dependency locks.
