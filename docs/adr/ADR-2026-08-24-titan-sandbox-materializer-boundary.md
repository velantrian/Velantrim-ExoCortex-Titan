# ADR — Titan Sandbox verified materializer boundary

Date: 2026-08-24
Status: Proposed
Scope: digest-only content resolution and verification; no filesystem or execution backend

## Context

The runtime threat model forbids arbitrary host bind mounts, and the Workspace
Manifest defines admitted sandbox inputs by relative destination path, SHA-256,
size, and executable bit. A runtime backend still needs a bounded seam between
that manifest and any future filesystem materialization.

Without an explicit seam, an implementation could accidentally treat a workspace
path as a host source path, skip digest verification, or fall back to ambient host
files when content resolution fails.

## Decision

Introduce a pure content-resolution layer before any filesystem writer:

```text
WorkspaceManifest
    -> BlobResolver.resolve(sha256)
    -> exact bytes
    -> digest + size verification
    -> VerifiedWorkspace bound to the exact WorkspaceManifest
```

`BlobResolver` receives only a content digest. It does not receive a host path or
workspace destination path. Resolution failure is fail-closed. Resolved payloads
must be immutable bytes and must exactly match both the declared SHA-256 and size.

`VerifiedWorkspace` retains the full bound `WorkspaceManifest` and rejects a file
set that does not exactly match the manifest descriptors. A manifest ID alone is
not sufficient binding.

## Trust invariants

1. Workspace destination paths are never interpreted as host source paths.
2. A missing digest fails closed; there is no path-based fallback.
3. Size and SHA-256 are verified before content becomes a verified workspace blob.
4. Mutable payload containers are rejected at this boundary.
5. Verified content is still untrusted input; digest equality is integrity, not truth.
6. `VerifiedWorkspace` is bound to the exact manifest, not merely a caller-supplied ID.
7. This layer performs no filesystem writes, symlink traversal, mounts, subprocesses,
   container-runtime calls, network access, or secret injection.
8. A future filesystem materializer must consume only verified workspace content
   and write only into backend-owned ephemeral storage.

## Explicit non-equivalences

```text
resolved blob != trusted blob
sha256 match != truth
VerifiedWorkspace != host workspace
VerifiedWorkspace != execution authorization
content resolver != filesystem resolver
```

## Follow-up

A later PR may add an ephemeral filesystem writer that consumes
`VerifiedWorkspace`, creates only backend-owned temporary state, uses no bind
mounts, rejects symlink/path escapes, verifies cleanup, and exposes no execution
capability by itself.

A Docker/Podman runtime backend remains a later separate change.