# CSM Stage C Scanner — bounded evidence checkpoint

Date: 2026-08-15  
Issue: #333  
Draft PR: #335  
Admission base: `main@43e20f2a777079bf382c4c6512061edb83c6c0d5`

## Claim boundary

This evidence record is for a **Draft implementation candidate**, not current-main behavior.

The candidate introduces:

- CSM-local schema v2 scan lifecycle;
- explicit repository registration/root binding;
- explicit caller-manifest Python stdlib-AST scanning;
- repository-scoped lease/generation fencing;
- strict complete-scan promotion;
- atomic current-snapshot finalization;
- deterministic semantic snapshot reuse.

It does not claim:

- Stage D query/read API;
- Git-clean source attestation;
- automatic repository discovery;
- Tree-sitter/LSP/SCIP support;
- incremental/background scanning;
- Project Cognition or ProjectContextPack integration;
- MCP/A2A;
- Canon/Truth/Policy/Audit authority;
- runtime enablement or production readiness.

## Historical first candidate

Initial PR head: `1b0a18b4e38e47b8c17362f564f658483f7e265e`.

Observed checks on that historical head:

- Docker #813 — SUCCESS;
- CodeQL #67 — SUCCESS;
- Ruff — SUCCESS;
- blocking mypy — SUCCESS;
- reproducible wheel — SUCCESS;
- deterministic lock SBOM — SUCCESS;
- pytest — FAILURE in the newly-added test surface.

The first failure was traced to a regression-test setup that attempted to instantiate a Stage-B `ScanBudget` with `max_file_bytes > max_total_bytes`. That configuration is correctly rejected by the frozen contract before scanner execution. The test was corrected so that each file is individually admissible while the cumulative two-file payload exceeds `max_total_bytes`.

No production scanner invariant was weakened to make the test pass.

Historical results above do **not** transfer to later PR heads.

## Focused Stage-C coverage

New tests exercise:

### Schema lifecycle

- transactional v1→v2 migration;
- preservation/backfill of existing Stage-B repository/snapshot/receipt state;
- rollback of a failed versioned migration;
- new-repository scan-state initialization;
- per-repository scan-generation uniqueness;
- immutable operational lease events.

### Scanner semantics

- explicit repository registration/root fingerprint binding;
- idempotent identical registration and fail-closed root drift;
- Python structural extraction without repository-code execution;
- MODULE/CLASS/FUNCTION/METHOD identity;
- directed CONTAINS edges;
- unresolved IMPORTS edges;
- repeated import-edge deterministic collapse;
- source literal/docstring minimization from structural persistence;
- source-state `dirty=true`, `commit_sha=None`;
- manifest-order determinism;
- repeated semantic scan reuses one snapshot while generation/receipt advance;
- parser failure isolation and no promotion;
- file-size, total-byte, file-count and path-depth budgets;
- NUL/binary, non-UTF-8 and unsupported-extension rejection;
- symlink rejection;
- active-lease exclusion;
- expired-lease recovery to newer generation;
- stale-lease rejection;
- atomic-finalization rollback preserving prior current snapshot;
- lease TTL > max scan duration requirement.

## Security corpus element

One scanner test parses a repository file containing:

- executable top-level file-write code;
- a secret-like literal default;
- an instruction-like docstring.

Acceptance requires that parsing does not execute the top-level code and that the secret/instruction/body strings are absent from the structural persistence surfaces under test.

This proves only the bounded tested persistence surface. It is not a general secret-scanning or hostile-filesystem sandbox claim.

## Exact-head acceptance rule

The authoritative candidate is always the live PR #335 head, not the hash written into an earlier evidence paragraph.

Before Ready/merge, require on the final code+documentation head:

- Full CI SUCCESS;
- Ruff SUCCESS;
- blocking mypy SUCCESS;
- full pytest SUCCESS;
- coverage ratchet SUCCESS;
- Docker SUCCESS when spawned/applicable;
- CodeQL SUCCESS;
- aggregate merge evidence SUCCESS after Ready;
- zero unresolved review threads;
- same-page Notion synchronization/read-back;
- live-main race check.

If the head moves, all earlier exact-head CI becomes historical.

## Remaining limitations

- CSM schema v2 is local to CSM; Titan project-state schema remains v7.
- Python stdlib AST only.
- Explicit manifest only.
- No Git-clean source claim.
- No descriptor-level filesystem sandbox/openat guarantee.
- Incomplete scan receipts retain reason counts, while path-level problem objects remain returned candidate diagnostics rather than current-snapshot structural rows.
- Scan lease v1 does not renew; declared lease TTL must exceed declared max scan duration.
- Scan lifecycle events are operational custody rows, not Titan AuditChain.
- CSM remains runtime-unwired and non-canonical.

## Authority state

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

No authority value changes in this Draft.
