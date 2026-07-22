"""
tests/test_version_store_temporal_consistency.py — PR-C1d (Issue #39)
==============================================================================

Issue #39 has two confirmed parts:

A/B/C. VersionStore.snapshot_before_change() sourced `recorded_at` from
   `t_ingestion_start`, which is frozen at a fact's ORIGINAL creation and
   never advances. Every historical snapshot of the same fact_id therefore
   got an IDENTICAL `recorded_at`, while `superseded_at` correctly advanced
   per call. get_fact_as_of()/get_graph_as_of() select by
   `recorded_at <= t AND (superseded_at IS NULL OR superseded_at > t)` —
   with a frozen recorded_at, a query time before a LATER supersession event
   still matched that later version's row, so `ORDER BY version_num DESC`
   returned a version that did not exist yet at the real query time `t`.
   There was also no way to resolve a query made strictly after the last
   snapshot: the live `facts` row was never considered, so
   get_fact_as_of(t_after_last) incorrectly returned None instead of the
   current state.

D. transition_esm() and invalidate_edge() called
   VersionStore.snapshot_before_change() BEFORE the canonical write
   (update_state() / the facts UPDATE), not after. A CAS miss, a missing
   fact_id, or a forced SQL failure still left behind a "superseded"
   fact_versions row for a transition that never actually committed to the
   canonical `facts` row — a phantom audit entry. (invalidate_edge() also
   had no CAS guard and no rowcount check at all — it always returned True,
   even for a nonexistent fact_id or a concurrently-modified row.)

Fix (this PR):
- VersionStore.snapshot_before_change(): recorded_at now prefers
  fact_data["updated_at"] (the moment the version being closed itself
  became current) over the frozen t_ingestion_start/created_at fields.
- get_fact_as_of()/get_graph_as_of(): historical version selection now uses
  each row's *effective* interval — [previous version's superseded_at (or
  its own recorded_at for version_num==1), own superseded_at) — computed
  via a window function over version_num, NOT via a raw recorded_at
  comparison. This is legacy-compatible by construction: even a
  pre-existing row with a stale/duplicate recorded_at resolves correctly,
  because only the version_num==1 row's own recorded_at is ever consulted
  directly; every later version's interval start comes from its
  predecessor's superseded_at. No migration, no backfill.
- A query at/after the last snapshot now falls through to a materialized
  "current" FactVersion built live from the `facts` row (version_id == 0 —
  see FactVersion docstring) when that row's own provable interval
  ([latest historical superseded_at (or t_ingestion_start/created_at/
  updated_at), t_ingestion_end)) contains the query time. Never inserted
  into fact_versions — read-time only.
- transition_esm(): snapshot moved to AFTER update_state() returns True.
  update_state() returning False (CAS miss, missing fact) or raising no
  longer leaves a phantom fact_versions row.
- invalidate_edge(): gained a CAS guard (WHERE ... AND updated_at = ?), a
  rowcount check, stale-L0 eviction on CAS miss, and its snapshot moved to
  strictly after the guarded UPDATE commits.

NOT in scope for this PR (explicit non-goals — see PR body):
- No VersionStore schema migration, no backfill of existing rows.
- No rewrite of historical fact_versions rows.
- No atomic single-transaction merge of the facts UPDATE and the
  fact_versions INSERT (still two connections/files — a crash in that
  narrow window can still leave a successful transition without a version
  snapshot; unchanged, pre-existing, and out of scope here).
- migrations/009_truth_kernel.sql, AuditChain, the live HTTP time-travel
  endpoint (`GET /facts/{fact_id}/time-travel`, backed by
  SQLiteGraphStore.get_fact_at(), an entirely separate bi-temporal query
  against `facts` directly) are all untouched.

NOTE ON FIXTURES: same convention as test_fact_version_consistency.py and
test_terminal_state_transition_consistency.py — a plain
SQLiteGraphStore(tmp_path / "x.db") only runs the runtime bootstrap DDL,
without any of migration 009's triggers. `migrated_store` explicitly
applies migrations 008-017 first.

NOTE ON TIMING: no test in this file relies on time.sleep() for ordering.
A shared `_FakeClock`, installed via the `clock` fixture, replaces both
core.memory._now() and the `datetime` name imported into
core.version_store, so every "now" read across both modules advances one
shared, deterministic, monotonically-increasing counter — chronological
order between recorded_at/superseded_at/history timestamps is exact and
reproducible, not dependent on real wall-clock resolution.
"""
from __future__ import annotations

