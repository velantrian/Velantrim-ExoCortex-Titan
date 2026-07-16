# RFC — Code Structural Memory Adapter for Velantrim Titan

**Status:** Draft / research architecture only  
**Runtime impact:** none in this RFC  
**Target implementation:** Python-only MVP  
**Feature flag:** `ENABLE_CODE_STRUCTURAL_MEMORY=false` by default  
**External inspiration:** `divyanshailani/graph-memory` (`Skeleton-to-Meat` pattern)  
**Code reuse status:** clean-room implementation required unless the upstream repository publishes an explicit license file or the author grants written permission

---

## 1. Purpose

Titan already provides long-term fact memory, epistemic states, provenance, recall policy, hybrid retrieval, graph analysis and privacy controls. What it does not yet provide is a deterministic structural model of a software repository.

This RFC defines a **Code Structural Memory Adapter** that maps source code into a bounded, queryable graph:

```text
Repository
├── Directory
├── File
├── Class
├── Function
├── Method
└── Dependency
```

The component is intended to help coding agents answer questions such as:

- Where is a mechanism implemented?
- Which modules import or depend on this file?
- What symbols are defined in a module?
- Which files may be affected by a proposed change?
- Which imports disappeared after a commit?
- Which architectural area contains a symbol?
- Which dependency cycles or high-centrality modules exist?

The adapter is **not** a replacement for Titan memory, TruthGate, RecallPolicy, HybridRetriever or Graph Lab. It is a new deterministic perception/indexing layer for code.

---

## 2. Core decision

The code graph MUST be an **operational structural index**, not canonical user/world memory.

```text
Titan canonical memory
  facts / evidence / ESM / TruthGate / RecallPolicy

Titan code structural memory
  repository snapshots / AST nodes / dependency edges / scan receipts
```

The MVP MUST use the same Titan-controlled SQLite database path, but MUST use dedicated tables and a dedicated adapter contract. It MUST NOT write source-code symbols into the canonical `facts` table or user-memory graph.

Rationale:

1. Code symbols are high-volume operational metadata, not ordinary semantic facts.
2. Writing thousands of symbols into `facts` would pollute recall and complicate erasure, promotion and epistemic transitions.
3. A second independent `.agents/graph_memory.sqlite` database would create a second source of truth and a second lifecycle to secure, back up and delete.
4. Dedicated tables in the same controlled database preserve one operational boundary while maintaining strict logical separation.

---

## 3. Non-goals for the MVP

The first implementation MUST NOT include:

- LLM-generated module summaries;
- MCP write tools;
- autonomous agent writeback;
- visual graph export;
- JavaScript, TypeScript, Go or Rust parsing;
- call-graph inference;
- type inference;
- dynamic import execution;
- package renaming or broad Titan refactoring;
- a separate SQLite database;
- direct writes to canonical memory;
- trust decay based on age;
- `trust_score` as the sole truth model;
- copying `graph-memory` engine or schema code.

These may be evaluated in later RFCs after the Python structural core is stable.

---

## 4. Architectural position

```text
Git repository / working tree
        │
        ▼
Repository Snapshot Resolver
        │
        ▼
Python Tree-sitter Scanner
        │
        ▼
Code Entity Normalizer
        │
        ▼
Internal Import Resolver
        │
        ▼
Staging Tables (scan-scoped)
        │
        ▼
Atomic Scan Finalizer
        │
        ▼
CodeGraphStore (same Titan DB, dedicated tables)
        │
        ├── CodeStructuralRetriever
        ├── ImpactAnalyzer
        ├── ArchitectureDiff
        └── Graph Lab adapter (read-only, later increment)
```

The scanner MUST be deterministic for the same input bytes, parser version and configuration.

---

## 5. Proposed package layout

```text
core/code_memory/
├── __init__.py
├── models.py
├── stable_ids.py
├── repository_snapshot.py
├── tree_sitter_python.py
├── import_resolver.py
├── scan_store.py
├── scan_finalizer.py
├── structural_retriever.py
├── impact_analyzer.py
├── metrics.py
└── errors.py
```

Optional later modules:

```text
moc_builder.py
summary_service.py
mcp_read_adapter.py
architecture_diff.py
```

---

## 6. Storage model

The MVP SHOULD add a new migration with dedicated tables.

### 6.1 `code_repositories`

```sql
CREATE TABLE code_repositories (
    repository_id      TEXT PRIMARY KEY,
    display_name       TEXT NOT NULL,
    canonical_root     TEXT NOT NULL,
    remote_url         TEXT,
    created_at         TEXT NOT NULL,
    updated_at         TEXT NOT NULL,
    status             TEXT NOT NULL DEFAULT 'active'
);
```

