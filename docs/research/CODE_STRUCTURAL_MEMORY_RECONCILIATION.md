# 🗂️ Code Structural Memory — Architecture Reconciliation

**Status:** `PROPOSED · DOCS-ONLY · NO RUNTIME AUTHORITY`  
**Historical source:** PR #30 head `c8cca1ca5422ccfc1a0da21a5963ebd067ccb076`  
**Reconciled against:** `main@3bc3607c503c2a32b7ab4f31753b7f9c10ee620f`  
**Disposition for PR #30:** `REVISE_AND_REPLACE`  
**Implementation:** separate future Draft PR only

## 1. Decision

Titan may maintain a deterministic, rebuildable structural index of a software repository. It is not canonical user/world memory and receives no truth, policy, answer or action authority.

```text
repository bytes + scan configuration
        ↓
trusted bounded discovery
        ↓
deterministic parser adapters
        ↓
staged structural records
        ↓
validation + repository generation CAS
        ↓
atomic current-snapshot promotion
        ↓
bounded typed structural queries
```

Core separation:

```text
canonical user/world memory
≠ project cognition documentation/history
≠ repository structural index
≠ LLM-generated code summary
```

The historical PR contains a useful architecture seed, but its stale branch must not be merged directly. This document resolves ownership, identity, concurrency, storage, security and lifecycle gaps before any implementation begins.

## 2. Non-authority boundary

This document creates no:

- parser dependency;
- database migration or table;
- repository registration;
- scan command, worker, scheduler or startup hook;
- MCP/tool endpoint;
- public API;
- automatic prompt injection;
- Canon, TruthGate or ordinary memory write;
- general RecallPolicy integration;
- code execution, build, import or shell command;
- LLM summary;
- runtime activation.

`INDEXED ≠ UNDERSTOOD ≠ CORRECT ≠ SAFE ≠ CANONICAL`.

## 3. Accepted owner map

| Concern | Owner | Rule |
|---|---|---|
| Repository structure | Code Structural Index projection | Rebuildable from repository bytes |
| User/world knowledge | Existing Canon and TruthGate paths | Code symbols never become ordinary facts automatically |
| Project decisions/history | Project Cognition and GitHub/Notion docs | Structural index does not replace human rationale |
| Policy and capabilities | PolicyKernel, PolicySnapshot, CapabilityLease | Indexer cannot infer or expand permission |
| Mutation safety | Existing mutation gates and explicit repository-index write service | No direct uncontrolled SQLite writes |
| AI prompt/context admission | ContextPack/Project Cognition policy | Query results are not inserted automatically |
| Event/receipt integrity | Neutral Claim → Event → Reduction → State → Projection → Receipt substrate | No second root of trust or uncontrolled graph store |
| Runtime activation | separate ADR and operator approval | No startup or background scan in architecture PR |

## 4. Repository identity

Every repository is registered explicitly and receives a stable `repository_id` independent of its local path.

Illustrative record:

```text
RepositoryRegistration
├── repository_id
├── canonical_origin?          # normalized remote identity when known
├── local_root_fingerprint
├── registration_policy_id
├── tenant_or_project_scope
├── created_at
├── status
└── retention / deregistration policy
```

Rules:

- local absolute paths are deployment metadata, not portable identity;
- two checkouts of the same origin may be distinct registrations when policy or tenant scope differs;
- one registration cannot silently change root or origin;
- symlinks cannot redefine the repository boundary;
- repository deregistration removes all derived snapshots, staging data and receipts under an explicit lifecycle;
- user-memory erasure must not accidentally delete an unrelated repository index, and repository deregistration must not leave derived code records behind.

## 5. Snapshot identity

Every query result binds to one immutable repository snapshot descriptor:

```text
RepositorySnapshot
├── snapshot_id
├── repository_id
├── generation
├── source_state
│   ├── commit_sha?
│   ├── dirty
│   └── tracked-file manifest digest
├── parser_profile_id
├── parser_versions
├── scan_config_digest
├── discovered_file_count
├── discovered_byte_count
├── structural_graph_digest
├── scan_receipt_id
└── promoted_at
```

