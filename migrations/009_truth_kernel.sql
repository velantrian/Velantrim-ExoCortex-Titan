-- migrations/009_truth_kernel.sql
-- Truth Kernel Hardening — Sprint 1a
-- =====================================================
-- ЦЕЛЬ: сделать так чтобы память нельзя было тихо повредить
--
-- Содержит:
--   A2: DB-level ESM триггеры
--   A3: Append-only audit log с hash-chain
--   A4: fact_version + content_hash для cache coherence
-- =====================================================

PRAGMA foreign_keys = ON;

-- ══════════════════════════════════════════════════════════════════
-- A4: Добавляем fact_version и content_hash в facts таблицу
-- ══════════════════════════════════════════════════════════════════

-- Безопасно добавляем колонки (IF NOT EXISTS через SELECT trick)
-- SQLite не поддерживает ADD COLUMN IF NOT EXISTS напрямую

-- fact_version: монотонно растёт при каждом изменении
ALTER TABLE facts ADD COLUMN fact_version INTEGER NOT NULL DEFAULT 1;

-- content_hash: SHA256 от (claim + confidence + epistemic_state)
-- Заполняем при следующем UPDATE или через rebuild_hashes.py
ALTER TABLE facts ADD COLUMN content_hash TEXT DEFAULT NULL;

-- ══════════════════════════════════════════════════════════════════
-- A3: Append-only audit log с hash-chain
-- ══════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS memory_events (
    event_id        TEXT PRIMARY KEY,
    event_type      TEXT NOT NULL,
    -- Типы событий:
    -- 'fact_created', 'fact_updated', 'esm_transition',
    -- 'fact_deprecated', 'fact_collapsed', 'truth_gate_verdict',
    -- 'immutable_attempt_blocked', 'audit_verify'

    fact_id         TEXT,                     -- какой факт
    from_state      TEXT,                     -- ESM откуда
    to_state        TEXT,                     -- ESM куда
    actor           TEXT NOT NULL,            -- кто сделал
    reason          TEXT,                     -- почему
    payload         TEXT,                     -- JSON доп данные
    confidence      REAL,                     -- confidence в момент события

    -- Hash-chain поля
    event_hash      TEXT NOT NULL UNIQUE,     -- SHA256(prev + payload)
    prev_event_hash TEXT,                     -- хэш предыдущего события (NULL для первого)

    created_at      TEXT NOT NULL DEFAULT (datetime('now')),

    -- Только вставка — никогда UPDATE или DELETE
    -- Обеспечивается через триггер
    FOREIGN KEY (fact_id) REFERENCES facts(fact_id)
);

-- ⚠️ CRITICAL: запрет UPDATE и DELETE в audit log
CREATE TRIGGER prevent_audit_update
BEFORE UPDATE ON memory_events
BEGIN
    SELECT RAISE(ABORT, 'VELANTRIM: audit log is append-only — UPDATE is forbidden');
END;

CREATE TRIGGER prevent_audit_delete
BEFORE DELETE ON memory_events
BEGIN
    SELECT RAISE(ABORT, 'VELANTRIM: audit log is append-only — DELETE is forbidden');
END;

-- Индекс для быстрой цепочки
CREATE INDEX IF NOT EXISTS idx_events_fact_id  ON memory_events(fact_id, created_at);
CREATE INDEX IF NOT EXISTS idx_events_prev     ON memory_events(prev_event_hash);
CREATE INDEX IF NOT EXISTS idx_events_type     ON memory_events(event_type, created_at);

-- ══════════════════════════════════════════════════════════════════
-- A2: ESM триггеры — DB-level enforcement
-- ══════════════════════════════════════════════════════════════════

-- Таблица разрешённых переходов ESM (формализует машину состояний)
CREATE TABLE IF NOT EXISTS esm_allowed_transitions (
    from_state  TEXT NOT NULL,
    to_state    TEXT NOT NULL,
    PRIMARY KEY (from_state, to_state)
);

