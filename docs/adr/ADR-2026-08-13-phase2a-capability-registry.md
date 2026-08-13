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

- `ProviderDescriptor` — stable provider identity plus policy-relevant locality/network
  declaration;
- `CapabilityDescriptor` — stable capability identity, kind, provider reference,
  capability-specific `data_mode`, optional model/revision and resource metadata;
- `ProviderHealth` — explicitly supplied `UNKNOWN / HEALTHY / DEGRADED / UNAVAILABLE`
  state; the registry performs no probing;
- `SelectionResult` / `CandidateEvaluation` — reason-coded, trace-ready explanation that
  preserves health reason separately from policy/selection reason;
- deterministic candidate ordering after health and policy eligibility.

Every health-eligible candidate must be evaluated by the existing process-wide
`PolicyKernel.lease_capability()` contract. `CapabilityRegistry()` takes **no policy or
leaser argument** and always obtains the owner through `get_policy_kernel()`. This closes a
potential authority-bypass extension point: future production callers cannot inject an
allow-all substitute through the registry constructor. Tests patch the module-level lookup
only inside the test process; that is not a production API.

Remote provider descriptors are invalid unless `requires_network=True`, preventing
metadata from hiding egress from PolicyKernel. `data_mode` is declared per capability and
forwarded to PolicyKernel because one provider may host operations with different payload
exposure. The declaration is policy input, never consent.

If policy evaluation raises or produces more than one policy snapshot/version during one
selection, the entire selection fails closed. This avoids policy-TOCTOU without copying
PolicyKernel logic into the registry.

The registry is not wired into `pipeline.py`, `server.py`, ADAO, LLM, embeddings,
reranking or remote egress in this phase.

## Authority boundary

- **Canon/ESM writes:** none.
- **Background execution:** none.
- **Network/provider access:** none; no probe or invocation is performed.
- **Policy authority:** remains the existing process-wide `PolicyKernel`; the registry
  consumes leases only and exposes no alternate policy-owner injection API.
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

A capability descriptor's `data_mode` is declarative input to PolicyKernel; it is not
consent and does not authorize transmission. Unknown health is fail-closed. Remote provider
metadata cannot omit its network requirement.

## Failure semantics

Fail closed on malformed metadata, duplicate identity, unknown provider references,
unknown/unavailable health, unknown explicit preference, PolicyKernel denial/evaluation
error, or inconsistent policy snapshot/version across one selection pass.

A DEGRADED provider may be selected only when no HEALTHY eligible candidate wins the
conservative ordering. Failure returns a bounded `SelectionResult`; it does not retry,
probe, invoke a provider or mutate another subsystem.

## Observability and receipts

`SelectionResult.as_trace_metadata()` produces bounded metadata that an already-authorized
future trace owner may attach to its own AnalysisTrace. The registry itself does not write
TRACE or AuditChain records.

Metadata includes selected capability id, overall reason code, each considered capability,
provider health state, `health_reason_code`, eligibility/policy reason and the PolicyKernel
snapshot/version where a lease was evaluated.

## Rollback

The Phase 2A module has no runtime caller. Rollback is removal/reversion of the module,
tests and documentation. No persistent migration or state recovery is needed.

## Validation

Focused tests cover the non-injectable policy owner, remote-network declaration, malformed
descriptors, invalid capability data modes, unknown health, local selection,
capability-specific policy data mode, remote preference under network denial,
unavailable/degraded handling, policy exceptions and policy snapshot changes.

Repository Ruff, blocking Mypy, pytest, architecture-freeze, project-state, coverage,
Docker and aggregate merge-evidence gates remain required before protected merge where the
workflow applies.

## Explicit non-goals

This ADR does not authorize embeddings/vector execution, reranker or LLM execution, ADAO,
ARM-04, remote consent implementation, provider probing, network activation, runtime route
replacement, runtime enablement, Operator GO, runtime authority, production authority,
Canon mutation, remote Canon, Continuity 13/12 or schema v8.