import os
import subprocess
import sys
from datetime import UTC, datetime, timedelta

import pytest

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "scripts")
APPLY_MIGRATIONS = os.path.join(SCRIPTS_DIR, "apply_migrations.py")


def _run_apply(db_path: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, APPLY_MIGRATIONS, "--db", db_path, "--no-backup"],
        capture_output=True, text=True,
    )


@pytest.fixture
def migrated_store(tmp_path, monkeypatch):
    """Same convention as test_fact_version_consistency.py's fixture of the
    same name — migrations 008-017 actually applied, real triggers present."""
    from core import memory

    db_path = str(tmp_path / "ts.db")
    memory.SQLiteGraphStore(db_path).get_fact("__bootstrap__")
    result = _run_apply(db_path)
    assert result.returncode == 0, (
        f"apply_migrations failed:\nstdout={result.stdout}\nstderr={result.stderr}"
    )

    fresh = memory.make_store(db_path)
    monkeypatch.setattr(memory, "_GLOBAL_STORE", fresh)
    monkeypatch.setattr(memory, "_L0", fresh._l0)
    monkeypatch.setattr(memory, "_DDL_INITIALIZED", fresh._ddl_initialized_paths)
    monkeypatch.setattr(memory, "SQLITE_PATH", db_path)
    yield fresh
    fresh.close()


class _FakeClock:
    """Deterministic, monotonically-increasing ISO-8601 clock shared between
    core.memory._now() and core.version_store's `datetime.now(UTC)` calls."""

    def __init__(self) -> None:
        self._t = datetime(2026, 1, 1, tzinfo=UTC)

    def tick(self) -> str:
        """Advance and return the new instant (str) — installed as memory._now."""
        self._t = self._t + timedelta(seconds=1)
        return self._t.isoformat()

    def now_dt(self) -> datetime:
        """Advance and return the new instant (datetime) — installed as the
        `datetime.now(tz)` classmethod seen by core.version_store."""
        self._t = self._t + timedelta(seconds=1)
        return self._t

    def peek(self) -> str:
        """Read the current instant without advancing — for building
        expected query timestamps between two known operations."""
        return self._t.isoformat()


@pytest.fixture
def clock(monkeypatch):
    from core import memory, version_store

    c = _FakeClock()
    monkeypatch.setattr(memory, "_now", c.tick)

    class _FakeDateTimeClass:
        @staticmethod
        def now(tz=None):
            return c.now_dt()

    monkeypatch.setattr(version_store, "datetime", _FakeDateTimeClass)
    return c


def _version_count(store, fact_id: str) -> int:
    with store._db() as conn:
        return conn.execute(
            "SELECT COUNT(*) FROM fact_versions WHERE fact_id = ?", (fact_id,)
        ).fetchone()[0]


def _version_rows(store, fact_id: str) -> list[tuple]:
    with store._db() as conn:
        return conn.execute(
            "SELECT version_num, claim, recorded_at, superseded_at "
            "FROM fact_versions WHERE fact_id = ? ORDER BY version_num",
            (fact_id,),
        ).fetchall()


def _raw_row(store, fact_id: str):
    with store._db() as conn:
        return conn.execute(
            "SELECT claim, epistemic_state, t_event_valid_end, t_ingestion_end, updated_at "
            "FROM facts WHERE fact_id = ?",
            (fact_id,),
        ).fetchone()


# ─── Scenarios 1-4: basic V1 -> V2 -> V3 time-travel resolution ─────────────

