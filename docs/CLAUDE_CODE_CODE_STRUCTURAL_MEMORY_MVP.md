# Claude Code Task — Python-only Code Structural Memory MVP

**Target repository:** `velantrian/Velantrim-ExoCortex-Titan`  
**Authoritative RFC:** [`research/CODE_STRUCTURAL_MEMORY_ADAPTER.md`](../research/CODE_STRUCTURAL_MEMORY_ADAPTER.md)  
**Delivery:** one isolated Draft PR  
**Merge:** prohibited without owner approval  
**Implementation style:** clean-room; do not copy source code from `divyanshailani/graph-memory`

---

## 1. Objective

Implement Phase 1 of the Code Structural Memory Adapter:

> A deterministic, Python-only Tree-sitter index that records repository, directory, file, class, function, method and import structure in dedicated code-memory tables inside the Titan-controlled SQLite database.

The result must be disabled by default, isolated from canonical user/world memory and safe under repeated, failed and concurrent scans.

---

## 2. Required preflight

Before changing code:

1. Run `git fetch origin`.
2. Confirm the working tree is clean.
3. Read the full RFC.
4. Inspect current `main`, storage contracts, feature configuration, metrics and migration conventions.
5. Determine the next unused migration number from the repository. Do not assume a migration number from this document.
6. Run and record the baseline commands used by current CI.
7. Search the repository for any existing code-structure scanner or code graph implementation to avoid duplication.
8. Verify the optional dependency strategy with the existing `pyproject.toml` design.
9. Create a new implementation branch from the exact current `origin/main` SHA.

Report the baseline SHA in the PR description.

---

## 3. Hard scope

Implement only:

- optional Tree-sitter Python parser dependency;
- repository registration;
- repository snapshot metadata;
- tracked-file discovery with safe fallback;
- deterministic Python AST extraction;
- stable node and edge IDs;
- internal/external/unresolved import classification;
- scan-scoped staging;
- atomic finalization;
- stale-node and stale-edge handling after successful scans;
- repository-scoped concurrency protection;
- scan receipt and deterministic graph digest;
- read-only Python service methods;
- metrics;
- tests;
- documentation required to run and verify the MVP.

---

## 4. Explicitly out of scope

Do not add:

- LLM summaries;
- MOC summaries;
- MCP tools;
- public HTTP endpoints;
- autonomous agent writeback;
- visual graph export;
- JavaScript, TypeScript, Go or Rust;
- call-graph inference;
- runtime code execution;
- a second SQLite database;
- writes to canonical `facts`;
- writes to ordinary user-memory `relations`;
- TruthGate or RecallPolicy changes;
- trust decay;
- a generic `trust_score` model;
- broad refactoring of Titan storage;
- package or repository renaming.

Scope expansion requires a separate PR and explicit approval.

---

## 5. Dependency contract

Preserve Titan's dependency-light default runtime.

Add an optional extra, for example:

```toml
[project.optional-dependencies]
code-memory = [
  "tree-sitter>=0.22,<1",
  "tree-sitter-python>=0.23,<1",
]
```

Use versions compatible with the current parser API and lock the accepted range narrowly enough to avoid silent breaking changes.

When the optional dependency is absent:

- Titan must still import and start normally;
- code memory remains disabled;
- an explicit scan request returns a typed `parser_unavailable` result;
- no broad import-time exception is allowed.

---

## 6. Feature configuration

Add a feature flag using the current Titan configuration mechanism:

```text
ENABLE_CODE_STRUCTURAL_MEMORY=false
```

Default must be off.

Suggested bounded settings:

```text
CODE_MEMORY_MAX_FILE_BYTES=2000000
CODE_MEMORY_MAX_FILES=100000
CODE_MEMORY_SCAN_TIMEOUT_SECONDS=600
CODE_MEMORY_MAX_QUERY_NODES=500
CODE_MEMORY_INCLUDE_UNTRACKED=false
CODE_MEMORY_RESPECT_GITIGNORE=true
```

