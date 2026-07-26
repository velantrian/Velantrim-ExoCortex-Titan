"""
tests/test_truth_maintenance_supersede.py — TruthMaintenance.supersede() regression
=====================================================================================

Confirmed bugs (pre-fix), all in core/truth_maintenance.py::supersede():

1. It called TruthGate with the wrong constructor: TruthGate(mode=CognitiveMode.PRECISION)
   — TruthGate.__init__() takes (store, contradiction_detector=...), not `mode`.
2. It unpacked TruthGate.evaluate() as `ok, msg = tg.evaluate(...)` — evaluate()
   actually returns a single TruthGateVerdict object, not an (ok, msg) tuple.
3. Both (1) and (2) always raised, and were caught by a broad `except Exception`,
   so the advertised TruthGate check never actually ran — supersede() silently
   fell through without ever gating the new fact.
4. The new fact was stored (store_fact()) BEFORE any verification happened.
5. Even when validation/promotion failed, the function still deprecated the old
   fact, added SUPERSEDED_BY, appended provenance, and returned the new fact_id
   — i.e. it could report success for an operation that never actually verified
   anything.
6. The new fact, old fact, cache, audit history and relation were never
   coordinated as one operation — each step was an independent store_fact()/
   transition_esm() call with its own commit, leaving windows where a crash or
   a failed later step left a durable new fact with no verification, or an
   orphaned old-fact mutation with no corresponding new fact.

Fix: supersede() is rewritten around two pieces:

- core.truth_gate.TruthGate(store, contradiction_detector="none").evaluate(
      candidate, mode=CognitiveMode.PRECISION, by="truth_maintenance.supersede")
  evaluated BEFORE any durable write — using the real API, no threshold-logic
  duplication. Any exception (including ImportError) here is treated as a
  fail-closed rejection (return None), never as "gate unavailable, promote
  anyway" (the exact bug in the old code).

- core.memory.SQLiteGraphStore.supersede_fact_cas(): a single atomic facts
  transaction (one `with self._db() as conn:` block) that either commits the
  new fact all the way from Observed to Validated AND the old fact to
  Deprecated together, or leaves both completely untouched. It is guarded by
  a CAS on the old fact's (fact_id, epistemic_state, updated_at) taken from
  the SAME durable snapshot TruthGate evaluated against — the exact fact
  TruthGate approved is the exact fact the transaction mutates, or it aborts.
  This is deliberately NOT built from independent store_fact()/
  promote_to_validated()/transition_esm() calls (each opens its own
  connection/transaction) — that would recreate the partial-commit window
  bug (6) above.

Success is reported (return new_fact_id) only when: the old durable snapshot
is still current, the new candidate passes TruthGate, the new fact reaches
Validated, the old fact reaches Deprecated, and both facts-table mutations
commit together. Any rejected/raced/failed operation returns None and leaves
the old fact completely unchanged, no new durable fact, no false relation, no
false audit record.

Known, documented, out-of-scope limitation (see docs/PROJECT_STATUS.md): the
causal-graph relation (SUPERSEDED_BY) and the provenance "fact_superseded"
event are written AFTER the atomic facts-transaction commits, on separate
connections/files — they are best-effort, not part of the same transaction.
A process crash after the facts commit but before those secondary writes can
leave a successful supersede without its audit/relation artifacts. These
tests stub causal_graph/provenance_chain to verify supersede() *calls* them
correctly post-commit, without depending on core.causal_graph's own relation-
type whitelist (SUPERSEDED_BY is not currently a member of
FORWARD_RELATION_TYPES there — a pre-existing, separate issue in
core/causal_graph.py, explicitly out of scope for this PR).

Follow-up fix (Codex review on PR #11 found 5 more issues, all addressed
here — the atomic CAS transaction from the section above is unchanged):

1. old_id was never checked against IMMUTABLE_FACT_IDS before mutation — the
   generic ESM_TRANSITIONS matrix alone allows Validated -> Deprecated, so
   supersede() could deprecate a protected VALUES_CORE/RING_ZERO fact and
   insert a replacement, bypassing the same guard transition_esm()/
   validate_and_promote() already enforce. Fixed: same check, same
   ImmutableStateError, before any read or mutation.
2. The new fact's INSERT never consulted core.memory_budget's
   check_before_write(is_new_insert=True) the way store_fact() does, so a
   store already at its hard limit could still grow via supersede(). Fixed:
   the same canonical helper now runs before the atomic transaction; a
   rejection leaves both facts untouched.
3. An omitted claim_type/origin_type defaulted straight to 'UNKNOWN' instead
   of running store_fact()'s deterministic classify_claim()/normalizers, so
   a superseded external world fact could become Validated but
   claim_type=UNKNOWN — losing VERIFIED truth-policy semantics under
   ENABLE_TRUTH_POLICY. Fixed: the exact same classification logic
   store_fact() runs is now reused (not routed through store_fact() itself).
4. The atomic insert never applied core.domain_tags' domain-metadata
   preparation (ENABLE_DOMAIN_TAGS, default ON) the way store_fact() does,
   so a superseded fact silently lost domain/content_domain and dropped out
   of domain-scoped reads. Fixed: the same apply_domain_to_metadata() call
   now runs before the candidate is built; explicit metadata.domain is
   preserved.
5. WriteGate (ENABLE_WRITE_GATE) was never consulted, so a WORLD_FACT with
   source='unknown' — which TruthGate alone does not reject, since it only
   checks the source string is non-empty — could reach Validated through
   supersede() even though an equivalent store_fact() call would have been
   rejected. Fixed: the same admit_fact() check now runs before TruthGate
   and before any durable mutation, honoring the existing feature flag
   exactly as store_fact() does (not made globally mandatory here).
"""

