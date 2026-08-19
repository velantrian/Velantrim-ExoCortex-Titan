# ADR — Typed Evidence Reference v1 Contract

- **Status:** proposed on draft PR #355; P1 remediation applied
- **Date:** 2026-08-19
- **Remediation checkpoints:** `cf58211a62ffc1df6b8b764ff07df3536fc945d0` → `c90ecc11617994e15670e8f9d81d1d1c143ccb1b`
- **Owner:** contract-only prototype; existing TruthGate / canonical-promotion owners unchanged
- **Documentation impact:** `GITHUB_AND_NOTION`

## Context

`core/truth_gate.py` currently derives its evidence threshold from legacy
`metadata.evidence_refs`, a list of unstructured strings. That shape can express
cardinality but cannot prove source resolvability, fragment integrity, lineage or
independence. It is therefore not an adequate contract for a future evidence-gated
admission decision.

Titan already has `core/evidence.py` and `EvidenceItem`, which model scoring inputs such
as source type, domain, directness and content hash. That object remains useful for
evidence-strength scoring, but it is not an immutable, source-resolvable reference
contract and must not be silently promoted into one.

The first increment defines and tests a narrow local contract before any change to
TruthGate outcome semantics, SQLite schema, ingestion, registry persistence or
canonical-promotion authority.

Review of the first draft found three P1 defects in the local registry prototype: mutable
fragment metadata, missing mapping-key/embedded-ID consistency checks, and caller-
controlled effective-independence classification. The bounded remediation removed those
defects without adding runtime or policy authority. A follow-up exact-head hardening
checkpoint binds each validation run to one immutable `EvidenceRegistrySnapshot` rather
than reading a mutable builder during validation.

## Decision

Introduce two **unwired, local-only prototype modules**:

- `core/evidence_reference.py` defines immutable `EvidenceReference` v1 with exact
  schema parsing, canonical serialization and a SHA-256 reference digest.
- `core/evidence_registry.py` defines local immutable source/fragment records, an
  `EvidenceRegistrySnapshot`, a mutable in-memory builder that can only supply snapshots
  to the validator, deterministic `EvidenceReferenceValidator`, and content-minimized
  `EvidenceValidationReceipt`.

`EvidenceReference` has a versioned exact schema with stable reference, source, fragment
and lineage identifiers; SHA-256 source/fragment digests; an explicit local span; and a
timezone-aware capture timestamp. It deliberately carries no producer-owned independence
classification and no raw source text, quote, URL, credentials, prompt, provider payload
or user content.

The local registry is an integrity/resolution prototype only. `EvidenceSourceRecord` does
**not** carry `effective_independence_class`. Registry construction validates technical
identifiers, exact lower-case SHA-256 digests, allowed spans, source status and fragment
record structure. A fragment mapping key must equal the embedded
`EvidenceFragmentRecord.fragment_id`, and source fragment mappings are copied into an
immutable snapshot.

`EvidenceRegistrySnapshot` defensively copies the source mapping, validates source mapping
keys against embedded `source_id`, exposes read-only resolution for one validation run,
and has a deterministic content digest. The mutable `InMemoryEvidenceRegistry` is only a
builder; validators consume `snapshot()` rather than live mutable registry state.

A valid reference may increase `validated_reference_count`, but this contract-only
prototype does not classify trusted independence. `EvidenceValidationOutcome` contains no
effective-independence field, and `distinct_independent_lineage_count` remains zero. A
future non-zero independence result requires a separately authorized, snapshot-bound
policy owner. Neither a producer nor this local Titan registry may grant that authority to
itself.

The receipt binds the exact immutable registry metadata used by validation through
`registry_snapshot_digest`. That digest proves deterministic local snapshot identity only;
it is not authentication, target-domain authorization, evidence of independence, or proof
that a referenced claim is true.

The prototype performs no filesystem scan, network access, provider call, retrieval, LLM
invocation, database write or background work. It emits deterministic, reason-coded
outcomes for duplicate IDs, conflicting IDs, unknown/revoked sources or fragments,
digest/lineage mismatches and invalid spans.

## Authority boundary