`repository_id` MUST be generated once and persisted. It MUST NOT be derived solely from an absolute filesystem path because the checkout may move.

### 6.2 `code_scans`

```sql
CREATE TABLE code_scans (
    scan_id            TEXT PRIMARY KEY,
    repository_id      TEXT NOT NULL,
    base_commit_sha    TEXT,
    snapshot_kind      TEXT NOT NULL,
    dirty_worktree     INTEGER NOT NULL DEFAULT 0,
    parser_name        TEXT NOT NULL,
    parser_version     TEXT NOT NULL,
    config_hash        TEXT NOT NULL,
    started_at         TEXT NOT NULL,
    completed_at       TEXT,
    status             TEXT NOT NULL,
    file_count         INTEGER NOT NULL DEFAULT 0,
    parse_error_count  INTEGER NOT NULL DEFAULT 0,
    graph_digest       TEXT,
    FOREIGN KEY(repository_id) REFERENCES code_repositories(repository_id)
);
```

Allowed `status` values:

```text
started
staged
completed
failed
cancelled
```

### 6.3 `code_nodes`

```sql
CREATE TABLE code_nodes (
    node_id            TEXT PRIMARY KEY,
    repository_id      TEXT NOT NULL,
    kind               TEXT NOT NULL,
    relative_path      TEXT NOT NULL,
    qualified_name     TEXT,
    language           TEXT NOT NULL,
    line_start         INTEGER,
    line_end           INTEGER,
    byte_start         INTEGER,
    byte_end           INTEGER,
    content_hash       TEXT,
    ast_hash           TEXT,
    signature          TEXT,
    first_seen_scan    TEXT NOT NULL,
    last_seen_scan     TEXT NOT NULL,
    status             TEXT NOT NULL DEFAULT 'active',
    properties_json    TEXT NOT NULL DEFAULT '{}',
    UNIQUE(repository_id, kind, relative_path, qualified_name),
    FOREIGN KEY(repository_id) REFERENCES code_repositories(repository_id)
);
```

Allowed MVP node kinds:

```text
repository
directory
file
class
function
method
external_dependency
unresolved_dependency
```

### 6.4 `code_edges`

```sql
CREATE TABLE code_edges (
    edge_id            TEXT PRIMARY KEY,
    repository_id      TEXT NOT NULL,
    source_node_id     TEXT NOT NULL,
    target_node_id     TEXT NOT NULL,
    relation_type      TEXT NOT NULL,
    first_seen_scan    TEXT NOT NULL,
    last_seen_scan     TEXT NOT NULL,
    status             TEXT NOT NULL DEFAULT 'active',
    properties_json    TEXT NOT NULL DEFAULT '{}',
    UNIQUE(repository_id, source_node_id, target_node_id, relation_type),
    FOREIGN KEY(source_node_id) REFERENCES code_nodes(node_id),
    FOREIGN KEY(target_node_id) REFERENCES code_nodes(node_id)
);
```

Allowed MVP relations:

```text
CONTAINS
DEFINES
IMPORTS
IMPORTS_EXTERNAL
IMPORTS_UNRESOLVED
RENAMED_TO
```

### 6.5 Scan staging

The implementation MUST stage results before changing the active graph.

Recommended staging tables:

```text
code_scan_nodes
code_scan_edges
```

Both MUST be keyed by `scan_id`.

A failed or interrupted scan MUST NOT mark active nodes stale and MUST NOT partially replace the active graph.

---

## 7. Stable identifiers

### 7.1 Repository identity

`repository_id` MUST be generated on first registration, for example as a UUID or random 128-bit identifier, and persisted in `code_repositories`.

### 7.2 Node identity

Node IDs MUST be deterministic within a registered repository:

```text
sha256(
  repository_id
  + "\0" + kind
  + "\0" + normalized_relative_path
  + "\0" + normalized_qualified_name
)
```

Line numbers MUST NOT be part of the ID because edits move symbols without changing identity.

Examples:

```text
repo:<repository_id>
file:core/memory.py
class:core/memory.py::SQLiteGraphStore
method:core/memory.py::SQLiteGraphStore.store_fact
function:core/recall_policy.py::is_fact_allowed_for_recall
```

### 7.3 Duplicate names

The following MUST remain distinct:

```text
core/utils.py
api/utils.py

tests/test_a.py::helper
core/module.py::helper

ClassA.save
ClassB.save
```

### 7.4 Rename semantics

For the MVP, path-based identity may change on file rename. When a removed path and a new path have the same strong content hash within one completed scan transition, the finalizer MAY emit:

```text
old_file_node -[RENAMED_TO]-> new_file_node
```

Rename detection MUST be conservative. Ambiguous matches MUST remain separate rather than being guessed.

---

## 8. Repository snapshot contract

Each scan MUST record whether it represents:

```text
commit        — clean worktree at a known commit
working_tree  — uncommitted local changes are present
archive       — non-git source tree
```

For a git checkout, the resolver SHOULD record:

- `base_commit_sha`;
- branch name if available;
- dirty worktree flag;
- normalized repository root;
- remote URL if available;
- scan configuration hash.

The scanner MUST never execute repository code.

---

## 9. File discovery and security boundaries

The scanner MUST remain inside the registered repository root.

It MUST reject or skip:

- symlinks resolving outside the root;
- device files and sockets;
- files exceeding a configured size limit;
- binary files;
- inaccessible files;
- generated or vendor directories according to policy.

Recommended discovery order:

1. use `git ls-files` plus optionally modified/untracked files when git is available;
2. otherwise use bounded recursive traversal;
3. always apply deny patterns.

Default exclusions SHOULD include:

```text
.git
.venv
venv
__pycache__
.pytest_cache
.mypy_cache
.ruff_cache
node_modules
dist
build
site-packages
```

The MVP MUST NOT store full source bodies, comments, string literals or secret values in the graph.

Allowed stored text:

- normalized relative path;
- symbol name;
- qualified name;
- safe signature without default literal values;
- parser diagnostics;
- bounded structural metadata.

---

## 10. Python AST extraction

The MVP MUST use Tree-sitter for Python.

It SHOULD extract:

- module files;
- classes;
- top-level functions;
- methods;
- import statements;
- from-import statements;
- relative import level;
- imported module path;
- aliases as metadata;
- line and byte ranges;
- safe signatures.

It MUST distinguish nested qualified names:

```text
Outer
Outer.method
Outer.Inner
Outer.Inner.method
outer_function
outer_function.inner_function
```

Anonymous lambdas SHOULD be skipped in the MVP unless a stable AST-path identity is explicitly implemented and tested.

Parse errors MUST be recorded per file. One malformed file MUST NOT abort the whole repository scan.

---

## 11. Internal import resolution

The resolver MUST distinguish:

```text
internal module
external dependency
unresolved dependency
```

It SHOULD support:

- absolute imports;
- relative imports;
- package `__init__.py`;
- `src/` layouts;
- aliases;
- module files and package directories;
- namespace-package fallback where unambiguous.

It MUST NOT pretend an unresolved import is an internal edge.

Example:

```python
from core.recall_policy import is_fact_allowed_for_recall
```

Expected structural edge:

```text
file:core/memory.py
  -[IMPORTS]->
file:core/recall_policy.py
```

An external import should resolve to a stable external dependency node:

```text
external:pydantic
external:fastapi
```

---

## 12. Atomic scan finalization

The scan lifecycle MUST be:

```text
1. create code_scans row: started
2. discover and parse files
3. write nodes/edges only to scan staging
4. validate staging invariants
5. compute deterministic graph digest
6. begin immediate transaction
7. upsert staged nodes/edges into active tables
8. mark previously active but unseen nodes/edges stale
9. mark scan completed
10. commit
```

If any step before commit fails:

```text
active graph remains unchanged
scan status = failed
staging rows are retained for diagnostics or safely deleted
```

A scan MUST NOT make stale decisions unless the scan reaches successful finalization.

---

## 13. Concurrency

Only one finalizing scan per repository MAY execute at a time.

The implementation MUST provide one of:

- a repository-scoped lock row with compare-and-set semantics;
- an SQLite transaction-backed lease;
- an in-process lock plus DB-level protection for multi-process safety.

A second concurrent scan MUST either:

```text
queue
or
return a typed `scan_in_progress` result
```

It MUST NOT interleave staging/finalization in a way that creates ghost nodes or edges.

---

## 14. Provenance and receipts

Code structure has different provenance requirements from user/world facts.

Each node and edge MUST be attributable to:

- repository ID;
- scan ID;
- source file path;
- parser name and version;
- byte/line range where applicable;
- content or AST hash.

Each completed scan MUST produce a deterministic `graph_digest` over sorted normalized node and edge records.

A scan receipt SHOULD contain:

```json
{
  "repository_id": "...",
  "scan_id": "...",
  "base_commit_sha": "...",
  "snapshot_kind": "commit|working_tree|archive",
  "dirty_worktree": false,
  "parser": "tree-sitter-python",
  "parser_version": "...",
  "config_hash": "...",
  "node_count": 0,
  "edge_count": 0,
  "parse_error_count": 0,
  "graph_digest": "sha256:...",
  "completed_at": "..."
}
```