class TestBasicTimeTravelResolution:
    def test_query_before_first_update_returns_v1(self, migrated_store, clock):
        store = migrated_store
        fid = "tt1"
        store.store_fact_result({"fact_id": fid, "claim": "claim A", "source": "s", "confidence": 0.5})
        t_before_v1v2 = clock.peek()
        store.store_fact_result({"fact_id": fid, "claim": "claim B", "source": "s", "confidence": 0.5})
        store.store_fact_result({"fact_id": fid, "claim": "claim C", "source": "s", "confidence": 0.5})

        from core.version_store import VersionStore
        vs = VersionStore(store.db_path)
        result = vs.get_fact_as_of(fid, t_before_v1v2)
        assert result is not None
        assert result.claim == "claim A", (
            f"expected the ONLY version that existed at t_before_v1v2, got {result.claim!r}"
        )

    def test_query_between_v1v2_and_v2v3_returns_v2(self, migrated_store, clock):
        store = migrated_store
        fid = "tt2"
        store.store_fact_result({"fact_id": fid, "claim": "claim A", "source": "s", "confidence": 0.5})
        store.store_fact_result({"fact_id": fid, "claim": "claim B", "source": "s", "confidence": 0.5})
        t_between = clock.peek()
        store.store_fact_result({"fact_id": fid, "claim": "claim C", "source": "s", "confidence": 0.5})

        from core.version_store import VersionStore
        vs = VersionStore(store.db_path)
        result = vs.get_fact_as_of(fid, t_between)
        assert result is not None
        assert result.claim == "claim B"

    def test_query_after_last_snapshot_returns_current_live_state(self, migrated_store, clock):
        store = migrated_store
        fid = "tt3"
        store.store_fact_result({"fact_id": fid, "claim": "claim A", "source": "s", "confidence": 0.5})
        store.store_fact_result({"fact_id": fid, "claim": "claim B", "source": "s", "confidence": 0.5})
        store.store_fact_result({"fact_id": fid, "claim": "claim C", "source": "s", "confidence": 0.5})
        t_after_last = clock.peek()

        from core.version_store import VersionStore
        vs = VersionStore(store.db_path)
        result = vs.get_fact_as_of(fid, t_after_last)
        assert result is not None, (
            "a query after the last snapshot must resolve to the CURRENT live "
            "facts row, not None — the live state was never represented before"
        )
        assert result.claim == "claim C"
        assert result.version_id == 0, (
            "a materialized-current FactVersion must be flagged version_id == 0 "
            "(not a persisted fact_versions row)"
        )

    def test_query_before_creation_returns_none(self, migrated_store, clock):
        store = migrated_store
        fid = "tt4"
        t_before_creation = clock.peek()
        store.store_fact_result({"fact_id": fid, "claim": "claim A", "source": "s", "confidence": 0.5})

        from core.version_store import VersionStore
        vs = VersionStore(store.db_path)
        result = vs.get_fact_as_of(fid, t_before_creation)
        assert result is None


# ─── Scenario 5: legacy rows with duplicate recorded_at still resolve ───────

class TestLegacyDuplicateRecordedAt:
    def test_legacy_rows_with_identical_recorded_at_still_resolve_correctly(self, migrated_store):
        """Simulate data written by the OLD (buggy) snapshot_before_change():
        two fact_versions rows for the same fact_id sharing an identical
        recorded_at, with superseded_at correctly advancing. This is exactly
        the shape of data already sitting in production databases — the fix
        must resolve these correctly WITHOUT any migration/backfill."""
        store = migrated_store
        fid = "legacy1"
        store.store_fact_result({"fact_id": fid, "claim": "claim C", "source": "s", "confidence": 0.5})

        frozen_recorded_at = "2020-01-01T00:00:00+00:00"
        t1 = "2020-06-01T00:00:00+00:00"
        t2 = "2020-09-01T00:00:00+00:00"
        with store._db() as conn:
            conn.execute(
                "INSERT INTO fact_versions (fact_id, version_num, claim, source, "
                "confidence, epistemic_state, metadata, recorded_at, superseded_at, "
                "caused_by, checksum) VALUES (?, 1, 'claim A', 's', 0.5, 'Observed', "
                "'{}', ?, ?, 'legacy', 'x')",
                (fid, frozen_recorded_at, t1),
            )
            conn.execute(
                "INSERT INTO fact_versions (fact_id, version_num, claim, source, "
                "confidence, epistemic_state, metadata, recorded_at, superseded_at, "
                "caused_by, checksum) VALUES (?, 2, 'claim B', 's', 0.5, 'Observed', "
                "'{}', ?, ?, 'legacy', 'x')",
                (fid, frozen_recorded_at, t2),  # <- identical recorded_at to v1
            )

        from core.version_store import VersionStore
        vs = VersionStore(store.db_path)

        before_v1v2 = "2020-03-01T00:00:00+00:00"
        between = "2020-07-01T00:00:00+00:00"

        r1 = vs.get_fact_as_of(fid, before_v1v2)
        assert r1 is not None and r1.claim == "claim A", (
            f"expected legacy V1 (claim A) at {before_v1v2}, got {r1.claim if r1 else None} "
            "— a duplicate recorded_at must not make the query resolve to a later version"
        )

        r2 = vs.get_fact_as_of(fid, between)
        assert r2 is not None and r2.claim == "claim B"