from __future__ import annotations

import copy

import pytest


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def store(tmp_path, monkeypatch):
    """Fresh, isolated SQLiteGraphStore wired in as core.memory._GLOBAL_STORE
    — supersede() (a module-level function) always operates on the global
    store, so tests must redirect it rather than constructing their own
    disconnected instance. tests/conftest.py's autouse fixture restores the
    original _GLOBAL_STORE after every test regardless."""
    import core.memory as memory_mod

    s = memory_mod.SQLiteGraphStore(str(tmp_path / "supersede.db"))
    monkeypatch.setattr(memory_mod, "_GLOBAL_STORE", s)
    return s


class _FakeCausalGraph:
    """Records add_relation() calls without core.causal_graph's real
    FORWARD_RELATION_TYPES whitelist (which does not currently include
    SUPERSEDED_BY — a separate, pre-existing gap, out of scope here)."""

    def __init__(self):
        self.calls: list[dict] = []

    def add_relation(self, from_fact_id, to_fact_id, relation_type,
                      confidence=0.8, **kwargs):
        self.calls.append({
            "from_fact_id": from_fact_id,
            "to_fact_id": to_fact_id,
            "relation_type": relation_type,
            "confidence": confidence,
        })
        return "fake_relation_id"


class _FakeProvenanceChain:
    def __init__(self):
        self.events: list[dict] = []

    def append(self, fact_id, *, event_type, actor="system", reason=None, **kwargs):
        self.events.append({
            "fact_id": fact_id, "event_type": event_type,
            "actor": actor, "reason": reason,
        })
        return True, "fake_event_hash"


@pytest.fixture
def fake_causal_graph(monkeypatch):
    import core.causal_graph as causal_graph_mod

    fake = _FakeCausalGraph()
    monkeypatch.setattr(causal_graph_mod, "get_causal_graph", lambda: fake)
    return fake


@pytest.fixture
def fake_provenance_chain(monkeypatch):
    import core.provenance_chain as provenance_mod

    fake = _FakeProvenanceChain()
    monkeypatch.setattr(provenance_mod, "get_provenance_chain", lambda: fake)
    return fake


def _make_old_fact(store, fact_id="old_fact", *, final_state="Validated"):
    """Create an old fact and legally walk it to `final_state`."""
    store.store_fact({
        "fact_id":    fact_id,
        "claim":      "old claim",
        "source":     "integration-test",
        "confidence": 0.9,
        "metadata":   {"evidence_refs": ["a", "b", "c", "d", "e"]},
    })
    ladder = {
        "Observed":     [],
        "Hypothesized": ["Hypothesized"],
        "Supported":    ["Hypothesized", "Supported"],
        "Validated":    ["Hypothesized", "Supported", "Validated"],
        "Contradicted": ["Hypothesized", "Contradicted"],
        "Collapsed":    ["Hypothesized", "Contradicted", "Collapsed"],
    }
    for state in ladder[final_state]:
        store.transition_esm(fact_id, state)
    return store._get_fact_durable(fact_id)


def _strong_candidate(new_id="new_fact"):
    """Passes PRECISION (min_confidence=0.9, min_evidence=5)."""
    return {
        "fact_id":    new_id,
        "claim":      "new claim",
        "source":     "integration-test",
        "confidence": 0.95,
        "metadata":   {"evidence_refs": ["a", "b", "c", "d", "e"]},
    }


def _weak_candidate(new_id="new_fact"):
    """Fails PRECISION on both confidence and evidence."""
    return {
        "fact_id":    new_id,
        "claim":      "weak new claim",
        "source":     "integration-test",
        "confidence": 0.5,
        "metadata":   {"evidence_refs": ["a"]},
    }


# ─── 1. Strong candidate succeeds ────────────────────────────────────────────