Validate numeric values and use safe bounded defaults for malformed environment input.

Do not trigger scans automatically on startup.

---

## 7. Package layout

Use this layout unless current repository conventions justify a small documented variation:

```text
core/code_memory/
├── __init__.py
├── errors.py
├── models.py
├── stable_ids.py
├── repository_snapshot.py
├── tree_sitter_python.py
├── import_resolver.py
├── scan_store.py
├── scan_finalizer.py
├── structural_retriever.py
├── impact_analyzer.py
└── metrics.py
```

Keep modules focused. Avoid a single large engine file.

---

## 8. Database migration

Create the next unused migration according to repository conventions.

Implement dedicated tables equivalent to the RFC:

```text
code_repositories
code_scans
code_nodes
code_edges
code_scan_nodes
code_scan_edges
```

Add any minimal lock/lease table required for multi-process scan serialization.

Requirements:

- foreign keys enabled where supported;
- indexes for repository, path, kind, qualified name, scan and active status;
- explicit uniqueness constraints;
- no changes to canonical fact semantics;
- no direct dependence on private internals of the global memory singleton;
- explicit `db_path` or storage dependency injection for tests.

Document rollback SQL or the repository-standard rollback mechanism.

---

## 9. Repository registration

Implement a service that registers a repository root and returns a persisted `repository_id`.

Rules:

- generate the ID once and persist it;
- do not derive identity solely from absolute path;
- normalize the root path;
- reject missing or non-directory roots;
- reject duplicate conflicting registrations;
- allow a moved checkout to be associated with an existing repository only through an explicit update path;
- store remote URL when available, but do not use it as the only identity.

---

## 10. File discovery

Preferred behavior for a Git checkout:

```text
git ls-files
```

Optionally include untracked files only when explicitly configured.

Use subprocess argument arrays, never `shell=True`.

Fallback traversal must:

- remain below the registered root;
- enforce maximum file count;
- skip symlinks escaping the root;
- skip binary, device and oversized files;
- apply deny patterns;
- process only `.py` in this PR.

Default exclusions:

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

Do not read or store `.env`, secret files or non-Python content as part of this scanner.

---

## 11. Snapshot metadata

Record:

- repository ID;
- base commit SHA when available;
- branch name as optional metadata;
- `snapshot_kind`: `commit`, `working_tree` or `archive`;
- dirty worktree flag;
- parser name/version;
- configuration hash;
- scan timestamps and status.

The scanner reads working-tree bytes. If tracked files are modified, the scan must be marked `working_tree`/dirty rather than falsely claiming an exact commit snapshot.

---

## 12. AST extraction

Use Tree-sitter Python and extract:

- file/module;
- classes;
- top-level functions;
- methods;
- nested classes/functions with qualified names;
- import statements;
- from-import statements;
- relative import level;
- aliases as metadata;
- byte and line ranges;
- safe signatures.

Safe signature rules:

- do not persist default literal values;
- do not persist function bodies;
- do not persist comments;
- do not persist string literals;
- replace defaults with a neutral marker if needed;
- keep annotations only if they can be extracted without storing arbitrary expressions.

Skip anonymous lambdas in the MVP.

One malformed file must produce a per-file parse diagnostic and must not abort the whole scan.

---

## 13. Stable IDs

Implement the RFC identity formula using:

```text
repository_id
kind
normalized relative path
normalized qualified name
```

Do not include line numbers.

Add collision detection. A computed ID collision with different canonical identity fields must fail the scan staging validation; it must not silently merge records.

Mandatory distinctness tests:

```text
core/utils.py != api/utils.py
A.save != B.save
file_a.py::helper != file_b.py::helper
outer.inner != other.inner
```

---

## 14. Import resolution

Classify every import as:

```text
internal
external
unresolved
```

Support:

- absolute imports;
- relative imports;
- `__init__.py` packages;
- common `src/` layouts;
- module aliases;
- package directories;
- unambiguous namespace-package fallback.

Never guess an internal target when resolution is ambiguous.

Store alias and imported-name details in bounded edge metadata, not in the edge ID.

Removing an import in a later successful scan must remove it from active retrieval by marking the previous edge stale.

---

## 15. Staging and atomic finalization

Do not write scan results directly to active tables.

Required lifecycle:

```text
create scan row (started)
→ parse into scan-scoped staging
→ validate staging
→ compute graph digest
→ acquire repository finalization lock
→ BEGIN IMMEDIATE
→ upsert current nodes/edges
→ stale previously active unseen nodes/edges
→ mark scan completed
→ commit
```

A failed or interrupted scan must leave the previously active graph unchanged.

Do not mark nodes stale from an incomplete scan.

After failure, set the scan status and retain only bounded diagnostics. Staging cleanup must be explicit and tested.

---

## 16. Concurrency

Implement DB-backed repository-scoped protection.

Two concurrent scans for the same repository must not finalize simultaneously.

The second request must either:

- return typed `scan_in_progress`; or
- wait under a bounded timeout and then proceed.

Tests must use two independent service/store instances against the same temporary DB, not only two threads sharing one object.

Scans for different repository IDs may proceed independently if SQLite serialization permits it safely.

---

## 17. Graph digest and receipt

Normalize and sort staged records before hashing.

Digest input must exclude volatile fields such as timestamps and scan IDs, while including all structural identity and relation data needed to detect graph changes.

Produce a JSON-ready receipt containing:

- repository ID;
- scan ID;
- snapshot metadata;
- parser/config identity;
- file/node/edge counts;
- parse-error count;
- graph digest;
- completion timestamp.

Identical structural input under the same parser/config must produce the same graph digest.

---

## 18. Read-only service API

Implement internal Python methods:

```python
find_symbol(query, *, repository_id, kinds=None, limit=20)
open_node(node_id, *, max_neighbors=100)
dependencies_of(node_id, *, depth=1, max_nodes=200)
dependents_of(node_id, *, depth=1, max_nodes=200)
impact_of(node_id, *, depth=2, max_nodes=500)
module_context(relative_path, *, max_nodes=300)
```

Requirements:

- active nodes/edges only by default;
- deterministic ordering;
- explicit truncation metadata;
- explicit not-found result;
- bounded depth, node count, edge count and time;
- no LLM call;
- no automatic injection into general recall.

`impact_of` should return reverse import dependents and affected structural neighborhood only. Do not claim semantic certainty about runtime behavior.

---

## 19. Metrics

Integrate with the existing Titan metrics pattern without introducing hard runtime dependencies.

At minimum record:

```text
scan duration
files discovered/parsed/skipped/failed
nodes and edges staged
nodes and edges added/updated/staled
unresolved imports
ID collisions
finalization failures
retrieval latency
retrieval returned nodes/edges
retrieval truncations
```

Tests should verify metric calls through an injected fake/no-op collector rather than asserting global process state.

---

## 20. Error contract

Use typed exceptions or typed result reasons for:

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

Do not hide storage/finalization programming errors behind broad `except Exception` blocks.

Graceful handling is appropriate at file-parse boundaries, but persistence and atomicity failures must remain visible and testable.

---

## 21. Mandatory tests

Implement all mandatory tests from the RFC, including these high-risk regressions:

### Identity

- duplicate basenames in separate directories;
- duplicate functions in separate files;
- duplicate method names in separate classes;
- nested qualified-name stability;
- line movement without identity change;
- collision guard.

### Differential scan

- exact repeated scan is idempotent;
- changed file updates hashes;
- removed function becomes stale;
- removed file becomes stale;
- removed import edge becomes stale;
- renamed file is represented conservatively;
- parse failure in one file does not invalidate other current nodes;
- total scan failure leaves active graph byte-for-byte/logically unchanged.

