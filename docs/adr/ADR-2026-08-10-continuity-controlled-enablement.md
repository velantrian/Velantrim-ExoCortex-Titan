# ADR-2026-08-10: Controlled enablement without runtime authority

- Status: Proposed for the bounded implementation tracked by issue #272
- Date: 2026-08-10
- Repository baseline: `main@6c4c6a584541d6a8d65374e84f4ec546984a8297`
- Scope: Continuity 11/12 internal controlled enablement only
- Target state: mechanism implemented, tested and internally wired; deployed runtime
  disabled unless one current exact operator decision is supplied; not observed; no
  production authority

## Context

Continuity 10/12 established one deployment-owned internal runtime composition:

```text
FastAPI lifespan
→ immutable runtime configuration
→ exact SQLite lifecycle owner
→ deterministic tenant-bound database path
→ explicit accepted-graph append / exact-scope replay
→ STOP
```

That composition is deliberately not enabled. Runtime configuration proves only which
internal owner and storage binding a deployment selected. It does not prove that an
operator authorized activation, that a lease remains current, that side effects are
permitted, or that production behavior was observed.

A plain boolean feature flag would collapse these states and would allow stale or
substituted configuration to masquerade as Operator GO. A new administrative service or
control plane would be disproportionate for this bounded slice and would create a second
lifecycle/authority surface.

## Decision

Add one internal module:

`core/continuity/controlled_enablement.py`

The module wraps the existing `ContinuityRuntimeCompositionOwner`; it does not replace or
duplicate it. The existing FastAPI lifespan composes the wrapper and retains the same
single application lifecycle root.

### Explicit deployment-owned decision

Controlled enablement uses two all-or-nothing deployment values:

- `VELANTRIM_CONTINUITY_ACTIVATION_MANIFEST`;
- `VELANTRIM_CONTINUITY_ACTIVATION_MANIFEST_SHA256`.

The manifest must be exact canonical JSON with no unknown or missing fields. It binds:

- schema version;
- action: `enable` or `disable`;
- positive monotonic decision sequence;
- operator reference;
- exact runtime configuration ID;
- exact lifecycle owner ID and version;
- exact tenant;
- content-free storage-location identity;
- the single supported internal append/replay scope;
- issued, effective and expiry times;
- `no_runtime_authority=true`;
- `no_side_effect_authority=true`.

An enable decision requires a bounded expiry. A disable decision has no expiry. Runtime
configuration without an activation manifest composes and starts only in `DISABLED`.
Activation configuration without complete runtime configuration fails startup.

The SHA-256 value proves deterministic integrity of the supplied canonical manifest. It
does not prove the human identity, legal authority or independent authenticity of the
operator. Those remain deployment/governance responsibilities and are not inferred from
a hash.

### State separation

The controller has these in-process states:

```text
NEW → DISABLED ↔ ENABLED → STOPPED
```

The following facts remain separate:

```text
mechanism implemented
≠ runtime currently enabled
≠ operator authorization present
≠ Operator GO recorded as project fact
≠ observed
≠ production-authoritative
```

The implementation may prove that a valid bounded enable decision can place a test
instance into `ENABLED`. The repository and status documents must still record the
actual deployment state independently. No activation manifest is committed to the
repository, so this implementation does not itself establish current Operator GO or a
currently enabled deployment.

### Monotonic and concurrent decisions

Activation decisions are append-only and ordered by a positive sequence number.

- replay of the same sequence and same digest is idempotent;
- a lower sequence is stale and rejected;
- the same sequence with a different digest is conflicting and rejected;
- a higher valid sequence supersedes the prior decision;
- a higher explicit disable dominates any older enable;
- one controller lock serializes in-process enable/disable races;
- SQLite `BEGIN IMMEDIATE`, primary-key and unique-sequence constraints fail closed on
  persistence conflict.

### Same-database audit evidence

Decision evidence is stored in a dedicated table inside the same deterministic
tenant-bound SQLite file already owned by runtime composition. No second database,
storage path, service, singleton or DI framework is introduced.

Each persisted row retains the canonical manifest, digest and exact indexed binding. On
startup, every persisted row is reconstructed and revalidated. Malformed JSON, digest
mismatch, substituted indexed values, authority flags, non-monotonic ordering or an
incompatible table schema fail closed.

