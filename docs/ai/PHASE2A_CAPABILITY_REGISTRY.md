# Phase 2A — Capability Registry AI Handoff

**Parent:** #53  
**Tracking:** #299  
**Implementation PR:** #300  
**Base:** `main@51058f2d5662edfdb91b037a46dce9297c441a1b`  
**Scope:** typed descriptor/provider-health/selection explanation contract only  
**Runtime:** UNWIRED / NOT ENABLED  
**Authority expansion:** NONE

## Read this first

Phase 2A must not be interpreted as LLM/provider activation. The registry is a read-side
metadata and selection-explanation component. It owns no provider call, network transport,
Canon write, policy rule, QueryRouter decision or runtime composition.

```text
ProviderDescriptor + CapabilityDescriptor + explicit ProviderHealth
                       |
                       v
               CapabilityRegistry()
                       |
                       | mandatory lease request
                       v
              get_policy_kernel()
                       |
             allow / deny + reason
                       |
                       v
                SelectionResult
```

`CapabilityRegistry()` exposes **no policy/leaser constructor argument**. Production code
cannot substitute a second permission owner through the registry API. Tests patch the
module-level `get_policy_kernel` lookup only inside the test process. `auto` and explicit
preference are ordering only, never permission.

## Existing owners that must be reused

- policy/network/remote-data/local-Canon boundary — `core/policy_kernel.py`;
- console LLM model catalogue — `core/provider_catalog.py`;
- compute-profile defaults — `core/compute_profile.py` / existing config;
- query routing — existing QueryRouter/pipeline;
- trace persistence — existing trace/analysis owners;
- Canon/ESM/TruthGate/WriteGate/AuditChain/VersionStore — unchanged owners.

Do not create a second owner for any of these.

## New bounded owner

`core/capability_registry.py` owns only:

- validated stable provider/capability descriptors;
- capability-specific declared `data_mode` passed to PolicyKernel;
- explicit provider health metadata;
- deterministic candidate evaluation;
- separate health reason and policy/selection reason codes;
- reason-coded selection/no-selection;
- trace-ready selection metadata.

The module is deliberately not wired into production/runtime callers in this milestone.

## Safety invariants

1. Policy authority is not constructor-injectable; use the existing `get_policy_kernel()`.
2. Remote provider metadata must declare `requires_network=True`.
3. Capability `data_mode` must be `none / redacted / raw`; it is policy input, not consent.
4. Missing health is `UNKNOWN` and cannot be selected.
5. UNAVAILABLE providers cannot be selected.
6. DEGRADED providers lose to HEALTHY eligible providers.
7. Every HEALTHY/DEGRADED candidate is checked by existing PolicyKernel leasing.
8. Explicit preference cannot override lease denial.
9. Any lease-evaluation exception fails the whole selection closed.
10. Different policy snapshot/version values within one selection fail closed.
11. Health reason remains separate from policy/selection reason.
12. Selection performs no retry/provider probe and no Canon/ESM/TRACE/Audit mutation.

## Out of scope

```text
embeddings/vector execution       OUT_OF_SCOPE
reranker execution                OUT_OF_SCOPE
LLM invocation                    OUT_OF_SCOPE
ADAO execution                    OUT_OF_SCOPE
ARM-04                            NOT_AUTHORIZED
remote consent implementation     OUT_OF_SCOPE
provider probing                  OUT_OF_SCOPE
network activation                OUT_OF_SCOPE
runtime route replacement         OUT_OF_SCOPE
runtime enablement                OUT_OF_SCOPE
Operator GO                       false
runtime authority                 false
production authority              false
schema v8                         NOT_CREATED
Continuity 13/12                  NOT_CREATED
```

## Validation route

Read:

1. `docs/adr/ADR-2026-08-13-phase2a-capability-registry.md`
2. `docs/operations/capability-registry-contract.md`
3. `core/capability_registry.py`
4. `tests/test_capability_registry.py`
5. `docs/ai/WORK_LOG.md`
6. exact-head CI, Docker, review threads and aggregate evidence on PR #300

Any earlier PR-head evidence is ancestor-only after a new commit. Before any later runtime
wiring, re-audit current main and open a separate bounded issue.