# ─── Scenario 6-7: get_graph_as_of() — same rules, graph-wide ──────────────

class TestGraphAsOf:
    def test_graph_as_of_resolves_correct_version_per_fact(self, migrated_store, clock):
        store = migrated_store
        fid = "g1"
        store.store_fact_result({"fact_id": fid, "claim": "claim A", "source": "s", "confidence": 0.5})
        t_before_v1v2 = clock.peek()
        store.store_fact_result({"fact_id": fid, "claim": "claim B", "source": "s", "confidence": 0.5})

        from core.version_store import VersionStore
        vs = VersionStore(store.db_path)
        rows = vs.get_graph_as_of(t_before_v1v2)
        matches = [r for r in rows if r.fact_id == fid]
        assert len(matches) == 1
        assert matches[0].claim == "claim A"

    def test_graph_as_of_legacy_duplicate_recorded_at(self, migrated_store):
        """Same shape as TestLegacyDuplicateRecordedAt, but exercised through
        get_graph_as_of(): TWO fact_versions rows share an identical
        recorded_at (as the old buggy snapshot_before_change() produced),
        with superseded_at correctly advancing — the graph-wide query must
        still resolve to the correct version at each point in time."""
        store = migrated_store
        fid = "g2"
        store.store_fact_result({"fact_id": fid, "claim": "claim C", "source": "s", "confidence": 0.5})
        frozen_recorded_at = "2020-01-01T00:00:00+00:00"
        t1 = "2020-06-01T00:00:00+00:00"
        t2 = "2020-09-01T00:00:00+00:00"
        with store._db() as conn:
            conn.execute(
                "INSERT INTO fact_versions (fact_id, version_num, claim, source, "
                "confidence, epistemic_state, metadata, recorded_at, superseded_at, "
                "caused_by, checksum) VALUES (?, 1, 'claim A', 's', 0.5, 'Observed', "
                "'{}', ?, ?, 'legacy', 'x')",
                (fid, frozen_recorded_at, t1),
            )
            conn.execute(
                "INSERT INTO fact_versions (fact_id, version_num, claim, source, "
                "confidence, epistemic_state, metadata, recorded_at, superseded_at, "
                "caused_by, checksum) VALUES (?, 2, 'claim B', 's', 0.5, 'Observed', "
                "'{}', ?, ?, 'legacy', 'x')",
                (fid, frozen_recorded_at, t2),  # <- identical recorded_at to v1
            )

        from core.version_store import VersionStore
        vs = VersionStore(store.db_path)

        before_v1 = "2020-03-01T00:00:00+00:00"
        rows = vs.get_graph_as_of(before_v1)
        matches = [r for r in rows if r.fact_id == fid]
        assert len(matches) == 1
        assert matches[0].claim == "claim A", (
            f"expected legacy V1 (claim A) graph-wide at {before_v1}, got "
            f"{matches[0].claim!r} — a duplicate recorded_at must not select "
            "a later version"
        )

        between = "2020-07-01T00:00:00+00:00"
        rows2 = vs.get_graph_as_of(between)
        matches2 = [r for r in rows2 if r.fact_id == fid]
        assert len(matches2) == 1
        assert matches2[0].claim == "claim B"

    def test_graph_as_of_one_version_per_fact_no_dupes_limit_after_dedup(self, migrated_store, clock):
        store = migrated_store
        fids = ["gd1", "gd2", "gd3", "gd4", "gd5"]
        for fid in fids:
            store.store_fact_result({"fact_id": fid, "claim": "v1", "source": "s", "confidence": 0.5})
            store.store_fact_result({"fact_id": fid, "claim": "v2", "source": "s", "confidence": 0.5})
        t_now = clock.peek()

        from core.version_store import VersionStore
        vs = VersionStore(store.db_path)

        full = vs.get_graph_as_of(t_now, limit=1000)
        our_fids = [r.fact_id for r in full if r.fact_id in fids]
        assert sorted(our_fids) == sorted(fids), "every fact must appear exactly once"
        assert len(our_fids) == len(set(our_fids)), "no fact_id may appear twice"

        limited = vs.get_graph_as_of(t_now, limit=2)
        assert len(limited) == 2, (
            "limit must be applied AFTER deduplication to one version per "
            "fact_id, not before it"
        )
        limited_ids = [r.fact_id for r in limited]
        assert len(limited_ids) == len(set(limited_ids))

        # Deterministic ordering: repeating the same query returns the same
        # sequence of fact_ids.
        limited_again = vs.get_graph_as_of(t_now, limit=2)
        assert [r.fact_id for r in limited_again] == limited_ids


