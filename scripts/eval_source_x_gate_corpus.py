"""Measure the source-X Gate against the hand-labeled corpus (no model calls).

Usage:
    python scripts/eval_source_x_gate_corpus.py [--json]

Reads ``tests/fixtures/source_x_gate_labeled_corpus_2026-11-23.json`` and
prints a confusion matrix per verdict, per-class precision / recall, the
binary block precision / recall, and every mismatch. Streaming items are
fed chunk by chunk through ``SourceXStreamBuffer`` when it is available;
the verdict is taken on the released text only.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core import source_x_gate as sxg  # noqa: E402

CORPUS = ROOT / "tests" / "fixtures" / "source_x_gate_labeled_corpus_2026-11-23.json"
VERDICTS = ("ALLOW", "FLAG_REVIEW", "FLAG_L1_REFUSAL", "BLOCKED_ATTEMPT")


def load_corpus(path: Path = CORPUS) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _item_text(item: dict[str, Any]) -> str:
    if "chunks" in item:
        return "".join(item["chunks"])
    return item["text"]


def predict(item: dict[str, Any], cfg: sxg.SourceXGateConfig) -> dict[str, Any]:
    """Return the gate verdict for one corpus item."""
    out: dict[str, Any] = {"early_release": False}
    if "chunks" in item and hasattr(sxg, "SourceXStreamBuffer"):
        buf = sxg.SourceXStreamBuffer(surface="corpus_eval", config=cfg)
        for chunk in item["chunks"]:
            if buf.feed(chunk) is not None:
                out["early_release"] = True
        outcome = buf.finalize()
        out["verdict"] = outcome.status
        out["delivered_text"] = outcome.text
    else:
        verdict = sxg.apply_gate(_item_text(item), config=cfg)
        out["verdict"] = verdict.event
    if "notes" in item:
        res = sxg.apply_to_pipeline_result(
            {"answer": _item_text(item), "notes": item["notes"]}, config=cfg
        )
        out["notes_event"] = res["source_x_notes_review"]["event"]
        out["answer_after"] = res["answer"]
    return out


def evaluate(corpus: dict[str, Any] | None = None) -> dict[str, Any]:
    corpus = corpus or load_corpus()
    cfg = sxg.SourceXGateConfig(enabled=True)
    labels = list(VERDICTS)
    confusion = {e: {p: 0 for p in labels + ["GATE_ERROR"]} for e in labels}
    mismatches: list[dict[str, Any]] = []
    notes_total = notes_ok = 0
    early = 0
    rows = []
    for item in corpus["items"]:
        pred = predict(item, cfg)
        exp = item["expected"]
        got = pred["verdict"]
        confusion[exp][got] = confusion[exp].get(got, 0) + 1
        if pred.get("early_release"):
            early += 1
        if got != exp:
            mismatches.append({"id": item["id"], "expected": exp, "got": got, "why": item.get("why", "")})
        if "notes" in item:
            notes_total += 1
            if pred["notes_event"] == item["expected_notes"]:
                notes_ok += 1
            else:
                mismatches.append(
                    {"id": item["id"] + ":notes", "expected": item["expected_notes"], "got": pred["notes_event"]}
                )
        rows.append({"id": item["id"], "expected": exp, "got": got})

    per_class = {}
    for cls in labels:
        tp = confusion[cls][cls]
        fn = sum(confusion[cls].values()) - tp
        fp = sum(confusion[e][cls] for e in labels if e != cls)
        per_class[cls] = {
            "support": tp + fn,
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "precision": (tp / (tp + fp)) if (tp + fp) else None,
            "recall": (tp / (tp + fn)) if (tp + fn) else None,
        }
    # Binary view: is the answer withheld from the user?
    def withheld(v: str) -> bool:
        return v in ("BLOCKED_ATTEMPT", "GATE_ERROR")

    btp = bfp = bfn = btn = 0
    for r in rows:
        e, g = withheld(r["expected"]), withheld(r["got"])
        if e and g:
            btp += 1
        elif g and not e:
            bfp += 1
        elif e and not g:
            bfn += 1
        else:
            btn += 1
    n = len(rows)
    return {
        "n_items": n,
        "accuracy": sum(1 for r in rows if r["expected"] == r["got"]) / n,
        "confusion": confusion,
        "per_class": per_class,
        "block_binary": {
            "tp": btp,
            "fp": bfp,
            "fn": bfn,
            "tn": btn,
            "precision": btp / (btp + bfp) if (btp + bfp) else None,
            "recall": btp / (btp + bfn) if (btp + bfn) else None,
        },
        "notes": {"n": notes_total, "correct": notes_ok},
        "stream_items": sum(1 for i in corpus["items"] if "chunks" in i),
        "stream_early_release": early,
        "mismatches": mismatches,
    }


def _fmt(x: float | None) -> str:
    return "n/a" if x is None else f"{x:.3f}"


def main(argv: list[str]) -> int:
    rep = evaluate()
    if "--json" in argv:
        print(json.dumps(rep, ensure_ascii=False, indent=1))
        return 0
    print(f"N={rep['n_items']} accuracy={rep['accuracy']:.3f}")
    head = "expected \\ got".ljust(18) + "".join(v[:14].rjust(16) for v in list(VERDICTS) + ["GATE_ERROR"])
    print(head)
    for e, row in rep["confusion"].items():
        print(e.ljust(18) + "".join(str(row[v]).rjust(16) for v in list(VERDICTS) + ["GATE_ERROR"]))
    for cls, m in rep["per_class"].items():
        print(f"{cls:16} support={m['support']:3} precision={_fmt(m['precision'])} recall={_fmt(m['recall'])}")
    b = rep["block_binary"]
    print(f"withheld (binary): tp={b['tp']} fp={b['fp']} fn={b['fn']} tn={b['tn']} "
          f"precision={_fmt(b['precision'])} recall={_fmt(b['recall'])}")
    print(f"notes: {rep['notes']['correct']}/{rep['notes']['n']} correct")
    print(f"stream items={rep['stream_items']} early_release={rep['stream_early_release']}")
    for m in rep["mismatches"]:
        print("MISMATCH", m)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
