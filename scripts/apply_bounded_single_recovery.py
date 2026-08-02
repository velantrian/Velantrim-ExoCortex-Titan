#!/usr/bin/env python3
"""One-shot exact patch for bounded single-fact recovery; removed before PR."""

from __future__ import annotations

from pathlib import Path


PATH = Path("core/erasure_coordinator.py")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one target, found {count}")
    return text.replace(old, new)


def main() -> int:
    text = PATH.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "from typing import TYPE_CHECKING, Any\n",
        "from typing import TYPE_CHECKING, Any, Callable\n",
        "typing import",
    )
    text = replace_once(
        text,
        "from core import memory\nfrom core.ngram_index import NGramIndex, get_global_ngram\n",
        "from core import memory\nfrom core.erasure_startup_recovery import RecoveryDomain, RecoveryDomainReceipt\nfrom core.ngram_index import NGramIndex, get_global_ngram\n",
        "contract import",
    )

    old_method = '''    def resume_incomplete_jobs(self) -> list[dict[str, Any]]:
        """Crash recovery sweep: re-run every job not in a terminal state.
'''
    new_method = '''    def resume_incomplete_jobs_bounded(
        self,
        *,
        max_jobs: int,
        deadline_monotonic: float,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> tuple[RecoveryDomainReceipt, bool]:
        """Run a deterministic bounded prefix of resumable single-fact jobs.

        This is the startup-safe counterpart to ``resume_incomplete_jobs()``.
        It reuses the same tombstone reconciliation and CAS claim paths, but
        limits the initial candidate set and stops between jobs when the shared
        monotonic deadline is reached. Unexpected DB/schema exceptions remain
        visible to the caller so the aggregate startup runner can emit an
        ``OBSERVER_FAILED`` receipt instead of inventing measured counters.

        ``remaining_backlog`` is measured after execution from current durable
        resumable rows, excluding jobs already represented by completed,
        partial, or failed outcomes in this receipt. Selected-but-unattempted
        jobs are conservatively retained even if a concurrent actor completed
        them before the post-run count, preserving fail-closed accounting.
        """
        if (
            isinstance(max_jobs, bool)
            or not isinstance(max_jobs, int)
            or max_jobs < 0
        ):
            raise ValueError("max_jobs must be a non-negative integer")
        if isinstance(deadline_monotonic, bool) or not isinstance(
            deadline_monotonic, (int, float)
        ):
            raise ValueError("deadline_monotonic must be numeric")

        with self._jobs_db() as conn:
            placeholders = ", ".join("?" for _ in _RESUMABLE_STATUSES)
            rows = conn.execute(
                f"SELECT job_id FROM erasure_jobs "  # noqa: S608
                f"WHERE status IN ({placeholders}) "
                "ORDER BY created_at, job_id LIMIT ?",
                (*_RESUMABLE_STATUSES, max_jobs),
            ).fetchall()

        selected_ids = [str(row["job_id"]) for row in rows]
        attempted = 0
        completed = 0
        partial = 0
        failed = 0
        skipped = 0
        accounted_ids: list[str] = []
        stopped_by_time_budget = False

        for job_id in selected_ids:
            if monotonic() >= float(deadline_monotonic):
                stopped_by_time_budget = True
                break
            attempted += 1
            reconciled = self._reconcile_completed_job_from_tombstone(job_id)
            result = (
                reconciled
                if reconciled is not None
                else self._run_job(job_id, wait_if_running=False)
            )
            if result is None:
                skipped += 1
                continue

            accounted_ids.append(job_id)
            outcome = str(result.get("outcome") or "")
            if outcome == COMPLETE:
                completed += 1
            elif outcome == FAILED:
                failed += 1
            else:
                partial += 1

        with self._jobs_db() as conn:
            status_placeholders = ", ".join("?" for _ in _RESUMABLE_STATUSES)
            if accounted_ids:
                id_placeholders = ", ".join("?" for _ in accounted_ids)
                row = conn.execute(
                    f"SELECT COUNT(*) AS count FROM erasure_jobs "  # noqa: S608
                    f"WHERE status IN ({status_placeholders}) "
                    f"AND job_id NOT IN ({id_placeholders})",
                    (*_RESUMABLE_STATUSES, *accounted_ids),
                ).fetchone()
            else:
                row = conn.execute(
                    f"SELECT COUNT(*) AS count FROM erasure_jobs "  # noqa: S608
                    f"WHERE status IN ({status_placeholders})",
                    _RESUMABLE_STATUSES,
                ).fetchone()

        durable_backlog = int(row["count"] if row is not None else 0)
        selected_but_unattempted = len(selected_ids) - attempted
        remaining_backlog = max(durable_backlog, selected_but_unattempted)
        error_codes = (
            ("single_fact_recovery_failed",) if failed > 0 else ()
        )
        receipt = RecoveryDomainReceipt(
            domain=RecoveryDomain.SINGLE_FACT,
            selected=len(selected_ids),
            attempted=attempted,
            completed=completed,
            partial=partial,
            failed=failed,
            skipped=skipped,
            remaining_backlog=remaining_backlog,
            error_codes=error_codes,
        )
        return receipt, stopped_by_time_budget

    def resume_incomplete_jobs(self) -> list[dict[str, Any]]:
        """Crash recovery sweep: re-run every job not in a terminal state.
'''
    text = replace_once(text, old_method, new_method, "bounded method")

    old_wrapper = '''def resume_incomplete_jobs() -> list[dict[str, Any]]:
    return get_coordinator().resume_incomplete_jobs()
'''
    new_wrapper = '''def resume_incomplete_jobs_bounded(
    *,
    max_jobs: int,
    deadline_monotonic: float,
    monotonic: Callable[[], float] = time.monotonic,
) -> tuple[RecoveryDomainReceipt, bool]:
    return get_coordinator().resume_incomplete_jobs_bounded(
        max_jobs=max_jobs,
        deadline_monotonic=deadline_monotonic,
        monotonic=monotonic,
    )


def resume_incomplete_jobs() -> list[dict[str, Any]]:
    return get_coordinator().resume_incomplete_jobs()
'''
    text = replace_once(text, old_wrapper, new_wrapper, "module wrapper")
    text = replace_once(
        text,
        '    "resume_incomplete_jobs",\n',
        '    "resume_incomplete_jobs_bounded",\n    "resume_incomplete_jobs",\n',
        "all export",
    )
    PATH.write_text(text, encoding="utf-8")
    print("Applied bounded single-fact recovery API")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
