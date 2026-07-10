"""
📌 core/curated_causal.py — курируемые причинные связи World Skills Core.

Источники (по убыванию доверия):
  1. Явная таблица 00_CURATED_CAUSAL_RELATIONS.ru.md
  2. Опциональные колонки Causes/Enables/Requires/... в батч-таблицах
  3. Детерминированные OPS-эвристики (явно помечены inferred)
  4. Safety-эвристики внутри подтемы (явно помечены inferred)
"""
from __future__ import annotations

import os
import re
from collections.abc import Sequence
from typing import Any

from core.knowledge_linker import normalize_type, _tier
from core.world_skills_ingest import (
    DEFAULT_KNOWLEDGE_DIR,
    FACT_ID_RE,
    split_markdown_table_row,
)

CURATED_RELATIONS_BASENAME = "00_CURATED_CAUSAL_RELATIONS.ru.md"

# Приоритетные OPS-домены: порядок строк в батче = операционная последовательность.
PRIORITY_OPS_MARKERS = (
    "ELECTRICAL", "PLUMBING", "INFECTION", "FOOD_SAFETY", "GUTTER",
    "ROOF", "CONSTRUCTION", "MAINTENANCE", "EMERGENCY_PLUMBING",
    "ELECTRICAL_INSTALLATION", "PLUMBING_INSTALLATION",
)

RELATION_COLUMN_MAP = {
    "causes": "causes",
    "enables": "enables",
    "requires": "requires",
    "prevents": "prevents",
    "dependson": "requires",
    "depends_on": "requires",
}

CURATED_FORWARD_TYPES = frozenset({
    "causes", "enables", "requires", "prevents", "precedes",
})


def _parse_confidence(raw: str, default: float = 0.88) -> float:
    try:
        val = float(str(raw).strip().replace(",", "."))
        return max(0.5, min(1.0, val))
    except (TypeError, ValueError):
        return default


def _parse_targets(raw: str) -> list[str]:
    if not raw or not str(raw).strip():
        return []
    out: list[str] = []
    for token in re.split(r"[,;\s]+", str(raw).strip()):
        tid = token.strip().strip("`").strip()
        if tid and FACT_ID_RE.fullmatch(tid):
            out.append(tid)
    return out


def parse_curated_relations_table(text: str, source_file: str = "") -> list[dict[str, Any]]:
    """Парсить таблицу | source | relation | target | evidence | confidence |."""
    edges: list[dict[str, Any]] = []
    col_map: dict[str, int] = {}
    for line_no, line in enumerate(text.splitlines(), 1):
        if not line.lstrip().startswith("|"):
            continue
        cells = split_markdown_table_row(line)
        if len(cells) < 3:
            continue
        low = [c.lower().strip("` ").strip() for c in cells]
        if ("source" in low or "source_id" in low) and (
            "target" in low or "target_id" in low
        ) and "relation" in low:
            col_map = {name: low.index(name) for name in (
                "source", "relation", "target", "evidence", "confidence",
            ) if name in low}
            # альтернативные заголовки
            if "source_id" in low:
                col_map["source"] = low.index("source_id")
            if "target_id" in low:
                col_map["target"] = low.index("target_id")
            continue
        if all(set(c) <= set("-: ") for c in cells if c):
            continue
        if not col_map:
            continue
        src = cells[col_map["source"]].strip("` ").strip()
        tgt = cells[col_map["target"]].strip("` ").strip()
        rel = cells[col_map["relation"]].strip().lower()
        if not FACT_ID_RE.fullmatch(src) or not FACT_ID_RE.fullmatch(tgt):
            continue
        if rel not in CURATED_FORWARD_TYPES:
            continue
        evidence = ""
        if "evidence" in col_map and col_map["evidence"] < len(cells):
            evidence = cells[col_map["evidence"]].strip()
        conf = _parse_confidence(
            cells[col_map["confidence"]] if "confidence" in col_map and col_map["confidence"] < len(cells) else "",
        )
        edges.append(_curated_edge(
            src, tgt, rel, evidence or f"{source_file}:{line_no}",
            conf, source_file, line_no,
        ))
    return edges


def _curated_edge(
    source_id: str,
    target_id: str,
    relation_type: str,
    evidence: str,
    confidence: float,
    source_file: str = "",
    source_line: int | None = None,
) -> dict[str, Any]:
    return {
        "source_id": source_id,
        "target_id": target_id,
        "relation_type": relation_type,
        "confidence": confidence,
        "knowledge_status": "known",
        "inference_source": "manual",
        "edge_basis": "curated_explicit",
        "evidence": evidence,
        "source_file": source_file,
        "source_line": source_line,
    }


def _heuristic_edge(
    source_id: str,
    target_id: str,
    relation_type: str,
    evidence: str,
    confidence: float,
    edge_basis: str,
    source_file: str = "",
) -> dict[str, Any]:
    """Эвристическая связь: полезна для навигации, но не является curated fact."""
    return {
        "source_id": source_id,
        "target_id": target_id,
        "relation_type": relation_type,
        "confidence": confidence,
        "knowledge_status": "inferred",
        "inference_source": "autolinker",
        "edge_basis": edge_basis,
        "evidence": evidence,
        "source_file": source_file,
    }


