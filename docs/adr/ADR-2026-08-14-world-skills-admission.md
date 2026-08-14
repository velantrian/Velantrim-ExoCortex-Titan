# ADR — World Skills provenance and Canon admission

**Status:** accepted for C9 / #52  
**Date:** 2026-08-14  
**Issue:** #52

## Context

World Skills Core predates Titan's current single-fact promotion ownership. The historical
curated-ingest path parsed markdown rows, stored them as external `WORLD_FACT` records,
and then called `SQLiteGraphStore.promote_to_validated()` directly. That route was
explicitly CI-locked as a `KNOWN_EXCEPTION` in the promotion ownership inventory.

The exception no longer matches parent #52. #52 requires every World Skills candidate to
carry structured truth/provenance/confidence/risk/limitations/review metadata before
admission, and requires an admission path equivalent to:

```text
Draft
→ Quarantine
→ Provenance Check
→ Domain Review
→ Truth Gate
→ Canon
```

The current markdown corpus does not provide that metadata for every row. Treating the
file location, type token, or the fact that a row was historically curated as evidence
would fabricate provenance and review state.

`SQLiteGraphStore.validate_and_promote()` also deliberately rejects an illegal direct
`Observed → Validated` transition. Any safe World Skills migration therefore must retain
the ordinary ESM ladder while ensuring weak/unreviewed candidates never move toward Canon.

## Decision

Keep `core/world_skills_ingest.py` as the existing curated-ingest orchestration surface,
but remove its direct `promote_to_validated()` exception.

### Candidate contract

Every parsed candidate exposes these #52 fields:

```text
truth_status
source_refs
confidence
risk_domain
limitations
review_status
reviewer
reviewed_at
```

Legacy rows receive safe non-claims rather than inferred evidence:

```text
truth_status = Draft
source_refs = []
risk_domain = ""
limitations = ""
review_status = unreviewed
reviewer = ""
reviewed_at = ""
```

Their historical `confidence=0.85` parser value is preserved for compatibility, but it
cannot overcome missing provenance or review gates.

### Admission path

```text
parsed candidate
  ↓
Draft / Quarantine
  ↓
Provenance Check
  ├─ source_refs missing/invalid/duplicated → STOP
  ↓
Domain Review
  ├─ risk_domain / limitations missing → STOP
  ├─ review_status != approved → STOP
  ├─ reviewer missing or reviewer == ingest actor → STOP
  ├─ reviewed_at missing / naive / malformed → STOP
  ↓
existing TruthGate read-only precheck
  ├─ ordinary explicit risk → BALANCED
  └─ explicit high-risk token → PRECISION
  ↓ only on PASS
legal ESM ladder → Supported
  ↓
existing PromotionGateway
  ↓
existing validate_and_promote()
  ↓
TruthGate recheck + CAS / VersionStore / AuditChain / active outbox semantics
  ↓
Validated = admitted local Canon fact
```

No confidence/evidence thresholds are copied into World Skills. Risk metadata chooses
only between existing `BALANCED` and existing `PRECISION` TruthGate modes; TruthGate owns
the numerical policy.

The read-only precheck intentionally occurs before ESM movement. A weak or insufficiently
sourced candidate therefore remains `Observed`. The final PromotionGateway evaluation is
still required after the legal ladder so the durable Supported snapshot is re-evaluated
and committed through the accepted CAS owner.

### Deterministic identity and replay evidence

C9 computes:

- a SHA-256 candidate digest over the candidate claim plus admission-bearing metadata;
- an order-independent SHA-256 pack ID over candidate digests.

These identifiers bind replay evidence to exact candidate content and review metadata.
They are integrity identifiers, **not cryptographic human signatures** and must never be
described as proof that a named reviewer owns a signing key.

The earlier promotion-inventory phrase `signed provenance` was underspecified. C9 narrows
the admitted claim to attributable `source_refs`, explicit reviewer identity/timestamp,
and content-bound deterministic digests. A future cryptographic reviewer-signature system,
if needed, requires its own key/identity owner and is not fabricated here.

## Existing owners preserved

- candidate parsing/admission orchestration: `core/world_skills_ingest.py`;
- ESM legality and non-Validated ladder movement: existing `SQLiteGraphStore` methods;
- final typed promotion caller: existing `PromotionGateway`;
- truth thresholds and verdict: existing `TruthGate`;
- Canon mutation/CAS/audit/outbox semantics: existing `SQLiteGraphStore.validate_and_promote()`.

C9 creates no second TruthGate, WriteGate, Canon writer, reviewer registry, key registry,
or global policy engine.

## Rejected alternatives

### Keep direct curated promotion because the corpus is "trusted"

Rejected. File location and historical curation are not attributable provenance or a
review verdict, and the direct route bypasses the required TruthGate admission path.

### Fill missing source/reviewer fields automatically

Rejected. Inferring provenance or reviewer identity from prose, filenames, Git history,
or an LLM would manufacture evidence.

### Weaken BALANCED TruthGate so current rows pass

Rejected. A curated-pack compatibility problem must not weaken every standard caller.

### Create a second WorldSkillsTruthGate or ArtifactCanon

Rejected. Titan already has accepted owners for truth evaluation and Canon mutation.

### Claim the deterministic digest is a digital signature

Rejected. SHA-256 content binding detects content drift but does not authenticate a human
signer without a separately governed key system.

## Consequences

### Positive

- legacy World Skills rows can still be parsed and used in scratch analysis;
- incomplete rows fail closed and no longer auto-promote;
- complete candidates have a deterministic route to the existing TruthGate/CAS owner;
- high-risk metadata automatically selects the stricter existing TruthGate mode;
- direct World Skills `Validated` authority disappears from the ownership guard;
- replay/pack identity becomes machine-verifiable.

### Costs / limitations

- the existing legacy corpus is not retroactively declared reviewed or sourced;
- most legacy rows will remain quarantined until real provenance/review metadata is added;
- C9 does not cryptographically authenticate reviewer identity;
- C9 does not activate runtime, remote Canon, Operator GO, or production authority.

## Non-claims

This ADR does not claim that every legacy World Skills statement is true, reviewed, or
ready for Canon. It does not authorize semantic rearchitecture of the corpus, automatic
source discovery, network lookup, LLM review, or production activation. It only defines
the bounded fail-closed admission contract required by #52.
