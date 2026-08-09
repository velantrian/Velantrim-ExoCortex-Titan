# ADR-2026-08-09: Bounded Continuity runtime composition

- Status: Proposed for the bounded implementation tracked by issue #269
- Date: 2026-08-09
- Repository baseline: `main@c2a60b5a54d2803b0e4de128df73e432b909dbf5`
- Scope: Continuity internal runtime wiring only
- Target state: implemented, tested, wired internally, not enabled, not observed,
  no runtime authority

## Context

The accepted Continuity chain already ends in a complete facade-bound admission result
and an explicitly invoked durable SQLite lifecycle:

```text
source result
→ deterministic Draft adapter
→ current-decision resolver
→ admission facade
→ accepted evidence graph
→ durable admission-artifact lifecycle
→ STOP
```

The historical lifecycle ADR intentionally records that this path was `UNWIRED`. The
lifecycle accepts a complete graph, assembles a content-addressed artifact, appends it
atomically, and supports exact-scope replay, bounded cleanup and erasure-addressable
neutralization. It does not select itself as a deployment owner and is not part of
server startup, shutdown, `/query`, a worker or a scheduler.

The tenth bounded Continuity capability is therefore composition, not enablement. The
system needs one deployment-owned lifecycle selection and one startup/shutdown owner
without creating a second application runtime or granting permission to use stored
evidence.

## Decision

Add `core/continuity/runtime_composition.py` and compose it around the existing FastAPI
lifespan that is installed by `server.py`.

`server.py` already calls `register_server_middleware(app)` after constructing the
FastAPI application. That registration function wraps the existing
`app.router.lifespan_context` exactly once. It does not create a second server or a
parallel startup system. The selected owner is held only on `app.state` while the
lifespan is active; no module-global singleton is introduced.

### Deployment configuration

Configuration is immutable, content-addressed and all-or-nothing. The deployment must
supply all four values:

- `VELANTRIM_CONTINUITY_RUNTIME_OWNER_ID`;
- `VELANTRIM_CONTINUITY_RUNTIME_OWNER_VERSION`;
- `VELANTRIM_CONTINUITY_RUNTIME_STORAGE_ROOT`;
- `VELANTRIM_CONTINUITY_RUNTIME_TENANT_REF`.

All four absent means:

```text
NO CONFIG
→ NO OWNER
→ NO SQLITE CREATION
→ NO IMPLICIT FALLBACK
```

A partial configuration fails startup. The only supported owner identity is:

```text
owner_id:      continuity.admission_artifact.sqlite
owner_version: 1
```

Unknown IDs and versions fail closed. There is no default-owner fallback.

The storage root must be an existing canonical absolute directory and cannot be a
symlink. The SQLite filename is derived from the deterministic configuration identity.
No persistence or replay invocation accepts a database path.

### Composition owner

`ContinuityRuntimeCompositionOwner` owns only:

- exact configuration and owner verification;
- deterministic SQLite location derivation;
- startup and shutdown state;
- one selected `ContinuityArtifactStore` instance;
- explicit accepted-graph persistence;
- explicit exact-scope replay;
- content-free diagnostic evidence;
- typed fail-closed error propagation.

The state machine is:

```text
NEW --startup--> STARTED --shutdown--> STOPPED
 |                 |                     |
 shutdown          startup               shutdown
 |                 |                     |
 v                 v                     v
STOPPED          STARTED               STOPPED

STOPPED --startup--> STARTED
```

A lock serializes startup, shutdown, append and replay through one logical owner.
Duplicate startup and shutdown are idempotent. Failed initialization never publishes a
started store. A cleanly stopped owner can restart.

Startup calls the existing lifecycle schema initializer and then validates the exact
selected table-column contract. Missing or incompatible schema fails closed before the
owner becomes `STARTED`.

### Accepted input boundary

The runtime owner accepts only `ContinuityAcceptedAdmissionGraph`, containing:

- principal and authorization contexts;
- source binding receipt and source envelope;
- complete Draft set;
- current-decision owner snapshots and composed evidence;
- admission registry and facade policy;
- `ContinuityAdmissionFacadeResult` with accepted Draft evidence;
- explicit retention policy and recording time.

It does not accept bare observations, bare Drafts, a raw evaluator result, a caller-built
artifact, caller owner identity, caller database path, caller tenant override or caller
subject override.

The existing `ContinuityAdmissionArtifact.create` remains the canonical graph validator.
The composition owner does not duplicate admission policy.

### Replay and recovery boundary

Replay is explicit and requires an exact `ContinuityArtifactScope`. Both append and
replay must match the deployment-bound tenant. The underlying lifecycle revalidates
artifact integrity, tenant, principal, authorization, subject set and policy snapshot.

The accepted claim is limited to:

> After a clean restart, the selected internal owner can revalidate configuration and
> schema, reopen the deterministic SQLite location, and perform explicit exact-scope
> replay.

This ADR does not claim backup/restore, disaster recovery, SLO, crash recovery,
automatic self-healing or production observation.

## Anti-bypass and side-effect boundary

The implementation must retain one non-test lifecycle construction path:

```text
FastAPI lifespan
→ ContinuityRuntimeCompositionOwner
→ ContinuityAcceptedAdmissionGraph
→ ContinuityAdmissionArtifact.create
→ ContinuityArtifactStore.append/replay
→ STOP
```

Static guards prove that no second non-test `ContinuityArtifactStore` path is added and
that `server.py` `/query` code does not reference the runtime owner or persistence
method.

The runtime composition does not import or call producer, Canon, ESM, TruthGate,
GoalStack, pipeline, LLM, reminder, notification, action, tool, delivery or scheduler
owners. Stored evidence and replay results retain `no_runtime_authority=True` and are not
permission tokens.

## Failure policy

Fail closed on:

- missing partial configuration;
- malformed or substituted configuration identity;
- unknown owner ID or unsupported version;
- non-canonical, missing or symlink storage root;
- tenant substitution;
- owner substitution;
- startup or schema initialization failure;
- incompatible selected schema;
- append or replay failure;
- operation outside `STARTED` state;
- non-facade-bound or unaccepted input;
- cross-tenant append or replay.

No exception is silently swallowed and no hidden retry loop is introduced.

## Explicit non-scope

This ADR does not add or authorize:

- Continuity 11/12;
- controlled enablement or a user feature flag;
- Operator GO;
- producer invocation;
- `/query` or answer modification;
- Canon, ESM, TruthGate or GoalStack writes;
- reminders, notifications, actions, tools or delivery;
- worker or scheduler activation;
- live monitoring, SLO, SLA, alerting or rollback orchestration;
- backup/restore or disaster-recovery claims;
- PostgreSQL, distributed storage, cloud sync or mobile integration;
- Phase II, ADAO, Research Copilot lifecycle or issue #249 work.

## Evidence required before acceptance

1. focused adversarial tests and static guards;
2. project-state validator, Ruff and blocking mypy success;
3. full pytest and coverage success on the exact implementation head;
4. required Continuity, Docker and aggregate workflow evidence;
5. submitted reviews, Codex comments and unresolved threads checked explicitly;
6. protected squash merge by exact head;
7. post-merge CI and aggregate success;
8. a separate status-sync PR preserving schema v1-v4 while introducing schema v5 only
   after exact evidence exists;
9. final synchronization and read-back of the existing Notion page.

Only after the separate status-sync merge may authoritative state advance to
`10/12 = 83.3%`. That state means implementation and internal-wiring readiness only.
