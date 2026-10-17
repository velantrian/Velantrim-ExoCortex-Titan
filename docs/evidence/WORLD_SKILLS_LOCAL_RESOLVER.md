# Local World Skills manifest resolver

The accompanying `core/world_skills_review_manifest.py` is an unwired local adapter over the existing typed EvidenceReference/registry contract. Its input is one fixed checked-in manifest and a bounded allowlist of repository source paths. HTTP routes, fact metadata, ingestion, TruthGate and promotion do not call it.

It distinguishes reference integrity, recorded source-review provenance, and claim-support review. A digest match is a location/integrity result, not evidence that the source is true or that a claim is supported. Reviewer IDs and approval references are attestations only; accepted review records remain `attested_unverified`, never authenticated owner identity or a signature. The checked-in candidate is not silently admitted as an active source.

Validation covers exact field sets, duplicate JSON keys, fixed path and symlink checks, strict UTF-8/NFC/newline policy, full-source and exact-fragment digests, source revocation, claim/reference/version binding, and spoofed fact-metadata rejection. Revocation is a metadata tombstone, not a claim of physical erasure.

The resolver has no canonical write side effects and does not grant admission, epistemic promotion, action or runtime authority. Runtime wiring and an authenticated owner-review/admission protocol remain separate decisions. Tests: `tests/test_world_skills_review_manifest.py` and the metadata-evidence regression in `tests/test_memory_ops.py`.