def extract_inline_curated_edges(facts: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Извлечь связи из опциональных полей факта (Causes, Enables, ...)."""
    edges: list[dict[str, Any]] = []
    for fact in facts:
        fid = str(fact.get("fact_id", ""))
        if not fid:
            continue
        meta = fact.get("metadata") or {}
        source_file = str(meta.get("knowledge_file", ""))
        evidence_default = str(fact.get("evidence") or meta.get("evidence") or source_file)
        conf = _parse_confidence(fact.get("relation_confidence", ""), 0.9)
        for field, rel_type in (
            ("causes", "causes"),
            ("enables", "enables"),
            ("requires", "requires"),
            ("prevents", "prevents"),
            ("depends_on", "requires"),
        ):
            for tgt in _parse_targets(fact.get(field, "")):
                edges.append(_curated_edge(
                    fid, tgt, rel_type, evidence_default, conf, source_file,
                ))
    return edges


def _is_priority_ops_file(filename: str) -> bool:
    upper = filename.upper()
    return any(marker in upper for marker in PRIORITY_OPS_MARKERS)


def build_ops_sequence_edges(facts: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """OPS SOP: precedes между соседними строками в приоритетных батчах."""
    by_file: dict[str, list[dict[str, Any]]] = {}
    for fact in facts:
        fn = str((fact.get("metadata") or {}).get("knowledge_file", ""))
        if fn and _is_priority_ops_file(fn):
            by_file.setdefault(fn, []).append(fact)
    edges: list[dict[str, Any]] = []
    for fn, group in sorted(by_file.items()):
        ordered = group  # parse_knowledge_dir сохраняет порядок строк
        for prev, nxt in zip(ordered, ordered[1:]):
            prev_id, next_id = prev["fact_id"], nxt["fact_id"]
            if prev_id == next_id:
                continue
            edges.append(_heuristic_edge(
                prev_id, next_id, "precedes",
                f"SOP sequence in {fn}",
                0.82, "heuristic_ops_sequence", fn,
            ))
    return edges


def build_safety_edges(facts: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Safety-critical: safety_rule prevents failure_mode; method requires safety_rule."""
    edges: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()

    def _add(src: str, tgt: str, rel: str, evidence: str, conf: float = 0.86) -> None:
        key = (src, tgt, rel)
        if key in seen:
            return
        seen.add(key)
        edges.append(_heuristic_edge(
            src, tgt, rel, evidence, conf, "heuristic_safety",
        ))

    # 1) Внутри каждого приоритетного OPS-файла — локальные safety-связи.
    by_file: dict[str, list[dict[str, Any]]] = {}
    for fact in facts:
        fn = str((fact.get("metadata") or {}).get("knowledge_file", ""))
        if fn and _is_priority_ops_file(fn):
            by_file.setdefault(fn, []).append(fact)
    for fn, group in by_file.items():
        safety = [f for f in group if normalize_type(f.get("type")) in {"safety_rule", "control", "quality_check"}]
        failures = [f for f in group if normalize_type(f.get("type")) == "failure_mode"]
        actions = [f for f in group if normalize_type(f.get("type")) in {"method", "practical", "process_step", "process"}]
        for s in safety:
            for fail in failures:
                _add(s["fact_id"], fail["fact_id"], "prevents",
                     f"safety prevents failure in {fn}", 0.88)
            for act in actions:
                _add(act["fact_id"], s["fact_id"], "requires",
                     f"operation requires safety in {fn}", 0.85)

    # 2) Доменные safety-пакеты: infcontrol, foodservice.safety, plumb, electric.
    safety_domains = ("infcontrol", "foodservice", "plumb", "electric", "emergplumb", "gutter", "construction")
    by_domain: dict[str, list[dict[str, Any]]] = {}
    for fact in facts:
        dom = str(fact.get("fact_id", "")).split(".", 1)[0]
        if dom in safety_domains or ".safety." in fact.get("fact_id", ""):
            by_domain.setdefault(dom, []).append(fact)
    for dom, group in by_domain.items():
        safety = [f for f in group if normalize_type(f.get("type")) in {"safety_rule", "control", "quality_check"}]
        failures = [f for f in group if normalize_type(f.get("type")) == "failure_mode"]
        actions = [f for f in group if normalize_type(f.get("type")) in {"method", "practical", "process_step", "process"}]
        for s in safety[:40]:
            for fail in failures[:20]:
                _add(s["fact_id"], fail["fact_id"], "prevents",
                     f"domain safety prevents failure in {dom}", 0.86)
            for act in actions[:25]:
                _add(act["fact_id"], s["fact_id"], "requires",
                     f"domain operation requires safety in {dom}", 0.84)

    # 3) Ключевые cross-fact safety bridges (электрика, пищевая безопасность, инфекконтроль).
    _SAFETY_BRIDGES = (
        ("electric.ops.gfci_afci_operation_test", "electric.ops.residential_wiring_basics", "requires",
         "GFCI/AFCI testing required before energizing new residential circuits"),
        ("electric.ops.grounding_earthing_system", "electric.ops.electrical_panel_wiring", "requires",
         "Panel wiring requires proper grounding electrode system"),
        ("electric.ops.smoke_co_alarm_install", "electric.ops.residential_wiring_basics", "requires",
         "Smoke/CO alarms required in residential electrical scope"),
        ("emergplumb.ops.gas_leak_detection", "plumbing.ops.copper_soldering", "prevents",
         "Gas leak protocol prevents fire during plumbing hot work"),
        ("foodservice.safety.handwashing", "foodservice.safety.cross_contamination", "prevents",
         "Hand hygiene prevents cross-contamination"),
        ("foodservice.safety.temperature", "foodservice.safety.danger_zone", "prevents",
         "Temperature control prevents danger-zone bacterial growth"),
        ("foodservice.safety.haccp", "foodservice.safety.temperature", "requires",
         "HACCP requires continuous temperature monitoring"),
        ("infcontrol.ops.five_moments_hand_hygiene", "infcontrol.ops.contact_precautions", "requires",
         "Contact precautions require WHO five moments hand hygiene"),
        ("infcontrol.ops.isolation_donning_doffing", "infcontrol.ops.contact_precautions", "requires",
         "Isolation precautions require correct PPE donning/doffing"),
        ("gutter.ops.winter_ice_dam_prevention", "gutter.ops.slope_hanger_spacing", "requires",
         "Ice dam prevention requires correct gutter slope and hanger spacing"),
    )
    valid = {str(f.get("fact_id", "")) for f in facts}
    for src, tgt, rel, evidence in _SAFETY_BRIDGES:
        if src in valid and tgt in valid:
            _add(src, tgt, rel, evidence, 0.9)

    return edges


def build_foundation_bridges(facts: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Теория → практика: foundation --enables--> ops в том же 2-level namespace."""
    by_prefix: dict[str, list[dict[str, Any]]] = {}
    for fact in facts:
        fid = str(fact.get("fact_id", ""))
        parts = fid.split(".")
        if len(parts) < 2:
            continue
        prefix = ".".join(parts[:2])
        by_prefix.setdefault(prefix, []).append(fact)

    edges: list[dict[str, Any]] = []
    for prefix, group in by_prefix.items():
        foundations = sorted(
            (f for f in group if _tier(f.get("type")) <= 1 and ".ops." not in f["fact_id"]),
            key=lambda f: (_tier(f.get("type")), f["fact_id"]),
        )
        ops = sorted(
            (f for f in group if ".ops." in f["fact_id"] or f["fact_id"].endswith(".ops")),
            key=lambda f: f["fact_id"],
        )
        if not foundations or not ops:
            continue
        anchor = foundations[0]
        for op in ops[:3]:
            edges.append(_heuristic_edge(
                anchor["fact_id"], op["fact_id"], "enables",
                f"foundation→practice bridge in {prefix}",
                0.8, "heuristic_foundation",
            ))
    return edges


def load_curated_relations_file(
    knowledge_dir: str = DEFAULT_KNOWLEDGE_DIR,
) -> list[dict[str, Any]]:
    path = os.path.join(knowledge_dir, CURATED_RELATIONS_BASENAME)
    if not os.path.isfile(path):
        return []
    with open(path, encoding="utf-8") as fh:
        return parse_curated_relations_table(fh.read(), os.path.basename(path))


def link_curated_relations(
    facts: Sequence[dict[str, Any]],
    *,
    knowledge_dir: str = DEFAULT_KNOWLEDGE_DIR,
    valid_ids: set[str] | None = None,
) -> list[dict[str, Any]]:
    """Собрать все курируемые рёбра и отфильтровать по существующим fact_id."""
    if valid_ids is None:
        valid_ids = {str(f.get("fact_id", "")) for f in facts if f.get("fact_id")}
    raw = [
        *load_curated_relations_file(knowledge_dir),
        *extract_inline_curated_edges(facts),
        *build_ops_sequence_edges(facts),
        *build_safety_edges(facts),
        *build_foundation_bridges(facts),
    ]
    seen: set[tuple[str, str, str]] = set()
    out: list[dict[str, Any]] = []
    for edge in raw:
        src, tgt, rel = edge["source_id"], edge["target_id"], edge["relation_type"]
        if src not in valid_ids or tgt not in valid_ids or src == tgt:
            continue
        key = (src, tgt, rel)
        if key in seen:
            continue
        seen.add(key)
        out.append(edge)
    return out


__all__ = [
    "CURATED_RELATIONS_BASENAME",
    "PRIORITY_OPS_MARKERS",
    "build_foundation_bridges",
    "build_ops_sequence_edges",
    "build_safety_edges",
    "extract_inline_curated_edges",
    "link_curated_relations",
    "load_curated_relations_file",
    "parse_curated_relations_table",
]
