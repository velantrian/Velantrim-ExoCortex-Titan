# Reader Core RDR-26 — Shadow burn-in campaign control

## Status

`SHADOW_CONTROL_PLANE_ONLY / EXPLICIT_SIGNED_TRANSITIONS / NO_RUNTIME_WIRING / NO_LIVE_AUTHORITY`

RDR-26 defines a deterministic control plane for a future isolated Reader Core
shadow burn-in. It consumes an active signed RDR-25 `approve_shadow_only`
decision, binds a bounded campaign to exact evidence and environment identity,
and records signed ARM, PAUSE, RESUME, STOP, and KILL transitions.

RDR-26 does **not** execute Reader Core. It does not add a worker, scheduler,
provider adapter, production mirror, `/query` hook, user-visible output, or
persistent write path.

## Why this layer exists

RDR-25 can state that an operator permits a later shadow-only evaluation. That
permission is intentionally too narrow to imply execution. Before any isolated
harness is reviewed, the project needs a stable answer to five questions:

1. Which exact signed operator decision permits the campaign?
2. Which environment, harness build, and work items are in scope?
3. What hard resource and failure budgets bound the campaign?
4. Is the campaign armed, paused, stopped, or killed now?
5. Is the underlying operator approval still active at the evaluation instant?

RDR-26 answers those questions without creating runtime authority.

## Artifact chain

```text
RDR-23 verified benchmark evidence
  + RDR-24 verified retained bytes
  + RDR-25 signed active shadow-only decision
        |
        v
ReaderShadowBurnInSource
        |
        v
ReaderShadowBurnInPlan
        |
        +--> detached HMAC-SHA256 plan signature
        |
        v
signed control receipt chain
ARM -> PAUSE -> RESUME -> STOP
  \-----------------------> KILL
        |
        v
explicit-time ReaderShadowBurnInStatusReceipt
```

Every artifact is content-addressed. Canonical loaders reject duplicate keys,
unknown or missing fields, non-finite JSON values, forged IDs, noncanonical
ordering, and noncanonical byte encodings.

## Campaign source

`ReaderShadowBurnInSource` records:

- campaign name;
- exact evaluation environment ID;
- exact harness digest;
- canonical planned start and end UTC timestamps;
- an explicit sorted set of work-item IDs;
- maximum attempts per work item;
- per-work-item timeout;
- total wall-time budget;
- total model-token budget;
- total artifact-byte budget;
- maximum consecutive failures;
- explicit condition codes.

No raw document text, human labels, model credentials, signing secrets, or
pipeline implementation is embedded in the source or plan.

## Plan construction gate

`ReaderShadowBurnInPlanBuilder` accepts only:

- a valid RDR-25 operator decision;
- disposition `approve_shadow_only`;
- a valid detached decision signature;
- status `active_shadow_approval` at the planned campaign start;
- a campaign window fully contained in the operator approval window;
- an optional valid RDR-25 revocation pair.

A revoked, expired, not-yet-valid, deferred, or no-go decision cannot produce a
plan.

The plan binds the exact:

- operator decision ID and signature ID;
- operator status receipt ID evaluated at campaign start;
- signed benchmark evidence ID;
- benchmark verification ID;
- retention manifest ID;
- retention verification ID;
- campaign source and budgets.

## Permanent authority boundary

A plan may set only:

```text
shadow_evaluation_authorized = true
```

The following fields are required to remain false in plans, control receipts,
and status receipts:

```text
production_traffic_authorized
user_visible_output_authorized
background_scheduling_authorized
query_path_wiring_authorized
canon_write_authorized
memory_write_authorized
graph_write_authorized
tool_execution_authorized
```

Construction and loading fail closed if any forbidden field is true.

`shadow_evaluation_authorized=true` in a plan is not sufficient to run work. A
current status receipt must also be `READY`, and a separate future reviewed
harness contract would still be required.

## Signed control chain

Each control source records:

- operator ID;
- action;
- canonical issue time;
- explicit reason codes;
- exact previous receipt ID when required.