### Imports

- absolute internal;
- relative internal;
- external;
- unresolved;
- alias;
- package `__init__`;
- `src/` layout;
- cyclic imports.

### Concurrency

- two independent scanners, same repository, same DB;
- one finalizer wins and the other returns/queues predictably;
- no mixed scan IDs in active results;
- no ghost edges after concurrency test.

### Security

- symlink escape;
- path traversal;
- oversized file;
- binary file;
- malicious symbol/path text serialization;
- target module is never imported/executed;
- source body, comments and default literals are not persisted.

### Integration

- Titan imports without optional dependency;
- flag off produces no scan behavior;
- canonical `facts` unchanged;
- ordinary memory `relations` unchanged;
- existing recall tests unchanged;
- migration from a clean DB succeeds;
- migration against a representative existing DB succeeds.

---

## 22. Quality gates

Run the repository's canonical commands. At minimum report:

```text
python -m pytest -q
ruff check core/ tests/
mypy core/
```

Use the exact current CI commands when they differ.

Also run focused tests repeatedly:

```text
code-memory unit tests
scan lifecycle tests
concurrency tests
migration tests
```

Do not weaken existing lint, type or test configuration to make the PR pass.

---

## 23. Documentation deliverables

Add concise user/developer documentation covering:

- optional installation;
- feature flag;
- repository registration;
- explicit scan invocation through the internal service or minimal CLI chosen for testing;
- receipt example;
- read-only query examples;
- limitations;
- privacy/security boundary;
- rollback procedure.

Do not claim support for languages or capabilities outside this PR.

---

## 24. Git and PR discipline

- Use one implementation branch from the recorded current `origin/main` SHA.
- Keep commits logically separated: migration/models, scanner/resolver, finalizer, retrieval, tests/docs.
- Do not modify unrelated files.
- Do not merge the PR.
- Open as Draft.
- Do not enable auto-merge.
- Do not resolve review findings without a finding-specific reply naming the fixing commit and regression test.
- Never force-push after review begins unless explicitly approved.

---

## 25. Required PR description

Include:

1. baseline `origin/main` SHA;
2. final head SHA;
3. exact scope and exclusions;
4. migration number and schema summary;
5. optional dependencies added;
6. feature flags/configuration;
7. invariants implemented;
8. test commands and exact results;
9. CI status;
10. known limitations;
11. proof that canonical `facts` and ordinary memory relations are untouched;
12. proof that a failed scan does not change the active graph;
13. proof that concurrent same-repository finalization is protected;
14. confirmation that no upstream source code was copied;
15. rollback instructions.

---

## 26. Stop conditions

Stop and request architectural review before proceeding if:

- the next migration number is contested;
- implementation requires changes to canonical fact semantics;
- Tree-sitter requires a breaking global dependency change;
- repository identity cannot be persisted without modifying unrelated storage contracts;
- atomic finalization cannot be achieved with the proposed tables;
- tests reveal current DB lifecycle assumptions incompatible with a shared SQLite file;
- implementation begins to require LLM summaries, MCP writes or additional languages;
- upstream code copying appears necessary.

---

## 27. Definition of done

The Draft PR is ready for independent review only when:

```text
[ ] feature off by default
[ ] optional parser dependency
[ ] dedicated same-DB tables
[ ] no canonical memory writes
[ ] deterministic stable IDs
[ ] Python AST extraction
[ ] internal/external/unresolved imports
[ ] scan staging
[ ] atomic finalization
[ ] stale cleanup after successful scans only
[ ] concurrent same-repository scan protection
[ ] deterministic graph digest and receipt
[ ] bounded read-only retrieval
[ ] metrics
[ ] mandatory tests
[ ] full existing CI green
[ ] documentation complete
[ ] clean-room implementation confirmed
[ ] Draft PR opened, not merged
```
