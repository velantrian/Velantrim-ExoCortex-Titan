# World Skills provenance and admission contract

Tracking: #52 · ADR: `docs/adr/ADR-2026-08-14-world-skills-admission.md`

World Skills Core is a curated knowledge corpus, but curation is not itself Canon
authority. C9 makes admission explicit and fail-closed while preserving the existing
Titan promotion owners.

## Required candidate metadata

A candidate must expose all of these fields before admission can proceed:

| Field | Meaning | Admission rule |
|---|---|---|
| `truth_status` | pre-Canon human truth status | must be `Supported`; `Validated` cannot be self-declared |
| `source_refs` | attributable evidence references | non-empty unique string list; TruthGate decides sufficiency |
| `confidence` | bounded candidate confidence | finite value in `[0,1]`; TruthGate owns mode threshold |
| `risk_domain` | explicit review risk classification | non-empty; high-risk tokens select existing `PRECISION` mode |
| `limitations` | explicit conditions/known limits | non-empty |
| `review_status` | domain-review result | must be `approved` |
| `reviewer` | attributable reviewer identifier | non-empty and cannot equal `world_skills_ingest` |
| `reviewed_at` | review time | valid timezone-aware ISO-8601 timestamp |

Legacy markdown rows do not contain these fields. The parser does not invent them:
legacy candidates are `Draft`, unreviewed, and have empty provenance/risk/reviewer fields.
They remain usable for scratch analysis but are quarantined from Canon admission.

## Admission state flow

```text
Markdown row
   │
   ▼
Draft candidate
   │
   ▼
Quarantine
   │
   ├── truth_status != Supported ──────────────── STOP
   │
   ▼
Provenance Check
   │
   ├── source_refs missing/invalid/duplicate ─── STOP
   │
   ▼
Domain Review
   │
   ├── risk_domain / limitations missing ─────── STOP
   ├── review not approved ────────────────────── STOP
   ├── reviewer missing/self-review ───────────── STOP
   ├── reviewed_at invalid/naive ───────────────── STOP
   │
   ▼
TruthGate precheck (read-only)
   │
   ├── BALANCED for ordinary explicit risk
   └── PRECISION for explicit high-risk tokens
   │
   ├── reject ─────────────────────────────────── STOP / remains Observed
   │
   ▼
legal ESM ladder → Supported
   │
   ▼
PromotionGateway
   │
   ▼
validate_and_promote()
   │
   ▼
TruthGate recheck + CAS
   │
   ▼
Validated / local Canon
```

The read-only precheck is intentionally before the ESM ladder. A candidate that cannot
meet TruthGate evidence/confidence policy never moves from `Observed` merely because it
was included in a World Skills file.

## Risk handling

C9 does not own numerical truth thresholds.

`risk_domain` is explicit metadata. If it contains a high-risk token such as medical,
health, legal, finance, security, safety, identity, or chemical safety (including the
listed Russian equivalents), C9 requests the existing `CognitiveMode.PRECISION` from
TruthGate. Other explicit risk labels request `BALANCED`.

This means, for example, two source references can satisfy the metadata provenance check
but still fail the stricter PRECISION TruthGate evidence requirement. That failure leaves
the candidate non-canonical.

## Deterministic pack evidence

`world_skill_candidate_digest()` hashes the candidate claim plus admission-bearing
metadata. `compute_world_skills_pack_id()` hashes a sorted set of candidate digests, so
the same candidate pack has the same identity regardless of input order.

Stored candidates carry:

```text
world_skills_admission_contract = world-skills-admission-v1
world_skills_candidate_digest   = <sha256>
world_skills_pack_id            = wsc_pack_<sha256>
evidence_refs                   = source_refs
```

The digest is content integrity evidence, not a digital human signature. C9 does not
create reviewer keys or claim cryptographic reviewer authentication.

## Scratch / analysis behavior

`ingest_facts(..., validate=False)` remains the safe analysis mode used by
`scripts/ingest_world_skills_run.py`. It stores candidates without admission or ESM
movement so deduplication/contradiction research can operate on non-canonical rows.

## Canon authority boundary

C9 does not own final promotion. The chain is deliberately reused:

```text
world_skills_ingest orchestration
  → existing TruthGate
  → existing legal ESM helper to Supported
  → existing PromotionGateway
  → existing SQLiteGraphStore.validate_and_promote()
  → existing TruthGate + CAS / VersionStore / AuditChain / active outbox semantics
```

Do not reintroduce a direct `promote_to_validated()` caller in World Skills. The
repository-wide promotion ownership guard is expected to fail if such a bypass returns.

## Non-claims

C9 does not assert that the current legacy corpus is reviewed, sourced, correct, or ready
for Canon. It does not perform network lookup, source discovery, LLM review, reviewer
identity verification, runtime activation, Operator GO, remote Canon, or production
enablement.
