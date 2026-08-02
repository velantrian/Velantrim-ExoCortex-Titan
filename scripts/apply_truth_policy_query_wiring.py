#!/usr/bin/env python3
"""Replace the confirmed `/query` TruthPolicy fail-open block; self-removing."""

from pathlib import Path


path = Path("server.py")
source = path.read_text(encoding="utf-8")
old = '''    # P2 (T1.4): явный вердикт truth_policy по пакету фактов. Аддитивно и за флагом
    # (ENABLE_TRUTH_POLICY, по умолчанию off → truth_block=None, поток управления не меняется).
    truth_block: dict[str, Any] | None = None
    truth_rejects_answer = False
    try:
        from core.runtime_flags import is_truth_policy_enabled

        if is_truth_policy_enabled():
            from core.truth_policy import decide as _truth_decide

            _verdict = _truth_decide(req.query, pipeline_facts, mode=eff_mode)
            truth_block = _verdict.to_dict()
            # reject ⇒ нет допустимых фактов ⇒ не выдумываем ответ через LLM
            truth_rejects_answer = _verdict.is_reject
    except Exception as exc:  # noqa: BLE001 — аддитивно; никогда не ломаем ответ
        logger.debug("truth_policy verdict skipped: %s", exc)

'''
new = '''    # TruthPolicy runtime boundary. Feature-disabled behavior remains additive;
    # an enabled policy/configuration failure is a content-free REJECT and blocks
    # unverified LLM generation instead of silently failing open.
    from core.truth_policy_runtime import evaluate_configured_truth_policy_runtime

    _truth_runtime = evaluate_configured_truth_policy_runtime(
        req.query,
        pipeline_facts,
        mode=eff_mode,
    )
    truth_block: dict[str, Any] | None = _truth_runtime.truth_block
    truth_rejects_answer = _truth_runtime.blocks_llm

'''
count = source.count(old)
if count != 1:
    raise SystemExit(f"expected one TruthPolicy query block, found {count}")
source = source.replace(old, new, 1)
path.write_text(source, encoding="utf-8")
