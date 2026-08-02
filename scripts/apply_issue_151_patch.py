#!/usr/bin/env python3
"""One-shot exact test-gate patch for issue #151; removed before PR creation."""

from __future__ import annotations

from pathlib import Path
import re


PATH = Path("tests/test_audit_chain_transition_ledger.py")
PATTERN = re.compile(
    r"class TestConcurrentWritersNoForkNoDuplicate:.*?\n\nclass TestRetrySemantics:",
    re.DOTALL,
)
REPLACEMENT = '''class TestConcurrentWritersNoForkNoDuplicate:
    def test_two_real_threads_same_fact_exactly_one_event_each_no_fork(self, migrated_store):
        store = migrated_store
        fid = "f_concurrent"
        _seed_fact_bypassing_audit(store, fid)
        store.transition_esm(fid, "Hypothesized", by="truth_gate")
        chain_id = _chain_id_for(store, fid)

        # Synchronize the exact stale-snapshot boundary that the CAS protects.
        # transition_esm() performs one _l0_get() through get_fact(), then
        # update_state() performs a second _l0_get() before entering the
        # CAS-guarded database transaction. Both writers must capture that
        # same second preimage before either writer is allowed to commit.
        stale_preimage_barrier = threading.Barrier(2)
        per_thread = threading.local()
        real_l0_get = store._l0_get
        results: dict[str, bool] = {}
        errors: list[BaseException] = []

        def _gated_l0_get(fact_id):
            value = real_l0_get(fact_id)
            call_count = getattr(per_thread, "l0_reads", 0) + 1
            per_thread.l0_reads = call_count
            if fact_id == fid and call_count == 2:
                stale_preimage_barrier.wait(timeout=5)
            return value

        store._l0_get = _gated_l0_get

        def _writer(name: str, state: str, actor: str) -> None:
            try:
                results[name] = store.transition_esm(fid, state, by=actor)
            except BaseException as exc:  # pragma: no cover - asserted below
                errors.append(exc)

        t_a = threading.Thread(
            target=_writer,
            args=("a", "Supported", "truth_gate"),
        )
        t_b = threading.Thread(
            target=_writer,
            args=("b", "Contradicted", "contradiction_resolver"),
        )
        try:
            t_a.start()
            t_b.start()
            t_a.join(timeout=10)
            t_b.join(timeout=10)
        finally:
            store._l0_get = real_l0_get

        assert not t_a.is_alive() and not t_b.is_alive(), "writers must terminate"
        assert errors == []
        assert sorted(results.values()) == [False, True]

        rows = _events(store, chain_id)
        # Exactly one of Supported/Contradicted wins the CAS from the same
        # Hypothesized preimage, so one event is added beyond the seed event.
        assert len(rows) == 2, (
            f"expected 2 events total (1 initial + 1 winner), got {len(rows)}"
        )
        to_states = [r["to_state"] for r in rows]
        assert to_states[0] == "Hypothesized"
        assert to_states[1] in ("Supported", "Contradicted")
        sequences = [r["chain_sequence"] for r in rows]
        assert sequences == sorted(set(sequences)), (
            "chain_sequence must be strictly increasing, no fork"
        )


class TestRetrySemantics:'''


def main() -> int:
    text = PATH.read_text(encoding="utf-8")
    updated, count = PATTERN.subn(REPLACEMENT, text)
    if count != 1:
        raise SystemExit(f"expected exactly one issue-151 target, found {count}")
    PATH.write_text(updated, encoding="utf-8")
    print("Applied issue #151 deterministic AuditChain test gate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
