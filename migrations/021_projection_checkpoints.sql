-- migrations/021_projection_checkpoints.sql
-- Version-monotonic same-DB projection checkpoint (issue #194, policy v1).
--
-- Records, per (aggregate_type, aggregate_id, scope_ref, projection_kind), the
-- highest canonical_version a local projection has actually been derived
-- from. Content-minimized: no claim, evidence, model output, arbitrary
-- payload JSON, user identity, tenant identity, stack trace or raw
-- exception text. Policy v1 closes every dimension except aggregate_id and
-- applied_canonical_version to exactly one value each.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS projection_checkpoints (
    aggregate_type             TEXT NOT NULL
        CHECK (aggregate_type = 'fact'),
    aggregate_id               TEXT NOT NULL,
    scope_ref                  TEXT NOT NULL
        CHECK (scope_ref = 'local:primary'),
    projection_kind            TEXT NOT NULL
        CHECK (projection_kind = 'fts'),
    applied_canonical_version  INTEGER NOT NULL
        CHECK (applied_canonical_version >= 1),
    updated_at                 TEXT NOT NULL,
    PRIMARY KEY (aggregate_type, aggregate_id, scope_ref, projection_kind)
);
