-- migrations/008_add_relations.sql
-- Patch 13: Causal Graph + Patch 14: Living Context
-- Применяется к существующей Velantrim БД (v8.4.4+)
-- Все операции безопасны для повторного запуска (IF NOT EXISTS)

PRAGMA foreign_keys = ON;

-- ══════════════════════════════════════════════════════════════════════════
-- PATCH 13: Causal Graph
-- Типизированные отношения между фактами (12 типов)
-- ══════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS relations (
    relation_id       TEXT PRIMARY KEY,
    from_fact_id      TEXT NOT NULL REFERENCES facts(fact_id) ON DELETE CASCADE,
    to_fact_id        TEXT NOT NULL REFERENCES facts(fact_id) ON DELETE CASCADE,
    relation_type     TEXT NOT NULL,

    -- Вероятность [0.0, 1.0] — "я видел это 7 из 10 раз"
    confidence        REAL NOT NULL DEFAULT 0.8,

    -- Откуда это знание — ОТДЕЛЬНО от confidence (разные вещи!)
    knowledge_status  TEXT NOT NULL DEFAULT 'known'
        CHECK (knowledge_status IN ('known', 'inferred', 'hypothetical', 'unknown')),

    -- Кем/чем выведено (если inferred)
    inference_source  TEXT DEFAULT NULL
        CHECK (inference_source IN (
            'manual', 'autolinker', 'counterfactual_engine',
            'llm_extraction', 'atlas_sync', 'affordance_inference', NULL
        )),

    -- Совместимость с Variant B: review_state для TruthGate
    truth_status      TEXT DEFAULT 'validated'
        CHECK (truth_status IN ('validated', 'hypothesis', 'pending')),
    review_state      TEXT DEFAULT 'approved'
        CHECK (review_state IN ('approved', 'pending', 'rejected')),

    -- Bi-temporal (совместимость с Velantrim bi-temporal model)
    evidence_ref      TEXT,         -- JSON: источник связи
    created_at        TEXT NOT NULL DEFAULT (datetime('now')),
    valid_from        TEXT NOT NULL DEFAULT (datetime('now')),
    valid_to          TEXT,         -- NULL = бессрочно

    metadata          TEXT,         -- JSON: дополнительный контекст

    -- Петли запрещены
    CHECK (from_fact_id != to_fact_id),

    -- Разные источники могут сосуществовать для одной пары (FIX ChatGPT)
    UNIQUE (from_fact_id, to_fact_id, relation_type, inference_source)
);

-- Индексы для быстрого графового обхода
CREATE INDEX IF NOT EXISTS idx_relations_from
    ON relations(from_fact_id, relation_type);
CREATE INDEX IF NOT EXISTS idx_relations_to
    ON relations(to_fact_id, relation_type);
CREATE INDEX IF NOT EXISTS idx_relations_type
    ON relations(relation_type);
CREATE INDEX IF NOT EXISTS idx_relations_status
    ON relations(knowledge_status);
CREATE INDEX IF NOT EXISTS idx_relations_from_type_status
    ON relations(from_fact_id, relation_type, truth_status);
CREATE INDEX IF NOT EXISTS idx_relations_to_type_status
    ON relations(to_fact_id, relation_type, truth_status);

-- Materialized paths (опционально — для производительности при глубоком обходе)
CREATE TABLE IF NOT EXISTS relation_paths (
    from_fact_id      TEXT NOT NULL,
    to_fact_id        TEXT NOT NULL,
    path_length       INTEGER NOT NULL,
    path_json         TEXT NOT NULL,   -- JSON: список relation_ids
    total_confidence  REAL NOT NULL,
    min_confidence    REAL NOT NULL,   -- слабое звено цепи
    has_hypothetical  INTEGER NOT NULL DEFAULT 0,  -- есть ли непроверенные рёбра
    computed_at       TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (from_fact_id, to_fact_id, path_length)
);

-- ══════════════════════════════════════════════════════════════════════════
-- PATCH 14: Living Context
-- "Что с этим можно делать?" — практические связи
-- ══════════════════════════════════════════════════════════════════════════

-- Основная таблица контекста (вынесена отдельно — не раздувает facts)
CREATE TABLE IF NOT EXISTS fact_living_context (
    fact_id    TEXT PRIMARY KEY REFERENCES facts(fact_id) ON DELETE CASCADE,
    ctx_where  TEXT NOT NULL DEFAULT '[]',   -- JSON список мест
    ctx_who    TEXT NOT NULL DEFAULT '[]',   -- JSON список агентов
    ctx_how    TEXT NOT NULL DEFAULT '[]',   -- JSON список действий (affordances)
    ctx_what   TEXT NOT NULL DEFAULT '[]',   -- JSON список продуктов
    ctx_feel   TEXT NOT NULL DEFAULT '{}',   -- JSON dict {качество: float}
    ctx_role   TEXT NOT NULL DEFAULT '[]',   -- JSON список ролей
    ctx_time   TEXT DEFAULT NULL,            -- JSON временной контекст
    ctx_deep   TEXT DEFAULT NULL,            -- JSON глубокое/научное знание
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Canonical affordances — нормализованный словарь действий
CREATE TABLE IF NOT EXISTS canonical_affordances (
    affordance_id  TEXT PRIMARY KEY,
    canonical_form TEXT NOT NULL UNIQUE,
    synonyms       TEXT NOT NULL DEFAULT '[]',   -- JSON список синонимов
    domain         TEXT,                          -- "ecology"|"cooking"|"engineering"|...
    created_at     TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Связь факт ↔ canonical affordance
CREATE TABLE IF NOT EXISTS fact_affordances (
    fact_id       TEXT NOT NULL REFERENCES facts(fact_id) ON DELETE CASCADE,
    affordance_id TEXT NOT NULL REFERENCES canonical_affordances(affordance_id),
    confidence    REAL NOT NULL DEFAULT 0.8,
    source        TEXT NOT NULL DEFAULT 'autolinker'
        CHECK (source IN ('manual', 'autolinker', 'causal_inference', 'llm')),
    PRIMARY KEY (fact_id, affordance_id)
);

-- Индексы для поиска по affordances
CREATE INDEX IF NOT EXISTS idx_fact_afford
    ON fact_affordances(affordance_id, source);
CREATE INDEX IF NOT EXISTS idx_living_ctx
    ON fact_living_context(fact_id);

-- ══════════════════════════════════════════════════════════════════════════
-- VARIANT C MVP: быстрые поля прямо на facts (для benchmark)
-- ══════════════════════════════════════════════════════════════════════════
-- Эти поля дополняют fact_living_context для простых случаев без JOIN
-- FIX (Perplexity): отдельная таблица токенов вместо LIKE по JSON

CREATE TABLE IF NOT EXISTS fact_affordance_tokens (
    fact_id TEXT NOT NULL REFERENCES facts(fact_id) ON DELETE CASCADE,
    token   TEXT NOT NULL,
    field   TEXT NOT NULL CHECK(field IN ('affordance', 'product', 'agent')),
    PRIMARY KEY (fact_id, token, field)
);

CREATE INDEX IF NOT EXISTS idx_fat_token
    ON fact_affordance_tokens(token, field);

-- ══════════════════════════════════════════════════════════════════════════
-- Проверка (запустить после применения миграции):
-- SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;
-- Ожидаемые новые таблицы:
--   canonical_affordances, fact_affordance_tokens, fact_affordances,
--   fact_living_context, relation_paths, relations
-- ══════════════════════════════════════════════════════════════════════════
