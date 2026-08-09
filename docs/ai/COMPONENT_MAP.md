# 🗺️ Component and Authority Map

**Repository checkpoint:** `main@66318e6883590cb29a4565157e0a3a25b3716d81`  
**Controlled-enablement implementation:** issue #272 · PR #273  
**Machine state:** [`docs/state/project_state.json`](../state/project_state.json) · schema v6  
**Reality:** `IMPLEMENTED · TESTED · WIRED · ENABLEMENT MECHANISM PRESENT · RUNTIME CURRENTLY DISABLED · OPERATOR GO ABSENT · NOT OBSERVED · NO RUNTIME AUTHORITY`

## 1. Accepted Continuity lineage

| Capability | Primary surface | State / authority |
|---|---|---|
| Source adapters | `state_source_adapter.py`, `goal_source_adapter.py`, `open_loop_source_adapter.py` | tested proposals only |
| Admission evaluator | `admission_evaluator.py` | pure deterministic evaluation |
| Admission facade | `admission_facade.py` | accepted binding boundary |
| Current-decision resolver | `current_decision_resolver.py` | six-owner evidence composition; no live adapters selected |
| Durable lifecycle | `admission_artifact_lifecycle.py` | internal SQLite append/replay/cleanup/erasure owner |
| Runtime composition | `runtime_composition.py` | tested and wired in lifespan |
| Controlled enablement | `controlled_enablement.py` | exact bounded decision gate; no authority escalation |
| Composition root | `server.py::lifespan` via `api/server_middleware.py` | startup/shutdown only |

## 2. Exact internal path

```text
State / Goal / OpenLoop result
→ deterministic source adapter
→ complete Draft/evidence set
→ six-owner current-decision evidence
→ admission-aware facade
→ accepted facade-bound graph
→ ContinuityRuntimeCompositionOwner
→ ControlledEnablementController
→ current exact finite enable decision required
→ existing tenant-bound SQLite lifecycle
→ explicit append / exact-scope replay
→ STOP
```

No public endpoint invokes this path. No current activation manifest is recorded, so the
runtime remains disabled.

## 3. Controlled-enablement ownership

| Concern | Accepted responsibility | Boundary |
|---|---|---|
| Runtime configuration | existing immutable deployment contract | not Operator GO |
| Activation input | canonical manifest + SHA-256 | integrity, not authenticity |
| Binding | exact config/owner/tenant/storage/scope | no substitution/path injection |
| Lease | finite effective/expiry interval | expired/future decisions rejected |
| Ordering | positive monotonic sequence | stale/conflicting decisions rejected |
| Decision evidence | existing tenant-bound SQLite file | never a permission token |
| Operation gate | existing explicit append/replay | no producer/action authority |
| Diagnostics | content-free state evidence | no user side effect |

## 4. State machines

```text
Runtime owner:
NEW ↔ STARTED ↔ STOPPED

Enablement controller:
NEW → DISABLED ↔ ENABLED → STOPPED
```

`ENABLED` requires a current exact unexpired decision. Shutdown revokes in-process
enablement. Restart without a current manifest returns to `DISABLED`, regardless of old
persisted enable evidence.

## 5. Authority map

| Decision | Accepted owner |
|---|---|
| Canon / ESM state | canonical memory and write services |
| Truth admission | TruthGate / accepted write path |
| hard policy | PolicyKernel / PolicySnapshot |
| current identity/authorization/consent/restriction/erasure | external domain owners; no live adapters selected |
| admission decision | facade + pure evaluator |
| artifact persistence/replay | durable lifecycle selected by runtime composition |
| runtime startup/shutdown | existing FastAPI lifespan |
| bounded enable/disable decision validation | controlled-enablement controller |
| operator identity/authenticity | deployment governance; not established here |
| Operator GO project fact | absent |
| production observation | absent |
| production authority | absent |

## 6. Anti-bypass guarantees

- runtime configuration alone cannot enable the controller;
- partial/unknown/noncanonical activation input fails closed;
- callers cannot select database path, owner, tenant or scope;
- persisted decisions cannot silently re-enable after restart;
- higher-sequence disable dominates older enable;
- no second non-test `ContinuityArtifactStore` path exists;
- `/query` does not call append or replay;
- producer, Canon, ESM, TruthGate, GoalStack, reminder, notification, action, tool and
  scheduler effects remain absent;
- neither manifest digest nor replay grants authorization.

## 7. Historical state

| Checkpoint | Issue / PR | Merge | Meaning |
|---|---|---|---|
| Current-decision resolver | #263 / #264 | `dc30817f2c4abb1afcaab2f127e679d5f9b884d7` | schema v3 · 8/12 |
| Durable lifecycle | #266 / #267 | `064845579c520e7464678cd0c41d9b650368dfa8` | schema v4 · 9/12 · unwired |
| Bounded runtime composition | #269 / #270 | `802e833fa251a8831add8a6b802a5ebb57533549` | schema v5 · 10/12 · wired/disabled |
| Controlled enablement | #272 / #273 | `66318e6883590cb29a4565157e0a3a25b3716d81` | schema v6 · 11/12 · mechanism present/runtime disabled |

Historical schema v5 remains unchanged; only schema v6 records the new mechanism.

## 8. Remaining boundary

```text
Current state: 11/12 = 91.7%

Remaining:
1. live monitored/observed evidence under separate authority.
```

Continuity 12/12 has not started.
