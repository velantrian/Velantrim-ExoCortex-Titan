"""
📚 core/world_skills_ingest.py — World Skills Core parsing and bounded admission.

Transforms curated markdown tables under ``docs/knowledge/world_skills_core/ru`` into
WORLD_FACT candidates plus typed causal-edge inputs. Markdown remains read-only and the
caller supplies the target store; this module does not select the canonical Titan DB.

C9 / #52 changes the historical curated-pack exception: parsed rows no longer become
``Validated`` merely because they came from World Skills. Legacy rows are explicit Draft
candidates and remain quarantined unless they carry attributable provenance, risk,
limitations, and review metadata. Canon admission reuses the existing TruthGate,
PromotionGateway, legal ESM ladder, and CAS mutation owner. No LLM is involved.
"""
from __future__ import annotations

import glob
import hashlib
import json
import logging
import math
import os
import re
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from core.promotion_gateway import PromotionGateway, PromotionRequest
from core.truth_gate import CognitiveMode, TruthGate

logger = logging.getLogger(__name__)

DEFAULT_KNOWLEDGE_DIR = "docs/knowledge/world_skills_core/ru"
FACT_ID_RE = re.compile(r"^[a-z0-9_]+(?:\.[a-z0-9_]+)+$")
WORLD_SKILLS_ADMISSION_CONTRACT = "world-skills-admission-v1"
WORLD_SKILLS_ADMISSION_ACTOR = "world_skills_ingest"

# Explicit risk metadata chooses only an existing TruthGate mode. It never changes
# TruthGate thresholds. Unknown/non-high-risk labels remain BALANCED; explicit high-risk
# labels are promoted only under the stricter existing PRECISION mode.
_HIGH_RISK_TOKENS = frozenset({
    "chemical",
    "chemistry",
    "financial",
    "finance",
    "health",
    "identity",
    "law",
    "legal",
    "medical",
    "medicine",
    "safety",
    "security",
    "биобезопасность",
    "безопасность",
    "здоровье",
    "медицина",
    "право",
    "финансы",
})

# Не-факт документы (карты/охват/протокол) — у них нет таблицы KnowledgeUnit-фактов.
_NON_FACT_FILES = frozenset({
    "00_WORLD_SKILLS_CORE_MAP.ru.md",
    "00_CURATED_CAUSAL_RELATIONS.ru.md",
    "10_PRACTICAL_FULL_SCOPE_MAP.ru.md",
    "11_AGRO_TEXTILE_INDUSTRY_ECONOMY_SCOPE.ru.md",
    "12_50K_COLLECTION_PROTOCOL.ru.md",
    "99_SOURCE_RULES_AND_COLLECTION_PLAN.ru.md",
})


class WorldSkillAdmissionStage(str, Enum):
    """Machine-readable stages from parent issue #52."""

    DRAFT = "Draft"
    QUARANTINE = "Quarantine"
    PROVENANCE_CHECK = "Provenance Check"
    DOMAIN_REVIEW = "Domain Review"
    TRUTH_GATE = "Truth Gate"
    CANON = "Canon"


@dataclass(frozen=True, slots=True)
class WorldSkillAdmissionDecision:
    """Fail-closed pre-admission result; no mutation authority is carried here."""

    stage: WorldSkillAdmissionStage
    passed: bool
    reason_code: str
    mode: CognitiveMode | None = None


def split_markdown_table_row(line: str) -> list[str]:
    """Split a markdown row without treating code-span or escaped pipes as columns."""
    row = line.strip()
    if not row.startswith("|"):
        return []
    cells: list[str] = []
    current: list[str] = []
    in_code = False
    escaped = False
    for char in row[1:]:
        if escaped:
            current.append(char)
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == "`":
            in_code = not in_code
            current.append(char)
        elif char == "|" and not in_code:
            cells.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    if current:
        cells.append("".join(current).strip())
    return cells


def _header_index(low: list[str], *names: str) -> int | None:
    wanted = {name.lower() for name in names}
    return next((i for i, cell in enumerate(low) if cell in wanted), None)


def _parse_source_refs(value: str) -> list[str]:
    """Parse semicolon-delimited source references without inventing provenance."""
    return [part.strip() for part in value.split(";") if part.strip()]


def _parse_confidence(value: str, *, fallback: float = 0.85) -> float:
    if not value.strip():
        return fallback
    try:
        parsed = float(value)
    except ValueError:
        return 0.0
    return parsed if math.isfinite(parsed) else 0.0


