# Telegram delivery identity and durable receipts

Status: draft implementation, stacked on PR #523. No deployment activation.

Telegram must not report saved after a rejected canonical write. A retry of one
(chat_id, message_id) must not create a new fact or overwrite the first accepted payload.

Reuse the existing canonical store, mandatory admission, initial raw-binding transaction,
VersionStore/audit/outbox mechanisms. Add optional create_only to the structured write
API; the legacy bool/upsert APIs retain their defaults. A durable existing row returns
NOOP_EXISTING. A concurrent insert conflict has WHERE NOT :create_only and returns before
any audit/version/projection follow-up, so exactly one attempt creates the row. No
second writer or admission policy is introduced.

Telegram uses a stable delivery fact_id, content-addressed immutable L0 input, and the
structured cognitive/canonical write result. New raw provenance binds in the canonical
creation transaction. Receipt success additionally checks stored claim/source/raw ID.
A reused key with different content is a conflict, never an edit or fresh random ID.
Without a message_id, each call intentionally has a new delivery identity.

A rejected action never sends a saved reply. An idempotent retry does not send another
saved reply or another created/updated event. The legacy deduplicated_raw field is
nullable/unknown because L0 returns only an ID; clients should use deduplicated_delivery
for the proven delivery result. Rejected L1 input can remain in immutable L0; it is not
a newly accepted canonical fact. No deletion or retroactive repair is performed.

Tests cover both cognitive-store configurations, denial, repeat, message_id=0, concurrent
same/different payloads, no duplicate facts/raw/events, and existing raw-provenance
canonical convergence. Full-suite fixtures resolve live modules after import-isolation
reloads; enum identity is not compared across stale module generations.