Supported states and transitions are:

```text
initial: ARM  -> ARMED
initial: KILL -> KILLED

ARMED  -> PAUSE -> PAUSED
ARMED  -> STOP  -> STOPPED
ARMED  -> KILL  -> KILLED
PAUSED -> RESUME -> ARMED
PAUSED -> STOP   -> STOPPED
PAUSED -> KILL   -> KILLED
```

`STOPPED` and `KILLED` are terminal. Control times must increase strictly, and
all actions must occur before the campaign end. Every noninitial transition
references the exact previous receipt and verifies its detached signature.

KILL is deliberately available as an initial action. This lets an operator
publish a cryptographically bound kill state even before an ARM action exists.

## Explicit-time status evaluation

`ReaderShadowBurnInEvaluator` verifies:

- plan signature;
- exact plan-to-RDR-25 decision binding;
- exact control-to-plan binding;
- control signature;
- optional RDR-25 revocation and signature;
- current RDR-25 decision status at `as_of_utc`;
- campaign time window;
- latest control state.

Possible statuses are:

- `not_yet_valid`;
- `ready`;
- `paused`;
- `stopped`;
- `killed`;
- `expired`;
- `approval_revoked`;
- `approval_inactive`.

Only `ready` sets `shadow_evaluation_authorized=true`. It requires all of:

```text
operator approval active now
AND campaign time window active now
AND latest signed control state ARMED
```

A later RDR-25 revocation disables an armed campaign without requiring a new
RDR-26 control artifact.

## Operator CLIs

### Create a signed plan

```bash
python scripts/create_reader_shadow_burn_in_plan.py \
  --decision operator-decision.json \
  --decision-signature operator-decision-signature.json \
  --source shadow-burn-in-source.json \
  --plan-output shadow-burn-in-plan.json \
  --signature-output shadow-burn-in-plan-signature.json \
  --hmac-key-env RDR26_HMAC_KEY \
  --key-id shadow-plan-key-v1
```

Optional RDR-25 revocation inputs must be supplied as a pair.

### Apply one control action

```bash
python scripts/control_reader_shadow_burn_in.py \
  --plan shadow-burn-in-plan.json \
  --plan-signature shadow-burn-in-plan-signature.json \
  --source arm-source.json \
  --receipt-output arm-receipt.json \
  --signature-output arm-signature.json \
  --hmac-key-env RDR26_HMAC_KEY \
  --key-id shadow-control-key-v1
```

PAUSE, RESUME, and STOP additionally require the previous receipt and detached
signature. KILL may be initial or chained.

### Evaluate current status

```bash
python scripts/evaluate_reader_shadow_burn_in.py \
  --plan shadow-burn-in-plan.json \
  --plan-signature shadow-burn-in-plan-signature.json \
  --decision operator-decision.json \
  --decision-signature operator-decision-signature.json \
  --control-receipt arm-receipt.json \
  --control-signature arm-signature.json \
  --as-of-utc 2026-08-01T10:30:00Z \
  --status-output shadow-status.json \
  --hmac-key-env RDR26_HMAC_KEY \
  --require-ready
```

`--require-ready` returns exit code `3` for a valid non-READY status. Validation
or signature errors return exit code `2`.

All secrets are read only from the named environment variable. Outputs are
canonical JSON, output files must be distinct where applicable, and existing
files are never overwritten.

## Non-goals

RDR-26 does not provide:

- an executable shadow harness;
- production request mirroring;
- background scheduling;
- provider or model selection;
- threshold calibration;
- automatic retry or budget accounting receipts;
- user-visible comparisons;
- Canon, memory, graph, policy, or tool writes;
- `/query` integration;
- canary or live authorization;
- Crystal or Native Kernel integration.

Those remain separate reviewable stages. In particular:

```text
signed operator approval != active campaign
active campaign != executed work
READY status != production traffic authority
shadow evidence != canary authorization
burn-in success != live authorization
```
