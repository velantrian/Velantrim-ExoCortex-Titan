# ADR — Titan Sandbox runtime threat model and admission profile

Date: 2026-08-23
Status: Proposed
Scope: security requirements for a future runtime-capable sandbox backend; no executor implementation

## Context

`core.sandbox` now defines execution-neutral contracts and a `SandboxBackend`
lifecycle boundary. Those types deliberately provide no runtime authority. Before
Titan may add a backend that starts untrusted or semi-trusted workloads, the
security boundary must be explicit enough to review and test independently of a
specific runtime.

The primary threat is not merely a command failing. A workload may be malicious,
compromised, dependency-confused, or simply buggy and may attempt to read host
state, escape its workspace, consume host resources, reach unintended network
services, steal credentials, persist after teardown, forge provenance, or cause
sandbox output to be mistaken for trusted evidence.

## Decision

A future runtime-capable backend MUST fail closed against the admission profile
below. Passing the profile permits only bounded execution; it does not grant
Canon, evidence, deployment, promotion, or production authority.

### 1. Image provenance

- Mutable tags such as `latest` are not sufficient runtime identity.
- The admitted image MUST resolve to an immutable content digest before execute.
- The resolved digest MUST be recorded in backend provenance.
- Pull/build credentials MUST NOT be exposed inside the workload.
- The Titan production service image MUST NOT be treated as an arbitrary-code
  sandbox image merely because it is already hardened.

### 2. Filesystem boundary

- Root filesystem MUST be read-only.
- The workload receives one backend-owned ephemeral writable workspace.
- Host paths, Docker/Podman sockets, SSH agents, credential stores, home
  directories, repository roots, and arbitrary bind mounts are forbidden.
- Workspace path traversal and symlink escape MUST be rejected during artifact
  collection.
- Artifact export MUST copy only explicitly admitted files and MUST enforce byte
  and count limits.
- Teardown MUST destroy backend-owned writable state even after failure,
  cancellation, or timeout.

### 3. Process and privilege boundary

- Workloads MUST run as non-root with no privilege escalation.
- Privileged containers/namespaces are forbidden.
- Linux capabilities MUST be dropped by default; adding a capability requires a
  separate reviewed profile revision.
- Host PID, IPC, user, cgroup, and network namespaces are forbidden.
- Runtime control sockets/devices and host device passthrough are forbidden.
- Resource limits for CPU, memory, PIDs, writable bytes, and wall-clock time MUST
  be enforced by the backend rather than trusted to the workload.

### 4. Network boundary

- Network policy defaults to `DENY`.
- `ALLOWLIST` MUST be enforced outside the workload; environment variables or
  application-level promises are not enforcement.
- Loopback/metadata/control-plane endpoints MUST remain unreachable unless a
  future reviewed profile explicitly requires them.
- DNS resolution MUST NOT silently widen an allowlist. A backend must define how
  names are resolved and pinned/validated against the admitted destination set.
- No inbound listener is published to the host by default.

### 5. Secret boundary

- Host environment inheritance remains forbidden.
- No ambient cloud, GitHub, package-registry, SSH, Docker, or Titan credentials
  may enter a workload.
- `SandboxSpec.environment` is configuration, not a secret channel.
- Secret injection is NOT authorized by this ADR. A future secret mechanism
  requires a separate capability contract with explicit source, audience,
  lifetime, redaction, and non-export rules.

### 6. Lifecycle, cancellation, and cleanup

- `prepare` may allocate only backend-owned ephemeral resources.
- `execute` MUST bind the native runtime object to the exact `run_id`/attempt.
- Timeout/cancellation MUST terminate the entire workload process tree/runtime
  object, not only the original command process.
- `collect` MUST reject foreign/stale receipts and MUST never follow paths outside
  the admitted workspace.
- `teardown` MUST be idempotent and best-effort cleanup is insufficient for a
  successful security result: residual runtime objects are a failed teardown.
- Crash recovery MUST provide a way to enumerate and reap orphaned Titan sandbox
  resources by provenance label without touching unrelated runtime objects.

### 7. Observation and authority boundary

- stdout, stderr, exit code, generated files, and runtime metadata are untrusted
  observations.
- A successful exit code does not establish truth, safety, test validity, or
  provenance of the workload's claims.
- Backend provenance MUST include backend identity, immutable image identity,
  effective security profile identity, and execution attempt identity.
- Sandbox output can enter evidence/Canon only through an independent admission
  boundary outside `core.sandbox`.

## Adversary model

The backend MUST assume workload-controlled command arguments, repository/file
content, build scripts, package hooks, test code, and generated artifacts may be
hostile. It MUST also assume a compromised dependency may intentionally probe the
sandbox boundary.

The initial local backend is NOT required to defend against a vulnerability in
the host kernel or container runtime itself. That residual risk must be stated in
documentation. Workloads requiring a stronger hostile-code boundary should use a
future stronger isolation backend (for example gVisor/microVM) rather than
quietly weakening this profile.

## Required pre-implementation tests

A runtime backend PR must include negative tests proving at least:

1. mutable/unresolved image identity is rejected;
2. root/privileged execution is rejected;
3. host bind mounts and runtime sockets are rejected;
4. host environment is not inherited;
5. default network access is unavailable;
6. allowlist enforcement fails closed for unapproved destinations;
7. timeout kills descendants/runtime object;
8. artifact traversal and symlink escape are rejected;
9. artifact byte/count limits are enforced;
10. teardown removes runtime and writable state;
11. foreign run/receipt provenance is rejected;
12. no sandbox receipt can carry Canon/production authority.

## Explicit non-equivalences

```text
runtime-capable backend != trusted execution
container isolation != hostile-code VM isolation
image digest != trusted image
sandbox success != truth
sandbox success != evidence admission
SandboxSpec.environment != secret injection
teardown requested != teardown verified
```

## Consequences

The first concrete backend can now be reviewed against a stable security target
instead of inventing policy while implementing runtime calls. This intentionally
raises the implementation bar: a backend that cannot enforce the profile must
fail closed or remain experimental/non-runtime-capable.

## Not authorized by this ADR

This ADR does not add subprocess execution, Docker/Podman access, image pulling,
network access, filesystem mounts, secret injection, artifact persistence,
deployment, promotion, or production authority. A concrete backend remains a
separate PR and must reference this threat model.