class TestSupersedeStrongCandidateSucceeds:
    def test_strong_candidate_succeeds(self, store, fake_causal_graph, fake_provenance_chain):
        from core.truth_maintenance import supersede

        _make_old_fact(store, "old_1", final_state="Validated")
        result = supersede("old_1", _strong_candidate("new_1"))

        assert result == "new_1"

        old = store._get_fact_durable("old_1")
        new = store._get_fact_durable("new_1")

        assert old["epistemic_state"] == "Deprecated"
        assert new["epistemic_state"] == "Validated"

        new_states = [h["state"] for h in new["history"]]
        assert new_states == ["Hypothesized", "Supported", "Validated"]
        assert all(h["by"] == "truth_maintenance.supersede" for h in new["history"])

        assert old["history"][-1]["state"] == "Deprecated"
        assert old["history"][-1]["by"] == "truth_maintenance.supersede"

        assert fake_causal_graph.calls == [{
            "from_fact_id": "old_1", "to_fact_id": "new_1",
            "relation_type": "SUPERSEDED_BY", "confidence": 0.95,
        }]
        assert len(fake_provenance_chain.events) == 1
        assert fake_provenance_chain.events[0]["fact_id"] == "old_1"
        assert fake_provenance_chain.events[0]["event_type"] == "fact_superseded"


# ─── 2. Weak candidate is rejected ───────────────────────────────────────────

class TestSupersedeWeakCandidateRejected:
    def test_weak_candidate_is_rejected(self, store, fake_causal_graph, fake_provenance_chain):
        from core.truth_maintenance import supersede

        before = _make_old_fact(store, "old_2", final_state="Validated")
        result = supersede("old_2", _weak_candidate("new_2"))

        assert result is None
        after = store._get_fact_durable("old_2")
        assert after["epistemic_state"] == before["epistemic_state"]
        assert after["updated_at"] == before["updated_at"]
        assert store.get_fact("new_2") is None
        assert fake_causal_graph.calls == []
        assert fake_provenance_chain.events == []


# ─── 3. TruthGate exception fails closed ────────────────────────────────────

class TestSupersedeTruthGateExceptionFailsClosed:
    def test_truthgate_exception_fails_closed(
        self, store, fake_causal_graph, fake_provenance_chain, monkeypatch,
    ):
        from core.truth_gate import TruthGate
        from core.truth_maintenance import supersede

        before = _make_old_fact(store, "old_3", final_state="Validated")

        def _broken_evaluate(self, fact, mode=None, by="truth_gate"):
            raise RuntimeError("simulated TruthGate crash")

        monkeypatch.setattr(TruthGate, "evaluate", _broken_evaluate)

        result = supersede("old_3", _strong_candidate("new_3"))

        assert result is None
        after = store._get_fact_durable("old_3")
        assert after["epistemic_state"] == before["epistemic_state"]
        assert after["updated_at"] == before["updated_at"]
        assert store.get_fact("new_3") is None
        assert fake_causal_graph.calls == []
        assert fake_provenance_chain.events == []

    def test_truthgate_import_error_fails_closed(
        self, store, fake_causal_graph, fake_provenance_chain, monkeypatch,
    ):
        """ImportError specifically (e.g. core.truth_gate broken/missing at
        runtime) must NOT fall back to promoting without a gate — that was
        the exact pre-fix behavior this PR removes."""
        import builtins

        from core.truth_maintenance import supersede

        _make_old_fact(store, "old_3b", final_state="Validated")

        real_import = builtins.__import__

        def _raising_import(name, *args, **kwargs):
            if name == "core.truth_gate":
                raise ImportError("simulated: core.truth_gate unavailable")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", _raising_import)
        result = supersede("old_3b", _strong_candidate("new_3b"))

        assert result is None
        assert store.get_fact("new_3b") is None


# ─── 4. Missing old fact ─────────────────────────────────────────────────────

class TestSupersedeMissingOldFact:
    def test_missing_old_fact(self, store, fake_causal_graph, fake_provenance_chain):
        from core.truth_maintenance import supersede

        result = supersede("does_not_exist", _strong_candidate("new_4"))

        assert result is None
        assert store.get_fact("new_4") is None
        assert fake_causal_graph.calls == []
        assert fake_provenance_chain.events == []


# ─── 5. Missing/invalid new fact_id, initial state, empty old_id ────────────

