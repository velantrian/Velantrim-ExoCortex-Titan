-- migrations/011_claim_type_modality.sql
-- v8.7 P0: Модальность памяти — claim_type + origin_type
--
-- Цель: разделить «что это за утверждение по природе» (claim_type)
--       от «откуда пришло» (origin_type) и от «насколько верифицировано» (epistemic_state).
--
-- Ключевое правило:
--   EMOTION/OPINION/INTERPRETATION/USER_EXPERIENCE — валидны КАК ЕСТЬ.
--   Только WORLD_FACT требует внешних доказательств/источника для продвижения.
--
-- БЕЗОПАСНО для повторного запуска: SQLite игнорирует ADD COLUMN если колонка уже есть
-- через обёртку IF NOT EXISTS (эмуляция — см. скрипт apply_migration.py).
-- При прямом выполнении на новой БД: факты таблица уже имеет колонки (DDL в memory.py).
-- При выполнении на существующей БД: ALTER TABLE добавляет колонки с DEFAULT 'UNKNOWN'.
--
-- Миграция существующих строк:
--   claim_type  = 'UNKNOWN'  (будет уточнён классификатором при следующей записи)
--   origin_type = 'UNKNOWN'  (будет уточнён по source при следующей записи)
--
-- ВАЖНО: НЕ удалять и НЕ изменять epistemic_state — это отдельная ось проверки.

PRAGMA foreign_keys = ON;

-- Добавить claim_type (модальность) — безопасный DEFAULT
ALTER TABLE facts ADD COLUMN claim_type TEXT NOT NULL DEFAULT 'UNKNOWN';

-- Добавить origin_type (происхождение) — безопасный DEFAULT
ALTER TABLE facts ADD COLUMN origin_type TEXT NOT NULL DEFAULT 'UNKNOWN';

-- Индекс для быстрой фильтрации по типу при retrieval
CREATE INDEX IF NOT EXISTS idx_facts_claim_type
    ON facts (claim_type);

CREATE INDEX IF NOT EXISTS idx_facts_origin_type
    ON facts (origin_type);

-- Составной индекс: retrieval "дай мне факты о мире с высокой уверенностью"
CREATE INDEX IF NOT EXISTS idx_facts_world_fact_conf
    ON facts (claim_type, confidence)
    WHERE claim_type = 'WORLD_FACT';
