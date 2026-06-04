"""
ProtoConcept → L3 promote (RFC0066, I50-b).

Единственный путь в граф: TruthGate + Epistemic Pipeline.
Создаёт :Entity:EmergentConcept и связи GROUPS_ENTITY к членам кластера.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from core.concept_emergence import ProtoConcept, get_concept_detector
from core.epistemic_pipeline import EpistemicResult, build_fact_candidate, evaluate_fact_candidate
from core.esm import EpistemicState
from core.feature_config import get_config

logger = logging.getLogger(__name__)


@dataclass
class ProtoPromoteResult:
    proto_id: str
    passed: bool
    reason: str
    concept_name: str | None = None
    entity_uuid: str | None = None
    epistemic_state: str = EpistemicState.OBSERVED.value
    skipped: bool = False


def is_concept_promote_enabled() -> bool:
    cfg = get_config().app
    return bool(
        getattr(cfg, "enable_concept_promote", False)
        and getattr(cfg, "enable_truth_gate", False)
        and getattr(cfg, "enable_concept_emergence", False)
    )


def build_proto_fact_candidate(proto: ProtoConcept) -> dict[str, Any]:
    """Fact-кандидат для TruthGate из ProtoConcept."""
    detector = get_concept_detector()
    name = proto.name or detector.lazy_name(proto.proto_id) or proto.proto_id
    entities = sorted(proto.entities)
    claim = (
        f"Emergent concept '{name}' groups co-occurring entities: "
        + ", ".join(entities)
    )
    return build_fact_candidate(
        chunk=claim,
        source="concept_emergence",
        fact_id=proto.proto_id,
        confidence=proto.confidence,
        evidence_refs=entities,
        metadata={
            "proto_id": proto.proto_id,
            "entity_count": len(entities),
            "co_occur_count": proto.co_occur_count,
            "cross_sessions": proto.cross_sessions,
            "kind": "ProtoConcept",
        },
    )


def evaluate_proto_for_promote(proto: ProtoConcept) -> EpistemicResult:
    """TruthGate + trace для ProtoConcept (I50-b)."""
    fact = build_proto_fact_candidate(proto)
    return evaluate_fact_candidate(fact)


async def persist_promoted_concept(
    graphiti,
    *,
    proto: ProtoConcept,
    result: EpistemicResult,
    concept_name: str | None = None,
) -> str | None:
    """
    Записать :EmergentConcept в Neo4j после успешного TruthGate.
    """
    if not result.passed or graphiti is None:
        return None

    driver = getattr(graphiti, "driver", None) or getattr(graphiti, "_driver", None)
    if not driver:
        return None

    cfg = get_config()
    name = concept_name or proto.name or proto.proto_id
    entity_uuid = str(uuid4())
    summary = result.to_metadata().get("truth_gate_justification") or (
        f"ProtoConcept {proto.proto_id}: "
        f"co_occur={proto.co_occur_count}, sessions={proto.cross_sessions}"
    )
    group_id = cfg.app.knowledge_group_id
    members = sorted(proto.entities)

    try:
        res = await driver.execute_query(
            """
            MERGE (c:Entity {name: $name})
            SET c:EmergentConcept,
                c.uuid = coalesce(c.uuid, $uuid),
                c.summary = $summary,
                c.group_id = $gid,
                c.proto_id = $proto_id,
                c.epistemic_state = $state,
                c.truth_gate_passed = true,
                c.truth_gate_mode = $mode,
                c.confidence = $confidence,
                c.promoted_at = $promoted_at,
                c.co_occur_count = $co_occur,
                c.member_entities = $members
            RETURN c.uuid AS uuid
            """,
            name=name,
            uuid=entity_uuid,
            summary=summary[:2000],
            gid=group_id,
            proto_id=proto.proto_id,
            state=EpistemicState.VALIDATED.value,
            mode=result.mode,
            confidence=result.confidence,
            promoted_at=datetime.now(UTC).isoformat(),
            co_occur=proto.co_occur_count,
            members=members,
        )
        stored_uuid = entity_uuid
        if res.records:
            stored_uuid = res.records[0].get("uuid") or entity_uuid

        for mname in members:
            await driver.execute_query(
                """
                MATCH (c:Entity {name: $cname})
                MATCH (e:Entity {name: $mname})
                MERGE (c)-[:GROUPS_ENTITY]->(e)
                """,
                cname=name,
                mname=mname,
            )

        proto.promoted = True
        proto.l3_entity_uuid = str(stored_uuid)
        return str(stored_uuid)
    except Exception as exc:  # noqa: BLE001
        logger.warning("persist_promoted_concept failed %s: %s", proto.proto_id, exc)
        return None


async def promote_proto_to_l3(
    graphiti,
    proto_id: str,
    *,
    force: bool = False,
) -> ProtoPromoteResult:
    """
    Промоут одного ProtoConcept в L3 через TruthGate.
    """
    if not force and not is_concept_promote_enabled():
        return ProtoPromoteResult(
            proto_id=proto_id,
            passed=False,
            reason="promote_disabled",
            skipped=True,
        )

    detector = get_concept_detector()
    proto = detector.get_proto(proto_id)
    if proto is None:
        return ProtoPromoteResult(
            proto_id=proto_id,
            passed=False,
            reason="proto_not_found",
        )

    if getattr(proto, "promoted", False):
        return ProtoPromoteResult(
            proto_id=proto_id,
            passed=True,
            reason="already_promoted",
            concept_name=proto.name,
            entity_uuid=getattr(proto, "l3_entity_uuid", None),
            epistemic_state=EpistemicState.VALIDATED.value,
            skipped=True,
        )

    min_conf = get_config().app.emergence_promote_min_confidence
    if not force and proto.confidence < min_conf:
        return ProtoPromoteResult(
            proto_id=proto_id,
            passed=False,
            reason=f"confidence_below_{min_conf}",
            concept_name=proto.name,
        )

    from core.concept_naming import resolve_proto_name

    await resolve_proto_name(proto)
    epistemic = evaluate_proto_for_promote(proto)

    if not epistemic.passed:
        return ProtoPromoteResult(
            proto_id=proto_id,
            passed=False,
            reason=epistemic.reason,
            concept_name=proto.name,
            epistemic_state=epistemic.epistemic_state,
        )

    uuid = await persist_promoted_concept(
        graphiti,
        proto=proto,
        result=epistemic,
        concept_name=proto.name,
    )

    logger.info(
        "ProtoConcept promoted: %s -> L3 uuid=%s mode=%s",
        proto_id,
        uuid,
        epistemic.mode,
    )

    return ProtoPromoteResult(
        proto_id=proto_id,
        passed=True,
        reason=epistemic.reason,
        concept_name=proto.name,
        entity_uuid=uuid,
        epistemic_state=epistemic.epistemic_state,
    )


async def try_promote_born_protos(
    graphiti,
    proto_ids: list[str],
) -> list[ProtoPromoteResult]:
    """Попытка авто-промоута после рождения (ingest hook)."""
    if not is_concept_promote_enabled():
        return []
    results: list[ProtoPromoteResult] = []
    for pid in proto_ids:
        try:
            r = await promote_proto_to_l3(graphiti, pid)
            results.append(r)
        except Exception as exc:  # noqa: BLE001
            logger.warning("try_promote_born_protos %s: %s", pid, exc)
            results.append(
                ProtoPromoteResult(
                    proto_id=pid, passed=False, reason=str(exc)
                )
            )
    return results


async def promote_eligible_protos(graphiti) -> dict[str, Any]:
    """Промоут всех активных proto с confidence >= порога."""
    detector = get_concept_detector()
    min_conf = get_config().app.emergence_promote_min_confidence
    results: list[ProtoPromoteResult] = []
    for proto in detector.list_active_protos():
        if proto.confidence >= min_conf and not getattr(proto, "promoted", False):
            results.append(await promote_proto_to_l3(graphiti, proto.proto_id))
    passed = sum(1 for r in results if r.passed and not r.skipped)
    return {
        "candidates": len(results),
        "passed": passed,
        "results": [r.__dict__ for r in results],
    }


__all__ = [
    "ProtoPromoteResult",
    "build_proto_fact_candidate",
    "evaluate_proto_for_promote",
    "is_concept_promote_enabled",
    "persist_promoted_concept",
    "promote_eligible_protos",
    "promote_proto_to_l3",
    "try_promote_born_protos",
]
