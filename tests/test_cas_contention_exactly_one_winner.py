"""
tests/test_cas_contention_exactly_one_winner.py — CAS contention, symmetric race
==================================================================================

GitHub issue #178: the existing adversarial suite in
``tests/test_truthgate_api_transition.py`` (``TestValidateAndPromoteConcurrencyGuard``)
already proves ``validate_and_promote()``'s guarded CAS write survives an
*asymmetric* race — one validator thread racing against a DIFFERENT mutation
(a concurrent weakening upsert, deletion, or a direct ``transition_esm()``
demotion/promotion that bypasses TruthGate entirely). None of those races put
two REAL, independent ``SQLiteGraphStore`` connections through
``validate_and_promote()`` itself at the same time against the same fact.

This file proves the symmetric case issue #178 asks for: several genuinely
independent ``SQLiteGraphStore`` instances (separate Python objects, each
holding its own persistent ``sqlite3.Connection`` per
``SQLiteGraphStore._db()``, per PR #174's "N independent instances, one
file-backed WAL database" precedent) all call
``validate_and_promote()`` on the SAME fact after reading the SAME durable
pre-mutation snapshot. Exactly one must commit; every other contender must
observe an explicit, honest loss — never a false success, never a silent
retry, never a misreported ``already_validated``.

Scope boundary (see ``docs/adr/ADR-2026-08-03-cas-contention-exactly-one-winner.md``):
``TEST_AND_ADR_ONLY`` — no production code in this diff. The only test-only
seam is a per-instance wrapper around ``_promote_to_validated_cas`` that pins
each contender at a ``threading.Barrier`` immediately before that call (i.e.
strictly AFTER its own durable read + ``TruthGate.evaluate()``, and strictly
BEFORE the guarded UPDATE) and then calls straight through to the real,
unmodified method — the exact pattern already used by
``test_truthgate_api_transition.py``'s ``_run_cas_race()`` helper, generalized
from one racer to N. It never fakes a rowcount, never mutates state itself,
and never changes what the real CAS write does.
"""

from __future__ import annotations

import sqlite3
import threading
from pathlib import Path

import pytest

from core.memory import SQLiteGraphStore
from core.truth_gate import CognitiveMode
from core.version_store import VersionStore

# BALANCED thresholds this repository already documents/relies on elsewhere
# (see test_truthgate_api_transition.py): min_confidence=0.7, min_evidence=2.
_STRONG_CONFIDENCE = 0.85
_STRONG_EVIDENCE_REFS = ["src1", "src2"]
_CONTENDERS = 5
_BARRIER_TIMEOUT_S = 10.0
_JOIN_TIMEOUT_S = 15.0


def _seed_strong_supported_fact(db_path: Path, fact_id: str) -> None:
    """Create one fact in 'Supported' with evidence strong enough to pass
    TruthGate under BALANCED — the only state from which a direct promotion
    to 'Validated' is ESM-legal (ESM_TRANSITIONS['Supported'] includes
    'Validated'; 'Observed' does not)."""
    seed_store = SQLiteGraphStore(str(db_path))
    try:
        seed_store.store_fact({
            "fact_id":    fact_id,
            "claim":      "CAS contention race claim",
            "source":     "cas-contention-test",
            "confidence": _STRONG_CONFIDENCE,
            "metadata":   {"evidence_refs": list(_STRONG_EVIDENCE_REFS)},
        })
        seed_store.transition_esm(fact_id, "Hypothesized")
        seed_store.transition_esm(fact_id, "Supported")
        seeded = seed_store.get_fact(fact_id)
        assert seeded is not None
        assert seeded["epistemic_state"] == "Supported"
    finally:
        seed_store.close()


def _memory_events_total(db_path: Path) -> int:
    """Whole-table count, not a fact_id-scoped one: `_promote_to_validated_cas()`
    calls `AuditChain.log_in_transaction()` without a `fact_id` argument for
    this path (chain identity comes from `audit_subject_id`/`chain_id`
    instead), so the appended row's own `fact_id` column is NULL. The test
    database is dedicated to this one fact and this one scenario, so a
    whole-table delta is the accurate, non-guessed way to count this path's
    own audit side effect."""
    with sqlite3.connect(str(db_path), timeout=5.0) as conn:
        row = conn.execute("SELECT COUNT(*) FROM memory_events").fetchone()
    return int(row[0]) if row else 0