The MVP SHOULD use scan-level receipts instead of appending one full general-purpose provenance-chain event per symbol, which would be unnecessarily expensive.

---

## 15. Retrieval contract

The first implementation SHOULD expose a Python service API, not a public write API.

Required methods:

```python
find_symbol(query, *, repository_id, kinds=None, limit=20)
open_node(node_id, *, max_neighbors=100)
dependencies_of(node_id, *, depth=1, max_nodes=200)
dependents_of(node_id, *, depth=1, max_nodes=200)
impact_of(node_id, *, depth=2, max_nodes=500)
module_context(relative_path, *, max_nodes=300)
```

All graph expansion MUST be bounded by:

- depth;
- node count;
- edge count;
- time budget.

Responses MUST report truncation explicitly.

Example:

```json
{
  "nodes": [],
  "edges": [],
  "truncated": true,
  "limits": {"depth": 2, "max_nodes": 500}
}
```

---

## 16. Retrieval routing in Titan

Future integration SHOULD route code questions as follows:

```text
exact symbol or file query
  → CodeStructuralRetriever

architecture / impact query
  → CodeStructuralRetriever + Graph Lab

semantic concept query
  → HybridRetriever

mixed query
  → bounded fusion of structural and semantic results
```

The MVP MUST NOT silently inject the whole graph into LLM context.

---

## 17. Feature flag and configuration

The component MUST be disabled by default:

```text
ENABLE_CODE_STRUCTURAL_MEMORY=false
```

Suggested configuration:

```text
CODE_MEMORY_MAX_FILE_BYTES=2000000
CODE_MEMORY_MAX_FILES=100000
CODE_MEMORY_SCAN_TIMEOUT_SECONDS=600
CODE_MEMORY_MAX_QUERY_NODES=500
CODE_MEMORY_INCLUDE_UNTRACKED=false
CODE_MEMORY_RESPECT_GITIGNORE=true
```

Invalid configuration MUST fail closed or fall back to safe bounded defaults.

---

## 18. Metrics

Required scan metrics:

```text
code_scan_duration_seconds
code_scan_files_discovered
code_scan_files_parsed
code_scan_files_skipped
code_scan_parse_errors
code_scan_nodes_staged
code_scan_edges_staged
code_scan_nodes_added
code_scan_nodes_updated
code_scan_nodes_staled
code_scan_edges_added
code_scan_edges_updated
code_scan_edges_staled
code_scan_unresolved_imports
code_scan_id_collisions
code_scan_finalize_failures
```

Required retrieval metrics:

```text
code_retrieval_latency_seconds
code_retrieval_nodes_returned
code_retrieval_edges_returned
code_retrieval_truncated_total
code_retrieval_not_found_total
```

Metrics MUST NOT include source contents or secrets.

---

## 19. Error model

The package SHOULD expose typed errors or typed result reasons:

```text
repository_not_registered
repository_root_invalid
scan_in_progress
scan_cancelled
scan_failed
parser_unavailable
file_outside_root
file_too_large
parse_failed
staging_invariant_failed
finalization_conflict
graph_not_available
node_not_found
query_limit_exceeded
```

Broad exception swallowing is prohibited in finalization and persistence code.

---

## 20. Mandatory invariants

### CSM-01 — Domain isolation

No code structural node or edge is written to canonical `facts` or ordinary user-memory relations.

### CSM-02 — Determinism

The same repository bytes, parser version and configuration produce the same normalized node/edge set and graph digest.

### CSM-03 — Stable identity

Duplicate filenames and duplicate symbol names in different scopes never collide.

### CSM-04 — Atomic visibility

A failed or interrupted scan cannot partially replace the active graph.

### CSM-05 — No ghost edges

After a successful scan, removed imports and removed symbols are not returned as active.

### CSM-06 — Conservative resolution

An unresolved import is never promoted to an internal dependency by guesswork.

### CSM-07 — Root confinement

The scanner never reads outside the registered repository root.

### CSM-08 — No source execution

Repository code is parsed as data and never imported or executed.

### CSM-09 — Bounded retrieval

Every graph expansion has explicit depth, node, edge and time limits.

### CSM-10 — Feature-off safety

With the feature flag disabled, no scan, migration-dependent runtime path or retrieval behavior is activated.

### CSM-11 — No implicit LLM truth

LLM output is absent from the MVP. Future summaries must remain derived, versioned and invalidatable.

