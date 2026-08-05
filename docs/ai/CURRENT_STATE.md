# 📍 Current System State

**Verified:** 2026-08-05  
**Current `main`:** `27b91a59f9e9291092b220ac1f53bfeae2daea28`

Verify material claims against exact SHAs, tests, workflows, wiring, configuration and runtime evidence. `MAIN`, `TESTED`, `WIRED`, `ENABLED` and `OBSERVED` are separate states.

## Continuity Milestone 1

Continuity Milestone 1 has been independently rebuilt on current `main` through five reviewed recovery layers:

| Layer | Merge SHA | State |
|---|---|---|
| R1 — immutable contracts | `06529700d70854504b88629eeecf737bdc6b81d5` | main, tested, unwired |
| R2 — process-local read-side and threads | `320d5ae9f89780efc553ffbfc3a17c1ebc83b47e` | main, tested, process-local, unwired |
| R3 — context/state/goal/open-loop projections and WorkingMemory adapters | `a19d16656676ad5c98c92d4776e9709edbfb920c` | main, tested, rebuildable, unwired |
| R4 — compatibility-preserving compute assessment | `529d8b6b182b1a548d27558173f0aca473bcc400` | main, tested, shadow-only, unwired |
| R5A — replay hard gates and Advisory Shadow v2 | `58e29bba26299ce7003b62e73fd3b25e028956de` | main, tested, shadow-only, unwired |
| R5B — complete disabled shadow runner | `27b91a59f9e9291092b220ac1f53bfeae2daea28` | main, tested, disabled by default, unwired |

### Complete shadow path

```text
ConversationEpisode
→ ThreadWeaver
→ Continuity context
→ State / Goal / OpenLoop projections
→ WorkingMemory adapters
→ existing WorkingMemoryGate
→ existing ContextPackBuilder
→ R4 compute assessment
→ R5A baseline/replay snapshots
→ ReplayEvaluationReport
→ R5A Advisory Shadow
→ immutable result + receipt
```

### Validation evidence for R5B

- final tested head: `8517c0d909b1e3465528f0bcc115265d8c1d1024`;
- Continuity workflow: `31025608097` — success;
- full Titan CI: `31025605121` — success;
- Docker hardening: `31025606554` — success;
- architecture freeze, branding, hygiene, Ruff, blocking mypy and full pytest passed.

### Authority status

R5B is **not** a live continuity feature. The default runner exits before component execution. No startup registration, API route, worker, scheduler, persistence, migration, retrieval, provider call, Canon/ESM/TruthGate mutation, answer modification, reminder delivery, tool call, action authorization or user-visible output exists.

Every runner receipt requires:

- `MAIN_ANSWER_UNTOUCHED`;
- `CANON_UNCHANGED`;
- `ADVISORY_SHADOW_ONLY`;
- `NO_RUNTIME_AUTHORITY`.

Historical stacked PRs #131–#147 were replaced by independently reviewed current-main recovery PRs; the remaining historical continuity PRs were closed without merge.

## Required before any live activation

- trusted and authenticated producers for events, assertions, attestations, open loops, compute signals and safety observations;
- one accepted policy owner for attention, recall, eligibility, privacy, protection and conflict facts;
- purpose-bound consent, tenant authorization, retention, erasure and durable evidence lifecycle;
- bounded input/resource policy and adversarial replay corpus;
- calibration, monitoring, rollback and operational SLOs;
- anti-spam, localization, scheduling and cancellation for any future advisory delivery;
- a separate activation ADR and explicit operator approval.

## Other current risks

- projection dispatcher is implemented and tested but remains unwired and unobserved;
- production compose profiles remain inconsistent;
- `server.py` remains a broad composition module;
- authentication remains shared API-key rather than per-user/tenant authorization;
- `core/identity_layer.py` remains `LEGACY/UNWIRED`; do not activate it.
