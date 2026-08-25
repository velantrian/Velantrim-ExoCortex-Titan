# 🔁 Titan MCP Side-Effect Idempotency v0.1

## Status

`BOUNDED IMPLEMENTATION · DRAFT · TRANSPORT RETRY SHIELD`

This increment adds a small retry-safety layer to the existing MCP transport. It does not create a second task system, transaction coordinator, identity system, or durable global event ledger.

## Problem

A client may execute a side-effecting tool successfully and lose the response because of a timeout or broken connection. Blind retry can then repeat the side effect.

```text
request
  → side effect commits
  → response is lost
  → client retries
  → duplicate side effect
```

## v0.1 behavior

Registered tools now declare whether they are side-effecting. The current side-effecting set is:

- `propose_hypothesis`
- `store_fact`
- `link_entity`
- `validate_fact`
- `contradict_fact`
- `supersede_fact`
- `forget_fact`
- `forget_all`
- `reset_graph`

Read-only tools remain uncached.

A caller may send:

```text
Idempotency-Key: <opaque visible-ASCII token up to 128 chars>
```

For a side-effecting `tools/call` that does **not** already own durable idempotency, Titan binds the key to:

```text
server-derived caller fingerprint
+ tool name
+ effective capability
+ canonical tool arguments
```

The first completed result is retained in a bounded process-local cache. A retry with the same key and same request returns the stored result without executing the tool again. Reusing the same key for different arguments fails closed.

JSON-RPC response IDs are not cached: a replay result is wrapped with the current request ID.

### Oversized responses

A completed side-effecting response may itself be very large. Counting cache entries alone would therefore not bound memory. v0.1 retains at most 64 KiB of replay payload per generic entry.

If the first response exceeds that ceiling, the original caller still receives the original response. The cache stores only a small replay marker. A retry with the same key receives that marker and the tool is **not** re-executed. The marker preserves the original `isError` class but honestly states that the original response body was not retained.

## Existing durable operation idempotency

`forget_all` already owns a durable `idempotency_key` contract inside its batch-erasure saga. The MCP transport therefore does not invent a competing cache or key namespace for that operation.

When `Idempotency-Key` is supplied and the operation argument is absent, the same transport key is passed into `forget_all(idempotency_key=...)`. Every retry is delegated back to the durable operation so it can resume/read back the same batch according to its own state machine. The process-local transport cache is deliberately bypassed for tools declaring `idempotencyArg`.

If both transport and operation keys are supplied and differ, the call fails closed before execution.

```text
transport retry key
        ↓
validate / reconcile
        ↓
existing operation idempotency key
        ↓
durable batch-erasure semantics
```

## Batch requests

For an HTTP JSON-RPC batch, one HTTP `Idempotency-Key` is deterministically scoped per JSON-RPC item using a fixed-length SHA-256 derivation over:

```text
validated <header-key> + canonical-json(<json-rpc-id>)
```

The original header key is validated **before** hashing, so derivation cannot turn an overlong or control-character key into an apparently valid digest. The resulting item key is `batch-<sha256>` (70 ASCII characters). JSON-RPC ID type is preserved by canonical JSON, so numeric `1` and string `"1"` derive different item keys; Unicode/whitespace string IDs remain safe because only the digest enters the transport idempotency surface.

Notifications without a JSON-RPC ID do not receive a derived idempotency key from the shared batch header.

## Compatibility

The feature is opt-in in v0.1. A side-effecting call without `Idempotency-Key` executes exactly as before. This avoids breaking existing MCP clients while exposing the safety contract in tool manifests through:

- `sideEffecting`
- optional `idempotencyArg`

A later version may make a key mandatory for selected high-risk operations only after client compatibility is proven.

## Hard limits / non-claims

The generic transport cache is:

- process-local;
- bounded to 1024 completed entries by default;
- bounded to 64 KiB retained replay payload per entry;
- lost on restart;
- not shared across multiple workers or hosts;
- bypassed when a tool already declares operation-owned durable idempotency.

Therefore:

```text
transport replay shield != exactly-once delivery
cache hit != durable receipt
idempotency key != permission
idempotency key != identity
same request != truth
successful tool execution != Canon authority
```

Titan's supported Docker and bootstrap runtime currently use one Uvicorn worker. If multi-worker execution becomes an authorized deployment mode, cross-process idempotency must be designed separately rather than pretending this process-local cache is sufficient.

## Authority boundary

This change does not alter:

- MCP capability ceiling;
- `PrincipalContext` authority;
- TruthGate / Guardian / Canon ownership;
- Reader authority;
- Soul identity semantics;
- Continuum continuity authority;
- provider routing;
- Sandbox authority;
- production authorization.

## Acceptance criteria

1. Same caller + same completed generic side-effecting request + same key replays the completed result without a second execution in the current supported single-worker runtime.
2. Same caller + same key + different arguments fails closed before a second generic execution.
3. Different server-derived callers may independently reuse the same opaque key.
4. Read-only tools are not cached.
5. Existing calls without an idempotency key remain compatible.
6. Operation-owned durable idempotency is delegated to and never shadowed by the transport cache.
7. Cache cardinality and retained replay bytes are bounded.
8. Batch-derived keys stay within the transport key bound and invalid source headers fail before derivation.
9. PR #397 stale capability visibility defense remains fail-closed.
10. No exactly-once, in-flight cross-thread, cross-worker, or post-restart durability claim is made.
