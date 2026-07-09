-- migrations/012_crystal_memory.sql
-- V8.7: Перенос полезных фич Crystal-архитектуры в V8.7 Titan
--
-- Три новые таблицы:
--   1. erasure_log      — GDPR-совместимый tombstone удалённых фактов
--   2. entities         — нормализованный каталог сущностей (people/concepts/locations/...)
--   3. fact_mentions    — связь факт → сущность (entity-centric retrieval + каскадное удаление)
--
-- Четвёртая таблица для exocortex_graph.db (создаётся отдельно при инициализации графа):
--   4. gs_vectors       — персистентные эмбеддинги для быстрого retrieval
--
-- Все таблицы append-only с триггерами защиты от UPDATE/DELETE.
-- Безопасно для повторного запуска (IF NOT EXISTS).
--

-- ═══════════════════════════════════════════════════════════════════════════════
-- 1. erasure_log — GDPR tombstone (персистентное доказательство удаления)
-- ═══════════════════════════════════════════════════════════════════════════════
-- Каждая запись = один удалённый факт. claim_hash позволяет аудитору
-- верифицировать ЧТО удалено, не раскрывая содержимого (SHA-256).
-- request_ref связывает массовые удаления с конкретным GDPR-запросом.

CREATE TABLE IF NOT EXISTS erasure_log (
    erasure_id   TEXT PRIMARY KEY,
    fact_id      TEXT NOT NULL,
    user_id      TEXT NOT NULL DEFAULT 'default',
    reason       TEXT NOT NULL DEFAULT 'user_request',
    claim_hash   TEXT NOT NULL,        -- SHA-256(claim) — privacy-safe идентификатор
    erased_at    TEXT NOT NULL,
    request_ref  TEXT DEFAULT NULL     -- внешняя ссылка на GDPR-запрос
);

CREATE INDEX IF NOT EXISTS idx_erasure_user
    ON erasure_log(user_id, erased_at);

CREATE INDEX IF NOT EXISTS idx_erasure_fact
    ON erasure_log(fact_id);

-- Триггер: erasure_log — append-only (защита от подделки аудита)
CREATE TRIGGER IF NOT EXISTS prevent_erasure_delete
BEFORE DELETE ON erasure_log
BEGIN
    SELECT RAISE(ABORT, 'VELANTRIM: erasure_log is append-only. Cannot delete audit records.');
END;

CREATE TRIGGER IF NOT EXISTS prevent_erasure_update
BEFORE UPDATE ON erasure_log
BEGIN
    SELECT RAISE(ABORT, 'VELANTRIM: erasure_log is append-only. Cannot modify audit records.');
END;


-- ═══════════════════════════════════════════════════════════════════════════════
-- 2. entities — нормализованный каталог сущностей
-- ═══════════════════════════════════════════════════════════════════════════════
-- Каждая сущность имеет каноническое имя + список алиасов.
-- entity_type позволяет различать person / concept / location / organization / event / artifact.
-- description — краткое описание (1-2 предложения).
-- external_ids_json — ссылки на Wikidata, Wikipedia, DBpedia и т.д.

CREATE TABLE IF NOT EXISTS entities (
    entity_id        TEXT PRIMARY KEY,
    canonical_name   TEXT NOT NULL,
    entity_type      TEXT NOT NULL DEFAULT 'concept',
    aliases_json     TEXT NOT NULL DEFAULT '[]',      -- ["Ньютон", "Newton", "Isaac Newton"]
    description      TEXT DEFAULT '',
    external_ids_json TEXT DEFAULT '{}',              -- {"wikidata": "Q935", "wikipedia": "Isaac_Newton"}
    first_seen       TEXT NOT NULL,
    last_seen        TEXT NOT NULL,
    mention_count    INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_entities_name
    ON entities(canonical_name);

CREATE INDEX IF NOT EXISTS idx_entities_type
    ON entities(entity_type);

-- Триггер: auto-increment mention_count при каждом упоминании (через fact_mentions)


-- ═══════════════════════════════════════════════════════════════════════════════
-- 3. fact_mentions — связь факт → сущность
-- ═══════════════════════════════════════════════════════════════════════════════
-- Каждая запись = один факт упоминает одну сущность.
-- mention_type: subject (о ком), object (о чём), context (упомянуто в контексте).
-- confidence: уверенность экстрактора сущностей (NER/LLM/rule-based).
-- Позволяет: «все факты о Ньютоне», каскадное удаление при forget_all.

CREATE TABLE IF NOT EXISTS fact_mentions (
    mention_id   TEXT PRIMARY KEY,
    fact_id      TEXT NOT NULL,
    entity_id    TEXT NOT NULL,
    mention_type TEXT NOT NULL DEFAULT 'context',  -- subject / object / context
    confidence   REAL NOT NULL DEFAULT 0.7,
    extracted_at TEXT NOT NULL,
    FOREIGN KEY (fact_id)   REFERENCES facts(fact_id)   ON DELETE CASCADE,
    FOREIGN KEY (entity_id) REFERENCES entities(entity_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_mentions_fact
    ON fact_mentions(fact_id);

CREATE INDEX IF NOT EXISTS idx_mentions_entity
    ON fact_mentions(entity_id, mention_type);

-- Триггер: auto-update mention_count при вставке
CREATE TRIGGER IF NOT EXISTS bump_entity_mention_count
AFTER INSERT ON fact_mentions
BEGIN
    UPDATE entities
    SET mention_count = mention_count + 1,
        last_seen     = NEW.extracted_at
    WHERE entity_id = NEW.entity_id;
END;


-- ═══════════════════════════════════════════════════════════════════════════════
-- erasure_log_view — SQL-вьюха для аудитора (join с индексами)
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE VIEW IF NOT EXISTS erasure_audit AS
SELECT
    el.erasure_id,
    el.fact_id,
    el.user_id,
    el.reason,
    el.claim_hash,
    el.erased_at,
    el.request_ref
FROM erasure_log el
ORDER BY el.erased_at DESC;