class TestSupersedeInputValidation:
    def test_empty_old_id_raises(self, store):
        from core.truth_maintenance import supersede

        with pytest.raises(ValueError):
            supersede("", _strong_candidate("new_5a"))
        assert store.get_fact("new_5a") is None

    def test_missing_new_fact_id_raises(self, store):
        from core.truth_maintenance import supersede

        _make_old_fact(store, "old_5b", final_state="Validated")
        candidate = _strong_candidate("new_5b")
        del candidate["fact_id"]

        with pytest.raises(ValueError):
            supersede("old_5b", candidate)

        after = store._get_fact_durable("old_5b")
        assert after["epistemic_state"] == "Validated"

    def test_empty_new_fact_id_raises(self, store):
        from core.truth_maintenance import supersede

        _make_old_fact(store, "old_5c", final_state="Validated")
        candidate = _strong_candidate("")

        with pytest.raises(ValueError):
            supersede("old_5c", candidate)

    def test_invalid_initial_state_raises(self, store):
        """Caller-supplied initial epistemic_state other than 'Observed' is
        a programmer error, not an operational rejection."""
        from core.truth_maintenance import supersede

        _make_old_fact(store, "old_5d", final_state="Validated")
        candidate = _strong_candidate("new_5d")
        candidate["epistemic_state"] = "Validated"

        with pytest.raises(ValueError):
            supersede("old_5d", candidate)
        assert store.get_fact("new_5d") is None


# ─── 6. old_id == new_id ─────────────────────────────────────────────────────

class TestSupersedeOldIdEqualsNewId:
    def test_old_id_equals_new_id_rejected(self, store):
        from core.truth_maintenance import supersede

        _make_old_fact(store, "same_id", final_state="Validated")
        before = store._get_fact_durable("same_id")

        with pytest.raises(ValueError):
            supersede("same_id", _strong_candidate("same_id"))

        after = store._get_fact_durable("same_id")
        assert after["epistemic_state"] == before["epistemic_state"]
        assert after["updated_at"] == before["updated_at"]


# ─── 7. Existing new_id collision ────────────────────────────────────────────

class TestSupersedeNewIdCollision:
    def test_existing_new_id_collision_rejected(
        self, store, fake_causal_graph, fake_provenance_chain,
    ):
        from core.truth_maintenance import supersede

        _make_old_fact(store, "old_7", final_state="Validated")
        store.store_fact({
            "fact_id": "taken_id", "claim": "pre-existing fact",
            "source": "integration-test", "confidence": 0.4,
        })
        target_before = store._get_fact_durable("taken_id")
        old_before = store._get_fact_durable("old_7")

        result = supersede("old_7", _strong_candidate("taken_id"))

        assert result is None
        target_after = store._get_fact_durable("taken_id")
        assert target_after["claim"] == target_before["claim"]
        assert target_after["confidence"] == target_before["confidence"]
        assert target_after["epistemic_state"] == target_before["epistemic_state"]

        old_after = store._get_fact_durable("old_7")
        assert old_after["epistemic_state"] == old_before["epistemic_state"]
        assert old_after["updated_at"] == old_before["updated_at"]
        assert fake_causal_graph.calls == []
        assert fake_provenance_chain.events == []


# ─── 8. Illegal old-state → Deprecated transition ───────────────────────────

class TestSupersedeIllegalOldStateTransition:
    def test_illegal_old_state_to_deprecated_rejected(
        self, store, fake_causal_graph, fake_provenance_chain,
    ):
        """Collapsed is terminal (ESM_TRANSITIONS['Collapsed'] == set()) —
        Deprecated is not reachable from it. Must be rejected before any
        mutation, not silently attempted."""
        from core.truth_maintenance import supersede

        before = _make_old_fact(store, "old_8", final_state="Collapsed")

        with pytest.raises(ValueError):
            supersede("old_8", _strong_candidate("new_8"))

        after = store._get_fact_durable("old_8")
        assert after["epistemic_state"] == before["epistemic_state"] == "Collapsed"
        assert after["updated_at"] == before["updated_at"]
        assert store.get_fact("new_8") is None
        assert fake_causal_graph.calls == []
        assert fake_provenance_chain.events == []


# ─── 9. Deterministic concurrent modification ───────────────────────────────

class TestSupersedeConcurrentModification:
    def test_deterministic_concurrent_modification(
        self, store, fake_causal_graph, fake_provenance_chain, monkeypatch,
    ):
        """A concurrent writer changes the old fact's state/updated_at AFTER
        TruthGate evaluated the candidate but BEFORE the guarded facts
        transaction commits. The CAS must catch this: no false success, no
        new fact, old fact keeps the concurrent writer's state (not ours),
        no relation/audit artifact."""
        from core.memory import SQLiteGraphStore
        from core.truth_gate import TruthGate
        from core.truth_maintenance import supersede

        _make_old_fact(store, "old_9", final_state="Validated")

        real_evaluate = TruthGate.evaluate

        def _racy_evaluate(self, fact, mode=None, by="truth_gate"):
            verdict = real_evaluate(self, fact, mode=mode, by=by)
            racer = SQLiteGraphStore(store.db_path)
            racer.store_fact({
                "fact_id": "old_9", "claim": "old claim",
                "source": "integration-test", "confidence": 0.1,
                "metadata": {"evidence_refs": ["a", "b", "c", "d", "e", "raced"]},
            })
            return verdict

        monkeypatch.setattr(TruthGate, "evaluate", _racy_evaluate)

        result = supersede("old_9", _strong_candidate("new_9"))

        assert result is None
        assert store.get_fact("new_9") is None

        raced = store._get_fact_durable("old_9")
        assert raced["confidence"] == 0.1, (
            "old fact must keep the concurrent writer's state, not ours"
        )
        assert raced["epistemic_state"] == "Validated"  # racer only weakened content
        assert fake_causal_graph.calls == []
        assert fake_provenance_chain.events == []


