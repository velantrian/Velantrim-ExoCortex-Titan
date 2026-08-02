# Reader Core RDR-27 — Shadow burn-in result ledger

## Status

`MEASURED_RECEIPTS_ONLY / READY_ADMISSION_REQUIRED / BOUNDED_LEDGER / NO_EXECUTION / NO_PROMOTION_AUTHORITY`

RDR-27 records authenticated results produced by a separately reviewed isolated
shadow harness. It consumes the bounded RDR-26 campaign plan and one exact
RDR-26 `READY` status for each admitted attempt, verifies detached signatures,
and maintains a content-addressed campaign ledger.

RDR-27 does **not** execute Reader Core, call a provider, choose a model, schedule
background work, mirror production traffic, or connect to `/query`.

## Why this layer exists

RDR-26 answers whether a bounded campaign is currently armed. It deliberately
does not answer what a harness did after admission or whether cumulative limits
were respected.

RDR-27 adds an evidence-only boundary:

```text
signed RDR-26 plan
+ exact RDR-26 READY status at attempt start
+ signed pre-measured work receipt
        |
        v
content-addressed burn-in ledger
        |
        +--> cumulative budgets
        +--> contiguous attempts
        +--> failure streak
        +--> terminal campaign status
```

The ledger retains measured overruns instead of deleting inconvenient evidence.
Once an overrun or failure limit is visible, the ledger becomes terminal and no
further receipt can be appended.

## Shadow work receipt

`ReaderShadowWorkReceipt` binds one pre-measured attempt to:

- exact plan ID and plan-signature ID;
- exact RDR-26 status ID;
- exact environment ID and harness digest;
- explicit work-item ID;
- contiguous attempt number;
- canonical UTC start and completion times;
- exact wall time derived from those timestamps;
- result: `succeeded` or `failed`;
- model-token count;
- produced artifact-byte count;
- canonical artifact IDs;
- stable error code for failures.

A successful receipt cannot carry an error code. A failed receipt must carry one.
Every receipt is authenticated with a detached HMAC-SHA256 signature.

## Mandatory zero-side-effect evidence

Every receipt explicitly records and requires:

```text
production_traffic_observed = false
user_visible_output_emitted = false
background_scheduling_used = false
query_path_writes = 0
canon_writes = 0
memory_writes = 0
graph_writes = 0
tool_executions = 0
```

Any nonzero or true value is rejected at construction. This does not prove that
an arbitrary external process behaved correctly; it defines the only receipt
shape Titan will accept into this shadow evidence ledger. Independent harness
review and environment controls remain required.

## Admission gate

An empty ledger or appended receipt requires:

- a valid RDR-26 plan object;
- a valid detached plan signature;
- a status receipt bound to that exact plan and signature;
- status `ready`;
- `shadow_evaluation_authorized=true`;
- a valid detached work-receipt signature;
- receipt `status_id` equal to the exact READY status ID;
- receipt start time equal to the READY status evaluation time.

The exact-time equality intentionally prevents a stale READY receipt from being
reused as a timeless authorization token. A future harness must obtain a fresh
RDR-26 status for every attempt.

## Ledger invariants

The ledger copies immutable bounds from the signed RDR-26 plan:

- environment and harness identity;
- canonical work-item set;
- maximum attempts per work item;
- per-work-item timeout;
- total wall-time limit;
- total model-token limit;
- total artifact-byte limit;
- maximum consecutive failures.

Receipts must:

- belong to the exact plan, environment, and harness;
- reference only planned work items;
- start attempts at one and increment contiguously;
- never exceed the per-work-item attempt limit;
- never follow a successful attempt for the same work item;
- use strict canonical completion ordering;
- have unique detached-signature IDs.

## Statuses

`ReaderShadowBurnInLedger.status` is derived from ledger content:

- `ready`: no receipt yet;
- `in_progress`: valid receipts exist and more work may be admitted;
- `complete_success`: every planned work item succeeded;
- `complete_with_failures`: no work item can be retried and some never succeeded;
- `budget_exhausted`: per-item timeout or total wall/token/artifact budget reached;
- `failure_limit_reached`: consecutive failure limit reached.

All statuses except `ready` and `in_progress` are terminal. Appending to a
terminal ledger is rejected.

`complete_success` takes precedence only when every planned work item has
succeeded. Otherwise a reached budget remains visible as `budget_exhausted`.

## Budget handling

The ledger reports deterministic exhaustion codes:

- `per_work_item_timeout_exceeded`;
- `total_wall_time_exhausted`;
- `total_model_tokens_exhausted`;
- `total_artifact_bytes_exhausted`.

A measured receipt that reaches or exceeds a total budget is retained, and the
ledger closes. RDR-27 cannot stop an external process itself; the separate
harness and RDR-26 kill switch must enforce operational interruption.

## Security boundary

HMAC signatures demonstrate possession of the configured shared key. They do
not establish human identity, organizational role, delegation, or hardware
attestation.

RDR-27 provides no:

- pipeline or model execution;
- provider selection;
- production request mirroring;
- scheduler or worker;
- automatic retries;
- user-visible output;
- `/query` integration;
- Canon, memory, graph, policy, or tool writes;
- canary authorization;
- live authorization;
- Crystal or Native Kernel integration.

The distinction remains explicit:

```text
READY admission != executed work
signed receipt != independently attested behavior
complete shadow ledger != benchmark promotion
complete shadow ledger != canary authorization
complete shadow ledger != live authorization
```

A later stage may package and independently verify complete RDR-27 evidence,
but promotion must remain a separate explicit operator decision.
