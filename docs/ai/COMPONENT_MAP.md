# 🗺️ Component and Authority Map

**Repository checkpoint:** `main@802e833fa251a8831add8a6b802a5ebb57533549`  
**Runtime-wiring implementation:** issue #269 · PR #270  
**Machine state:** [`docs/state/project_state.json`](../state/project_state.json) · schema v5  
**Reality:** `INTERNAL · TESTED · WIRED INTERNALLY · NOT ENABLED · NOT OBSERVED · NO RUNTIME AUTHORITY`

## 1. Accepted Continuity lineage

| Capability | Primary surface | State / authority |
|---|---|---|
| Source adapters | `state_source_adapter.py`, `goal_source_adapter.py`, `open_loop_source_adapter.py` | tested proposals only |
| Admission evaluator | `admission_evaluator.py` | pure deterministic evaluation |
| Admission facade | `admission_facade.py` | accepted binding boundary |
| Current-decision resolver | `current_decision_resolver.py` | six-owner evidence composition; no live adapters selected |
| Durable lifecycle | `admission_artifact_lifecycle.py` | internal SQLite append/replay/cleanup/erasure owner |
| Runtime composition | `runtime_composition.py` | tested and wired in lifespan; disabled and without authority |
| Composition root | `server.py::lifespan` via `api/server_middleware.py` | startup/shutdown owner only |

## 2. Exact internal path

```text
State / Goal / OpenLoop result
→ deterministic source adapter
→ complete Draft/evidence set
→ six-owner current-decision evidence
→ admission-aware facade
→ accepted facade result
→ ContinuityRuntimeCompositionOwner
→ continuity.admission_artifact.sqlite@1
→ derived tenant-bound SQLite location
→ existing durable lifecycle append / exact-scope replay
→ STOP
```

No public endpoint invokes this path. The lifespan selects and starts the owner only when
all deployment configuration fields are present. Missing configuration creates no owner
and no SQLite database.

## 3. Runtime-composition ownership

| Concern | Composition responsibility | Boundary |
|---|---|---|
| Configuration | frozen content-addressed deployment contract | no caller substitution |
| Owner selection | exact owner ID/version | unknown values fail closed |
| Storage | canonical absolute root + deterministic filename | no caller DB path |
| Tenant | exact deployment binding | cross-tenant use rejected |
| Startup | schema initialization and verification | one logical initialization |
| Shutdown | deterministic owner release | idempotent |
| Append | complete accepted graph only | existing lifecycle remains validator |
| Replay | exact scope after restart | evidence, never authorization |
| Diagnostics | content-free internal evidence | no user side effect |

## 4. State machine

```text
NEW --startup--> STARTED --shutdown--> STOPPED
 |                 |                     |
 shutdown          startup               shutdown
 |                 |                     |
 v                 v                     v
STOPPED          STARTED               STOPPED

STOPPED --startup--> STARTED
```

An `RLock` serializes startup, shutdown, append and replay through one logical owner.
Failed initialization never publishes a started store.

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
| controlled enablement | no accepted owner |
| Operator GO | absent |
| production observation | absent |

## 6. Anti-bypass guarantees

- bare observations, bare Drafts and raw evaluator results are not accepted;
- callers cannot supply artifacts, owner identity, database path, tenant or subject set;
- no second non-test `ContinuityArtifactStore` construction path exists;
- `/query` does not reference the runtime owner or persistence method;
- replay does not call a producer, action, tool or authorization owner;
- stored artifacts retain no runtime authority;
- no Canon, ESM, TruthGate or GoalStack writes are introduced.

## 7. Historical state

| Checkpoint | Issue / PR | Merge | Meaning |
|---|---|---|---|
| Current-decision resolver | #263 / #264 | `dc30817f2c4abb1afcaab2f127e679d5f9b884d7` | schema v3 · 8/12 |
| Durable lifecycle | #266 / #267 | `064845579c520e7464678cd0c41d9b650368dfa8` | schema v4 · 9/12 · unwired |
| Bounded runtime composition | #269 / #270 | `802e833fa251a8831add8a6b802a5ebb57533549` | schema v5 · 10/12 · internally wired |

Historical schema v4 remains `wired=false`; schema v5 alone records the new wiring.

## 8. Remaining boundary

```text
Current state: 10/12 = 83.3%

Remaining:
1. controlled enablement + explicit Operator GO;
2. live monitored/observed evidence.
```

Do not start 11/12 from this checkpoint automatically.