# ─── Scenario 8: process restart — fresh VersionStore instance ────────────

class TestProcessRestart:
    def test_fresh_instance_same_db_path_returns_identical_result(self, migrated_store, clock):
        store = migrated_store
        fid = "restart1"
        store.store_fact_result({"fact_id": fid, "claim": "claim A", "source": "s", "confidence": 0.5})
        t_before_v1v2 = clock.peek()
        store.store_fact_result({"fact_id": fid, "claim": "claim B", "source": "s", "confidence": 0.5})

        from core.version_store import VersionStore
        vs1 = VersionStore(store.db_path)
        r1 = vs1.get_fact_as_of(fid, t_before_v1v2)

        vs2 = VersionStore(store.db_path)  # simulated process restart
        r2 = vs2.get_fact_as_of(fid, t_before_v1v2)

        assert r1 is not None and r2 is not None
        assert r1.claim == r2.claim == "claim A"
        assert r1.version_num == r2.version_num


# ─── Scenario 9: recorded_at sourced from updated_at, not frozen t_ingestion_start

class TestRecordedAtSourcedFromUpdatedAt:
    def test_second_snapshot_recorded_at_differs_from_first(self, migrated_store, clock):
        """V1's snapshot and V2's snapshot must have DIFFERENT recorded_at
        values (t0 then t1) — the original bug sourced recorded_at from the
        frozen t_ingestion_start, so both snapshots got the SAME (creation)
        timestamp regardless of how many updates had actually happened."""
        store = migrated_store
        fid = "rec1"
        store.store_fact_result({"fact_id": fid, "claim": "claim A", "source": "s", "confidence": 0.5})
        store.store_fact_result({"fact_id": fid, "claim": "claim B", "source": "s", "confidence": 0.5})
        store.store_fact_result({"fact_id": fid, "claim": "claim C", "source": "s", "confidence": 0.5})

        rows = _version_rows(store, fid)
        assert len(rows) == 2, f"expected exactly 2 closed snapshots (V1, V2), got {rows}"
        v1_recorded_at = rows[0][2]
        v2_recorded_at = rows[1][2]
        assert v1_recorded_at != v2_recorded_at, (
            f"V1.recorded_at ({v1_recorded_at}) and V2.recorded_at "
            f"({v2_recorded_at}) must differ — both being equal reproduces "
            "Issue #39's frozen-t_ingestion_start defect"
        )
        assert v1_recorded_at < v2_recorded_at


# ─── Scenario 10-12: transition_esm() snapshot ordering ────────────────────

