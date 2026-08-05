# ⚠️ Known Risks and Required Proof

**Snapshot date:** 2026-08-05  
**Baseline:** `main` at `024454e5ee17a52f6de321e6917bf29eb5cc88ca`

This register is optimized for engineering hand-off. It complements
`docs/PROJECT_STATUS.md`; it does not replace security review, legal compliance work,
or runtime evidence.

## Priority model

- **P0:** blocks a trustworthy production claim or can cause silent integrity/operability
  failure.
- **P1:** materially increases maintenance, integration, privacy, or governance risk.
- **P2:** important quality and repository hygiene work that can follow the hardening
  blockers.

## P0

### RISK-P0-01 — Projection delivery is not runtime-wired

**Current evidence**

- outbox, checkpoints, version-monotonic FTS apply, and bounded dispatcher are in main;
- focused lease/retry/park/ack and crash-window tests exist;
- no production caller, scheduler, startup hook, or worker cadence exists.

**Impact**

- outbox backlog can grow indefinitely;
- derived FTS state can lag Canon;
- operators cannot see delivery age or version lag.

**Required sequence**

1. backlog/age/retry/park/version-lag metrics and health state;
2. manual bounded dispatch command or protected operator action;
3. feature-gated bounded worker with cancellation, jitter, backoff and clean shutdown;
4. reconciliation/repair path for missing or stale projection state.

**Closure proof**

- runtime caller and lifecycle tests;
- restart/backlog/duplicate/crash tests;
- health and metrics evidence from a running instance;
- bounded resource and SQLite-pressure behavior.

### RISK-P0-02 — Production deployment contract is ambiguous

**Current evidence**

- `docker-compose.yml` and `docker-compose.prod.yml` are both presented as production
  oriented;
- they differ materially in network binding, hardening, resource limits and enabled
  research modules.

**Impact**

- operators can deploy different security and feature postures while believing both are
  the canonical production profile.

**Required action**

- choose one canonical production contract;
- rename or clearly classify the other profile;
- test documentation, environment defaults, exposed ports and enabled modules together.

### RISK-P0-03 — Coverage policy is configured but not enforced

**Current evidence**

- a coverage threshold exists in project configuration;
- primary CI runs pytest without a blocking coverage command.

**Impact**

- repository claims can imply a gate that does not actually block regressions.

**Required action**

- establish an honest measured baseline;
- add a non-regressive blocking threshold;
- ratchet intentionally rather than declaring an unmeasured target satisfied.

### RISK-P0-04 — Static-analysis scope excludes important runtime surfaces

**Current evidence**

- main CI focuses Ruff and mypy on `core/`;
- `server.py`, `api/`, `utils/` and runtime composition are not all covered by the same
  gate.

**Impact**

- type and lint defects can survive in network, lifecycle and integration layers.

**Required action**

- expand in staged scopes;
- fix baseline debt explicitly;
- keep component-specific workflows for high-risk contracts.

### RISK-P0-05 — Storage concurrency is not systemically proven

**Current evidence**

- selected CAS races are covered;
- no broad writer stress matrix and no repository-wide verified WAL contract exist.

**Impact**

- contention, lock handling, fairness, partial failure and performance behavior remain
  uncertain beyond the proven narrow paths.

**Required proof**

- 1/10/25/50/100-writer profiles;
- busy/locked, crash, restart, disk-full and migration interaction tests;
- explicit journal/busy-timeout contract and observed latency/error metrics.

### RISK-P0-06 — Supply chain and build are not fully reproducible

**Current evidence**

- broad dependency ranges remain;
- lockfile is not the authoritative install path for CI and Docker;
- some runtime installation choices are outside the main dependency declaration;
- actions and base image are not all immutable-digest pinned.

**Impact**

- identical source commits can resolve to different dependency graphs or image contents.

**Required action**

- select one lock/update policy;
- make CI and image builds consume it;
- add dependency audit, SBOM/provenance and controlled update automation.

## P1

### RISK-P1-01 — Continuity stack is not independently reviewable yet

**Current evidence**

- draft stacked PRs #131–#147;
- no formal independent reviews recorded;
- PR #146 has a failing mypy contract gate;
- upper PR #147 contains a typing fix needed by #146;
- PR #144 changes the public compute contract and introduces `DEFER_PATH`;
- a downstream cost map in `rapid_orientation.py` omits `DEFER_PATH` on the stack branch;
- live dialogue → trusted goal/open-loop producer is missing.

**Required action**

1. move the typing fix to #146 and make it independently green;
2. add `DEFER_PATH` mapping plus exhaustive enum-consumer tests;
3. add differential compatibility tests with `continuity=None`;
4. rebase upper PRs;
5. conduct review gates at #136, #142, #144 and the final aggregate;
6. design producer-side candidate/attestation/confirmation separately.

### RISK-P1-02 — Identity layer is a legacy mutable prototype

**Current evidence**

- direct `INSERT OR REPLACE` store;
- no proven audit/version/reconciliation lifecycle;
- no established tests or runtime owner;
- no accepted consent/scope/erasure contract.

**Impact**

- accidental activation could create a parallel identity authority and retain sensitive
  personal assertions without adequate contestation or deletion semantics.

**Required action**

- mark and guard as legacy/unwired;
- prevent new production imports/writes;
- define Identity Assertion/Admission/Reconciliation contracts;
- keep mechanism evolution under RFC-0084 or a successor governance protocol.

### RISK-P1-03 — Canon mutation ownership is still fragmented

**Current evidence**

- standard promotion ownership has improved;
- not every mutation family is proven to use one typed envelope;
- explicit exceptions remain.

**Required action**

- inventory mutation families;
- define typed commands/receipts per family;
- enforce no-new-direct-writer guards;
- prove transaction, audit, rollback and concurrency behavior.

### RISK-P1-04 — `server.py` is a composition monolith

**Impact**

- hidden initialization order, singleton coupling, lifecycle complexity and broad change
  blast radius.

**Required action**

- extract settings, lifecycle, dependency composition and route groups incrementally;
- retain behavior with characterization and integration tests.

### RISK-P1-05 — Authentication is not multi-user authorization

**Current evidence**

- shared API key;
- no per-user accounts, scopes, tenant isolation or role model.

**Impact**

- unsuitable for sensitive multi-user internet exposure without an external trusted
  boundary or new authorization model.

### RISK-P1-06 — Wheel and container runtime are different packaging surfaces

**Current evidence**

- wheel package discovery covers a narrow set;
- Docker separately copies server, application and runtime assets.

**Impact**

- “package works” and “container works” can describe different products.

**Required action**

- define supported artifacts and smoke-test each independently;
- publish an explicit runtime manifest.

## P2

### RISK-P2-01 — Large generated knowledge artifact in Git history

`kb_graph.json` is large and should be evaluated for Release assets, LFS, or a
reproducible build pipeline.

### RISK-P2-02 — Historical audits can look current

Old audits and action lists remain useful but may contain closed findings or obsolete
counts. Add clear `SUPERSEDED` headers or archive them under a dated index.

### RISK-P2-03 — Repository governance metadata is thin

Add or verify CODEOWNERS, Dependabot/update policy, PR/issue templates, labels and
branch protection. Branch-protection status must be verified through an authorized
administrative view rather than inferred from files.

### RISK-P2-04 — Repository discovery metadata is weak

Improve description, homepage and topics so external reviewers understand the project
before inspecting code.

## Risk update rule

A risk is not closed because code was added. Record closure only when the required
behavior is implemented, tested, wired where applicable, enabled intentionally, and
supported by the stated evidence.
