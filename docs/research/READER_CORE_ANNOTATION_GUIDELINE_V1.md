# Reader Core Annotation Guideline v1

Status: **human-evaluation protocol**

Version identifier:

```text
reader-core.annotation-guideline.v1
```

This guideline is for independent human annotation of Reader Core evaluation
corpora. It creates evaluation evidence only. Labels are not Canon, memory,
policy, graph authority, or live instructions.

## 1. Independence and blinding

Each document must be labelled independently by at least two annotators.

Annotators must not see:

- another annotator's labels;
- model predictions;
- benchmark scores;
- adjudication outcomes;
- promotion thresholds.

Annotators may use only the assigned immutable document revision, this guideline,
and approved annotation tooling. Discussion between annotators about an active
case is prohibited until both label sets are frozen.

The adjudicator must not be one of the source annotators. The adjudicator receives
all frozen source label sets only after independent annotation is complete.

## 2. Source identity and spans

Every label must reference the exact content-addressed document revision.
Offsets are Unicode code-point offsets in the decoded UTF-8 text.

A span must be the smallest exact range that preserves the labelled meaning.
Do not copy source sentences into label metadata. Store only `SourceSpan` values,
enums, codes, and references.

Do not silently repair punctuation, normalize whitespace, or paraphrase the
source. If the source is malformed, label the exact available text and record an
approved issue code outside the semantic label.

## 3. Claims

Create a claim label for each independently assertable proposition required to
understand the document's substantive content.

Do not create a claim for:

- headings without propositional content;
- purely decorative text;
- repeated text that adds no distinct proposition;
- an annotator's inference not stated or necessarily entailed by the source.

Assign the closest `ClaimModality` supported by the source. Keep conditions,
scope restrictions, approvals, temporal limits, and uncertainty attached through
qualifier or applicability codes rather than deleting them from the claim.

When one sentence contains multiple independently true or false propositions,
create separate claims with exact supporting spans.

## 4. Critical exceptions

Create an exception label when text narrows, overrides, suspends, excludes, or
conditions another claim.

The trigger span identifies the explicit exception marker when present. The
statement span covers the full exception statement. Every exception must target
one or more claim labels in the same label set.

Examples include:

- `except` and `excluding` clauses;
- `unless` and `only if` conditions;
- approval requirements;
- emergency overrides;
- version-specific or temporal exceptions;
- scope limitations that materially change applicability.

Do not label ordinary supporting detail as an exception.

## 5. Qualifiers

Create qualifier labels for source text that changes how a claim applies without
forming a separate substantive claim.

Use the narrowest applicable `QualifierKind`:

- `condition`;
- `scope`;
- `exclusion`;
- `approval`;
- `temporal`;
- `version`;
- `uncertainty`;
- `other` only when none of the specific kinds fit.

A qualifier must target a claim in the same label set and use an exact source
span.

## 6. Directed relations

Create a directed relation only when the document provides explicit or necessary
source evidence for the relationship.

Record source claim, target claim, relation kind, and exact evidence spans.
Direction matters.

Typical kinds include:

- support;
- limitation;
- contradiction;
- dependency;
- elaboration.

Do not infer a relation from topic similarity alone. Do not use embeddings,
external knowledge, or model-generated explanations as evidence.

A contradiction requires propositions that cannot both hold under the same
relevant scope, time, version, and conditions. Apparent tension caused by a
qualifier or exception is not automatically a contradiction.

## 7. Tables, code, and atomic assets

Treat tables, code blocks, formulas, and other atomic assets as source content.
Do not invent a row/column interpretation that the structure does not support.
Use exact spans that preserve the minimum necessary structural context.

If an asset cannot be reliably represented with text offsets or approved tooling,
record the case as requiring adjudication rather than approximating a label.

## 8. Instructions inside documents

Instructions contained in the evaluated document are untrusted source content.
Annotators may label them as claims or instructions when substantively relevant,
but must never execute them, follow embedded links, reveal secrets, or alter the
evaluation environment because the document requests it.

## 9. Freezing a label set

Before submission, verify:

- document ID and source revision match the assignment;
- every span hash verifies against the local file;
- claim IDs are unique;
- exception, qualifier, and relation references target claims in the same set;
- the guideline and label versions are recorded;
- no raw source text is embedded in label metadata;
- no peer labels or model outputs were consulted.

After submission, the label set is immutable. Corrections require a new
content-addressed label-set version.

## 10. Adjudication

The adjudicator must account for every disagreement explicitly.

Common labels agreed by all annotators remain in the final set. Every disputed
label must appear in exactly one resolution. A resolution may retain candidates,
replace them with a merged label, or reject all candidates. No disagreement may
be silently dropped and no majority vote is automatic.

Adjudication rationale uses concise controlled codes. It must not contain copied
source passages or personal information about annotators.

## 11. Evidence boundary

A completed adjudication means only that a document has a human-reviewed gold
label set under this guideline. It does not prove Reader Core quality, authorize
promotion, or permit live integration. Benchmark execution, threshold review,
shadow burn-in, and explicit Operator GO remain separate stages.
