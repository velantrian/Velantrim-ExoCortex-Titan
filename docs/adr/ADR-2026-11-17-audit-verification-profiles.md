# Expand audit verification to HTTP and fallback profiles

Status: proposed draft implementation, stacked on PR #523.

The main CI checks core only and two acceptance workflows resolve dependencies with pip
outside uv.lock. A critical TruthGate projection test can download an optional model,
while dependency license evidence is absent from the installed environment record.

Use the frozen installer for Stage 9/10. Lock Playwright in the browser-tests extra;
browser installation remains the version-selected Chromium bundle. Upgrade Ruff to
0.17.5 and block its existing rule set across core, server, API, app, scripts and utils.
Optional spelling remains accepted (UP045), preserving the existing UP007 style policy.
Do not mass-reformat runtime code or weaken semantic F rules.

Run the existing Python CodeQL workflow for stacked PR targets as well as main;
its permissions, language, query suite and immutable action pins remain unchanged.

Keep core mypy and add a Pydantic-aware HTTP profile, so default model fields are
understood without suppressing real argument/None errors. Reconcile async callback
annotations and omitted TTS arguments where this exposes existing contract drift.

Add a frozen server/dev/parser CI job without BM25 or sentence-transformers. The
existing full embedding-enabled job remains. Numpy belongs to dev because projection
contract tests import it without requiring model packages. The TruthGate test supplies
one deterministic retrieval candidate instead of loading a model; empty retrieval is
covered by the existing pipeline insufficiency tests.

Record actual installed license metadata as a CI artifact. Missing data stays explicit;
this does not certify legal compatibility, enable optional licensed parsers or change
Titan's own MIT license. See the operations license-inventory document.

No Canon writer, promotion owner, feature activation or production authority is added.
Exact-head CI is required for each parent/child; local fallback tests do not stand in
for the embedding-enabled job or real Chromium acceptance.
