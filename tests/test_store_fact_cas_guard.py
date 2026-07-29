"""
Regression tests for the M3 CAS-guard fix (Claude audit 2026-07-28).

store_fact()'s UPSERT has no `WHERE epistemic_state=?` guard of its own — it
relies on the DB triggers `prevent_collapsed_mutation`/
`prevent_immutablecore_mutation` (migration 009) to fail closed on any UPDATE
to a Collapsed/ImmutableCore row. That's correct (no silent corruption), but
store_fact() (the legacy bool API) only ever documented ValueError /
MemoryBudgetExceededError as its exceptions — the raw sqlite3.IntegrityError
from the DB trigger bubbled straight out instead, so a caller that only
catches the documented exceptions would still crash.
store_fact_result() already converted the identical failure into
WriteStatus.FAILED_STORAGE via its own outer try/except — this fix brings
the legacy bool API's behavior in line (raising ValueError, its own
documented exception family) rather than leaking the DB-level exception type.

NOTE: store_facts_batch() has the same missing CAS-guard SQL shape, but its
existing, deliberate contract (see
tests/test_fact_version_consistency.py::test_batch_one_conflicting_record_still_rolls_back_whole_transaction
and tests/test_canonical_write_protocol.py::test_batch_version_failure_rolls_back_every_record_and_audit)
is to let sqlite3.IntegrityError propagate on ANY batch conflict, of which a
Collapsed/ImmutableCore race is just one cause among several (fact_version
bump violations, forced audit-evidence failures). Swallowing only the
Collapsed/ImmutableCore case there would make store_facts_batch()'s failure
behavior depend on which trigger fired — inconsistent and surprising versus
its current uniform "raises on any conflict" contract. Left as-is; not part
of this fix.

A fact reaching Collapsed and then receiving a further claim update is the
simplest real trigger for this — no artificial race/monkeypatching needed,
since the trigger aborts on ANY update to a Collapsed row regardless of which
columns change.

NOTE ON FIXTURES: same convention as
tests/test_terminal_state_transition_consistency.py — a plain
SQLiteGraphStore(tmp_path / "x.db") only runs the runtime bootstrap DDL, which
does NOT include migration 009's triggers. `migrated_store` explicitly
applies migrations 008-017 first so prevent_collapsed_mutation is genuinely
present; without it these tests would pass trivially regardless of the fix.
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


def _make_collapsed_fact(store, fact_id="collapsed-1"):
    store.store_fact_result({
        "fact_id": fact_id,
        "claim": "original claim",
        "source": "test_src",
        "confidence": 0.5,
    })
    assert store.transition_esm(fact_id, "Hypothesized", by="setup")
    assert store.transition_esm(fact_id, "Contradicted", by="setup")
    assert store.transition_esm(fact_id, "Collapsed", by="setup")
    assert store.get_fact(fact_id)["epistemic_state"] == "Collapsed"
    return fact_id


class TestStoreFactRaisesValueErrorNotRawIntegrityError:
    def test_updating_a_collapsed_fact_raises_value_error(self, migrated_store):
        store = migrated_store
        fact_id = _make_collapsed_fact(store)

        with pytest.raises(ValueError, match="CAS race"):
            store.store_fact({
                "fact_id": fact_id,
                "claim": "a different claim",
                "source": "test_src",
                "confidence": 0.9,
            })

        # The row must still read exactly as it did before the rejected call.
        row = store.get_fact(fact_id)
        assert row["epistemic_state"] == "Collapsed"
        assert row["claim"] == "original claim"

    def test_store_fact_result_still_reports_failed_storage(self, migrated_store):
        """store_fact_result() already handled this correctly before the fix
        (audit M3) — kept as a sibling assertion so the two APIs' behavior
        can't silently diverge again."""
        from core.write_result import WriteStatus

        store = migrated_store
        fact_id = _make_collapsed_fact(store)

        result = store.store_fact_result({
            "fact_id": fact_id,
            "claim": "a different claim",
            "source": "test_src",
            "confidence": 0.9,
        })
        assert result.status == WriteStatus.FAILED_STORAGE
        assert result.durable_write is False
