"""One-shot exact patch helper for the recovery single-winner hotfix.

This file is deleted by the workflow in the same commit that applies the
source/test changes. It must never reach the pull-request diff.
"""

from pathlib import Path


source_path = Path("core/erasure_batch_coordinator.py")
source = source_path.read_text(encoding="utf-8")
old = "\n".join(
    [
        "        if not claimed:",
        "            current = self._load_batch(batch_id)",
        "            if current[\"status\"] in _TERMINAL_BATCH_STATUSES:",
        "                return self._report(current, self._load_items(batch_id))",
        "            if wait_if_running:",
        "                return self._wait_for_batch_completion(batch_id)",
        "            return None",
    ]
) + "\n"
new = "\n".join(
    [
        "        if not claimed:",
        "            if not wait_if_running:",
        "                # A recovery sweep reports only work this worker actually",
        "                # claimed. The winning worker may have completed the batch",
        "                # between candidate selection and this failed CAS; returning",
        "                # its terminal report here would make the loser falsely",
        "                # appear to have processed the batch as well.",
        "                return None",
        "            current = self._load_batch(batch_id)",
        "            if current[\"status\"] in _TERMINAL_BATCH_STATUSES:",
        "                return self._report(current, self._load_items(batch_id))",
        "            return self._wait_for_batch_completion(batch_id)",
    ]
) + "\n"
if source.count(old) != 1:
    raise SystemExit(f"expected one source match, found {source.count(old)}")
source_path.write_text(source.replace(old, new), encoding="utf-8")


test_path = Path("tests/test_erasure_batch_coordinator.py")
tests = test_path.read_text(encoding="utf-8")
marker = "\n\n# ── Idempotency ──────────────────────────────────────────────────────────\n"
regression = '''

def test_recovery_claim_loser_does_not_report_winner_terminal_result(rig, monkeypatch):
    """A recovery worker that loses the batch CAS returns no result,
    even when the winner reaches a terminal state before the loser
    observes the row. Live/idempotent callers still get cached readback.
    """
    batch, coordinator, store, *_ = rig
    store.store_fact(_fact("f1"))
    batch_id = batch._create_batch_snapshot(
        user_id="userA", reason="dsr", actor="tester", force=False,
        scope=None, idempotency_key=None, actor_capability="reader",
        request_fingerprint="fp-deterministic-recovery-loser",
    )
    with sqlite3.connect(store.db_path) as conn:
        conn.execute(
            "UPDATE erasure_batch_items SET status = ? WHERE batch_id = ?",
            (COMPLETE, batch_id),
        )
        conn.execute(
            "UPDATE erasure_batches SET status = ?, runner_id = ?, "
            "lease_expires_at = NULL WHERE batch_id = ?",
            (COMPLETE, "winning-runner", batch_id),
        )
        conn.commit()

    worker = BatchErasureCoordinator(store=store, coordinator=coordinator)
    monkeypatch.setattr(
        worker,
        "_claim_batch_for_running",
        lambda *args, **kwargs: False,
    )

    assert worker._run_batch(batch_id, wait_if_running=False) is None
    cached = worker._run_batch(batch_id, wait_if_running=True)
    assert cached is not None
    assert cached["batch_id"] == batch_id
    assert cached["outcome"] == COMPLETE
'''
if tests.count(marker) != 1:
    raise SystemExit(f"expected one test marker, found {tests.count(marker)}")
test_path.write_text(tests.replace(marker, regression + marker), encoding="utf-8")
