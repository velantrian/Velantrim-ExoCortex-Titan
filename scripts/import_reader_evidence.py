#!/usr/bin/env python3
"""Import returned Reader Core human evidence and write a readiness bundle.

Example:
    python scripts/import_reader_evidence.py \
      --root /secure/titan-reader-evidence \
      --spec /secure/titan-reader-evidence/evidence-spec.json \
      --submission-dir /secure/titan-reader-evidence/returns \
      --output /secure/titan-reader-evidence/artifacts/readiness.json

This command validates supplied human artifacts. It does not create labels,
execute a benchmark, or authorize promotion.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.reader_corpus_adjudication import ReaderCorpusError  # noqa: E402
from core.reader_evidence_import import (  # noqa: E402
    ReaderEvidenceImportError,
    ReaderEvidenceImporter,
)
from core.reader_evidence_intake import ReaderEvidenceIntakeError  # noqa: E402
from core.reader_evidence_pack import (  # noqa: E402
    ReaderEvidencePackBuilder,
    ReaderEvidencePackError,
    load_evidence_source_spec,
    write_canonical_json,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Import local human annotation and adjudication submissions, "
            "verify source spans, and write a deterministic readiness bundle."
        )
    )
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--spec", required=True, type=Path)
    parser.add_argument("--submission-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--require-ready",
        action="store_true",
        help=(
            "Exit 3 unless every evidence case is ready for benchmark. "
            "Readiness still does not execute or authorize a benchmark."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        spec = load_evidence_source_spec(args.spec)
        pack = ReaderEvidencePackBuilder().build(root=args.root, spec=spec)
        bundle = ReaderEvidenceImporter().import_directory(
            root=args.root,
            pack=pack,
            submission_directory=args.submission_dir,
        )
        write_canonical_json(args.output, bundle)
    except (
        ReaderEvidenceImportError,
        ReaderEvidencePackError,
        ReaderEvidenceIntakeError,
        ReaderCorpusError,
        OSError,
        UnicodeError,
    ) as exc:
        print(f"reader evidence import error: {exc}", file=sys.stderr)
        return 2

    stage_counts: dict[str, int] = {}
    for case in bundle.readiness.cases:
        stage_counts[case.stage.value] = stage_counts.get(case.stage.value, 0) + 1
    summary = {
        "adjudication_submission_count": len(
            bundle.adjudication_submissions
        ),
        "annotation_submission_count": len(bundle.annotation_submissions),
        "benchmark_executed": False,
        "bundle_id": bundle.bundle_id,
        "evidence_pack_id": bundle.evidence_pack_id,
        "is_ready_for_benchmark": bundle.readiness.is_ready_for_benchmark,
        "label_verification_count": len(bundle.label_verifications),
        "live_integration_authorized": False,
        "output": str(args.output),
        "readiness_report_id": bundle.readiness.report_id,
        "stage_counts": dict(sorted(stage_counts.items())),
    }
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    if args.require_ready and not bundle.readiness.is_ready_for_benchmark:
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
