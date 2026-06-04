#!/usr/bin/env python3
"""Живое демо TruthGate — вердикты по режимам без HTTP."""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.memory import SQLiteGraphStore
from core.truth_gate import CognitiveMode, TruthGate


def run_case(gate: TruthGate, label: str, fact: dict, mode: CognitiveMode) -> None:
    v = gate.evaluate(fact, mode=mode)
    status = "PASS" if v.passed else "FAIL"
    print(f"\n[{label}] mode={mode.value} -> {status}")
    print(f"  reason:         {v.reason}")
    print(f"  justification:  {v.justification}")
    print(f"  confidence:     {v.confidence} (порог mode)")
    print(f"  evidence_count: {v.evidence_count}")


def main() -> int:
    tmp = tempfile.mkdtemp(prefix="velantrim_truthgate_demo_")
    db_path = os.path.join(tmp, "demo.db")
    store = SQLiteGraphStore(db_path=db_path)
    gate = TruthGate(store)

    print("=" * 60)
    print("TruthGate — живой прогон")
    print("=" * 60)
    print(f"БД: {db_path}")

    good = {
        "fact_id": "tg_good",
        "claim": "Земля вращается вокруг Солнца",
        "source": "astronomy_textbook",
        "confidence": 0.95,
        "metadata": {"evidence_refs": ["ref1", "ref2", "ref3"]},
    }
    low_conf = {**good, "fact_id": "tg_low", "confidence": 0.5}
    no_evidence = {
        **good,
        "fact_id": "tg_noev",
        "metadata": {},
    }
    no_source = {**good, "fact_id": "tg_nosrc", "source": ""}

    run_case(gate, "Хороший факт", good, CognitiveMode.BALANCED)
    run_case(gate, "Низкая уверенность", low_conf, CognitiveMode.BALANCED)
    run_case(gate, "Низкая уверенность", low_conf, CognitiveMode.EXPLORATION)
    run_case(gate, "Без evidence_refs", no_evidence, CognitiveMode.BALANCED)
    run_case(gate, "Пустой source", no_source, CognitiveMode.BALANCED)
    run_case(gate, "PRECISION (5 evidence)", good, CognitiveMode.PRECISION)

    store.close()
    print("\n" + "=" * 60)
    print("Готово. Все проверки — через TruthGate.evaluate()")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
