# ADR — Phase 2A capability registry without authority expansion

- **Status:** accepted for bounded implementation by issue #299
- **Date:** 2026-08-13
- **Owner:** human maintainer/operator via #53 → #299 admission

## Context

Issue #53 defines a local-first adaptive-capability architecture. Phase 1 ModelFreeCore is
merged and post-merge hardened. The current Phase 2A audit confirms that Titan already has
an authority owner in `core/policy_kernel.py` for effective policy, network/remote-data
bounds, local-only canonical-write policy and reason-coded capability leases.

Titan also already has `core/provider_catalog.py`, but that file is a console-facing LLM
model catalogue. It does not own capability permission, provider-health admission or a
generic deterministic selection contract and must not be silently promoted into one.

The remaining bounded gap is descriptive and read-side: stable capability/provider
identity, explicit provider-health state, deterministic selection/no-selection reasons and
trace-ready explanation metadata. This must be implemented without creating a second
policy engine, runtime router or provider execution path.

## Decision

Introduce `core/capability_registry.py` as an **unwired, in-memory descriptor and selection
contract**.

It owns only:

- `ProviderDescriptor` — stable provider identity plus policy-relevant locality/network/data
  declaration;
- `CapabilityDescriptor` — stable capability identity, kind, provider reference, optional
  model/revision and resource metadata;
- `ProviderHealth` — explicitly supplied `UNKNOWN / HEALTHY / DEGRADED / UNAVAILABLE`
  state; the registry performs no probing;
- `SelectionResult` / `CandidateEvaluation` — reason-coded, trace-ready explanation;
- deterministic candidate ordering after health and policy eligibility.

Every health-eligible candidate must be evaluated by the existing
`PolicyKernel.lease_capability()` contract (through a structural `CapabilityLeaser`
interface for tests). Registry preference cannot convert a denied lease into permission.
Remote provider descriptors are invalid unless `requires_network=True`, preventing
metadata from hiding egress from PolicyKernel.

If policy evaluation raises or produces more than one policy snapshot during one selection,
the entire selection fails closed. This avoids policy-TOCTOU without copying PolicyKernel
logic into the registry.

The registry is not instantiated or wired into `pipeline.py`, `server.py`, ADAO, LLM,
embeddings, reranking or remote egress in this phase.

## Authority boundary

- **Canon/ESM writes:** none.
- **Background execution:** none.
- **Network/provider access:** none; no probe or invocation is performed.
- **Policy authority:** remains `PolicyKernel`; the registry consumes leases only.
- **Provider catalogue ownership:** existing `core/provider_catalog.py` remains the console
  LLM catalogue; it is not replaced.
- **Routing authority:** none; current QueryRouter/pipeline ownership is unchanged.
- **External actions:** none.
- **User-visible influence:** none; module is unwired.

`auto` and explicit capability preference are optimization hints only. Health and policy
eligibility dominate them.

## Data, scope and privacy

Registry state is process-local metadata. It contains provider/capability identifiers,
health reason codes, policy snapshot identifiers and configuration-like resource metadata.
It stores no memory claims, user content, prompts, provider responses, secrets or Canon.

A provider descriptor's `data_mode` is declarative input to PolicyKernel; it is not consent
and does not authorize transmission. Unknown health is fail-closed. Remote provider
metadata cannot omit its network requirement.

## Failure semantics

Fail closed on:

- malformed/ambiguous descriptor tokens;
- duplicate provider or capability identity;
- capability referencing an unknown provider;
- unknown or unavailable provider health;
- unknown explicit preference;
- PolicyKernel lease denial;
- PolicyKernel evaluation exception;
- inconsistent policy snapshot/version across one selection pass.

A DEGRADED provider may be selected only when no HEALTHY eligible candidate wins the
conservative ordering. Failure returns a bounded `SelectionResult`; it does not retry,
probe, invoke a provider or mutate another subsystem.

## Observability and receipts

`SelectionResult.as_trace_metadata()` produces bounded metadata that an already-authorized
future trace owner may attach to its own AnalysisTrace. The registry itself does not write
TRACE or AuditChain records.

Metadata includes selected capability id, overall reason code, each considered capability,
provider health state, eligibility reason and the PolicyKernel snapshot/version where a
lease was evaluated.

## Rollback

The Phase 2A module has no runtime caller. Rollback is removal/reversion of the module,
tests and documentation. No persistent migration or state recovery is needed.

## Validation

Focused tests cover:

- remote descriptors cannot hide network requirements;
- malformed/duplicate descriptors fail;
- unknown providers fail;
- unknown health is fail-closed;
- healthy local selection and trace-ready explanation;
- an explicitly preferred remote candidate cannot bypass network denial;
- unavailable preferred provider downgrades to an allowed local candidate;
- healthy candidates beat degraded preference;
- degraded-only bounded selection;
- policy exceptions fail the full selection closed;
- policy snapshot changes during selection fail closed;
- unknown explicit preference is not silently ignored.

Repository Ruff, blocking Mypy, pytest, architecture-freeze, project-state, coverage and
aggregate merge-evidence gates remain required before protected merge.

## Explicit non-goals

This ADR does not authorize embeddings/vector execution, reranker or LLM execution, ADAO,
ARM-04, remote consent implementation, provider probing, network activation, runtime route
replacement, runtime enablement, Operator GO, runtime authority, production authority,
Canon mutation, remote Canon, Continuity 13/12 or schema v8.
