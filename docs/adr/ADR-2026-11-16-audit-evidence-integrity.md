# Preserve admission and evidence invariants under failure

Status: proposed implementation in draft PR; no deployment activation.

The audit of main `485c4b0906ec35829ff7231c6276bf7d817f096f` demonstrated late
origin classification, a classifier exception becoming UNKNOWN admission, optional
FactsPack policy in the main query path, and repetition-derived confidence influencing
promotion selection.

Both modality axes must be final before the existing mandatory admission gate.
An unavailable required classifier rejects the attempted write without durable mutation.
UNKNOWN remains a classification sentinel; a successful classification may legitimately
return UNKNOWN under the existing policy. Invalid explicit types are input errors.

The query pipeline requires the existing FactsPack policy and withholds evidence on
failure. The compatibility helper's optional raw-pack mode remains available only to
callers that explicitly choose it; it is not the canonical answering path.

Consolidation uses stored confidence unchanged. Token overlap, repeated sources,
negations and conditions do not establish independent corroboration. Removing the
heuristic boost preserves the existing promotion gateway as the sole admission owner.
An eventual independent-evidence mechanism needs a separate provenance contract.

BM25 ordering may use zero or negative Okapi scores; lexical membership determines
candidate eligibility. Retrieval score never becomes epistemic confidence.
Explicit invalid promotion modes fail rather than silently weakening expected policy.

Alternatives rejected: normalization to UNKNOWN on errors, unfiltered fallback answers,
a count-only confidence bonus, or a second admission/promotion owner. Existing CAS,
VersionStore, audit/outbox and subjective user-report policies remain in place.

Verification: new single/batch create/update fault-injection tests, policy unavailable
answer tests, repeated/contradictory-source consolidation regression, invalid-mode
pre-read rejection, and small-corpus BM25 regression. See the PR for exact runs.
