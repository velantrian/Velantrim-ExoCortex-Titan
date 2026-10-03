# Pilot-0 reproducible harness — implementation-only package

**Status:** implemented in the review branch and unit-tested on synthetic fixtures only. No corpus run, Reader extraction, model inference, Q&A evaluation, benchmark, annotation, or operational authorization was performed. This is not wired into a runtime command, enabled, observed, or a production path.

**Base:** `ef134c324ef08c1a5f7f011433b8e2424e40ecea` (`main`, verified at task start).

## Implemented boundaries

- `core/pilot0/pdf_input.py` accepts a regular local `.pdf` file only and pins one installed parser: `pypdf==6.18.1`. It enforces file/page/extracted-character limits, records a SHA-256 source revision, and fails closed on missing/mismatched parser, encrypted/invalid input, or bounds. It has no fallback parser, package installer, download, URL input, or remote client.
- `core/pilot0/artifact.py` canonicalizes an already-produced `SemanticReader` result; it does **not** call `extract`. It requires an exact source revision and validates every claim against its source spans. The canonical JSON uses a fixed allowlist, deterministic UTF-8 encoding, a payload digest, and a digest over the exact serialized envelope bytes. Timestamps, arbitrary environment data, a separate raw-source field, full source maps, credentials, and unapproved receipt fields are excluded; Reader claims remain by design, while secret-shaped claim text is refused rather than persisted.
- The artifact records Reader identity/version, capsule and prompt versions, source identity/revision, parser identity/version, mode, budget, allowlisted Reader settings, claims and spans, coverage, synthesis/essence, warnings, and bounded reproducibility metadata. The current `SemanticReader`/`KnowledgeCapsule` contract has no section-card or relation output and no ReaderCore coverage axes; those collections/axes are represented as empty, not inferred.
- `core/pilot0/evaluator.py` accepts a verified frozen Reader JSON byte envelope plus a strict blind-question JSON or Markdown file containing exactly Q1–Q15. Its entry point also requires an injected local evaluator callable for tests/consumer composition; no evaluator/model client is included. The callable receives only the frozen Reader representation and one blind question, never source paths or source text. A blank/`None` response maps to `INSUFFICIENT_EVIDENCE`. File intake rejects non-JSON Reader inputs, PDF/raw-text paths, and filename patterns for manuscript, source map, sealed key, and prior answers; strict question schemas reject extra answer/source fields.
- The existing `LlmReaderAdapter` gained an optional `deepseek_thinking` setting with exact accepted values `off|high|max`; unsupported values fail closed. The existing DeepSeek request mapping remains the mapping used for payload construction: `high` produces `thinking.type=enabled` and `reasoning_effort=high`. Provider configuration is fixed to `deepseek`; model selection remains `OWNER_SELECTED`. No OpenRouter selection or model choice is made.

## Network, secret, and authority boundary

- Network policy for the parser, canonical serialization/freezing, evaluator implementation, and tests in this package is **DENY**. The focused tests use synthetic in-memory PDF/artifact data, a fake evaluator, a fake router transport, and network tripwires; no provider, HTTP, or DNS call is made. No remote egress policy was changed or enabled.
- This code does **not** claim that the existing remote policy is host-bounded or restricts egress exclusively to DeepSeek. A future DeepSeek call is a separate capability boundary and was not exercised.
- No API key was requested, received, read from the environment, stored, or used. No `.env` was created. `SECRET_INTAKE_SAFE=NO`. The existing adapter still has its pre-existing key parameter; this work adds no key-intake path. A future runtime needs a separately reviewed safe secret-injection path.
- No Canon, ESM, persistence, runtime route, or production authority is added. No Operator GO is implied.

## Frozen-input handling

The frozen corpus was not parsed, extracted, copied, sent to an evaluator, or used in tests. Only the PDF and blind-question bytes were hashed for integrity evidence; both matched their owner-supplied expected SHA-256 values at implementation time. The sealed key was deliberately not opened, read, hashed, or used. No source map, change log, blocker report, or prior answer was sent to an evaluator.

The actual Pilot-0 experiment was **not** run. Rights/publication limits remain unresolved.

## Verification

Focused command (offline):

```bash
PYTHONPATH=. python3 -m unittest discover -s tests -p 'test_pilot0_harness.py' -v
```

Result at implementation time: **15 tests passed**. `compileall` and `git diff --check` also passed. The local environment lacked `httpx`; tests used a transport stub rather than installing any package. The synthetic local PDF integration test ran against the exact installed `pypdf 6.18.1` parser. The real frozen Markdown question file was not opened or parsed, so its exact syntax compatibility remains unverified by design.

## Blockers before any real Pilot-0 run

1. **Parser dependency alignment:** the environment available for this task had `pypdf 6.18.1`, while the repository's existing optional `parsers` extra declares `pypdf>=6.19.0,<7`. The Pilot-0 code intentionally pins the already-installed local version and fails closed on mismatch. Do not change the shared dependency constraint implicitly; a separately authorized compatible runtime/dependency decision is needed before relying on the standard `parsers` extra.
2. **Safe secret injection:** `SECRET_INTAKE_SAFE=NO`; a future runtime must establish a safe injection and lifecycle before any real DeepSeek call.
3. **Model selection:** model remains `OWNER_SELECTED`; no model was selected or confirmed here.
4. **Egress/capability:** the future DeepSeek operation needs its own capability/egress review. This package neither changes nor claims a provider-exclusive or host-bounded egress policy.
5. **Rights and publication limits:** remain unresolved and must be resolved by the owner before using the frozen manuscript.
6. **Separate authorization:** no Operator GO, benchmark authorization, human annotation/transfer, production enablement, or release is included in this branch.
7. **Injected evaluator limitation:** the interface itself contains no network implementation, but an arbitrary caller-supplied Python callable is not a sandbox. Any future evaluator execution needs an explicit offline/capability-controlled caller; tests inject only a local fake.
8. **Frozen question syntax:** only the filename/extension and SHA-256 of the frozen Markdown questions were checked. The parser supports a strict synthetic Q1–Q15 marker format; confirm compatibility in a separately authorized step without exposing prior answers or sending any other corpus artifact to the evaluator.
