# ADR — Titan Sandbox Docker launch plan v0.1

Date: 2026-08-24
Status: Proposed
Scope: pure compilation of Docker security intent; no Docker API/CLI execution

## Context

Titan Sandbox now has contracts, a runtime security profile, digest-addressed
workspace manifests, verified content resolution, and backend-owned ephemeral
filesystem materialization. The next runtime step would configure an isolated
container. Encoding those controls directly inside runtime calls would make
security policy harder to review and test.

## Decision

Introduce a pure `DockerPlanCompiler` that converts an admitted `SandboxSpec`
and an open `EphemeralWorkspace` into an immutable `DockerLaunchPlan`.

The compiler performs no Docker API/CLI call and stores no Docker socket, daemon
host, credential, container ID, or host bind path.

Docker v0.1 security intent is fixed to:

- digest-pinned image only;
- non-root numeric user `65532:65532`;
- read-only root filesystem;
- `network_mode=none`;
- drop all Linux capabilities;
- `no-new-privileges:true`;
- explicit PID, memory, CPU, wall-clock, and writable-byte limits;
- exact `SandboxSpec.workspace_ref == EphemeralWorkspace.manifest_id` binding;
- explicit environment only, with no host environment inheritance.

## Network decision

Docker v0.1 supports only `NetworkPolicy.DENY`.

`ALLOWLIST` fails closed because ordinary Docker network configuration alone does
not satisfy the existing threat model requirement for external destination
allowlist enforcement and DNS pinning/validation. A later reviewed networking
adapter may add allowlisting without weakening this plan.

## Trust invariants

1. Plan compilation is not execution authorization.
2. `SandboxSpec` must pass the runtime security profile before a plan exists.
3. The filesystem workspace must still be open and exactly bound by manifest ID.
4. No caller can select bridge/host networking in Docker plan v0.1.
5. No caller can weaken the fixed user, read-only root, capability drop, or
   no-new-privileges settings.
6. CPU limits must be finite and positive before conversion to Docker nano CPUs.
7. A `DockerLaunchPlan` contains security intent, not runtime evidence.
8. Plan success does not imply Docker availability, workload success, truth,
   evidence admission, Canon admission, deployment, or production authority.

## Explicit non-equivalences

```text
DockerLaunchPlan != Docker container
plan compiled != workload executed
network_mode=none != general network policy implementation
image digest != trusted image
non-root container != hostile-code VM isolation
plan success != production authorization
```

## Follow-up

A later PR may add a concrete Docker runtime adapter consuming only
`DockerLaunchPlan`. That adapter must independently verify Docker daemon/runtime
capabilities, bind native container identity to `run_id`, enforce timeout and
resource limits, avoid ambient credentials/host namespaces/devices/sockets, and
verify container plus workspace teardown.

Workspace attachment remains an explicit runtime design question. This ADR does
not authorize arbitrary bind mounts merely because the workspace is backend-owned.