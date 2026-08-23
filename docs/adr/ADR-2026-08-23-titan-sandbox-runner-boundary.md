# ADR — Titan Sandbox Runner trust and execution boundary

Date: 2026-08-23
Status: Proposed
Scope: contracts only; no execution backend

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

Introduce `core.sandbox` as a contracts-only boundary.

The initial contract contains:

- `SandboxSpec`: declarative execution request;
- `ResourceLimits`: bounded CPU, memory, process, writable-space, and time limits;
- `NetworkPolicy`: fail-closed by default (`DENY`), with explicit allowlisting;
- `SandboxRun`: lifecycle snapshot for one execution attempt;
- `ArtifactRef`: digest-addressed untrusted output;
- `ExecutionReceipt`: deterministic observation of an execution result.

No Docker/Podman/Firecracker/gVisor integration is added in this ADR.
No code path in `core.sandbox` starts a process, opens a network connection,
mounts a host path, reads host secrets, writes memory, or mutates Canon.

## Trust invariants

1. Sandbox execution is ephemeral in v0.1.
2. Host environment inheritance is forbidden.
3. Network access defaults to deny.
4. Network allowlisting must be explicit.
5. Resource limits are mandatory and positive.
6. Sandbox artifacts and receipts are untrusted outputs.
7. `SUCCEEDED` means only that the bounded execution reported success.
8. A receipt cannot carry `trusted`, `canon_admitted`, or
   `production_authorized` authority.
9. Sandbox output may become an evidence candidate only through a separate
   admission path outside this package.
10. The contract is backend-neutral; Docker is one possible future backend, not
    the semantic definition of the sandbox.

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
Sandbox Backend (future)
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
- Makes authority boundaries reviewable and testable before implementation.

### Costs

- A future backend must translate its native controls into these contracts.
- Backend-specific concepts may require additive contract revisions.
- This ADR intentionally delivers no executable sandbox functionality.

## Follow-up, not authorized by this ADR

A later PR may add a backend interface and one concrete implementation after a
separate threat-model review. Candidate backends include Docker/Podman for local
use and stronger isolation such as gVisor or Firecracker where threat posture
requires it.

That later PR must define filesystem mount policy, secret injection, network
enforcement, image provenance, artifact export, cancellation, cleanup, and
backend-specific escape mitigations before being considered runtime-capable.
