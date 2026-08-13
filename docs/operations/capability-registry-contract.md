# Capability Registry Phase 2A Contract

**Tracking:** #53 → #299  
**Reality status in this PR:** implemented candidate · focused tests included · **UNWIRED** · **NOT ENABLED**  
**Authority:** descriptor/health/selection metadata only; the existing process-wide `PolicyKernel` remains permission owner.

## Purpose

Phase 2A adds a small contract for describing capabilities and providers, recording an
explicit provider-health snapshot, and explaining why one candidate was selected or why
none was selected.

It does **not** call providers. It does not replace the existing console-facing
`core/provider_catalog.py`. It does not route the current query path and it cannot grant
permission.

```text
registered metadata
  + explicit provider health
  + existing process-wide PolicyKernel lease
            |
            v
 deterministic SelectionResult
            |
            +--> selected capability id OR bounded no-selection reason
            +--> health reason + policy reason
            +--> policy snapshot/version evidence
            +--> trace-ready metadata (not persisted here)
```

## Ownership

| Concern | Owner |
|---|---|
| effective policy / network / remote-data permission | existing `core/policy_kernel.py` / `get_policy_kernel()` |
| console LLM model catalogue | existing `core/provider_catalog.py` |
| compute profile feature defaults | existing `core/compute_profile.py` / config owners |
| TRACE persistence/ownership | existing trace / analysis owners |
| capability/provider descriptive registry | `core/capability_registry.py` |
| provider invocation / egress | **not owned by Phase 2A** |

The registry consumes `CapabilityLease` results from the existing owner; it may not mint
permission or reinterpret a denial. The default registry constructor reuses
`get_policy_kernel()` and does not create another PolicyKernel instance. Test doubles may
be injected only to isolate the contract in tests.

## Main types

### `ProviderDescriptor`

Stable provider-level metadata:

- `provider_id`;
- `locality`: `local | remote`;
- `requires_network`;
- optional revision and privacy class.

A remote descriptor with `requires_network=False` is invalid. This prevents provider
metadata from hiding network egress from PolicyKernel. Provider descriptors contain no
credential or consent state.

### `CapabilityDescriptor`

Stable capability-level metadata:

- `capability_id`;
- capability `kind`;
- provider reference;
- declared `data_mode`: `none | redacted | raw`;
- optional model/revision;
- deterministic flag;
- small immutable resource-profile metadata.

`data_mode` is capability-specific because different operations on one provider can expose
different payload classes. It is forwarded to PolicyKernel as lease input and is never
interpreted as consent. Registration fails if the provider is absent or identity is
duplicated.

### `ProviderHealth`

Phase 2A never probes a provider. A caller must explicitly supply health:

```text
UNKNOWN      -> fail closed / not selectable
HEALTHY      -> policy evaluation required
DEGRADED     -> policy evaluation required; lower priority than HEALTHY
UNAVAILABLE  -> not selectable
```

No missing-health assumption becomes `healthy`.

### `CandidateEvaluation` / `SelectionResult`

The explanation preserves two different reasons rather than collapsing them:

- `health_reason_code` — why the provider is healthy/degraded/unavailable;
- `reason_code` — selection/policy eligibility result, including PolicyKernel denial.

`SelectionResult` contains:

- selected capability id or `None`;
- overall reason code;
- requested kind and preference;
- deterministic candidate evaluations;
- health state and health reason;
- lease/selection reason;
- PolicyKernel snapshot id/version where evaluated.

`as_trace_metadata()` only returns data. It does not persist TRACE or audit state.

## Selection precedence

```text
health eligibility
  > existing PolicyKernel lease
  > one consistent policy snapshot/version for the pass
  > HEALTHY over DEGRADED
  > explicit preference (if still eligible)
  > local over remote
  > deterministic over non-deterministic
  > stable capability id tie-break
```

Therefore:

```text
preference = auto
or preference = remote-capability

NEVER means:
network denied -> remote allowed
remote data forbidden -> remote allowed
provider unavailable -> provider allowed
policy dependency error -> fallback permission
```

An explicit preference can influence ordering only after health and policy have admitted
the candidate.

## Fail-closed reason codes

Representative result/candidate codes:

- `no_registered_capability`;
- `preferred_capability_unknown`;
- `provider_health_unknown`;
- provider-supplied unavailable/degraded health reason;
- existing PolicyKernel denial reason such as `network_denied`;
- `policy_lease_error`;
- `policy_evaluation_incomplete`;
- `policy_snapshot_changed_during_selection`;
- `no_allowed_healthy_capability`;
- `selected`;
- `selected_degraded_provider`.

## Policy-TOCTOU boundary

`PolicyKernel.lease_capability()` remains the sole permission evaluator. The registry
reuses the process-wide owner returned by `get_policy_kernel()` by default. Because the
existing lease method captures its own immutable snapshot, Phase 2A verifies that every
lease produced during one multi-candidate selection has the same snapshot id and policy
version. If they differ, selection fails closed rather than composing decisions from
different policy moments.

This is a consistency check, not copied policy logic.

## Privacy and data

The registry stores no user prompt, memory claim, provider result, token, secret or
credential. Capability `data_mode` is declarative policy input only and never counts as
consent. Provider health metadata is explicit input, not an active network probe.

## Runtime state

For this Phase 2A slice:

```text
implemented candidate:  true (PR branch only until merge)
tested:                 pending final exact-head CI after review-stage edits
wired:                  false
enabled:                false
provider calls:         false
network calls:          false
Canon writes:           false
Operator GO:            false
runtime authority:      false
production authority:   false
```

No caller should wire this contract in the same PR. Runtime composition belongs to a
separate admitted milestone with separate evidence and authorization.
