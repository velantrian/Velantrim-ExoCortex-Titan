# 🗺️ Component and Authority Map

**Repository checkpoint:** `main@39ba28dbf6bce4da1e18d6726ae4f4f79dc5f24e`  
**Bounded-observation implementation:** issue #275 · PR #276  
**Bounded observation canary:** issue #275 · operator-authorized · executed at this exact checkpoint  
**Machine state:** [`docs/state/project_state.json`](../state/project_state.json) · schema v7 — see `docs/ai/CURRENT_STATE.md`  
**Reality:** `IMPLEMENTED · TESTED · WIRED · ENABLEMENT MECHANISM PRESENT · OBSERVATION MECHANISM PRESENT · RUNTIME CURRENTLY DISABLED · OPERATOR GO ABSENT (CURRENT) · OBSERVED (HISTORICAL, ONE ROLLED-BACK CANARY) · NO RUNTIME AUTHORITY · NO PRODUCTION AUTHORITY`

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
| Bounded observation | `bounded_observation.py` | read-only, content-free evidence; one real rolled-back canary |
| Composition root | `server.py::lifespan` via `api/server_middleware.py` | startup/shutdown + open/close only |

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

ControlledEnablementController.diagnostic() / .lease_valid_at()
→ ContinuityBoundedObservationController.observe() [read-only]
→ fixed invariant checklist
→ content-free evidence row, same tenant-bound SQLite database
→ summarize_observation_session() [pure]
→ STOP
```

No public endpoint invokes either path. No current activation manifest is recorded, so
the runtime remains disabled, and nothing calls `observe()` automatically. One
operator-authorized canary exercised this exact path directly (a standalone script
calling the same production composition functions with an explicit `environ` mapping),
never through a public endpoint, and left the runtime disabled again afterward — see
`docs/adr/ADR-2026-08-10-continuity-12-12-bounded-observation-canary.md`.

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

## 3a. Bounded-observation ownership

| Concern | Accepted responsibility | Boundary |
|---|---|---|
| Diagnostic read | existing enablement `diagnostic()` / new `lease_valid_at()` | no state mutation |
| Invariant evaluation | fixed, closed seven-entry checklist | no caller-supplied invariants |
| Observation evidence | same tenant-bound SQLite file, dedicated table | never a permission token |
| Sequencing | positive monotonic, idempotent, conflict-rejecting | stale/conflicting sequence rejected |
| Session result | pure `summarize_observation_session` reduction | no Operator GO, no production authority |
| Canary evidence | one real, human-operator-authorized, rolled-back canary | single-use grant, exhausted; not a standing authorization |

## 4. State machines

```text
Runtime owner:
NEW ↔ STARTED ↔ STOPPED

Enablement controller:
NEW → DISABLED ↔ ENABLED → STOPPED

Observation controller:
NEW → READY → CLOSED
```

`ENABLED` requires a current exact unexpired decision. Shutdown revokes in-process
enablement. Restart without a current manifest returns to `DISABLED`, regardless of old
persisted enable evidence. The observation controller only reads `READY`; it never
transitions the enablement controller's own state and rejects `observe()` while the
underlying runtime is `NEW` or `STOPPED`.

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
| Operator GO project fact | absent (current) — the one canary grant is exhausted |
| observation mechanism | bounded-observation controller |
| real observed evidence | present (historical) — one operator-authorized, rolled-back canary |
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
- neither manifest digest nor replay grants authorization;
- the observation controller never calls `persist_accepted_admission` or `replay`,
  never issues/evaluates a decision, and constructing/persisting evidence cannot grant
  authority — `no_new_authority_granted`/`evidence_is_not_permission` are fixed `True`
  markers, not caller-supplied claims.

## 7. Historical state

| Checkpoint | Issue / PR | Merge | Meaning |
|---|---|---|---|
| Current-decision resolver | #263 / #264 | `dc30817f2c4abb1afcaab2f127e679d5f9b884d7` | schema v3 · 8/12 |
| Durable lifecycle | #266 / #267 | `064845579c520e7464678cd0c41d9b650368dfa8` | schema v4 · 9/12 · unwired |
| Bounded runtime composition | #269 / #270 | `802e833fa251a8831add8a6b802a5ebb57533549` | schema v5 · 10/12 · wired/disabled |
| Controlled enablement | #272 / #273 | `66318e6883590cb29a4565157e0a3a25b3716d81` | schema v6 · 11/12 · mechanism present/runtime disabled |
| Bounded observation mechanism | #275 / #276 | `456b762b1e752a2f5fb22762869336be9fed42a4` | schema v6 unchanged · 11/12 unchanged · mechanism present, real evidence `BLOCKED_ON_OPERATOR_GO` |
| Bounded observation canary | #275 | `39ba28dbf6bce4da1e18d6726ae4f4f79dc5f24e` | schema v7 · 12/12 · one operator-authorized, rolled-back canary; `observed=true` (historical), `enabled=false` (current) |

Historical schemas v1-v6 remain unchanged. Schema v7 is the current schema; it exists
because schema v6's shared validator could not represent `observed=true` while
`enabled=false` without conflating durable historical evidence with current runtime
state — see `docs/ai/CURRENT_STATE.md`'s "Machine-readable state" section and the
canary ADR.

## 8. Remaining boundary

```text
Current state: 12/12 = 100%

Remaining: none.
```

Continuity 12/12 is complete. This is not a production-readiness, production-authority,
or standing-Operator-GO claim — see `docs/ai/CURRENT_STATE.md`'s "Explicit non-goals
preserved" section and `docs/ai/KNOWN_RISKS.md`.

## 9. Post-Continuity canonical PII-redaction ownership

This section records a post-Continuity canonical-memory hardening decision; it does not
change the 12/12 Continuity checkpoint or runtime authority above.

| Concern | Accepted owner / surface | Boundary |
|---|---|---|
| PII detection/replacement policy | `core.forgetting.redact_pii()` | deterministic claim-text transformation only |
| PII claim mutation | `core.pii_redaction.CanonicalPiiRedactor` | narrow mutation-family service over existing `SQLiteGraphStore`; no general write authority |
| Legacy compatibility | `ForgettingEngine.redact_pii_fact()` / `.redact_pii_batch()` | adapter only; no direct raw-SQL claim UPDATE |
| Current Canon | existing `SQLiteGraphStore` transaction | CAS-guarded claim + integrity metadata + version bump |
| Version history | privacy-sanitized `fact_versions` | exact plaintext pre-image is intentionally not retained for redacted claim surface |
| Tamper-evident evidence | content-free `AuditChain` event | does not store removed claim payload |
| FTS | synchronous refresh in same SQLite transaction when present | rebuildable projection; never Canon |
| Other local projections | content-free migration-020 outbox refresh intent when active | no direct graph/vector authority added |
| Full physical erasure | `ErasureCoordinator` / batch erasure | separate contract; claim redaction is not Art. 17 proof for every storage surface |

See `docs/adr/ADR-2026-08-10-pii-redaction-privacy-history-exception.md` and
`docs/operations/canonical-pii-redaction.md`. Review-stage implementation is tracked in
#282 / PR #283 and is not implementation truth until protected merge evidence exists.
