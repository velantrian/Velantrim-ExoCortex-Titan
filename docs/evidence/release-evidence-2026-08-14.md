# Release evidence snapshot — 2026-08-14 / reconciled 2026-08-15

Status: **evidence snapshot, not a new GitHub Release**  
Parent hardening issue: #52  
Repository: `velantrian/Velantrim-ExoCortex-Titan`

## 1. Scope and maturity

This document records the repository evidence for Titan 9.0 across the Issue #52
public-truth closure. It is deliberately narrower than a release announcement.

Current maturity claim: **research-grade prototype moving toward production
hardening**. This report does not claim production authority, an independent
security audit, a certified compliance program, or a new packaged release.

The C10 public-truth/release-evidence closure is protected-merged as:

- C10 accepted PR head: `a07c2a6ec0b8901ee0aeb7e7ca93919f36a6f0ea`;
- C10 merge/main SHA: `0074ea569030e0708ea345693c74e8506ada94a5`;
- parent SHA: `0b2c49d701b88d12c66042148c19199638130d03`;
- GitHub commit verification: `verified=true`, `reason=valid`;
- public version: Titan `v9.0.0` (`pyproject.toml` / `core.__version__`).

The earlier `main@0b2c49d...` evidence remains a historical pre-C10 baseline, not the
current merge pointer.

## 2. C10 exact-head and post-merge evidence

Final C10 exact-head acceptance:

| Evidence | Run | Result |
|---|---:|---|
| Full CI | #1188 / `31868539149` | SUCCESS, 5/5 jobs |
| Docker build/runtime hardening checks | #784 / `31868539169` | SUCCESS |
| CodeQL Python security analysis | #26 / `31868539183` | SUCCESS |
| Ready aggregate merge evidence | #1247 / `31868852712` | SUCCESS |

Post-merge evidence on exact `main@0074ea569030e0708ea345693c74e8506ada94a5`:

| Evidence | Run | Result |
|---|---:|---|
| Full CI | #1189 / `31868888467` | SUCCESS, 5/5 jobs |
| Docker build/runtime hardening checks | #785 / `31868888451` | SUCCESS |
| CodeQL Python security analysis | #27 / `31868888435` | SUCCESS |
| Aggregate merge evidence | #1248 / `31868888440` | SUCCESS |

Full CI includes pytest, the blocking core coverage ratchet, deterministic lock SBOM,
dependency vulnerability audit and reproducible-wheel verification. Docker includes the
final-runtime container SBOM/hardening path. These are repository CI results for the cited
commit; they are not a claim that all deployment environments, workloads or external
services have been tested.

A prior Ready aggregate #1246 / `31868809837` failed only because the PR body omitted the
machine metadata line `Notion access: AVAILABLE`. The same-page Notion synchronization had
already occurred. Correcting the PR metadata changed no source bytes/head; fresh aggregate
#1247 then succeeded.

## 3. Supply-chain evidence carried into this snapshot

Issue #52 converged the following bounded controls:

- immutable Docker base-image digest policy;
- CI and Docker consumption of the repository's locked Python dependency set;
- blocking dependency vulnerability audit;
- deterministic lock SBOM with source/input binding;
- final-runtime container/OS+Python SBOM generation and artifact evidence;
- blocking core coverage ratchet;
- bounded `uv` Dependabot policy and live GitHub-managed execution proof;
- bounded Python CodeQL workflow/platform evidence;
- reproducible Titan Python wheel procedure with two clean byte-identical builds;
- World Skills admission behind structured provenance/domain review, existing TruthGate,
  existing PromotionGateway and CAS.

Important boundary: **reproducible Titan wheel does not mean the OCI image is
byte-reproducible**. No such stronger claim is made here.

## 4. Runtime/public-truth boundary closed by C10

C10 closed concrete public-truth and diagnostic-boundary drift:

- `/system/epigenetic` now reuses the existing API-key owner and converts internal endpoint
  exceptions to a generic 500 detail without exposing raw exception text;
- `docker-compose.prod.yml` is documented as the hardened deny-by-default profile;
- historical `docker-compose.yml` is documented as compatibility/research behavior and is
  not presented as the hardened production configuration;
- automatic immutable-core scheduling is not runtime-wired and is not claimed as an
  automatic 24-hour snapshot service;
- the C9 World Skills direct promotion exception is removed from current public status;
- README/status/security wording is qualified so implementation evidence is not represented
  as production authority.

Dedicated `/system/epigenetic` regressions run inside the full suite. Their test module
resolves current runtime modules at test time because integration tests intentionally
reload `server`, `core.*` and `api.*`; this prevents stale module references from producing
false auth results.

## 5. Historical GitHub Release classification

At audit time the repository exposes one historical GitHub Release/tag:

- tag: `9.0-production-db-20260712`;
- tag commit: `d2d53a123524986f4a57be08dd9cd591075ee874`;
- published: 2026-07-12;
- asset: `velantrim_production_db_20260712.zip`;
- recorded asset digest: `sha256:0da2c51e034a622e54e298f9a6705b89352e4dd1f7919a22a27d2d970df15e7a`;
- GitHub Release title reads `Velantrim Crystal v0.1.0 — Verifiable local-first AI memory core`.

That title is cross-project/mislabeled metadata inside the Titan repository. The release is
therefore classified for current Titan truth as:

`HISTORICAL_MISLABELED_NOT_CURRENT_TITAN_RELEASE_EVIDENCE`

This audit does **not** reinterpret it as a current Titan release and does not create a
replacement tag or release. Absence of a new 2026-08-15 packaged GitHub Release is explicit
rather than hidden.

## 6. Known limitations / residual risks

This evidence snapshot does not close or weaken the following known boundaries:

1. no independent third-party security audit or penetration test;
2. no certified GDPR/compliance program;
3. SQLite concurrency/crash behavior has bounded characterization, not a production-scale
   or unlimited-concurrency guarantee;
4. the hardened profile's remote-egress denial is enforced at the Titan application/policy
   layer, not as host/network-namespace isolation;
5. TruthPolicy remains fail-open in its current read-path failure mode and is therefore
   pinned off by the hardened production profile;
6. response-integrity checks do not yet cover every provider-generated final answer path;
7. response auditing remains unreachable without the event bus and is pinned off by the
   hardened profile;
8. `ImmutableCoreScheduler` is not started by the server, so automatic scheduled integrity
   snapshots are not claimed;
9. this evidence document is not a software bill of materials itself, a signed attestation,
   or a substitute for the workflow artifacts it references;
10. the legacy World Skills corpus is not retroactively reviewed merely because the new
    admission path fails closed.

## 7. Authority invariants

Nothing in C10 or the C11 final documentation reconciliation changes the authority state:

- Continuity: `12/12` complete;
- project-state schema: `v7`;
- Continuity runtime enabled: `false`;
- Operator GO: `false`;
- runtime authority: `false`;
- production authority: `false`;
- Canon: local;
- remote Canon: forbidden.

Historical bounded observation evidence remains historical evidence; it is not current
enablement or production authority.

## 8. C11 closure boundary

C11 exists only to reconcile final repository/Notion maturity state and the historical PR
queue acceptance text. It does not create a release or change runtime behavior. Parent #52
may close only after the C11 documentation PR has exact-head acceptance, protected merge,
post-merge evidence and same-page Notion FINAL/read-back, and the final requirement matrix
contains no `PARTIAL`, `UNKNOWN` or `NOT VERIFIED` rows.
