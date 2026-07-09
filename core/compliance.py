# core/compliance.py
# VELANTRIM Titan — GDPR Compliance Operations (Art. 18 restriction + Art. 30 RoPA)
# Adapted from the Crystal open core to Titan's SQLite storage.
#
#   Art. 18 — restriction of processing: restrict_processing() "freezes" a fact —
#     it stays stored but is excluded from recall / answers (see
#     core/memory.py get_facts_by_ids, which drops facts flagged
#     metadata.restricted). Reversible via unrestrict_processing(). Not a
#     deletion, not an ESM state change.
#
#   Art. 30 — record of processing: record_of_processing() builds an aggregate,
#     content-free report (counts by category / state, restrictions, erasures,
#     configuration). No personal data (claim) is included — only counters,
#     identifiers and config.
#
# NOTE (honest): restriction exclusion is wired into get_facts_by_ids — the
# primary recall materialisation used by the pipeline. Other query surfaces
# (search / hybrid_retriever direct paths) are a documented follow-up.

import os
from collections import Counter
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from core.memory import set_restricted, get_fact, get_all_facts, get_tombstones
from core import pii, crypto


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def restrict_processing(
    fact_id: str, *, reason: str = "data_subject_request", actor: str = "operator",
) -> Dict[str, Any]:
    """Restrict processing of a fact (GDPR Art. 18). found=False if it is absent."""
    found = set_restricted(fact_id, True)
    return {"fact_id": fact_id, "restricted": True, "found": found,
            "reason": reason, "actor": actor, "at": _now()}


def unrestrict_processing(fact_id: str, *, actor: str = "operator") -> Dict[str, Any]:
    """Lift the processing restriction (Art. 18) — the fact rejoins recall."""
    found = set_restricted(fact_id, False)
    return {"fact_id": fact_id, "restricted": False, "found": found,
            "actor": actor, "at": _now()}


def _is_restricted_fact(fact: Optional[Dict[str, Any]]) -> bool:
    return bool(fact and (fact.get("metadata") or {}).get("restricted"))


def is_restricted(fact_id: str) -> bool:
    """True if processing of the fact is restricted (Art. 18)."""
    return _is_restricted_fact(get_fact(fact_id))


def restricted_facts() -> List[str]:
    """fact_ids of all facts under a processing restriction."""
    return [f["fact_id"] for f in get_all_facts() if _is_restricted_fact(f)]


def record_of_processing(controller: Optional[str] = None) -> Dict[str, Any]:
    """
    Build a record of processing (GDPR Art. 30): an aggregate, content-free
    report. Contains no personal data (claim) — only counters, identifiers and
    configuration.
    """
    facts = get_all_facts()  # full view (NOT recall-filtered) — RoPA must see all
    by_claim_type = Counter(f.get("claim_type", "UNKNOWN") for f in facts)
    by_state = Counter(f.get("epistemic_state", "Observed") for f in facts)
    restricted = [f["fact_id"] for f in facts if _is_restricted_fact(f)]
    erasures = get_tombstones()

    backend = os.environ.get(
        "STORAGE_BACKEND", os.environ.get("VELANTRIM_L3_BACKEND", "sqlite"))

    return {
        "generated_at": _now(),
        "regulation": "GDPR (EU) 2016/679, Art. 30",
        "controller": controller or os.environ.get(
            "VELANTRIM_CONTROLLER", "(operator-defined)"),
        "processing_purpose": (
            "Verifiable AI memory: storage and provenance-tracked retrieval of "
            "facts for trustworthy AI systems"),
        "data_location": (
            "local: L1 (SQLite). No third-party transfer in the default "
            "configuration."),
        "backends": {"storage": backend},
        "pii_redaction_at_ingest": pii.redaction_enabled(),
        "encryption_at_rest": crypto.is_enabled(),
        "encryption_backend": crypto.backend_name(),
        "fact_count": len(facts),
        "categories_of_data": dict(by_claim_type),
        "by_epistemic_state": dict(by_state),
        "restricted_count": len(restricted),
        "restricted_fact_ids": restricted,
        "erasure_count": len(erasures),
        "erasure_log": erasures,
        "data_subject_rights": {
            "access": "memory.get_all_facts (Art. 15)",
            "erasure": "erasure.erase_fact (Art. 17)",
            "restriction": "compliance.restrict_processing (Art. 18)",
            "data_minimisation": "pii.redact at ingest (Art. 5(1)(c))",
        },
        "security_measures": [
            "single-entry TruthGate (Graph = Truth, I1)",
            "Ring Zero immutability (I6)",
            "validated ESM transitions",
            "content-free erasure tombstones (Art. 17/30)",
            "no telemetry; no outbound calls by default",
        ],
    }
