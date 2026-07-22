"""
tests/test_terminal_state_transition_consistency.py — PR-C1c (Issue #40)
==============================================================================

Issue #40: update_state() split a single logical ESM transition into TWO
UPDATE statements — the main state-changing UPDATE, then an unconditional
follow-up `UPDATE facts SET metadata = ?`. migration 009's
prevent_collapsed_mutation/prevent_immutablecore_mutation triggers are
`BEFORE UPDATE ON facts` with no `OF <column>` restriction and fire on ANY
subsequent UPDATE once epistemic_state is already Collapsed/ImmutableCore —
so the second (metadata-only) statement always tripped the guard against
the very state the first statement just wrote, aborting the WHOLE
transaction. Result: no fact could ever successfully transition to
'Collapsed' through transition_esm()/update_state() (100% reproducible,
not a race).

Fix (this PR): both statements are merged into ONE UPDATE — state, history,
metadata, fact_version bump, and t_ingestion_end all in the same SET list —
so the trigger sees exactly one row-change per logical transition. Also:
- update_state() now explicitly rejects new_state == "ImmutableCore" itself
  (previously this was accidentally blocked only by the same self-tripping
  bug being fixed here — removing that bug without adding this guard would
  have silently OPENED a Ring-Zero bypass for any direct update_state()
  caller).
- update_state() now checks the merged UPDATE's rowcount and returns False
  (instead of an unconditional True) when the CAS guard misses a
  concurrent modification — the pre-existing two-statement version had no
  rowcount check at all, so a stale caller's metadata UPDATE (no
  epistemic_state condition) would "succeed" even when the real state
  transition silently affected zero rows, corrupting metadata out of sync
  with the actual (unrelated, concurrently-written) epistemic_state.
- update_state() now returns False (not an incorrect True) when the fact
  doesn't exist at all.

NOT in scope for this PR (see Issue #39, left open and untouched):
- VersionStore's pre-commit snapshot call sites (transition_esm() line
  ~2244, invalidate_edge() line ~2890) are NOT moved to post-commit here.
  A forced/failed transition still leaves a phantom fact_versions row via
  transition_esm()'s pre-write snapshot — tracked in #39, not fixed here.
- VersionStore query semantics (get_fact_as_of/get_graph_as_of) are
  unchanged.
- migrations/009_truth_kernel.sql and its triggers are unchanged — the DB
  guards (prevent_collapsed_mutation, prevent_immutablecore_mutation,
  prevent_invalid_esm_transition, bump_fact_version) are exactly as before;
  this PR fixes the application SQL that was tripping over them, not the
  guards themselves.

NOTE ON FIXTURES: same as tests/test_fact_version_consistency.py — a plain
SQLiteGraphStore(tmp_path / "x.db") only runs the runtime bootstrap DDL,
which does NOT include any of migration 009's triggers. `migrated_store`
explicitly applies migrations 008-017 first so the real
prevent_collapsed_mutation/prevent_immutablecore_mutation triggers are
genuinely present — without this, these tests would pass trivially
regardless of the fix (this is exactly why the pre-existing ESM test suite
never caught Issue #40 in the first place).
"""
from __future__ import annotations

import os
import subprocess
import sys

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


@pytest.fixture
def legacy_store(tmp_path, monkeypatch):
    """A store with NO migrations applied at all — the pre-migration-009
    schema (no fact_version column, none of the ESM/terminal-state
    triggers). Used for the "legacy DB without fact_version" compatibility
    scenario (requirement 10)."""
    from core import memory

    db_path = str(tmp_path / "legacy.db")
    fresh = memory.make_store(db_path)
    monkeypatch.setattr(memory, "_GLOBAL_STORE", fresh)
    monkeypatch.setattr(memory, "_L0", fresh._l0)
    monkeypatch.setattr(memory, "_DDL_INITIALIZED", fresh._ddl_initialized_paths)
    monkeypatch.setattr(memory, "SQLITE_PATH", db_path)
    yield fresh
    fresh.close()


def _raw_row(store, fact_id: str):
    with store._db() as conn:
        return conn.execute(
            "SELECT claim, confidence, epistemic_state, metadata, history, "
            "fact_version, t_ingestion_end FROM facts WHERE fact_id = ?",
            (fact_id,),
        ).fetchone()


def _version_count(store, fact_id: str) -> int:
    with store._db() as conn:
        return conn.execute(
            "SELECT COUNT(*) FROM fact_versions WHERE fact_id = ?", (fact_id,)
        ).fetchone()[0]


