# Runtime audit: preserve data, lifecycle and producer/consumer contracts

Status: draft implementation stacked on audit integrity PR #523. No activation.

Base main: `485c4b0906ec35829ff7231c6276bf7d817f096f`.

The audit found successful-looking operations that dropped node properties, never
delivered events, left episode tasks alive, read stale blocks or misread producer fields.
The existing owners retain their decisions; this change repairs execution contracts.

- A derived edge insertion only creates missing endpoints; it cannot replace existing
  labels/properties. Existing explicit node upsert still replaces its payload.
- SQLite embedding methods close connections on all paths. A failed batch commit
  reports zero; row failures are visible. This remains a best-effort derived store.
- CoreMemoryBlocks reads a fresh committed SQLite snapshot. There is no competing
  process-local cache publication that can reorder commits or hide another instance.
- SleepTimeWorker start is idempotent; episode bursts coalesce to one owned think task;
  stop cancels and awaits the loop and all episode tasks. Default activation is unchanged.
- EventBus lifespan owns one consumer. Background publish without a live consumer
  dispatches inline, so acceptance is not silently parked. Delivery has the existing
  30-second budget; interrupted/failed delivery is parked in the existing bounded DLQ.
  Queue state remains volatile/process-local, queued items survive stop/start of the
  same bus object, and failure can have partial side effects. Exactly-once/durable replay
  is not promised. No new Canon writer or automatic promotion is introduced.
- Archive nesting is a ContextVar scoped to one parse; shared parser registries are
  never swapped during recursion. All child text reaches the downstream Reader,
  within existing archive extraction/depth budgets. No per-file text cut is added.
- MHI report consumers use the actual MHIReport fields. Facade bridges expose the
  actual passive Observer callable and caller-selected notebook; gist constraints
  are read only when the caller selects a session.
- VelantrimApp initializes lazy registrations in its constructor. Store replacement
  updates getters and dependent factories. Causal graph connections bind to the selected
  store and are explicitly owned/closed by the app, not an expired store context manager.
- GraphLab uses read-only owned connections, SQL seed/row budgets, exact node bounds
  and bounded short-cycle DFS (10,000 expansions / 250 ms / 50 outputs). Cycle budget
  exhaustion is explicit, never evidence of acyclicity. Domain bridge filtering is
  rejected as unsupported; full domain semantics are not invented by this patch.
- Multilingual startup wiring forwards domain and reuses the existing bounded candidate
  and recall owners. It honors use_ngram and returns explicit lexical retrieval scores.
- Role requests apply explicit domain/mode via the existing query policy before branch
  generation. Ordinary branch retrieval no longer loads the full store; operational
  failure is separate from empty evidence in BranchResult.retrieval_error_code.
- Dev exposure defaults to loopback. PATCH and MCP idempotency headers are allowed by
  the existing CORS policy. The morphology dependency matches installed pymorphy3.

Rejected: creating new write/promotion owners; loading entire corpora into role retrieval;
swallowing a failed commit; silently ignoring supplied scope; inferring cross-process
coherence from locks around a single instance; truncating Reader text to hide resource use.

Tests exercise producer→consumer behavior, real SQLite/Ladybug, commit fault injection,
parallel archive parsing, worker cancellation/restart, EventBus inline/background delivery,
GraphLab bounds and a differential cycle oracle. Exact results are recorded in the PR.