# ─── 10. Transaction rollback on injected mid-transaction failure ───────────

class TestSupersedeTransactionRollback:
    def test_rollback_after_new_insertion_before_old_deprecation(
        self, store, fake_causal_graph, fake_provenance_chain, monkeypatch,
    ):
        """Inject a failure strictly between the new fact's insert+ESM-ladder
        and the old fact's guarded Deprecated UPDATE — supersede_fact_cas()
        calls _now() exactly once per ladder step (3) plus once at the very
        top and once for the old-fact deprecation timestamp (5 calls total
        on the success path); raising on the 5th call lands exactly in that
        window."""
        import core.memory as memory_mod
        from core.truth_maintenance import supersede

        before = _make_old_fact(store, "old_10", final_state="Validated")

        real_now = memory_mod._now
        call_count = {"n": 0}

        def _counting_now():
            call_count["n"] += 1
            if call_count["n"] == 5:
                raise RuntimeError("injected failure before old-fact deprecation")
            return real_now()

        monkeypatch.setattr(memory_mod, "_now", _counting_now)

        result = supersede("old_10", _strong_candidate("new_10"))

        assert result is None
        assert call_count["n"] == 5, "injection point was never reached"
        assert store.get_fact("new_10") is None, (
            "new fact must not survive a mid-transaction rollback"
        )
        after = store._get_fact_durable("old_10")
        assert after["epistemic_state"] == before["epistemic_state"]
        assert after["updated_at"] == before["updated_at"]
        assert fake_causal_graph.calls == []
        assert fake_provenance_chain.events == []


# ─── 11. Cache correctness ───────────────────────────────────────────────────

class TestSupersedeCacheCorrectness:
    def test_success_exposes_committed_final_states(
        self, store, fake_causal_graph, fake_provenance_chain,
    ):
        from core.truth_maintenance import supersede

        _make_old_fact(store, "old_11", final_state="Validated")
        result = supersede("old_11", _strong_candidate("new_11"))
        assert result == "new_11"

        # get_fact() prefers L0 — must reflect the committed truth, not a
        # stale or absent entry.
        old_cached = store.get_fact("old_11")
        new_cached = store.get_fact("new_11")
        assert old_cached["epistemic_state"] == "Deprecated"
        assert new_cached["epistemic_state"] == "Validated"

    def test_failed_attempt_leaves_no_speculative_l0_entry(
        self, store, fake_causal_graph, fake_provenance_chain,
    ):
        from core.truth_maintenance import supersede

        _make_old_fact(store, "old_11b", final_state="Validated")
        store._l0_del("old_11b")
        assert store._l0_get("old_11b") is None, "setup: expected uncached"

        result = supersede("old_11b", _weak_candidate("new_11b"))

        assert result is None
        assert store._l0_get("new_11b") is None, (
            "a rejected supersede must not leave a speculative L0 entry "
            "for the never-created new fact"
        )
        old_l0 = store._l0_get("old_11b")
        assert old_l0 is None or old_l0["epistemic_state"] != "Deprecated", (
            "a rejected supersede must not leave a speculative Deprecated "
            "L0 entry for the untouched old fact"
        )


# ─── 12. Caller-input immutability ──────────────────────────────────────────

class TestSupersedeCallerInputImmutability:
    def test_new_fact_dict_unchanged_after_success(
        self, store, fake_causal_graph, fake_provenance_chain,
    ):
        from core.truth_maintenance import supersede

        _make_old_fact(store, "old_12a", final_state="Validated")
        candidate = _strong_candidate("new_12a")
        frozen = copy.deepcopy(candidate)

        result = supersede("old_12a", candidate)

        assert result == "new_12a"
        assert candidate == frozen, "supersede() mutated the caller's dict"

    def test_new_fact_dict_unchanged_after_rejection(
        self, store, fake_causal_graph, fake_provenance_chain,
    ):
        from core.truth_maintenance import supersede

        _make_old_fact(store, "old_12b", final_state="Validated")
        candidate = _weak_candidate("new_12b")
        frozen = copy.deepcopy(candidate)

        result = supersede("old_12b", candidate)

        assert result is None
        assert candidate == frozen, "supersede() mutated the caller's dict"


