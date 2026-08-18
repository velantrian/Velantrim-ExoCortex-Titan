# ADR — Typed Evidence Reference v1 Contract

- **Status:** proposed for the contract-only first PR
- **Date:** 2026-08-19
- **Owner:** existing TruthGate / canonical-promotion owners; no new authority owner
- **Documentation impact:** `GITHUB_AND_NOTION`

## Context

`core/truth_gate.py` currently derives its evidence threshold from legacy
`metadata.evidence_refs`, a list of unstructured strings. That shape can express
cardinality but cannot prove source resolvability, fragment integrity, lineage or
independence. It is therefore not an adequate contract for a future evidence-gated
admission decision.

Titan already has `core/evidence.py` and `EvidenceItem`, which model scoring inputs
such as source type, domain, directness and content hash. That object remains useful
for evidence-strength scoring, but it is not an immutable, source-resolvable reference
contract and must not be silently promoted into one.

The first increment must define and test the narrow local contract before changing
TruthGate outcome semantics, SQLite schema, ingestion, registry persistence or
canonical-promotion authority.

## Decision

Introduce two **unwired, local-only prototype modules**:

- `core/evidence_reference.py` defines immutable `EvidenceReference` v1 with exact
  schema parsing, canonical serialization and a SHA-256 reference digest.
- `core/evidence_registry.py` defines an in-memory `EvidenceRegistry` prototype,
  local `EvidenceSourceRecord`/`EvidenceFragmentRecord` metadata, deterministic
  `EvidenceReferenceValidator`, and content-minimized `EvidenceValidationReceipt`.

`EvidenceReference` has a versioned exact schema with stable reference, source,
fragment and lineage identifiers; SHA-256 source/fragment digests; an explicit local
span; an independence class; and a timezone-aware capture timestamp. It carries no
raw source text, quote, URL, credentials, prompt, provider payload or user content.

The prototype resolver accepts an explicitly supplied local registry only. It performs
no filesystem scan, network access, provider call, retrieval, LLM invocation, database
write or background work. It emits reason-coded outcomes for duplicates, unknown or
revoked sources/fragments, digest/lineage mismatches and invalid spans. Its receipt
separates raw, unique, validated and distinct-independent-lineage counts.

## Authority boundary

- **Canon / ESM writes:** none. The prototype exposes no `store_fact`,
  `transition_esm` or `validate_and_promote` method.
- **TruthGate thresholds:** unchanged. `TruthGate` remains the existing owner and its
  `evidence_count` behavior is deliberately untouched in this PR.
- **Promotion/CAS:** unchanged. The prototype is not a second promotion gateway and
  cannot trigger an ESM transition.
- **Persistence/schema:** none. The registry is in-memory; no migration is admitted.
- **Network/provider access:** none. Source resolution is local and explicit.
- **Runtime wiring/activation:** none. No route, startup hook, worker, feature flag,
  default configuration or Operator GO is introduced.
- **Policy authority:** unchanged. This contract neither grants permission nor replaces
  PolicyKernel/WriteGate/TruthGate policy.

## Data and privacy

The v1 reference stores only technical identifiers, digests, local selectors and
classification metadata. It must not persist full source content or public URL strings
in its canonical JSON or validation receipt. Future registry persistence requires a
separate admission decision and data-classification review.

## Failure semantics

Parsing is strict: missing or unexpected fields, unknown schema versions, invalid
technical identifiers, malformed SHA-256 digests, invalid spans and naive timestamps
are rejected. Registry validation is fail-closed for unresolvable/tampered/revoked
references. A validated reference in the prototype means only that its local metadata
and integrity fields resolve; it does not declare the linked claim true.

No retry, fallback reference synthesis, automatic legacy conversion or automatic fact
reclassification is permitted.

## Compatibility and rollout

This first PR adds the new `evidence_refs_v1` contract surface only. It does not
change the legacy `metadata.evidence_refs: list[str]` field and does not alter historic
facts. A later, separately reviewed sequence may add:

1. a persisted local registry and transaction boundary;
2. `LEGACY`, `OBSERVE` and opt-in `ENFORCE` validation modes;
3. receipt attachment by the existing authorized audit/metadata owner;
4. producer migration only where stable source artifacts exist.

No legacy fact may be auto-upgraded, downgraded or assigned synthetic provenance.

## Validation

Focused tests must prove deterministic canonical reference/receipt digests, strict
schema rejection, immutability, duplicate-ID deduplication, same-lineage counting,
derived-reference treatment, unknown/revoked/tampered source handling, receipt
content minimization and absence of write/promotion shortcuts. Repository Ruff, Mypy,
full pytest and the usual CI gates remain required before a draft PR can be promoted.

## Rollback

The modules are unwired and hold no persistent state. Rollback is a normal reversion of
this ADR, the two modules and their focused tests. No data migration, runtime shutdown
or canonical state recovery is required.

## Explicit non-goals

This ADR does not authorize TruthGate enforcement changes, confidence-score changes,
NLI contradiction detection, registry persistence, external evidence fetching, source
scraping, provider calls, network egress, new policy engine, new canonical write path,
retry policy, SQLite migration/WAL/backend work, runtime enablement, Operator GO,
runtime authority, production authority or a claim of automated truth verification.
