# core/erasure.py
# VELANTRIM Titan — Right to Erasure (GDPR Art. 17)
#
# Physical deletion of a fact across Titan's memory fabrics + accountability.
# Adapted from the Crystal open core to Titan's SQLite storage layer.
#
# Principle: deletion must be COMPLETE and PROVABLE at the same time.
#   Complete — the fact disappears from L0 (LRU cache) and L1 (SQLite `facts`)
#             together with every dependent row: relations (both directions),
#             living context, affordances, L0 provenance links, and the FTS
#             index. No personal data or dangling references remain.
#   Provable — a content-free tombstone is written to `erasure_log`: fact_id,
#             time, reason, actor and sha256(claim) — never the claim itself.
#             This is a record of processing (Art. 30): one can prove WHAT and
#             WHEN was deleted without recreating what was erased.
#
# Ring Zero / VALUES_CORE are NOT deletable (invariant I6): they are system
# values, not personal data.
#
# LIMITATION (honest, Phase-1 follow-up): the immutable L0 raw store
# (l0_raw_memory) is append-only by design — anti-drift triggers forbid DELETE.
# Raw originals are therefore NOT physically erased in this version; the derived
# (interpreted) fact layer IS fully erased. Full raw erasure needs an explicit,
# audited invariant exception and is tracked separately. See docs/LIMITATIONS.md.

import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List

from core.memory import (
    get_fact,
    delete_fact_l1,
    write_tombstone,
    get_tombstone,
    get_tombstones,
    IMMUTABLE_FACT_IDS,
    ImmutableStateError,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash_claim(claim: str) -> str:
    """Hash of the erased claim — proof of WHAT was erased without storing it."""
    return "sha256:" + hashlib.sha256(claim.encode("utf-8")).hexdigest()


def erase_fact(
    fact_id: str,
    *,
    reason: str = "data_subject_request",
    actor: str = "operator",
) -> Dict[str, Any]:
    """
    Physically and irreversibly delete a fact (GDPR Art. 17, right to be forgotten).

    Removes the fact from L0 + L1 and all dependent rows, then writes a
    content-free tombstone to erasure_log.

    Ring Zero / VALUES_CORE are non-deletable (I6) → ImmutableStateError.

    Idempotent: re-erasing an already-erased fact returns erased_now=False and
    does not duplicate the tombstone (the first erasure is the record).
    """
    if fact_id in IMMUTABLE_FACT_IDS:
        raise ImmutableStateError(
            f"erase_fact: '{fact_id}' is protected by Ring Zero (I6) and cannot be deleted"
        )

    fact = get_fact(fact_id)
    content_hash = _hash_claim(fact["claim"]) if fact and fact.get("claim") else None

    erased_now = delete_fact_l1(fact_id)

    # Immutable tombstone: first erasure wins, hash preserved on repeats.
    write_tombstone(fact_id, reason=reason, actor=actor, content_hash=content_hash)
    tombstone = get_tombstone(fact_id)

    return {
        "fact_id": fact_id,
        "erased_now": erased_now,
        "reason": reason,
        "actor": actor,
        "content_hash": (tombstone or {}).get("content_hash"),
        "erased_at": (tombstone or {}).get("erased_at", _now()),
    }


def is_erased(fact_id: str) -> bool:
    """True if a tombstone exists for the fact (it was erased)."""
    return get_tombstone(fact_id) is not None


def erasure_log() -> List[Dict[str, Any]]:
    """
    Log of all erasures (Art. 30, record of processing). Content-free:
    fact_id / time / reason / actor / hash — no personal data.
    """
    return get_tombstones()