# ─── 13. Ring Zero protection (Codex review on PR #11, finding #1) ─────────

class TestSupersedeRingZeroProtection:
    @pytest.mark.parametrize("ring_zero_id", ["VALUES_CORE", "RING_ZERO"])
    def test_ring_zero_old_id_rejected(
        self, store, fake_causal_graph, fake_provenance_chain, ring_zero_id,
    ):
        from core.memory import ImmutableStateError
        from core.truth_maintenance import supersede

        store.store_fact({
            "fact_id": ring_zero_id, "claim": "protected core claim",
            "source": "system", "confidence": 0.99,
            "epistemic_state": "Validated",
        })
        before = store._get_fact_durable(ring_zero_id)

        with pytest.raises(ImmutableStateError):
            supersede(ring_zero_id, _strong_candidate(f"new_from_{ring_zero_id}"))

        after = store._get_fact_durable(ring_zero_id)
        assert after == before, "Ring Zero fact must be completely unchanged"
        assert store.get_fact(f"new_from_{ring_zero_id}") is None
        assert fake_causal_graph.calls == []
        assert fake_provenance_chain.events == []

    def test_ring_zero_check_precedes_durable_read(
        self, store, fake_causal_graph, fake_provenance_chain,
    ):
        """The guard must fire even when no row exists yet at the Ring Zero
        ID — transition_esm()/validate_and_promote() check the ID string
        itself, not the row, and supersede() must match that."""
        from core.memory import ImmutableStateError
        from core.truth_maintenance import supersede

        with pytest.raises(ImmutableStateError):
            supersede("VALUES_CORE", _strong_candidate("new_no_row"))
        assert store.get_fact("new_no_row") is None


# ─── 14. Memory budget parity (Codex review on PR #11, finding #2) ─────────

class TestSupersedeMemoryBudgetParity:
    def test_budget_disabled_allows_supersede(
        self, store, fake_causal_graph, fake_provenance_chain, monkeypatch,
    ):
        import core.memory_budget as mb
        from core.truth_maintenance import supersede

        monkeypatch.setattr(mb, "is_memory_budget_enabled", lambda: False)
        _make_old_fact(store, "old_14a", final_state="Validated")

        result = supersede("old_14a", _strong_candidate("new_14a"))
        assert result == "new_14a"

    def test_budget_enabled_and_allowed(
        self, store, fake_causal_graph, fake_provenance_chain, monkeypatch,
    ):
        import core.memory_budget as mb
        from core.truth_maintenance import supersede

        monkeypatch.setattr(mb, "is_memory_budget_enabled", lambda: True)
        monkeypatch.setattr(
            mb, "evaluate_budget",
            lambda: mb.BudgetStatus(
                fact_count=1, limit=100_000, utilization=0.00001, action="allow",
            ),
        )
        _make_old_fact(store, "old_14b", final_state="Validated")

        result = supersede("old_14b", _strong_candidate("new_14b"))
        assert result == "new_14b"

    def test_hard_limit_rejects_with_no_partial_state(
        self, store, fake_causal_graph, fake_provenance_chain, monkeypatch,
    ):
        import core.memory_budget as mb
        from core.truth_maintenance import supersede

        before = _make_old_fact(store, "old_14c", final_state="Validated")
        monkeypatch.setattr(mb, "is_memory_budget_enabled", lambda: True)
        monkeypatch.setattr(
            mb, "evaluate_budget",
            lambda: mb.BudgetStatus(
                fact_count=100_000, limit=100_000, utilization=1.0,
                action="hard_limit",
            ),
        )

        result = supersede("old_14c", _strong_candidate("new_14c"))

        assert result is None
        after = store._get_fact_durable("old_14c")
        assert after["epistemic_state"] == before["epistemic_state"]
        assert after["updated_at"] == before["updated_at"]
        assert store.get_fact("new_14c") is None
        assert fake_causal_graph.calls == []
        assert fake_provenance_chain.events == []

    def test_hard_limit_checked_before_atomic_transaction(
        self, store, fake_causal_graph, fake_provenance_chain, monkeypatch,
    ):
        """The budget gate must run before supersede_fact_cas() is ever
        called — not merely reject via a rollback after partial writes."""
        import core.memory as memory_mod
        import core.memory_budget as mb
        from core.truth_maintenance import supersede

        _make_old_fact(store, "old_14d", final_state="Validated")
        monkeypatch.setattr(mb, "is_memory_budget_enabled", lambda: True)
        monkeypatch.setattr(
            mb, "evaluate_budget",
            lambda: mb.BudgetStatus(
                fact_count=100_000, limit=100_000, utilization=1.0,
                action="hard_limit",
            ),
        )

        called = {"n": 0}
        original = memory_mod.SQLiteGraphStore.supersede_fact_cas

        def _counting_cas(self, *args, **kwargs):
            called["n"] += 1
            return original(self, *args, **kwargs)

        monkeypatch.setattr(
            memory_mod.SQLiteGraphStore, "supersede_fact_cas", _counting_cas,
        )

        result = supersede("old_14d", _strong_candidate("new_14d"))

        assert result is None
        assert called["n"] == 0, "atomic transaction must not run when budget is exceeded"