Persisted evidence is not permission. After restart:

- no current manifest → controller remains disabled, even if an old enable row exists;
- the same current manifest → binding and lease are revalidated before enablement;
- expired, future-effective, malformed or conflicting manifest → startup fails closed.

### Operation gate

Only two existing internal operations are gated:

- `persist_accepted_admission`;
- exact-scope `replay`.

Both require:

1. the underlying runtime owner to be started;
2. controller state `ENABLED`;
3. one current unexpired enable decision;
4. the latest persisted decision to match the active decision exactly.

The controller then delegates to the existing runtime owner. It does not construct a
second `ContinuityArtifactStore`, accept a database path, weaken graph validation, or
turn replayed evidence into authorization.

### Lifespan integration

`api/server_middleware.py` keeps the existing one-time lifespan wrapper. It now composes
the controlled-enablement controller instead of exposing the bare runtime owner. Startup
passes an explicit UTC evaluation time; shutdown revokes in-process enablement and stops
the underlying owner.

The lifespan does not call append, replay, a producer, scheduler, action or public API.

## Fail-closed policy

Reject or refuse enablement for:

- absent runtime configuration combined with activation input;
- partial activation input;
- malformed or non-canonical JSON;
- unknown fields or schema version;
- invalid digest;
- unsupported action or scope;
- non-positive sequence;
- substituted configuration, owner, tenant or storage binding;
- caller-controlled path injection;
- authority flags other than exact `true` no-authority values;
- future-effective or expired enable lease;
- stale or conflicting decision sequence;
- enable before startup or after shutdown;
- malformed or incompatible persisted state;
- operation while disabled or after lease expiry;
- SQLite initialization, read or write failure.

No permissive fallback, hidden retry loop or automatic authority escalation exists.

## Authority matrix

| Concern | Owner after this ADR | Explicitly not granted |
|---|---|---|
| Runtime composition | existing `ContinuityRuntimeCompositionOwner` | enablement authority |
| Activation decision validation | controlled-enablement controller | operator authenticity |
| Decision evidence | same tenant-bound SQLite file | permission token semantics |
| Append/replay gate | controlled-enablement controller | producer or action authority |
| Admission and artifact validation | existing facade/lifecycle owners | new admission policy |
| Canon/ESM/TruthGate/GoalStack | existing canonical owners | any write from this slice |
| Public `/query` | existing legacy route | Continuity invocation |
| Operator GO project fact | explicit future operational evidence | inferred from implementation |
| Observation/production authority | Continuity 12/12 or later evidence | this ADR |

## Explicit non-scope

This ADR does not add or authorize:

- Continuity 12/12 or production observation;
- a committed live activation manifest or Operator GO;
- public rollout or user activation;
- producer invocation or event creation;
- Canon, ESM, TruthGate or GoalStack writes;
- reminders, notifications, tools, actions or delivery;
- worker, scheduler or autonomous loops;
- `/query` or answer changes;
- external telemetry, alerts, SLO/SLA or rollback orchestration;
- backup/restore, disaster recovery or multi-process deployment proof;
- a new control-plane service, endpoint, runtime, store, path, singleton or DI framework;
- issue #249, dependency upgrades, Phase II, ADAO or unrelated refactoring;
- production-readiness or independent-review claims.

## Required evidence before acceptance

1. focused and adversarial tests for configuration, binding, leases, persistence,
   idempotency, monotonic decisions, concurrency, restart and malformed state;
2. structural proof of one runtime/store path, unchanged `/query` and absent forbidden
   side-effect imports;
3. Ruff, blocking mypy and focused tests on the exact head;
4. project architecture checks, full pytest and blocking coverage;
5. Continuity, full Titan CI, Docker and exact aggregate merge evidence as required;
6. submitted reviews, Codex comments and unresolved threads checked on the exact head;
7. protected merge using the verified head SHA;
8. post-merge CI and aggregate evidence;
9. separate schema-v6 status synchronization preserving schemas v1-v5;
10. update and read-back of the existing Notion page only after final GitHub evidence.

Only then may authoritative implementation readiness advance to `11/12 = 91.7%`.
That status must record the enablement mechanism separately from actual runtime
activation, Operator GO, observation and production authority.
