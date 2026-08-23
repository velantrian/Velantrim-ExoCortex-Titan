# ADR — Titan Sandbox backend-owned ephemeral workspace

Date: 2026-08-24
Status: Proposed
Scope: local filesystem materialization of already-verified inputs; no execution backend

## Context

The Workspace Manifest defines safe destination paths and content identities, and
the Materializer resolves those identities into `VerifiedWorkspace` bytes. A
future runtime needs those verified inputs in backend-owned writable storage, but
must not turn a user-controlled path into a host bind mount or ambient filesystem
capability.

## Decision

Add an `EphemeralWorkspaceWriter` that creates its own private OS temporary root
and accepts only `VerifiedWorkspace`.

The writer:

- exposes no parameter for a caller-selected host root;
- writes only manifest-bound verified payloads;
- creates destination directories only beneath the newly allocated root;
- uses exclusive file creation;
- applies owner-only permissions where the platform supports POSIX modes;
- flushes each file before use;
- rereads materialized files and verifies exact size and SHA-256;
- removes partially materialized state on failure;
- provides idempotent explicit cleanup and verifies the root no longer exists.

## Trust invariants

1. Caller/workload paths never select the host workspace root.
2. Only `VerifiedWorkspace` content may be written.
3. Workspace paths remain sandbox-relative destinations, never host source paths.
4. Materialization must remain beneath the allocated ephemeral root.
5. Existing destination files are not overwritten.
6. A partial write is not a usable workspace and triggers cleanup.
7. Successful materialization means only that verified bytes were reproduced on
   local ephemeral storage; it is not execution, evidence, or authority.
8. Cleanup requested is not sufficient: successful close requires the workspace
   root to be absent afterward.
9. This layer does not mount the directory into a container or start a workload.

## Explicit non-equivalences

```text
ephemeral workspace != sandbox execution
filesystem materialized != runtime authorized
private temp directory != hostile-code isolation
verified bytes on disk != trusted evidence
workspace path != arbitrary host path
```

## Residual boundary

This pre-execution writer does not claim to defend against a same-identity host
process racing filesystem operations or against kernel/filesystem compromise. A
future runtime backend must separately define how the workspace is transferred
or attached to the isolated runtime and how post-execution hostile filesystem
state is collected and destroyed.

## Follow-up

The next runtime-capable PR may introduce a concrete local container adapter only
if it enforces the existing runtime security profile, does not expose ambient host
paths or secrets, defaults networking to deny, binds native runtime identity to
`run_id`, enforces limits/timeouts, and verifies teardown.