def _make_fact_at(store, fact_id: str, state: str, *, claim: str = "c",
                   confidence: float = 0.9, metadata=None) -> None:
    """Create a fact and walk it (legally) to `state` via transition_esm()."""
    store.store_fact_result({
        "fact_id": fact_id, "claim": claim, "source": "s",
        "confidence": confidence, "metadata": metadata or {},
    })
    ladder = {
        "Observed": [],
        "Hypothesized": ["Hypothesized"],
        "Contradicted": ["Hypothesized", "Contradicted"],
        "Deprecated": ["Hypothesized", "Contradicted", "Deprecated"],
        "Supported": ["Hypothesized", "Supported"],
        "Validated": ["Hypothesized", "Supported", "Validated"],
    }
    for step in ladder[state]:
        store.transition_esm(fact_id, step, by="setup")


# ─── Scenarios 1-2: legal transitions into Collapsed now succeed ─────────────

class TestCollapsedTransitionSucceeds:
    def test_contradicted_to_collapsed_succeeds_atomically(self, migrated_store):
        store = migrated_store
        fid = "t1"
        _make_fact_at(store, fid, "Contradicted", claim="original")
        before = _raw_row(store, fid)
        v0 = before[5]

        ok = store.transition_esm(fid, "Collapsed", by="test")
        assert ok is True

        row = _raw_row(store, fid)
        assert row[2] == "Collapsed"
        assert row[5] == v0 + 1, f"fact_version must bump by exactly 1, got {v0} -> {row[5]}"
        assert row[6] is not None, "t_ingestion_end must be set on a terminal-state transition"

        history = _get_history(store, fid)
        assert history[-1]["state"] == "Collapsed"
        assert history[-1]["from"] == "Contradicted"

        # metadata must reflect the NEW state (checksum recomputed for
        # Collapsed) — i.e. the metadata update genuinely landed, not just
        # the state column.
        import json as _json
        meta = _json.loads(row[3])
        assert "content_checksum" in meta

    def test_deprecated_to_collapsed_succeeds_atomically(self, migrated_store):
        store = migrated_store
        fid = "t2"
        _make_fact_at(store, fid, "Deprecated", claim="original")
        before = _raw_row(store, fid)
        v0 = before[5]

        ok = store.transition_esm(fid, "Collapsed", by="test")
        assert ok is True

        row = _raw_row(store, fid)
        assert row[2] == "Collapsed"
        assert row[5] == v0 + 1
        assert row[6] is not None

        history = _get_history(store, fid)
        assert history[-1]["state"] == "Collapsed"
        assert history[-1]["from"] == "Deprecated"


def _get_history(store, fact_id: str) -> list:
    import json as _json
    row = _raw_row(store, fact_id)
    return _json.loads(row[4])


# ─── Scenario 3: illegal transition into Collapsed is still rejected ─────────

class TestIllegalCollapsedTransitionRejected:
    def test_observed_to_collapsed_raises_and_changes_nothing(self, migrated_store):
        store = migrated_store
        fid = "t3"
        store.store_fact_result({"fact_id": fid, "claim": "c", "source": "s", "confidence": 0.9})
        before = _raw_row(store, fid)

        with pytest.raises(ValueError):
            store.transition_esm(fid, "Collapsed", by="test")

        after = _raw_row(store, fid)
        assert after == before, "an illegal transition attempt must change nothing at all"
        assert _version_count(store, fid) == 0, (
            "the ESM-legality rejection happens before any snapshot/write — "
            "no fact_versions row either"
        )


# ─── Scenario 4: DB guard still blocks mutating an ALREADY-Collapsed fact ────

class TestAlreadyCollapsedGuardNotWeakened:
    def test_direct_update_state_on_collapsed_fact_still_blocked(self, migrated_store):
        """Bypass transition_esm()'s ESM-legality pre-check (which would
        reject Collapsed->Collapsed/anything before even reaching SQL) by
        calling update_state() directly — confirms prevent_collapsed_mutation
        itself still fires for a genuine attempt to further mutate an
        already-Collapsed fact. This PR must not weaken that guard."""
        import sqlite3

        store = migrated_store
        fid = "t4"
        _make_fact_at(store, fid, "Contradicted", claim="original")
        store.transition_esm(fid, "Collapsed", by="test")
        before = _raw_row(store, fid)

        with pytest.raises(sqlite3.IntegrityError):
            store.update_state(
                fid, "Deprecated",
                {"state": "Deprecated", "at": "2026-01-01T00:00:00Z", "by": "test2"},
                "2026-01-01T00:00:00Z",
            )

        after = _raw_row(store, fid)
        assert after == before, "the blocked mutation attempt must change nothing"


# ─── Scenarios 5-6: ImmutableCore bypass prevention ──────────────────────────

