# Phase 2A — Capability Registry AI Handoff

**Parent:** #53  
**Tracking:** #299  
**Base:** `main@51058f2d5662edfdb91b037a46dce9297c441a1b`  
**Scope:** typed descriptor/provider-health/selection explanation contract only  
**Runtime:** UNWIRED / NOT ENABLED  
**Authority expansion:** NONE

## Read this first

Phase 2A must not be interpreted as LLM/provider activation. The new registry is a
read-side metadata and selection-explanation component. It owns no provider call, network
transport, Canon write, policy rule, QueryRouter decision or runtime composition.

Authority chain:

```text
ProviderDescriptor + CapabilityDescriptor + explicit ProviderHealth
                       |
                       v
               CapabilityRegistry
                       |
                       | asks for a lease
                       v
              existing PolicyKernel
                       |
             allow / deny + reason
                       |
                       v
                SelectionResult
```

`PolicyKernel` remains the permission owner. Registry selection cannot reinterpret a denied
lease. `auto` is ordering, not permission.

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

- validated stable descriptors;
- explicit provider health metadata;
- deterministic candidate evaluation;
- reason-coded selection/no-selection;
- trace-ready selection metadata.

The module is deliberately not wired into production/runtime callers in this milestone.

## Safety invariants

1. Remote provider metadata must declare `requires_network=True`.
2. Missing health is `UNKNOWN` and cannot be selected.
3. UNAVAILABLE providers cannot be selected.
4. DEGRADED providers lose to HEALTHY eligible providers.
5. Every HEALTHY/DEGRADED candidate is checked by existing PolicyKernel leasing.
6. Explicit preference cannot override lease denial.
7. Any lease-evaluation exception fails the whole selection closed.
8. Different policy snapshot/version values within one selection fail the whole selection
   closed; do not combine permission decisions from different policy moments.
9. Selection returns bounded explanation metadata; it performs no retry/provider probe.
10. No Canon/ESM/TRACE/Audit mutation occurs here.

## Out of scope

```text
embeddings/vector execution       OUT_OF_SCOPE
reranker execution                OUT_OF_SCOPE
LLM invocation                    OUT_OF_SCOPE
ADAO execution                    OUT_OF_SCOPE
ARM-04                            NOT_AUTHORIZED
remote consent implementation     OUT_OF_SCOPE
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
5. exact-head CI and review evidence on the Phase 2A PR

Before any later runtime wiring, re-audit current main and open a separate bounded issue.