- **Canon / ESM writes:** none. No canonical mutation method is introduced.
- **TruthGate thresholds:** unchanged. Current legacy `evidence_count` behavior is not
  modified by this PR.
- **Promotion/CAS:** unchanged. The prototype is not a promotion gateway and cannot
  trigger an ESM transition.
- **Persistence/schema:** none. The registry remains in-memory; no migration is admitted.
- **Network/provider access:** none. Source resolution is local and explicit.
- **Runtime wiring/activation:** none. No route, startup hook, worker, feature flag,
  default configuration or Operator GO is introduced.
- **Policy authority:** unchanged. This contract neither grants permission nor replaces
  PolicyKernel / WriteGate / TruthGate policy.
- **Independence authority:** none is created here. Neither producer payload nor supplied
  Titan registry may self-grant effective trusted independence.
- **Ecosystem boundary:** Titan remains a resolver/projection/prototype in this increment;
  trusted evidence admission remains with the separately authorized evidence owner.

## Data and privacy

The v1 reference stores only technical identifiers, digests and local selectors. The
validation receipt stores bounded counts, reason-coded outcomes and the registry snapshot
digest. Neither artifact persists full source content or public URL strings. Future
registry persistence requires a separate admission decision, ownership decision and
data-classification review.

## Failure semantics

Parsing is strict: missing or unexpected fields, producer-supplied independence fields,
unknown schema versions, invalid technical identifiers, malformed SHA-256 digests,
invalid spans and naive timestamps are rejected. Registry construction also rejects
mapping-key/embedded-record-ID mismatch and malformed registry metadata.

Registry validation is fail-closed for unresolvable, tampered or revoked references.
Conflicting payloads that reuse one `reference_id` are all rejected rather than selecting
an input-order winner. A validated reference means only that its local metadata and pinned
integrity fields resolve; it does not declare the linked claim true or independent.

No retry, fallback reference synthesis, automatic legacy conversion or automatic fact
reclassification is permitted.

## Compatibility and rollout

This first PR defines the typed contract intended for a later separately admitted
producer/integration surface. It does not add a new metadata field to current facts,
change legacy `metadata.evidence_refs: list[str]`, or alter historic facts.

Any future sequence must be separately reviewed and may include only after explicit
architecture/admission decisions:

1. naming the target-domain-authorized owner for effective independence policy;
2. defining verifiable policy-snapshot semantics and receipt binding;
3. an OBSERVE phase that cannot affect TruthGate outcomes;
4. an ENFORCE phase only after differential, fault and authority-boundary evidence;
5. persistence only after data-classification and transaction-boundary decisions;
6. producer migration only where stable source artifacts exist.

No legacy fact may be auto-upgraded, downgraded or assigned synthetic provenance.

## Validation

The remediated focused contract suite covers canonical digests, strict schema rejection,
immutable source/fragment metadata, immutable validator-facing registry snapshots,
source/fragment mapping-key consistency, identifier/digest/span validation, duplicate and
conflicting IDs, unknown/revoked/tampered references, deterministic snapshot/receipt
evidence and absence of write/promotion shortcuts.

The first P1 remediation checkpoint `cf58211a...` passed GitHub Main CI #1327, Docker #874
and CodeQL #166, and aggregate workflow #1673 completed successfully. The follow-up
snapshot-binding checkpoint is `c90ecc11617994e15670e8f9d81d1d1c143ccb1b`; fresh
exact-head CI must be evaluated on that head and again after this documentation-sync
commit. Green automation is evidence only and is not independent human approval.

## Rollback

The modules are unwired and hold no persistent state. Rollback is a normal reversion of
this ADR, the two modules and their focused tests. No data migration, runtime shutdown or
canonical state recovery is required.

## Explicit non-goals

This ADR does not authorize TruthGate enforcement changes, confidence-score changes, NLI
contradiction detection, registry persistence, external evidence fetching, source
scraping, provider calls, network egress, a new policy engine, a new canonical write path,
retry policy, SQLite migration/WAL/backend work, runtime enablement, Operator GO, runtime
authority, production authority or a claim of automated truth verification.
