#!/usr/bin/env python3
"""Soft L1 scenario sets: expected vs actual Gate status (no model calls).

REGRESSION sets, not independent benchmarks:
- tests/fixtures/source_x_soft_l1_contradiction_cases_2026-11-24.json
  (PR #537 secfix, Manus audit 2026-11-24; written by the fix's executor)
- tests/fixtures/source_x_soft_l1_probe_2026-11-24.json (probe, known gaps)
- tests/source_x_soft_l1_fixtures.json (six-model refusal / strict texts)

Prints per-set agreement, false allows (expected BLOCKED, delivered) and
false blocks (expected delivered, BLOCKED) separately.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.source_x_gate import SourceXGateConfig, apply_gate  # noqa: E402

CFG = SourceXGateConfig(enabled=True)


def _contradiction_cases() -> list[tuple[str, str, str]]:
    doc = json.loads((ROOT / "tests/fixtures/source_x_soft_l1_contradiction_cases_2026-11-24.json")
                     .read_text(encoding="utf-8"))
    return [(c["id"], c["text"], c["expected"]) for c in doc["items"]]


def _six_model_cases() -> list[tuple[str, str, str]]:
    doc = json.loads((ROOT / "tests/source_x_soft_l1_fixtures.json").read_text(encoding="utf-8"))
    out = []
    for c in doc["FLAG_L1_REFUSAL"]:
        out.append((c["id"], c["text"], "FLAG_L1_REFUSAL"))
    for c in doc["KEEP_STRICT"]:
        out.append((c["id"], c["text"], "BLOCKED_ATTEMPT"))
    return out


def _probe_cases() -> list[tuple[str, str, str]]:
    doc = json.loads((ROOT / "tests/fixtures/source_x_soft_l1_probe_2026-11-24.json").read_text(encoding="utf-8"))
    return [(c["id"], c["text"], c["expected"]) for c in doc["items"]]


def report(name: str, cases: list[tuple[str, str, str]]) -> dict[str, int]:
    agree = false_allow = false_block = 0
    rows = []
    for cid, text, expected in cases:
        got = apply_gate(text, config=CFG).event
        if got == expected:
            agree += 1
            continue
        if expected == "BLOCKED_ATTEMPT":
            false_allow += 1
        elif got == "BLOCKED_ATTEMPT":
            false_block += 1
        rows.append((cid, expected, got))
    print(f"[{name}] ROLE: REGRESSION (not an independent benchmark)")
    print(f"[{name}] n={len(cases)} agree={agree} false_allow={false_allow} false_block={false_block}")
    for cid, exp, got in rows:
        print(f"[{name}]   MISMATCH {cid}: expected={exp} got={got}")
    return {"n": len(cases), "agree": agree, "false_allow": false_allow, "false_block": false_block}


def main() -> int:
    report("contradiction_cases_2026-11-24", _contradiction_cases())
    report("six_model_fixtures", _six_model_cases())
    report("probe_2026-11-24 (not held out; known gaps)", _probe_cases())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
