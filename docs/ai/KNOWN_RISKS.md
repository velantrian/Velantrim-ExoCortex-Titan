# ⚠️ Known Risks and Required Proof

**Snapshot date:** 2026-08-05  
**Reference main before PR #200:** `649d12953eb141aa783729555861e788cc03c150`

This register is an engineering hand-off. Code presence does not close a risk; closure
requires the stated tests, wiring, operational evidence and governance decision.

## Priority model

- **P0:** blocks a trustworthy production claim or can cause silent integrity or
  operability failure.
- **P1:** materially increases maintenance, privacy, integration or governance risk.
- **P2:** important quality and repository-governance work.

## P0

### RISK-P0-01 — Projection delivery is not runtime-wired

Outbox, checkpoints, version-monotonic apply and bounded dispatch exist, but there is no
accepted lifecycle owner, cadence, backlog/age SLO or reconciliation loop.

**Required sequence:** metrics and health → protected manual bounded dispatch →
feature-gated worker with cancellation/backoff → reconciliation and restart evidence.

### RISK-P0-02 — Production deployment contract is ambiguous

`docker-compose.yml` and `docker-compose.prod.yml` present materially different
production-oriented network, hardening, resource and feature defaults.

**Closure:** select one canonical contract, classify the other, and test documentation,
environment, ports, hardening and enabled modules together.

### RISK-P0-03 — Verification scope is narrower than repository claims may imply

Coverage configuration, Ruff, mypy and pytest do not form one uniform gate across every
runtime surface. `server.py`, `api/`, `utils/`, packaging and optional profiles need
staged expansion and honest baselines.

### RISK-P0-04 — Storage concurrency is not systemically proven

Selected CAS and recovery races are tested, but no repository-wide WAL/contention,
crash/restart, disk-full and migration stress matrix exists.

### RISK-P0-05 — Supply chain and builds are not fully reproducible

Broad ranges, non-authoritative lock usage, mutable action/image references and
wheel/container differences can produce different artifacts from identical source.

## P1

### RISK-P1-01 — Continuity requires a clean current-main rebuild

The old PR #131–#147 stack is not independently mergeable as one chain. Known work:

1. move the Advisory typing fix to its owning layer;
2. add `DEFER_PATH` to all exhaustive consumers;
3. add differential legacy-compatibility tests;
4. rebuild and review layers from current `main`;
5. keep all output shadow-only;
6. design trusted candidate/attestation producers separately.

### RISK-P1-02 — Selective-memory extraction is heuristic and proposal-only

PR #200 hardens ARM-03 but does not make candidate extraction authoritative.

Residual risks:

- regex/type classification can miss, over-classify or misclassify statements;
- English/Russian injection patterns are bounded examples, not complete semantic prompt
  injection detection;
- `POSSIBLE_UPDATE_OF` is an within-input hint, not durable reconciliation;
- raw exact source text remains in protected in-process evidence to verify offsets and
  must never be copied to logs/receipts except through the redacted safe serializer;
- subject/context identifiers are caller-supplied and require a trusted upstream owner;
- a redacted candidate can still be sensitive metadata;
- benchmark success does not establish candidate precision or user value.

**Required before ARM-04:**

1. approved replay corpus with explicit consent/synthetic data;
2. precision/recall and false-retention measurements by candidate type;
3. privacy review of source evidence and portable receipts;
4. erasure/revocation propagation design;
5. WorkingMemoryGate disposition and explicit Write Gate contract;
6. no query-path admission or persistence;
7. operator approval in a separate PR.

### RISK-P1-03 — Identity layer is a legacy mutable prototype

`core/identity_layer.py` has no accepted assertion lifecycle, consent/scope, contestation,
version/audit or erasure closure. Prevent production activation and define a separate
Identity Assertion/Admission/Reconciliation protocol.

### RISK-P1-04 — Canon mutation ownership remains fragmented

Standard promotion ownership improved, but every mutation family is not yet proven to
use one typed command/receipt/transaction boundary.

### RISK-P1-05 — `server.py` remains a composition monolith

Initialization order, singletons, lifecycle, routes and provider wiring have broad blast
radius. Extract in characterized increments.

### RISK-P1-06 — Authentication is not multi-user authorization

A shared API key does not provide accounts, roles, scopes, tenant isolation or sensitive
multi-user policy.

### RISK-P1-07 — Wheel and container are distinct packaging surfaces

Define supported artifacts, manifests and independent smoke tests rather than treating
one successful build as proof for all delivery forms.

## P2

### RISK-P2-01 — Large generated knowledge artifact

Evaluate `kb_graph.json` for a reproducible build, Release asset or LFS strategy.

### RISK-P2-02 — Historical audits can look current

Mark obsolete audits `SUPERSEDED` or index/archive them by date and verified SHA.

### RISK-P2-03 — Repository governance metadata remains incomplete

Verify CODEOWNERS, branch protection, update automation, labels and templates through
both repository files and authorized settings.

### RISK-P2-04 — Project discovery metadata is weak

Improve repository description, homepage and topics with verified capability language.

## Risk update rule

Use exact status words: proposed, implemented, tested, wired, enabled and observed. A
risk is not closed merely because code or documentation was added.