A dirty working tree must never claim exact commit identity. Its snapshot identity includes the tracked-file manifest/content digest and `dirty=true`.

`snapshot_id` is content-addressed from canonical snapshot inputs. Wall-clock time is metadata, not semantic identity.

## 6. Stable node identity

Required identity shape:

```text
node_id = H(
  schema_version,
  repository_id,
  node_kind,
  normalized_relative_path,
  normalized_qualified_name
)
```

### Required fields

- `repository_id`;
- `node_kind`;
- normalized repository-relative path;
- normalized non-null `qualified_name`;
- structural source span;
- parser/profile identity;
- snapshot/generation reference.

### Identity exclusions

The following must not alter node identity:

- scan ID;
- timestamp;
- line number when the structural symbol is otherwise stable;
- alias spelling from a particular import site;
- parser diagnostic text;
- LLM output;
- ordering of unrelated files.

Anonymous/local constructs require a deterministic qualified-name policy based on structural containment and an explicit ordinal derived from parser order within the parent, never a random ID.

## 7. Stable edge identity

The historical RFC did not define edge identity precisely enough. Required shape:

```text
edge_id = H(
  schema_version,
  repository_id,
  edge_kind,
  source_node_id,
  target_node_id_or_normalized_unresolved_target
)
```

Possible edge kinds include:

- `CONTAINS`;
- `IMPORTS`;
- `DEFINES`;
- `INHERITS`;
- `CALLS_STATIC_CANDIDATE` only when the parser can justify the structural target;
- `REFERENCES_SYMBOL`;
- `DECORATED_BY`.

Rules:

- both resolved endpoints must belong to the same `repository_id` at schema and transaction levels;
- cross-repository edges are impossible unless a future explicit external-symbol contract is accepted;
- alias, source line, scan ID and timestamp remain edge metadata, not identity;
- unresolved targets are typed and normalized, not fabricated nodes;
- static candidates never claim dynamic runtime call certainty;
- edge provenance records parser adapter, source span and resolution rule.

## 8. Repository-scoped schema invariants

All primary, foreign and unique keys include or prove `repository_id`.

Illustrative constraints:

```text
UNIQUE(repository_id, node_id)
UNIQUE(repository_id, edge_id)
FOREIGN KEY(repository_id, source_node_id)
  REFERENCES nodes(repository_id, node_id)
FOREIGN KEY(repository_id, target_node_id)
  REFERENCES nodes(repository_id, node_id)
```

Every read API requires `repository_id`, including path-oriented calls such as `module_context`.

Forbidden:

- path-only global query;
- symbol lookup across all repositories by default;
- edges whose endpoint repository differs;
- nullable `qualified_name` in identity uniqueness;
- one uncontrolled second database or graph store.

## 9. Discovery boundary

The first accepted slice is Python-only and tracked-files-first.

Discovery must:

- resolve and freeze the repository root before scanning;
- reject root escape through symlinks, junctions or path normalization;
- prefer a bounded tracked-file manifest;
- reject unsupported file types;
- enforce file count, individual size, total byte, path depth and scan-time budgets;
- treat binary, generated, vendored and ignored files according to an explicit profile;
- isolate per-file read/parser failures;
- never execute repository code;
- never invoke repository-provided hooks;
- never interpolate untrusted paths into a shell command;
- record omitted files and reasons in the scan receipt.

A scan exceeding a hard budget fails or returns an incomplete staging result. It never silently promotes a partial snapshot.

## 10. Parser boundary

Tree-sitter may be an optional parser adapter, not a hard architectural dependency.

The parser layer returns bounded structural records only:

- module/package identity;
- classes, functions, methods and selected declarations;
- imports and aliases;
- containment;
- decorators and inheritance targets;
- safe signature shape;
- source spans and parser diagnostics.

Do not persist:

- full function/class bodies;
- arbitrary comments or docstrings by default;
- string/default literal values;
- credentials, tokens or secrets;
- generated natural-language summaries as primary representation;
- runtime values inferred by executing code.

