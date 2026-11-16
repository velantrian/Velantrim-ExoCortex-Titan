# 🧵 Titan MCP Session Serialization v0.1

## Status

`BOUNDED IMPLEMENTATION · PROCESS-LOCAL · SIDE-EFFECTING TOOLS ONLY`

This increment closes the remaining OpenClaw-adoption invariant for
**per-session serialization of competing side-effecting runs**. It does not
import OpenClaw, create a second gateway, grant Canon authority, or claim
cross-process exactly-once semantics.

## Problem

Idempotency alone does not stop two different side-effecting calls on the same
MCP session from interleaving:

```text
session S
  → tools/call mutate_a  (in flight)
  → tools/call mutate_b  (starts before a finishes)
  → competing writes / torn intermediate state
```

Retry shields and session serialization are complementary:

```text
idempotency  = same key + same request → do not re-execute
serialization = same session side-effects → do not interleave
```

## v0.1 behavior

`core/mcp_transport.py` serializes **side-effecting** `tools/call` execution
behind a process-local per-scope `RLock`:

1. Explicit `Mcp-Session-Id` → scope `session:<id>`
2. Missing session → fallback scope `anon:<credential_fingerprint>:<capability>`

Read-only tools do **not** take the lock and may proceed while a side-effecting
call for the same session is in flight.

`DELETE /mcp` removes the session capability binding immediately. If a
side-effecting request is already executing or waiting on that session lock,
the lock entry is retained until all such requests leave; a later request with
the same ID therefore cannot overlap the in-flight critical section. The
entry is discarded once idle, avoiding permanent lock-map retention for deleted
sessions. This is process-local and does not cancel an operation already in
flight.

## Explicit non-claims

- not cross-process / multi-worker serialization;
- not cancel-on-supersede / generation-token preemption;
- not a durable queue or scheduler;
- not sandbox/policy/elevated split (separate increment);
- not identity, Canon, TruthGate, or Continuum authority.

Current Titan Docker/bootstrap posture still documents a single Uvicorn worker.
If multi-worker execution becomes an authorized deployment mode, cross-process
session serialization must be designed separately.

## Authority boundary

```text
session lock != permission
serialization != admission
tool success != Canon truth
OpenClaw pattern != OpenClaw import
```

## Tests

`tests/test_mcp_session_serialization.py` covers:

- same-session side-effects do not interleave;
- different sessions may overlap;
- read-only calls are not blocked by a same-session side-effect;
- idle session delete discards the lock entry;
- delete during an active side-effect preserves serialization, including through
  the authenticated HTTP gateway;
- scope key derivation for explicit vs anonymous sessions.

## Documentation impact

`GITHUB_ONLY` — focused operational transport contract over the existing MCP
handler. Notion: `NOT_REQUIRED`.
