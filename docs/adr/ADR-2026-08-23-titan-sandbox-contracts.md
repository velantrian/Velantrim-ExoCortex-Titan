# ADR — Titan Sandbox Runner v0.1 contracts

**Date:** 2026-08-23  
**Status:** Proposed  
**Scope:** Titan only

## Context

Titan already has a hardened production Docker image, a local-development Compose profile, domain-specific runners, and the cognitive Working Notebook. None of those components is a general-purpose bounded execution sandbox.

The production Docker image exists to package and run Titan itself. The Working Notebook models the user's current goals, constraints, priorities, materials, and open questions. Domain runners execute narrowly defined Titan pipelines. Reusing any of those components as an arbitrary code-execution surface would conflate responsibilities and trust boundaries.

## Decision

Introduce a dedicated `core.sandbox` contract layer before adding any execution backend.

The v0.1 package is declarative only. It defines:

- `SandboxSpec` — a requested bounded execution environment;
- `ResourceLimits` — mandatory ceilings for time, CPU, memory, PIDs, and writable storage;
- `NetworkPolicy` — fail-closed network posture;
- `SandboxRun` — lifecycle identity for one backend attempt;
- `ArtifactRef` — content-addressed references to produced artifacts;
- `ExecutionReceipt` — a tamper-evident observation of what a backend reports happened.

No v0.1 contract starts processes, shells out, talks to Docker/Podman, mounts filesystems, reads host secrets, writes Canon, deploys software, or grants promotion authority.

## Trust boundary

The core invariant is:

```text
sandbox success != truth
sandbox success != evidence admission
sandbox success != Canon write
sandbox success != production authorization
sandbox artifact != trusted artifact
CI green != deployment permission
```

`ExecutionReceipt` is explicitly an **untrusted observation**. It may later become input to another review or admission process, but it cannot carry `trusted`, `canon_admitted`, or `production_authorized` authority itself.

## Relationship to existing Titan components

```text
Working Notebook
    = cognitive workspace / current user intent

Domain Runner
    = executor for one specific Titan subsystem

Titan production Docker image
    = packaged Titan service runtime

Sandbox Runner
    = future bounded execution backend
```

The Working Notebook may eventually influence orchestration decisions, but it must not execute code itself.

The production Titan image must not be repurposed as the sandbox execution image by default. A sandbox backend may use containers as an implementation detail, but the contract intentionally remains backend-neutral so Docker, Podman, gVisor, Firecracker, Kubernetes Jobs, or another executor can be considered later.

## Fail-closed defaults

For v0.1:

- sandbox runs are ephemeral;
- host environment inheritance is forbidden;
- network access defaults to deny;
- network allowlists must be explicit;
- resource limits are mandatory and positive;
- artifacts are content-addressed by SHA-256;
- deterministic contract IDs are derived from canonical content;
- authority-bearing receipt flags are rejected.

## Non-goals

This ADR does **not** authorize or implement:

- Docker daemon access;
- arbitrary shell execution;
- repository checkout;
- package installation;
- network egress;
- secret injection;
- host bind mounts;
- privileged containers;
- persistent workspaces;
- automatic evidence admission;
- Crystal Canon writes;
- deployment or promotion.

Those capabilities require separate ADRs and explicit review.

## Future backend shape

A later implementation can satisfy a narrow interface conceptually equivalent to:

```text
prepare(spec) -> run
execute(run) -> receipt
collect(receipt) -> artifact refs
teardown(run) -> destruction receipt
```

The backend must enforce the contract rather than merely trust fields supplied by callers.

## Consequences

Positive:

- execution semantics become explicit before runtime code exists;
- Titan gains a stable place for future sandbox backends;
- Docker packaging remains separated from arbitrary execution;
- Working Notebook remains purely cognitive;
- receipts can integrate with Titan reasoning without silently becoming trusted state.

Trade-off:

- v0.1 is intentionally not useful for actually running code yet;
- future backend work must implement and prove the declared isolation guarantees.