Safe signatures must redact or hash literal defaults according to policy.

## 11. Scan lease, generation and concurrency

The historical design allowed staging before acquiring a lease. That permits overlapping writers and stale finalization.

Required sequence:

```text
acquire repository-scoped scan lease
→ allocate monotonic generation
→ discover manifest
→ parse into generation-scoped staging
→ validate counts, references and digest
→ compare active generation / lease token
→ atomic CAS finalization
→ release lease
→ emit receipt
```

The lease is acquired **before discovery/staging**.

A monotonic generation is carried through every staging row. Finalization rejects a generation older than the current active generation even if a lease expired and was later reacquired.

Lease requirements:

- repository-scoped;
- holder/token identity;
- issued/expiry time supplied by the owning service;
- bounded renewal;
- crash recovery;
- no automatic stale-holder overwrite without CAS;
- receipt for acquisition, recovery, rejection and release.

## 12. Staging and atomic finalization

Staging is never query-visible as the current snapshot.

Validation before promotion includes:

- all records belong to the repository and allocated generation;
- resolved edge endpoints exist in the same staged snapshot;
- identity uniqueness holds;
- structural spans are bounded and within file sizes;
- parser/config identity is complete;
- discovered manifest and parsed record counts reconcile;
- graph digest is reproducible;
- scan has not exceeded hard budgets;
- active generation has not advanced.

Promotion occurs in one database transaction:

```text
verify lease/generation CAS
→ mark previous snapshot non-current
→ mark validated staged snapshot current
→ write scan/promotion receipt
→ commit
```

A crash before commit leaves the prior current snapshot intact.

Abandoned staging data has bounded retention and explicit cleanup receipts. Cleanup cannot delete the active snapshot.

## 13. Structural graph digest

The digest is computed over canonical sorted structural records:

```text
H(
  schema_version,
  repository_id,
  source-state digest,
  parser/config identities,
  sorted nodes,
  sorted edges,
  normalized omissions
)
```

It excludes timestamps, database row IDs and diagnostic ordering.

Repeated scans of identical bytes under the same profile must produce the same structural digest.

## 14. Query boundary

All queries are:

- repository-scoped;
- snapshot-bound;
- bounded by result count, traversal depth and serialized byte size;
- read-only;
- deterministic for the same snapshot and request;
- typed and source-linked.

Possible first-slice APIs:

```text
find_symbol(repository_id, snapshot_id, qualified_name)
module_context(repository_id, snapshot_id, relative_path)
structural_neighbors(repository_id, snapshot_id, node_id, edge_kinds, depth)
reverse_imports(repository_id, snapshot_id, node_id)
impact_neighborhood(repository_id, snapshot_id, node_id, depth)
scan_status(repository_id)
```

`impact_neighborhood` means structural reverse-import/containment/reference neighborhood. It must not claim semantic runtime impact, breakage probability or correctness.

No query automatically enters an AI prompt. A separate Project Cognition/ContextPack policy decides whether bounded records are admitted to a model context.

## 15. Project Cognition relationship

```text
Code Structural Index
→ deterministic repository topology

Project Cognition
→ goals, decisions, architecture history, risks and engineering context
```

They may reference each other through explicit IDs and receipts, but neither automatically writes into the other.

Examples:

- Project Cognition may cite a snapshot/node ID when discussing a component;
- a code-review context pack may combine approved project documentation with bounded structural records;
- an LLM summary remains a disposable projection and is never the primary structural record;
- repository structure does not become evidence of human intent or product requirements.

## 16. Security and privacy threat model

Minimum threats:

- symlink/root escape;
- decompression or generated-file bombs;
- enormous/minified source files;
- parser crashes or pathological syntax;
- secret/literal ingestion;
- repository-controlled hooks or executable imports;
- path traversal in registration/query;
- cross-repository row/edge leakage;
- stale finalizer overwriting a newer snapshot;
- incomplete scan becoming current;
- prompt injection embedded in comments, names or strings;
- unbounded graph traversal;
- poisoned generated summaries;
- deregistered repository data remaining in derived tables;
- dirty tree misrepresented as a commit snapshot.

