#!/usr/bin/env python
"""Удаление автогенерированных шаблонных фактов из batch-файлов."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RU = ROOT / "docs/knowledge/world_skills_core/ru"
sys.path.insert(0, str(ROOT))

# Суффиксы из fill_sparse_auto.py
AUTO_SUFFIXES = {
    "intake_assessment", "safety_ppe_briefing", "site_prep_access",
    "tool_calibration_check", "execution_sequence", "quality_inspection_checklist",
    "customer_walkthrough", "documentation_photo_report", "pricing_transparency",
    "warranty_rework_policy", "scheduling_buffer", "material_selection_spec",
    "waste_disposal_compliance", "subcontractor_coordination", "emergency_stop_protocol",
    "training_new_crew", "inventory_restock", "invoice_itemization", "followup_feedback",
    "seasonal_preparation", "troubleshooting_common_fault", "regulatory_permit_check",
    "communication_delay_notice", "insurance_liability_proof", "upsell_maintenance_plan",
    "clinical_application_bridge", "differential_diagnosis_pearl", "diagnostic_workup_sequence",
    "treatment_first_line", "monitoring_parameters", "contraindication_screen",
    "documentation_note_standard", "patient_safety_check", "evidence_level_note",
    "lab_interpretation_pitfall", "anatomical_variant_clinical", "emergency_referral_criteria",
    "prevention_screening", "multidisciplinary_handoff", "ethics_consent_edge",
    "teaching_mnemonic", "research_translation_gap", "quality_metric_link",
    "simulation_training_drill", "resource_limited_adaptation",
}

# id.suffix или id.suffix_hash_123
SUFFIX_RE = re.compile(
    r"^\|\s*([a-z0-9_.]+)\.\s*("
    + "|".join(re.escape(s) for s in sorted(AUTO_SUFFIXES, key=len, reverse=True))
    + r")(?:_[a-f0-9]+(?:_\d+)?)?\s*\|",
    re.I,
)

MARKERS = (
    "При приёме работ по теме",
    "При приёме работ:",
    "Без оценки на месте — недооценка трудозатрат",
    "не в работ по теме",
    "Допработ по теме",
    "Гарантия на работ по теме",
)


def count_rows(text: str) -> int:
    return sum(
        1
        for l in text.splitlines()
        if l.startswith("|") and not l.startswith("|---") and "ID |" not in l
    )


def is_template_row(line: str) -> bool:
    if not line.startswith("|") or line.startswith("|---") or "ID |" in line:
        return False
    if SUFFIX_RE.match(line):
        return True
    return any(m in line for m in MARKERS)


def main() -> int:
    removed = 0
    files = 0
    for path in sorted(RU.glob("*.ru.md")):
        if "BATCH" not in path.name:
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        kept = [l for l in lines if not is_template_row(l)]
        n = len(lines) - len(kept)
        if not n:
            continue
        removed += n
        files += 1
        text = "\n".join(kept)
        if "**KnowledgeUnits:**" in text:
            text = re.sub(
                r"(\*\*KnowledgeUnits:\*\*\s*)\d+",
                rf"\g<1>{count_rows(text)}",
                text,
                count=1,
            )
        if not text.endswith("\n"):
            text += "\n"
        path.write_text(text, encoding="utf-8")
    print(f"Файлов очищено: {files}, строк удалено: {removed}")
    from core.world_skills_ingest import parse_knowledge_dir

    print(f"Парсер: {len(parse_knowledge_dir())} фактов")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
