#!/usr/bin/env python3
"""Apply the exact PATCH /facts/{fact_id}/transition gateway migration.

Temporary PR machinery. The one-shot workflow deletes this script before the
final branch head is published.
"""

from pathlib import Path


PATH = Path("server.py")


def replace_once(source: str, old: str, new: str, *, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return source.replace(old, new, 1)


def main() -> None:
    source = PATH.read_text(encoding="utf-8")

    source = replace_once(
        source,
        "    transition_esm,\n    validate_and_promote,\n)\nfrom core.mhi import",
        "    transition_esm,\n)\n"
        "from core.promotion_gateway import PromotionGateway, PromotionRequest\n"
        "from core.mhi import",
        label="gateway import and direct-memory import removal",
    )

    source = replace_once(
        source,
        "_store: SQLiteGraphStore = _GLOBAL_STORE\n_sleep_worker:",
        "_store: SQLiteGraphStore = _GLOBAL_STORE\n"
        "_promotion_gateway = PromotionGateway(_store)\n"
        "_sleep_worker:",
        label="gateway construction",
    )

    source = replace_once(
        source,
        """            # SECURITY (I68): единственный API-путь в 'Validated' — обязан
            # пройти TruthGate. См. core.memory.validate_and_promote().
            verdict = await asyncio.to_thread(
                validate_and_promote, fact_id, actor_id
            )
            if verdict.reason == "not_found":
                raise HTTPException(status_code=404, detail=verdict.justification)
            if verdict.reason == "concurrent_modification":
                # SECURITY (TOCTOU): факт изменился между оценкой TruthGate и
                # записью — не 422 (truth_gate_rejected), т.к. это не был
                # ложный вердикт, а гонка. Клиент должен просто повторить.
                raise HTTPException(
                    status_code=409,
                    detail={
                        "error": "concurrent_modification",
                        "reason": verdict.reason,
                        "justification": verdict.justification,
                    },
                )
            if not verdict.passed:
                raise HTTPException(
                    status_code=422,
                    detail={
                        "error": "truth_gate_rejected",
                        "reason": verdict.reason,
                        "justification": verdict.justification,
                        "mode": verdict.mode.value,
                        "confidence": verdict.confidence,
                        "evidence_count": verdict.evidence_count,
                    },
""",
        """            # SECURITY (I68): единственный API-путь в 'Validated' — обязан
            # пройти PromotionGateway → TruthGate + CAS. Gateway не владеет
            # порогами и не дублирует policy.
            outcome = await asyncio.to_thread(
                _promotion_gateway.promote,
                PromotionRequest(fact_id=fact_id, requested_by=actor_id),
            )
            verdict = outcome.verdict
            if verdict.reason_code == "not_found":
                raise HTTPException(status_code=404, detail=verdict.justification)
            if verdict.reason_code == "concurrent_modification":
                # SECURITY (TOCTOU): факт изменился между оценкой TruthGate и
                # записью — не 422 (truth_gate_rejected), т.к. это не был
                # ложный вердикт, а гонка. Клиент должен просто повторить.
                raise HTTPException(
                    status_code=409,
                    detail={
                        "error": "concurrent_modification",
                        "reason": verdict.reason_code,
                        "justification": verdict.justification,
                    },
                )
            if not verdict.passed:
                raise HTTPException(
                    status_code=422,
                    detail={
                        "error": "truth_gate_rejected",
                        "reason": verdict.reason_code,
                        "justification": verdict.justification,
                        "mode": verdict.mode.value,
                        "confidence": verdict.confidence,
                        "evidence_count": verdict.evidence_count,
                    },
""",
        label="validated endpoint block",
    )

    PATH.write_text(source, encoding="utf-8")


if __name__ == "__main__":
    main()
