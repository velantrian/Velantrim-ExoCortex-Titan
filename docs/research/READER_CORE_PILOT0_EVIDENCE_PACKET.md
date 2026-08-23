# Reader Core Pilot-0 evidence packet

Status: **CANDIDATE_PREPARATION_ONLY / NOT_PRODUCTION_EVIDENCE**

Base at packet creation: `097ca0d4d6e3067b4b7f801dd9bbb37c8cf0e566`

This packet defines the next bounded operational step for Issue #120 after the
Reader Product benchmark adapter landed in main. It does **not** acquire source
files, assert rights clearance, create human labels, execute a benchmark,
calibrate thresholds, authorize shadow integration, or grant live/production
authority.

## Hard boundary

```text
CANDIDATE_CORPUS_ONLY
NO_RIGHTS_CLEARANCE_ASSERTION
NO_SOURCE_HASHES_UNTIL_LOCAL_FREEZE
NO_MODEL_GENERATED_GOLD_LABELS
NO_SELF_ADJUDICATION
NO_BENCHMARK_RESULT_CLAIM
NO_THRESHOLD_CALIBRATION
NO_SHADOW_BURN_IN
NO_OPERATOR_GO
NO_QUERY_WIRING
NO_MEMORY_OR_CANON_WRITE
NO_CRYSTAL_CHANGES
```

## Why rights remain fail-closed

NIST's Research Library states that NIST publications are generally public
domain and not subject to copyright in the United States. NIST also states in
its copyright guidance that NIST publications may remain copyright-protected
outside the United States and that permission for reuse outside the U.S. may be
required.

Because Pilot-0 may be executed from Germany, the corpus must **not** be marked
rights-cleared solely from the U.S. public-domain rule. Each document needs a
recorded rights basis applicable to the actual benchmark location/use before its
bytes enter a production-evidence corpus package.

Reference surfaces checked for this packet:

- NIST Library FAQ: https://www.nist.gov/nist-research-library/library-faqs
- NIST copyright FAQ: https://www.nist.gov/cyberframework/faqs

## Candidate corpus

All entries below are **CANDIDATE_ONLY** and **UNFROZEN**.

| Candidate | Official identity | Official source | Current rights state | Freeze state |
| --- | --- | --- | --- | --- |
| AI Risk Management Framework 1.0 | NIST AI 100-1 | https://doi.org/10.6028/NIST.AI.100-1 | `RIGHTS_REVIEW_REQUIRED_OUTSIDE_US` | `UNFROZEN` |
| Generative AI Profile | NIST AI 600-1 | https://doi.org/10.6028/NIST.AI.600-1 | `RIGHTS_REVIEW_REQUIRED_OUTSIDE_US` | `UNFROZEN` |
| Reducing Risks Posed by Synthetic Content | NIST AI 100-4 | https://doi.org/10.6028/NIST.AI.100-4 | `RIGHTS_REVIEW_REQUIRED_OUTSIDE_US` | `UNFROZEN` |
| Secure Software Development Framework v1.1 | NIST SP 800-218 | https://doi.org/10.6028/NIST.SP.800-218 | `RIGHTS_REVIEW_REQUIRED_OUTSIDE_US` | `UNFROZEN` |
| Secure Software Development Practices for Generative AI and Dual-Use Foundation Models | NIST SP 800-218A | https://doi.org/10.6028/NIST.SP.800-218A | `RIGHTS_REVIEW_REQUIRED_OUTSIDE_US` | `UNFROZEN` |

The European Commission DGT guide remains deferred from this packet until its
exact reuse basis is independently verified. OpenStax remains excluded from the
candidate set unless an explicit permission path is established.

## Source-freeze gate

A candidate may move from `UNFROZEN` to `FROZEN_FOR_ANNOTATION` only after all
of the following are recorded from the exact local bytes that will be annotated:

- canonical publication identifier and title;
- exact retrieval URL / DOI;
- retrieval timestamp;
- applicable usage basis and rights reference;
- privacy class;
- redistribution flag;
- media type;
- SHA-256 of exact bytes;
- byte size;
- UTF-8 character count of the normalized benchmark text representation;
- `source_revision == content_sha256` under the existing RDR-11 contract;
- successful local `CorpusDocumentDescriptor` / corpus-package verification.

No placeholder digest, guessed revision, mutable web-page identity, or DOI alone
may stand in for the exact frozen source bytes.

## Annotation gate

Annotation remains `NOT_STARTED` until the source-freeze gate passes.

The existing `READER_CORE_ANNOTATION_GUIDELINE_V1.md` and RDR-16 intake
contracts remain authoritative. Pilot-0 requires, per document:

1. at least two genuinely independent annotators;
2. blind annotation assignments;
3. claims with exact source spans;
4. critical exceptions;
5. qualifiers;
6. directed relations and contradictions where supported by source evidence;
7. an adjudicator independent from all source annotators;
8. explicit resolution of every disagreement;
9. only an `ADJUDICATED` label set entering benchmark scoring.

Model-generated labels, maintainer self-review, or a single person's duplicate
passes do not satisfy independent human annotation.

## Benchmark gate

Only a fully verified adjudicated case may enter the merged RDR-28 adapter.
Each case then requires two replays through the existing RDR-14 executor.
Unavailable Reader Product v1 measurements remain explicitly unavailable; they
must not be fabricated or inferred from unrelated runtime telemetry.

A successful local batch still does not satisfy Issue #120 by itself. Retained
raw per-case evidence, signed reports, measured threshold calibration, separate
shadow burn-in, and an explicit Operator decision remain mandatory.

## Pilot-0 state matrix

| Gate | State now | Evidence required to advance |
| --- | --- | --- |
| Candidate identification | `READY` | official publication identity recorded |
| Rights clearance for actual execution jurisdiction | `BLOCKED` | applicable permission / rights basis per document |
| Exact source freeze | `NOT_STARTED` | local exact bytes + SHA-256 + descriptor verification |
| Independent annotation | `NOT_STARTED` | >=2 independent annotators per document |
| Independent adjudication | `NOT_STARTED` | complete disagreement resolution |
| Real two-replay benchmark batch | `NOT_STARTED` | adjudicated verified cases + RDR-28 execution |
| Signed retained evidence | `NOT_STARTED` | canonical evidence bundle/signatures |
| Threshold calibration | `NOT_STARTED` | measured real-batch data |
| Shadow burn-in | `NOT_STARTED` | separate reviewed shadow-only integration |
| Operator decision | `NOT_STARTED` | explicit human decision after evidence review |

## Next external action

The next real-world action is **rights clearance**, not another Reader algorithm.
For each selected publication, obtain or record a reuse basis applicable to the
actual benchmark jurisdiction and use. Only after that evidence exists should the
exact document bytes be frozen and annotation assignments be issued.
