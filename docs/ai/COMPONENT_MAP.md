# 🗺️ Component and Authority Map

Use exact SHAs, callers and tests. Presence is not wiring.

## Continuity Milestone 1 — accepted current-main lineage

| Layer | Merge SHA | Primary surface | Runtime state |
|---|---|---|---|
| R1 contracts | `06529700d70854504b88629eeecf737bdc6b81d5` | `core/continuity/contracts.py` | unwired |
| R2 read-side/threads | `320d5ae9f89780efc553ffbfc3a17c1ebc83b47e` | `event_port.py`, `conversation_bridge.py`, `thread_weaver.py` | process-local, unwired |
| R3 projections/adapters | `a19d16656676ad5c98c92d4776e9709edbfb920c` | `context_pack.py`, `state_reconciler.py`, `goal_open_loop.py`, adapters | rebuildable, unwired |
| R4 compute assessment | `529d8b6b182b1a548d27558173f0aca473bcc400` | `core/compute_controller.py` | shadow-only, unwired |
| R5A replay/advisory | `58e29bba26299ce7003b62e73fd3b25e028956de` | `evaluation.py`, `advisory_shadow.py` | shadow-only, unwired |
| R5B complete runner | `27b91a59f9e9291092b220ac1f53bfeae2daea28` | `shadow_runner.py` | disabled by default, unwired |

## R5B review surface

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
6. Does the runner reuse the existing `WorkingMemoryGate` and `ContextPackBuilder`?
7. Does it call R4 `assess_compute_with_continuity()` without changing legacy routing?
8. Is only the final R4 decision snapshotted, never executed?
9. Do baseline and reversed-order replay produce the same snapshot?
10. Do R5A hard-gate failures prevent reminder-shaped output?
11. Are shared audiences silenced?
12. Do all receipts include `NO_RUNTIME_AUTHORITY`?
13. Are server, startup, worker, scheduler, persistence, network, answer, delivery, tool and action interfaces absent?

## Decision ownership

- truth and Canon: existing canonical memory/TruthGate paths;
- WorkingMemory disposition: existing `WorkingMemoryGate`;
- final prompt context: existing `ContextPackBuilder`;
- legacy compute routing: `decide_compute_path()`;
- continuity compute evidence: R4 assessment only;
- replay evidence: R5A evaluation;
- Advisory candidate selection: R5A shadow gate only;
- complete orchestration: R5B disabled in-memory runner;
- runtime activation: no accepted owner exists.

## Historical status

The old stacked PR sequence #131–#147 is superseded by current-main recovery PRs #201–#206. Historical branches are not accepted integration targets.

## Other review surfaces

Projection delivery remains unwired. Identity remains legacy/unwired. API/deployment review starts with `server.py`, API auth, egress, Docker/compose and dependency locks.
