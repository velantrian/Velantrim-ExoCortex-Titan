#!/usr/bin/env python3
"""Копирует ExoCortex-модули из Graphiti_fractal-main в VELANTRIM V8.6."""

from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT.parent / "Graphiti_fractal-main"
DST_CORE = ROOT / "core"
DST_BACKENDS = DST_CORE / "backends"

FILES = [
    "graph_store.py",
    "storage_facade.py",
    "types.py",
    "text_utils.py",
    "fsrs.py",
    "velum.py",
    "velum_bridge.py",
    "velum_context.py",
    "salience.py",
    "salience_fsrs.py",
    "etir.py",
    "etir_bridge.py",
    "immutable_core.py",
    "graph_ring_zero.py",
    "concept_emergence.py",
    "concept_promote.py",
    "concept_naming.py",
    "reasoning_bank.py",
    "causal_bridge.py",
    "response_audit.py",
    "focus_engine.py",
    "l45_bridge.py",
    "sae_prediction.py",
    "lsm_prediction.py",
    "predictive_fusion.py",
    "fusion_bridge.py",
    "decay_orchestrator.py",
    "daad.py",
    "vintage_decay.py",
    "epistemic_pipeline.py",
    "conversation_buffer.py",
    "velum_persistence.py",
]

BACKEND_FILES = [
    "__init__.py",
    "factory.py",
    "memory_graph.py",
    "sqlite_graph.py",
    "cypher_graph_base.py",
    "kuzu_graph.py",
    "ladybug_graph.py",
]

REPLACEMENTS = [
    (r"from core\.config import get_config", "from core.feature_config import get_config"),
    (r"from core\.config import", "from core.feature_config import"),
]


def patch_file(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    for old, new in REPLACEMENTS:
        text = re.sub(old, new, text)
    path.write_text(text, encoding="utf-8")


def main() -> None:
    if not SRC.is_dir():
        raise SystemExit(f"Источник не найден: {SRC}")

    DST_BACKENDS.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        s = SRC / "core" / name
        if not s.exists():
            print(f"skip missing: {name}")
            continue
        d = DST_CORE / name
        shutil.copy2(s, d)
        patch_file(d)
        print(f"copied: {name}")

    for name in BACKEND_FILES:
        s = SRC / "core" / "backends" / name
        if not s.exists():
            continue
        d = DST_BACKENDS / name
        shutil.copy2(s, d)
        patch_file(d)
        print(f"copied: backends/{name}")

    print("done")


if __name__ == "__main__":
    main()