class TestTransitionEsmSnapshotOrdering:
    def test_successful_transition_creates_exactly_one_snapshot_with_pre_image(self, migrated_store):
        store = migrated_store
        fid = "te1"
        store.store_fact_result({"fact_id": fid, "claim": "original", "source": "s", "confidence": 0.9})
        store.transition_esm(fid, "Hypothesized", by="test")
        before_count = _version_count(store, fid)

        ok = store.transition_esm(fid, "Supported", by="test")
        assert ok is True

        after_count = _version_count(store, fid)
        assert after_count == before_count + 1, "exactly one new historical snapshot"

        rows = _version_rows(store, fid)
        last_snapshot = rows[-1]
        assert last_snapshot[1] == "original", "snapshot must contain the PRE-image (old claim)"

        fact = store.get_fact(fid)
        last_history_at = fact["history"][-1]["at"]
        assert last_snapshot[3] == last_history_at, (
            "snapshot's superseded_at must be the same timestamp as the "
            "transition's own history entry — one canonical 'now', not a "
            "separately-read later timestamp from a second connection"
        )

    def test_cas_miss_returns_false_and_leaves_no_phantom_snapshot(self, migrated_store):
        store = migrated_store
        fid = "te2"
        store.store_fact_result({"fact_id": fid, "claim": "c", "source": "s", "confidence": 0.9})
        store.transition_esm(fid, "Hypothesized", by="setup")
        # Populate L0 with the current (soon-to-be-stale) state.
        assert store.get_fact(fid)["epistemic_state"] == "Hypothesized"

        # Concurrent modification via raw SQL, bypassing L0 — simulates a
        # second writer transitioning the fact without this process knowing.
        with store._db() as conn:
            conn.execute(
                "UPDATE facts SET epistemic_state = 'Supported', "
                "fact_version = fact_version + 1, updated_at = '2026-06-01T00:00:00+00:00' "
                "WHERE fact_id = ?",
                (fid,),
            )

        before_count = _version_count(store, fid)
        ok = store.transition_esm(fid, "Contradicted", by="test")
        assert ok is False, "a stale-L0 CAS miss inside update_state() must surface as False"

        after_count = _version_count(store, fid)
        assert after_count == before_count, (
            "no phantom fact_versions row may be created for a transition "
            "that never actually committed to the canonical facts row"
        )
        assert store._l0_get(fid) is None, "stale L0 entry must be evicted on CAS miss"

    def test_forced_sql_failure_propagates_exception_and_leaves_no_phantom_snapshot(self, migrated_store):
        store = migrated_store
        fid = "te3"
        store.store_fact_result({"fact_id": fid, "claim": "c", "source": "s", "confidence": 0.9})
        store.transition_esm(fid, "Hypothesized", by="setup")

        before_count = _version_count(store, fid)

        def _broken_bump_sql(self, conn):
            return "this_column_does_not_exist = this_column_does_not_exist + 1, "

        import core.memory as memory_mod
        orig = memory_mod.SQLiteGraphStore._fact_version_bump_sql
        memory_mod.SQLiteGraphStore._fact_version_bump_sql = _broken_bump_sql
        try:
            with pytest.raises(Exception):
                store.transition_esm(fid, "Supported", by="test")
        finally:
            memory_mod.SQLiteGraphStore._fact_version_bump_sql = orig

        after_count = _version_count(store, fid)
        assert after_count == before_count, (
            "update_state()'s exception must propagate (not be hidden) and "
            "must not leave a phantom fact_versions row"
        )
        row = _raw_row(store, fid)
        assert row[1] == "Hypothesized", "canonical state must be fully rolled back"


# ─── Scenario 13-15: invalidate_edge() CAS + post-commit snapshot ──────────

class TestInvalidateEdgeCasAndOrdering:
    def test_success_closes_row_and_creates_exactly_one_pre_image_snapshot(self, migrated_store):
        store = migrated_store
        fid = "ie1"
        store.store_fact_result({"fact_id": fid, "claim": "c", "source": "s", "confidence": 0.9})
        before_count = _version_count(store, fid)

        ok = store.invalidate_edge(fid)
        assert ok is True

        after_count = _version_count(store, fid)
        assert after_count == before_count + 1

        row = _raw_row(store, fid)
        assert row[2] is not None, "t_event_valid_end must be set"
        assert row[3] is not None, "t_ingestion_end must be set"

        rows = _version_rows(store, fid)
        assert rows[-1][1] == "c", "snapshot must contain the durable pre-image"

    def test_missing_fact_returns_false_and_creates_no_snapshot(self, migrated_store):
        store = migrated_store
        fid = "does-not-exist"
        ok = store.invalidate_edge(fid)
        assert ok is False
        assert _version_count(store, fid) == 0

    def test_cas_miss_returns_false_no_snapshot_stale_l0_evicted_no_overwrite(self, migrated_store):
        store = migrated_store
        fid = "ie3"
        store.store_fact_result({"fact_id": fid, "claim": "c", "source": "s", "confidence": 0.9})
        assert store.get_fact(fid) is not None  # populate L0

        # Concurrent writer changes updated_at (and t_ingestion_end) via raw
        # SQL, bypassing this process's L0.
        with store._db() as conn:
            conn.execute(
                "UPDATE facts SET updated_at = '2026-06-01T00:00:00+00:00', "
                "t_ingestion_end = '2026-06-01T00:00:00+00:00' WHERE fact_id = ?",
                (fid,),
            )

        before_count = _version_count(store, fid)
        ok = store.invalidate_edge(fid)
        assert ok is False, "stale-L0 CAS miss must surface as False, not a silent True"

        after_count = _version_count(store, fid)
        assert after_count == before_count, "no snapshot for a write that never committed"
        assert store._l0_get(fid) is None, "stale L0 entry must be evicted"

        row = _raw_row(store, fid)
        assert row[3] == "2026-06-01T00:00:00+00:00", (
            "the concurrent writer's canonical row must not be overwritten "
            "by the losing invalidate_edge() call"
        )


