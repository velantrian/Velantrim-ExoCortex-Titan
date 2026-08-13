# Capability Registry Phase 2A Contract

**Tracking:** #53 → #299  
**Reality status in this PR:** implemented candidate · focused tests included · **UNWIRED** · **NOT ENABLED**  
**Authority:** descriptor/health/selection metadata only; the existing process-wide `PolicyKernel` remains permission owner.

## Purpose

Phase 2A adds a small contract for describing capabilities/providers, recording explicit
provider health, and explaining why one candidate was selected or why none was selected.
It does **not** call providers, replace `core/provider_catalog.py`, route the current query
path, or grant permission.

```text
registered metadata + explicit health
              |
              v
      CapabilityRegistry
              |
              | mandatory lease request
              v
        get_policy_kernel()
              |
              v
 deterministic SelectionResult
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

The production constructor takes **no policy/leaser parameter**. It always resolves the
existing process-wide owner through `get_policy_kernel()`. This prevents a future caller
from supplying an allow-all substitute through the registry API. Tests replace the
module-level lookup with `unittest.mock.patch` only inside the test process; that is not a
production extension point.

## Main types

### `ProviderDescriptor`

Provider-level metadata: `provider_id`, `locality`, `requires_network`, optional revision
and privacy class. A remote descriptor with `requires_network=False` is invalid. The
metadata contains no credential or consent state.

### `CapabilityDescriptor`

Capability-level metadata: `capability_id`, kind, provider reference, declared `data_mode`
(`none | redacted | raw`), optional model/revision, deterministic flag and bounded resource
metadata. `data_mode` is capability-specific and is forwarded to PolicyKernel as lease
input; it is never consent.

### `ProviderHealth`

The registry never probes providers:

```text
UNKNOWN      -> fail closed / not selectable
HEALTHY      -> PolicyKernel lease required
DEGRADED     -> PolicyKernel lease required; lower priority than HEALTHY
UNAVAILABLE  -> not selectable
```

### `CandidateEvaluation` / `SelectionResult`

The explanation separates:

- `health_reason_code` — provider health observation;
- `reason_code` — policy/selection eligibility result.

It also carries PolicyKernel snapshot/version evidence where a lease was evaluated.
`as_trace_metadata()` returns data only; it does not persist TRACE or AuditChain state.

## Selection precedence

```text
health eligibility
  > existing PolicyKernel lease
  > one consistent policy snapshot/version for the pass
  > HEALTHY over DEGRADED
  > explicit preference (if still eligible)
  > local over remote
  > deterministic over non-deterministic
  > stable capability-id tie-break
```

`auto` and explicit preference are ordering hints only. They cannot weaken network,
remote-data, locality or other PolicyKernel denials.

## Fail-closed behavior

Fail closed on:

- malformed typed metadata;
- duplicate provider/capability identity;
- unknown provider reference;
- unknown/unavailable health;
- unknown explicit preference;
- PolicyKernel denial or evaluation exception;
- different policy snapshot/version values inside one selection pass.

Failure returns a bounded result. It does not retry, probe, invoke a provider or mutate
another subsystem.

## Privacy and runtime boundary

The registry stores no user prompt, memory claim, provider result, token, secret or
credential. It performs no provider/network call and no Canon/ESM/TRACE/Audit mutation.

```text
implemented candidate:  true (PR branch only until merge)
wired:                  false
enabled:                false
provider calls:         false
network calls:          false
Canon writes:           false
Operator GO:            false
runtime authority:      false
production authority:   false
```

Any runtime composition requires a later, separately admitted milestone with its own
review, exact-head evidence and authorization.