INSERT OR IGNORE INTO esm_allowed_transitions VALUES
    -- Наблюдение → Гипотеза
    ('Observed',      'Hypothesized'),
    -- Гипотеза → Supported/Contradicted
    ('Hypothesized',  'Supported'),
    ('Hypothesized',  'Contradicted'),
    ('Hypothesized',  'Deprecated'),
    -- Supported → Validated/Contradicted
    ('Supported',     'Validated'),
    ('Supported',     'Contradicted'),
    ('Supported',     'Hypothesized'),  -- downgrade если новые данные
    -- Validated → выше или ниже
    ('Validated',     'ImmutableCore'),
    ('Validated',     'Contradicted'),
    ('Validated',     'Deprecated'),
    -- Contradicted → пересмотр или архив
    ('Contradicted',  'Hypothesized'),  -- пересмотр
    ('Contradicted',  'Collapsed'),
    ('Contradicted',  'Deprecated'),
    -- Deprecated → архив
    ('Deprecated',    'Collapsed'),
    -- ImmutableCore: никуда не переходит
    -- Collapsed: финальное состояние — никуда
    -- Observed: может вернуться в себя при обновлении
    ('Observed',      'Observed');
    -- (Observed может сразу стать Hypothesized)

-- 🛡️ TRIGGER 1: Запрет незаконных ESM переходов
CREATE TRIGGER prevent_invalid_esm_transition
BEFORE UPDATE OF epistemic_state ON facts
WHEN OLD.epistemic_state != NEW.epistemic_state
BEGIN
    SELECT CASE
        WHEN (
            SELECT COUNT(*) FROM esm_allowed_transitions
            WHERE from_state = OLD.epistemic_state
              AND to_state   = NEW.epistemic_state
        ) = 0
        THEN RAISE(ABORT, 'VELANTRIM ESM VIOLATION: transition not allowed. Use transition_esm() with proper audit trail.')
    END;
END;

-- 🛡️ TRIGGER 2: ImmutableCore абсолютная защита
CREATE TRIGGER prevent_immutablecore_mutation
BEFORE UPDATE ON facts
WHEN OLD.epistemic_state = 'ImmutableCore'
BEGIN
    SELECT RAISE(ABORT, 'VELANTRIM: ImmutableCore facts are read-only. Requires 2+ approvers and special protocol.');
END;

-- 🛡️ TRIGGER 3: Collapsed факты не изменяются
CREATE TRIGGER prevent_collapsed_mutation
BEFORE UPDATE ON facts
WHEN OLD.epistemic_state = 'Collapsed'
BEGIN
    SELECT RAISE(ABORT, 'VELANTRIM: Collapsed facts cannot be modified. They are archived — create a new fact instead.');
END;

-- 🛡️ TRIGGER 4: Обновление fact_version при изменении
CREATE TRIGGER bump_fact_version
BEFORE UPDATE ON facts
WHEN OLD.claim != NEW.claim
  OR OLD.confidence != NEW.confidence
  OR OLD.epistemic_state != NEW.epistemic_state
BEGIN
    -- SQLite не поддерживает SET в BEFORE trigger,
    -- но можно проверить что version будет увеличена
    SELECT CASE
        WHEN NEW.fact_version <= OLD.fact_version
        THEN RAISE(ABORT, 'VELANTRIM: fact_version must increase on update. Set fact_version = fact_version + 1.')
    END;
END;

-- 🛡️ TRIGGER 5: Запрет прямого DELETE факта (должен через Collapsed)
CREATE TRIGGER prevent_fact_delete
BEFORE DELETE ON facts
BEGIN
    SELECT CASE
        WHEN OLD.epistemic_state NOT IN ('Collapsed', 'Deprecated')
        THEN RAISE(ABORT, 'VELANTRIM: Cannot DELETE facts directly. Transition to Collapsed or Deprecated first.')
    END;
END;

-- ══════════════════════════════════════════════════════════════════
-- Таблица integrity_checks — результаты проверок целостности
-- ══════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS integrity_checks (
    check_id     TEXT PRIMARY KEY,
    check_type   TEXT NOT NULL,    -- 'audit_chain', 'esm_validity', 'cache_coherence'
    status       TEXT NOT NULL,    -- 'passed', 'failed', 'warning'
    details      TEXT,             -- JSON с деталями
    checked_at   TEXT NOT NULL DEFAULT (datetime('now')),
    checked_by   TEXT NOT NULL DEFAULT 'system'
);

-- ══════════════════════════════════════════════════════════════════
-- Проверка установки — запусти после применения миграции
-- ══════════════════════════════════════════════════════════════════
-- SELECT name FROM sqlite_master WHERE type IN ('table','trigger') ORDER BY name;
--
-- Ожидаемые новые объекты:
--   TABLE: esm_allowed_transitions, integrity_checks, memory_events
--   TRIGGER: prevent_audit_delete, prevent_audit_update,
--             prevent_collapsed_mutation, prevent_fact_delete,
--             prevent_immutablecore_mutation, prevent_invalid_esm_transition,
--             bump_fact_version