The structural layer treats all repository text as untrusted data, not instructions.

## 17. Receipts

A scan receipt contains:

```text
ScanReceipt
├── receipt_id
├── repository_id
├── generation
├── previous_snapshot_id?
├── candidate_snapshot_id
├── source_state / manifest digest
├── parser and config identities
├── counts and byte budgets
├── omitted/error reason counts
├── structural graph digest
├── lease/CAS result
├── final disposition
├── started_at / completed_at
└── no_runtime_authority = true
```

Receipts do not certify semantic correctness. They certify the declared bounded scan and promotion procedure.

## 18. Retention and removal

Separate lifecycles:

- source repository removal;
- repository registration revocation;
- staging cleanup;
- old snapshot retention;
- scan receipts;
- Project Cognition references;
- user-data erasure.

Repository deregistration must:

1. block new scans and queries;
2. remove active and historical derived structural records according to policy;
3. invalidate derived context caches;
4. preserve only the minimum permitted tombstone/receipt evidence;
5. prove no cross-repository records were removed.

## 19. Implementation sequence

### Stage A — architecture only

- merge this reconciliation;
- close historical PR #30 as superseded;
- synchronize GitHub and Notion;
- keep runtime implementation at zero.

### Stage B — contracts and schema Draft PR

- optional parser dependency declaration;
- immutable repository/snapshot/node/edge/receipt contracts;
- repository-scoped SQLite schema;
- migration rollback and compatibility tests;
- no scanner, endpoint or runtime wiring.

### Stage C — bounded Python scanner Draft PR

- explicit registration and command invocation only;
- lease-before-staging;
- deterministic parser adapter;
- staging validation and atomic CAS finalization;
- adversarial repository fixtures;
- no background worker.

### Stage D — bounded read API Draft PR

- repository/snapshot-scoped queries;
- strict budgets;
- no model context admission;
- no public network endpoint unless separately approved.

### Stage E — Project Cognition context adapter

Requires separate policy, evaluation and no-prompt-injection proof.

## 20. Mandatory tests before implementation merge

- repeated identical scans produce identical IDs/digest;
- file ordering does not affect output;
- dirty tree cannot claim clean commit identity;
- symlink/root escape is rejected;
- binary/oversized/deep/unsupported files are bounded and receipted;
- parser failure is isolated and cannot promote an incomplete snapshot;
- two concurrent scans cannot both finalize;
- stale generation cannot replace a newer current snapshot;
- crash before commit preserves prior current snapshot;
- cross-repository edge insertion fails at schema/transaction boundary;
- every path query requires repository and snapshot scope;
- `qualified_name` identity is non-null and normalized;
- no source body/secret/default literal is persisted;
- traversal budgets are enforced;
- repository deregistration removes only that repository's derived state;
- no automatic ContextPack, Canon, TruthGate or general recall integration.

## 21. Stop conditions

Stop and keep Draft if any change introduces:

- symbols as canonical facts;
- automatic TruthGate evidence;
- a second uncontrolled database/graph store;
- staging visible as current;
- scan after startup or on a background scheduler;
- repository code execution;
- full source-body or secret persistence;
- path query without repository scope;
- stale finalizer authority;
- cross-repository edges;
- unbounded traversal;
- automatic prompt injection;
- runtime implementation mixed with architecture approval.

## 22. Progress by state

```text
Architecture reconciliation:  1/1 = 100%
Schema/contracts:              0/5 =   0%
Scanner implementation:       0/8 =   0%
Tests/security corpus:         0/8 =   0%
Runtime wiring:                0/1 =   0%
Runtime readiness:             0/1 =   0%
```

## 23. Final disposition

```text
PR #30 = REVISE_AND_REPLACE
Concept = ACCEPTED AS DOCS-ONLY ARCHITECTURE
Implementation = separate future default-off Draft PR
```

The historical branch remains a research source and must not be merged directly.