class TestImmutableCoreBypassPrevented:
    def test_direct_update_state_immutablecore_rejected(self, migrated_store):
        from core.memory import ImmutableStateError

        store = migrated_store
        fid = "t5"
        _make_fact_at(store, fid, "Validated", claim="original",
                      metadata={"evidence_refs": ["a", "b"]})
        before = _raw_row(store, fid)
        # 3 legitimate transitions (Observed->Hypothesized->Supported->
        # Validated) already happened in setup — each legitimately creates
        # its own fact_versions snapshot. The assertion below is that the
        # REJECTED call adds nothing on top of that, not that the count is 0.
        versions_before = _version_count(store, fid)

        with pytest.raises(ImmutableStateError):
            store.update_state(
                fid, "ImmutableCore",
                {"state": "ImmutableCore", "at": "2026-01-01T00:00:00Z", "by": "test"},
                "2026-01-01T00:00:00Z",
            )

        after = _raw_row(store, fid)
        assert after == before, (
            "a rejected direct ImmutableCore transition must change nothing: "
            "state, fact_version, metadata, history all untouched"
        )
        assert _version_count(store, fid) == versions_before, (
            "no snapshot side effect from a rejected call — it raises before "
            "ever reaching _snapshot_before_change()"
        )

    def test_transition_esm_immutablecore_still_blocked(self, migrated_store):
        from core.memory import ImmutableStateError

        store = migrated_store
        fid = "t6"
        _make_fact_at(store, fid, "Validated", claim="original")

        with pytest.raises(ImmutableStateError):
            store.transition_esm(fid, "ImmutableCore", by="test")


# ─── Scenario 7: ordinary non-terminal transition unaffected ─────────────────

class TestOrdinaryTransitionUnaffected:
    def test_observed_to_hypothesized_works_as_before(self, migrated_store):
        store = migrated_store
        fid = "t7"
        store.store_fact_result({"fact_id": fid, "claim": "c", "source": "s", "confidence": 0.9})
        v0 = _raw_row(store, fid)[5]

        ok = store.transition_esm(fid, "Hypothesized", by="test")
        assert ok is True

        row = _raw_row(store, fid)
        assert row[2] == "Hypothesized"
        assert row[5] == v0 + 1
        history = _get_history(store, fid)
        assert history[-1]["state"] == "Hypothesized"


# ─── Scenario 8: forced SQL failure rolls back the WHOLE merged statement ────

class TestForcedFailureRollsBackCompletely:
    def test_forced_bump_failure_rolls_back_state_history_metadata_together(
        self, migrated_store, monkeypatch,
    ):
        """Disable the fact_version bump helper (same deterministic
        injection technique as tests/test_fact_version_consistency.py) to
        force the merged UPDATE to trip bump_fact_version on an ordinary
        (non-terminal) transition. Since state/history/metadata/version are
        now all ONE statement, a forced failure must roll back all of them
        together — nothing partially applied.

        Not checked here (see Issue #39, not this PR's scope): whether
        transition_esm()'s pre-write VersionStore snapshot leaves a phantom
        fact_versions row for this same failed attempt. It does — that is
        the still-open, separately-tracked defect in #39.
        """
        store = migrated_store
        fid = "t8"
        store.store_fact_result({"fact_id": fid, "claim": "c", "source": "s", "confidence": 0.9})
        before = _raw_row(store, fid)

        monkeypatch.setattr(store, "_fact_version_bump_sql", lambda conn: "")

        import sqlite3
        with pytest.raises(sqlite3.IntegrityError):
            store.transition_esm(fid, "Hypothesized", by="test")

        after = _raw_row(store, fid)
        assert after == before, (
            "a forced failure must roll back state, history, metadata, and "
            "fact_version together — the whole merged statement, or nothing"
        )


# ─── Scenario 9: CAS / concurrency — no false success ────────────────────────