### CSM-12 — Scan receipt

Every completed scan has a verifiable digest and recorded parser/configuration identity.

---

## 21. Required tests for MVP acceptance

### Identity and parsing

- same filename in different directories produces different IDs;
- same function name in different files produces different IDs;
- same method name in different classes produces different IDs;
- nested symbols receive stable qualified names;
- line-number-only edits do not change symbol IDs;
- syntax errors are isolated to the affected file;
- binary and oversized files are skipped safely.

### Imports

- absolute internal import resolves to the correct file;
- relative import resolves correctly;
- external import produces an external dependency node;
- unresolved import remains explicitly unresolved;
- removing an import removes or stales the active edge after successful scan;
- cyclic imports do not break scanning.

### Scan lifecycle

- identical second scan is idempotent;
- changed file updates hashes and last-seen scan;
- removed symbol becomes stale only after successful finalization;
- removed file becomes stale only after successful finalization;
- failed scan leaves the previously active graph unchanged;
- concurrent scan is rejected or queued deterministically;
- staging validation failure does not modify active tables;
- graph digest is stable for identical normalized input.

### Security

- symlink escaping repository root is rejected;
- path traversal is rejected;
- scanner does not import or execute target code;
- source literals and comments are not stored;
- malicious names serialize safely.

### Titan integration

- feature flag off means no active behavior;
- no writes occur in canonical `facts`;
- no writes occur through WriteGate/TruthGate because this is an isolated operational index;
- existing recall behavior is unchanged;
- existing test suite remains green;
- migration is reversible or has an explicit rollback procedure.

---

## 22. Phased implementation plan

### Phase 0 — RFC and review

- approve storage separation;
- approve stable-ID rules;
- approve scan finalization contract;
- confirm migration number;
- confirm Tree-sitter dependency strategy;
- confirm no upstream code copying.

### Phase 1 — Python structural core

- migration and models;
- repository registration;
- snapshot resolver;
- Python scanner;
- stable IDs;
- staging and atomic finalization;
- import resolution;
- unit and integration tests;
- metrics;
- feature flag.

### Phase 2 — Read-only retrieval

- symbol search;
- open node;
- dependencies/dependents;
- impact analysis;
- bounded serialization;
- CLI or internal service adapter.

### Phase 3 — Graph analytics

- read-only projection into Graph Lab;
- centrality;
- cycles;
- communities;
- architectural-area generation.

### Phase 4 — Derived summaries

Only after separate RFC and threat model:

- MOC construction;
- bounded source-node selection;
- summary input hash;
- model and prompt version;
- derived epistemic state;
- invalidation when source graph changes;
- no default high trust.

### Phase 5 — MCP read compatibility

Read-only tools only:

```text
search_code_nodes
open_code_node
find_dependencies
find_dependents
impact_analysis
```

Write tools require a separate security RFC.

---

## 23. External-project adoption policy

The external `graph-memory` project is useful as architectural inspiration for:

- Tree-sitter structural scanning;
- structural-first retrieval;
- bounded neighborhood serialization;
- separation between deterministic skeleton and derived summaries;
- MCP-compatible read concepts.

Titan MUST NOT adopt unchanged:

- file IDs based only on basename;
- MOC IDs based only on final directory name;
- string-split import parsing;
- one-dimensional trust scores;
- `MAX(trust_score)` update semantics;
- age-based truth decay;
- direct MCP writes with default high trust;
- automatic quiet writes by agents;
- LLM summaries stored with default trust;
- a second independent SQLite database;
- orphan-only cleanup as the primary differential-sync mechanism.

Until the upstream repository includes a clear license file or written permission is obtained, implementation MUST be clean-room and documentation MUST cite the project as inspiration rather than copied source.

---

## 24. Acceptance decision

The Code Structural Memory Adapter is considered ready for implementation when:

```text
[ ] RFC reviewed
[ ] table separation approved
[ ] migration number allocated
[ ] Python-only scope confirmed
[ ] Tree-sitter dependency approved
[ ] clean-room rule accepted
[ ] feature flag name accepted
[ ] concurrency strategy accepted
[ ] mandatory tests accepted
[ ] no LLM/MCP-write scope creep accepted
```

---

## 25. Summary

The correct adoption path is:

```text
graph-memory idea
    → extract the deterministic AST insight
    → redesign IDs, sync, provenance and safety
    → implement as a Titan-native operational code index
    → keep canonical memory isolated
    → add read-only structural retrieval
    → evaluate summaries and MCP only later
```

This gives Titan a precise map of software structure without weakening its existing truth, provenance, privacy or recall contracts.