# ─── 15. Claim classification parity (Codex review on PR #11, finding #3) ──

class TestSupersedeClaimClassificationParity:
    def test_omitted_claim_type_classified_as_world_fact(
        self, store, fake_causal_graph, fake_provenance_chain,
    ):
        """An external world claim with no explicit claim_type/origin_type
        must classify the same way store_fact() would — WORLD_FACT/EXTERNAL
        — not default to UNKNOWN."""
        from core.truth_maintenance import supersede

        _make_old_fact(store, "old_15a", final_state="Validated")
        candidate = {
            "fact_id": "new_15a",
            "claim": "Вода кипит при 100°C",
            "source": "physics.thermo",
            "confidence": 0.95,
            "metadata": {"evidence_refs": ["a", "b", "c", "d", "e"]},
        }

        result = supersede("old_15a", candidate)

        assert result == "new_15a"
        new_fact = store._get_fact_durable("new_15a")
        assert new_fact["claim_type"] == "WORLD_FACT"
        assert new_fact["origin_type"] == "EXTERNAL"

    def test_verified_truth_policy_precondition_preserved(
        self, store, fake_causal_graph, fake_provenance_chain,
    ):
        """core/pipeline.py's ENABLE_TRUTH_POLICY branch marks a fact
        VERIFIED iff epistemic_state == 'Validated' and claim_type ==
        'WORLD_FACT' (see pipeline.py's ESM-promotion step). A superseded
        external world fact must still satisfy both, not silently regress
        to claim_type=UNKNOWN and lose VERIFIED semantics."""
        from core.truth_maintenance import supersede

        _make_old_fact(store, "old_15b", final_state="Validated")
        candidate = {
            "fact_id": "new_15b",
            "claim": "Дерево горит на воздухе",
            "source": "chemistry.combustion",
            "confidence": 0.95,
            "metadata": {"evidence_refs": ["a", "b", "c", "d", "e"]},
        }

        result = supersede("old_15b", candidate)
        assert result == "new_15b"

        new_fact = store._get_fact_durable("new_15b")
        would_be_verified = (
            new_fact["epistemic_state"] == "Validated"
            and new_fact.get("claim_type") == "WORLD_FACT"
        )
        assert would_be_verified, (
            f"superseded fact would be UNVERIFIED under ENABLE_TRUTH_POLICY: "
            f"epistemic_state={new_fact['epistemic_state']!r}, "
            f"claim_type={new_fact.get('claim_type')!r}"
        )

    def test_explicit_claim_type_preserved(
        self, store, fake_causal_graph, fake_provenance_chain,
    ):
        """An explicit, valid claim_type/origin_type must win over the
        classifier (classify_claim()'s own contract, reused as-is)."""
        from core.truth_maintenance import supersede

        _make_old_fact(store, "old_15c", final_state="Validated")
        candidate = _strong_candidate("new_15c")
        candidate["claim_type"] = "OPINION"
        candidate["origin_type"] = "USER_REPORTED"

        result = supersede("old_15c", candidate)

        assert result == "new_15c"
        new_fact = store._get_fact_durable("new_15c")
        assert new_fact["claim_type"] == "OPINION"
        assert new_fact["origin_type"] == "USER_REPORTED"


# ─── 16. Domain tagging parity (Codex review on PR #11, finding #4) ────────