def parse_batch_markdown(text: str) -> list[dict[str, Any]]:
    """Parse a World Skills markdown table into candidate fact dictionaries.

    Legacy tables do not contain the C9 admission fields. They therefore receive safe
    non-claims: ``truth_status=Draft``, empty provenance/review/risk fields, and cannot
    pass admission. Enriched tables may provide the exact #52 fields as additional
    columns. Missing data is never inferred from a file name, claim text, or LLM.
    """
    facts: list[dict[str, Any]] = []
    seen: set[str] = set()
    claim_idx: int = 2
    type_idx: int = 1
    unit_idx: int | None = None
    conditions_idx: int | None = 3
    links_idx: int | None = 4
    practical_idx: int | None = None
    causes_idx: int | None = None
    enables_idx: int | None = None
    requires_idx: int | None = None
    prevents_idx: int | None = None
    depends_idx: int | None = None
    evidence_idx: int | None = None
    rel_conf_idx: int | None = None
    truth_status_idx: int | None = None
    source_refs_idx: int | None = None
    confidence_idx: int | None = None
    risk_domain_idx: int | None = None
    limitations_idx: int | None = None
    review_status_idx: int | None = None
    reviewer_idx: int | None = None
    reviewed_at_idx: int | None = None
    header_width: int | None = None

    for line in text.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = split_markdown_table_row(line)
        if len(cells) < 3:
            continue
        low = [c.lower().strip("` ").strip() for c in cells]
        claim_header_idx = next(
            (i for i, cell in enumerate(low) if "суть" in cell or cell == "claim"),
            None,
        )
        if "id" in low and claim_header_idx is not None:
            header_width = len(cells)
            claim_idx = claim_header_idx
            type_idx = low.index("тип") if "тип" in low else (
                low.index("type") if "type" in low else 1
            )
            unit_idx = _header_index(low, "knowledgeunit", "knowledge_unit")
            conditions_idx = next(
                (i for i, cell in enumerate(low) if "услов" in cell or "границ" in cell),
                _header_index(low, "conditions"),
            )
            links_idx = _header_index(low, "связи", "links")
            practical_idx = next(
                (i for i, cell in enumerate(low) if "практическ" in cell),
                _header_index(low, "practical"),
            )
            causes_idx = _header_index(low, "causes")
            enables_idx = _header_index(low, "enables")
            requires_idx = _header_index(low, "requires")
            prevents_idx = _header_index(low, "prevents")
            depends_idx = _header_index(low, "dependson", "depends_on", "depends on")
            evidence_idx = _header_index(low, "evidence")
            rel_conf_idx = _header_index(low, "relationconfidence", "relation_confidence")
            truth_status_idx = _header_index(low, "truth_status")
            source_refs_idx = _header_index(low, "source_refs")
            confidence_idx = _header_index(low, "confidence")
            risk_domain_idx = _header_index(low, "risk_domain")
            limitations_idx = _header_index(low, "limitations")
            review_status_idx = _header_index(low, "review_status")
            reviewer_idx = _header_index(low, "reviewer")
            reviewed_at_idx = _header_index(low, "reviewed_at")
            continue

        if all(set(c) <= set("-: ") for c in cells if c):
            continue
        fid = cells[0].strip("` ").strip()
        if not fid or fid.lower() == "id" or set(fid) <= set("-: "):
            continue
        if not FACT_ID_RE.fullmatch(fid):
            logger.warning("Skipping malformed World Skills fact ID: %s", fid)
            continue

        ci = claim_idx if claim_idx < len(cells) else (2 if len(cells) > 2 else len(cells) - 1)
        overflow = header_width is not None and len(cells) > header_width
        claim = " | ".join(cells[ci:]).strip() if overflow else cells[ci].strip()
        if len(claim) < 8 or fid in seen:
            continue
        seen.add(fid)
        ftype = cells[type_idx].strip() if type_idx < len(cells) else ""
        domain = fid.split(".")[0] if "." in fid else fid

        def _cell(idx: int | None) -> str:
            return cells[idx].strip() if idx is not None and idx < len(cells) else ""

        truth_status = "Draft" if overflow else (_cell(truth_status_idx) or "Draft")
        source_refs = [] if overflow else _parse_source_refs(_cell(source_refs_idx))
        confidence = 0.85 if overflow else _parse_confidence(_cell(confidence_idx))
        risk_domain = "" if overflow else _cell(risk_domain_idx)
        limitations = "" if overflow else _cell(limitations_idx)
        review_status = "unreviewed" if overflow else (
            _cell(review_status_idx) or "unreviewed"
        )
        reviewer = "" if overflow else _cell(reviewer_idx)
        reviewed_at = "" if overflow else _cell(reviewed_at_idx)

        admission_metadata = {
            "truth_status": truth_status,
            "source_refs": source_refs,
            "confidence": confidence,
            "risk_domain": risk_domain,
            "limitations": limitations,
            "review_status": review_status,
            "reviewer": reviewer,
            "reviewed_at": reviewed_at,
        }
        facts.append({
            "fact_id": fid,
            "knowledge_unit": _cell(unit_idx),
            "type": ftype,
            "claim": claim,
            "conditions": "" if overflow else _cell(conditions_idx),
            "links": "" if overflow else _cell(links_idx),
            "practical": "" if overflow else _cell(practical_idx),
            "causes": "" if overflow else _cell(causes_idx),
            "enables": "" if overflow else _cell(enables_idx),
            "requires": "" if overflow else _cell(requires_idx),
            "prevents": "" if overflow else _cell(prevents_idx),
            "depends_on": "" if overflow else _cell(depends_idx),
            "evidence": "" if overflow else _cell(evidence_idx),
            "relation_confidence": "" if overflow else _cell(rel_conf_idx),
            "source": f"wsc:{ftype or 'unknown'}",
            "confidence": confidence,
            **admission_metadata,
            "metadata": {
                "domain": domain,
                "type": ftype,
                "table_overflow_repaired": overflow,
                **admission_metadata,
            },
        })
    return facts


