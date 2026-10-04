# Pilot-0 reproducible harness — implementation-only package

**Status:** implemented in the review branch and unit-tested on synthetic fixtures only. No corpus run, Reader extraction, model inference, Q&A evaluation, benchmark, annotation, or operational authorization was performed. This is not wired into a runtime command, enabled, observed, or a production path.

**Base:** `ef134c324ef08c1a5f7f011433b8e2424e40ecea` (`main`, verified at task start).

## Implemented boundaries

- `core/pilot0/pdf_input.py` accepts a regular local `.pdf` file only and pins the repository baseline parser: `pypdf==6.19.0` (`pypdf>=6.19.0,<7` in the existing optional dependency; lock `6.19.0`). It enforces file/page/extracted-character limits, records a SHA-256 source revision, and fails closed on missing/mismatched parser, encrypted/invalid input, or bounds. The local pinned parser path contains no fallback, cascade, installer, download, URL input, or remote client.
- `core/pilot0/artifact.py` canonicalizes an already-produced `SemanticReader` result; it does **not** call `extract`. It requires an exact source revision and validates every claim against its source spans. The canonical JSON uses a fixed allowlist, deterministic UTF-8 encoding, a payload digest, and a digest over the exact serialized envelope bytes. Timestamps, arbitrary environment data, a separate raw-source field, full source maps, credentials, and unapproved receipt fields are excluded; Reader claims remain by design, while secret-shaped claim text is refused rather than persisted.
- The artifact records Reader identity/version, capsule and prompt versions, source identity/revision, parser identity/version, mode, budget, allowlisted Reader settings, claims and spans, coverage, synthesis/essence, warnings, and bounded reproducibility metadata. The current `SemanticReader`/`KnowledgeCapsule` contract has no section-card or relation output and no ReaderCore coverage axes; those collections/axes are represented as empty, not inferred.
- `core/pilot0/evaluator.py` accepts already-loaded Reader JSON and blind-question bytes; it does not open filesystem paths or treat filename patterns as a security boundary. It requires the trusted `expected_reader_artifact_sha256` and compares the exact serialized Reader bytes before parsing either input. Markdown supports both `Q1.` markers and the frozen source syntax `**1.**` through `**15.**`; strict question schemas reject extra answer/source fields. An in-process Python callback is not a sandbox: the callback is never invoked, and evaluator execution fails closed until a separately verified restricted runtime is integrated.
- The existing `LlmReaderAdapter` constructor contract is unchanged. At the low-level DeepSeek request boundary, `deepseek_thinking` accepts only exact values `off|high|max`; unsupported values fail closed. The existing payload mapping is preserved: `high` produces `thinking.type=enabled` and `reasoning_effort=high`. Pilot-0 provider configuration remains fixed to `deepseek`; model selection remains `OWNER_SELECTED`. No OpenRouter selection or model choice is made.

## Network, secret, and authority boundary

- The local pinned parser path contains no fallback/download/URL path; process-wide network denial is a separate runtime capability and is not established by this package. The parser and canonicalizer do not make provider/API calls. Tests use synthetic in-memory PDF/artifact data and fake router transport; the evaluator callback is not invoked. No remote egress policy was changed or enabled.
- This code does **not** claim that the existing remote policy is host-bounded or restricts egress exclusively to DeepSeek. A future DeepSeek call is a separate capability boundary and was not exercised.
- No API-key value was written to the repository or artifacts; this package did not read/use a runtime credential and made no provider/API call; no `.env` was created; `SECRET_INTAKE_SAFE=NO`. The existing adapter still has its pre-existing key parameter; this work adds no key-intake path. A future runtime needs a separately reviewed safe secret-injection path.
- No Canon, ESM, persistence, runtime route, or production authority is added. No Operator GO is implied.

## Frozen-input handling

The PDF was checked by streaming SHA-256 only; it was not opened as a document, parsed, or extracted. After its expected SHA matched, the frozen Markdown question file was inspected only for its numbered-marker syntax (`**1.**` through `**15.**`); question text was not answered, tested, or sent to any model/evaluator. Both expected SHA-256 values matched. The sealed key was deliberately not opened, read, hashed, or used. No source map, change log, blocker report, or prior answer was sent to an evaluator.

The actual Pilot-0 experiment was **not** run. Rights/publication limits remain unresolved.

## Verification

Focused synthetic command (offline, using an already available exact-version environment; no packages installed):

```bash
PYTHONPATH=. python3 -m unittest discover -s tests -p 'test_pilot0_harness.py' -v
```

The focused synthetic suite asserts the installed parser version exactly; version mismatch is a test failure, not a skip. Its synthetic PDF test runs only with `pypdf==6.19.0`. The real frozen Markdown file is never passed to the evaluator or parser; only its marker syntax is inspected after its hash matches.

## Blockers before any real Pilot-0 run

1. **Process/network boundary:** absence of a parser fallback/download/URL path is a code-path property only. It does not provide process-wide network denial or a restricted evaluator runtime.
2. **Safe secret injection:** `SECRET_INTAKE_SAFE=NO`; a future runtime must establish a safe injection and lifecycle before any real DeepSeek call.
3. **Model selection:** model remains `OWNER_SELECTED`; no model was selected or confirmed here.
4. **Egress/capability:** the future DeepSeek operation needs its own capability/egress review. This package neither changes nor claims a provider-exclusive or host-bounded egress policy.
5. **Rights and publication limits:** remain unresolved and must be resolved by the owner before using the frozen manuscript.
6. **Separate authorization:** no Operator GO, benchmark authorization, human annotation/transfer, production enablement, or release is included in this branch.
7. **Restricted evaluator runtime:** any in-process Python callback can access process capabilities and is not sandboxed. Execution is blocked until a separately verified restricted runtime is provided.
8. **Frozen question syntax:** the marker syntax was checked after the expected hash matched; the question text was not passed to parser/evaluator/model code and no answers were produced.