class TestSupersedeDomainTaggingParity:
    def test_replacement_gets_domain_metadata_and_is_domain_readable(
        self, store, fake_causal_graph, fake_provenance_chain,
    ):
        """With ENABLE_DOMAIN_TAGS (default ON), a replacement with no
        explicit metadata.domain must still be tagged the same way
        store_fact() would tag it, and remain visible to domain-scoped
        reads such as get_all_facts(domain=...)."""
        from core.truth_maintenance import supersede

        _make_old_fact(store, "old_16a", final_state="Validated")
        candidate = _strong_candidate("new_16a")
        assert "domain" not in candidate["metadata"]

        result = supersede("old_16a", candidate)
        assert result == "new_16a"

        new_fact = store._get_fact_durable("new_16a")
        assert new_fact["metadata"].get("domain"), (
            "replacement fact is missing domain metadata store_fact() would "
            "have attached"
        )
        assert new_fact["metadata"].get("content_domain") == new_fact["metadata"].get("domain")

        domain = new_fact["metadata"]["domain"]
        domain_facts = store.get_all_facts(domain=domain)
        assert any(f["fact_id"] == "new_16a" for f in domain_facts), (
            "replacement fact is not visible to a domain-scoped read"
        )

    def test_explicit_domain_preserved(
        self, store, fake_causal_graph, fake_provenance_chain,
    ):
        from core.truth_maintenance import supersede

        _make_old_fact(store, "old_16b", final_state="Validated")
        candidate = _strong_candidate("new_16b")
        candidate["metadata"]["domain"] = "science"

        result = supersede("old_16b", candidate)
        assert result == "new_16b"

        new_fact = store._get_fact_durable("new_16b")
        assert new_fact["metadata"]["domain"] == "science"
        domain_facts = store.get_all_facts(domain="science")
        assert any(f["fact_id"] == "new_16b" for f in domain_facts)


# ─── 17. WriteGate parity (Codex review on PR #11, finding #5) ─────────────

class TestSupersedeWriteGateParity:
    def test_legacy_gate_disable_cannot_promote_world_fact_without_source(
        self, store, fake_causal_graph, fake_provenance_chain, monkeypatch,
    ):
        import core.write_gate as wg
        from core.truth_maintenance import supersede

        monkeypatch.setattr(wg, "is_write_gate_enabled", lambda: False)
        _make_old_fact(store, "old_17a", final_state="Validated")
        candidate = _strong_candidate("new_17a")
        candidate["claim_type"] = "WORLD_FACT"
        candidate["origin_type"] = "EXTERNAL"
        candidate["source"] = "unknown"

        result = supersede("old_17a", candidate)
        assert result is None
        assert store.get_fact("new_17a") is None
        assert store.get_fact("old_17a")["epistemic_state"] == "Validated"

    def test_gate_enabled_valid_candidate_accepted(
        self, store, fake_causal_graph, fake_provenance_chain, monkeypatch,
    ):
        import core.write_gate as wg
        from core.truth_maintenance import supersede

        monkeypatch.setattr(wg, "is_write_gate_enabled", lambda: True)
        _make_old_fact(store, "old_17b", final_state="Validated")
        candidate = _strong_candidate("new_17b")
        candidate["claim_type"] = "WORLD_FACT"
        candidate["origin_type"] = "EXTERNAL"

        result = supersede("old_17b", candidate)
        assert result == "new_17b"

    def test_gate_enabled_world_fact_unknown_source_rejected(
        self, store, fake_causal_graph, fake_provenance_chain, monkeypatch,
    ):
        import core.write_gate as wg
        from core.truth_maintenance import supersede

        monkeypatch.setattr(wg, "is_write_gate_enabled", lambda: True)
        before = _make_old_fact(store, "old_17c", final_state="Validated")
        candidate = _strong_candidate("new_17c")
        candidate["claim_type"] = "WORLD_FACT"
        candidate["origin_type"] = "EXTERNAL"
        candidate["source"] = "unknown"

        result = supersede("old_17c", candidate)

        assert result is None
        after = store._get_fact_durable("old_17c")
        assert after["epistemic_state"] == before["epistemic_state"]
        assert after["updated_at"] == before["updated_at"]
        assert store.get_fact("new_17c") is None
        assert fake_causal_graph.calls == []
        assert fake_provenance_chain.events == []

    def test_gate_enabled_runs_before_truthgate(
        self, store, fake_causal_graph, fake_provenance_chain, monkeypatch,
    ):
        """WriteGate must run before TruthGate.evaluate() — a rejected
        candidate must never reach the TruthGate call at all."""
        import core.write_gate as wg
        from core.truth_gate import TruthGate
        from core.truth_maintenance import supersede

        monkeypatch.setattr(wg, "is_write_gate_enabled", lambda: True)
        _make_old_fact(store, "old_17d", final_state="Validated")
        candidate = _strong_candidate("new_17d")
        candidate["claim_type"] = "WORLD_FACT"
        candidate["origin_type"] = "EXTERNAL"
        candidate["source"] = "unknown"

        called = {"n": 0}
        original_evaluate = TruthGate.evaluate

        def _counting_evaluate(self, *args, **kwargs):
            called["n"] += 1
            return original_evaluate(self, *args, **kwargs)

        monkeypatch.setattr(TruthGate, "evaluate", _counting_evaluate)

        result = supersede("old_17d", candidate)

        assert result is None
        assert called["n"] == 0, "TruthGate.evaluate() must not run when WriteGate rejects"
