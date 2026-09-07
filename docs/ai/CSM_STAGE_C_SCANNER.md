# Code Structural Memory — Stage C Scanner

Status: **IMPLEMENTED · TESTED · PROTECTED-MERGED · POST-MERGE VERIFIED · UNWIRED · NOT ENABLED · NON-CANONICAL · NO RUNTIME AUTHORITY**  
Tracking issue: **#333 · CLOSED / completed**  
Implementation PR: **#335 · MERGED**  
Protected squash merge: `b4c6f0c16ef9920607d95e590a75df8176d92d71`  
Historical reconciliation head (2026-08-16): `main@8ed2fb60c1edaa96d9af9955184c4abc31ef8500` — not today's repository head; re-query live GitHub  
Predecessor: PC-01 / CSM Stage B, merged via PR #326.

This page is the bounded AI hand-off for the first executable Code Structural Memory scanner slice. Stage C is now factual implementation truth in `main`; later commits, including PR #341, advanced the repository head without changing this scanner's authority or runtime posture.

## Purpose

Stage B froze deterministic structural contracts and a repository/snapshot-scoped SQLite boundary. Stage C adds the smallest explicit execution lifecycle needed to materialize those contracts from a caller-provided Python file manifest.

```text
explicit caller
    |
    v
registered repository root
    |
    v
repository scan lease + generation
    |
    v
bounded manifest validation/read
    |
    v
stdlib Python AST parse
    |
    v
in-memory structural staging
    |
    v
identity / budget / completeness validation
    |
    v
receipt + semantic snapshot CAS
    |
    v
atomic current-scan pointer
```

The scanner remains a **derived, rebuildable, repository-scoped, snapshot-bound, non-canonical projection producer**.

`INDEXED != UNDERSTOOD != CORRECT != SAFE != CANONICAL`.

## Public Stage-C API

Package: `core.code_structural_memory`

- `local_root_fingerprint(root)`
- `register_repository(conn, registration=..., root=...)`
- `scan_python_repository(...)`
- `ScanOutcome`
- bounded scanner/lease error types

There is no server route, startup hook, background worker, watcher, daemon, MCP adapter or default runtime call site.

## CSM-local schema v2

`core/code_structural_memory/schema.py` evolves the **dedicated CSM database** from v1 to v2.

This is **not** Titan project-state schema evolution. Titan project-state remains v7.

Stage C adds:

- one repository-scoped `next_generation` allocator;
- current semantic snapshot / latest scan generation / latest receipt pointer;
- one expiring repository-scoped scan lease;
- immutable operational lease lifecycle rows;
- exact receipt↔generation↔current-snapshot guard;
- unique scan receipt generation within a repository;
- transactional v1→v2 migration.

Lease-event rows are CSM operational custody receipts only. They are **not Titan AuditChain evidence** and do not become a second audit root.

## Source-state claim boundary

The Stage-C scanner is filesystem-only. It does not execute Git and does not have authority to claim that a working tree equals an exact commit.

Every scanner-produced source state is therefore:

```text
dirty = true
commit_sha = None
```

A future separately reviewed Git-aware attestation adapter would be required before CSM can claim an exact clean commit snapshot.

`dirty tree != exact commit snapshot` remains fail closed.

## Explicit manifest only

The caller supplies repository-relative paths. Stage C does not enumerate the repository by itself.

The manifest path is normalized and bounded before use:

- maximum observed file entries;
- repository-relative path only;
- maximum path depth;
- `.py` only;
- stable pre-existing symlink components rejected;
- registered repository root opened as an anchored directory file descriptor with no-follow semantics;
- intermediate components traversed relative to the anchored parent descriptor with `O_DIRECTORY | O_NOFOLLOW`;
- final file opened relative to its anchored parent with `O_NOFOLLOW`;
- `fstat()` and bounded `os.read()` operate on the same opened file object;
- platforms without the required `dir_fd` / `O_NOFOLLOW` support fail closed instead of falling back to pathname reads;
- per-file and total-byte limits;
- wall-time budget;
- NUL/binary and non-UTF-8 rejection.

The scanner does not:

- import repository modules;
- execute repository Python;
- run hooks;
- spawn shell commands;
- build/install packages;
- run repository tests;
- follow symlinks permissively.

## Parser baseline

The first evidence baseline uses Python stdlib `ast` only. Tree-sitter/LSP/SCIP remain later evidence decisions.

Stage-C node kinds:

- `MODULE`
- `CLASS`
- `FUNCTION`
- `METHOD`

Stage-C edge kinds:

- directed `CONTAINS`
- typed unresolved `IMPORTS`

Import resolution is intentionally conservative. An import target is stored as an `UnresolvedTarget`; the scanner does not fabricate a symbol/file node just to create a precise-looking edge.

Static calls, inheritance, decorators, references, test ownership and richer dependency projection remain later work.

## Data minimization

CSM persists structural coordinates and deterministic digests, not repository source bodies.

The scanner does not persist:

- function/class bodies;
- comments;
- docstrings;
- literal/default values;
- prompt-like repository text;
- runtime values;
- environment values;
- credentials.

An adversarial regression includes a source file containing both a secret-like literal and an instruction-like docstring and verifies that those strings do not appear in persisted structural rows.

## Completeness rule

Stage C v1 uses a deliberately strict promotion rule:

```text
any omission OR parser/read error
        |
        v
INCOMPLETE_REJECTED
        |
        +--> reason-count receipt retained
        +--> current snapshot unchanged
```

A complete scan is required before current-snapshot promotion.

This is stricter than a future profile-aware coverage model and prevents the first scanner from silently converting partial coverage into an `indexed` success claim.

## Semantic snapshot identity vs scan generation

The Stage-B invariant remains binding:

```text
semantic snapshot identity != scan generation
```

`generation` is stale-writer fencing/custody metadata. It remains outside `snapshot_id`.

If a later scan observes identical source/config/parser/graph semantics:

- a new scan generation is allocated;
- a new immutable scan receipt is recorded;
- the previously materialized content-addressed snapshot may be reused;
- current scan generation/receipt advances by exact lease/generation CAS;
- a duplicate semantic snapshot is not fabricated merely because time passed.

Before reuse, Stage C verifies the stored snapshot semantic header, node materialization and edge materialization against the deterministic candidate.

## Concurrency and failure contract

```text
acquire lease
  -> generation N
  -> scan/parse in memory
  -> begin finalization transaction
  -> verify exact token + generation + non-expiry
  -> receipt
  -> persist/reuse semantic snapshot
  -> current pointer CAS
  -> finalization event
  -> commit
```

Properties:

- one non-expired repository lease at a time;
- expired lease recovery gets a newer generation;
- stale holder/generation cannot finalize;
- finalization failure rolls back candidate receipt/materialization/current-head mutation;
- the previous current snapshot survives failed finalization;
- ordinary Python failures release only the exact current token best-effort;
- a process crash may leave an expiring lease; recovery is only after expiry.

Stage C v1 has no lease renewal. `lease_ttl_seconds` must exceed the declared maximum scan duration.

## Final merge and verification evidence

The accepted Stage-C implementation was protected-squash-merged through PR #335.

```text
tracking issue:                 #333 · CLOSED / completed
implementation PR:              #335 · MERGED
final accepted PR head:         2be69dc8c9007dd3fd7d9eae998e137095f1d4a1
protected squash merge:         b4c6f0c16ef9920607d95e590a75df8176d92d71
parent main:                     7a513724836fc9624f9870120215c06f94e97ad4
merge signature:                VERIFIED / valid
exact-head Full CI:             #1273 · 31927808211 · SUCCESS
exact-head Docker:              #855  · 31927808219 · SUCCESS
exact-head CodeQL:              #111  · 31927808241 · SUCCESS
READY aggregate:                #1519 · 31928109777 · SUCCESS
post-merge Full CI:             #1274 · 31928517680 · SUCCESS
post-merge Docker:              #856  · 31928517601 · SUCCESS
post-merge CodeQL:              #112  · 31928517705 · SUCCESS
post-merge aggregate:           #1520 · 31928517687 · SUCCESS
unresolved review threads:      0
```

The independent Manus follow-up found two material hardening requirements before final acceptance:

1. aggregate byte-budget accounting had to charge bounded reads even when decode/parse later rejected the file;
2. an equal-size symlink `swap-read-restore` race showed pathname checks were not a sufficient hostile-filesystem boundary.

Both were closed before merge. The final implementation anchors traversal/read to descriptors (`dir_fd`, `O_DIRECTORY`, `O_NOFOLLOW`, same-object `fstat(fd)` and bounded `os.read(fd)`), and unsupported required descriptor/no-follow capability fails closed. Earlier candidate CI/audit checkpoints remain historical evidence; the exact-head and post-merge results above are the accepted closure evidence.

## Known limitations

- Python only.
- Caller-provided manifest only; no tracked-file/Git attestation.
- Every scanner source state is dirty/no-commit.
- No Tree-sitter/LSP/SCIP.
- No incremental/watch mode.
- No Stage-D read/query API.
- No cross-repository edges.
- Import targets remain unresolved in this slice.
- Descriptor-anchored hostile-filesystem containment requires platform support for `dir_fd`, `O_DIRECTORY` and `O_NOFOLLOW`; unsupported platforms fail closed and do not use a permissive pathname-read fallback.
- `max_scan_seconds` remains cooperative rather than a preemptive interruption guarantee inside one OS read or AST parse operation.
- Incomplete attempt receipts persist deterministic omission/error reason counts; detailed path-level problems are returned by `ScanOutcome` but are not promoted into a current snapshot.
- CSM operational lease events are not tamper-evident Titan AuditChain evidence.

## Authority boundary

Unchanged:

```text
Continuity:             12/12
Titan project schema:   v7
runtime enabled:        false
Operator GO:            false
runtime authority:      false
production authority:   false
Canon:                  local
remote Canon:           forbidden
```

The Stage-C scanner has no Canon, ESM, TruthGate, WriteGate, PolicyKernel, QueryRouter, TRACE, Audit, answer, action or permission authority.

## Next boundary

Stage C closure does **not** admit Stage D.

A separate bounded admission decision is required before any repository/snapshot-scoped read/query API, automatic Git/repository attestation, Project Cognition ingestion, ProjectContextPack, MCP/A2A integration, review intelligence, semantic embeddings, runtime wiring or activation. Phase 3B remains **NOT ADMITTED / NOT STARTED** at this reconciliation checkpoint.