def parse_batch_file(path: str) -> list[dict[str, Any]]:
    with open(path, encoding="utf-8") as fh:
        facts = parse_batch_markdown(fh.read())
    filename = os.path.basename(path)
    upper_name = filename.upper()
    practical_domain = any(
        marker in upper_name
        for marker in ("_OPS", "_OPERATIONS", "_PRACTICAL", "_MAINTENANCE", "_REPAIR")
    )
    for fact in facts:
        metadata = fact.setdefault("metadata", {})
        metadata["knowledge_file"] = filename
        metadata["practical_domain"] = practical_domain
    return facts


def parse_knowledge_dir(knowledge_dir: str = DEFAULT_KNOWLEDGE_DIR) -> list[dict[str, Any]]:
    """Parse every fact table under the RU World Skills corpus."""
    facts: list[dict[str, Any]] = []
    seen: set[str] = set()
    for path in sorted(glob.glob(os.path.join(knowledge_dir, "*.ru.md"))):
        if os.path.basename(path) in _NON_FACT_FILES:
            continue
        for fact in parse_batch_file(path):
            if fact["fact_id"] not in seen:
                seen.add(fact["fact_id"])
                facts.append(fact)
    return facts


def _candidate_identity_payload(fact: dict[str, Any]) -> dict[str, Any]:
    refs = fact.get("source_refs", [])
    safe_refs = sorted(ref for ref in refs if isinstance(ref, str)) if isinstance(refs, list) else []
    return {
        "fact_id": fact.get("fact_id", ""),
        "claim": fact.get("claim", ""),
        "truth_status": fact.get("truth_status", "Draft"),
        "source_refs": safe_refs,
        "confidence": fact.get("confidence", 0.0),
        "risk_domain": fact.get("risk_domain", ""),
        "limitations": fact.get("limitations", ""),
        "review_status": fact.get("review_status", "unreviewed"),
        "reviewer": fact.get("reviewer", ""),
        "reviewed_at": fact.get("reviewed_at", ""),
    }


