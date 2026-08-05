# 📍 Current System State

**Verified:** 2026-08-05  
**Current `main`:** `58e29bba26299ce7003b62e73fd3b25e028956de`  
**Continuity R5B review surface:** draft PR #206

Verify claims against exact SHAs, tests, workflows, wiring and runtime evidence. `MAIN`, `TESTED`, `WIRED`, `ENABLED`, `OBSERVED`, `OPEN PR`, `RESEARCH` and `LEGACY/UNWIRED` are separate states.

## Continuity R1–R5A

| Layer | Merge | State |
|---|---|---|
| R1 immutable contracts | `06529700d70854504b88629eeecf737bdc6b81d5` | main, tested, unwired |
| R2 read-side/threads | `320d5ae9f89780efc553ffbfc3a17c1ebc83b47e` | main, tested, process-local, unwired |
| R3 projections/adapters | `a19d16656676ad5c98c92d4776e9709edbfb920c` | main, tested, rebuildable, unwired |
| R4 compute assessment | `529d8b6b182b1a548d27558173f0aca473bcc400` | main, tested, shadow-only, unwired |
| R5A replay/advisory | `58e29bba26299ce7003b62e73fd3b25e028956de` | main, tested, shadow-only, unwired |

R4 preserves the five legacy compute paths and exposes a separate assessment. R5A adds deterministic replay hard gates and Advisory Shadow v2. Advisory text cannot be delivered or shown by these layers.

## Continuity R5B

Draft PR #206 composes the complete current R1–R5A path in memory.

**Status:** `OPEN PR / FOCUSED TESTED / DISABLED BY DEFAULT / NOT WIRED`.

The default runner exits before component execution. Explicit local evaluation can build baseline/replay artifacts, compare hard gates and inspect an Advisory shadow candidate. The result receipt requires `NO_RUNTIME_AUTHORITY` and confirms the main answer and Canon remain untouched.

R5B adds no startup, API, worker, persistence, retrieval, network, Canon, answer, delivery, tool, action or user-visible authority.

## After R5B

Milestone 1 recovery is complete only as a disabled tested composition. The next phase is not live activation. Required separately:

- trusted producers for events, assertions, attestations, open loops, compute signals and observations;
- one policy owner for attention, recall, eligibility, privacy and conflict facts;
- consent, tenant authorization, retention, erasure and durable evidence lifecycle;
- replay corpus, calibration, monitoring, rollback and operational SLO;
- anti-spam, localization, scheduling and cancellation;
- explicit operator approval and an activation ADR.

## Other current risks

- projection dispatcher remains implemented/tested but unwired;
- production compose profiles remain inconsistent;
- `server.py` remains a broad composition module;
- authentication remains shared API-key rather than per-user/tenant authorization;
- `core/identity_layer.py` remains `LEGACY/UNWIRED`; do not activate it.