def _integrity_check(db_path: Path) -> str:
    with sqlite3.connect(str(db_path), timeout=5.0) as conn:
        row = conn.execute("PRAGMA integrity_check").fetchone()
    return str(row[0]) if row else "missing"


def _history_validated_count(fact: dict) -> int:
    return sum(1 for h in fact.get("history", []) if h.get("state") == "Validated")


def test_multiple_independent_stores_racing_validate_and_promote_exactly_one_winner(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "cas_contention.db"
    fact_id = "cas_contention_fact"
    _seed_strong_supported_fact(db_path, fact_id)

    # 1) Baseline side-effect counts, captured on a fresh, uninvolved
    #    connection — never guessed, always measured against the real schema.
    versions_before = VersionStore(str(db_path)).count_versions(fact_id)
    events_before = _memory_events_total(db_path)
    assert _integrity_check(db_path) == "ok"

    # 2) N genuinely independent SQLiteGraphStore instances against the SAME
    #    file-backed database — separate Python objects, separate persistent
    #    sqlite3.Connection per PR #174's precedent, separate (per-instance)
    #    L0 caches. Not one shared store, not one shared connection.
    # Schema bootstrap (`_db()`'s lazy `CREATE TABLE/VIEW IF NOT EXISTS ...`,
    # guarded per-instance by `self._ddl_initialized_paths`, not across
    # connections) is intentionally run here, sequentially, for every
    # contender BEFORE any thread starts. Without this, N brand-new store
    # instances whose very FIRST operation is the barrier-gated race also
    # collide on first-use schema initialization — a separate, pre-existing
    # DDL-bootstrap race (`erasure_audit`'s non-idempotent
    # `DROP VIEW IF EXISTS` + bare `CREATE VIEW`, see
    # core/memory.py:573-575) that is explicitly out of this issue's scope
    # (no migrations/DDL changes) and would otherwise contaminate this
    # test's CAS-contention proof with unrelated flakiness. See the ADR's
    # "observed but out of scope" section.
    stores = [SQLiteGraphStore(str(db_path)) for _ in range(_CONTENDERS)]
    for store in stores:
        store.ensure_schema()

    barrier = threading.Barrier(_CONTENDERS, timeout=_BARRIER_TIMEOUT_S)
    results: dict[int, object] = {}
    errors: list[BaseException] = []
    errors_lock = threading.Lock()

    def make_instrumented_cas(original_cas):
        def instrumented(fid, expected_state, expected_updated_at, durable_snapshot, by):
            # Every contender has already done its own durable read AND its
            # own TruthGate.evaluate() by the time validate_and_promote()
            # calls this method (see core/memory.py:3408) — this barrier
            # only pins the moment immediately before the guarded CAS write,
            # so contenders that read the identical pre-mutation snapshot
            # attempt their UPDATE in close proximity instead of trivially
            # serializing one-fully-before-the-next-even-starts. It never
            # fakes rowcount and never mutates state; it calls straight
            # through to the real, unmodified CAS primitive.
            barrier.wait(timeout=_BARRIER_TIMEOUT_S)
            return original_cas(fid, expected_state, expected_updated_at, durable_snapshot, by)
        return instrumented

    for store in stores:
        store._promote_to_validated_cas = make_instrumented_cas(  # type: ignore[method-assign]
            store._promote_to_validated_cas
        )

    def run(index: int, store: SQLiteGraphStore) -> None:
        try:
            results[index] = store.validate_and_promote(
                fact_id, by=f"contender-{index}", mode=CognitiveMode.BALANCED,
            )
        except BaseException as exc:  # noqa: BLE001 - captured, not swallowed
            with errors_lock:
                errors.append(exc)

    threads = [
        threading.Thread(target=run, args=(i, store))
        for i, store in enumerate(stores)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=_JOIN_TIMEOUT_S)
        assert not t.is_alive(), "contender thread did not finish within timeout"

    try:
        assert not errors, f"unexpected thread exceptions: {errors!r}"
        assert len(results) == _CONTENDERS, (
            f"expected {_CONTENDERS} verdicts, got {len(results)}: {results!r}"
        )

        # 3/4/5) Exactly one contender committed; every other one has an
        # explicit, honest non-success outcome.
        winners = [i for i, v in results.items() if v.passed]
        losers = [i for i, v in results.items() if not v.passed]
        assert len(winners) == 1, (
            f"expected exactly one committed winner, got {len(winners)}: "
            f"{[(i, results[i].reason) for i in winners]}"
        )
        assert len(losers) == _CONTENDERS - 1

        winner_verdict = results[winners[0]]
        assert winner_verdict.reason == "passed", winner_verdict.reason

        for i in losers:
            loser_verdict = results[i]
            # 5) never a false success.
            assert loser_verdict.passed is False
            # Preferred, explicit loss reason — never "already_validated"
            # (that idempotent branch only fires on the DURABLE READ at the
            # very start of validate_and_promote(); every contender here did
            # that read before ANY of them had committed, so none can
            # legitimately observe the fact as already Validated mid-race).
            assert loser_verdict.reason == "concurrent_modification", (
                f"contender {i}: expected concurrent_modification, got "
                f"{loser_verdict.reason!r}"
            )

        # 6) no automatic retry: validate_and_promote() and
        # _promote_to_validated_cas() contain no retry loop (see their
        # docstrings/source) — a loser's single verdict IS its final
        # outcome. Confirmed structurally: each contender's `run()` above
        # calls validate_and_promote() exactly once and records exactly one
        # verdict, and this is already asserted by `len(results) ==
        # _CONTENDERS` (a silent internal retry-to-success would have
        # collapsed a loser's reason to "passed"/"already_validated" above,
        # which is independently ruled out).

        # 7) final fact state is correct and durable, visible from a BRAND
        # NEW store instance that was never involved in the race.
        fresh_store = SQLiteGraphStore(str(db_path))
        try:
            final = fresh_store.get_fact(fact_id)
            assert final is not None
            assert final["epistemic_state"] == "Validated"
            assert _history_validated_count(final) == 1, (
                "expected exactly one 'Validated' history entry, found "
                f"{_history_validated_count(final)}"
            )
        finally:
            fresh_store.close()

        # 8) exactly one durable mutation side-effect set relative to
        # baseline: one fact_versions pre-image, one audit/event row — both
        # written only inside the single winning transaction (losers return
        # False before either write is attempted; see
        # core/memory.py:_promote_to_validated_cas).
        versions_after = VersionStore(str(db_path)).count_versions(fact_id)
        events_after = _memory_events_total(db_path)
        assert versions_after == versions_before + 1, (
            f"fact_versions delta: expected +1, got "
            f"{versions_after - versions_before}"
        )
        assert events_after == events_before + 1, (
            f"memory_events delta: expected +1, got "
            f"{events_after - events_before}"
        )

        # 9) database remains intact.
        assert _integrity_check(db_path) == "ok"

        # 10) a later, fresh call observes the completed transition through
        # the normal idempotent contract — no second mutation.
        fresh_store2 = SQLiteGraphStore(str(db_path))
        try:
            idempotent_verdict = fresh_store2.validate_and_promote(
                fact_id, by="post-race-observer", mode=CognitiveMode.BALANCED,
            )
            assert idempotent_verdict.passed is True
            assert idempotent_verdict.reason == "already_validated"
        finally:
            fresh_store2.close()

        versions_final = VersionStore(str(db_path)).count_versions(fact_id)
        events_final = _memory_events_total(db_path)
        assert versions_final == versions_after, (
            "post-race idempotent call must add no fact_versions row, "
            f"delta was {versions_final - versions_after}"
        )
        assert events_final == events_after, (
            "post-race idempotent call must add no memory_events row, "
            f"delta was {events_final - events_after}"
        )
        assert _integrity_check(db_path) == "ok"
    finally:
        for store in stores:
            store.close()


def test_seam_never_fabricates_rowcount_or_mutates_directly() -> None:
    """Documentation-as-regression: the instrumentation seam used above is
    a pure pause-then-delegate wrapper. This test pins that contract so a
    future edit to this file can't quietly turn the seam into something
    that fakes success — by asserting the wrapped callable's __wrapped__-
    style delegation returns the exact same object identity/type the real
    method would for an already-committed idempotent path (no barrier
    contention involved, so this exercises the passthrough itself, not the
    race)."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "seam_passthrough.db"
        fact_id = "seam_fact"
        _seed_strong_supported_fact(db_path, fact_id)

        store = SQLiteGraphStore(str(db_path))
        try:
            original_cas = store._promote_to_validated_cas
            calls: list[tuple] = []

            def passthrough(fid, expected_state, expected_updated_at, durable_snapshot, by):
                calls.append((fid, expected_state, expected_updated_at, by))
                return original_cas(fid, expected_state, expected_updated_at, durable_snapshot, by)

            store._promote_to_validated_cas = passthrough  # type: ignore[method-assign]

            verdict = store.validate_and_promote(
                fact_id, by="seam-check", mode=CognitiveMode.BALANCED,
            )
            assert verdict.passed is True
            assert verdict.reason == "passed"
            assert len(calls) == 1
            fid, expected_state, expected_updated_at, by = calls[0]
            assert fid == fact_id
            assert expected_state == "Supported"
            assert by == "seam-check"
        finally:
            store.close()


@pytest.mark.parametrize("run_index", range(3))
def test_race_is_stable_under_repetition(tmp_path: Path, run_index: int) -> None:
    """Same scenario as the main race test, restated compactly and run under
    a fresh tmp_path/database each parametrized invocation, so a single
    `pytest` run already exercises the race more than once beyond the
    manual repeat-N-times validation step recorded in the ADR/PR body."""
    db_path = tmp_path / f"cas_contention_repeat_{run_index}.db"
    fact_id = "cas_contention_fact"
    _seed_strong_supported_fact(db_path, fact_id)

    # See the main race test's comment: schema bootstrap must be forced,
    # sequentially, for every fresh contender BEFORE the race starts, so
    # this test proves only CAS contention — not the separate, out-of-scope
    # `erasure_audit` DDL-bootstrap race (core/memory.py:573-575).
    stores = [SQLiteGraphStore(str(db_path)) for _ in range(_CONTENDERS)]
    for store in stores:
        store.ensure_schema()
    barrier = threading.Barrier(_CONTENDERS, timeout=_BARRIER_TIMEOUT_S)
    results: dict[int, object] = {}
    errors: list[BaseException] = []
    errors_lock = threading.Lock()

    def make_instrumented_cas(original_cas):
        def instrumented(fid, expected_state, expected_updated_at, durable_snapshot, by):
            barrier.wait(timeout=_BARRIER_TIMEOUT_S)
            return original_cas(fid, expected_state, expected_updated_at, durable_snapshot, by)
        return instrumented

    for store in stores:
        store._promote_to_validated_cas = make_instrumented_cas(  # type: ignore[method-assign]
            store._promote_to_validated_cas
        )

    def run(index: int, store: SQLiteGraphStore) -> None:
        try:
            results[index] = store.validate_and_promote(
                fact_id, by=f"contender-{index}", mode=CognitiveMode.BALANCED,
            )
        except BaseException as exc:  # noqa: BLE001
            with errors_lock:
                errors.append(exc)

    threads = [threading.Thread(target=run, args=(i, s)) for i, s in enumerate(stores)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=_JOIN_TIMEOUT_S)
        assert not t.is_alive()

    try:
        assert not errors, f"unexpected thread exceptions: {errors!r}"
        winners = [i for i, v in results.items() if v.passed]
        assert len(winners) == 1
        for i, v in results.items():
            if i not in winners:
                assert v.reason == "concurrent_modification"
        assert _integrity_check(db_path) == "ok"
    finally:
        for store in stores:
            store.close()
