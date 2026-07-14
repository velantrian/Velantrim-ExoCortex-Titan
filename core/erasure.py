# core/erasure.py
# VELANTRIM Titan — Right to Erasure (GDPR Art. 17)
#
# DEPRECATED (P0-B): this module's erase_fact() used to run its own
# single-pass, single-DB deletion and unconditionally write a tombstone
# regardless of whether that deletion actually succeeded — it could not
# prove anything once a fact's data spans three independent SQLite files
# (facts, embeddings, ngram) and could not recover from a crash mid-erasure.
#
# The enforced entrypoint is now core.erasure_coordinator.erase_fact_durable()
# — a durable, resumable saga (erasure_jobs / erasure_job_steps) that proves
# deletion per dependent table and per storage backend, and only ever writes
# the completion tombstone when every step is provably COMPLETE. See
# core/erasure_coordinator.py for the full design rationale.
#
# The functions below are kept ONLY so pre-existing callers/imports don't
# break at import time; every one of them delegates to the coordinator — none
# of them re-implements deletion logic. ToolRegistry does NOT register these;
# it registers core.erasure_coordinator.erase_fact_durable directly, so no
# production tool call can reach this shim.
#
# Ring Zero / VALUES_CORE are NOT deletable (invariant I6): they are system
# values, not personal data.
#
# LIMITATION (honest, tracked separately): the immutable L0 raw store
# (l0_raw_memory) is append-only by design — anti-drift triggers forbid DELETE.
# Raw originals are therefore NOT physically erased by this or any erasure
# path; the derived (interpreted) fact layer IS fully erased. See
# docs/LIMITATIONS.md. The coordinator surfaces this as `residual` on its
# report ("raw_original_present") rather than silently reporting COMPLETE.

import warnings
from typing import Any, Dict, List

from core.erasure_coordinator import erase_fact_durable, erasure_log as _erasure_log, is_erased as _is_erased


def erase_fact(
    fact_id: str,
    *,
    reason: str = "data_subject_request",
    actor: str = "operator",
) -> Dict[str, Any]:
    """DEPRECATED — delegates to core.erasure_coordinator.erase_fact_durable().

    Kept for backward compatibility only. New code (and all production
    tools) must call erase_fact_durable() directly to get the full job
    report (outcome/residual/steps); this shim narrows that down to the
    legacy result shape.
    """
    warnings.warn(
        "core.erasure.erase_fact() is deprecated — use "
        "core.erasure_coordinator.erase_fact_durable() directly.",
        DeprecationWarning,
        stacklevel=2,
    )
    report = erase_fact_durable(fact_id, reason=reason, actor=actor)
    return {
        "fact_id": report["fact_id"],
        "erased_now": report["erased_now"],
        "reason": report["reason"],
        "actor": report["actor"],
        "content_hash": report["content_hash"],
        "erased_at": report["erased_at"],
        "outcome": report["outcome"],
        "residual": report["residual"],
    }


def is_erased(fact_id: str) -> bool:
    """DEPRECATED — delegates to core.erasure_coordinator.is_erased()."""
    return _is_erased(fact_id)


def erasure_log() -> List[Dict[str, Any]]:
    """DEPRECATED — delegates to core.erasure_coordinator.erasure_log()."""
    return _erasure_log()
