# ARM-03 audit checklist (pending)

1. Verify default-off short circuit before extraction.
2. Verify no forbidden imports or write-capable surface.
3. Verify exact offsets and SHA-256 span hashes.
4. Verify safe serialization excludes synthetic PII/credentials.
5. Verify injection-shaped text is rejected by default.
6. Verify subject/context change candidate identity.
7. Verify budgets and deterministic replay.
8. Run focused and full CI, benchmark and evaluation replay.

This temporary checklist will be consolidated before merge.