def world_skill_candidate_digest(fact: dict[str, Any]) -> str:
    """Content-bind one candidate without claiming a cryptographic human signature."""
    encoded = json.dumps(
        _candidate_identity_payload(fact),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def compute_world_skills_pack_id(facts: Sequence[dict[str, Any]]) -> str:
    """Return an order-independent deterministic identity for one candidate pack."""
    digests = sorted(world_skill_candidate_digest(fact) for fact in facts)
    encoded = "\n".join(digests).encode("utf-8")
    return f"wsc_pack_{hashlib.sha256(encoded).hexdigest()}"


def _truth_gate_mode(risk_domain: str) -> CognitiveMode:
    tokens = {
        token
        for token in re.split(r"[^\w]+", risk_domain.lower(), flags=re.UNICODE)
        if token
    }
    return (
        CognitiveMode.PRECISION
        if tokens & _HIGH_RISK_TOKENS
        else CognitiveMode.BALANCED
    )


def _reviewed_at_is_valid(value: str) -> bool:
    if not value:
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() is not None


def evaluate_world_skill_candidate(
    fact: dict[str, Any],
    *,
    actor: str = WORLD_SKILLS_ADMISSION_ACTOR,
) -> WorldSkillAdmissionDecision:
    """Evaluate metadata gates before any ESM movement toward Canon."""
    truth_status = str(fact.get("truth_status", "Draft")).strip().lower()
    if truth_status != "supported":
        return WorldSkillAdmissionDecision(
            WorldSkillAdmissionStage.QUARANTINE,
            False,
            "truth_status_not_supported",
        )

    refs = fact.get("source_refs")
    if not isinstance(refs, list) or not refs:
        return WorldSkillAdmissionDecision(
            WorldSkillAdmissionStage.PROVENANCE_CHECK,
            False,
            "source_refs_missing",
        )
    if any(not isinstance(ref, str) or not ref.strip() for ref in refs):
        return WorldSkillAdmissionDecision(
            WorldSkillAdmissionStage.PROVENANCE_CHECK,
            False,
            "source_refs_invalid",
        )
    normalized_refs = [ref.strip() for ref in refs]
    if len(set(normalized_refs)) != len(normalized_refs):
        return WorldSkillAdmissionDecision(
            WorldSkillAdmissionStage.PROVENANCE_CHECK,
            False,
            "source_refs_duplicate",
        )

    confidence = fact.get("confidence")
    if (
        not isinstance(confidence, (int, float))
        or isinstance(confidence, bool)
        or not math.isfinite(float(confidence))
        or not 0.0 <= float(confidence) <= 1.0
    ):
        return WorldSkillAdmissionDecision(
            WorldSkillAdmissionStage.QUARANTINE,
            False,
            "confidence_invalid",
        )

    risk_domain = str(fact.get("risk_domain", "")).strip()
    limitations = str(fact.get("limitations", "")).strip()
    if not risk_domain:
        return WorldSkillAdmissionDecision(
            WorldSkillAdmissionStage.DOMAIN_REVIEW,
            False,
            "risk_domain_missing",
        )
    if not limitations:
        return WorldSkillAdmissionDecision(
            WorldSkillAdmissionStage.DOMAIN_REVIEW,
            False,
            "limitations_missing",
        )

    review_status = str(fact.get("review_status", "unreviewed")).strip().lower()
    if review_status != "approved":
        return WorldSkillAdmissionDecision(
            WorldSkillAdmissionStage.DOMAIN_REVIEW,
            False,
            "review_not_approved",
        )
    reviewer = str(fact.get("reviewer", "")).strip()
    if not reviewer:
        return WorldSkillAdmissionDecision(
            WorldSkillAdmissionStage.DOMAIN_REVIEW,
            False,
            "reviewer_missing",
        )
    if reviewer.lower() == actor.lower():
        return WorldSkillAdmissionDecision(
            WorldSkillAdmissionStage.DOMAIN_REVIEW,
            False,
            "self_review_forbidden",
        )
    reviewed_at = str(fact.get("reviewed_at", "")).strip()
    if not _reviewed_at_is_valid(reviewed_at):
        return WorldSkillAdmissionDecision(
            WorldSkillAdmissionStage.DOMAIN_REVIEW,
            False,
            "reviewed_at_invalid",
        )

    return WorldSkillAdmissionDecision(
        WorldSkillAdmissionStage.TRUTH_GATE,
        True,
        "metadata_admitted",
        _truth_gate_mode(risk_domain),
    )


def _storage_payload(fact: dict[str, Any], pack_id: str) -> dict[str, Any]:
    metadata = dict(fact.get("metadata") or {})
    refs = fact.get("source_refs", [])
    safe_refs = [ref.strip() for ref in refs if isinstance(ref, str)] if isinstance(refs, list) else []
    metadata.update({
        "truth_status": fact.get("truth_status", "Draft"),
        "source_refs": safe_refs,
        "confidence": fact.get("confidence", 0.0),
        "risk_domain": fact.get("risk_domain", ""),
        "limitations": fact.get("limitations", ""),
        "review_status": fact.get("review_status", "unreviewed"),
        "reviewer": fact.get("reviewer", ""),
        "reviewed_at": fact.get("reviewed_at", ""),
        "evidence_refs": safe_refs,
        "world_skills_admission_contract": WORLD_SKILLS_ADMISSION_CONTRACT,
        "world_skills_candidate_digest": world_skill_candidate_digest(fact),
        "world_skills_pack_id": pack_id,
    })
    return {
        "fact_id": fact["fact_id"],
        "claim": fact["claim"],
        "source": fact["source"],
        "confidence": fact.get("confidence", 0.85),
        "metadata": metadata,
        "claim_type": "WORLD_FACT",
        "origin_type": "EXTERNAL",
        "memory_type": "semantic",
    }


def ingest_facts(
    store: Any,
    facts: Sequence[dict[str, Any]],
    validate: bool = True,
) -> dict[str, Any]:
    """Store candidates, then attempt the bounded C9 admission path when requested.

    ``validate=False`` preserves the existing scratch-analysis behavior: candidates are
    stored but no admission or ESM movement is attempted.

    ``validate=True`` is fail-closed. Metadata/review gates run first. The existing
    TruthGate then performs a read-only precheck while the fact is still non-canonical.
    Only a passed precheck permits the ordinary legal ESM ladder to ``Supported``; the
    existing PromotionGateway immediately re-runs TruthGate on the durable Supported
    snapshot and owns the final CAS-guarded transition to ``Validated``.
    """
    pack_id = compute_world_skills_pack_id(facts)
    rep: dict[str, Any] = {
        "parsed": len(facts),
        "ingested": 0,
        "validated": 0,
        "quarantined": 0,
        "truth_gate_rejected": 0,
        "errors": 0,
        "pack_id": pack_id,
        "admission_contract": WORLD_SKILLS_ADMISSION_CONTRACT,
    }
    if not facts:
        return rep

    payload = [_storage_payload(fact, pack_id) for fact in facts]

    try:
        bstats = store.store_facts_batch(payload)
        rep["ingested"] = int(bstats.get("stored", 0)) + int(bstats.get("updated", 0))
        rep["errors"] += int(bstats.get("errors", 0))
    except Exception as exc:  # noqa: BLE001 — compatibility fallback for stores without batch
        logger.debug("store_facts_batch failed (%s) → per-fact", exc)
        for item in payload:
            try:
                if store.store_fact(item):
                    rep["ingested"] += 1
                else:
                    rep["errors"] += 1
            except Exception:  # noqa: BLE001
                rep["errors"] += 1

    if not validate:
        return rep

    gateway = PromotionGateway(store)
    for fact in facts:
        decision = evaluate_world_skill_candidate(fact)
        if not decision.passed or decision.mode is None:
            rep["quarantined"] += 1
            continue

        fact_id = str(fact["fact_id"])
        try:
            durable = store.get_fact_durable(fact_id)
            if durable is None:
                rep["errors"] += 1
                continue

            precheck = TruthGate(store).evaluate(
                durable,
                mode=decision.mode,
                by=WORLD_SKILLS_ADMISSION_ACTOR,
            )
            if not precheck.passed:
                rep["truth_gate_rejected"] += 1
                continue

            current_state = durable.get("epistemic_state", "Observed")
            if current_state != "Validated" and current_state != "Supported":
                if not store.promote_esm_to(
                    fact_id,
                    "Supported",
                    by=WORLD_SKILLS_ADMISSION_ACTOR,
                ):
                    rep["errors"] += 1
                    continue

            outcome = gateway.promote(PromotionRequest(
                fact_id=fact_id,
                requested_by=WORLD_SKILLS_ADMISSION_ACTOR,
                mode=decision.mode,
            ))
            if outcome.verdict.passed:
                rep["validated"] += 1
            else:
                rep["truth_gate_rejected"] += 1
        except Exception as exc:  # noqa: BLE001 — fail closed per candidate
            logger.debug("World Skills admission %s: %s", fact_id, exc)
            rep["errors"] += 1
    return rep


def ingest_world_skills(
    store: Any,
    knowledge_dir: str = DEFAULT_KNOWLEDGE_DIR,
    validate: bool = True,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    """Parse corpus, store/admit facts, then derive typed linker edges."""
    facts = parse_knowledge_dir(knowledge_dir)
    rep = ingest_facts(store, facts, validate=validate)
    try:
        from core.knowledge_linker import link_facts
        edges = link_facts(facts)
    except Exception as exc:  # noqa: BLE001
        logger.debug("link_facts: %s", exc)
        edges = []
    rep["edges"] = len(edges)
    return rep, facts, edges


__all__ = [
    "DEFAULT_KNOWLEDGE_DIR",
    "WORLD_SKILLS_ADMISSION_ACTOR",
    "WORLD_SKILLS_ADMISSION_CONTRACT",
    "WorldSkillAdmissionDecision",
    "WorldSkillAdmissionStage",
    "compute_world_skills_pack_id",
    "evaluate_world_skill_candidate",
    "ingest_facts",
    "ingest_world_skills",
    "parse_batch_file",
    "parse_batch_markdown",
    "parse_knowledge_dir",
    "split_markdown_table_row",
    "world_skill_candidate_digest",
]