class TestCasConcurrency:
    def test_stale_expected_state_does_not_overwrite_concurrent_winner(self, migrated_store):
        """Simulate a concurrent winner changing epistemic_state between a
        caller's read and its update_state() call. Before this fix,
        update_state() had NO rowcount check at all and always returned
        True — the CAS-guarded state UPDATE would silently affect zero
        rows, but the (pre-fix) separate metadata UPDATE had no state
        condition and would still "succeed", corrupting metadata into
        inconsistency with the actual (concurrently-written) state."""
        store = migrated_store
        fid = "t9"
        store.store_fact_result({
            "fact_id": fid, "claim": "c", "source": "s", "confidence": 0.9,
            "metadata": {"tag": "before"},
        })

        # Concurrent winner: directly advances the fact past what our
        # about-to-be-stale caller believes the state to be.
        with store._db() as conn:
            conn.execute(
                "UPDATE facts SET epistemic_state='Hypothesized', "
                "fact_version=fact_version+1 WHERE fact_id=?", (fid,),
            )
        store._l0_del(fid)

        # Stale caller: still believes the fact is 'Observed'.
        stale = dict(store.get_fact(fid))
        stale["epistemic_state"] = "Observed"
        store._l0_put(fid, stale)

        ok = store.update_state(
            fid, "Contradicted",
            {"state": "Contradicted", "from": "Observed", "at": "2026-01-01T00:00:00Z", "by": "stale"},
            "2026-01-01T00:00:00Z",
        )
        assert ok is False, "a CAS miss must report False, never a false success"

        row = _raw_row(store, fid)
        assert row[2] == "Hypothesized", "the concurrent winner's state must survive untouched"
        import json as _json
        assert _json.loads(row[3])["tag"] == "before", (
            "metadata must NOT be corrupted by the stale, rejected attempt"
        )

        # Review finding on PR #41: a CAS miss must evict the stale L0 entry
        # it just proved wrong, so the NEXT reader gets a fresh row instead
        # of repeating the same staleness (and potentially the same CAS
        # miss / illegal-transition decision downstream).
        assert store._l0_get(fid) is None, (
            "update_state() must evict L0 on a CAS miss, not leave the "
            "caller's stale snapshot cached for the next reader"
        )
        fresh = store.get_fact(fid)
        assert fresh["epistemic_state"] == "Hypothesized", (
            "a fresh read after the CAS miss must see the real (concurrent "
            "winner's) state, not the stale one the failed caller assumed"
        )

    def test_update_state_on_nonexistent_fact_returns_false(self, migrated_store):
        store = migrated_store
        ok = store.update_state(
            "does_not_exist", "Hypothesized",
            {"state": "Hypothesized", "at": "2026-01-01T00:00:00Z", "by": "test"},
            "2026-01-01T00:00:00Z",
        )
        assert ok is False

    def test_legacy_fallback_evicts_stale_l0_when_row_vanished(self, migrated_store, monkeypatch):
        """Suppressed low-confidence Copilot finding on PR #41, confirmed
        legitimate: the non-JSON-insert fallback branch's own existence
        check (`if not row: return False`) is symmetric to the CAS-miss
        path above — a stale L0 entry surviving a concurrent deletion (or
        just an L0 entry for a fact_id whose row vanished between our
        cached read and this fallback SELECT) must not be left cached for
        the next reader."""
        store = migrated_store
        monkeypatch.setattr(store, "use_json_insert", False)  # force the legacy fallback branch

        fid = "legacy_vanish"
        _make_fact_at(store, fid, "Deprecated", claim="original")

        # Seed L0 with a (soon-to-be-stale) cached copy of the fact.
        stale = dict(store.get_fact(fid))
        store._l0_put(fid, stale)

        # Concurrent deletion of the canonical row, between the caller's
        # cached read and update_state()'s own fallback SELECT.
        # prevent_fact_delete permits DELETE only from Deprecated/Collapsed
        # — exactly the state _make_fact_at() left this fact in.
        with store._db() as conn:
            conn.execute("DELETE FROM facts WHERE fact_id = ?", (fid,))

        ok = store.update_state(
            fid, "Collapsed",
            {"state": "Collapsed", "from": "Deprecated", "at": "2026-01-01T00:00:00Z", "by": "test"},
            "2026-01-01T00:00:00Z",
        )
        assert ok is False, "a vanished row must report False, never a false success"
        assert store._l0_get(fid) is None, (
            "the stale L0 entry for a now-deleted fact must be evicted, "
            "not left for the next reader to repeat the same staleness"
        )
        assert store.get_fact(fid) is None, (
            "a fresh read after the fallback miss must see the real "
            "(deleted) state, not the stale cached copy"
        )


# ─── Scenario 10: both schema modes ───────────────────────────────────────────

class TestBothSchemaModes:
    def test_collapsed_transition_succeeds_on_migrated_schema(self, migrated_store):
        store = migrated_store
        fid = "schema_migrated"
        _make_fact_at(store, fid, "Contradicted")
        assert store.transition_esm(fid, "Collapsed", by="test") is True
        assert _raw_row(store, fid)[2] == "Collapsed"

    def test_collapsed_transition_succeeds_on_legacy_schema_without_fact_version(
        self, legacy_store,
    ):
        """A DB with none of migration 009 applied (no fact_version column,
        no ESM/terminal-state triggers at all) must still work — the merged
        UPDATE's {bump} fragment is empty on this schema, and there are no
        triggers to self-trip against in the first place."""
        store = legacy_store
        fid = "schema_legacy"
        _make_fact_at(store, fid, "Contradicted")

        with store._db() as conn:
            cols = {r[1] for r in conn.execute("PRAGMA table_info(facts)").fetchall()}
        assert "fact_version" not in cols, "sanity: this schema genuinely predates migration 009"

        assert store.transition_esm(fid, "Collapsed", by="test") is True
        assert store.get_fact(fid)["epistemic_state"] == "Collapsed"
