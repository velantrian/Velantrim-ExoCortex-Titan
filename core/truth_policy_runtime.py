"""Fail-closed runtime boundary for optional TruthPolicy evaluation.

The policy itself remains owned by :mod:`core.truth_policy`. This adapter only
normalizes disabled, measured, and failure states for hot-path callers. A
failure while the feature is enabled blocks unverified LLM generation and
returns a content-free canonical REJECT block; it never copies exception text,
paths, SQL, fact payloads, or provider data into client-visible evidence.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

from core.core3_adapter import REJECT
from core.truth_policy import TruthVerdict, decide

logger = logging.getLogger("velantrim.truth_policy_runtime")
_SAFE_REASON_CODE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")


@dataclass(frozen=True, slots=True)
class TruthPolicyRuntimeResult:
    enabled: bool
    evaluated: bool
    blocks_llm: bool
    truth_block: dict[str, Any] | None
    reason_code: str

    def __post_init__(self) -> None:
        if not isinstance(self.enabled, bool):
            raise TypeError("enabled must be bool")
        if not isinstance(self.evaluated, bool):
            raise TypeError("evaluated must be bool")
        if not isinstance(self.blocks_llm, bool):
            raise TypeError("blocks_llm must be bool")
        if _SAFE_REASON_CODE.fullmatch(self.reason_code) is None:
            raise ValueError("reason_code must be lower_snake_case and at most 64 characters")
        if not self.enabled:
            if self.evaluated or self.blocks_llm or self.truth_block is not None:
                raise ValueError("disabled TruthPolicy cannot claim evaluation or blocking")
        elif self.truth_block is None:
            raise ValueError("enabled TruthPolicy result requires truth_block")


def _failure_truth_block() -> dict[str, Any]:
    return TruthVerdict(
        decision=REJECT,
        truth_status="policy_unavailable",
        reason="truth_policy_unavailable",
        admissible_count=0,
        evidence_ids=[],
        trace_note="",
    ).to_dict()


def evaluate_truth_policy_runtime(
    query: str,
    facts: Sequence[dict[str, Any]],
    *,
    mode: str | None,
    enabled: bool,
    decider: Callable[..., TruthVerdict] = decide,
) -> TruthPolicyRuntimeResult:
    """Evaluate TruthPolicy without allowing an enabled policy to fail open."""

    if not isinstance(enabled, bool):
        raise TypeError("enabled must be bool")
    if not enabled:
        return TruthPolicyRuntimeResult(
            enabled=False,
            evaluated=False,
            blocks_llm=False,
            truth_block=None,
            reason_code="truth_policy_disabled",
        )

    try:
        verdict = decider(query, facts, mode=mode)
        if not isinstance(verdict, TruthVerdict):
            raise TypeError("TruthPolicy decider returned an invalid verdict type")
        block = verdict.to_dict()
        decision = str(block.get("decision") or "")
        if decision not in {"allow", "gap_notice", "reject"}:
            raise ValueError("TruthPolicy decider returned an unknown decision")
        return TruthPolicyRuntimeResult(
            enabled=True,
            evaluated=True,
            blocks_llm=verdict.is_reject,
            truth_block=block,
            reason_code=f"truth_policy_{decision}",
        )
    except Exception:  # noqa: BLE001 - converted to content-free fail-closed evidence
        logger.exception("TruthPolicy runtime evaluation failed")
        return TruthPolicyRuntimeResult(
            enabled=True,
            evaluated=False,
            blocks_llm=True,
            truth_block=_failure_truth_block(),
            reason_code="truth_policy_unavailable",
        )


__all__ = ["TruthPolicyRuntimeResult", "evaluate_truth_policy_runtime"]
