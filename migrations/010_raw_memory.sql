-- migrations/010_raw_memory.sql
-- L0 Immutable Raw Memory — защита от Semantic Drift
-- ====================================================
-- ПРОБЛЕМА (Gemini): при суммаризации L1→L2→L3 факты медленно
-- меняют смысл. Оригинальный текст теряется. Через N итераций
-- "волки иногда избегают людей" становится "волки боятся людей".
--
-- РЕШЕНИЕ: хранить оригинальный текст в отдельной таблице.
-- Он НИКОГДА не изменяется. Любой derived факт ссылается на него.
--
-- Контракт:
--   - l0_raw_memory: только INSERT, никогда UPDATE или DELETE
--   - facts.derived_from → l0_raw_memory.raw_id (FK)
--   - Суммаризации — производные, НЕ истина последней инстанции

PRAGMA foreign_keys = ON;

-- ── Основная таблица L0 ───────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS l0_raw_memory (
    raw_id          TEXT PRIMARY KEY,
    original_text   TEXT NOT NULL,            -- оригинальный текст, никогда не меняется
    content_hash    TEXT NOT NULL UNIQUE,     -- SHA256(original_text) — для дедупликации
    source          TEXT,                     -- откуда пришёл текст
    source_url      TEXT,                     -- URL если известен
    source_type     TEXT DEFAULT 'unknown',   -- 'file', 'api', 'user_input', 'web', ...
    language        TEXT DEFAULT 'unknown',   -- язык текста
    char_count      INTEGER NOT NULL DEFAULT 0,
    word_count      INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    -- Metadata: JSON с дополнительными полями (страница PDF, временная метка аудио, ...)
    metadata        TEXT DEFAULT '{}'
);

-- Индексы для поиска
CREATE INDEX IF NOT EXISTS idx_raw_hash    ON l0_raw_memory(content_hash);
CREATE INDEX IF NOT EXISTS idx_raw_source  ON l0_raw_memory(source, created_at);
CREATE INDEX IF NOT EXISTS idx_raw_created ON l0_raw_memory(created_at);

-- 🛡️ TRIGGER: Raw memory — только append, никогда UPDATE
CREATE TRIGGER IF NOT EXISTS prevent_raw_update
BEFORE UPDATE ON l0_raw_memory
BEGIN
    SELECT RAISE(ABORT, 'VELANTRIM L0: l0_raw_memory is immutable — UPDATE is forbidden. Create a new raw entry instead.');
END;

-- 🛡️ TRIGGER: Raw memory — нельзя DELETE
CREATE TRIGGER IF NOT EXISTS prevent_raw_delete
BEFORE DELETE ON l0_raw_memory
BEGIN
    SELECT RAISE(ABORT, 'VELANTRIM L0: l0_raw_memory is immutable — DELETE is forbidden. Deprecate associated facts instead.');
END;

-- ── Связь facts → l0_raw_memory ───────────────────────────────────────────────

-- Добавляем derived_from в facts
-- (безопасно если уже существует — SQLite не поддерживает IF NOT EXISTS для ALTER)
-- Если колонка уже есть, команда упадёт — это нормально, ignore этот шаг.
ALTER TABLE facts ADD COLUMN derived_from TEXT REFERENCES l0_raw_memory(raw_id);

-- Индекс для быстрого поиска "все факты из этого raw"
CREATE INDEX IF NOT EXISTS idx_facts_derived ON facts(derived_from);

-- ── Таблица цепочки суммаризации ──────────────────────────────────────────────
-- Позволяет восстановить путь: raw → chunk → summary → fact

CREATE TABLE IF NOT EXISTS raw_derivation_chain (
    step_id         TEXT PRIMARY KEY,
    raw_id          TEXT NOT NULL REFERENCES l0_raw_memory(raw_id),
    derived_fact_id TEXT NOT NULL REFERENCES facts(fact_id),
    derivation_type TEXT NOT NULL DEFAULT 'direct',
    -- 'direct'      — факт прямо из raw текста
    -- 'chunked'     — факт из куска raw текста
    -- 'summarized'  — факт через суммаризацию (ОСТОРОЖНО: drift risk)
    -- 'inferred'    — факт выведен из raw через reasoning
    step_index      INTEGER NOT NULL DEFAULT 0,  -- 0 = прямо из raw, 1+ = через N шагов
    transformation  TEXT,                         -- описание что было сделано
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_chain_raw  ON raw_derivation_chain(raw_id);
CREATE INDEX IF NOT EXISTS idx_chain_fact ON raw_derivation_chain(derived_fact_id);

-- ── Проверка после применения ─────────────────────────────────────────────────
-- SELECT name FROM sqlite_master WHERE type IN ('table','trigger')
--   AND name LIKE '%raw%' ORDER BY name;
--
-- Ожидаемые объекты:
--   TABLE:   l0_raw_memory, raw_derivation_chain
--   TRIGGER: prevent_raw_delete, prevent_raw_update
--   COLUMN:  facts.derived_from
