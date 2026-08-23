# ADR — Titan Sandbox Runner trust and execution boundary

Date: 2026-08-23
Status: Proposed
Scope: contracts and non-executing backend interfaces; no execution backend

## Context

Titan already has a production Docker image, a local-development compose profile,
Working Notebook state, domain-specific runners, and scattered subprocess usage.
Those facilities do not form a general-purpose isolated execution layer.

The production Docker image is a service runtime and supply-chain boundary. It
must not be repurposed as an arbitrary-code sandbox. Working Notebook is a
cognitive scratchpad and must not become an execution authority. Domain runners
execute specific Titan workflows and must not silently become a generic shell.

Titan needs an explicit place to model future bounded build/test/inspection
workloads without conflating execution success with truth or authorization.

## Decision

Introduce `core.sandbox` as a contracts-first boundary.

The initial contract contains:

- `SandboxSpec`: declarative execution request;
- `ResourceLimits`: bounded CPU, memory, process, writable-space, and time limits;
- `NetworkPolicy`: fail-closed by default (`DENY`), with explicit allowlisting;
- `SandboxRun`: lifecycle snapshot for one execution attempt;
- `ArtifactRef`: digest-addressed untrusted output;
- `ExecutionReceipt`: deterministic observation of an execution result.

Each execution attempt has an explicit `attempt_id`. `run_id` is derived from
`spec_id`, backend, and `attempt_id`, but not lifecycle status. This keeps one
attempt stable across PREPARED/RUNNING/terminal snapshots while preventing two
repeated executions of the same spec from collapsing into one provenance identity.

A follow-up protocol phase may define `SandboxBackend` plus deliberately
non-executing adapters/test doubles. Such code may model lifecycle behavior but
must not start processes, access container daemons, touch external networks,
mount host paths, inherit host secrets, or create a runtime execution surface.

No Docker/Podman/Firecracker/gVisor integration is authorized by this ADR.
No code path covered by this ADR starts a process, opens a network connection,
mounts a host path, reads host secrets, writes memory, or mutates Canon.

## Trust invariants

1. Sandbox execution is ephemeral in v0.1.
2. Host environment inheritance is forbidden.
3. Network access defaults to deny.
4. Network allowlisting must be explicit.
5. Resource limits are mandatory and positive.
6. Sandbox artifacts and receipts are untrusted outputs.
7. `SUCCEEDED` means only that the bounded execution reported success.
8. A receipt must describe a terminal run state and use coherent exit-code semantics.
9. A receipt cannot carry `trusted`, `canon_admitted`, or
   `production_authorized` authority.
10. Distinct execution attempts must have distinct provenance identities.
11. Sandbox output may become an evidence candidate only through a separate
    admission path outside this package.
12. The contract is backend-neutral; Docker is one possible future backend, not
    the semantic definition of the sandbox.
13. A protocol implementation or test double is not evidence that runtime
    execution authority has been approved.

## Explicit non-equivalences

```text
sandbox success != truth
sandbox success != Canon admission
sandbox success != promotion approval
sandbox success != deployment permission
artifact digest != trusted evidence
ExecutionReceipt != authorization
Working Notebook != execution sandbox
production Docker image != sandbox image
FakeBackend != execution capability
SandboxBackend protocol != runtime authorization
```

## Intended future flow

```text
User / Agent
    |
    v
Titan Orchestrator
    |
    v
SandboxSpec
    |
    v
Sandbox Backend (future runtime-capable implementation)
    |
    +--> ephemeral workspace
    +--> bounded command
    +--> resource/network policy
    +--> artifact collection
    |
    v
ExecutionReceipt + ArtifactRef[]
    |
    v
Titan reasoning
    |
    +--> optional evidence candidate
             |
             v
        separate admission boundary
```

## Consequences

### Positive

- Prevents ad-hoc subprocess calls from becoming an implicit generic executor.
- Keeps production Docker hardening separate from arbitrary-workload isolation.
- Gives future backends a stable semantic contract.
- Allows lifecycle orchestration to be tested without an execution surface.
- Makes authority boundaries reviewable and testable before implementation.
- Preserves per-attempt provenance across lifecycle transitions.

### Costs

- A future backend must translate its native controls into these contracts.
- Backend-specific concepts may require additive contract revisions.
- The orchestrator/backend must allocate a unique execution-attempt identifier.
- Protocol/test-double support intentionally delivers no executable sandbox functionality.

## Follow-up, not authorized by this ADR

A later PR may add one concrete runtime-capable backend only after a separate
threat-model review. Candidate backends include Docker/Podman for local use and
stronger isolation such as gVisor or Firecracker where threat posture requires it.

That later PR must define filesystem mount policy, secret injection, network
enforcement, image provenance, artifact export, cancellation, cleanup, and
backend-specific escape mitigations before being considered runtime-capable.