# ─── Scenario 16: VELANTRIM_VERSION_SNAPSHOTS=false ────────────────────────

class TestSnapshotsDisabled:
    def test_snapshots_disabled_canonical_write_and_fact_version_still_work(self, migrated_store, monkeypatch):
        monkeypatch.setenv("VELANTRIM_VERSION_SNAPSHOTS", "false")
        store = migrated_store
        fid = "nosnap1"
        store.store_fact_result({"fact_id": fid, "claim": "claim A", "source": "s", "confidence": 0.5})
        store.store_fact_result({"fact_id": fid, "claim": "claim B", "source": "s", "confidence": 0.5})

        assert _version_count(store, fid) == 0

        with store._db() as conn:
            row = conn.execute(
                "SELECT claim, fact_version FROM facts WHERE fact_id = ?", (fid,)
            ).fetchone()
        assert row[0] == "claim B"
        assert row[1] == 2, "fact_version bump must not depend on snapshotting"

    def test_current_row_not_returned_before_its_own_updated_at(self, migrated_store, monkeypatch, clock):
        """Copilot review finding (PR #42): when no fact_versions row bounds
        current_start (here: snapshots disabled throughout), the current
        facts row must not be treated as valid all the way back to its
        frozen t_ingestion_start — that would invent history for the window
        between creation and the (un-snapshotted) update that actually
        produced the current contents. current_start must come from
        updated_at instead."""
        monkeypatch.setenv("VELANTRIM_VERSION_SNAPSHOTS", "false")
        store = migrated_store
        fid = "bound1"

        store.store_fact_result({"fact_id": fid, "claim": "V1", "source": "s", "confidence": 0.5})
        t_between = clock.tick()
        store.store_fact_result({"fact_id": fid, "claim": "V2", "source": "s", "confidence": 0.5})
        t2 = clock.peek()

        assert _version_count(store, fid) == 0, "snapshots disabled — no historical row ever written"

        from core.version_store import VersionStore
        vs = VersionStore(store.db_path)

        before_update = vs.get_fact_as_of(fid, t_between)
        assert before_update is None or before_update.claim != "V2", (
            f"a query strictly before the update that produced V2 (at "
            f"{t_between}) must not resolve to V2 — got "
            f"{before_update.claim if before_update else None!r}; this "
            "would invent history for a window with no snapshot proof"
        )

        after_update = vs.get_fact_as_of(fid, t2)
        assert after_update is not None
        assert after_update.claim == "V2"

        assert _version_count(store, fid) == 0, "no synthetic snapshot may be written by a read"


# ─── Scenario 17: verify_versions_integrity() stays green ─────────────────

class TestVerifyVersionsIntegrity:
    def test_integrity_check_passes_for_created_historical_rows(self, migrated_store):
        store = migrated_store
        fid = "vi1"
        store.store_fact_result({"fact_id": fid, "claim": "claim A", "source": "s", "confidence": 0.9})
        store.transition_esm(fid, "Hypothesized", by="test")
        store.transition_esm(fid, "Contradicted", by="test")
        store.invalidate_edge(fid)

        from core.version_store import VersionStore
        vs = VersionStore(store.db_path)
        result = vs.verify_versions_integrity(fid)
        assert result["ok"] is True, result
