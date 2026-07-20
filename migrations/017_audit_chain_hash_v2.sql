-- migrations/017_audit_chain_hash_v2.sql
-- AuditChain Hash v2 — versioned, canonical, concurrency-safe audit chain
-- =====================================================================
-- ЦЕЛЬ: добавить версионированный hash-chain поверх существующего
-- memory_events, не трогая ни одной существующей строки.
--
-- Существующие (v1) события остаются как есть — hash_version=1,
-- chain_id='memory_events' (backfilled by DEFAULT, metadata only — the
-- hashed fields themselves are never rewritten), chain_sequence=NULL
-- (v1 rows are never retroactively numbered).
--
-- Новые события по умолчанию получают hash_version=2, явный chain_id и
-- монотонно растущий chain_sequence, allocated atomically by
-- core.audit_chain.AuditChain.log() — this migration only adds the
-- schema; AuditChain owns sequence allocation at runtime.
--
-- Append-only triggers (prevent_audit_update / prevent_audit_delete) from
-- migration 009 are NEVER touched here.
-- =====================================================================

PRAGMA foreign_keys = ON;

-- ATOMIC: the whole migration (column adds, new table/index, head seed) is
-- wrapped in one explicit BEGIN/COMMIT — mirrors migration 016's documented
-- rationale for why sqlite3.Connection.executescript() alone does not give
-- a multi-statement script real transactional atomicity (each statement
-- outside an explicit transaction autocommits on its own). A failure at
-- any point rolls back the entire migration, including the column adds —
-- never a partially-applied intermediate state.

BEGIN;

-- SQLite ALTER TABLE ADD COLUMN is not idempotent — scripts/apply_migrations.py
-- strips these lines (mirroring the 010/011/013/014/016 pattern) when the
-- column already exists (e.g. added by a prior runtime self-heal via
-- AuditChain._ensure_schema()).

ALTER TABLE memory_events ADD COLUMN hash_version INTEGER NOT NULL DEFAULT 1;
ALTER TABLE memory_events ADD COLUMN chain_id TEXT NOT NULL DEFAULT 'memory_events';
ALTER TABLE memory_events ADD COLUMN chain_sequence INTEGER;

-- One sequence position per (chain_id, chain_sequence) — only enforced for
-- non-NULL sequences, so historical v1 rows (chain_sequence IS NULL) are
-- exempt.
CREATE UNIQUE INDEX IF NOT EXISTS idx_memory_events_chain_seq
ON memory_events(chain_id, chain_sequence) WHERE chain_sequence IS NOT NULL;

-- ══════════════════════════════════════════════════════════════════
-- audit_chain_heads — derived mutable coordination state (NOT the
-- immutable audit evidence itself) used to allocate the next
-- chain_sequence and the correct prev_event_hash atomically.
-- ══════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS audit_chain_heads (
    chain_id        TEXT PRIMARY KEY,
    last_sequence   INTEGER NOT NULL DEFAULT 0,
    last_event_hash TEXT,
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Seed the head for the default chain from the ACTUAL last durable event
-- (regardless of its hash_version), so the first v2 append correctly
-- chains onto the last v1 hash of a pre-existing chain. last_sequence
-- stays 0 until the first v2 event is appended — v1 rows are never
-- retroactively numbered.
INSERT OR IGNORE INTO audit_chain_heads (chain_id, last_sequence, last_event_hash)
SELECT
    'memory_events',
    0,
    (SELECT event_hash FROM memory_events ORDER BY rowid DESC LIMIT 1)
WHERE NOT EXISTS (
    SELECT 1 FROM audit_chain_heads WHERE chain_id = 'memory_events'
);

COMMIT;

-- ══════════════════════════════════════════════════════════════════
-- Проверка установки — запусти после применения миграции
-- ══════════════════════════════════════════════════════════════════
-- SELECT name FROM sqlite_master WHERE type IN ('table','index') AND
--   name IN ('audit_chain_heads', 'idx_memory_events_chain_seq');
-- PRAGMA table_info(memory_events);  -- ожидаем hash_version/chain_id/chain_sequence
