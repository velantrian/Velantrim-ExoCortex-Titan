"""Gate precision / recall on a NEW hand-labeled corpus (Codex audit item 4).

The corpus (``tests/fixtures/source_x_gate_labeled_corpus_2026-11-23.json``)
is hand-written for this hardening PR and is not reused from the ICT-01 /
TASK-03 model drafts. Labels follow ADR-2026-11-23 and were assigned before
running the gate. No model calls.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.feature_config import clear_config_cache
from scripts.eval_source_x_gate_corpus import CORPUS, evaluate, load_corpus

ROOT = Path(__file__).resolve().parents[1]

# Over-blocks the gate still makes on purpose (safe direction): the soft-L1
# refusal list from Memory-Ruslan PR #62 does not know these phrasings.
# Loosening it is a separate decision. Any change here must be explicit.
KNOWN_MISMATCHES = {
    ("refusal_official-02", "FLAG_L1_REFUSAL", "BLOCKED_ATTEMPT"),  # «исключён» with ё
    ("refusal_official-07", "FLAG_L1_REFUSAL", "BLOCKED_ATTEMPT"),  # English "do not use"
}


@pytest.fixture(autouse=True)
def _reset_config():
    clear_config_cache()
    yield
    clear_config_cache()


@pytest.fixture(scope="module")
def report():
    return evaluate()


def test_corpus_covers_required_categories():
    corpus = load_corpus()
    cats = {i["category"] for i in corpus["items"]}
    assert {
        "plain_x", "dot_comma", "refusal_official", "refusal_strict", "l2_name",
        "notes_only", "clean", "near_miss", "stream_split",
    } <= cats
    ids = [i["id"] for i in corpus["items"]]
    assert len(ids) == len(set(ids))
    for item in corpus["items"]:
        assert item["expected"] in corpus["verdicts"]


def test_corpus_is_not_reused_from_ict01_fixtures():
    old = json.loads((ROOT / "tests" / "source_x_soft_l1_fixtures.json").read_text("utf-8"))
    old_texts = set()
    for key in ("FLAG_L1_REFUSAL", "KEEP_STRICT"):
        for row in old.get(key, []):
            for v in (row.values() if isinstance(row, dict) else [row]):
                if isinstance(v, str) and len(v) > 30:
                    old_texts.add(v.strip())
    for item in load_corpus()["items"]:
        text = item.get("text") or "".join(item.get("chunks", []))
        assert text.strip() not in old_texts


def test_no_leak_every_labeled_block_is_withheld(report):
    b = report["block_binary"]
    assert b["fn"] == 0, report["mismatches"]
    assert b["recall"] == 1.0


def test_allow_and_flag_review_are_never_blocked(report):
    c = report["confusion"]
    assert c["ALLOW"]["BLOCKED_ATTEMPT"] == 0
    assert c["FLAG_REVIEW"]["BLOCKED_ATTEMPT"] == 0
    assert c["ALLOW"]["ALLOW"] == report["per_class"]["ALLOW"]["support"]


def test_mismatches_are_exactly_the_known_over_blocks(report):
    got = {(m["id"], m["expected"], m["got"]) for m in report["mismatches"]}
    assert got == KNOWN_MISMATCHES


def test_notes_are_annotation_only(report):
    assert report["notes"]["correct"] == report["notes"]["n"] > 0


def test_streaming_items_release_nothing_before_verdict(report):
    assert report["stream_items"] > 0
    assert report["stream_early_release"] == 0


def test_corpus_path_is_the_committed_fixture():
    assert CORPUS.exists()
