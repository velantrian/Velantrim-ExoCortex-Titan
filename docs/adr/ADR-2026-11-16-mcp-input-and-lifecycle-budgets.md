# Bound MCP transport inputs and process-local lifecycle

Status: draft implementation, not deployment activation.

Main at `485c4b0906ec35829ff7231c6276bf7d817f096f` buffers MCP bodies and batches
without bounds, invokes synchronous tools on the ASGI event loop and retains idle
session/lock state indefinitely.

Count actual streamed bytes before JSON parsing, with a configurable 1 MiB default.
Reject an excessive Content-Length early, but never trust it instead of counting.
Reject batches over 100 items before dispatch and JSON container depth over 64.
Invalid UTF-8, non-finite numbers, decoder recursion and invalid integer JSON return
fixed HTTP 400 responses; oversized envelopes/batches return 413. These HTTP envelope
budgets do not limit Reader source-document size. Operators may raise the positive
MCP_MAX_BODY_BYTES, MCP_MAX_BATCH_ITEMS and MCP_MAX_JSON_DEPTH settings.

Run synchronous dispatch in Starlette/AnyIO's existing bounded thread pool. This keeps
the event loop responsive and preserves sequential dispatch within a batch and existing
session serialization. A tool is not killed by an HTTP cancellation; cancellation is
not permission to re-execute a side effect. No second executor or action authority is
introduced. Execution timeouts, per-credential rate limits and durable operation-owned
idempotency remain separate contracts.

Session state uses an idle TTL of one hour and LRU capacity 4096. Access refreshes idle
TTL. Expiry/eviction removes only session metadata; it does not interrupt an active
operation. Lock entries are removed only after their last holder/waiter exits, including
anonymous scopes. These mechanisms remain process-local and do not promise cross-worker
or post-restart exactly-once execution. Existing authentication, capability ceiling and
operation-owned canonical writes remain authoritative.

Rejected alternatives: Content-Length-only enforcement; unbounded threads; dropping a
mutex while a waiter still references it; or imposing arbitrary Reader text truncation.

Tests include exact/over limits, absent Content-Length, real loopback Uvicorn chunked
HTTP, invalid JSON/UTF-8, dispatch-before-rejection controls, event-loop responsiveness,
TTL/capacity, and existing capability/idempotency/session serialization regressions.
