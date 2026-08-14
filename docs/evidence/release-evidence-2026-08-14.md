# Release evidence snapshot — 2026-08-14

Status: **evidence snapshot, not a new GitHub Release**  
Parent hardening issue: #52  
Repository: `velantrian/Velantrim-ExoCortex-Titan`

## 1. Scope and maturity

This document records the repository evidence available for Titan 9.0 during the
Issue #52 public-truth closure. It is deliberately narrower than a release
announcement.

Current maturity claim: **research-grade prototype moving toward production
hardening**. This report does not claim production authority, an independent
security audit, a certified compliance program, or a new packaged release.

The evidence baseline for this snapshot is the signed `main` commit after the
World Skills admission closure:

- baseline merge SHA: `0b2c49d701b88d12c66042148c19199638130d03`;
- parent SHA: `1909e3f10330c4032641970ad0934a67649681e3`;
- GitHub commit verification: `verified=true`, `reason=valid`;
- public version: Titan `v9.0.0` (`pyproject.toml` / `core.__version__`).

The C10 merge SHA is intentionally not invented here before merge. The final C10
merge SHA and post-merge evidence belong in the PR/Issue #52 final closure record
and the existing Notion status page.

## 2. Baseline CI evidence

The baseline commit above has completed repository-owned push evidence:

| Evidence | Run | Result |
|---|---:|---|
| Full CI | #1181 / `31839014136` | SUCCESS, 5/5 jobs |
| Docker build/runtime hardening checks | #779 / `31839014137` | SUCCESS |
| CodeQL Python security analysis | #19 / `31839014207` | SUCCESS |
| Aggregate merge evidence | #1213 / `31839014181` | SUCCESS |

The Full CI evidence for this baseline includes the full pytest/coverage path:
**4160 tests passed** and repository coverage **76%**, above the enforced **74%**
ratchet. CI also includes the deterministic dependency-lock SBOM, dependency
vulnerability audit and reproducible-wheel verification paths.

These are repository CI results for the cited commit. They are not a claim that
all deployment environments, workloads or external services have been tested.

## 3. Supply-chain evidence carried into this snapshot

Issue #52 has already converged the following bounded controls before this
snapshot:

- CI and Docker consume the repository's locked dependency set;
- dependency vulnerability audit is blocking;
- deterministic lock SBOM exists;
- container SBOM generation/verification exists;
- coverage ratchet is blocking;
- Dependabot policy is explicit;
- CodeQL is a blocking/observed security-analysis surface;
- the Python wheel is rebuilt twice and verified byte-identical under the
  repository procedure;
- World Skills candidates are no longer admitted to local Canon without the
  C9 provenance/domain-review/TruthGate/PromotionGateway path.

Important boundary: **reproducible Titan wheel does not mean the OCI image is
byte-reproducible**. No such stronger claim is made here.

## 4. Runtime/public-truth boundary in this C10 candidate

The C10 workstream exists because documentation and one diagnostic endpoint did
not fully match the hardened runtime boundary:

- `/system/epigenetic` is being brought under the existing API-key boundary and
  generic 500-response sanitization, with dedicated regression tests;
- `docker-compose.prod.yml` is the hardened, deny-by-default production profile;
- the historical `docker-compose.yml` is a compatibility/research convenience
  profile and must not be presented as the hardened production configuration;
- automatic immutable-core scheduling is not runtime-wired and therefore is not
  claimed as an automatic 24-hour snapshot service;
- the C9 World Skills promotion exception has been removed from current public
  status text.

Exact-head CI for the C10 candidate must be recorded in the PR before merge; this
document does not pre-claim those future results.

## 5. Historical GitHub Release classification

At audit time the repository exposes one historical GitHub Release/tag:

- tag: `9.0-production-db-20260712`;
- tag commit: `d2d53a123524986f4a57be08dd9cd591075ee874`;
- published: 2026-07-12;
- asset: `velantrim_production_db_20260712.zip`;
- recorded asset digest: `sha256:0da2c51e034a622e54e298f9a6705b89352e4dd1f7919a22a27d2d970df15e7a`;
- GitHub Release title currently reads `Velantrim Crystal v0.1.0 — Verifiable local-first AI memory core`.

That title is cross-project/mislabeled metadata inside the Titan repository. The
release is therefore classified for current Titan truth as:

`HISTORICAL_MISLABELED_NOT_CURRENT_TITAN_RELEASE_EVIDENCE`

This audit does **not** reinterpret it as a current Titan release and does not
create a replacement tag or release. Absence of a current 2026-08-14 GitHub
Release is explicit rather than hidden.

## 6. Known limitations / residual risks

This evidence snapshot does not close or weaken the following known boundaries:

1. no independent third-party security audit or penetration test;
2. no certified GDPR/compliance program;
3. SQLite concurrency/crash behavior has bounded characterization, not a
   production-scale or unlimited-concurrency guarantee;
4. the hardened profile's remote-egress denial is enforced at the Titan
   application/policy layer, not as host/network-namespace isolation;
5. TruthPolicy remains fail-open in its current read-path failure mode and is
   therefore pinned off by the hardened production profile;
6. response-integrity checks do not yet cover every provider-generated final
   answer path;
7. response auditing remains unreachable without the event bus and is pinned
   off by the hardened profile;
8. `ImmutableCoreScheduler` is not started by the server, so automatic scheduled
   integrity snapshots are not claimed;
9. this evidence document is not a software bill of materials itself, a signed
   attestation, or a substitute for the workflow artifacts it references.

## 7. Authority invariants

Nothing in this C10 evidence/reconciliation work changes the current authority
state:

- Continuity: `12/12` complete;
- project-state schema: `v7`;
- Continuity runtime enabled: `false`;
- Operator GO: `false`;
- runtime authority: `false`;
- production authority: `false`;
- Canon: local;
- remote Canon: forbidden.

Historical bounded observation evidence remains historical evidence; it is not
current enablement or production authority.
