# Legacy version index

The public product is **Velantrim Titan 9.0**. Older version numbers (V8.6, V8.7, V8.8) are
preserved for history in two places:

1. **[CHANGELOG.md](../../CHANGELOG.md)** — the canonical version-by-version history.
2. **In-place legacy docs** — some documents are still version-specific by design (audits,
   migration plans). Rather than move them here and break the cross-references other docs
   make to them, they carry an explicit `⚠️ LEGACY` banner at the top:
   - [docs/AUDIT_V8_6.ru.md](../AUDIT_V8_6.ru.md) — full V8.6 audit
   - [docs/MIGRATION_V8.6_TO_CANON.ru.md](../MIGRATION_V8.6_TO_CANON.ru.md) — V8.6 → canon
     migration plan (still tracks open conformance work, so it stays live rather than archived)

This folder exists as the canonical pointer for "where did the old version docs go" — new
version-specific historical documents that are no longer referenced elsewhere should be moved
here going forward.
